---
name: scp-economic-development
description: What St. Charles Parish, Louisiana government pursues for economic development before a land-use case exists, and what it applied for, received, built or promised for a site or project. Covers the Department of Economic Development and Tourism and its yearly Council report, Economic Development Council minutes, grant applications (LED FastSites, EDA, Delta Regional Authority, Office of Community Development), cooperative endeavor agreements with the state and companies, state capital outlay lines in HB2 with line-item vetoes, Treasury allocations, federal grants and subawards, roads built toward a site, and economic development districts that can levy taxes or pledge tax increments. Use for what the parish did to prepare or market a site, what grants or state money it sought, or how its actions line up in time with what it said in public. Tax incentives go to scp-incentives.
argument-hint: "<site, project, road, company, grant program or district>"
allowed-tools: Bash, Read, Write, Grep, Glob, Skill, WebSearch, WebFetch
---

# St. Charles Parish economic development

Trace what the parish government itself did for a site or project, and set it in time beside what the parish said in public. Write `econdev-<project>.md` in the user's project folder. If the working directory is this plugin, ask where to write it. Project findings never go in the plugin.

```bash
ED="${CLAUDE_PLUGIN_ROOT}/skills/scp-economic-development/scripts/econdev.py"
python3 "$ED" council --term "<site, road or company>" [--since 2015-01-01]
python3 "$ED" council --kind grant --kind state --kind district --since 2021-01-01
python3 "$ED" edc [--since 2025-01-01] [--dir <project folder>/edc --term "<name>"]
python3 "$ED" outlay --session 26RS [--match "<project>"]
python3 "$ED" deck <file.pptx>
python3 "$ED" federal [--sub] [--since 2015-10-01] [--match "<project>"]
```

Shell state may not carry between calls, so set `ED` in each one. It needs Python 3 and `poppler`, not bayou.
- **Exit codes:** `0` found; `1` the source answered and nothing matched; `2` the source wasn't reached. Never report `2` as "none".
- **Where files go:** `edc --dir` saves meeting files to the user's folder. `outlay` caches the act PDFs in `~/.cache/scp-civics/econdev`.

This is research, not legal advice. Date every finding ("as of 2026-11-19") and keep **established** apart from **not established**. Never say the parish hid something, or acted improperly or in bad faith. Say what the record shows, and when.

## Boundary

| The user wants | Use |
|---|---|
| PILOTs, IDB leases, bonds, ITEP | `scp-civics:scp-incentives` |
| What a budget line or capital project report says | `scp-civics:scp-budget` |
| How members voted on these matters | `scp-civics:scp-decisions` |
| What was said at a Council meeting | `scp-civics:scp-meeting-record` |
| When the Economic Development Council meets next | `scp-civics:scp-watch` `calendar` (it covers this body) |
| The rezoning that followed | `scp-civics:scp-case-check` |
| LED's own records: Certified Sites, LEDC board, FastSites rules, news | `bayou:led-project-signals`. Without bayou, use opportunitylouisiana.gov: its FastSites, Certified Sites and LEDC board pages and its news releases |
| Documents that aren't posted | `scp-civics:scp-prr` |

## 1. Who acts for the parish

Read `references/record-map.md` before naming who did something. In short:

- **Department of Economic Development and Tourism.** Created by Code Sec. 2-23. It runs industrial and business development programs, recommends policy to the Council, and acts as liaison with state and federal agencies. Its director is appointed by the President. Each year it gives the Council a report, a "Report Filed" matter titled with the department's name, with slides attached. The slides can list announced projects and awards. The PDF copy is one image per page, but the `.pptx` attached to the same matter has the text, tables, SmartArt and speaker notes. Fetch it from `https://stcharlesgov.legistar1.com/stcharlesgov/attachments/<MatterAttachmentFileName>` (the API's `/snohomish/` hyperlink returns 404) and read it with `deck`. No OCR is needed for that text. Logos and photos are pictures. Look at a slide image yourself (render one page with `pdftoppm -r 100 -f N -l N -png`, or `Read` a file from `ppt/media`) only when a finding depends on it, such as which companies a slide names, and not for every picture-only slide. A typed memo scan reads well with tesseract (`--psm 4`).
- **Economic Development Council** (Legistar "SCP Economic Development", body 180). An advisory group with a private chair. Parish directors sit on it ex officio. It meets monthly at the River Parishes Community College campus in Boutte.
  - Its minutes and packets are files on each meeting page. The API's minutes status reads "Draft".
  - It takes no Council action, so nothing here is a decision.
  - Whether it is a public body under the Open Meetings Law and Public Records Act isn't established.
  - Sec. 2-51 creates a different body, a three-member Economic Development Commission. As of 2026-11-19, no Council title naming that Commission had been found, so whether it is active isn't established.
