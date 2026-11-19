---
name: scp-government
description: How St. Charles Parish, Louisiana government is organized and how a resident takes part. Who decides what under the Home Rule Charter (Council, Parish President, departments, committees, appointed boards) and which offices and districts the Council doesn't control (School Board, Sheriff, Assessor, Clerk, DA, Coroner, levee districts, Port of South Louisiana); how an ordinance moves from introduction to veto; Council, Commission and board speaking rules, including the written request a week ahead to address the Council; getting an item on an agenda; board appointments; initiative, Charter amendment and recall petitions; which council district, school board district, precinct and polling place an address is in; and an Open Meetings Law timing check for one meeting. Also the plugin's front door, which routes a plain question to the right skill. For one land-use case, records requests, budgets or votes, it hands off to that skill.
argument-hint: "<question about parish government, an address, a body, or a meeting>"
allowed-tools: Bash, Read, Grep, Glob, Skill, WebFetch
---

# St. Charles Parish government

```bash
GOV="${CLAUDE_PLUGIN_ROOT}/skills/scp-government/scripts/government.py"
REF="${CLAUDE_PLUGIN_ROOT}/skills/scp-government/references"
```

This is not legal advice. Date every answer ("as of 2026-11-17"), cite the Charter section, rule or statute, and separate what is established from what isn't.

## 1. Route the question

Answer here only questions about structure and participation. Hand everything else off and say which skill and why:

| The user wants | Use |
|---|---|
| Where one rezoning, plat or variance stands, its notice and deadlines | `scp-civics:scp-case-check` |
| How land-use procedure works, Commission hearing practice, notice rules | `scp-civics:scp-land-use-process` |
| To be told when something appears (notices, matters, meetings, agendas) | `scp-civics:scp-watch` |
| How the Council has voted, precedent, a member's record | `scp-civics:scp-decisions` |
| What was said or voted at one meeting, the recording | `scp-civics:scp-meeting-record` |
| What the code or Charter says | `scp-civics:scp-ordinances` |
| Budgets, capital projects, millages, audits | `scp-civics:scp-budget` |
| PILOTs, IDB leases, bonds, ITEP | `scp-civics:scp-incentives` |
| What the parish applied for, received or promised for a site: grants, state capital outlay, federal awards, economic development districts, the Economic Development Council | `scp-civics:scp-economic-development` |
| Plants at an address, reporting a release | `scp-civics:scp-facilities` |
| Drainage plan, Comprehensive Plan | `scp-civics:scp-master-drainage-plan`, `scp-civics:scp-comprehensive-plan` |
| Documents from any parish body | `scp-civics:scp-prr` |
| A custodian replied, produced records, denied, charged a fee or went silent | `scp-civics:scp-prr --after` |

A question often has two parts ("can I speak against this rezoning at Council?"). Answer the participation part here and pass the case part on.

## 2. Who decides what

Read `$REF/structure.md` before saying who controls something. In short:

- The **Council** legislates and appropriates. Every address has three members: its district member and two at-large members elected parishwide.
- The **President** runs the departments, proposes the budget and can veto.
- The Council creates and appoints to a set of boards. Some, like the IDB, the 911 District and the Hospital District, are separate public bodies with their own records.
- The **School Board, Sheriff, Assessor, Clerk of Court, District Attorney and Coroner** are outside the Charter (Art. VII.G).
- The **levee districts and the Port** are created by state law. The structure file says how far the parish reaches into each.

A common mistake is to treat the Council as answerable for an independent office. It can't direct the Sheriff or the School Board. It can ask, and it can fund or withhold only what it funds.

Charter text stays out of this repository. Paraphrase with the section, and quote only after reading it with `python3 "${CLAUDE_PLUGIN_ROOT}/skills/scp-ordinances/scripts/code_search.py" get "Charter IV C"` and checking the page image, as that skill describes. Without a code index, cite the section and give the user the Municode link.

## 3. Taking part

