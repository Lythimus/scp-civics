# Adding a plan document to the corpus

Use this when a new Master Drainage Plan PDF appears (a missing volume, a detailed report, a new
public-meeting deck). The procedure and its lessons come from the conversion recorded in
`$MDP/STATUS.md`. Read that file first.

This mode writes into `corpus/`, so run it in a clone of the repository, not an installed copy. Say what will be added and get a yes before writing. Never delete or
overwrite an existing `.md` or image; if a file must be replaced, move the old one to the Trash.

## When to use something else

For a scanned permit application headed to `bayou:permit-analysis`, use `bayou:document-ocr`,
`bayou:ocr-validate` and `bayou:ocr-verify`. Those produce `.txt` plus per-line evidence. This
procedure is for engineering reports where tables and map exhibits must survive as Markdown.

## Requirements

- **MinerU** (the conversion used 3.4.5, pipeline backend). Check with `mineru --version`. It is
  not known to be installed. Installing it downloads layout, OCR and table models from
  HuggingFace. The download is large (gigabytes; look up the current figure, do not guess it).
  State the size and ask before installing or running it for the first time.
- On a network that inspects TLS, HuggingFace downloads fail certificate checks unless
  `SSL_CERT_FILE` and `REQUESTS_CA_BUNDLE` point at a CA bundle that includes the inspecting CA.
- `pdftotext` and `pdftoppm` (poppler).

## Steps

1. **Place the PDF** in `$SCP_CIVICS_DATA/`. Skip duplicates (a `(1)` copy of Bar
   None is already there).
2. **Layout parse.** Run MinerU on the PDF into a scratch directory. It writes `content_list.json`
   plus figure and table crops.
3. **Build.** `python3 $SKILL/scripts/build_md.py <mineru_out> <dest>` into a scratch `<dest>`, not
   straight into `corpus/`. It writes one `.md` with `## Page N` sections, `**Table N**` blocks, a
   snapshot link under every table, and a `> **Figure description:** TODO` under every figure.
4. **Number check.** `python3 $SKILL/scripts/check2.py <dest> <pdf-dir>` reports table numbers and
   words absent from that page's text layer. A table whose numbers are missing from the text
   layer is an image table read by OCR and needs a visual check. A report over 200 lines can be
   summarized with `ask-local`; the visual checks cannot.
5. **Table visual check.** For each flagged table, Read the snapshot and compare it with the
   Markdown. Fix `$` read as `S`, `s` or `6`, stray `D`, `X` or `Š`, shifted or collapsed columns,
   legend tables collapsed into one cell, and words glued across wrapped cells
   (`PipeApproximately`, `CFS2400`). Scan table lines with `rg "[a-z]{2,}[A-Z][a-z]+"` afterwards.
6. **Figure descriptions**, in batches of 20. List placeholders with
   `rg -n "^> \*\*Figure description:\*\* TODO" <dest>/*.md | sort -t: -k1,1 -k2,2n` (sort, because
   `rg` output order is not file order). Read the 20 images in one turn. Write descriptions in a
   Python dict keyed by (doc, page, figure), assert each placeholder matches exactly once, then
   replace. This step needs vision, so it does not go to the local model.
7. **Arithmetic check.** `python3 $SKILL/scripts/mdp_index.py check --mdp <dest>`. Then compare the
   summary table with each detail exhibit by hand.
8. **Move the result into `corpus/`** after the user confirms: the `.md` and its `images/` files.
   Rebuild the index with `mdp_index.py build`.
9. **Record it.** Add the document to `references/watersheds.md`, add anything unresolved to
   `references/known-discrepancies.md`, and append what was verified, corrected and left open to
   `corpus/STATUS.md`.

## Rules learned the hard way

- **Text layer first, vision second.** Before calling a value illegible, run
  `pdftotext -layout -f N -l N <pdf> -`. Use `pdftoppm -r 110 -f N -l N` and a visual read only for
  pages with no text layer.
- **Snapshots can be cut off.** MinerU's table crop sometimes ends mid-table. Check the text layer
  and the next page before marking rows missing. Tables continue across pages, and the tail shows
  up as an empty "table body not recovered" stub that is a continuation, not a lost table.
- **Arithmetic is the cheapest validator.** Sum rows against printed subtotals and totals. It
  caught two source errors in the first conversion and more when the index was built.
- **When two printed tables disagree, find a third source** (a detail exhibit, the subtotal
  arithmetic) before choosing. Keep the source value as printed, add a `> **Note:**` line under
  the table, and record it. The index reads those notes and flags the rows.
- **Figures:** describe only what is printed: area, streets, canals, structures, legend items,
  printed numbers with their labels. Drop logos, north arrows, scale bars and cover art. Keep
  locator insets and near-duplicates. Flag cropped tables, rotated call-outs, unlabeled fills and
  legends with no key; do not guess their meaning.
- **Provenance:** keep the snapshot link under every table.
