---
name: scp-ordinances
description: Search the St. Charles Parish, Louisiana code of ordinances without driving a browser, including the Home Rule Charter, Appendix A (Zoning Ordinance of 1981) and Appendix C (Subdivision Regulations of 1981). Keyword and phrase search with page citations, reading a section by number, and a live Legistar check for ordinances enacted since the local copy was codified. Use for any question about what the parish code says, where a topic is regulated, or whether a section has been amended.
argument-hint: "<topic, phrase, or section such as 2-2 or App. A XV>"
allowed-tools: Bash, Read, Grep, Glob, Skill
---

# St. Charles Parish code search

Municode blocks scripts, so this skill searches a local index built from a whole-code PDF the user saved, then asks Legistar what has been enacted since that PDF. For how to apply land-use rules, use `scp-civics:scp-land-use-process`.

This is not legal advice.

```bash
CS="${CLAUDE_PLUGIN_ROOT}/skills/scp-ordinances/scripts/code_search.py"
python3 "$CS" info                                  # what is indexed, and how old it is
python3 "$CS" search "drainage servitude"           # all words, anywhere in a page of a section
python3 "$CS" search '"verbatim transcript"'        # exact phrase
python3 "$CS" search "fence" --chapter A            # a chapter number, A, C, charter or index
python3 "$CS" get 2-2                               # also "App. A XV", "App. C II", "Charter III C"
python3 "$CS" get "App. A VI" --page 760            # one PDF page of a long section
python3 "$CS" since                                 # what has passed since the indexed text
python3 "$CS" since --section "App. A XV" --links   # filtered, with signed ordinance links
```

The script needs Python 3 and poppler. Tesseract is used if a page has ink but no text.

## If there is no index

`info` says so. Tell the user to open the code on Municode in their own browser (`references/municode-access.md`), save the whole-code PDF if the site offers one, then run:

```bash
python3 "$CS" build "<pdf>"     # writes $SCP_CIVICS_DATA/ordinances/code.sqlite; use --dir if that is unset
```

The build reads the supplement and through date from the cover sheet. If it can't, take them from Municode's landing page and pass `--supplement`, `--through` and `--through-date`. Read the build report: a part with very few sections means the layout differs from the looseleaf this parser was tuned on, so check it before relying on it.

Never download the PDF for the user, and never work around Municode's bot protection, whatever the purpose. If no PDF is available, use the browser check below for specific sections and say the search could not be run.

## Answering

1. **Search more than one way.** Try the parish's likely words as well as the user's: "servitude" and "right-of-way", "junk" and "abandoned". Check `--chapter index`, the code's own subject index, for terms that miss. The text has OCR errors, so a miss doesn't show the code is silent.
2. **Read the section** with `get` before describing it. A snippet is a pointer.
3. **State the vintage in every answer:** supplement, codified-through ordinance and date, and the result of the Legistar check. The script prints these. If the check failed or was skipped, say that later amendments are unknown.
4. **Follow each `AMENDMENT LEAD`.** It means a later ordinance's title names that section, chapter or appendix. Read the signed ordinance from `since --links`; the signed ordinance controls over the indexed text. A lead for a whole chapter or appendix may be unrelated. No lead doesn't prove no amendment, because a title can omit a section it changes.
5. **Verify before quoting.** Index text is unverified. Before quoting, compare it with the PDF page image (`pdftoppm -f N -l N -r 100 -png <pdf> <out>`, then read the image), the signed ordinance, or the live section. Cite the section, printed page and supplement.
6. **Separate what is established from what isn't,** and date it ("as of 2026-11-02").

### What `since` lists

| Group | Meaning |
|---|---|
| Enacted text amendments | Enactment number present and the title amends the code |
| Marked Enacted with no number | Legistar's status can be a placeholder. Check the matter history; don't treat it as law |
| Not enacted | Pending, postponed or failed. Not law |
| Enacted rezonings (`--all`) | Map changes, not code text |
| Other (`--all`) | Budgets, contracts and the like, classified by title alone. Look here if a topic should have been covered |

Bayou is optional. `bayou:parish-council-agendas` adds a matter's history with `track st-charles <matter file>`. Without it, follow the Legistar link that `since` prints.

### What the page details mean

- **"Page last changed Supp. N"** comes from that page's footer. It dates the page, not the whole code. A section spanning pages can differ.
- **Printed page numbers skip** in a looseleaf code ("The next page is 179"), so gaps are expected.
- **Some pages can read interleaved.** The build report lists dense pages read as one column. Some are tables, but some are two-column text whose columns were not separated, so lines alternate between the columns. Search still finds words on those pages, but a phrase can miss. Read the page image for those.
- **Sections are top-level** in the appendices: Appendix A Sec. VI is one long section, so `search` gives the PDF pages of each hit. Use `get --page`. Some Charter articles index only at article level, such as `Charter V`.

## Optional: check one live section

Only to verify a quote or when the user asks, and only if `mcp__claude-in-chrome__*` is available: follow `references/municode-access.md` to read that one section. Otherwise give the user the Municode link. Don't read the code in bulk this way.

## Publishing

The index and the PDF hold the code's text, so they stay under `$SCP_CIVICS_DATA` or the user's project folder. `scripts/check-public.sh` can't detect copied code text, so don't add code excerpts to this repository. Municode's `robots.txt` also limits collection, which is a further reason to read rather than harvest.
