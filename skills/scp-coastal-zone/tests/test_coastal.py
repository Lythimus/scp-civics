"""Offline tests for coastal.py: python3 -m unittest discover -s skills/scp-coastal-zone/tests

Agenda fixtures copy the committee's layouts with made-up applicants and permit numbers. No private
applicant from a real agenda belongs here.
"""
import datetime as dt
import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import coastal  # noqa: E402

# 2026-03 layout: dotted outline numbers, codes in parentheses, concern only from the heading.
DOTTED = [
    "4. Manager’s Briefing",
    "4.1. Last Month’s Joint Permit Applications (2 JPAs)",
    "4.1.1.1. P20990001 - Example Pipeline LP (NDSI)",
    "4.1.1.2. P20990002 - Example Parish Works (Exempt)",
    "4.2. JPA open for public comment",
    "4.2.1. State Concerns (1)",
    "4.2.1.1. P20990003 - Example Terminal, LLC – (CUP)",
    "4.2.2. Local Concerns (1)",
    "4.2.2.1. P20990004 - Example Applicant (Returned for additional Info)",
    "4.2.3. Update on recent coastal zone activities in St. Charles Parish",
    "4.2.3.1. Quarterly Report",
]
# 2026-07 layout: lettered outline, (LOCAL)/(STATE) tags, code at the end of a description.
LETTERED = [
    "4. Manager’s Briefing (3 JPAs)",
    "A) JPA open for public comment",
    "1) State Concerns (1)",
    "(a) P20990010 (STATE) EXAMPLE CO. Proposed borings. IN REVIEW",
    "2) Local Concerns (0)",
    "B) Last Month’s Joint Permit Applications with determinations",
    "1) P20990011 (LOCAL) EXAMPLE, APPLICANT fill of lot. RFD EXEMPT",
    "2) P20990012 (STATE) EXAMPLE CO. Maintenance dredging. NDSI",
    "C) Update on recent coastal zone activities in St. Charles Parish",
    "(a) Example project underway P20990099",
]
# 2026-11 layout: one agenda item per permit, description on the next line.
ROMAN = [
    "IV. Manager’s Briefing (2 JPAs)",
    "IV.A. JPA open for public comment",
    "IV.A.1.a. P20990020 Example Utility - Proposed maintenance dredging. NDSI",
    "IV.B. Last Month’s Joint Permit Applications with determinations",
    "IV.B.1. P20990021 (STATE) Example Parish Works CUP",
    "Proposed construction of a floodwall in front of an example pump station.",
    "V. Announcements",
]
# 2025-11 layout: parish SCP numbers with no P-number, no codes.
SCP_ONLY = [
    "4.1. Last Month’s Joint Permit Applications (1 JPAs)",
    "4.1.1. SCP-2099-04 Example Boat Ramp Repair",
    "4.1.2. SCP-2099-05 Example Co P20990030 - EXEMPT",
]


def row(rows, permit):
    return next(r for r in rows if r["permit"] == permit)


