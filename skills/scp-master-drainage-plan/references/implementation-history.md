# Tracing what has been funded or built

The executive summaries are plans, and they print no date and no status. Whether a project was
built has to come from other records. Work outward from the corpus, and keep the parish's claims
separate from independent confirmation.

## Status vocabulary

Use exactly one per plan project, with the source and its date:

| Status | Needs |
|---|---|
| Built | A completion record: final acceptance or substantial completion by the council, a parish completion announcement, or dated imagery showing the structure |
| Under construction | A contract award or notice to proceed, without a completion record |
| Funded | An award or appropriation that names the project, without a construction contract |
| Application submitted | A grant application or capital outlay request, without an award |
| No record found | Nothing located. State where you looked. This is not "not built." |

A plan project can be built at a different size from the plan's (a 200 cfs station where the plan
calls for 500 cfs, or 25-year sizing where the plan lists 100-year). Record the built size and
compare it with the plan row. That comparison is usually the point.

## Step 1: what the corpus already says

- `st-rose-drainage-townhall-11123.md` p13, "Grant Funding for St. Rose Drainage": six requests as
  of 2023-11-01 across State Capital Outlay, the Louisiana Watershed Initiative and FEMA HMGP. One
  is marked awarded ($825,000, Fairfield and Oakland Pump Station Improvements); the rest are
  applications. Read the snapshot, since the first row holds two amounts in one cell.
- Same deck, p14: the five-basin program is 65 projects, $105,267,058.95. p15 describes the parish
  elevation program (FEMA FMA repetitive-loss properties).
- `luling-and-luling-i310-mimosa-willowdale-public-meeting-62024.md` (2024-06-20): read it through
  for any statement of what is designed, funded or scheduled.
- Search every document for status words:
  `rg -n -i "awarded|funded|under construction|completed|bid|capital outlay|watershed initiative|hazard mitigation" $MDP/*.md`

Establish the plan's start from documents, not memory. The summaries name authors (Principal
Engineering for the East Bank, TBS for four West Bank watersheds) and the Montz volume cites an earlier
10-year study by Meyer Engineers. Dates for each volume are on the PDF cover pages or in the PDF
metadata (`pdfinfo "<file>.pdf"`), and on the parish's document pages.

## Step 2: your own files

Before searching the web, check any local folders of council minutes, committee minutes, meeting
transcripts, or applicants' site-specific drainage statements.

Search by project name, pump station name, canal name and the engineer's name. Transcripts spell
names phonetically, so also search fragments (`rg -i "almed|almeid"`).

## Step 3: parish records

Search in this order. Each is a place where a plan project leaves a dated trace.

1. **Council ordinances and resolutions.** Engineering contracts, construction contract awards,
   change orders, servitude acquisitions and final acceptances are all adopted by the council and
   name the project. The parish posts agendas, minutes and legislation online.
   Search them through the Legistar web API, which needs no token for this parish:
   `scripts/legistar_harvest.py` pulls every matter whose title contains a search term into
   `index/legistar_matters.csv`. For one matter's history and attachment links, use
   `bayou:parish-council-agendas`: `agendas.py track st-charles <file no.>`. Use `--terms-file` to search for a street, canal or
   parish project number (`P` + year + month + sequence, e.g. `P200801`). The API matches titles
   only, so a project named only in an attachment will not be found. Titles map onto the status
   vocabulary: a professional services agreement is design funding, a "Contract with" a builder
   is a construction award, and "Change Order No. N (Final)" closes the contract. Completion
   is usually not a matter of its own: the Certificate of Substantial Completion and Final
   Acceptance are filed as attachments on the award or change-order matter, so run `track` on
   those and open the certificate for the date. State-funded work can have a separate
   resolution accepting the work as complete.
2. **Parish capital projects reports.** Public Works posts a status report per category
   (Drainage, Levees, Roadway, Wastewater, Miscellaneous) and a council summary at
   `https://www.stcharlesparish.gov/departments/public-works/capital-projects`. Each line gives
   status, estimated construction cost, schedule and remarks, and some cite the plan priority the
   project implements. The site refuses scripted requests, so save the PDF through a browser into
   `$SCP_CIVICS_DATA/`, then write a new dated `index/parish_tracker_<yyyy-mm>.csv` and point `scripts/status_build.py` and `scripts/legistar_harvest.py` at it. The "Council" report covers every category, including the Levee page where the Montz pump stations are listed. Downloaded council attachments go in `$SCP_CIVICS_DATA/council-attachments/` with a `.txt` beside each (`ocrmypdf --force-ocr --sidecar` for scans); attachment links printed by the API return 404, and `agendas.py track` prints the working form. These are the
   parish's claims: keep them apart from council records.
3. **Capital budget.** The annual budget ordinance and its capital projects schedule list
   drainage projects by name with amounts, by year. Comparing consecutive years shows what moved.
4. **Bid advertisements and tabulations.** Public works bids are advertised in the official
   journal and posted by the parish's purchasing office.
5. **The parish's Master Drainage Plan and drainage pages** on stcharlesparish.gov, including any
   volumes or meeting decks newer than the corpus.
6. **Parish news releases and the St. Charles Herald-Guide** for groundbreakings and completions.

## Step 4: funders

| Source | What it shows | How |
|---|---|---|
| Louisiana Watershed Initiative | Round awards by project and parish | LWI award announcements and project lists, searched by parish and project name |
| State Capital Outlay (HB 2) | Line items by parish, with priority level | Search each year's HB 2 for "St. Charles" and the project name |
| FEMA HMGP / BRIC / FMA | Obligated mitigation projects | `bayou:fema-flood` for openFEMA; the mitigation-projects dataset lists subrecipient and project type |
| Federal earmarks and appropriations | Named drainage items | `bayou:federal-register-search`, congressional project disclosures |
| USACE | Permits for canal, culvert, pump station or levee work | `bayou:usace-408-permits` |
| LDENR Office of Coastal Management | Coastal use permits for the same work | `bayou:la-coastal-use-permits` |

A permit application for a pump station or canal widening is evidence the project reached design,
and its drawings give the built size.

## Step 5: physical confirmation

For a pump station, a canal widening or a new pond, dated imagery settles "built." Use
`bayou:satellite-imagery` for a before and after pair bracketing the claimed construction dates.

## Step 6: records requests

Where the public record is thin, draft requests with `bayou:la-public-records-request`. Drafts
only. Useful asks:

- The detailed report volume for the basin (the executive summary says it accompanies one).
- The parish's integrated priority list. The East Bank summaries say the parish is expected to
  "create an integrated priority list consisting of projects from all basins."
- The project status tracker or capital improvement schedule for Master Drainage Plan projects.
- For a specific development: the drainage impact study submitted with it and the parish
  engineer's review comments.

## Output

A table keyed to plan rows: basin, plan ID, plan name, plan scope and cost, status, built scope
if different, source and date. Follow it with totals: plan cost by status for the basin, and the
share of Phase 1 or Priority 1 cost with any funding. Put the "no record found" rows in the table,
since the unfunded remainder is often the finding.
