#!/usr/bin/env python3
"""Find a St. Charles Parish meeting recording, get a timestamped transcript, and check it.

  meeting_record.py find --body BODY --date YYYY-MM-DD
  meeting_record.py captions --video YOUTUBE_ID --dir DIR
  meeting_record.py audio --url URL --out FILE.flac
  meeting_record.py transcribe --audio FILE --dir DIR [--model NAME]
  meeting_record.py coverage --event ID --transcript FILE.txt
  meeting_record.py names --transcript FILE.txt [--known NAME ...]
  meeting_record.py quote --transcript FILE.txt --text "words as quoted"
  meeting_record.py votes --event ID
  meeting_record.py documents --event ID [--dir DIR]
  meeting_record.py roster [--write FILE]

Transcripts, audio and reports go in the user's project folder, never in the plugin.

Stdlib only. Also needs ffmpeg for audio, yt-dlp for YouTube, and uv for local Whisper.
"""
import argparse, datetime as dt, difflib, html, json, platform, re, shutil, subprocess, sys, time
import urllib.parse, urllib.request
from pathlib import Path

PLUGIN_ROOT = Path(__file__).resolve().parents[3]
sys.dont_write_bytecode = True  # the plugin folder may be a read-only snapshot
ROSTER = PLUGIN_ROOT / "skills" / "scp-meeting-record" / "references" / "officials.md"

LEGISTAR = "https://webapi.legistar.com/v1/stcharlesgov"
CABLECAST = "https://reflect-stcharlesparishla.cablecast.tv/cablecastapi/v1"
CHANNEL = "https://www.youtube.com/channel/UCx8V26EfjQtxPIxbLNdGEQQ"
GRANICUS_CLIP = "https://stcharlesgov.granicus.com/player/clip/{id}"
BOARDS = "https://stcharlesgov.granicus.com/boards/w/93386f0e12a43d7c/boards/{id}"
UA = {"User-Agent": "Mozilla/5.0"}

# The Community Action Advisory Board is left out on purpose: its seats include private and
# low-income community representatives, who aren't public officials in the way these members are.
BOARD_IDS = {
    "Planning and Zoning Commission": 44509,
    "Zoning Board of Adjustment": 44510,
    "Industrial Development Board": 44516,
    "Local ITEP Committee": 52395,
    "Economic Development Council": 53248,
    "Coastal Zone Advisory Committee": 44511,
    "Housing Authority": 44512,
    "Hospital Service District No. 1": 44514,
    "Library Board of Control": 44515,
    "Civil Service Board": 44513,
    "Communications District": 44508,
}
# What a body is called in Cablecast titles, where the spelling varies ("Developement").
TITLE_TERMS = {"economic": "Economic Development", "aging": "Council on Aging", "planning": "Planning", "zoning board": "Zoning Board", "adjustment": "Zoning Board",
               "council": "Parish Council", "industrial": "Industrial", "idb": "Industrial",
               "legislative": "Legislative", "coastal": "Coastal", "housing": "Housing",
               "hospital": "Hospital", "library": "Library", "civil service": "Civil Service",
               "communications": "Communications", "911": "911", "budget": "Budget"}
# A parish upload usually follows its meeting within days, though some come weeks later.
UPLOAD_WINDOW_DAYS = 7
NAME_RATIO = 0.66  # a wrong candidate costs one check of the audio; a missed one stays unresolved
QUOTE_RATIO = 0.8
# Words that follow a title or honorific in speech but aren't names.
NOT_NAMES = {"chairman", "chair", "president", "secretary", "councilman", "councilwoman", "the", "and", "mr", "mrs", "ms"}
CONTACT = re.compile(r"@|\d{3}[-.)]\s?\d{3}|\b(p\.?o\.? box|street|avenue|drive|road|highway)\b", re.I)
SPEAKER = re.compile(r"\b(?:(?:motion by|second by|seconded by|moved by)(?:\s+(?:mr|mrs|ms|dr)\.?)?|"
                     r"mr|mrs|ms|miss|dr|councilman|councilwoman|councilmember|commissioner)\.?\s+"
                     r"([a-zà-ÿ'’-]{2,})", re.I)
