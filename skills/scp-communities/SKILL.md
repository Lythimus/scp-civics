---
name: scp-communities
description: Who lives next to what in St. Charles Parish, Louisiana. A profile of each of the parish's 14 communities (Norco, St. Rose, Killona, Hahnville, Luling, Taft and the rest) with council districts, levee district, exact 2020 census counts by race and ethnicity, ACS estimates with margins of error (poverty, age, vehicles, limited English, income), the population in industrial Future Land Use categories and within a set distance of LDEQ-registered sites, and nearby schools and nursing homes. Also compares all 14 side by side, gives tract and block group figures for an address, and shows where enacted rezonings to industrial districts have landed by community and council district since 1999. Use for environmental-justice comparisons, describing a fenceline community, or asking whether industrial land use and rezonings fall unevenly across the parish. Public places and bodies only, never a household.
argument-hint: "<community name, address, or a distribution question>"
allowed-tools: Bash, Read, Grep, Glob, Skill
---

# St. Charles Parish communities

```bash
COM="${CLAUDE_PLUGIN_ROOT}/skills/scp-communities/scripts/communities.py"
```

Date every figure ("2020 census", "ACS 2020-2024, as of 2026-11-19"). Keep what the data shows apart from what it doesn't. Living near a registered site, or in a high-poverty tract, doesn't prove harm, and the skill never says it does.

## 1. Pick the command

| The user wants | Run |
|---|---|
| All 14 communities compared | `python3 "$COM" places [--km 2] [--all-types]` |
| One community in depth | `python3 "$COM" profile Norco [--km 2] [--all-types] [--top 25]` |
| The neighbourhood around an address | `python3 "$COM" point "15045 River Rd, Hahnville"` or `--point LAT,LON` |
| Where rezonings to industry have gone | `python3 "$COM" distribution [--since 1999]` |

By default, sites are `scp-facilities`' roster: LDEQ's chemical, refining and pipeline AIs plus its named power plants and terminals (Waterford 1 & 2, J. Wayne Leonard, Vopak and the others in `EXTRA_AIS`). `--all-types` also counts the broader `near` types (utilities, oil and gas field equipment, trucking, food plants). Those types also hold septic, dump and other records filed under private people's names, so they are counted by type and never named. Use the default for environmental-justice comparisons.

Census tables come from api.census.gov when a key is available: the `CENSUS_API_KEY` environment variable, or a `CENSUS_API_KEY:` line in bayou's `bayou-credentials.md` (in the Claude config folder) if bayou is set up. Without a key, or if the key fails, they come from data.census.gov's table endpoint, which is undocumented and could change; the rows are the same. A free key is at api.census.gov/data/key_signup.html.

Public data is cached in `~/.cache/scp-civics/communities` for 7 days (`--max-age`, `--refresh`). The first run takes about 20 seconds. `distribution`'s first run fetches every rezoning matter through `scp-decisions` and takes about a minute.

## 2. Two population figures: say which one you are quoting

- **2020 census counts (exact).** These are summed over the 2020 blocks whose interior point falls inside the **parish's own** community polygon (parish GIS Community Boundaries). The tiling check in `places` confirmed all 52,549 residents fall inside one of the 14 polygons (as of 2026-11-19). Race and ethnicity come from the P2 table: Black alone, not Hispanic; Hispanic of any race; and so on.
- **ACS 5-year estimates (with margins of error).** These are the Census Bureau's published figures for the **Census Designated Place** of the same name. A CDP's boundary isn't the parish polygon. Taft's polygon held 506 people in 2020, while Taft CDP held 61. Cite the CDP by name and quote the margin. The script marks a share "unreliable" when its coefficient of variation is over 30%, which is common in the small CDPs (Killona, Taft, Ama). Don't build an argument on an unreliable figure; give the tract figure from `point` beside it.

The next ACS release (2021-2025) is due in December 2026. After it is out, change `ACS_YEAR` in the script.

## 3. Reading each section

