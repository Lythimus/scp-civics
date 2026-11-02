"""Numbers in each Markdown table must appear on the source page; words are checked with spaces removed."""
import glob, os, re, subprocess, sys
MD_DIR, PDF_DIR = sys.argv[1], sys.argv[2]
def pdf_for(slug):
    for p in glob.glob(os.path.join(PDF_DIR, "*.pdf")):
        n = os.path.basename(p)
        if "(1)" in n or "Coastal" in n: continue
        if re.sub(r"[^a-z0-9]+", "-", n[:-4].lower()).strip("-") == slug: return p
def page_text(pdf, p):
    return subprocess.run(["pdftotext", "-layout", "-f", str(p), "-l", str(p), pdf, "-"], capture_output=True, text=True).stdout
nums_total = nums_miss = words_total = words_miss = 0
report = []
for md in sorted(glob.glob(os.path.join(MD_DIR, "*.md"))):
    slug = os.path.basename(md)[:-3]; pdf = pdf_for(slug)
    if not pdf: print("NO PDF", slug); continue
    page = None; cells = {}; in_t = False
    for line in open(md).read().split("\n") + ["## Page END"]:
        m = re.match(r"^## Page (\d+)$", line)
        if m: page = int(m.group(1)); in_t = False; continue
        if line.startswith("|---"): in_t = True; continue
        if line.startswith("|") and in_t:
            cells.setdefault(page, []).extend(c.strip() for c in re.split(r"(?<!\\)\|", line.strip("|")))
        else: in_t = False
    for pg, cs in cells.items():
        raw = page_text(pdf, pg)
        squashed = re.sub(r"[^a-z0-9]", "", raw.lower())
        for cell in cs:
            for n in re.findall(r"\d[\d,]*\.?\d*", cell.replace("<br>", " ")):
                nums_total += 1
                if n.rstrip(".") not in raw and n.rstrip(".").replace(",", "") not in raw.replace(",", ""):
                    nums_miss += 1; report.append(f"{slug} p{pg} NUM {n} in {cell[:60]!r}")
            for w in re.findall(r"[A-Za-z]{4,}", cell):
                words_total += 1
                if w.lower() not in squashed:
                    words_miss += 1; report.append(f"{slug} p{pg} WORD {w!r}")
open("check2-report.txt","w").write("\n".join(report)+"\n")
print(f"numbers checked={nums_total} missing={nums_miss}; words checked={words_total} missing={words_miss}")
