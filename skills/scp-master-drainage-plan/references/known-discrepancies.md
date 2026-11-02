# Known discrepancies in the plan documents

Check this file before citing any number from the listed pages. "As printed" means the Markdown
keeps the source value and the source itself is inconsistent. The conversion ledger with the full
history is `corpus/STATUS.md`.

When citing a discrepant value in a public document, give the printed value, say what it
disagrees with, and say which figure the plan's own detail supports. An inconsistent cost table
in a parish planning document can be a finding in its own right.

## Numbers that disagree between tables

| Document | Where | What disagrees | Cite |
|---|---|---|---|
| hahnville-ii | p02 Table 1 vs exhibits ES-9, ES-10, ES-11 (p12-p14) and the ES-13 summary (p16) | p02 prints the 100-year values in the 25-year column for IG-7, IG-8, IG-9 ($528,900 / $824,400 / $772,400), giving a Priority 3 subtotal of $2,665,500 and a 25-year total of $17,114,275. The exhibits and the p16 summary give $504,600 / $785,800 / $750,900. | 25-year: IG-7 $504,600, IG-8 $785,800, IG-9 $750,900, Priority 3 subtotal $2,581,100, total **$17,029,875** (equals the sum of the ten group costs). 100-year total $26,764,700 is consistent everywhere. |
| amasellers | p09 summary table vs p02 Table 1 and the IG-2 detail map | p09 prints Group 2 as $416,000 / $635,000 and totals $7,117,500 / $13,500,400. p02 and the detail map give $424,100 / $646,500 and totals $7,125,600 / $13,511,900. Each table sums correctly on its own values. | The p02 values. Treat p09 as stale. |

## Printed subtotals that do not equal their rows

`mdp_index.py check` reports these on every run. All were confirmed against the PDF text layer,
so they are in the source, not the conversion.

| Document | Where | Printed | Rows sum to | Difference |
|---|---|---|---|---|
| ormond | p08 Table 4, Phase 3 Subtotal (rows 3-1 to 3-14; 3-14 and the subtotal sit at the top of PDF p09) | $3,129,175 | $3,129,200 | +$25 |
| ormond | p11 Table 6, Phase 4 Subtotal (rows 4-1 to 4-5) | $1,072,050 | $1,059,050 | -$13,000 |
| paradis-da-sunset | p03 Table 1, Total Cost for Improvements | $2,688,700 | $2,642,800 (the three priority subtotals, each of which matches its own rows) | -$45,900 |
| mimosa-willowdale | p02 Table 1, Priority 1 Projects Subtotal | $6,564,000 | $6,458,000 (IG-1 $5,471,800 + IG-2 $986,200) | -$106,000 |
| mimosa-willowdale | p02 Table 1, Total Cost for Improvements | $9,764,600 | $9,851,000 (the two printed subtotals) or $9,745,000 (the four costed rows) | matches neither |

Mimosa Willowdale lists a "Willowdale Pump Station" at "TBD" with no improvement-group number,
above IG-1 (Heather Drive Culverts). The unexplained differences may relate to it; the summary
does not say.

Each of these carries a `> **Note:**` line under its table in the Markdown.

## Tables that cannot be summed

| Document | Where | Why |
|---|---|---|
| montz | p08 Table 4 (Phase 3) | Three rows share ID 3-1; two are marked as alternatives. The printed subtotal $21,664,704 includes the $19,200,000 Alternative 3 pump station. |
| norco | p04 Table 2 (Phase 1) | Two rows for 1-1: Alternative 1 ($3,650,000 pump station upgrade) and Alternative 2 ($14,980,000 additional pump station). State which alternative a total assumes. |
| plantation-business-center | p04 Table 3 (Phase 1) | Row 1-1 has an "(Alternate 1)" version ($3,000,000 box culverts in place of $2,800,000 jack-and-bore). Both subtotals are printed: $3,342,625 and $3,542,625 (Alternate 1). |
| destrehan-east, st-rose | throughout | The phase tables repeat for each alternative. The same ID has different scope and cost in different alternatives (destrehan-east 1-1 is $2,160,000 in the base program and $3,600,000 in a later one). Cite the page. |

## Conversion artifacts still in the Markdown

- hahnville-i p03, hahnville-ii p03 and ormond p09 hold "Table" stubs that are the tails of the
  previous page's table. Their rows are already in the earlier table.
- Words glued across wrapped cells remain in places (`PumpStation`, `WayDrive`, `andIII`). They do
  not affect values. Search with a fragment if a full name gets no hit.

## Labels and numbering to check before citing

- **new-sarpy:** the Cotton Canal culvert is Phase 1-6 on fig 2 (p05) and Phase 1-7 on fig 4 (p09).
  ID 1-3 is used for both the 10-acre pond and the Canal #1 addition.
- **turtle-pond:** fig 6 labels both 4-5 and 4-9 "CN railroad south canal." Fig 3's bottom-left
  call-out is cut off.
- **st-rose:** figs 3, 7 and 11 are all titled 25-year criteria with selected 100-year
  improvements. Figs 7 and 11 are labelled ALT-1 and ALT-2; fig 3 has no ALT label. Several
  figures are drawn rotated.
- **destrehan-east:** p15 fig 7 and p23 fig 11 are both titled "Phase 2 improvements" but show
  different phase sets.
- **st-rose-drainage-townhall:** figs 3-6 show Dianne Place, Palomino Dr / Rue Landry, Almedia and
  Walker Structure / Oakland / Fairfield, not St. Rose. Page headings on p07 and p09 read "Bar-None
  Program" and "Turtle Pond Program," while the table headings on p06, p08, p10, p12 read Dianne
  Place, Bar None, Turtle Pond, Almedia. The p08 table prints a "Phase 1 Projects" header over a
  "Phase 2 Subtotal" row. On p13 the grant table's first row holds two amounts and two statuses in
  one cell ($825,000 awarded and $7.6M requested, State Capital Outlay).
- **hahnville-i:** figs 16, 19 and 23 (Jack and Bore maps for IG 8, 9, 10) show only the 100-year
  value. p10 fig 8 is a cropped table.
- **hahnville-ii:** figures p10 fig 10, p11 fig 12 and p14 fig 17 contain cropped tables. Take
  values from the `.md` tables.
- **luling deck:** cyan fills on figs 3-7 and 17-21 have no legend; lettered markers on figs 10 and
  22 have no key. Fig 23 is a 25-year depth map with no units printed. Do not state what a fill
  means without the page text.
- **hahnville-i and mimosa-willowdale** both print a focus area of "approximately 2,509 acres."
  Unverified whether one is carried over from the other; do not cite either acreage without
  the detailed report.
