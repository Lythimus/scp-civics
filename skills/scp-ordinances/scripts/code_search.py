#!/usr/bin/env python3
"""Search a local copy of the St. Charles Parish code, and check Legistar for later amendments.

The index is built from a whole-code PDF the user saved from Municode. It holds the code's text, so
it lives outside the repository, under $SCP_CIVICS_DATA/ordinances/ or a directory given with --dir.

Usage:
  code_search.py build <pdf> [--dir DIR] [--supplement N --through ORD --through-date YYYY-MM-DD]
  code_search.py info [--dir DIR]
  code_search.py search "<terms>" [--chapter X] [--limit N] [--no-legistar] [--dir DIR]
  code_search.py get "<section>" [--page N] [--max-chars N] [--no-legistar] [--dir DIR]
  code_search.py since [--section "<section>"] [--since YYYY-MM-DD] [--links] [--all] [--dir DIR]

Sections are written 2-2, "Sec. 2-2", "App. A XV", "App. C II" or "Charter III C".

Index text comes from a PDF text layer, much of it old OCR, and is good for finding a provision but
not for quoting one. Check the printed page, the signed ordinance or the live section first.
"""
import argparse
import datetime as dt
import html
import json
import os
import re
import shutil
import sqlite3
import subprocess
import sys
import tempfile
import time
import urllib.parse
import urllib.request
from pathlib import Path

API = "https://webapi.legistar.com/v1/stcharlesgov"
WEB = "https://stcharlesgov.legistar.com/gateway.aspx?m=l&id=/matter.aspx?key="
ATTACH = "https://stcharlesgov.legistar1.com/stcharlesgov/attachments/"
MUNICODE = "https://library.municode.com/la/st._charles_parish/codes/code_of_ordinances"
PAGE = 1000  # the API caps $top at 1000
INK_THRESHOLD = 0.02  # blank versos in the looseleaf scan measure about 0.3% from scanner noise

MONTHS = {m: i + 1 for i, m in enumerate(
    "January February March April May June July August September October November December".split())}
ROMAN = {v: i + 1 for i, v in enumerate(
    "I II III IV V VI VII VIII IX X XI XII XIII XIV XV XVI XVII XVIII XIX XX XXI XXII XXIII XXIV XXV "
    "XXVI XXVII XXVIII XXIX XXX XXXI XXXII XXXIII XXXIV XXXV".split())}

WORD = re.compile(r'<word xMin="([\d.]+)" yMin="([\d.]+)" xMax="([\d.]+)" yMax="([\d.]+)">(.*?)</word>', re.S)
CHAPTER = re.compile(r"^(?:Chapter|CHAPTER) (\d+(?:\.\d+)?)\s*\*?$")
SEC = re.compile(r"^Secs?\. ?(\d+(?:\.\d+)?-\d+(?:\.\d+)?)(?:\s*[—–-]+\s*\d+(?:\.\d+)?-\d+(?:\.\d+)?)?\.\s*(.*)$")
MID_SEC = re.compile(r"^(\S.*?) (Secs?\. ?\d+(?:\.\d+)?-\d+(?:\.\d+)?\. [A-Z].*)$")
APP_A_SEC = re.compile(r"^(?:Section|SECTION) ([IVXL]+)\.\s*(.*)$")
APP_C_SEC = re.compile(r"^([IVXL]+)\.\s+([A-Z].*)$")
CHARTER_ART = re.compile(r"^ARTICLE ([IVX]+)\.\s*(.*)$")
CHARTER_SEC = re.compile(r"^Section ([A-Z])\.\s*(.*)$")
RUNNING_HEAD = re.compile(
    r"^(?:APPENDIX [A-Z]\s*[—–-].*|ST\. CHARLES PARISH CODE|CODE COMPARATIVE TABLE|CODE INDEX|CHARTER"
    r"|§§? ?[\w.-]+(?: ?[—–-] ?[\w.-]+)?|Art\. [IVX]+,? (?:§|Sec\.) ?\w+|[\d.]+"
    r"|[A-Z][A-Z ,&'.-]{3,}\s*§§? ?[\w.-]+|§§? ?[\w.-]+\s+[A-Z][A-Z ,&'.-]{3,})$")
FOOTER = re.compile(r"^(?:Supp\. ?No\. ?\d+)?\s*(?:\[?The next page is [\w.]+\]?)?\s*(?:[\d.]+)?$")
HEAD_CAPS = re.compile(r"^[A-Z][A-Z ,&'.—–-]{3,}$")
KEEP_CAPS = re.compile(r"ARTICLE|CHAPTER|1981|PREAMBLE|DIVISION|PART ")


def die(msg):
    sys.exit(f"code_search: {msg}")


# ---- PDF to page lines ---------------------------------------------------------------------------

