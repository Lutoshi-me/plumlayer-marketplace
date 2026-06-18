---
name: drawing-index-merge
description: "Merge per-issue Drawing Index CSVs (Conformed Set + Bulletins + Addenda + ASIs) into a single 'Franken Set' CSV showing where the LATEST version of every sheet lives. ALWAYS use this skill when the user asks to build, generate, or refresh the Franken Set, the current set, the latest set, the most-recent-version index, or a merged drawing index across multiple issues. Trigger on 'franken set', 'frankenset', 'current set index', 'latest set', 'merge bulletins', 'consolidate drawing index', 'roll up bulletins', 'combine bulletin indexes', 'most recent set', or '/franken-set'. Inputs are two or more per-issue Drawing Index CSVs (produced by the drawing-index or drawing-index-bulletin skills) supplied in CHRONOLOGICAL order (earliest first). Output is a single CSV where each sheet appears once, sourced from its most recent issue, with a Source Issue column for audit. This skill performs PURE CSV manipulation — no PDFs are read, fast and deterministic. It does NOT physically assemble the merged PDFs themselves (that is the drawing-set-assemble skill, not yet built) and does NOT produce a polished .xlsx (that is the drawing-index-publish skill, not yet built). Do NOT use this skill to INDEX an issue from raw PDFs — that is drawing-index (for full discipline-split issues) or drawing-index-bulletin (for combined single-PDF issues)."
---

# Drawing Index Merge — Franken Set Builder

Read this entire file before producing any Franken Set output.

---

## Overview

This skill rolls multiple per-issue Drawing Index CSVs forward into a single **Franken Set** CSV that answers the question "where is the latest version of sheet X?" for every sheet in the project.

It is pure CSV manipulation: no PDFs are read, no narratives are parsed. All upstream knowledge has already been baked into the per-issue CSVs by `drawing-index` (Conformed-shape) and `drawing-index-bulletin` (Bulletin-shape). This skill just decides who wins.

### Merge rule

**Latest issue containing the sheet wins.** When the same sheet # appears in multiple per-issue CSVs, the most recent CSV (the last one in the input order) is the source of record. Sheets that exist in an older issue but were not re-issued by a newer Bulletin keep their older source. Sheets that first appear in a Bulletin (e.g. SKS sketches, late additions) are added as new rows.

### Title backfill

`drawing-index-bulletin` deliberately leaves the `Page Title` column blank because Bulletin title-block text is too noisy to extract cleanly, and a sheet's title doesn't change between revisions anyway. The merger backfills any blank title from the first earlier issue that has a non-blank title for that sheet #.

---

## Workflow

**Trigger:** User asks to build / refresh the Franken Set, or wants to know where the latest version of any sheet lives.

**Action:**

1. Locate the per-issue CSVs. Default location: `<project>/Drawings/Drawing Index - *.csv`. If the user didn't specify which CSVs to merge, ask — or assume all `Drawing Index - <date> <issue>.csv` files in chronological order and confirm.
2. Confirm chronological order from filenames (issues are typically `YYYY-MM-DD <name>`). If you can't infer order from filenames, ask the user to specify it. Order is the merge rule — getting it wrong inverts the latest-wins logic.
3. Run `references/build_franken_set.py <issue1.csv> <issue2.csv> ...` with the CSVs in chronological order. The last argument is the most recent issue.
4. Read the output CSV and the optional companion files; tell the user:
   - Total sheets in the Franken Set.
   - Per-source-issue counts (how many sheets came from each issue).
   - Any sheets that newly appeared in a Bulletin (added rows).
   - Any sheets with blank titles still (the script logs these).

### Inputs

- **Required:** two or more per-issue Drawing Index CSVs in chronological order. Example for a project with two bulletins:
  ```
  "Drawing Index - 2025-12-15 Conformed Set.csv"
  "Drawing Index - 2026-02-09 Bulletin 01.csv"
  "Drawing Index - 2026-05-05 Bulletin 02.csv"
  ```
- **Optional:** path to a `Drawing Index - Unlisted Sheets.csv` (produced by `drawing-index` when discipline PDFs contain sheets not on the master drawing list) — use `--unlisted <path>` to fold those rows into the Conformed source.

### Output

Written next to the inputs:

- **`Drawing Index - Franken Set.csv`** — one row per sheet, sourced from its most recent issue.
- **`Drawing Index - Franken Set Changes.csv`** *(optional, present when 2+ inputs)* — for every sheet in the Franken Set, lists which issues touched it. Useful as a change log.

If the file is locked in Excel, version it `v2`, `v3`… (same convention as the other drawing-index skills).

### Output schema

| Column | Notes |
|---|---|
| Discipline | From the per-issue row that wins |
| Sheet Number | The merge key |
| Page Title | Backfilled from the earliest issue that has a non-blank title for this sheet # |
| Source Issue | Human-readable issue label (filename minus the "Drawing Index - " prefix and ".csv" suffix) |
| Source PDF File | The PDF filename from the winning issue |
| Source Page in PDF | The page number within that PDF |
| Touched By | Comma-separated list of every issue that touched this sheet (e.g. "Conformed Set, Bulletin 02") |

---

## How the merge works

```
franken = {}  # sheet_no -> winning row
title_by_sheet = {}  # sheet_no -> first non-blank title we've seen
touched = defaultdict(list)

for csv in input_csvs_in_chronological_order:
    issue_label = derive_issue_label_from_filename(csv)
    for row in csv:
        sheet = row["Sheet Number"]
        touched[sheet].append(issue_label)
        # Newer CSV always wins for source columns
        franken[sheet] = {
            "Discipline": row["Discipline"],
            "Source Issue": issue_label,
            "Source PDF File": row["PDF File"],
            "Source Page in PDF": row["Page in PDF"],
        }
        if row["Page Title"] and sheet not in title_by_sheet:
            title_by_sheet[sheet] = row["Page Title"]

# Sort by discipline (in known order) then by sheet number
write_csv(franken sorted by (discipline_rank, sheet_sort_key))
```

### Sheet-number sort

Sheet numbers don't sort cleanly as strings — `A-100` would sort before `A-99`. The script implements a numeric-aware sort: split on `-`, sort the numeric part numerically, suffix letters last. Decimal sheets like `A-100.2` sort between `A-100` and `A-100.3`.

### Discipline order

Follows the standard G-series discipline order (as on a typical G-001 drawing list): GENERAL, LIFE SAFETY, CIVIL, ARCHITECTURAL DEMO, ARCHITECTURAL, STRUCTURAL, FIRE PROTECTION, PLUMBING, HVAC, ELECTRICAL, FIRE ALARM, SECURITY, TELECOMMUNICATIONS, ELEVATOR. Unknown disciplines sort last alphabetically.

---

## What to do after the run

1. Tell the user the total sheet count and per-issue breakdown — e.g. "410 sheets total: 312 from Conformed, 70 from Bulletin 01, 28 from Bulletin 02" (numbers are illustrative).
2. Highlight any **newly added sheets** (rows where `Touched By` shows only a Bulletin issue, no Conformed). These are sheets the architect introduced post-Conformed — possibly worth a sanity check.
3. If the user asked "where is the latest A-XXX?", the Franken Set answers it directly — give them the row.
4. The Franken Set is the input to two downstream skills:
   - **`drawing-set-assemble`** (not yet built) — uses the Franken Set to slice pages out of each source PDF and stitch them into a clean discipline-split folder + combined PDF.
   - **`drawing-index-publish`** (not yet built) — uses the Franken Set + per-issue CSVs to build a Master Drawing Index .xlsx with one tab per issue plus a Franken Set tab.

---

## Failure modes

- **Inputs out of order.** Catastrophic — latest-wins inverts. The script tries to detect this by checking for date prefixes in filenames and warns if the filename dates aren't monotonically increasing. Always confirm order before running.
- **Schema drift.** All input CSVs must have the columns `Discipline, Sheet Number, Page Title, PDF File, Page in PDF`. The script errors clearly if a column is missing.
- **Duplicate sheet # within a single issue.** Indicates upstream parser confusion. The script logs and keeps the first occurrence per issue. Investigate the offending CSV.
- **Sheet absent from all later issues.** Stays at its oldest source. This is correct — an unrevised sheet stays at its Conformed state.
- **All issues have blank title for a sheet.** Sheet appears with a blank Page Title. Logged to stderr.
