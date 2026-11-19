#!/usr/bin/env python3
"""What St. Charles Parish government itself applies for, receives, builds and promises for economic
development, from four public sources.

  econdev.py council [--term TEXT ...] [--kind KIND ...] [--since YYYY-MM-DD]
  econdev.py edc [--term TEXT ...] [--since YYYY-MM-DD] [--dir DIR]
  econdev.py outlay --session 26RS [--match TEXT] [--json]
  econdev.py deck FILE.pptx
  econdev.py federal [--sub] [--since YYYY-MM-DD] [--recipient RE] [--agency RE] [--match RE] [--json]

council  Parish Council matter titles: grant applications, state and company cooperative endeavor
         agreements, state capital outlay and Treasury allocations, economic development districts,
         and the department's yearly report.
edc      Meetings of the Economic Development Council (Legistar body 180): agenda items, the files on
         each meeting page, and with --dir, term hits by page in the saved minutes and packets
         (--term needs --dir). Files already saved are reused on a rerun.
outlay   The state capital outlay act (HB2) for one regular session: every line for St. Charles
         Parish government and every project whose location names St. Charles, flagged against the
         Governor's line-item veto message.
deck     Text of a .pptx by slide: text boxes, tables, SmartArt and speaker notes, with a count of the
         pictures on each slide. Slides posted as a PDF are often one image per page; the .pptx
         beside it usually has the text, so read it instead of OCRing the PDF.
federal  Federal grants to recipients named St. Charles Parish from USAspending.gov. --sub lists
         subawards reported by state agencies (pass-through money) instead of prime awards.

Exit codes: 0 found, 1 the source answered and nothing matched, 2 a source wasn't reached.
Downloads go in the user's folder (--dir) or ~/.cache/scp-civics/econdev, never in the plugin.
Standard library plus poppler (pdftotext).
"""
import argparse, datetime as dt, html, json, os, re, subprocess, sys, urllib.parse, urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scp-meeting-record" / "scripts"))
import meeting_record as mr  # noqa: E402

EDC_BODY = 180
GATEWAY = "https://stcharlesgov.legistar.com/gateway.aspx?M=L&ID={}"
LEGIS = "https://legis.la.gov/legis/"
USASPENDING = "https://api.usaspending.gov/api/v2/search/spending_by_award/"
CACHE = Path(os.environ.get("XDG_CACHE_HOME", Path.home() / ".cache")) / "scp-civics" / "econdev"
TOP = 1000  # Legistar's page cap

# Title phrases for each kind of record. Legistar's substringof ignores case and word boundaries,
# so every hit is checked again against the regex beside it.
KINDS = {
    "grant": [("grant application", r"grant application"),
              ("submit an application", r"submit an application"),
              ("supporting the application", r"supporting the application"),
              ("Delta Regional Authority", r"Delta Regional Authority"),
              ("Economic Development Administration", r"Economic Development Administration")],
    "state": [("Department of the Treasury", r"Department of the Treasury"),
              ("Facility Planning and Control", r"Facility Planning and Control"),
              ("Capital Outlay", r"Capital Outlay"),
              ("Office of Community Development", r"Office of Community Development")],
    "cea": [("Cooperative Endeavor", r"Cooperative Endeavor")],
    "district": [("Economic Development District", r"Economic Development District")],
    "report": [("Department of Economic Development", r"Department of Economic Development")],
    "led": [("Louisiana Economic Development", r"Louisiana Economic Development"),
            ("Louisiana Department of Economic Development", r"Louisiana Department of Economic Development")],
}
FPC_NUMBER = re.compile(r"\b\d{2}-[A-Z]\d{2}-\d{2}-\d{2}\b")
MONEY = re.compile(r"\$\s?[\d,]+(?:\.\d{2})?")


def die(msg, code=2):
    print(msg, file=sys.stderr)
    sys.exit(code)


def term_regex(term):
    """Short all-capital terms (EDA, LED, GNO) are acronyms and must match as whole words with their
    case; anything else matches as a case-insensitive phrase."""
    if re.fullmatch(r"[A-Z0-9&]{2,5}", term.strip()):
        return re.compile(rf"\b{re.escape(term.strip())}\b")
    return re.compile(re.escape(term.strip()), re.I)


