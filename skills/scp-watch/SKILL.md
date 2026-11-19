---
name: scp-watch
description: Keep a standing search for a St. Charles Parish, Louisiana project, applicant, place or topic across the Herald Guide legal notices, Legistar's Parish Council matters and the Legistar meeting calendar for every parish body (Council and committees, Planning & Zoning Commission, Zoning Board of Adjustment, Industrial Development Board, Coastal Zone Advisory Committee, Economic Development, bid openings and the rest), and report only what is new since the last run. The calendar lists meetings weeks before their agendas are public, shows cancellation notes, and its posted agendas are searched for the terms. Use when the user wants to watch for a rezoning, plat, variance, coastal use permit, ordinance, hearing or meeting, asks what has appeared since they last checked, or asks what parish meetings are coming up.
argument-hint: "<terms to watch, or the watch folder to rerun>"
allowed-tools: Bash, Read, Write, Grep, Glob, Skill, AskUserQuestion
---

# St. Charles Parish watch

```bash
W="${CLAUDE_PLUGIN_ROOT}/skills/scp-watch/scripts/watch.py"
```

## 1. Set up or find the watch

A watch is a folder in the user's project, holding `watch.json`, issue PDFs, OCR text and `reports/`. Look for an existing `watch.json` first. If there's no project folder, ask where to put one. The script refuses a folder inside the plugin, because terms reveal what the user is following.

Choose terms with the user. Terms are plain text, not case-sensitive, and can wrap across OCR lines.

- Use what a notice prints: applicant or company, case number, lot or tract, road, subdivision.
- Prefer distinctive terms. A term like "zoning" matches most issues.
- Add a shorter form of a name that OCR might garble, since one misread letter loses a hit.

```bash
python3 "$W" add --dir <watch folder> --term "<term>" --term "<term>" [--since YYYY-MM-DD] [--body "<body name>"]
```

`--since` defaults to 42 days back. Run `add` again to extend a watch. A new term also searches the issues already on hand. `--body` limits the calendar section to bodies whose name or calendar note contains the text (for example `--body Planning --body "Parish Council"`); without it every body is listed. Short forms in notes count: `Planning` also matches "P&Z", `Coastal` "CZAC", `Industrial` "IDB", `Zoning Board` "ZBA".

For a one-off look at what is scheduled, with no watch folder and nothing saved:

```bash
python3 "$W" calendar [--body "<body name>"] [--term "<term>"]
```

## 2. Run it

```bash
python3 "$W" run --dir <watch folder>
```

Use a background run the first time, since OCR takes minutes per issue. Later runs read only new issues. The Herald Guide comes out on Thursdays, so a weekly run after that is enough. This skill doesn't schedule itself; if the user wants a schedule, they set one up.

`--no-paper`, `--no-legistar` and `--no-calendar` skip a source and the report says so. The report is saved in `reports/`.

## 3. Check what it found

- **New notices:** read each one in the OCR text. Before stating a date, name or number from it, check the page image, since OCR misreads digits:

  ```bash
  pdftoppm -r 150 -png -f <page> -l <page> <watch folder>/HGLegals_<yyyymmdd>.pdf <scratch prefix>
  ```

- **Repeats:** matched to an earlier notice by near-identical OCR text, so confirm the match before counting it as a publication. The threshold is strict, so a true repeat with poor OCR can show up as a new notice. The same case also appears as separate notices when the Commission notice, Council notice and minutes differ.
- **Missing issues and gaps:** report them. Those weeks weren't searched, and the next run retries them.
- **Changed matters:** a Legistar status is a label, not an outcome. "Enacted" with a blank enactment number doesn't establish that anything was enacted, so check the matter's history and the minutes. `scp-civics:scp-decisions` reads the history and member votes.
- **Calendar, coming up:** read from Legistar's public calendar page for last month, this month and next month. Each line gives the body, date, time, place, the clerk's note and one status:
  - *scheduled; details and agenda not public yet*: the meeting is on the calendar but the clerk hasn't published it. The Legistar API leaves these meetings out entirely, so this page is the earliest place they show.
  - *agenda posted, N items*: N counts agenda lines that aren't standard headings (call to order, minutes, adjourn and the like). It is a rough count.
  - *agenda posted with no business items beyond headings*: the agenda lists nothing to act on. That often means the meeting won't be held or was a formality, but the calendar doesn't say so. Report it as it reads, not as "cancelled", and confirm with the body's staff or the minutes.
  - A note in bold contains "cancel", "postpone" or "resched". The clerk records most cancellations this way ("Meeting Cancelled on <date>", "due to lack of quorum"). Some show on a *General Chamber Booking* row instead, for example "Meeting Cancelled - P&Z Department" or "Alternate date for SCP Coastal Zone Advisory Committee", so those booking rows are kept when their note says something about a body.
- **Agenda items matching the terms:** lines from posted agendas, read through the API by body and date. Agenda attachments and packets aren't searched. A posted agenda the script couldn't match to one API meeting is listed as a gap, so open that meeting page by hand.
- **Calendar changes:** new meetings, a changed time, place, note, publication, agenda or minutes, and meetings no longer listed. A meeting that drops off may have been cancelled, moved or re-entered under another name; the calendar doesn't say which.
- **Calendar gaps:** a view that couldn't be read, or that claims more meetings than were read, is reported, and no meeting is called "no longer listed" on that run.

## 4. Cover what the script can't see

- **Commission cases as matters:** Legistar's matters are Council items. On 2026-11-02 every matter introduced since 2026-08-01 had the body "Parish Council". Commission cases show up only as agenda lines in the calendar section, and in the paper.
- **Agenda attachments and packets:** the calendar section reads agenda lines, not the files. For a meeting that matters, list its files with `scp-civics:scp-meeting-record` (`documents --event <id>`), or `bayou:parish-council-agendas` (`get st-charles ... --what packet`). Without either, open the meeting page from the link in the report.
- **Zoning Board of Adjustment documents:** its meetings are on the Legistar calendar, but its staff reports and results are on the [parish's board page](https://www.stcharlesparish.gov/departments/planning-and-zoning/zoning-board-of-adjustment). The paper still carries its notices.
- **Meetings outside Legistar:** the calendar covers the bodies in Legistar's list (21 on 2026-11-16, counting Council committees, bid openings and chamber bookings). Bodies the Council doesn't run, such as the School Board, the Sheriff, the levee district and the Port, aren't on it.
- **L'Observateur (LaPlace) is not searched.** It is St. John the Baptist Parish's official journal, and the state housing agency's list of official journals gives St. Charles to the Herald Guide. On 2026-11-13 the St. Charles parish filter on louisianapublicnotice.com returned only the Herald Guide's weekly "Legal notices" items for the previous 30 days. Not established: whether a St. Charles applicant ever places a notice there. For a project on the St. John line, search louisianapublicnotice.com by parish and newspaper in a browser. L'Observateur's own notice pages failed on expired TLS certificates on 2026-11-12, so don't count on them.

## 5. Report

Lead with what is new and what needs attention soon: a meeting within two weeks, a new cancellation note, an agenda newly posted with a matching item. For each item give the source, issue date and page, Legistar file number, or meeting date and body. Then list the issues, calendar views and sources checked. Word a negative as "no hit for <terms> in the issues of <first> to <last>, <gaps>", never "no notice was published".

For a case that turns up, use `scp-civics:scp-case-check`. Its notice audit needs publication dates, which the report's first-seen and repeat dates can start, once checked against the page images. Skills research and draft only. This one doesn't contact anyone or file anything.
