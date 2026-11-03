# Reaching the code on Municode

As of 2026-11-02, the online code was Supplement 77, updated 10/15/2026, codified through Ord. 26-6-3 (6/1/2026). The landing page shows the current figures and an "Adopted Ordinances Not Yet Codified" list.

- Landing page: https://library.municode.com/la/st._charles_parish/codes/code_of_ordinances
- One section: add `?nodeId=<id>` to that URL

Cloudflare answers scripts with 403, so `curl` and `WebFetch` don't work. `robots.txt` disallows ClaudeBot and sets `ai-train=no` and `use=reference`. Don't try to get past either one: no TLS impersonation or similar tools, no replaying the site's credentials against its API, and no crawling.

## Getting the PDF

The user does this in their own browser and saves the file under `$SCP_CIVICS_DATA`. Whether a whole-code PDF of the current supplement is offered is not established. The copy this skill was tuned on is a looseleaf compilation of Supplement 75. If only sections can be downloaded, the existing index plus `code_search.py since` covers the gap, and the parish sells the code on paper (`scp-civics:scp-prr`, `references/fees.md`).

## Reading one section in the browser

For verifying a quote, or when the user asks. In the claude-in-chrome browser:

1. Open the section URL and wait for it to load.
2. Read `document.body.innerText` with `javascript_tool`. Each result is cut at about 1,000 characters, so store the text in a `window` variable and read slices in a `browser_batch`.
3. Note the version date shown beside the code, and any "amended" or "modified" badge.

A page holds its whole parent, so one zoning section's page holds all of Appendix A (about 450K characters). Find the section by searching the stored text. Don't POST the text to a localhost receiver: Chrome's local-network prompt hangs the tab.

## Node IDs

Read 2026-11-01.

| nodeId | Holds |
|---|---|
| `PTIIPACO_APXASTCHPAZOOR1981_SXVAMPR` | Appendix A (Zoning Ordinance of 1981), Sec. XV: Amendment procedure |
| `PTIIPACO_APXCSTCHPASURE1981` | Appendix C (Subdivision Regulations of 1981), the whole appendix on one page (~172K chars) |
| `PTISTCHPA` | Home Rule Charter |
| `SUHITA` | Supplement History Table |

Other IDs appear in the page's table of contents.
