# MDP Markdown conversion: status and handoff

Written for: the next session that describes figures and finishes table checks.

## What is here
- One `.md` per Master Drainage Plan PDF (22 files), built from MinerU 3.4.5 pipeline output.
- `images/`: figures (`<slug>-pNN-figN.jpg`) and table snapshots (`<slug>-pNN-tableN-snapshot.jpg`). Each table snapshot is MinerU's crop of the source table, for checking.
- `tools/build_md.py`: builds the Markdown from MinerU `content_list.json`. Run as `build_md.py <mineru_out> <dest>`.
- `tools/check2.py`: checks that every number in a table appears in that page's `pdftotext` output. Writes `check2-report.txt`.

## Figures (140 described, 0 remaining)
- Described (in sorted file order, except as noted): almedia-executive-summary figs 1-7, amasellers-executive-summary figs 1-9, bar-none-executive-summary figs 1-5, dianne-place-executive-summary figs 1-5, destrehan-east-executive-summary figs 1-12, destrehan-plantation-executive-summary figs 1-3, destrehan-west-executive-summary figs 1-4, hahnville-i-executive-summary figs 1-27, hahnville-ii-executive-summary figs 1-22 (complete). montz-executive-summary figs 1-4 and norco-executive-summary figs 1-4 were done out of order, because the first batch was selected from unsorted `rg` output. luling-and-luling public-meeting figs 1-27 (complete), new-sarpy figs 1-4 (complete), ormond figs 1-5 (complete), and plantation-business-center figs 1-4 (complete), st-rose-drainage-townhall-11123 figs 1-6 (complete) and st-rose figs 1-12 (complete).
- Remaining: 0 placeholder lines. 140 figures are referenced and described; 26 non-content images (logos, north arrows, scale bars, cover graphics) were extracted but their references were removed, so `images/` holds 166 `fig` files. The per-document ranges below use the original figure numbers. The turtle-pond figs 1-6 (p03-p11) show one project area built up in phases: fig 3 is Phase 1, fig 4 adds Phase 2, fig 5 adds Phase 3, and fig 6 adds Phase 4. Fig 1 is a locator inset and fig 2 is the base map. Fig 6 labels both 4-5 and 4-9 as "CN railroad south canal"; check the source before citing either. Fig 3's bottom-left call-out is cut off.
- st-rose-drainage-townhall-11123 figs 3-6 (p05, p07, p09, p11) show other areas, not St. Rose: Dianne Place, Palomino Dr / Rue Landry, Almedia, and Walker Structure / Oakland / Fairfield. Check the page text to see why these appear in this document before citing them as St. Rose projects. Fig 1 (p01) is a non-content bridge cover photo.
- st-rose-executive-summary base maps with no call-outs: figs 1, 5 and 9 (p03, p11, p19) have the same extent and labels. Figs 2 and 10 (p05, p21) are the same Phase 1 layout. Dedupe or keep all.
- st-rose-executive-summary Phase 2 and Phase 3 figures: figs 3, 7 and 11 are titled 25-year criteria with selected 100-year improvements (figs 7 and 11 are labelled ALT-1 and ALT-2). Fig 3 has no ALT label. Figs 4, 8 and 12 are the Phase 3 overlays. Check the title block before citing a specific alternative.
- Several st-rose figures are drawn rotated (vertical call-out text). Read them rotated before citing any label.
- Non-content found in the session that described luling figs 1-18 and hahnville-ii figs 21-22 (described as non-content): hahnville-ii p16 fig 21 (TBS logo). luling p01 fig 1 (compass-rose cover graphic), p02 fig 2, p12 fig 9 and p14 fig 12 (TBS logo only).
- Near-duplicates in luling: figs 4-7 (p08-p11) show the same aerial extent, labels and cyan fill, with slightly different fill patterns. Fig 17 (p20) and fig 18 (p21) share an extent. Fig 8 (p12) and fig 10 (p13) share one base map, with fig 10 adding lettered markers A-R that have no key on the figure.
- The luling cyan fills (figs 3-7, 17-18) have no legend, so they are described as "cyan fill" without a stated meaning. Check the source page text before citing their meaning.
- hahnville-ii fig 22 summary table: the 25-year and 100-year columns sum to $17,029,875 and $26,764,700, matching the printed totals.
- Also non-content (still referenced, described as non-content): hahnville-ii p10 fig 11, p13 fig 15 and p15 fig 20 (TBS logo only), and p12 fig 13 and p14 fig 18 (logo, north arrow, scale bar).
- Cropped tables in hahnville-ii figures: p10 fig 10 (group "5", $845,000 / $845,000, row label cut off), p11 fig 12 (group "6", $539,800 / $602,600, group number partly cut off), p14 fig 17 (Improvement Group 9 header only, values cut off at the image bottom). Check these against the table snapshots before citing them.
- Hahnville I figs 16, 19 and 23 are Jack and Bore maps for Improvement Groups 8, 9 and 10. Their 100-year values ($487,100, $488,100, $496,400) are cut off in the image and match the summary table on page 16. The 25-year column is not visible.
- Non-content images in this batch (still referenced, described as non-content): hahnville-i p13 figs 17-18, p14 figs 20-21, p15 figs 22, 24-25 and p16 fig 26 (logos, north arrows, scale bars). hahnville-ii p5 fig 2, p7 fig 5 and p8 fig 7 (logos and map furniture). References removed.
- Find them with `rg "^> \*\*Figure description:\*\* TODO" *.md`. Do not search `tools/` or this file, since they contain the placeholder text too.
- Replace each placeholder with a factual description: area shown, projects, pump stations, legend items, and any numbers printed on the figure.
- Non-content images found so far: amasellers p4 fig 2 and p7 fig 7 (TBS logo only). Also hahnville-i p8 fig 6, p10 fig 9, p11 fig 13 and p12 fig 15 (TBS logo only), and hahnville-i p11 figs 10-11 (scale bar and north arrow, map furniture). All are still referenced and described as non-content. References removed.
- destrehan-east base maps on p3 fig 1, p11 fig 5 and p19 fig 9 look the same (no projects shown). Dedupe or keep all three.
- destrehan-east p15 fig 7 and p23 fig 11 are both titled "Phase 2 improvements", but they show different phase sets. Check the title block before citing either.
- hahnville-i p10 fig 8 is a cropped table: only the 100-year value ($232,400) is visible, with the row label cut off. Check the source PDF before citing it.
- hahnville-i improvement-group tables on p6-p9 (IG1-IG4) cross-checked against the p02 table: all match (IG1 $615,400 / $679,600, IG2 $394,100 / $516,400, IG3 $488,700 / $503,200, IG4 $313,200 / $340,500).
- bar-none p5 fig 2 and p7 fig 4 are the same locator inset. Keep both or dedupe.
- Number discrepancy in amasellers (not fixed in source): the p09 summary table (Group 2 $416,000 / $635,000, total $7,117,500 / $13,500,400) disagrees with the p02 table and the IG-2 detail map ($424,100 / $646,500, total $7,125,600 / $13,511,900). Both tables sum correctly on their own values. The p02 table agrees with the detail map, so treat p09 as stale.
- luling figs 19-21 (p22-p24) are near-duplicates: cyan fill on the same Boutte extent, no legend. Fig 22 (p25) has lettered markers A-M with no key. Fig 23 (p26) is the titled 25-YR depth map with a legend; units are not printed.
- new-sarpy fig 1 (p03) is a locator inset, described as non-content. ormond fig 1 (p03) has a vicinity inset of the same area. Keep both or dedupe.
- new-sarpy numbering: the Cotton Canal culvert is Phase 1-6 on fig 2 (p05) and Phase 1-7 on fig 4 (p09). Phase 1-3 is used for both the 10 acre pond and New Canal #1.
- plantation-business-center fig 1 (p03) is a base map with no projects.

