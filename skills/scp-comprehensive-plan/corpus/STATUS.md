# Comprehensive Plan corpus: status

As of 2026-11-02. Written for: an agent or reviewer deciding how far to trust the corpus and what to check next.

## What is here
- `scp-2030-comprehensive-plan.md`: the 2030 Comprehensive Plan (2011), 220 PDF pages.
- `scp-2030-comprehensive-plan-update.md`: the 2030 Comprehensive Plan Update (adopted November 3, 2022), 185 PDF pages.
- `images/`: 80 figure crops (`...-pNN-figN.jpg`) and 103 table snapshots (`...-pNN-tableN-snapshot.jpg`). All 183 are linked from the Markdown; none is unused; no link is broken. Size of the corpus: about 19 MB.
- Source PDFs are parish records and are not in the plugin. They were read from the local folder `$SCP_CIVICS_DATA`. The Pedestrian & Bicycle Master Plan (January 2019) is out of scope and is not indexed.

## How it was built
- **Converter:** MinerU 3.4.5, `pipeline` backend, `-m txt` (both PDFs have a text layer), `MINERU_PROCESSING_WINDOW_SIZE=4`, formulas off, on 16 GB. PDFs were split into chunks; every table page was re-run alone so that no table is merged across pages. Pages were renumbered to PDF page numbers.
- **Page headings:** one `## Page N` per PDF page: 220 and 185, matching `pdfinfo`. Printed page numbers differ from PDF pages (plan body: PDF page = printed + 10 up to the point where the PDF duplicates pages). Cite PDF pages.
- **Independent witness:** the PDFs' text layer (`pdftotext`). Surya was not run, because OCR adds nothing where a text layer exists. Pages with no text layer: plan p2 and p4, Update p2 and p185. Those pages were read from the images only.
- **Haiku 5.5 helpers** (many small sessions): proofread each of the 103 table snapshots against its Markdown (about 295 issues reported, 23 tables clean, many false alarms); rewrote 50 tables; described 46 supporting maps. Their output was applied by script only where a word-level diff against the original matched (ratio 0.85 or better, row count within 2). Four rewrites below that bar (Update p27 table 4, p156 table 25, p157 table 26; plan p203 table 42) were read by hand and kept because they restore truncated content.
- **Azure Document Intelligence** was suggested for the tables and not used. It is the obvious second opinion for the Update's action tables (see "Next checks").

## Counts
| | 2030 plan | Update |
|---|---|---|
| PDF pages / `## Page N` sections | 220 / 220 | 185 / 185 |
| Figures MinerU detected | 117 | 137 |
| Figures kept (map, diagram, locator, graphic) | 30 | 50 |
| Dropped (photos, logos, charts, ornaments) | 87 | 87 |
| Figures with a description | 30 of 30 | 50 of 50 |
| Tables (Markdown, each with a snapshot) | 43, plus 1 added by hand | 60 |
| Text-layer supplement blocks | 33 pages | 38 pages |

- "Table N:" at the start of a table caption is the build's sequence number, not the document's. The document's own label follows it (for example "Table 1: Table CON-1: ...").
- The plan's List of Tables (p8) has 13 entries. CON-1, ED-1, LU-1, LU-2, LU-3, LU-5, LU-6, PR-1, IMP-1 and IMP-2 are tables and are present. LU-4 (p67) is a bulleted call-out box, added by hand as a block. CON-2 and CON-3 (p39) are age-pyramid charts, not tables; their numbers appear only in the text-layer supplement, unordered. The Update has no List of Tables.
- Plan Table IMP-1 (action plan, PDF pp174-202) was rebuilt from the text layer, not from MinerU. The PDF repeats action-plan pages: pp185-195 duplicate the content of pp174-184. The corpus keeps both, as printed.
- Plan Table LU-6 (p84, land-use categories against zoning districts) was rebuilt from text-layer coordinates and checked against the image. The marks are: Rural Residential O-L; Low-Density R-1A, R-1AM, R-1B; Moderate-Density R-1AM, R-2, R-3, CR-1; Manufactured Home/RV R-1M; General Commercial C-2, C-3; Neighborhood Commercial CR-1, C-1, C-2 (circled); Riverfront Commercial B-1, G; Heavy Industrial M-2, M-3; Light Industrial M-1, AV-1; Riverfront Industrial B-2; Wetlands O-L, W-1; Parks and Open Space most districts. The H and MS columns carry the printed vertical text "Deletion or revision recommended".

