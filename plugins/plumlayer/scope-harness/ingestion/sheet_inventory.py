"""
Stage 0-2 sheet-inventory ingestion -- the foundational drawing-set process.

Turns a real architect-issued PDF set into a grounded, source-linked SHEET
INVENTORY (the "drawing log"): one record per page = sheet-number + title
candidates, each with bbox evidence + method + confidence + trustClass. This is
the `mosot-atomic-unit-of-truth.md` truth engine run at SHEET granularity --
the subject is `sheet:A-101`, the page number is an attribute claim.

Paradigm (project-north-star.md):
  * deterministic GROUNDS -- pull all title-block text + coordinates + font size
    (PyMuPDF). The sheet number is LOCALIZED by perception signals (largest
    sheet-grammar token, title-block region), NOT inferred by a title-block
    regex. Grammar match (SHEETNO_RE) is used only to MATCH/canonicalize.
  * agent READS + judges -- low-confidence rows (ambiguous / missing / off-region
    / degraded) are flagged for a vision-agent read of the rendered crop; this
    script does not guess them.
  * humans review + promote -- nothing here is "approved"; rows are proposed /
    authoritative-candidate claims awaiting reconciliation + review.

Self-calibration (PLU-182 + PLU-186 Slice 2):
  Two-pass over the page range. Pass A collects candidate picks; a per-set
  title-block region is LEARNED from the set's own evidence (font-size-weighted
  modal cluster in (cx,cy) space).  Pass B scores each pick by proximity to that
  learned region instead of a hardcoded cx>0.80/cy>0.70 gate.  This generalizes
  across firms whose title-block location differs from the 31 Milk / 150 Main /
  South Shore family (b107 Charlestown: cx~0.785, rescued from 0% -> high-conf
  on calibration; 248 Dorchester Appendix interior-design run: cy~0.26).
  On very small sets (< MIN_CALIB_PAGES picks) the static gate is used as a
  fallback and the summary says so.

  Multi-region calibration (PLU-186 Slice 2, deterministic tier):
  After the primary cluster is learned, residual picks (those NOT within
  CALIB_TOLERANCE of the primary centre) are inspected for secondary clusters
  using the same grid -> dominant-cell -> refinement algorithm.  Each secondary
  cluster must have >= MIN_CALIB_PAGES refined picks to be admitted (symmetric
  floor to the primary); at most MAX_CLUSTERS total are kept.  Scoring uses the
  NEAREST cluster per pick so D-series sheets at a minority title-block position
  score in-region against their own template, not against the majority one.
  All gates (planting-flag, grammar, confidence ladder) are unchanged -- the
  cluster list is a position prior only, never a trust bypass.

Stage 3-4 (index parse + reconcile) is a light first cut here: page-0/index
declared sheet list vs extracted sheets -> match / declared-not-found / found-not-
declared. Real precision/recall needs the hand-verified inventory (next step).

New flags (additive keys on claim / evidence objects -- existing keys unchanged):
  extractionWarning -- text-layer degradation detected on this page (MuPDF
    structural errors or garbled-text heuristic); downstream agent backstop
    reads the rendered image rather than the broken text layer.
  disciplineUncertain -- the discipline was inferred via the first-char fallback
    (or is unknown); flagged rather than silently promoted.
Calibration is not a separate claim key: when the per-set region is learned, it is
recorded in the claim `method` value as "vector-calibrated" (primary cluster) or
"vector-secondary" (secondary cluster) vs "vector" for the static-fallback gate --
the method field IS the calibration provenance.  "vector-secondary" is additive; it
does not change the trust tier or confidence ladder.

Confidential: writes only to INGEST_OUT_DIR (default ./output/, gitignored). ASCII output. PyMuPDF + stdlib.
Run:  python sheet_inventory.py            (full set)
      python sheet_inventory.py 0 20       (page range, inclusive start/exclusive end)
"""
import json
import os
import re
import sys
from collections import Counter

import fitz  # PyMuPDF

# Force UTF-8 stdout: sheet titles can contain non-cp1252 glyphs (e.g. the
# bullet char on 65 Kilmarnock); a Windows cp1252 console otherwise crashes the
# run with UnicodeEncodeError. Output-only guard -- no extraction logic change.
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

# No project default -- the PDF is always supplied per run. The old hardcoded
# 31-Milk default was both confidential AND went stale when the corpus relocated
# to ~/dev/plumlayer-private/ (2026-06-12); a silent default is a footgun.
PDF = os.environ.get("INGEST_PDF")
if not PDF:
    sys.exit("[error] set INGEST_PDF to the drawing PDF path (Windows-style, e.g. C:/.../set.pdf) -- no default")
SET_TAG = os.environ.get("INGEST_SET_TAG", "SET")
REVISION = os.environ.get("INGEST_REVISION", "unspecified")
# Output goes to the caller's working directory, never into this (read-only, possibly
# plugin-bundled) script's directory -- set INGEST_OUT_DIR to steer it; default ./output.
OUT_DIR = os.environ.get("INGEST_OUT_DIR") or os.path.join(os.getcwd(), "output")

# Sheet-number grammar (AIA/NCS): A-101, AD-101, A-110A, G-001, S-201, the
# decimal sub-sheet form A-100.1, and the SINGLE-DIGIT-MAJOR decimal form that
# dominates 150 Main: E1.01, G0.00, FA1.06, S1.03A (PLU-44 -- the old \d{2,3}
# floor matched the largest-font corner token on only 11/243 pages; \d{1,3}
# raises that to 241/243).
#
# PLU-182: the optional 1-2 digit BUILDING/AREA PREFIX before the dash --
# A1-101, A2-101.1, A4-103.1, E6-101B (Azola Westford numbers sheets by building:
# A1- = building 1 architectural). The old grammar REJECTED these as a strict
# FILTER, throwing out ~564 valid title-block sheets purely on dash position --
# hardcoded format-guessing the doctrine forbids. The grammar is a PERMISSIVE
# CANDIDATE NET, never a correctness gate: localization (font dominance + learned
# region + the confidence ladder) still picks the right token and keeps false
# positives out of `authoritative`; the regex only widens which tokens compete.
# The newly-admitted shape is EXACTLY [A-Z]{1,3}\d{1,2}-<num> -- the building-
# prefix-with-dash family and nothing else (verified by exhaustive delta-enum);
# every prior false-positive class (DTT-2Z, SW-100, A1, XX-123) was already
# matched by the old grammar and is gated downstream, not by format.
SHEETNO_RE = re.compile(r"^[A-Z]{1,3}(?:\d{1,2}-|-?)\d{1,3}(?:\.\d+)?[A-Z]?$")