def page_words(pdf):
    """One word list per PDF page, as (x0, y0, x1, y1, text)."""
    if not shutil.which("pdftotext"):
        die("pdftotext not found; install poppler")
    out = subprocess.run(["pdftotext", "-bbox-layout", str(pdf), "-"], capture_output=True, check=True).stdout
    pages = out.decode("utf-8", "replace").split("<page ")[1:]
    return [[(float(a), float(b), float(c), float(d), html.unescape(t).strip())
             for a, b, c, d, t in WORD.findall(p)] for p in pages]


def to_rows(words):
    """Group words into rows by baseline, as (mid-y, words sorted left to right)."""
    rows = []
    for w in sorted(words, key=lambda w: ((w[1] + w[3]) / 2, w[0])):
        mid = (w[1] + w[3]) / 2
        if rows and abs(rows[-1][0] - mid) <= 3.5:
            rows[-1][1].append(w)
        else:
            rows.append((mid, [w]))
    return [(mid, sorted(ws, key=lambda w: w[0])) for mid, ws in rows]


def row_text(row):
    return " ".join(w[4] for w in row[1])


def find_gutter(words, width=612.0):
    """The x position of the column gap, or None for a single-column page.

    Looseleaf margins alternate by page and the scans drift, so the gutter is found per page. Any x
    through running text crosses a word on most rows, while a real gutter is crossed only by the odd
    full-width row. That difference holds whatever the word count.
    """
    if len(words) < 40:
        return None
    xs = range(int(width * 0.38), int(width * 0.68))
    counts = {x: sum(1 for w in words if w[0] < x < w[2]) for x in xs}
    allowed = max(3, 0.25 * len(to_rows(words)))

    def runs_of(xrange, test):
        runs, start, prev = [], None, None
        for x in xrange:
            if test(x):
                start = x if start is None else start
                prev = x
            elif start is not None:
                runs.append((start, prev))
                start = None
        if start is not None:
            runs.append((start, prev))
        return runs

    def balance(run):
        x = (run[0] + run[1]) / 2
        return min(sum(1 for w in words if w[2] <= x), sum(1 for w in words if w[0] >= x))

    # The real gap is the widest quiet run with text on both sides. Narrower ones are chance alignments
    # of word spaces, which can cross fewer words than a gutter with full-width rows through it.
    runs = [r for r in runs_of(xs, lambda x: counts[x] <= allowed) if r[1] - r[0] >= 2]
    runs = [r for r in runs if balance(r) >= 0.05 * len(words)]
    if not runs:
        return None
    lo, hi = max(runs, key=lambda r: r[1] - r[0])
    # A short right column makes that run reach into the column, so cut at the emptiest part of it.
    span = range(lo, hi + 1)
    fewest = min(counts[x] for x in span)
    a, b = max(runs_of(span, lambda x: counts[x] == fewest), key=lambda r: r[1] - r[0])
    gutter = (a + b) / 2
    left = sum(1 for w in words if w[2] <= gutter)
    right = sum(1 for w in words if w[0] >= gutter)
    return gutter if min(left, right) >= 0.05 * len(words) else None


def reading_order(words):
    """Body text as lines, with full-width rows breaking the two columns into stacked blocks."""
    gutter = find_gutter(words)
    if gutter is None:
        return [row_text(r) for r in to_rows(words)]
    rows = to_rows(words)
    wide = [r for r in rows if any(w[0] < gutter < w[2] for w in r[1])]
    wide_words = {id(w) for r in wide for w in r[1]}
    rest = [w for w in words if id(w) not in wide_words]
    out, prev = [], float("-inf")
    for mid, text in [(r[0], row_text(r)) for r in wide] + [(float("inf"), None)]:
        block = [w for w in rest if prev <= (w[1] + w[3]) / 2 < mid]
        left = to_rows([w for w in block if w[2] <= gutter])
        right = to_rows([w for w in block if w[2] > gutter])
        # A short heading just above a full-width table sits in the left column's x-range but is read
        # after both columns. Limited to a few rows, since a short right column is otherwise normal.
        trailing = []
        if text is not None and right:
            trailing = [r for r in left if r[0] > right[-1][0] + 6]
            trailing = trailing if len(trailing) <= 3 else []
        out += [row_text(r) for r in left[:len(left) - len(trailing)] + right + trailing]
        if text is not None:
            out.append(text)
        prev = mid
    return out


def split_page(words):
    """Separate running heads and footers from the body: (heads, body words, printed page, Supp. No.).

    This runs before column splitting because a footer's parts sit either side of the gutter and
    would otherwise land in the middle of the text.
    """
    rows = to_rows(words)
    heads, printed, supp = [], None, None
    while rows:
        text = row_text(rows[0])
        if not (RUNNING_HEAD.match(text) or (HEAD_CAPS.match(text) and not KEEP_CAPS.search(text))):
            break
        heads.append(text)
        num = re.search(r"\b(\d{1,4}(?:\.\d+)?)$", text)
        printed = num.group(1) if num and "§" not in text else printed
        rows.pop(0)
    while rows:
        text = row_text(rows[-1])
        if not FOOTER.match(text):
            break
        m = re.search(r"Supp\. ?No\. ?(\d+)", text)
        supp = int(m.group(1)) if m else supp
        num = re.search(r"(?:^|\s)(\d{1,4}(?:\.\d+)?)$", text)
        printed = num.group(1) if num else printed
        rows.pop()
    return heads, [w for r in rows for w in r[1]], printed, supp


