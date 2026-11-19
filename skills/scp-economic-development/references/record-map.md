# Record map: who acts and where it is recorded

Probed 2026-11-19 unless a line says otherwise. Recheck anything you will rely on.

## Actors

| Actor | Authority | Where its record is | Notes |
|---|---|---|---|
| Department of Economic Development and Tourism | Code Sec. 2-23 (Ord. 90-9-3, 98-9-6). Duties include industrial, community and business development programs, statistics, policy recommendations to the Council, and liaison with agencies and outside groups, which the section names, including the Economic Development Council, the IDB and the Port | Yearly "Report Filed" Council matter titled with the department's name, 2013 on, with slides attached (some years also a .pptx); director confirmation hearings (Appointment by Motion) | Director appointed by the President. Letterhead: P.O. Box 302, Hahnville, 985-783-5140. The 2026 slides (matter 2026-0330, 2026-10-12) show an org chart under a deputy CAO, an "announced projects" figure and a FastSites award line. The `.pptx` attachment has the slide text, tables and notes (read it with `econdev.py deck`); only logos and photos are images |
| Economic Development Council | Not established. Its 2027 schedule says special meetings may be called by the chair or five voting members, regular meetings are open to the public, and attendance rules end membership | Legistar body 180 "SCP Economic Development": agendas, minutes and packets as meeting-page files, 2025-01-15 on. Roster on the parish's Granicus boards page (board 53248), with parish directors ex officio | Private chair. Meets 8 AM, usually the third Wednesday, at River Parishes Community College / United Way campus, Boutte. Its documents give the address as both 13145 and 13415 Highway 90, so confirm before going. Minutes include a machine-style Summary/Outline/Action Items. Votes recorded are on its own membership |
| Economic Development Commission | Code Sec. 2-51 (Ord. 86-2-1): three members nominated by the President and appointed by the Council | No Council title naming it found | Whether it exists in practice isn't established |
| Highway 90 Economic Development District No. 1 | Ord. 24-9-6 (matter 2024-0298) under R.S. 33:9038.31 et seq.; notice-of-intent Res. 6790 | Ordinance attachments: Exhibit A (boundaries, .docx) and the signed ordinance with map (scanned) | Governing authority: President and Council. Introduced by the President for the department. Res. 6790 also provided for special counsel |
| Luling Bridge Economic Development District No. 1 | Ord. 24-12-16 (matter 2024-0401); notice-of-intent Res. 6804 | As above, plus the Council Secretary's transmittal memo, copied to the Attorney General | Introduced by two Council members for the department |
| Parish Council | Charter | Legistar matters | Approves applications, agreements and budget amendments |
| President | Charter | Signs applications and support letters | Letters and applications aren't on Legistar |
| IDB, Port, South Central Planning & Development Commission | See `scp-civics:scp-government` structure file | Their own records | IDB money is in `scp-civics:scp-incentives` |

## Title patterns seen on Legistar, 1999 to 2026

- **Grant applications.** "approving and authorizing the Parish President to submit an application …" (DRA, USDA), "supporting the application for funding of … through …" (EDA, OCD LGAP and CWEF). Counts by phrase on 2026-11-19: "Delta Regional" 6, "Economic Development Administration" 3, "grant application" 21.
- **Treasury allocations.** "Cooperative Endeavor Agreement between the Louisiana Department of the Treasury and the State of Louisiana, and St. Charles Parish regarding the allocation of $X to be utilized for Y". These come in batches each fall.
- **Capital outlay agreements.** "Cooperative Endeavor Agreement between the State of Louisiana and St. Charles Parish for funding to … (Facility Planning and Control Project No. 50-J45-yy-nn)". Agency 50/J45 is the parish's code in HB2.
- **Company agreements.** "Cooperative Endeavor Agreement between <company> and the Parish of St. Charles providing for the construction of a road …".
- **Road projects toward a site.** Professional services agreements for planning or design, Treasury allocations naming the road, federal application resolutions. Search the road's name.
- **EDA rail spur.** A 2009 EDA award (USAspending, $2,000,000, "RAIL SPUR") and a 2014 resolution executing EDA's offer to terminate award 08-79-04437. That pair shows how a federal award and its end can both be traced.
- **Older LED items.** 2002: the President as "Sponsoring Entity" for an LED/LEDC Economic Development Award Program grant, and a budget amendment to buy acreage in a business park. 2009: a cooperative endeavor agreement with LED for funding.

## HB2 (capital outlay act)

- **Where.** legis.la.gov bill page `BillInfo.aspx?s=<session>&b=HB2`, with links "HB2 Act N", "HB2 Enrolled" and "HB2 Veto Message". Sessions 23RS to 26RS all had line-item vetoes.
- **Layout.** Each page has numbered lines and a "Page N of M" footer. Agency headers look like `50/J45 ST. CHARLES PARISH`. Projects look like `(577293) Title`, then the location in parentheses, then the funding lines. In 2023, project numbers were three or four digits.
- **Vetoes.** The veto message lists "Delete Lines a through b on Page N of M", or "a-b". The act PDF still prints those lines.
- **Priorities, from the 2026 act's Section 1.**
  - **1:** previously authorized projects with cash lines of credit, and reauthorized Priority 5 amounts that will need cash this year.
  - **2:** planning, land, site preparation or construction expected to begin in the fiscal year.
  - **3 and 4:** future-year portions.
  - **5:** the portion of construction contracts that won't need cash in the year. It needs a non-cash line of credit before award.
  - Quote the act for the year in question.
- **Requests.** Facility Planning and Control's capital outlay page publishes CORTS procedures and training, not entities' requests (2026-11-19).

## Federal

- **USAspending prime awards.** `POST https://api.usaspending.gov/api/v2/search/spending_by_award/` with `recipient_search_text` and grant type codes 02 to 05. Recipient names include "ST CHARLES PARISH", "ST CHARLES PARISH SCHOOL BOARD", "ST CHARLES SHERIFF OFFICE" and "ST CHARLES PARISH HOUSING AUTHORITY".
- **Subawards.** The same call with `"subawards": true`. The state's primes include the Division of Administration (OCD) and GOHSEP. Rows repeat once per report.
- **Dates.** A prime award's start date can fall before the search window, because the window filters on action dates.

## Economic development districts (statute, read 2026-11-19 at legis.la.gov)

- **R.S. 33:9038.32.** Creation by ordinance after notice published twice in the official journal. The governing authority is the creating subdivision's governing authority. The district is a political subdivision.
- **R.S. 33:9038.34.** Sales tax increment financing.
  - **Bonds.** Revenue bonds need a resolution of intent, publication once a week for two weeks, and a hearing at least 14 days after the first publication.
  - **Other recipients.** Pledging other tax recipients' increments requires an intergovernmental agreement with each one, other than the state (A)(5).
  - **The state's share.** It needs a submission by the LED secretary to the Joint Legislative Committee on the Budget (A)(6).
- **R.S. 33:9038.36.** Project costs include studies, land assembly, site preparation, and public streets and utilities "within or without" the district. They also include reimbursement to developers for preparation costs the subdivision approves.
- **R.S. 33:9038.39.**
  - **Taxes.** Up to 5 mills ad valorem, 2% sales and 2% hotel occupancy, by a resolution of intent, publication and a hearing, then an election of the district's qualified electors.
  - **No election.** None is required "in the event there are no qualified electors in the district as certified by the registrar of voters".
- Sections 9038.33, .37, .38, .40, .41 and .42 were pulled but not summarized here. Read them before relying on what this file leaves out.
