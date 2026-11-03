---
name: scp-comprehensive-plan
description: Look up what the St. Charles Parish, Louisiana 2030 Comprehensive Plan (2011) and its 2022 10-year Update say about a place, parcel, Future Land Use category or topic, with document and PDF page. Keeps the Future Land Use Map designation separate from the plan's goals and recommendations, says which map is current, and marks a map reading of a parcel as a visual reading. Use when a rezoning or Future Land Use Map change is tested against the plan (App. A Sec. XV.D.1 and XV.E.1), when someone cites the plan, or for the plan's treatment of industrial land, residential areas near industry, a community or a land-use category.
argument-hint: <place, parcel (address or lat,lon), land-use category, or topic>
allowed-tools: Bash, Read, Grep, Glob, Skill, AskUserQuestion, WebSearch, WebFetch
---

# St. Charles Parish Comprehensive Plan: what it says

The corpus is converted and checked. Work from it; do not re-download or re-convert the PDFs. This is research, not legal advice. Whether a rezoning is "consistent" with the plan is a judgment for the Commission, the Council and counsel, so report what the plan says, not a verdict.

```bash
CP="${CLAUDE_PLUGIN_ROOT}/skills/scp-comprehensive-plan/corpus"
# $CP/scp-2030-comprehensive-plan.md          2011 plan, 220 PDF pages
# $CP/scp-2030-comprehensive-plan-update.md   2022 Update, 185 PDF pages
# $CP/images/   figure crops and table snapshots    $CP/STATUS.md  what was verified and what was not
```

Read `$CP/STATUS.md` before relying on a table, a map legend or a figure description. The source PDFs are not in the plugin. If `SCP_CIVICS_DATA` points to a folder holding them, check quotes against them. If it is unset, cite the corpus and say that no check against the PDF was run.

## Which document governs (as of 2026-11-02)

- The **Update** (cover: adopted November 3, 2022) says it "does not replace" the 2030 plan but "serves as a companion document" (Update p16). It revises the Future Land Use Map, with "streamlined" categories (Update p41), and carries an updated action matrix.
- **Current map:** Update Figure LU-8, "Source: St. Charles Parish/CPEX May 2022" (Update p42), with zoom insets on pp47-50. The 2011 map (plan Figure LU-5, p72; repeated at p18) is the earlier map.
- The Update's resolution text (Update p2) records an intermediate "St. Charles Parish Future Land Use Map 2016", approved by the Commission on 2016-09-01 and supported by Ordinance 16-9-16. That digital map is not in the corpus.
- The 2030 plan was adopted by the Commission on June 2, 2011 and by the Council on June 20, 2011 (plan p31). The Update was adopted by Commission Resolution 2022-1, supported by Council Resolution 6688 (Legistar 2023-0056, approved 2023-03-13); see `scp-civics:scp-land-use-process`, `references/code-sections.md`.
- **Not established:** whether the map was amended after the Update. A Legistar API title search on 2026-11-02 found no Council matter naming "Future Land Use" after 2021. It doesn't cover Commission resolutions, which aren't in the API, or rezonings whose titles don't name the map. Check Commission and Council agendas (`scp-civics:scp-land-use-process`) before calling the 2022 map current for a case.
- The category names differ between documents. The plan has 18 map categories in five groups (plan pp73-78). The Update has 12 (Update pp41-44). The Update's map legend uses short names ("Residential High") where its tables say "High-Density Residential". Quote the document you cite; do not merge them.

## Steps

1. **Classify the input.**
   - *Community or place name:* go to step 2a.
   - *Parcel* (address, parcel number or coordinates): step 2b.
   - *Category* (for example "Heavy Industrial"): step 2c.
   - *Topic* (for example residential near industry): step 2d.
2. **Find the map designation.** Keep it apart from everything in step 3.
   - **a. Community.** Update pp47-50 give a "Future Land Use" paragraph per community (Montz, Norco, New Sarpy, Destrehan, St. Rose and the others), each with a zoom inset. The plan's map prints no community names, so use the Update for names. Plan Table LU-3 (p66) and Update p36 give population by community.
   - **b. Parcel.** The plan gives no parcel-level designations in text. Read the parcel's category from Figure LU-8 and its insets, and label it **a visual reading**, with the roads and neighbors you matched it by, unless a plan paragraph names the site. To place the parcel, use `bayou:parish-assessor-gis` (polygon at an address or point, owner of record, zoning). **Without bayou:** use the parish assessor's or GIS viewer, or the street address and the cross roads, and say that the location came from the street names. Then ask Planning & Zoning (contacts in `scp-civics:scp-land-use-process`) for the digital Future Land Use layer or a written designation. Committed images are downsampled (see STATUS), so a small parcel may not be resolvable at all. Say so rather than guess.
   - **c. Category.** Update Tables LU-5, LU-6 and LU-7 (pp41, 43, 44) give each category's description and recommended zoning districts. Plan pp73-78 give the 2011 descriptions. Plan Table LU-6 (p84) correlates 2011 categories with zoning districts.
   - **d. Topic.** `rg -n -i "<term>" "$CP"/*.md`. Search both spellings where the Update drops a doubled letter (`buf+er`, `of+ice`, `traf+ic`); STATUS explains the repair. Table rows and text-layer supplements are searchable the same way.
3. **Find the goals and recommendations.** These are separate from the map. Plan goals and policies: p81 on (Land Use, Housing and Community Character), then each element's goals and the Action Plan tables (Table IMP-1, from plan p173; the PDF repeats some of those pages). Update: goals p52, updated land use actions pp53-56, the rezoning and development decision policies (Policies 1-9, the guidance for Action LU 1.4) pp57-60, the goals and priority actions summary pp154-157, and the action tables pp158-184. Give each item's number, wording and page, and its timing or lead where a table gives them.
4. **Write the answer** in this order: designation (map, document, page, whether text or visual reading); category description and recommended zoning (quote); goals and recommendations (quote, with numbers); context such as population (dated); **Established** (each fact with document and page); **Not established** (each gap, and what was searched, with the date). Cite PDF pages as "Update p47". Printed page numbers differ from PDF pages.

## Rules

- Quote or paraphrase closely; give document and PDF page for every claim. If the corpus and the PDF disagree, the PDF wins and the difference goes in the answer.
- A figure description is a visual reading written during conversion. It is not the plan's text. Cite the figure and page, and say it is a reading.
- Perishable facts get dates: map currency, population figures (2010 and 2020 census years in the Update), adoption dates.
- Say what the plan does not cover. It sets no parcel boundaries, and it is guidance: App. A Sec. XV.D.1 tests the Future Land Use Map, and XV.E.1 tests the "goals and recommendations", so give both and let the user argue consistency. Procedure, notice rules and the R.S. 33:108 amendment path are in `scp-civics:scp-land-use-process` and `scp-civics:scp-case-check`.
- Sub-plans the Update cites are not in the corpus: the Comprehensive Pedestrian and Bicycle Master Plan (January 2019), the Paul Maillard Corridor study and the Master Drainage Plan (`scp-civics:scp-master-drainage-plan`). Say which one a question needs and that it was not read here.
- Skills draft and research. Never send a request, file a comment or contact staff on the user's behalf.
