#!/usr/bin/env python3
"""After a Louisiana public records request is sent: statutory dates and a production index.

  prr_after.py dates --sent 2026-11-03 [--received 2026-11-05] [--today 2026-11-17] [--holiday YYYY-MM-DD]
  prr_after.py index <download-folder> [--out <folder>] [--force]

`dates` counts the R.S. 44:33(B) three-day and 44:32(D) / 44:35(A) five-day periods, skipping
Saturdays, Sundays and the R.S. 1:55 legal holidays. `index` writes manifest.csv and an INDEX.md
skeleton for a folder of produced files: size, SHA-256, pages, which pages lack a text layer,
exemption or redaction markers, exact duplicates and text contained in another file. What each
file is, and which request item it answers, is left to the reader.

Writes go in the user's project folder, never in the plugin. Standard library plus poppler.
Exit codes: 0 done, 1 nothing to report (an empty folder), 2 could not check.
"""
import argparse, csv, datetime as dt, hashlib, importlib.util, re, shutil, subprocess, sys
from pathlib import Path

PLUGIN_ROOT = Path(__file__).resolve().parents[3]
sys.dont_write_bytecode = True  # the plugin folder may be a read-only snapshot

# The holiday table lives with the Open Meetings notice counter, so both skills count the same days.
_GOV = Path(__file__).resolve().parents[2] / "scp-government" / "scripts" / "government.py"
_spec = importlib.util.spec_from_file_location("scp_government", _GOV)
_gov = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_gov)


# ---------------------------------------------------------------- dates

def holidays_for(start, extra=()):
    """Legal holidays for the start year and the next, since a forward count can cross New Year."""
    days, conditional = {}, {}
    for year in (start.year, start.year + 1):
        d, c = _gov.legal_holidays(year)
        days.update(d)
        conditional.update(c)
    days.update({x: "given with --holiday" for x in extra})
    return days, conditional


def is_business_day(day, holidays):
    return day.weekday() < 5 and day not in holidays


def add_business_days(start, n, holidays):
    """Day 1 is the first business day after `start`; returns day n and the holidays skipped."""
    day, counted, skipped = start, 0, []
    while counted < n:
        day += dt.timedelta(days=1)
        if is_business_day(day, holidays):
            counted += 1
        elif day.weekday() < 5:
            skipped.append(day)
    return day, skipped


def business_days_between(start, end, holidays):
    """Business days after `start` up to and including `end`."""
    n, day = 0, start
    while day < end:
        day += dt.timedelta(days=1)
        if is_business_day(day, holidays):
            n += 1
    return n


def fmt(day):
    return day.strftime("%a %Y-%m-%d")


PERIODS = [
    # (days, label, which start date the statute counts from)
    (3, "R.S. 44:33(B)(1): a record in active use, certificate fixing a day and hour within (start date is this skill's reading)", "request"),
    (5, "R.S. 44:32(D): written determination when the custodian questions whether a record is public, within", "receipt"),
    (5, "R.S. 44:35(A): no written determination or time estimate by then, and the requester may sue; counted from the request,", "request"),
]


def cmd_dates(a):
    starts = {"request": [("sent", a.sent)], "receipt": [("received", a.received or a.sent)]}
    if a.received and a.received != a.sent:
        starts["request"].append(("received", a.received))  # "date of his request" is not defined for mail
    holidays, conditional = holidays_for(min(a.sent, a.received or a.sent), a.holiday)
    print("Day 1 is the first business day after the start date. Saturdays, Sundays and R.S. 1:55 legal "
          "holidays are skipped. The counting convention is this skill's; how a court counts isn't established.")
    if not a.received:
        print("No --received date: receipt is assumed to be the send date (true for the parish portal and "
              "email; not for mail).")
    for days, label, basis in PERIODS:
        print(f"\n{label} {days} days")
        for name, start in starts[basis]:
            end, skipped = add_business_days(start, days, holidays)
            line = f"   from {name} {fmt(start)}: day {days} is {fmt(end)}"
            if skipped:
                line += "  (skipped " + ", ".join(f"{d} {holidays[d]}" for d in skipped) + ")"
            print(line)
            maybe = {d: n for d, n in conditional.items() if start < d <= end and d.weekday() < 5}
            if maybe:
                alt, _ = add_business_days(start, days, {**holidays, **maybe})
                print(f"      if {', '.join(maybe.values())} counts: {fmt(alt)}")
    if a.today:
        print()
        for name, start in starts["request"]:
            n = business_days_between(start, a.today, holidays)
            print(f"As of {fmt(a.today)}: {n} business day(s) since {name} {fmt(start)}.")
    print("\nAn acknowledgment, or \"research in progress\" with no date, is neither a written determination "
          "nor an estimate of time under 44:35(A). Whether an estimate is reasonable is a question for a court.")
    return 0


