#!/usr/bin/env python3
"""Harvest St. Charles Parish Council legislation that may record drainage work.

Queries the public Legistar web API (no token needed for this client) for matters whose title
contains any search term, introduced on or after a start date, and writes one CSV row per matter.

Usage:
  legistar_harvest.py [--since YYYY-MM-DD] [--out FILE] [--terms-file FILE]
  legistar_harvest.py projects [--no-attachments]
                                                roll the harvest up to one row per parish project
                                                number in index/parish_projects.csv

One matter's history and attachment links: bayou:parish-council-agendas, `agendas.py track
st-charles <matter file>`.

The CSV is a raw harvest. A title match is not a finding: many matters that mention a canal or a
servitude have nothing to do with the Master Drainage Plan, and matching to plan rows is a
separate, reviewed step recorded in index/status.csv.
"""
import argparse
import csv
import json
import re
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

API = "https://webapi.legistar.com/v1/stcharlesgov"
# The gateway redirects to the public detail page; that page's own ID and GUID differ from the API's.
WEB = "https://stcharlesgov.legistar.com/gateway.aspx?m=l&id=/matter.aspx?key="
PAGE = 1000  # the API caps $top at 1000
ATTACH = "https://stcharlesgov.legistar1.com/stcharlesgov/attachments/"
# Titles from which no name can be parsed, or which name only one phase of a phased project.
NAMES = {
    "P200602": "West Bank Master Drainage Plan",
    "P200701": "Ormond area drainage surveying",
    "P200702": "Ormond and Montz railroad drainage surveying",
    "P240701": "Riverbend Drive hydrologic and hydraulic analysis (St. Rose)",
    "P210202": "Primrose Canal Cleaning and Improvements (phased; award shown is the latest phase)",
}

# Title substrings. Kept broad on purpose: council titles name the structure or street, and often
# never use the word "drainage".
TERMS = [
    "drainage", "pump station", "culvert", "canal", "jack and bore", "detention", "retention",
    "pond", "servitude", "levee", "flood", "stormwater", "storm water", "watershed",
    "hazard mitigation", "capital outlay", "T. Baker Smith", "Principal Engineering",
    "Consolidated Operating and Capital Budget",
    "railroad", "outfall", "ditch", "bank stabilization", "sump", "Willowdale", "Ashton",
    # Public Works project numbers (P + yymm + sequence) appear in nearly every contract title.
    "Project No. P", "Project Number P",
]

FIELDS = [
    "matter_file", "type", "status", "intro_date", "passed_date", "enactment_no", "title",
    "matched_terms", "url", "matter_id",
]


def get(path, params=None):
    url = f"{API}/{path}"
    if params:
        url += "?" + urllib.parse.urlencode(params, quote_via=urllib.parse.quote)
    for attempt in range(4):
        try:
            with urllib.request.urlopen(url, timeout=90) as r:
                return json.load(r)
        except Exception as e:  # transient gateway errors are common on this API
            if attempt == 3:
                raise
            print(f"retry {attempt + 1}: {e}", file=sys.stderr)
            time.sleep(3 * (attempt + 1))


def matters_for(term, since):
    esc = term.replace("'", "''")
    flt = f"MatterIntroDate ge datetime'{since}' and substringof('{esc}',MatterTitle)"
    skip = 0
    while True:
        page = get("matters", {"$filter": flt, "$top": PAGE, "$skip": skip,
                               "$orderby": "MatterIntroDate"})
        yield from page
        if len(page) < PAGE:
            return
        skip += PAGE


def web_url(m):
    return f"{WEB}{m['MatterId']}"


