#!/usr/bin/env python3
"""Write references/status-ledger.md from index/status.csv and the other index files.

Run after status_build.py. The prose sections of the ledger live in this script, so change them
here rather than in the Markdown.
"""
import csv,json,collections,sys
from pathlib import Path
SK=Path(__file__).resolve().parents[1]
M={r['matter_file']:r for r in csv.DictReader(open(SK/'index/legistar_matters.csv'))}
rows=list(csv.DictReader(open(SK/'index/status.csv')))
for r in rows: r['row']=int(r['row'])
def s(f):
    r=M[f]; return f"{'Res.' if r['type']=='Resolution' else 'Ord.'} {r['enactment_no'] or '(none: '+r['status']+')'} [{f}, {r['passed_date'] or r['intro_date']}]"
def money(c):
    try: return '/'.join('$'+format(float(x),',.2f').rstrip('0').rstrip('.') if x else 'TBD' for x in c.split('/')) if c else 'TBD'
    except ValueError: return c
L=[]
A=L.append
A('''# Implementation status ledger

Council record as of 2026-10-13, from 2020-01-01. Parish capital report as of 10/8/2026, read
2026-11-03. Read this before searching; then search only for what is newer than those dates, and
update `index/status.csv` and this file together.

`index/status.csv` holds one row per plan project (369 rows, keyed on doc + page + table +
project_id + row, because IDs repeat across volumes and alternatives; `row` counts repeats of an
ID inside one table). This file is the readable
summary. Rows from the two public-meeting decks are left out because they repeat the summaries.

## What was searched, and what was not

| Source | Done | Result |
|---|---|---|
| Council legislation titles, Legistar API, 2020-01-01 to 2026-10-13 | Yes | 482 matters in `index/legistar_matters.csv`; every non-ceremonial title read and matched by hand |
| Council titles searched by each West Bank plan project's street or canal name | Yes | No further drainage matters |
| Parish news releases (stcharlesparish.gov), Herald Guide, L'Observateur | Partly | Three searches; used only to corroborate the Ormond, Destrehan No. 2 and Montz rows |
| Parish capital projects report, "Drainage - May 2026" (dated 5/29/2026, 11 pages) | Yes | Transcribed to `index/parish_tracker.csv` (54 project lines) from `$SCP_CIVICS_DATA/scp-capital-drainage-2026-05.pdf`. Source page: `https://www.stcharlesparish.gov/departments/public-works/capital-projects`. The site refuses scripted requests, so save new reports through a browser |
| Parish capital projects report, "Council - July 2026" (dated 7/31/2026, 21 pages: Drainage, Roadway, Wastewater, Levee, Miscellaneous) | Yes | Drainage and Levee pages read; `index/parish_tracker_2026-07.csv` (58 lines). PDF and text at `$SCP_CIVICS_DATA/scp-capital-council-2026-07.pdf` |
| Parish capital projects report, "2026 10 Capital Projects" (updated 10/8/2026, 11 pages: Drainage, Roadway, Wastewater, Levee, Other, each headed "Active Projects") | Yes | Drainage and Levee pages read on the page images; `index/parish_tracker_2026-10.csv` (27 lines). PDF and text at `$SCP_CIVICS_DATA/scp-capital-council-2026-10.pdf` |
| Other items on that page: the separate Roadway, Wastewater, Levees and Miscellaneous reports (May 2026), the Murray Hill and Ormond jack-and-bore presentations, and the "Master Drainage Studies" page | No | The July Council report repeats the category reports |
| Capital budget schedules | Partly | 2027 proposed budget read (`index/budget_2027_proposed.csv`). Adopted budgets for 2021 to 2026 not read; their Exhibit A and B attachments are fund summaries with no project lines |
| Louisiana Watershed Initiative award lists | Partly | Round 2 list checked for the two St. Rose pump stations only |
| HB 2 capital outlay, FEMA mitigation data | No | Only what council resolutions and the corpus town hall deck say |
| Local folders `scp-council/`, `scp-legislative/`, `scp-prr-fees/` | Checked | A handful of passing mentions in 2025 transcripts; not read for status |
| Legislation attachments (contracts, bid tabs, certificates) | Partly | Read for the two Built and three Under-construction rows and the Vial servitude (20 PDFs, OCR where scanned). Not read for the 34 design-only rows or for projects outside the plan |

"No record found" therefore means: no council matter since 2020 whose title names the project.
Small culvert and pipe rows could have been built by parish crews or inside a larger contract
without ever appearing in a title.

## When the plan was written

| Event | Source |
|---|---|
| Engineering agreements for the "2020 East Bank Master Drainage Plan" (Principal Engineering, P200601) and "2020 West Bank Master Drainage Plan" (T. Baker Smith, P200602) | %s; %s |
| Moratorium on major subdivisions until the drainage and sewer master plans for a community are accepted by council resolution, or 18 months | %s |
| East Bank amendments | %s; %s (design services, $80,400.00); %s ($569,737.50) |
| West Bank amendments | %s; %s ($506,218.25) |
| Council resolution accepting any volume of the plan | None found by title |

PDF creation dates in `scp/` (an upper bound on each summary's date, and for the 2026 dates
probably the day the file was saved): Ama-Sellers, Hahnville I and II 2021-11-11; Montz, New
Sarpy, Norco, Ormond 2021-12-06; St. Rose, Almedia, Bar None, Dianne Place, Turtle Pond
2023-11-02; Luling, Mimosa Willowdale 2024-06-18; Killona Taft, Paradis, Destrehan East, West and
Plantation, Plantation Business Center 2026-09-21. Projects with a "P19..." or earlier parish
project number were under way before the plan contracts were signed.

## Totals

| Status | Plan rows |
|---|---|
''' % (s('2020-0181'),s('2020-0180'),s('2020-0178'),s('2021-0196'),s('2022-0093'),s('2023-0163'),s('2021-0208'),s('2023-0053')))
c=collections.Counter(r['status'] for r in rows)
LAB={'Built':'Built (one part only, one match unconfirmed)','Funded':'Funded (design, survey or grant only)'}
for k in ('Built','Under construction','Funded','Application submitted','No record found'): A(f'| {LAB.get(k,k)} | {c.get(k,0)} |\n')
FUNDED=c.get('Funded',0)
A('''
The two "Built" rows are council projects that are complete, matched to a plan row by name;
whether what was built is what the plan row describes is unconfirmed for both. All "Funded" rows are design, survey or pre-construction contracts, or grant agreements, with no
construction contract. The Ormond sheet-pile rows (1-2 to 1-4, 1-6, 1-7) are matched to design
contracts signed in 2020-07, before the Ormond summary, for widening and structures. Rows repeat across alternatives, so counts are rows, not distinct projects.
Plan costs are not summed by status here: alternatives would double count.

By bank: East Bank has every built and under-construction row. West Bank has six rows with any
trace (Hahnville 1 IG-1 and IG-2, Hahnville 2 IG-1, Ama-Sellers IG-1 and IG-2, the Willowdale
Pump Station), all design or survey only, though the parish report says its crews dug ditches for
King and Hahn Street and Bamboo Street. Neither the council titles nor the parish report names
any Luling, Luling I-310, Killona Taft or Paradis improvement group. West Bank construction is
on projects outside the plan (Primrose Canal, Kinler and Paul Frederick, Lakewood Pump Station).

The parish report itself ties six projects to the plan by priority: Bamboo Street (Hahnville 2
Priority 1), the U.P. Railroad ditch in Ama (Ama Priority 1), Engineers Canal Pump Station (Norco
Phase 1 Priority 1), Clayton Pond Outfall (Norco Phase 1 Priority 3 and 4), New Sarpy Pump Station
(New Sarpy Phase 1 Priority 2) and Schexnaydre Pump Station (New Sarpy Phase 1 Priority 1). Its
statuses are in the `parish_report_2026_07_31` column of `index/status.csv`. Many are "On Hold"
awaiting construction funding, including the Ormond canal sheet-pile projects designed in 2021.
The October report prints no plan priority, so those ties rest on the May and July reports.

## What the October report changed

The report updated 10/8/2026 is headed "Active Projects". It has 23 drainage lines where July had
54, and the same four levee lines. **A line missing from it isn't closed, cancelled or finished.**
The report doesn't say why any line left. No line has the report's grey "Completed" fill. So
`parish_report_2026_07_31` keeps its text, and `parish_report_2026_10_08` holds the newer line
where there is one. `july_project` in `index/parish_tracker_2026-10.csv` names the July line each
October line continues, and its `new_comments` column holds the report's red "new comments".

These are the parish's statements. No plan row's status in `index/status.csv` changed, since none
of this adds a council award or completion record. Council titles weren't searched again after
2026-10-13.

| Line | July | October |
|---|---|---|
| Lakewood Pump Station Discharge (P241106) | Design | Construction; contract ordinance voted 9/14/26 |
| Kinler & Paul Frederick Phase 1 (P210704) | Design, $2,500,000 | Construction, $728,906; notice to proceed for 9/10/2026, ends 2Q27 |
| Montz Pump Station at CN Railroad (P210301) and #2 at Airline (P210806) | Design printed, with construction dates | Construction; both still end 4Q26 |
| Turtle Pond Pump Station Replacement | Funding Application, no dates | Final Design; 3Q27 to 1Q29; 90% submittal expected by end of October |
| Oakland and Fairfield Airline Crossing | Planning, 3Q26 start | Final Design, 2Q27 to 2Q28 |
| Oakland and Fairfield Upstream | Planning, $500,000 | Final Design, $950,000, 2Q27 to 4Q27 |
| Des Allemands Bulk Head Phase 2 | Preliminary Design | Final Design; aiming to bid before the end of 2026 |
| Engineers Canal Crossing at CPKC | Negotiations, no team | Preliminary Design, GIS, 4Q27 to 2Q29; CPKC no longer able to do the work |
| Oakland and Fairfield CPKC Crossing | Planning | Planning; CPKC no longer able to do the work, proposal to come from HNTB |
| Evangeline Road & CN Railroad Box Culvert | 2Q26 to 4Q26 | Dates TBD; on hold until 2027 funding |
| Ormond CN Culverts Sites 1&2 and Ormond Center | Both end 3Q26 | Both end 2Q27; 65% and 30% complete |
| Murray Hill and Destrehan Drive; Primrose Phase 1B | End 3Q26 | End 4Q26; 85% and 50% complete |
| King and Hahn Street | Design, final plans requested | Design; bid opening scheduled for 10/13 |
| Engineers Canal Pump Station | Improvements (P220206), Final Design, $15,000,000, 1Q26 to 1Q27 | A line named "Design refinement" with no number, status, team, cost or dates; proposal to come from HNTB |

The July lines not listed in October include these, which July didn't show as on hold: Carriage/Dunleith
Canals Drainage Structure (Final Design), Hill Heights Phase 2, Clayton Pond Outfall and Cousins Canal
Bank Stabilization Phases 1 to 3 (Design), Oak Street and Dianne Pump Stations (Conceptual), and
Lemoine Lane, St. Mark Street and Davis Plantation (in-house or partly internal). Ask Public Works
what became of a line before saying anything about it.

Oddities as printed, not corrected:

- New Sarpy Pump Station prints a construction start of 2Q27 and an end of 3Q23.
- Turtle Pond Upstream is "Conceptual", with "90% Design Plans" received.
- The Engineers Canal "Design refinement" line carries the same CPKC sentences as the crossing line,
  though its description is the pump station. Its match to P220206 rests on the name alone: it
  prints 150 to 340 cfs, where July's P220206 line printed 185 to 250 cfs.
- P260803 is the crossing's number in the report, while a council title gives it to the pump
  station's design refinement (see Norco 1-1). The registry keeps the crossing as its own
  parish-report row, not under that council row.
- P251001 is on both the CPKC Crossing and Upstream lines.
- Sunset Pump Station is P080905-11B in October and P080905-11D in July.

## What the attachments, the July report and the 2027 budget added

Read 2026-10-13. PDFs and their text are in `$SCP_CIVICS_DATA/council-attachments/`
(file names start with the matter file number) and `$SCP_CIVICS_DATA/scp-capital-*.pdf`.

- **Montz stations.** The parish report of 7/31/2026 (Levee page) lists "Montz Pump Station (at CN
  Railroad)", 267 cfs (P210301) and "Montz Pump Station #2 (at Airline)", 340 cfs (P210806). Bid
  tabulations show four and five 67 CFS pumps. The plan rows are 200 CFS (1-1) and 340 CFS (3-1,
  Alternative 3, existing station removed); the report says the Corps permit requires removing the
  Prescott Pump Station after Montz #2 starts. Station 1 is larger than the plan row.
- **Destrehan No. 2.** Substantially complete 2024-04-03 (P190507) and 2024-10-21 (P181101). The
  bid items are sheet pile walls, a trash rack structure, bar screen cleaners and excavation. No
  document read states a sump storage volume, so the match to Ormond 1-1 stays unconfirmed.
- **Hill Heights.** The finished contract was about 182 running feet of sheet piles, final cost
  $728,098.20, final acceptance 2023-06-15. The plan row is about 690 linear feet at $4,973,750.
- **Ormond CN culverts.** The award recommendation gives no sizes; the itemized bid tabulation is
  a rotated scan that OCR could not read. Sizes still rest on the parish news release.
- **Vial servitude (Ord. 26-4-7, file 2026-0128).** The servitude plat places it in Sections 8, 9,
  11, 12 and 122, T13S-R20E, between the Union Pacific Railroad and LA 3127, beside Fashion
  Plantation Subdivision and the Vial Canal, on land of private owners of record and
  JCJR St. Charles, LLC. The parish report assigns the Vial servitude and the JCJR
  donations to the Bamboo Street project (Hahnville 2).
- **July report against May.** Same 54 drainage lines. Each row's status, cost and dates were checked by script against the July PDF text; progress notes were picked by reading and are not a full diff
  (`july_note` in `index/parish_tracker_2026-07.csv`). The July file adds the four Levee lines.
  The May file `index/parish_tracker.csv` is kept as transcribed.
- **Projects under two numbers.** The registry does not link Turtle Pond P190801 and P250901, or Fairfield and Oakland P240601, P180301-A/B/C and P251001. The October report prints P250901 on both Turtle Pond lines and P241001 on the Airline Crossing.
- **Kinler Street Canal number.** The May and July reports print P250507; the council title (Ord.
  25-9-1) and the October report say P250705.
- **2027 proposed budget** (file 2026-0173, "2027 Proposed Budget 9.30.2026", 308 pages). Capital
  outlay lines for funds 112, 123, 312 and 313 are in `index/budget_2027_proposed.csv`. Largest:
  Cousins Pump Station T-wall and sump $23,366,315; Engineers Canal Pump Station $21,985,000; LWI
  Round 2 Turtle Pond Pump Station $15,000,000; Sunset Pump Station Upgrade $14,333,685; LWI Ormond
  Area Consolidated Drainage Improvements $10,781,677. West Bank plan-related lines: Willowdale
  Pump Station Bottleneck $1,650,000; Jack & Bore at Lowe Plantation $653,773; Hahnville 2
  Watershed Jack & Bore $450,000 (engineering). No Luling, Killona Taft or Paradis plan project is
  named. The budget's goals table says a preliminary draft of the Master Drainage Plans was
  completed in Q4 2022 (PDF page 57). These are requested amounts, not adopted ones.
- **Louisiana Watershed Initiative.** The state's Round 2 list shows Fairfield and Oakland Pump
  Station Upgrades $5.77 million and Turtle Pond Pump Station Upgrades $9.23 million, conditional
  on a feasibility study and full application (https://watershed.la.gov/round-2).

Still not searched: adopted budgets for 2021 to 2026, HB 2 capital outlay by year, FEMA mitigation
awards, local meeting transcripts, and news beyond five searches (one 2026 search of the Herald
Guide and L'Observateur for Luling drainage returned nothing current).

## Plan rows with a council record

| Basin | ID | Plan name | Plan cost | Status | Parish source | Notes |
|---|---|---|---|---|---|---|
''')
for r in rows:
    if r['status']=='No record found': continue
    n=r['notes']+((' Independent: '+r['independent_source']) if r['independent_source'] else '')
    A(f"| {r['doc'].replace('-executive-summary','')} p{r['page']} | {r['project_id'] or '(none)'} | {r['name']} | {money(r['plan_cost'])} | {r['status']} | {r['parish_source']} | {n} |\n")
