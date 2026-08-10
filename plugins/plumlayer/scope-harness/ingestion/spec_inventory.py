"""
spec_inventory.py -- deterministic spec-section skeleton extractor.

The spec analog of sheet_inventory.py (the drawing-side foundation-pass tool).
Reads a project manual PDF, or a folder of per-division PDFs, and emits one
grounded project record skeleton per CSI spec section (specSection:<6-digit-packed>):

  hasTitle       the section title ("Gypsum Board Assemblies")
  locatedAt      where the section lives in the manual: {instrument, pageStart, pageEnd}
  inDivision     the CSI division ("09")   [derived from the key]
  partOfIssue    the manual's version scope {label}

Paradigm (project-north-star.md, spec-ingestion-design.md):
  * deterministic GROUNDS -- the per-page section-ID footer is PRIMARY (every
    page self-labels "<6-digit-code> - <page-within-section>"); the PDF bookmark
    tree and the text TOC are corroborating instruments.
  * Footer primary, bookmark/TOC corroborate -- three-signal agreement raises
    confidence; disagreements surface as proposed completeness findings (never
    silently dropped).
  * Title is extracted from the section's internal-page-1 by CONTENT PATTERN:
    find the "SECTION <code>" line; the next non-empty, non-code line is the
    title. All three corpus manuals use uniform 10pt type -- no font-size
    localization applies here. Falls back to the bookmark title (proposed tier).
  * Residue cascade (minimal, honest): a footer region with NO text emits a
    proposed specSection:unknown-pg<N> so no page is silently dropped. None of
    the three validated fixtures (31 Milk, 150 Main, 248 Dorchester) need OCR;
    the cascade is present so a worse manual surfaces residue, not silence.
  * Trust tiers:
      footer + bookmark agree, title from header   --> authoritative, conf 0.95
      footer only, title from header               --> authoritative, conf 0.90
      footer + bookmark agree, title from bookmark --> authoritative, conf 0.90
                                                       (locatedAt); proposed,
                                                       conf 0.80 (hasTitle)
      bookmark only (not in footer)                --> proposed, conf 0.75
      completeness diff findings                   --> proposed, conf 0.60

Packaging-agnostic: combined manual (single PDF) and per-division folder (N
PDFs) produce the same claim set. Use INGEST_PDF for a single PDF; use
INGEST_SPEC_DIR for a folder and the script unions across all PDFs found.

Confidential: writes only to INGEST_OUT_DIR (default ./output/, gitignored).
PyMuPDF + stdlib. ASCII-safe output.

PLU-968: vendored verbatim from the marketplace reference
(plugins/plumlayer/scope-harness/ingestion/spec_inventory.py) with exactly two
additive changes, both marked PLU-968 inline below: (1) the dead
emit_unknown_page_claim call is wired up so a no-footer page actually emits a
durable residue claim instead of silently vanishing; (2) a
spec_inventory_summary.json sidecar is written next to the claims jsonl, the
same structured-run-summary contract sheet_inventory.py already carries, so
the server-side extract_spec_toc worker function reads structured data
instead of scraping stdout. Everything else -- parse regexes, the trust
ladder, the completeness diff, title extraction -- is ported verbatim.

Run (combined manual):
  INGEST_PDF=".../Project Manual.pdf" \\
  INGEST_SET_TAG="31-milk-conformed" \\
  INGEST_REVISION="31 Milk Conformed 2025-12-15" \\
  INGEST_OUT_DIR=~/dev/plumlayer-private/spec-inventory-output/31-milk-combined \\
  python spec_inventory.py

Run (per-section folder -- union of all PDFs in the directory):
  INGEST_SPEC_DIR=".../spec-sections/" \\
  INGEST_SET_TAG="31-milk-conformed" \\
  INGEST_REVISION="31 Milk Conformed 2025-12-15" \\
  INGEST_OUT_DIR=~/dev/plumlayer-private/spec-inventory-output/31-milk-folder \\
  python spec_inventory.py
"""
import json
import os
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

try:
    import fitz  # PyMuPDF
except ImportError:
    sys.exit("[error] PyMuPDF (fitz) not installed -- pip install pymupdf")

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

# ---------------------------------------------------------------------------
# Environment
# ---------------------------------------------------------------------------

PDF_PATH = os.environ.get("INGEST_PDF")
SPEC_DIR = os.environ.get("INGEST_SPEC_DIR")
SET_TAG = os.environ.get("INGEST_SET_TAG", "SET")
REVISION = os.environ.get("INGEST_REVISION", "unspecified")
OUT_DIR = os.environ.get("INGEST_OUT_DIR") or os.path.join(os.getcwd(), "output")