# Discipline designators: NCS standard + non-NCS codes seen in the corpus
# (PLU-182 Step 3a). Fallback discipline assignment is FLAGGED, not silent (FM-9d).
DISCIPLINE = {
    # NCS standard
    "G": "General", "C": "Civil", "L": "Landscape", "S": "Structural",
    "A": "Architectural", "AD": "Arch-Demo", "I": "Interiors", "F": "Fire",
    "P": "Plumbing", "M": "Mechanical", "H": "HVAC", "E": "Electrical",
    "T": "Telecom", "FP": "Fire-Protection", "FA": "Fire-Alarm",
    # Non-NCS prefixes confirmed in corpus (PLU-182 characterization)
    "GT": "Geotechnical",   # geotechnical drawings
    "TY": "Security",       # security/access-control (248 Dorchester: 22 sheets)
    "X": "Demolition",      # demolition (b107 Charlestown: confirmed X-series)
    "AV": "Audiovisual",    # AV/low-voltage
    "D": "Interior-Design", # interior design (248 Dorchester Appendix)
    "EM": "Emergency",      # emergency/egress drawings
    "GL": "Glazing",        # glazing/curtainwall
    "CS": "Civil-Site",     # civil site detail (seen in 248 Dorchester)
}

# Planting-zone / subcategory codes that match SHEETNO_RE but are NOT real sheet
# prefixes (FM-9a; 1515 Comm). These cannot be `authoritative`; a pick dominated
# by one of these gets a planting-flag and stays `proposed` regardless of region.
PLANTING_PREFIXES = frozenset({"SW", "LI", "RM", "BN", "MF", "RD", "ST"})

# ---- Stamp / issue-note detection (title extraction, PLU-225 grounding fix) ----
# Set-constant stamp phrases are detected by FREQUENCY across Pass A title-window
# candidates: any normalized phrase that appears on >= STAMP_RECUR_FRAC of pages
# with title-window content is treated as an issue stamp and excluded from hasTitle
# in Pass B.  Structural invariant used: the issue stamp is the SAME phrase on every
# sheet; the real title varies per sheet.  This generalises across firms -- no
# per-firm vocabulary list required.
# Falls back to STAMP_PHRASES (static blocklist) when the set has fewer than
# STAMP_DETECT_MIN_PAGES title-window-bearing pages (too few to trust frequency).
STAMP_CY_GAP = 0.015          # max cy gap between adjacent spans to group as one phrase
STAMP_RECUR_FRAC = 0.40       # fraction of title-window pages to call a phrase a stamp
STAMP_MIN_PAGES = 5           # absolute minimum occurrences (floor for small sets)
STAMP_DETECT_MIN_PAGES = 12   # min title-window pages required to trust freq detection

# Static stamp phrase blocklist -- fast-path + fallback for small sets.
# Matched case-insensitively against RECONSTRUCTED cluster phrases (not individual
# spans): "ISSUED FOR" + "CONSTRUCTION" on separate lines reconstructs as
# "ISSUED FOR CONSTRUCTION" and is caught.  Exact full-phrase match only --
# no substring search -- so "STAIR DETAILS WOOD CONSTRUCTION" is never filtered.
STAMP_PHRASES = frozenset({
    "ISSUED FOR CONSTRUCTION",
    "ISSUED FOR BID",
    "ISSUED FOR PERMIT",
    "ISSUED FOR REVIEW",
    "ISSUED FOR REVIEW AND COMMENT",
    "NOT FOR CONSTRUCTION",
    "100% CONSTRUCTION DOCUMENTS",
})

# Self-calibration parameters (PLU-182 Step 1; PLU-186 Slice 2 multi-region)
MIN_CALIB_PAGES = 8        # min in-cluster picks to trust the learned region;
                            # below this, fall back to the static gate.  Applied
                            # symmetrically to primary AND secondary clusters.
CALIB_GRID_STEP = 0.05     # coarse grid cell size for modal-cluster detection
CALIB_TOLERANCE = 0.08     # radius around dominant cell centre for refinement
CALIB_IN_REGION_TOL = 0.08 # max (cx,cy) L1 distance from nearest cluster -> in_region
CALIB_SIZE_TOL_FRAC = 0.40 # pick size must be >= (1-tol)*learned_size for font-ok
                            # (catches 9.5pt off-region vs 75pt title block)
MAX_CLUSTERS = 4            # primary + at most 3 secondary clusters per set.
                            # A drawing set should not have more than ~4 distinct
                            # title-block templates; above this a warning is emitted
                            # rather than admitting more clusters.
SEC_MAX_NCOMP = 3           # max competing-token count for a pass-A pick to qualify
                            # for secondary-cluster detection.  High ncomp indicates
                            # riser-diagram / legend pages where the dominant grammar
                            # token competes with many same-size tokens -- not a real
                            # title-block zone.  Primary cluster admission is unfiltered.
# Static fallback gate (used when calibration is not trusted / set too small)
STATIC_CX_GATE = 0.80
STATIC_CY_GATE = 0.70


def canon_sheetno(s):
    """Normalize for MATCHING only (A1.1 / A-1.1 / A101 families collapse to A-#).

    Two forms:
      * Building/area-prefixed (PLU-182): letters + 1-2 building digits + dash +
        number -- A1-101, E6-101B. The building prefix is IDENTITY-BEARING, so it
        is preserved verbatim (A1-101 stays A1-101, NOT collapsed to A-1101 and
        NOT merged with A-101). This branch requires the explicit dash, so it
        never steals the leading digit of the decimal-major form below.
      * Standard / decimal-major: A-101, A101 -> A-101, E1.01 -> E-1.01,
        G0.00 -> G-0.00, FA1.06 -> FA-1.06 (current behavior, unchanged).
    """
    s = s.strip().upper()
    m = re.match(r"^([A-Z]{1,3}\d{1,2})-(\d{1,3}(?:\.\d+)?[A-Z]?)$", s)
    if m:
        return "%s-%s" % (m.group(1), m.group(2))
    m = re.match(r"^([A-Z]{1,3})-?(\d{1,3}(?:\.\d+)?[A-Z]?)$", s)
    return "%s-%s" % (m.group(1), m.group(2)) if m else s


