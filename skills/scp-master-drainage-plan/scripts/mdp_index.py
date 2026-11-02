#!/usr/bin/env python3
"""Index, arithmetic-check and search the St. Charles Parish Master Drainage Plan Markdown.

Reads the verified Markdown in the MDP folder and never writes to it. The plan documents come in
two layouts, and both are handled here:

  phase layout (East Bank volumes)   | 1-3: Title<br>scope lines... | $ 2,480,000.00 |
  group layout (West Bank watersheds) | 1 | IG-2 | Name | $424,100 | $646,500 |

Usage:
  mdp_index.py build [--mdp DIR] [--out DIR]   write projects.csv and figures.csv
  mdp_index.py check [--mdp DIR]               sum project rows against printed subtotals/totals
  mdp_index.py find  [--mdp DIR] TERM...       where a street, canal or structure is named
"""
import argparse
import csv
import os
import re
import sys

SKILL_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_MDP = os.path.join(SKILL_DIR, "corpus")
DEFAULT_OUT = os.path.join(SKILL_DIR, "index")

MONEY = re.compile(r"\$\s*([\d,]+(?:\.\d+)?)")
PHASE_ROW = re.compile(r"^(\(Alt[^)]*\)\s*)?(\d+-\d+(?:\.\d+)?)\s*(\([^)]*\))?\s*:\s*(.*)$", re.S)
# OCR reads the dollar sign in a cost cell as S, s or 6; the digits after it are still the printed value.
COST_CELL = re.compile(r"^(?:[$Ss6]\s+|\$)?\s*([\d,]{3,}(?:\.\d+)?)$")
IG_ID = re.compile(r"^IG[-\s]?(\d+)$", re.I)
PROJECT_FIELDS = ["doc", "bank", "page", "table", "table_title", "scheme", "row_kind", "project_id",
                  "name", "scope", "cost", "cost_25yr", "cost_100yr", "needs_review", "snapshot"]
FIGURE_FIELDS = ["doc", "bank", "page", "figure", "image", "description"]


def money(text):
    m = MONEY.search(text or "")
    return float(m.group(1).replace(",", "")) if m else None


def cell_cost(text):
    m = COST_CELL.match((text or "").strip())
    return float(m.group(1).replace(",", "")) if m else None


def cells(line):
    return [c.strip() for c in re.split(r"(?<!\\)\|", line.strip().strip("|"))]


def parse_doc(path):
    """Split one Markdown file into tables and figures, each tagged with its page."""
    doc = os.path.basename(path)[:-3]
    lines = open(path, encoding="utf-8").read().split("\n")
    head = " ".join(lines[:14]).lower()
    bank = "west" if "west bank" in head else "east" if "east bank" in head else ""
    page, tables, figures, pages = None, [], [], {}
    cur, title, image = None, "", None
    for line in lines:
        m = re.match(r"^## Page (\d+)$", line)
        if m:
            page, cur, title = int(m.group(1)), None, ""
            continue
        if page is not None:
            pages.setdefault(page, []).append(line)
        m = re.match(r"^\*\*Table (\d+)(?::\s*(.*?))?\*\*$", line)
        if m:
            cur = {"doc": doc, "bank": bank, "page": page, "table": int(m.group(1)),
                   "title": m.group(2) or "", "rows": [], "snapshot": "", "notes": []}
            tables.append(cur)
            continue
        if line.startswith("|") and cur is not None:
            if not line.startswith("|---"):
                cur["rows"].append(cells(line))
            continue
        if cur is not None and line.startswith("> **Note:**"):
            cur["notes"].append(line)
        m = re.search(r"Table snapshot \(for checking\): !\[[^\]]*\]\(([^)]+)\)", line)
        if m and cur is not None:
            cur["snapshot"] = m.group(1)
            continue
        m = re.match(r"^!\[Figure\]\(([^)]+)\)", line)
        if m:
            image = m.group(1)
            continue
        m = re.match(r"^> \*\*Figure description:\*\*\s*(.*)$", line)
        if m and image:
            fig = re.search(r"-fig(\d+)\.", image)
            figures.append({"doc": doc, "bank": bank, "page": page, "figure": fig.group(1) if fig else "",
                            "image": image, "description": m.group(1)})
            image = None
    return doc, bank, tables, figures, pages