if not PDF_PATH and not SPEC_DIR:
    sys.exit(
        "[error] set INGEST_PDF (path to a single PDF) or INGEST_SPEC_DIR "
        "(directory of per-division PDFs) -- no default"
    )

# ---------------------------------------------------------------------------
# Regex patterns
# ---------------------------------------------------------------------------

# Footer: "<6-digit-packed> - <page-within-section>"
# e.g. "011000 - 15" or "092116-3" or "011000 -1"
FOOTER_CSI_RE = re.compile(r"\b(\d{6})\s*[-]\s*(\d{1,4})\b")

# CSI 6-digit code -- used for bookmark/TOC extraction (no strict word boundary
# after digits; titles run code straight into hyphen, e.g. "011000-general").
CSI_LEAD_RE = re.compile(r"(\d{6})")

# "SECTION 011000" header pattern on the section's first page.
# Handles "SECTION 011000", "SECTION 01 10 00", "Section 011000".
SECTION_HDR_RE = re.compile(r"SECTION\s+(\d[\d\s]{4,8})", re.IGNORECASE)

# Minimum SECTION-keyword density to classify a page as a TOC page.
TOC_SECTION_THRESHOLD = 4

# Bottom fraction of page height used as "footer region".
FOOTER_FRAC = 0.80  # below 80% of page height

# Top fraction used for title header search.
HEADER_FRAC = 0.40  # above 40% of page height


# ---------------------------------------------------------------------------
# CSI key normalisation
# ---------------------------------------------------------------------------

def canon_csi(raw: str) -> str:
    """Strip whitespace; verify exactly 6 ASCII digits; return packed string.

    Raises ValueError if the result is not exactly 6 digits. This is the
    identity gate -- malformed codes never become subjects.
    """
    packed = re.sub(r"\s+", "", raw.strip())
    if not re.fullmatch(r"\d{6}", packed):
        raise ValueError(f"not a valid 6-digit CSI code: {raw!r}")
    return packed


def division_of(csi: str) -> str:
    """First two digits of a packed CSI code -- the division."""
    return csi[:2]


# ---------------------------------------------------------------------------
# Page text helpers
# ---------------------------------------------------------------------------

def _page_spans(page):
    """All text spans from a page as list of {text, size, cy, bbox, page_idx}.

    Returns spans in document order (top-to-bottom within blocks/lines).
    cy is normalised (0=top, 1=bottom) relative to the page height.
    """
    r = page.rect
    H = r.height
    out = []
    d = page.get_text("dict")
    for blk in d.get("blocks", []):
        for line in blk.get("lines", []):
            for sp in line.get("spans", []):
                t = sp["text"].strip()
                if not t:
                    continue
                bb = sp["bbox"]  # (x0, y0, x1, y1) in page points
                cy = ((bb[1] + bb[3]) / 2) / H if H > 0 else 0.0
                out.append({
                    "text": t,
                    "size": round(sp["size"], 2),
                    "cy": cy,
                    "bbox": [round(v, 2) for v in bb],
                })
    return out


def _footer_text_and_bbox(page):
    """Text + (first-span bbox) from the bottom FOOTER_FRAC of the page."""
    spans = _page_spans(page)
    footer_spans = [s for s in spans if s["cy"] >= FOOTER_FRAC]
    text = " ".join(s["text"] for s in footer_spans)
    bbox = footer_spans[0]["bbox"] if footer_spans else None
    return text, bbox


def _header_spans(page):
    """All spans from the top HEADER_FRAC of the page, in document order."""
    return [s for s in _page_spans(page) if s["cy"] < HEADER_FRAC]


# ---------------------------------------------------------------------------
# Footer scan -- the primary signal
# ---------------------------------------------------------------------------

class SectionEntry:
    """Accumulated page-range and evidence for one spec section."""

    __slots__ = (
        "csi", "first_page", "last_page",
        "internal_page_1_idx",     # PDF page index of internal page 1
        "first_page_bbox",         # footer bbox on first_page (for evidence)
        "page_count",
        "source_pdf",              # label of the PDF file (for multi-PDF mode)
        "_title",                  # title string from section header page (or None)
        "_title_bbox",             # bbox of title span (or None)
        "_header_csi",             # CSI code found in header (may differ from footer)
    )

    def __init__(self, csi: str, first_page: int, footer_bbox, source_pdf: str):
        self.csi = csi
        self.first_page = first_page
        self.last_page = first_page
        self.internal_page_1_idx = None
        self.first_page_bbox = footer_bbox
        self.page_count = 1
        self.source_pdf = source_pdf
        self._title = None
        self._title_bbox = None
        self._header_csi = None   # set when header has a different CSI than footer

    def extend(self, page_idx: int):
        self.last_page = page_idx
        self.page_count += 1


