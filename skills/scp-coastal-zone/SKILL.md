---
name: scp-coastal-zone
description: St. Charles Parish, Louisiana's own coastal permitting under its Local Coastal Program and Code Chapter 26. Reads the Coastal Zone Advisory Committee's agendas into a permit list (P-number, SCP number, local or state concern, EXEMPT, NDSI or CUP), checks a site or project footprint against the state's coastal zone, Five Foot Contour and Fastlands maps for the "wholly" exemption test, lists mapped coastal use permits near a place, looks up one permit, and dates the comment, hearing, appeal and reconsideration clocks. Searches the converted Local Coastal Program document (goals, the 14 Environmental Management Units, administration) with PDF page. Use for any coastal use permit, CUP, joint permit application, exemption or "no direct and significant impact" question in the parish, to find whether a project is local or state concern, when to comment or appeal, or what the program says about a place.
argument-hint: "<permit number, applicant, address or lat,lon, or a question about the program>"
allowed-tools: Bash, Read, Grep, Glob, Skill, AskUserQuestion, WebFetch
---

# St. Charles Parish coastal zone

The parish runs its own coastal program. It issues coastal use permits for uses of local concern and reviews the state's permits for uses of state concern. Everything here is research, not legal advice. The skill never files a comment, appeal or request.

```bash
CZ="${CLAUDE_PLUGIN_ROOT}/skills/scp-coastal-zone"
python3 "$CZ/scripts/coastal.py" czac [--since 2026-01-01] [--term Entergy] [--permit P20260816] [--json]
python3 "$CZ/scripts/coastal.py" site "<address>" | --point LAT,LON | --geojson footprint.geojson
python3 "$CZ/scripts/coastal.py" near "<address>" | --point LAT,LON [--radius 1000] [--since 2020]
python3 "$CZ/scripts/coastal.py" permit P20250727
python3 "$CZ/scripts/coastal.py" clock --notice YYYY-MM-DD [--decision YYYY-MM-DD] [--activity YYYY-MM-DD]
LCP="$CZ/corpus"   # st-charles-local-coastal-program.md, images/, STATUS.md
```

How the program works is in `references/program.md`: who decides, local versus state concern, exemptions, the process and its clocks, appeals and court review, and enforcement. Read it before answering a process question.

## Commands

- **`czac`** parses Legistar body 189 agendas. They begin 2025-07-10; earlier committee agendas are not on Legistar. Ord. 25-4-4 gave the committee's work to the Planning Commission for up to six months in 2025, so check P&Z agendas for that gap (`scp-civics:scp-land-use-process`).
  - Each row is either *open for comment*, where the code is the staff's proposed call, or a *determination*, from "last month's" list.
  - Codes are copied as printed. NDSI means no direct and significant impact. The meaning of RFD is not stated anywhere, so don't expand it.
  - A row whose concern is `?` had neither a tag nor a heading.
- **`site`** reports, for a point or footprint:
  - the state coastal zone (the whole parish is inside it)
  - any mapped fastland, with its raw STATUS
  - the Five Foot Contour class
  - the parish's NWI wetlands and DFIRM flood zone
  - the community and council district
  - USGS ground elevation, for context only

  The statute's exemption needs the activity to be *wholly* on high land or in a fastland (R.S. 49:214.34(A)). A point can't show that, so ask for the footprint as GeoJSON: lon, lat in WGS84, including access, staging and borrow areas. The footprint test samples vertices plus an interior grid. The output never says more than "an exemption may apply; OCM decides".
- **`near`** lists mapped permits from OCM's point, polygon and line layers. State and parish permits share the P-number series. The line layer's company and status stop in 2023.
- **`permit`** gives:
  - the permit's mapped location and acres
  - the community at its centre
  - every committee agenda row that names it
  - its SONRIS document link

  The SONRIS link often times out for scripts. Use `bayou:sonris-doc-search` if installed; without bayou, open the link in a browser.
- **`clock`** dates the Chapter 26 periods from the notice, decision or activity date. The counting rule (calendar days, trigger day not counted, weekends and holidays flagged but not moved) is this skill's convention. Say so, and tell the user to file early.

Exit codes: 0 answered, 1 no match, 2 a source was unreachable. On exit 2, say which source failed and what was not checked.

## The program document (corpus)

`$LCP/st-charles-local-coastal-program.md` is the 2016 Local Coastal Program converted page by page. `## Page N` is the PDF page, followed by the printed page where the page carries one. Read `$LCP/STATUS.md` before relying on a table or figure description. Search with `rg -n -i "<term>" "$LCP"/*.md`.