def kinds_of(title):
    return [k for k, pats in KINDS.items() if any(re.search(rx, title, re.I) for _, rx in pats)]


# ---------- council ----------

def matter_rows(phrase, since=None):
    quoted = phrase.replace("'", "''")
    flt = f"substringof('{quoted}',MatterTitle)"
    if since:
        flt += f" and MatterIntroDate ge datetime'{since}'"
    return mr.legistar("/matters", **{"$filter": flt, "$orderby": "MatterIntroDate desc", "$top": str(TOP)})


def format_matter(r):
    title = mr.squash(r.get("MatterTitle"))
    extras = []
    fpc = FPC_NUMBER.findall(title)
    if fpc:
        extras.append("FP&C " + ", ".join(fpc))
    money = MONEY.findall(title)
    if money:
        extras.append("amounts in title " + ", ".join(m.replace(" ", "") for m in money))
    return (f"- {r['MatterFile']} {(r.get('MatterIntroDate') or '')[:10]} {r.get('MatterTypeName') or ''}, "
            f"{r.get('MatterStatusName') or ''}, no. {r.get('MatterEnactmentNumber') or 'none'}"
            + (f" [{'; '.join(extras)}]" if extras else "")
            + f": {title} {GATEWAY.format(r['MatterId'])}")


def cmd_council(a):
    searches = []
    if a.term:
        searches = [(t, term_regex(t)) for t in a.term]
    else:
        for kind in a.kind or list(KINDS):
            searches += [(p, re.compile(rx, re.I)) for p, rx in KINDS[kind]]
    found, seen, capped = {}, set(), []
    try:
        for phrase, rx in searches:
            # An acronym is sent to Legistar as is; the regex then drops "Veda" for EDA and "filed" for LED.
            rows = matter_rows(phrase.strip(), a.since)
            if len(rows) >= TOP:
                capped.append(phrase)
            for r in rows:
                if r["MatterId"] in seen or not rx.search(mr.squash(r.get("MatterTitle"))):
                    continue
                seen.add(r["MatterId"])
                kinds = kinds_of(r.get("MatterTitle") or "") or ["other"]
                if a.kind and not set(kinds) & set(a.kind):
                    continue
                found.setdefault(kinds[0], []).append(r)
    except Exception as e:
        die(f"Legistar couldn't be reached ({e}). Nothing was checked.")
    print(f"Council matter titles, Legistar API, checked {dt.date.today()}"
          + (f", introduced on or after {a.since}" if a.since else "") + ".\n")
    for kind in list(KINDS) + ["other"]:
        rows = sorted(found.get(kind, []), key=lambda r: r.get("MatterIntroDate") or "", reverse=True)
        if rows:
            print(f"## {kind}: {len(rows)}")
            for r in rows:
                print(format_matter(r))
            print()
    for phrase in capped:
        print(f"\"{phrase}\" reached Legistar's {TOP}-row cap; narrow it with --since.")
    print("Titles only. A title can leave out the site, the company or the program, and an agreement "
          "can sit under a budget amendment or a professional services contract.")
    return 0 if found else 1


# ---------- edc ----------

BOILERPLATE = re.compile(r"^(?:[IVX]+\.\s*)?(call to order|adjourn|next meeting date|other business\s*$)", re.I)
# Packets reprint news articles after the council's own pages. Those own pages carry one of these
# headings; any other page in a packet is treated as a reprint, since an article can run several
# pages without a byline on each.
OWN_PAGE = re.compile(r"economic development council|agenda|statistical report|meeting schedule|"
                      r"department of economic development", re.I)
POSTED_SUMMARY = re.compile(r"^\s*(summary|action items|outline)\s*$", re.I | re.M)


def page_hits(text, terms, packet=False):
    """(page number, line, tag) for each line naming a term. pdftotext separates pages with form
    feeds. The tag marks a reprinted article or the minutes' posted summary."""
    hits = []
    for n, page in enumerate(text.split("\f"), 1):
        reprint = packet and not OWN_PAGE.search(page)
        summary_at = POSTED_SUMMARY.search(page)
        for line in page.splitlines():
            if any(term_regex(t).search(line) for t in terms):
                tag = ("reprinted article" if reprint else
                       "posted summary, not verbatim" if summary_at and page.find(line) > summary_at.start() else "")
                hits.append((n, mr.squash(line), tag))
    return hits


