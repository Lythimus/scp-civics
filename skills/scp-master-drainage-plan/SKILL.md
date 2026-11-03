---
name: scp-master-drainage-plan
description: Assess how a proposed project (subdivision, industrial site, data center, pipeline, road or fill) in St. Charles Parish, Louisiana would interact with the parish Master Drainage Plan — which watershed study covers the site, which planned canals, culverts, railroad crossings and pump stations it sits on or drains to, what the plan assumed about future development there, and what each planned improvement costs. Also traces whether plan projects have been funded or built, and documents how to add new plan PDFs to the local corpus. Use for any St. Charles Parish drainage, flooding, rezoning or permit question that should be checked against the plan.
argument-hint: <project description + address, street, or lat,lon> | --history [<watershed or project>] | --add <new-plan.pdf>
allowed-tools: Bash, Read, Write, Grep, Glob, WebSearch, WebFetch, Skill, AskUserQuestion
---

# St. Charles Parish Master Drainage Plan: project impact

The corpus is verified. Work from it; do not re-download or re-OCR the plan.

The corpus ships with the plugin in `corpus/`. The source PDFs and downloaded council attachments do
not. If you keep them locally, set `SCP_CIVICS_DATA` to their folder. If it is unset, cite the corpus
and the index, and say any check against a source PDF or attachment was not run. Statewide sources below are `bayou:` skills from the optional bayou plugin; without
it, name the source and say the check was not run.

```bash
MDP="${CLAUDE_PLUGIN_ROOT}/skills/scp-master-drainage-plan/corpus"   # 22 verified .md, images/, STATUS.md (read-only)
SKILL="${CLAUDE_PLUGIN_ROOT}/skills/scp-master-drainage-plan"
IDX=$SKILL/scripts/mdp_index.py                    # executable; stdlib Python 3 only
```

| Path | Holds |
|---|---|
| `$MDP/<slug>.md` | One file per plan PDF: `## Page N` sections, tables, figure descriptions |
| `$MDP/images/` | Figure crops (`<slug>-pNN-figK.jpg`) and table snapshots (`...-tableN-snapshot.jpg`) |
| `$MDP/STATUS.md` | Ledger of what was verified, corrected and left unresolved in the conversion |
| `$SKILL/index/projects.csv`, `figures.csv` | Generated index of every costed project row and figure. Rebuild with `$IDX build` |
| `references/watersheds.md` | Which document covers which community, and how the two banks differ |
| `references/known-discrepancies.md` | Numbers that disagree inside the plan, and which to cite |
| `references/implementation-history.md` | How to trace what has been funded or built |
| `references/status-ledger.md`, `index/status.csv` | What council records show as funded, under construction or built, per plan row, with an as-of date |
| `index/legistar_matters.csv` | Raw harvest of council legislation titles since 2020. Refresh with `scripts/legistar_harvest.py` |
| `index/parish_projects.csv` | Every parish drainage and levee project the council has acted on since 2020, by parish project number, with phase, contractor, award and matched plan rows. Rebuild with `scripts/legistar_harvest.py projects` |
| `index/parish_tracker_2026-10.csv` | The parish's own capital projects report updated 10/8/2026, one row per drainage or levee line it prints: status, estimated construction cost, schedule, remarks, new comments, and matched plan rows. It's headed "Active Projects" and lists 27 lines, so a line missing from it isn't closed. `index/parish_tracker_2026-07.csv` is the 2026-07-31 report (58 lines, with the plan priority it cites), and `index/parish_tracker.csv` is the 2026-05-29 drainage report. Source PDFs and text: `$SCP_CIVICS_DATA/scp-capital-*.pdf` |
| `index/budget_2027_proposed.csv` | Drainage and flood protection capital outlay lines requested in the 2027 proposed budget |
| `scripts/status_build.py`, `scripts/status_ledger_md.py` | Generators for `index/status.csv` and `references/status-ledger.md`. New evidence goes in the MATCH list in `status_build.py`; hand edits to either output are overwritten |
| `$SCP_CIVICS_DATA/council-attachments/` | Council attachments already downloaded (contracts, bid tabulations, completion certificates, the 2027 proposed budget), each with a `.txt` beside it. Check here before downloading |
| `references/adding-documents.md` | Converting a new plan PDF into the corpus |

`$MDP` is read-only for this skill. `--add` is the one mode that writes there, and
it asks first.

## What the plan can and cannot answer

The corpus is executive summaries and two public-meeting decks. Keep these limits in view, and
carry the ones that apply into the output:

- **No geometry.** There are no shapefiles, coordinates or basin boundaries, and no parish GIS
  service for drainage basins has been confirmed. Location is established from street, canal and
  structure names in the text and on the figures. State how each match was made (step 3).