CASE_NUMBER = re.compile(r"\b(\d{4})-(\d+)-([A-Z]{1,4})\b")


def fetch(url, headers=UA, tries=3):
    for attempt in range(tries):
        try:
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=60) as r:
                return r.read()
        except Exception:  # transient gateway errors are common on the Legistar API
            if attempt == tries - 1:
                raise
            time.sleep(2 * (attempt + 1))


def fetch_json(url):
    return json.loads(fetch(url))


def legistar(path, **params):
    query = urllib.parse.urlencode(params, quote_via=urllib.parse.quote, safe="$'(),")
    return fetch_json(f"{LEGISTAR}{path}" + (f"?{query}" if query else ""))


def check_output(path):
    if Path(path).resolve().is_relative_to(PLUGIN_ROOT):
        sys.exit(f"{path} is inside the plugin. Recordings and transcripts go in the user's project folder.")


def squash(text):
    return re.sub(r"\s+", " ", text or "").strip()


def clock(seconds):
    s = int(seconds)
    return f"{s // 3600:02d}:{s % 3600 // 60:02d}:{s % 60:02d}"


def title_dates(title):
    """Meeting dates written in a title. Upload dates differ, sometimes by weeks."""
    found = []
    for m in re.finditer(r"([A-Z][a-z]+)\.?\s+(\d{1,2})(?:st|nd|rd|th)?[.,]?\s+(\d{4})", title):
        with_month = f"{m[1][:3]} {m[2]} {m[3]}"
        try:
            found.append(dt.datetime.strptime(with_month, "%b %d %Y").date())
        except ValueError:
            pass
    for m in re.finditer(r"\b(\d{1,2})[-/](\d{1,2})[-/](\d{4})\b", title):
        try:
            found.append(dt.date(int(m[3]), int(m[1]), int(m[2])))
        except ValueError:
            pass
    return found


def title_term(body):
    low = body.lower()
    return next((term for key, term in TITLE_TERMS.items() if key in low), body)


# ---------- finding a recording ----------

def find_events(body, day):
    events = legistar("/events", **{"$filter": f"EventDate eq datetime'{day}'"})
    low = body.lower()
    words = [t for k, t in TITLE_TERMS.items() if k in low]
    return [e for e in events if low in e["EventBodyName"].lower()
            or any(w.lower() in e["EventBodyName"].lower() for w in words)]


def granicus_clip(event):
    """The clip ID behind a Legistar meeting page's Video link, or None if it has no video."""
    try:
        page = fetch(event["EventInSiteURL"]).decode("utf8", "ignore")
    except Exception:
        return None
    tag = re.search(r'hypVideo"[^>]*>', page)
    clip = re.search(r"ID1=(\d+)", html.unescape(tag[0])) if tag else None
    return clip[1] if clip else None


def cablecast_shows(body, day):
    term = urllib.parse.quote(title_term(body))
    data = fetch_json(f"{CABLECAST}/shows?page_size=500&include=vod&search={term}")
    vods = {v["id"]: v for v in data.get("vods", [])}
    day = dt.date.fromisoformat(day)
    rows = []
    for show in data["shows"]:
        named = title_dates(show["title"])
        uploaded = dt.date.fromisoformat(show["eventDate"][:10])
        if named:
            if day not in named:
                continue
            basis = "title"
        elif 0 <= (uploaded - day).days <= UPLOAD_WINDOW_DAYS:
            basis = "upload date only"
        else:
            continue
        for vid in show.get("vods") or []:
            vod = vods.get(vid) or {}
            rows.append({"show": show["id"], "title": show["title"], "seconds": vod.get("length") or show.get("totalRunTime"),
                         "url": vod.get("url"), "captions": bool(show.get("hasCaptions")), "date_from": basis})
    return rows