def search_outcome(terms, any_hit, unsearched):
    """Exit code and closing line for a term search. A file that couldn't be searched leaves a
    negative unproven, so no hits plus any unsearched file is 'not checked', not 'nothing found'."""
    if not terms:
        return 0, ""
    note = (f"{len(unsearched)} file(s) weren't searched (image only or not fetched): {'; '.join(unsearched)}. "
            "OCR them (bayou:document-ocr, or ocrmypdf) and rerun." if unsearched else "")
    if any_hit:
        return 0, note
    if unsearched:
        return 2, "No hits in the files that were searched. " + note
    return 1, "No hits in any saved file."


def cmd_edc(a):
    if a.term and not a.dir:
        die("--term searches the saved files, so it needs --dir <project folder>. Nothing was searched.")
    if a.dir:
        mr.check_output(a.dir)
    flt = f"EventBodyId eq {EDC_BODY}" + (f" and EventDate ge datetime'{a.since}'" if a.since else "")
    try:
        events = mr.legistar("/events", **{"$filter": flt, "$orderby": "EventDate desc"})
    except Exception as e:
        die(f"Legistar couldn't be reached ({e}). Nothing was checked.")
    if not events:
        print("No Economic Development Council meetings listed for that period.")
        return 1
    print(f"Economic Development Council (Legistar body {EDC_BODY}): {len(events)} meetings listed, "
          f"{events[-1]['EventDate'][:10]} to {events[0]['EventDate'][:10]}. Checked {dt.date.today()}.\n")
    any_hit, unsearched = False, []
    for e in events:
        day = e["EventDate"][:10]
        note = mr.squash(e.get("EventComment"))
        print(f"## {day} {e.get('EventTime') or ''} at {mr.squash(e.get('EventLocation'))} (event {e['EventId']}): "
              f"{e['EventInSiteURL']}" + (f"\nNote: {note}" if note else ""))
        try:
            items = mr.legistar(f"/events/{e['EventId']}/eventitems")
        except Exception:
            items = []
            print("Agenda items: not read (Legistar error).")
        for i in sorted(items, key=mr.sequence):
            title = mr.squash(i.get("EventItemTitle"))
            if title and not BOILERPLATE.match(title):
                print(f"- {title[:220]}")
        try:
            docs = mr.parse_documents(mr.fetch(e["EventInSiteURL"]).decode("utf-8", "ignore"))
        except Exception:
            docs = None
            unsearched.append(f"{day} meeting page")
            print("Files: meeting page not read.")
        if docs is not None:
            # Sign-in sheets carry members of the public's handwriting and are never saved.
            docs = [d for d in docs if not re.search(r"sign.?in", d[0], re.I)]
            if not any("minutes" in n.lower() for n, _ in docs):
                print("Minutes: none on the meeting page.")
            for name, url in docs:
                if not a.dir:
                    print(f"File: {name}: {url}")
                    continue
                try:
                    pdf, words = mr.save_document(f"{day}_{name}", url, a.dir)
                except Exception:
                    unsearched.append(f"{day} {name}")
                    print(f"File: {name}: not fetched, {url}")
                    continue
                print(f"File: {pdf} ({words} words of text{'; image only, needs OCR' if words < 20 else ''})")
                if a.term and words < 20:
                    unsearched.append(str(pdf.name))
                elif a.term:
                    text = pdf.with_suffix(".txt").read_text(errors="ignore")
                    for page, line, tag in page_hits(text, a.term, packet="packet" in name.lower()):
                        any_hit = True
                        print(f"    p. {page}{f' [{tag}]' if tag else ''}: {line[:200]}")
        print()
    code, note = search_outcome(a.term, any_hit, unsearched)
    if note:
        print(note)
    return code


# ---------- deck ----------

def _runs(xml):
    return [html.unescape(t) for t in re.findall(r"<a:t>([^<]*)</a:t>", xml)]


def _slide_no(name):
    return int(re.search(r"(\d+)\.xml$", name).group(1))


