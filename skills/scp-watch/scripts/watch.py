#!/usr/bin/env python3
"""Standing search of the Herald Guide legal notices, Legistar's Parish Council matters and the
Legistar meeting calendar for every parish body.

  watch.py add --dir DIR --term "plain text" [--term ...] [--since YYYY-MM-DD] [--body NAME ...]
  watch.py run --dir DIR [--through YYYY-MM-DD] [--no-paper] [--no-legistar] [--no-calendar]
  watch.py calendar [--body NAME ...] [--term TEXT ...]     one look at the calendar, no state

DIR holds the watch: watch.json (terms and what has been seen), the issue PDFs and their
OCR, and reports/. It belongs in the user's project folder, never in the plugin.

Terms are plain text, not regexes, because the Legistar filter only takes substrings.
Stdlib plus poppler and tesseract. OCR takes minutes per issue, so run `run` in the
background on a first pass.
"""
import argparse, contextlib, datetime as dt, difflib, glob, json, os, re, shutil, subprocess, sys, time
import html as htmllib, urllib.parse, urllib.request
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
# The calendar page is the only public list of meetings whose details aren't published yet: the
# API's /events leaves them out until the clerk makes the meeting viewable, usually with the agenda.
CALENDAR = "https://stcharlesgov.legistar.com/Calendar.aspx"
# Legistar reads the period filter from this cookie, so no form postback is needed. 109 is the
# parish's Legistar client number (GID=109 in its meeting links).
CAL_COOKIE = "Setting-109-Calendar Year"
# Each view stays under the grid's 100-row page; a full year (about 250 rows) would be cut off.
CAL_WINDOWS = ("Last Month", "This Month", "Next Month")
CAL_FIELDS = ("time", "location", "note", "viewable", "agenda", "minutes")
EVENTS = "https://webapi.legistar.com/v1/stcharlesgov/events"
# Chamber bookings are mostly holidays and conferences. Keep the ones that say something about a
# public body: a cancellation, an alternate date, or a public meeting held under the booking.
BOOKING_SIGNAL = re.compile(r"cancel|alternate|public meeting|hearing|postpone|resched", re.I)
CANCEL = re.compile(r"cancel|postpone|resched", re.I)
# Agenda lines that are structure, not business. An agenda made only of these lists nothing to act on.
HEADING = re.compile(r"^(call to order|pledge|prayer|silent prayer|invocation|moment of silence|roll call|attendance|"
                     r"also present|approval of|minutes|unfinished|old business|new business|other business|adjourn|"
                     r"announcements|meetings|persons to address|public comment|reports?\b|resolutions|ordinances|"
                     r"special business|page break|executive session)", re.I)
ENUMERATOR = re.compile(r"^\s*(?:[IVX]+\.|[A-Z]\.|\d+\.)+\s*")
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
    return re.sub(r"\s+", " ", text or "").strip()


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


# ---------- meeting calendar ----------

def norm_body(name):
    return re.sub(r"\s+", " ", (name or "")).strip()


def cell_text(cell):
    return squash(htmllib.unescape(re.sub(r"<[^>]+>", " ", cell)))


def parse_calendar(page):
    """Rows of one Legistar Calendar.aspx view, and the record count the page claims."""
    claimed = re.search(r"(\d+)\s+records", page)
    rows = []
    for tr in re.findall(r'<tr[^>]*class="rg(?:Alt)?Row"[^>]*>(.*?)</tr>', page, flags=re.S):
        cells = re.findall(r"<td[^>]*>(.*?)</td>", tr, flags=re.S)
        if len(cells) < 6:
            continue
        try:
            day = dt.datetime.strptime(cell_text(cells[1]), "%m/%d/%Y").date().isoformat()
        except ValueError:
            continue
        note = re.search(r"<em>(.*?)</em>", cells[4], flags=re.S)
        location = re.sub(r"<em>.*?</em>", "", cells[4], flags=re.S)
        detail = re.search(r'hypMeetingDetail" href="([^"]+)"', tr)
        rows.append({
            "body": norm_body(cell_text(cells[0])), "date": day, "time": cell_text(cells[3]),
            "location": cell_text(location), "note": cell_text(note.group(1)) if note else "",
            # Meetings the clerk hasn't published show the details link greyed out as "Not viewable".
            "viewable": "meeting_NotViewable" not in tr,
            "agenda": 'hypAgenda" href' in tr, "minutes": 'hypMinutes" href' in tr,
            "url": "https://stcharlesgov.legistar.com/" + htmllib.unescape(detail.group(1)) if detail else "",
        })
    return rows, int(claimed.group(1)) if claimed else None


