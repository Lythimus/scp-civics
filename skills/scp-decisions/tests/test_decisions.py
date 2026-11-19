"""Offline tests for decisions.py: python3 skills/scp-decisions/tests/test_decisions.py

Fixtures are made up. No real applicant or case belongs here.
"""
import argparse
import importlib.util
import pathlib
import unittest

SCRIPT = pathlib.Path(__file__).resolve().parents[1] / "scripts" / "decisions.py"
spec = importlib.util.spec_from_file_location("decisions", SCRIPT)
dec = importlib.util.module_from_spec(spec)
spec.loader.exec_module(dec)

_ids = iter(range(1, 10_000))


def h(body, name, flag=None, date="2099-01-01", event=None, seq=0):
    return {"MatterHistoryId": next(_ids), "MatterHistoryActionBodyName": body, "MatterHistoryActionName": name,
            "MatterHistoryPassedFlagName": flag, "MatterHistoryActionDate": date + "T18:00:00",
            "MatterHistoryEventId": event if event is not None else (1 if flag else None),
            "MatterHistoryMinutesSequence": seq}


C, P, PC, ST = dec.COUNCIL, dec.PRESIDENT, dec.COMMISSION, dec.STAFF


class Result(unittest.TestCase):
    def test_adopted_and_failed(self):
        self.assertEqual(dec.council_result([h(C, "Approved 1", "Pass")])[0], "adopted")
        self.assertEqual(dec.council_result([h(C, "Approved 1", "Fail"), h(C, "Failed", seq=2)])[0], "failed")

    def test_voted_row_stays_deciding_when_clerk_repeats_it(self):
        voted = h(C, "Postponed Indefinitely", "Pass", seq=1)
        result, row = dec.council_result([voted, h(C, "Postponed Indefinitely", seq=2)])
        self.assertEqual(result, "postponed indefinitely")
        self.assertIs(row, voted)
        failed = h(C, "Approved 1", "Fail", seq=1)
        self.assertIs(dec.council_result([failed, h(C, "Failed", seq=2)])[1], failed)

    def test_veto_sequence(self):
        rows = [h(C, "Approved 1", "Pass", "2099-01-01"), h(P, "Vetoed by the Par. Pres.", date="2099-01-08"),
                h(C, "Approved Notwithstanding the Executive's Veto", "Fail", "2099-01-15", seq=1),
                h(C, "Veto Sustained", date="2099-01-15", seq=2)]
        result, row = dec.council_result(rows)
        self.assertEqual(result, "veto sustained")
        self.assertEqual(row["MatterHistoryPassedFlagName"], "Fail")
        rows[2]["MatterHistoryPassedFlagName"] = "Pass"
        self.assertEqual(dec.council_result(rows[:3])[0], "veto overridden")

    def test_reopen_then_decide(self):
        rows = [h(C, "Tabled.", "Pass", "2099-01-01"), h(C, "Removed from the Table 1", "Pass", "2099-02-01"),
                h(C, "Approved 1", "Pass", "2099-02-01", seq=5)]
        self.assertEqual(dec.council_result(rows[:2])[0], "reopened, no later decision recorded")
        self.assertEqual(dec.council_result(rows)[0], "adopted")

    def test_removed_rule_8_and_nothing(self):
        self.assertEqual(dec.council_result([h(C, "Rmv'd from Consid. (Council Rule 8)")])[0],
                         "removed from consideration (Council Rule 8)")
        self.assertEqual(dec.council_result([h(C, "Publish/Scheduled for Public Hearing")])[0],
                         "no Council decision recorded")

    def test_rule_8_postponement_without_vote(self):
        rows = [h(C, "Tabled.", "Pass", "2099-01-01"), h(C, "Remained Tabled", date="2099-01-15"),
                h(C, "Postponed Indefinitely (Council Rule 8)", date="2099-02-01")]
        self.assertEqual(dec.council_result(rows)[0], "postponed indefinitely (Council Rule 8)")

    def test_recommendations(self):
        rows = [h(ST, "Received/Assigned PH"), h(ST, "Recommended  Denial"), h(PC, "Rcmnd'd  Approval w/Stip.")]
        self.assertEqual(dec.recommendation(rows, ST), "Recommended Denial")
        self.assertEqual(dec.recommendation(rows, PC), "Recommended Approval w/Stip.")
        self.assertEqual(dec.recommendation([], PC), "")


class Labels(unittest.TestCase):
    def test_enacted_without_number_and_disagreement(self):
        note = dec.label_note({"MatterStatusName": "Enacted", "MatterEnactmentNumber": None}, "postponed indefinitely")
        self.assertIn("no enactment number", note)
        self.assertIn("disagrees", note)
        self.assertEqual(dec.label_note({"MatterStatusName": "Enacted", "MatterEnactmentNumber": "99-1-1"}, "adopted"), "")
        self.assertEqual(dec.label_note({"MatterStatusName": "Removed (Council Rule 8) ", "MatterEnactmentNumber": None},
                                        "removed from consideration (Council Rule 8)"), "")
        self.assertEqual(dec.label_note({"MatterStatusName": "Postponed (Council Rule 8)", "MatterEnactmentNumber": None},
                                        "postponed indefinitely (Council Rule 8)"), "")

    def test_decision_label_with_no_decision_in_history(self):
        note = dec.label_note({"MatterStatusName": "Failed", "MatterEnactmentNumber": None}, "no Council decision recorded")
        self.assertIn("no Council decision in the history", note)
        self.assertEqual(dec.label_note({"MatterStatusName": "Filed", "MatterEnactmentNumber": None},
                                        "no Council decision recorded"), "")


