#!/usr/bin/env python3
"""Find a St. Charles Parish budget year's records on Legistar and search budget documents by page.

  budget.py cycle --year YYYY [--dir DIR] [--match REGEX]
  budget.py millage --tax-year YYYY [--line REGEX] [--dir DIR]
  budget.py search "<regex>" --dir DIR [--context N]

Downloads go in the user's project folder, never in the plugin. Standard library plus poppler.
Exit codes: 0 found, 1 the source answered and nothing matched, 2 the source could not be read.
"""
import argparse, re, subprocess, sys, tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scp-meeting-record" / "scripts"))
import meeting_record as mr  # noqa: E402

# The API's MatterAttachmentHyperlink points at a /snohomish/ path that returns 404.
ATTACH = "https://stcharlesgov.legistar1.com/stcharlesgov/attachments/"
GATEWAY = "https://stcharlesgov.legistar.com/gateway.aspx?M=L&ID={}"
TITLE_TERMS = ["Consolidated Operating and Capital Budget", "levying and imposing", "Capital Program Budget",
               "Capital Improvements Budget"]
ROLES = ["adoption", "amendment", "millage levy", "capital program"]
SCAN_WORDS_PER_PAGE = 20  # below this a PDF is treated as a scan with no usable text layer


def attachment_url(a):
    return ATTACH + a["MatterAttachmentFileName"] if a.get("MatterAttachmentFileName") else a["MatterAttachmentHyperlink"]


def role(matter, year):
    """How a matter bears on budget year `year`, or None. A levy on one tax roll funds the next budget year."""
    title = mr.squash(matter.get("MatterTitle"))
    intro = (matter.get("MatterIntroDate") or "")[:4]
    if re.search(rf"appropriation of Funds.*Fiscal Year {year}\b", title, re.I):
        return "adoption"
    if re.search(rf"amend the {year} Consolidated Operating and Capital Budget", title, re.I):
        return "amendment"
    if re.search(r"levying and imposing", title, re.I) and "in excess of" not in title and intro == str(year - 1):
        return "millage levy"
    span = re.search(r"Capital (?:Program|Improvements) Budget.*?fiscal year (\d{4}) through (\d{4})", title, re.I)
    if span and int(span.group(1)) <= year <= int(span.group(2)):
        return "capital program"
    return None


def budget_matters():
    clause = " or ".join(f"substringof('{t}',MatterTitle)" for t in TITLE_TERMS)
    return mr.legistar("/matters", **{"$filter": clause, "$orderby": "MatterIntroDate desc"})


def read_source(call):
    """Exit 2 on a network failure, so a failed lookup is never reported as an empty result."""
    try:
        return call()
    except Exception as e:
        sys.exit(print(f"NOT CHECKED: Legistar could not be read ({e}).", file=sys.stderr) or 2)


def cmd_cycle(a):
    if a.dir:
        mr.check_output(a.dir)
    rows = [(role(m, a.year), m) for m in read_source(budget_matters)]
    rows = [(r, m) for r, m in rows if r]
    if not rows:
        print(f"No matter titles found for budget year {a.year}. This searches titles only.")
        return 1
    for name in ROLES:
        group = sorted((m for r, m in rows if r == name), key=lambda m: m.get("MatterIntroDate") or "")
        print(f"## {name}: {len(group)}")
        for m in group:
            print(f"- {m['MatterFile']} {(m.get('MatterIntroDate') or '')[:10]} {m['MatterStatusName']}, "
                  f"no. {m.get('MatterEnactmentNumber') or 'none'}: {mr.squash(m['MatterTitle'])[:170]}\n"
                  f"  {GATEWAY.format(m['MatterId'])}")
            for att in read_source(lambda: mr.legistar(f"/matters/{m['MatterId']}/attachments")):
                show(att, m, a)
        print()
    print("Titles only: a budget action under another title won't appear. Enacted status can be a placeholder, "
          "so check the enactment number.")
    return 0


def show(att, matter, a):
    name, url = mr.squash(att["MatterAttachmentName"]), attachment_url(att)
    if not a.dir or (a.match and not re.search(a.match, name, re.I)):
        print(f"    {name}: {url}")
    elif not url.lower().endswith(".pdf"):
        print(f"    {name}: {url} (not a PDF, not saved)")
    else:
        pdf, words = mr.save_document(f"{matter['MatterFile']}_{name}", url, a.dir)
        print(f"    {name}: {pdf} ({scan_note(pdf, words)})")


def scan_note(pdf, words):
    result = subprocess.run(["pdfinfo", str(pdf)], capture_output=True, text=True).stdout
    pages = re.search(r"Pages:\s+(\d+)", result)
    count = int(pages.group(1)) if pages else 1
    return f"{count} pp., {words} words" + (", scan: run OCR before searching" if words < count * SCAN_WORDS_PER_PAGE else "")


def parse_schedule(text):
    """(years, {line label: {year: rate}}) from the Finance schedule's first table.

    Cells are matched to header columns by their right edge, because a line started in a later
    year leaves its early cells blank and a line's change-from-prior-year column has no year.
    """
    # Only the first page holding the header counts: later pages are revenue tables with other columns.
    page = next((x for x in text.split("\f") if re.search(r"(?:\b20\d\d\b.*){5}", x)), None)
    if page is None:
        return [], {}
    lines = page.splitlines()
    head = next(i for i, x in enumerate(lines) if len(re.findall(r"\b20\d\d\b", x)) >= 5)
    columns = [(int(m.group()), m.end()) for m in re.finditer(r"\b20\d\d\b", lines[head])]
    while len(columns) > 1 and columns[-1][0] <= columns[-2][0]:
        columns.pop()
    last_edge = columns[-1][1]
    rows = {}
    for line in lines[head + 1:]:
        cells = list(re.finditer(r"\(?-?\d+\.\d+\)?", line))
        if not cells:
            continue
        label = mr.squash(line[:cells[0].start()])
        row = {}
        for cell in cells:
            if cell.end() > last_edge + 3:
                continue
            year = min(columns, key=lambda c: abs(c[1] - cell.end()))[0]
            row[year] = cell.group()
        key, n = label, 2
        # The schedule prints two lines both named "Council on Aging".
        while key in rows:
            key, n = f"{label} ({n})", n + 1
        rows[key] = row
    return [c[0] for c in columns], rows


