# After sending

Statute text pulled from legis.la.gov on 2026-11-17: R.S. 44:31, 44:32 (last amended by Acts 2024, No. 411), 44:33, 44:34, 44:35 (last amended by Acts 2024, No. 493) and 44:37. Pull them again before quoting, as Step 4 of the skill says. This is not legal advice.

Everything here writes to the user's project folder, never the plugin. Request numbers, security keys, the requester's details and what came back are private.

## 1. Keep a log

One file per project, `prr-log.md` beside the drafts. One row per request number, including numbers the custodian opens itself:

| Column | What goes in it |
|---|---|
| Request | Short subject and the draft file it came from |
| Custodian | And the channel used: portal, email, mail, in person |
| Number | The custodian's request number, or "none" (Sheriff's Office letters have none) |
| Sent | Date and time, and where the proof is saved: portal confirmation, sent-email header, certified-mail receipt |
| Received | Mail only: the date on the return receipt or stamped copy |
| Dates | Output of `dates` (section 2) |
| Replies | Date, sender, one line on what it says, and the saved file |
| Productions | Date, folder, and its `INDEX.md` |
| Status and next | What is open, and the next date to act |

- **Keep portal security keys out of the log.** Anyone holding a number and its key can see the request and the requester's form details. Keep keys in a separate private file the user controls. Don't print them in chat, drafts or indexes.
- **A split gets its own row.** A custodian can open a subsidiary request, for example to run an email search separately. Note which number it came from and which fields it took.
- **Save each notice as a file** (`.eml`, or a PDF of the page) beside the log. A pasted copy is not a record of who sent what and when.
- **Record what was actually sent.** If the sent text differs from the approved draft, the quoted copy in the custodian's reply or the sent folder is the record.