def discipline_of(sheetno):
    """Return (discipline_label, uncertain_flag).

    uncertain_flag is True when the full prefix is not a known designator and we
    fell back to the first char or to 'Unknown'. The flag surfaces for agent
    confirm rather than silently accepting the guess (FM-9d fix, PLU-182).

    The ALPHA designator is extracted independent of any 1-2 digit building/area
    prefix (PLU-182): A1-101 -> 'A' (Architectural), E6-101B -> 'E' (Electrical),
    so the ~564 building-prefixed Azola sheets get a clean discipline instead of
    a spurious disciplineUncertain flag. The building digits are identity-bearing
    in the subject but are NOT part of the discipline designator.
    """
    m = re.match(r"^([A-Z]{1,3})\d{0,2}-", sheetno)
    if not m:
        return "Unknown", True
    pre = m.group(1)
    if pre in DISCIPLINE:
        return DISCIPLINE[pre], False
    # First-char fallback: attempt a guess but always flag it
    if pre[0] in DISCIPLINE:
        return DISCIPLINE[pre[0]] + "(?)", True
    return "Unknown", True


def spans_of(page):
    """All text spans with text, font size, and normalized-page center + bbox,
    reported in the RENDERED (rotation-applied) frame.

    get_text returns coordinates in UNROTATED page space; on a /Rotate page the
    visual bottom-right title block therefore lands at a different corner (150
    Main's L/E/FA/H sheets are /Rotate 270 -> the sheet number normalized to
    cy~1.33, breaking corner detection). Mapping every bbox through
    page.rotation_matrix (identity when rotation == 0, so no change to 31 Milk)
    puts cx/cy + bboxPts in the same frame the page renders in, so corner
    localization, title banding, and citation crops all agree (PLU-44).

    Returns (spans_list, mupdf_warnings_list).  mupdf_warnings are drained from
    fitz.TOOLS per page for FM-9h (XObject/keyword errors on b107 Charlestown).
    """
    r = page.rect
    W, H = r.width, r.height
    mat = page.rotation_matrix
    out = []
    d = page.get_text("dict")
    for blk in d.get("blocks", []):
        for line in blk.get("lines", []):
            for sp in line.get("spans", []):
                t = sp["text"].strip()
                if not t:
                    continue
                rect = fitz.Rect(sp["bbox"]) * mat  # unrotated -> rendered frame
                x0, x1 = min(rect.x0, rect.x1), max(rect.x0, rect.x1)
                y0, y1 = min(rect.y0, rect.y1), max(rect.y0, rect.y1)
                out.append({
                    "text": t, "size": round(sp["size"], 2),
                    "bboxPts": [round(x0, 2), round(y0, 2), round(x1, 2), round(y1, 2)],
                    "cx": (((x0 + x1) / 2) - r.x0) / W,
                    "cy": (((y0 + y1) / 2) - r.y0) / H,
                })
    # Drain per-page MuPDF warnings (FM-9h)
    raw_warns = fitz.TOOLS.mupdf_warnings()
    warns = raw_warns.splitlines() if raw_warns else []
    return out, warns


def _is_garbled(spans):
    """Heuristic degradation check (FM-9c: corrupted/unembedded fonts).

    Returns True when the title-band region (cy > 0.60) is dominated by
    replacement-character / non-printable glyphs, indicating the text layer
    cannot be decoded from the embedded font.
    """
    title_band = [s for s in spans if s["cy"] > 0.60]
    if not title_band:
        return False
    total_chars = sum(len(s["text"]) for s in title_band)
    if total_chars == 0:
        return False
    bad = sum(
        1 for s in title_band for ch in s["text"]
        if ch == "�" or (ord(ch) < 0x20 and ch not in "\t\n\r")
    )
    return bad / total_chars > 0.15


def _detect_extraction_warning(spans, mupdf_warns):
    """Combine FM-9h (MuPDF structural errors) and FM-9c (garbled text).

    Returns (warn_bool, reason_string_or_None).
    """
    reasons = []
    if mupdf_warns:
        reasons.append("mupdf-xobject-error")
    if _is_garbled(spans):
        reasons.append("garbled-text-layer")
    return bool(reasons), ("; ".join(reasons) if reasons else None)


def _collect_title_phrases(spans, sx, sy):
    """Collect all phrase clusters from the title-block window for one page.

    Used in Pass A to build frequency data for set-constant stamp detection.
    Uses the same window and grouping logic as pick_title so that the phrases
    counted here match exactly the candidates that pick_title evaluates.

    sx, sy: cx/cy of the Pass-A raw best candidate (approximation of the sheet
    number position before calibration -- accurate enough for frequency counting).

    Returns a frozenset of normalized (uppercase, stripped) phrase strings.
    """
    block = [s for s in spans
             if abs(s["cx"] - sx) < 0.18 and s["cy"] < sy and s["cy"] > sy - 0.30
             and not SHEETNO_RE.match(s["text"].replace(" ", ""))
             and any(ch.isalpha() for ch in s["text"]) and len(s["text"]) >= 3]
    if not block:
        return frozenset()
    sorted_block = sorted(block, key=lambda s: s["cy"])
    clusters = []
    cur = [sorted_block[0]]
    for s in sorted_block[1:]:
        if s["cy"] - cur[-1]["cy"] <= STAMP_CY_GAP:
            cur.append(s)
        else:
            clusters.append(cur)
            cur = [s]
    clusters.append(cur)
    phrases = set()
    for cl in clusters:
        top = max(s["size"] for s in cl)
        dominant = [s for s in cl if top - s["size"] <= 0.6]
        phrase = " ".join(
            s["text"] for s in sorted(dominant, key=lambda s: (s["cy"], s["cx"]))
        ).strip().upper()
        if phrase:
            phrases.add(phrase)
    return frozenset(phrases)


