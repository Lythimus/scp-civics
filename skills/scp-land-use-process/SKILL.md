---
name: scp-land-use-process
description: St. Charles Parish, Louisiana land-use procedure and where its records live. Covers rezoning and Future Land Use Map amendments, preliminary plats and subdivision waivers, notice rules and how to check them, the Herald-Guide legal notices (image-only, OCR script included), Legistar quirks (Planning & Zoning packets, and meetings its API doesn't list), the Industrial Development Board (PILOTs, bonds), and parish custodians, phone numbers and record fees. Use for any St. Charles Parish rezoning, plat, variance, permit, comprehensive plan, PILOT or public-notice question, whatever the project.
argument-hint: <case number, applicant, address, or question about a St. Charles Parish land-use step>
allowed-tools: Bash, Read, Write, Grep, Glob, WebSearch, WebFetch, Skill
---

# St. Charles Parish land-use process

This skill covers the parish-specific mechanics. To audit one case, use `scp-civics:scp-case-check`. To follow a project over time, use `scp-civics:scp-watch`. For what was said or voted at a meeting, use `scp-civics:scp-meeting-record`. For PILOTs, IDB leases, bonds and tax exemptions, use `scp-civics:scp-incentives`. For parish budgets, capital projects reports and millages, use `scp-civics:scp-budget`. For drainage questions, use `scp-civics:scp-master-drainage-plan`. For what the Comprehensive Plan and its Future Land Use Map say, use `scp-civics:scp-comprehensive-plan`. Statewide sources are the `bayou:` skills named below, from the optional bayou plugin. Without it, go to the source in the same row: Legistar at https://stcharlesgov.legistar.com, the statute by title and section at https://legis.la.gov/legis/LawSearch.aspx, parcels at the parish assessor.

```bash
SK="${CLAUDE_PLUGIN_ROOT}/skills/scp-land-use-process"
HG=$SK/scripts/hg_legals.py            # Herald-Guide fetch / OCR / grep (stdlib + poppler + tesseract)
```

`references/code-sections.md` holds the rules: the Appendix A Sec. XV rezoning notice and standard, the Charter, the R.S. 33 overlay, state rules on court review and deadlines with how far each reaches a home rule parish, the Appendix C plat, waiver and drainage-analysis rules, and how to count notice days. Read it before stating any procedural requirement.

## Bodies

- **Planning & Zoning Commission:** hears rezonings, Future Land Use Map amendments and preliminary plats, and recommends to the Council. Under the Charter it is the zoning commission. It meets on Thursdays at 6 PM in Council Chambers, usually monthly (2026: 10/8, 11/5 cancelled, 12/3; then 1/7/2027).
- **Parish Council:** adopts rezoning ordinances, gives final plat approval, and passes the "supporting resolution" every subdivision waiver needs.
- **Zoning Board of Adjustment:** variances and appeals of administrative decisions (App. A Sec. XIII). It is a separate body, so don't call the Commission "the zoning board". It meets on the third Thursday if cases are scheduled, and can't grant a variance in a case that needs special permit or special exception approval. Its rules, agendas, results and minutes are on [its parish page](https://www.stcharlesparish.gov/departments/planning-and-zoning/zoning-board-of-adjustment), open in the browser.
- **Industrial Development Board of the Parish of St. Charles, Louisiana, Inc.:** PILOT leases and conduit revenue bonds. It meets a few times a year at 11:30 AM. It is **its own records custodian**: it adopted the Council's fee schedule by its own resolution, so a parish records request may not reach its files. How to submit to it: `scp-civics:scp-prr`.
- **Coastal Zone Management Section:** coastal use permits under the parish program (`SCP-yyyy-nn`), noticed in the Herald-Guide; see `bayou:la-coastal-use-permits`. The contact is 985-783-5060.

## Where records are

| Need | Where | Notes |
|---|---|---|
| Agendas, minutes, legislation | Legistar, via `bayou:parish-council-agendas` (`meetings st-charles --body Planning`, `track st-charles "<case or name>"`, `items`, `get`) | As of 2026-11-03, the Legistar web API (`webapi.legistar.com/v1/stcharlesgov/events`) returns Commission meetings that have a posted agenda (body "SCP Planning & Zoning Commission"), but it listed neither the cancelled 11/5 meeting nor the 12/3 one, and recent `matters` rows are all Parish Council. For whether a Commission meeting is scheduled or cancelled, read https://stcharlesgov.legistar.com/Calendar.aspx in a browser. A Commission meeting's staff reports can sit in an attachment named "Agenda" on its meeting page, not in the one-page agenda file; `bayou:parish-council-agendas` `get --what packet` reports no packet for these. Signed minutes for the Commission, IDB and other boards are attachments on the meeting page, which the API doesn't return, and they post only after a later meeting approves them. `scp-civics:scp-meeting-record` `documents` reads them. A matter's "Enacted" status can be a placeholder, so check its history and enactment number. |
| Meeting video, captions and member votes | `scp-civics:scp-meeting-record` | Finds the recording, makes a timestamped transcript and checks names, quotes and votes. Officials and board members: its `references/officials.md`. |
| Legal notices (rezoning, plat and ZBA hearings, coastal use permits, Council ordinances) | Herald-Guide, Thursdays: `https://www.heraldguide.com/wp-content/uploads/{yyyy}/{mm}/HGLegals_{yyyymmdd}.pdf` | **Image-only**, so the text layer is just the masthead. Use `$HG fetch`, then `$HG ocr` (minutes per issue; run in the background for many issues), then `$HG grep`. Planning & Zoning notices end with "PUBLISH: <dates>" and often "ALTERNATE DATE:". Save the OCR as a sibling `.txt` beside the PDF in the case folder. |
| Code of ordinances | `scp-civics:scp-ordinances` | Searches a local copy of the code, flags later amendments from Legistar, and covers reaching Municode. Rule notes for land-use cases are in `references/code-sections.md`. |
| Applications, staff reports, plats, drainage studies | Agenda packets on Legistar, or a public records request to the parish (`bayou:la-public-records-request`) | Staff reports post with the agenda, about a week ahead. A plat or study for a case not yet on an agenda may not be online, so use a records request. |
| Comprehensive Plan and Future Land Use Map | [Comprehensive Plan page](https://www.stcharlesparish.gov/departments/planning-and-zoning/comprehensive-plan): the 2030 plan and its update. Searchable copy with page cites: `scp-civics:scp-comprehensive-plan` | Sec. XV.D and XV.E test rezonings against it. `references/code-sections.md` says when to read it. |
| Building and site permits | Planning & Zoning, Permit Administration. Applicants file through MyGovernmentOnline, per the [permits page](https://www.stcharlesparish.gov/departments/planning-and-zoning/permits-and-applications), as of 2026-11-02 | **Not established:** whether MyGovernmentOnline lets the public search this parish's permits; its site wasn't readable when checked. Look there first if you can, otherwise use a records request (`scp-civics:scp-prr`). Commercial and industrial permits also draw on drainage plans, MS4, Fire Marshal, health, levee district, waterworks and wastewater approvals, listed on the parish's [new construction page](https://www.stcharlesparish.gov/residents/planning-and-zoning/new-construction). |
| Land records | St. Charles Clerk of Court eClerks: a $20 24-hour pass that the user buys and signs in to | Index rows are free to view once signed in; images need the pass. |
| LLC officers | Secretary of State, https://coraweb.sos.la.gov/CommercialSearch/CommercialSearch.aspx | The detail page is free, but open it through a search; a direct link redirects to the search form. Amendment images are paid: "Original Documents, Amendments, and Last Annual Report" costs $30 per entity and "Original Documents" $20. Stop and tell the user the price; never buy. |
| Incentives | `scp-civics:scp-incentives` joins the IDB, Council, State Bond Commission, ITEP and taxing bodies | R.S. 51:1157.1 requires SBC approval of IDB bonds, but a lease can run with no bond issued. If no docket turns up, say "not found on SBC agendas <first>–<last>". |
| Parcels | `bayou:parish-assessor-gis` | |

## Contacts (from the record, 2026)

- **Planning & Zoning:** 985-783-5060; P.O. Box 302, Hahnville, LA 70057. The Director in 2026 was Michael Albert, AICP.
- **Council Secretary:** 985-783-5125; Courthouse, 15045 Highway 18, Hahnville. This is also the contact block printed on the IDB's agendas.
- **stcharlesparish.gov** returns 403 to scripts; open it in the browser.

## Checks worth running on any case

1. **Notice.** Get every publication date from the Herald-Guide, then check the sign and the certified mail. Sec. XV.B requires mail to abutting owners; the Appendix C plat rule requires mail to adjoining owners and the Council Secretary.
2. **Future Land Use Map.** Read the site's designation and the plan's goals with `scp-civics:scp-comprehensive-plan`. If the rezoning is inconsistent with the map, look for a Commission **resolution** amending the plan, noticed with its purpose (R.S. 33:108). An ordinance that "authorizes" the department to amend the map is not the same thing. Past map changes haven't all taken one route, so compare with the list in `references/code-sections.md`.
3. **Plat versus drainage study.** Compare the plat's lot acreages, which are printed on the plat image (sum them), with the drainage study's study area. Sec. IV.5 requires a "comprehensive" analysis of "all proposed subdivision".
4. **Waivers.** Open-ditch drainage on a plat note means the subsurface waiver is needed, which takes Commission approval plus a Council resolution.
5. **Last hearing.** An approved industrial park can later be resubdivided without a hearing (App. C V.B.2).
6. **Transcript.** Ask what went to the Council: Sec. XV.A.2 requires a verbatim transcript.

## Before a Commission hearing: what to ask by phone

The agenda and staff report post only about a week ahead, so a comment can't wait for them without knowing the written-comment deadline. Ask Planning & Zoning early:
- Is the case on the agenda, and at what time and room?
- How are written comments submitted, and by when? Do commissioners get them before the meeting, and do they enter the record?
- What are the speaker rules: sign-up, time limit, yielding time, paper handouts?
- What email address takes written questions? None is printed in the case records.
- Who receives records requests for the IDB? Ask the Council Secretary.

Record each answer with the name and date. A records request filed after the staff report posts won't come back before the hearing (R.S. 44:33(B) sets three days only to certify unavailability, not to produce), so send requests as soon as the case is noticed.

Label legal readings "not legal advice" and frame them as questions.
