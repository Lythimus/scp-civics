"""Offline tests for econdev.py: python3 -m pytest skills/scp-economic-development/tests (or run this file).

Fixtures are synthetic and shaped like the sources' text layers; nothing is fetched.
"""
import argparse
import contextlib
import importlib.util
import io
import pathlib
import unittest

SCRIPT = pathlib.Path(__file__).resolve().parents[1] / "scripts" / "econdev.py"
spec = importlib.util.spec_from_file_location("econdev", SCRIPT)
ed = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ed)

# Two pages of an act in pdftotext -layout form: numbered lines, a running head, and a footer that
# closes each page. The second St. Charles item straddles the page break.
ACT = """
     HB NO. 2                                                               ENROLLED
40   07/274     PUBLIC IMPROVEMENTS
41   (500001) River Deepening, Planning and Construction
42            (Ascension, Jefferson, St. Charles,
43            St. James)
44            Payable from General Obligation Bonds
45                Priority 1                                               $    55,500,000
46                Priority 5                                               $    25,000,000
47            Total                                                        $    80,500,000
48   50/J45     ST. CHARLES PARISH
49   (500002) Canal Sheet Pile, Planning and Construction
50            (St. Charles)
                                     Page 7 of 9
     HB NO. 2                                                               ENROLLED
 1            Payable from General Obligation Bonds
 2                Priority 5                                               $     3,250,000
 3   (500003) Street Drainage Improvements, Planning and
 4            Construction
 5            (St. Charles)
 6            Payable from General Obligation Bonds
 7                Priority 5                                           $      4,000,000
 8            Payable from State General Fund (Direct) Non-Recurring
 9            Revenues                                                 $        450,000
10            Total                                                    $      4,450,000
11   50/J47     ST. JAMES PARISH
12   (500004) Road Rehabilitation, Planning and Construction
13            (St. James)
14            Payable from General Obligation Bonds
15                Priority 1                                            $      745,362
                                     Page 8 of 9
"""

VETO = """
RE: Line Item Vetoes in House Bill No. 2
Veto No. 1:         Delete Lines 3 through 10 on Page 8 of 9
Veto No. 2       Delete Lines 1-2 on Page 8 of 9
"""


class OutlayParse(unittest.TestCase):
    def setUp(self):
        self.items = {i["project"]: i for i in ed.parse_items(ACT)}

    def test_every_item_and_agency(self):
        self.assertEqual(set(self.items), {"500001", "500002", "500003", "500004"})
        self.assertEqual(self.items["500002"]["agency_code"], "50/J45")
        self.assertEqual(self.items["500001"]["agency"], "PUBLIC IMPROVEMENTS")

    def test_item_carried_across_page_break(self):
        it = self.items["500002"]
        self.assertEqual(it["positions"][0], (7, 49))
        self.assertIn((8, 2), it["positions"])
        self.assertEqual(it["total"], 3_250_000)
        self.assertEqual(it["funding"][-1], "Priority 5  $3,250,000")

    def test_multi_line_title_and_location(self):
        self.assertEqual(self.items["500003"]["title"], "Street Drainage Improvements, Planning and Construction")
        self.assertEqual(self.items["500001"]["location"], "Ascension, Jefferson, St. Charles, St. James")

    def test_total_line_wins_over_sum(self):
        self.assertEqual(self.items["500001"]["total"], 80_500_000)
        self.assertEqual(self.items["500003"]["total"], 4_450_000)

    def test_parish_filter(self):
        kept = {i["project"] for i in self.items.values() if ed.in_parish(i)}
        self.assertEqual(kept, {"500001", "500002", "500003"})

    def test_vetoes(self):
        v = ed.parse_vetoes(VETO)
        self.assertEqual(v, {8: [(3, 10), (1, 2)]})
        self.assertEqual(ed.veto_status(self.items["500003"], v), "VETOED")
        # Only the funding lines on page 8 fall in the second range; the header is on page 7.
        self.assertTrue(ed.veto_status(self.items["500002"], v).startswith("PARTLY"))
        self.assertEqual(ed.veto_status(self.items["500001"], v), "")

    def test_three_digit_project_numbers(self):
        old = "33   50/J45     ST. CHARLES PARISH\n34   (311)      Bulkhead, Planning\n35              (St. Charles)\n" \
              "36              Payable from General Obligation Bonds\n37                  Priority 1      $   150,000\n" \
              "                     Page 70 of 161\n"
        items = ed.parse_items(old)
        self.assertEqual([(i["project"], i["total"]) for i in items], [("311", 150_000)])


class CouncilTitles(unittest.TestCase):
    def test_acronyms_need_whole_word_and_case(self):
        rx = ed.term_regex("EDA")
        self.assertTrue(rx.search("application to the EDA Disaster Supplemental"))
        self.assertFalse(rx.search("Lease with Veda Jackson"))
        self.assertFalse(ed.term_regex("LED").search("Report Filed"))
        self.assertTrue(ed.term_regex("pump station").search("Turtle Pond Pump Station Upgrades"))

    def test_kinds(self):
        self.assertEqual(ed.kinds_of("A resolution supporting the application to the U.S. Economic Development "
                                     "Administration's FY2025 EDA Disaster Supplemental"), ["grant"])
        self.assertEqual(ed.kinds_of("Cooperative Endeavor Agreement between the State of Louisiana and St. Charles "
                                     "Parish (Facility Planning and Control Project No. 50-J45-25-02)"), ["state", "cea"])
        self.assertEqual(ed.kinds_of("An ordinance creating the Highway 90 Economic Development District No. 1"),
                         ["district"])

    def test_format_pulls_fpc_number_and_amounts(self):
        row = {"MatterId": 1, "MatterFile": "2025-0001", "MatterIntroDate": "2025-09-22T00:00:00",
               "MatterTypeName": "Resolution", "MatterStatusName": "Approved", "MatterEnactmentNumber": "6860",
               "MatterTitle": "Agreement for $1,000,000.00 (Facility Planning and Control Project No. 50-J45-25-02)."}
        line = ed.format_matter(row)
        self.assertIn("FP&C 50-J45-25-02", line)
        self.assertIn("$1,000,000.00", line)
        self.assertIn("gateway.aspx?M=L&ID=1", line)