def _detect_stamp_phrases(pass_a_title_phrases):
    """Detect set-constant stamp phrases by frequency across title-window pages.

    pass_a_title_phrases: list of frozensets -- one per page with a sheet-number
    candidate in Pass A; each set holds the normalized title-window phrases for
    that page (from _collect_title_phrases).

    A phrase is flagged as a stamp when it appears on >= STAMP_RECUR_FRAC of
    pages that have any title-window content AND at minimum STAMP_MIN_PAGES
    occurrences.  Structural invariant: the real title varies per sheet; only
    set-constant repetitions (the issue stamp) reach this threshold.

    Returns (detected, full_stamps) where:
      detected   -- frozenset of phrases found by frequency alone (may overlap
                    STAMP_PHRASES; useful for reporting what freq actually found).
      full_stamps -- detected | STAMP_PHRASES (the operative exclusion set passed
                    to pick_title; STAMP_PHRASES acts as fast-path and fallback).

    When the set is too small (< STAMP_DETECT_MIN_PAGES pages with content),
    detected is empty and full_stamps == STAMP_PHRASES.
    """
    pages_with_content = [p for p in pass_a_title_phrases if p]
    n = len(pages_with_content)
    if n < STAMP_DETECT_MIN_PAGES:
        return frozenset(), STAMP_PHRASES  # too small; static list governs
    phrase_counts = Counter(
        phrase for page_phrases in pages_with_content for phrase in page_phrases
    )
    threshold = max(STAMP_MIN_PAGES, int(STAMP_RECUR_FRAC * n))
    detected = frozenset(
        phrase for phrase, cnt in phrase_counts.items() if cnt >= threshold
    )
    return detected, detected | STAMP_PHRASES


# ---------------------------------------------------------------------------
# Self-calibration: per-set learned title-block region (PLU-182 Step 1)
# ---------------------------------------------------------------------------

def _learn_region(pass_a_picks):
    """Learn the set's title-block (cx, cy) clusters from Pass A raw picks.

    pass_a_picks: list of {cx, cy, size} -- the best-candidate span per page
    (font-size dominant, no gate applied yet) collected during Pass A.

    Returns (clusters, calibrated, cap_hit) where:
      clusters: list of dicts, each {cx, cy, size, n, is_secondary}.
                clusters[0] is the primary (dominant) cluster.
                clusters[1:] are secondary clusters (PLU-186 multi-region).
                Empty list when calibration fails.
      calibrated: True when at least the primary cluster was trusted.
      cap_hit: True when MAX_CLUSTERS was reached with qualified residual picks
               still remaining (some minority templates may be unclustered).

    calibrated=False means the static fallback gate should be used.

    Algorithm (deterministic, stdlib-only, no new dependencies):
      Primary cluster:
        1. Build a (cx, cy) grid with cell size CALIB_GRID_STEP; weight each pick
           by its font size (large title-block numbers dominate; tiny body tokens
           contribute proportionally little).
        2. Find the dominant cell (max size-weight sum).
        3. Refine: picks within CALIB_TOLERANCE of the dominant cell centre ->
           size-weighted median cx, cy, and font size.
        4. Require >= MIN_CALIB_PAGES refined picks; else static fallback.

      Secondary clusters (PLU-186 Slice 2 multi-region):
        5. Remove primary-cluster picks from the residual pool.
        6. Filter residual to low-competition picks (ncomp <= SEC_MAX_NCOMP=3).
           High-ncomp picks are riser-diagram / legend pages where the dominant
           grammar token competes with many same-size tokens -- not title-block
           pages.  This prevents a coincidental cluster of cross-reference tokens
           from being admitted as a secondary title-block template.
        7. Repeat grid -> dominant-cell -> refinement on the filtered residual.
        8. Admit each secondary cluster if it has >= MIN_CALIB_PAGES refined picks.
        9. Stop when the residual dominant cell has < MIN_CALIB_PAGES picks or
           MAX_CLUSTERS total clusters are reached.

    The 40% multimodal heuristic is retained for diagnostics only (multimodal
    flag in primary cluster dict) but is NOT a gate for secondary cluster
    admission -- it requires a comparable-size second cluster and silently misses
    real minority templates (e.g. D-series at 7% of 248 Dorchester).
    """
    def cell_weight(picks):
        return sum(pp["size"] for pp in picks)

    def weighted_median(value_weight_pairs):
        """Weighted median of (value, weight) pairs (deterministic, stdlib)."""
        pairs = sorted(value_weight_pairs, key=lambda x: x[0])
        half = sum(w for _, w in pairs) / 2.0
        acc = 0.0
        for v, w in pairs:
            acc += w
            if acc >= half:
                return v
        return pairs[-1][0]

    def _fit_cluster(pool):
        """Fit one cluster to a pool of picks.  Returns (cluster_dict, residual_pool)
        or (None, pool) when the pool has no trustworthy cluster."""
        if not pool:
            return None, pool

        grid = {}
        for p in pool:
            rk = int(p["cy"] / CALIB_GRID_STEP)
            ck = int(p["cx"] / CALIB_GRID_STEP)
            grid.setdefault((rk, ck), []).append(p)

        sorted_cells = sorted(grid.items(), key=lambda kv: cell_weight(kv[1]), reverse=True)
        dom_key, _ = sorted_cells[0]
        dom_cy_centre = (dom_key[0] + 0.5) * CALIB_GRID_STEP
        dom_cx_centre = (dom_key[1] + 0.5) * CALIB_GRID_STEP

        # Multimodality check (diagnostics only -- not a gate)
        dom_weight = cell_weight(sorted_cells[0][1])
        second_weight = cell_weight(sorted_cells[1][1]) if len(sorted_cells) > 1 else 0.0
        multimodal = (second_weight >= 0.40 * dom_weight) and (dom_weight > 0)

        refined = [p for p in pool
                   if abs(p["cx"] - dom_cx_centre) <= CALIB_TOLERANCE
                   and abs(p["cy"] - dom_cy_centre) <= CALIB_TOLERANCE]

        if len(refined) < MIN_CALIB_PAGES:
            return None, pool  # not enough picks to trust this cluster

        region_cx = weighted_median([(p["cx"], p["size"]) for p in refined])
        region_cy = weighted_median([(p["cy"], p["size"]) for p in refined])
        region_size = weighted_median([(p["size"], p["size"]) for p in refined])

        cluster = {
            "cx": region_cx, "cy": region_cy, "size": region_size,
            "n": len(refined), "multimodal": multimodal, "is_secondary": False,
        }
        # Residual = pool minus the picks absorbed into this cluster
        residual = [p for p in pool
                    if not (abs(p["cx"] - dom_cx_centre) <= CALIB_TOLERANCE
                            and abs(p["cy"] - dom_cy_centre) <= CALIB_TOLERANCE)]
        return cluster, residual

    if not pass_a_picks:
        return [], False, False

    # --- Primary cluster ---
    primary, primary_residual = _fit_cluster(pass_a_picks)
    if primary is None:
        return [], False, False  # calibration fails; caller uses static fallback

    clusters = [primary]

    # --- Secondary clusters ---
    # Filter the primary residual to low-competition picks before secondary fitting.
    # High ncomp indicates a riser-diagram / legend page where the dominant
    # grammar token competes with many same-size tokens -- these are NOT in a
    # title-block zone.  Real secondary title-block templates are identified on
    # pages where the pick is the clear winner (ncomp <= SEC_MAX_NCOMP).
    # Primary cluster admission is unfiltered (it must handle all page types).
    residual_qualified = [p for p in primary_residual if p.get("ncomp", 1) <= SEC_MAX_NCOMP]
    while len(clusters) < MAX_CLUSTERS and residual_qualified:
        sec, residual_qualified = _fit_cluster(residual_qualified)
        if sec is None:
            break  # no more trustworthy clusters in the qualified residual
        sec["is_secondary"] = True
        clusters.append(sec)

    cap_hit = (len(clusters) == MAX_CLUSTERS and bool(residual_qualified))
    return clusters, True, cap_hit