- **Summaries only.** Each West Bank summary says it "shall always be accompanied by the
  comprehensive detailed report." Model inputs (curve numbers, impervious assumptions, tailwater,
  water-surface elevations) are in those detailed reports, which are not in the corpus. If the
  question turns on them, say so and draft a records request (step 6).
- **Improvement extents are conceptual.** West Bank figures carry the note that extents are "meant
  for general description only" and "subject to change as part of permitting and detailed
  engineering design." A project that overlaps a drawn improvement overlaps a concept, not a
  surveyed alignment.
- **Costs are conceptual and incomplete.** Mitigation, permitting and land acquisition are
  excluded (some summaries also exclude utility relocation). West Bank totals include a 20%
  contingency. Costs are in the dollars of the study year, and the summaries print no date.
- **West Bank 25-year improvements were sized, not modeled.** Where a summary prints 25-year and
  100-year costs, the 25-year sizes "have not been analyzed to determine the effect on water
  surface elevation." Railroad crossings stay at 100-year size in both columns.
- **Not every part of the parish is covered.** See `references/watersheds.md` for the list. A site
  outside every study is a finding in itself.

## Mode 1: project impact (default)

### 1. Pin the project down

From the request or the project's own documents, get: location (address, streets, or coordinates),
footprint acreage, what changes on the ground (impervious area, fill, new or relocated ditches,
culverts, outfalls, detention), and where the site says its stormwater goes. If the location is
missing, ask for it once. Everything else can be reported as unknown.

For a facility known only by name, use `bayou:facility-coordinates`. Use `bayou:geo-distance` for
distances to named structures.

Take the parcel, owner, current zoning and acreage from `bayou:parish-assessor-gis`.
`parcels.py at <lat> <lon>` gives the parcel under a point. For a multi-parcel site,
`parcels.py footprint --owner "<applicant>" --near <lat> <lon>` or `--pins` gives the site's
acreage. These are GIS acres; the application's figure governs if the two differ, so report both.
The parcel's `community` and situs street are search terms for step 2.

### 2. Find the watershed study

Read `references/watersheds.md` and pick the study by community and bank. Then confirm it from
the text, because basin names do not always match postal place names (the St. Rose town hall deck
covers five East Bank basins, and Hahnville is split in two):

```bash
$IDX find "Courthouse Lane"          # one street, canal, railroad or structure name per call
$IDX find "Vial Canal" "LA 3127"     # several terms are OR-ed
```

Search for the site's street, the cross streets, the nearest canal and the nearest railroad or
highway crossing. Each hit is labelled by the kind of evidence it gives:

| Label | Meaning | Confidence it gives |
|---|---|---|
| `PROJECT` | Named in a cost table row | A planned improvement is named for that place |
| `FIGURE` | Labelled on a map | The place is inside or beside the mapped study area |
| `TEXT` | Narrative only | The study discusses it; position unknown |

No hits on any term means the site is probably outside the studied basins. Check the neighbouring
studies before concluding that, then report it as "not covered by the corpus."

### 3. Read the study and look at the maps

Read the whole `.md` for the matched study (they are short), then Read the figure images for the
pages that hit. Figure descriptions say what is labelled, not where the site falls relative to
it, so the image is the evidence for anything spatial. Some St. Rose figures are drawn rotated.

Establish, with a confidence level for each:

- **On an improvement:** the footprint overlaps a drawn ditch, channel widening, culvert,
  jack-and-bore, pond or pump station site, or a servitude shown in the legend.
- **Upstream of an improvement:** the site drains to a planned improvement, so added runoff uses
  capacity the plan sized for other flows.
- **Downstream of, or beside, the outfall:** the site sits on the outfall canal, sump or pump
  station the basin depends on.
- **In the basin, no named improvement nearby.**

Confidence levels: **shown** (visible on a figure, cite the image file), **named** (the street or
structure is in a table row or page text, cite page), **inferred** (from drainage direction
described in the text; say what the inference rests on).

Record every planned improvement the project touches with its ID, name, scope line, cost and
page. Get costs from the `.md` table, not from a figure description, and check each one against
`references/known-discrepancies.md` before citing it.

### 4. Test the project against the plan

Answer each of these from the study text. Quote the sentence and cite `<slug>.md` page N.

1. **Design storm.** What event is the basin's recommended program built for (25-year, 100-year,
   or 25-year with selected 100-year crossings)? What does the project's own drainage study
   design to? A site designed to a smaller storm than the basin plan is the first thing to flag.
2. **Development assumption.** Does the study say it considered "planned and potential future
   development," and does the legend show a "Proposed Development" area? Is this project inside
   one? The summaries do not list which developments were assumed, so a project not shown as
   proposed development is not known to be in the model. State it that way.
3. **Known problem areas.** Does the study's "current drainage issues" or "existing flood-prone
   areas" passage name the site's streets or canal?