| PDF pages | Printed | Content |
|---|---|---|
| 31-74 | 1-x | Environmental setting |
| 75-86 | 2-x | Principal resources (Bonnet Carré, Davis Pond, LaBranche, wildlife management areas) |
| 87-100 | 3-x | Socioeconomic characteristics |
| 101-108 | 4-x | Environmental issues |
| 109-124 | 5-x | Goals 1-8 with objectives and policies |
| 125-204 | 6-x | The 14 Environmental Management Units. Table 6-1 is on PDF p. 126. Each unit has terrain, soils and land-use maps and "Specific Goals and Objectives". |
| 205-226 | 7-x | Administration: local and state concern, exemptions, appeals, performance standards, special areas (7-16), uses of greater than local benefit (7-17), federal consistency, consistency with the 2030 plan (7-22) |
| 227-236 | 8-x | Public participation |
| 237-248 | App. A | Definitions |
| 249-276 | App. B | The **2015** ordinance text, not current law. Read current Chapter 26 with `scp-civics:scp-ordinances` (`code_search.py get 26-6`). |
| 277-285 | Apps. C-D | Public participation record; references |

The 14 units are:

- **East bank:**
  1. East Bank Community
  2. Montz Urbanized Levee
  3. East LaPlace Wetland
  4. Bonnet Carré Floodway
  5. New Sarpy Swamp
  6. Ormond Swamp
  7. LaBranche Wetlands
- **West bank:**
  8. West Bank Community
  9. Bayou Gauche Community
  10. Paradis Mitigation Area
  11. Allemand Wetland
  12. Salvador Management Area
  13. Couba Island Wetland
  14. Davis Management Unit

No GIS layer holds them. To place a site in a unit, open the chapter 6 map image itself (`$LCP/images/`) and read it against `site` output. Call the result a visual reading. The figure descriptions in the corpus are machine-generated. A first pass got most placements wrong, and a second model then checked every description against its image. Still, don't rely on what a description says about where something lies or which colour means what. Each description's label says how it was checked.

## Steps

1. **Identify the permit.** Herald Guide notices carry `SCP-yyyy-nn` and the state's `P{yyyy}{nnnn}`. If the user has neither, run `near` at the place and `czac --term <applicant>`.
2. **Local or state concern.** Take it from the agenda tag, then check it against the R.S. 49:214.25 list in `references/program.md`.
   - **State concern** (pipelines, mineral activity, multi-parish work, state-funded projects): OCM decides, and the parish only comments. Use OCM's public notices page or `bayou:la-coastal-use-permits` for the state record.
   - **Local concern:** the parish decides, and the local clocks and appeals apply.
3. **Clocks.** Find the official journal notice date: the Herald Guide's "Notice of Pending Application", searched through `scp-civics:scp-watch` or `hg_legals.py` in `scp-civics:scp-land-use-process`. Then run `clock`.
   - The committee's determinations list comes after the comment window, and often after the 15-day appeal window, so never treat it as notice.
   - **Issue preservation:** an administrative appeal can't raise issues that weren't raised during the application, with narrow exceptions (Sec. 26-9(b)(6)). Comments must cover every issue the user may later appeal.
4. **Site facts.** Run `site` on the footprint. Add the EMU, its goals (chapter 6) and the program's policies (chapters 5 and 7) that bear on the work. The parish reviews permits for consistency with them.
5. **Answer** with:
   - the permit facts (numbers, concern, codes, meeting dates);
   - the dates and their sources;
   - the program text, with PDF page;
   - **Established**, each fact with its source and the date read;
   - **Not established**, each gap with what was searched.

## Rules

- **Dates and currency:**
  - Date every live read ("Legistar read 2026-11-20").
  - Chapter 26 text comes from the code, never from LCP Appendix B.
  - The agency is now the Department of Conservation and Energy. Older records say DNR.
- **Facts not to state:**
  - The date of final state and federal approval of the program is not established (see `references/program.md`).
  - Don't reconcile the two court-review periods in Sec. 26-9. Give both and say a lawyer decides which applies.
- **Private applicants:** agenda rows and permit records can name private applicants and residences. Report them to the user as public records. Don't put them in anything this plugin publishes, and don't single out a resident in campaign material.
- **Related skills:**
  - Drainage projects that need coastal permits, such as pump stations and canal maintenance: `scp-civics:scp-master-drainage-plan`.
  - Council actions on coastal matters: `scp-civics:scp-meeting-record` or `scp-civics:scp-decisions`.
  - Requesting a permit file from the parish CZM office: `scp-civics:scp-prr`.
- **Bayou is optional.** The state-side search (`bayou:la-coastal-use-permits`) and SONRIS documents (`bayou:sonris-doc-search`) need it. Without bayou:
  - the OCM public notices page (https://www.dce.louisiana.gov/page/coastal-management-public-notices) for current state notices;
  - OCM's semi-monthly status reports (https://www.denr.louisiana.gov/assets/OCM/PublicNotices/SR_{yyyy}/SR_{mm}_{01|16}_{yyyy}.pdf) for decisions;
  - the SONRIS link from `permit`, opened in a browser.
