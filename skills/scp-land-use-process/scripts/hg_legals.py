#!/usr/bin/env python3
"""Herald-Guide legal notices (St. Charles Parish official journal): fetch, OCR, grep.

The weekly legals PDF is image-only (the text layer holds just the masthead), so every
notice has to be OCRed. Issues come out on Thursdays.

  hg_legals.py fetch --from 2026-06-01 --to 2026-10-31 --dir DIR
  hg_legals.py ocr --dir DIR [--dpi 200]      # writes DIR/ocr/<name>.txt, one per issue
  hg_legals.py grep --dir DIR REGEX [REGEX ...]

Stdlib plus poppler (pdftoppm) and tesseract on PATH. A 20-page issue takes a few
minutes to OCR, so run `ocr` in the background for more than a handful of issues.
"""
import argparse, datetime as dt, glob, os, re, subprocess, sys, time, urllib.request

URL = "https://www.heraldguide.com/wp-content/uploads/{y}/{m:02d}/HGLegals_{d}.pdf"


def thursdays(a, b):
    d = a + dt.timedelta(days=(3 - a.weekday()) % 7)
    while d <= b:
        yield d
        d += dt.timedelta(days=7)


def fetch(args):
    os.makedirs(args.dir, exist_ok=True)
    a, b = dt.date.fromisoformat(args.date_from), dt.date.fromisoformat(args.date_to)
    for d in thursdays(a, b):
        name = f"HGLegals_{d:%Y%m%d}.pdf"
        out = os.path.join(args.dir, name)
        if os.path.exists(out) and os.path.getsize(out) > 0:
            continue
        # The upload folder is the month the file was posted, which is occasionally the
        # month before the issue date (an issue on the 1st posted on the 30th).
        prev = d.replace(day=1) - dt.timedelta(days=1)
        for y, m in ((d.year, d.month), (prev.year, prev.month)):
            url = URL.format(y=y, m=m, d=f"{d:%Y%m%d}")
            try:
                req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
                data = urllib.request.urlopen(req, timeout=60).read()
            except Exception:
                continue
            if data[:4] == b"%PDF":
                open(out, "wb").write(data)
                print(f"{name}  {len(data)/1e6:.1f} MB  {url}")
                break
        else:
            print(f"{name}  not found (no issue that week, or a different file name)")
        time.sleep(1)


def ocr(args):
    od = os.path.join(args.dir, "ocr")
    os.makedirs(od, exist_ok=True)
    for pdf in sorted(glob.glob(os.path.join(args.dir, "HGLegals_*.pdf"))):
        base = os.path.splitext(os.path.basename(pdf))[0]
        txt = os.path.join(od, base + ".txt")
        if os.path.exists(txt) and os.path.getsize(txt) > 0:
            continue
        subprocess.run(["pdftoppm", "-r", str(args.dpi), "-png", pdf, os.path.join(od, base)],
                       check=True, stderr=subprocess.DEVNULL)
        pngs = sorted(glob.glob(os.path.join(od, base + "-*.png")),
                      key=lambda p: int(re.search(r"-(\d+)\.png$", p).group(1)))
        parts = []
        for p in pngs:
            n = re.search(r"-(\d+)\.png$", p).group(1)
            t = subprocess.run(["tesseract", p, "stdout", "--psm", "3"],
                               capture_output=True, text=True).stdout
            parts.append(f"=== PAGE {int(n)} [OCR; tesseract {args.dpi} dpi] ===\n{t}")
            os.remove(p)
        open(txt, "w").write("\n".join(parts))
        print(f"{base}: {len(pngs)} pages")


def grep(args):
    rx = re.compile("|".join(args.patterns), re.I)
    for txt in sorted(glob.glob(os.path.join(args.dir, "ocr", "HGLegals_*.txt"))):
        page = "?"
        for line in open(txt, errors="replace"):
            m = re.match(r"=== PAGE (\d+)", line)
            if m:
                page = m.group(1)
                continue
            if rx.search(line):
                print(f"{os.path.basename(txt)[9:17]} p{page}: {line.strip()[:160]}")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sp = ap.add_subparsers(dest="cmd", required=True)
    f = sp.add_parser("fetch"); f.add_argument("--from", dest="date_from", required=True)
    f.add_argument("--to", dest="date_to", default=dt.date.today().isoformat()); f.add_argument("--dir", required=True)
    o = sp.add_parser("ocr"); o.add_argument("--dir", required=True); o.add_argument("--dpi", type=int, default=200)
    g = sp.add_parser("grep"); g.add_argument("--dir", required=True); g.add_argument("patterns", nargs="+")
    a = ap.parse_args()
    {"fetch": fetch, "ocr": ocr, "grep": grep}[a.cmd](a)


if __name__ == "__main__":
    sys.exit(main())
