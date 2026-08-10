"""
schedule_ground.py -- ground phase for the schedule-ingestion pipeline.

Doctrine role (schedule-ingestion-design.md, recalibration 2026-06-28):
  The pipeline is: prepare -> agent-column-map -> ground.
  This script is the GROUND phase: given a manifest that the agent has filled in
  with column-maps (one per table per sheet), it reads the prepared spans, assigns
  each span to its column by the agent-provided x-ranges, clusters into row y-bands,
  stitches multi-span cells, and emits one grounded project record claim per cell.

The agent-column-map contract (written into manifest 'column_maps' entries):
  {
    "tableTitle": str,             -- human label for the table (from sheet title / header)
    "kind": str,                   -- project record kind namespace (e.g. "plumbingFixtureType")
    "tableType": "definition" | "instance",  -- default "definition"; "instance" for
                                   --   opening/room/instance keyed tables. Adds
                                   --   ambiguityClass:"instance" to all claims.
    "layout": "tabular" | "matrix",
    "regionBbox": [x0,y0,x1,y1],  -- PDF-point bbox of the table region (data + headers)
    "headerRowCount": int,         -- number of header rows (>=1; typically 1-2, but
                                   --   deep 3-4 tier HVAC/plumbing headers are supported)
    "keyColumn": {                 -- the code/key column
      "name": str,                 -- predicate name (camelCase, e.g. "designation")
      "xLeft": float,
      "xRight": float,
      "wrapped": bool,             -- OPTIONAL (default false). true = the key cell is
                                   --   split across N stacked lines that read as one
                                   --   code (e.g. "HP" over "A" => "HP-A"). Selects the
                                   --   key-first stacking path; the deterministic tool
                                   --   joins the stack's lines top-to-bottom with '-'.
                                   --   Absent = today's row-cluster behavior, unchanged.
      "numericKey": bool           -- OPTIONAL (default false). true = accept a bare
                                   --   integer key on a DEFINITION table (opens the same
                                   --   gate tableType:"instance" opens, without the
                                   --   instance ambiguity tag). Never loosens the global
                                   --   canon_code gate; scoped to this table only.
    },
    "columns": [                   -- attribute columns in left-to-right order
      {"name": str, "xLeft": float, "xRight": float},
      ...
    ],
    "deferredRegions": [           -- optional: non-table regions flagged present-and-deferred
      {"type": "notes"|"diagram"|"imageSwatches"|"mixed", "regionBbox": [...]}
    ]
  }

For matrix layout, "keyColumn" is the attribute-label column (leftmost), and
"columns" are code-keyed columns (one per code). The ground phase treats each
code column as a separate subject whose attributes are the row labels.
keyColumn.numericKey applies to the tabular path only -- matrix layout has no
numeric-key concept; its numeric code-columns gate their canon_code check via
tableType:"instance" (same as any other matrix code column), not numericKey.

Grounding logic (deterministic, no inference):
  1. Isolate table spans: spans whose bbox y-center falls within regionBbox y-range,
     and after stripping the header rows (top N rows worth of y-height).
  2. Cluster isolated spans by y-center into row y-bands (ROW_Y_TOL = 6pt), then split
     any band that greedy-centroid drift stitched from two tightly-packed code rows
     (>=2 distinct key-column y-centers, ROW_SPLIT_Y_TOL) into one sub-row per code. A
     continuation row (empty key cell) has no key span and is never split.
  3. Assign each span to its column by checking which column's [xLeft, xRight]
     interval contains the span's x-center. Spans whose x-center falls outside
     all column intervals are flagged residue (never silently assigned or dropped).
  4. Stitch multi-span cells: join spans in the same (row, column) by ascending
     y then x into a single text value + union bbox.
  5. Continuation-row merge: rows with an empty key cell are merged UP into the
     previous code row's same column accumulators rather than flagged as residue.
     This recovers multi-line cells (e.g. "SEE FLOOR" / "PLANS" across two y-bands,
     or numbered accessory sub-items). Only after all continuation rows are merged
     does the tool stitch and emit each column's final value.
  6. Extract the key-column cell per row as the subject code. Apply canon_code gate:
     rows that fail are flagged residue (reason: "canon_code-fail").
  7. Emit one claim per non-empty data cell, keyed by the code, plus locatedAt /
     definedOnSheet / partOfIssue anchors.
  8. Instance tables (tableType:"instance"): claim kind namespace reflects the
     instance subject class (e.g. "door:" for door openings) and all claims carry
     ambiguityClass:"instance" so reviewers know these are opening/room instances,
     not type definitions.

Every emitted value carries its exact grounded span text + bbox. Nothing invented.

Output:
  schedule_claims.jsonl          -- grounded project record claims (one per line)
  schedule_ground_residue.json   -- rows that could not be grounded
  schedule_ground_stats.json     -- per-sheet counts

Confidential: all I/O paths outside the repo. PyMuPDF + stdlib (fitz only
for the canon_code gate, which is pure Python -- no PDF open needed here).

Run:
  INGEST_SET_TAG="1270-COMM-IFC" \\
  INGEST_REVISION="1270 Comm IFC 2025-12-19" \\
  INGEST_OUT_DIR=~/dev/plumlayer-private/schedule-ingest-output \\
  python schedule_ground.py
"""

from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

SET_TAG = os.environ.get("INGEST_SET_TAG", "SET")
REVISION = os.environ.get("INGEST_REVISION", "unspecified")
OUT_DIR = os.environ.get("INGEST_OUT_DIR") or os.path.join(os.getcwd(), "output")

ASSERTER = "schedule_ground.py"

# Row y-band clustering tolerance (PDF points).
# Spans within ROW_Y_TOL of a row's centroid are in the same row.
ROW_Y_TOL = 6.0

