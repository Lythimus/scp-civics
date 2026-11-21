# Status of the converted Local Coastal Program

As of 2026-11-20.

## Source

- **Document:** *St. Charles Parish Local Coastal Program Document* (St. Charles Parish with the South Central Planning and Development Commission, 2016). The state publishes it at data.dnr.la.gov/lcp/StCharlesCZM.pdf.
- **Size:** 285 PDF pages. The PDF itself is not published here.
- **Conversion:** MinerU 3.4.5 (pipeline backend, text-layer mode), run in 25-page chunks and merged.
- **Page headings:** `## Page N` is the PDF page. "(printed X)" follows when the page carries a printed number. PDF page 276 (printed B-28) holds only its header and page number.

## What was checked

- **Numbers and words in tables** were compared against the PDF text layer with the drainage skill's `check2.py`:
  - 377 numbers and 958 words were checked.
  - Every value that check2 reports as missing is on PDF page 91. That table is an image with no text layer, so check2 cannot confirm any of it. It was transcribed by hand from the page image (see below).
- **Prose** was not compared word for word. MinerU took prose from the PDF text layer, so its errors are mostly in reading order and hyphenation, not in wording.

## What was corrected

- **Table 1-2** (PDF p. 37): MinerU read this table from the image and ran wrapped words together ("SalinityRange", "Soiis"). Rebuilt from the text layer.
- **Tables 1-6 to 1-11** (PDF pp. 54-57), the plant lists:
  - MinerU joined each scientific name to its common name.
  - It also merged Table 1-7 into Table 1-6, which left Table 1-7 empty.
  - All six were rebuilt from the text layer's word positions, as *Scientific name* (Common name).
  - Spellings are kept as printed, including source errors such as "Froxinus", "Percea" and "Salidago".
- **Table 3-2** (PDF p. 91): MinerU's version shifted the income values by one row. Transcribed again from the page image. "Labor Forced" is as printed.
- **Table 2-1** (PDF p. 76): the 2009 shrimp trawl licence count was misread as 183. The PDF says 83.
- **Single headers** on PDF pp. 38, 73 and 76: run-together words separated ("% Land Area", "Federal Status", "Commercial Fishermen").

## Figure descriptions

- **The cover (PDF p. 1):** its 10 image fragments are marked as cover art and not described.
- **First pass:** Claude Haiku described the other 106 figures from the images. Each agent got the figure's caption and surrounding text, and was told to describe only what it could see.
- **Second pass:** Claude Sonnet checked every first-pass description against its image, in two rounds.
  - Chapter 6 (PDF pp. 127-201), the EMU maps a site is placed from: 51 checked, 43 corrected.
  - Everything else: 52 checked, 36 corrected. These were the other maps, charts, photographs and signature blocks. Chart fixes were mostly bar lengths read against gridlines; photograph fixes removed things not visible.
  - The fixes were almost all about where things lie, which colour matches which legend entry, or claims about things not visible. A few were misread labels, such as "BMU" for "EMU".
  - Legend entries and printed labels from the first pass were usually right.
- **Checked by hand:** 6 descriptions were compared with their images: p. 43, 49, 77, 127, 168 and 178. The first-pass versions of three of them (pp. 43, 49 and 168) had placement errors, which were corrected.
- **Every description is labelled:**
  - "machine-generated, checked against the image": the 6 checked by hand;
  - "machine-generated, checked by a second model against the image": the other 100.
- **"Not readable or uncertain" lines** under a description give what the model could not read. Many maps have soil or land-use colours too close together to match to the legend.
- **Signature blocks** (Appendix B) say "Handwritten signature; not transcribed", plus the printed text around them.
- **A source labelling error:** Figure 6-1 (PDF p. 127) is titled "West Bank Community" on the map, but it shows all fourteen units.

## Open

- The 100 second-pass descriptions were checked by a model, not a person. Three of them (pp. 27, 48 and 96) were compared with their images afterwards. Placements were right; one partly covered number on p. 48 had been read with false confidence and is now marked uncertain. Before relying on a placement, look at the image.
- Prose outside the tables was not proofread against the PDF.
- Appendix B is the 2015 ordinance as adopted. It is not current law; read Chapter 26 from the code.

## Redaction

Chapter 8 (PDF pp. 231-233) names four people who commented on the 2015 draft. Here their names are replaced with "Commenter 1" to "Commenter 4". The source document prints them, and the stated affiliations (LSU AgCenter, Dow Chemical Company) are kept. Nothing else in the text was redacted.
