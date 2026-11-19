#!/usr/bin/env python3
"""How the St. Charles Parish Council has decided, across meetings, from Legistar's public API.

  decisions.py rezonings [filters] [--csv FILE]     every rezoning ordinance since 1999
  decisions.py search --term TEXT [--term ...] [--type Ordinance] [filters] [--max N]
  decisions.py matter FILE                          one matter: every action, mover, seconder, vote
  decisions.py member NAME [filters]                one member's votes on the rezonings that match
  decisions.py like FILE [--top N]                  the past rezonings closest to one matter

Filters: --to CODE, --from CODE (zoning districts, e.g. M-2; "M-" for any M district),
--where TEXT (community or words in the title), --since YYYY, --until YYYY,
--result adopted|failed|..., --commission approval|denial|tabled|none.

The result comes from the matter's history, not its status label: a label can read "Enacted" on a
matter the Council postponed. Member votes are Council votes. Planning Commission recommendations
are history entries with no member votes; the Commission's roll calls are in its signed minutes.

Public data is cached in --cache (default ~/.cache/scp-civics/decisions), never in the plugin.
Stdlib only.
"""
import argparse, collections, concurrent.futures as cf, csv, json, os, re, sys, time
import urllib.parse, urllib.request
from pathlib import Path

PLUGIN_ROOT = Path(__file__).resolve().parents[3]
sys.dont_write_bytecode = True  # the plugin folder may be a read-only snapshot
API = "https://webapi.legistar.com/v1/stcharlesgov"
GATEWAY = "https://stcharlesgov.legistar.com/gateway.aspx?M=L&ID={id}"
DEFAULT_CACHE = Path(os.environ.get("XDG_CACHE_HOME", Path.home() / ".cache")) / "scp-civics" / "decisions"
PAGE = 1000  # the API caps $top at 1000
WORKERS = 6
# Title wordings of a map amendment. Each misses some years; together they found 431 ordinances
# from 1999 to 2026 when checked on 2026-11-16.
REZONING_PHRASES = ("zoning classification", "change of zoning")
COMMISSION_BODY = 166  # SCP Planning & Zoning Commission's Legistar body id
COUNCIL = "Parish Council"
COMMISSION = "Planning Commission"
STAFF = "Department of Planning & Zoning"
PRESIDENT = "Parish President"

# A district code, allowing the hyphen to be missing as older titles sometimes have it ("B1", "OL").
CODE = re.compile(r"(?<![\w-])(O-?L|PUD|[A-Z]{1,3}-?\d[A-Z]{0,2}(?:\s?\([A-Z]{1,2}\))?)(?![\w-])")
# Where a "to" list of districts stops and the property description begins.
PLACE_START = re.compile(r"\s(?:on|at|for|in|located|fronting|along|of property|property)\b", re.I)
REQUESTER = re.compile(r"\bas requested by\b.*$", re.I)
COMMUNITIES = ("Ama", "Bayou Gauche", "Boutte", "Des Allemands", "Destrehan", "Good Hope", "Hahnville", "Killona",
               "Luling", "Montz", "New Sarpy", "Norco", "Paradis", "St. Rose", "Taft", "Mimosa Park", "Willowdale")
# Words in a property description that say nothing about where it is.
PLACE_STOP = {"lot", "lots", "square", "sq", "block", "tract", "tracts", "portion", "property", "properties",
              "parcel", "subdivision", "designated", "being", "located", "highway", "hwy", "parish", "louisiana",
              "la", "st", "charles", "the", "and", "of", "on", "at", "a", "an", "to", "as", "side", "east", "west",
              "north", "south", "street", "road", "drive", "avenue", "lane", "approximately", "acres", "acre",
              "section", "sections", "zoning", "district", "ordinance", "classification", "change", "from", "in",
              "known", "formerly", "adjacent", "fronting", "undeveloped", "with", "by", "for", "or", "all", "ft",
              "plantation", "business", "park", "estates", "place", "addition", "remainder", "revised", "resubdivided"}


# ---------- fetching and cache ----------

def check_path(path):
    if Path(path).resolve().is_relative_to(PLUGIN_ROOT):
        sys.exit(f"{path} is inside the plugin. The cache and exports go outside it.")