def pick_sheet_number_scored(spans, clusters, calibrated):
    r"""LOCALIZE the title-block sheet number: among sheet-grammar spans, the
    largest font wins (tie-break: proximity to the NEAREST learned cluster).
    Returns (span, confidence, reason, n_distinct_competing, planting_flag,
             nearest_cluster_idx).

    PLU-182 self-calibration: when calibrated=True, 'in_region' is proximity to
    the nearest cluster centre (L1 distance <= CALIB_IN_REGION_TOL).  Font
    dominance is re-anchored to that nearest cluster's learned size so a tiny
    off-region body token cannot be region-font-consistent (FM-3/FM-9i gate).

    PLU-186 Slice 2 multi-region: clusters is now a list (primary + any secondary
    clusters learned by _learn_region).  Each grammar candidate is scored against
    all clusters and its nearest cluster wins.  All gates are unchanged -- the
    cluster list is a position prior, never a trust bypass.  Planting-flag picks
    (FM-9a) are still capped at 0.80 regardless of which cluster they land in.

    Confidence ladder -- authoritative floor (0.88) is PRESERVED, not lowered:
      in_region AND (unique OR region-font-ok) -> 0.95  [authoritative]
      in_region                                -> 0.88  [authoritative]
      off-region, peer-dominant                -> 0.80  [proposed]
      off-region, unique                       -> 0.75  [proposed]
      ambiguous                                -> 0.55  [proposed]

    nearest_cluster_idx: 0 = primary cluster, >0 = secondary cluster index.
    Used by the caller to choose the method string (vector-calibrated vs
    vector-secondary).  -1 when not calibrated.
    """
    cands = [s for s in spans if SHEETNO_RE.match(s["text"].replace(" ", ""))]
    if not cands:
        return None, 0.0, "no-grammar-token", 0, False, -1

    if calibrated and clusters:
        # For each candidate, find its nearest cluster (L1 distance)
        for s in cands:
            dists = [abs(s["cx"] - cl["cx"]) + abs(s["cy"] - cl["cy"])
                     for cl in clusters]
            s["_nearest_dist"] = min(dists)
            s["_nearest_idx"] = dists.index(min(dists))
        # Sort: largest font, tie-break by proximity to the nearest cluster
        cands.sort(key=lambda s: (s["size"], -s["_nearest_dist"]), reverse=True)
    else:
        for s in cands:
            s["_nearest_dist"] = None
            s["_nearest_idx"] = -1
        cands.sort(key=lambda s: (s["size"], s["cx"] + s["cy"]), reverse=True)

    best = cands[0]
    distinct = {canon_sheetno(s["text"]) for s in cands}
    nearest_idx = best.get("_nearest_idx", -1)

    # Planting-prefix check (FM-9a) on the ACTUAL emitted pick (best), AFTER the
    # sort -- not a separately-derived largest token. When a planting token and a
    # real token share a rounded font size, the region tie-break can make the
    # planting code `best` while a font-only pick would not; deriving the flag
    # from `best` ensures whatever token is emitted carries the right cap. The
    # alpha prefix is extracted independent of any 1-2 digit building prefix
    # (PLU-182) so a building-prefixed planting code (SW1-101) is still demoted --
    # the wider grammar must not open a hole that lets a planting code reach
    # authoritative.  A planting code in a secondary cluster is still demoted
    # (PLU-186: cluster list is position prior only, not trust bypass).
    m_pre = re.match(r"^([A-Z]{1,3})\d{0,2}-", canon_sheetno(best["text"]))
    planting_flag = bool(m_pre and m_pre.group(1) in PLANTING_PREFIXES)

    # Region / corner test
    if calibrated and clusters:
        nearest_cl = clusters[nearest_idx]
        dist = best["_nearest_dist"]
        in_region = dist <= CALIB_IN_REGION_TOL
        reason_pfx = "learned-region"
        nearest_size = nearest_cl["size"]
    else:
        in_region = best["cx"] > STATIC_CX_GATE and best["cy"] > STATIC_CY_GATE
        reason_pfx = "corner"
        nearest_size = None

    # Peer font dominance (relative to other grammar tokens on this page)
    smaller = [s["size"] for s in cands if s["size"] < best["size"] - 0.6]
    peer_dominant = (not smaller) or best["size"] >= 1.6 * max(smaller)

    # Region-font-consistency: pick size in the ballpark of the nearest cluster's
    # learned title size.  Only active when calibrated; falls back to peer_dominant
    # otherwise.
    if calibrated and nearest_size is not None:
        region_font_ok = best["size"] >= nearest_size * (1.0 - CALIB_SIZE_TOL_FRAC)
    else:
        region_font_ok = peer_dominant

    # Planting-flag: cap at proposed, max 0.80
    if planting_flag:
        if in_region:
            return best, 0.80, "%s+planting-flag" % reason_pfx, len(distinct), True, nearest_idx
        return best, 0.55, "planting-flag-off-region", len(distinct), True, nearest_idx

    # Standard confidence ladder (unchanged)
    if in_region and (len(distinct) == 1 or region_font_ok):
        conf = 0.95
        reason = "%s+unique" % reason_pfx if len(distinct) == 1 else "%s+font" % reason_pfx
    elif in_region:
        conf, reason = 0.88, reason_pfx
    elif peer_dominant:
        conf, reason = 0.80, "font-dominant-off-%s" % ("region" if calibrated else "corner")
    elif len(distinct) == 1:
        conf, reason = 0.75, "unique-but-off-%s" % ("region" if calibrated else "corner")
    else:
        conf, reason = 0.55, "ambiguous-largest-font"

    return best, conf, reason, len(distinct), False, nearest_idx


