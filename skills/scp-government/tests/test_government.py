"""Offline tests for government.py: python3 -m unittest discover -s skills/scp-government/tests

Fixtures are made up or public buildings. No resident's address belongs here.
"""
import datetime as dt
import sys
import tempfile
import unittest
from pathlib import Path

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import government as gov  # noqa: E402

C = gov.CENTRAL


def at(y, m, d, hh=18, mm=0):
    return dt.datetime(y, m, d, hh, mm, tzinfo=C)


class Holidays(unittest.TestCase):
    def test_easter(self):
        for year, day in ((2024, (3, 31)), (2025, (4, 20)), (2026, (4, 5)), (2027, (3, 28)), (2038, (4, 25))):
            self.assertEqual(gov.easter(year), dt.date(year, *day))

    def test_floating_days(self):
        days, conditional = gov.legal_holidays(2026)
        self.assertEqual(days[dt.date(2026, 1, 19)], "Dr. Martin Luther King, Jr.'s Birthday")
        self.assertEqual(days[dt.date(2026, 4, 3)], "Good Friday")
        self.assertEqual(days[dt.date(2026, 5, 25)], "National Memorial Day")
        self.assertEqual(days[dt.date(2026, 11, 26)], "Thanksgiving Day")
        self.assertIn(dt.date(2026, 2, 17), conditional)  # Mardi Gras needs a parish ordinance

    def test_observed_days(self):
        days, _ = gov.legal_holidays(2022)  # Christmas 2022 was a Sunday
        self.assertIn(dt.date(2022, 12, 26), days)
        days, conditional = gov.legal_holidays(2026)  # July 4, 2026 is a Saturday
        self.assertNotIn(dt.date(2026, 7, 3), days)
        self.assertIn(dt.date(2026, 7, 3), conditional)

    def test_extra_holiday(self):
        days, _ = gov.holidays_around(dt.date(2026, 3, 1), [dt.date(2026, 2, 17)])
        self.assertIn(dt.date(2026, 2, 17), days)


class Deadline(unittest.TestCase):
    def deadline(self, start, extra=()):
        days, _ = gov.holidays_around(start.date(), extra)
        return gov.notice_deadline(start, days)

    def test_weekday_meeting(self):
        self.assertEqual(self.deadline(at(2026, 10, 27)), at(2026, 10, 26))  # Tue 6 PM -> Mon 6 PM

    def test_monday_skips_weekend(self):
        self.assertEqual(self.deadline(at(2026, 11, 9)), at(2026, 11, 6))  # Mon 6 PM -> Fri 6 PM
        self.assertEqual(self.deadline(at(2026, 11, 9, 12)), at(2026, 11, 6, 12))

    def test_holiday_in_window(self):
        # Thu 11/12/2026 6 PM; Wed 11/11 is Veterans' Day -> Tue 6 PM
        self.assertEqual(self.deadline(at(2026, 11, 12)), at(2026, 11, 10))

    def test_meeting_on_a_holiday(self):
        # Mon 2024-01-08 4 PM is itself a legal holiday, so none of that day counts -> Thu midnight
        self.assertEqual(self.deadline(at(2024, 1, 8, 16)), at(2024, 1, 5, 0))

    def test_given_holiday(self):
        # Wed 2026-02-18 6 PM: Mon 2/16 is Washington's Birthday; with Mardi Gras (Tue 2/17) declared
        # too, the count reaches back to Fri 6 PM
        self.assertEqual(self.deadline(at(2026, 2, 18), [dt.date(2026, 2, 17)]), at(2026, 2, 13))
        self.assertEqual(self.deadline(at(2026, 2, 18)), at(2026, 2, 17))

    def test_saturday_meeting(self):
        self.assertEqual(self.deadline(at(2026, 11, 14, 10)), at(2026, 11, 13, 0))  # Sat -> start of Fri


class Precinct(unittest.TestCase):
    def test_split_school_board(self):
        lines, notes = gov.precinct_report({"name": "1-3", "pj": "1", "sb": "1 | 2", "rep": "57",
                                            "f2023r": 99, "partywin": "X"}, "1")
        self.assertTrue(any("1 | 2" in l for l in lines))
        self.assertTrue(any("split" in n for n in notes))
        self.assertFalse(any("99" in l or "X" in l for l in lines))  # vote totals are never printed

    def test_council_mismatch(self):
        _, notes = gov.precinct_report({"name": "2-1", "pj": "2", "sb": "2"}, "1")
        self.assertTrue(any("precinct record says 2" in n for n in notes))
        _, notes = gov.precinct_report({"name": "2-1", "pj": "2", "sb": "2"}, "2")
        self.assertEqual(notes, [])

    def test_split_values(self):
        self.assertEqual(gov.split_values(" 5 | 6 "), ["5", "6"])
        self.assertEqual(gov.split_values(None), [])


class Roster(unittest.TestCase):
    def test_parse(self):
        text = ("# Officials\n\n## Parish Council\n\n| Name |\n|---|\n| Pat Doe (Dist. 3) |\n"
                "| Sam Roe (Div. A) |\n\n## Planning and Zoning Commission\n\n| Lee Poe (Dist. 9) |\n")
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "officials.md"
            path.write_text(text)
            self.assertEqual(gov.roster_members(path), {"Dist. 3": "Pat Doe", "Div. A": "Sam Roe"})
            self.assertEqual(gov.roster_members(Path(tmp) / "missing.md"), {})


class Small(unittest.TestCase):
    def test_event_start(self):
        e = {"EventDate": "2026-11-09T00:00:00", "EventTime": "6:00 PM"}
        self.assertEqual(gov.event_start(e), at(2026, 11, 9))
        self.assertIsNone(gov.event_start({"EventDate": "2026-11-09T00:00:00", "EventTime": None}))

    def test_utc_to_central(self):
        self.assertEqual(gov.utc_to_central("2026-11-04T16:47:58.093"), at(2026, 11, 4, 10, 47).replace(second=58))
        self.assertEqual(gov.utc_to_central("2026-10-07T13:45:44.037").hour, 8)  # CDT before 11/1
        self.assertIsNone(gov.utc_to_central(None))

    def test_decided_matters(self):
        items = [{"EventItemMatterId": 1, "EventItemPassedFlag": 1, "EventItemActionName": "Amended"},
                 {"EventItemMatterId": 1, "EventItemPassedFlag": 1, "EventItemActionName": "Adopted"},
                 {"EventItemMatterId": 2, "EventItemPassedFlag": 0, "EventItemActionName": "Failed"},
                 {"EventItemMatterId": None, "EventItemPassedFlag": 1, "EventItemActionName": "adjourn"},
                 {"EventItemMatterId": 3, "EventItemPassedFlag": None}]
        self.assertEqual(gov.decided_matters(items), {1, 2})

    def test_squash(self):
        self.assertEqual(gov.squash("Council  Chambers,\n Courthouse"), "Council Chambers, Courthouse")

    def test_district_needs_input(self):
        with self.assertRaises(SystemExit):
            gov.main(["district"])


if __name__ == "__main__":
    unittest.main()
