---
name: scp-prr
description: Get records from a St. Charles Parish, Louisiana public body. Takes a plain description of the information wanted, works out which custodian holds it (parish government and council, Industrial Development Board, Sheriff's Office, Clerk of Court, School Board), asks the questions that decide scope and speed, drafts the public records request, and can fill the parish JustFOIA form in the browser up to but not including Submit. Also covers where and how to send a request and what to do afterward. Use when the user wants documents, emails or data from a St. Charles Parish body, or asks how to file or follow up on a records request there.
argument-hint: "<what you want to find out or obtain>"
allowed-tools: Bash, Read, Write, Grep, Glob, WebSearch, WebFetch, Skill, AskUserQuestion
---

# St. Charles Parish public records requests

The user describes what they want. This skill works out who holds it, narrows it, drafts it, and optionally fills the parish form. **The user sends it.** Never click Submit, solve a reCAPTCHA, tick an acknowledgment, send an email or mail anything.

This is not legal advice, and the draft is not checked by a lawyer.

Reference files, all under `${CLAUDE_PLUGIN_ROOT}/skills/scp-prr/`:

| File | Read it |
|---|---|
| `references/general-rules.md` | Always, before drafting |
| `references/drafting-patterns.md` | Always, before drafting |
| `references/custodians/parish.md` | Parish government or council records |
| `references/custodians/idb.md` | Industrial Development Board records |
| `references/custodians/scpso.md` | Sheriff's Office records |
| `references/custodians/others.md` | Clerk of Court, School Board, anything else |
| `references/departments.md` | Choosing departments on the parish form |
| `references/fees.md` | Parish requests involving paper, video, media or GIS, or when the user asks about parish cost. Sheriff's Office fees are in its custodian file |
| `references/portal-form.md` | Before writing the parish field sheet or filling the form. It holds the full field map, so no page reading is needed to plan the values |
| `profile.example.md` | When the user has no profile yet |

## Step 1: Choose the custodian

Decide from the subject, say which one and why in one sentence, and let the user correct it. The user should not have to know how the parish is organized.

The custodian still matters, because each public body keeps its own files and a request to one does not reach another. If the records plausibly sit with two bodies, produce one draft per body and say why. For the Industrial Development Board, expect two pieces by item: Council-office items (resolutions, minutes, Council consent) and board items (applicant file, lease, correspondence) sent to the board's president, as `references/custodians/idb.md` lays out. Sheriff's records, for instance, are not reached through the parish form, but the parish may hold its own copies of correspondence with the Sheriff's Office.

If the custodian file says something is unestablished or is a stub, tell the user rather than filling the gap from memory.

## Step 2: Check it is not already public

A request for something posted online costs everyone time. Check first, and name what was found in the draft so it is not produced again.

- Agendas, minutes, ordinances, packet attachments: `bayou:parish-council-agendas` if available, otherwise https://stcharlesgov.legistar.com directly.
- Code of ordinances: `scp-civics:scp-ordinances`.
- Drainage plan documents: `scp-civics:scp-master-drainage-plan`.
- Budgets, capital reports, millages and audits: `scp-civics:scp-budget`.
- The user's project folder, if they have one: look for requests already drafted or sent, and for what came back, so the draft doesn't repeat them.
- Parish web pages: open them in the browser if a script gets a 403.

If a check could not be run, say so in the drafting notes.

## Step 3: Ask what is still unknown

Use AskUserQuestion. Ask only what the prompt and the checks have not answered, and offer concrete choices built from what was found. If you can't ask, list the questions and state each assumption in the drafting notes. These answers decide most of the turnaround.

1. **What the records are.** Get the underlying question too, because it helps name record types. It stays out of the letter.
2. **When it is needed, and why.** Ask for a hearing, vote, comment deadline or other date. Be plain that the Act has no expedited track. A real date supports a request for priority, and that is all.
3. **Conversations?** Emails, letters, calendar entries, texts. If yes, collect:
   - whose accounts (named people and offices)
   - Date From and Date To
   - 5 to 9 search terms, preferring unique terms such as case numbers, project names and company names over common words
   - whether to include text messages or personal accounts used for public business
4. **Speed or completeness.** This sets the shape; see `references/drafting-patterns.md`.
   - One narrow request
   - Part 1 (existing file) and Part 2 (communications), produced on a rolling basis
   - Separate requests, so slow items cannot hold up fast ones
5. **Attorney records.** If they want them, explain that they invite privilege review and may be redacted, and suggest a separate item or request.
6. **Earlier requests** whose productions should be excluded.
7. **Delivery.** Electronic, paper, or inspection. For the parish, ask for a fee ceiling only if paper, video, media or GIS products are involved. For the Sheriff's Office, warn about its $1 per page charge, point out free inspection, and always ask for a ceiling.

For a parish request, choose departments from `references/departments.md`, show the choice, and let the user adjust it.

## Step 4: Pull the current statute

Use `bayou:la-rs-search` if available. Otherwise enter the title and section at https://legis.la.gov/legis/LawSearch.aspx, since its `Law.aspx?d=` numbers can't be guessed. Pull each section the draft cites, normally R.S. 44:1(A)(2)(a), 44:32(C)(3), 44:32(D) and 44:33(B)(1), plus R.S. 1:55 for legal holidays when computing dates. For the Sheriff's Office, also pull 44:3, 44:3.1, 44:32(B) and 44:34, plus 44:35 for a body-worn camera recording. Quote from what comes back. Do not reuse wording from an earlier letter, and do not quote from memory: the Act has been amended repeatedly and the day counts differ by section.

## Step 5: Draft

Do not write in the plugin folder. If the working directory is the plugin itself, ask where the draft should go. Otherwise write to the user's project folder as `prr-<custodian>-<short-subject>-<YYYY-MM-DD>.md`, headed **DRAFT ONLY. NOT SENT.**

Requester details come from the file named by `$SCP_CIVICS_PROFILE`. If that is unset or missing, ask, and offer to set up a private profile from `profile.example.md` outside this repository. Never copy those details into the plugin.

The draft holds:

1. **Drafting notes** (deleted before sending): what was checked, what is unconfirmed, fees that apply, and that a request can alert the subject of the records.
2. **Field sheet** for the parish form: every value from `references/portal-form.md`. For other custodians: the address, channel and delivery method.
3. **Request text**, with a date line, in plain text that survives flattening (`Part 1:`, `1.`, `•`). The parish form removes line breaks and does not render Markdown.

Then run the checklist at the end of `references/drafting-patterns.md`, fix what it catches, and tell the user about anything left on purpose.

## Step 6: Fill the parish form, only if asked

Follow `references/portal-form.md`. Plan the values from its field map, not by exploring the page, then check the page against the map after filling. Show the exact values and get a yes in chat on every run. Enter only the approved values. Leave the street address blank unless the user asks otherwise. Leave the tab open and list what remains for the user: review, tick the acknowledgment, attach any letter, reCAPTCHA, Submit.

`bayou:la-public-records-request` never touches a web form. This skill fills one field by field at the user's request and still never sends, so the rule "skills draft and research; they never send a request" holds. Only the parish form is covered. Without claude-in-chrome, hand over the field sheet for pasting.

## Step 7: Hand back

Tell the user:

- The draft path, and how to send it.
- **Parish requests: they will get emails about the request.** Parish notices come from a `request.justfoia.com` address, so check spam. Portal messages may themselves be public records.
- Parish portal tracking: https://stcharlesparishla.justfoia.com/publicportal/home/track needs both the request number and the security key. Keep them in private notes; anyone holding both can see the request and the requester's form details.
- **Other custodians:** there is no portal. For the Sheriff's Office, follow "Hand-back for this custodian" in its file.
- The statutory dates, computed from the send date with legal holidays excluded (from the receipt date for the Sheriff's Office), and a suggestion to put them on a calendar.
- What comes next, from `references/general-rules.md`: checking the production against each numbered item and how to follow up.
- Productions are often scanned images. `bayou:document-ocr` handles them; without bayou, name the files as needing OCR and say it was not run.

$ARGUMENTS