def get(path, params=None):
    url = f"{API}/{path}"
    if params:
        url += "?" + urllib.parse.urlencode(params, quote_via=urllib.parse.quote, safe="$'(),")
    for attempt in range(4):
        try:
            with urllib.request.urlopen(url, timeout=90) as r:
                return json.load(r)
        except Exception:  # transient gateway errors are common on this API
            if attempt == 3:
                raise
            time.sleep(2 * (attempt + 1))


def list_matters(flt):
    out, skip = [], 0
    while True:
        rows = get("matters", {"$filter": flt, "$top": PAGE, "$skip": skip})
        out += rows
        if len(rows) < PAGE:
            return out
        skip += PAGE


def quote(text):
    return text.replace("'", "''")


def rezoning_matters():
    found = {}
    for phrase in REZONING_PHRASES:
        for m in list_matters(f"substringof('{quote(phrase)}',MatterTitle) and MatterTypeName eq 'Ordinance'"):
            found[m["MatterId"]] = m
    return list(found.values())


def search_matters(terms, kind, since, until):
    found = {}
    for term in terms:
        flt = f"substringof('{quote(term)}',MatterTitle)"
        if kind:
            flt += f" and MatterTypeName eq '{quote(kind)}'"
        if since:
            flt += f" and MatterIntroDate ge datetime'{since}-01-01'"
        if until:
            flt += f" and MatterIntroDate lt datetime'{int(until) + 1}-01-01'"
        for m in list_matters(flt):
            found[m["MatterId"]] = m
    return list(found.values())


def decided(h):
    """A history row carries member votes only when it records a vote with a pass or fail flag."""
    return h.get("MatterHistoryEventId") and h.get("MatterHistoryPassedFlagName")


def load_record(matter, cache, refresh=False):
    """The matter with its histories and the votes on each decided history row, cached by its
    last-modified stamp. The history row's id is also its event item id, which the votes hang on."""
    path = cache / "matters" / f"{matter['MatterId']}.json"
    if path.exists() and not refresh:
        rec = json.loads(path.read_text())
        if rec.get("modified") == matter.get("MatterLastModifiedUtc"):
            return rec
    histories = get(f"matters/{matter['MatterId']}/histories")
    votes = {str(h["MatterHistoryId"]): get(f"eventitems/{h['MatterHistoryId']}/votes")
             for h in histories if decided(h)}
    rec = {"modified": matter.get("MatterLastModifiedUtc"), "matter": matter, "histories": histories, "votes": votes}
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(rec))
    tmp.replace(path)
    return rec


def load_all(matters, cache, refresh=False):
    check_path(cache)
    records, failed = [], []
    with cf.ThreadPoolExecutor(WORKERS) as ex:
        futures = {ex.submit(load_record, m, cache, refresh): m for m in matters}
        for fut in cf.as_completed(futures):
            try:
                records.append(fut.result())
            except Exception as exc:
                failed.append(f"{futures[fut].get('MatterFile')}: {type(exc).__name__}")
    records.sort(key=lambda r: (r["matter"].get("MatterIntroDate") or "", r["matter"].get("MatterFile") or ""))
    return records, failed


# ---------- reading a record ----------

def squash(text):
    return re.sub(r"\s+", " ", text or "").strip()


def action(h):
    """The action name without Legistar's version suffix and doubled spaces: "Approved 1" -> "approved"."""
    return re.sub(r"\s+1$", "", squash(h.get("MatterHistoryActionName"))).lower()


def ordered(histories):
    return sorted(histories, key=lambda h: (h.get("MatterHistoryActionDate") or "", h.get("MatterHistoryMinutesSequence") or 0,
                                            h.get("MatterHistoryId") or 0))


