---
name: scp-budget
description: Find and read St. Charles Parish, Louisiana government money records. Covers the annual Consolidated Operating and Capital Budget, proposed and adopted exhibits, hearing amendments, rollover and final amendments, the Roads and Bridges capital program, Public Works capital projects reports, Parish Council millage levies, sales tax history and audited financial statements. Use when the user asks what the parish budgeted or spent on a project, fund or department, what is planned in a council district, what a Council millage is, how a budget gets adopted, or what an audit reported.
argument-hint: "<project, fund, department, council district, millage line or budget year>"
allowed-tools: Bash, Read, Write, Grep, Glob, WebSearch, WebFetch, Skill
---

# St. Charles Parish budget, capital projects and millages

Find the record, cite its document and page, and keep each kind of number apart. If the user wants a file, write it in their project folder. If the working directory is this plugin, ask where. Project findings never go in the plugin.

This is research, not legal or accounting advice. A number that doesn't reconcile is a question for the Finance Department. Don't call it an error, a shortfall or misuse. This skill doesn't draft a comment or send a request.

```bash
BU="${CLAUDE_PLUGIN_ROOT}/skills/scp-budget/scripts/budget.py"
python3 "$BU" cycle --year 2027                         # a budget year's matters and attachment links
python3 "$BU" cycle --year 2027 --dir <folder> --match "adopted|proposed budget|amendments"   # saves those PDFs with text
python3 "$BU" millage --tax-year 2026 --line "road|total"
python3 "$BU" search "turtle pond" --dir <folder> --context 1   # PDF and page for each match
```

Shell state may not carry between calls, so set `BU` in each one. Needs Python 3 and `poppler`, not bayou. `search` writes a `.txt` beside each PDF that lacks one, so copy PDFs from a folder you shouldn't change into your project folder first. Exit `0` means found, `1` means the source answered and nothing matched, and `2` means not checked. Never report `2` as no result. `search` lists any PDF it couldn't read, so say those weren't searched; `bayou:document-ocr` or `ocrmypdf` makes them searchable. Before saving anything, look in `$SCP_CIVICS_DATA/council-attachments/` if that variable is set. It may hold the file already, and that folder is the user's.

## Which number answers the question

The same project can have several amounts, and each means something different. Name which one you're giving.

| Number | Source, as of 2026-11-03 | What it is |
|---|---|---|
| Requested | Proposed budget book, attached to the adoption matter | The president's proposal. It can change at the hearings |
| Adopted | "ADOPTED" or "APPROVED" Exhibit A&B plus the hearing amendments, same matter | Fund totals and the changes made. A project line stays as proposed unless an amendment changes it, so check the amendments. The exhibits don't print project lines, so say "requested, with no amendment found in <files>", not "adopted at" |
| Amended | First amendment, usually May to July and labeled a rollover; final amendment, usually December to May | Carried-over capital money and the true-up to actuals. An amendment can be filed in the following year |
| Spent | Audited financial statements | Actual results by fund. They don't usually show a single project |
| Estimated cost and status | Public Works capital projects report | A project's estimated construction cost, schedule and remarks. It's the department's status report, not an appropriation |
| Multi-year plan | Roads and Bridges Capital Program, Exhibit A | Road program for three fiscal years, adopted by its own ordinance |

In the budget book, capital lines are in each fund's "Narrative Explanation of Capital Outlay". Search for the project and read the whole page, since a name can appear in several funds, such as a drainage pump station and a wastewater lift station. Keep each fund's line separate. Enterprise Fund 401's 2027 page is headed "Memorandum only", and the pages read don't explain that, so quote the heading and ask Finance.

For drainage or levee projects against the Master Drainage Plan, use `scp-civics:scp-master-drainage-plan`, which already joins the plan, capital reports and 2027 requested lines. For PILOTs, use `scp-civics:scp-incentives`.

## 1. Get the year's records

`cycle` finds these by title, on Legistar's public API:

- **Adoption:** calendar of official action, proposed book, Council budget, boards and agencies budgets, hearing dates, amendments by hearing date, adopted exhibits, final ordinance.
- **Amendments:** matters that amend that year's budget.
- **Millage levy:** the prior year's tax roll, which funds this budget year.
- **Capital program:** each Roads and Bridges program whose three years include this one. The programs overlap, so compare them and cite the newest.

