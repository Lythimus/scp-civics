"""Offline tests for watch.py: python3 skills/scp-watch/tests/test_watch.py

Fixtures are made up. No real applicant, case or watch belongs here.
"""
import datetime as dt
import importlib.util
import pathlib
import unittest
from unittest import mock

SCRIPT = pathlib.Path(__file__).resolve().parents[1] / "scripts" / "watch.py"
spec = importlib.util.spec_from_file_location("watch", SCRIPT)
watch = importlib.util.module_from_spec(spec)
spec.loader.exec_module(watch)


def row_html(body, date, time="6:00 PM", location="Council Chambers, Courthouse", note="",
             viewable=True, agenda=False, minutes=False, ident=1):
    detail = (f'<a id="x_hypMeetingDetail" href="MeetingDetail.aspx?ID={ident}&amp;GUID=G">Meeting&nbsp;details</a>'
              if viewable else '<a id="x_hypMeetingDetail" title="Not viewable by the public" class="meeting_NotViewable">Meeting&nbsp;details</a>')
    agenda_link = ('<a id="x_hypAgenda" href="View.ashx?M=A&amp;ID=1">Agenda</a>' if agenda
                   else '<a id="x_hypAgenda" class="meetingAgendaNotAvailbleLink">Not&nbsp;available</a>')
    minutes_link = ('<a id="x_hypMinutes" href="View.ashx?M=M&amp;ID=1">Minutes</a>' if minutes
                    else '<a id="x_hypMinutes" class="otherNotAvaiableMinutes">Not&nbsp;available</a>')
    return (f'<tr class="rgRow" id="r{ident}"><td><a id="x_hypBody" href="D.aspx">{body}</a></td>'
            f'<td class="rgSorted">{date}</td><td><span>ical</span></td><td><span>{time}</span></td>'
            f'<td>{location}<br /><em>{note}</em></td><td>{detail}</td><td>{agenda_link}</td>'
            f'<td><span>packet</span></td><td>{minutes_link}</td><td>video</td></tr>')


def page(*rows, claimed=None):
    count = len(rows) if claimed is None else claimed
    return f'<html><span class="rmText">{count} records</span><table>{"".join(rows)}</table></html>'


class Paper(unittest.TestCase):
    def test_terms_match_across_line_breaks(self):
        rx = watch.compile_terms(["Sample Creek Road"])
        blocks = watch.find_blocks("notice for 12 Sample\nCreek   Road in the parish", rx)
        self.assertEqual(len(blocks), 1)

    def test_nearby_hits_merge_into_one_notice(self):
        rx = watch.compile_terms(["alpha", "beta"])
        text = "alpha " + "x" * 50 + " beta" + " y" * 400 + " alpha"
        self.assertEqual(len(watch.find_blocks(text, rx)), 2)

    def test_publish_line_needs_a_colon_not_the_word_published(self):
        rx = watch.compile_terms(["alpha"])
        self.assertEqual(watch.find_blocks("alpha was Published widely", rx)[0]["publish"], "")
        self.assertEqual(watch.find_blocks("alpha notice\nPUBLISH: 1/2, 1/9", rx)[0]["publish"], "1/2, 1/9")

    def test_repeat_needs_near_identical_text_and_another_issue(self):
        notices = [{"text": "notice of hearing on case 2099-1-R for lot 4", "issues": ["2099-01-01"]}]
        self.assertIsNotNone(watch.match_notice(notices, "notice of hearing on case 2099-1-R for lot 4", "2099-01-08"))
        self.assertIsNone(watch.match_notice(notices, "notice of hearing on case 2099-1-R for lot 4", "2099-01-01"))
        self.assertIsNone(watch.match_notice(notices, "minutes approving case 2099-1-R for lot 4 and lot 9", "2099-01-08"))


