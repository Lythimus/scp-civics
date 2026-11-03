# St. Charles Parish Civics

A Claude Code plugin for residents, journalists and advocates researching local government in St. Charles Parish, Louisiana.

It records how parish processes work and where the records are, including what the parish portals and websites make hard to find.

**This is not legal advice.** Check every citation, deadline and contact against its source before relying on it. Parish staff, fee schedules and code sections change, and each skill says when its information was last checked.

## Skills

| Skill | Use it for |
|---|---|
| `scp-civics:scp-land-use-process` | Rezonings, Future Land Use Map amendments, plats and waivers, notice rules, Herald-Guide legal notices, Legistar quirks, the parish code on Municode, the Industrial Development Board, parish contacts |
| `scp-civics:scp-master-drainage-plan` | Checking a proposed project against the parish Master Drainage Plan: which study covers the site, which planned improvements it touches, what they cost, and whether they have been funded or built |
| `scp-civics:scp-prr` | Getting records from a St. Charles Parish body: finds the custodian, asks what decides scope and speed, drafts the request, can fill the parish portal form up to Submit, and covers follow-up |

The plugin drafts and researches. At your request it can fill the parish records form, but you review it and click Submit. It never sends a request, files a comment or buys a record.

## Install

```
/plugin marketplace add Lythimus/scp-civics
/plugin install scp-civics@scp-civics
```

Some scripts need Python 3. Herald-Guide OCR also needs `poppler` and `tesseract`.

## Using it with bayou

This plugin works alone. [Bayou Blockade](https://github.com/Lythimus/bayou-blockade-skills) is an optional companion covering Louisiana and federal environmental-justice research. Install both and the `bayou:` skills named in these instructions become available, including:

| Bayou skill | Used for | Without bayou |
|---|---|---|
| `la-public-records-request`, `la-rs-search` | Drafting a request and quoting current Title 44 | Read R.S. 44:1 et seq. at [legis.la.gov](https://legis.la.gov) |
| `parish-council-agendas` | Searching agendas, minutes and legislation | Use [parish Legistar](https://stcharlesgov.legistar.com) directly |
| `parish-assessor-gis` | Parcel, owner and zoning lookups | Use the parish assessor's site |
| `itep-lookup`, `la-bond-dockets` | Incentive and bond records | Use LED FastLane and State Bond Commission agendas |
| `la-coastal-use-permits`, `fema-flood`, `document-ocr` and others | Coastal permits, flood zones, scanned documents | The skill names the source, and says the check was not run |

## Drainage plan documents

`skills/scp-master-drainage-plan/corpus/` holds Markdown conversions of the parish's Master Drainage Plan executive summaries and public-meeting decks, with figure and table images. The images make this plugin about 50 MB to install. They are there because the plan has no maps in data form, so locating a site means reading the drawings.

The source PDFs are not included; the parish publishes them on its website. The Apache license covers this project's own work, and the plan documents remain parish records. `corpus/STATUS.md` records what was verified in the conversion, and `references/adding-documents.md` describes the method.

To check against your own copies of the PDFs and council attachments, set `SCP_CIVICS_DATA` to their folder.

To keep your requester details out of the repository, copy `skills/scp-prr/profile.example.md` elsewhere and set `SCP_CIVICS_PROFILE` to the copy.

## Contributing

See [CLAUDE.md](CLAUDE.md). This repository is public, so nothing specific to a person's own case belongs in it. Run `scripts/check-public.sh` before committing.

## License

Apache-2.0. See [LICENSE](LICENSE).