def cmd_millage(a):
    if a.dir:
        mr.check_output(a.dir)
    levies = [m for m in read_source(budget_matters) if role(m, a.tax_year + 1) == "millage levy"]
    if not levies:
        print(f"No levy ordinance title found for tax year {a.tax_year}.")
        return 1
    m = levies[0]
    atts = read_source(lambda: mr.legistar(f"/matters/{m['MatterId']}/attachments"))
    schedule = next((x for x in atts if re.search(r"ADVAL", x["MatterAttachmentName"], re.I)), None)
    print(f"Levy: {m['MatterFile']}, no. {m.get('MatterEnactmentNumber') or 'none'}, {GATEWAY.format(m['MatterId'])}")
    if not schedule:
        print("No attachment named ADVAL. Read the matter's files:")
        for att in atts:
            print(f"  {mr.squash(att['MatterAttachmentName'])}: {attachment_url(att)}")
        return 1
    url = attachment_url(schedule)
    with tempfile.TemporaryDirectory() as tmp:
        try:
            pdf, _ = mr.save_document(f"{m['MatterFile']}_{schedule['MatterAttachmentName']}", url, a.dir or tmp)
        except Exception as e:
            print(f"NOT CHECKED: the schedule could not be read ({e}): {url}", file=sys.stderr)
            return 2
        sidecar = pdf.with_suffix(".txt")
        text = sidecar.read_text(errors="ignore") if sidecar.exists() else ""
    years, rows = parse_schedule(text)
    print(f"Schedule: {mr.squash(schedule['MatterAttachmentName'])}: {url}")
    if a.tax_year not in years:
        print(f"Couldn't read a {a.tax_year} column (columns read: {years}). Read the file by hand.")
        return 1
    show_years = [y for y in years if y >= a.tax_year - 2 and y <= a.tax_year]
    print(f"Tax roll {a.tax_year}, collected in {a.tax_year + 1}. Council-levied lines only; other bodies set their own.\n")
    print(f"{'Line':<40}" + "".join(f"{y:>8}" for y in show_years))
    found = 0
    for label, row in rows.items():
        if a.line and not re.search(a.line, label, re.I):
            continue
        found += 1
        print(f"{label[:39]:<40}" + "".join(f"{row.get(y, ''):>8}" for y in show_years))
    if not found:
        print(f"No line matches {a.line!r}. Lines: {'; '.join(rows)}")
        return 1
    print("\nRead from the PDF's text layer. Check a figure on the page image before quoting it.")
    return 0


def search_pages(text, pattern, context=0):
    """Yield (pdf page, [lines]) for each match. pdftotext separates pages with form feeds."""
    for number, page in enumerate(text.split("\f"), 1):
        lines = page.splitlines()
        last = -1
        for i, line in enumerate(lines):
            if pattern.search(line) and i > last:
                last = i + context
                yield number, [mr.squash(x) for x in lines[max(0, i - context):i + context + 1] if x.strip()]


def cmd_search(a):
    folder = Path(a.dir)
    pdfs = sorted(folder.glob("*.pdf"))
    if not pdfs:
        print(f"NOT CHECKED: no PDFs in {folder}.", file=sys.stderr)
        return 2
    try:
        pattern = re.compile(a.pattern, re.I)
    except re.error:
        pattern = re.compile(re.escape(a.pattern), re.I)
    hits, skipped = 0, []
    for pdf in pdfs:
        txt = pdf.with_suffix(".txt")
        if not txt.exists():
            subprocess.run(["pdftotext", "-layout", str(pdf), str(txt)], capture_output=True)
        text = txt.read_text(errors="ignore") if txt.exists() else ""
        pages = text.count("\f") or 1
        if len(text.split()) < pages * SCAN_WORDS_PER_PAGE:
            skipped.append(pdf.name)
            continue
        for page, lines in search_pages(text, pattern, a.context):
            hits += 1
            print(f"{pdf.name}, PDF p. {page}:")
            for line in lines:
                print(f"    {line[:190]}")
    print(f"\n{hits} match(es) in {len(pdfs) - len(skipped)} PDF(s).")
    if skipped:
        print(f"NOT SEARCHED, little or no text layer: {', '.join(skipped)}. Run OCR, then search again.")
    return 0 if hits else 1


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("cycle"); s.add_argument("--year", type=int, required=True); s.add_argument("--dir"); s.add_argument("--match")
    s.set_defaults(fn=cmd_cycle)
    s = sub.add_parser("millage"); s.add_argument("--tax-year", type=int, required=True); s.add_argument("--line"); s.add_argument("--dir")
    s.set_defaults(fn=cmd_millage)
    s = sub.add_parser("search"); s.add_argument("pattern"); s.add_argument("--dir", required=True); s.add_argument("--context", type=int, default=0)
    s.set_defaults(fn=cmd_search)
    a = p.parse_args()
    sys.exit(a.fn(a))


if __name__ == "__main__":
    main()