### Procedure for each session (20 figures)
Written for: a fresh session that describes the next batch of figures.

1. Find the next 20 placeholders: `cd "$MDP" && rg -n "^> \*\*Figure description:\*\* TODO" *-executive-summary*.md *drainage*.md *public-meeting*.md | sort -t: -k1,1 -k2,2n | head -20`. `rg` searches files in parallel, so its output is not in file order without the `sort`. Take them in that order: files sorted by name, then by line. Each placeholder names its file, page and figure.
2. Find each figure's image: the image line directly above the placeholder (`images/<doc>-pNN-figK.jpg`). Read each one with the Read tool. Send all 20 Read calls in one turn.
3. Write the descriptions to a Python script in the session's scratchpad, as a dict keyed by `(doc, page, figure)`. Follow the existing ones in the `.md` files for length and style: area shown, streets or projects, pump stations and culverts, legend items, and printed numbers with their labels. Mark logos and title blocks as non-content.
4. Replace each placeholder with `> **Figure description:** <text>`. Assert that each old string matches exactly once before writing.
5. Update the "Figures" section of this file: the count described, the remaining count, and any new non-content or duplicate findings. The remaining count goes down by 20 per session.
6. Run the `rg` from step 1 to confirm the total matches the expected remaining count.

Do not use the table snapshots for this job. Do not touch `mdp/` or `tools/`.

