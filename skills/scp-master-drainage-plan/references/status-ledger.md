# Implementation status ledger

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
| Engineering agreements for the "2020 East Bank Master Drainage Plan" (Principal Engineering, P200601) and "2020 West Bank Master Drainage Plan" (T. Baker Smith, P200602) | Ord. 20-7-6 AMENDED [2020-0181, 2020-07-06]; Ord. 20-7-7 AMENDED [2020-0180, 2020-07-06] |
| Moratorium on major subdivisions until the drainage and sewer master plans for a community are accepted by council resolution, or 18 months | Ord. 20-8-18 [2020-0178, 2020-08-10] |
| East Bank amendments | Ord. 21-8-5 [2021-0196, 2021-08-09]; Ord. 22-4-6 [2022-0093, 2022-04-18] (design services, $80,400.00); Ord. 23-7-11 [2023-0163, 2023-07-10] ($569,737.50) |
| West Bank amendments | Ord. 21-8-8 [2021-0208, 2021-08-09]; Ord. 23-3-5 [2023-0053, 2023-03-27] ($506,218.25) |
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
| Built (one part only, one match unconfirmed) | 2 |
| Under construction | 3 |
| Funded (design, survey or grant only) | 34 |
| Application submitted | 0 |
| No record found | 330 |

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
| almedia p4 | 1-2 | Fairfield Pump Station Replacement | $4,500,000 | Funded | Res. 6623 [file 2022-0083, 2022-04-04]; Res. 6842 [file 2025-0215, 2025-08-04]; Res. 6843 [file 2025-0218, 2025-08-04]; Ord. 25-11-3 [file 2025-0318, 2025-11-03]; Ord. 25-11-6 [file 2025-0324, 2025-11-03]; Res. 6918 [file 2026-0244, 2026-07-27] | State capital outlay agreement for Fairfield and Oakland Pump Station Discharge Improvements (FP&C 50-J45-21-02); Louisiana Watershed Initiative scope and budget revision (2025); Fairfield and Oakland Drainage Improvements (P251001) engineering not to exceed $787,285.30; grant applications to EDA (2025) and Delta Regional Authority ($500,000.00, 2026). No construction contract found. Titles say "discharge" and "conveyance" improvements, not station replacement. Independent: Corpus: st-rose-drainage-townhall-11123.md p13, $825,000 capital outlay marked awarded as of 2023-11-01. State Round 2 list: Fairfield and Oakland Pump Station Upgrades, $5.77 million, conditional on a feasibility study and full application (https://watershed.la.gov/round-2) |
| almedia p4 | 1-3 | Oakland Pump Station Replacement | $6,750,000 | Funded | Res. 6623 [file 2022-0083, 2022-04-04]; Res. 6842 [file 2025-0215, 2025-08-04]; Res. 6843 [file 2025-0218, 2025-08-04]; Ord. 25-11-3 [file 2025-0318, 2025-11-03]; Ord. 25-11-6 [file 2025-0324, 2025-11-03]; Res. 6918 [file 2026-0244, 2026-07-27] | Same council record as Almedia 1-2. Independent: Corpus: st-rose-drainage-townhall-11123.md p13 |
| amasellers p2 | IG-1 | Primary Culvert and Channel Improvements | $1,157,000/$1,613,200 | Funded | Ord. 22-6-7 [file 2022-0171, 2022-06-20] | Design or survey contract only; no construction contract found. U.P. Railroad Drainage Ditch and Outfall Improvements (P220205). The parish report calls it Priority 1 from the Ama watershed without naming the improvement group, so it is listed against both Priority 1 groups. |
| amasellers p2 | IG-2 | Secondary Culvert and Channel Improvements | $424,100/$646,500 | Funded | Ord. 22-6-7 [file 2022-0171, 2022-06-20] | Same council project as Ama-Sellers IG-1. |
| dianne-place p4 | 1-1 | Dianne Place Pump Station and Sump Upgrade | $4,650,000 | Funded | Parish capital projects report, 2026-07-31 | No council matter found by title. The parish report lists Dianne Pump Station (P241105), engineering agreement 12/19/2024, status Conceptual; preliminary report received 6/12/2025. |
| hahnville-i p2 | IG-1 | King Street | $615,400/$679,600 | Funded | Ord. 22-3-7 AMENDED [file 2022-0057, 2022-03-07]; Ord. 23-11-6 [file 2023-0287, 2023-11-06]; Ord. 25-8-10 [file 2025-0232, 2025-08-18] | Design or survey contract only; no construction contract found. King and Hahn Street Drainage Improvements (P220202): engineering not to exceed $432,650.00, plus amendments of $149,707.00 and $52,767.00. |
| hahnville-i p2 | IG-2 | Hahn Street | $394,100/$516,400 | Funded | Ord. 22-3-7 AMENDED [file 2022-0057, 2022-03-07]; Ord. 23-11-6 [file 2023-0287, 2023-11-06]; Ord. 25-8-10 [file 2025-0232, 2025-08-18] | Same council project as Hahnville 1 IG-1. |
| hahnville-ii p2 | IG-1 | Bamboo Street | $1,245,000/$1,327,700 | Funded | Ord. 23-5-3 [file 2023-0100, 2023-05-08] | Survey contract only: Bamboo Street Drainage Improvements (P221101), $26,350.00. No design or construction contract found. |
| mimosa-willowdale p2 | (none) | Willowdale Pump Station | TBD | Funded | Ord. not enacted (Public Hearing) [file 2026-0328, 2026-09-28] | Design or survey contract only; no construction contract found. Willowdale Pump Station Sump Improvements (P241102): Amendment No. 2 (not to exceed $315,610.00, overall $351,560.00) was at public hearing as of this ledger; the original agreement was not found by title search. The plan prints this row's cost as TBD. |
| montz p4 | 1-1 | 200 CFS Pump Station on CC Canal | $11,300,000 | Under construction | Ord. 21-4-7 AMENDED [file 2021-0097, 2021-04-19]; Res. 6706 [file 2023-0169, 2023-07-10]; Ord. 25-4-13 AMENDED [file 2025-0107, 2025-04-21]; Ord. 25-11-9 [file 2025-0339, 2025-11-17] | Montz Pump Station No. 1 (P210301, CPRA PO-0200). Contract $13,479,955.00 (Sealevel); Change Order 1 adds $111,702.07. The parish report of 2026-07-31 calls this station "Montz Pump Station (at CN Railroad)"; the plan row puts its station on the CC Canal downstream of the railroad. The match rests on that location and is not confirmed from plans. Independent: Herald Guide, 2026-01: Montz 1 scheduled for completion end of 2026 (https://www.heraldguide.com/featured/185011) |
| montz p4 | 1-5 | Jack-and-Bore at CN Railroad and Evangeline Canal | $691,200 | Funded | Ord. 20-12-12 [file 2020-0344, 2020-12-21]; Ord. 21-8-14 AMENDED [file 2021-0214, 2021-08-23]; Ord. 25-8-3 [file 2025-0200, 2025-08-04] | Design or survey contract only; no construction contract found. Montz Railroad Culverts and Drainage Improvements (P201101); Evangeline Road & CN Railroad Box Culvert (P210701), contract value now $389,718.34. |
| montz p4 | 1-6 | Jack-and-Bore at CN Railroad and Hollywood Canal | $172,800 | Funded | Ord. 20-12-12 [file 2020-0344, 2020-12-21] | Design or survey contract only; no construction contract found. Montz Railroad Culverts and Drainage Improvements (P201101). The title does not name the crossing. |
| montz p8 | 3-1 | Additional Pump Station | $19,200,000 | Under construction | Ord. 21-11-4 AMENDED [file 2021-0267, 2021-11-15]; Ord. 25-7-11 [file 2025-0188, 2025-07-21]; Ord. 25-7-15 [file 2025-0193, 2025-07-21] | Montz Pump Station No. 2 and Drainage Improvements (P210806). Contract $18,882,865.00 (Sealevel); the bid included the US 61 canal improvements (P230602). The parish report of 2026-07-31 calls it "Montz Pump Station #2 (at Airline)" and says the Corps permit requires removal of the Prescott Pump Station after startup, which matches the plan row (340 CFS station between the KCS railroad and Airline Highway, existing station removed). Independent: Herald Guide, 2026-01: Montz II scheduled for completion early 2027 (https://www.heraldguide.com/featured/185011) |
| montz p8 | 3-2 | Concrete Box Culvert Under Evangeline Road along Airline HighwayDitch | $234,000 | Funded | Ord. 21-8-14 AMENDED [file 2021-0214, 2021-08-23]; Ord. 25-8-3 [file 2025-0200, 2025-08-04] | Design or survey contract only; no construction contract found. Evangeline Road & CN Railroad Box Culvert (P210701). The same council project is listed against Montz 1-5; the title does not say which plan row it is. |
| new-sarpy p4 | 1-1 | Schexnaydre Pump Station Upgrade | $1,500,000 | Funded | Ord. 22-6-10 [file 2022-0174, 2022-06-20]; Ord. 20-8-10 AMENDED [file 2020-0228, 2020-08-10]; Ord. 21-10-3 [file 2021-0224, 2021-10-18] | Schexnaydre Pump Station Improvements (P220207): engineering $20,500.00 (2022), no construction contract found. An earlier project at the same station (P190502, contract $654,016.00) closed with a final change order in 2021-10; whether the plan row is that work or a further upgrade is not established. |
| new-sarpy p4 | 1-2 | New Sarpy Pump Station Upgrade | $3,740,000 | Funded | Ord. 22-6-8 AMENDED [file 2022-0172, 2022-06-20]; Ord. 24-7-21 [file 2024-0248, 2024-07-22] | Design or survey contract only; no construction contract found. New Sarpy Pump Station Improvements (P220203), amended to not to exceed $471,762.50. |
| new-sarpy p6 | 2-1 | 1-60" Steel Pipe under CN RR at Schexnaydre Canal | $604,800 | Funded | Ord. 25-4-1 [file 2025-0081, 2025-04-07] | Design or survey contract only; no construction contract found. New Sarpy CN Culvert Crossings (P250301), not to exceed $692,052.00. The title does not say which crossings. |
| new-sarpy p6 | 2-2 | 1-60" Steel Pipe under CN RR West of Schexnaydre Canal | $302,400 | Funded | Ord. 25-4-1 [file 2025-0081, 2025-04-07] | Design or survey contract only; no construction contract found. New Sarpy CN Culvert Crossings (P250301), not to exceed $692,052.00. The title does not say which crossings. |
| new-sarpy p6 | 2-4 | 2-60" Steel Pipe under CN RR at New Sarpy Mid Canal | $561,600 | Funded | Ord. 25-4-1 [file 2025-0081, 2025-04-07] | Design or survey contract only; no construction contract found. New Sarpy CN Culvert Crossings (P250301), not to exceed $692,052.00. The title does not say which crossings. |
| new-sarpy p6 | 2-6 | 1-48" Steel Pipe under CN RR at Vans Lane | $275,000 | Funded | Ord. 25-4-1 [file 2025-0081, 2025-04-07] | Design or survey contract only; no construction contract found. New Sarpy CN Culvert Crossings (P250301), not to exceed $692,052.00. The title does not say which crossings. |
| new-sarpy p6 | 2-7 | 2-60" Steel Pipe under CN RR at Troxclair Canal | $345,600 | Funded | Ord. 25-4-1 [file 2025-0081, 2025-04-07] | Design or survey contract only; no construction contract found. New Sarpy CN Culvert Crossings (P250301), not to exceed $692,052.00. The title does not say which crossings. |
| new-sarpy p6 | 2-8 | 2-60" Pipe under CN RR at Cotton Canal | $345,600 | Funded | Ord. 25-4-1 [file 2025-0081, 2025-04-07] | Design or survey contract only; no construction contract found. New Sarpy CN Culvert Crossings (P250301), not to exceed $692,052.00. The title does not say which crossings. |
| new-sarpy p6 | 2-10 | 2-60" Steel Pipe under CN RR East of West Easy St. | $345,600 | Funded | Ord. 25-4-1 [file 2025-0081, 2025-04-07] | Design or survey contract only; no construction contract found. New Sarpy CN Culvert Crossings (P250301), not to exceed $692,052.00. The title does not say which crossings. |
| norco p4 | 1-1 | Engineer's Canal Pump Station Upgrade (Alternative 1) | $3,650,000 | Funded | Ord. 22-6-9 AMENDED [file 2022-0173, 2022-06-20]; Ord. 23-7-10 [file 2023-0162, 2023-07-10]; Ord. 23-12-10 [file 2023-0343, 2023-12-18]; Ord. 24-2-7 [file 2024-0049, 2024-02-05]; Res. 6797 [file 2024-0354, 2024-11-04]; Ord. 26-8-13 [file 2026-0265, 2026-08-24] | Engineers Canal Pump Station Improvements (P220206): planning, design (not to exceed $716,508.00), Construction Manager at Risk pre-construction agreement $2,550,000.00 (Cajun Industries), state allocation $150,000.00, design refinement (P260803) not to exceed $1,423,978.00, and purchase of 679 West Pine Street. No construction contract found. Titles do not say which of the plan's two alternatives for 1-1 is being designed. |
| norco p4 | 1-1 | Additional Pump Station along Engineers Canal downstream of Airline Highway (Alternative 2) | $14,980,000 | Funded | Ord. 22-6-9 AMENDED [file 2022-0173, 2022-06-20]; Ord. 23-7-10 [file 2023-0162, 2023-07-10]; Ord. 23-12-10 [file 2023-0343, 2023-12-18]; Ord. 24-2-7 [file 2024-0049, 2024-02-05]; Res. 6797 [file 2024-0354, 2024-11-04]; Ord. 26-8-13 [file 2026-0265, 2026-08-24] | Engineers Canal Pump Station Improvements (P220206): planning, design (not to exceed $716,508.00), Construction Manager at Risk pre-construction agreement $2,550,000.00 (Cajun Industries), state allocation $150,000.00, design refinement (P260803) not to exceed $1,423,978.00, and purchase of 679 West Pine Street. No construction contract found. Titles do not say which of the plan's two alternatives for 1-1 is being designed. |
| norco p4 | 1-3 | 2-72" Pipes crossing KCS RR at Engineer's Canal | $1,761,200 | Funded | Ord. 22-7-3 [file 2022-0188, 2022-07-05] | Design or survey contract only; no construction contract found. Clayton's Pond Outfall Improvements (P220204), which the parish report ties to Priority 3 and 4 of Norco Phase 1 and says the parish plans to cancel with the consultant. The report also lists an unfunded Engineers Canal Crossing at CPKC Railroad (three 72-inch culverts, status Negotiations), which matches this row's scope. |
| norco p4 | 1-4 | Connect Engineers Canal and Pond between KCS RR and AirlineHighway | $478,200 | Funded | Ord. 22-7-3 [file 2022-0188, 2022-07-05] | Same council project as Norco 1-3 (Clayton's Pond Outfall Improvements, P220204). |
| ormond p4 | 1-1 | Destrehan #2 Sump Improvements | $3,300,000 | Built | Ord. 23-6-10 AMENDED [file 2023-0141, 2023-06-19]; Ord. 24-4-4 [file 2024-0119, 2024-04-01]; Ord. 24-10-2 [file 2024-0320, 2024-10-07]; Ord. 25-2-9 [file 2025-0026, 2025-02-24]; Ord. 22-12-7 AMENDED [file 2022-0338, 2022-12-05]; Ord. 24-6-14 [file 2024-0202, 2024-06-17] | Probable match. Two council projects at this station: Destrehan P.S. No. 2 Conveyance Improvements (P181101), contract $9,190,697.00, Change Order 3 (Final) 2025; and Hydraulic Bottleneck Near Destrehan P.S. No. 2 (P190507), contract $2,264,960.00, Change Order 2 (Final) 2024. Certificates of Substantial Completion: P181101 on 2024-10-21 (issued 2024-10-28), P190507 on 2024-04-03 (issued 2024-04-10). P181101 bid was a $7,426,997.00 base bid plus $1,763,700.00 Alternate 1. The two contracts total $11,455,657.00 before change orders against a plan cost of $3,300,000. Independent: stcharlesparish.gov news calls it "the recently improved Destrehan No. 2 Pump Station" (https://www.stcharlesparish.gov/Home/Components/News/News/15609/26) |
| ormond p4 | 1-2 | Dunleith Canal Sheet Piles | $3,437,100 | Funded | Ord. 20-8-13 AMENDED [file 2020-0232, 2020-08-10]; Ord. 25-2-10 [file 2025-0027, 2025-02-24] | Design or survey contract only; no construction contract found. Carriage/Dunleith Canals Drainage Structure (P200706), contract value now not to exceed $473,378.00. Council title describes a drainage structure; plan row is sheet piles. |
| ormond p4 | 1-3 | Carriage Lane Canal Sheet Piles | $16,966,248 | Funded | Ord. 20-8-12 [file 2020-0231, 2020-08-10]; Ord. 20-8-13 AMENDED [file 2020-0232, 2020-08-10]; Ord. 20-8-15 [file 2020-0234, 2020-08-10] | Design or survey contract only; no construction contract found. Carriage Canal Widening (P200705); Carriage/Dunleith structure (P200706); Drainage Structure for Carriage, Houmas and A Canals (P200707). Titles describe widening and structures; plan row is sheet piles. |
| ormond p4 | 1-4 | Carriage Lane Canal Sheet Piles | $2,755,175 | Funded | Ord. 20-8-12 [file 2020-0231, 2020-08-10]; Ord. 20-8-13 AMENDED [file 2020-0232, 2020-08-10]; Ord. 20-8-15 [file 2020-0234, 2020-08-10] | Design or survey contract only; no construction contract found. Same council projects as Ormond 1-3. |
| ormond p4 | 1-5 | Hill Heights Ditch Sheet Piles | $4,973,750 | Built | Ord. 22-3-14 [file 2022-0068, 2022-03-21]; Ord. 23-7-1 [file 2023-0152, 2023-07-10] | Probable match. Hill Heights Drainage Improvements - Destrehan (P190802): contract with APC Construction, LLC dated 2023-02-13 for $844,383.00; Change Order 1 (Final) brought it to $728,098.20. Substantial completion 2023-05-08; final acceptance 2023-06-15. The contract is an attachment to files 2022-0068 and 2023-0152; no separate award ordinance was found by title. Final cost is against a plan cost of $4,973,750 for the full length. |
| ormond p4 | 1-6 | Canal A Sheet Piles | $6,430,570 | Funded | Ord. 20-8-14 [file 2020-0233, 2020-08-10]; Ord. 20-8-15 [file 2020-0234, 2020-08-10] | Design or survey contract only; no construction contract found. Canal A Improvements (P200704); Drainage Structure for Carriage, Houmas and A Canals (P200707). |
| ormond p4 | 1-7 | Houma's Canal Sheet Piles | $1,914,000 | Funded | Ord. 20-8-15 [file 2020-0234, 2020-08-10] | Design or survey contract only; no construction contract found. Drainage Structure for Carriage, Houmas and A Canals (P200707). |
| ormond p4 | 1-8 | Ormond Oak Ditch Sheet Piles | $7,953,000 | Funded | Ord. 22-12-6 [file 2022-0337, 2022-12-05]; Ord. not enacted (Postponed Indefinitely) [file 2023-0289, 2023-11-06] | Design or survey contract only; no construction contract found. Ormond Oaks Channel (P210203), not to exceed $29,900.00; a 2023 amendment to $67,403.00 shows no enactment number. |
| ormond p6 | 2-1 | CN RR Jack & Bore | $3,888,000 | Under construction | Ord. 20-9-5 [file 2020-0258, 2020-09-21]; Res. 6707 [file 2023-0170, 2023-07-10]; Ord. 25-7-9 AMENDED [file 2025-0184, 2025-07-21]; Ord. 26-1-4 [file 2025-0393, 2026-01-12]; Ord. 26-8-5 [file 2026-0253, 2026-08-10] | Ormond CN Railway Culverts (P200801). Contract $10,542,425.00 (BLD Services); Change Order 1 adds $1,005,921.76. State CDBG-MIT agreement $6,314,616.00. Independent: stcharlesparish.gov news: groundbreaking 2025-12-09; first of five bores set for 2026-08-26 (https://www.stcharlesparish.gov/Home/Components/News/News/15862/26) |
| st-rose p4 | 1-2 | Oak St Pump Station and Sump Replace and Upgrade | $8,500,000 | Funded | Ord. 25-5-11 [file 2025-0138, 2025-05-19] | Design or survey contract only; no construction contract found. Oak Street Pump Station Improvements (P241104), $89,500.00. The corpus town hall deck (p13) lists a Louisiana Watershed Initiative application for Oak Street; no award found. |
| st-rose p20 | 1-2 | Oak St Pump Station and Sump Replace and Upgrade | $8,500,000 | Funded | Ord. 25-5-11 [file 2025-0138, 2025-05-19] | Design or survey contract only; no construction contract found. Oak Street Pump Station Improvements (P241104), $89,500.00. The corpus town hall deck (p13) lists a Louisiana Watershed Initiative application for Oak Street; no award found. |
| turtle-pond p6 | 2-1 | Turtle Pond Pump Station Replace and Upgrade | $8,470,000 | Funded | Ord. 25-9-8 [file 2025-0271, 2025-09-22]; Res. 6861 [file 2025-0292, 2025-09-22]; Ord. 25-11-5 [file 2025-0323, 2025-11-03]; Res. 6887 [file 2026-0035, 2026-01-26]; Ord. 26-6-6 [file 2026-0174, 2026-06-15] | Design or survey contract only; no construction contract found. Turtle Pond Pump Station and Upstream Drainage Improvements (P250901), engineering not to exceed $609,085.50; Louisiana Watershed Initiative scope and budget revision (2025); Local Government Assistance Program application (2026). The 2027 proposed budget carries $15,000,000 for "LWI - Round 2 Turtle Pond Pump Station" in fund 313 and $4,342,441 in fund 112. Independent: State Round 2 list: Turtle Pond Pump Station Upgrades, $9.23 million, conditional on a feasibility study and full application (https://watershed.la.gov/round-2) |

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

As built on 2026-11-03 from council titles harvested through 2026-10-13: 82 projects. Drainage: 38 in design, 12 in construction, 7 complete. Levee system: 3 in design, 2 in construction, 7 complete.

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
| Primrose Canal Cleaning and Improvements (P210202) | Mimosa (West Bank) | Phase 1A contract $2,757,000.00, Change Order 2 (Final) 2024; Phase 1B contract $1,507,765.04, 2026 | Ord. 23-12-11 AMENDED [2023-0344, 2023-12-18]; Ord. 24-9-8 [2024-0302, 2024-09-23]; Ord. 26-1-11 [2025-0401, 2026-01-26]; Res. 6849 [2025-0264, 2025-09-08] |
| Ormond Center Drainage Improvements (P190505) | Ormond | Contract $3,097,730.00; Change Order 1 adds $271,095.41; Change Order 2 at public hearing | Ord. 26-1-3 AMENDED [2025-0392, 2026-01-12]; Ord. 26-8-3 [2026-0251, 2026-08-10]; Ord. (none: Public Hearing) [2026-0325, 2026-09-28] |
| Murray Hill Drive and Destrehan Drive Drainage Improvements (P201001) | Destrehan | Contract $2,112,258.00, 2025 | Ord. 21-3-3 AMENDED [2021-0057, 2021-03-15]; Ord. 25-6-5 [2025-0152, 2025-06-02] |
| Engineer's Canal Phase 1 Bank Stabilization (P190301) | Norco | Contract $1,405,350.00; Change Order 1, 2024. Plan rows Norco 2-1 and 2-7 are "reshape and clean", not bank stabilization | Ord. 23-11-13 AMENDED [2023-0311, 2023-11-20]; Ord. 24-9-5 [2024-0288, 2024-09-09] |
| Fifth Street Drainage Improvements (P190506) |  | Contract $1,182,515.00; Change Order 1, 2022 | Ord. 21-5-11 AMENDED [2021-0132, 2021-05-17]; Ord. 22-7-4 [2022-0189, 2022-07-05] |
| Lakewood Pump Station Discharge Modifications (P241106) | Luling | Contract $959,300.00, 2026 | Ord. 25-3-5 [2025-0050, 2025-03-10]; Ord. 26-9-8 [2026-0266, 2026-09-14] |
| Kinler and Paul Frederick Roadway and Drainage Improvements (P210704) | Luling | Phase I contract $728,906.00, 2026 | Ord. 22-1-2 AMENDED [2021-0225, 2022-01-10]; Ord. 26-7-3 [2026-0196, 2026-07-13] |
| Kinler St. Canal Improvements (P250705) | Luling | Design $52,101.00, 2025 | Ord. 25-9-1 [2025-0247, 2025-09-08] |
| Ama Drainage Improvements Rebid (P150801-2) | Ama | Contract $2,752,705.00; Change Order 1 and Final 2023. A 2015 project; may overlap Ama-Sellers IG-1 or IG-2, scope not compared | Ord. 22-2-5 AMENDED [2022-0021, 2022-02-07]; Ord. 23-12-7 [2023-0325, 2023-12-04] |
| Mimosa and Lagatutta Drainage Improvements (P090904) |  | Change Order 1, 2022. A 2009 project | Ord. 22-9-5 [2022-0238, 2022-09-19] |
| Cousins Canal Bank Stabilization (P241103) | Luling | Design not to exceed $618,000.00, 2025 | Ord. 25-2-16 [2025-0033, 2025-02-24] |
| KCS Canal Drainage Improvements (P230401) |  | Design not to exceed $260,348.00, 2023. Candidate rows: Almedia 4-1, 4-2 (KS RR Canal) or Norco KCS rows | Ord. 23-7-4 [2023-0156, 2023-07-10] |
| US 61 Canal Improvements (P230602) | Montz | Design not to exceed $48,656.25, 2023; the parish report says it was bid inside Montz Pump Station No. 2 | Ord. 23-7-8 [2023-0160, 2023-07-10] |
| Engineers and Good Hope Canals Pipeline Location Investigation (P230402) | Norco | $112,315.00, amended 2025 | Ord. 23-7-6 AMENDED [2023-0158, 2023-07-10]; Ord. 25-5-12 [2025-0139, 2025-05-19] |
| River Point - River Village Drainage Improvements (P210805) |  | Design 2021; grant application 2024 | Ord. 21-11-1 [2021-0266, 2021-11-01]; Res. 6753 [2024-0065, 2024-02-05] |
| Riverbend Hydraulic Design (P240701); Riverbend Subsurface Drainage (P250702) | St. Rose | Analysis and design, 2024-2025. Candidate rows: Almedia 1-4, Turtle Pond 3-1, 3-6 | Ord. 24-12-6 [2024-0385, 2024-12-02]; Ord. 25-8-5 [2025-0202, 2025-08-04] |
| Lemoine Lane, Hirsch Street and St. Mark Street Drainage Improvements (P220201) | Ama | Design not to exceed $194,931.00, 2022 | Ord. 22-6-6 [2022-0170, 2022-06-20] |
| U.P. Railroad Drainage Ditch & Outfall Improvements (P220205) |  | Design not to exceed $194,931.00, 2022 | Ord. 22-6-7 [2022-0171, 2022-06-20] |
| Clayton's Pond Outfall Improvements (P220204) |  | Design not to exceed $141,179.00, 2022 | Ord. 22-7-3 [2022-0188, 2022-07-05] |
| JCJR Outfall Ditches (P250701) |  | $70,248.00, 2025. JCJR St. Charles, LLC is the Fashion Plantation rezoning applicant (Hahnville), so this may relate to Hahnville 2 IG-3 | Ord. 25-8-6 [2025-0204, 2025-08-04] |
| Milling Drainage Improvements (P260501) |  | $85,575.00, 2026 | Ord. 26-6-4 [2026-0172, 2026-06-01] |
| Davis Plantation Subdivision Drainage Analysis (P210703) | Luling | Postponed indefinitely, 2021 | Ord. (none: Postponed Indefinitely) [2021-0221, 2021-08-23] |
| Drainage right of way along Davis Plantation (1998 grant) revoked and abandoned | Luling | 2025 | Ord. 25-9-4 [2025-0267, 2025-09-22] |
| 30-foot drainage servitude donated by private landowners; 15-foot servitude of 2013 revoked | Hahnville | 2026. The parish report places a Vial property servitude in the Bamboo Street project (Hahnville 2 IG-1) | Ord. 26-4-7 [2026-0128, 2026-04-20] |
| 110 Ducayet Drive purchased for drainage improvements | Destrehan | 2021 | Ord. 21-1-7 [2021-0017, 2021-01-25] |
| Public Works Drainage Maintenance Facility (P260401) |  | Design $124,486.00, 2026 | Ord. 26-5-2 [2026-0159, 2026-05-18] |

Closed out in 2020 under pre-plan project numbers: Oak Street Pump Station Improvements
(P080502-18A, Ord. 20-2-3 [2020-0042, 2020-02-17]), Engineer's Canal Pump Station Improvements (P080502-22A, Ord. 20-7-4 [2020-0177, 2020-07-06]), Dunleith Canal
Bank Stabilization Phases 7 and 8 (Ord. 20-5-4 [2020-0101, 2020-05-04]; Ord. 20-11-6 [2020-0313, 2020-11-16]).

Hurricane-protection levee work is outside the plan and is not listed row by row: Magnolia Ridge,
Ellington, Kellogg and Cousins pump station structures, the Paradis Canal flood control structure,
the Sunset screen cleaner ($12,594,880.00 contract, Ord. 24-7-3 AMENDED [2024-0223, 2024-07-08]) and Sunset pump station rehabilitation,
and the Cross Bayou Pump Station transfer. They are in `index/legistar_matters.csv`.

## Related council actions

- Post-construction stormwater standard set to a 25-year, 24-hour storm: Ord. 20-12-7 [2020-0317, 2020-12-07].
- Council discussion items on drainage project status: Ord. (none: Filed) [2020-0146, 2020-06-01]; Ord. (none: Filed) [2024-0319, 2024-10-21]. No documents were read.
- State Treasury allocations for drainage: $300,000.00 Destrehan (Res. 6559 [2021-0139, 2021-05-17]), $500,000.00 Montz (Res. 6560 [2021-0140, 2021-05-17]),
  $1,000,000.00 (Res. 6587 [2021-0259, 2021-10-18]), $260,000.00 (Res. 6638 [2022-0165, 2022-06-06]).
- Statewide Flood Control Program pre-applications, project not named in the title: Res. 6481 [2020-0081, 2020-03-09], Res. 6482 [2020-0082, 2020-03-09], Res. 6483 [2020-0083, 2020-03-09], Res. 6906 [2026-0147, 2026-04-20].
- Judge Edward Dufresne Parkway Extension (P210706), a road project:
  Ord. 21-8-15 [2021-0220, 2021-08-23]; a 2022 planning agreement for $984,850.00 shows no enactment number (file 2022-0192).

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