# ---------------------------------------------------------------- index

MARKERS = [
    ("exemption sheet", re.compile(r"public\s+records\s+exemptions", re.I)),
    ("Privacy Information", re.compile(r"privacy\s+information", re.I)),
    ("Client Privilege", re.compile(r"client\s+privilege", re.I)),
    ("attorney-client", re.compile(r"attorney[\s-]+client", re.I)),
    ("work product", re.compile(r"work\s+product", re.I)),
    ("redacted", re.compile(r"\bredact(ed|ion)\b", re.I)),
    ("R.S. 44 citation", re.compile(r"\b(?:R\.?\s*S\.?|La\.?\s*R\.?\s*S\.?)\s*44\s*:\s*\d", re.I)),
]
MESSAGE_SUFFIXES = {".msg", ".eml"}
EMPTY_PAGE_CHARS = 20  # fewer non-space characters than this and the page is treated as image-only


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def pdf_pages_text(path):
    """(page count, [text per page]) from poppler. Raises RuntimeError when poppler can't read it."""
    info = subprocess.run(["pdfinfo", str(path)], capture_output=True, text=True)
    m = re.search(r"^Pages:\s+(\d+)", info.stdout, re.M)
    if info.returncode or not m:
        raise RuntimeError((info.stderr or "pdfinfo gave no page count").strip().splitlines()[-1])
    pages = int(m.group(1))
    out = subprocess.run(["pdftotext", "-layout", str(path), "-"], capture_output=True, text=True,
                         errors="replace")
    if out.returncode:
        raise RuntimeError((out.stderr or "pdftotext failed").strip().splitlines()[-1])
    texts = out.stdout.split("\f")
    texts = (texts + [""] * pages)[:pages]
    return pages, texts


def page_ranges(nums):
    """[1,2,3,7] -> '1-3, 7'"""
    out, run = [], []
    for n in nums:
        if run and n == run[-1] + 1:
            run.append(n)
        else:
            if run:
                out.append(f"{run[0]}-{run[-1]}" if len(run) > 1 else str(run[0]))
            run = [n]
    if run:
        out.append(f"{run[0]}-{run[-1]}" if len(run) > 1 else str(run[0]))
    return ", ".join(out)


def text_layer_label(pages, empty):
    if not pages:
        return ""
    if not empty:
        return "yes"
    if len(empty) == pages:
        return f"no ({pages} of {pages} pp)"
    return f"partial (no text on p. {page_ranges(empty)})"


def shingles(text, k=5):
    words = re.findall(r"[a-z0-9]+", text.lower())
    return {" ".join(words[i:i + k]) for i in range(max(len(words) - k + 1, 0))}


def containment(rows, threshold=0.9, min_shingles=50):
    """Pairs where most of one file's text appears in another, e.g. the same minutes with a stamp added."""
    found, owners = [], {}
    for i, r in enumerate(rows):
        for sh in r["_shingles"]:
            owners.setdefault(sh, set()).add(i)
    pairs = set()
    for idx in owners.values():
        if 1 < len(idx) <= 50:  # a run shared by dozens of files is boilerplate (signatures, disclaimers)
            pairs.update((x, y) for x in idx for y in idx if x < y)
    for i, j in sorted(pairs):
        a, b = rows[i], rows[j]
        sa, sb = a["_shingles"], b["_shingles"]
        if a["sha256"] == b["sha256"] or min(len(sa), len(sb)) < min_shingles:
            continue
        small, big = (a, b) if len(sa) <= len(sb) else (b, a)
        share = len(small["_shingles"] & big["_shingles"]) / len(small["_shingles"])
        if share >= threshold:
            found.append((small["file"], big["file"], share))
    return found


def ocr_siblings(pdf):
    """Text files made from a PDF by OCR, named <stem>.txt or <stem>.<reader>.txt beside it."""
    return sorted(q for q in pdf.parent.glob(glob_escape(pdf.stem) + "*.txt")
                  if q.name == pdf.stem + ".txt" or (q.name.startswith(pdf.stem + ".") and q.name.count(".") >= 2))


def glob_escape(s):
    return re.sub(r"([*?\[])", r"[\1]", s)


