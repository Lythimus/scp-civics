---
name: scp-watch
description: Keep a standing search for a St. Charles Parish, Louisiana project, applicant, place or topic across the Herald-Guide legal notices and Legistar's Parish Council matters, and report only what is new since the last run. The paper can be the earliest public signal, because Legistar's API shows a meeting only once its agenda posts and its matters don't include Planning & Zoning Commission cases. Use when the user wants to watch for a rezoning, plat, variance, coastal use permit, ordinance or hearing, or asks what has appeared since they last checked.
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
python3 "$W" add --dir <watch folder> --term "<term>" --term "<term>" [--since YYYY-MM-DD]
```

`--since` defaults to 42 days back. Run `add` again to extend a watch. A new term also searches the issues already on hand.

## 2. Run it

```bash
python3 "$W" run --dir <watch folder>
```

Use a background run the first time, since OCR takes minutes per issue. Later runs read only new issues. The Herald-Guide comes out on Thursdays, so a weekly run after that is enough. This skill doesn't schedule itself; if the user wants a schedule, they set one up.

`--no-paper` and `--no-legistar` skip a source and the report says so. The report is saved in `reports/`.

## 3. Check what it found

- **New notices:** read each one in the OCR text. Before stating a date, name or number from it, check the page image, since OCR misreads digits:

  ```bash
  pdftoppm -r 150 -png -f <page> -l <page> <watch folder>/HGLegals_<yyyymmdd>.pdf <scratch prefix>
  ```

- **Repeats:** matched to an earlier notice by near-identical OCR text, so confirm the match before counting it as a publication. The threshold is strict, so a true repeat with poor OCR can show up as a new notice. The same case also appears as separate notices when the Commission notice, Council notice and minutes differ.
- **Missing issues and gaps:** report them. Those weeks weren't searched, and the next run retries them.
- **Changed matters:** a Legistar status is a label, not an outcome. "Enacted" with a blank enactment number doesn't establish that anything was enacted, so check the matter's history and the minutes.

## 4. Cover what the script can't see

- **Commission meetings:** read https://stcharlesgov.legistar.com/Calendar.aspx in a browser. The Legistar API lists a Commission meeting only once its agenda posts, and on 2026-11-02 every matter introduced since 2026-08-01 had the body "Parish Council".
- **Agenda items:** run `bayou:parish-council-agendas` with `alerts st-charles --term "<term>"`. It keeps no state, so compare with the last report. Without bayou, search the agendas on the calendar page by hand and say so.
- **Zoning Board of Adjustment:** agendas are on the [parish's board page](https://www.stcharlesparish.gov/departments/planning-and-zoning/zoning-board-of-adjustment), not Legistar. The paper still carries its notices.

## 5. Report

Lead with what is new and what needs attention soon. For each item give the source, issue date and page or Legistar file number. Then list the issues and sources checked. Word a negative as "no hit for <terms> in the issues of <first> to <last>, <gaps>", never "no notice was published".

For a case that turns up, use `scp-civics:scp-case-check`. Its notice audit needs publication dates, which the report's first-seen and repeat dates can start, once checked against the page images. Skills research and draft only. This one doesn't contact anyone or file anything.