def phase_rows(t):
    """East Bank layout: one project per row, the phase subtotal as the last row."""
    out = []
    for row in t["rows"]:
        first = row[0]
        cost = next((cell_cost(c) for c in reversed(row[1:]) if cell_cost(c) is not None), None)
        m = PHASE_ROW.match(first)
        if m:
            parts = [p.strip() for p in m.group(4).split("<br>")]
            # Rows marked as alternatives are options, not additions, so the phase will not sum.
            alt = (m.group(1) or m.group(3) or "").strip() or (
                "(Alternative)" if re.search(r"\(Alternative", parts[0]) else "")
            out.append({"row_kind": "project", "project_id": m.group(2), "name": parts[0],
                        "scope": " / ".join(parts[1:]), "cost": cost,
                        "needs_review": f"alternative row {alt}: do not add to the other rows" if alt else ""})
        elif re.search(r"subtotal", first, re.I) and cost is not None:
            if first.lower().startswith("(alt"):
                # Subtotal of an alternative; it has no row set of its own to sum.
                out.append({"row_kind": "alt_subtotal", "project_id": "", "name": first, "scope": "", "cost": cost})
                continue
            first = first[re.search(r"Phase \d+ Subtotal|subtotal", first, re.I).start():]
            out.append({"row_kind": "subtotal", "project_id": "", "name": first, "scope": "", "cost": cost})
        elif re.match(r"^(Phase \d+|Total)$", first, re.I) and cost is not None:
            # Program summary table: one line per phase, plus the program total.
            kind = "total" if first.lower() == "total" else "phase_summary"
            out.append({"row_kind": kind, "project_id": "", "name": first,
                        "scope": row[1] + " projects" if len(row) > 2 and row[1].isdigit() else "", "cost": cost})
        elif cost is not None and re.match(r"^Phase \d+ Projects", t["rows"][0][0], re.I):
            run = sum(r["cost"] or 0 for r in out if r["row_kind"] == "project")
            if out and abs(run - cost) < 0.005:
                out.append({"row_kind": "subtotal", "project_id": "", "name": "Subtotal (label lost in the Markdown)",
                            "scope": "", "cost": cost})
                continue
            # A costed row with no ID means the converter split or merged rows; the cost is still a printed value.
            out.append({"row_kind": "project", "project_id": "", "name": first.split("<br>")[0], "scope": "",
                        "cost": cost, "needs_review": "no project ID on this row: rows are split or merged in "
                                                      "the Markdown, so read IDs from the snapshot"})
    return out


def group_rows(t):
    """West Bank layout: improvement groups, either one per row or stacked in a cell with <br>."""
    out = []
    for row in t["rows"]:
        if len(row) < 4:
            continue
        cols = [[p.strip() for p in c.split("<br>") if p.strip()] for c in row]
        flat = [p for c in cols for p in c]
        ids = [p for p in flat if IG_ID.match(p)]
        label = next((p for p in flat if re.search(r"subtotal|total cost", p, re.I)), "")
        costcols = [c for c in cols if any(MONEY.search(p) or p == "TBD" for p in c)]
        if not ids and not label:
            name = next((p for c in cols[1:] for p in c if not MONEY.search(p) and p != "TBD"), "")
            if name and costcols:
                # A named, costed line with no group number, such as a pump station priced "TBD".
                out.append({"row_kind": "project", "project_id": "", "name": name, "costs": [money(c[0]) for c in costcols],
                            "priority": cols[0][0] if cols[0] and cols[0][0].isdigit() else ""})
            continue
        if not ids:
            if not costcols:
                continue
            vals = [money(c[-1]) for c in costcols]
            kind = "subtotal" if "subtotal" in label.lower() else "total"
            out.append({"row_kind": kind, "project_id": "", "name": label, "costs": vals, "priority": ""})
            continue
        names = [p for c in cols[1:] for p in c
                 if not IG_ID.match(p) and not MONEY.search(p) and p != "TBD" and p != label]
        priority = cols[0][0] if cols[0] and cols[0][0].isdigit() else ""
        want = len(ids) + (1 if label else 0)
        aligned = len(names) == len(ids) and all(len(c) == want for c in costcols)
        if not aligned:
            # Pairing IDs with names by position would assign the wrong name; keep the cell whole.
            out.append({"row_kind": "project", "priority": priority, "costs": [None for _ in costcols],
                        "project_id": "; ".join("IG-" + IG_ID.match(p).group(1) for p in ids),
                        "name": "; ".join(names),
                        "needs_review": "stacked cell misaligned, IDs and names not paired: " + " | ".join(row)})
            ids = []
        for i, pid in enumerate(ids):
            out.append({"row_kind": "project", "project_id": "IG-" + IG_ID.match(pid).group(1),
                        "name": names[i] if i < len(names) else "", "priority": priority,
                        "costs": [money(c[i]) if aligned else None for c in costcols],
                        # A stacked cell whose lines do not pair up one-to-one cannot be split safely.
                        "needs_review": "" if aligned else "stacked cell misaligned: " + " | ".join(row)})
        if label:
            out.append({"row_kind": "subtotal", "project_id": "", "name": label, "priority": priority,
                        "costs": [money(c[-1]) for c in costcols],
                        "needs_review": "" if aligned else "stacked cell misaligned"})
    return out