def youtube_streams(day):
    if not shutil.which("yt-dlp"):
        return None
    out = subprocess.run(["yt-dlp", "--no-warnings", "--flat-playlist", "--print",
                          "%(id)s\t%(duration)s\t%(title)s", f"{CHANNEL}/streams"],
                         capture_output=True, text=True, timeout=180)
    day = dt.date.fromisoformat(day)
    rows = []
    for line in out.stdout.splitlines():
        parts = line.split("\t", 2)
        if len(parts) == 3 and day in title_dates(parts[2]):
            rows.append({"video": parts[0], "seconds": parts[1], "title": parts[2]})
    return rows


def cmd_find(a):
    events = find_events(a.body, a.date)
    print(f"## Legistar events on {a.date} matching '{a.body}'")
    if not events:
        print("None. The API lists a meeting once its agenda posts, so check the Calendar page too.")
    for e in events:
        clip = granicus_clip(e)
        print(f"- event {e['EventId']}: {e['EventBodyName'].strip()} {e['EventTime']}; minutes status "
              f"{e.get('EventMinutesStatusName')}; minutes file {e.get('EventMinutesFile') or 'none'}")
        print(f"  page: {e['EventInSiteURL']}")
        print(f"  agenda: {e.get('EventAgendaFile') or 'none'}")
        print("  Granicus player, for watching only: " + (GRANICUS_CLIP.format(id=clip) if clip else "no video link"))

    print("\n## Cablecast (SCP-TV) replays")
    shows = cablecast_shows(a.body, a.date)
    if not shows:
        print("None matched. Titles vary, so list them: "
              f"{CABLECAST}/shows?page_size=500&search={urllib.parse.quote(title_term(a.body))}")
    for s in shows:
        print(f"- show {s['show']}: {s['title']}; {clock(s['seconds'] or 0)}; captions {s['captions']}; "
              f"date from {s['date_from']}\n  {s['url']}")

    print("\n## YouTube, parish channel livestreams")
    if "council" not in a.body.lower() and "budget" not in a.body.lower() and "legislative" not in a.body.lower():
        print("Skipped: as of 2026-11-03 the channel's streams list has Council and budget meetings, and a few "
              "committee meetings from 2021-2022. Use Cablecast.")
        return
    rows = youtube_streams(a.date)
    if rows is None:
        print("yt-dlp isn't installed.")
    elif not rows:
        print(f"None matched. Check {CHANNEL}/streams")
    for r in rows or []:
        print(f"- {r['video']}: {r['title']}; {r['seconds']} s")


# ---------- transcripts ----------

def vtt_time(stamp):
    parts = [float(x) for x in stamp.split(":")]  # Whisper omits the hour under one hour
    return sum(x * 60 ** i for i, x in enumerate(reversed(parts)))


def parse_vtt(text):
    """(start, line) pairs. YouTube's rolling captions repeat each line in the next cue, so a line
    is kept only the first time, and inline word timing tags are dropped."""
    out, recent = [], []
    for block in re.split(r"\n\s*\n", text):
        lines = block.strip().splitlines()
        stamp = next((i for i, l in enumerate(lines) if "-->" in l), None)
        if stamp is None:
            continue
        start = vtt_time(lines[stamp].split("-->")[0].strip())
        for raw in lines[stamp + 1:]:
            line = squash(html.unescape(re.sub(r"<[^>]+>", "", raw)))
            if not line or line in recent:
                continue
            out.append((start, line))
            recent = (recent + [line])[-3:]
    return out


def write_transcript(pairs, path, header):
    with open(path, "w") as f:
        f.write(header + "\n")
        for start, line in pairs:
            f.write(f"[{clock(start)}] {line}\n")


def read_transcript(path):
    pairs = []
    for line in Path(path).read_text().splitlines():
        m = re.match(r"\[(\d\d):(\d\d):(\d\d)\] (.*)", line)
        if m:
            pairs.append((int(m[1]) * 3600 + int(m[2]) * 60 + int(m[3]), m[4]))
    return pairs


