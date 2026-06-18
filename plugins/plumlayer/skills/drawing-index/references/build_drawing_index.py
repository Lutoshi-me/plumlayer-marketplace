"""Build the drawing-index CSV for a discipline-split drawing set.

Usage:
    python build_drawing_index.py <path to Drawings by Discipline folder>
    python build_drawing_index.py <folder> --issue "2026-05-05 Bulletin 02"

Output: two CSVs written one directory up from the input folder.
  - Drawing Index - <issue>.csv          (one row per listed sheet)
  - Drawing Index - Unlisted Sheets.csv  (only if anomalies found)

See ../SKILL.md for the full design rationale.
"""

from __future__ import annotations

import argparse
import csv
import os
import re
import subprocess
import sys
from collections import Counter, defaultdict, OrderedDict
from typing import Iterable

import pdfplumber

# English function/preposition words that appear in sheet titles but not discipline headers.
# Used to distinguish a multi-word continuation fragment ("AND PERSONNEL ACCESS") from a
# discipline header ("FIRE PROTECTION"). Single-word continuations ("ACCESS") are handled
# by the continuation-first ordering in parse_drawing_list.
_FUNCTION_WORDS = frozenset({
    "AND", "OR", "FOR", "OF", "THE", "A", "AN", "IN", "ON", "AT",
    "TO", "FROM", "BY", "WITH", "AS", "IS", "ARE", "BE", "NOT",
})

# Matches both dash-separated (G-001, LS-100.1, A-100.2, D-101A, FP-100A, T-100A)
# and no-dash (A01, A00, S100, M201A) sheet number formats.
SHEET_RE = re.compile(
    r"^((?:[A-Z]{1,3}D?-[0-9]{1,4}(?:\.[0-9]+)?[A-Z]?)"   # G-001, LS-100.1, A-100.2, D-101A
    r"|(?:[A-Z]{1,3}[0-9]{2,4}[A-Z]?)"                      # A01, A00, S100, M201A (no dash)
    r"|(?:VT[0-9]{2}))$"                                     # VT01 (special case)
)


# ---------- master list discovery ----------

def find_drawing_list_pdf(folder: str) -> tuple[str, int]:
    """Scan all PDFs for the architect's master drawing list page.

    Collects every page (first 5 per PDF) that contains the text 'DRAWING LIST',
    then returns the candidate with the most lines of content — the actual list page
    rather than any incidental reference to one.
    """
    pdfs = sorted(f for f in os.listdir(folder) if f.lower().endswith(".pdf"))
    candidates: list[tuple[int, str, int]] = []  # (line_count, pdf_name, page_idx)

    for pdf_name in pdfs:
        fp = os.path.join(folder, pdf_name)
        try:
            with pdfplumber.open(fp) as pdf:
                for page_idx, page in enumerate(pdf.pages[:5]):
                    text = page.extract_text() or ""
                    if "DRAWING LIST" in text.upper():
                        line_count = sum(1 for l in text.splitlines() if l.strip())
                        candidates.append((line_count, pdf_name, page_idx))
        except Exception as exc:
            print(f"[warn] Could not scan {pdf_name}: {exc}", file=sys.stderr)

    if not candidates:
        raise RuntimeError(
            "Could not find a 'DRAWING LIST' page in any PDF in the folder. "
            "Check that at least one PDF contains the architect's drawing list."
        )

    # Most content wins — the real drawing list has far more lines than incidental mentions.
    candidates.sort(reverse=True)
    _, pdf_name, page_idx = candidates[0]
    return pdf_name, page_idx


# ---------- discipline → PDF discovery (dynamic) ----------