def fetch_calendar(window):
    req = urllib.request.Request(CALENDAR, headers={"User-Agent": "Mozilla/5.0",
                                                    "Cookie": f"{CAL_COOKIE}={window}; Setting-109-Calendar Body=All"})
    for attempt in range(3):
        try:
            with urllib.request.urlopen(req, timeout=90) as r:
                return r.read().decode("utf-8", "ignore")
        except Exception:
            if attempt == 2:
                raise
            time.sleep(2 * (attempt + 1))


def month_bounds(today):
    """First day of last month and last day of next month: the span the three views cover."""
    first_this = today.replace(day=1)
    start = (first_this - dt.timedelta(days=1)).replace(day=1)
    after_next = (first_this + dt.timedelta(days=62)).replace(day=1)
    return start, after_next - dt.timedelta(days=1)


def key_rows(rows):
    """Key each row by body and date, numbering repeats, so a changed time reads as a change."""
    keyed, count = {}, {}
    for r in sorted(rows, key=lambda r: (r["body"], r["date"], r["time"])):
        base = f"{r['body']}|{r['date']}"
        count[base] = count.get(base, 0) + 1
        keyed[base if count[base] == 1 else f"{base}#{count[base]}"] = r
    return keyed


# Notes on other rows name a body by its short form ("Meeting Cancelled - P&Z Department"), so a
# --body filter also matches these.
BODY_ALIASES = {"planning": ("p&z", "p & z", "planning"), "zoning board": ("zba", "board of adjustment"),
                "adjustment": ("zba", "board of adjustment"), "coastal": ("czac", "coastal"),
                "industrial": ("idb", "industrial"), "economic": ("economic", "edc"),
                "communications": ("911", "communications"), "council": ("council",)}


def wanted(row, bodies):
    if row["body"] == "SCP General Chamber Booking" and not BOOKING_SIGNAL.search(row["note"]):
        return False
    if not bodies:
        return True
    text = f"{row['body']} {row['note']}".lower()
    for b in bodies:
        b = b.lower()
        names = {b}.union(*[set(v) for k, v in BODY_ALIASES.items() if k in b])
        if any(n in text for n in names):
            return True
    return False


def business_items(items):
    """Agenda lines that aren't standard headings. A rough count, for spotting an empty agenda."""
    out = []
    for i in items:
        title = squash(i.get("EventItemTitle"))
        if not title:
            continue
        if i.get("EventItemMatterId") or not HEADING.match(ENUMERATOR.sub("", title)):
            out.append(title)
    return out


def api_events(start, end):
    flt = f"EventDate ge datetime'{start}' and EventDate le datetime'{end}'"
    url = EVENTS + "?" + urllib.parse.urlencode({"$filter": flt}, quote_via=urllib.parse.quote)
    with urllib.request.urlopen(url, timeout=90) as r:
        return json.load(r)


def event_items(event_id):
    with urllib.request.urlopen(f"{EVENTS}/{event_id}/eventitems", timeout=90) as r:
        return json.load(r)


def read_agendas(rows, agendas, regexes, today):
    """Fill each posted agenda's business count and term hits, reusing what an unchanged agenda gave.

    Joined to the API by body and date, because the calendar's meeting IDs aren't the API's.
    """
    posted = [r for r in rows.values() if r["agenda"]]
    if not posted:
        return []
    gaps = []
    dates = sorted(r["date"] for r in posted)
    try:
        events = api_events(dates[0], dates[-1])
    except Exception as exc:
        return [f"agenda items not read: {type(exc).__name__}: {exc}"]
    by_key = {}
    for e in events:
        by_key.setdefault(f"{norm_body(e['EventBodyName'])}|{e['EventDate'][:10]}", []).append(e)
    for key, r in rows.items():
        if not r["agenda"]:
            continue
        matches = by_key.get(key.split("#")[0], [])
        if len(matches) != 1:
            gaps.append(f"{key}: agenda posted but its lines weren't read ({len(matches)} API meetings for that body "
                        "and date); open the meeting page")
            continue
        e = matches[0]
        stamp = e.get("EventAgendaLastPublishedUTC") or e.get("EventLastModifiedUtc")
        cached = agendas.get(str(e["EventId"]))
        if not cached or cached.get("stamp") != stamp:
            # Past meetings' agendas don't change what is coming up, so skip them unless never read.
            if cached and r["date"] < today.isoformat():
                r.update({"event": e["EventId"], **{k: cached[k] for k in ("business", "titles")}})
                continue
            try:
                titles = business_items(event_items(e["EventId"]))
            except Exception as exc:
                gaps.append(f"{key}: agenda items not read ({type(exc).__name__})")
                continue
            cached = {"stamp": stamp, "business": len(titles), "titles": titles}
            agendas[str(e["EventId"])] = cached
        r.update({"event": e["EventId"], "business": cached["business"], "titles": cached["titles"]})
    for r in rows.values():
        r["hits"] = [t for t in r.get("titles", []) if any(rx.search(t) for rx in regexes.values())]
    return gaps