def scan(folder):
    files = sorted(p for p in folder.rglob("*") if p.is_file() and not p.name.startswith(".")
                   and p.name not in ("manifest.csv", "INDEX.md"))
    derived = {q for p in files if p.suffix.lower() == ".pdf" for q in ocr_siblings(p)}
    files = [p for p in files if p not in derived]
    rows, problems = [], []
    for p in files:
        row = {"file": str(p.relative_to(folder)), "bytes": p.stat().st_size, "sha256": sha256(p),
               "type": p.suffix.lower().lstrip(".") or "none", "pages": "", "chars": "", "text_layer": "",
               "markers": [], "duplicate_of": "", "_shingles": set()}
        if "redacted" in p.name.lower():
            row["markers"].append("'Redacted' in file name")
        if p.suffix.lower() == ".pdf":
            try:
                pages, texts = pdf_pages_text(p)
            except RuntimeError as e:
                problems.append(f"{row['file']}: {e}")
                row["text_layer"] = "not read"
            else:
                empty = [i + 1 for i, t in enumerate(texts) if len(re.sub(r"\s", "", t)) < EMPTY_PAGE_CHARS]
                full = "\n".join(texts)
                row.update(pages=pages, chars=len(re.sub(r"\s", "", full)),
                           text_layer=text_layer_label(pages, empty), _shingles=shingles(full))
                for label, rx in MARKERS:
                    hit = [i + 1 for i, t in enumerate(texts) if rx.search(t)]
                    if hit:
                        row["markers"].append(f"{label} (p. {page_ranges(hit)})")
                if empty:
                    # Image-only pages hide exactly the sheets that matter, so read an OCR copy if one exists.
                    for sib in ocr_siblings(p):
                        txt = sib.read_text(errors="replace")
                        for label, rx in MARKERS:
                            if rx.search(txt) and not any(m.startswith(label) for m in row["markers"]):
                                row["markers"].append(f"{label} (in {sib.name})")
        elif p.suffix.lower() in MESSAGE_SUFFIXES:
            row["markers"].append("native message file: headers may show sender, recipients and dates")
        rows.append(row)
    first = {}
    for row in rows:
        if row["sha256"] in first:
            row["duplicate_of"] = first[row["sha256"]]
        else:
            first[row["sha256"]] = row["file"]
    return rows, problems


FIELDS = ["file", "bytes", "sha256", "type", "pages", "chars", "text_layer", "markers", "duplicate_of"]


def write_manifest(rows, path):
    with open(path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS, extrasaction="ignore")
        w.writeheader()
        for r in rows:
            w.writerow({**r, "markers": "; ".join(r["markers"])})


def md_cell(s):
    return str(s).replace("|", "\\|")


def index_md(folder, rows, contained, problems):
    today = dt.date.today().isoformat()
    lines = [f"# Production index: {folder.name}", "",
             f"Written {today} by `prr_after.py index` from `{folder.name}`: {len(rows)} file(s). "
             "Size, hash, pages, text layer and markers are from the files; the description and item columns "
             "are blank until someone reads each file. Keep this index next to the files and out of any public "
             "repository: productions can carry other people's details.", "",
             "Request: [custodian, request number, date sent]. Delivery: [the email or letter that delivered "
             "these files, and where it is saved]. Cover letter or exemption sheet: [where].", "",
             "| # | File | Size | Pages | Text layer | Markers | Duplicate of | What it is | Request item |",
             "|---|---|---|---|---|---|---|---|---|"]
    for i, r in enumerate(rows, 1):
        size = f"{r['bytes'] / 1e6:.2f} MB" if r["bytes"] >= 10_000 else f"{r['bytes']} B"
        lines.append(f"| {i} | {md_cell(r['file'])} | {size} | {r['pages']} | {r['text_layer']} | "
                     f"{md_cell('; '.join(r['markers']))} | {md_cell(r['duplicate_of'])} |  |  |")
    no_text = [r["file"] for r in rows if r["text_layer"].startswith(("no", "partial"))]
    lines += ["", "## Found by the script", ""]
    lines.append("- Needs OCR before searching: " + (", ".join(no_text) if no_text else "none") + ".")
    dups = [r for r in rows if r["duplicate_of"]]
    lines.append("- Byte-identical copies: " + (", ".join(f"{r['file']} = {r['duplicate_of']}" for r in dups)
                                                 if dups else "none") + ".")
    if len(contained) > 200:
        lines.append(f"- {len(contained)} containment pairs; the first 200 are listed.")
        contained = contained[:200]
    if contained:
        lines.append("- Text largely contained in another file (compare before treating as distinct; a stamp or "
                     "added pages can be the only difference):")
        lines += [f"  - {s} in {b} ({share:.0%} of its five-word runs)" for s, b, share in contained]
    marked = [r for r in rows if any(not m.startswith("native message") for m in r["markers"])]
    lines.append("- Files with exemption or redaction markers: " +
                 (", ".join(r["file"] for r in marked) if marked else "none") +
                 ". A marker found by text search is a lead. Image-only pages are searched only through an OCR copy "
                 "saved beside the PDF as <name>.txt.")
    if problems:
        lines.append("- Not read: " + "; ".join(problems) + ".")
    lines += ["", "## Against the request", "",
              "One row per numbered item of the request as sent. Status is one of: produced; partly produced; "
              "produced under a split request number; withheld, basis cited; withheld, no basis cited; "
              "certified not in custody (R.S. 44:34); said not to exist; nothing produced and nothing said; "
              "still in progress.", "",
              "| Item | Asked for | Status | Where (file, page) | What shows a missing record exists |",
              "|---|---|---|---|---|", "|  |  |  |  |  |", "",
              "Produced but not asked for: [files].", ""]
    return "\n".join(lines)


