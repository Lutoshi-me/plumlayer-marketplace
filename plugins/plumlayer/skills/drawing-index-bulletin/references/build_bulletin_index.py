"""Build a per-issue Drawing Index CSV for a Bulletin / ASI / Addendum.

A Bulletin folder typically contains:
  - One combined drawings PDF (every revised sheet across all disciplines)
  - A Narrative of Changes PDF
  - A transmittal PDF
  - Optionally per-discipline narratives or specs

Usage:
    python build_bulletin_index.py <Bulletin folder>
    python build_bulletin_index.py <folder> --issue "2026-05-05 Bulletin 02"

Output: written to the parent of the Bulletin folder, alongside other Drawing Index CSVs.
  - Drawing Index - <issue>.csv
  - Drawing Index - <issue> - Narrative Mismatch.csv  (only if mismatches found)

See ../SKILL.md for the full design rationale.
"""

from __future__ import annotations

import argparse
import csv
import os
import re
import subprocess
import sys
from collections import Counter, defaultdict
from typing import Iterable

# Sheet # pattern — must match drawing-index's regex for downstream compatibility.
SHEET_RE = re.compile(r"^((?:[A-Z]{1,3}D?-[0-9]{1,4}(?:\.[0-9]+)?[A-Z]?)|(?:VT[0-9]{2})|(?:SKS-[0-9]+))$")

# Map sheet # prefix → discipline. Order matters: longer prefixes first.
PREFIX_TO_DISCIPLINE = [
    ("SKS-", "STRUCTURAL"),
    ("FPD-", "FIRE PROTECTION"),
    ("FP-",  "FIRE PROTECTION"),
    ("FA-",  "FIRE ALARM"),
    ("LS-",  "LIFE SAFETY"),
    ("HD-",  "HVAC"),
    ("ES-",  "SECURITY"),
    ("PD-",  "PLUMBING"),
    ("VT",   "ELEVATOR"),
    ("G-",   "GENERAL"),
    ("C-",   "CIVIL"),
    ("D-",   "ARCHITECTURAL DEMO"),
    ("A-",   "ARCHITECTURAL"),
    ("S-",   "STRUCTURAL"),
    ("P-",   "PLUMBING"),
    ("H-",   "HVAC"),
    ("E-",   "ELECTRICAL"),
    ("T-",   "TELECOMMUNICATIONS"),
]

def discipline_for(sheet_no: str) -> str:
    for prefix, disc in PREFIX_TO_DISCIPLINE:
        if sheet_no.startswith(prefix):
            return disc
    return "UNKNOWN"


# ---------- file discovery ----------

def find_pdfs(folder: str) -> dict[str, str]:
    """Return {role: filename} for the combined drawings PDF + narrative PDF.

    Heuristics:
      - drawings: filename contains 'drawings' (case-insensitive) OR is the largest PDF
                  that isn't the narrative/transmittal.
      - narrative: filename contains 'narrative' or 'changes' or 'summary'.
    """
    pdfs = [f for f in sorted(os.listdir(folder)) if f.lower().endswith(".pdf")]
    if not pdfs:
        raise RuntimeError(f"No PDFs found in {folder}")

    sizes = {f: os.path.getsize(os.path.join(folder, f)) for f in pdfs}

    narrative = next(
        (f for f in pdfs
         if any(kw in f.lower() for kw in ("narrative", "changes", "summary of"))),
        None,
    )
    transmittal = next((f for f in pdfs if "transmittal" in f.lower()), None)

    drawings = next(
        (f for f in pdfs if "drawing" in f.lower() and f != narrative),
        None,
    )
    if not drawings:
        # Fall back to largest non-narrative, non-transmittal PDF
        remaining = {f: s for f, s in sizes.items() if f not in {narrative, transmittal}}
        drawings = max(remaining, key=remaining.get) if remaining else None

    if not drawings:
        raise RuntimeError(f"Could not identify the combined drawings PDF in {folder}")

    return {"drawings": drawings, "narrative": narrative or "", "transmittal": transmittal or ""}


# ---------- pdftotext helpers ----------

def pdftotext_pages(pdf_path: str) -> list[str]:
    out = subprocess.check_output(
        ["pdftotext", "-layout", pdf_path, "-"],
        text=True, encoding="utf-8", errors="replace",
        stderr=subprocess.DEVNULL,
    )
    pages = out.split("\f")
    if pages and not pages[-1].strip():
        pages = pages[:-1]
    return pages