class Matters(unittest.TestCase):
    def matter(self, status):
        return {"MatterId": 7, "MatterFile": "2099-0001", "MatterTypeName": "Ordinance", "MatterStatusName": status,
                "MatterAgendaDate": None, "MatterPassedDate": None, "MatterEnactmentNumber": None, "MatterTitle": "t"}

    def test_new_then_changed(self):
        new, changed, snap = watch.diff_matters({"t": [self.matter("Introduced")]}, {})
        self.assertEqual((len(new), len(changed)), (1, 0))
        new, changed, snap = watch.diff_matters({"t": [self.matter("Enacted")]}, snap)
        self.assertEqual((len(new), len(changed)), (0, 1))
        self.assertEqual(changed[0]["fields"]["MatterStatusName"], ("Introduced", "Enacted"))


class CalendarParse(unittest.TestCase):
    def test_parses_fields_and_count(self):
        rows, claimed = watch.parse_calendar(page(
            row_html("SCP Example Board ", "12/3/2099", viewable=False),
            row_html("Example Council", "12/7/2099", note="Meeting Cancelled on 12/1/2099", agenda=True, minutes=True)))
        self.assertEqual(claimed, 2)
        first, second = rows
        self.assertEqual(first["body"], "SCP Example Board")
        self.assertEqual(first["date"], "2099-12-03")
        self.assertFalse(first["viewable"])
        self.assertEqual(first["url"], "")
        self.assertEqual(second["note"], "Meeting Cancelled on 12/1/2099")
        self.assertEqual(second["location"], "Council Chambers, Courthouse")
        self.assertTrue(second["agenda"] and second["minutes"])

    def test_bookings_kept_only_when_they_say_something(self):
        booking = {"body": "SCP General Chamber Booking", "note": "HOLIDAY - COURTHOUSE CLOSED ALL DAY"}
        self.assertFalse(watch.wanted(booking, []))
        booking["note"] = "Alternate date for SCP Example Committee"
        self.assertTrue(watch.wanted(booking, []))
        self.assertTrue(watch.wanted(booking, ["example committee"]))
        self.assertFalse(watch.wanted({"body": "Example Council", "note": ""}, ["example committee"]))

    def test_body_filter_matches_short_forms_in_notes(self):
        booking = {"body": "SCP General Chamber Booking", "note": "Meeting Cancelled - P&Z Department"}
        self.assertTrue(watch.wanted(booking, ["Planning"]))
        self.assertFalse(watch.wanted(booking, ["Coastal"]))

    def test_repeated_body_and_date_get_their_own_keys(self):
        rows = [{"body": "B", "date": "2099-01-01", "time": "9:00 AM"}, {"body": "B", "date": "2099-01-01", "time": "1:00 PM"}]
        self.assertEqual(sorted(watch.key_rows(rows)), ["B|2099-01-01", "B|2099-01-01#2"])

    def test_month_bounds(self):
        self.assertEqual(watch.month_bounds(dt.date(2099, 1, 15)), (dt.date(2098, 12, 1), dt.date(2099, 2, 28)))
        self.assertEqual(watch.month_bounds(dt.date(2099, 11, 30)), (dt.date(2099, 10, 1), dt.date(2099, 12, 31)))


class Agendas(unittest.TestCase):
    def test_headings_only_counts_zero(self):
        items = [{"EventItemTitle": t} for t in ("CALL TO ORDER", "PLEDGE OF ALLEGIANCE", "UNFINISHED BUSINESS",
                                                 "NEW BUSINESS", "MINUTES - January 1, 2099", "ADJOURN",
                                                 "I. Call to Order Pat Example, Chairman", "VII. Adjourn", None)]
        self.assertEqual(watch.business_items(items), [])

    def test_case_and_matter_lines_count(self):
        items = [{"EventItemTitle": "2099-1-R requested by Example Co. for a change of zoning"},
                 {"EventItemTitle": "RESOLUTIONS", "EventItemMatterId": 5}]
        self.assertEqual(len(watch.business_items(items)), 2)