def pick_title(spans, sheet_span, stamp_phrases=frozenset()):
    """Title candidate: largest non-stamp phrase cluster in the title-block window.

    Window (unchanged): ±0.18 cx and ≤0.30 cy above the sheet number span.
    Within the window, spans are grouped into phrase clusters by cy proximity
    (Δcy ≤ STAMP_CY_GAP) so that multi-span stamps ("ISSUED FOR" on one line,
    "CONSTRUCTION" on the next) are reconstructed as a single phrase before
    exclusion.  Each cluster's text is assembled in cy-then-cx order (reading
    order for vertically stacked lines -- fixes the former cx-only sort that
    scrambled multi-line titles like "LEVEL 4 & LEVEL 5 LIFE / SAFETY PLANS").
    Within each cluster, only the dominant-size spans (±0.6pt) are joined.

    Stamp exclusion: clusters matching stamp_phrases | STAMP_PHRASES (exact
    case-insensitive phrase match) are skipped.  stamp_phrases is the
    set-constant set detected by _detect_stamp_phrases in Pass A; STAMP_PHRASES
    is the static blocklist fast-path.  Either can catch the stamp independently.

    stamp_phrases=frozenset() is safe for single-page calls outside the pipeline;
    STAMP_PHRASES alone then governs.

    This is the judgment-heavy field -- emitted as a low-trust proposed claim.
    """
    if sheet_span is None:
        return None
    sx, sy = sheet_span["cx"], sheet_span["cy"]
    block = [s for s in spans
             if abs(s["cx"] - sx) < 0.18 and s["cy"] < sy and s["cy"] > sy - 0.30
             and not SHEETNO_RE.match(s["text"].replace(" ", ""))
             and any(ch.isalpha() for ch in s["text"]) and len(s["text"]) >= 3]
    if not block:
        return None

    # Group into phrase clusters by cy proximity (reading order).
    sorted_block = sorted(block, key=lambda s: s["cy"])
    clusters = []
    cur = [sorted_block[0]]
    for s in sorted_block[1:]:
        if s["cy"] - cur[-1]["cy"] <= STAMP_CY_GAP:
            cur.append(s)
        else:
            clusters.append(cur)
            cur = [s]
    clusters.append(cur)

    # Pick the highest-size non-stamp cluster.
    all_stamps = stamp_phrases | STAMP_PHRASES
    best_cluster = None
    best_size = -1.0
    for cl in clusters:
        top = max(s["size"] for s in cl)
        # Within the cluster, retain only the dominant-size tier (±0.6pt).
        dominant = [s for s in cl if top - s["size"] <= 0.6]
        phrase = " ".join(
            s["text"] for s in sorted(dominant, key=lambda s: (s["cy"], s["cx"]))
        ).strip().upper()
        if phrase in all_stamps:
            continue
        if top > best_size:
            best_size = top
            best_cluster = dominant

    if best_cluster is None:
        return None
    best_cluster = sorted(best_cluster, key=lambda s: (s["cy"], s["cx"]))
    return {"text": " ".join(s["text"] for s in best_cluster),
            "size": best_size, "bboxPts": best_cluster[0]["bboxPts"]}


def claim(subject, predicate, value, method, conf, trust, src_bbox, snippet,
          extraction_warning=None, discipline_uncertain=False):
    """Build a MOSOT claim dict.

    Existing keys (subject, predicate, value, evidence, trustClass, confidence,
    status, assertedBy, promotedBy) are UNCHANGED in shape.  The new PLU-182
    flags (extractionWarning, disciplineUncertain) are ADDITIVE optional keys
    that are only present when True/non-None -- no reader is broken by their
    absence on old claims or presence on new ones.
    """
    c = {
        "subject": subject, "predicate": predicate, "value": value,
        "evidence": [{"source": "%s/%s" % (SET_TAG, src_bbox["page"]),
                      # rendered (rotation-applied) frame -- spans_of maps bboxes
                      # through page.rotation_matrix, so on /Rotate pages these are
                      # NOT raw unrotated PDF user space (identical when rot==0).
                      "locator": {"frame": "page-points-rendered", "bboxPts": src_bbox["bbox"]},
                      "method": method, "snippet": snippet}],
        "trustClass": trust, "confidence": conf,
        "status": "current", "assertedBy": "sheet_inventory.py", "promotedBy": None,
    }
    if extraction_warning:
        c["extractionWarning"] = extraction_warning
    if discipline_uncertain:
        c["disciplineUncertain"] = True
    return c