# Span x-center tolerance beyond a column's xLeft/xRight before calling it
# "outside all columns" (a small slop for spans that slightly overflow the header bbox).
X_SLOP_PT = 4.0

# Two key-column spans whose y-centers are more than ROW_SPLIT_Y_TOL apart belong to
# distinct code rows. A row-band holding that pattern is a collision -- greedy-centroid
# clustering (ROW_Y_TOL) chained two tightly-packed code rows through the data row
# between them -- and is split, one sub-row per key y-center. Kept >= ROW_Y_TOL so it
# never re-splits spans the clustering legitimately merged into one row.
ROW_SPLIT_Y_TOL = 6.0

# Wrapped-key stacking tolerance (PDF points), used ONLY on the agent-declared
# keyColumn.wrapped path. A wrapped key's lines sit a few points apart (E-704's stack is
# ~9pt); distinct code rows are a full row pitch apart (~36pt). This tolerance groups the
# wrapped stack and separates the rows. The discriminator is the agent's declared
# structure, never text geometry alone: E-704's 9.0pt within-key gap and P-003's 10.56pt
# between-distinct-keys gap are not separable by any y-threshold, so only the hint can
# tell "these lines are one code" from "these are two codes". Assumes row pitch exceeds
# this tolerance beyond the wrap gap (true of the real HVAC schedules).
WRAPPED_KEY_STACK_Y_TOL = 15.0


# ---------------------------------------------------------------------------
# canon_code -- the identity gate (identical to schedule_inventory.py)
# ---------------------------------------------------------------------------

_CODE_RE = re.compile(
    r"^[A-Za-z]{0,4}-?\d{1,4}[A-Za-z]?$"             # A1, D4, F-1, P-1A, DOAS-1
    r"|"
    r"^[A-Za-z]{1,3}$"                                 # single/2/3-letter mark: U, HM, STD
    r"|"
    r"^[A-Za-z]{1,4}-\d{1,4}-\d{1,4}$"               # WD-1-4 (all-numeric after 2nd hyphen)
    r"|"
    r"^[A-Za-z]{1,4}-\d{1,4}-[A-Za-z]\d{1,4}$"      # E-36-D1, E-36-D8 (alpha+digit after 2nd)
    r"|"
    r"^[A-Za-z]{1,4}-[A-Za-z]{1,3}$"                 # FD-A, RD-B, OFD-A, AD-A (letter-letter)
    r"|"
    r"^[A-Za-z]{1,4}-[A-Za-z]{1,3}-\d{1,4}[A-Za-z]?$"  # U-CW-1, U-AP-10, U-FX-1A
    r"|"
    r"^[A-Za-z]{1,4}-[A-Za-z]{1,3}-\d{1,4}-[A-Za-z]{1,4}$"  # U-SH-1-ALT
    r"|"
    r"^[A-Za-z]{2,4}\d[A-Za-z]{2}$"                  # LRP4PH, EP2PH, OSP4PH (fused alpha-digit-PH)
    r"|"
    r"^[A-Za-z]{1,4}-[A-Za-z]{1,4}\d{1,3}$"         # EF-T1, EF-DOAS1, PEV-A1 (alpha-hyphen-alphaDigit)
    r"|"
    r"^[A-Za-z]{1,4}-[A-Za-z]?\d{1,3}[A-Za-z]?-\d{1,4}$"  # BC-R2-1, FCU-1A-1 (mid alpha+digit)
    r"|"
    # CSI-style two-digit prefix + two letters: 27AV, 28FA. Lowest-confidence branch --
    # the first to drop if it ever admits a false positive. Validated zero-false-positive
    # against the real residue set at authoring (PLU-309 A2), but the shape is weak.
    r"^\d{2}[A-Za-z]{2}$"
    r"|"
    # 4-segment wrapped-key family: alpha prefix, a leading numeric segment, then a mid
    # tier that MUST carry a letter (alpha-then-digit or digit-then-alpha) before the final
    # numeric segment. FCU-1-1A-1 comes from a wrapped key cell ('FCU' stacked over
    # '1-1A-1') on E-705's fan-coil schedule. The mandatory mid-letter is deliberately
    # narrower than the 3-segment branch above's optional-both-sides shape: without it this
    # branch also swallowed the generic "A-1-2-3" 4-segment shape the triple-hyphen guard
    # (TestCanonCode.test_three_hyphens) exists to reject. Validated zero-false-positive
    # against the real residue set at authoring (PLU-309 A3).
    r"^[A-Za-z]{1,4}-\d{1,2}-(?:[A-Za-z]\d{1,3}[A-Za-z]?|\d{1,3}[A-Za-z])-\d{1,4}$"  # FCU-1-1A-1
    r"|"
    # Long-prefix shade-mark family (PLU-376 fourth instance / PLU-431 tail, 2026-07-08):
    # alpha prefix of 5-6 letters (every other branch caps the prefix at 4; the floor of 5
    # here is deliberate -- it is what keeps this branch from re-admitting short-prefix
    # multi-trailing-letter shapes the base branch's "only one trailing alpha" rule already
    # rejects, e.g. P-1AB / TestCanonCode.test_multi_char_trailing) + hyphen + 1-2 digits +
    # up to 3 trailing letters. Recovers SHADE-1MA, SHADE-2MA, SHADE-1MI, SHADE-2MI,
    # SHADE-3MI, SHADE-4MI, SHADE-5MI, SHADE-1DMI (150 Main A-10.02 shade schedule). Scoped
    # narrowly to this exact shape, not a general widening of the alpha-prefix cap.
    r"^[A-Za-z]{5,6}-\d{1,2}[A-Za-z]{1,3}$"          # SHADE-1MA, SHADE-1DMI
    r"|"
    # Two-segment counterpart of the above: SHADE-1D-MA (prefix + digit-letter segment +
    # trailing letter segment, both hyphen-separated). Same PLU-376/PLU-431 shade family
    # and same 5-6 letter prefix floor, not a general 2-hyphen widening -- the middle
    # segment is still digit-led.
    r"^[A-Za-z]{5,6}-\d{1,2}[A-Za-z]{1,3}-[A-Za-z]{1,3}$"  # SHADE-1D-MA
)

