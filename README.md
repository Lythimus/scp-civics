# St. Charles Parish Civics

A Claude Code plugin for residents, journalists and advocates researching local government in St. Charles Parish, Louisiana.

It records how parish processes work and where the records are, including what the parish portals and websites make hard to find.

**This is not legal advice.** Check every citation, deadline and contact against its source before relying on it. Parish staff, fee schedules and code sections change, and each skill says when its information was last checked.

## Skills

| Skill | Use it for |
|---|---|
| `scp-civics:scp-land-use-process` | Rezonings, Future Land Use Map amendments, plats and waivers, variances, permit routes, notice rules, Herald-Guide legal notices, Legistar quirks, the Industrial Development Board, parish contacts |
| `scp-civics:scp-case-check` | Auditing one rezoning, plat or variance from its case number: its path, notice day counts, deadlines, Future Land Use Map resolution, plat against drainage study, waivers, and questions for staff |
| `scp-civics:scp-watch` | A standing search for a project, applicant, place or topic across the Herald-Guide legal notices and Parish Council matters on Legistar, reporting only what is new since the last run. The watch lives in your project folder. |
| `scp-civics:scp-meeting-record` | What was said and voted at a parish meeting: finds the recording, makes a timestamped transcript (YouTube captions or local Whisper), checks it against the agenda, flags garbled names against a roster of officials and board members, and checks quotes and votes against Legistar |
| `scp-civics:scp-ordinances` | Searching the parish code, Charter, zoning and subdivision appendices from a local copy, reading a section by number, and checking Legistar for later amendments |
| `scp-civics:scp-master-drainage-plan` | Checking a proposed project against the parish Master Drainage Plan: which study covers the site, which planned improvements it touches, what they cost, and whether they have been funded or built |
| `scp-civics:scp-comprehensive-plan` | What the 2030 Comprehensive Plan (2011) and its 2022 Update say about a place, parcel, Future Land Use category or topic, with document and page. Keeps the map designation apart from goals and recommendations, and says which map is current |
| `scp-civics:scp-prr` | Getting records from a St. Charles Parish body: finds the custodian, asks what decides scope and speed, drafts the request, can fill the parish portal form up to Submit, and covers follow-up |

The plugin drafts and researches. At your request it can fill the parish records form, but you review it and click Submit. It never sends a request, files a comment or buys a record.

## Install

```
/plugin marketplace add Lythimus/scp-civics
/plugin install scp-civics@scp-civics
```

Some scripts need Python 3. Herald-Guide OCR also needs `poppler` and `tesseract`. Code search needs `poppler`. Meeting transcripts need `yt-dlp` for YouTube captions, or `ffmpeg` and `uv` for local Whisper, whose model is a download of about 3 GB.

## Using it with bayou

This plugin works alone. [Bayou Blockade](https://github.com/Lythimus/bayou-blockade-skills) is an optional companion covering Louisiana and federal environmental-justice research. Install both and the `bayou:` skills named in these instructions become available, including:

| Bayou skill | Used for | Without bayou |
|---|---|---|
| `la-public-records-request`, `la-rs-search` | Drafting a request and quoting current Title 44 | Read R.S. 44:1 et seq. at [legis.la.gov](https://legis.la.gov) |
| `parish-council-agendas` | Searching agendas, minutes and legislation | Use [parish Legistar](https://stcharlesgov.legistar.com) directly |
| `parish-assessor-gis` | Parcel, owner and zoning lookups | Use the parish assessor's site |
| `itep-lookup`, `la-bond-dockets` | Incentive and bond records | Use LED FastLane and State Bond Commission agendas |
| `hearing-prep --debrief` | Comparing a meeting transcript with prepared questions | `scp-meeting-record` writes its own record |
| `la-coastal-use-permits`, `fema-flood`, `document-ocr` and others | Coastal permits, flood zones, scanned documents | The skill names the source, and says the check was not run |

## Plan documents

`skills/scp-master-drainage-plan/corpus/` holds Markdown conversions of the parish's Master Drainage Plan executive summaries and public-meeting decks, with figure and table images. `skills/scp-comprehensive-plan/corpus/` does the same for the 2030 Comprehensive Plan (2011) and its 2022 Update, about 19 MB. Together the images make this plugin about 70 MB to install. They are there because the plan has no maps in data form, so locating a site means reading the drawings.

The source PDFs are not included; the parish publishes them on its website. The Apache license covers this project's own work, and the plan documents remain parish records. Each corpus's `STATUS.md` records what was verified in the conversion and what was not, and `references/adding-documents.md` describes the method.

To check against your own copies of the PDFs and council attachments, set `SCP_CIVICS_DATA` to their folder.

## Parish code

This repository doesn't include the code's text. To use `scp-ordinances`, save a whole-code PDF from [Municode](https://library.municode.com/la/st._charles_parish/codes/code_of_ordinances) in your browser, set `SCP_CIVICS_DATA`, and build a local index:

```
python3 skills/scp-ordinances/scripts/code_search.py build "<pdf>"
```

## Your details

To keep your requester details out of the repository, copy `skills/scp-prr/profile.example.md` elsewhere and set `SCP_CIVICS_PROFILE` to the copy.

## Contributing

See [CLAUDE.md](CLAUDE.md). This repository is public, so nothing specific to a person's own case belongs in it. Run `scripts/check-public.sh` before committing.

## License

Apache-2.0. See [LICENSE](LICENSE).
