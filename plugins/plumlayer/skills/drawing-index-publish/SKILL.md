---
name: drawing-index-publish
description: "Publish the Master Drawing Index Excel workbook (.xlsx) — one tab per issue (Conformed, each Bulletin/Addendum/ASI) plus a Franken Set tab, with hyperlinks on every sheet # that open the source PDF directly to that page. ALWAYS use this skill when the user asks to publish, build, or generate the Master Drawing Index, Master Drawing Index Excel, drawing index workbook, multi-tab drawing index, or a polished/Excel/xlsx version of the drawing index. Trigger on 'master drawing index', 'publish drawing index', 'build drawing index excel', 'drawing index xlsx', 'drawing index workbook', 'tabbed drawing index', or '/publish-drawing-index'. Inputs are one or more per-issue Drawing Index CSVs (from drawing-index or drawing-index-bulletin) plus the Franken Set CSV (from drawing-index-merge). Output is a single .xlsx file with one tab per input CSV plus a Franken Set tab, frozen header rows, autofilter, sized columns, and =HYPERLINK formulas on each Sheet Number cell pointing to file:///<path>#page=<N> so a click opens Acrobat to the right page. This skill performs PURE CSV → xlsx publication; no PDFs are read. Do NOT use this skill to build the underlying indexes — those come from drawing-index, drawing-index-bulletin, and drawing-index-merge. Do NOT use this skill to assemble the actual PDFs — that is drawing-set-assemble. Use this skill IN COMBINATION with the base `xlsx` skill for Excel best practices."
---

# Drawing Index Publish — Master Drawing Index.xlsx

Read this entire file before producing the workbook.

---

## Overview

This skill takes the family of Drawing Index CSVs we've already produced and binds them into a single Excel workbook intended for everyday team use:

- **One tab per issue** (Conformed Set, Bulletin 01, Bulletin 02, …) — each shows the sheets that issue contained.
- **A "Franken Set" tab** — the latest-version index, the answer to "where is the current XYZ sheet?"
- **An "Anomalies" tab** *(if anomaly CSVs are present)* — narrative-mismatch and unlisted-sheet findings that may be RFI-worthy.
- **Hyperlinks** on every Sheet Number cell — clicking opens the source PDF in Acrobat to the right page (uses the `file:///<path>#page=<N>` open parameter).

This is the deliverable the field/sub-facing team actually wants: a one-click navigation experience grounded in the architect's set.

---

## Workflow

**Trigger:** User asks to publish / build / produce the Master Drawing Index xlsx.

**Action:**

1. Locate the inputs. Defaults:
   - Per-issue CSVs in the project's drawing-index output folder (e.g. `Drawing Index - *.csv` alongside the issue folders).
   - Franken Set CSV (e.g. in the `00-Most Recent Complete Set/` folder if the project uses that convention).
   - Anomalies CSVs (optional): `Drawing Index - Unlisted Sheets.csv` and any `* - Narrative Mismatch.csv` files.
2. Confirm chronological order of the per-issue CSVs (earliest tab leftmost; Franken Set last tab).
3. Resolve the actual on-disk paths of each PDF referenced in the CSVs so the hyperlinks point at real files. Use the same recursive-search approach as `drawing-set-assemble`.
4. Run `references/build_master_index_xlsx.py` with the inputs.
5. Tell the user the path of the output workbook and how to use the hyperlinks (one click = right page in Acrobat).

### Dependencies

- **Python 3** with `openpyxl` (`pip install openpyxl` if missing).
- Base **`xlsx` skill** (Anthropic's stock skill) for any custom formatting tweaks beyond what the script does.

### Inputs

- **Required:** one or more per-issue CSVs (positional args, chronological order).
- **Required:** the Franken Set CSV (`--franken <path>`).
- **Optional:** any number of anomaly CSVs (`--anomaly <path>` repeatable).
- **Optional:** `--out <path>` to override the output filename.

### Output

- **Default:** `Master Drawing Index.xlsx` written alongside the per-issue CSVs.
- Excel-lock handling: if a target file is open, version it `v2`, `v3`… (same as the other skills).

---

## Workbook structure

| Tab | Source CSV | Columns | Notes |
|---|---|---|---|
| `Conformed Set` | Per-issue CSV for the Conformed Set | Discipline, Sheet Number, Page Title, PDF Page, Open | "Open" is the HYPERLINK |
| `Bulletin 01` | Per-issue CSV for B01 | same | Only sheets revised in B01 |
| `Bulletin 02` | Per-issue CSV for B02 | same | Only sheets revised in B02 |
| `Franken Set` | Franken Set CSV | Discipline, Sheet Number, Page Title, Source Issue, PDF Page, Open | The latest-state index |
| `Anomalies` | Concatenation of anomaly CSVs | Source Issue, Sheet Number, Discipline, Type, Note | Skipped if no anomaly CSVs |

### Formatting (all tabs)

- Frozen pane at row 2 (header row stays visible).
- AutoFilter enabled on the data range.
- Column widths sized to content (Sheet Number ~12, Page Title 50-80, Discipline 20, PDF Page 10, Open 14).
- Header row: bold, light-gray fill.
- Discipline values get a light background per group (visual grouping; not banded — same color for same discipline).
- Franken Set tab gets a stronger tab color to mark it as the canonical view.

### The hyperlink

```
=HYPERLINK("file:///<absolute path to PDF>#page=42", "Open")
```

The `#page=N` open parameter is supported by Adobe Acrobat, Edge, Chrome, and Foxit. For the Franken Set tab, the link should point at the **new Franken Set discipline PDF** (e.g. `Drawings by Discipline/Franken Set -- Architectural.pdf`) at the page within that file. For per-issue tabs, the link points at the original source PDF at the original page.

Mapping for the Franken Set tab requires resolving each sheet # to its new page index in the appropriate discipline PDF. The script reproduces the same sort the assemble skill uses (discipline → sheet-# sort key) to compute new page indices without re-reading PDFs.

If the Franken Set discipline PDFs don't exist on disk yet (user hasn't run `drawing-set-assemble`), the script falls back to linking to the source PDF instead — and warns the user that the polished view will improve once the assembled PDFs exist.

---

## What to do after the run

1. Tell the user the path of the .xlsx and which tabs it contains.
2. Highlight that the Franken Set tab is the canonical view; the per-issue tabs are historical.
3. Mention any hyperlinks that fell back to source PDFs (because Franken Set assembled PDFs weren't found) — they should run `drawing-set-assemble` first to get the polished experience.
4. Suggest opening the file and clicking a hyperlink to verify the page-jump behavior (Acrobat is preferred over Edge for this — Edge handles `#page=N` but doesn't preserve the bookmark panel).

---

## Failure modes

- **Source PDF path unresolvable.** The CSV has a basename; the script needs an absolute path for the hyperlink. If the search roots don't find the basename, the hyperlink falls back to a literal `"<missing: NAME>"` cell so it's obvious. The user should run `--search-root <folder>` for the missing file's parent.
- **Excel file open.** The script versions the filename. Close the file and re-run for a clean overwrite.
- **Sheet # mismatch between Franken Set and assembled PDFs.** If the user edited the Franken Set CSV by hand after `drawing-set-assemble` ran, the page indices won't match. The script logs which Franken Set rows have inconsistent page numbers; re-running `drawing-set-assemble` realigns them.
- **CSV missing expected columns.** Per-issue and Franken Set CSVs have different schemas; the script accepts both and adapts column selection accordingly.