def council_result(histories):
    """(result, deciding history row) from the Council's last decisive action.

    Later actions override earlier ones, so a reconsideration, a removal from the table or a
    reintroduction reopens a matter, and a veto override vote settles it. The clerk often follows a
    voted row with an unvoted one naming the same result ("Postponed Indefinitely", "Failed"); the
    voted row stays the deciding one, because it holds the roll call.
    """
    result, row = "no Council decision recorded", None
    for h in ordered(histories):
        body, name, flag = h.get("MatterHistoryActionBodyName"), action(h), h.get("MatterHistoryPassedFlagName")
        found = None
        if body == PRESIDENT and name.startswith("vetoed"):
            found = "vetoed by the Parish President"
        elif body != COUNCIL:
            continue
        elif name.startswith("approved notwithstanding"):
            found = "veto overridden" if flag == "Pass" else "veto sustained"
        elif name == "veto sustained":
            found = "veto sustained"
        elif name.startswith(("approved", "adopted")) and flag:
            found = "adopted" if flag == "Pass" else "failed"
        elif name == "failed":
            found = "failed"
        elif name.startswith(("rmv'd from consid", "removed from consideration")) and flag != "Fail":
            found = "removed from consideration (Council Rule 8)" if "rule 8" in name else "removed from consideration"
        elif name.startswith("postponed indefinitely") and "reintroduced" not in name and flag != "Fail":
            # Under Council Rule 8 a matter lapses this way with no vote, after sitting on the table.
            found = "postponed indefinitely (Council Rule 8)" if "rule 8" in name else "postponed indefinitely"
        elif name.startswith("tabled") and flag != "Fail":
            found = "tabled"
        elif ("reintroduced" in name or name.startswith("removed from the table") or name == "reconsidered") and flag != "Fail":
            found = "reopened, no later decision recorded"
        if found is None:
            continue
        if found == result and row is not None and row.get("MatterHistoryPassedFlagName") and not flag:
            continue
        result, row = found, h
    return result, row


def recommendation(histories, body):
    """The last recommendation a body made, as Legistar labels it, or "" if none is recorded."""
    rec = ""
    for h in ordered(histories):
        if h.get("MatterHistoryActionBodyName") == body:
            name = squash(h.get("MatterHistoryActionName"))
            if re.search(r"rec|rcmnd|tabled", name, re.I) and "assigned" not in name.lower():
                rec = re.sub(r"\s+1$", "", name).replace("Rcmnd'd", "Recommended")
    return rec


def president_action(histories):
    for h in reversed(ordered(histories)):
        if h.get("MatterHistoryActionBodyName") == PRESIDENT and action(h) != "introduced":
            return squash(h.get("MatterHistoryActionName"))
    return ""


LABELS = {"adopted": {"Enacted", "Approved", "Adopted"}, "veto overridden": {"Enacted", "Approved", "Adopted"},
          "failed": {"Failed"}, "veto sustained": {"Vetoed"}, "vetoed by the Parish President": {"Vetoed"},
          "postponed indefinitely": {"Postponed Indefinitely"},
          "postponed indefinitely (Council Rule 8)": {"Postponed (Council Rule 8)", "Postponed Indefinitely"},
          "tabled": {"Tabled"}}
# Labels that don't claim a decision, so a history with none doesn't contradict them.
UNDECIDED = {"", "Filed", "Introduced", "Pending", "Tabled", "In Committee", "Agenda Ready", "Draft"}


def label_note(matter, result):
    """Say where Legistar's status label and the history disagree."""
    status = squash(matter.get("MatterStatusName"))
    notes = []
    if status == "Enacted" and not matter.get("MatterEnactmentNumber"):
        notes.append("label Enacted with no enactment number")
    expected = LABELS.get(result)
    if result.startswith("removed"):
        expected = {s for s in [status] if s.lower().startswith("removed")} or {"Removed from Consideration"}
    if expected is not None and status not in expected:
        notes.append(f"label {status} disagrees with history")
    if (result.startswith(("no Council decision", "reopened"))) and status not in UNDECIDED:
        notes.append(f"label {status} but no Council decision in the history")
    return "; ".join(notes)


def person(name):
    """Name without the seat label: "Pat Example (Dist. 2)" -> ("Pat Example", "Dist. 2")."""
    m = re.match(r"(.*?)\s*\(([^)]*)\)\s*$", squash(name))
    return (m.group(1), m.group(2)) if m else (squash(name), "")


def tally(votes):
    counts = collections.Counter(v.get("VoteValueName") or "?" for v in votes)
    others = [f"{v.get('VoteValueName')}: {person(v.get('VotePersonName'))[0]}" for v in votes
              if (v.get("VoteValueName") or "") not in ("Yea", "Aye")]
    if not votes:
        return "no member votes in API", []
    yes = counts.get("Yea", 0) + counts.get("Aye", 0)
    no = counts.get("Nay", 0) + counts.get("No", 0)
    return f"{yes}-{no}", others


