"""Build per-document Markdown from MinerU content_list.json output.

Usage: build_md.py <mineru_out_dir> <dest_dir>

Each source PDF produces <dest_dir>/<slug>.md. Images are copied to
<dest_dir>/images/ and referenced relatively. Tables are emitted as
GitHub pipe tables with merged cells expanded, plus a link to the
MinerU table snapshot for visual checking.
"""

import ast
import glob
import json
import os
import re
import shutil
import sys
from html.parser import HTMLParser

MINERU_OUT, DEST = sys.argv[1], sys.argv[2]
IMG_DIR = os.path.join(DEST, "images")
os.makedirs(IMG_DIR, exist_ok=True)


class TableParser(HTMLParser):
    """Collects a <table> into a grid of strings, expanding rowspan/colspan."""

    def __init__(self):
        super().__init__()
        self.rows = []  # list of list of (text, rowspan, colspan)
        self._row = None
        self._cell = None
        self._spans = None

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == "tr":
            self._row = []
        elif tag in ("td", "th"):
            self._cell = []
            self._spans = (int(a.get("rowspan", 1) or 1), int(a.get("colspan", 1) or 1))
        elif tag == "br" and self._cell is not None:
            self._cell.append(" ")

    def handle_endtag(self, tag):
        if tag in ("td", "th") and self._cell is not None:
            text = re.sub(r"\s+", " ", "".join(self._cell)).strip()
            self._row.append((text, self._spans[0], self._spans[1]))
            self._cell = None
        elif tag == "tr" and self._row is not None:
            self.rows.append(self._row)
            self._row = None

    def handle_data(self, data):
        if self._cell is not None:
            self._cell.append(data)


def logical_rows(rows):
    """Group raw HTML rows that a rowspan ties together into one table row.

    MinerU splits a visual row whose name wraps onto two lines into two HTML rows,
    with the price cell spanning both. Joining them restores one row per item, and
    each value appears once instead of being repeated in every covered row.
    Multi-line text in a column is joined with <br>; colspan text sits in its origin
    column only, so no value is duplicated.
    """
    placed = []
    occupied = set()
    for r, row in enumerate(rows):
        c = 0
        for text, rs, cs in row:
            while (r, c) in occupied:
                c += 1
            for dr in range(rs):
                for dc in range(cs):
                    occupied.add((r + dr, c + dc))
            placed.append((r, c, text, rs, cs))
            c += cs

    parent = list(range(len(rows)))

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    for r, _, _, rs, _ in placed:
        for dr in range(1, rs):
            if r + dr < len(rows):
                parent[find(r + dr)] = find(r)

    groups = {}
    for r in range(len(rows)):
        groups.setdefault(find(r), []).append(r)
    width = max((c + cs for _, c, _, _, cs in placed), default=0)
    by_row = {}
    for r, c, text, _, _ in placed:
        by_row.setdefault(r, []).append((c, text))

    out = []
    for root in sorted(groups, key=lambda g: min(groups[g])):
        cells = [""] * width
        pieces = {}
        for r in groups[root]:
            for c, text in by_row.get(r, []):
                if text:
                    pieces.setdefault(c, []).append(text)
        for c, texts in pieces.items():
            cells[c] = "<br>".join(texts)
        out.append(cells)
    return out


def md_table(html):
    p = TableParser()
    p.feed(html)
    grid = logical_rows(p.rows)
    if not grid:
        return ""
    esc = lambda s: s.replace("|", "\\|")
    header = [esc(x) for x in grid[0]]
    lines = ["| " + " | ".join(header) + " |", "|" + "|".join(["---"] * len(header)) + "|"]
    for row in grid[1:]:
        lines.append("| " + " | ".join(esc(x) for x in row) + " |")
    return "\n".join(lines)


def join_caption(value):
    # MinerU stores captions as a list, sometimes already parsed and sometimes as its string repr.
    if isinstance(value, str):
        value = ast.literal_eval(value)
    return " ".join(v for v in value if v)


def heading(level):
    # Pages are ##, so document-level headings start at ###.
    return "#" * min(int(level) + 2, 5)


def build(stem_dir, stem, slug):
    cl_path = glob.glob(os.path.join(stem_dir, "*", "*_content_list.json"))
    if not cl_path:
        print("MISSING content list:", stem)
        return None
    items = json.load(open(cl_path[0]))
    base = os.path.dirname(cl_path[0])
    pages = {}
    for it in items:
        if it["type"] in ("header", "footer", "page_number", "aside_text"):
            continue
        pages.setdefault(int(it["page_idx"]), []).append(it)

    out = [f"# {stem}", "", f"Source: `{stem}.pdf` (St. Charles Parish, Master Drainage Plan). Pages: {max(pages) + 1 if pages else 0}.", ""]
    img_seq = 0
    table_count = 0
    for pidx in sorted(pages):
        out += [f"## Page {pidx + 1}", ""]
        for it in pages[pidx]:
            t = it["type"]
            if t == "text":
                txt = it["text"].strip()
                if not txt:
                    continue
                if it.get("text_level"):
                    out += [f"{heading(it['text_level'])} {txt}", ""]
                else:
                    out += [txt, ""]
            elif t == "table":
                table_count += 1
                cap = join_caption(it["table_caption"]) if it.get("table_caption") and it["table_caption"] != "[]" else ""
                foot = join_caption(it["table_footnote"]) if it.get("table_footnote") and it["table_footnote"] != "[]" else ""
                if cap:
                    out += [f"**Table {table_count}: {cap}**", ""]
                else:
                    out += [f"**Table {table_count}**", ""]
                md = md_table(it.get("table_body", ""))
                out += [md if md else "_(table body not recovered; see snapshot)_", ""]
                if foot:
                    out += [f"_{foot}_", ""]
                if it.get("img_path"):
                    snap_src = os.path.join(base, it["img_path"])
                    snap_name = f"{slug}-p{pidx + 1:02d}-table{table_count}-snapshot.jpg"
                    if os.path.exists(snap_src):
                        shutil.copy(snap_src, os.path.join(IMG_DIR, snap_name))
                        out += [f"Table snapshot (for checking): ![{slug} page {pidx + 1} table {table_count}](images/{snap_name})", ""]
            elif t == "image":
                img_seq += 1
                src = os.path.join(base, it["img_path"])
                name = f"{slug}-p{pidx + 1:02d}-fig{img_seq}.jpg"
                if os.path.exists(src):
                    shutil.copy(src, os.path.join(IMG_DIR, name))
                cap = join_caption(it["image_caption"]) if it.get("image_caption") and it["image_caption"] != "[]" else ""
                out += [f"![{cap or 'Figure'}](images/{name})", ""]
                out += [f"> **Figure description:** TODO ({slug} page {pidx + 1}, figure {img_seq})", ""]
            elif t in ("equation", "list"):
                out += [it.get("text", ""), ""]
    return "\n".join(out).rstrip() + "\n", table_count, img_seq


if __name__ == "__main__":
    summary = []
    for stem_dir in sorted(glob.glob(os.path.join(MINERU_OUT, "*", ""))):
        stem = os.path.basename(os.path.normpath(stem_dir))
        slug = re.sub(r"[^a-z0-9]+", "-", stem.lower()).strip("-")
        result = build(stem_dir, stem, slug)
        if result is None:
            continue
        md, tables, figs = result
        with open(os.path.join(DEST, slug + ".md"), "w") as f:
            f.write(md)
        summary.append((slug, tables, figs, len(md.split())))
    for s in summary:
        print(f"{s[0]:45} tables={s[1]:2} figures={s[2]:3} words={s[3]}")