class EdcPages(unittest.TestCase):
    PACKET = ("ECONOMIC DEVELOPMENT COUNCIL MEETING\nAGENDA\nII. Monthly Report\n"
              "\fMonthly Statistical Report\nSt. Charles Properties (Land & Buildings) - 2\n"
              "\fThe money comes through FastSites, a state initiative\n"
              "\fofficials said the FastSites award will extend the road\n")
    MINUTES = ("Economic Development Monthly Report\n- FastSites update given.\n"
               "\fSummary\nThe meeting discussed FastSites and other items.\n")

    def test_reprints_tagged_in_packets_only(self):
        hits = ed.page_hits(self.PACKET, ["FastSites"], packet=True)
        self.assertEqual([(p, t) for p, _, t in hits], [(3, "reprinted article"), (4, "reprinted article")])
        hits = ed.page_hits(self.PACKET, ["FastSites"], packet=False)
        self.assertEqual({t for _, _, t in hits}, {""})

    def test_posted_summary_tagged(self):
        hits = ed.page_hits(self.MINUTES, ["FastSites"])
        self.assertEqual([(p, t) for p, _, t in hits], [(1, ""), (2, "posted summary, not verbatim")])

    def test_term_without_dir_is_refused_before_any_fetch(self):
        args = argparse.Namespace(term=["FastSites"], dir=None, since=None)
        with contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit) as cm:
            ed.cmd_edc(args)
        self.assertEqual(cm.exception.code, 2)

    def test_search_outcome(self):
        self.assertEqual(ed.search_outcome(None, False, [])[0], 0)
        self.assertEqual(ed.search_outcome(["x"], False, [])[0], 1)
        code, note = ed.search_outcome(["x"], False, ["2026-03-18_Agenda.pdf"])
        self.assertEqual(code, 2)
        self.assertIn("weren't searched", note)
        code, note = ed.search_outcome(["x"], True, ["2026-03-18_Agenda.pdf"])
        self.assertEqual(code, 0)
        self.assertIn("2026-03-18_Agenda.pdf", note)

    def test_boilerplate_items(self):
        for t in ["I. Call to Order Chairman", "VII. Adjourn", "VI. Next Meeting Date - May 20, 2026", "V. Other Business"]:
            self.assertTrue(ed.BOILERPLATE.match(t), t)
        self.assertFalse(ed.BOILERPLATE.match("V. Other Business Nomination and vote for representative"))
        self.assertFalse(ed.BOILERPLATE.match("III. Guest Speaker Topic: Site readiness"))


class FederalRows(unittest.TestCase):
    def test_dedupe_repeated_reports(self):
        row = {"Sub-Award ID": "X1", "Sub-Awardee Name": "ST CHARLES PARISH", "Sub-Award Amount": 100.0,
               "Sub-Award Date": "2010-09-01", "Prime Recipient Name": "STATE AGENCY", "Awarding Agency": "FEMA",
               "Sub-Award Description": "PUMP STATION", "Prime Award ID": "P1"}
        rows = [ed.normalize(row, True) for _ in range(3)]
        self.assertEqual(len(ed.dedupe(rows)), 1)
        other = dict(row, **{"Sub-Award Amount": 200.0})
        self.assertEqual(len(ed.dedupe(rows + [ed.normalize(other, True)])), 2)

    def test_prime_normalize(self):
        row = {"Award ID": "A1", "Recipient Name": "ST CHARLES PARISH", "Award Amount": 2_000_000.0,
               "Start Date": "2009-12-24", "Awarding Agency": "Department of Commerce",
               "Awarding Sub Agency": "Economic Development Administration", "Description": "RAIL SPUR",
               "CFDA Number": "11.307"}
        n = ed.normalize(row, False)
        self.assertEqual((n["id"], n["via"], n["cfda"]), ("A1", "Economic Development Administration", "11.307"))


class DeckTests(unittest.TestCase):
    def test_text_table_diagram_and_notes(self):
        import tempfile, zipfile
        with tempfile.TemporaryDirectory() as d:
            f = pathlib.Path(d) / "deck.pptx"
            with zipfile.ZipFile(f, "w") as z:
                z.writestr("ppt/slides/slide2.xml", "<p:pic></p:pic><p:pic></p:pic>")
                z.writestr("ppt/slides/slide10.xml", "<a:t>Rank</a:t><a:t>St. Charles &amp; Co</a:t>")
                z.writestr("ppt/slides/_rels/slide2.xml.rels",
                           '<R Target="../diagrams/data1.xml"/><R Target="../notesSlides/notesSlide2.xml"/>')
                z.writestr("ppt/diagrams/data1.xml", "<a:t>~$16.2B*</a:t>")
                z.writestr("ppt/notesSlides/notesSlide2.xml", "<a:t>Ruveon rebrand</a:t><a:t>2</a:t>")
            got = ed.deck_slides(f)
        self.assertEqual([g[0] for g in got], [2, 10])  # numeric, not lexical, order
        self.assertEqual(got[0][2:], (2, ["~$16.2B*"], ["Ruveon rebrand"]))
        self.assertEqual(got[1][1], ["Rank", "St. Charles & Co"])


if __name__ == "__main__":
    unittest.main()