def scan_pdf_footers(doc, source_pdf_label: str) -> dict:
    """Scan all pages of a PDF for the section-ID footer.

    Returns:
        section_map: {csi_code: SectionEntry}
        no_footer_pages: list of PDF page indices that had NO footer CSI code
                         and had text content (residue candidates)
        image_only_pages: list of indices with empty text layer (OCR candidates)
    """
    section_map = {}
    no_footer_pages = []     # text present but no footer CSI code
    image_only_pages = []    # no text at all

    # Track current section to detect page-range continuity
    prev_code = None

    for i in range(doc.page_count):
        page = doc[i]
        footer_text, footer_bbox = _footer_text_and_bbox(page)

        # Check if page has any text at all
        full_text = page.get_text("text").strip()
        if not full_text:
            image_only_pages.append(i)
            continue

        m = FOOTER_CSI_RE.search(footer_text)
        if not m:
            no_footer_pages.append(i)
            prev_code = None
            continue

        raw_code = m.group(1)
        internal_pg = int(m.group(2))

        try:
            csi = canon_csi(raw_code)
        except ValueError:
            no_footer_pages.append(i)
            continue

        if csi not in section_map:
            entry = SectionEntry(csi, i, footer_bbox, source_pdf_label)
            section_map[csi] = entry
        else:
            section_map[csi].extend(i)

        # Record the PDF page index where this section's internal page 1 lives
        if internal_pg == 1:
            section_map[csi].internal_page_1_idx = i

        prev_code = csi

    return section_map, no_footer_pages, image_only_pages


# ---------------------------------------------------------------------------
# Bookmark corroboration
# ---------------------------------------------------------------------------

def bookmark_sections(toc: list) -> dict:
    """Extract {csi_code: title_string} from a bookmark tree.

    The PDF bookmark format across the corpus:
      "011000-general requirements"       (31 Milk / 248 Dorchester)
      "011000 - General Requirements"     (150 Main)
      "000110 -TABLE OF CONTENTS"         (248 Dorchester, with leading space)

    Strategy: find any bookmark entry whose title begins with a 6-digit code
    (with optional surrounding whitespace), split off the code, normalise the
    remainder as the title. Entries at ANY level are considered -- 31 Milk has
    section entries at L1, 150 Main at L3.
    """
    result = {}
    for _level, title, _page in toc:
        m = CSI_LEAD_RE.search(title.replace(" ", "")[:8])  # code is always near start
        if not m:
            continue
        raw = m.group(1)
        try:
            csi = canon_csi(raw)
        except ValueError:
            continue
        # Strip the CSI code + delimiter from the title
        remainder = re.sub(r"^\s*\d{6}\s*[-\s]*", "", title, count=1).strip()
        # Normalise: title-case, strip trailing parenthetical (corpus-specific suffixes)
        remainder = re.sub(r"\s*\([^)]+\)\s*$", "", remainder).strip()
        if remainder and csi not in result:
            result[csi] = remainder.title()
    return result


# ---------------------------------------------------------------------------
# Title extraction from section header page
# ---------------------------------------------------------------------------

