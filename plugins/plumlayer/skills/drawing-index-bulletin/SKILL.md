---
name: drawing-index-bulletin
description: "Build a per-issue Drawing Index CSV for a construction Bulletin, ASI, or Addendum that ships as a SINGLE combined PDF (not split by discipline). ALWAYS use this skill when the user asks to index, list, or catalog a Bulletin, ASI, Addendum, or any partial-issue drawing release where every revised sheet across all disciplines is bound into one combined PDF. Trigger on 'index this bulletin', 'list the sheets in bulletin XX', 'what changed in bulletin XX', 'bulletin index', 'addendum index', 'ASI sheet list', or '/drawing-index-bulletin'. Output is a .csv (Discipline, Sheet Number, Page Title, PDF File, Page in PDF) for the revised sheets, plus a companion .csv flagging any discrepancy between the architect's Narrative of Changes and the actual pages in the Bulletin PDF (RFI-worthy). This skill cross-checks the architect's Narrative of Changes letter against title-block scans of each page — narrative-only sheets and PDF-only sheets are both flagged. Use this skill IN COMBINATION with the base `pdf` skill if the user wants to spot-check specific title blocks. Do NOT use this skill on the Conformed Set, Permit Set, or any full discipline-split issue — that is the drawing-index skill. Do NOT use this skill to merge multiple issues into a current-state set — that is the drawing-index-merge skill."
---

# Drawing Index (Bulletin) Builder — Full Instructions

Read this entire file before producing any Bulletin-index output.

---

## Overview

This skill indexes a **partial drawing issue** (Bulletin, ASI, Addendum) where the architect bundles every revised sheet across all disciplines into one combined PDF. Output schema matches the `drawing-index` skill's per-issue CSV exactly — so the downstream `drawing-index-merge` skill can ingest both without distinguishing them:

| Discipline | Sheet Number | Page Title | PDF File | Page in PDF |
|---|---|---|---|---|

Two outputs are written next to the input folder:

1. **`Drawing Index - <issue>.csv`** — one row per page in the combined Bulletin PDF.
2. **`Drawing Index - <issue> - Narrative Mismatch.csv`** — present only when the architect's Narrative of Changes and the title-block scan disagree on which sheets were revised. **Always RFI-worthy.**

---

## Workflow

**Trigger:** User asks to index a Bulletin, ASI, or Addendum. Typical folder layout:

```
<project>/Drawings/<YYYY-MM-DD Bulletin XX>/
    <combined drawings PDF>
    <Narrative of Changes PDF>
    Transmittal - NNNNN.pdf
    [optional: per-discipline narratives]
```

**Action:**