A('''
West Bank costs are printed as 25-year/100-year. Check any cost against
`known-discrepancies.md` before citing it.

## Parish project registry

`index/parish_projects.csv` lists every parish drainage and levee-system project the council has
acted on since 2020, one row per parish project number: name, phase (design, construction,
complete), contractor, award amount, change-order count, first and last council action, whether
a Certificate of Substantial Completion or Final Acceptance is attached, the plan rows it is
matched to, the matter file numbers, and links. `award_link` opens the construction award and
`links` opens every matter; each Legistar page lists that matter's attachments, which is where
the contract, bid tabulation, scope exhibits, change orders and completion certificates are. It is generated, so do not edit it by hand:

```bash
scripts/legistar_harvest.py            # refresh index/legistar_matters.csv
scripts/legistar_harvest.py projects   # rebuild index/parish_projects.csv
```

REGCOUNT

Reading it:

- Phase comes from title wording only. "Complete" means a final change order; "construction" means
  an award or a non-final change order with nothing later. A project that closed out without a
  change order stays at "construction" (Fifth Street, P190506, last acted on in 2022, is likely
  one). Check `completion_docs`, then the attachments.
- Only enacted or approved matters count, so a pending item is absent (the Willowdale Pump Station
  Sump Improvements, P241102, has only a pending amendment).
- `kind` is "levee system" when a title ties the project to a hurricane protection levee. The two
  Montz pump stations are labelled that way by the parish and are also matched to Montz plan rows.
- `contract_amount` is the latest construction award, before change orders. Multi-phase projects
  (Primrose Canal, P210202) show the latest phase.
- `plan_rows` is filled from `index/status.csv`. Blank means no plan row was matched, not that
  none applies. The table below lists those projects with notes.
- Projects with no parish project number in the title are missing.

## Drainage work that matches no plan row

Council projects since 2020 that are drainage work but could not be tied to a plan row from the
title. Some may implement a plan row under another name; the scope documents attached to each
ordinance would settle it. "Area" is given only where the title states it.

| Project (parish no.) | Area | Latest council action | Sources |
|---|---|---|---|
''')
U=[
('Primrose Canal Cleaning and Improvements (P210202)','Mimosa (West Bank)','Phase 1A contract $2,757,000.00, Change Order 2 (Final) 2024; Phase 1B contract $1,507,765.04, 2026',['2023-0344','2024-0302','2025-0401','2025-0264']),
('Ormond Center Drainage Improvements (P190505)','Ormond','Contract $3,097,730.00; Change Order 1 adds $271,095.41; Change Order 2 at public hearing',['2025-0392','2026-0251','2026-0325']),
('Murray Hill Drive and Destrehan Drive Drainage Improvements (P201001)','Destrehan','Contract $2,112,258.00, 2025',['2021-0057','2025-0152']),
("Engineer's Canal Phase 1 Bank Stabilization (P190301)",'Norco','Contract $1,405,350.00; Change Order 1, 2024. Plan rows Norco 2-1 and 2-7 are "reshape and clean", not bank stabilization',['2023-0311','2024-0288']),
('Fifth Street Drainage Improvements (P190506)','','Contract $1,182,515.00; Change Order 1, 2022',['2021-0132','2022-0189']),
('Lakewood Pump Station Discharge Modifications (P241106)','Luling','Contract $959,300.00, 2026',['2025-0050','2026-0266']),
('Kinler and Paul Frederick Roadway and Drainage Improvements (P210704)','Luling','Phase I contract $728,906.00, 2026',['2021-0225','2026-0196']),
('Kinler St. Canal Improvements (P250705)','Luling','Design $52,101.00, 2025',['2025-0247']),
('Ama Drainage Improvements Rebid (P150801-2)','Ama','Contract $2,752,705.00; Change Order 1 and Final 2023. A 2015 project; may overlap Ama-Sellers IG-1 or IG-2, scope not compared',['2022-0021','2023-0325']),
('Mimosa and Lagatutta Drainage Improvements (P090904)','','Change Order 1, 2022. A 2009 project',['2022-0238']),
('Cousins Canal Bank Stabilization (P241103)','Luling','Design not to exceed $618,000.00, 2025',['2025-0033']),
('KCS Canal Drainage Improvements (P230401)','','Design not to exceed $260,348.00, 2023. Candidate rows: Almedia 4-1, 4-2 (KS RR Canal) or Norco KCS rows',['2023-0156']),
('US 61 Canal Improvements (P230602)','Montz','Design not to exceed $48,656.25, 2023; the parish report says it was bid inside Montz Pump Station No. 2',['2023-0160']),
('Engineers and Good Hope Canals Pipeline Location Investigation (P230402)','Norco','$112,315.00, amended 2025',['2023-0158','2025-0139']),
('River Point - River Village Drainage Improvements (P210805)','','Design 2021; grant application 2024',['2021-0266','2024-0065']),
('Riverbend Hydraulic Design (P240701); Riverbend Subsurface Drainage (P250702)','St. Rose','Analysis and design, 2024-2025. Candidate rows: Almedia 1-4, Turtle Pond 3-1, 3-6',['2024-0385','2025-0202']),
("Lemoine Lane, Hirsch Street and St. Mark Street Drainage Improvements (P220201)",'Ama','Design not to exceed $194,931.00, 2022',['2022-0170']),
('U.P. Railroad Drainage Ditch & Outfall Improvements (P220205)','','Design not to exceed $194,931.00, 2022',['2022-0171']),
("Clayton's Pond Outfall Improvements (P220204)",'','Design not to exceed $141,179.00, 2022',['2022-0188']),
('JCJR Outfall Ditches (P250701)','','$70,248.00, 2025. JCJR St. Charles, LLC is the Fashion Plantation rezoning applicant (Hahnville), so this may relate to Hahnville 2 IG-3',['2025-0204']),
('Milling Drainage Improvements (P260501)','','$85,575.00, 2026',['2026-0172']),
('Davis Plantation Subdivision Drainage Analysis (P210703)','Luling','Postponed indefinitely, 2021',['2021-0221']),
('Drainage right of way along Davis Plantation (1998 grant) revoked and abandoned','Luling','2025',['2025-0267']),
('30-foot drainage servitude donated by private landowners; 15-foot servitude of 2013 revoked','Hahnville','2026. The parish report places a Vial property servitude in the Bamboo Street project (Hahnville 2 IG-1)',['2026-0128']),
('110 Ducayet Drive purchased for drainage improvements','Destrehan','2021',['2021-0017']),
('Public Works Drainage Maintenance Facility (P260401)','','Design $124,486.00, 2026',['2026-0159']),
]
for n,a,act,fs in U: A(f"| {n} | {a} | {act} | {'; '.join(s(f) for f in fs)} |\n")
A('''
Closed out in 2020 under pre-plan project numbers: Oak Street Pump Station Improvements
(P080502-18A, %s), Engineer's Canal Pump Station Improvements (P080502-22A, %s), Dunleith Canal
Bank Stabilization Phases 7 and 8 (%s; %s).

Hurricane-protection levee work is outside the plan and is not listed row by row: Magnolia Ridge,
Ellington, Kellogg and Cousins pump station structures, the Paradis Canal flood control structure,
the Sunset screen cleaner ($12,594,880.00 contract, %s) and Sunset pump station rehabilitation,
and the Cross Bayou Pump Station transfer. They are in `index/legistar_matters.csv`.

## Related council actions

- Post-construction stormwater standard set to a 25-year, 24-hour storm: %s.
- Council discussion items on drainage project status: %s; %s. No documents were read.
- State Treasury allocations for drainage: $300,000.00 Destrehan (%s), $500,000.00 Montz (%s),
  $1,000,000.00 (%s), $260,000.00 (%s).
- Statewide Flood Control Program pre-applications, project not named in the title: %s, %s, %s, %s.
- Judge Edward Dufresne Parkway Extension (P210706), a road project:
  %s; a 2022 planning agreement for $984,850.00 shows no enactment number (file 2022-0192).

## Updating this ledger

Run from the skill folder. Steps 1 to 3 pull new records; steps 4 to 6 rebuild the outputs. Do
not edit `index/status.csv` or this file by hand: both are regenerated.

```bash
# 1. New council legislation since the as-of date (rewrites the whole harvest; the count should only grow)
scripts/legistar_harvest.py
# 2. Read what is new, and get the attachment links for anything that matters
agendas.py track st-charles 2025-0184   # bayou:parish-council-agendas
# 3. Rebuild the project registry (calls the API once per built or under-construction project)
scripts/legistar_harvest.py projects
# 4. After editing the MATCH list and AS_OF in scripts/status_build.py
scripts/status_build.py
# 5. After editing the prose and dates in scripts/status_ledger_md.py
scripts/status_ledger_md.py
# 6. Confirm the plan index is untouched
scripts/mdp_index.py build
```

- **New council action on a plan row:** add the matter file number to that row's rule in the
  MATCH list in `scripts/status_build.py`, or add a rule (basin, plan ID, name fragment, status,
  built scope, matter files, note, independent source, its date). The script stops if a rule
  matches no plan row.
- **Status changes:** a construction contract moves a row to Under construction; a final change
  order plus a completion certificate moves it to Built. Read the certificate and the bid
  tabulation and put what was built in the built-scope field.
- **New parish capital report:** save it through a browser from the Capital Projects page into
  `$SCP_CIVICS_DATA/`, run `pdftotext -layout`, and read the page images, since the text run can't
  show which remark belongs to which row. Write a new `index/parish_tracker_<yyyy-mm>.csv` of the
  lines it prints, with `july_project` and `plan_rows` carried from the line each continues. Change
  the file names in `scripts/status_build.py` and `scripts/legistar_harvest.py`, and the dates
  they hard-code: the `parish_report_<date>` column and the "not listed" status label. A report can
  omit lines, as October's "Active Projects" did, so keep the older file and its column.
- **New budget:** the capital outlay lines are on the "Narrative Explanation of Capital Outlay"
  pages for funds 112, 123, 312 and 313 of the proposed or approved budget attached to the
  budget ordinance. Write a new `index/budget_<year>_<proposed|approved>.csv`.
- **Downloaded attachments:** keep them in `$SCP_CIVICS_DATA/council-attachments/`
  named by matter file number, with a `.txt` beside each (`ocrmypdf --force-ocr --sidecar` for
  scans).
- **Dates:** change `AS_OF` in `scripts/status_build.py` and the "As of" line and the
  searched-sources table in `scripts/status_ledger_md.py`. Move items out of "Still not
  searched" only when they have been searched.

Statuses follow `implementation-history.md`. "Built" here rests on a final change order plus a
Certificate of Substantial Completion or Final Acceptance attached to the matter (listed by
`agendas.py track st-charles <file no.>` in bayou:parish-council-agendas). Those attachments were read for the two Built rows; what they show against the plan row is in the `built_scope` column. The API prints attachment links with a wrong path; `track` prints the working form.
''' % (s('2020-0042'),s('2020-0177'),s('2020-0101'),s('2020-0313'),s('2024-0223'),s('2020-0317'),s('2020-0146'),s('2024-0319'),s('2021-0139'),s('2021-0140'),s('2021-0259'),s('2022-0165'),s('2020-0081'),s('2020-0082'),s('2020-0083'),s('2026-0147'),s('2021-0220')))
import collections as _c
PR=list(csv.DictReader(open(SK/'index/parish_projects.csv')))
cc=_c.Counter((r['kind'],r['phase']) for r in PR)
txt=''.join(L).replace('REGCOUNT','As built on 2026-11-03 from council titles harvested through 2026-10-13: %d projects. Drainage: %d in design, %d in construction, %d complete. Levee system: %d in design, %d in construction, %d complete.'%(len(PR),cc[('drainage','design')],cc[('drainage','construction')],cc[('drainage','complete')],cc[('levee system','design')],cc[('levee system','construction')],cc[('levee system','complete')]))
(SK/'references/status-ledger.md').write_text(txt)
print(len(''.join(L)))
