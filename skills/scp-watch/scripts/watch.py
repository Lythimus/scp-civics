#!/usr/bin/env python3
"""Standing search of the Herald-Guide legal notices and Legistar's Parish Council matters.

  watch.py add --dir DIR --term "plain text" [--term ...] [--since YYYY-MM-DD]
  watch.py run --dir DIR [--through YYYY-MM-DD] [--no-paper] [--no-legistar]

DIR holds the watch: watch.json (terms and what has been seen), the issue PDFs and their
OCR, and reports/. It belongs in the user's project folder, never in the plugin.

Terms are plain text, not regexes, because the Legistar filter only takes substrings.
Stdlib plus poppler and tesseract. OCR takes minutes per issue, so run `run` in the
background on a first pass.
"""
import argparse, contextlib, datetime as dt, difflib, glob, json, os, re, shutil, subprocess, sys, time
import urllib.parse, urllib.request
from pathlib import Path

PLUGIN_ROOT = Path(__file__).resolve().parents[3]
sys.dont_write_bytecode = True  # the plugin folder may be a read-only snapshot
sys.path.insert(0, str(PLUGIN_ROOT / "skills" / "scp-land-use-process" / "scripts"))
import hg_legals  # noqa: E402

API = "https://webapi.legistar.com/v1/stcharlesgov/matters"
# The API's MatterId isn't the ID LegislationDetail.aspx takes, so link through the gateway.
DETAIL = "https://stcharlesgov.legistar.com/gateway.aspx?M=L&ID={id}"
PAGE = 1000
LOOKBACK_DAYS = 42  # a notice's first run can come three weeks or more before its hearing
MERGE_GAP = 300  # term hits this close on a page are read as one notice
CONTEXT = 150
PUBLISH_SPAN = 2500  # a notice's "PUBLISH:" line follows its text within about this many characters
# Reruns of a notice are the same typesetting and OCR almost identically. The same ordinance in a
# different document (hearing notice, then minutes) scored up to 0.89 and should stay separate. Set
# high because a missed repeat only shows as new, while a false one hides a new notice.
REPEAT_RATIO = 0.95
THIN_OCR = 200  # fewer characters than this means the search saw almost nothing in the issue
MATTER_FIELDS = ("MatterStatusName", "MatterAgendaDate", "MatterPassedDate", "MatterEnactmentNumber", "MatterTitle")


def state_path(d):
    return Path(d) / "watch.json"


def load_state(d):
    p = state_path(d)
    if not p.exists():
        sys.exit(f"No watch at {d}. Start one with: watch.py add --dir {d} --term ...")
    return json.loads(p.read_text())


def save_state(d, state):
    # Written last and atomically, so a run that dies early reports its hits again next time.
    p = state_path(d)
    tmp = p.with_suffix(".tmp")
    tmp.write_text(json.dumps(state, indent=1))
    tmp.replace(p)


def check_dir(d):
    if Path(d).resolve().is_relative_to(PLUGIN_ROOT):
        sys.exit(f"{d} is inside the plugin. A watch holds case terms and goes in the user's project folder.")


def compile_terms(terms):
    return {t: re.compile(r"\s+".join(map(re.escape, t.split())), re.I) for t in terms}


def squash(text):
    return re.sub(r"\s+", " ", text).strip()


def find_blocks(text, regexes):
    """Term hits on one OCR page, merged into blocks that each stand for one notice.

    Matches across line breaks, since OCR wraps a phrase wherever the column ends.
    """
    spans = sorted((m.start(), m.end(), term) for term, rx in regexes.items() for m in rx.finditer(text))
    blocks = []
    for start, end, term in spans:
        if blocks and start - blocks[-1]["end"] <= MERGE_GAP:
            blocks[-1]["end"] = max(end, blocks[-1]["end"])
            blocks[-1]["hits"].append((term, start))
        else:
            blocks.append({"start": start, "end": end, "hits": [(term, start)]})
    for b in blocks:
        b["snippet"] = squash(text[max(0, b["start"] - CONTEXT):b["end"] + CONTEXT])
        after = text[b["end"]:b["end"] + PUBLISH_SPAN]
        m = re.search(r"\bPUBLISH\s*[:;.]\s*([^\n]*(?:\n[^\n]*)?)", after)
        b["publish"] = squash(m.group(1)) if m else ""
    return blocks


def pages(txt):
    """Split an OCR file written by hg_legals into (page number, text) pairs."""
    parts = re.split(r"^=== PAGE (\d+)[^\n]*\n", Path(txt).read_text(errors="replace"), flags=re.M)
    return [(int(parts[i]), parts[i + 1]) for i in range(1, len(parts) - 1, 2)]


def match_notice(notices, snippet, issue):
    best, best_ratio = None, REPEAT_RATIO
    for n in notices:
        if issue in n["issues"]:  # a notice runs once per issue, so a match here is a different one
            continue
        r = difflib.SequenceMatcher(None, n["text"].lower(), snippet.lower(), autojunk=False).ratio()
        if r >= best_ratio:
            best, best_ratio = n, r
    return best


