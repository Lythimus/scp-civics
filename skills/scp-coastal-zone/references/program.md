# How the St. Charles coastal program works

As of 2026-11-20. Sources: the State and Local Coastal Resources Management Act (SLCRMA), R.S. 49:214.21
et seq. (read from legis.la.gov on 2026-11-20); Parish Code Chapter 26 (Supp. 77, through Ord. 26-6-3,
read through `scp-civics:scp-ordinances`); the Local Coastal Program document (`corpus/`, chapter 7).
Chapter 26 is paraphrased here, never copied. Before quoting it, read the section with `code_search.py get 26-N`
and check for later ordinances with `since --section 26`.

This is not legal advice.

## Who decides

| Role | Who | Source |
|---|---|---|
| State administrator | Secretary of the Department of Conservation and Energy, through the Office of Coastal Management (OCM). Chapter 26 and older parish records still say DNR or "the secretary". The department was renamed by Acts 2023 No. 150. | R.S. 49:214.22, .30 |
| Local CZM administrator | The parish Coastal Zone Management office. The parish contracts permitting services to Bella Marketing LLC dba Coastal Permitting (Ord. 16-5-4; Ord. 25-3-7). | Sec. 26-6 |
| Coastal Zone Advisory Committee (CZAC) | 7 members appointed by a Council majority, 4-year staggered terms (Ord. 25-8-7, effective 2025-08-01). It comments on applications when the administrator asks, nominates appeal hearers, helps with the regular report to the secretary, and is the body a citizen-suit request goes to. Ord. 25-4-4 (April 2025) moved its functions to the Planning Commission for up to six months. | Sec. 26-4, 26-10 |
| Appeals panel | Three people appointed by the Council. | Sec. 26-9 |

**Approval history.** The CZAC recommended adoption on 2015-10-01. The Council adopted the program by Ord. 15-10-12 and Chapter 26 by Ord. 15-10-13. The state held its hearing on 2016-05-05. The date of final state and federal (NOAA) approval is **not established**. OCM lists St. Charles among the approved local programs. The parish and the department have renewed implementation agreements by Ord. 17-9-5, 18-10-3, 19-8-14, 22-7-7 and 25-7-8.

The LCP document (chapter 7) cites "Section 19-56 of the Ordinance". That is a draft numbering. The adopted ordinance is Chapter 26, and its 2015 text is reprinted as LCP Appendix B. Sec. 26-4 has since been amended, so read current law from the code, not from Appendix B.

## Local concern or state concern

R.S. 49:214.25 sets the line. The parish issues permits for uses of local concern. The state issues the rest, and the parish only reviews them for consistency with its program and may comment.

- **State concern:**
  - any dredge or fill that intersects more than one water body
  - state-owned lands or water bottoms
  - state-funded projects
  - national-interest projects
  - projects in more than one parish
  - all mineral activities and their dredge and fill
  - all pipelines gathering or carrying oil, gas or other minerals
  - energy facility siting
  - local-concern uses that significantly affect regional, state or national interests
- **Local concern:**
  - private or public projects that aren't state concern
  - maintenance of local uses
  - jetties and breakwaters
  - dredge or fill within one water body
  - bulkheads, piers, camps and cattle walks
  - maintenance dredging
  - private water-control structures under $15,000
  - uses on cheniers, salt domes and similar landforms

The administrator makes the determination, and the secretary can review it (R.S. 49:214.30(C)(1)). Every application, with the local/state determination, goes to the secretary within 2 days (Sec. 26-6).

The committee's agendas mark each application `(LOCAL)` or `(STATE)`. In 2025-2026 most listed applications were state concern: industry, pipelines, Entergy and parish public works projects. Local-concern rows were mostly lot fill and residences.

## When no permit is needed

R.S. 49:214.34(A) exempts listed activities only when they happen **wholly** on land 5 ft or more above mean sea level or within a fastland. That holds "except when the secretary finds" a direct and significant impact on coastal waters. The secretary keeps maps of high land and fastlands for applicants to compare against their footprints, and the applicant is liable for a wrong self-determination (R.S. 49:214.34(B); LCP chapter 7). The LCP also lists:
- the exempt categories, including emergency uses, normal maintenance and repair, a residence or camp, navigational aids, and normal agriculture, forestry and aquaculture;
- a blanket exemption for uses lawfully begun before the permit program;
- uses the secretary finds have no direct and significant impact.

The parish sends its exempt and "no direct and significant impact" findings to OCM for concurrence (Sec. 26-6). The committee's codes:

| Code | Meaning |
|---|---|
| `EXEMPT` | Exempt |
| `NDSI` | No direct and significant impact |
| `CUP` | Permit required, or a permit was issued |
| `DENIAL`, `WITHDRAWN`, `IN REVIEW` | As written |
| `RFD` | Its meaning is not stated on the agendas. Ask the office in writing rather than guess. |

`coastal.py site` checks a point or footprint against the state's Five Foot Contour and Fastlands layers. Its output can say only that an exemption *may* apply.