4. **The limiting structure.** Most basins name what limits conveyance (railroad crossings, a
   pump station, an outfall canal). Is the project upstream of it? Has that structure been
   upgraded (Mode 2)? Added runoff upstream of an unbuilt upgrade is the strongest form of the
   argument.
5. **Conflict or foreclosure.** Would the project occupy land the plan needs (pond site, channel
   widening, pump station, servitude), raise the cost of a planned improvement, or fix a
   crossing size below the plan's? `parcels.py at` on the planned pond or pump-station site
   names its current owner. If the project's applicant owns that land, the conflict is direct.
6. **Consistency.** Does the project propose something the plan also proposes (a culvert, a
   detention pond), and at the same size?
7. **Who pays.** If the project depends on a plan improvement that is not built, what does that
   improvement cost and what is its priority or phase?

### 5. Bring in the surrounding record

Use other skills for what the plan does not hold. Do not restate their methods here.

| Question | Skill |
|---|---|
| Flood claims, policies and declarations near the site | `bayou:fema-flood` |
| Levee, surge and land-loss context; coastal projects in the parish | `bayou:cpra-master-plan` |
| Coastal use permit for the project or the plan improvement | `bayou:la-coastal-use-permits` |
| Corps permit or Section 408 on a levee, canal or pump station | `bayou:usace-408-permits` |
| Receiving water impairment where the basin discharges | `bayou:cwa-watershed-context` |
| Historic drainage and land form | `bayou:usgs-historic-topo-lidar` |
| Parcel, owner of record and zoning district of the site or of a plan improvement's land (rezoning questions) | `bayou:parish-assessor-gis` |
| When the project's rezoning, servitude revocation or drainage contract comes before P&Z or the council, and the ordinance's history and hearing date (`agendas.py track st-charles "<applicant or case>"`) | `bayou:parish-council-agendas` |
| The project's own drainage study or permit application | `bayou:document-ocr` then `bayou:permit-analysis` |

`$SCP_CIVICS_DATA/St Charles Local Coastal Program.pdf`, if present, is
not part of the plan. Cite it separately.

### 6. Report

Write the findings as a section in the project's own notes, or to chat if no project folder
applies. Structure:

1. **Coverage:** the study that covers the site, bank, author, and how the match was made.
2. **Planned improvements the project touches:** table of ID, name, scope, cost, page,
   relationship (on / upstream / outfall), confidence.
3. **Findings** against the seven tests, each with a quoted sentence and page.
4. **What the plan does not say,** including model inputs held only in the detailed report.
5. **Limits** from "What the plan can and cannot answer" that apply.
6. **Next records:** the detailed report volume for that basin, the project's drainage impact
   study, and parish records on the limiting structure. Draft requests with
   `bayou:la-public-records-request`. Drafts only.

Cite every number as `<slug>.md` page N, table N, and keep the snapshot path for table values.
Do not round costs. If two printed values disagree, give both and say which the plan's own
detail supports.

## Mode 2: `--history`, what has been funded or built

Read `references/status-ledger.md` first. It records the status of every plan row as of its date,
what was searched and what was not. Answer from it, then search only for what is newer than its
as-of date or listed there as not yet searched, following `references/implementation-history.md`.
For council and P&Z items since the as-of date, first run `bayou:parish-council-agendas`:
`agendas.py alerts st-charles --term "drainage|culvert|canal|pump station|levee" --category custom --since <as-of date>`
(`--category custom` leaves out the skill's own rezoning and financing hits).
It reads agendas only, so the harvest is still what updates the ledger.
When a search changes a row, change the MATCH list in `scripts/status_build.py`, then run it and
`scripts/status_ledger_md.py`, and move the as-of date.

For "what has the parish built or started near X", search `index/parish_projects.csv` by name
first: it also holds the projects that match no plan row. Its `award_link` and `links` columns open the
Legistar pages whose attachments are the technical record (contract, bid tabulation, scope
exhibits, completion certificates). `index/parish_tracker_2026-10.csv` gives the parish's stated status
and cost for active projects, and the July file has the lines October left out (see the ledger for the source page). Report each plan
project as one of: built, under construction, funded, application submitted, no record found.
"No record found" is not "not built."

## Mode 3: `--add`, a new plan document

Follow `references/adding-documents.md`. It needs MinerU, which downloads large models. Announce
the size and get a yes before any download.

## After any change to `$MDP`

```bash
$IDX build     # regenerate index/projects.csv and figures.csv
$IDX check     # sum project rows against printed subtotals and totals
```

`check` exits non-zero when a printed subtotal does not equal its rows. Every mismatch it prints
today is listed in `references/known-discrepancies.md`. A new one is either an OCR or layout
defect in the Markdown (compare the table snapshot, then `pdftotext -layout -f N -l N <pdf> -`) or
an error in the source. Keep the printed value, add a note under the table, and record it in the
discrepancy file. Never correct a source value silently.

$ARGUMENTS