def scan_paper(d, since, through, state, regexes):
    """Fetch and OCR the window, then return what the search found and what it couldn't check."""
    a, b = dt.date.fromisoformat(since), dt.date.fromisoformat(through)
    with contextlib.redirect_stdout(sys.stderr):
        hg_legals.fetch(argparse.Namespace(dir=str(d), date_from=since, date_to=through))
    gaps = []
    if shutil.which("pdftoppm") and shutil.which("tesseract"):
        try:
            with contextlib.redirect_stdout(sys.stderr):
                hg_legals.ocr(argparse.Namespace(dir=str(d), dpi=200))
        except subprocess.CalledProcessError as exc:
            gaps.append(f"OCR stopped: {exc}. Issues after that point weren't read")
    else:
        gaps.append("pdftoppm or tesseract isn't on PATH, so no new issue was OCRed")

    seen, new, read, missing = set(state["seen"]), [], [], []
    for day in hg_legals.thursdays(a, b):
        stem = f"HGLegals_{day:%Y%m%d}"
        txt = Path(d) / "ocr" / f"{stem}.txt"
        if not (Path(d) / f"{stem}.pdf").exists():
            missing.append(day.isoformat())
            continue
        if not txt.exists() or not txt.stat().st_size:
            gaps.append(f"{day}: downloaded but not OCRed")
            continue
        read.append(day.isoformat())
        doc = pages(txt)
        if sum(len(t) for _, t in doc) < THIN_OCR:
            gaps.append(f"{day}: OCR returned almost no text, so this issue wasn't really searched")
        for page, text in doc:
            for block in find_blocks(text, regexes):
                ids = [f"{day}|{page}|{term}|{pos}" for term, pos in block["hits"]]
                if seen.issuperset(ids):
                    continue
                seen.update(ids)
                prior = match_notice(state["notices"], block["snippet"], day.isoformat())
                entry = {"issue": day.isoformat(), "page": page, "terms": sorted({t for t, _ in block["hits"]}),
                         "snippet": block["snippet"], "publish": block["publish"]}
                if prior:
                    entry["first"] = prior["issues"][0]
                    prior["issues"] = sorted(prior["issues"] + [entry["issue"]])
                    entry["issues"] = prior["issues"]
                else:
                    state["notices"].append({"text": block["snippet"], "issues": [entry["issue"]]})
                    entry["issues"] = [entry["issue"]]
                new.append(entry)
    state["seen"] = sorted(seen)
    return new, read, missing, gaps


def api(params):
    url = API + "?" + urllib.parse.urlencode(params, quote_via=urllib.parse.quote)
    for attempt in range(3):
        try:
            with urllib.request.urlopen(url, timeout=60) as r:
                return json.load(r)
        except Exception:  # transient gateway errors are common on this API
            if attempt == 2:
                raise
            time.sleep(2 * (attempt + 1))


def query_matters(term, since):
    t = term.replace("'", "''")
    flt = (f"(substringof('{t}',MatterTitle) or substringof('{t}',MatterName) or substringof('{t}',MatterFile)) "
           f"and (MatterLastModifiedUtc ge datetime'{since}' or MatterIntroDate ge datetime'{since}')")
    out, skip = [], 0
    while True:
        rows = api({"$filter": flt, "$top": PAGE, "$skip": skip})
        out += rows
        if len(rows) < PAGE:
            return out
        skip += PAGE


def diff_matters(rows_by_term, snapshot):
    """Compare fetched matters with the stored snapshot, and return (new, changed, updated snapshot)."""
    new, changed, updated = [], [], dict(snapshot)
    by_id = {}
    for term, rows in rows_by_term.items():
        for m in rows:
            by_id.setdefault(str(m["MatterId"]), (m, set()))[1].add(term)
    for mid, (m, terms) in sorted(by_id.items(), key=lambda kv: kv[1][0]["MatterFile"] or ""):
        now = {f: m.get(f) for f in MATTER_FIELDS}
        record = {"file": m.get("MatterFile"), "terms": sorted(terms), "type": m.get("MatterTypeName"), "now": now,
                  "url": DETAIL.format(id=m["MatterId"])}
        before = snapshot.get(mid)
        if before is None:
            new.append(record)
        else:
            fields = {f: (before.get(f), now[f]) for f in MATTER_FIELDS if before.get(f) != now[f]}
            if fields:
                record["fields"] = fields
                changed.append(record)
        updated[mid] = now
    return new, changed, updated


def show_date(value):
    return (value or "")[:10] or "blank"


def matter_line(r):
    now = r["now"]
    return (f"- **{r['file']}** ({r['type']}), status {now['MatterStatusName']}, agenda {show_date(now['MatterAgendaDate'])}, "
            f"passed {show_date(now['MatterPassedDate'])}, enactment {now['MatterEnactmentNumber'] or 'blank'}. "
            f"Term: {', '.join(r['terms'])}\n  {squash(now['MatterTitle'] or '')[:400]}\n  {r['url']}")