def page_ink(pdf, page):
    """Share of dark pixels on a page, read from a low-resolution PGM render."""
    if not shutil.which("pdftoppm"):
        return 0.0
    data = subprocess.run(["pdftoppm", "-f", str(page), "-l", str(page), "-r", "40", "-gray", str(pdf)],
                          capture_output=True).stdout
    m = re.match(rb"P5\s+(?:#.*\s+)*(\d+)\s+(\d+)\s+(\d+)\s", data)
    if not m:
        return 0.0
    px = data[m.end():]
    return sum(1 for b in px if b < 128) / max(1, len(px))


def ocr_page(pdf, page):
    if not shutil.which("tesseract") or not shutil.which("pdftoppm"):
        return None
    with tempfile.TemporaryDirectory() as d:
        subprocess.run(["pdftoppm", "-f", str(page), "-l", str(page), "-r", "200", "-gray", "-png", str(pdf),
                        f"{d}/p"], check=True, capture_output=True)
        img = next(Path(d).glob("p*.png"))
        text = subprocess.run(["tesseract", str(img), "-", "--psm", "1"], capture_output=True, text=True).stdout
    return [ln.strip() for ln in text.splitlines() if ln.strip()]


# ---- sections -------------------------------------------------------------------------------------

def join_hyphens(lines):
    """Rejoin words split across lines. A compound such as right-of- keeps its hyphen."""
    out = []
    for ln in lines:
        if out and re.search(r"[a-z]-$", out[-1]) and re.match(r"[a-z]", ln):
            last = out[-1].split()[-1] if out[-1].split() else ""
            out[-1] = out[-1] + ln if "-" in last[:-1] else out[-1][:-1] + ln
        else:
            out.append(ln)
    return out


def cover_vintage(pages):
    """Supplement and through-ordinance from the newest supplement's cover sheet, or None.

    Both come from one page, read without column splitting. The file holds every old cover in turn,
    so reading further could pair this supplement with an earlier supplement's through date.
    """
    for words in pages[:6]:
        text = " ".join(row_text(r) for r in to_rows(words))
        sup = re.search(r"SUPPLEMENT NO\.\s*(\d+)", text)
        if not sup:
            continue
        thr = re.search(r"Ordinance No\.\s*([\d-]+),\s*adopted\s+(\w+)\s+(\d+),\s*(\d{4})", text)
        if not thr or thr.group(2) not in MONTHS:
            return None
        return {"supplement": sup.group(1), "through": thr.group(1),
                "through_date": dt.date(int(thr.group(4)), MONTHS[thr.group(2)], int(thr.group(3))).isoformat()}
    return None