def summarize(rec):
    m, hs = rec["matter"], rec["histories"]
    result, row = council_result(hs)
    votes = rec["votes"].get(str(row["MatterHistoryId"]), []) if row else []
    count, others = tally(votes)
    title = squash(m.get("MatterTitle"))
    frm, to = districts(title)
    return {
        "file": m.get("MatterFile"), "intro": (m.get("MatterIntroDate") or "")[:10], "title": title,
        "from": frm, "to": to, "where": communities(title),
        "staff": recommendation(hs, STAFF), "commission": recommendation(hs, COMMISSION),
        "result": result, "decided": (row.get("MatterHistoryActionDate") or "")[:10] if row else "",
        "action": squash(row.get("MatterHistoryActionName")) if row else "", "votes": count, "others": others,
        "passed": bool(row) and row.get("MatterHistoryPassedFlagName") == "Pass",
        "mover": squash(row.get("MatterHistoryMoverName")) if row else "",
        "seconder": squash(row.get("MatterHistorySeconderName")) if row else "",
        "president": president_action(hs),
        "status": squash(m.get("MatterStatusName")), "enactment": m.get("MatterEnactmentNumber") or "",
        "note": label_note(m, result), "url": GATEWAY.format(id=m["MatterId"]), "id": m["MatterId"],
        "vote_rows": votes,
    }


# ---------- titles ----------

def norm_code(code):
    c = code.upper().replace(" ", "")
    c = re.sub(r"^([A-Z]+)(\d)", r"\1-\2", c)
    if c == "OL":
        c = "O-L"
    return "R-1A(M)" if c == "R-1AM" else c


def districts(title):
    """(from codes, to codes) of a map amendment's title, or two empty lists for a text amendment.

    A title can carry several "from ... to ..." clauses ("from R-1A to O-L on Lot 1 and from C-2
    to O-L on Lot 2"), and district names sit between codes ("from C-3, Highway Commercial to M-1,
    Light Manufacturing and Industry").
    """
    text = REQUESTER.sub("", squash(title))
    frm, to = [], []
    for clause in re.split(r"\bfrom\b", text, flags=re.I)[1:]:
        split = re.search(r"\sto\s+(?=[\"']?(?:O-?L|PUD|[A-Z]{1,3}-?\d))", clause)
        if not split:
            continue
        left, right = clause[:split.start()], clause[split.end():]
        stop = PLACE_START.search(right)
        right = right[:stop.start()] if stop else right
        frm += [norm_code(c) for c in CODE.findall(left)]
        to += [norm_code(c) for c in CODE.findall(right)]
    return sorted(set(frm)), sorted(set(to))


def communities(title):
    text = REQUESTER.sub("", squash(title))
    return [c for c in COMMUNITIES if re.search(rf"\b{re.escape(c)}\b", text, re.I)]


def place_words(title):
    text = REQUESTER.sub("", squash(title))
    m = PLACE_START.search(text.split(" to ", 1)[-1]) if " to " in text else None
    tail = text[text.find(m.group(0)):] if m else text
    words = re.findall(r"[A-Za-z][A-Za-z'.-]+", tail)
    return {w.lower().strip(".'") for w in words if w.lower().strip(".'") not in PLACE_STOP and len(w) > 2}


# ---------- filters and output ----------

def code_match(want, codes):
    want = norm_code(want) if not want.endswith("-") else want.upper()
    return any(c.startswith(want) if want.endswith("-") else c == want for c in codes)


def keep(s, a):
    year = s["intro"][:4]
    if getattr(a, "since", None) and year < str(a.since):
        return False
    if getattr(a, "until", None) and year > str(a.until):
        return False
    if getattr(a, "to", None) and not code_match(a.to, s["to"]):
        return False
    if getattr(a, "frm", None) and not code_match(a.frm, s["from"]):
        return False
    if getattr(a, "where", None) and a.where.lower() not in REQUESTER.sub("", s["title"]).lower():
        return False
    if getattr(a, "result", None) and not s["result"].startswith(a.result.lower()):
        return False
    if getattr(a, "commission", None):
        want = a.commission.lower()
        have = s["commission"].lower()
        if (want == "none" and have) or (want != "none" and want not in have):
            return False
    return True


def cell(text):
    return str(text).replace("|", "/").replace("\n", " ")