- **Census tracts:** the 2020 tracts holding the community's population, with shares. Tract-level sources such as CDC's Environmental Justice Index use these.
- **Council districts:** the community's 2020 population in each district, on today's lines (Ord. 22-12-12, 26-2-3). For members, use `scp-civics:scp-government` `district`.
- **Levee district:** this is set by bank, east (Pontchartrain) or west (Lafourche Basin). It is a general rule. For a specific site, check the district's map and `scp-government`'s structure.md.
- **Future Land Use Map (2023):** population by the FLUM category at each block's interior point, plus the categories with land in or touching the community. For what a category means and which map is current, use `scp-civics:scp-comprehensive-plan`. A FLUM category is the parish's plan for the land, not its zoning.
- **Sites:** LDEQ AIs inside or within `--km` of the boundary, ordered by how many of the community's residents live within `--km`. Distance runs from LDEQ's plotted point, which can be a gate or an old office. A registration isn't an operating plant. Take an AI number to `scp-civics:scp-facilities` (`find <AI>`) for the record. Wind, stack height and release history decide what reaches people; distance doesn't. A large complex has one plotted point, so distance from it can understate how close homes are to the fence. Read the Ind.FLUM share and the FLUM section beside it.
- **Schools, nursing homes, hospital:** from NCES (public schools 2024-25, private schools 2023-24) and CMS. NCES listed 15 public schools and one private school in the parish. Check the count against the School Board's own list before saying a school is absent. Child care centers and parks aren't covered.
- **Drainage:** the Master Drainage Plan's basins don't follow community lines. Use `scp-civics:scp-master-drainage-plan`.

## 4. An address (`point`)

`point` reports the community, council district, FLUM category, and ACS figures for the 2020 block group and tract around the address. It sends only the address, and only to the parish's own geocoder. Use `--point` to send nothing.

It never prints block-level figures, because a block can be a handful of homes. Don't work them out by hand either. If the user names a home, report the block group and tract, not "this household".

## 5. Distribution of rezonings

`distribution` starts from `scp-decisions`' set of 431 rezoning matters. It places each **enacted** ordinance through the ordinance numbers recorded on the parish zoning layer, using the polygon's centroid. As of 2026-11-19, 305 of 336 enacted ordinances were placed.

Limits to state whenever this is quoted:

- **The zoning layer shows today's zoning.** A later rezoning or a merged polygon can overwrite an earlier ordinance number, and the "placed / not placed" line shows how many were lost.
- **Failed, withdrawn and postponed rezonings aren't on the map,** so they can't be placed this way. Use `scp-civics:scp-decisions` `rezonings --where <community>` for those. Its title search is rougher, so say so.
- **Districts are today's lines,** not the lines when each vote was cast.
- **A centroid on a community edge can land in the neighbouring community.** Check any single case against its staff report.
- **"Newly industrial (M)"** means a target district of M-1, M-2 or M-3 from a non-M district. M-to-M changes are counted separately. MS isn't counted as industrial.

Raw counts aren't rates. Communities differ in size and in how much land is open to development, so compare a count with the community's population and its FLUM land before calling a pattern uneven. Then present the comparison as a question for the Council.

**Capital spending by district** is in the capital projects report's Council District column. Read it with `scp-civics:scp-budget`. No source reports capital spending by tract or community, so don't assign a parishwide line to one.

## 6. What isn't covered

- Child care centers, parks, churches and private schools beyond NCES's list.
- Health outcomes. These are statewide sources, so leave them to the bayou plugin.
- History of a place, unless a public source is cited for it.
- Point-level environmental indices: `bayou:ejscreen-report` profiles a point. Without bayou, say that the check wasn't run and name the CDC Environmental Justice Index as the source to read.

## 7. Report

Lead with the comparison the user asked for, then the figures, each with its source and vintage: "2020 census, parish polygon" or "ACS 2020-2024, Killona CDP, ±". Name the limits that apply from §2 and §5. Public places and bodies only. Never name a resident, a landowner outside a verbatim record title, or a household's figures.

This skill researches. It never contacts an office, files a comment or sends a request.

$ARGUMENTS
