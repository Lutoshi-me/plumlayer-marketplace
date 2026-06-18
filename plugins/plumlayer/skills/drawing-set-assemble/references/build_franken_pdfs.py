"""Assemble the Franken Set PDFs from a Franken Set CSV.

Outputs:
  - <out>/Drawings by Discipline/Franken Set -- <Discipline>.pdf
  - <out>/Most Current Set.pdf  (unless --no-combined)

Preserves per-page annotations (links, URL embeds, sticky notes) via pypdf's native
page copy. Synthesizes a fresh bookmark tree (one entry per sheet) at the document level.

Usage:
    python build_franken_pdfs.py <franken_set.csv>
    python build_franken_pdfs.py <csv> --out <folder>
    python build_franken_pdfs.py <csv> --no-combined
    python build_franken_pdfs.py <csv> --no-by-discipline
    python build_franken_pdfs.py <csv> --search-root <folder>  (repeatable)

See ../SKILL.md for the full design rationale.
"""

from __future__ import annotations

import argparse
import csv
import os
import re
import sys
from collections import OrderedDict, defaultdict

import pypdf

DISCIPLINE_ORDER = {
    name: i for i, name in enumerate([
        "GENERAL", "LIFE SAFETY", "CIVIL", "ARCHITECTURAL DEMO", "ARCHITECTURAL",
        "STRUCTURAL", "FIRE PROTECTION", "PLUMBING", "HVAC", "ELECTRICAL",
        "FIRE ALARM", "SECURITY", "TELECOMMUNICATIONS", "ELEVATOR",
    ])
}

REQUIRED_COLS = ["Discipline", "Sheet Number", "Source PDF File", "Source Page in PDF"]


def sheet_sort_key(sn: str) -> tuple:
    """Numeric-aware sheet # sort. Matches drawing-index-merge's implementation."""
    m = re.match(r"^([A-Z]+-?)([0-9]+)(?:\.([0-9]+))?([A-Z]?)$", sn)
    if not m:
        return (sn, 0, 0, "")
    prefix, intpart, decpart, suffix = m.groups()
    return (prefix, int(intpart), int(decpart) if decpart else 0, suffix or "")


def safe_filename(s: str) -> str:
    """Filesystem-safe version of a discipline name."""
    return re.sub(r'[<>:"/\\|?*]', "_", s).strip()


def build_source_index(search_roots: list[str]) -> dict[str, str]:
    """basename -> absolute path. Multiple matches: last one wins (later roots override)."""
    index: dict[str, str] = {}
    for root in search_roots:
        if not os.path.isdir(root):
            continue
        for dirpath, _, files in os.walk(root):
            for f in files:
                if f.lower().endswith(".pdf"):
                    index[f] = os.path.join(dirpath, f)
    return index


def safe_write_pdf(writer: pypdf.PdfWriter, path: str) -> str:
    target = path
    base, ext = os.path.splitext(path)
    n = 2
    while True:
        try:
            with open(target, "wb") as f:
                writer.write(f)
            return target
        except PermissionError:
            target = f"{base} v{n}{ext}"
            n += 1