def deck_slides(path):
    """[(slide number, text runs, picture count, diagram runs, note runs)] in slide order. Table
    cells, text boxes and placeholders all appear as runs in the slide XML; SmartArt text sits in
    ppt/diagrams/data*.xml and is reached through the slide's relationships."""
    import zipfile
    z = zipfile.ZipFile(path)
    names = set(z.namelist())
    out = []
    for name in sorted((n for n in names if re.fullmatch(r"ppt/slides/slide\d+\.xml", n)), key=_slide_no):
        n = _slide_no(name)
        xml = z.read(name).decode("utf-8", "ignore")
        rels_name = f"ppt/slides/_rels/slide{n}.xml.rels"
        rels = z.read(rels_name).decode("utf-8", "ignore") if rels_name in names else ""
        diagram, notes = [], []
        for target in re.findall(r'Target="\.\./diagrams/(data\d+\.xml)"', rels):
            diagram += _runs(z.read(f"ppt/diagrams/{target}").decode("utf-8", "ignore"))
        m = re.search(r'Target="\.\./notesSlides/(notesSlide\d+\.xml)"', rels)
        if m:
            # A notes page repeats the slide number as its own run.
            notes = [t for t in _runs(z.read(f"ppt/notesSlides/{m.group(1)}").decode("utf-8", "ignore"))
                     if not t.strip().isdigit()]
        out.append((n, _runs(xml), len(re.findall(r"<p:pic>", xml)), diagram, notes))
    return out


def cmd_deck(a):
    p = Path(a.file)
    if not p.is_file():
        die(f"{p} not found. Nothing was read.")
    try:
        slides = deck_slides(p)
    except Exception as e:
        die(f"{p} couldn't be read as a .pptx ({e}). Nothing was read.")
    for n, runs, pics, diagram, notes in slides:
        print(f"## Slide {n} ({pics} pictures)")
        if runs:
            print(" | ".join(r.strip() for r in runs if r.strip()))
        if diagram:
            print("Diagram: " + " | ".join(r.strip() for r in diagram if r.strip()))
        if notes:
            print("Notes: " + " | ".join(r.strip() for r in notes if r.strip()))
        if pics and len(runs) < 3 and not diagram:
            print("Mostly pictures (logos, photos or charts); their content is not in the text. "
                  "View the image only if a finding depends on it.")
        print()
    return 0 if slides else 1


# ---------- outlay ----------

FOOTER = re.compile(r"^\s*Page (\d+) of (\d+)\s*$")
RUNNING_HEAD = re.compile(r"^\s*HB NO\. \d+\s+(?:ENROLLED|REENGROSSED|ENGROSSED)?\s*$")
NUMBERED = re.compile(r"^\s{0,3}(\d{1,2})\s{2,}(\S.*)$")
AGENCY = re.compile(r"^(\d{2}/[A-Z0-9]{2,4})\s+(.+)$")
PROJECT = re.compile(r"^\((\d{1,7})\)\s+(.+)$")  # 2023 used three-digit numbers
VETO = re.compile(r"Delete\s+Lines?\s+(\d+)(?:\s*(?:through|to|-|–)\s*(\d+))?\s+on\s+Page\s+(\d+)", re.I)


def act_lines(text):
    """(page, line number, content) for every numbered line of the act. A page's lines come before
    its 'Page N of M' footer."""
    out, pending = [], []
    for raw in text.splitlines():
        foot = FOOTER.match(raw)
        if foot:
            out += [(int(foot.group(1)), n, c) for n, c in pending]
            pending = []
            continue
        if RUNNING_HEAD.match(raw):
            continue
        m = NUMBERED.match(raw)
        if m:
            pending.append((int(m.group(1)), m.group(2).rstrip()))
    if pending:
        last = out[-1][0] + 1 if out else 1
        out += [(last, n, c) for n, c in pending]
    return out


def amount(s):
    m = re.search(r"\$\s*([\d,]+)", s)
    return int(m.group(1).replace(",", "")) if m else None


