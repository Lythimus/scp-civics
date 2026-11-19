---
name: scp-decisions
description: How the St. Charles Parish, Louisiana Parish Council has actually decided, across meetings. Lists every rezoning ordinance since 1999, or every matter on a topic, with the Planning & Zoning staff and Commission recommendations, the Council result read from the matter's history (not its status label), the vote count and who voted no or was absent. Also one member's rezoning votes, one matter's full history with movers and roll calls, and the past rezonings closest to a pending one. Use for precedent before a hearing ("the last M-2 rezonings and how each member voted"), how often the Council overrides a Commission denial, how a member votes on industrial rezonings, or what happened to a matter whose Legistar status looks wrong.
argument-hint: "<district, place, topic, member or matter file number>"
allowed-tools: Bash, Read, Write, Grep, Glob, Skill
---

# St. Charles Parish decisions

```bash
D="${CLAUDE_PLUGIN_ROOT}/skills/scp-decisions/scripts/decisions.py"
```

The script reads Legistar's public web API and caches what it reads in `~/.cache/scp-civics/decisions` (`--cache DIR` to move it; never inside the plugin). The first rezoning run reads about 430 matters with their histories and votes and takes about a minute. Later runs reread only matters whose Legistar record has changed. `--refresh` rereads everything, for example if a vote looks missing.

## 1. Pick the question

| Question | Command |
|---|---|
| Past rezonings to a district, from a district, in a place, or in a period | `python3 "$D" rezonings --to M-2` (add `--from C-3`, `--where Luling`, `--since 2015`, `--until 2020`, `--result failed`, `--commission denial`) |
| Every matter on a topic, not only rezonings | `python3 "$D" search --term "data center" [--term ...] [--type Ordinance] [--since 2020]` |
| One matter in full: every action, mover, seconder, roll call, motion text, and where the Commission's roll call is | `python3 "$D" matter 2099-0123` |
| One member's rezoning votes, and where they were on the losing side or didn't vote | `python3 "$D" member <surname> [--to M-] [--since 2020]` |
| The past rezonings closest to a pending one | `python3 "$D" like 2099-0123 [--top 15]` |

District filters take a code (`M-2`, `R-1A(M)`, `O-L`) or a prefix ending in a hyphen (`M-` for every M district, `R-` for every R). `rezonings` and `search` take `--csv FILE` to save the rows in the user's project folder, and `--titles` to print each full title under its row.

Ask the user which period matters. Members, districts and the code itself have changed since 1999, so a 25-year count can mislead where the last ten years would not.

## 2. Read the output

- **Council result** comes from the matter's history: the Council's last decisive action, with later actions overriding earlier ones. Results are adopted, failed, removed from consideration, postponed indefinitely (either of these two can be under Council Rule 8, which lapses a tabled matter with no vote), tabled, vetoed, veto sustained, veto overridden, reopened with no later decision, or no Council decision recorded.
- **Label** is Legistar's status label. It is shown because it can be wrong. A label of "Enacted" with no enactment number, a label that disagrees with the history, and a decision label on a matter whose history records no Council decision are all flagged. On 2026-11-16, 2 of the 431 rezonings were flagged. Before stating the outcome of a flagged matter, read its history (`matter`) and the minutes.
- **Vote** counts yeas and nays on the deciding action, which is not always a vote to adopt. A 9-0 vote on a postponement is nine votes to postpone. *Not yea* names everyone recorded as Nay, Absent, Abstain or Recused, with seat labels dropped. `matter` shows the seats.
- **Staff** and **Commission** are recommendations as Legistar's history labels them: Recommended Approval, Recommended Denial, Recommended Approval w/Stip., Tabled. They aren't votes. Planning Commission member votes aren't in the API. Its roll call is in the signed minutes attached to the Commission's meeting page. `matter` names that meeting when Legistar has it (Commission meetings are on Legistar from January 2025). Get the minutes with `scp-civics:scp-meeting-record` (`documents --event <id>`). For earlier years, the minutes are a records request (`scp-civics:scp-prr`).
- **From → to** and **Where** are parsed from the title. District names sit between codes in recent titles, and older titles drop hyphens ("B1", "OL"). Both are normalized, and "R-1AM" is read as "R-1A(M)". A title with no "from ... to ..." is reported as possibly a text amendment. Where lists only the parish communities the title names, leaving out the "as requested by" part, so a missing community means the title doesn't name one, not that the land is outside every community.
- **Crosstab** counts Commission recommendation against Council result for the rows shown. The cases where the Council went against a denial, or rejected an approval, are where to look in the minutes and recordings.
- **like** ranks by shared target district first, then the original district, community and place words. It compares titles only. A close title doesn't make a close case: check acreage, setting, the record and the reasons given before calling one a precedent.

## 3. What this doesn't cover

- **Coverage starts in 1999,** where Legistar's records begin. Member votes are present from 1999 on.
- **Rezonings are found by title wording.** On 2026-11-16, "zoning classification" and "change of zoning" together found 431 ordinances. A rezoning titled some other way is missed. Run `search` with another phrase if the count looks short.
- **Planning Commission cases that never reached the Council** aren't Council matters, so they aren't here. They are in the Commission's agendas and minutes. `scp-civics:scp-watch` (`calendar --body Planning --term ...`) reads agenda lines for last month through next month. Older Commission agendas and minutes from January 2025 on are on Legistar's meeting pages (`scp-civics:scp-meeting-record`, `documents --event <id>`); earlier ones are a records request.
- **Zoning Board of Adjustment variances** are decided by the board, not the Council, and its results are on the parish's board page.
- **Why** a member voted as they did is in the minutes and the recording (`scp-civics:scp-meeting-record`), not the vote.
- **The API's vote record** can be incomplete for a meeting the clerk hasn't finished. If a decided row shows no member votes, say "no member votes in the API", not "voice vote" or "unanimous".

## 4. Report

Give the question, the filters, the period, and the date the data was read. Lead with the answer (counts, the closest precedents, the pattern) and then the table. Cite each matter by file number with its Legistar link. Keep the Commission recommendation, the Council result and the status label apart, and say where they differ. For a pattern claim ("the Council approves most industrial rezonings the Commission denies"), give the counts and the files behind it. If the counts are small, say so rather than calling it a pattern.

Applicants' names are in the titles. They are public records, but a report for publication names the matter and the place, not a private applicant, unless the user needs the name.

For one pending case's procedure and notice, use `scp-civics:scp-case-check`. For how the process works, use `scp-civics:scp-land-use-process`. This skill researches only. It doesn't contact anyone or file anything.