def scan_calendar(bodies, regexes, snapshot, agendas, today):
    """Fetch the three calendar views and compare with the last snapshot.

    Returns (rows, new, changed, gone, gaps, span). A row missing from a view is only reported
    gone when its date falls inside the span the views covered on this run.
    """
    rows, gaps, short = [], [], []
    for window in CAL_WINDOWS:
        try:
            got, claimed = parse_calendar(fetch_calendar(window))
        except Exception as exc:
            short.append(f"calendar view '{window}' not read: {type(exc).__name__}: {exc}")
            continue
        if claimed is not None and claimed != len(got):
            short.append(f"calendar view '{window}' claims {claimed} meetings but {len(got)} were read")
        rows += got
    gaps += short
    span = month_bounds(today)
    keyed = {k: r for k, r in key_rows(rows).items() if wanted(r, bodies)}
    gaps += read_agendas(keyed, agendas, regexes, today)
    new, changed = [], []
    for k, r in keyed.items():
        before = snapshot.get(k)
        if before is None:
            new.append(r)
            continue
        fields = {f: (before.get(f), r[f]) for f in CAL_FIELDS if before.get(f) != r[f]}
        if fields:
            changed.append((r, fields))
    # A view that failed or came back short can't show that a meeting is gone.
    gone = [] if short else [
        dict(v, key=k) for k, v in snapshot.items()
        if k not in keyed and span[0].isoformat() <= v.get("date", "") <= span[1].isoformat()
        and wanted(v, bodies)]
    return keyed, new, changed, gone, gaps, span


def meeting_status(r):
    bits = []
    if CANCEL.search(r["note"]):
        bits.append(f"**note: {r['note']}**")
    elif r["note"]:
        bits.append(f"note: {r['note']}")
    if not r["viewable"]:
        bits.append("scheduled; details and agenda not public yet")
    elif r["agenda"] and "business" in r:
        bits.append("agenda posted with no business items beyond headings" if r["business"] == 0
                    else f"agenda posted, {r['business']} items")
    elif r["agenda"]:
        bits.append("agenda posted")
    else:
        bits.append("no agenda posted")
    if r["minutes"]:
        bits.append("minutes posted")
    return "; ".join(bits)


def calendar_lines(r):
    event = f" (API event {r['event']})" if r.get("event") else ""
    return f"- **{r['date']} {r['time'] or ''}** {r['body']}, {r['location'] or 'no location'}. {meeting_status(r)}{event}"


def render_calendar(result, today, first_run):
    out = ["## Meeting calendar (Legistar Calendar.aspx)"]
    if result is None:
        return out + ["Not checked on this run.", ""]
    rows, new, changed, gone, gaps, span = result
    out.append(f"Views read: {', '.join(CAL_WINDOWS)} ({span[0]} to {span[1]}).")
    ahead = sorted((r for r in rows.values() if r["date"] >= today.isoformat()), key=lambda r: (r["date"], r["time"]))
    out += ["", f"### Coming up: {len(ahead)}"] + [calendar_lines(r) for r in ahead]
    # A meeting with nothing on its agenda may not have met, but the calendar doesn't say so, and
    # the clerk records most cancellations in the note. Report both as they read.
    past = sorted((r for r in rows.values() if r["date"] < today.isoformat()
                   and (CANCEL.search(r["note"]) or r.get("business") == 0)), key=lambda r: r["date"])
    out += ["", f"### Past meetings with a cancellation note or an agenda of headings only: {len(past)}"]
    out += [calendar_lines(r) for r in past]
    hits = [r for r in sorted(rows.values(), key=lambda r: r["date"]) if r.get("hits")]
    out += ["", f"### Agenda items matching the terms: {sum(len(r['hits']) for r in hits)}"]
    for r in hits:
        out.append(f"- **{r['date']}** {r['body']} (API event {r.get('event')}) {r['url']}")
        out += [f"  - {t[:300]}" for t in r["hits"]]
    if not first_run:
        out += ["", f"### New on the calendar since the last run: {len(new)}"] + [calendar_lines(r) for r in new]
        out += ["", f"### Changed since the last run: {len(changed)}"]
        for r, fields in changed:
            out.append(calendar_lines(r))
            out += [f"  {f}: {a!r} -> {b!r}" for f, (a, b) in fields.items()]
        out += ["", f"### No longer listed: {len(gone)}",
                "A meeting can drop off because it was cancelled, moved or entered again under another name. "
                "The calendar doesn't say which."]
        out += [f"- {g['date']} {g.get('time', '')} {g['body']}" for g in gone]
    for g in gaps:
        out += ["", f"Gap: {g}."]
    return out + [""]