# Words that match _CODE_RE (short all-alpha branch) but are never schedule marks.
# Drawn from common construction drawing note words that appear in key-column cells.
_CODE_DENYLIST: frozenset[str] = frozenset({
    "NTS", "SIM", "TYP", "YES", "NO", "TBD", "EQ", "AFF", "OC", "CLR",
    "MAX", "MIN", "REF", "NIC", "VIF", "VIC", "GSM", "GWB", "LVL",
    "BY", "OR", "IN", "AT", "TO", "OF", "IF",
    "SEE", "GC", "PC", "EC", "MC", "SC",
})


def canon_code(raw: str, *, allow_numeric: bool = False) -> str:
    """Validate and normalise a schedule code. Raises ValueError if invalid.

    allow_numeric: accept a bare-integer key (e.g. a door-opening number 162, 180).
    Enabled ONLY for instance tables (tableType:"instance"), whose key column is an
    opening/room number, not a type mark. Definition tables keep rejecting bare
    integers (there a bare integer is a stray row number, never a schedule mark).
    """
    cleaned = raw.strip().upper()
    if not cleaned:
        raise ValueError(f"empty code: {raw!r}")
    if len(cleaned) > 16:
        raise ValueError(f"too long to be a schedule mark: {raw!r}")
    if re.fullmatch(r"\d+", cleaned):
        if allow_numeric:
            return cleaned
        raise ValueError(f"pure-numeric (row number): {raw!r}")
    if not _CODE_RE.match(cleaned):
        raise ValueError(f"not a valid schedule mark: {raw!r}")
    if cleaned in _CODE_DENYLIST:
        raise ValueError(f"denylist note-word (not a schedule mark): {raw!r}")
    return cleaned


# ---------------------------------------------------------------------------
# Claim builder (same canonical shape as schedule_inventory.py)
# ---------------------------------------------------------------------------

def _make_claim(
    subject: str,
    predicate: str,
    value,
    method: str,
    conf: float,
    trust: str,
    evidence_source: str,
    evidence_locator: list[float] | None,
    snippet: str,
    ambiguity_class: str | None = None,
) -> dict:
    ev: dict = {
        "source": evidence_source,
        "method": method,
        "snippet": snippet,
    }
    if evidence_locator is not None:
        ev["locator"] = {"frame": "page-points", "bboxPts": evidence_locator}
    claim: dict = {
        "subject": subject,
        "predicate": predicate,
        "value": value,
        "evidence": [ev],
        "trustClass": trust,
        "confidence": round(conf, 2),
        "status": "current",
        "assertedBy": ASSERTER,
        "promotedBy": None,
    }
    if ambiguity_class:
        claim["ambiguityClass"] = ambiguity_class
    return claim


# ---------------------------------------------------------------------------
# Span type (plain dict from JSONL; no dataclass needed here)
# ---------------------------------------------------------------------------

def _cx(span: dict) -> float:
    bb = span["bbox"]
    return (bb[0] + bb[2]) / 2


def _cy(span: dict) -> float:
    bb = span["bbox"]
    return (bb[1] + bb[3]) / 2


# ---------------------------------------------------------------------------
# Column assignment by agent-provided x-ranges
# ---------------------------------------------------------------------------

def _assign_column(
    span: dict,
    key_col: dict,
    columns: list[dict],
) -> str | None:
    """Return the column name whose [xLeft, xRight] contains the span's x-center.

    Returns None if the span falls outside all columns (with X_SLOP_PT tolerance).
    The key column is checked first (it is often the leftmost).
    """
    cx = _cx(span)
    all_cols = [key_col] + columns
    for col in all_cols:
        if col["xLeft"] - X_SLOP_PT <= cx <= col["xRight"] + X_SLOP_PT:
            return col["name"]
    return None


# ---------------------------------------------------------------------------
# Row y-band clustering
# ---------------------------------------------------------------------------

def _cluster_rows(spans: list[dict]) -> list[list[dict]]:
    """Cluster spans into row y-bands by y-center (greedy merge within ROW_Y_TOL)."""
    if not spans:
        return []
    ordered = sorted(spans, key=lambda s: _cy(s))
    rows: list[list[dict]] = []
    current: list[dict] = [ordered[0]]
    current_cy = _cy(ordered[0])

    for sp in ordered[1:]:
        sp_cy = _cy(sp)
        if abs(sp_cy - current_cy) <= ROW_Y_TOL:
            current.append(sp)
            # Update centroid
            current_cy = sum(_cy(s) for s in current) / len(current)
        else:
            rows.append(current)
            current = [sp]
            current_cy = sp_cy

    if current:
        rows.append(current)

    return rows


# ---------------------------------------------------------------------------
# Cell stitch
# ---------------------------------------------------------------------------

def _stitch(spans: list[dict]) -> tuple[str, list[float]]:
    """Join spans (sorted top-to-bottom, left-to-right) into cell text + union bbox."""
    if not spans:
        return "", []
    ordered = sorted(spans, key=lambda s: (_cy(s), _cx(s)))
    text = " ".join(s["text"] for s in ordered)
    bb = [
        min(s["bbox"][0] for s in ordered),
        min(s["bbox"][1] for s in ordered),
        max(s["bbox"][2] for s in ordered),
        max(s["bbox"][3] for s in ordered),
    ]
    return text, [round(v, 2) for v in bb]


# ---------------------------------------------------------------------------
# Header height estimation from a column map entry
# ---------------------------------------------------------------------------