def extract_section_title(doc, page_idx: int, csi: str):
    """Find the section title on the section's internal-page-1.

    The corpus pattern (confirmed on 31 Milk, 150 Main, 248 Dorchester):
      Line N:   "SECTION 011000"   (or "SECTION 01 10 00")
      Line N+1: "GENERAL REQUIREMENTS"

    All text is uniform 10pt -- no font-size signal. Title is the next
    non-empty, non-code line after "SECTION <code>".

    Pass 1: look for the exact footer CSI code in the header (canonical match).
    Pass 2: if pass 1 fails, look for ANY SECTION header -- some sections have a
    footer code that differs from the body code (edition-mismatch data quality
    issue; e.g. footer=061000 but body says "SECTION 061050"). Return the title
    together with the code actually found in the body so the caller can surface
    the mismatch as a proposed finding.

    Returns (title_str, title_bbox, found_csi) where found_csi == csi for an
    exact match or found_csi != csi for a mismatch.  All three are None when no
    SECTION header is found at all.
    """
    if page_idx is None or page_idx >= doc.page_count:
        return None, None, None

    page = doc[page_idx]
    spans = _header_spans(page)

    def _next_title(spans_list, after_idx):
        """Return (title, bbox) from the span immediately after after_idx."""
        for sp in spans_list[after_idx + 1:]:
            t = sp["text"].strip()
            if not t:
                continue
            if SECTION_HDR_RE.search(t):
                break   # another SECTION ref -- ambiguous, bail
            if re.fullmatch(r"\d[\d\s.]+", t):
                continue  # pure numeric (subsection number) -- skip
            if len(t) < 3:
                continue
            return t, sp["bbox"]
        return None, None

    # Pass 1: exact code match
    for i, sp in enumerate(spans):
        m = SECTION_HDR_RE.search(sp["text"])
        if m:
            try:
                if canon_csi(m.group(1)) == csi:
                    title, bbox = _next_title(spans, i)
                    return title, bbox, csi   # found_csi == csi: clean match
            except ValueError:
                pass

    # Pass 2: any SECTION header -- edition-mismatch or unexpected format.
    # IMPORTANT: restrict to spans in the top 20% of the page (cy < 0.20).
    # Real section headers appear at cy ~0.10-0.15; TOC-body references to
    # other sections appear throughout the page and would give the wrong title
    # (e.g. the TOC section 000110's pages list "SECTION 011000" in the body,
    # so an unrestricted pass 2 assigns 011000's title to the TOC section).
    TOP_FRAC_P2 = 0.20
    top_spans = [s for s in spans if s["cy"] < TOP_FRAC_P2]
    for i, sp in enumerate(top_spans):
        m = SECTION_HDR_RE.search(sp["text"])
        if m:
            try:
                found_csi = canon_csi(m.group(1))
                title, bbox = _next_title(top_spans, i)
                return title, bbox, found_csi   # found_csi != csi: mismatch
            except ValueError:
                pass

    return None, None, None


# ---------------------------------------------------------------------------
# TOC section extraction (corroboration)
# ---------------------------------------------------------------------------

def toc_page_sections(doc) -> set:
    """Collect CSI codes appearing on dense-SECTION-reference pages (the TOC).

    A page is treated as a TOC page when it contains >= TOC_SECTION_THRESHOLD
    "SECTION <code>" references. Returns a set of packed CSI codes.
    """
    codes = set()
    for i in range(doc.page_count):
        text = doc[i].get_text("text")
        matches = SECTION_HDR_RE.findall(text)
        if len(matches) >= TOC_SECTION_THRESHOLD:
            for raw in matches:
                try:
                    codes.add(canon_csi(raw))
                except ValueError:
                    pass
    return codes


# ---------------------------------------------------------------------------
# Claim builder
# ---------------------------------------------------------------------------

def _make_claim(
    subject: str,
    predicate: str,
    value,
    method: str,
    conf: float,
    trust: str,
    evidence_source: str,
    evidence_locator,
    snippet: str,
) -> dict:
    """Build a project record claim dict in the canonical shape."""
    ev: dict = {
        "source": evidence_source,
        "method": method,
        "snippet": snippet,
    }
    if evidence_locator is not None:
        ev["locator"] = {"frame": "page-points", "bboxPts": evidence_locator}
    return {
        "subject": subject,
        "predicate": predicate,
        "value": value,
        "evidence": [ev],
        "trustClass": trust,
        "confidence": round(conf, 2),
        "status": "current",
        "assertedBy": "spec_inventory.py",
        "promotedBy": None,
    }