## Checks run
- **Numbers and words against the text layer** (`scripts/check2.py` from the drainage skill, then a word comparison): 2 of 1,977 numbers and 9 of 17,419 words in the Markdown tables and text did not appear in the page's text layer. The residue was not chased.
- **Whole-document shingle check** (12-character strings from each page's text layer): flagged about 33 plan pages and 29 Update pages. Most are maps and charts, whose labels are in the images. Real losses were sidebars and call-outs (worst on Update pp93, 142, 145). Every page with 10 or more missing words got a "Text-layer supplement" block (unordered text appended to the page). Search hits in a supplement may lack context.
- **Ligatures:** the Update's text layer drops the second "f" (bufer, ofice, trafic, eforts); the plan's has spaced "fi" and "fl" (signifi cant, fi shing). 696 repairs were made with a dictionary-guarded script (log kept in the scratch area, not published). A few residuals remain, such as "fl oodprotection" and "fi shermen". Search both spellings. `<sub>` tags were stripped and the footer fragment "I M P LE M E N TAT I O N" was removed.
- **Tables:** every table was proofread by Haiku against its snapshot; 50 were rewritten; the rewrites were checked by diff and by the text layer. I compared two rewritten tables with their snapshots myself (Update p23 table 3, p35 table 7). Both matched.
- **Figure descriptions:** 34 of the 80 were written by looking at the image; 46 by Haiku. Four Haiku descriptions were spot-checked against images (plan p119 levee map, plan p145 park needs map, Update p120 West Shore Lake Pontchartrain map, Update p142 flood-depth page). All four were accurate and hedged. Each description is marked "visual reading, not stated in the plan's text".

## Future Land Use Map
- Images are at most 1400 px wide, JPEG quality 72. Plan Figure LU-5 (p72, also p18) and Update Figure LU-8 (p42, also p9) are legible at that size for area and category colors. The 14 zoom insets for communities (Update pp47-50) are readable at block scale. A single small parcel may not be resolvable at 1400 px. Ask Planning & Zoning for the digital layer.
- Both legends were transcribed by eye from the images into the figure descriptions. The Update's legend uses short names ("Residential High") where its tables say "High-Density Residential"; they are not merged.
- The 2016 interim Future Land Use Map named in Update p2 is not in the corpus.

## Not verified
- No visual sample of body pages. Only plan pp67 and 84 were compared with page images; other body pages were checked only against the text layer.
- Not every Haiku-rewritten table was re-viewed after the fix.
- Chart data is not tabulated (age pyramids, Update Figures LU-9 and LU-12).
- Some legends are not fully transcribed: the plan's zoning map (LU-4) and the Update's zoning map (LU-6) have small print cut at the edge; the plan's ED-1 legend heading is cut off; Update p86 fig 77 is cut off, p120 fig 106 is too small, p142 fig 123 has unreadable swatch labels.
- Whether the Future Land Use Map was amended after the Update: not established.
- Sub-plans the Update cites (Pedestrian and Bicycle Master Plan, Paul Maillard corridor study, Master Drainage Plan) were not read here.

## Source quirks, as printed
- Update Table LU-5 describes Low-to-Moderate Residential as "over six dwellings per acre". The plan's densities are Rural under 4, Low 4 to 8, Moderate over 8 dwellings per acre.
- The Update spells "Paul Mallard"; the street is Paul Maillard.
- The plan's map prints no community names. Community names come from the Update (pp47-50).
- The plan was adopted by the Commission on June 2, 2011 and by the Council on June 20, 2011 (plan p31). The Update says it is a "companion document" and "does not replace" the plan (p16).

## Test questions, answered from the corpus and checked against the PDF
Quotes below were found in the PDF text layer (`pdftotext`) for Update pp43, 44, 47 and 60. They are from the PDF, not copied from the corpus.

1. **Future Land Use categories and what each allows.**
   - Update (current map, Figure LU-8, p42): 12 categories. Residential, Table LU-5 p41: four. Employment, Table LU-6 p43: five. Buffers, wetlands and open space, Table LU-7 p44: three. Each row gives a description and recommended zoning districts.
   - Plan (2011, Figure LU-5 p72): 18 categories in five groups on pp73-79. Residential: Rural (under 4 du/ac), Low-Density (4-8), Moderate-Density (over 8), Manufactured Home/RV Park, Residential/Mixed Use. Employment: Heavy Industrial, Light Industrial, Riverfront Industrial, Business Park (p74). Commercial: three (p75). Activity centers: Regional, Mixed Use Corridor, Civic/Town Center (pp76-78). Recreation/Open Space p78; Wetlands p79. Plan Table LU-6 (p84) correlates categories with zoning districts.
2. **Industrial land and residential areas near industry.**
   - Plan p74, Heavy Industrial: potential to impact adjacent uses, so proper buffering is called for.
   - Update p43, Heavy Industrial: "Buffering is recommended".
   - Update p44, Industrial Buffer: separates heavy industry from residential uses.
   - Update p47, Montz: the industrial buffer discourages future residential uses near heavy industry.
   - Update p60, decision Policies 6, 7 and 9: segregate incompatible uses; incompatible detached single-family housing is not placed adjacent to existing industrial uses.
3. **One community: Norco.**
   - Map designation (Update p47, with inset): the Future Land Use paragraph describes neighborhood nodes and industrial buffers beside some industrial areas.
   - Goals and recommendations: plan pp76 and 81, Apple Street Mixed Use Corridor overlay (Action LU 1.1); Update pp52-60 (goals, actions, policies); Update p36 population by community; plan p66 Table LU-3 (Norco 3,597 to 3,074, 2000 to 2010, a 14% decline).
   - Established: the text designation and the policy wording above. Not established: any parcel-level designation. Reading a parcel from the inset is a visual reading.

## Next checks
1. Azure Document Intelligence (`bayou:document-ocr`, needs the user's approval and key) on the Update action tables (pp158-184) and plan Tables LU-6 and IMP-1, to compare against the Markdown.
2. Look at a sample of body pages in each document against the page images.
3. Obtain the digital Future Land Use layer from Planning & Zoning.
4. Check Commission and Council agendas for any map amendment after the Update.
5. Index the Pedestrian and Bicycle Master Plan if a case needs it.
