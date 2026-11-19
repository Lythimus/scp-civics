# Open Meetings Law check for one meeting

The Open Meetings Law is R.S. 42:11 et seq. The sections below were read on legis.la.gov on 2026-11-17, and the quotes come from that text. Pull current text before relying on any of it: use `bayou:la-rs-search`, or without bayou, enter the title and section at https://legis.la.gov/legis/LawSearch.aspx. Sections 42:15 (school boards' comment periods), 42:17 (executive session subjects) and 42:17.2 (remote participation) weren't pulled.

This is not legal advice. Everything `government.py notice` reports is an indicator for a question to the custodian, not a finding that the law was broken.

## What the law covers

- **A meeting** is "the convening of a quorum of a public body to deliberate or act on a matter over which the public body has supervision, control, jurisdiction, or advisory power". It also covers a quorum convened to receive information on such a matter (42:13(A)(2)). Chance meetings and social gatherings with no vote or polling are excluded (42:13(B)).
- **Public bodies** include parish governing authorities, school boards, levee and port boards, planning and zoning commissions, and "any committee or subcommittee" of them (42:13(A)(3)). Council committees and the Commission are covered.
- **A quorum** is "a simple majority of the total membership" (42:13(A)(4)).

## Checklist

| Rule | What it says | How to check | `notice` |
|---|---|---|---|
| Annual notice | Regular meetings set by law, resolution or ordinance get written notice of "dates, times, and places" at the beginning of each year (42:19(A)(1)(a)) | For the Council, the "Adopt <year> Parish Council Meeting Schedule" special matter. For a board, ask | Council only |
| 24-hour notice | Written notice of any regular, special or rescheduled meeting "no later than twenty-four hours, exclusive of Saturdays, Sundays, and legal holidays, before the meeting", including "the agenda, date, time, and place" (42:19(A)(1)(b)(i)-(ii)) | The notice must be posted at the body's principal office or published in its official journal. If the body has a website, it must also be posted there, but late or failed website posting "shall not be a violation" (42:19(A)(2)(a)). Anyone who asks must be given notice the same way members get it (42:19(A)(2)(b)) | Compares Legistar's last agenda publish time with the computed deadline |
| No late changes | "The agenda shall not be changed less than twenty-four hours, exclusive of Saturdays, Sundays, and legal holidays, prior to the scheduled time" (42:19(A)(1)(b)(ii)(aa)) | Ask for each version of the agenda and when each was posted. Legistar's timestamp is the *last* publication, so a late one may be a change or a republish of the same text | Same comparison |
| Items described | Each item "listed separately and described with reasonable specificity", and read aloud before action (42:19(A)(1)(b)(ii)(bb)) | Read the agenda against the minutes and the recording | No |
| Items added at the meeting | Only by unanimous vote of members present, identified in the motion with its purpose and entered in the minutes, after public comment on the motion. Not "as a subterfuge" (42:19(A)(1)(b)(ii)(cc)) | Minutes and recording | No |
| Litigation | The notice must identify the court, case number and parties for pending litigation to be considered, and the parties and subject for prospective litigation after a written demand (42:19(A)(1)(b)(iii)) | Read the notice | No |
| Broadcast info on the notice | A body that must broadcast live must say on the notice where to watch (42:19(A)(1)(c)) | Read the notice | No |
| Public comment | Bodies other than school boards "shall allow a public comment period at any point in the meeting prior to action on an agenda item upon which a vote is to be taken", under reasonable rules (42:14(D)) | Minutes ("Public comment opened") and the recording | Counts comment openings in the minutes against decided items |
| Votes | No proxy or secret ballot (42:14(B)). Votes are viva voce and recorded; electronic voting displayed and recorded counts (42:14(C)) | Minutes | No |
| Executive session | Needs two-thirds of members present, voting at an open meeting. Each member's vote and the reason are recorded. No final action inside. Limited to the subjects in 42:17 (42:16) | Minutes | Flags any mention |
| Minutes | Kept for every open meeting, with the date, time, place, members present and absent, "the substance of all matters decided", and individual votes if a member asks (42:20(A)). Available "within a reasonable time". Adopted minutes go on the website: within ten days of journal publication if the body must publish them, and kept there at least three months (42:20(B)) | Legistar minutes status and date | Status and last-published time |
| Live broadcast | A parish governing authority in a parish of 25,000 or more "shall broadcast live all of its proceedings in public meetings, including the parish governing authority's committee meetings" (42:23(B)(2)(a)(i)). A nonelected board that can levy a tax must record or broadcast (42:23(B)(1)). Anyone may record a public meeting (42:23(A)) | `scp-civics:scp-meeting-record` `find <body> <date>` | Says whether the rule reaches the body |

Sec. 2-16.3 of the parish code adds that all boards and commissions meet at the courthouse and are televised. It is a parish rule, not the state law.

## How the deadline is computed

- `notice` counts back 24 hours from the meeting's start, skipping Saturdays, Sundays and the legal holidays in R.S. 1:55(A)(1).
- That list includes days when offices stay open: January 8 (Battle of New Orleans), August 30 (Huey P. Long Day), Columbus Day and All Saints' Day. Counting them gives an earlier deadline.
- R.S. 1:55(A)(3) lets St. Charles make Mardi Gras a holiday by ordinance, and (A)(4) lets it do the same for the Friday before a Saturday Christmas, New Year's Day or July 4. Whether the parish has done either isn't established, so `notice` shows the deadline both ways when one of those days falls in the window. Add any other holiday with `--holiday YYYY-MM-DD`.
- A courthouse holiday on the Legistar chamber calendar that isn't on the statute's list is printed as a hint.
- Legistar labels its publish times UTC. The label is consistent with the data: read as UTC, the 2025-26 agenda publish times fall between 6 AM and 3 PM Central, and read as local time they would run past 8 PM. It hasn't been checked against a posted notice.

## Enforcement

- An action taken in violation is "voidable", and a suit to void it "must be commenced within sixty days of the action" (42:24).
- The Attorney General and each district attorney enforce the law. Each "shall institute such proceedings upon a complaint filed with him by any person, unless written reasons are given as to why the suit should not be filed" (42:25(A)-(B)). In St. Charles that is the 29th Judicial District's District Attorney. The Charter makes the DA the parish's legal advisor until the Council creates a legal department (III.C.3), and the code has a Department of Legal Services (Sec. 2-21). Whether the DA still advises the parish on anything isn't established, so ask before relying on a DA complaint.
- Any person denied a right under the law, or with reason to believe it was violated, may sue (42:25(C)). Remedies are mandamus, injunction, declaratory judgment, voiding the action and civil penalties. A plaintiff who prevails "shall be awarded reasonable attorney fees" (42:26).
- A member who "knowingly and wilfully" takes part in a violating meeting faces a civil penalty of up to $500 per violation, personally, with suit within sixty days (42:28).
- The 60-day windows run from the action, so a check is worth doing within days of a meeting, not months.

## Getting the proof

The posted notice and its posting time aren't on Legistar. Ask for them by records request through `scp-civics:scp-prr`:

- the notice as posted, with the date and time of posting
- each version of the agenda, with when each was posted
- any request-for-notice list
- the minutes
- the recording

Ask the custodian the questions `notice` raises in writing, and keep the reply.