def note_flag(noted, r):
    """A note under a table concerns the rows it names, and every subtotal and total they feed."""
    if not noted:
        return ""
    if r["row_kind"] != "project" or any(
            re.search(rf"(?<![\w-]){re.escape(i)}(?![\w.-])", noted) for i in r["project_id"].split("; ") if i):
        return "printed-value note on this table names this row; read it before citing"
    return ""


def table_records(t):
    text = " ".join(" ".join(r) for r in t["rows"])
    base = {"doc": t["doc"], "bank": t["bank"], "page": t["page"], "table": t["table"],
            "table_title": t["title"] or (t["rows"][0][0] if t["rows"] else ""), "snapshot": t["snapshot"],
            "needs_review": ""}
    noted = " ".join(t["notes"])
    recs = []
    if re.search(r"\bIG[-\s]?\d", text):
        header = next((r for r in t["rows"] if any("year" in c.lower() or "yr" in c.lower() for c in r)), [])
        labels = [c for c in header if "cost" in c.lower()]
        for r in group_rows(t):
            rec = dict(base, scheme="improvement-group", scope="priority " + r["priority"] if r.get("priority") else "")
            rec.update({k: r[k] for k in ("row_kind", "project_id", "name")})
            costs = r["costs"]
            if len(costs) == 2:
                rec["cost_25yr"], rec["cost_100yr"] = costs
            elif len(costs) == 1:
                key = "cost_100yr" if labels and "100" in labels[0] else "cost_25yr" if labels and "25" in labels[0] else "cost"
                rec[key] = costs[0]
            rec["needs_review"] = "; ".join(x for x in (note_flag(noted, r), r.get("needs_review", "")) if x)
            recs.append(rec)
    else:
        for r in phase_rows(t):
            note = "; ".join(x for x in (note_flag(noted, r), r.pop("needs_review", "")) if x)
            recs.append(dict(base, scheme="phase", **r, needs_review=note))
    return recs


def load(mdp):
    files = sorted(f for f in os.listdir(mdp) if f.endswith(".md") and f != "STATUS.md")
    if not files:
        sys.exit(f"no plan Markdown found in {mdp}")
    return [parse_doc(os.path.join(mdp, f)) for f in files]


def fmt(v):
    return "" if v is None else f"{v:.2f}".rstrip("0").rstrip(".") if isinstance(v, float) else v


def cmd_build(a):
    os.makedirs(a.out, exist_ok=True)
    projects, figures = [], []
    for _, _, tables, figs, _ in load(a.mdp):
        for t in tables:
            projects.extend(table_records(t))
        figures.extend(figs)
    for name, fields, rows in (("projects.csv", PROJECT_FIELDS, projects), ("figures.csv", FIGURE_FIELDS, figures)):
        with open(os.path.join(a.out, name), "w", newline="", encoding="utf-8") as fh:
            w = csv.DictWriter(fh, fieldnames=fields, extrasaction="ignore")
            w.writeheader()
            for r in rows:
                w.writerow({k: fmt(r.get(k, "")) for k in fields})
    n = sum(r["row_kind"] == "project" for r in projects)
    flagged = sum(bool(r["needs_review"]) for r in projects)
    print(f"{n} project rows, {len(projects) - n} subtotal/total rows ({flagged} flagged needs_review), "
          f"{len(figures)} figures -> {a.out}")