## 2. The clock

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/skills/scp-prr/scripts/prr_after.py" dates --sent YYYY-MM-DD [--received YYYY-MM-DD] [--today YYYY-MM-DD] [--holiday YYYY-MM-DD]
```

| Period | Statute | Counted from |
|---|---|---|
| A record "in active use": the custodian certifies that in writing and fixes "a day and hour within three days" | 44:33(B)(1) | The statute doesn't say; this skill counts from the application |
| A question whether a record is public: written notice of the determination, the reasons, and "a reference to the basis under law", "within five days … of the receipt of the request" | 44:32(D) | Receipt |
| No "determination in writing" and no "estimate of the time reasonably necessary for collection, segregation, redaction, examination, or review" after five days, and the requester may sue | 44:35(A) | "the date of his in-person, written, or electronic request" |

- All three exclude "Saturdays, Sundays, and legal public holidays". The holiday table is the one `scp-civics:scp-government` uses for meeting notice (R.S. 1:55). Mardi Gras and some observed days count only if the parish declared them, so the script shows both readings when one falls inside a period.
- **Day 1 is the first business day after the start date.** That is this skill's convention. The Act doesn't say how to count, and how a court would count isn't established.
- **Mail has two possible start dates.** 44:32(D) counts from receipt. 44:35(A) says "the date of his … request", which for a mailed letter could be the mailing date or the receipt date. The script shows both; don't choose one for the user.
- Portal and email requests are received the day they are sent, unless the custodian says otherwise.
- **What stops the 44:35(A) count** is a written determination or an estimate of time. An acknowledgment, or "research in progress" with no date, is neither. Whether a long estimate is "reasonably necessary" is a question for a court, so record it without calling it unreasonable.

## 3. Read each reply

Take the reply's own words, find its row, and log it. Quote the statute only where the reply calls for it.

| The reply says | What the Act says | Check | Next |
|---|---|---|---|
| Received, or research in progress, no date | Neither a determination nor an estimate (44:35(A)) | Business days since the request (`dates --today`) | Wait. Past day 5, a short status request (template B) |
| An estimated date | An estimate of time stops the 44:35(A) count | The date, and what it covers if the request was split | Calendar it. If a hearing or deadline comes first, offer to narrow (template B) |
| Asks what is meant | The custodian may ask about "the specificity of the records sought" if it "is unable to ascertain what records are being requested" (44:32(A)(1)), but may not ask why | Is the question about specificity, or about purpose? | Answer the specificity question. Don't give a purpose |
| Too much work, or would disrupt operations | Access may be denied only "after reasonable attempts to narrow or specify the request with the requestor" (44:32(A)(2)) | Did the custodian offer to narrow? | Narrow within the original fields, so it isn't a new request (template B) |
| Fee estimate or prepayment | Copies may be withheld if the requester "fails to pay the applicable copying fees after being notified of the amount in advance of production" or has "an outstanding balance from a prior request". The custodian "may request payment of fees in advance" and must post its schedule (44:32(C)(1)(a)). No fee to examine a record, and none "for examination or review to determine if a record is subject to disclosure" (44:32(C)(3)) | The charge against the posted schedule: parish `fees.md`, Sheriff's Office `custodians/scpso.md` | Pay, drop items, or inspect for free instead |
| Withheld or redacted | The written notice "shall contain a reference to the basis under law" (44:32(D)). The public part is to be separated and made available (44:32(B)). The custodian bears the burden of proof (44:31(B)(3)) | Is a legal basis cited for each label or withheld item? Was the rest released? | If no basis is cited, ask for it, label by label (template A). Don't guess which statute a label stands for |
| The record is held elsewhere | When a record "is not in the custody or control" of the person asked, that person "shall promptly certify this in writing", giving the reason, its location, who has it, and how and when it left (44:34) | Does the reply name a vendor, counsel or another body? | Ask for the 44:34 certificate, and send a request to the holder if it is a public body |
| No responsive records | The Act reaches existing records. Whether 44:34 applies to a record that never existed isn't established | Does any produced or posted record mention the missing one? | Template A, naming the record that shows it exists |
| In active use | A written certificate fixing "a day and hour within three days" (44:33(B)(1)) | Was a day and hour given? | Go at that time, or ask for one |
| Too burdensome to segregate | The custodian "shall so state in writing and shall state the location of the requested record" (44:33(A)(2)) | Was the location given? | Inspection, then copies of what matters |
| A second request number | A split. Each part has its own production | Which items went where | Log both, and track each |
| Complete | The custodian considers it finished. That doesn't mean everything was found | Section 4 | Reconcile, then template A if anything is missing |
| From outside counsel | Counsel answers for the custodian | Counsel's file number | Copy counsel on later letters and quote the number |

**Parish practice, observed 2026-11:** a redacted file can carry a one-page "Public Records Exemptions" sheet. It lists a reason label (`Privacy Information`, `Client Privilege`) and a page count, with no statute cited. If a production's sheet cites no basis, template A asks for the legal basis behind each label.

## 4. Index and reconcile a production

1. Save the email or letter that delivered the files. Download the files into a new folder in the project.
2. Run the index. It writes `manifest.csv` and an `INDEX.md` skeleton, and never overwrites either unless given `--force`:

   ```bash
   python3 "${CLAUDE_PLUGIN_ROOT}/skills/scp-prr/scripts/prr_after.py" index "<download folder>" [--out "<folder>"]
   ```

   For each file it records size, SHA-256, pages, and which pages have no text layer. It finds exemption and redaction markers (an exemption sheet, `Privacy Information`, `Client Privilege`, `Redacted`, an R.S. 44 citation) and flags byte-identical copies. It also lists files whose text is mostly contained in another, such as the same minutes with a received stamp added. Exit 1 means an empty folder; exit 2 means something was not read, or poppler is missing.
3. **OCR image-only files.** Use `bayou:document-ocr`. Without bayou, run any OCR available and save the text beside the PDF as `<name>.txt`, or list the files as needing OCR and say it was not run. Rerun with `--force` after saving OCR text, so markers on image-only pages are found. Exemption sheets are often image-only.
4. **Read every file** and fill the description and item columns. The script doesn't decide what a file is, and doesn't pair files whose text overlaps only partly.
5. **Fill "Against the request"** from the request as sent, one row per numbered item:
   - produced
   - partly produced
   - produced under a split request number
   - withheld, basis cited
   - withheld, no basis cited
   - certified not in custody (44:34)
   - said not to exist
   - nothing produced and nothing said
   - still in progress

   For anything missing, note the produced or posted record that shows it exists. List files produced but not asked for.
6. **Compare overlapping copies.** Email searches can return several renderings of one thread with different redactions, and sometimes a native `.msg` or `.eml` file with full headers.
7. **Other people's details stay private.** Productions can include other requesters' requests and contact details. Don't republish them.

If files are moved after indexing, the hash in `manifest.csv` shows each one arrived unchanged.

## 5. Follow-up drafts

Write to the project folder as `prr-followup-<custodian>-<short-subject>-<YYYY-MM-DD>.md`, headed **DRAFT ONLY. NOT SENT.**, with drafting notes at the top as in Step 5 of the skill. The user sends it.

Channel: for the parish, reply to the portal notice, which reaches the request. For the Sheriff's Office, send a new dated letter by mail or in person (`custodians/scpso.md`); its email is a courtesy copy only. For others, use the channel in their custodian file.

New records are a new request: run Steps 1 to 5. A follow-up only pursues what the original request covered.

### A. Missing or unexplained records

No questions and no argument. Each line names a record and what shows it exists.

```
[DATE]. Re: [request number], submitted [date].