- **Economic development districts.** Political subdivisions governed by the President and Council (R.S. 33:9038.32(D)). Two exist: Highway 90 EDD No. 1 (Ord. 24-9-6) and Luling Bridge EDD No. 1 (Ord. 24-12-16). See §5.
- **The Council** approves grant applications, cooperative endeavor agreements and budget amendments by resolution or ordinance. Not everything goes to it (§2).

## 2. Council record

```bash
python3 "$ED" council --term "<site>" --term "<road>" --term "<company>"
python3 "$ED" council --kind grant --kind state --since 2021-01-01
```

The command groups titles by kind:

| Kind | Examples |
|---|---|
| `grant` | Applications to EDA, DRA, OCD and USDA |
| `state` | Treasury allocations, Facility Planning and Control agreements, OCD agreements |
| `cea` | Cooperative endeavor agreements, including with companies, such as one with a company to build a connecting road |
| `district` | Economic development districts |
| `report` | The department's yearly report |
| `led` | LED titles |

Each line shows any Facility Planning and Control project number (FP&C, `50-J45-yy-nn`) and any dollar amounts in the title. Acronym terms (`EDA`, `LED`) match only as whole words with their capitals.

**What titles miss.** Most program applications found (DRA, EDA, USDA, OCD) have a Council resolution authorizing or supporting them. The exception found: the department's 2026 Council report lists a FastSites award, and as of 2026-11-19 no Council title named FastSites. Who applied for it isn't shown by any posted record read. An award can later show up under the following, so search the road or site name, not only the program:
- a budget amendment
- a professional services agreement for the road
- a servitude or an expropriation

## 3. State money

```bash
python3 "$ED" outlay --session 26RS
```

- **HB2, the capital outlay act.** It lists every line for agency `50/J45 ST. CHARLES PARISH`, plus every state, levee or port project whose location names St. Charles. Multi-parish projects show their full location list.
  - The act text still prints vetoed lines. The script reads the Governor's veto message and flags vetoed items.
  - **An appropriation isn't cash.** Priority 5 is a non-cash line of credit. Quote the priority definitions from the act's Section 1 before saying money is available.
  - Sessions 23RS to 26RS were parsed on 2026-11-19. 2023 used three-digit project numbers.