class Agenda(unittest.TestCase):
    def test_dotted_layout(self):
        rows = coastal.parse_agenda(DOTTED)
        self.assertEqual([r["permit"] for r in rows], ["P20990001", "P20990002", "P20990003", "P20990004"])
        self.assertEqual(row(rows, "P20990001")["section"], "determined")
        self.assertEqual(row(rows, "P20990001")["codes"], ["NDSI"])
        self.assertEqual(row(rows, "P20990002")["codes"], ["EXEMPT"])
        self.assertIsNone(row(rows, "P20990002")["concern"])  # no heading or tag in that section
        self.assertEqual(row(rows, "P20990003")["section"], "open")
        self.assertEqual(row(rows, "P20990003")["concern"], "STATE")
        self.assertEqual(row(rows, "P20990004")["concern"], "LOCAL")
        self.assertEqual(row(rows, "P20990004")["codes"], ["RETURNED FOR ADDITIONAL INFO"])

    def test_lettered_layout(self):
        rows = coastal.parse_agenda(LETTERED)
        self.assertEqual([r["permit"] for r in rows], ["P20990010", "P20990011", "P20990012"])  # not the update
        self.assertEqual(row(rows, "P20990010")["codes"], ["IN REVIEW"])
        self.assertEqual(row(rows, "P20990011")["concern"], "LOCAL")
        self.assertEqual(row(rows, "P20990011")["codes"], ["RFD", "EXEMPT"])
        self.assertTrue(row(rows, "P20990011")["text"].startswith("P20990011 (LOCAL)"))

    def test_description_on_next_line(self):
        rows = coastal.parse_agenda(ROMAN)
        self.assertEqual(row(rows, "P20990020")["section"], "open")
        last = row(rows, "P20990021")
        self.assertEqual((last["section"], last["concern"], last["codes"]), ("determined", "STATE", ["CUP"]))
        self.assertIn("floodwall", last["text"])

    def test_scp_numbers(self):
        rows = coastal.parse_agenda(SCP_ONLY)
        self.assertEqual(rows[0]["scp"], "SCP-2099-04")
        self.assertIsNone(rows[0]["permit"])
        self.assertEqual((rows[1]["scp"], rows[1]["permit"], rows[1]["codes"]), ("SCP-2099-05", "P20990030", ["EXEMPT"]))

    def test_code_words_inside_other_words_ignored(self):
        rows = coastal.parse_agenda(["A) JPA open for public comment",
                                     "(a) P20990040 (STATE) EXAMPLE CUPOLA REPAIR, EXEMPTION REQUEST"])
        self.assertEqual(rows[0]["codes"], [])

    def test_strip_number(self):
        for raw, want in (("3.2.1.4. P1 x", "P1 x"), ("IV.B.2.  P1 x", "P1 x"), ("(a) P1 x", "P1 x"),
                          ("1) P1 x", "P1 x"), ("A) JPA open", "JPA open")):
            self.assertEqual(coastal.strip_number(raw), want)

    def test_flatten_orders_items(self):
        items = [{"EventItemAgendaSequence": 2, "EventItemTitle": "b\r\n  c"},
                 {"EventItemAgendaSequence": 1, "EventItemTitle": "a"}, {"EventItemAgendaSequence": 3, "EventItemTitle": None}]
        self.assertEqual(coastal.flatten(items), ["a", "b", "c"])


SQUARE = [[[0, 0], [10, 0], [10, 10], [0, 10], [0, 0]]]
LEFT_HALF = [[[0, 0], [5, 0], [5, 10], [0, 10], [0, 0]]]


class Site(unittest.TestCase):
    def test_wholly_on_high_ground(self):
        samples = coastal.sample_points([[[1, 1], [4, 1], [4, 9], [1, 9], [1, 1]]], grid=4)
        classes = coastal.classify(samples, [{"a": {"ELEVATION": "Above 7 foot"}, "rings": LEFT_HALF}], [])
        self.assertTrue(all(c == "Above 7 foot" for c in classes))
        self.assertIn("may apply", coastal.exemption_screen(classes, is_point=False)[0])

    def test_straddling_footprint_is_not_wholly(self):
        samples = coastal.sample_points([[[2, 2], [8, 2], [8, 8], [2, 8], [2, 2]]], grid=6)
        classes = coastal.classify(samples, [{"a": {"ELEVATION": "5 to 7 foot"}, "rings": LEFT_HALF}], [])
        self.assertTrue(any(classes) and not all(classes))
        text = coastal.exemption_screen(classes, is_point=False)[0]
        self.assertIn("wholly", text)
        self.assertIn("does not appear to apply", text)

    def test_fastland_wins_over_contour(self):
        classes = coastal.classify([(3, 3)], [{"a": {"ELEVATION": "5 to 7 foot"}, "rings": SQUARE}],
                                   [{"a": {"NAME": "X"}, "rings": SQUARE}])
        self.assertEqual(classes, ["fastland"])

    def test_point_always_warns(self):
        lines = coastal.exemption_screen(["fastland"], is_point=True)
        self.assertEqual(len(lines), 2)
        self.assertIn("--geojson", lines[1])
        self.assertIn("does not appear", coastal.exemption_screen([None], is_point=True)[0])

    def test_holes_are_outside(self):
        donut = SQUARE + [[[4, 4], [6, 4], [6, 6], [4, 6], [4, 4]]]
        self.assertFalse(coastal.contains(donut, 5, 5))
        self.assertTrue(coastal.contains(donut, 2, 2))

    def test_read_geojson(self):
        fc = {"type": "FeatureCollection", "features": [
            {"type": "Feature", "geometry": {"type": "Polygon", "coordinates": [[[-90.41, 29.99], [-90.40, 29.99], [-90.40, 30.0], [-90.41, 29.99]]]}},
            {"type": "Feature", "geometry": {"type": "MultiPolygon", "coordinates": [[[[-90.42, 29.98, 3.0], [-90.41, 29.98, 3.0], [-90.41, 29.985, 3.0], [-90.42, 29.98, 3.0]]]]}}]}
        with tempfile.NamedTemporaryFile("w", suffix=".geojson", delete=False) as f:
            json.dump(fc, f)
        rings = coastal.read_geojson(f.name)
        self.assertEqual(len(rings), 2)
        self.assertEqual(rings[1][0], [-90.42, 29.98])  # elevation dropped

    def test_read_geojson_rejects_swapped_axes(self):
        poly = {"type": "Polygon", "coordinates": [[[29.99, -90.41], [29.99, -90.40], [30.0, -90.40], [29.99, -90.41]]]}
        with tempfile.NamedTemporaryFile("w", suffix=".geojson", delete=False) as f:
            json.dump(poly, f)
        with self.assertRaises(ValueError):
            coastal.read_geojson(f.name)