def cmd_captions(a):
    check_output(a.dir)
    if not shutil.which("yt-dlp"):
        sys.exit("yt-dlp isn't installed.")
    out_dir = Path(a.dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    subprocess.run(["yt-dlp", "--no-warnings", "-q", "--skip-download", "--write-subs", "--write-auto-subs",
                    "--sub-langs", "en,en-orig", "--sub-format", "vtt", "-o", str(out_dir / "%(id)s.%(ext)s"),
                    f"https://www.youtube.com/watch?v={a.video}"], check=True, timeout=300)
    vtts = sorted(out_dir.glob(f"{a.video}*.vtt"))
    if not vtts:
        sys.exit(f"No captions for {a.video}. Use `audio` and `transcribe`.")
    pairs = parse_vtt(vtts[0].read_text())
    txt = out_dir / f"{a.video}.txt"
    write_transcript(pairs, txt, f"# YouTube captions for {a.video}, machine-made and unchecked. "
                                 f"https://www.youtube.com/watch?v={a.video}")
    print(f"{len(pairs)} lines, last at {clock(pairs[-1][0]) if pairs else '-'}: {txt}")


def cmd_audio(a):
    check_output(a.out)
    if not shutil.which("ffmpeg"):
        sys.exit("ffmpeg isn't installed.")
    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    # Streaming only the audio track avoids downloading the video, which ran to 740 MB for 19 minutes.
    subprocess.run(["ffmpeg", "-nostdin", "-v", "error", "-y", "-i", a.url, "-vn", "-ac", "1", "-ar", "16000",
                    "-c:a", "flac", a.out], check=True)
    print(a.out)


def roster_people():
    if not ROSTER.exists():
        return []
    people, current = [], None
    for line in ROSTER.read_text().splitlines():
        if line.startswith("## "):
            current = line[3:].strip()
        elif line.startswith("| ") and current and not line.startswith(("| Name", "|---")):
            people.append((current, line.split("|")[1].strip()))
    return people


def surname(name):
    parts = re.sub(r",?\s+(Jr\.?|Sr\.?|II|III|IV)$", "", re.sub(r"\(.*?\)", "", name)).split()
    return parts[-1].rstrip("'’") if parts else ""


def cmd_transcribe(a):
    check_output(a.dir)
    if not shutil.which("uv"):
        sys.exit("uv isn't installed. Install it, or run a Whisper tool yourself and write VTT to the same folder.")
    out_dir = Path(a.dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    if platform.system() == "Darwin" and platform.machine() == "arm64":
        cmd = ["uv", "run", "-q", "--no-project", "--python", "3.12", "--with", "mlx-whisper", "mlx_whisper", a.audio,
               "--model", a.model, "--language", "en", "--output-format", "all", "--output-dir", str(out_dir),
               "--condition-on-previous-text", "False"]
    else:
        model = a.model.rsplit("/", 1)[-1].replace("whisper-", "").replace("-mlx", "")
        cmd = ["uv", "run", "-q", "--no-project", "--python", "3.12", "--with", "openai-whisper", "whisper", a.audio,
               "--model", model, "--language", "en", "--output_format", "all", "--output_dir", str(out_dir),
               "--condition_on_previous_text", "False"]
    subprocess.run(cmd, check=True)
    stem = Path(a.audio).stem
    pairs = parse_vtt((out_dir / f"{stem}.vtt").read_text())
    txt = out_dir / f"{stem}.timed.txt"
    write_transcript(pairs, txt, f"# Local Whisper transcript ({a.model}), machine-made and unchecked.")
    print(f"{len(pairs)} lines, last at {clock(pairs[-1][0]) if pairs else '-'}: {txt}")


# ---------- checks ----------

def normalize(text):
    """Lowercase words only, so "2026 dash 4-h op" and "2026-4-HOP" can meet."""
    text = re.sub(r"\bdash\b", " ", text.lower())
    return re.sub(r"[^a-z0-9]+", " ", text).strip()


def number_key(text):
    return re.sub(r"[^a-z0-9]", "", text.lower())


def item_heard(title, spoken_key, spoken_words):
    case = CASE_NUMBER.search(title or "")
    if case and number_key(case[0]) in spoken_key:
        return f"yes, number {case[0]}"
    words = [w for w in normalize(title or "").split() if len(w) > 3][:12]
    if not words:
        return "no title to compare"
    share = sum(w in spoken_words for w in words) / len(words)
    label = f"number {case[0]} not heard; " if case else ""
    return f"{label}{share:.0%} of the title's first words heard"


def sequence(item):
    return item.get("EventItemAgendaSequence") or item.get("EventItemMinutesSequence") or 0


def cmd_coverage(a):
    pairs = read_transcript(a.transcript)
    spoken = " ".join(line for _, line in pairs)
    key, words = number_key(spoken), set(normalize(spoken).split())
    print(f"Transcript: {len(pairs)} lines, last at {clock(pairs[-1][0]) if pairs else '-'}")
    print("A low share means look in the recording. It doesn't establish the item was skipped.\n")
    print("| Agenda order | File | Title | Heard in transcript |\n|---|---|---|---|")
    for i in sorted(legistar(f"/events/{a.event}/eventitems"), key=sequence):
        title = squash(i.get("EventItemTitle"))
        if not title or title.lower() == "page break":
            continue
        print(f"| {sequence(i)} | {i.get('EventItemMatterFile') or ''} | "
              f"{title[:80]} | {item_heard(title, key, words)} |")


def cmd_names(a):
    known = {}
    for body, name in roster_people():
        known.setdefault(surname(name), f"{name}, {body}")
    known.update({surname(n): f"{n}, supplied" for n in a.known or []})
    counts, first = {}, {}
    for start, line in read_transcript(a.transcript):
        for m in SPEAKER.finditer(line):
            word = m[1].rstrip("'’.,")
            if word.lower() in NOT_NAMES:
                continue
            key = word.lower()
            counts[key] = counts.get(key, 0) + 1
            first.setdefault(key, (start, word))
    print("Suggestions only. The transcript isn't changed. Confirm against the audio before correcting a name.\n")
    print("| Heard | Times | First at | Exact or closest name on file | Status |\n|---|---|---|---|---|")
    surnames = {s.lower(): s for s in known}
    for key in sorted(counts, key=lambda k: first[k][0]):
        start, word = first[key]
        if key in surnames:
            print(f"| {word} | {counts[key]} | {clock(start)} | {known[surnames[key]]} | matches |")
            continue
        close = difflib.get_close_matches(key, surnames, n=1, cutoff=NAME_RATIO)
        if close:
            print(f"| {word} | {counts[key]} | {clock(start)} | {known[surnames[close[0]]]} | likely garbled, check audio |")
        else:
            print(f"| {word} | {counts[key]} | {clock(start)} | | unresolved |")


def cmd_quote(a):
    pairs = read_transcript(a.transcript)
    target = normalize(a.text).split()
    words, starts = [], []
    for start, line in pairs:
        for w in normalize(line).split():
            words.append(w)
            starts.append(start)
    if not target or not words:
        sys.exit("Nothing to compare.")
    size = len(target)
    best, best_i = 0.0, 0
    matcher = difflib.SequenceMatcher(autojunk=False)
    matcher.set_seq2(target)
    for i in range(max(1, len(words) - size + 1)):
        matcher.set_seq1(words[i:i + size])
        score = matcher.ratio()
        if score > best:
            best, best_i = score, i
    found = " ".join(words[best_i:best_i + size])
    verdict = "close match, confirm against the audio" if best >= QUOTE_RATIO else "not found in this transcript"
    print(f"{verdict}\nscore {best:.2f} at {clock(starts[best_i])}\ntranscript: {found}")


def cmd_votes(a):
    print("| File | Title | Action | Result | Votes |\n|---|---|---|---|---|")
    with_votes = 0
    for i in sorted(legistar(f"/events/{a.event}/eventitems"), key=sequence):
        votes = legistar(f"/eventitems/{i['EventItemId']}/votes") if i.get("EventItemMatterId") else []
        with_votes += bool(votes)
        if not votes and not i.get("EventItemActionName"):
            continue
        by_value = {}
        for v in votes:
            by_value.setdefault(v["VoteValueName"], []).append(surname(v["VotePersonName"]))
        summary = "; ".join(f"{k} ({len(v)}): {', '.join(v)}" for k, v in by_value.items()) or "no member votes in API"
        print(f"| {i.get('EventItemMatterFile') or ''} | {squash(i.get('EventItemTitle'))[:70]} | "
              f"{i.get('EventItemActionName') or ''} | {i.get('EventItemPassedFlagName') or ''} | {summary} |")
    print(f"\n{with_votes} items have member votes in the API.")


# ---------- roster ----------

def board_members(board_id):
    """Name, term, seat and appointing authority only. The page also holds appointees' personal
    contact details, which must never reach a report or this plugin."""
    page = fetch(BOARDS.format(id=board_id)).decode("utf8", "ignore")
    page = re.sub(r"<(script|style).*?</\1>", "", page, flags=re.S)
    lines = [squash(html.unescape(x)) for x in re.sub(r"<[^>]+>", "\n", page).splitlines()]
    lines = [x for x in lines if x and not CONTACT.search(x)]
    marks = [i for i, x in enumerate(lines) if re.fullmatch(r"(\d(st|nd|rd|th)|Partial|Current) Term", x)]
    labels = {"Appointing Authority", "Position", "Office/Role", "Category"}
    rows = []
    for n, i in enumerate(marks):
        end = marks[n + 1] - 2 if n + 1 < len(marks) else len(lines)
        fields, j = {}, i + 2
        while j < end - 1:
            if lines[j] in labels:
                fields[lines[j]] = lines[j + 1]
                j += 2
            else:
                j += 1
        rows.append({"name": f"{lines[i - 2]} {lines[i - 1]}", "term": lines[i + 1].replace("  ", " "),
                     "seat": " ".join(filter(None, [fields.get("Position"), fields.get("Office/Role"), fields.get("Category")])),
                     "appointed": fields.get("Appointing Authority", "")})
    return rows


def parse_documents(page):
    """(name, url) for each file on a Legistar meeting page, which the web API doesn't return."""
    docs = []
    for href, label in re.findall(r'href="(View\.ashx\?M=(?:AO|M)&[^"]*)"[^>]*>(.*?)</a>', page, flags=re.S):
        name = squash(re.sub(r"<[^>]+>", " ", label))
        docs.append((name, "https://stcharlesgov.legistar.com/" + html.unescape(href)))
    return docs


def meeting_documents(event):
    url = legistar(f"/events/{event}")["EventInSiteURL"]
    return parse_documents(fetch(url).decode("utf-8", "ignore"))


def save_document(name, url, folder):
    """Save a meeting file and its text layer, returning (pdf path, word count)."""
    folder = Path(folder)
    folder.mkdir(parents=True, exist_ok=True)
    pdf = folder / (re.sub(r"[^\w.-]+", "_", name) + ".pdf")
    if not pdf.exists():
        pdf.write_bytes(fetch(url))
    text = pdf.with_suffix(".txt")
    if not text.exists():
        subprocess.run(["pdftotext", "-layout", str(pdf), str(text)], capture_output=True)
    return pdf, len(text.read_text(errors="ignore").split()) if text.exists() else 0


def cmd_documents(a):
    if a.dir:
        check_output(a.dir)
    event = legistar(f"/events/{a.event}")
    print(f"{event['EventBodyName'].strip()} {event['EventDate'][:10]}: {event['EventInSiteURL']}")
    docs = parse_documents(fetch(event["EventInSiteURL"]).decode("utf-8", "ignore"))
    if not docs:
        print("No files on the meeting page.")
    for name, url in docs:
        # Sign-in sheets can carry speakers' home addresses and aren't needed to check the record.
        if a.dir and not re.search(r"sign.?in", name, re.I):
            pdf, words = save_document(name, url, a.dir)
            print(f"- {name}: {pdf} ({words} words of text)")
        else:
            print(f"- {name}: {url}")


def cmd_roster(a):
    today = dt.date.today().isoformat()
    records = legistar("/officerecords", **{"$filter": f"OfficeRecordEndDate ge datetime'{today}'", "$top": "1000"})
    council = sorted(squash(r["OfficeRecordFullName"]) for r in records if r["OfficeRecordBodyName"].strip() == "Parish Council")
    staff = sorted((r["OfficeRecordBodyName"].strip(), squash(r["OfficeRecordFullName"])) for r in records
                   if r["OfficeRecordBodyName"].startswith(("Department", "Parish President", "Personnel")))
    out = ["# St. Charles Parish officials", "",
           f"Generated by `scripts/meeting_record.py roster` on {today}. Check a name against its source before relying on it.",
           "",
           "Use these to check names in captions and transcripts. Council names, department heads and the Parish President "
           "come from Legistar's office records. Board members come from the parish's Boards & Commissions pages "
           "(Granicus), with personal contact details left out. Legistar's office-record end dates aren't shown because "
           "some are yearly records rather than the end of a seat's term.", "",
           "The Community Action Advisory Board isn't listed because its seats include private community representatives.",
           "", "## Parish Council", "", "| Name |", "|---|"]
    out += [f"| {n} |" for n in council]
    out += ["", "## Parish President and department heads", "", "| Name | Office |", "|---|---|"]
    out += [f"| {n} | {o} |" for o, n in staff]
    for body, board_id in BOARD_IDS.items():
        out += ["", f"## {body}", "", f"Source: {BOARDS.format(id=board_id)}", "",
                "| Name | Seat | Term | Appointed by |", "|---|---|---|---|"]
        members = board_members(board_id)
        out += [f"| {m['name']} | {m['seat']} | {m['term']} | {m['appointed']} |" for m in members]
        print(f"{body}: {len(members)}", file=sys.stderr)
    text = "\n".join(out) + "\n"
    if a.write:
        Path(a.write).parent.mkdir(parents=True, exist_ok=True)
        Path(a.write).write_text(text)
        print(a.write)
    else:
        print(text)


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("find"); s.add_argument("--body", required=True); s.add_argument("--date", required=True)
    s.set_defaults(fn=cmd_find)
    s = sub.add_parser("captions"); s.add_argument("--video", required=True); s.add_argument("--dir", required=True)
    s.set_defaults(fn=cmd_captions)
    s = sub.add_parser("audio"); s.add_argument("--url", required=True); s.add_argument("--out", required=True)
    s.set_defaults(fn=cmd_audio)
    s = sub.add_parser("transcribe"); s.add_argument("--audio", required=True); s.add_argument("--dir", required=True)
    s.add_argument("--model", default="mlx-community/whisper-large-v3-mlx")
    s.set_defaults(fn=cmd_transcribe)
    s = sub.add_parser("coverage"); s.add_argument("--event", required=True, type=int); s.add_argument("--transcript", required=True)
    s.set_defaults(fn=cmd_coverage)
    s = sub.add_parser("names"); s.add_argument("--transcript", required=True); s.add_argument("--known", nargs="*")
    s.set_defaults(fn=cmd_names)
    s = sub.add_parser("quote"); s.add_argument("--transcript", required=True); s.add_argument("--text", required=True)
    s.set_defaults(fn=cmd_quote)
    s = sub.add_parser("votes"); s.add_argument("--event", required=True, type=int)
    s.set_defaults(fn=cmd_votes)
    s = sub.add_parser("documents"); s.add_argument("--event", required=True, type=int); s.add_argument("--dir")
    s.set_defaults(fn=cmd_documents)
    s = sub.add_parser("roster"); s.add_argument("--write")
    s.set_defaults(fn=cmd_roster)
    a = p.parse_args()
    a.fn(a)


if __name__ == "__main__":
    main()