## The local permit process and its clocks

Chapter 26 periods, counted by `coastal.py clock`:

| Step | Period | Source |
|---|---|---|
| Answer a request for more information | 30 days, or the application is treated as withdrawn | Sec. 26-5 |
| Public notice of a local-concern application | Opens a 25-day comment period. The notice gives the permit number and location. | Sec. 26-6 |
| Request a public hearing (the applicant or a committee majority) | Within 25 days of the official journal publication. Calling a hearing interrupts the processing clock. | Sec. 26-6 |
| Parish comments to the state on a state-concern application | Within 25 days of the official journal notice | Sec. 26-6 |
| Decision | Within 30 days of public notice, or 15 days after a hearing record closes. Written responses to comments. | Sec. 26-6; R.S. 49:214.30(C)(3) |
| Permit term | 2 years, extendable to 3 | Sec. 26-6 |
| After-the-fact permit request | Within 15 days of the activity | Sec. 26-7(c) |

The LCP (chapter 7) also says the parish publishes notice within 10 days of receiving a complete application from the state. It estimates 40 to 50 days to a decision, and 50 to 70 more days with a hearing. Copies of an application are available from the parish CZM office at cost (Sec. 26-6).

**The official journal notice starts the clocks.** The parish's journal is the St. Charles Herald Guide. Notices are titled "Notice of Pending Application" and carry `SCP-yyyy-nn` with the state's P-number. The committee's "last month's determinations" list arrives after the comment window, and often after the appeal window, so it can't serve as notice. Watch the paper with `scp-civics:scp-watch`. Watch state-concern applications through OCM's public notices page (https://www.dce.louisiana.gov/page/coastal-management-public-notices).

## Appeals and review (Sec. 26-9)

- **Administrative appeal:**
  - Filed in writing within 15 days of the decision.
  - Anyone adversely affected, any parish landowner or resident, or any government authority can file.
  - The notice must say how the decision is contrary to law, state the facts, and say what remedy is wanted.
  - **The notice can't raise issues that weren't raised during the application process, except for:** new evidence that diligence could not have found, fraud or corruption, or other good grounds such as a failure to consider pertinent facts.
  - So comment within the 25-day window on every issue you may want to appeal.
- **Public appeal:**
  - Needs 10 or more residents of this parish, or of any parish where impacts may be felt.
  - The request is due in writing within 10 days of the decision, or of the notice of administrative appeal.
  - It is held with a verbatim transcript.
  - The administrator schedules either kind of appeal within 10 days of a complete request.
- **Panel standard:** the appellant must make a prima facie case. The panel asks whether the decision was supported by substantial evidence (R.S. 49:964).
- **Mediation:** good-faith mediation or other recognized dispute resolution stops the appeal clock. Using it to delay is bad faith, with penalties.
- **Court review: two periods in the same section, both stated and neither reconciled here.**
  - Sec. 26-9(r) allows review of the panel's decision on a written request filed in the district court of the project's parish within **15 days** of the panel's final decision. The request must come from an interested party who took part before the panel.
  - Sec. 26-9(w)(3), which follows R.S. 49:214.35, allows a petition in that district court within **30 days** after notice of the secretary's final decision is mailed, or 30 days after a decision on reconsideration.
  - Which applies to a given decision is a question for a lawyer. Until then, treat the shorter period as controlling.
- **Reconsideration:**
  - Sec. 26-9(w)(1) allows a written petition within 10 days of public notice of a final permit, or of receiving written notice of a determination.
  - R.S. 49:214.35(B), as amended, counts the state's 10 days from posting on the department's website.
- **Interim review:** a determination of local or state concern, or of direct and significant impact, can be reviewed immediately when waiting for the final decision would not give an adequate remedy (Sec. 26-9(w)(2), following R.S. 49:214.35).

## Enforcement (Sec. 26-10 to 26-14)

- **Citizen suit:** anyone may sue to enforce the chapter after sending the committee a written request that goes unanswered for 15 days.
- **Fines:** up to $2,000 a day.
- **Other sections:** complaints (26-12), cease-and-desist contents (26-13), entry onto property (26-14).
- **Mitigation:** fees go to a parish fund, or 25% to the state Wetland Conservation and Restoration Fund when the parish has no mitigation bank (26-15, 26-16).

## What the program document adds

- **Chapter 5:** eight goals with objectives and policies.
- **Chapter 6:** 14 Environmental Management Units (Table 6-1), each with maps and its own goals. The permit review checks consistency with the EMU goals for the site. No queryable GIS layer holds the St. Charles EMUs (OCM's EMU layer has no St. Charles rows, checked 2026-11-20), so an EMU placement is read from the chapter 6 figures and must be said to be read from a figure.
- **Chapter 7:**
  - performance standards (the review checklist for a comment)
  - special areas nomination
  - uses of greater than local benefit
  - federal consistency under the Coastal Zone Management Act, which reaches activities on excluded federal lands that affect the coastal zone
  - consistency with the parish's 2030 Comprehensive Plan
