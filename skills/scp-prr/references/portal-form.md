# Parish JustFOIA form

Read and test-filled 2026-11-02 with placeholder values, not submitted. **Fill from this map without studying the page first.** Afterward, check the page against the map and report any difference.

Direct form URL: https://stcharlesparishla.justfoia.com/Forms/Launch/544da055-4116-4fab-9cbc-5a74469c041e

Going through https://stcharlesparishla.justfoia.com/publicportal/home/newrequest also works, but its **Public Records Request** link opens the form in a new tab, so a fill aimed at the first tab misses it.

The form says requests need not be in writing; a request can also be made through the Council Office at 985-783-5125.

## Field map, in page order

| Label | Control | Required | Value |
|---|---|---|---|
| Name of Requestor | Text | Yes | Profile |
| Phone | Text, `###-###-####` | Yes | Profile |
| Email | Email | Yes | Profile. Notices go here |
| Company/Organization | Text | No | Profile, usually blank |
| Address | Text | No | **Blank by default.** Its "123 Example Drive" is placeholder text, not a value |
| City, State, Zip | Text | No | Profile |
| Department(s) | 24 checkboxes, none ticked | No | Set chosen ones to `true`. Exact labels below |
| Description of Request | Textarea | Yes | Plain text. Line breaks collapse and Markdown shows literally. If it runs past about 2,700 characters, summarize and attach the letter |
| Click here to view our Fee Schedule | Checkbox | No | **Leave alone.** Fees are in `fees.md` |
| Estimated Date of Requested Record(s) | Free text | No | The date range |
| Are you requesting email/correspondence record(s)? | Select: `No` (default), `Yes` | No | Set `Yes` first when conversations are wanted; the next four fields then appear |
| Date From | Text, shown after Yes | No | `MM/DD/YYYY` was accepted on screen; format is not checked until submission, which was not tested |
| Date To | Text, shown after Yes | No | Same |
| Email Account(s) | Text, shown after Yes | No | Addresses or names and titles, separated by semicolons |
| Key Search Words | Text, shown after Yes | No | Terms separated by semicolons |
| Preferred Delivery Method | Select: `Electronic` (default), `Paper`, `Onsite` | No | `Onsite` displays as "Review/Inspect Onsite" |
| "By submitting this request, I understand..." | Checkbox | User only | **Leave alone.** Accepts terms: no duty to create records, release under R.S. 44:33, a possible deposit |
| Attachments | File upload | No | Attach only files the user names. A hidden "Attachments are required." alert exists in the page, but no attachment requirement is known; submission was not tested |
| reCAPTCHA, SUBMIT | | User only | **Leave alone** |

## Department labels

Administration (Parish President & Executive Staff); Animal Control; Community Center; Community Services; Contract Monitor; Council Office; Economic Development & Tourism; Finance; GIS; Government Buildings; Grants; Homeland Security & Emergency Preparedness/Hurricane Preparedness; Information Technology (IT); Legal; Parks & Recreation; Personnel; Planning & Zoning (Violations, permits, licenses, etc.); Procurement; Public Information; Public Works/Engineering; Risk Management; Wastewater; Waterworks; Workforce Investment Act (WIOA).

## Filling it

1. Show the user every value that will be entered, including personal details, and get a clear yes in chat. Approval on an earlier run does not carry over.
2. Open the direct URL in a new tab with claude-in-chrome.
3. Get element references with one `read_page` using filter `all`. References change on every load, so they cannot be saved. Filter `interactive` left out the checkboxes, Description and selects in the one test run. Page JavaScript may be blocked, so do not rely on it. Expect permission prompts.
4. Enter approved values with `form_input`. Set the email question to `Yes`, then use `find` for its four fields, which have no references until they appear.
5. **Check the page.** Compare the labels and options read in step 3 with this map, and take screenshots to compare the entered values with the field sheet. If anything differs, do not guess: leave that field blank, tell the user, and note that this file needs updating.
6. Stop. Do not tick the acknowledgment or fee box, solve the reCAPTCHA or click SUBMIT. Do not press Enter inside a single-line field, in case that submits the form.
7. Leave the tab open and tell the user what remains.

If a step fails twice, stop and hand over the field sheet for pasting.

## After submission

- The form returns a reference number (`PRR-nnn-yyyy`) and a security key. Save both.
- A weekend submission may be logged on the next business day, so keep the confirmation.
- Records appear under the request on the tracking page, and notices come by email.