def table(rows, titles=False):
    head = "| File | Intro | From → to | Where | Staff | Commission | Council result | Vote | Not yea | Label |"
    out = [head, "|---" * (head.count("|") - 1) + "|"]
    for s in rows:
        out.append("| " + " | ".join(cell(x) for x in (
            f"[{s['file']}]({s['url']})", s["intro"],
            f"{', '.join(s['from']) or '?'} → {', '.join(s['to']) or '?'}" if s["from"] or s["to"] else "",
            ", ".join(s["where"]), s["staff"], s["commission"], f"{s['result']} {s['decided']}".strip(), s["votes"],
            "; ".join(s["others"]), s["note"] or s["status"])) + " |")
        if titles:
            out.append(f"|  | {cell(s['title'][:600])} |||||||||")
    return out


def crosstab(rows):
    grid = collections.Counter((s["commission"] or "none recorded", s["result"]) for s in rows)
    results = sorted({r for _, r in grid})
    recs = sorted({c for c, _ in grid})
    out = ["| Commission \\ Council | " + " | ".join(results) + " |", "|---|" + "---|" * len(results)]
    out += [f"| {c} | " + " | ".join(str(grid.get((c, r), 0)) for r in results) + " |" for c in recs]
    return out


def write_csv(rows, path):
    check_path(path)
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    fields = ["file", "intro", "from", "to", "where", "staff", "commission", "result", "decided", "action", "votes",
              "others", "mover", "seconder", "president", "status", "enactment", "note", "url", "title"]
    with open(path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        for s in rows:
            w.writerow({k: "; ".join(s[k]) if isinstance(s[k], list) else s[k] for k in fields})
    print(f"Saved: {path}")


def report(rows, failed, scope, a, rezoning=True):
    print(f"# {scope}\n")
    print(f"Matching: {len(rows)}. Source: Legistar API, read {time.strftime('%Y-%m-%d')}. "
          "Result from each matter's history; Vote is the Council vote on the deciding action.\n")
    if failed:
        print(f"Not read, so left out: {', '.join(failed)}\n")
    by = collections.Counter(s["result"] for s in rows)
    print("Results: " + "; ".join(f"{k} {v}" for k, v in by.most_common()) + "\n")
    print("\n".join(table(rows, getattr(a, "titles", False) or not rezoning)))
    if rows:
        print("\n## Commission recommendation against Council result\n")
        print("\n".join(crosstab(rows)))
    text = [s for s in rows if not s["from"] and not s["to"]]
    if text and rezoning:
        print(f"\n{len(text)} of these have no 'from ... to ...' districts in the title. They may be text amendments "
              "or titles worded another way; check the title (--titles).")
    flagged = [s["file"] for s in rows if s["note"]]
    if flagged:
        print(f"\nStatus label and history disagree, or Enacted has no number: {', '.join(flagged)}. Check the "
              "minutes before stating an outcome.")
    if getattr(a, "csv", None):
        write_csv(rows, a.csv)


def cmd_rezonings(a):
    records, failed = load_all(rezoning_matters(), Path(a.cache), a.refresh)
    rows = [s for s in map(summarize, records) if keep(s, a)]
    report(rows, failed, "Rezoning ordinances, St. Charles Parish Council", a)


def cmd_search(a):
    matters = search_matters(a.term, a.type, a.since, a.until)
    if len(matters) > a.max:
        sys.exit(f"{len(matters)} matters match. Narrow the terms, add --type or --since, or raise --max.")
    records, failed = load_all(matters, Path(a.cache), a.refresh)
    rows = [s for s in map(summarize, records) if keep(s, a)]
    report(rows, failed, f"Matters with {' or '.join(repr(t) for t in a.term)} in the title", a, rezoning=False)


def find_matter(file):
    rows = get("matters", {"$filter": f"MatterFile eq '{quote(file)}'"})
    if not rows:
        sys.exit(f"No matter {file} in Legistar.")
    return rows[0]


def commission_event(date):
    """The Commission's Legistar meeting on a date, whose signed minutes hold its roll call."""
    try:
        events = get("events", {"$filter": f"EventBodyId eq {COMMISSION_BODY} and EventDate eq datetime'{date}'"})
    except Exception:
        return None
    return events[0] if events else None


def cmd_matter(a):
    check_path(a.cache)
    rec = load_record(find_matter(a.file), Path(a.cache), a.refresh)
    s = summarize(rec)
    print(f"# {s['file']}: {s['title']}\n\n{s['url']}\n")
    print(f"Intro {s['intro']}. From {', '.join(s['from']) or '?'} to {', '.join(s['to']) or '?'}. "
          f"Legistar label: {s['status']}, enactment number {s['enactment'] or 'blank'}.")
    print(f"Result from history: **{s['result']}** {s['decided']}" + (f" ({s['note']})" if s["note"] else "") + "\n")
    print("| Date | Body | Action | Result | Mover | Seconder | Votes |\n|---|---|---|---|---|---|---|")
    for h in ordered(rec["histories"]):
        votes = rec["votes"].get(str(h["MatterHistoryId"]), [])
        by = collections.defaultdict(list)
        for v in votes:
            by[v.get("VoteValueName")].append(person(v.get("VotePersonName"))[0])
        vtext = "; ".join(f"{k} ({len(v)}): {', '.join(v)}" for k, v in by.items())
        print("| " + " | ".join(cell(x) for x in (
            (h.get("MatterHistoryActionDate") or "")[:10], h.get("MatterHistoryActionBodyName") or "",
            squash(h.get("MatterHistoryActionName")), h.get("MatterHistoryPassedFlagName") or "",
            squash(h.get("MatterHistoryMoverName")), squash(h.get("MatterHistorySeconderName")), vtext)) + " |")
    texts = [squash(h.get("MatterHistoryActionText")) for h in ordered(rec["histories"]) if decided(h)]
    if texts:
        print("\nMotion text as the clerk recorded it:")
        print("\n".join(f"- {t}" for t in texts if t))
    for h in ordered(rec["histories"]):
        if h.get("MatterHistoryActionBodyName") == COMMISSION:
            e = commission_event((h.get("MatterHistoryActionDate") or "")[:10])
            where = (f"Legistar event {e['EventId']}, {e['EventInSiteURL']}" if e
                     else "no Commission meeting on that date in the Legistar API (it holds Commission meetings from 2025 on)")
            print(f"\nCommission action {(h.get('MatterHistoryActionDate') or '')[:10]}: {squash(h.get('MatterHistoryActionName'))}. "
                  f"No member votes in the API. Roll call: signed minutes, {where}.")
            break


def matches_person(name, query):
    return query.lower() in squash(name).lower()


def cmd_member(a):
    records, failed = load_all(rezoning_matters(), Path(a.cache), a.refresh)
    rows = [s for s in map(summarize, records) if keep(s, a)]
    mine, seats = [], collections.Counter()
    for s in rows:
        for v in s["vote_rows"]:
            if matches_person(v.get("VotePersonName"), a.name):
                name, seat = person(v.get("VotePersonName"))
                seats[(v.get("VotePersonId"), name, seat)] += 1
                mine.append((s, v.get("VoteValueName")))
    if not mine:
        sys.exit(f"No Council votes by a member matching '{a.name}' on the rezonings that match the filters.")
    print(f"# Votes matching '{a.name}' on rezoning ordinances\n")
    print("People matched (Legistar person id, name, seat label as recorded):")
    print("\n".join(f"- {pid} {name} ({seat}): {n} votes" for (pid, name, seat), n in seats.most_common()))
    if len({pid for pid, _, _ in seats}) > 1:
        print("\nMore than one person matched. Narrow the name before reading the counts below.")
    print("\nVotes by value: " + "; ".join(f"{k} {v}" for k, v in collections.Counter(x for _, x in mine).most_common()))
    against = [(s, x) for s, x in mine
               if (x in ("Yea", "Aye") and not s["passed"]) or (x in ("Nay", "No") and s["passed"])
               or x not in ("Yea", "Aye", "Nay", "No")]
    print(f"\n## On the losing side of the deciding vote, or not voting yea or nay: {len(against)}\n")
    print("The deciding vote can be a motion to postpone or remove, not only to adopt; see the Council result. "
          "Absences, abstentions and recusals are listed too. Read the minutes for why.\n")
    print("| File | Intro | From → to | Where | Commission | Council result | Vote | This member |\n|---|---|---|---|---|---|---|---|")
    for s, x in against:
        print(f"| [{s['file']}]({s['url']}) | {s['intro']} | {', '.join(s['from'])} → {', '.join(s['to'])} | "
              f"{', '.join(s['where'])} | {s['commission']} | {s['result']} | {s['votes']} | {x} |")
    if failed:
        print(f"\nNot read, so left out: {', '.join(failed)}")


def similarity(base, other):
    """Shared districts weigh most, then shared place words. Returns (score, reasons)."""
    score, why = 0, []
    to = set(base["to"]) & set(other["to"])
    frm = set(base["from"]) & set(other["from"])
    where = set(base["where"]) & set(other["where"])
    words = place_words(base["title"]) & place_words(other["title"])
    if to:
        score += 4 * len(to)
        why.append(f"to {', '.join(sorted(to))}")
    if frm:
        score += 2 * len(frm)
        why.append(f"from {', '.join(sorted(frm))}")
    if where:
        score += 2
        why.append(", ".join(sorted(where)))
    if words - {w.lower() for w in base["where"]}:
        score += min(3, len(words))
        why.append("words: " + ", ".join(sorted(words)[:6]))
    return score, why


def cmd_like(a):
    check_path(a.cache)
    target = summarize(load_record(find_matter(a.file), Path(a.cache), a.refresh))
    records, failed = load_all(rezoning_matters(), Path(a.cache), a.refresh)
    scored = []
    for s in map(summarize, records):
        if s["id"] == target["id"]:
            continue
        score, why = similarity(target, s)
        if score:
            scored.append((score, s["intro"], s, why))
    scored.sort(key=lambda x: (x[0], x[1]), reverse=True)  # closest first, newer first among equals
    print(f"# Past rezonings closest to {target['file']}\n")
    print(f"{target['file']}: from {', '.join(target['from']) or '?'} to {', '.join(target['to']) or '?'}; "
          f"{', '.join(target['where']) or 'no community named'}; result so far {target['result']}.\n")
    print("Ranked by shared target district, then shared original district, community and place words. "
          "Closeness is by title only; a similar title isn't a similar case until the record is read.\n")
    print("| Score | File | Intro | From → to | Where | Commission | Council result | Vote | Not yea | Why |")
    print("|---|---|---|---|---|---|---|---|---|---|")
    for score, _, s, why in scored[:a.top]:
        print(f"| {score} | [{s['file']}]({s['url']}) | {s['intro']} | {', '.join(s['from'])} → {', '.join(s['to'])} | "
              f"{', '.join(s['where'])} | {s['commission']} | {s['result']} | {s['votes']} | {cell('; '.join(s['others']))} | "
              f"{cell('; '.join(why))} |")
    if failed:
        print(f"\nNot read, so left out: {', '.join(failed)}")


def add_filters(p):
    p.add_argument("--to", help="district the land goes to, e.g. M-2; M- for any M district")
    p.add_argument("--from", dest="frm", help="district the land comes from")
    p.add_argument("--where", help="community or other words in the title, applicant names excluded")
    p.add_argument("--since", type=int, help="first year of introduction")
    p.add_argument("--until", type=int, help="last year of introduction")
    p.add_argument("--result", help="adopted, failed, removed, postponed, tabled, veto, vetoed, reopened, no")
    p.add_argument("--commission", help="approval, denial, stip, tabled, or none")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--cache", default=str(DEFAULT_CACHE))
    ap.add_argument("--refresh", action="store_true", help="refetch every record instead of trusting the cache")
    sp = ap.add_subparsers(dest="cmd", required=True)
    p = sp.add_parser("rezonings"); add_filters(p); p.add_argument("--csv"); p.add_argument("--titles", action="store_true")
    p.set_defaults(fn=cmd_rezonings)
    p = sp.add_parser("search"); add_filters(p); p.add_argument("--term", action="append", required=True)
    p.add_argument("--type", help="Ordinance, Resolution, Motion, ..."); p.add_argument("--max", type=int, default=200)
    p.add_argument("--csv"); p.add_argument("--titles", action="store_true")
    p.set_defaults(fn=cmd_search)
    p = sp.add_parser("matter"); p.add_argument("file"); p.set_defaults(fn=cmd_matter)
    p = sp.add_parser("member"); p.add_argument("name"); add_filters(p); p.set_defaults(fn=cmd_member)
    p = sp.add_parser("like"); p.add_argument("file"); p.add_argument("--top", type=int, default=15)
    p.set_defaults(fn=cmd_like)
    a = ap.parse_args()
    a.fn(a)


if __name__ == "__main__":
    main()
