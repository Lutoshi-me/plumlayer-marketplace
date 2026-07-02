"""
schedule_prepare.py -- prepare phase for the schedule-ingestion pipeline.

Doctrine role (schedule-ingestion-design.md, recalibration 2026-06-28):
  The pipeline is: prepare -> agent-column-map -> ground.
  This script is the PREPARE phase: for each schedule sheet in the roster,
  render the page to a PNG and dump its text spans to JSONL. It emits a
  manifest file that the agent (column-map phase) then fills in per-table
  with the column structure and region typing (table / diagram / notes).

Output (all OUTSIDE the repo, at INGEST_OUT_DIR):
  prepare/
    <sheetId>_p<page>.png          -- rendered page at RENDER_DPI dpi
    <sheetId>_p<page>_spans.jsonl  -- one span per line {text, bbox}
  schedule_prepare_manifest.json   -- the manifest, initially with empty
                                       column_maps per entry, to be filled
                                       by the agent column-map phase.

The manifest shape (one entry per roster sheet):
  {
    "sheetId": "sheet:P-002",
    "pageIdx": 337,
    "sourceInstrument": "1270-COMM-IFC/337",
    "renderPath": "prepare/P-002_p337.png",
    "spansPath": "prepare/P-002_p337_spans.jsonl",
    "spanCount": 412,
    "column_maps": []   <-- to be filled by the agent
  }

column_map shape (filled by the agent, one per table on the sheet):
  {
    "tableTitle": "RESIDENTIAL UNIT PLUMBING FIXTURE SCHEDULE",
    "kind": "plumbingFixtureType",
    "layout": "tabular",
    "regionBbox": [x0, y0, x1, y1],   -- in PDF points
    "headerRowCount": 1,
    "keyColumn": {"name": "designation", "xLeft": 145.0, "xRight": 210.0},
    # keyColumn takes two OPTIONAL structural hints (both default false; absent = today's
    # behavior). "wrapped": true  -- the key cell is split across N stacked lines that
    #   read as one code ("HP" over "A" => "HP-A"); selects the key-first stacking path,
    #   the tool joins the stack top-to-bottom with '-'. "numericKey": true  -- accept a
    #   bare integer key on a DEFINITION table (same gate tableType:"instance" opens, no
    #   instance tag); never loosens the global canon_code gate. Both hints apply to the
    #   tabular path only -- in matrix layout "keyColumn" is the attribute-label column,
    #   and numeric matrix code-columns gate via tableType:"instance" instead.
    "columns": [
      {"name": "description", "xLeft": 210.0, "xRight": 355.0},
      {"name": "areaLocation", "xLeft": 355.0, "xRight": 450.0},
      ...
    ],
    "deferredRegions": [
      {"type": "notes", "regionBbox": [x0, y0, x1, y1]}
    ]
  }

Confidential: reads from INGEST_PDF (local path, outside the repo).
Writes to INGEST_OUT_DIR (also outside the repo). PyMuPDF + stdlib.

Run:
  INGEST_PDF="/path/to/set.pdf" \\
  INGEST_SET_TAG="1270-COMM-IFC" \\
  INGEST_OUT_DIR=~/dev/plumlayer-private/schedule-ingest-output \\
  INGEST_PAGES="337,12"  # optional: comma-separated 0-indexed page nums \\
  RENDER_DPI=150  # optional, default 150 \\
  python schedule_prepare.py

Optional INGEST_PAGES: comma-separated 0-indexed page nums (from the roster).
If not set, all sheets in the roster are prepared.
"""

from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path

try:
    import fitz  # PyMuPDF
    _FITZ_AVAILABLE = True
except ImportError:
    _FITZ_AVAILABLE = False

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

PDF_PATH = os.environ.get("INGEST_PDF", "")
SET_TAG = os.environ.get("INGEST_SET_TAG", "SET")
OUT_DIR = os.environ.get("INGEST_OUT_DIR") or os.path.join(os.getcwd(), "output")
INGEST_PAGES = os.environ.get("INGEST_PAGES", "")
RENDER_DPI = int(os.environ.get("RENDER_DPI", "150"))


# ---------------------------------------------------------------------------
# Roster loading (reuses the same JSONL format as schedule_inventory.py)
# ---------------------------------------------------------------------------

def load_roster_from_jsonl(path: str) -> list[dict]:
    entries: list[dict] = []
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            entries.append(json.loads(line))
    return entries


# ---------------------------------------------------------------------------
# Span extraction (rotation-aware, same as LocalSpanProvider in schedule_inventory.py)
# ---------------------------------------------------------------------------