def _estimate_header_bottom(
    region_bbox: list[float],
    header_row_count: int,
    data_spans: list[dict],
) -> float:
    """Estimate the y-coordinate below which data rows start.

    Strategy: find the first ROW_Y_TOL-cluster of spans whose centroid is inside
    the regionBbox, then skip 'header_row_count' clusters. Return the y1 of the
    last header cluster + 2pt as the data-start y.

    Falls back to top 20% of region height if the span-based estimate fails.
    """
    region_y0, region_y1 = region_bbox[1], region_bbox[3]
    in_region = [
        s for s in data_spans
        if region_y0 <= _cy(s) <= region_y1
    ]
    if not in_region:
        # Fall back to proportional estimate
        return region_y0 + (region_y1 - region_y0) * 0.2

    rows = _cluster_rows(in_region)
    if not rows or header_row_count <= 0:
        return region_y0

    # The top N row-clusters are header rows
    header_clusters = rows[:header_row_count]
    last_header_span = max(
        (s for cluster in header_clusters for s in cluster),
        key=lambda s: s["bbox"][3],
    )
    return last_header_span["bbox"][3] + 2.0


# ---------------------------------------------------------------------------
# Collision split -- separate two code rows a drifting centroid stitched together
# ---------------------------------------------------------------------------

def _split_collided_rows(
    row_spans: list[dict],
    key_col: dict,
    columns: list[dict],
) -> list[list[dict]]:
    """Split a row-band that centroid drift stitched from two+ code rows.

    A tabular data band should hold exactly one key cell. _cluster_rows uses a greedy
    running centroid, so two tightly-packed code rows (distinct key spans a few points
    more than ROW_Y_TOL apart, e.g. HWHP-1 / HWHP-2 ~11pt apart) can chain into one
    band through the data row between them, stitching the key cell into a two-code
    string that then fails canon_code.

    Detection is purely GEOMETRIC: two or more key-column spans whose y-centers are
    more than ROW_SPLIT_Y_TOL apart. The band is partitioned into one sub-row per
    distinct key y-center, every span (key and attribute alike) assigned to the
    nearest key y-center. Never keys on text meaning; a recovered code comes from a
    real key-column span with its own bbox.

    A band with fewer than two distinct key cells is returned unchanged, so a
    continuation row (empty key cell) is never split and still flows into the
    continuation-merge path. Sub-rows are returned top-to-bottom.
    """
    key_spans = [
        s for s in row_spans
        if _assign_column(s, key_col, columns) == key_col["name"]
    ]
    if len(key_spans) < 2:
        return [row_spans]

    # Group the key spans into distinct rows by y-center gap.
    key_spans.sort(key=_cy)
    groups: list[list[dict]] = [[key_spans[0]]]
    for ks in key_spans[1:]:
        if _cy(ks) - _cy(groups[-1][-1]) <= ROW_SPLIT_Y_TOL:
            groups[-1].append(ks)
        else:
            groups.append([ks])

    if len(groups) < 2:
        return [row_spans]

    anchors = [sum(_cy(s) for s in g) / len(g) for g in groups]
    sub_rows: list[list[dict]] = [[] for _ in anchors]
    for sp in row_spans:
        cyv = _cy(sp)
        nearest = min(range(len(anchors)), key=lambda i: abs(cyv - anchors[i]))
        sub_rows[nearest].append(sp)
    return sub_rows


# ---------------------------------------------------------------------------
# Wrapped-key bucketing -- key-first assembly for keyColumn.wrapped tables
# ---------------------------------------------------------------------------

def _wrapped_key_buckets(
    data_spans: list[dict],
    key_col: dict,
    columns: list[dict],
) -> list[list[dict]]:
    """Assemble one bucket per code for a wrapped-key table (keyColumn.wrapped=true).

    In a wrapped-key table the key cell is split across N stacked lines that the reader
    reads top-to-bottom as one code (e.g. 'HP' over 'A' => 'HP-A'; 'AC' over '0-1' =>
    'AC-0-1'; 'VRF' over 'R' over '1A' => 'VRF-R-1A'). The row-cluster path cannot handle
    this: greedy y-clustering either splits the wrapped lines into separate rows or a
    _stitch would space-join them into a two-token string that fails canon_code.

    Key-first assembly, GEOMETRIC (never keyed on text meaning):
      1. Group key-column spans into per-code stacks by y-center pitch
         (WRAPPED_KEY_STACK_Y_TOL groups the wrapped lines, separates the row pitch).
      2. Within each stack, split into lines (ROW_Y_TOL) and join the line texts
         top-to-bottom with '-' into the code; union the stack bboxes. The joined code
         is carried on a single synthetic key span (union bbox), so it grounds to the
         real key-line locations, and the '-' is a structural join the agent declared,
         not an invented token.
      3. Bucket every non-key span to the nearest stack by y-center.
      4. Return one bucket per stack (synthetic key span + that stack's data spans),
         top-to-bottom, so the existing assign/stitch/continuation-merge/emit loop runs
         unchanged. This path and _split_collided_rows are mutually exclusive per table;
         the hint selects.

    Returns [] if no span in data_spans falls inside the key column's x-range (an empty
    stack list, never a residue entry -- this function has no residue_rows to write to).
    The caller (_ground_tabular) treats an empty return as "no key spans" and flags every
    span in data_spans residue rather than letting the empty row_clusters make the per-row
    loop a silent no-op.
    """
    key_spans = [
        s for s in data_spans
        if _assign_column(s, key_col, columns) == key_col["name"]
    ]
    non_key = [
        s for s in data_spans
        if _assign_column(s, key_col, columns) != key_col["name"]
    ]
    if not key_spans:
        return []

    # (1) Group key spans into per-code stacks by y-center pitch.
    key_spans.sort(key=_cy)
    stacks: list[list[dict]] = [[key_spans[0]]]
    for ks in key_spans[1:]:
        if _cy(ks) - _cy(stacks[-1][-1]) <= WRAPPED_KEY_STACK_Y_TOL:
            stacks[-1].append(ks)
        else:
            stacks.append([ks])

    # (2) Join each stack's lines top-to-bottom with '-' into a synthetic key span.
    anchors: list[float] = []
    synthetic_keys: list[dict] = []
    for stack in stacks:
        lines = _cluster_rows(stack)                       # top-to-bottom lines
        line_texts = [_stitch(line)[0] for line in lines]
        code_text = "-".join(t for t in line_texts if t)
        union = [
            round(min(s["bbox"][0] for s in stack), 2),
            round(min(s["bbox"][1] for s in stack), 2),
            round(max(s["bbox"][2] for s in stack), 2),
            round(max(s["bbox"][3] for s in stack), 2),
        ]
        synthetic_keys.append({"text": code_text, "bbox": union})
        anchors.append(sum(_cy(s) for s in stack) / len(stack))

    # (3) Bucket every non-key span to the nearest stack anchor by y-center.
    buckets: list[list[dict]] = [[sk] for sk in synthetic_keys]
    for sp in non_key:
        cyv = _cy(sp)
        nearest = min(range(len(anchors)), key=lambda i: abs(cyv - anchors[i]))
        buckets[nearest].append(sp)

    # (4) Buckets are already in top-to-bottom stack order.
    return buckets


