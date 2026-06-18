---
name: drawing-set-assemble
description: "Assemble a fresh discipline-split drawing set (one PDF per discipline, mirroring the Conformed Set folder shape) from a Franken Set CSV, pulling the latest version of every sheet from its source PDF. ALWAYS use this skill when the user asks to assemble, build, generate, or produce the Franken Set PDFs, the merged drawing set, the current PDFs, the latest PDF set, the merged Drawings by Discipline folder, or a single combined latest-set PDF. Trigger on 'assemble franken set', 'build franken pdfs', 'merge drawings into pdfs', 'create current set', 'rebuild drawings by discipline', 'split franken set by discipline', 'combine into one pdf', 'merged drawing pdf', or '/assemble-set'. Inputs are a Franken Set CSV (from the drawing-index-merge skill) and the source PDFs it references. Outputs are (1) a Drawings by Discipline folder with one PDF per discipline containing only the latest sheets in sheet-# order, AND (2) optionally a single combined PDF. Both outputs preserve per-page annotations, links, and URL embeds from the source PDFs, and add fresh bookmarks (one per sheet, labeled with sheet # + title) at the document level. Use this skill IN COMBINATION with the base `pdf` skill for any post-assembly QC. Do NOT use this skill to BUILD the Franken Set CSV — that is the drawing-index-merge skill. Do NOT use this skill to produce the Master Drawing Index Excel workbook — that is the drawing-index-publish skill."
---

# Drawing Set Assemble — Franken Set PDF Builder

Read this entire file before producing any assembled output.

---

## Overview

This skill takes a **Franken Set CSV** (which says "for every sheet, the latest version lives at source_pdf, page N") and physically assembles two deliverables:

1. **`Drawings by Discipline/`** — a folder mirroring the Conformed Set's `Drawings by Discipline` structure. One PDF per discipline (Arch, Structural, Plumbing, …), each containing only the latest sheets in sheet-# order. Drop-in replacement for working from a single discipline.
2. **`Most Current Set.pdf`** *(optional)* — a single combined PDF with every latest sheet, sorted by discipline then sheet number. Useful for printing the whole set or for the field.

Both outputs:

- **Preserve per-page annotations** — links, URL embeds, callouts, sticky notes — using pypdf's native page copy. Anything the architect placed on the page (inter-sheet hyperlinks, key plan callouts) carries through.
- **Add fresh bookmarks** — one entry per sheet, labeled `<sheet#>  <Page Title>` (e.g. `A-101  ENLARGED CONSTRUCTION PLAN - BASEMENT LEVEL`). This produces a navigation experience that is typically better than the source PDFs, which often have no bookmarks.

---

## Workflow

**Trigger:** User asks to assemble / build / produce the Franken Set PDFs, or wants a current-state drawing set as a folder or single PDF.

**Action:**

1. Locate the Franken Set CSV. If absent, run the `drawing-index-merge` skill first.
2. Locate the source PDFs. The Franken Set CSV's `Source PDF File` column holds basenames only — the script must resolve them to absolute paths. Default search roots: the Conformed Set's `Drawings by Discipline/` folder plus each Bulletin's folder. The script walks these roots to build a basename→fullpath map.
3. Run `references/build_franken_pdfs.py <franken_set_csv>` with optional flags:
   - `--no-combined` — skip the single combined PDF, produce only the discipline folder.
   - `--no-by-discipline` — skip the discipline folder, produce only the combined PDF.
   - `--out <folder>` — override the output folder (default: same folder as the Franken Set CSV).
   - `--search-root <path>` — add a search root for source PDFs (repeatable).
4. After the run, report:
   - Number of output PDFs written and total page count.
   - Any sheets that couldn't be assembled (source PDF missing, page out of range).
   - Where annotations were preserved vs. where they were synthetic.

### Dependencies

- **Python 3** with `pypdf` (`pip install pypdf` if missing).
- No `pdftotext` or `pdfplumber` needed — this is a pure pypdf job.

### Inputs

- **Required:** a Franken Set CSV with columns `Discipline, Sheet Number, Page Title, Source Issue, Source PDF File, Source Page in PDF`.
- **Source PDFs:** the script needs to find each `Source PDF File` referenced in the CSV. By default it scans up from the CSV's location, but pass `--search-root` to extend.

### Outputs

Written to `<franken_csv_parent>/` by default:

1. **`Drawings by Discipline/Franken Set -- <Discipline>.pdf`** — one PDF per discipline.
2. **`Most Current Set.pdf`** — single combined PDF (omit with `--no-combined`).

If a target file is locked in Excel/Acrobat, version it `v2`, `v3`… (same convention as the other skills).