Read `$REF/participation.md`. The facts residents most often get wrong:

- **Two routes to speak at Council.**
  - On an item set for public hearing, including P&Z petitions: three minutes. The rules state no advance request.
  - On anything else, under "Persons to Address the Council": a written request stating the subject must reach the Council Secretary a week ahead (Charter VII.I). Since 2024-01-08 the subject must be germane to parish government, and the same subject is barred within eight weeks. Five minutes.
- **Written comment** on a pending ordinance can be attached to it by the Council Secretary (Rule 33). Anything mailed or emailed to the Council Office becomes a public record (Rule 39).
- **Only a member or the President can introduce an ordinance.** The resident's route is a sponsor, before the Rule 34 deadline (4 PM, sixth business day before the meeting).
- **The Commission and ZBA** have their own rules: three minutes per item at the Commission; no stated limit at the ZBA. Commission comment deadlines are in `scp-civics:scp-land-use-process`.
- **Initiative, Charter amendment and recall petitions** have fixed thresholds and clocks. Give the section and say it is a summary.

Tell the user to confirm the rule with staff before a meeting that matters, and to record who said it and when.

## 4. Who represents an address

```bash
python3 "$GOV" district "15045 River Rd, Hahnville"
python3 "$GOV" district --point 29.9634,-90.4070
```

- **What it returns:** the council district with its member and the two at-large members (names from `scp-meeting-record`'s roster), community, fire district, and from the parish precinct layer: precinct, school board district, state House and Senate, congressional, PSC and BESE districts, and polling place.
- **What it sends:** only the address, to the parish's own geocoder at maps.scpgis.com, and it caches nothing. Use `--point` if the user would rather not send an address.
- **Split precincts.** Many precincts are split between school board districts, shown as "1 | 2". Say the precinct can't settle it and the Registrar can.
- **Layer vintage.** The precinct layer is the parish's 2023 copy. As of 2026-11-17, the council layer's District 1 polygon was edited in March 2026, after Ord. 26-2-3 changed Districts 1 and 7, but District 7 carries no edit date. If an address is near that line, check the ordinance. The script prints both and flags any disagreement between the two layers.
- **Authority.** The Registrar of Voters and the Secretary of State's voter portal decide a voter's districts.
- **Exit codes:** 1 means no confident match or a point outside the parish; 2 means the parish GIS couldn't be reached.

## 5. Which bodies meet

```bash
python3 "$GOV" bodies [--months 12]
```

Lists every Legistar body with meetings held in the period, the last meeting, the next one listed, and where it usually meets. The API lists a meeting only once it is published, so for scheduled meetings use `scp-civics:scp-watch` `calendar`. Several Council committees haven't met in a year or more, so don't tell a user an item "goes to committee" without its history showing it.

## 6. Was a meeting properly noticed?

```bash
python3 "$GOV" notice --event <Legistar event id>
python3 "$GOV" notice --body Planning --date 2026-11-05 [--holiday 2026-02-17]
```

Read `$REF/open-meetings.md` first. The script computes the R.S. 42:19 deadline (24 hours, skipping weekends and R.S. 1:55 legal holidays) and compares it with when Legistar last published the agenda. It also reports the minutes status, counts public-comment openings in the minutes against decided items, says whether live broadcast is required, and for the Council, finds the annual schedule.

**Report every result as a question.**
- Legistar dates only the website copy, and only its last publication.
- The statute is met by the posted or journal notice.
- A late website posting alone "shall not be a violation".

Give the 60-day windows (R.S. 42:24, 42:28) and the records to ask for through `scp-civics:scp-prr`. Never tell a user a meeting was unlawful.

## 7. Report

Lead with the answer, then the source and date. For people, cite the roster and say to check Legistar. For a rule, give the rule number or section and the adopting matter. Name what wasn't established (`structure.md` marks these) instead of filling the gap from memory.

This skill researches and drafts. It never contacts an office, files a request or comment, or signs a petition.

$ARGUMENTS