def parse_items(text):
    """Every project in the act with its agency, title, location, funding lines and the
    (page, line) positions it covers."""
    items, agency, cur = [], ("", ""), None
    for page, num, content in act_lines(text):
        c = content.strip()
        ag = AGENCY.match(c)
        pr = PROJECT.match(c)
        if ag or pr:
            if cur:
                items.append(cur)
                cur = None
        if ag:
            agency = (ag.group(1), mr.squash(ag.group(2)))
            continue
        if pr:
            cur = {"agency_code": agency[0], "agency": agency[1], "project": pr.group(1),
                   "title": pr.group(2), "location": "", "funding": [], "positions": [(page, num)],
                   "stage": "title"}
            continue
        if not cur:
            continue
        cur["positions"].append((page, num))
        if cur["stage"] == "title" and c.startswith("("):
            cur["stage"] = "location"
        if cur["stage"] == "title":
            cur["title"] += " " + c
        elif cur["stage"] == "location":
            cur["location"] += (" " if cur["location"] else "") + c
            if ")" in c:
                cur["stage"] = "funding"
        else:
            cur["funding"].append(re.sub(r"\$\s+", "$", re.sub(r"\s{2,}", "  ", c)))
    if cur:
        items.append(cur)
    for it in items:
        it.pop("stage")
        it["title"] = mr.squash(it["title"])
        it["location"] = mr.squash(it["location"]).strip("()")
        total = [amount(f) for f in it["funding"] if f.lower().startswith("total")]
        parts = [amount(f) for f in it["funding"] if not f.lower().startswith("total") and amount(f) is not None]
        it["total"] = total[-1] if total else (sum(parts) if parts else None)
    return items


def parse_vetoes(text):
    """{page: [(first line, last line)]} from the Governor's veto message."""
    out = {}
    for first, last, page in VETO.findall(text):
        out.setdefault(int(page), []).append((int(first), int(last or first)))
    return out


def veto_status(item, vetoes):
    hit = [(p, n) for p, n in item["positions"] if any(a <= n <= b for a, b in vetoes.get(p, []))]
    if not hit:
        return ""
    return "VETOED" if item["positions"][0] in hit else "PARTLY VETOED (some funding lines)"


def in_parish(item):
    return item["agency_code"].endswith("/J45") or re.search(r"\bSt\.?\s+Charles\b", item["location"])


def bill_documents(session):
    page = mr.fetch(f"{LEGIS}BillInfo.aspx?s={session}&b=HB2&sbi=y").decode("utf-8", "ignore")
    docs = {}
    for d, label in re.findall(r'ViewDocument\.aspx\?d=(\d+)"[^>]*>([^<]+)</a>', page):
        label = html.unescape(label).strip()
        if re.fullmatch(r"HB2 Act(?: \d+)?", label):
            docs.setdefault("act", (d, label))
        elif label == "HB2 Enrolled":
            docs.setdefault("enrolled", (d, label))
        elif label == "HB2 Veto Message":
            docs.setdefault("veto", (d, label))
    status = (re.search(r"Signed by the Governor with[^<]*", page)
              or re.search(r"(Signed by the Governor[^<]*|Becomes Act[^<]*|Vetoed[^<]*)", page))
    return docs, (status.group(0).strip() if status else "")


def cached_text(doc_id, name):
    CACHE.mkdir(parents=True, exist_ok=True)
    pdf = CACHE / f"{name}.pdf"
    if not pdf.exists():
        pdf.write_bytes(mr.fetch(f"{LEGIS}ViewDocument.aspx?d={doc_id}"))
    txt = pdf.with_suffix(".txt")
    if not txt.exists():
        subprocess.run(["pdftotext", "-layout", str(pdf), str(txt)], capture_output=True)
    return txt.read_text(errors="ignore") if txt.exists() else ""