## Tables (130 total)
Verified by the number check: all numbers appear on the source page.

All 30 table pages that needed a visual check have been compared against the snapshots (see "Table visual check" below). Rows cut off in a snapshot were taken from the PDF text layer.

Continuation stubs: hahnville-i p03, hahnville-ii p03 and ormond p09 hold the tail of the previous page's table. Their rows are already in Table 1 / Table 4, and the stubs now say so.

Glued words: `Approximately`, `Existing`, `Add`, `Replace` and similar glued to the preceding cell text were split with `<br>` (153 table rows), and `CFS2400`, `PrioritizationLevel`, `ImprovementGroup` and 14 other glued word pairs were split. `rg "[a-z]{2,}[A-Z][a-z]+"` on table lines is the check.

Table layout: merged rows are joined into one row, with multi-line cell text separated by `<br>`. Check that this holds for each table you verify.

## Arithmetic check and layout repairs (index build)
Written for: the next session that cites or edits table values.

Every cost table was summed against its printed subtotal and total with `$SKILL/scripts/mdp_index.py check`. 105 printed sums equal their rows. Three tables hold alternative rows and cannot be summed (montz p08, norco p04, plantation-business-center p04).

Printed sums that do not equal their rows. Each was confirmed against the PDF text layer, so the inconsistency is in the parish's document and not in the conversion. The `.md` keeps the printed values and carries a `> **Note:**` under the table.
- ormond p08: Phase 3 rows sum to $3,129,200; printed subtotal $3,129,175 (already recorded above).
- ormond p11: Phase 4 rows sum to $1,059,050; printed subtotal $1,072,050 ($13,000 more).
- paradis-da-sunset p03: the three priority subtotals sum to $2,642,800; printed total $2,688,700 ($45,900 more).
- mimosa-willowdale p02: IG-1 and IG-2 sum to $6,458,000; printed Priority 1 subtotal $6,564,000. Printed total $9,764,600 matches neither the two subtotals ($9,851,000) nor the four costed rows ($9,745,000). The Willowdale Pump Station row is "TBD" with no group number.

Layout repairs (no printed value changed; a copy of the files before the repairs was taken):
- `S` for `$` in cost cells: 36 cells in 10 East Bank files.
- `$` split into its own column: 30 rows re-joined and the tables narrowed by one column (destrehan-east Phase 2 tables on p06, p14, p22; norco p08; st-rose program summary tables).
- destrehan-east p06, p14, p22: the last row read "Approximately 260 Linear Feet / 460,306.00". Restored as the scope line of 2-3 and a "Phase 2 Subtotal" row, per the PDF text layer. Name and scope lines of 2-1, 2-2.1 and 2-2.2 split with `<br>`.
- norco p08: Phase 3 rows 3-1 to 3-9 rebuilt from the PDF text layer (IDs for 3-5 to 3-9 sat on the wrong rows). The nine costs are unchanged and sum to the printed $1,581,875.
- mimosa-willowdale p02: the stacked cells paired IG-1 with Willowdale Pump Station. Rebuilt as one row per line from the table snapshot: the pump station has no group number, IG-1 is Heather Drive Culverts, IG-2 is Willowdale Drive Culverts.

`tools/check2.py` rerun after the repairs: 255 numbers absent from the text layer, against 256 in `tools/check2-report.txt`. That report predates the earlier table corrections and was not regenerated.

## Open decisions
- Non-content figures (logos, north arrows, scale bars, cover graphics): 26 image references and their descriptions were removed from the `.md` files. The image files are still in `images/`. The two locator insets (turtle-pond fig 1, new-sarpy fig 1) were kept. 
- Near-duplicate figures are kept. Similar figures are acceptable.