def emit_section_claims(
    entry: "SectionEntry",
    conf_located: float,
    title: str | None,
    title_bbox,
    title_method: str,
    title_conf: float,
    title_trust: str,
    folder_mode: bool = False,
) -> list:
    """Emit all skeleton claims for one section."""
    csi = entry.csi
    subj = f"specSection:{csi}"
    # In folder mode the instrument names the specific source PDF so the page
    # numbers in locatedAt resolve to the right file; in single-PDF mode the
    # SET_TAG covers the whole manual.
    instrument = f"{SET_TAG}/{entry.source_pdf}" if folder_mode else SET_TAG
    source_ref = f"{SET_TAG}/pg{entry.first_page}"
    trust_located = "authoritative" if conf_located >= 0.88 else "proposed"
    loc_evidence_locator = entry.first_page_bbox

    claims = []

    # 1. locatedAt
    claims.append(_make_claim(
        subject=subj,
        predicate="locatedAt",
        value={"instrument": instrument,
               "pageStart": entry.first_page,
               "pageEnd": entry.last_page},
        method="spec-parse",
        conf=conf_located,
        trust=trust_located,
        evidence_source=source_ref,
        evidence_locator=loc_evidence_locator,
        snippet=f"{csi} pages {entry.first_page}-{entry.last_page}",
    ))

    # 2. hasTitle
    if title:
        claims.append(_make_claim(
            subject=subj,
            predicate="hasTitle",
            value=title,
            method=title_method,
            conf=title_conf,
            trust=title_trust,
            evidence_source=source_ref,
            evidence_locator=title_bbox,
            snippet=title[:80],
        ))

    # 3. inDivision (derived from the CSI key -- deterministic, no new read)
    div = division_of(csi)
    claims.append(_make_claim(
        subject=subj,
        predicate="inDivision",
        value=div,
        method="derived-from-csi",
        conf=0.99,
        trust="derived",
        evidence_source=source_ref,
        evidence_locator=None,
        snippet=csi,
    ))

    # 4. partOfIssue (from INGEST_REVISION -- caller-supplied, not read off cover)
    claims.append(_make_claim(
        subject=subj,
        predicate="partOfIssue",
        value={"label": REVISION},
        method="user-asserted",
        conf=0.90,
        trust=trust_located,  # trust mirrors the location claim
        evidence_source="user-supplied",
        evidence_locator=None,
        snippet=REVISION,
    ))

    return claims


def emit_completeness_claim(csi: str, status: str, source_ref: str) -> dict:
    """Proposed completeness finding: section declared in one instrument but not
    found in the other. Never silently dropped; surfaced for human review."""
    return _make_claim(
        subject=f"specSection:{csi}",
        predicate="hasCompletenessStatus",
        value=status,
        method="spec-parse-diff",
        conf=0.60,
        trust="proposed",
        evidence_source=source_ref,
        evidence_locator=None,
        snippet=f"{csi} {status}",
    )


def emit_unknown_page_claim(page_idx: int) -> dict:
    """Residue: text present but no footer CSI code. Never silently dropped."""
    return _make_claim(
        subject=f"specSection:unknown-pg{page_idx}",
        predicate="hasCompletenessStatus",
        value="footer-unresolved",
        method="spec-parse-residue",
        conf=0.30,
        trust="proposed",
        evidence_source=f"{SET_TAG}/pg{page_idx}",
        evidence_locator=None,
        snippet=f"page {page_idx} had text but no footer CSI code",
    )


# ---------------------------------------------------------------------------
# Multi-PDF folder support
# ---------------------------------------------------------------------------