def harvest(since, out, terms):
    found = {}
    for term in terms:
        n = 0
        for m in matters_for(term, since):
            n += 1
            row = found.setdefault(m["MatterId"], {"m": m, "terms": []})
            row["terms"].append(term)
        print(f"{n:5d}  {term}", file=sys.stderr)
    rows = sorted(found.values(), key=lambda r: (r["m"]["MatterIntroDate"] or "", r["m"]["MatterFile"] or ""))
    with open(out, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        w.writeheader()
        for r in rows:
            m = r["m"]
            w.writerow({
                "matter_file": m["MatterFile"],
                "type": m["MatterTypeName"],
                "status": m["MatterStatusName"],
                "intro_date": (m["MatterIntroDate"] or "")[:10],
                "passed_date": (m["MatterPassedDate"] or "")[:10],
                "enactment_no": m["MatterEnactmentNumber"] or "",
                "title": " ".join((m["MatterTitle"] or "").split()),
                "matched_terms": "; ".join(r["terms"]),
                "url": web_url(m),
                "matter_id": m["MatterId"],
            })
    print(f"{len(rows)} matters -> {out}", file=sys.stderr)


PROJ_NO = re.compile(r"\b([PS]\d{6}(?:-\d+[A-Z]?)?)\b")
MONEY = re.compile(r"\$\s?([\d,]+(?:\.\d{2})?)")
DRAINAGE = re.compile(r"drainage|pump station|p\.s\.|canal|culvert|ditch|outfall|sump|bank stabilization"
                      r"|channel|bottleneck|hydraulic|stormwater|screen cleaner|t-wall|levee|flood", re.I)
LEVEE = re.compile(r"levee|t-wall|hurricane protection|P080905", re.I)
NOT_DRAINAGE = re.compile(r"oxidation pond|sewer|lift station|force main|wastewater", re.I)
PROJ_FIELDS = [
    "project_no", "name", "kind", "phase", "contractor", "contract_amount", "change_orders",
    "first_action", "last_action", "last_action_summary", "completion_docs", "plan_rows",
    "parish_report_status", "parish_report_est_cost",
    "matter_files", "award_link", "links",
]


def classify(title):
    t = title.lower()
    if "change order" in t:
        return "final change order" if "final" in t else "change order"
    if "amendment no" in t:
        return "amendment"
    if re.search(r"(professional|engineering) services|contract for engineering|agreement for professional"
                 r"|services agreement|services contract", t):
        return "services agreement"
    if re.search(r"execution of a (construction )?contract with|construction manager at risk", t):
        return "construction contract"
    if re.search(r"servitude|act of sale|purchase of|expropriat|donation", t):
        return "land or servitude"
    if re.search(r"cooperative endeavor|intergovernmental agreement|application|federally funded"
                 r"|funding", t):
        return "funding"
    return "other"


def project_name(title, no):
    """Council titles put the project name either just before or just after the number."""
    t = " ".join(title.split())
    m = re.search(r"(?:for|to) (?:the |a |an )?(?:construction of the )?([A-Z](?:[^()]|\(P\.S\.\)){3,90}?),? ?\(?(?:Parish )?"
                  r"Project (?:No\.|Number) ?" + re.escape(no), t)
    if m and not re.search(r"Agreement|Ordinance|Contract with|Order No", m.group(1)):
        return m.group(1).strip(" ,")
    m = re.search(r"for (?:the )?([A-Z][^()]{3,90}?) \(" + re.escape(no), t)
    if m and not re.search(r"Agreement|Ordinance|Contract with|Order No", m.group(1)):
        return m.group(1).strip(" ,")
    m = re.search(re.escape(no) + r",? ([A-Z][^,()]{3,80}?)(?:,| in the| with| to | for |\.|$)", t)
    name = m.group(1).strip() if m else ""
    return "" if name in ("Parish", "Public Works") else name


def attachment_url(a):
    """The API's hyperlink carries another client's path and returns 404; the file name is right."""
    return ATTACH + a["MatterAttachmentFileName"] if a.get("MatterAttachmentFileName") else a["MatterAttachmentHyperlink"]


def bare_no(project_no):
    m = PROJ_NO.search(project_no.replace(" ", ""))
    return m.group(1).split("-")[0] if m else ""


# The 10/8/2026 report prints P260803 on this line, but the council title under that number
# (2026-0265) is the pump station's design refinement. Joining by number would pin it to that row.
NOT_JOINED_BY_NUMBER = {"Engineers Canal Crossing at CPKC Railroad"}


def parish_report(tracker_csv, prior_csv):
    """Parish capital report lines by bare project number, and the same lines by their July number.

    The newest report lists active projects only, so an older line it doesn't continue is kept
    with its date. The second dict lets a project the parish renumbered still reach its council
    matters, which are filed under the old number.
    """
    by_no, by_old_no = {}, {}
    current = list(csv.DictReader(open(tracker_csv))) if Path(tracker_csv).exists() else []
    prior = list(csv.DictReader(open(prior_csv))) if Path(prior_csv).exists() else []
    continued = {r["july_project"] for r in current}
    old_no = {r["project"]: bare_no(r["project_no"]) for r in prior}
    for r in current:
        by_no.setdefault("" if r["project"] in NOT_JOINED_BY_NUMBER else bare_no(r["project_no"]), []).append(r)
        old = old_no.get(r["july_project"], "")
        if old and old != bare_no(r["project_no"]):
            by_old_no.setdefault(old, []).append(r)
    for r in prior:
        if r["project"] not in continued:
            by_no.setdefault(bare_no(r["project_no"]), []).append(
                r | {"status": f"{r['status']} (report of 7/31/2026; not listed 10/8/2026)"})
    return by_no, by_old_no


def completion_docs(matter_id):
    names = [a["MatterAttachmentName"] or "" for a in get(f"matters/{matter_id}/attachments")]
    return sorted({k for n in names for k in ("Substantial Completion", "Final Acceptance")
                   if k.lower() in n.lower()})


def projects(matters_csv, out, status_csv, attachments, tracker_csv, prior_csv):
    """Roll the harvested matters up to one row per parish project number."""
    plan = {}
    if Path(status_csv).exists():
        for r in csv.DictReader(open(status_csv)):
            for f in re.findall(r"file (\d{4}-\d{4})", r["parish_source"]):
                label = f"{r['doc'].replace('-executive-summary', '')} {r['project_id'] or r['name']}"
                plan.setdefault(f, [])
                if label not in plan[f]:
                    plan[f].append(label)
    report, renumbered = parish_report(tracker_csv, prior_csv)
    told = lambda no, f: " || ".join(f(t) for t in report.get(no.split("-")[0], []) + renumbered.get(no.split("-")[0], []))
    groups = {}
    for r in csv.DictReader(open(matters_csv)):
        if r["status"] not in ("Enacted", "Approved"):
            continue
        for no in set(PROJ_NO.findall(r["title"])):
            groups.setdefault(no, []).append(r)
    rows = []
    for no, ms in groups.items():
        text = " ".join(m["title"] for m in ms)
        if NOT_DRAINAGE.search(text) and not re.search(r"drainage|canal|culvert", text, re.I):
            continue
        if not DRAINAGE.search(text):
            continue
        ms.sort(key=lambda m: m["passed_date"] or m["intro_date"])
        acts = [(classify(m["title"]), m) for m in ms]
        kinds = {a for a, _ in acts}
        award = next((m for a, m in reversed(acts) if a == "construction contract"), None)
        when = lambda m: m["passed_date"] or m["intro_date"]
        finals = [when(m) for a, m in acts if a == "final change order"]
        awards = [when(m) for a, m in acts if a == "construction contract"]
        # A later phase can be awarded after an earlier phase has closed out.
        reopened = bool(finals and awards and max(awards) > max(finals))
        phase = ("complete" if finals and not reopened else
                 "construction" if award or "change order" in kinds else
                 "design" if kinds & {"services agreement", "amendment"} else "other")
        names = [n for n in (project_name(m["title"], no) for m in ms) if n]
        contractor = amount = ""
        if award:
            c = re.search(r"[Cc]ontract(?: \(Contract\))? with (.+?),? (?:for|to perform)", award["title"])
            contractor = c.group(1) if c else ""
            a = MONEY.search(award["title"])
            amount = a.group(1) if a else ""
        docs = []
        if attachments and phase in ("complete", "construction"):
            for _, m in acts:
                docs += completion_docs(m["matter_id"])
        last = ms[-1]
        rows.append({
            "project_no": no,
            "name": NAMES.get(no) or (max(sorted(set(names)), key=lambda n: (names.count(n), len(n))) if names else ""),
            "kind": "levee system" if LEVEE.search(text) else "drainage",
            "phase": phase,
            "contractor": contractor,
            "contract_amount": amount,
            "change_orders": sum(1 for a, _ in acts if "change order" in a),
            "first_action": ms[0]["passed_date"] or ms[0]["intro_date"],
            "last_action": last["passed_date"] or last["intro_date"],
            "last_action_summary": f"{classify(last['title'])} ({last['enactment_no'] or last['matter_file']})",
            "completion_docs": "; ".join(sorted(set(docs))),
            "plan_rows": "; ".join(sorted({p for m in ms for p in plan.get(m["matter_file"], [])})),
            "parish_report_status": told(no, lambda t: f"{t['project']}: {t['status']}"),
            "parish_report_est_cost": told(no, lambda t: t["est_construction_cost"]),
            "matter_files": " ".join(m["matter_file"] for m in ms),
            # Each Legistar page lists the matter's attachments: contract, bid tab, scope, certificates.
            "award_link": award["url"] if award else "",
            "links": " ".join(m["url"] for m in ms),
        })
    # The parish report also lists projects the council has not acted on by number in a title.
    seen = {r["project_no"].split("-")[0] for r in rows}
    for no, lines in report.items():
        if no in seen:
            continue
        for t in lines:
            rows.append(dict.fromkeys(PROJ_FIELDS, "") | {
                "project_no": t["project_no"], "name": t["project"],
                "kind": "levee system" if t["section"] == "Levee" else "drainage",
                "phase": "parish report only", "change_orders": 0, "plan_rows": t["plan_rows"],
                "parish_report_status": f"{t['project']}: {t['status']}",
                "parish_report_est_cost": t["est_construction_cost"],
            })
    rows.sort(key=lambda r: (r["kind"], r["project_no"]))
    with open(out, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=PROJ_FIELDS)
        w.writeheader()
        w.writerows(rows)
    print(f"{len(rows)} projects -> {out}", file=sys.stderr)


def main():
    here = Path(__file__).resolve().parent.parent
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd")
    pr = sub.add_parser("projects")
    pr.add_argument("--no-attachments", action="store_true",
                    help="skip the per-matter attachment lookups for completion certificates")
    ap.add_argument("--since", default="2020-01-01")
    ap.add_argument("--out", default=str(here / "index" / "legistar_matters.csv"))
    ap.add_argument("--terms-file", help="one title substring per line; replaces the built-in list")
    a = ap.parse_args()
    if a.cmd == "projects":
        projects(here / "index" / "legistar_matters.csv", here / "index" / "parish_projects.csv",
                 here / "index" / "status.csv", not a.no_attachments,
                 here / "index" / "parish_tracker_2026-10.csv", here / "index" / "parish_tracker_2026-07.csv")
        return
    terms = TERMS
    if a.terms_file:
        terms = [t.strip() for t in Path(a.terms_file).read_text().splitlines() if t.strip()]
    harvest(a.since, a.out, terms)


if __name__ == "__main__":
    main()