class Segmenter:
    """Walks pages in order and cuts them into sections.

    Chapters head sections "Sec. 2-2.", Appendix A "Section XV.", Appendix C a bare "II." and the
    Charter "ARTICLE III." then "Section C.". Each style is accepted only inside its own part, and
    roman numerals must advance by a small step, because "Section XV" and list items also start
    lines in running text.
    """

    def __init__(self):
        self.region = "front"
        self.chapter = None
        self.article = None
        self.letter = ""
        self.roman = 0
        self.current = None
        self.chunks = []

    def open(self, sid, part, title, page):
        self.current = {"sid": sid, "part": part, "title": title.strip(" .")[:160], "page": page}

    def add(self, line, page, printed, supp):
        c = self.current
        if c is None:
            return
        if self.chunks and self.chunks[-1]["sid"] == c["sid"] and self.chunks[-1]["page"] == page:
            self.chunks[-1]["lines"].append(line)
        else:
            self.chunks.append({**c, "page": page, "printed": printed, "supp": supp, "lines": [line]})

    def feed(self, lines, page, printed, supp):
        if self.region == "chapter":
            # Where no gutter was found, a heading can share a row with the other column's text.
            split = []
            for line in lines:
                m = MID_SEC.match(line)
                split += [m.group(1), m.group(2)] if m else [line]
            lines = split
        for i, line in enumerate(lines):
            if self.transition(line, page):
                continue
            if self.region == "charter":
                m = CHARTER_ART.match(line)
                if m and m.group(1) in ROMAN and ROMAN[m.group(1)] >= (ROMAN.get(self.article) or 0):
                    self.article = m.group(1)
                    self.letter = ""
                    self.open(f"Charter-{self.article}", "Home Rule Charter", f"Art. {self.article}. {m.group(2)}", page)
                    self.add(line, page, printed, supp)
                    continue
                m = CHARTER_SEC.match(line)
                if m and self.article and m.group(1) > self.letter:
                    self.letter = m.group(1)
                    self.open(f"Charter-{self.article}-{m.group(1)}", "Home Rule Charter",
                              f"Art. {self.article}, Sec. {m.group(1)}. {m.group(2)}", page)
            elif self.region == "chapter":
                m = SEC.match(line)
                if m and self.is_heading(m, lines[i + 1:i + 2]):
                    self.open(m.group(1), f"Chapter {self.chapter}", m.group(2), page)
            elif self.region in ("appA", "appC"):
                m = (APP_A_SEC if self.region == "appA" else APP_C_SEC).match(line)
                if m and m.group(1) in ROMAN and 0 < ROMAN[m.group(1)] - self.roman <= 3:
                    self.roman = ROMAN[m.group(1)]
                    letter = "A" if self.region == "appA" else "C"
                    self.open(f"App-{letter}-{m.group(1)}", f"Appendix {letter}", m.group(2), page)
            self.add(line, page, printed, supp)

    def is_heading(self, m, following):
        """A real heading's chapter matches, and a table-of-contents line is followed by a later one."""
        sec_chapter = m.group(1).split("-")[0]
        if sec_chapter != self.chapter:
            return False
        if m.group(2) and m.group(2)[0].islower():
            return False
        if following:
            nxt = SEC.match(following[0])
            if nxt:
                num = lambda sid: [float(x) for x in sid.split("-")]
                return num(nxt.group(1)) < num(m.group(1))
        return True

    def transition(self, line, page):
        m = CHAPTER.match(line)
        if m and self.region in ("charter", "charter_table", "chapter") and (
                self.chapter is None or float(m.group(1)) > float(self.chapter)):
            self.region, self.chapter = "chapter", m.group(1)
            self.open(f"Ch-{self.chapter}", f"Chapter {self.chapter}", "chapter front matter", page)
            return True
        if self.region == "front" and re.match(r"^ARTICLE I\.\s*ESTABLISHMENT", line):
            self.region = "charter"
            self.article = None
            return False
        if self.region == "charter" and "CHARTER COMPARATIVE TABLE" in line:
            self.region, self.current = "charter_table", None
            return True
        if "ZONING ORDINANCE OF 1981 *" in line and self.region == "chapter":
            self.region, self.roman = "appA", 0
            self.open("App-A", "Appendix A", "appendix front matter", page)
            return False
        if "SUBDIVISION REGULATIONS OF 1981 *" in line and self.region in ("chapter", "appA"):
            self.region, self.roman = "appC", 0
            self.open("App-C", "Appendix C", "appendix front matter", page)
            return False
        if line.startswith("CODE COMPARATIVE TABLE") and self.region in ("appA", "appC"):
            self.region, self.current = "tables", None
            return True
        if line.startswith("CODE INDEX") and self.region == "tables":
            self.region = "index"
            self.open("Index", "Code Index", "subject index", page)
            return True
        return False


def dedupe(chunks):
    """Keep each section's longest run of chunks, which drops table-of-contents copies of a heading."""
    runs, order = {}, []
    prev = None
    for c in chunks:
        if c["sid"] != prev:
            runs.setdefault(c["sid"], []).append([])
            if c["sid"] not in order:
                order.append(c["sid"])
            prev = c["sid"]
        runs[c["sid"]][-1].append(c)
    out = []
    for sid in order:
        best = max(runs[sid], key=lambda run: sum(len(" ".join(c["lines"])) for c in run))
        out += best
    return out


def resolve_dir(arg):
    if arg:
        return Path(arg).expanduser()
    root = os.environ.get("SCP_CIVICS_DATA")
    if not root:
        die("SCP_CIVICS_DATA is not set; set it to your data folder, or pass --dir")
    return Path(root) / "ordinances"


