---
name: drawing-index
description: "Build the master Drawing Index CSV (Discipline, Sheet Number, Page Title, PDF File, Page in PDF) for a construction drawing set issued by discipline. ALWAYS use this skill when the user asks to build, regenerate, or update a drawing index, drawing list, sheet schedule, sheet index, or per-discipline sheet inventory from a folder of discipline-split PDFs (e.g. a Conformed Set, Permit Set, Bulletin, Addendum, ASI, or any dated issue folder organized as one PDF per discipline). Trigger on 'drawing index', 'drawing list', 'sheet schedule', 'sheet inventory', 'list every sheet', 'what's in this drawing set', 'rebuild the index for [issue name]', or '/drawing-index'. Output is always a .csv file (one row per sheet) plus a companion .csv when the architect's master list and the discipline PDFs disagree. This skill produces the STRUCTURAL SPINE only — sheet #, title, and PDF location. It does NOT extract per-sheet revision numbers/dates (that is the drawing-revisions skill, not yet built), does NOT add engineer/CSI/buyout-package context (drawing-context skill, not yet built), does NOT produce a polished .xlsx (drawing-index-publish skill, not yet built), and does NOT diff against a prior issue (drawing-index-diff skill, not yet built). Use this skill IN COMBINATION with the base `pdf` skill if the user wants you to verify any of the parsing manually. Do NOT use this skill when the user wants to extract content FROM a sheet (text, dimensions, schedules) — that is general pdf reading, not index building."
---

# Drawing Index Builder — Full Instructions

Read this entire file before producing any drawing-index output.

---

## Overview

This skill builds the **structural spine** of the project drawing index from a folder containing one PDF per discipline. The output is a CSV with one row per sheet:

| Discipline | Sheet Number | Page Title | PDF File | Page in PDF |
|---|---|---|---|---|

This is the canonical lookup that downstream skills (drawing-revisions, drawing-context, drawing-index-publish, drawing-index-diff) extend. It is **read-only authoritative for the issue** — once written, do not edit by hand; rebuild from source if anything looks wrong.

---

## Workflow

**Trigger:** User asks to build a drawing index for a specific issue folder (Conformed Set, Bulletin XX, Permit Set, Addendum, etc.) — or points at the project's default issue folder.

**Action:**

1. Locate the input folder. If the user didn't specify, ask. Typical project paths look like `<project>/Drawings/<issue name>/Drawings by Discipline/`. The folder must contain one PDF per discipline (filename should encode the discipline; e.g. `... -- General.pdf`, `... -- Architectural.pdf`).
2. Verify dependencies (see below).
3. Run `references/build_drawing_index.py <folder>` — it writes the CSV and (if anomalies exist) the companion CSV next to the input folder.
4. Read both output CSVs and surface a short summary to the user: total sheets, per-discipline counts, and a one-line callout per anomaly. **Do not bury anomalies** — they are usually worth flagging to the architect (on one real set we tested, 6 sheets in the PDFs were missing from the master drawing list, an RFI-worthy issue).

### Dependencies