# ---------------------------------------------------------------------------
# Ground one table (tabular layout)
# ---------------------------------------------------------------------------

def _ground_tabular(
    col_map: dict,
    spans: list[dict],
    source_instrument: str,
    sheet_subject: str,
    revision: str,
) -> tuple[list[dict], list[dict]]:
    """Ground a tabular table from agent column-map + raw spans.

    Tabular: code column is on the left; attributes spread across the top.
    Continuation rows (empty key cell) are merged into the previous code row's
    column accumulators before stitching, recovering multi-line cells.
    Returns (claims, residue_rows).
    """
    claims: list[dict] = []
    residue_rows: list[dict] = []

    region_bbox: list[float] = col_map["regionBbox"]
    key_col: dict = col_map["keyColumn"]
    columns: list[dict] = col_map["columns"]
    kind: str = col_map["kind"]
    header_row_count: int = col_map.get("headerRowCount", 1)
    # tableType "instance" tags all claims ambiguityClass:"instance"
    is_instance: bool = col_map.get("tableType", "definition") == "instance"
    amb_class: str | None = "instance" if is_instance else None
    # Agent-declared structural hints on the key column (both optional; absent = today's
    # behavior). 'wrapped' selects the key-first stacking path; 'numericKey' opens the
    # bare-numeric gate on a definition table (never loosens the global gate, and does
    # NOT imply instance semantics -- a numeric-keyed definition stays a definition).
    wrapped_key: bool = bool(key_col.get("wrapped", False))
    numeric_key: bool = bool(key_col.get("numericKey", False))

    # Isolate spans inside this table's region bbox
    region_spans = [
        s for s in spans
        if (region_bbox[0] - X_SLOP_PT <= _cx(s) <= region_bbox[2] + X_SLOP_PT
            and region_bbox[1] <= _cy(s) <= region_bbox[3])
    ]

    # Determine where data rows start (below headers)
    header_bottom = _estimate_header_bottom(region_bbox, header_row_count, region_spans)
    data_spans = [s for s in region_spans if _cy(s) > header_bottom]

    if not data_spans:
        residue_rows.append({
            "reason": "no-data-spans-after-header",
            "tableTitle": col_map.get("tableTitle", ""),
            "regionBbox": region_bbox,
        })
        return claims, residue_rows

    if wrapped_key:
        # Wrapped-key table: assemble one bucket per code by stacking the key column's
        # lines (agent-declared structure). Mutually exclusive with _split_collided_rows.
        row_clusters = _wrapped_key_buckets(data_spans, key_col, columns)
        if not row_clusters:
            # No key-column span captured any data span (e.g. a mis-set xLeft/xRight on
            # a narrow stacked-key column). Without a key span there is no row structure
            # to reconstruct geometrically, so every data span is flagged residue rather
            # than silently discarded (the empty row_clusters would otherwise make the
            # per-row loop below a no-op).
            residue_rows.append({
                "reason": "wrapped-table-no-key-spans",
                "tableTitle": col_map.get("tableTitle", ""),
                "regionBbox": region_bbox,
                "spans": [{"text": s["text"], "bbox": s["bbox"]} for s in data_spans],
            })
            return claims, residue_rows
    else:
        # Cluster into row y-bands, then split any band that centroid drift stitched from
        # two tightly-packed code rows (>=2 distinct key cells) back into one sub-row per
        # code. A continuation row (empty key cell) has no key span and is never split.
        row_clusters = _cluster_rows(data_spans)
        row_clusters = [
            sub
            for band in row_clusters
            for sub in _split_collided_rows(band, key_col, columns)
        ]

    # Two-pass: first collect all span clusters into code rows (with continuation merge),
    # then emit claims per fully-accumulated code row.
    #
    # code_rows: list of (code, key_bbox, by_col accumulator, outside_spans)
    # where by_col accumulator accumulates spans from the key row + all continuation rows.
    code_rows: list[tuple[str, list[float], dict[str, list[dict]], list[dict]]] = []

    for row_spans in row_clusters:
        # Assign each span to a column
        by_col: dict[str, list[dict]] = {key_col["name"]: []}
        for col in columns:
            by_col[col["name"]] = []
        outside: list[dict] = []

        for sp in row_spans:
            col_name = _assign_column(sp, key_col, columns)
            if col_name is None:
                outside.append(sp)
            else:
                by_col[col_name].append(sp)

        # Check key cell
        key_spans = by_col.get(key_col["name"], [])
        key_text, key_bbox = _stitch(key_spans)

        if not key_text:
            if code_rows:
                # Mid-table continuation: merge into previous code row's accumulators
                # (recovers multi-line cells — expected, normal operation).
                prev_code, prev_key_bbox, prev_by_col, prev_outside = code_rows[-1]
                for col_name, col_spans in by_col.items():
                    prev_by_col.setdefault(col_name, []).extend(col_spans)
                prev_outside.extend(outside)
            else:
                # Leading continuation before any code row — cannot merge.
                # If this row has attribute-column spans, the key column is probably
                # misaligned (the real key cell fell into an attribute column).
                # Emit a distinguishable reason so the pattern is visible.
                attr_spans = [
                    {"text": s["text"], "bbox": s["bbox"]}
                    for col_name, spans_list in by_col.items()
                    if col_name != key_col["name"]
                    for s in spans_list
                ]
                reason = (
                    "key-cell-empty-has-attribute-spans"
                    if attr_spans
                    else "leading-continuation-no-parent"
                )
                residue_rows.append({
                    "reason": reason,
                    "row_y": sum(_cy(s) for s in row_spans) / max(len(row_spans), 1),
                    "tableTitle": col_map.get("tableTitle", ""),
                    "spans": [{"text": s["text"], "bbox": s["bbox"]} for s in row_spans],
                    **({"attrSpans": attr_spans} if attr_spans else {}),
                })
            continue

        # New code row
        try:
            code = canon_code(key_text, allow_numeric=is_instance or numeric_key)
        except ValueError as exc:
            residue_rows.append({
                "reason": f"canon_code-fail: {exc}",
                "key_text": key_text,
                "row_y": sum(_cy(s) for s in row_spans) / max(len(row_spans), 1),
                "tableTitle": col_map.get("tableTitle", ""),
            })
            continue

        code_rows.append((code, key_bbox, by_col, outside))

    # Emit claims per code row (all continuations already merged into accumulators)
    for code, key_bbox, by_col, outside in code_rows:
        subject = f"{kind}:{code}"

        # Flag spans that fell outside all columns (from key row or continuations)
        if outside:
            residue_rows.append({
                "reason": "spans-outside-columns",
                "subject": subject,
                "tableTitle": col_map.get("tableTitle", ""),
                "spans": [{"text": s["text"], "bbox": s["bbox"]} for s in outside],
            })

        # Emit one attribute claim per non-empty column
        cell_bboxes: list[list[float]] = []
        if key_bbox:
            cell_bboxes.append(key_bbox)

        for col in columns:
            col_spans = by_col.get(col["name"], [])
            cell_text, cell_bbox = _stitch(col_spans)
            if not cell_text:
                continue
            if cell_bbox:
                cell_bboxes.append(cell_bbox)
            claims.append(_make_claim(
                subject=subject,
                predicate=col["name"],
                value=cell_text,
                method="schedule-parse",
                conf=0.90,
                trust="proposed",
                evidence_source=source_instrument,
                evidence_locator=cell_bbox if cell_bbox else None,
                snippet=cell_text[:80],
                ambiguity_class=amb_class,
            ))

        # locatedAt claim (row bbox = union of all cell bboxes)
        if cell_bboxes:
            row_bbox = [
                round(min(bb[0] for bb in cell_bboxes), 2),
                round(min(bb[1] for bb in cell_bboxes), 2),
                round(max(bb[2] for bb in cell_bboxes), 2),
                round(max(bb[3] for bb in cell_bboxes), 2),
            ]
        else:
            row_bbox = None

        loc_value: dict = {
            "instrument": source_instrument,
            "sheetId": sheet_subject,
        }
        if row_bbox:
            loc_value["bbox"] = row_bbox

        claims.append(_make_claim(
            subject=subject,
            predicate="locatedAt",
            value=loc_value,
            method="schedule-parse",
            conf=0.90,
            trust="proposed",
            evidence_source=source_instrument,
            evidence_locator=row_bbox,
            snippet=f"{code} on {sheet_subject}",
            ambiguity_class=amb_class,
        ))

        claims.append(_make_claim(
            subject=subject,
            predicate="definedOnSheet",
            value=sheet_subject,
            method="schedule-parse",
            conf=0.95,
            trust="proposed",
            evidence_source=source_instrument,
            evidence_locator=None,
            snippet=sheet_subject,
            ambiguity_class=amb_class,
        ))

        if revision and revision != "unspecified":
            claims.append(_make_claim(
                subject=subject,
                predicate="partOfIssue",
                value={"label": revision},
                method="user-asserted",
                conf=0.90,
                trust="proposed",
                evidence_source="user-supplied",
                evidence_locator=None,
                snippet=revision,
                ambiguity_class=amb_class,
            ))

    return claims, residue_rows