def pdftotext_full(pdf_path: str) -> str:
    return subprocess.check_output(
        ["pdftotext", "-layout", pdf_path, "-"],
        text=True, encoding="utf-8", errors="replace",
        stderr=subprocess.DEVNULL,
    )


# ---------- title-block extraction ----------

def page_sheet_no(page_text: str) -> str | None:
    """Find the title-block sheet # on a page of pdftotext -layout output.

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
    candidates.sort(key=lambda c: (-c[1], -c[0]))
    return candidates[0][2]


def page_sheet_title(page_text: str) -> str:
    """Find the sheet title block content. Title sits under a 'SHEET TITLE' anchor in the
    title block. Stitches up to ~4 lines below the anchor and to the right of x≈80% of width.
    Best-effort — leaves blank if extraction is ambiguous.
    """
    lines = page_text.splitlines()
    # locate 'SHEET TITLE' anchor (two words usually on adjacent lines or same line)
    title_idx = None
    for i in range(len(lines) - 1, -1, -1):
        u = lines[i].upper()
        if "SHEET" in u and "TITLE" in u:
            title_idx = i
            break
    if title_idx is None:
        return ""
    # Take next several lines that have alphabetic content and aren't obvious junk
    title_lines: list[str] = []
    for j in range(title_idx + 1, min(title_idx + 10, len(lines))):
        l = lines[j].strip()
        if not l:
            continue
        # Stop at the next title-block label (PROJECT NUMBER, DRAWN BY, etc.) or at the sheet #
        if any(kw in l.upper() for kw in (
            "PROJECT NUMBER", "DRAWN BY", "CHECKED BY", "SCALE", "DATE", "NORTH",
            "CONSULTANT", "STAMP", "ARCHITECT", "KEY PLAN", "REVISION",
        )):
            break
        if SHEET_RE.match(l.split()[-1] if l.split() else ""):
            break
        title_lines.append(l)
        if len(title_lines) >= 4:
            break
    # Best-effort: join, collapse whitespace
    return " ".join(title_lines).strip()


# ---------- narrative parsing ----------

# Match a "bulleted" line that names one or more sheet numbers, optionally as a range.
# Examples we want to match:
#   • A-100.2: Rotate shaft at basement per structural
#   • D-100 – D-101A: revisions to demo due to reconfigured stair layout
#   • A-110: revision to unit layouts per MEP coordination (A-108, A-112, A-114, A-116 SIM)
#   • A-820 – A-821: update replacement window details
#   • SKS-1 dated 03/19/2026 is indicated on S-101 and S-203
SHEET_TOK = r"(?:[A-Z]{1,3}D?-[0-9]{1,4}(?:\.[0-9]+)?[A-Z]?|VT[0-9]{2}|SKS-[0-9]+)"
SHEET_TOK_RE = re.compile(SHEET_TOK)


def _expand_range(a: str, b: str) -> list[str]:
    """Expand a sheet # range. Handles A-100..A-110, A-100.1..A-100.4, and the asymmetric
    case D-100..D-101A (include D-100, D-101, AND D-101A). Falls back to [a, b] if the
    expansion is too ambiguous."""
    m_a = re.match(r"^([A-Z]+-?)([0-9]+(?:\.[0-9]+)?)([A-Z]?)$", a)
    m_b = re.match(r"^([A-Z]+-?)([0-9]+(?:\.[0-9]+)?)([A-Z]?)$", b)
    if not (m_a and m_b) or m_a.group(1) != m_b.group(1):
        return [a, b]
    prefix = m_a.group(1)
    num_a, num_b, suf_a, suf_b = m_a.group(2), m_b.group(2), m_a.group(3), m_b.group(3)

    # Decimal range: 100.2..100.4 → .2 .3 .4 (integer parts must match)
    if "." in num_a and "." in num_b:
        int_a, dec_a = num_a.split(".")
        int_b, dec_b = num_b.split(".")
        if int_a == int_b and suf_a == suf_b:
            try:
                lo, hi = int(dec_a), int(dec_b)
                return [f"{prefix}{int_a}.{d}{suf_a}" for d in range(lo, hi + 1)]
            except ValueError:
                return [a, b]
        return [a, b]

    # Integer range. If suffixes match, straightforward. If asymmetric (D-100..D-101A),
    # emit each intermediate without suffix, then add the suffixed endpoint at the end.
    try:
        lo, hi = int(num_a), int(num_b)
    except ValueError:
        return [a, b]
    if suf_a == suf_b:
        return [f"{prefix}{n}{suf_a}" for n in range(lo, hi + 1)]
    if not suf_a and suf_b:
        return [f"{prefix}{n}" for n in range(lo, hi + 1)] + [f"{prefix}{hi}{suf_b}"]
    if suf_a and not suf_b:
        return [f"{prefix}{lo}{suf_a}"] + [f"{prefix}{n}" for n in range(lo, hi + 1)]
    return [a, b]


def parse_narrative(narrative_path: str) -> tuple[set[str], list[str], list[str]]:
    """Return (revised_sheets, deleted_sheets, spec_additions)."""
    if not narrative_path or not os.path.isfile(narrative_path):
        return set(), [], []

    text = pdftotext_full(narrative_path)
    revised: set[str] = set()
    deleted: list[str] = []
    specs: list[str] = []

    # Walk line-by-line. A "revision line" starts with one or more sheet #s (possibly
    # preceded by ANY non-word characters — bullets render as •, ·, *, -, U+FFFD).
    # Three shapes we recognize as the LEADING sheet list of a bullet line:
    #   1. SHEET: text                         → 1 sheet
    #   2. SHEET, SHEET, SHEET: text           → N sheets (comma-separated)
    #   3. SHEET DASH SHEET: text              → expanded range
    DASH = r"[–—\-�]"
    # A leading sheet list: one sheet, OR a comma list, OR a range. Tolerate stray spaces.
    LEADING = rf"({SHEET_TOK}(?:\s*,\s*{SHEET_TOK})*(?:\s*{DASH}\s*{SHEET_TOK})?)"
    # Strict ':' terminator — using '[:,]' here lets the regex backtrack and falsely match
    # mid-sentence comma lists like "(A-135, A-141, A-145, A-147 SIM)".
    bullet_re = re.compile(rf"^[^\w\n]*\s*{LEADING}\s*:\s*(.*)$")
    range_re = re.compile(rf"^({SHEET_TOK})\s*{DASH}\s*({SHEET_TOK})$")

    # Inline "(... SIM)" parentheticals = "applies by similarity," not separate revised
    # drawings. Strip before parsing so they don't inject false leading sheets.
    sim_paren_re = re.compile(r"\([^)]*\bSIM\b[^)]*\)", re.IGNORECASE)

    # Structural-sketch prose form: "SKS-X dated <date> is indicated on S-101 and S-203"
    # — the referenced sheets are revised (to add the callout).
    indicated_re = re.compile(
        rf"\b(SKS-[0-9]+)\b[^.]*?\bindicated on\b\s+([^.]+?)(?:\.|\s+per\s+|$)",
        re.IGNORECASE,
    )

    for raw in text.splitlines():
        line = raw.strip()
        if not line:
            continue

        # Spec section additions (logged, not added to revised set)
        m_spec = re.search(r"\bAdd(?:s)? section\s+([0-9]{6})\b(.*)", line, re.IGNORECASE)
        if m_spec:
            specs.append(f"{m_spec.group(1)}{m_spec.group(2)}".strip())
            continue

        line_clean = sim_paren_re.sub("", line)

        # "SKS-X is indicated on Y, Z" — the referenced sheets (S-101, S-203, etc.) are
        # revised to add the callout. The SKS sketch itself is a detail on those sheets,
        # NOT a standalone revised drawing, so we deliberately do NOT add SKS-X to revised.
        for m in indicated_re.finditer(line_clean):
            for s in SHEET_TOK_RE.findall(m.group(2)):
                revised.add(s)

        m = bullet_re.match(line_clean)
        if not m:
            continue
        leading, rest = m.group(1), m.group(2)

        # Parse the leading sheet list. It's either a range (DASH separator), a comma list,
        # or a single sheet. Range and comma are mutually exclusive in practice.
        sheets: list[str] = []
        if DASH[1:-1] in leading or any(d in leading for d in "–—-�"):
            r = range_re.match(leading)
            if r:
                sheets = _expand_range(r.group(1), r.group(2))
        if not sheets:
            sheets = [s.strip() for s in re.split(r"\s*,\s*", leading) if SHEET_RE.match(s.strip())]
        if not sheets:
            sheets = SHEET_TOK_RE.findall(leading)

        for s in sheets:
            if re.search(r"\bdelete\s+(sheet\s+)?" + re.escape(s) + r"\b", rest, re.IGNORECASE):
                deleted.append(s)
            revised.add(s)

    return revised, deleted, specs


# ---------- output ----------

def safe_write_csv(path: str, header: list[str], rows: Iterable[list[str]]) -> str:
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
    ap.add_argument("folder", help="Path to the Bulletin / ASI / Addendum folder.")
    ap.add_argument("--issue", default=None,
                    help="Issue label for the output filename (default: folder basename).")
    args = ap.parse_args()

    folder = os.path.abspath(args.folder)
    if not os.path.isdir(folder):
        sys.exit(f"Not a directory: {folder}")

    issue = args.issue or os.path.basename(folder.rstrip("/\\"))
    out_dir = os.path.dirname(folder.rstrip("/\\"))

    files = find_pdfs(folder)
    drawings_pdf = files["drawings"]
    narrative_pdf = files["narrative"]
    print(f"[info] drawings PDF: {drawings_pdf}", file=sys.stderr)
    print(f"[info] narrative PDF: {narrative_pdf or '(none found)'}", file=sys.stderr)

    pages_text = pdftotext_pages(os.path.join(folder, drawings_pdf))
    print(f"[info] {len(pages_text)} pages in combined drawings PDF", file=sys.stderr)

    out_rows: list[list[str]] = []
    pdf_sheets: set[str] = set()
    unreadable_pages: list[int] = []
    for i, ptxt in enumerate(pages_text):
        sn = page_sheet_no(ptxt)
        if not sn:
            unreadable_pages.append(i + 1)
            continue
        # Page Title intentionally left blank in Bulletin CSVs. The architect's title-block
        # text is mixed with body callouts in the pdftotext layout output, and bulk title
        # extraction would be lossy. The drawing-index-merge skill backfills titles from
        # the Conformed CSV (a sheet's title doesn't change between revisions).
        disc = discipline_for(sn)
        out_rows.append([disc, sn, "", drawings_pdf, str(i + 1)])
        pdf_sheets.add(sn)

    # Narrative cross-check
    narrative_sheets, deletions, specs = parse_narrative(
        os.path.join(folder, narrative_pdf) if narrative_pdf else ""
    )

    mismatches: list[list[str]] = []
    if narrative_pdf:
        only_in_narr = narrative_sheets - pdf_sheets - set(deletions)
        only_in_pdf = pdf_sheets - narrative_sheets
        for s in sorted(only_in_narr):
            mismatches.append([s, discipline_for(s), "narrative_only",
                               "Narrative claims sheet was revised; not present in combined PDF."])
        for s in sorted(only_in_pdf):
            # Don't flag SKS sketches as missing from the narrative — they're often inline
            mismatches.append([s, discipline_for(s), "pdf_only",
                               "Sheet appears in combined PDF; not listed in Narrative of Changes."])

    # Write main CSV
    main_csv = os.path.join(out_dir, f"Drawing Index - {issue}.csv")
    written = safe_write_csv(
        main_csv,
        ["Discipline", "Sheet Number", "Page Title", "PDF File", "Page in PDF"],
        out_rows,
    )
    print(f"[ok] wrote {written}  ({len(out_rows)} rows)")

    if mismatches:
        mm_csv = os.path.join(out_dir, f"Drawing Index - {issue} - Narrative Mismatch.csv")
        mm_written = safe_write_csv(
            mm_csv,
            ["Sheet Number", "Discipline", "Type", "Note"],
            mismatches,
        )
        print(f"[ok] wrote {mm_written}  ({len(mismatches)} mismatches — review for RFI)")
    else:
        print("[ok] no narrative mismatches" if narrative_pdf else "[warn] no narrative available — cross-check skipped")

    if specs:
        print(f"[info] spec additions noted in narrative (NOT in CSV):", file=sys.stderr)
        for s in specs:
            print(f"  - {s}", file=sys.stderr)

    if unreadable_pages:
        print(f"[warn] {len(unreadable_pages)} pages had no readable sheet # in title block:",
              file=sys.stderr)
        print(f"  pages {unreadable_pages}", file=sys.stderr)

    counts = Counter(r[0] for r in out_rows)
    print("\n[summary] sheets per discipline:", file=sys.stderr)
    for disc in sorted(counts):
        print(f"  {disc:22s} {counts[disc]}", file=sys.stderr)


if __name__ == "__main__":
    main()