1. Locate the input folder. If unspecified, ask.
2. Identify the combined drawings PDF (largest .pdf in the folder whose filename mentions "Drawings" or similar; fall back to the largest PDF that isn't the narrative/transmittal).
3. Identify the Narrative of Changes PDF (filename contains "Narrative" or "Changes" or "summary of changes").
4. Run `references/build_bulletin_index.py <folder>` — it writes both CSVs.
5. Report to the user:
   - Total sheets in the combined PDF.
   - Per-discipline counts.
   - Any narrative mismatch as a callout (these are usually RFIs).
   - New sheet numbers introduced by this issue (sheet # patterns not seen on prior issues — only known if the prior CSV is also on disk; the script logs candidates).

### Dependencies

- **Python 3** with `pdfplumber` (`pip install pdfplumber` if missing).
- **`pdftotext`** (poppler-utils) for fast page-by-page title-block scans.
- The base **`pdf` skill** for any manual verification.

---

## How the parser works

### 1. Discipline inference from sheet number prefix

A Bulletin has no G-001 master list, so we infer the discipline from the sheet number prefix:

| Prefix | Discipline |
|---|---|
| `G-` | GENERAL |
| `LS-` | LIFE SAFETY |
| `C-` | CIVIL |
| `D-` | ARCHITECTURAL DEMO |
| `A-` | ARCHITECTURAL |
| `S-`, `SKS-` | STRUCTURAL (SKS = structural sketch) |
| `FP-`, `FPD-` | FIRE PROTECTION |
| `P-`, `PD-` | PLUMBING |
| `H-`, `HD-` | HVAC |
| `E-` | ELECTRICAL |
| `FA-` | FIRE ALARM |
| `ES-` | SECURITY |
| `T-` | TELECOMMUNICATIONS |
| `VT` | ELEVATOR |

If a new prefix appears (e.g. an architect introduces a `K-` for kitchen), the script flags it; update the table.

### 2. Page-by-page title-block scan

`pdftotext -layout` ⇒ split on form-feed ⇒ for each page, find the sheet number in the bottom-right title-block region (rightmost matching token in the bottom 30% of non-empty lines). Same heuristic as `drawing-index`, but a stricter `SHEET_RE`: the bulletin regex requires a hyphen separator (e.g. `A-100`, `LS-001`) and does NOT match hyphen-less formats like `A05`, `LS001`, or `M201` that `drawing-index` handles via a no-dash branch. If the project uses hyphen-less sheet numbers the completeness guard will abort and report the grammar mismatch — use the PLU-182 foundation pass instead.

### 3. Sheet title extraction

The title block also carries the **sheet title** below a `SHEET TITLE` anchor. Look for `TITLE` near the bottom right; the title text occupies the next few lines beneath it (often broken across 2–4 short lines). Stitch into a single string. If extraction fails, the cell is left blank — the merger can backfill from the Conformed CSV.

### 4. Narrative of Changes parsing

The narrative commonly comes from two or more authors:

- **Architect's memo** (top of the file): bullet-list with `<SHEET-#>: <description>` lines per discipline. Sometimes a range: `D-100 – D-101A: ...` — expand the range into individual sheets. Watch for em-dash (`–`), en-dash, hyphen, or `to`.
- **MEP/FP engineer's narrative** (attached afterward): each sheet is its own section header `<SHEET-#>: <TITLE>` followed by bullet points. Extract just the sheet #s.
- **Additional consultant narratives** (security/low-voltage/telecom etc.): same shape as MEP/FP when present.

Build a set of `narrative_sheets` — every sheet # the narratives say was revised.

### 5. Cross-check

- **In narrative but not in PDF** — Possibly a deletion ("delete sheet X" can leave the sheet out of the Bulletin). Verify by reading the narrative line. If it's not a deletion, flag as RFI: the sheet was claimed revised but isn't in the bundle.
- **In PDF but not in narrative** — Possibly an omission from the narrative. Always RFI-worthy: a sheet was revised but the change wasn't documented.

Write both classes of mismatch to the companion CSV with a `Type` column (`narrative_only` / `pdf_only`).

### 6. Spec section additions (out of scope, but worth noting)

The narrative often mentions added/changed spec sections (e.g. `Add section 085160 Aluminum Storm Windows`). Log these to stderr — do **not** put them in the CSV. They belong to a future spec-tracking skill.

---

## Output details

### Naming

- **Main CSV:** `Drawing Index - <issue>.csv` where `<issue>` defaults to the folder name (e.g. `2026-05-05 Bulletin 02`).
- **Mismatch CSV:** `Drawing Index - <issue> - Narrative Mismatch.csv` — only created when mismatches exist.
- **Excel-lock handling:** if the file is open, version it `v2`, `v3`, … (same as `drawing-index`).

### Stable schema

| Column | Source | Notes |
|---|---|---|
| Discipline | Sheet # prefix lookup | Inferred — confirm against narrative section if available |
| Sheet Number | Title block | Authoritative source for what page is what |
| Page Title | Title block (or blank) | Bulletin titles match Conformed titles when the sheet existed before; merger can backfill |
| PDF File | Filename of the combined Bulletin PDF | Single value for every row |
| Page in PDF | 1-indexed page in the combined PDF | Direct lookup |

---

## What to do after the run

1. Confirm row count matches what's expected (the narrative gives a rough count).
2. If `Narrative Mismatch.csv` exists: read each row, classify (deletion vs. omission vs. extra sheet), and tell the user. Offer to draft RFI text if it's a real mismatch.
3. Tell the user the path to the per-issue CSV. They (or the `drawing-index-merge` skill) will use it next.

---

## Failure modes

- **No narrative found.** Fall back to title-block scan only. CSV is still produced; mismatch CSV is skipped. Warn the user that cross-check is not available.
- **Narrative is a scan with no text layer.** Run OCR via the base `pdf` skill, then re-run.
- **Combined PDF is itself a scan.** Title-block scan fails; the script reports per-page extraction status. OCR required before retry.
- **Range expansion ambiguity.** A line like `A-100.2 – A-100.4` is unambiguous (3 sheets). A line like `H-501 – H-509` could mean 9 sheets or could refer to a non-contiguous range if the architect skips numbers. The script expands every integer between the endpoints and the merger flags any expanded sheet # not actually in the PDF — handle case-by-case.
- **SKS sheets.** Some bulletins introduce structural sketches (`SKS-1`, `SKS-2`, etc.) that are referenced on other structural sheets (e.g. S-101, S-203). These may appear as standalone pages in the Bulletin PDF (in which case the indexer captures them) or only as embedded callouts on the referenced sheets (in which case they don't have their own page). When in doubt, check the Bulletin PDF for a page whose sheet # is `SKS-1` / `SKS-2`.
