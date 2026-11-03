---
name: scp-meeting-record
description: Build a checked record of what happened at a St. Charles Parish, Louisiana public meeting from its recording. Finds Parish Council, Planning & Zoning Commission, Zoning Board of Adjustment, Industrial Development Board and other parish board video, gets captions or a local Whisper transcript with timestamps, checks the recording against the agenda, flags garbled names against an officials roster, and checks quotes and votes against Legistar. Use for what was said at a parish meeting, who moved or voted, or whether a quote, minutes entry or "Enacted" status holds up. Also holds the roster of parish officials and appointed board members.
argument-hint: "<body and meeting date, a case or ordinance number, or a quote to check>"
allowed-tools: Bash, Read, Write, Grep, Glob, WebFetch, Skill
---

# St. Charles Parish meeting record

Turn a parish recording into a timestamped, checked record. Write it to `meeting-record-<body>-<yyyy-mm-dd>.md` in the user's project folder, with the audio and transcripts beside it. If the working directory is this plugin, ask where to write. None of it goes in the plugin.

```bash
MR="${CLAUDE_PLUGIN_ROOT}/skills/scp-meeting-record/scripts/meeting_record.py"
```

Shell state may not carry between calls, so set this in each one that uses it.

`references/officials.md` lists parish officials and appointed board members, with its generation date. To refresh it, run `python3 "$MR" roster --write <project folder>/officials.md`. Refresh before relying on a name from a meeting after that date, and use a roster from the meeting's time for an older one.

## 1. Find the recording

If you have only a case or ordinance number, get its meeting dates first with `scp-civics:scp-case-check` step 1 or the matter's Legistar history.

```bash
python3 "$MR" find --body "Planning" --date YYYY-MM-DD
```

It lists the Legistar event ID, minutes status, and each recording. As of 2026-11-03:

