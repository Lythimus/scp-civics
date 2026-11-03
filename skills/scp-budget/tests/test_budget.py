"""Offline tests for budget.py: python3 skills/scp-budget/tests/test_budget.py"""
import importlib.util
import pathlib
import re
import unittest

SCRIPT = pathlib.Path(__file__).resolve().parents[1] / "scripts" / "budget.py"
spec = importlib.util.spec_from_file_location("budget", SCRIPT)
budget = importlib.util.module_from_spec(spec)
spec.loader.exec_module(budget)


def matter(title, intro="2026-07-27"):
    return {"MatterTitle": title, "MatterIntroDate": intro + "T00:00:00"}


SCHEDULE = """                                                                                         2026/
AREA/TAXING DISTRICT/Tax Roll          2023    2024    2025    2026 2025
PARISHWIDE:
General Fund                           3.11    2.92    2.85    2.85    -
Council on Aging                       0.89    0.83    0.83    0.83    -
Council on Aging                               0.69    0.65    0.65    -
Wastewater Facility                    2.16    2.03    2.01    1.99   (0.02)
\f
Mills on the next page                 9.99    9.99    9.99    9.99
"""


class Role(unittest.TestCase):
    def test_adoption_names_the_fiscal_year(self):
        title = "An ordinance to approve and adopt the appropriation of Funds for the Budget for Fiscal Year 2027."
        self.assertEqual(budget.role(matter(title), 2027), "adoption")
        self.assertIsNone(budget.role(matter(title), 2026))

    def test_amendment_belongs_to_the_year_amended_not_the_year_filed(self):
        title = "An ordinance to amend the 2023 Consolidated Operating and Capital Budget to adjust"
        self.assertEqual(budget.role(matter(title, "2024-05-06"), 2023), "amendment")
        self.assertIsNone(budget.role(matter(title, "2024-05-06"), 2024))

    def test_levy_on_one_roll_funds_the_next_budget_year(self):
        title = "An ordinance adopting, setting forth, levying and imposing taxes on all property"
        self.assertEqual(budget.role(matter(title, "2026-07-27"), 2027), "millage levy")
        self.assertIsNone(budget.role(matter(title, "2026-07-27"), 2026))

    def test_excess_levy_is_not_the_annual_levy(self):
        title = "An ordinance setting forth, levying and imposing taxes on all property in excess of the rates"
        self.assertIsNone(budget.role(matter(title, "2026-07-27"), 2027))

    def test_capital_program_covers_each_year_in_its_span(self):
        title = "An ordinance adopting the Road and Bridges Capital Program Budget for fiscal year 2026 through 2028"
        for year in (2026, 2027, 2028):
            self.assertEqual(budget.role(matter(title, "2025-11-17"), year), "capital program")
        self.assertIsNone(budget.role(matter(title, "2025-11-17"), 2029))


class Attachment(unittest.TestCase):
    def test_file_name_avoids_the_dead_hyperlink(self):
        att = {"MatterAttachmentFileName": "a.pdf",
               "MatterAttachmentHyperlink": "https://stcharlesgov.legistar1.com/snohomish/attachments/a.pdf"}
        self.assertEqual(budget.attachment_url(att), "https://stcharlesgov.legistar1.com/stcharlesgov/attachments/a.pdf")


class Schedule(unittest.TestCase):
    def setUp(self):
        self.years, self.rows = budget.parse_schedule(SCHEDULE)

    def test_change_column_header_is_not_a_year(self):
        self.assertEqual(self.years, [2023, 2024, 2025, 2026])

    def test_full_row(self):
        self.assertEqual(self.rows["General Fund"], {2023: "3.11", 2024: "2.92", 2025: "2.85", 2026: "2.85"})

    def test_late_start_row_keeps_cells_in_their_years(self):
        self.assertEqual(self.rows["Council on Aging (2)"], {2024: "0.69", 2025: "0.65", 2026: "0.65"})

    def test_change_cell_is_dropped(self):
        self.assertEqual(self.rows["Wastewater Facility"][2026], "1.99")
        self.assertNotIn("(0.02)", self.rows["Wastewater Facility"].values())

    def test_stops_at_page_break(self):
        self.assertNotIn("Mills on the next page", self.rows)

    def test_no_table(self):
        self.assertEqual(budget.parse_schedule("no table here"), ([], {}))


class Search(unittest.TestCase):
    def test_page_numbers_follow_form_feeds(self):
        text = "first page\n\fsecond\nTurtle Pond Pump Station 4,342\n\fthird\n"
        found = list(budget.search_pages(text, re.compile("turtle pond", re.I)))
        self.assertEqual(found, [(2, ["Turtle Pond Pump Station 4,342"])])

    def test_context_does_not_repeat_a_block(self):
        text = "a\nhit one\nhit two\nb\n"
        found = list(budget.search_pages(text, re.compile("hit"), 1))
        self.assertEqual(len(found), 1)
        self.assertEqual(found[0][1], ["a", "hit one", "hit two"])


if __name__ == "__main__":
    unittest.main()