def render(state, through, first_run, paper, legistar):
    out = [f"# Watch report, run {dt.datetime.now():%Y-%m-%d %H:%M}", "",
           f"Terms: {', '.join(state['terms'])}", f"Window: {state['since']} to {through}", ""]
    if first_run:
        out += ["First run, so everything below is new only to this watch.", ""]

    out.append("## Herald-Guide (OCR text; check the page image before relying on it)")
    if paper is None:
        out += ["Not checked on this run.", ""]
    else:
        new, read, missing, gaps = paper
        out.append(f"Issues read: {len(read)}" + (f", {read[0]} to {read[-1]}" if read else ""))
        fresh = [e for e in new if "first" not in e]
        repeats = [e for e in new if "first" in e]
        out += ["", f"### New notices: {len(fresh)}"]
        for e in fresh:
            out.append(f"- **{e['issue']} p{e['page']}** [{', '.join(e['terms'])}] {e['snippet']}")
            if e["publish"]:
                out.append(f"  PUBLISH line (OCR): {e['publish']}")
        out += ["", f"### Repeats of a notice already seen: {len(repeats)}"]
        for e in repeats:
            out.append(f"- **{e['issue']} p{e['page']}**, first seen {e['first']}, seen in {', '.join(e['issues'])}. "
                       f"[{', '.join(e['terms'])}] {e['snippet']}")
        if missing:
            out += ["", f"No PDF found for: {', '.join(missing)}. These issues weren't searched. "
                        "There may be no issue that week, a different file name or a failed request; the next run retries them."]
        for g in gaps:
            out += ["", f"Gap: {g}."]
        out.append("")

    out.append("## Legistar, Parish Council matters")
    if legistar is None:
        out += ["Not checked on this run.", ""]
    elif isinstance(legistar, str):
        out += [f"Not checked: {legistar}. The next run compares against the last good snapshot.", ""]
    else:
        new, changed = legistar
        out.append(f"### New matters: {len(new)}")
        out += [matter_line(r) for r in new]
        out += ["", f"### Changed matters: {len(changed)}"]
        for r in changed:
            out.append(matter_line(r))
            for f, (a, b) in r["fields"].items():
                out.append(f"  {f.removeprefix('Matter')}: {squash(str(a))[:120]} -> {squash(str(b))[:120]}")
        out.append("")

    out += ["## What this search can't see",
            "- A term OCR garbled, or wrote differently from how the notice spells it. No hit doesn't mean no notice.",
            "- Commission cases, which aren't in Legistar's matters, and Commission meetings without a posted agenda. Read the calendar page in a browser.",
            "- Signs and certified mail, which never appear in the paper.", ""]
    return "\n".join(out)


def cmd_add(args):
    check_dir(args.dir)
    Path(args.dir).mkdir(parents=True, exist_ok=True)
    default = (dt.date.today() - dt.timedelta(days=LOOKBACK_DAYS)).isoformat()
    if args.since:
        dt.date.fromisoformat(args.since)
    if state_path(args.dir).exists():
        state = load_state(args.dir)
        state["terms"] = sorted(set(state["terms"]) | set(args.term))
        if args.since:
            state["since"] = min(state["since"], args.since)
    else:
        state = {"terms": sorted(set(args.term)), "since": args.since or default, "last_run": None,
                 "seen": [], "notices": [], "matters": {}}
    save_state(args.dir, state)
    print(f"Watching {state['terms']} from {state['since']} in {args.dir}")


def cmd_run(args):
    check_dir(args.dir)
    state = load_state(args.dir)
    through = args.through or dt.date.today().isoformat()
    first_run = state["last_run"] is None
    regexes = compile_terms(state["terms"])

    paper = None if args.no_paper else scan_paper(args.dir, state["since"], through, state, regexes)

    legistar = None
    if not args.no_legistar:
        try:
            rows = {t: query_matters(t, state["since"]) for t in state["terms"]}
        except Exception as exc:  # the snapshot stays as it was, so nothing is lost to an outage
            legistar = f"{type(exc).__name__}: {exc}"
        else:
            new, changed, state["matters"] = diff_matters(rows, state["matters"])
            legistar = (new, changed)

    report = render(state, through, first_run, paper, legistar)
    out = Path(args.dir) / "reports" / f"watch-{dt.datetime.now():%Y-%m-%d-%H%M%S}.md"
    out.parent.mkdir(exist_ok=True)
    out.write_text(report)
    state["last_run"] = dt.datetime.now().isoformat(timespec="seconds")
    save_state(args.dir, state)
    print(report)
    print(f"Saved: {out}")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sp = ap.add_subparsers(dest="cmd", required=True)
    a = sp.add_parser("add")
    a.add_argument("--dir", required=True)
    a.add_argument("--term", action="append", required=True)
    a.add_argument("--since", help=f"YYYY-MM-DD; default {LOOKBACK_DAYS} days back")
    r = sp.add_parser("run")
    r.add_argument("--dir", required=True)
    r.add_argument("--through", help="YYYY-MM-DD; default today")
    r.add_argument("--no-paper", action="store_true")
    r.add_argument("--no-legistar", action="store_true")
    args = ap.parse_args()
    {"add": cmd_add, "run": cmd_run}[args.cmd](args)


if __name__ == "__main__":
    main()