def match_disciplines_to_pdfs(folder: str, disciplines: list[str]) -> dict[str, str]:
    """Match discipline names (as parsed from the drawing list) to PDF filenames.

    Tries progressively looser criteria so that project-specific naming conventions
    work without any hardcoded keyword lists. Most-specific discipline names (most words)
    are matched first to prevent 'ARCHITECTURAL DEMO' stealing the 'ARCHITECTURAL' PDF.

    Pass 1 — full discipline name appears as substring in PDF basename.
    Pass 2 — every word of the discipline name appears in PDF basename.
    Pass 3 — each word tried longest-first; first hit wins.
    """
    pdfs = sorted(f for f in os.listdir(folder) if f.lower().endswith(".pdf"))
    mapping: dict[str, str] = {}
    used: set[str] = set()

    # Match most-specific disciplines first (most words → longest name → most precise)
    ordered = sorted((d for d in disciplines if d), key=lambda d: (-len(d.split()), -len(d)))

    for disc in ordered:
        dl = disc.lower()
        words = dl.split()
        best: str | None = None

        # Pass 1: full name substring
        for f in pdfs:
            if f not in used and dl in f.lower():
                best = f
                break

        # Pass 2: all words present
        if not best:
            for f in pdfs:
                if f not in used and all(w in f.lower() for w in words):
                    best = f
                    break

        # Pass 3: words tried longest-first, first match wins
        if not best:
            for w in sorted(words, key=len, reverse=True):
                for f in pdfs:
                    if f not in used and w in f.lower():
                        best = f
                        break
                if best:
                    break

        if best:
            mapping[disc] = best
            used.add(best)
        else:
            print(f"[warn] {disc}: no matching PDF found in folder", file=sys.stderr)

    leftover = [f for f in pdfs if f not in used]
    if leftover:
        print(f"[warn] PDFs not matched to any discipline: {leftover}", file=sys.stderr)

    return mapping


# ---------- master list parser ----------