def cmd_outlay(a):
    session = a.session.upper()
    try:
        docs, status = bill_documents(session)
    except Exception as e:
        die(f"legis.la.gov couldn't be reached ({e}). Nothing was checked.")
    which = docs.get("act") or docs.get("enrolled")
    if not which:
        die(f"No HB2 Act or Enrolled text listed for {session}.", 1)
    try:
        text = cached_text(which[0], f"hb2-{session}-{which[1].replace(' ', '-')}")
        veto_text = cached_text(docs["veto"][0], f"hb2-{session}-veto") if "veto" in docs else ""
    except Exception as e:
        die(f"The HB2 text couldn't be fetched ({e}). Nothing was checked.")
    items = [i for i in parse_items(text) if in_parish(i)]
    if a.match:
        items = [i for i in items if re.search(a.match, i["title"], re.I)]
    vetoes = parse_vetoes(veto_text)
    for i in items:
        i["veto"] = veto_status(i, vetoes)
    if a.json:
        print(json.dumps({"session": session, "source": which[1], "status": status, "items": items}, indent=1))
        return 0 if items else 1
    print(f"HB2 of the 20{session[:2]} Regular Session, from \"{which[1]}\" "
          f"({LEGIS}ViewDocument.aspx?d={which[0]}). {status}")
    if "veto" in docs:
        print(f"Veto message ({LEGIS}ViewDocument.aspx?d={docs['veto'][0]}): "
              + (f"{sum(len(v) for v in vetoes.values())} deletions read." if vetoes else
                 "no \"Delete Lines\" instructions read; check it by hand."))
    else:
        print("No veto message listed.")
    if which[0] == docs.get("enrolled", ("",))[0]:
        print("No Act text listed, so this is the enrolled bill.")
    print("The act text still prints vetoed lines; the flags below come from the veto message.\n")
    if not items:
        print("No line for St. Charles Parish found" + (f" matching {a.match!r}" if a.match else "") + ".")
        return 1
    for it in items:
        where = "St. Charles Parish government" if it["agency_code"].endswith("/J45") else it["agency"]
        multi = "" if it["location"].strip() == "St. Charles" else f" Location: {it['location']}."
        print(f"- ({it['project']}) {it['title']}. {where} [{it['agency_code']}], p. {it['positions'][0][0]} "
              f"line {it['positions'][0][1]}.{multi}" + (f" {it['veto']}." if it["veto"] else ""))
        for f in it["funding"]:
            print(f"    {f}")
    print("\nAn appropriation isn't cash. Read each priority against the act's own definitions "
          "(Section 1, early pages) before saying money is available.")
    return 0


# ---------- federal ----------

RECIPIENTS = ["ST CHARLES PARISH", "PARISH OF ST. CHARLES", "ST. CHARLES PARISH"]
GRANTS = ["02", "03", "04", "05"]


def usaspending(body):
    req = urllib.request.Request(USASPENDING, data=json.dumps(body).encode(),
                                 headers={"Content-Type": "application/json", **mr.UA})
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.loads(r.read())


MAX_ROWS = 1000


def award_rows(sub, since, until, max_rows=MAX_ROWS):
    fields = (["Sub-Award ID", "Sub-Awardee Name", "Sub-Award Amount", "Sub-Award Date", "Prime Recipient Name",
               "Awarding Agency", "Sub-Award Description", "Prime Award ID"] if sub else
              ["Award ID", "Recipient Name", "Award Amount", "Start Date", "Awarding Agency", "Awarding Sub Agency",
               "Description", "CFDA Number"])
    rows, page = [], 1
    while len(rows) < max_rows:
        body = {"filters": {"recipient_search_text": RECIPIENTS, "award_type_codes": GRANTS,
                            "time_period": [{"start_date": since, "end_date": until}],
                            "recipient_locations": [{"country": "USA", "state": "LA"}]},
                "fields": fields, "limit": 100, "page": page,
                "sort": "Sub-Award Amount" if sub else "Award Amount", "order": "desc"}
        if sub:
            body["subawards"] = True
        data = usaspending(body)
        rows += data.get("results", [])
        if not data.get("page_metadata", {}).get("hasNext"):
            break
        page += 1
    return rows


def normalize(r, sub):
    if sub:
        return {"id": r.get("Sub-Award ID"), "recipient": r.get("Sub-Awardee Name"), "amount": r.get("Sub-Award Amount"),
                "date": r.get("Sub-Award Date"), "agency": r.get("Awarding Agency"),
                "via": r.get("Prime Recipient Name"), "description": mr.squash(r.get("Sub-Award Description")),
                "prime": r.get("Prime Award ID")}
    return {"id": r.get("Award ID"), "recipient": r.get("Recipient Name"), "amount": r.get("Award Amount"),
            "date": r.get("Start Date"), "agency": r.get("Awarding Agency"), "via": r.get("Awarding Sub Agency"),
            "description": mr.squash(r.get("Description")), "cfda": r.get("CFDA Number")}