def cmd_index(a):
    folder = a.folder.expanduser().resolve()
    out = (a.out.expanduser().resolve() if a.out else folder)
    if not folder.is_dir():
        print(f"Not a folder: {folder}", file=sys.stderr)
        return 2
    if out.is_relative_to(PLUGIN_ROOT):
        print("Refusing to write inside the plugin folder; give --out in the user's project folder.",
              file=sys.stderr)
        return 2
    if not (shutil.which("pdfinfo") and shutil.which("pdftotext")):
        print("poppler (pdfinfo, pdftotext) is not installed, so pages and text layers can't be read. "
              "On macOS: brew install poppler.", file=sys.stderr)
        return 2
    targets = [out / "manifest.csv", out / "INDEX.md"]
    existing = [t for t in targets if t.exists()]
    if existing and not a.force:
        print("Already present, not overwritten (use --out elsewhere, or --force): " +
              ", ".join(str(t) for t in existing), file=sys.stderr)
        return 2
    rows, problems = scan(folder)
    if not rows:
        print(f"No files in {folder}.")
        return 1
    contained = containment(rows)
    out.mkdir(parents=True, exist_ok=True)
    write_manifest(rows, targets[0])
    targets[1].write_text(index_md(folder, rows, contained, problems))
    print(f"{len(rows)} file(s) indexed. Wrote {targets[0]} and {targets[1]}.")
    for r in rows:
        flags = [x for x in (r["text_layer"] if r["text_layer"] not in ("", "yes") else "",
                             "; ".join(r["markers"]), f"duplicate of {r['duplicate_of']}" if r["duplicate_of"] else "")
                 if x]
        print(f"  {r['file']}  {r['pages'] or '-'} pp  " + ("  ".join(flags) if flags else ""))
    for s, b, share in contained[:20]:
        print(f"  text of {s} is {share:.0%} contained in {b}")
    if problems:
        print("Not read:\n  " + "\n  ".join(problems), file=sys.stderr)
        return 2
    return 0


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = p.add_subparsers(dest="cmd", required=True)
    d = sub.add_parser("dates", help="statutory response dates")
    d.add_argument("--sent", required=True, type=dt.date.fromisoformat,
                   help="date the request was submitted, emailed, mailed or handed in (YYYY-MM-DD)")
    d.add_argument("--received", type=dt.date.fromisoformat,
                   help="date the custodian received it, e.g. from a return receipt (YYYY-MM-DD)")
    d.add_argument("--today", type=dt.date.fromisoformat, help="show business days elapsed as of this date")
    d.add_argument("--holiday", action="append", default=[], type=dt.date.fromisoformat,
                   help="another legal holiday to skip, YYYY-MM-DD (repeatable)")
    i = sub.add_parser("index", help="manifest and index skeleton for a folder of produced files")
    i.add_argument("folder", type=Path)
    i.add_argument("--out", type=Path, help="where to write manifest.csv and INDEX.md (default: the folder)")
    i.add_argument("--force", action="store_true", help="overwrite an existing manifest.csv or INDEX.md")
    a = p.parse_args(argv)
    return cmd_dates(a) if a.cmd == "dates" else cmd_index(a)


if __name__ == "__main__":
    sys.exit(main())
