"""Offline tests for prr_after.py: python3 -m pytest skills/scp-prr/tests (or run this file).

Fixtures are synthetic. PDFs are built with a minimal writer below, so no real production is needed.
"""
import contextlib
import csv
import datetime as dt
import importlib.util
import io
import pathlib
import shutil
import tempfile
import unittest

SCRIPT = pathlib.Path(__file__).resolve().parents[1] / "scripts" / "prr_after.py"
spec = importlib.util.spec_from_file_location("prr_after", SCRIPT)
pa = importlib.util.module_from_spec(spec)
spec.loader.exec_module(pa)

D = dt.date
HAVE_POPPLER = bool(shutil.which("pdfinfo") and shutil.which("pdftotext"))


def make_pdf(path, pages):
    """Write a PDF with one Helvetica text line per page; an empty string makes a page with no text."""
    objs = ["<< /Type /Catalog /Pages 2 0 R >>", None,
            "<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>"]
    kids = []
    for text in pages:
        lines = []
        for line in text.split("\n"):
            safe = line.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
            lines.append(f"({safe}) Tj 0 -12 Td")
        stream = f"BT /F1 10 Tf 40 740 Td {' '.join(lines)} ET" if text else ""
        objs.append(f"<< /Length {len(stream)} >>\nstream\n{stream}\nendstream")
        content = len(objs)
        objs.append(f"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] "
                    f"/Resources << /Font << /F1 3 0 R >> >> /Contents {content} 0 R >>")
        kids.append(f"{len(objs)} 0 R")
    objs[1] = f"<< /Type /Pages /Kids [{' '.join(kids)}] /Count {len(kids)} >>"
    out, offsets = bytearray(b"%PDF-1.4\n"), []
    for n, body in enumerate(objs, 1):
        offsets.append(len(out))
        out += f"{n} 0 obj\n{body}\nendobj\n".encode("latin-1")
    xref = len(out)
    out += f"xref\n0 {len(objs) + 1}\n0000000000 65535 f \n".encode()
    out += "".join(f"{o:010d} 00000 n \n" for o in offsets).encode()
    out += f"trailer\n<< /Size {len(objs) + 1} /Root 1 0 R >>\nstartxref\n{xref}\n%%EOF\n".encode()
    pathlib.Path(path).write_bytes(bytes(out))


def quiet(fn, *args):
    with contextlib.redirect_stdout(io.StringIO()) as out, contextlib.redirect_stderr(io.StringIO()) as err:
        code = fn(*args)
    return code, out.getvalue(), err.getvalue()


class HolidayImport(unittest.TestCase):
    def test_holiday_table_comes_from_scp_government(self):
        self.assertTrue(pa._GOV.exists())
        days, _ = pa.holidays_for(D(2026, 9, 1))
        self.assertEqual(days[D(2026, 9, 7)], "Labor Day")


class BusinessDays(unittest.TestCase):
    def test_labor_day_week(self):
        # Received Wed 9/2/2026; Labor Day Mon 9/7 is skipped, so day 5 is Thu 9/10 and day 3 is Tue 9/8.
        h, _ = pa.holidays_for(D(2026, 9, 2))
        self.assertEqual(pa.add_business_days(D(2026, 9, 2), 5, h), (D(2026, 9, 10), [D(2026, 9, 7)]))
        self.assertEqual(pa.add_business_days(D(2026, 9, 2), 3, h)[0], D(2026, 9, 8))

    def test_count_crosses_new_year(self):
        # 12/30, 12/31, (Fri 1/1 holiday), 1/4, 1/5, 1/6. Needs the next year's holidays loaded.
        h, _ = pa.holidays_for(D(2026, 12, 29))
        end, skipped = pa.add_business_days(D(2026, 12, 29), 5, h)
        self.assertEqual(end, D(2027, 1, 6))
        self.assertIn(D(2027, 1, 1), skipped)

    def test_weekend_start(self):
        h, _ = pa.holidays_for(D(2026, 11, 14))
        self.assertEqual(pa.add_business_days(D(2026, 11, 14), 1, h)[0], D(2026, 11, 16))

    def test_extra_holiday(self):
        h, _ = pa.holidays_for(D(2026, 2, 13), [D(2026, 2, 17)])
        self.assertEqual(pa.add_business_days(D(2026, 2, 13), 1, h)[0], D(2026, 2, 18))  # skips 2/16 and 2/17

    def test_elapsed(self):
        h, _ = pa.holidays_for(D(2026, 9, 2))
        self.assertEqual(pa.business_days_between(D(2026, 9, 2), D(2026, 9, 9), h), 4)

    def test_dates_output_shows_both_starts_for_mail(self):
        a = pa.argparse.Namespace(sent=D(2026, 8, 31), received=D(2026, 9, 2),
                                                       today=None, holiday=[])
        code, out, _ = quiet(pa.cmd_dates, a)
        self.assertEqual(code, 0)
        self.assertIn("from sent Mon 2026-08-31: day 5 is Tue 2026-09-08", out)
        self.assertIn("from received Wed 2026-09-02: day 5 is Thu 2026-09-10", out)

    def test_conditional_holiday_shown_both_ways(self):
        # Mardi Gras 2027 is Tue 2/9; it counts only if the parish declared it.
        a = pa.argparse.Namespace(sent=D(2027, 2, 5), received=None, today=None, holiday=[])
        _, out, _ = quiet(pa.cmd_dates, a)
        self.assertIn("Mardi Gras", out)