def cmd_build(a):
    pdf = Path(a.pdf).expanduser()
    if not pdf.exists():
        die(f"no such file: {pdf}")
    out = resolve_dir(a.dir)
    out.mkdir(parents=True, exist_ok=True)
    pages = page_words(pdf)
    if not pages:
        die("the PDF yielded no pages")
    ocr, blank, ordered, one_column = [], 0, [], []
    for n, words in enumerate(pages, 1):
        if words:
            heads, body, printed, supp = split_page(words)
            if len(body) > 150 and find_gutter(body) is None:
                one_column.append(n)
            ordered.append((heads, reading_order(body), printed, supp))
            continue
        if page_ink(pdf, n) >= INK_THRESHOLD:
            lines = ocr_page(pdf, n)
            if lines:
                ocr.append(n)
                ordered.append(([], lines, None, None))
                continue
            print(f"warning: page {n} has ink but no text, and OCR was not available", file=sys.stderr)
        else:
            blank += 1
        ordered.append(([], [], None, None))

    vintage = cover_vintage(pages)
    if a.supplement or a.through or a.through_date:
        if not (a.supplement and a.through and a.through_date):
            die("--supplement, --through and --through-date go together")
        vintage = {"supplement": a.supplement, "through": a.through, "through_date": a.through_date}
    if not vintage:
        die("could not read the supplement and through-date from the cover sheet. Take them from Municode's "
            "landing page and pass --supplement, --through and --through-date. An index needs a vintage.")

    seg = Segmenter()
    for n, (heads, body, printed, supp) in enumerate(ordered, 1):
        for head in heads:
            seg.transition(head, n)
        seg.feed(body, n, printed, supp)
    chunks = dedupe(seg.chunks)
    if not chunks:
        die("no sections recognised; this PDF's layout differs from the looseleaf the parser expects")

    db = out / "code.sqlite"
    db.unlink(missing_ok=True)
    con = sqlite3.connect(db)
    con.executescript("""
        CREATE TABLE meta(key TEXT PRIMARY KEY, value TEXT);
        CREATE TABLE chunks(id INTEGER PRIMARY KEY, sid TEXT, part TEXT, title TEXT, page INTEGER,
                            printed TEXT, supp INTEGER, body TEXT);
        CREATE INDEX chunks_sid ON chunks(sid);
        CREATE VIRTUAL TABLE fts USING fts5(body, content='chunks', content_rowid='id',
                                            tokenize='porter unicode61');
    """)
    for c in chunks:
        con.execute("INSERT INTO chunks(sid,part,title,page,printed,supp,body) VALUES (?,?,?,?,?,?,?)",
                    (c["sid"], c["part"], c["title"], c["page"], c["printed"], c["supp"],
                     "\n".join(join_hyphens(c["lines"]))))
    con.execute("INSERT INTO fts(fts) VALUES ('rebuild')")
    meta = {**vintage, "source": pdf.name, "pdf": str(pdf), "pages": str(len(pages)),
            "built": dt.date.today().isoformat()}
    con.executemany("INSERT INTO meta VALUES (?,?)", meta.items())
    con.commit()

    print(f"Built {db}")
    print(vintage_line(meta))
    print(f"PDF pages {len(pages)}; blank {blank}; OCR'd {len(ocr)}{' ' + str(ocr[:20]) if ocr else ''}")
    print(f"Dense pages read as one column: {len(one_column)}. Tables are expected here; two-column text "
          f"would read interleaved. {one_column}")
    print("Sections per part:")
    for part, n in con.execute("SELECT part, COUNT(DISTINCT sid) FROM chunks GROUP BY part ORDER BY MIN(id)"):
        print(f"  {part}: {n}")
    return 0


# ---- index reads ----------------------------------------------------------------------------------

def open_index(a):
    d = resolve_dir(a.dir)
    db = d / "code.sqlite"
    if not db.exists():
        die(f"no index at {db}. Save the code PDF from Municode in your browser, then run: "
            f"code_search.py build <pdf>")
    con = sqlite3.connect(db)
    return con, dict(con.execute("SELECT key, value FROM meta"))


def vintage_line(meta):
    return (f"Text from Supplement {meta['supplement']}, codified through Ord. {meta['through']} "
            f"({meta['through_date']}). Source: {meta['source']}, indexed {meta['built']}.")


def normalize_section(s):
    s = re.sub(r"\s+", " ", s.strip())
    m = re.fullmatch(r"(?:Secs?\.?|Section|§)?\s*(\d+(?:\.\d+)?-\d+(?:\.\d+)?)\.?", s, re.I)
    if m:
        return m.group(1)
    m = re.fullmatch(r"(?:App(?:endix|\.)?)\s*([AC])[,\s]*(?:Sec(?:tion|\.)?|§)?\s*([IVXL]+)\b.*", s, re.I)
    if m:
        return f"App-{m.group(1).upper()}-{m.group(2).upper()}"
    m = re.fullmatch(r"(?:Charter|Art(?:icle|\.)?)\s*(?:Art(?:icle|\.)?)?\s*([IVX]+)[,\s]*(?:Sec(?:tion|\.)?|§)?\s*([A-Z])?\b.*", s, re.I)
    if m:
        return f"Charter-{m.group(1).upper()}" + (f"-{m.group(2).upper()}" if m.group(2) else "")
    return s


def display_sid(sid):
    m = re.fullmatch(r"App-([AC])(?:-(\w+))?", sid)
    if m:
        return f"Appendix {m.group(1)}" + (f" Sec. {m.group(2)}" if m.group(2) else " front matter")
    m = re.fullmatch(r"Charter-(\w+)(?:-(\w+))?", sid)
    if m:
        return f"Charter Art. {m.group(1)}" + (f" Sec. {m.group(2)}" if m.group(2) else "")
    if sid.startswith("Ch-"):
        return f"Chapter {sid[3:]} front matter"
    return sid if sid == "Index" else f"Sec. {sid}"