def collect_pdfs(spec_dir: str) -> list:
    """Return sorted list of PDF paths in a directory (case-insensitive dedup)."""
    p = Path(spec_dir)
    if not p.is_dir():
        sys.exit(f"[error] INGEST_SPEC_DIR is not a directory: {spec_dir}")
    # On Windows the filesystem is case-insensitive; glob("*.pdf") + glob("*.PDF")
    # would return the same files twice. Deduplicate via resolved lower-cased stem.
    seen = set()
    pdfs = []
    for candidate in sorted(p.iterdir()):
        if candidate.suffix.lower() == ".pdf" and candidate.is_file():
            key = candidate.resolve()
            if key not in seen:
                seen.add(key)
                pdfs.append(candidate)
    if not pdfs:
        sys.exit(f"[error] no PDF files found in {spec_dir}")
    return pdfs


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    # ── Collect PDFs ──────────────────────────────────────────────────────────
    folder_mode = bool(SPEC_DIR)
    if folder_mode:
        pdf_paths = collect_pdfs(SPEC_DIR)
        mode_label = f"FOLDER ({len(pdf_paths)} PDFs)"
    else:
        pdf_paths = [Path(PDF_PATH)]
        mode_label = "SINGLE PDF"

    print("=" * 100)
    print(f"SPEC INVENTORY  |  {SET_TAG}  |  revision: {REVISION}  |  mode: {mode_label}")
    print("-" * 100)

    # ── Scan all PDFs ─────────────────────────────────────────────────────────
    # Merged across all PDFs in folder mode
    merged_sections: dict = {}       # csi -> SectionEntry (first seen wins for p1 idx)
    all_no_footer: list = []         # (pdf_label, page_idx)
    all_image_only: list = []
    all_toc_codes: set = set()
    all_bm_sections: dict = {}       # csi -> title (first seen wins)
    total_pages = 0

    # PLU-968 follow-up: an unreadable source file must never be invisible in a
    # successful result. files_requested/files_opened/files_failed are the honest
    # per-file accounting the caller (extract_spec_toc) reads back -- a zero-open
    # run (every source file unreadable) is the caller's signal to fail loudly
    # instead of depositing a fabricated zero-section success.
    files_requested = len(pdf_paths)
    files_opened = 0
    files_failed: list = []   # [{"file": pdf_label, "error": str}]

    for pdf_path in pdf_paths:
        pdf_label = pdf_path.name
        try:
            doc = fitz.open(str(pdf_path))
        except Exception as e:
            err_text = str(e)
            print(f"  [WARN] could not open {pdf_label}: {err_text}")
            # Also to stderr: a skipped file must show in Railway logs even on an
            # otherwise-clean run (stdout alone is easy to miss when the run
            # "succeeds").
            sys.stderr.write(f"[spec_inventory] WARN: could not open {pdf_label}: {err_text}\n")
            files_failed.append({"file": pdf_label, "error": err_text})
            continue

        files_opened += 1
        total_pages += doc.page_count

        # Footer scan (primary)
        sec_map, no_footer, image_only = scan_pdf_footers(doc, pdf_label)

        for csi, entry in sec_map.items():
            if csi not in merged_sections:
                merged_sections[csi] = entry
            else:
                # Extend the existing entry's page range (folder mode: a code
                # should only appear in ONE division PDF; warn if it appears in two)
                existing = merged_sections[csi]
                if folder_mode and existing.source_pdf != pdf_label:
                    print(f"  [WARN] section {csi} appears in both "
                          f"{existing.source_pdf} and {pdf_label} -- using first")
                else:
                    existing.extend(entry.last_page)

        all_no_footer.extend((pdf_label, pg) for pg in no_footer)
        all_image_only.extend((pdf_label, pg) for pg in image_only)

        # Bookmark corroboration
        toc = doc.get_toc()
        bm = bookmark_sections(toc)
        for csi, title in bm.items():
            if csi not in all_bm_sections:
                all_bm_sections[csi] = title

        # TOC page corroboration
        all_toc_codes |= toc_page_sections(doc)

        # Title extraction (needs the doc open -- do it now per-PDF)
        for csi, entry in sec_map.items():
            if entry.internal_page_1_idx is not None:
                title, bbox, found_csi = extract_section_title(
                    doc, entry.internal_page_1_idx, csi)
                if title and entry._title is None:
                    entry._title = title
                    entry._title_bbox = bbox
                    # Record when the header has a different code than the footer
                    if found_csi and found_csi != csi:
                        entry._header_csi = found_csi

        doc.close()

    # ── Compute confidence and corroboration ──────────────────────────────────
    footer_codes = set(merged_sections.keys())
    bm_codes = set(all_bm_sections.keys())
    toc_codes = all_toc_codes

    agree = footer_codes & bm_codes           # footer AND bookmark
    footer_only = footer_codes - bm_codes     # in PDF body, not in bookmark
    bm_only = bm_codes - footer_codes         # declared in bookmark, not in footer

    # ── Build claims ──────────────────────────────────────────────────────────
    claims_out: list = []
    sections_titled = 0
    sections_no_title = []
    title_from_header = 0
    title_from_bm = 0

    for csi in sorted(merged_sections.keys()):
        entry = merged_sections[csi]
        corroborated = csi in agree

        # locatedAt confidence
        conf_located = 0.95 if corroborated else 0.90

        # Title resolution
        title = getattr(entry, "_title", None)
        title_bbox = getattr(entry, "_title_bbox", None)

        if title:
            # Title found on the section header page -- authoritative grounding
            title_method = "spec-parse"
            title_conf = 0.95 if corroborated else 0.90
            title_trust = "authoritative"
            title_from_header += 1
            sections_titled += 1
        elif csi in all_bm_sections:
            # Title from bookmark only -- single instrument, proposed
            title = all_bm_sections[csi]
            title_method = "spec-parse-bookmark"
            title_conf = 0.80
            title_trust = "proposed"
            title_from_bm += 1
            sections_titled += 1
        else:
            # No title found
            title = None
            title_method = ""
            title_conf = 0.0
            title_trust = "proposed"
            sections_no_title.append(csi)

        new_claims = emit_section_claims(
            entry, conf_located, title, title_bbox,
            title_method, title_conf, title_trust,
            folder_mode=folder_mode,
        )
        claims_out.extend(new_claims)

    # ── Completeness diff claims (proposed) ───────────────────────────────────
    # Only emit when at least one corroborating instrument (bookmark tree or
    # text TOC) is present in the scanned set. In per-division folder mode the
    # individual PDFs typically carry no cross-section bookmark tree, so the
    # entire section set appears as "footer-only" -- that is a vacuous finding,
    # not a real completeness concern. Suppress to avoid false positives.
    source_ref = f"{SET_TAG}/toc"
    completeness_claims = 0
    # Completeness diffs require a COMBINED-MANUAL bookmark tree that covers all
    # sections. In folder mode each individual PDF's bookmark tree covers only
    # its own division; "footer section not in bookmark" is vacuous there and
    # generates false positives for every section. Suppress in folder mode.
    if not folder_mode:
        for csi in sorted(footer_only):
            claims_out.append(emit_completeness_claim(csi, "found-not-declared", source_ref))
            completeness_claims += 1
        for csi in sorted(bm_only):
            claims_out.append(emit_completeness_claim(csi, "declared-not-found", source_ref))
            completeness_claims += 1
    else:
        print("  (folder mode -- completeness diff suppressed; each PDF covers "
              "only its own division, not the full manual)")

    # ── Section-number mismatch findings (proposed) ──────────────────────────
    # Footer says code X but the section header body says "SECTION Y".  This is
    # a data quality issue in the spec (edition mismatch / tagging error). We
    # emit a proposed finding so it surfaces for review rather than being silent.
    mismatch_claims = 0
    mismatch_sections = []
    for csi, entry in sorted(merged_sections.items()):
        if entry._header_csi and entry._header_csi != csi:
            claims_out.append(_make_claim(
                subject=f"specSection:{csi}",
                predicate="hasCompletenessStatus",
                value=f"footer-header-code-mismatch:{entry._header_csi}",
                method="spec-parse-diff",
                conf=0.60,
                trust="proposed",
                evidence_source=f"{SET_TAG}/pg{entry.internal_page_1_idx}",
                evidence_locator=None,
                snippet=f"footer={csi} header={entry._header_csi}",
            ))
            mismatch_claims += 1
            mismatch_sections.append((csi, entry._header_csi))

    # ── Residue: no-footer pages (never silently dropped) ────────────────────
    # Only emit for non-trivial pages (not blank) -- image_only pages have
    # no text and are expected dividers/tabs, so we count but don't emit claims.
    # no_footer pages had text but no recognisable section code -- these are
    # TOC pages, cover pages, or potential OCR residue.
    residue_claims = 0
    for pdf_label, pg in all_no_footer:
        # PLU-968: the dead residue path, wired up. emit_unknown_page_claim was
        # defined above but this loop was a bare `pass` -- a no-footer page
        # (text present, no recognisable section code: a TOC page, a cover
        # page, or genuine residue) vanished from the durable claim set
        # entirely. Every scanned page must be attributed to a section OR
        # surfaced as residue; this is the surfacing. NOTE: in folder mode the
        # emitted subject (specSection:unknown-pg<N>, unchanged from the
        # reference) is keyed on the PDF-local page index only, not
        # (pdf_label, page index) -- see the PLU-968 report for the resulting
        # cross-PDF collision class this inherits from the reference design.
        claims_out.append(emit_unknown_page_claim(pg))
        residue_claims += 1

    # ── Print per-section table ───────────────────────────────────────────────
    div_dist = Counter(division_of(csi) for csi in merged_sections)
    print(f"{'CSI':8}  {'Div':3}  {'Pg0':5}  {'PgN':5}  {'Pgs':4}  "
          f"{'Crb':3}  {'Title source':16}  Title (first 48 chars)")
    print("-" * 100)
    for csi in sorted(merged_sections.keys()):
        entry = merged_sections[csi]
        corr_mark = "Y" if csi in agree else (" " if csi in footer_only else "BM")
        title_txt = getattr(entry, "_title", None) or all_bm_sections.get(csi) or "--"
        title_src = ("header" if getattr(entry, "_title", None) else
                     ("bookmark" if csi in all_bm_sections else "MISSING"))
        print(f"{csi:8}  {division_of(csi):3}  {entry.first_page:5d}  "
              f"{entry.last_page:5d}  {entry.last_page - entry.first_page + 1:4d}  "
              f"{corr_mark:3}  {title_src:16}  {title_txt[:48]}")

    # ── Summary ───────────────────────────────────────────────────────────────
    print("=" * 100)
    print(f"files opened .................. {files_opened}/{files_requested}"
          + (f"  (failed: {[f['file'] for f in files_failed]})" if files_failed else ""))
    print(f"total pages scanned .......... {total_pages}")
    print(f"sections found (footer) ...... {len(footer_codes)}")
    print(f"  corroborated by bookmark ... {len(agree)}  (footer AND bookmark)")
    print(f"  footer only ................ {len(footer_only)}  (in PDF, not in bookmark)")
    print(f"  bookmark only .............. {len(bm_only)}  (in bookmark, not in footer)")
    print(f"sections titled .............. {sections_titled}")
    print(f"  title from header page ..... {title_from_header}")
    print(f"  title from bookmark ........ {title_from_bm}")
    print(f"sections with NO title ....... {len(sections_no_title)}"
          + (f"  {sections_no_title[:10]}" if sections_no_title else ""))
    print(f"completeness diffs emitted ... {completeness_claims}  (proposed claims)")
    if mismatch_claims:
        print(f"footer/header code mismatches  {mismatch_claims}  (proposed findings):"
              + "".join(f"\n  footer={a} header={b}" for a, b in mismatch_sections))
    print(f"pages with no footer CSI ..... {len(all_no_footer)}"
          + f"  (TOC/cover/divider/residue -- {residue_claims} claim(s) emitted, never silently dropped)")
    print(f"image-only pages ............. {len(all_image_only)}"
          + "  (no text layer -- expected divider tabs)")
    print(f"division coverage ............ {dict(sorted(div_dist.items()))}")

    if bm_only:
        print(f"\nBookmark-only (declared, not in PDF footer -- completeness candidates):")
        for csi in sorted(bm_only):
            title = all_bm_sections.get(csi, "--")
            print(f"  {csi}  {title[:60]}")
    if footer_only:
        print(f"\nFooter-only (in PDF body, not in bookmark -- completeness candidates):")
        for csi in sorted(footer_only):
            title = getattr(merged_sections[csi], "_title", None) or "--"
            print(f"  {csi}  {title[:60]}")
    if sections_no_title:
        print(f"\nSections with no title resolved:")
        for csi in sections_no_title:
            print(f"  {csi}  (internal_page_1 idx: "
                  f"{merged_sections[csi].internal_page_1_idx})")

    # ── Write output ──────────────────────────────────────────────────────────
    os.makedirs(OUT_DIR, exist_ok=True)
    out_path = os.path.join(OUT_DIR, "spec_claims.jsonl")
    with open(out_path, "w", encoding="utf-8") as f:
        for c in claims_out:
            f.write(json.dumps(c) + "\n")

    print("-" * 100)
    print(f"wrote {len(claims_out)} spec claims ({len(merged_sections)} sections x 4 predicates"
          f" + {completeness_claims} completeness diffs"
          + (f" + {mismatch_claims} mismatch findings" if mismatch_claims else "")
          + f" + {residue_claims} residue findings"
          f") -> {os.path.relpath(out_path)}")
    print("=" * 100)

    # ── Structured run-summary sidecar (PLU-968, extract_spec_toc) ────────────
    # The same per-section table + counts already printed to the console,
    # serialized so the server-side extract_spec_toc worker function reads
    # structured data instead of scraping stdout -- the same sidecar contract
    # sheet_inventory.py's sheet_inventory_summary.json already carries
    # (PLU-225 ground_sheets). Additive: the local CLI workflow ignores this
    # file. Nothing new is computed here -- every field mirrors a value already
    # printed above.
    summary_out = os.path.join(OUT_DIR, "spec_inventory_summary.json")
    run_summary = {
        "setTag": SET_TAG,
        "mode": mode_label,
        # PLU-968 follow-up: honest per-file accounting -- a source file that
        # never opens must be visible here, never just a lower pagesScanned.
        "filesRequested": files_requested,
        "filesOpened": files_opened,
        "filesFailed": files_failed,
        "pagesScanned": total_pages,
        "sectionsFound": len(footer_codes),
        "corroboratedCount": len(agree),
        "footerOnlyCount": len(footer_only),
        "bookmarkOnlyCount": len(bm_only),
        "sectionsTitled": sections_titled,
        "titleFromHeaderCount": title_from_header,
        "titleFromBookmarkCount": title_from_bm,
        "noTitleCount": len(sections_no_title),
        "completenessDiffCount": completeness_claims,
        "mismatchCount": mismatch_claims,
        # Residue: every no-footer page, now durably claimed above (PLU-968) --
        # this count/list is the same set, projected for the worker's summary
        # read rather than a re-derivation.
        "residueCount": residue_claims,
        "imageOnlyCount": len(all_image_only),
        "residue": [{"pdf": pdf_label, "page": pg} for pdf_label, pg in all_no_footer],
        "divisionCoverage": dict(sorted(div_dist.items())),
    }
    with open(summary_out, "w", encoding="utf-8") as f:
        json.dump(run_summary, f)


if __name__ == "__main__":
    main()