class Districts(unittest.TestCase):
    def test_names_between_codes(self):
        t = ("An ordinance to change the zoning classification from C-3, Highway Commercial to M-1, Light Manufacturing "
             "and Industry and M-2, Heavy Manufacturing and Industry on property designated as Lots 1 and 2, Example "
             "Tract as requested by Example Co.")
        self.assertEqual(dec.districts(t), (["C-3"], ["M-1", "M-2"]))

    def test_variants_and_multiple_clauses(self):
        t = ("to change of zoning classification from R-1AM to OL at Lot 1A Block F and from R-1A to O-L on Lot 11A "
             "Block H, Example Subdivision, Norco")
        self.assertEqual(dec.districts(t), (["R-1A", "R-1A(M)"], ["O-L"]))
        self.assertEqual(dec.districts("from B1 to B2 on approximately 35 acres"), (["B-1"], ["B-2"]))

    def test_text_amendment_has_none(self):
        self.assertEqual(dec.districts('to add "Sheet metal shops" to the C-2 district'), ([], []))

    def test_place_numbers_and_highways_are_not_codes(self):
        t = "from O-L to M-2 at Sections 52 and 85, T12S R19E, Square 15-A, near I-10 and LA 3127"
        self.assertEqual(dec.districts(t), (["O-L"], ["M-2"]))

    def test_requester_is_not_a_place(self):
        t = "from C-2 to C-3 on Lot 4, Example Acres, Luling as requested by Pat Hahnville Example"
        self.assertEqual(dec.communities(t), ["Luling"])
        self.assertNotIn("pat", dec.place_words(t))


class Filters(unittest.TestCase):
    def row(self, **kw):
        base = {"intro": "2010-01-01", "from": ["C-3"], "to": ["M-1"], "title": "x Luling", "result": "adopted",
                "commission": "Recommended Denial"}
        base.update(kw)
        return base

    def args(self, **kw):
        a = argparse.Namespace(since=None, until=None, to=None, frm=None, where=None, result=None, commission=None)
        for k, v in kw.items():
            setattr(a, k, v)
        return a

    def test_code_prefix_and_exact(self):
        self.assertTrue(dec.keep(self.row(), self.args(to="M-")))
        self.assertTrue(dec.keep(self.row(), self.args(to="m-1")))
        self.assertFalse(dec.keep(self.row(), self.args(to="M-2")))
        self.assertTrue(dec.keep(self.row(to=["R-1A(M)"]), self.args(to="R-1AM")))

    def test_years_result_commission(self):
        self.assertFalse(dec.keep(self.row(), self.args(since=2011)))
        self.assertTrue(dec.keep(self.row(), self.args(until=2010)))
        self.assertTrue(dec.keep(self.row(), self.args(result="adopt", commission="denial")))
        self.assertFalse(dec.keep(self.row(), self.args(commission="none")))
        self.assertTrue(dec.keep(self.row(commission=""), self.args(commission="none")))


class Votes(unittest.TestCase):
    def test_tally_and_seat_label(self):
        votes = [{"VotePersonName": "Pat Example (Dist. 1)", "VoteValueName": "Yea"},
                 {"VotePersonName": "Sam Sample (Div. A)", "VoteValueName": "Nay"},
                 {"VotePersonName": "Lee Test", "VoteValueName": "Absent"}]
        count, others = dec.tally(votes)
        self.assertEqual(count, "1-1")
        self.assertEqual(others, ["Nay: Sam Sample", "Absent: Lee Test"])
        self.assertEqual(dec.person("Pat Example (Dist. 1)"), ("Pat Example", "Dist. 1"))
        self.assertEqual(dec.tally([])[0], "no member votes in API")

    def test_summary_uses_deciding_rows_votes(self):
        decide = h(C, "Approved 1", "Pass")
        rec = {"matter": {"MatterId": 5, "MatterFile": "2099-0001", "MatterIntroDate": "2099-01-01T00:00:00",
                          "MatterTitle": "from C-2 to M-1 on Lot 1, Taft", "MatterStatusName": "Enacted",
                          "MatterEnactmentNumber": "99-1-1"},
               "histories": [h(PC, "Recommended  Approval"), decide],
               "votes": {str(decide["MatterHistoryId"]): [{"VotePersonName": "Pat Example", "VoteValueName": "Yea"}]}}
        s = dec.summarize(rec)
        self.assertEqual((s["result"], s["votes"], s["commission"], s["where"], s["passed"]),
                         ("adopted", "1-0", "Recommended Approval", ["Taft"], True))


class Like(unittest.TestCase):
    def test_target_district_outranks_place(self):
        base = {"to": ["M-2"], "from": ["C-3"], "where": ["Luling"], "title": "from C-3 to M-2 on Lot 1, Example Tract, Luling"}
        same_zone = {"to": ["M-2"], "from": ["O-L"], "where": [], "title": "from O-L to M-2 on Lot 9, Other Tract"}
        same_place = {"to": ["R-2"], "from": ["R-1A"], "where": ["Luling"], "title": "from R-1A to R-2 on Lot 2, Luling"}
        self.assertGreater(dec.similarity(base, same_zone)[0], dec.similarity(base, same_place)[0])


class Guard(unittest.TestCase):
    def test_refuses_plugin_folder(self):
        with self.assertRaises(SystemExit):
            dec.check_path(str(dec.PLUGIN_ROOT / "cache"))


if __name__ == "__main__":
    unittest.main()