def fts_query(terms, prefix=False):
    """Plain words are ANDed, quoted phrases are kept, and FTS operators can't be typed by accident."""
    parts = re.findall(r'"[^"]+"|[^\s"]+', terms)
    out = []
    for p in parts:
        if p.startswith('"'):
            out.append(p)
        else:
            w = re.sub(r"[^\w.-]", "", p)
            if w:
                out.append(f'"{w}"' + ("*" if prefix else ""))
    return " ".join(out)


def cmd_search(a):
    con, meta = open_index(a)
    q = fts_query(a.terms)
    if not q:
        die("no search terms")
    where, args = "", []
    if a.chapter:
        where = "AND c.part = ?"
        args = [{"A": "Appendix A", "C": "Appendix C", "CHARTER": "Home Rule Charter", "INDEX": "Code Index"}
                .get(a.chapter.upper(), f"Chapter {a.chapter}")]
    sql = f"""SELECT c.sid, c.part, c.title, c.page, c.printed, c.supp,
                     snippet(fts, 0, '[', ']', ' ... ', 28), bm25(fts)
              FROM fts JOIN chunks c ON c.id = fts.rowid
              WHERE fts MATCH ? {where} ORDER BY bm25(fts)"""
    rows = con.execute(sql, [q] + args).fetchall()
    note = ""
    if not rows:
        rows = con.execute(sql, [fts_query(a.terms, prefix=True)] + args).fetchall() if '"' not in a.terms else []
        if rows:
            note = "No exact match, so these are prefix matches.\n"
    print(vintage_line(meta))
    amendments, status = later_amendments(meta, a.no_legistar)
    print(status)
    print(note, end="")
    grouped = {}
    for r in rows:
        grouped.setdefault(r[0], []).append(r)
    print(f"{len(grouped)} sections, {len(rows)} page hits. The text layer has OCR errors, so a miss is not proof of absence.\n")
    for sid, hits in list(grouped.items())[:a.limit]:
        first = hits[0]
        pages = sorted({h[3] for h in hits})
        print(f"{display_sid(sid)}. {first[2]} ({first[1]})")
        print(f"  PDF p. {', '.join(map(str, pages[:8]))}{' ...' if len(pages) > 8 else ''}"
              f"; printed p. {first[4] or '?'}; page last changed Supp. {first[5] or '?'}")
        print("  " + re.sub(r"\s+", " ", first[6]))
        for line in flags_for(sid, first[1], amendments):
            print("  " + line)
        print()
    if len(grouped) > a.limit:
        print(f"... and {len(grouped) - a.limit} more sections; raise --limit to see them.")
    return 0


def cmd_get(a):
    con, meta = open_index(a)
    sid = normalize_section(a.section)
    rows = con.execute("SELECT part, title, page, printed, supp, body FROM chunks WHERE sid = ? ORDER BY id", (sid,)).fetchall()
    if not rows:
        like = con.execute("SELECT DISTINCT sid FROM chunks WHERE sid LIKE ? LIMIT 12", (f"{sid}%",)).fetchall()
        die(f"no section {sid!r} in the index." + (f" Close: {', '.join(r[0] for r in like)}" if like else ""))
    if a.page:
        rows = [r for r in rows if r[2] == a.page]
        if not rows:
            die(f"{sid} has no text on PDF p. {a.page}")
    print(vintage_line(meta))
    amendments, status = later_amendments(meta, a.no_legistar)
    print(status)
    print(f"{display_sid(sid)}. {rows[0][1]} ({rows[0][0]}); PDF p. {rows[0][2]}-{rows[-1][2]}")
    print("Unverified PDF text. Check it against the page image before quoting.")
    for line in flags_for(sid, rows[0][0], amendments):
        print(line)
    print()
    used = 0
    for r in rows:
        if used >= a.max_chars:
            print(f"[stopped at --max-chars {a.max_chars}; continue with --page {r[2]}]")
            break
        print(f"--- PDF p. {r[2]}; printed p. {r[3] or '?'}; page last changed Supp. {r[4] or '?'}")
        print(r[5][:a.max_chars - used])
        used += len(r[5])
    return 0


def cmd_info(a):
    con, meta = open_index(a)
    print(vintage_line(meta))
    print(f"PDF: {meta['pdf']}")
    for part, n in con.execute("SELECT part, COUNT(DISTINCT sid) FROM chunks GROUP BY part ORDER BY MIN(id)"):
        print(f"  {part}: {n}")
    return 0


# ---- Legistar -------------------------------------------------------------------------------------

def api(path, params=None):
    url = f"{API}/{path}"
    if params:
        url += "?" + urllib.parse.urlencode(params, quote_via=urllib.parse.quote)
    for attempt in range(3):
        try:
            with urllib.request.urlopen(url, timeout=60) as r:
                return json.load(r)
        except Exception:  # transient gateway errors are common on this API
            if attempt == 2:
                raise
            time.sleep(2 * (attempt + 1))