def cmd_calendar(args):
    today = dt.date.today()
    result = scan_calendar(args.body or [], compile_terms(args.term or []), {}, {}, today)
    print("\n".join(render_calendar(result, today, True)))


def show_date(value):
    return (value or "")[:10] or "blank"


def matter_line(r):
    now = r["now"]
    return (f"- **{r['file']}** ({r['type']}), status {now['MatterStatusName']}, agenda {show_date(now['MatterAgendaDate'])}, "
            f"passed {show_date(now['MatterPassedDate'])}, enactment {now['MatterEnactmentNumber'] or 'blank'}. "
            f"Term: {', '.join(r['terms'])}\n  {squash(now['MatterTitle'] or '')[:400]}\n  {r['url']}")


def render(state, through, first_run, paper, legistar, calendar=None):
    out = [f"# Watch report, run {dt.datetime.now():%Y-%m-%d %H:%M}", "",
           f"Terms: {', '.join(state['terms'])}", f"Window: {state['since']} to {through}", ""]
    if first_run:
        out += ["First run, so everything below is new only to this watch.", ""]

    out.append("## Herald Guide (OCR text; check the page image before relying on it)")
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

    out += render_calendar(calendar, dt.date.today(), first_run)

    out += ["## What this search can't see",
            "- A term OCR garbled, or wrote differently from how the notice spells it. No hit doesn't mean no notice.",
            "- Commission cases, which aren't in Legistar's matters. The calendar section reads their agenda lines once an agenda posts.",
            "- Agenda attachments and packets, which the calendar section doesn't open.",
            "- The Zoning Board of Adjustment's documents, which are on the parish's board page rather than Legistar.",
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
    if args.body:
        state["bodies"] = sorted(set(state.get("bodies", [])) | set(args.body))
    save_state(args.dir, state)
    print(f"Watching {state['terms']} from {state['since']} in {args.dir}"
          + (f"; calendar bodies {state['bodies']}" if state.get("bodies") else "; calendar: all bodies"))


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

    calendar = None
    if not args.no_calendar:
        # Watches made before the calendar source existed have no snapshot, so their first calendar
        # run lists everything as current rather than as new.
        cal_first = "calendar" not in state
        # The calendar's views are relative to the server's today, whatever --through says.
        calendar = scan_calendar(state.get("bodies", []), regexes, state.get("calendar", {}),
                                 state.setdefault("agendas", {}), dt.date.today())
        state["calendar"] = {k: {f: r[f] for f in ("body", "date") + CAL_FIELDS} for k, r in calendar[0].items()}
        if cal_first and not first_run:
            calendar = (calendar[0], [], [], [], calendar[4] + ["first calendar run for this watch, so nothing is marked new"], calendar[5])

    report = render(state, through, first_run, paper, legistar, calendar)
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
    a.add_argument("--body", action="append", help="limit the calendar to bodies whose name or note contains this")
    r = sp.add_parser("run")
    r.add_argument("--dir", required=True)
    r.add_argument("--through", help="YYYY-MM-DD; default today")
    r.add_argument("--no-paper", action="store_true")
    r.add_argument("--no-legistar", action="store_true")
    r.add_argument("--no-calendar", action="store_true")
    c = sp.add_parser("calendar")
    c.add_argument("--body", action="append")
    c.add_argument("--term", action="append")
    args = ap.parse_args()
    {"add": cmd_add, "run": cmd_run, "calendar": cmd_calendar}[args.cmd](args)


if __name__ == "__main__":
    main()