## Table visual check and figure QA (snapshot comparison)
Written for: the next session. Compared 30 table pages against `images/*-snapshot.jpg` (the task brief said 31; the list given sums to 30).

Verified, no change: amasellers p06; hahnville-i p07, p08, p10, p12, p13, p14, p16 (summary table); hahnville-ii p06, p09, p16 (values verified; layout fixes listed below where applicable).

Corrected:
- amasellers p09: `$` misplaced in Group 2 row (`$ | 416,000 $ | 635,000`) and `Š` in Total row; table collapsed to 3 columns. Values unchanged.
- hahnville-i p09: stray `D` in legend row and an empty row removed. p11, p15: stray `$` column merged into 3-column layout. p16: `Legend` glued to first item, split.
- hahnville-ii p08: `s 910,500` to `$`. p10: `s`/`S` to `$`; stray `X` removed from legend; `4) ... 5) ...` split. p11: `S` to `$`. p12: `25-ye ar` to `25-year`, `s 504,600` to `$`. p13: shifted columns re-aligned. p14: `s 750,900` to `$`. Legend tables on p06, p08, p10, p11, p12, p15 rebuilt as one entry per row from the snapshots (p12 and p15 were single-cell blobs; items missing from the blob, Hahnville 2 Study Area and the Improvement Groups list, added).
- ormond p08: `Approximately ...` glued onto the preceding line in rows 3-1 to 3-13 (`Pond 2Approximately`, `tolremain`); `<br>` inserted. Row 3-13 `tolremain` to `to remain`.
- st-rose-townhall p04: `CFS2400`, `WidthApproximately`, `CulvertApproximately` split with `<br>`. p06: `6` for `$` and a 3-column layout fixed. p08: `S` to `$`, `1-42"Steel` spacing, glued lines split. p10: `Co.,Inc.` to `Co., Inc.`, glued lines split. p12: `S` to `$`.

Resolved from the PDF text layer (the snapshots are cut off, the text layer is not):
- hahnville-i p02: Priority 3, 4 and Total rows match the PDF text and the p16 summary.
- hahnville-ii p02: Priority 3, 4 and Total rows match the PDF text. The p16 summary is an image with no text layer.
- ormond p08: row 3-14 is $94,000.00 and the Phase 3 subtotal $3,129,175; both sit at the top of PDF page 9. Rows 3-1 to 3-14 sum to $3,129,200, $25 over the printed subtotal (as printed).

Discrepancy, resolved in favor of p16 (hahnville-ii p02 vs p16): the p02 table is the outlier.
- p02 prints IG-7/8/9 25-year as $528,900 / $824,400 / $772,400 (the 100-year values), Priority 3 subtotal $2,665,500 and total $17,114,275.
- The detail exhibits ES-9, ES-10, ES-11 (p12, p13, p14) and the ES-13 summary (p16) all give $504,600 / $785,800 / $750,900. Those give a Priority 3 subtotal of $2,581,100 and a total of $17,029,875, which equals the sum of the ten 25-year group costs.
- The `.md` keeps p02 as printed. Cite $17,029,875 for the 25-year total.

Figure QA (14 checked): corrected st-rose-townhall figs 2, 3, 5, 6; hahnville-i p11 fig 12; hahnville-ii p10 fig 10, p13 fig 16, p14 fig 17. Confirmed unchanged: st-rose-townhall fig 4, turtle-pond p05 fig 3, st-rose-executive-summary figs 1/5/9 (identical), hahnville-i p10 fig 8.
- Observation, not changed: turtle-pond p05 fig 3 and st-rose-townhall fig 5 show the same Almedia area.
- Observation, not changed: st-rose-townhall page text on p07 reads "BAR-NONE PROGRAM - PHASE 1 IMPROVEMENTS" and on p09 "TURTLE POND PROGRAM - PHASE 1 IMPROVEMENTS" (with "25-YEAR CRITERIA WITH SELECTED 100-YEAR IMPROVEMENTS"); the table headings on p06, p08, p10, p12 read Dianne Place, Bar None, Turtle Pond, Almedia. p08 table prints "Phase 1 Projects" header over a "Phase 2 Subtotal" row (as printed).
