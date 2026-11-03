---
name: scp-incentives
description: Trace a St. Charles Parish, Louisiana project's local tax incentives through the Industrial Development Board (IDB), Parish Council, State Bond Commission and ITEP, and name the taxing bodies affected. Covers PILOT leases, payments in lieu of taxes, "Lease Agreement and Agreement to Issue Bonds", acts of conveyance, conduit revenue bonds, IDB audits and minutes, Council consent under the IDB's articles, the resident-hiring policy, and Industrial Tax Exemption resolutions. Use when the user asks what incentives a St. Charles project has or is seeking, what an IDB resolution did, or who loses or gets tax revenue.
argument-hint: "<company, project, applicant LLC, site or IDB resolution number>"
allowed-tools: Bash, Read, Write, Grep, Glob, WebSearch, WebFetch, Skill
---

# St. Charles Parish incentives trace

Trace one project and write `incentives-<project>.md` in the user's project folder. If the working directory is this plugin, ask where to write it instead. Project findings never go in the plugin.

This is research, not legal advice. A missing step is a question for the Council Secretary or a lawyer. Never write "illegal", "void" or "improper".

```bash
IN="${CLAUDE_PLUGIN_ROOT}/skills/scp-incentives/scripts/incentives.py"
MR="${CLAUDE_PLUGIN_ROOT}/skills/scp-meeting-record/scripts/meeting_record.py"
```

Shell state may not carry between calls, so set these in each one that uses them. Needs `poppler`.

## How the money works

The IDB is a nonprofit public corporation under R.S. 51:1151 et seq. and Code Sec. 19-13. The Council appoints its seven directors. Property it owns is exempt "from all taxation in the state of Louisiana", and it may require the lessee to pay a sum in lieu of ad valorem taxes "through the normal collecting agency", capped at the taxes the lessee would otherwise owe (R.S. 51:1160). The parish isn't liable on its bonds (R.S. 51:1161).

The pattern in its 2021-2026 records, which a project may not follow in full:

1. Preliminary approval of the company's proposal.
2. A "Lease Agreement and Agreement to Issue Bonds", the PILOT lease, setting a bond ceiling and the rent.
3. An act of conveyance putting property in the IDB's name, sometimes repeated yearly as additions are built.
4. Amendments changing the rent terms.
5. Bonds, if any are issued. A lease can run for years with none.

## 1. Fix the names

List the applicant LLC, parent, affiliates, site, any project code name and each resolution number the user has. Filings often use a different entity from the announcement. Search every variant at each step, and report which ones you used. Agendas can misspell an applicant within a single meeting, so read every resolution `idb` prints, not only those marked `[match]`.

## 2. Get the lease list from the audits

The audits are the only public list found of every lease, because Legistar starts too late. As of 2026-11-03, the newest one confirmed was FY2023, so a later lease won't be in it. Look for newer years: open the by-agency tab at https://www.lla.la.gov/reports/audit-reports in a browser, or search the web for `"Industrial Development Board of the Parish of St. Charles" site:lla.la.gov`. Check the entity name, since other parishes' boards have similar names.

```bash
python3 "$IN" audit --url "<PDF URL>" --dir <project folder>/audits
```

It prints the "Direct Financing Leases" note: each lessee, year, term, bond ceiling, administrative rent, and whether bonds were issued. Absence from an audit means only that the lease wasn't listed for that period.

## 3. Read the IDB's own record

```bash
python3 "$IN" idb --term "<name>" --term "<name>" --dir <project folder>/idb
python3 "$IN" replays
```

| Period | What is public, as of 2026-11-03 |
|---|---|
| 2025-12-22 on | Legistar agendas. Signed minutes, with adopted resolutions and exhibits, are attachments on the meeting page once a later meeting approves them. The scans have a text layer with OCR errors, so check figures against the page image |
| Before that | Not on Legistar. Later resolutions recite earlier resolution numbers, dates, lease dates and conveyance amounts. Cablecast has some replays from 2021 |

Agenda items carry no matter number, so `bayou:parish-council-agendas track` won't link them. For each resolution, record its number, date, action, lease date and term, amounts, mover, and votes by name.

For a meeting with no signed minutes yet, the result isn't established by its agenda. Use the replay with `scp-civics:scp-meeting-record` and report it "as spoken".

Read the lease's rent terms when you have them. Besides PILOT rent there can be administrative rent to the IDB and supplemental rent. Ask who receives each one, since the audit's "same proportion" language describes PILOT payments.

## 4. Look for Council consent