class CalendarDiff(unittest.TestCase):
    TODAY = dt.date(2099, 11, 16)

    def run_scan(self, rows, snapshot, events=(), items=()):
        with mock.patch.object(watch, "fetch_calendar", side_effect=[page(*rows), page(), page()]), \
             mock.patch.object(watch, "api_events", return_value=list(events)), \
             mock.patch.object(watch, "event_items", return_value=list(items)):
            return watch.scan_calendar([], watch.compile_terms(["change of zoning"]), snapshot, {}, self.TODAY)

    def test_first_scan_reads_agenda_and_hits(self):
        events = [{"EventId": 9, "EventBodyName": "SCP Example Commission ", "EventDate": "2099-11-05T00:00:00",
                   "EventAgendaLastPublishedUTC": "s1"}]
        items = [{"EventItemTitle": "CALL TO ORDER"}, {"EventItemTitle": "2099-2-R for a change of zoning"}]
        rows, new, changed, gone, gaps, span = self.run_scan(
            [row_html("SCP Example Commission", "11/5/2099", agenda=True)], {}, events, items)
        r = rows["SCP Example Commission|2099-11-05"]
        self.assertEqual((r["business"], len(r["hits"])), (1, 1))
        self.assertEqual(gaps, [])

    def test_changes_and_gone_inside_span_only(self):
        snapshot = {
            "SCP Example Commission|2099-12-03": {"body": "SCP Example Commission", "date": "2099-12-03", "time": "5:00 PM",
                                                  "location": "Council Chambers, Courthouse", "note": "",
                                                  "viewable": False, "agenda": False, "minutes": False},
            "SCP Example Commission|2099-11-20": {"body": "SCP Example Commission", "date": "2099-11-20"},
            "SCP Example Commission|2099-08-20": {"body": "SCP Example Commission", "date": "2099-08-20"},
        }
        rows, new, changed, gone, gaps, span = self.run_scan(
            [row_html("SCP Example Commission", "12/3/2099", viewable=False)], snapshot)
        self.assertEqual(changed[0][1], {"time": ("5:00 PM", "6:00 PM")})
        self.assertEqual([g["date"] for g in gone], ["2099-11-20"])

    def scan_views(self, views, snapshot):
        with mock.patch.object(watch, "fetch_calendar", side_effect=views), \
             mock.patch.object(watch, "api_events", return_value=[]):
            return watch.scan_calendar([], {}, snapshot, {}, self.TODAY)

    SNAP = {"B|2099-11-20": {"body": "B", "date": "2099-11-20"}}

    def test_short_view_alone_suppresses_gone(self):
        rows, new, changed, gone, gaps, span = self.scan_views([page(claimed=150), page(), page()], self.SNAP)
        self.assertTrue(any("claims 150" in g for g in gaps))
        self.assertEqual(gone, [])

    def test_failed_view_alone_suppresses_gone(self):
        rows, new, changed, gone, gaps, span = self.scan_views([page(), OSError("down"), page()], self.SNAP)
        self.assertTrue(any("not read" in g for g in gaps))
        self.assertEqual(gone, [])

    def test_whole_views_report_gone(self):
        rows, new, changed, gone, gaps, span = self.scan_views([page(), page(), page()], self.SNAP)
        self.assertEqual([g["date"] for g in gone], ["2099-11-20"])

    def test_unjoined_agenda_is_a_gap(self):
        rows, new, changed, gone, gaps, span = self.run_scan(
            [row_html("SCP Example Commission", "11/5/2099", agenda=True)], {}, events=[])
        self.assertTrue(any("weren't read" in g for g in gaps))

    def test_status_wording(self):
        r = {"note": "", "viewable": True, "agenda": True, "minutes": False, "business": 0}
        self.assertIn("no business items", watch.meeting_status(r))
        r = {"note": "Meeting Cancelled on 1/1/2099", "viewable": False, "agenda": False, "minutes": False}
        self.assertIn("**note: Meeting Cancelled", watch.meeting_status(r))
        self.assertIn("not public yet", watch.meeting_status(r))


class Guard(unittest.TestCase):
    def test_refuses_plugin_folder(self):
        with self.assertRaises(SystemExit):
            watch.check_dir(str(watch.PLUGIN_ROOT / "skills"))


if __name__ == "__main__":
    unittest.main()