def extract_spans(page: "fitz.Page") -> list[dict]:
    """Extract text spans from a page, applying rotation correction."""
    mat = page.rotation_matrix
    spans: list[dict] = []
    for blk in page.get_text("dict")["blocks"]:
        for line in blk.get("lines", []):
            for sp in line.get("spans", []):
                t = sp["text"].strip()
                if not t:
                    continue
                r = fitz.Rect(sp["bbox"]) * mat
                spans.append({
                    "text": t,
                    "bbox": [round(r.x0, 2), round(r.y0, 2),
                             round(r.x1, 2), round(r.y1, 2)],
                })
    return spans


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    if not PDF_PATH:
        sys.exit(
            "[error] INGEST_PDF must be set to the local combined PDF path.\n"
            "Also set INGEST_OUT_DIR."
        )
    if not _FITZ_AVAILABLE:
        sys.exit("[error] PyMuPDF (fitz) not installed -- pip install pymupdf")

    out_dir = Path(OUT_DIR)
    roster_path = out_dir / "schedule_roster.jsonl"
    if not roster_path.exists():
        sys.exit(
            f"[error] roster file not found: {roster_path}\n"
            "Fetch the roster first: python fetch_schedule_roster.py"
        )

    roster = load_roster_from_jsonl(str(roster_path))

    # Filter to specific pages if INGEST_PAGES is set
    if INGEST_PAGES:
        page_filter = {int(p.strip()) for p in INGEST_PAGES.split(",") if p.strip()}
        roster = [e for e in roster if e.get("page_idx", -1) in page_filter]

    # Prepare output subdirectory
    prepare_dir = out_dir / "prepare"
    prepare_dir.mkdir(parents=True, exist_ok=True)

    print("=" * 80)
    print(f"SCHEDULE PREPARE  |  {SET_TAG}  |  {len(roster)} sheets")
    print(f"PDF: {PDF_PATH}")
    print(f"Output: {prepare_dir}  @{RENDER_DPI}dpi")
    print("-" * 80)

    doc = fitz.open(PDF_PATH)
    manifest_entries: list[dict] = []

    for entry in roster:
        page_idx: int = entry.get("page_idx", -1)
        subject: str = entry.get("subject", "")
        source_instrument: str = entry.get("source_instrument", "")

        # Slug: "sheet:P-002" -> "P-002"
        slug = subject.replace("sheet:", "").replace("/", "_").replace(":", "_")

        if page_idx < 0:
            # No numeric page ref -- include in manifest as deferred
            manifest_entries.append({
                "sheetId": subject,
                "pageIdx": page_idx,
                "sourceInstrument": source_instrument,
                "renderPath": None,
                "spansPath": None,
                "spanCount": 0,
                "deferredReason": "no-page-ref-agent-vision-crop",
                "column_maps": [],
            })
            print(f"  {subject:16s}  page  -1  [DEFERRED: no page ref]")
            continue

        # Render PNG
        page = doc[page_idx]
        mat = fitz.Matrix(RENDER_DPI / 72, RENDER_DPI / 72)
        pix = page.get_pixmap(matrix=mat)
        png_name = f"{slug}_p{page_idx}.png"
        png_path = prepare_dir / png_name
        pix.save(str(png_path))

        # Extract spans
        spans = extract_spans(page)
        spans_name = f"{slug}_p{page_idx}_spans.jsonl"
        spans_path = prepare_dir / spans_name
        with spans_path.open("w", encoding="utf-8") as fh:
            for sp in spans:
                fh.write(json.dumps(sp) + "\n")

        manifest_entries.append({
            "sheetId": subject,
            "pageIdx": page_idx,
            "sourceInstrument": source_instrument,
            "renderPath": f"prepare/{png_name}",
            "spansPath": f"prepare/{spans_name}",
            "spanCount": len(spans),
            "column_maps": [],   # to be filled by the agent column-map phase
        })

        print(f"  {subject:16s}  page {page_idx:3d}  {len(spans):4d} spans  "
              f"-> {png_name}")

    doc.close()

    # Write manifest (with empty column_maps, ready for agent fill-in)
    manifest_path = out_dir / "schedule_prepare_manifest.json"
    with manifest_path.open("w", encoding="utf-8") as fh:
        json.dump(manifest_entries, fh, indent=2)

    print("-" * 80)
    print(f"manifest .......... {manifest_path}")
    print(f"  entries: {len(manifest_entries)}  "
          f"(deferred: {sum(1 for e in manifest_entries if e['pageIdx'] < 0)})")
    print(f"renders + spans ... {prepare_dir}")
    print("=" * 80)
    print()
    print("Next: fill 'column_maps' in the manifest (agent column-map phase),")
    print("then run schedule_ground.py to emit grounded claims.")


if __name__ == "__main__":
    main()
