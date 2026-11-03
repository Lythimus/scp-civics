---
name: scp-case-check
description: Audit one St. Charles Parish, Louisiana land-use case from its case or ordinance number. Covers the case's path through the Commission and Council, publication dates and notice day counts, the deadline calendar, whether a Future Land Use Map change has a Commission resolution, plat acreage against the drainage study, subdivision waivers, the record's gaps and what to ask staff. Use for a rezoning, preliminary plat, variance or council ordinance when the user wants to know where a case stands, whether its notice and procedure check out, or what is coming up. For how the process works in general, use scp-land-use-process.
argument-hint: "<case or ordinance number, e.g. yyyy-nn-R, yyyy-nn-MAJ or a Legistar file number>"
allowed-tools: Bash, Read, Write, Grep, Glob, WebSearch, WebFetch, Skill, AskUserQuestion
---

# St. Charles Parish case check

Audit one case and write the result to `case-check-<case>.md` in the user's project folder. If the working directory is this plugin, ask where to write it instead. Case findings never go in the plugin.

This is research, not legal advice. A skipped or unexpected step is a question for staff or a lawyer. Never write "defective", "illegal" or "void".

```bash
SK="${CLAUDE_PLUGIN_ROOT}/skills/scp-land-use-process"
HG=$SK/scripts/hg_legals.py
DAYS="${CLAUDE_PLUGIN_ROOT}/skills/scp-case-check/scripts/notice_days.py"
```

Shell state may not carry between calls, so set these in each one that uses them.

Read `$SK/references/code-sections.md` first. It holds the rules this audit applies. Check any section you cite with `scp-civics:scp-ordinances`, which also flags later amendments.

## 1. Find the record

Run `bayou:parish-council-agendas` with `track st-charles "<case>"`. It can take minutes, so use a long timeout or run it in the background. It links a Commission case to its Council ordinance through the applicant name, because the Council title doesn't cite the case number, so confirm that the match is the same land.

Without bayou, search Legislation at https://stcharlesgov.legistar.com by case number, applicant and location, then open each matter's history and attachments. Say the search was by hand.

Read https://stcharlesgov.legistar.com/Calendar.aspx in a browser for scheduled or cancelled meetings, since the API lists a Commission meeting only once its agenda posts. For each Commission meeting, open its meeting page and read the attachments. The staff reports can be in one named "Agenda", not in the one-page agenda file, and bayou's `get --what packet` won't find them. Zoning Board of Adjustment agendas and results are on the parish's board page, not Legistar: https://www.stcharlesparish.gov/departments/planning-and-zoning/zoning-board-of-adjustment.

Save what you use in the project folder: minutes, staff report, plat, drainage study, ordinance and notices. Many attachments are image-only, so check for a text layer, then read the page images or OCR them with `pdftoppm` and `tesseract`, or `bayou:document-ocr`. If a document isn't posted, record the gap and add it to the questions.

The applicant's notices can reveal a linked case, such as a plat filed alongside a rezoning. List it and report its dates, and run a separate check if the user wants one.

## 2. Trace the path

List every step the case type requires, with its date and source, or "not found". Include steps still ahead.

| Case | Steps |
|---|---|
| Rezoning | Commission hearing (App. A Sec. XV), verbatim transcript to the Council (XV.A.2), Council introduction, Council hearing, ordinance and enactment number |
| Major subdivision | Director's approval of the drainage and traffic analyses, Commission hearing (App. C II.E.4), construction approval, Council final approval. Commission decision within 60 days; approval valid 6 months |
| Minor or administrative resubdivision | App. C II.C or II.B |
| Variance | Rejection letter, Board hearing and written findings of fact, one-year expiration, appeal to court (App. A Sec. XIII) |
| Special permit or special exception use | Read App. A Sec. IV with `scp-civics:scp-ordinances`. The reference file doesn't cover these |

A Legistar status is a label, not an outcome. "Enacted" with a blank enactment number means the result isn't established: check the matter's history, then the minutes. If the last action is postponed, withdrawn or failed, report that action and the contradicting status. Commission minutes can stay marked "Draft".

Compare what each stage names: lots, acreage, zoning districts and purpose, across the Commission notices, Commission agenda, Council notices, ordinance and map exhibit. Report each difference in a table, without assuming which one is right.

## 3. Audit the notice

Pull each issue from about six weeks before the hearing through the hearing date, and through the hearing date of any linked case. OCR takes minutes per issue, so run it in the background for several.

```bash
python3 "$HG" fetch --from YYYY-MM-DD --to YYYY-MM-DD --dir <project folder>/notices
python3 "$HG" ocr --dir <project folder>/notices
python3 "$HG" grep --dir <project folder>/notices "<case number>" "<applicant>" "<location>"
```

Search several terms, because OCR garbles text. Read each hit's "PUBLISH:" line and "ALTERNATE DATE:". Count a date only if you found it in that issue; a date in a "PUBLISH:" line for an issue not yet out or not found is only scheduled. If `fetch` finds no issue for a week, report that week as not searched.

Run the count for every hearing, including cancelled or rescheduled ones:

```bash
python3 "$DAYS" --rule rezoning --hearing YYYY-MM-DD --published YYYY-MM-DD YYYY-MM-DD YYYY-MM-DD
```

Rules are `rezoning`, `plat`, `zba`, `council` (R.S. 33:4780.43) and `plan` (R.S. 33:108). A special permit or exception use has no rule here, so report dates only and cite whatever Sec. IV requires.

Report the plain count and how the parish's other recent cases compare, if you have them. A short plain count is a question about how the parish counts days.

The newspaper can't prove the sign or the certified mail. Mark both "not established" unless a dated record shows them, and add them to the questions.

## 4. Build the deadline calendar

For each hearing still ahead, list these dates in order, with the rule behind each. If none is scheduled, say so, then run the dates for the next regular meeting of the body and label them as an assumption. If a notice's alternate date isn't on the calendar, mark that date not established and run its dates too.

- Latest first publication, sign and mailing, from `$DAYS` with only `--rule` and `--hearing`.
- Commission withdrawal: Wednesday noon before the meeting (XV.F.1). Council withdrawal: Thursday noon before the hearing (XV.F.2).
- Written-comment deadline: "ask staff" unless the record states it.
- Latest useful records request. R.S. 44:33(B) sets three days only to certify unavailability, not to produce, so send it now.

If the Commission meeting was cancelled or moved, notices for the old date don't establish notice for the new one. Search for new notices and say whether any were found.

## 5. Check the Future Land Use Map

Skip this for a plat or variance unless the record raises it. Answer each of these from the record:

1. What does staff say the map shows, and did staff find guideline one (XV.D.1) met? Confirm the designation in the plan itself with `scp-civics:scp-comprehensive-plan` (map designation, goals and recommendations kept apart, with page cites; a parcel read off the map is a visual reading). `$SK/references/code-sections.md` says when to read it.
2. Is the change consistent with the map, or does it need an amendment?
3. If it needs one, is there a Commission **resolution** adopting the amendment (R.S. 33:108(C))? Check agendas, minutes and Legistar for a separate item.
4. Did a notice state the amendment's **purpose** at least 10 days ahead (R.S. 33:108(B))? A notice of "a change of zoning" alone doesn't.
5. Does the ordinance instead authorize the department to amend the map, or change the "Future Land Use Designation" in its own title? Quote it, and compare it with the past routes listed in `$SK/references/code-sections.md`.

Report "no resolution found in <sources checked>, <date>", not "no resolution exists". Treat the reading of R.S. 33:108 as an open question, since no case law has been checked and the parish may rely on home-rule authority.

## 6. Compare the plat and drainage study

A rezoning's plat is often a separate case. If neither is in the record, say what was searched, and ask for them from staff or with `scp-civics:scp-prr`. If the case has a plat or a drainage study, read the plat's lots from the page image, because acreages often aren't in the text layer. Add them up and label the total as your arithmetic. Take the study area from the study's text and exhibits. Report both numbers, the difference, and which lots or districts the study's map appears to leave out.

Sec. IV.5 requires "a comprehensive drainage impact analysis of all proposed subdivision". Ask whether the study meets that. Also report how the study models the land proposed for the heaviest use. Label anything read off a map as a visual reading. Use `scp-civics:scp-master-drainage-plan` for what the parish plan says about the site.

## 7. List waivers and later steps

- Read plat notes and staff reports for open ditch or swale drainage. That needs the Sec. IV subsurface waiver: formal letter, two directors' acceptance letters, Commission approval and a supporting Council resolution. Say which of those are on record.
- Check each other requested waiver against "impracticable" or "undue hardship" (App. C II.E.4.c, V.B.1). Financial hardship doesn't count.
- For an industrial park or development, say that the plat hearing may be the last public one, because later resubdivision takes only two signatures (V.B.2).
- Note the protest route (R.S. 33:4780.44) for a rezoning, and whether a parcel check has been run with `bayou:parish-assessor-gis` or the parish assessor.
- Ask what transcript reached the Council (XV.A.2). Report what the record holds, and whether an attachment labelled "Minutes" or an excerpt is the verbatim transcript is a question. For what was said and how the vote went, use `scp-civics:scp-meeting-record`; its machine transcript isn't that verbatim transcript.

## 8. Write the report

Use these sections, in this order:

1. **Status as of <date>:** one paragraph on where the case stands and the next date.
2. **Path:** the table from step 2.
3. **Notice:** one row per hearing with publication dates, plain count, rule, sign and mail.
4. **Calendar:** dates ahead, soonest first.
5. **Differences across the record:** the table from step 2.
6. **Future Land Use Map, Plat and drainage, Waivers:** one short section each, or "does not apply".
7. **Established:** each fact with its document and page.
8. **Not established:** each gap, with what was searched and when.
9. **Questions for staff:** only those the record left open, each naming who to call. Contacts are in `scp-civics:scp-land-use-process`, which also has the standard pre-hearing questions.

Every number and date needs a source. For public records, use `scp-civics:scp-prr`. For a comment, hand off the report. This skill doesn't draft or file one.