- **The join.** A Council agreement "with the State of Louisiana … (Facility Planning and Control Project No. 50-J45-25-02)" is the parish's agreement for an HB2 line. Match its project title against `outlay`.
- **Treasury agreements** ("allocation of $X to be utilized for Y") are state money passed to the parish. Each agreement attached to its matter names the act behind it. The one read (2026-0344, 2026-10-26) cites a line-item appropriation in Act 3 of the 2026 Regular Session, not HB2 (Act 4), with Treasury's Local Government Fund Management Division as contract monitor. Read each one's attachment before naming its act.
- **Requests.** What the parish asked for in its capital outlay requests (the state's CORTS system) isn't published on the state's site. Compare the HB2 Original with the Act, or request the submission (§7).
- **LED programs.** FastSites (Site Investment and Infrastructure Improvement Fund, R.S. 51:2316, LAC 13:I Chapter 55) and Certified Sites are LED's records, so use `bayou:led-project-signals`.
  - LED's posted FastSites "NOI register" files are rulemaking notices, not lists of applicants. On 2026-11-19, neither register named St. Charles.
  - An application becomes public through LED's award release or a records request.

## 4. Federal money

```bash
python3 "$ED" federal --since 2015-10-01
python3 "$ED" federal --sub --since 2015-10-01 --match "pump|road|rail"
```

- **Prime grants.** USAspending lists federal grants made directly to recipients named St. Charles Parish. The School Board, Sheriff and Housing Authority appear under their own names.
- **Subawards (`--sub`).** Money passed through state agencies (OCD, GOHSEP), where the state reported it. The School Board's monthly food and education subawards outnumber the parish's, so add `--recipient '^ST CHARLES PARISH$'` for parish government alone (43 of 244 rows from 2015-10-01, checked 2026-11-19).
- **Reading the rows.** The same award repeats across reports, and the script removes the duplicates. Amounts are obligations, not money spent.
- **Use it to close a loop.** A Council title approves an application and USAspending shows the award. A later Council title can end it, as one 2014 resolution did by terminating a 2009 EDA rail-spur award.

## 5. Economic development districts

Read the statute notes in `references/record-map.md`, and check the current text with `bayou:la-rs-search` or legis.la.gov before quoting it. As read on 2026-11-19:

- **Taxes (R.S. 33:9038.39).** A district may levy up to 5 mills, a 2% sales tax and a 2% hotel tax.
  - **Steps.** It must adopt a resolution of intent, publish it once a week for two weeks (the first publication at least 14 days before the hearing), and hold an election.
  - **Exception.** No election is required if the registrar certifies the district has no qualified electors. So a district's voter count matters.
- **Tax increment pledges (R.S. 33:9038.34).** Revenue bonds may be paid from sales tax increments. Other tax recipients' increments need an intergovernmental agreement with each of them (A)(5). The state's share needs Joint Legislative Committee on the Budget approval.
- **Costs (R.S. 33:9038.36).** Eligible costs include payments to developers for site preparation, and public streets and utilities inside or outside the district.
- **Status.** As of 2026-11-19, no Council title had been found levying a tax, pledging an increment or adopting a plan for either district. Report "none found in Council titles", not "none". Each district's boundaries are Exhibit A to its ordinance.

## 6. Economic Development Council

```bash
python3 "$ED" edc --since 2025-01-01
python3 "$ED" edc --since 2025-01-01 --dir <project folder>/edc --term "<site>" --term "<company>"
```

It lists each meeting, agenda items without boilerplate, and the files on the page. Sign-in sheets are never saved. With `--dir` and `--term`, it prints hits by page. Two tags matter:

- **`[posted summary, not verbatim]`.** The minutes carry a Summary, Outline and Action Items section that reads as machine-generated. Treat its figures ("$15 billion in announced projects") as claims made at the meeting, and cite them as the posted summary. For exact words, find a recording with `scp-civics:scp-meeting-record`, if one exists.
- **`[reprinted article]`.** Packets reprint newspaper articles after the council's own pages, and any packet page without an agenda, statistical-report or schedule heading gets this tag. Cite the article by paper and date, not the packet, and don't reproduce it. What an article says officials said is reporting, not a parish record.

Legistar holds this body's meetings from 2025-01-15 on. The packet's monthly statistical report counts "properties" inquiries, which shows site demand without naming sites.

- **Long runs.** `--dir` over many meetings downloads every file and can run past a two-minute command limit, so give it a long timeout or run it in the background. Output is line-buffered. A rerun reuses files already saved.
- **Searching terms.** `--term` needs `--dir`. If an image-only file wasn't searched, the run says so and exits `2` rather than `1` when nothing else matched.

## 7. Records that aren't posted

Hand these to `scp-civics:scp-prr`. The parish is the custodian unless noted:

- a grant or FastSites application with its budget workbook
- the President's support letters
- the award letter and the grant or cooperative endeavor agreement
- any LED-prepared model or analysis the parish received
- the parish's capital outlay request
- an economic development district's plan and any intergovernmental agreement
- the Economic Development Council's membership list and bylaws

LED is a separate custodian. R.S. 44:22 lets it keep an active negotiation's records confidential only on stated conditions and for a limited time. `bayou:led-project-signals` summarizes them. Without bayou, read R.S. 44:22 at legis.la.gov. LED's records-request page is opportunitylouisiana.gov/public-information/public-records-request.

## 8. Report

Write `econdev-<project>.md`:

1. **Status as of <date>.**
2. **Timeline.** One row per action: date, actor (department, President, Council, EDC, state, federal), action, record and page, amount. Mark rows taken from a recital or a posted summary.
3. **Said in public.** EDC minutes, the department's report, Council remarks, each with its date. Put each beside the timeline row nearest in time. Don't infer intent from the order of events. Say "the application is dated A; the Council heard B on C".
4. **Established** and **Not established**, kept apart.
5. **Records to request** and **questions for the department** (985-783-5140, per its letterhead, 2026-10) or the Council Secretary (contacts in `scp-civics:scp-government`).

Every number needs a source and a date. This skill researches and drafts. It never sends a request, files a comment or contacts an office.

$ARGUMENTS