class Permits(unittest.TestCase):
    def test_gather_dedupes_and_keeps_nearest(self):
        feats = [{"attributes": {"CUPNO": "P20990001"}, "geometry": {"x": -90.40, "y": 30.0}},
                 {"attributes": {"CUPNO": "P20990001"}, "geometry": {"x": -90.41, "y": 30.0}},
                 {"attributes": {"CUPNO": " "}, "geometry": {"x": -90.41, "y": 30.0}}]
        rows = coastal.gather_permits(feats, "point", -90.41, 30.0)
        self.assertEqual(list(rows), ["P20990001"])
        self.assertLess(rows["P20990001"]["metres"], 1)

    def test_merge_across_layers(self):
        a = coastal.gather_permits([{"attributes": {"CUPNO": "P20990002", "ACRES": 2.5},
                                     "geometry": {"rings": SQUARE}}], "polygon", 5, 5)
        b = coastal.gather_permits([{"attributes": {"DOCNO": "P20990002", "COMPANY": "Example Co"},
                                     "geometry": {"paths": [[[20, 20], [30, 30]]]}}], "line", 5, 5)
        m = coastal.merge(a, b)["P20990002"]
        self.assertEqual((m["kinds"], m["metres"], m["acres"], m["company"]), ({"polygon", "line"}, 0.0, 2.5, "Example Co"))

    def test_permit_year(self):
        self.assertEqual(coastal.permit_year("P20260816"), 2026)
        self.assertIsNone(coastal.permit_year("SCP-2026-01"))


class Clock(unittest.TestCase):
    def test_periods_from_notice(self):
        rows = coastal.clock_rows({"notice": dt.date(2026, 11, 12)}, {})
        due = {label: d for label, d, _, _ in rows}
        self.assertEqual(due["Public comment period ends (local concern)"], dt.date(2026, 12, 7))
        self.assertEqual(due["Parish decision due, if no hearing is held"], dt.date(2026, 12, 12))
        self.assertNotIn("Administrative appeal due", due)

    def test_weekend_and_holiday_flagged_not_moved(self):
        holidays = {dt.date(2026, 12, 25): "Christmas Day"}
        rows = coastal.clock_rows({"decision": dt.date(2026, 12, 10)}, holidays)
        appeal = next(r for r in rows if r[0] == "Administrative appeal due")
        self.assertEqual(appeal[1], dt.date(2026, 12, 25))
        self.assertIn("Christmas Day", appeal[3])
        self.assertIn("2026-12-28", appeal[3])

    def test_after_the_fact(self):
        rows = coastal.clock_rows({"activity": dt.date(2026, 3, 2)}, {})
        self.assertEqual([(r[0], r[1]) for r in rows], [("After-the-fact permit request due", dt.date(2026, 3, 17))])


class Cache(unittest.TestCase):
    def test_refuses_plugin_folder(self):
        with self.assertRaises(SystemExit):
            coastal.Cache(coastal.SKILLS / "scp-coastal-zone" / "cache")

    def test_reuses_value(self):
        with tempfile.TemporaryDirectory() as d:
            c = coastal.Cache(d)
            self.assertEqual(c.get("k", lambda: [1]), [1])
            self.assertEqual(c.get("k", lambda: [2]), [1])
            self.assertEqual(coastal.Cache(d, refresh=True).get("k", lambda: [3]), [3])


if __name__ == "__main__":
    unittest.main()