Thank you for the records produced on [date]. The following items of the request appear to be missing or incomplete:

1. Item [n], [record]. [The produced record, with file and page, or the posted record] refers to it. Please produce it, or give the written basis for withholding it under La. R.S. 44:32(D).
2. Item [n], [record]. The production includes [label] redactions on [file, pages] with no legal basis cited. Please give the basis under law for each, as La. R.S. 44:32(D) requires, and release any part that is not exempt (La. R.S. 44:32(B)).
3. Item [n]. If these records are held by another person or body, please provide the certificate described in La. R.S. 44:34.

[Name]
```

### B. Narrowing, scheduling or status

Process questions are fine here. **Number every ask**, because unnumbered ones tend to go unanswered.

- Narrow within the original accounts, terms and dates, so the reply can't be treated as a new request.
- Name the event and date that matters, and the first installment wanted before it.
- Offer to narrow further, and ask for the facts that would help, such as how many messages a search returned and from which accounts.
- Ask where an unanswered part stands (text messages, a split item) as its own numbered item.

```
[DATE]. Re: [request number].

Thank you for the update. [Event] is on [date]. To help with what is most useful before then:

1. As a first installment, could you produce [narrower slice: accounts, dates, terms already in the request] before [date]? The rest can follow on your schedule.
2. Could you tell me roughly how many records the search returned, and from which [accounts or offices]? I'm glad to narrow it further.
3. Where does [unanswered part] stand?

[Name]
```

### Before handing back

- The request number and date are on the first line.
- There is one numbered line per ask.
- There is no argument, no threat of suit, and no theory of the case.
- Statutes are cited only where the reply calls for them.
- Nothing asks for records outside the original request.
- The draft is plain text that survives being pasted into a portal reply.
- No other person's details appear.

## 6. The enforcement route

This section says what the statute provides. It isn't advice on whether to sue. The skill drafts no pleadings and sends nothing.

- **Who may sue, and when** (44:35(A)): "Any person who has been denied the right to inspect, copy, reproduce, or obtain a copy" of a record, either by the custodian's determination or by five days passing with no written determination or estimate of time. The suit asks for mandamus or for injunctive or declaratory relief.
- **Where:** "the district court for the parish in which the office of the custodian is located". Most St. Charles custodians are in the parish. The listed addresses of the Port (Reserve) and both levee districts (Lutcher, Vacherie) are outside it, so check where the custodian's office actually is.
- **How the court decides** (44:35(B), (C)): it decides "de novo", and "the burden is on the custodian to sustain his action". It may view the records in camera. The suit is "tried by preference and in a summary manner".
- **Fees and penalties** (44:35(D) to (F)):
  - A requester who prevails "shall be awarded reasonable attorney fees and other costs of litigation". On partial success, an award is at the court's discretion.
  - For an arbitrary or capricious withholding, the court may award actual damages.
  - For an unreasonable or arbitrary failure to respond as 44:32 requires, it may award civil penalties "not to exceed one hundred dollars per day", excluding weekends and holidays.
  - The public body pays, not the employee, and fees are capped at the rates the attorney general approves for outside counsel.
- **Criminal penalties** (44:37) apply to a custodian who "arbitrarily or capriciously violates" the Chapter. They are a prosecution by the state, not a step the requester takes.
- **What a lawyer will want:** the log, the request as sent with proof of sending and receipt, every reply as a file, each production's `INDEX.md` with its item table, and the follow-ups. The skill can assemble a dated chronology from these.

## Not established

- How a court counts the days, and whether "the date of his … request" under 44:35(A) means mailing or receipt for a letter.
- Whether 44:34 applies to a record the custodian says never existed.
- Any time limit for filing a 44:35 suit. Not researched.
- How courts have treated long estimates of time, or redaction labels with no cited basis. Not researched. `bayou:la-court-opinions` can search for both; without bayou, say the case law wasn't checked.