def _column_bands(words: list[dict]) -> list[tuple[float, float]]:
    """Derive x-bands of a multi-column drawing list via gap analysis on word left-edges."""
    if not words:
        return []

    xs = [w["x0"] for w in words]
    lo = min(xs)
    hi = max(w["x1"] for w in words)
    span = hi - lo
    if span < 1:
        return [(lo, hi)]

    # Build histogram of word left-edges in 200 equal-width bins
    N = 200
    counts = [0] * N
    for x in xs:
        b = min(int((x - lo) / span * N), N - 1)
        counts[b] += 1

    # Smooth with a 3-bin moving average to reduce noise
    smooth = ([counts[0]]
              + [(counts[i-1] + counts[i] + counts[i+1]) / 3.0 for i in range(1, N-1)]
              + [counts[-1]])

    # A gap is a run of bins below 10% of the median non-zero bin count
    nz = sorted(c for c in smooth if c > 0)
    if not nz:
        return [(lo, hi)]
    gap_thresh = max(0.5, nz[len(nz) // 2] * 0.10)

    gap_runs: list[tuple[int, int]] = []
    in_gap = False
    run_start = 0
    for i, c in enumerate(smooth):
        if c <= gap_thresh and not in_gap:
            in_gap, run_start = True, i
        elif c > gap_thresh and in_gap:
            in_gap = False
            gap_runs.append((run_start, i - 1))
    if in_gap:
        gap_runs.append((run_start, N - 1))

    # Keep only gaps that are ≥ 3% of total span and not at the very margins
    margin_bins = int(N * 0.04)
    min_gap_bins = max(2, int(N * 0.03))
    sig = [(s, e) for s, e in gap_runs
           if e - s >= min_gap_bins and s > margin_bins and e < N - margin_bins]

    # Pick the 2 widest gaps as column separators (→ 3 columns) or 1 gap (→ 2 columns)
    sig.sort(key=lambda g: -(g[1] - g[0]))
    separators = sorted(sig[:2])

    if not separators:
        return [(lo, hi)]

    def b2x(b: int) -> float:
        return lo + (b + 0.5) / N * span

    bands: list[tuple[float, float]] = []
    prev = lo
    for gs, ge in separators:
        bands.append((prev, b2x(gs)))
        prev = b2x(ge + 1)
    bands.append((prev, hi))
    return bands


def _is_discipline_header(line: str) -> bool:
    """Heuristic: a discipline section header is all-caps, has no digits, is ≤ 40 chars,
    and contains no English function/preposition words (those appear in titles, not headers).
    """
    if not line.isupper():
        return False
    if len(line) < 2 or len(line) > 40:
        return False
    if any(c.isdigit() for c in line):
        return False
    words = set(line.split())
    if words & _FUNCTION_WORDS:
        return False
    return True


def parse_drawing_list(list_page) -> tuple[list[tuple[str, str, str]], int | None]:
    """Return [(discipline, sheet_no, page_title), ...], total_sheets_claimed.

    Walks the drawing list's columns top-to-bottom, then left-to-right. Section headers
    are detected heuristically (all-caps, no digits, no function words). Sheet rows parse
    as `<sheet#> <title>` or `<sheet#> - <title>` (both styles supported). Continuation
    lines (wrapped long sheet names) are appended to the previous sheet's title. Discipline
    names are entirely derived from the document — nothing is hardcoded.

    Hardened against two known artifact classes (a hardening fix):

    1. Phantom row from title-block sheet number — the G-001 sheet's own large title-block
       number sits far right of the list columns but its y-band can fall between printed
       table rows, causing the y-sorted row assembler to sweep it in. Fix: exclude words
       whose rendered height exceeds _TABLE_TEXT_MAX_HEIGHT (table body text is uniformly
       ~9.5 pt; the title-block token is much larger). Filter is applied after column-band
       detection so the title-block word does not warp the band boundaries either.

    2. Row merge hiding a listed sheet — a page-margin annotation token (e.g. "MP") at the
       far-left margin can cluster with the adjacent sheet row (within ytol=6 pt) because
       pdfplumber measures font height differently for these glyphs. The same height filter
       excludes these margin tokens. A second guard splits any assembled row whose title
       contains an embedded sheet-number token: if the title of row N begins with or
       contains `<sheet#> <words>`, the second sheet-number and its trailing words are
       split out as a new row and row N's title is truncated. This catches any merge that
       survives the height filter.
    """
    # Table body text on a typical drawing list is uniformly ~9.5 pt tall.
    # Anything taller is title-block text, page-margin annotation, or a column header.
    # 15 pt gives comfortable headroom without risk of cutting real table content.
    _TABLE_TEXT_MAX_HEIGHT = 15.0

    words = list_page.extract_words(use_text_flow=False, keep_blank_chars=False)
    bands = _column_bands(words)
    if not bands:
        return [], None

    page_h = list_page.height
    # Restrict to drawing-list body — skip top headers and bottom footers.
    # Height filter: exclude over-tall words (title-block numbers, margin annotations)
    # whose y-band would otherwise sweep them into table row assembly.
    body = [w for w in words if 160 < w["top"] < page_h - 60
            and bands[0][0] <= w["x0"] < bands[-1][1]
            and w["bottom"] - w["top"] <= _TABLE_TEXT_MAX_HEIGHT]

    def col_of(w):
        cx = (w["x0"] + w["x1"]) / 2
        for i, (a, b) in enumerate(bands):
            if a <= cx < b:
                return i
        return -1

    cols: dict[int, list[dict]] = defaultdict(list)
    for w in body:
        c = col_of(w)
        if c >= 0:
            cols[c].append(w)

    def cluster_rows(ws, ytol=6):
        ws = sorted(ws, key=lambda w: (w["top"], w["x0"]))
        rows, cur, cur_y = [], [], None
        for w in ws:
            y = (w["top"] + w["bottom"]) / 2
            if cur_y is None or abs(y - cur_y) <= ytol:
                cur.append(w)
                cur_y = y if cur_y is None else (cur_y * len(cur) + y) / (len(cur) + 1)
            else:
                rows.append(sorted(cur, key=lambda w: w["x0"]))
                cur, cur_y = [w], y
        if cur:
            rows.append(sorted(cur, key=lambda w: w["x0"]))
        return rows

    sequence: list[str] = []
    for col_i in range(len(bands)):
        for row in cluster_rows(cols[col_i]):
            sequence.append(" ".join(w["text"] for w in row).strip())

    # Structural noise: column-header labels. Project-name + "DRAWING LIST" page titles
    # are caught by the "DRAWING LIST" skip below rather than by exact string.
    HEADER_NOISE = {"SHEET", "NO.", "NO. SHEET NAME", "SHEET NAME", "SHEET NO."}
    sequence = [s for s in sequence if s and s not in HEADER_NOISE]

    # Sheet rows: support both "G-001 SOME TITLE" and "A01 - SOME TITLE" (dash optional)
    sheet_split_re = re.compile(
        r"^((?:[A-Z]{1,3}D?-[0-9]{1,4}(?:\.[0-9]+)?[A-Z]?)"   # G-001, A-100.2
        r"|(?:[A-Z]{1,3}[0-9]{2,4}[A-Z]?)"                      # A01, S100 (no dash)
        r"|(?:VT[0-9]{2}))"                                       # VT01
        r"\s*(?:-\s*)?(.+)$"                                      # optional dash separator, then title
    )

    rows_out: list[list[str]] = []
    current_disc: str | None = None
    last_idx = -1
    total_claimed: int | None = None

    for line in sequence:
        # Skip page-title or column-header lines that mention "DRAWING LIST" but aren't a sheet entry
        if "DRAWING LIST" in line.upper() and not sheet_split_re.match(line):
            continue

        # Detect the architect's footer "Total Number of Sheets: NNN"
        m_total = re.match(r"Total Number of Sheets:\s*(\d+)", line, re.IGNORECASE)
        if m_total:
            total_claimed = int(m_total.group(1))
            continue

        # Sheet row (checked before discipline header — a sheet line cannot be a header)
        m = sheet_split_re.match(line)
        if m:
            sn, raw_title = m.group(1), m.group(2).strip()
            # Split rows that contain a second embedded sheet-number token.
            # A page-margin annotation token (or any other stray word) that survives the
            # height filter and clusters with a sheet row will produce a line like:
            #   "A-500 UNIT MOUNTING HEIGHTS"  (correct first row)
            #   "STRAY A-501 KITCHEN PLANS"    (merged row — stray word at position 0)
            # When the merged line itself starts with a sheet number, sheet_split_re already
            # handles it correctly. The problem case is a NON-sheet-number prefix ("STRAY")
            # followed by a sheet number mid-title, which makes the whole line look like a
            # continuation. That case is caught below.
            # We also guard against a title that itself begins with a second sheet number
            # (no prefix noise survived), meaning two sheets were merged into one row.
            m2 = sheet_split_re.match(raw_title)
            if m2:
                # Title starts with another sheet number → the row is a merge of two printed
                # rows. Emit both rows; second row's title is whatever follows its number.
                print(
                    f"[warn] row merge detected: {sn!r} title starts with second sheet "
                    f"{m2.group(1)!r} — splitting into two rows",
                    file=sys.stderr,
                )
                rows_out.append([current_disc or "", sn, ""])
                rows_out.append([current_disc or "", m2.group(1), m2.group(2).strip()])
                last_idx = len(rows_out) - 1
            else:
                rows_out.append([current_disc or "", sn, raw_title])
                last_idx = len(rows_out) - 1
            continue

        # Continuation of previous sheet's title is checked BEFORE discipline header detection.
        # This handles single-word all-caps continuations (e.g. "ACCESS" wrapping from the
        # previous row) which would otherwise false-positive as a discipline header.
        # Multi-word continuations containing function words are also caught here.
        if last_idx >= 0 and not _is_discipline_header(line):
            # A stray prefix word (e.g. "MP") that survived the height filter can cluster
            # with the next sheet's row, producing a continuation-candidate like
            # "MP A-501 KITCHEN PLANS & ELEVATIONS". Detect this by scanning the
            # continuation candidate for an embedded sheet-number token; if found, split
            # there instead of appending to the prior row.
            _embedded = sheet_split_re.search(line)
            if _embedded and _embedded.start() > 0:
                # Something before the sheet number (the stray prefix) — emit as new row.
                print(
                    f"[warn] embedded sheet number in continuation: {_embedded.group(1)!r} "
                    f"in {line!r} — splitting as new row (prefix discarded)",
                    file=sys.stderr,
                )
                rows_out.append([current_disc or "", _embedded.group(1), _embedded.group(2).strip()])
                last_idx = len(rows_out) - 1
            else:
                rows_out[last_idx][2] = (rows_out[last_idx][2] + " " + line).strip()
            continue

        # Discipline section header — detected entirely from the document, no hardcoded names
        if _is_discipline_header(line):
            print(f"[info] discipline: {line}", file=sys.stderr)
            current_disc = line
            continue

        # Fallback continuation (e.g. mixed-case wrapped text when last_idx is set)
        if last_idx >= 0:
            rows_out[last_idx][2] = (rows_out[last_idx][2] + " " + line).strip()

    return [tuple(r) for r in rows_out], total_claimed


# ---------- title-block scan via pdftotext ----------

def page_sheet_no_from_text(page_text: str) -> str | None:
    """Find the title-block sheet number on a single page of pdftotext -layout output.

    Title-block sheet # is in big text at the bottom right — typically the rightmost
    token in the bottom 30% of non-empty lines."""
    lines = page_text.splitlines()
    nonempty = [(i, l) for i, l in enumerate(lines) if l.strip()]
    if not nonempty:
        return None
    cut = max(int(len(nonempty) * 0.70), len(nonempty) - 40)
    bottom = nonempty[cut:]
    candidates: list[tuple[int, int, str]] = []
    for i, l in bottom:
        for tok in l.split():
            if SHEET_RE.match(tok):
                candidates.append((i, l.rfind(tok), tok))
    if not candidates:
        return None
    # rightmost column wins; ties broken by depth from top (later wins)
    candidates.sort(key=lambda c: (-c[1], -c[0]))
    return candidates[0][2]


def pdftotext_pages(pdf_path: str) -> list[str]:
    out = subprocess.check_output(
        ["pdftotext", "-layout", pdf_path, "-"],
        text=True, encoding="utf-8", errors="replace",
        stderr=subprocess.DEVNULL,  # suppress poppler syntax-error noise
    )
    pages = out.split("\f")
    if pages and not pages[-1].strip():
        pages = pages[:-1]
    return pages


# ---------- reconciliation ----------

def reconcile(
    folder: str,
    listed_by_disc: "OrderedDict[str, list[tuple[str, str, str]]]",
    disc_to_pdf: dict[str, str],
) -> tuple[dict[str, tuple[str, int]], list[tuple[str, str, int, str]]]:
    """Return (sheet_to_loc, extras).

    sheet_to_loc: {sheet_no: (pdf_filename, 1-based page#)}
    extras:       list of (discipline, pdf_filename, page#, sheet_no) for unlisted sheets.
    """
    sheet_to_loc: dict[str, tuple[str, int]] = {}
    extras: list[tuple[str, str, int, str]] = []

    for disc, listed in listed_by_disc.items():
        pdf_name = disc_to_pdf.get(disc)
        if not pdf_name:
            print(f"[warn] {disc}: no PDF found — skipping", file=sys.stderr)
            continue
        fp = os.path.join(folder, pdf_name)
        listed_sheets = [r[1] for r in listed]
        # Count PDF pages (cheap: pdfplumber.open just parses xref)
        with pdfplumber.open(fp) as pdf:
            n_pages = len(pdf.pages)

        if len(listed_sheets) == n_pages:
            # Positional mapping. Trust list order = PDF order.
            for i, sn in enumerate(listed_sheets):
                sheet_to_loc[sn] = (pdf_name, i + 1)
            continue

        # Counts diverge — scan title blocks to locate listed sheets and identify extras.
        print(f"[info] {disc}: list={len(listed_sheets)} pdf={n_pages} — scanning title blocks", file=sys.stderr)
        pages_text = pdftotext_pages(fp)
        listed_set = set(listed_sheets)
        seen: set[str] = set()
        for i, page_text in enumerate(pages_text):
            sn = page_sheet_no_from_text(page_text)
            if sn and sn in listed_set and sn not in seen:
                sheet_to_loc[sn] = (pdf_name, i + 1)
                seen.add(sn)
            elif sn and sn not in listed_set:
                extras.append((disc, pdf_name, i + 1, sn))
        # If list count > PDF pages OR some listed sheet's title block wasn't readable,
        # fall back to positional for whatever remains.
        unfound = [sn for sn in listed_sheets if sn not in seen]
        if unfound and n_pages >= len(listed_sheets):
            extra_pages = {p for _, _, p, _ in extras if _ == disc}
            free_pages = [p for p in range(1, n_pages + 1)
                          if p not in extra_pages and (pdf_name, p) not in set(sheet_to_loc.values())]
            for sn, p in zip(unfound, free_pages):
                sheet_to_loc[sn] = (pdf_name, p)

    return sheet_to_loc, extras


# ---------- output ----------

def safe_write_csv(path: str, header: list[str], rows: Iterable[list[str]]) -> str:
    """Write CSV; if locked (Excel has it open), version it as v2/v3/...."""
    target = path
    base, ext = os.path.splitext(path)
    n = 2
    while True:
        try:
            with open(target, "w", newline="", encoding="utf-8") as f:
                w = csv.writer(f)
                w.writerow(header)
                w.writerows(rows)
            return target
        except PermissionError:
            target = f"{base} v{n}{ext}"
            n += 1


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("folder", help="Path to the 'Drawings by Discipline' folder.")
    ap.add_argument("--issue", default=None,
                    help="Issue label for the output filename (default: parent folder name).")
    args = ap.parse_args()

    folder = os.path.abspath(args.folder)
    if not os.path.isdir(folder):
        sys.exit(f"Not a directory: {folder}")

    # The input folder is `Drawings by Discipline`; the issue folder is its parent
    # (e.g. `2025-12-15 Conformed Set`); the output goes one level above that, alongside
    # the issue folder — same level as `drawing-index-bulletin` writes its CSV.
    issue_folder = os.path.dirname(folder.rstrip("/\\"))
    issue = args.issue or os.path.basename(issue_folder)
    out_dir = os.path.dirname(issue_folder)

    # Parse the drawing list first to discover what disciplines actually exist in this set,
    # then match those discipline names to PDFs. This keeps discipline names fully dynamic —
    # no hardcoded lists are needed.
    list_pdf, list_page_idx = find_drawing_list_pdf(folder)
    print(f"[info] parsing master list from {list_pdf} (page {list_page_idx + 1})", file=sys.stderr)
    with pdfplumber.open(os.path.join(folder, list_pdf)) as pdf:
        listed_rows, total_claimed = parse_drawing_list(pdf.pages[list_page_idx])

    # Group listed rows by discipline, preserving the architect's order
    listed_by_disc: "OrderedDict[str, list[tuple[str, str, str]]]" = OrderedDict()
    for r in listed_rows:
        listed_by_disc.setdefault(r[0], []).append(r)

    disciplines = list(listed_by_disc.keys())
    print(f"[info] master list: {len(listed_rows)} sheets across {len(disciplines)} disciplines"
          + (f" (master list claims {total_claimed})" if total_claimed else ""), file=sys.stderr)

    disc_to_pdf = match_disciplines_to_pdfs(folder, disciplines)

    sheet_to_loc, extras = reconcile(folder, listed_by_disc, disc_to_pdf)

    # Build output rows in master-list order
    out_rows: list[list[str]] = []
    for disc, rows in listed_by_disc.items():
        for r in rows:
            loc = sheet_to_loc.get(r[1], ("", ""))
            out_rows.append([r[0], r[1], r[2], loc[0], str(loc[1]) if loc[1] else ""])

    main_csv = os.path.join(out_dir, f"Drawing Index - {issue}.csv")
    written = safe_write_csv(
        main_csv,
        ["Discipline", "Sheet Number", "Page Title", "PDF File", "Page in PDF"],
        out_rows,
    )
    print(f"[ok] wrote {written}  ({len(out_rows)} rows)")

    if extras:
        anom_csv = os.path.join(out_dir, "Drawing Index - Unlisted Sheets.csv")
        anom_written = safe_write_csv(
            anom_csv,
            ["Discipline", "PDF File", "Page in PDF", "Sheet Number"],
            [[d, f, str(p), s] for d, f, p, s in extras],
        )
        print(f"[ok] wrote {anom_written}  ({len(extras)} unlisted sheets)")
    else:
        print("[ok] no anomalies — every PDF page mapped to a listed sheet")

    # Summary per discipline (stderr so it doesn't pollute scripted use)
    counts = Counter(r[0] for r in out_rows)
    print("\n[summary] sheets per discipline:", file=sys.stderr)
    for d in listed_by_disc:
        print(f"  {d:22s} {counts[d]}", file=sys.stderr)


if __name__ == "__main__":
    main()