def already_codified(m, through):
    """True for the through ordinance and earlier ones adopted the same day, which share its number run."""
    num, thr = m.get("MatterEnactmentNumber") or "", through or ""
    a, b = re.fullmatch(r"(\d+-\d+)-(\d+)", num), re.fullmatch(r"(\d+-\d+)-(\d+)", thr)
    return bool(a and b and a.group(1) == b.group(1) and int(a.group(2)) <= int(b.group(2)))


def ordinances_since(since):
    flt = (f"MatterTypeName eq 'Ordinance' and (MatterPassedDate ge datetime'{since}' "
           f"or MatterIntroDate ge datetime'{since}')")
    out, skip = [], 0
    while True:
        page = api("matters", {"$filter": flt, "$top": PAGE, "$skip": skip, "$orderby": "MatterPassedDate desc"})
        out += page
        if len(page) < PAGE:
            return out
        skip += PAGE


def targets(title):
    """What an ordinance title says it amends: section numbers, chapters, appendix sections, appendices."""
    t = title or ""
    # Titles also hold bare number pairs such as voting precincts, so a section needs its "Sec." label.
    labelled = re.findall(r"\b(?:Secs?\.?|Sections?)\s*(\d+(?:\.\d+)?-\d+(?:\.\d+)?(?:[,\s]+(?:and\s+)?\d+(?:\.\d+)?-\d+(?:\.\d+)?)*)", t, re.I)
    found = {"sections": {x for run in labelled for x in re.findall(r"\d+(?:\.\d+)?-\d+(?:\.\d+)?", run)},
             "chapters": set(re.findall(r"\bChapter\s+(\d+(?:\.\d+)?)\b", t, re.I)),
             "appendices": set(), "romans": set(re.findall(r"\bSection\s+([IVXL]+)\b", t))}
    if re.search(r"Appendix\s+A\b|Zoning Ordinance", t, re.I):
        found["appendices"].add("A")
    if re.search(r"Appendix\s+C\b|Subdivision Regulations", t, re.I):
        found["appendices"].add("C")
    if re.search(r"Home Rule Charter|\bCharter\b", t, re.I):
        found["appendices"].add("Charter")
    found["chapters"] |= {s.split("-")[0] for s in found["sections"]}
    return found


def classify(m):
    """text = amends the code's words; map = rezones land; other = not an amendment of the code."""
    t = m.get("MatterTitle") or ""
    if re.search(r"change the zoning classification|zoning classification|Official Zoning Map|Future Land Use", t, re.I) \
            and not re.search(r"Section\s+[IVXL]+\b", t):
        return "map"
    if re.search(r"amend|add|repeal|revise|adopt", t, re.I) and re.search(
            r"Code of Ordinance|Zoning Ordinance|Subdivision Regulations|Appendix [AC]|Home Rule Charter", t, re.I):
        return "text"
    return "other"


def enacted(m):
    return (m.get("MatterStatusName") or "").startswith("Enacted") and m.get("MatterEnactmentNumber")


def later_amendments(meta, skip=False):
    """Text amendments after the index vintage, plus a status line that says whether the check ran."""
    if skip:
        return [], "Legistar check skipped, so later amendments are unknown."
    try:
        rows = ordinances_since(meta["through_date"])
    except Exception as e:
        return [], f"LEGISTAR CHECK FAILED ({e}), so later amendments are unknown."
    rows = [m for m in rows if not already_codified(m, meta["through"])]
    text = [m for m in rows if classify(m) == "text" and enacted(m)]
    return text, (f"Legistar checked {dt.date.today().isoformat()}: {len(text)} enacted text amendments "
                  f"since {meta['through_date']}. Run `since` for the list.")


def flags_for(sid, part, amendments):
    """Name later ordinances that may reach this section. A title match is a lead, and silence proves nothing."""
    out = []
    m = re.fullmatch(r"App-([AC])(?:-(\w+))?", sid)
    chapter = part.split()[-1] if part.startswith("Chapter") else None
    for o in amendments:
        t = targets(o.get("MatterTitle"))
        level = None
        if m:
            if m.group(1) in t["appendices"]:
                level = "this section" if m.group(2) and m.group(2) in t["romans"] else "this appendix"
        elif sid.startswith("Charter"):
            level = "the Charter" if "Charter" in t["appendices"] else None
        elif sid in t["sections"]:
            level = "this section"
        elif chapter and chapter in t["chapters"]:
            level = "this chapter"
        if level:
            out.append((0 if level == "this section" else 1, o, level))
    out.sort(key=lambda x: x[0])
    return [f"AMENDMENT LEAD ({level}): Ord. {o['MatterEnactmentNumber']}, passed {(o.get('MatterPassedDate') or '')[:10]}, "
            f"file {o['MatterFile']}: {' '.join((o.get('MatterTitle') or '').split())[:150]}"
            for _, o, level in out[:6]]