# ---------------------------------------------------------------------------
# Ground one table (matrix layout)
# ---------------------------------------------------------------------------

def _ground_matrix(
    col_map: dict,
    spans: list[dict],
    source_instrument: str,
    sheet_subject: str,
    revision: str,
) -> tuple[list[dict], list[dict]]:
    """Ground a matrix/transposed table from agent column-map + raw spans.

    Matrix: code-keyed columns across the top; attribute labels down the left.
    The key column (agent-named 'keyColumn') is the attribute-label column.
    Each entry in 'columns' is a code-keyed column.
    Returns (claims, residue_rows).
    """
    claims: list[dict] = []
    residue_rows: list[dict] = []

    region_bbox: list[float] = col_map["regionBbox"]
    label_col: dict = col_map["keyColumn"]   # leftmost: attribute labels
    code_cols: list[dict] = col_map["columns"]  # each is one code subject
    kind: str = col_map["kind"]
    header_row_count: int = col_map.get("headerRowCount", 1)
    is_instance: bool = col_map.get("tableType", "definition") == "instance"
    amb_class: str | None = "instance" if is_instance else None

    # Isolate + strip headers
    region_spans = [
        s for s in spans
        if (region_bbox[0] - X_SLOP_PT <= _cx(s) <= region_bbox[2] + X_SLOP_PT
            and region_bbox[1] <= _cy(s) <= region_bbox[3])
    ]
    header_bottom = _estimate_header_bottom(region_bbox, header_row_count, region_spans)
    data_spans = [s for s in region_spans if _cy(s) > header_bottom]

    if not data_spans:
        residue_rows.append({
            "reason": "no-data-spans-after-header",
            "tableTitle": col_map.get("tableTitle", ""),
            "regionBbox": region_bbox,
        })
        return claims, residue_rows

    row_clusters = _cluster_rows(data_spans)

    # Validate code column names
    valid_code_cols: list[dict] = []
    for col in code_cols:
        try:
            canon_code(col["name"], allow_numeric=is_instance)
            valid_code_cols.append(col)
        except ValueError as exc:
            residue_rows.append({
                "reason": f"matrix-code-col-invalid: {exc}",
                "colName": col["name"],
                "tableTitle": col_map.get("tableTitle", ""),
            })

    if not valid_code_cols:
        residue_rows.append({
            "reason": "no-valid-code-columns-in-matrix",
            "tableTitle": col_map.get("tableTitle", ""),
        })
        return claims, residue_rows

    # Build per-code attribute lists
    all_cols = [label_col] + valid_code_cols
    code_attrs: dict[str, list[dict]] = {col["name"]: [] for col in valid_code_cols}

    for row_spans in row_clusters:
        by_col: dict[str, list[dict]] = {col["name"]: [] for col in all_cols}
        outside: list[dict] = []

        for sp in row_spans:
            col_name = _assign_column(sp, label_col, valid_code_cols)
            if col_name is None:
                outside.append(sp)
            else:
                by_col[col_name].append(sp)

        # Emit residue for spans that fell outside all column intervals.
        if outside:
            residue_rows.append({
                "reason": "matrix-spans-outside-columns",
                "tableTitle": col_map.get("tableTitle", ""),
                "spans": [{"text": s["text"], "bbox": s["bbox"]} for s in outside],
            })

        label_text, _ = _stitch(by_col.get(label_col["name"], []))
        if not label_text:
            # Empty label row — emit residue if it has code-column content (hidden data).
            code_spans_present = any(
                by_col.get(col["name"], []) for col in valid_code_cols
            )
            if code_spans_present:
                residue_rows.append({
                    "reason": "matrix-empty-label-row",
                    "tableTitle": col_map.get("tableTitle", ""),
                    "spans": [
                        {"text": s["text"], "bbox": s["bbox"]}
                        for col in valid_code_cols
                        for s in by_col.get(col["name"], [])
                    ],
                })
            continue

        predicate = _norm_predicate(label_text)

        for code_col in valid_code_cols:
            cell_spans = by_col.get(code_col["name"], [])
            cell_text, cell_bbox = _stitch(cell_spans)
            if cell_text:
                code_attrs[code_col["name"]].append({
                    "predicate": predicate,
                    "value": cell_text,
                    "bbox": cell_bbox,
                })

    # Emit claims per code column
    for code_col in valid_code_cols:
        code = canon_code(code_col["name"], allow_numeric=is_instance)  # already validated above
        subject = f"{kind}:{code}"
        attrs = code_attrs[code_col["name"]]

        for attr in attrs:
            claims.append(_make_claim(
                subject=subject,
                predicate=attr["predicate"],
                value=attr["value"],
                method="schedule-parse",
                conf=0.90,
                trust="proposed",
                evidence_source=source_instrument,
                evidence_locator=attr["bbox"] if attr["bbox"] else None,
                snippet=attr["value"][:80],
                ambiguity_class=amb_class,
            ))

        claims.append(_make_claim(
            subject=subject,
            predicate="definedOnSheet",
            value=sheet_subject,
            method="schedule-parse",
            conf=0.95,
            trust="proposed",
            evidence_source=source_instrument,
            evidence_locator=None,
            snippet=sheet_subject,
            ambiguity_class=amb_class,
        ))

        if revision and revision != "unspecified":
            claims.append(_make_claim(
                subject=subject,
                predicate="partOfIssue",
                value={"label": revision},
                method="user-asserted",
                conf=0.90,
                trust="proposed",
                evidence_source="user-supplied",
                evidence_locator=None,
                snippet=revision,
                ambiguity_class=amb_class,
            ))

    return claims, residue_rows


