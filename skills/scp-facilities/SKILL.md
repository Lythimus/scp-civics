---
name: scp-facilities
description: St. Charles Parish, Louisiana industrial facilities and who to contact about an odor, flare, smoke, noise, spill or release. Holds a parish-wide roster joining LDEQ AI numbers to EPA registry IDs and RMP filings, finds what is registered near a point or at an address, routes a report by the hour and the situation (911, parish Emergency Operations Center, LDEQ, State Police, National Response Center), and drafts the report without sending it. Use for "what's that smell", "who do I call about the flare", "what plant is at this address", finding a parish facility's AI or EPA ID, or writing up a release.
argument-hint: "<what you saw or smelled, and where and when; or a company, address or ID>"
allowed-tools: Bash, Read, Write, Grep, Glob, WebSearch, WebFetch, Skill, AskUserQuestion
---

# St. Charles Parish facilities and reporting

```bash
FAC="${CLAUDE_PLUGIN_ROOT}/skills/scp-facilities/scripts/facilities.py"
```

Shell state may not carry between calls, so set this in each one that uses it. The script needs only Python 3.

## 1. If it's happening now, give the route first

If anyone may be in danger, say **call 911** and stop there. Otherwise give the route before any research, because an inspector can only measure what's still going on. Read `references/reporting-routes.md` for the numbers, and quote them from there, not from memory.

- **Any hour:** the parish Emergency Operations Center (EOC), (985) 783-5050, is staffed 24/7 and takes odor reports.
- **Weekdays 8:00-4:30:** also LDEQ's Single Point of Contact, 225-219-3640 or 888-763-5424. The caller can stay anonymous. It's closed nights and weekends, so don't send anyone to that line then. The online form takes a report at any hour. Expect days for a reply and weeks to months for the file to post, as described in the reference.
- **Hazmat emergency:** State Police Hazmat Hotline. **Federal record of a release:** National Response Center.

This skill doesn't call or submit anything. The person makes the report.

## 2. Find what's there

`references/facilities.md` is the parish roster. Read its "How to read it" section before quoting a row. Then:

```bash
python3 "$FAC" find "<name, address or ID>" --neighbors   # every LDEQ AI matching, and others at that address
python3 "$FAC" near <lat> <lon> --km 5                    # industrial AIs by distance from a point
python3 "$FAC" roster --md <file>                         # rebuild the roster, about 2 minutes
```

`find` and `near` read LDEQ live. If a source is down, the script says so; fall back on the roster and give its date. `find` and `near --all` search every AI type, and those rows can hold private people's names on complaint and dump-site records, so never copy such a name into a report or a public file.

**Don't name a plant from a smell.** A location, a time and the wind are what the record supports, and a smell doesn't identify its source.

- Several companies share one address (355 Hwy 3142, 11842, 12501 and 16122 River Rd), so "the plant" may be a neighbor.
- Report who's nearby, then "source not established".
- For wind, use `bayou:wind-history`. Without bayou, read the [National Weather Service observations for New Orleans airport (KMSY)](https://forecast.weather.gov/data/obhistory/KMSY.html), which cover about the last three days, and say that the station is miles from the site.
- A facility's chemicals come from its RMP and TRI filings, not from a list of what smells like what: `bayou:epa-rmp-lookup` and `bayou:epa-tri-search`. Without bayou, use the [RMP viewer](https://data-liberation-project.github.io/epa-rmp-viewer/) and [EPA's TRI program pages](https://www.epa.gov/toxics-release-inventory-tri-program).

## 3. Draft the report

Write `report-<yyyy-mm-dd>-<place>.md` in the user's project folder. If the working directory is this plugin, ask where to write it instead. Reports never go in the plugin. Start the file with **DRAFT ONLY. NOT SENT.**

Follow the order of LDEQ's form, which also works as a phone script:

1. **Reporter:** name, phone and email from the file named by `$SCP_CIVICS_PROFILE`. If that's unset or missing, ask, and offer to set one up from `${CLAUDE_PLUGIN_ROOT}/skills/scp-prr/profile.example.md` outside this repository. **Before using them, tell the person that LDEQ can post a named complaint with their name, phone, mailing address and email in its public document system.** Let them choose. If they want to be anonymous, leave these out and give them LDEQ's public line, 225-219-3640, weekdays 8:00-4:30. Anonymous complaints go by phone only, and LDEQ warns they can lack what it needs, so the phone script should cover the place, time and landmarks.
2. **Location:** where the person was, with cross streets or landmarks, and the parish.
3. **Date and time it began,** whether it's still going on, and when it stopped.
4. **What was seen, smelled, heard or felt,** in the person's own words. Include direction of the smoke or flame if seen, and any symptoms if the person chooses to give them.
5. **Possible sources:** LDEQ's "alleged violator address" is a required field on the form. Give the nearest facility only as nearby, with its AI number, as in "nearest registered site: ...". If the person can't point to one, say so.
6. **Wind,** with its source and time, if checked.
7. **Attachments:** photos or video with times. LDEQ's form takes 5 files of 3 MB each.
8. **Requests:** the incident number, and a follow-up on the inspector's findings.
9. **Route:** who to call now and who to file with, and each one's hours.

Keep it to observations. Don't write "violation", "illegal", or that a chemical was present unless a record says so. The regulatory tests in the reference file can't be applied by a resident, so don't state that a standard was exceeded. This is not legal advice.

## 4. After the event

Add these to the draft as next steps, and run them only if asked. Files can take weeks to months to post, so a search that finds nothing soon after an event doesn't show that nothing was filed. To find a complaint's own file, follow "Finding the file" in the reference; EDMS can't search by tracking number.

| What | With bayou | Without bayou |
|---|---|---|
| Facility's permits | `bayou:ldeq-permit-status` | LDEQ's [Check Permit Status](https://internet.deq.louisiana.gov/portal/ONLINESERVICES/CHECK-PERMIT-STATUS) |
| Incident reports and inspections in LDEQ's files | `bayou:ldeq-edms-search` | [EDMS](https://edms.deq.louisiana.gov), search by AI number |
| Compliance and enforcement | `bayou:epa-echo-search` | [ECHO](https://echo.epa.gov), using the roster's registry ID. A complex's record may cover several tenants |
| Federal spill reports | `bayou:csb-nrc-hazmat` | [National Response Center](https://nrc.uscg.mil) data downloads |
| Air monitors nearby | `bayou:public-air-monitors` | Say the check wasn't run |
| Facility's records from the parish | `scp-civics:scp-prr` | Same |
| LDEQ's or another agency's records | `bayou:la-public-records-request` | Write the custodian under R.S. 44:1 et seq. ([legis.la.gov](https://legis.la.gov)); `scp-civics:scp-prr` has the method |

For a project still being rezoned, permitted or given incentives, use `scp-civics:scp-case-check`, `scp-civics:scp-watch` or `scp-civics:scp-incentives`.

## Reporting back

Separate what's established from what isn't, and date it. A row in the roster shows that a site is registered, not that it's operating or that it caused anything. Say "the roster as of <date>" and which address matched.