def dedupe(rows):
    """Sub-award reports repeat one award once per report; the same ID, amount and date is one row."""
    seen, out = set(), []
    for r in rows:
        key = (r["id"], r["amount"], r["date"], r["description"][:60])
        if key not in seen:
            seen.add(key)
            out.append(r)
    return out


def cmd_federal(a):
    until = dt.date.today().isoformat()
    try:
        rows = award_rows(a.sub, a.since, until)
    except Exception as e:
        die(f"USAspending couldn't be reached ({e}). Nothing was checked.")
    capped = len(rows) >= MAX_ROWS
    rows = dedupe([normalize(r, a.sub) for r in rows])
    if a.recipient:
        rows = [r for r in rows if re.search(a.recipient, r["recipient"] or "", re.I)]
    if a.agency:
        rows = [r for r in rows if re.search(a.agency, f"{r['agency']} {r['via']}", re.I)]
    if a.match:
        rows = [r for r in rows if re.search(a.match, r["description"], re.I)]
    if a.json:
        print(json.dumps(rows, indent=1))
        return 0 if rows else 1
    kind = "Subawards reported by prime recipients" if a.sub else "Prime federal grants"
    print(f"{kind} to recipients named St. Charles Parish in Louisiana, USAspending.gov, {a.since} to {until}, "
          f"checked {dt.date.today()}. Recipient names are matched as text, so other parish bodies appear "
          "under their own names.\n")
    if not rows:
        print("Nothing matched.")
        return 1
    groups = {}
    for r in rows:
        groups.setdefault(r["recipient"] or "unnamed", []).append(r)
    for name, rs in sorted(groups.items(), key=lambda kv: -sum(x["amount"] or 0 for x in kv[1])):
        print(f"## {name}: {len(rs)}")
        for r in sorted(rs, key=lambda x: x["date"] or "", reverse=True):
            amt = f"${r['amount']:,.0f}" if isinstance(r["amount"], (int, float)) else "amount not given"
            via = f" via {r['via']}" if r["via"] else ""
            print(f"- {r['date'] or 'no date'} {amt} {r['agency'] or ''}{via} [{r['id']}]: {r['description'][:160]}")
        print()
    if capped:
        print(f"The search stopped at {MAX_ROWS} rows before filtering, largest first; narrow it with --since.")
    print("Amounts are obligations as reported, not money spent. "
          + ("Subawards appear only when the state agency reported them."
             if a.sub else "State pass-through money (OCD, GOHSEP and others) is listed with --sub, not here."))
    return 0


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("council")
    s.add_argument("--term", action="append")
    s.add_argument("--kind", action="append", choices=list(KINDS))
    s.add_argument("--since")
    s.set_defaults(fn=cmd_council)
    s = sub.add_parser("edc")
    s.add_argument("--term", action="append")
    s.add_argument("--since")
    s.add_argument("--dir")
    s.set_defaults(fn=cmd_edc)
    s = sub.add_parser("deck")
    s.add_argument("file")
    s.set_defaults(fn=cmd_deck)
    s = sub.add_parser("outlay")
    s.add_argument("--session", required=True, help="regular session code, e.g. 26RS")
    s.add_argument("--match")
    s.add_argument("--json", action="store_true")
    s.set_defaults(fn=cmd_outlay)
    s = sub.add_parser("federal")
    s.add_argument("--sub", action="store_true")
    s.add_argument("--since", default="2008-10-01")
    s.add_argument("--recipient", help="regex on the recipient name, e.g. '^ST CHARLES PARISH$'")
    s.add_argument("--agency")
    s.add_argument("--match")
    s.add_argument("--json", action="store_true")
    s.set_defaults(fn=cmd_federal)
    a = p.parse_args()
    # Long runs are often piped or backgrounded; line buffering lets a reader see progress.
    sys.stdout.reconfigure(line_buffering=True)
    sys.exit(a.fn(a))


if __name__ == "__main__":
    main()