# ---------------------------------------------------------------------------
# Predicate normalisation (clean camelCase from label text)
# ---------------------------------------------------------------------------

def _norm_predicate(raw: str) -> str:
    """Convert a column header or row label to a camelCase predicate name.

    'FIRE RATING' -> 'fireRating'
    'Trap / Waste' -> 'trapWaste'
    'SUPPLY (CW)' -> 'supplyCw'
    """
    words = re.sub(r"[^A-Za-z0-9\s]", " ", raw).split()
    if not words:
        return "unknown"
    result = words[0].lower()
    for w in words[1:]:
        result += w.capitalize()
    return result


# ---------------------------------------------------------------------------
# Ground one manifest entry
# ---------------------------------------------------------------------------

def _ground_entry(
    entry: dict,
    out_dir: Path,
) -> tuple[list[dict], list[dict], dict]:
    """Ground all column_maps for one manifest entry.

    Returns (claims, residue_rows, stats_entry).
    """
    claims: list[dict] = []
    residue_rows: list[dict] = []

    sheet_id: str = entry["sheetId"]
    page_idx: int = entry["pageIdx"]
    source_instrument: str = entry["sourceInstrument"]
    spans_path_rel: str | None = entry.get("spansPath")
    col_maps: list[dict] = entry.get("column_maps", [])

    if page_idx < 0 or not spans_path_rel:
        return [], [{
            "reason": "deferred-no-page-ref",
            "sheetId": sheet_id,
        }], {
            "sheetId": sheet_id,
            "pageIdx": page_idx,
            "tables": 0,
            "codes": 0,
            "claims": 0,
            "residue": 1,
        }

    if not col_maps:
        return [], [{
            "reason": "no-column-maps-provided",
            "sheetId": sheet_id,
            "pageIdx": page_idx,
        }], {
            "sheetId": sheet_id,
            "pageIdx": page_idx,
            "tables": 0,
            "codes": 0,
            "claims": 0,
            "residue": 1,
        }

    # Load spans from JSONL
    spans_path = out_dir / spans_path_rel
    spans: list[dict] = []
    if spans_path.exists():
        with spans_path.open(encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if line:
                    spans.append(json.loads(line))
    else:
        return [], [{
            "reason": f"spans-file-not-found: {spans_path}",
            "sheetId": sheet_id,
        }], {
            "sheetId": sheet_id,
            "pageIdx": page_idx,
            "tables": 0,
            "codes": 0,
            "claims": 0,
            "residue": 1,
        }

    # Ground each table
    n_tables = 0
    for col_map in col_maps:
        layout = col_map.get("layout", "tabular")
        if layout == "matrix":
            t_claims, t_residue = _ground_matrix(
                col_map, spans, source_instrument, sheet_id, REVISION
            )
        else:
            t_claims, t_residue = _ground_tabular(
                col_map, spans, source_instrument, sheet_id, REVISION
            )

        claims.extend(t_claims)
        for r in t_residue:
            r.setdefault("sheetId", sheet_id)
            r.setdefault("pageIdx", page_idx)
            residue_rows.append(r)
        n_tables += 1

    # Count distinct code subjects (non-meta predicates)
    meta_predicates = {"locatedAt", "definedOnSheet", "partOfIssue"}
    code_subjects = {
        c["subject"] for c in claims
        if c["predicate"] not in meta_predicates
    }

    return claims, residue_rows, {
        "sheetId": sheet_id,
        "pageIdx": page_idx,
        "tables": n_tables,
        "codes": len(code_subjects),
        "claims": len(claims),
        "residue": len(residue_rows),
    }


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    out_dir = Path(OUT_DIR)
    manifest_path = out_dir / "schedule_prepare_manifest.json"
    if not manifest_path.exists():
        sys.exit(
            f"[error] manifest not found: {manifest_path}\n"
            "Run schedule_prepare.py first, then fill 'column_maps' entries."
        )

    with manifest_path.open(encoding="utf-8") as fh:
        manifest: list[dict] = json.load(fh)

    # Check that at least some column_maps are filled
    filled = [e for e in manifest if e.get("column_maps")]
    if not filled:
        sys.exit(
            "[error] No column_maps found in manifest -- fill them in first.\n"
            "Each entry needs 'column_maps' populated by the agent column-map phase."
        )

    print("=" * 80)
    print(f"SCHEDULE GROUND  |  {SET_TAG}  |  revision: {REVISION}")
    print(f"Manifest: {manifest_path}  ({len(manifest)} entries, {len(filled)} with column_maps)")
    print("-" * 80)

    all_claims: list[dict] = []
    all_residue: list[dict] = []
    all_stats: list[dict] = []

    for entry in manifest:
        claims, residue, stats = _ground_entry(entry, out_dir)
        all_claims.extend(claims)
        all_residue.extend(residue)
        all_stats.append(stats)

        meta_predicates = {"locatedAt", "definedOnSheet", "partOfIssue"}
        code_subjects = {
            c["subject"] for c in claims
            if c["predicate"] not in meta_predicates
        }
        n_codes = len(code_subjects)
        tables = stats["tables"]
        status = (
            "DEFERRED" if entry.get("pageIdx", -1) < 0
            else ("NO-MAP" if not entry.get("column_maps") else
                  ("GROUNDED" if not residue else "GROUNDED+RESIDUE"))
        )
        print(f"  {entry['sheetId']:20s}  pg {entry['pageIdx']:4}  "
              f"{tables} tables  {n_codes:3d} codes  {len(claims):4d} claims  "
              f"{len(residue):2d} residue  [{status}]")

    # Write outputs
    out_claims = out_dir / "schedule_claims.jsonl"
    with out_claims.open("w", encoding="utf-8") as fh:
        for c in all_claims:
            fh.write(json.dumps(c) + "\n")

    out_residue = out_dir / "schedule_ground_residue.json"
    with out_residue.open("w", encoding="utf-8") as fh:
        json.dump(all_residue, fh, indent=2)

    out_stats = out_dir / "schedule_ground_stats.json"
    with out_stats.open(encoding="utf-8", mode="w") as fh:
        json.dump(all_stats, fh, indent=2)

    # Summary
    meta_predicates = {"locatedAt", "definedOnSheet", "partOfIssue"}
    total_subjects = len({
        c["subject"] for c in all_claims
        if c["predicate"] not in meta_predicates
    })
    grounded_sheets = sum(1 for s in all_stats if s["claims"] > 0)

    print("=" * 80)
    print(f"sheets with claims ........... {grounded_sheets} / {len(manifest)}")
    print(f"total distinct subjects ....... {total_subjects}")
    print(f"total claims .................. {len(all_claims)}")
    print(f"total residue entries ......... {len(all_residue)}")
    print(f"zero invented ................. TRUE (every cell traced to a real span)")
    print("-" * 80)
    print(f"schedule_claims.jsonl ......... {out_claims}")
    print(f"schedule_ground_residue.json .. {out_residue}")
    print(f"schedule_ground_stats.json .... {out_stats}")
    print("=" * 80)


if __name__ == "__main__":
    main()