Article XIII of the IDB's articles says no official action "regarding the financing of any capital project or the issuance of any bonds shall be taken without the prior consent of the governing authority" of the parish, "given by resolution or ordinance". The 2021 amendments didn't change that article. The IDB's audits repeat it. The articles are the scanned "Current Information" file on the [IDB's board page](https://stcharlesgov.granicus.com/boards/w/93386f0e12a43d7c/boards/44516); read them with OCR, and quote only what you have checked.

```bash
python3 "$IN" council --term "<name>" --term "Industrial Development Board" --term "Agreement to Issue Bonds"
```

Also search the resolutions and minutes from step 3 for a cited Council resolution or ordinance number. As of 2026-11-03, title searches found no consent item for the leases tried, and the two sets of signed minutes read cited none. Consent may sit under a title that doesn't name the project, so report "no consent found in <sources>, <date>", not "no consent". The requirement comes from the articles, which Code Sec. 19-14 ties to Ord. 66-3-561, not from Chapter 7: R.S. 51:1165 says no proceedings, notice or approval are required for bonds except as that chapter provides. So don't frame a gap as a statutory violation. Whether the articles bind here, whether a lease with no bonds yet issued is a covered action, and whether an earlier action counts as consent are open questions. Ask the Council Secretary, 985-783-5125.

## 5. Check the hiring commitment

Code Sec. 19-16(b) (Ord. 82-7-14) requires those using these services to employ "whenever reasonably possible" at least 40% parish residents. The IDB must communicate that policy to each applicant, who must commit to it. Say whether the record read shows that commitment. If not, add it to the records list in step 9.

## 6. Check the State Bond Commission

R.S. 51:1157.1 requires SBC approval of IDB bonds and of any instrument securing them. Use `bayou:la-bond-dockets` (`sbc_dockets.py search <names> --from YYYY-MM-DD`). Without bayou, read agendas at https://www.treasury.la.gov/state-bond-commission.

Report "not found on SBC agendas <first>-<last>". No docket is expected if no bond was issued, so check the audit first. Whether an agreement to issue bonds needs SBC approval before any bond issues is a legal question. If bonds do issue, look for a TEFRA hearing notice. R.S. 51:1165 limits what the chapter itself requires, so how the public hears of an IDB resolution beyond its posted agenda isn't established.

## 7. Check other incentives

PILOT and ITEP can apply to different property of one company, so check for both.

- **State record:** `bayou:itep-lookup` (`fastlane.py search <name> --parish "St. Charles"`, then `compare`). Without bayou, use LED's [FastLane public reports](https://fastlaneng.louisianaeconomicdevelopment.com/public/reports).
- **Council:** `python3 "$IN" council --term "Industrial Tax Exemption"` shows the Council's ITEP resolutions and project IDs.
- **Local ITEP Committee:** see its roster in the `scp-civics:scp-meeting-record` officials file. Its meetings and how to find its decisions weren't probed, so say what you looked at.
- **Other agreements:** also search the company's name for cooperative endeavor or other direct agreements with taxing bodies, such as the foreign trade subzone agreement in Ord. 23-6-3, which lists the bodies that signed it.

## 8. Name the taxing bodies

The audit says the parish collects PILOT payments and distributes them "in the same proportion as ad valorem tax would be distributed". So every body with a millage on the property is affected. Use the sheet for the year in question. As of 2026-11-03, the [assessor's page](https://stcharlesassessor.azurewebsites.net/app/clientpages/stcharles/about.html) posted sheets only through 2020, so get newer rates from the assessor or the Louisiana Tax Commission, and date what you use.

The 2020 sheet lists these parishwide. The grouping is by each line's name, so confirm who levies a millage before saying so:

- **Parish government:** general alimony, recreation, council on aging, mosquito control, wastewater, road lighting, health unit, roads and bridges, fire protection, 911, ARC, levees and flood protection.
- **Public library**
- **Public schools**
- **Hospital Service District No. 1**
- **Law enforcement district**
- **Assessment district**

It adds a levee district by bank: Lafourche on the west (districts 1, 2, 4, 7), Pontchartrain on the east (3, 5, 6). Confirm the site's bank with `bayou:parish-assessor-gis` or the assessor.

Show each body's share only as arithmetic from a dated sheet, labelled as yours. Don't state dollars lost without the assessed value, lease schedule and exemption. No statewide rule requiring each taxing body to approve a St. Charles PILOT has been established here, so frame that as a question.

After a conveyance, the IDB should appear as owner of record. Check with `bayou:parish-assessor-gis` or the assessor, and note that its data lags. The act and a notice of lease should be in the conveyance records; see `bayou:eclerks-land-index`, or the Clerk of Court without bayou. The user buys any pass.

## 9. Write the report

1. **Status as of <date>:** the project's stage and next step.
2. **Timeline:** date, body, action, document and page, amount, vote, one row each. Mark any row taken from a recital, not the original. Audit years and lease dates can differ, so cite each.
3. **Checks:** Council consent, hiring commitment, SBC, ITEP, each with sources searched and date.
4. **Taxing bodies:** names, sheet year and any labelled arithmetic.
5. **Established** and **Not established**, kept apart.
6. **Records to request:** usually the lease and exhibits, application, hiring commitment, unposted minutes and PILOT distribution records. The IDB is its own custodian, so hand this list to `scp-civics:scp-prr`. The parish holds PILOT collection and distribution records, and the two may need separate requests.
7. **Questions for the Council Secretary.**

Every number and date needs a source. This skill doesn't draft or file a request or comment.
