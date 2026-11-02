---
name: la-prr-submission
description: How to submit (not draft) a Louisiana public records request (PRR) to a specific custodian - which channel, who receives it, fees, follow-up and logging. Per-custodian sections for the St. Charles Parish Industrial Development Board (IDB) and the St. Charles Parish Council/Parish Records portal; stubs for the SCP Council office detail and the St. Charles Parish Sheriff's Office (SCPSO). Use when the user asks where or how to send a records request, after the letter is drafted with bayou:la-public-records-request.
argument-hint: "<custodian: idb | scp-council | scpso | other>"
allowed-tools: Bash, Read, Write, Grep, Glob, WebSearch, WebFetch, Skill
---

# Submitting a Louisiana public records request

Drafting is `bayou:la-public-records-request` (statute text, deadlines, fees). Statute lookups: `bayou:la-rs-search` (R.S. 44:1 et seq.). Both are in the optional bayou plugin; without it, read the current text of R.S. 44:1 et seq. at https://legis.la.gov before quoting any deadline or fee. This skill covers only where a finished request goes, and what to do afterward. Never send a request for the user: drafts stay marked "DRAFT ONLY. NOT SENT." until the user sends them.

## Rules that apply to every custodian

- Each public body that keeps its own files is its own custodian. A request to the parish does not reach a board, agency or office that keeps separate records.
- A record not in active use must be presented immediately. If it is in active use, the custodian certifies that in writing and sets a day and hour within three days (R.S. 44:33(B)). If the custodian questions whether a record is public, it owes a written determination within five days (R.S. 44:32(D), amended by Acts 2024, No. 411; older templates still say three). Both counts exclude Saturdays, Sundays and legal public holidays. R.S. 44:35 covers the remedy for no response. Re-pull the current text before quoting these figures.
- Ask for a written fee estimate above a stated ceiling, offer in-person inspection, and ask the custodian to cite the exemption for anything withheld.
- A request can alert the subject of the records that someone is looking.
- Keep the sent copy and proof of sending (portal confirmation number, sent-email header, certified-mail receipt) beside the draft, and record the send date and any tracking number in the project's notes.
- Name records already produced under an earlier request (e.g. PRR-nnn-yyyy) so the custodian does not re-produce them.

## St. Charles Parish Industrial Development Board (IDB)

Full name: Industrial Development Board of the Parish of St. Charles, Louisiana, Inc. A nonprofit corporation with seven directors appointed by the Parish Council. It handles PILOT leases and conduit revenue bonds, meets a few times a year at 11:30 AM, and holds its own files.

**What is established (as of 2026-11-02):**
- The IDB adopted the Council's Public Records Fee Schedule as its own (Res. 2026-5, 10/26/2026 agenda). That confirms it treats itself as a separate custodian.
- Its agenda contact block is the Council's: Courthouse, 15045 Highway 18 (parish pages also say River Road), P.O. Box 302, Hahnville, LA 70057; 985-783-5125 (Council Secretary's line).
- Web search found no IDB-specific records contact, phone, email, web page or portal. Legistar shows no minutes or attachments for its 2026 meetings.

**What is NOT established:** who the IDB's records custodian is, and whether it takes requests by email or through the parish JustFOIA portal. Do not tell the user either is confirmed.

**Recommended path (in order):**
1. Phone 985-783-5125 (Council Secretary, 8:30-4 Mon-Fri) and ask: "Who is the custodian of records for the Industrial Development Board, and how does it accept requests?" Note the name, date and answer in the request's drafting notes.
2. Send in writing, addressed to "Custodian of Records, Industrial Development Board of the Parish of St. Charles, Louisiana, Inc.", by email to whatever address the phone call gives. If none is given, email the Council Secretary (mimpastato@stcharlesgov.net) with the subject line marked "For the Industrial Development Board" and ask for written confirmation of receipt and routing.
3. Backstop: certified mail, return receipt, to the P.O. Box 302 address above, in the same wording. Certified mail also fixes the date for statutory deadlines.
4. Do not file the IDB request through the parish JustFOIA portal unless the phone call says to; a portal request may be logged as a parish request and routed away from the board.
5. If no written acknowledgment arrives in 3 business days, call again and log it.

## St. Charles Parish Council / Parish Records & Research (SCP)

*Stub - to be filled in with specifics.*

Known so far:
- Portal: https://stcharlesparishla.justfoia.com/publicportal/ (paste the letter body into the description box).
- Email: Parish Records & Research, mimpastato@stcharlesgov.net. Custodian of Public Records is Council Secretary Michelle Impastato; 985-783-5125; Courthouse 3rd floor, 15045 River Road, P.O. Box 302, Hahnville, LA 70057.
- The parish's own page (https://www.stcharlesparish.gov/government/parish-council/public-records-request) says to use its form or call the Council Office. It returns 403 to scripts, so open it in the browser (claude-in-chrome).
- Per the parish page, Sheriff's Office, court, vital and school board records are not handled there.

To add: fee schedule amounts, observed turnaround, how department-specific requests (Planning, Waterworks, Public Works) are routed, text-message and email search scope.

## St. Charles Parish Sheriff's Office (SCPSO)

*Stub - to be filled in with specifics.* Not handled by the parish portal. Still to determine: custodian, channel (form, email, mail), fee schedule, and which record classes are exempt (e.g. active investigations under R.S. 44:3).