| Source | Holds | Use |
|---|---|---|
| YouTube, [parish channel](https://www.youtube.com/channel/UCx8V26EfjQtxPIxbLNdGEQQ/streams) | Council and budget meetings, a few committee meetings from 2021-2022 | Machine captions, fetched without a browser. Some dates have two uploads |
| [Cablecast, SCP-TV](https://reflect-stcharlesparishla.cablecast.tv/internetchannel/?channel=1) | Council, Commission, Zoning Board, IDB, Legislative Committee and other boards | Direct video files. Almost no captions, so transcribe |
| Granicus, the "Video" link on a Legistar meeting page | The same meetings, with some titles marked "(trimmed)" | Watching only. Its stream returned 403 to scripts and its caption files were empty. Don't try to get around that |

Not every body records every meeting. On a sample of recent meetings, Economic Development, the Communications District and Council on Aging had no video link. If nothing is found, say what was searched, and ask for the recording with `scp-civics:scp-prr`.

## 2. Get a transcript

**With YouTube captions:**

```bash
python3 "$MR" captions --video VIDEO_ID --dir <project folder>/transcripts
```

**Without captions,** stream the audio from the Cablecast URL, then transcribe it locally. On the 19-minute test, audio took about 20 seconds and transcription about 3 minutes on Apple Silicon. Run a long meeting in the background.

```bash
python3 "$MR" audio --url VOD_URL --out <project folder>/audio/<name>.flac
python3 "$MR" transcribe --audio <project folder>/audio/<name>.flac --dir <project folder>/transcripts
```

`transcribe` needs `uv` and `ffmpeg`. It uses `mlx-whisper` on Apple Silicon and `openai-whisper` elsewhere. The default model, `whisper-large-v3`, is a download of about 3 GB if it isn't cached, so tell the user first. Pass a smaller one with `--model` if they prefer. `transcribe` leaves VTT, SRT, JSON and a `.timed.txt` file that the later steps read.

Without these tools, give the user the replay links and work from a transcript they supply. It needs `[hh:mm:ss] text` lines for steps 3 to 6.

Both kinds of transcript are machine-made. Whisper can invent words in silence or crosstalk. When a passage matters and both sources exist, get both, and report where they differ. Timestamps differ between sources because the uploads aren't cut the same, so cite the source with each timestamp.

## 3. Check what the recording covers

```bash
python3 "$MR" coverage --event EVENT_ID --transcript <file>.timed.txt
```

Report the recording's length, its last timestamp and any agenda item it doesn't appear to reach. A case number can be misheard, so a low score means look closer, not that the item was skipped. Replays can be edited or cut, and uploads of one meeting differed by more than nine minutes in the sample checked. Say if the recording might not be the whole meeting.

A parish replay or this transcript isn't the "verbatim transcript" App. A Sec. XV.A.2 requires for the Council. Whether one reached the Council is a question for `scp-civics:scp-case-check` step 7.

## 4. Check the names

```bash
python3 "$MR" names --transcript <file>.timed.txt --known "Applicant Name" "Speaker Name"
```

Pass applicants and others named on the agenda as `--known`. The command only lists names heard after a title or "motion by", so also read the transcript for other names.

The roster check does not correct anything:
- **matches:** the spelling is on file. It may still be someone else with that surname.
- **likely garbled:** give the name on file and the heard form together, as "Keen [heard: Keene]". Say it comes from the roster, not the audio.
- **unresolved:** keep the heard form in quotes, with its timestamp, and list it for the user to check. Don't guess, even if a member's name seems close. It could be staff or a member of the public.

Name someone from the public only as far as the user needs, and only as the record names them. Don't add details about a private speaker.

Adding names to a Whisper prompt didn't improve them: on the test meeting every roster name came out the same.

## 5. Check the votes

```bash
python3 "$MR" votes --event EVENT_ID
python3 "$MR" documents --event EVENT_ID --dir <project folder>/minutes
```

`documents` reads the Legistar meeting page, which holds files the API doesn't return. It saves each one with its text layer, skipping sign-in sheets, which it only lists. Signed minutes appear there after a later meeting approves them, even while the API still says "Draft" and has no minutes file.

| Body | What exists, as of 2026-11-03 | How to report |
|---|---|---|
| Parish Council | Member votes from Legistar on many items, once the record is finished | Compare each spoken result with the API row. Report any difference, without saying which is right |
| Commission, Zoning Board, IDB and others | No member votes in the API on the meetings sampled. Signed minutes attached to the meeting page give YEAS, NAYS and ABSENT by name, as sampled for the Commission and IDB | Use the signed minutes and compare them with the recording. If none are posted, report the result "as spoken at <timestamp>". "Passes unanimously" isn't a roll call: say who the attendance shows, if known, and don't list individual votes |

An item can appear more than once, and an action with no vote row isn't a vote. A Legistar status is a label, so "Enacted" can sit on an item whose last action says otherwise. Check the history, the event item and the recording, and report any conflict.

## 6. Check each quote

```bash
python3 "$MR" quote --transcript <file>.timed.txt --text "the words as quoted"
```

For each quote you or the user will rely on, give the timestamp and the transcript's words. A close match shows the transcript has similar words, not that the speaker said them, and "not found" isn't proof they didn't. Mark every quote "machine transcript; confirm against the recording" until a person has listened. Give the user a link to the moment: for YouTube add `&t=<seconds>s`, and for Cablecast use `https://reflect-stcharlesparishla.cablecast.tv/internetchannel/show/<show>?channel=1` with the timestamp.

## 7. Write the record

Use these sections, in this order:

1. **Meeting:** body, date, Legistar event, minutes status, recording links and lengths, and how each transcript was made.
2. **Items:** one row per item of interest: agenda item, timestamp, what was said in brief, mover and second as heard, result as spoken, and the Legistar action and votes.
3. **Quotes:** each with speaker, timestamp, source and check result.
4. **Differences:** spoken result against Legistar, minutes against recording, and captions against Whisper.
5. **Established:** what a Legistar record or document states, with its citation.
6. **As heard only:** what rests on a machine transcript, with timestamps.
7. **Not established:** unresolved names, gaps in the recording, and what to check.

This is research, not legal advice. Don't write that a vote or meeting was improper. Raise it as a question.

`bayou:hearing-prep --debrief` can take the transcript and compare what was said with a prep file. Without bayou, this record stands alone. For a case's notice and procedure, use `scp-civics:scp-case-check`.