def cmd_check(a):
    """Printed subtotals and totals must equal the sum of the rows above them."""
    bad = ok = skipped = 0
    for _, _, tables, _, _ in load(a.mdp):
        for t in tables:
            recs = table_records(t)
            where = f"{t['doc']} p{t['page']:02d} table {t['table']}"
            blocked = [r for r in recs if r["row_kind"] == "project"
                       and re.search(r"alternative row|misaligned", r.get("needs_review", ""))]
            if blocked:
                skipped += 1
                print(f"UNCHECKED {where}: {blocked[0]['needs_review'][:60]}")
                continue
            for key in ("cost", "cost_25yr", "cost_100yr"):
                run, grand, subs = 0.0, 0.0, 0
                for r in recs:
                    v = r.get(key)
                    if r["row_kind"] in ("project", "phase_summary"):
                        if v is None:
                            continue
                        run += v
                        grand += v
                        continue
                    if v is None:
                        continue
                    # A total that follows subtotals covers every row; one with no subtotals covers the run.
                    got = grand if r["row_kind"] == "total" else run
                    if r["row_kind"] == "subtotal":
                        subs += 1
                        run = 0.0
                    if got == 0:
                        continue
                    if abs(got - v) < 0.005:
                        ok += 1
                    else:
                        bad += 1
                        print(f"MISMATCH {where} [{key}] {r['name']}: printed {v:,.2f}, rows sum to {got:,.2f} "
                              f"(diff {got - v:+,.2f})")
    print(f"{ok} sums match, {bad} mismatch, {skipped} tables unchecked")
    print("A mismatch is a lead, not a verdict: check the table snapshot and references/known-discrepancies.md.")
    return 1 if bad else 0


def cmd_find(a):
    """Report every place a term is named, labelled by the kind of evidence it gives."""
    pat = re.compile("|".join(re.escape(t) for t in a.terms), re.I)
    hits = 0
    for doc, bank, tables, figs, pages in load(a.mdp):
        for t in tables:
            for r in table_records(t):
                if r["row_kind"] == "project" and pat.search(f"{r['name']} {r.get('scope', '')}"):
                    cost = " / ".join(f"${v:,.0f}" for v in (r.get("cost"), r.get("cost_25yr"), r.get("cost_100yr")) if v is not None)
                    flag = "  [needs_review]" if r["needs_review"] else ""
                    print(f"PROJECT  {doc} p{t['page']:02d} table {t['table']}  {r['project_id']} {r['name']}  {cost}{flag}")
                    if r["needs_review"]:
                        print(f"         review: {r['needs_review'][:160]}")
                    if "printed-value note" in r["needs_review"]:
                        for note in t["notes"]:
                            print(f"         {note[2:]}")
                    hits += 1
        for f in figs:
            if pat.search(f["description"]):
                print(f"FIGURE   {doc} p{f['page']:02d} fig {f['figure']}  {f['image']}\n         {f['description'][:300]}")
                hits += 1
        for page, lines in sorted(pages.items()):
            for line in lines:
                if line.startswith(("|", ">", "!", "Table snapshot")) or not pat.search(line):
                    continue
                m = pat.search(line)
                s = max(0, m.start() - 110)
                print(f"TEXT     {doc} p{page:02d}  ...{line[s:m.end() + 130].strip()}...")
                hits += 1
    print(f"{hits} hits for {a.terms}. PROJECT = named in a cost table; "
          "FIGURE = labelled on a map; TEXT = narrative only.")
    return 0 if hits else 1


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)
    for name, fn in (("build", cmd_build), ("check", cmd_check), ("find", cmd_find)):
        s = sub.add_parser(name)
        s.add_argument("--mdp", default=DEFAULT_MDP)
        s.set_defaults(fn=fn)
        if name == "build":
            s.add_argument("--out", default=DEFAULT_OUT)
        if name == "find":
            s.add_argument("terms", nargs="+")
    a = p.parse_args()
    if not os.path.isdir(a.mdp):
        sys.exit(f"corpus not found at {a.mdp!r}: pass --mdp DIR")
    sys.exit(a.fn(a) or 0)


if __name__ == "__main__":
    main()