- **Python 3** with `pdfplumber` (`pip install pdfplumber pypdf` if missing).
- **`pdftotext`** (poppler-utils) — used for fast per-page title-block scans on disciplines where list count ≠ PDF page count. Install via your OS package manager if missing.
- The base **`pdf` skill** (Anthropic's stock skill) — only needed if the user asks you to spot-check the parsing by reading specific sheet title blocks manually. The script does not depend on it.

### Inputs

- **Required:** absolute path to a folder of discipline-split PDFs (one PDF per discipline, filename contains the discipline name).
- **Optional:** issue label override (defaults to the parent folder's name, e.g. `2025-12-15 Conformed Set`).

### Outputs

Written **two levels up from `Drawings by Discipline`** — i.e., the parent of the issue folder. This matches where `drawing-index-bulletin` writes its CSV, so `drawing-index-merge` can find both alongside each other.

For the typical layout:
```
<project>/Drawings/
    Drawing Index - 2025-12-15 Conformed Set.csv          <-- written here
    Drawing Index - Unlisted Sheets.csv                   <-- and here
    2025-12-15 Conformed Set/
        Drawings by Discipline/                           <-- input
```

1. **`Drawing Index - <issue name>.csv`** — every listed sheet, with PDF File and Page in PDF columns populated.
2. **`Drawing Index - Unlisted Sheets.csv`** — present only if any discipline PDF contains pages whose sheet numbers aren't on the architect's master list. Each row identifies the discipline, PDF file, page number, and unlisted sheet #.

If the destination CSV is open in Excel (write fails with PermissionError), the script writes `<name> v2.csv` (or v3, v4 …) instead. **Do not delete the original** — versioning is intentional so the user can compare.

---

## How the parser works (so you can debug it)

1. **Locate the master list.** Scan all PDFs in the folder (first 5 pages each) for a page whose extracted text contains `DRAWING LIST`. When multiple PDFs match, the page with the most lines of content wins — the real drawing list has far more text than an incidental reference. On many projects this is the `General` discipline PDF, page 2 (sheet `G-001`); on other projects it may be a sheet like `A01 - DRAWING LIST` inside the Architectural PDF. Parse the found page with `pdfplumber.extract_words()`. The list is a multi-column table; column bands are computed dynamically from word left-edge distribution via histogram gap analysis — no hardcoded page-dimension values.
2. **Identify discipline section headers** within the list heuristically — no hardcoded name list is used. A header is any all-caps line, ≤ 40 chars, no digits, and containing no English function/preposition words (`AND`, `FOR`, `OF`, `THE`, etc.). Function words filter out wrapped sheet-title continuations (e.g. `AND PERSONNEL ACCESS`) that would otherwise look like headers. Single-word all-caps continuations (e.g. bare `ACCESS`) are protected by a continuation-first ordering. Each detected header is logged as `[info] discipline: <NAME>`.
3. **Map discipline → PDF filename** dynamically, using the discipline names actually found in the drawing list. Matching is tried in three passes (most-specific disciplines first to avoid `ARCHITECTURAL DEMO` stealing the `ARCHITECTURAL` PDF): (1) full discipline name as substring, (2) all words present, (3) words tried longest-first. No hardcoded keyword lists.
4. **Per discipline, reconcile listed sheets against actual PDF pages:**
   - If `len(listed) == PDF page count` → **positional mapping**: sheet #N in the list lives at PDF page N. This is fast (no per-page reading) and correct when the PDF is bound in list order.
   - If counts differ → run `pdftotext -layout` over the PDF, scan each page for a sheet number in the bottom-right title-block region (rightmost token matching the sheet-# regex in the bottom 30% of non-empty lines). Match found sheets to the master list; any unmatched page is an **unlisted sheet** (write to the anomalies CSV).
5. **Sheet number regex:** handles both dash-separated (`G-001`, `LS-100.1`, `A-100.2`, `D-101A`, `FP-100A`, `VT01`) and no-dash (`A01`, `A00`, `S100`, `M201A`) formats. Sheet-title separator dashes (`A01 - COVER SHEET`) are also stripped. Pattern: `^((?:[A-Z]{1,3}D?-[0-9]{1,4}(?:\.[0-9]+)?[A-Z]?)|(?:[A-Z]{1,3}[0-9]{2,4}[A-Z]?)|(?:VT[0-9]{2}))$`.
6. **Wrapped titles in the master list.** Long sheet names occasionally wrap to a second line (e.g. `... PERSONNEL AND` continued by `ACCESS` on the next row). The parser appends any sheet-number-less row to the previous sheet's title. Verify against the actual sheet title block when this happens — sometimes the master list is itself truncated (on some real sets, `E-421` and `E-422` both have longer titles in their title blocks than what the list shows).
7. **Source typos.** Preserve typos exactly as printed in the master list. On one real set, `A-100.2` read `E.OS. PLAN` (missing the second period) in both the list and the sheet's own title block — leave it as the architect wrote it.

---

## What to do after the run

1. **Read the main CSV.** Confirm row count matches what the master list claims (the script looks for a `Total Number of Sheets: NNN` footer and prints it if found).
2. **Read the anomalies CSV if it exists.** For each unlisted sheet, decide:
   - **Likely RFI** — sheet appears in the discipline PDF with a normal title block but isn't on the master list. Tell the user this is RFI-worthy and ask if they want a draft.
   - **Likely intentional** — cover sheet, divider, or transmittal page (rare with discipline-split sets). User judgment.
3. **Report.** Give the user:
   - File path of the main CSV.
   - Total sheet count and per-discipline counts (table form).
   - A one-line callout per anomaly with sheet # and source page.
   - One sentence on what to do next (typically: review anomalies, then run drawing-revisions if/when that skill exists).

---

## Failure modes to watch for

- **Cloud-only placeholder PDFs.** Files that are synced from SharePoint or Google Drive may show a file size but fail to open. The script raises a clear error; tell the user to open the file once in Explorer/Finder to force a sync.
- **PDF with no text layer.** If a discipline PDF is a flat scan, `pdftotext` returns empty pages and title-block scans miss everything. The script reports this per file. Fall back to running OCR (the base `pdf` skill covers this) before retrying, or trust positional mapping if counts happen to match.
- **Drawing list not found.** The script scans the first 5 pages of every PDF in the folder for a page containing `DRAWING LIST`. If no PDF contains this text, it errors with a clear message — likely a scanned-image PDF (no text layer) or a non-standard folder layout. OCR the relevant PDF first if needed.
- **Discipline PDF not matched.** If a discipline name from the drawing list can't be matched to any PDF filename (all three passes fail), the script warns `[warn] DISCIPLINE: no matching PDF found in folder` and skips those sheets in the reconciliation. This usually means the PDF was named with an abbreviation the matching passes can't resolve — check the `[warn]` output and rename or symlink the PDF to include a recognizable word from the discipline name.
- **The pdfplumber word extraction can time out on very large PDFs** (large Arch PDFs can be 100 MB+). The script avoids touching large PDFs entirely when their list count matches their page count, which is the normal case. If counts diverge and the script has to scan a large PDF, expect a 1–3 minute pdftotext pass.

---

## Re-runnability

This skill is fully re-runnable on the same folder with no side effects: it overwrites the main CSV (or versions it `v2`, `v3` … if Excel locks it). Always rebuild from source — do not edit the CSV by hand.

When a new Bulletin or ASI lands as its own `Drawings by Discipline` folder, point the skill at that folder. The output sits beside the new issue folder, parallel to the prior issue's CSV. Differencing two issues' CSVs is the job of the (not-yet-built) drawing-index-diff skill.