---

## How assembly works

```python
# Pseudocode
franken = read_csv(franken_set_csv)
source_pdfs = {}  # basename -> PdfReader, opened once per source

# Group by discipline for the by-discipline output
by_discipline = group_by(franken, "Discipline")

# Order within each discipline: sheet # ascending (numeric-aware)
for disc, rows in by_discipline.items():
    writer = PdfWriter()
    for row in sorted(rows, key=sheet_sort_key):
        src = open_or_cache(row["Source PDF File"])
        page_idx = int(row["Source Page in PDF"]) - 1  # 1-indexed in CSV
        new_idx = len(writer.pages)
        writer.add_page(src.pages[page_idx])  # preserves annotations
        writer.add_outline_item(
            title=f"{row['Sheet Number']}  {row['Page Title']}",
            page_number=new_idx,
        )
    write_to_disk(writer, output_path)
```

### Sheet ordering

Sheet numbers must sort numerically, not lexically. Reuse `sheet_sort_key` from the `drawing-index-merge` skill: split on `-`, sort numeric portion as int, decimals sort between integers, suffix letters last. Decimals: `A-100`, `A-100.1`, `A-100.2`, `A-101`. Suffix letters: `A-101`, `A-101A`, `A-101B`, `A-102`.

### Discipline ordering (for combined PDF)

Follows the standard G-series discipline order (as on a typical G-001 drawing list): GENERAL, LIFE SAFETY, CIVIL, ARCHITECTURAL DEMO, ARCHITECTURAL, STRUCTURAL, FIRE PROTECTION, PLUMBING, HVAC, ELECTRICAL, FIRE ALARM, SECURITY, TELECOMMUNICATIONS, ELEVATOR. New disciplines sort last alphabetically.

### Annotation preservation

`pypdf.PdfWriter.add_page(reader.pages[N])` copies the page object including its `/Annots` array. Per-page links (Internal Links cross-referencing other sheets) survive **within the same source PDF**, but a link from a Conformed-source page pointing to "page 47 of Arch.pdf" will end up pointing into the *original* Arch.pdf, not the new Franken Set discipline PDF. That's typically acceptable — Acrobat will open the original target if available — but worth noting.

True per-page annotations (sticky notes, text highlights, URL embeds in the page itself) carry through correctly.

### Bookmark synthesis

After all pages are added, the writer's outline is built fresh:

```python
for disc, rows in by_discipline.items():
    parent = writer.add_outline_item(disc, page_number=first_page_of_discipline)
    for row in sorted(rows, key=sheet_sort_key):
        writer.add_outline_item(
            title=f"{row['Sheet Number']}  {row['Page Title']}",
            page_number=row.new_page_index,
            parent=parent,
        )
```

For the discipline-split outputs, the outer parent loop is unnecessary — each output already represents one discipline. For the combined output, the discipline-level parent gives a two-tier outline.

---

## What to do after the run

1. Tell the user the path of the new `Drawings by Discipline/` folder (and the combined PDF if produced).
2. Report any sheets that couldn't be assembled — typically because the source PDF wasn't found in the search roots. Log them with their CSV row so the user can investigate.
3. Suggest opening one of the new PDFs in Acrobat to verify the bookmark panel and confirm page-level annotations (e.g. inter-sheet hyperlinks) still work.
4. Remind the user that any existing combined set PDFs live in the same folder — they may want to rename or archive them once they trust the new output.

---

## Failure modes

- **Source PDF not found.** Most common cause: the Franken Set CSV references a PDF by basename, but it's not on the user's search roots. The script logs the missing basename(s) and continues with the assemblable rows. Re-run with `--search-root <path>` pointing at the missing file's parent.
- **Page index out of range.** Indicates the source PDF was edited since the Franken Set was built (someone replaced the file). The CSV row's `Source Page in PDF` no longer aligns. Tell the user to re-run `drawing-index-merge` to refresh the Franken Set first.
- **Encrypted source PDF.** pypdf can read most architect-encrypted PDFs (they typically only restrict editing/printing, not viewing). If a source is fully encrypted, the script raises and tells the user.
- **Very large output.** The combined PDF can exceed 300 MB on large projects. Writing is incremental, but the final file is big. Consider running with `--no-combined` if you only need the discipline folder.
- **Output file locked in Acrobat.** The skill versions the filename (`v2`, `v3`…). Close the open file and re-run for a clean overwrite.
- **Sheet appears in CSV but title is blank.** Bookmark label falls back to just the sheet # (no second column). User can fill titles later via the future `drawing-revisions` skill, then re-assemble.