class Helpers(unittest.TestCase):
    def test_page_ranges(self):
        self.assertEqual(pa.page_ranges([1, 2, 3, 7, 9, 10]), "1-3, 7, 9-10")

    def test_text_layer_label(self):
        self.assertEqual(pa.text_layer_label(3, []), "yes")
        self.assertEqual(pa.text_layer_label(3, [1, 2, 3]), "no (3 of 3 pp)")
        self.assertEqual(pa.text_layer_label(4, [2, 3]), "partial (no text on p. 2-3)")

    def test_containment_pairs_stamped_copy(self):
        body = " ".join(f"word{i}" for i in range(200))
        rows = [{"file": "a.pdf", "sha256": "1", "_shingles": pa.shingles(body)},
                {"file": "b.pdf", "sha256": "2", "_shingles": pa.shingles("RECEIVED NOV 06 " + body + " more pages")},
                {"file": "c.pdf", "sha256": "3", "_shingles": pa.shingles(" ".join(f"other{i}" for i in range(200)))}]
        found = pa.containment(rows)
        self.assertEqual([(s, b) for s, b, _ in found], [("a.pdf", "b.pdf")])

    def test_ocr_siblings(self):
        with tempfile.TemporaryDirectory() as t:
            t = pathlib.Path(t)
            for n in ("x [1].pdf", "x [1].txt", "x [1].azure.txt", "x [1]-other.txt", "y.txt"):
                (t / n).write_text("")
            self.assertEqual([q.name for q in pa.ocr_siblings(t / "x [1].pdf")], ["x [1].azure.txt", "x [1].txt"])


@unittest.skipUnless(HAVE_POPPLER, "poppler not installed")
class Index(unittest.TestCase):
    def setUp(self):
        self.tmp = pathlib.Path(tempfile.mkdtemp())
        self.src = self.tmp / "download"
        self.src.mkdir()
        minutes = "\n".join(" ".join(f"minute{i}" for i in range(j, j + 8)) for j in range(0, 80, 8))
        make_pdf(self.src / "minutes.pdf", [minutes])
        make_pdf(self.src / "minutes-stamped.pdf", ["RECEIVED " + minutes, "Resolution text " * 5])
        make_pdf(self.src / "statement-Redacted.pdf", ["", "", ""])
        (self.src / "statement-Redacted.txt").write_text("Public Records Exemptions\nPrivacy Information 2\n")
        make_pdf(self.src / "letter.pdf", ["Withheld under La. R.S. 44:4.1; Client Privilege applies."])
        shutil.copy(self.src / "letter.pdf", self.src / "letter (2).pdf")
        (self.src / "thread.msg").write_bytes(b"\xd0\xcf\x11\xe0")
        self.out = self.tmp / "out"

    def tearDown(self):
        shutil.rmtree(self.tmp)

    def run_index(self, *extra):
        return quiet(pa.main, ["index", str(self.src), "--out", str(self.out), *extra])

    def rows(self):
        with open(self.out / "manifest.csv") as f:
            return {r["file"]: r for r in csv.DictReader(f)}

    def test_manifest(self):
        code, out, err = self.run_index()
        self.assertEqual(code, 0, err)
        r = self.rows()
        self.assertNotIn("statement-Redacted.txt", r)  # an OCR copy, not a produced file
        self.assertEqual(r["statement-Redacted.pdf"]["text_layer"], "no (3 of 3 pp)")
        self.assertIn("exemption sheet (in statement-Redacted.txt)", r["statement-Redacted.pdf"]["markers"])
        self.assertIn("'Redacted' in file name", r["statement-Redacted.pdf"]["markers"])
        self.assertIn("R.S. 44 citation (p. 1)", r["letter.pdf"]["markers"])
        self.assertIn("Client Privilege (p. 1)", r["letter.pdf"]["markers"])
        self.assertEqual(r["letter.pdf"]["duplicate_of"], "letter (2).pdf")
        self.assertEqual(r["minutes.pdf"]["pages"], "1")
        self.assertEqual(r["minutes-stamped.pdf"]["pages"], "2")
        self.assertIn("native message", r["thread.msg"]["markers"])
        self.assertEqual(len(r["minutes.pdf"]["sha256"]), 64)
        index = (self.out / "INDEX.md").read_text()
        self.assertIn("minutes.pdf in minutes-stamped.pdf", index)
        self.assertIn("## Against the request", index)

    def test_no_overwrite_without_force(self):
        self.out.mkdir()
        (self.out / "INDEX.md").write_text("hand-written index")
        code, _, err = self.run_index()
        self.assertEqual(code, 2)
        self.assertIn("not overwritten", err)
        self.assertEqual((self.out / "INDEX.md").read_text(), "hand-written index")
        self.assertEqual(self.run_index("--force")[0], 0)

    def test_refuses_plugin_folder(self):
        code, _, err = quiet(pa.main, ["index", str(self.src), "--out", str(pa.PLUGIN_ROOT / "tmp-index")])
        self.assertEqual(code, 2)
        self.assertIn("plugin folder", err)
        self.assertFalse((pa.PLUGIN_ROOT / "tmp-index").exists())

    def test_empty_folder(self):
        empty = self.tmp / "empty"
        empty.mkdir()
        self.assertEqual(quiet(pa.main, ["index", str(empty), "--out", str(self.out)])[0], 1)

    def test_unreadable_pdf_is_not_silent(self):
        (self.src / "broken.pdf").write_bytes(b"not a pdf")
        code, _, err = self.run_index()
        self.assertEqual(code, 2)
        self.assertIn("broken.pdf", err)
        self.assertEqual(self.rows()["broken.pdf"]["text_layer"], "not read")


if __name__ == "__main__":
    unittest.main()