def attachment_url(a):
    """The API's hyperlink carries another client's path and returns 404; the file name is right."""
    return ATTACH + a["MatterAttachmentFileName"] if a.get("MatterAttachmentFileName") else a["MatterAttachmentHyperlink"]


def cmd_since(a):
    meta = {}
    if not a.since:
        con, meta = open_index(a)
        print(vintage_line(meta))
    since = a.since or meta["through_date"]
    rows = [m for m in ordinances_since(since) if not already_codified(m, meta.get("through"))]
    groups = {"text": [], "unconfirmed": [], "map": [], "pending": [], "other": []}
    for m in rows:
        kind = classify(m)
        status = m.get("MatterStatusName") or ""
        if kind == "other":
            groups["other"].append(m)
        elif status.startswith("Enacted") and not m.get("MatterEnactmentNumber"):
            groups["unconfirmed"].append(m)
        elif enacted(m):
            groups[kind].append(m)
        else:
            groups["pending"].append(m)
    if a.section:
        sid = normalize_section(a.section)
        ch = sid.split("-")[0]
        app = re.fullmatch(r"App-([AC])(?:-(\w+))?", sid)

        def hits(m):
            t = targets(m.get("MatterTitle"))
            if app:
                return app.group(1) in t["appendices"] and (not app.group(2) or not t["romans"] or app.group(2) in t["romans"])
            if sid.startswith("Charter"):
                return "Charter" in t["appendices"]
            return sid in t["sections"] or ch in t["chapters"]
        groups = {k: [m for m in v if hits(m)] for k, v in groups.items()}
        print(f"Filtered to titles reaching {display_sid(sid)}. A title can omit a section it changes.")
    print(f"Ordinances since {since}, from the Legistar API, checked {dt.date.today().isoformat()}.\n")

    def show(label, ms, links=False):
        print(f"{label}: {len(ms)}")
        for m in ms:
            print(f"  {m.get('MatterEnactmentNumber') or 'no number'} | {(m.get('MatterPassedDate') or '')[:10] or 'not passed'} | "
                  f"{m['MatterFile']} | {m.get('MatterStatusName')} | {' '.join((m.get('MatterTitle') or '').split())[:200]}")
            print(f"    {WEB}{m['MatterId']}")
            if links:
                try:
                    atts = api(f"matters/{m['MatterId']}/attachments")
                    final = [x for x in atts if re.search(r"final\s+ord", x.get("MatterAttachmentName") or "", re.I)]
                    for att in final or atts:
                        print(f"    {att.get('MatterAttachmentName')}: {attachment_url(att)}")
                except Exception as e:
                    print(f"    attachments could not be read: {e}")
        print()

    show("Enacted text amendments (signed ordinance is the authority)", groups["text"], a.links)
    show("Marked Enacted with no enactment number (unconfirmed; check the matter history)", groups["unconfirmed"], a.links)
    show("Text or map items not enacted (pending, postponed or failed)", groups["pending"])
    if a.all:
        show("Enacted rezonings (map changes, not code text)", groups["map"])
        show("Other ordinances, not amending the code by title", groups["other"])
    else:
        print(f"Not listed: {len(groups['map'])} enacted rezonings and {len(groups['other'])} other ordinances; use --all.")
    return 0


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)

    b = sub.add_parser("build")
    b.add_argument("pdf")
    b.add_argument("--supplement")
    b.add_argument("--through")
    b.add_argument("--through-date")
    b.set_defaults(fn=cmd_build)

    i = sub.add_parser("info")
    i.set_defaults(fn=cmd_info)

    s = sub.add_parser("search")
    s.add_argument("terms")
    s.add_argument("--chapter", help="a chapter number, A, C, charter or index")
    s.add_argument("--limit", type=int, default=25)
    s.add_argument("--no-legistar", action="store_true")
    s.set_defaults(fn=cmd_search)

    g = sub.add_parser("get")
    g.add_argument("section")
    g.add_argument("--page", type=int)
    g.add_argument("--max-chars", type=int, default=12000)
    g.add_argument("--no-legistar", action="store_true")
    g.set_defaults(fn=cmd_get)

    n = sub.add_parser("since")
    n.add_argument("--section")
    n.add_argument("--since", help="YYYY-MM-DD; defaults to the index's through date")
    n.add_argument("--links", action="store_true", help="also list attachment links; one request per ordinance")
    n.add_argument("--all", action="store_true")
    n.set_defaults(fn=cmd_since)

    for sp in (b, i, s, g, n):
        sp.add_argument("--dir", help="index directory; defaults to $SCP_CIVICS_DATA/ordinances")
    a = p.parse_args()
    return a.fn(a)


if __name__ == "__main__":
    sys.exit(main())