Final ordinances are often scans. Exhibits and the Finance millage schedule have a text layer. The 2027 calendar lists a Waterworks capital budget, but the newest title found with "Capital Improvements Budget" was from 2005. So report "no recent Waterworks capital budget title found", and ask.

The API's attachment hyperlink, on a `/snohomish/` path, returned 404. `cycle` builds the working address. If you query the API yourself, use `https://stcharlesgov.legistar1.com/stcharlesgov/attachments/<MatterAttachmentFileName>`.

The parish site blocks scripts, so these need a browser:

- [Annual Budgets](https://www.stcharlesparish.gov/departments/finance/annual-budgets): 2009-2026, and the Finance page links the 2027 proposal.
- [Financial Statements (Audits)](https://www.stcharlesparish.gov/departments/finance/financial-statements-audits): back to 2007.
- [Capital Projects](https://www.stcharlesparish.gov/departments/public-works/capital-projects): the newest report, "2026 10 Capital Projects". Ask the user to save it to a project folder or `$SCP_CIVICS_DATA`, then run `search`. Earlier reports seen were dated 2026-05 and 2026-07, so check for a newer one and cite the report's date. The October report, updated 10/8/2026, is headed "Active Projects" and leaves out lines the July report carried, including on-hold ones, without saying why. So a missing project isn't a finished or cancelled one, and `scp-civics:scp-master-drainage-plan` keeps the July lines.

## 2. By council district

Only part of the record is by district.

- The capital projects report has a Council District column, with some projects in several districts. A site's district is often named in its staff report or Commission agenda. If two records give different districts, quote both and ask Public Works or Planning & Zoning.
- Each council member's office has its own budget, such as 001-400115 for District V in the 2027 amendments.
- The operating budget and fund capital lines aren't broken down by district. Don't assign a parishwide line to a district. To place a named project, use the capital report.

## 3. Millages

`millage` reads the Finance Department's schedule attached to each year's levy ordinance. The Council levied these lines by ordinance each July or August. For tax roll 2026, the schedule's rates matched signed Ord. 26-8-1, read by OCR.

- **The year is the tax roll.** Finance's 2026 mills are "to be collected in 2027". Say which year you mean.
- **It covers Council-levied lines only.** The School Board, Sheriff, assessment district, levee districts and other special districts aren't in it. For the total on one property, use its tax bill or the assessor.
- **Quote the ordinance for a past year.** Schedules can restate: the 2025 schedule shows 0.66 and a 26.37 total for the second Council on Aging line, and the 2026 schedule shows 0.65 and 26.36 for the same year.
- **Before 2023,** the attachment may have another name. `millage` then lists the matter's files.

**Don't give one "total millage".** The parish's published figures don't reconcile, and none explains the others:

| Figure | Source | Label |
|---|---|---|
| 26.36 | Finance schedule, Ord. 26-8-1 | Total parishwide, Council lines, tax roll 2026 |
| 106.17 | FY2025 audit, Exhibit D-6, and 2027 budget | "Total Direct & Overlapping" for 2025, marked unaudited, with a source line reading "2024 Tax Roll" |
| 118.41 to 100.9 | 2027 budget message | The president's description of the total rate |

Exhibit D-6's "St. Charles Parish" and "Parish" columns (19.04 and 32.89 for 2025) don't match the 26.36 either. In the 2027 budget's table of millages, every "Approved 2027 Millage" value equals the schedule's 2024 rate, and every "Current 2027 Millage" value equals its 2025 and 2026 rate. Quote each with its label and source, and ask Finance what the differences are. The budget's table can name a line differently: its "Public Roads" row carries the schedule's Road Maintenance rates.

The Finance schedule's revenue page shows the assessed value it assumed. Any dollar figure of your own needs a dated rate and assessed value, and a label saying it's your arithmetic. Before treating a tax's revenue as available for something, read its stated dedication in the budget book's revenue section, next to the millage table in 2027's.

## 4. Audits

If the `bayou:la-legislative-auditor` skill is available, use it: `agency "St. Charles Parish Council"`. That's the auditor's name for the parish government's audit, and it had 31 reports as of 2026-11-03, the newest FY2025, posted 2026-07-15. Other bodies file separately, such as `St. Charles Parish School Board`, `St. Charles Parish Sheriff`, `St. Charles Parish Tax Collector`, `St. Charles Parish Assessor` and `St. Charles Parish Hospital Service District`. Its `agencies "St. Charles"` lists them. Exit 1 means not found in that search, and exit 2 means not checked.

Without that skill, or on exit 2, use the [parish's audits page](https://www.stcharlesparish.gov/departments/finance/financial-statements-audits) or the By Agency tab at https://lla.la.gov/reports/audit-reports, both in a browser. Until one is opened, report the audit as not checked. Say "not found in LLA reports as of <date>", never "no audit exists". The auditor's link opens a short page leading to the PDF, so confirm a saved file really is a PDF.

When reading an audit:

- Name the firm that signed the opinion, Carr, Riggs & Ingram, LLC for FY2025. An outside CPA's audit is not a finding by the Legislative Auditor.
- Findings are in the Schedule of Findings and Questioned Costs, with a summary of prior findings and management's response. Quote them from there. Budget amendments can be one: FY2025's Finding 2025-001 cites R.S. 39:1311 and the Flood Protection Fund, noted as originating in 2023. Its condition is that budgeted expenditures exceeded actual, the reverse of how R.S. 39:1311(A)(2) words spending, so it doesn't say the parish overspent. Quote it, and read the current year's before describing it.
- "Budget and Actual" schedules compare budget with results by fund, starting with the General Fund and Flood Protection Fund in FY2025.
- The statistical section is marked "(Unaudited)". It includes tax rates, principal taxpayers, sales tax and debt, so cite it as unaudited.

## 5. Sales tax

The Finance [sales tax page](https://www.stcharlesparish.gov/departments/finance/sales-tax-collections) lists the parish's 2% share by year, but stopped at 2020 as of 2026-11-03. For later years, use the audit's "Sales Tax Collections, Last Ten Years" table. The budget book's revenue section describes each tax's dedication. The School Board collects the tax under an agreement with the parish; the parish page points other questions to www.scpsalestax.com.

## 6. How a budget is adopted

Charter Art. V, read from the code's OCR text, so check the page image or use `scp-civics:scp-ordinances` before quoting:

- The fiscal year is the calendar year. The president submits balanced operating and capital budgets, with a budget message, at least 75 days before it starts.
- The Council holds three public hearings and adopts at least 30 days before it starts. Any resident may speak at them.
- Budgets can be amended only during those hearings, and if the Council doesn't act in time, the budget takes effect as submitted.
- After adoption, changes come by supplemental or emergency appropriation or by amendment ordinance. See Art. V, Sec. F for the limits.

State law applies too. In the Local Government Budget Act, read 2026-11-03, R.S. 39:1311(A) has the chief executive advise the governing authority in writing when, within a fund, revenue or beginning fund balance falls short, or actual and projected spending exceeds budget, by 5% or more. Under 39:1311(B), the notice and the amendment are required for a special revenue fund only at $500,000 or more in anticipated expenditures. R.S. 39:1310 then calls for an amendment adopted in an open meeting, and bars one proposing expenditures above estimated funds available. Whether the Act's other parts bind this home rule parish wasn't checked, though its audit applies R.S. 39:1311. The levy title cites Const. Art. VII, Sec. 23 and R.S. 47:1705(B), which weren't read. Look these up with `bayou:la-rs-search`. Without bayou, enter the title and section at https://legis.la.gov/legis/LawSearch.aspx, since its `Law.aspx?d=` numbers can't be guessed.

The dates are in that year's calendar and "hearing-date" attachments. For 2027, the calendar set a 10-day gap from the published Notice of Availability to the first hearing, and hearings were on 10/20, 10/22 and 10/26/2026. The window to speak therefore falls in October, before the adopted exhibits exist. Use `scp-civics:scp-watch` to follow the next cycle.

Code Sec. 2-72 requires Finance to give the Council a quarterly budget-versus-actual report. A Legistar title search on 2026-11-03 found no such reports, and attachments weren't searched. Report "not found in Legistar titles", and request them through `scp-civics:scp-prr` if needed. Finance holds budgets, payments, invoices and audits.

## Reporting

1. **Answer,** with amount, kind of number from the table above, fiscal year, document and PDF page, which can differ from the printed page number.
2. **Sources checked,** each with its date, including any not found or not checked.
3. **Established** and **Not established,** kept apart.
4. **Questions for Finance or Public Works,** and any record to request. This skill lists no phone numbers for them, so use the department's parish page, in a browser.

Every figure needs a source. Check a figure on the page image before it goes in anything published, since `pdftotext` can misalign columns. Budget books and audits are public records, but don't copy preparer names from worksheets into a report when the office will do.