def assemble_one_pdf(rows, source_readers, out_path, title_for_outline=False, parent_groups=False):
    """Write a PDF containing the given rows (in input order), with one bookmark per row.

    If parent_groups=True, group bookmarks by discipline (used for the combined output)."""
    writer = pypdf.PdfWriter()
    discipline_parents: dict[str, object] = {}
    skipped: list[tuple[str, str]] = []

    for row in rows:
        src_name = row["Source PDF File"]
        try:
            page_num = int(row["Source Page in PDF"])
        except (TypeError, ValueError):
            skipped.append((row["Sheet Number"], f"non-integer page: {row['Source Page in PDF']!r}"))
            continue
        reader = source_readers.get(src_name)
        if reader is None:
            skipped.append((row["Sheet Number"], f"source PDF not found: {src_name}"))
            continue
        if not (1 <= page_num <= len(reader.pages)):
            skipped.append((row["Sheet Number"], f"page {page_num} out of range in {src_name}"))
            continue

        new_idx = len(writer.pages)
        writer.add_page(reader.pages[page_num - 1])

        sheet_no = row["Sheet Number"]
        title = (row.get("Page Title") or "").strip()
        label = f"{sheet_no}  {title}" if title else sheet_no

        if parent_groups:
            disc = row["Discipline"]
            if disc not in discipline_parents:
                discipline_parents[disc] = writer.add_outline_item(disc, page_number=new_idx)
            writer.add_outline_item(label, page_number=new_idx, parent=discipline_parents[disc])
        else:
            writer.add_outline_item(label, page_number=new_idx)

    written = safe_write_pdf(writer, out_path)
    return written, len(writer.pages), skipped


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("franken_csv", help="Path to the Franken Set CSV.")
    ap.add_argument("--out", default=None,
                    help="Output folder (default: parent of the Franken Set CSV).")
    ap.add_argument("--no-by-discipline", action="store_true",
                    help="Skip the per-discipline PDFs.")
    ap.add_argument("--no-combined", action="store_true",
                    help="Skip the combined single PDF.")
    ap.add_argument("--search-root", action="append", default=[],
                    help="Additional folder to search for source PDFs (repeatable).")
    args = ap.parse_args()

    if not os.path.isfile(args.franken_csv):
        sys.exit(f"Not found: {args.franken_csv}")

    out_dir = args.out or os.path.dirname(os.path.abspath(args.franken_csv))
    os.makedirs(out_dir, exist_ok=True)

    # Load Franken Set
    with open(args.franken_csv, encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    if not rows:
        sys.exit("Franken Set CSV is empty.")
    missing = [c for c in REQUIRED_COLS if c not in rows[0]]
    if missing:
        sys.exit(f"Franken Set CSV missing required columns: {missing}")

    # Default search roots: walk up from the CSV to find source PDFs.
    search_roots = list(args.search_root)
    csv_parent = os.path.dirname(os.path.abspath(args.franken_csv))
    # Try parent and grandparent of csv_parent
    for candidate in [
        os.path.dirname(csv_parent),
        os.path.dirname(os.path.dirname(csv_parent)),
    ]:
        if candidate and candidate not in search_roots and os.path.isdir(candidate):
            search_roots.append(candidate)
    print(f"[info] searching for source PDFs in:", file=sys.stderr)
    for r in search_roots:
        print(f"  {r}", file=sys.stderr)

    pdf_index = build_source_index(search_roots)
    print(f"[info] indexed {len(pdf_index)} PDFs across search roots", file=sys.stderr)

    # Open each referenced source PDF once (lazy)
    needed = {r["Source PDF File"] for r in rows if r.get("Source PDF File")}
    source_readers: dict[str, pypdf.PdfReader] = {}
    for name in needed:
        path = pdf_index.get(name)
        if path is None:
            print(f"[warn] source PDF not found anywhere: {name}", file=sys.stderr)
            continue
        try:
            source_readers[name] = pypdf.PdfReader(path)
        except Exception as e:
            print(f"[warn] failed to open {name}: {e}", file=sys.stderr)

    # Group by discipline; within each group, sort by sheet #
    by_discipline: "OrderedDict[str, list[dict]]" = OrderedDict()
    for r in rows:
        by_discipline.setdefault(r["Discipline"], []).append(r)
    for disc in by_discipline:
        by_discipline[disc].sort(key=lambda r: sheet_sort_key(r["Sheet Number"]))

    # ----- Output 1: Drawings by Discipline -----
    if not args.no_by_discipline:
        by_disc_dir = os.path.join(out_dir, "Drawings by Discipline")
        os.makedirs(by_disc_dir, exist_ok=True)
        print("\n[info] writing per-discipline PDFs:", file=sys.stderr)
        for disc, disc_rows in by_discipline.items():
            out_path = os.path.join(by_disc_dir, f"Franken Set -- {safe_filename(disc.title())}.pdf")
            written, n_pages, skipped = assemble_one_pdf(disc_rows, source_readers, out_path)
            print(f"  {disc:22s} {n_pages:4d} pages -> {os.path.basename(written)}", file=sys.stderr)
            for sheet_no, reason in skipped:
                print(f"    [skip] {sheet_no}: {reason}", file=sys.stderr)

    # ----- Output 2: combined Most Current Set.pdf -----
    if not args.no_combined:
        # Sort disciplines into standard G-001 order, then within each by sheet #
        all_rows: list[dict] = []
        disc_sorted = sorted(by_discipline.keys(),
                             key=lambda d: (DISCIPLINE_ORDER.get(d, 999), d))
        for disc in disc_sorted:
            all_rows.extend(by_discipline[disc])
        out_path = os.path.join(out_dir, "Most Current Set.pdf")
        print(f"\n[info] writing combined PDF -> {os.path.basename(out_path)}", file=sys.stderr)
        written, n_pages, skipped = assemble_one_pdf(
            all_rows, source_readers, out_path, parent_groups=True,
        )
        print(f"  {n_pages} pages -> {written}", file=sys.stderr)
        for sheet_no, reason in skipped:
            print(f"  [skip] {sheet_no}: {reason}", file=sys.stderr)


if __name__ == "__main__":
    main()