def main():
    doc = fitz.open(PDF)
    start = int(sys.argv[1]) if len(sys.argv) > 1 else 0
    end = int(sys.argv[2]) if len(sys.argv) > 2 else doc.page_count

    # ------------------------------------------------------------------
    # PASS A: collect raw localizer output per page (no claims, no gates)
    # ------------------------------------------------------------------
    pass_a = []  # [{cx, cy, size, ncomp}] -- best-candidate span per page
    pass_a_title_phrases = []  # parallel: title-window phrase sets for stamp detection
    for i in range(start, end):
        spans, _ = spans_of(doc[i])
        cands = [s for s in spans if SHEETNO_RE.match(s["text"].replace(" ", ""))]
        if cands:
            best = max(cands, key=lambda s: (s["size"], s["cx"] + s["cy"]))
            # ncomp: distinct sheet-grammar tokens at the same font-size tier
            # (within 0.6pt of best -- same rounding band the peer-dominant test uses).
            # High ncomp on a pass-A pick means the page has many competing grammar
            # tokens at the same size: riser diagrams, tabular sheets, legend pages.
            # Real title-block pages have ncomp=1 (unique title number in the block).
            # Used by _learn_region to qualify secondary-cluster picks (PLU-186 Slice 2).
            same_tier = len({s["text"] for s in cands
                             if abs(s["size"] - best["size"]) <= 0.6})
            pass_a.append({"cx": best["cx"], "cy": best["cy"],
                           "size": best["size"], "ncomp": same_tier})
            # Collect title-window phrase clusters using the raw (pre-calibration)
            # best position -- accurate enough for frequency counting across all pages.
            pass_a_title_phrases.append(
                _collect_title_phrases(spans, best["cx"], best["cy"]))

    # ------------------------------------------------------------------
    # Learn the per-set title-block region(s) from Pass A
    # ------------------------------------------------------------------
    clusters, calibrated, cap_hit = _learn_region(pass_a)

    # Detect set-constant stamp phrases from Pass A title-window frequency data.
    # Phrases on >= STAMP_RECUR_FRAC of title-window pages are the set's issue stamp;
    # excluded from hasTitle candidates in Pass B.  n_tw is reported in the summary.
    # freq_detected: raw set found by frequency; stamp_phrases: the operative union
    # (freq_detected | STAMP_PHRASES) passed to pick_title.
    freq_detected, stamp_phrases = _detect_stamp_phrases(pass_a_title_phrases)
    n_tw = sum(1 for p in pass_a_title_phrases if p)  # pages with title-window content

    # ------------------------------------------------------------------
    # PASS B: score each page against the learned (or fallback) region
    # ------------------------------------------------------------------
    rows, claims_out = [], []
    warn_count = 0

    for i in range(start, end):
        spans, mupdf_warns = spans_of(doc[i])
        ext_warn, ext_warn_reason = _detect_extraction_warning(spans, mupdf_warns)
        if ext_warn:
            warn_count += 1

        sheet_span, conf, reason, ncomp, planting_flag, nearest_idx = pick_sheet_number_scored(
            spans, clusters, calibrated)

        sheetno = canon_sheetno(sheet_span["text"]) if sheet_span else None
        title = pick_title(spans, sheet_span, stamp_phrases)
        # planting-flag picks stay proposed regardless of conf >= 0.88
        trust = "authoritative" if (conf >= 0.88 and not planting_flag) else "proposed"

        disc_label, disc_uncertain = discipline_of(sheetno) if sheetno else ("Unknown", True)

        rows.append({
            "page": i, "sheetno": sheetno, "conf": conf, "reason": reason,
            "ncomp": ncomp, "discipline": disc_label,
            "disciplineUncertain": disc_uncertain,
            "plantingFlag": planting_flag,
            "nearestClusterIdx": nearest_idx,
            "title": title["text"] if title else None,
            "cx": round(sheet_span["cx"], 3) if sheet_span else None,
            "cy": round(sheet_span["cy"], 3) if sheet_span else None,
            "extractionWarning": ext_warn_reason,
        })

        if sheetno:
            if not calibrated:
                method = "vector"
            elif nearest_idx > 0:
                method = "vector-secondary"
            else:
                method = "vector-calibrated"
            claims_out.append(claim(
                "sheet:%s" % sheetno, "appearsOnPage", i, method,
                conf, trust,
                {"page": i, "bbox": sheet_span["bboxPts"]},
                sheet_span["text"],
                extraction_warning=ext_warn_reason,
                discipline_uncertain=disc_uncertain,
            ))
            if title:
                claims_out.append(claim(
                    "sheet:%s" % sheetno, "hasTitle", title["text"],
                    "vector-localized", min(conf, 0.7), "proposed",
                    {"page": i, "bbox": title["bboxPts"]}, title["text"],
                    extraction_warning=ext_warn_reason,
                ))

    # ---- printed drawing log ----
    print("=" * 100)
    print("SHEET INVENTORY  |  %s  |  pages %d-%d of %d" % (SET_TAG, start, end, doc.page_count))
    print("-" * 100)
    # Calibration state -- printed before the per-page table so coverage is honest
    if calibrated and clusters:
        primary = clusters[0]
        secondary = clusters[1:]
        print("CALIBRATION  primary cluster: cx=%.3f cy=%.3f size=%.1f  (%d in-cluster picks)"
              % (primary["cx"], primary["cy"], primary["size"], primary["n"]))
        if primary.get("multimodal"):
            print("CALIBRATION  NOTE: primary cluster is bimodal (second grid cell >= 40%% weight).")
        for si, sc in enumerate(secondary, start=1):
            print("CALIBRATION  secondary cluster %d: cx=%.3f cy=%.3f size=%.1f  (%d picks)"
                  % (si, sc["cx"], sc["cy"], sc["size"], sc["n"]))
        if not secondary:
            print("CALIBRATION  no secondary clusters (all residual cells < %d picks)" % MIN_CALIB_PAGES)
        if cap_hit:
            print("CALIBRATION WARNING: cluster cap hit (MAX_CLUSTERS=%d); some minority templates may be unclustered" % MAX_CLUSTERS)
    else:
        n_a = len(pass_a)
        print("CALIBRATION  FALLBACK: static gate (cx>%.2f, cy>%.2f); pass-A picks: %d (need >= %d)."
              % (STATIC_CX_GATE, STATIC_CY_GATE, n_a, MIN_CALIB_PAGES))
        print("             Off-corner title-block sets will score low in fallback mode.")
    # Stamp detection summary
    freq_new = freq_detected - STAMP_PHRASES      # new discoveries beyond the static list
    freq_confirmed = freq_detected & STAMP_PHRASES # static phrases also confirmed by frequency
    if n_tw < STAMP_DETECT_MIN_PAGES:
        print("STAMP DETECT  FALLBACK: static blocklist only (%d title-window pages, need >= %d)"
              % (n_tw, STAMP_DETECT_MIN_PAGES))
    elif freq_detected:
        print("STAMP DETECT  freq-detected %d stamp phrase(s) (>= %.0f%% of %d pages)%s"
              % (len(freq_detected), STAMP_RECUR_FRAC * 100, n_tw,
                 ": %s" % sorted(freq_new)[:4] if freq_new else " (all already in static list)"))
        if freq_confirmed:
            print("STAMP DETECT  freq-confirmed from static list: %s" % sorted(freq_confirmed)[:4])
    else:
        print("STAMP DETECT  no set-constant phrases >= %.0f%% threshold; static list only (%d pages)"
              % (STAMP_RECUR_FRAC * 100, n_tw))
    print("-" * 100)
    print("%4s %-8s %5s %-26s %4s  %-11s %-2s %s" %
          ("pg", "sheet#", "conf", "reason", "comp", "(cx,cy)", "?", "title-candidate"))
    for r in rows:
        disc_mark = "!" if r["disciplineUncertain"] else " "
        suffix = ("" + (" [W]" if r["extractionWarning"] else "")
                  + (" [P]" if r["plantingFlag"] else ""))
        print("%4d %-8s %5.2f %-26s %4s  %-11s %-2s %s%s" % (
            r["page"], r["sheetno"] or "--", r["conf"], r["reason"][:26], r["ncomp"],
            "(%s,%s)" % (r["cx"], r["cy"]) if r["cx"] is not None else "--",
            disc_mark,
            (r["title"] or "")[:38], suffix))

    # ---- stage-0/2 summary ----
    found = [r for r in rows if r["sheetno"]]
    hi = [r for r in found if r["conf"] >= 0.88 and not r["plantingFlag"]]
    flagged = [r for r in rows if r["conf"] < 0.88 or r["plantingFlag"]]
    disc_uncertain_count = sum(1 for r in found if r["disciplineUncertain"])
    planting_count = sum(1 for r in found if r["plantingFlag"])
    secondary_count = sum(1 for r in rows if r.get("nearestClusterIdx", 0) > 0)
    disc = Counter(r["discipline"] for r in found)
    print("-" * 100)
    print("pages scanned ........ %d" % len(rows))
    print("sheet# extracted ..... %d  (high-conf >=0.88: %d)" % (len(found), len(hi)))
    print("flagged for review ... %d  (low-conf / missing / planting -> agent-read queue)" % len(flagged))
    print("extraction warnings .. %d%s" % (
        warn_count,
        "  (mupdf-error/garbled -> agent reads rendered image)" if warn_count else ""))
    if secondary_count:
        print("secondary-cluster .. %d  (vector-secondary method; minority title-block template)" % secondary_count)
    if disc_uncertain_count:
        print("discipline uncertain . %d  (fallback fired; flagged for agent confirm [!])" % disc_uncertain_count)
    if planting_count:
        print("planting-code picks .. %d  (SW-/LI-/etc.; cannot be authoritative [P])" % planting_count)
    print("by discipline ........ %s" % dict(disc))
    dups = [s for s, c in Counter(r["sheetno"] for r in found).items() if c > 1]
    if dups:
        print("duplicate sheet# ..... %s  (supersession / revision collision -> reconcile)" % dups)

    # ---- stage 3-4: locate the index/sheet-list page(s) by title, then reconcile ----
    # (Don't assume page 0 is the index -- A-001 here is "Overall Building Plans".
    #  Detect by keyword. A combined multi-discipline set carries MANY drawing-list
    #  pages -- one per discipline (150 Main: the structural list on p120, etc.) --
    #  so union ALL of them, not just the first. If none, say so honestly.)
    INDEX_KEYS = ("DRAWING INDEX", "SHEET INDEX", "SHEET LIST", "DRAWING LIST",
                  "INDEX OF DRAWINGS")
    idx_pgs = [i for i in range(start, end)
               if any(k in doc[i].get_text("text").upper() for k in INDEX_KEYS)]
    extracted = {r["sheetno"] for r in found}
    print("-" * 100)
    if idx_pgs:
        # A declared token must look like a real sheet number, not a grid bubble
        # ("A1") or a stray body token: require >=2 digits.
        declared = set()
        for ip in idx_pgs:
            for t in doc[ip].get_text("text").replace("\n", " ").split():
                t = t.strip().strip(".,")
                if SHEETNO_RE.match(t) and sum(c.isdigit() for c in t) >= 2:
                    declared.add(canon_sheetno(t))
        missing = sorted(declared - extracted)
        extra = sorted(extracted - declared)
        print("index/drawing-list page(s): %s  (declare %d distinct sheets)"
              % (idx_pgs[:8], len(declared)))
        print("declared & found (match) ........... %d" % len(declared & extracted))
        print("declared, NOT found (RFI cand) ..... %d  %s" % (len(missing), missing[:12]))
        print("found, NOT declared (stale/addn) ... %d  %s" % (len(extra), extra[:12]))
    else:
        print("no index / sheet-list page in this discipline split")
        print("  -> cross-discipline reconciliation deferred (cover index likely in the G-series PDF)")

    os.makedirs(OUT_DIR, exist_ok=True)
    out = os.path.join(OUT_DIR, "sheet_inventory_claims.jsonl")
    with open(out, "w", encoding="utf-8") as f:
        for c in claims_out:
            f.write(json.dumps(c) + "\n")
    print("-" * 100)
    print("wrote %d sheet-inventory claims -> %s" % (len(claims_out), os.path.relpath(out)))
    doc.close()


if __name__ == "__main__":
    main()
