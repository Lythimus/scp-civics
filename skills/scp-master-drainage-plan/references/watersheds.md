# Which document covers which place

Source PDFs are on the parish website and are not in this plugin; the Markdown slug is the lower-cased,
hyphenated PDF name. Basin names are the plan's, and they do not always match postal place names.
Confirm a site's basin with `mdp_index.py find <street>` before relying on this table.

## The two banks are two different plans

| | East Bank Master Drainage Plan | West Bank Master Drainage Plan |
|---|---|---|
| Author named in the summaries | Principal Engineering, Inc. (every volume) | TBS in the Ama-Sellers, Hahnville 1, Hahnville 2 and Luling summaries. The Killona Taft, Mimosa Willowdale and Paradis summaries name no author; they share the format but do not attribute them to TBS without the detailed report. |
| Unit of study | "Drainage Area," numbered volumes | "Watershed" |
| Project IDs | `phase-number`, e.g. `1-3`, `2-2.1` | Improvement Groups, `IG-1` ... |
| Ordering | Phases (Phase 1 first) | Prioritization Level 1-4 |
| Cost columns | One cost per project | 25-year and 100-year cost, or 25-year only |
| Design basis as stated | 25-year improvements plus selected 100-year improvements at major street and railroad crossings; NOAA Atlas 14; models in EPA SWMM and Autodesk Storm and Sanitary Analysis | 100-year for the Hahnville and Ama-Sellers studies; 25-year for the Killona Taft, Mimosa Willowdale, Luling and Paradis studies, with railroad crossings at 100-year |
| 25-year goal | Canal water surface one foot below top of bank | Sized from 25-year flows, not modeled for water surface |
| Alternatives | Some volumes print Alternate 1 / Alternate 2 programs with their own phase tables | None |

Read the study's own first page for its design basis. The row above is a summary, and individual
studies vary.

An ID such as `1-3` is unique only within one volume, and within one alternative of that volume.
Always cite it with the basin name, and with the alternative where there is one.

## East Bank volumes

| Vol. | Basin | Slug | Notes |
|---|---|---|---|
| 2 | Montz | `montz-executive-summary` | Builds on an earlier 10-year study by Meyer Engineers. Phase 3 has alternative rows. |
| 3 | Norco | `norco-executive-summary` | Engineer's Canal, West Canal, Mary St. Canal; Bonnet Carre Spillway side. Phase 1 has two alternatives for 1-1. |
| 4 | New Sarpy | `new-sarpy-executive-summary` | Schexnaydre and New Sarpy pump stations. Project numbering collides between figures. |
| 5 | Ormond | `ormond-executive-summary` | Pond-to-pond culverts. Four phases. |
| 6 | St. Rose | `st-rose-executive-summary` | Fourth St and Oak St pump stations. Three program variants (base, ALT-1, ALT-2) repeat the tables. |
| 7 | Dianne Place | `dianne-place-executive-summary` | |
| 8 | Bar None | `bar-none-executive-summary` | |
| 9 | Turtle Pond | `turtle-pond-executive-summary` | Riverbend pump stations. Figures build up by phase. |
| 10 | Almedia | `almedia-executive-summary` | Six phases. Spelled "Almeida" in places. |
| 11 | Destrehan Plantation | `destrehan-plantation-executive-summary` | |
| 12 | Plantation Business Center | `plantation-business-center-executive-summary` | Base program and Alternate 1. |
| 13 | Destrehan West | `destrehan-west-executive-summary` | |
| 14 | Destrehan East | `destrehan-east-executive-summary` | Base program, Alternate 1 and Alternate 2, each with its own phase tables. |

Volume 1 is not in the corpus. It is likely the plan-wide volume; confirm before saying so.

## West Bank watersheds

| Watershed | Slug | Notes |
|---|---|---|
| Ama-Sellers | `amasellers-executive-summary` | Forced drainage basin; pump station and outfall channel. |
| Hahnville 1 | `hahnville-i-executive-summary` | Jack-and-bore culverts under the UP railroad. |
| Hahnville 2 | `hahnville-ii-executive-summary` | Vial Canal outfall to the Eighty Arpent Canal; courthouse area. |
| Killona Taft | `killona-taft-executive-summary` | Mary's Canal; drains toward LA 3127. |
| Luling and Luling I-310 | `luling-executive-summary` | Two cost tables, one per sub-basin. |
| Mimosa Willowdale | `mimosa-willowdale-executive-summary` | Peterson Canal; Beaupre Drive siphon. |
| Paradis, Des Allemands, Sunset | `paradis-da-sunset-executive-summary` | Hwy 90 crossings. |

Boutte has no executive summary in the corpus, but the Luling public-meeting deck has Boutte maps
(figs 17-23), so a Boutte study may exist. Absence from this folder is not absence from the plan:
when a site matches no study, check the parish's Master Drainage Plan page for a volume that was
not downloaded before reporting the site as unstudied.

The Killona Taft, Luling, Mimosa Willowdale and Paradis summaries have no figures, so nothing in
them can be matched as "shown." The Luling deck has maps for Luling and Mimosa Willowdale.

## Public-meeting decks

| Slug | Date | Covers |
|---|---|---|
| `st-rose-drainage-townhall-11123` | 2023-11-01 | St. Rose, Dianne Place, Bar None, Turtle Pond and Almedia. Includes the grant-funding status table (p13) and the five-basin total: 65 projects, $105,267,058.95 (p14). |
| `luling-and-luling-i310-mimosa-willowdale-public-meeting-62024` | 2024-06-20 | Luling, Luling I-310, Mimosa Willowdale, and Boutte maps. |

The decks are later than the executive summaries and are the parish's own account of status. In
the town hall deck, page headings and table headings disagree about which basin a page shows
(see `known-discrepancies.md`). Take project values from the basin's executive summary and use
the deck for status.

## Not part of the plan

`St Charles Local Coastal Program.pdf`. The
duplicate `Bar None  Executive Summary (1).pdf` is byte-identical to the original and is skipped.
