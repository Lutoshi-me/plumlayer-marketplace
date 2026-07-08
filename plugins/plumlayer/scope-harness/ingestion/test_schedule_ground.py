"""
test_schedule_ground.py -- pytest coverage for schedule_ground.py.

Tests the pure ground-phase functions against synthetic fixtures.
No confidential data — all codes, values, and column names are fabricated.

Covers:
  - canon_code: valid marks, invalid inputs, triple-hyphen extension (E-36-D1)
  - _cluster_rows: y-band grouping, tolerance, greedy merge
  - _assign_column: span-to-column assignment by x-interval, slop, outside-all
  - _stitch: multi-span cell join (text order, bbox union)
  - _norm_predicate: camelCase normalisation
  - _ground_tabular: full table grounding on a synthetic fixture
  - _ground_tabular continuation-row merge: empty-key rows merge into parent
  - _ground_tabular instance-table flag: ambiguityClass:"instance" on all claims
  - _ground_matrix: code-column matrix on synthetic fixture
  - _ground_entry: end-to-end with JSONL span file + manifest entry
  - zero-invented assertion: all claim values traced to input span text

Stdlib + pytest only. No PDF, no network, no cloud.
"""

from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent))

from schedule_ground import (  # noqa: E402
    canon_code,
    _cluster_rows,
    _assign_column,
    _stitch,
    _norm_predicate,
    _split_collided_rows,
    _wrapped_key_buckets,
    _ground_tabular,
    _ground_matrix,
    _ground_entry,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _span(text: str, x0: float, y0: float, x1: float, y1: float) -> dict:
    """Build a synthetic span dict in the same shape the ground phase expects."""
    return {"text": text, "bbox": [x0, y0, x1, y1]}


META_PREDS = {"locatedAt", "definedOnSheet", "partOfIssue"}


def _attr_claims(claims: list[dict]) -> list[dict]:
    """Return only attribute (non-meta) claims."""
    return [c for c in claims if c["predicate"] not in META_PREDS]


# ---------------------------------------------------------------------------
# canon_code
# ---------------------------------------------------------------------------

class TestCanonCode:
    # --- valid marks ---
    def test_simple_alpha_digit(self):
        assert canon_code("A1") == "A1"

    def test_hyphen_digit(self):
        assert canon_code("F-1") == "F-1"

    def test_four_letter_prefix(self):
        assert canon_code("DOAS-1") == "DOAS-1"

    def test_trailing_alpha(self):
        assert canon_code("P-1A") == "P-1A"

    def test_all_alpha_short(self):
        assert canon_code("HM") == "HM"
        assert canon_code("U") == "U"

    def test_double_hyphen_numeric(self):
        assert canon_code("WD-1-4") == "WD-1-4"

    # --- triple-hyphen extension (refinement 1) ---
    def test_triple_hyphen_alpha_digit(self):
        """E-36-D1 style: alpha-digit after the second hyphen."""
        assert canon_code("E-36-D1") == "E-36-D1"
        assert canon_code("E-36-D8") == "E-36-D8"
        assert canon_code("A-12-B3") == "A-12-B3"

    # --- letter-only-suffix codes (FD-A, RD-B, OFD-A) ---
    def test_letter_hyphen_letter(self):
        """FD-A, RD-B, OFD-A style: alpha prefix + hyphen + 1-3 alpha."""
        assert canon_code("FD-A") == "FD-A"
        assert canon_code("RD-B") == "RD-B"
        assert canon_code("AD-A") == "AD-A"
        assert canon_code("OFD-A") == "OFD-A"
        assert canon_code("TD-A") == "TD-A"

    # --- unit-prefix codes (U-CW-1, U-AP-10, U-FX-1A) ---
    def test_unit_prefix_codes(self):
        """U-CW-1, U-AP-10, U-FX-1A style: alpha + alpha-segment + digit."""
        assert canon_code("U-CW-1") == "U-CW-1"
        assert canon_code("U-AP-10") == "U-AP-10"
        assert canon_code("U-FX-1A") == "U-FX-1A"
        assert canon_code("U-FL-3") == "U-FL-3"

    # --- unit-prefix with trailing alt suffix (U-SH-1-ALT) ---
    def test_unit_prefix_alt_suffix(self):
        """U-SH-1-ALT style: alpha + alpha-segment + digit + alpha-suffix."""
        assert canon_code("U-SH-1-ALT") == "U-SH-1-ALT"

    # --- denylist (note-words that match the regex but are not marks) ---
    def test_denylist_note_words_rejected(self):
        """Common note abbreviations must not become schedule subjects."""
        for word in ("NTS", "TYP", "YES", "NO", "TBD", "EQ", "AFF", "NIC", "VIF",
                     "GC", "PC", "EC", "MC", "SEE", "BY", "OR", "OF"):
            with pytest.raises(ValueError, match="denylist"):
                canon_code(word)

    def test_short_marks_not_on_denylist_accepted(self):
        """Legit short marks that resemble note-words must still pass."""
        # HM, STD, U are real marks not on the denylist
        assert canon_code("HM") == "HM"
        assert canon_code("U") == "U"
        assert canon_code("STD") == "STD"

    # --- invalid marks ---
    def test_empty(self):
        with pytest.raises(ValueError):
            canon_code("")

    def test_pure_numeric(self):
        with pytest.raises(ValueError):
            canon_code("162")

    def test_too_long(self):
        with pytest.raises(ValueError):
            canon_code("ABCDEFGHIJKLMNOPQRSTUVWXYZ")

    def test_has_space(self):
        with pytest.raises(ValueError):
            canon_code("B05 EMR")

    def test_three_hyphens(self):
        with pytest.raises(ValueError):
            canon_code("A-1-2-3")

    def test_uppercase_normalise(self):
        assert canon_code("p-2") == "P-2"

    def test_multi_char_trailing(self):
        # Only one trailing alpha allowed
        with pytest.raises(ValueError):
            canon_code("P-1AB")


# ---------------------------------------------------------------------------
# _cluster_rows
# ---------------------------------------------------------------------------

class TestClusterRows:
    def test_empty(self):
        assert _cluster_rows([]) == []

    def test_single(self):
        s = _span("X", 0, 10, 5, 20)   # cy = 15
        rows = _cluster_rows([s])
        assert len(rows) == 1
        assert rows[0] == [s]

    def test_two_close_rows_merge(self):
        """cy differ by 5pt (within ROW_Y_TOL=6)."""
        a = _span("A", 0, 10, 5, 20)   # cy=15
        b = _span("B", 0, 12, 5, 22)   # cy=17
        rows = _cluster_rows([a, b])
        assert len(rows) == 1
        assert set(s["text"] for s in rows[0]) == {"A", "B"}

    def test_two_separate_rows(self):
        """cy differ by 20pt (outside ROW_Y_TOL=6)."""
        a = _span("A", 0, 10, 5, 20)   # cy=15
        b = _span("B", 0, 40, 5, 50)   # cy=45
        rows = _cluster_rows([a, b])
        assert len(rows) == 2

    def test_three_row_table(self):
        rows_in = [
            _span("R1", 0, 10, 5, 20),  # cy=15
            _span("R2", 0, 30, 5, 40),  # cy=35
            _span("R3", 0, 50, 5, 60),  # cy=55
        ]
        rows = _cluster_rows(rows_in)
        assert len(rows) == 3

    def test_row_order_by_y(self):
        """Result rows are ordered top-to-bottom."""
        a = _span("A", 0, 50, 5, 60)  # cy=55 -- lower on page
        b = _span("B", 0, 10, 5, 20)  # cy=15 -- higher on page
        rows = _cluster_rows([a, b])
        # First row should be the one with cy=15
        assert rows[0][0]["text"] == "B"
        assert rows[1][0]["text"] == "A"


# ---------------------------------------------------------------------------
# _assign_column
# ---------------------------------------------------------------------------

class TestAssignColumn:
    @pytest.fixture
    def key_col(self):
        return {"name": "code", "xLeft": 0.0, "xRight": 100.0}

    @pytest.fixture
    def cols(self):
        return [
            {"name": "descr", "xLeft": 100.0, "xRight": 300.0},
            {"name": "size",  "xLeft": 300.0, "xRight": 400.0},
        ]

    def test_assigns_to_key(self, key_col, cols):
        s = _span("X", 40, 0, 60, 10)  # cx=50 -> key
        assert _assign_column(s, key_col, cols) == "code"

    def test_assigns_to_first_attr(self, key_col, cols):
        s = _span("X", 150, 0, 250, 10)  # cx=200 -> descr
        assert _assign_column(s, key_col, cols) == "descr"

    def test_assigns_to_second_attr(self, key_col, cols):
        s = _span("X", 320, 0, 380, 10)  # cx=350 -> size
        assert _assign_column(s, key_col, cols) == "size"

    def test_outside_returns_none(self, key_col, cols):
        s = _span("X", 410, 0, 450, 10)  # cx=430 -> outside all
        assert _assign_column(s, key_col, cols) is None

    def test_slop_catches_slightly_outside(self, key_col, cols):
        """Span cx=401 is 1pt past xRight=400 but within X_SLOP_PT=4."""
        s = _span("X", 398, 0, 404, 10)  # cx=401
        # Should assign to "size" (xRight=400, slop=4 -> passes)
        assert _assign_column(s, key_col, cols) == "size"


# ---------------------------------------------------------------------------
# _stitch
# ---------------------------------------------------------------------------

class TestStitch:
    def test_empty(self):
        text, bbox = _stitch([])
        assert text == ""
        assert bbox == []

    def test_single_span(self):
        s = _span("PELICAN", 100, 10, 200, 20)
        text, bbox = _stitch([s])
        assert text == "PELICAN"
        assert bbox == [100.0, 10.0, 200.0, 20.0]

    def test_two_spans_left_to_right(self):
        a = _span("SEE", 100, 10, 130, 20)   # cy=15
        b = _span("FLOOR", 140, 10, 190, 20)  # cy=15, further right
        text, bbox = _stitch([b, a])  # order shouldn't matter, sorts by cy then cx
        assert text == "SEE FLOOR"
        assert bbox[0] == 100.0   # leftmost x0
        assert bbox[2] == 190.0   # rightmost x1

    def test_two_spans_top_to_bottom(self):
        """Multi-line cell: sorted by cy then cx."""
        a = _span("SEE FLOOR", 100, 10, 190, 20)   # cy=15
        b = _span("PLANS", 140, 25, 180, 35)        # cy=30
        text, bbox = _stitch([b, a])
        assert text == "SEE FLOOR PLANS"

    def test_bbox_is_union(self):
        a = _span("A", 10, 5, 50, 15)
        b = _span("B", 60, 20, 100, 30)
        _, bbox = _stitch([a, b])
        assert bbox == [10.0, 5.0, 100.0, 30.0]


# ---------------------------------------------------------------------------
# _norm_predicate
# ---------------------------------------------------------------------------

class TestNormPredicate:
    def test_fire_rating(self):
        assert _norm_predicate("FIRE RATING") == "fireRating"

    def test_trap_waste_slash(self):
        assert _norm_predicate("TRAP / WASTE") == "trapWaste"

    def test_single_word(self):
        assert _norm_predicate("MANUFACTURER") == "manufacturer"

    def test_with_parens(self):
        assert _norm_predicate("SUPPLY (CW)") == "supplyCw"

    def test_empty(self):
        assert _norm_predicate("") == "unknown"

    def test_preserves_digit(self):
        # Numbers in predicate names should stay
        assert _norm_predicate("ZONE 1") == "zone1"


# ---------------------------------------------------------------------------
# _ground_tabular -- basic extraction
# ---------------------------------------------------------------------------

def _make_tabular_col_map(
    kind: str = "lightingType",
    table_type: str = "definition",
    region_bbox: list = None,
) -> dict:
    """Return a minimal col_map for a 3-column synthetic fixture table."""
    return {
        "tableTitle": "SYNTHETIC LIGHTING SCHEDULE",
        "kind": kind,
        "tableType": table_type,
        "layout": "tabular",
        "regionBbox": region_bbox or [0.0, 0.0, 500.0, 200.0],
        "headerRowCount": 1,
        "keyColumn": {"name": "type", "xLeft": 0.0, "xRight": 100.0},
        "columns": [
            {"name": "manufacturer", "xLeft": 100.0, "xRight": 250.0},
            {"name": "watts",        "xLeft": 250.0, "xRight": 350.0},
        ],
    }


def _make_tabular_spans() -> list[dict]:
    """
    Synthetic 3-row schedule:
      Header row at y=10: "TYPE", "MANUFACTURER", "WATTS"
      Data row 1 at y=30: "LC-1", "ACME CO", "40W"
      Data row 2 at y=50: "LC-2", "BRIGHTCO", "60W"
      Data row 3 at y=70: "LC-3", "DIMCO", "25W"
    """
    return [
        # header row
        _span("TYPE",         10,  5, 80, 15),
        _span("MANUFACTURER", 110,  5, 240, 15),
        _span("WATTS",        260,  5, 340, 15),
        # data row 1
        _span("LC-1",  10, 25, 70, 35),
        _span("ACME CO", 110, 25, 220, 35),
        _span("40W",   260, 25, 320, 35),
        # data row 2
        _span("LC-2",  10, 45, 70, 55),
        _span("BRIGHTCO", 110, 45, 230, 55),
        _span("60W",   260, 45, 320, 55),
        # data row 3
        _span("LC-3",  10, 65, 70, 75),
        _span("DIMCO", 110, 65, 200, 75),
        _span("25W",   260, 65, 320, 75),
    ]


class TestGroundTabularBasic:
    @pytest.fixture
    def col_map(self):
        return _make_tabular_col_map()

    @pytest.fixture
    def spans(self):
        return _make_tabular_spans()

    def test_extracts_three_codes(self, col_map, spans):
        claims, residue = _ground_tabular(col_map, spans, "SET/0", "sheet:A-01", "IFC")
        codes = {c["subject"] for c in _attr_claims(claims)}
        assert codes == {"lightingType:LC-1", "lightingType:LC-2", "lightingType:LC-3"}

    def test_no_residue(self, col_map, spans):
        _, residue = _ground_tabular(col_map, spans, "SET/0", "sheet:A-01", "IFC")
        assert residue == []

    def test_attribute_claim_shape(self, col_map, spans):
        claims, _ = _ground_tabular(col_map, spans, "SET/0", "sheet:A-01", "IFC")
        # Find the manufacturer claim for LC-1
        c = next(x for x in claims
                 if x["subject"] == "lightingType:LC-1" and x["predicate"] == "manufacturer")
        assert c["value"] == "ACME CO"
        assert c["trustClass"] == "proposed"
        assert c["evidence"][0]["method"] == "schedule-parse"
        assert "bboxPts" in c["evidence"][0]["locator"]
        assert c.get("ambiguityClass") is None

    def test_located_at_claim(self, col_map, spans):
        claims, _ = _ground_tabular(col_map, spans, "SET/0", "sheet:A-01", "IFC")
        loc = next(x for x in claims
                   if x["subject"] == "lightingType:LC-1" and x["predicate"] == "locatedAt")
        assert loc["value"]["sheetId"] == "sheet:A-01"
        assert "bbox" in loc["value"]

    def test_defined_on_sheet_claim(self, col_map, spans):
        claims, _ = _ground_tabular(col_map, spans, "SET/0", "sheet:A-01", "IFC")
        dos = next(x for x in claims
                   if x["subject"] == "lightingType:LC-2" and x["predicate"] == "definedOnSheet")
        assert dos["value"] == "sheet:A-01"

    def test_all_values_in_input_spans(self, col_map, spans):
        """Zero-invented: every claim value must appear in the input span texts."""
        input_texts = {s["text"] for s in spans}
        claims, _ = _ground_tabular(col_map, spans, "SET/0", "sheet:A-01", "IFC")
        for c in _attr_claims(claims):
            v = c["value"]
            if isinstance(v, str):
                # The value may be a stitch of multiple spans; each part in input_texts
                for part in v.split():
                    assert any(part in t for t in input_texts), (
                        f"Claim value {v!r} not traceable to any input span"
                    )

    def test_deterministic(self, col_map, spans):
        """Same input -> identical output."""
        claims1, _ = _ground_tabular(col_map, spans, "SET/0", "sheet:A-01", "IFC")
        claims2, _ = _ground_tabular(col_map, spans, "SET/0", "sheet:A-01", "IFC")
        assert json.dumps(claims1) == json.dumps(claims2)


# ---------------------------------------------------------------------------
# _ground_tabular -- continuation-row merge (refinement 3)
# ---------------------------------------------------------------------------

class TestContinuationRowMerge:
    """Continuation rows (empty key cell) must merge into the previous code row."""

    def _col_map(self) -> dict:
        return {
            "tableTitle": "FIXTURE SCHEDULE",
            "kind": "plumbingFixtureType",
            "tableType": "definition",
            "layout": "tabular",
            "regionBbox": [0.0, 0.0, 500.0, 300.0],
            "headerRowCount": 1,
            "keyColumn": {"name": "designation", "xLeft": 0.0, "xRight": 100.0},
            "columns": [
                {"name": "description",  "xLeft": 100.0, "xRight": 250.0},
                {"name": "areaLocation", "xLeft": 250.0, "xRight": 350.0},
            ],
        }

    def test_continuation_merges_area_location(self):
        """
        P-1 row spans two y-bands:
          y=30: "P-1"   "WATER CLOSET"   "SEE FLOOR"
          y=50: (blank) (blank)           "PLANS"
        """
        spans = [
            # header
            _span("DESIGNATION", 10, 5, 80, 15),
            _span("DESCRIPTION", 110, 5, 230, 15),
            _span("AREA LOCATION", 260, 5, 340, 15),
            # data row 1 (key row)
            _span("P-1",          10, 25, 60, 35),
            _span("WATER CLOSET", 110, 25, 210, 35),
            _span("SEE FLOOR",    260, 25, 340, 35),
            # data row 1 continuation (empty designation)
            _span("PLANS",        260, 45, 310, 55),  # same col as "SEE FLOOR"
            # data row 2
            _span("P-2",          10, 70, 60, 80),
            _span("LAVATORY",     110, 70, 190, 80),
            _span("SEE FLOOR",    260, 70, 340, 80),
        ]
        claims, residue = _ground_tabular(self._col_map(), spans, "SET/337", "sheet:P-002", "IFC")

        # A pure continuation row (no attribute spans in the continuation except the
        # areaLocation text "PLANS") should NOT produce "leading-continuation-no-parent"
        # since code_rows is non-empty at that point.  It should merge silently.
        leading = [r for r in residue if r.get("reason") == "leading-continuation-no-parent"]
        assert leading == [], f"Unexpected leading-continuation residue: {leading}"

        # P-1's areaLocation should be "SEE FLOOR PLANS" (merged across two y-bands)
        p1_area = next(
            c for c in claims
            if c["subject"] == "plumbingFixtureType:P-1" and c["predicate"] == "areaLocation"
        )
        assert p1_area["value"] == "SEE FLOOR PLANS"
        # P-2 must also be captured
        subjects = {c["subject"] for c in _attr_claims(claims)}
        assert "plumbingFixtureType:P-2" in subjects

    def test_multiple_continuation_rows(self):
        """Comments column spans 3 continuation y-bands."""
        spans = [
            # header
            _span("TYPE",    10, 5, 80, 15),
            _span("COMMENT", 110, 5, 400, 15),
            # key row
            _span("LC-1", 10, 25, 70, 35),
            _span("1. SEE DRAWINGS.", 110, 25, 380, 35),
            # continuation 1
            _span("2. PROVIDE DIMMER.", 110, 45, 380, 55),
            # continuation 2
            _span("3. VERIFY WITH EE.", 110, 65, 380, 75),
        ]
        col_map = {
            "tableTitle": "LIGHTING SCHEDULE",
            "kind": "lightingType",
            "tableType": "definition",
            "layout": "tabular",
            "regionBbox": [0.0, 0.0, 500.0, 200.0],
            "headerRowCount": 1,
            "keyColumn": {"name": "type",    "xLeft": 0.0,   "xRight": 100.0},
            "columns":   [{"name": "comment", "xLeft": 100.0, "xRight": 450.0}],
        }
        claims, residue = _ground_tabular(col_map, spans, "SET/0", "sheet:A-01", "IFC")

        # Mid-table continuation rows (with a parent code row present) merge silently —
        # no residue emitted regardless of whether they carry attribute spans.
        assert residue == [], f"Unexpected residue from mid-table continuations: {residue}"
        c = next(x for x in claims
                 if x["subject"] == "lightingType:LC-1" and x["predicate"] == "comment")
        # All three numbered comments joined
        assert "1. SEE DRAWINGS." in c["value"]
        assert "2. PROVIDE DIMMER." in c["value"]
        assert "3. VERIFY WITH EE." in c["value"]

    def test_leading_continuation_no_attr_spans_goes_to_residue(self):
        """A leading continuation with NO attribute spans emits leading-continuation-no-parent."""
        spans = [
            # header
            _span("TYPE", 10, 5, 80, 15),
            _span("DESC", 110, 5, 230, 15),
            # blank row: no key, no attr spans (falls entirely outside both columns)
            _span("NOTE", 360, 25, 390, 35),  # outside desc column (xRight=350)
            # first real code row
            _span("LC-1", 10, 45, 70, 55),
            _span("ACME", 110, 45, 200, 55),
        ]
        col_map = {
            "tableTitle": "LIGHTING",
            "kind": "lightingType",
            "tableType": "definition",
            "layout": "tabular",
            "regionBbox": [0.0, 0.0, 400.0, 100.0],
            "headerRowCount": 1,
            "keyColumn": {"name": "type", "xLeft": 0.0,   "xRight": 100.0},
            "columns":   [{"name": "desc", "xLeft": 100.0, "xRight": 350.0}],
        }
        claims, residue = _ground_tabular(col_map, spans, "SET/0", "sheet:A-01", "IFC")
        reasons = [r["reason"] for r in residue]
        assert "leading-continuation-no-parent" in reasons

    def test_leading_continuation_with_attr_spans_emits_diagnostic_reason(self):
        """A leading continuation WITH attribute spans emits key-cell-empty-has-attribute-spans.

        This distinguishes a misaligned-key-column situation (the real key fell into
        an attribute column) from a true blank-leading-header row.
        """
        spans = [
            # header
            _span("TYPE", 10, 5, 80, 15),
            _span("DESC", 110, 5, 230, 15),
            # leading row: empty key column, has content in desc column
            _span("ORPHAN TEXT", 110, 25, 200, 35),
            # first real code row
            _span("LC-1", 10, 45, 70, 55),
            _span("ACME", 110, 45, 200, 55),
        ]
        col_map = {
            "tableTitle": "LIGHTING",
            "kind": "lightingType",
            "tableType": "definition",
            "layout": "tabular",
            "regionBbox": [0.0, 0.0, 400.0, 100.0],
            "headerRowCount": 1,
            "keyColumn": {"name": "type", "xLeft": 0.0,   "xRight": 100.0},
            "columns":   [{"name": "desc", "xLeft": 100.0, "xRight": 350.0}],
        }
        claims, residue = _ground_tabular(col_map, spans, "SET/0", "sheet:A-01", "IFC")
        reasons = [r["reason"] for r in residue]
        # Should use the diagnostic reason, NOT the generic continuation reason
        assert "key-cell-empty-has-attribute-spans" in reasons, (
            f"Expected key-cell-empty-has-attribute-spans in {reasons}"
        )
        assert "leading-continuation-no-parent" not in reasons
        # LC-1 must still be captured (orphan row does not block it)
        subjects = {c["subject"] for c in _attr_claims(claims)}
        assert "lightingType:LC-1" in subjects


# ---------------------------------------------------------------------------
# _ground_tabular -- instance-table flag (refinement 2)
# ---------------------------------------------------------------------------

class TestInstanceTableFlag:
    """tableType:'instance' adds ambiguityClass:'instance' to all claims."""

    def test_instance_claims_flagged(self):
        col_map = _make_tabular_col_map(
            kind="door",
            table_type="instance",
        )
        spans = _make_tabular_spans()
        # Swap marks to door-like codes (the fixture uses LC-x which pass canon_code)
        claims, _ = _ground_tabular(col_map, spans, "SET/12", "sheet:A-09", "IFC")
        attr_claims = _attr_claims(claims)
        assert len(attr_claims) > 0
        for c in claims:
            assert c.get("ambiguityClass") == "instance", (
                f"Expected ambiguityClass:'instance' on {c['predicate']} but got {c.get('ambiguityClass')!r}"
            )

    def test_definition_claims_not_flagged(self):
        col_map = _make_tabular_col_map(kind="lightingType", table_type="definition")
        spans = _make_tabular_spans()
        claims, _ = _ground_tabular(col_map, spans, "SET/0", "sheet:A-01", "IFC")
        for c in claims:
            assert c.get("ambiguityClass") is None, (
                f"Definition table claim should not have ambiguityClass, got {c.get('ambiguityClass')!r}"
            )

    def test_instance_kind_namespace(self):
        """kind:'door' (not 'doorType') used for instance tables."""
        col_map = _make_tabular_col_map(kind="door", table_type="instance")
        spans = _make_tabular_spans()
        claims, _ = _ground_tabular(col_map, spans, "SET/12", "sheet:A-09", "IFC")
        subjects = {c["subject"] for c in _attr_claims(claims)}
        # All subjects should use 'door:' prefix
        assert all(s.startswith("door:") for s in subjects)


# ---------------------------------------------------------------------------
# _ground_tabular -- triple-hyphen codes (refinement 1)
# ---------------------------------------------------------------------------

class TestTripleHyphenCodes:
    """E-36-D1 style codes must be extracted, not gated to residue."""

    def test_triple_hyphen_extracts(self):
        col_map = {
            "tableTitle": "UNIT DOOR TYPES",
            "kind": "doorType",
            "tableType": "definition",
            "layout": "tabular",
            "regionBbox": [0.0, 0.0, 400.0, 200.0],
            "headerRowCount": 1,
            "keyColumn": {"name": "type", "xLeft": 0.0, "xRight": 80.0},
            "columns": [{"name": "description", "xLeft": 80.0, "xRight": 350.0}],
        }
        spans = [
            _span("DOOR TYPE",      5, 5, 75, 15),
            _span("DESCRIPTION",   85, 5, 340, 15),
            _span("E-36-D1",        5, 25, 70, 35),
            _span("UNIT TERRACE 1", 85, 25, 300, 35),
            _span("E-36-D2",        5, 45, 70, 55),
            _span("UNIT TERRACE 2", 85, 45, 300, 55),
        ]
        claims, residue = _ground_tabular(col_map, spans, "SET/0", "sheet:A-09", "IFC")
        codes = {c["subject"] for c in _attr_claims(claims)}
        assert "doorType:E-36-D1" in codes
        assert "doorType:E-36-D2" in codes
        # No canon_code-fail residue
        fails = [r for r in residue if "canon_code-fail" in r.get("reason", "")]
        assert fails == []


# ---------------------------------------------------------------------------
# _ground_matrix
# ---------------------------------------------------------------------------

class TestGroundMatrix:
    """Matrix layout: codes across top row, attribute labels down the left."""

    def _col_map(self) -> dict:
        return {
            "tableTitle": "HARDWARE MATRIX",
            "kind": "hardwareSetType",
            "tableType": "definition",
            "layout": "matrix",
            "regionBbox": [0.0, 0.0, 400.0, 200.0],
            "headerRowCount": 1,
            "keyColumn": {"name": "attribute", "xLeft": 0.0, "xRight": 100.0},
            "columns": [
                {"name": "H1", "xLeft": 100.0, "xRight": 200.0},
                {"name": "H2", "xLeft": 200.0, "xRight": 300.0},
            ],
        }

    def _spans(self) -> list[dict]:
        """
        Header:  | attribute | H1  | H2  |
        Row 1:   | CLOSER    | YES | YES |
        Row 2:   | LOCKSET   | NO  | YES |
        """
        return [
            # header row (y=5-15)
            _span("attribute", 10,  5, 90, 15),
            _span("H1",       110,  5, 190, 15),
            _span("H2",       210,  5, 290, 15),
            # data row 1 (y=25-35)
            _span("CLOSER",   10, 25, 90, 35),
            _span("YES",      110, 25, 190, 35),
            _span("YES",      210, 25, 290, 35),
            # data row 2 (y=45-55)
            _span("LOCKSET",  10, 45, 90, 55),
            _span("NO",       110, 45, 190, 55),
            _span("YES",      210, 45, 290, 55),
        ]

    def test_extracts_two_code_subjects(self):
        claims, residue = _ground_matrix(self._col_map(), self._spans(), "SET/0", "sheet:A-09", "IFC")
        codes = {c["subject"] for c in _attr_claims(claims)}
        assert codes == {"hardwareSetType:H1", "hardwareSetType:H2"}

    def test_attribute_values(self):
        claims, _ = _ground_matrix(self._col_map(), self._spans(), "SET/0", "sheet:A-09", "IFC")
        h1_closer = next(c for c in claims
                         if c["subject"] == "hardwareSetType:H1" and c["predicate"] == "closer")
        assert h1_closer["value"] == "YES"
        h1_lockset = next(c for c in claims
                          if c["subject"] == "hardwareSetType:H1" and c["predicate"] == "lockset")
        assert h1_lockset["value"] == "NO"

    def test_no_residue(self):
        _, residue = _ground_matrix(self._col_map(), self._spans(), "SET/0", "sheet:A-09", "IFC")
        assert residue == []

    def test_matrix_outside_column_spans_emitted_to_residue(self):
        """Spans outside all matrix column intervals must appear in residue (not silently dropped)."""
        spans = self._spans() + [
            # Span at x=350-390, outside all columns (label: 0-100, H1: 100-200, H2: 200-300)
            _span("EXTRA", 355, 25, 385, 35),
        ]
        _, residue = _ground_matrix(self._col_map(), spans, "SET/0", "sheet:A-09", "IFC")
        outside = [r for r in residue if r["reason"] == "matrix-spans-outside-columns"]
        assert outside, "Expected matrix-spans-outside-columns residue but got none"
        all_outside_texts = [s["text"] for r in outside for s in r["spans"]]
        assert "EXTRA" in all_outside_texts

    def test_matrix_empty_label_row_with_code_content_emitted_to_residue(self):
        """An empty-label matrix row that carries code-column content must appear in residue."""
        spans = self._spans() + [
            # Row at y=65-75: empty label column, has data in H1 column
            _span("EXTRA-VAL", 115, 65, 185, 75),
        ]
        _, residue = _ground_matrix(self._col_map(), spans, "SET/0", "sheet:A-09", "IFC")
        empty_label = [r for r in residue if r["reason"] == "matrix-empty-label-row"]
        assert empty_label, "Expected matrix-empty-label-row residue but got none"
        all_texts = [s["text"] for r in empty_label for s in r["spans"]]
        assert "EXTRA-VAL" in all_texts


# ---------------------------------------------------------------------------
# _ground_entry -- end-to-end with temp JSONL files
# ---------------------------------------------------------------------------

class TestGroundEntry:
    """Full entry grounding: writes JSONL span file + manifest entry, calls _ground_entry."""

    def _write_spans(self, tmp_dir: Path, spans: list[dict], name: str) -> Path:
        p = tmp_dir / "prepare" / name
        p.parent.mkdir(parents=True, exist_ok=True)
        with p.open("w", encoding="utf-8") as fh:
            for s in spans:
                fh.write(json.dumps(s) + "\n")
        return p

    def test_basic_entry(self, tmp_path):
        spans = _make_tabular_spans()
        spans_path = self._write_spans(tmp_path, spans, "SYN_p0_spans.jsonl")

        entry = {
            "sheetId": "sheet:SYN-01",
            "pageIdx": 0,
            "sourceInstrument": "SYN/0",
            "spansPath": "prepare/SYN_p0_spans.jsonl",
            "column_maps": [_make_tabular_col_map()],
        }
        claims, residue, stats = _ground_entry(entry, tmp_path)

        assert stats["codes"] == 3
        assert stats["claims"] > 0
        assert stats["tables"] == 1

    def test_deferred_no_page_ref(self, tmp_path):
        entry = {
            "sheetId": "sheet:TW-1",
            "pageIdx": -1,
            "sourceInstrument": "p0131_TW-1",
            "spansPath": None,
            "column_maps": [],
        }
        claims, residue, stats = _ground_entry(entry, tmp_path)
        assert claims == []
        assert any("deferred" in r.get("reason", "") for r in residue)

    def test_no_column_maps(self, tmp_path):
        spans = _make_tabular_spans()
        self._write_spans(tmp_path, spans, "SYN_p1_spans.jsonl")
        entry = {
            "sheetId": "sheet:SYN-02",
            "pageIdx": 1,
            "sourceInstrument": "SYN/1",
            "spansPath": "prepare/SYN_p1_spans.jsonl",
            "column_maps": [],
        }
        claims, residue, stats = _ground_entry(entry, tmp_path)
        assert claims == []
        assert any("no-column-maps" in r.get("reason", "") for r in residue)

    def test_missing_spans_file(self, tmp_path):
        entry = {
            "sheetId": "sheet:SYN-03",
            "pageIdx": 5,
            "sourceInstrument": "SYN/5",
            "spansPath": "prepare/nonexistent_spans.jsonl",
            "column_maps": [_make_tabular_col_map()],
        }
        claims, residue, stats = _ground_entry(entry, tmp_path)
        assert claims == []
        assert any("spans-file-not-found" in r.get("reason", "") for r in residue)


# ---------------------------------------------------------------------------
# Golden determinism test
# ---------------------------------------------------------------------------

class TestGoldenDeterminism:
    """Same synthetic input must produce identical JSON output on repeated runs."""

    def test_tabular_golden(self):
        col_map = _make_tabular_col_map()
        spans = _make_tabular_spans()
        results = [
            json.dumps(
                _ground_tabular(col_map, spans, "SET/0", "sheet:TEST", "IFC")[0],
                sort_keys=True,
            )
            for _ in range(3)
        ]
        assert len(set(results)) == 1, "Non-deterministic output across runs"


# ---------------------------------------------------------------------------
# canon_code allow_numeric (fix 2) -- numeric instance keys
# ---------------------------------------------------------------------------

class TestCanonCodeAllowNumeric:
    """Pure-numeric keys pass ONLY under allow_numeric (instance tables)."""

    def test_numeric_rejected_by_default(self):
        with pytest.raises(ValueError, match="pure-numeric"):
            canon_code("162")
        with pytest.raises(ValueError, match="pure-numeric"):
            canon_code("162", allow_numeric=False)

    def test_numeric_accepted_when_allowed(self):
        assert canon_code("162", allow_numeric=True) == "162"
        assert canon_code("180", allow_numeric=True) == "180"
        assert canon_code("101", allow_numeric=True) == "101"

    def test_allow_numeric_does_not_relax_other_gates(self):
        # allow_numeric only opens the pure-numeric branch; everything else still holds.
        with pytest.raises(ValueError, match="empty"):
            canon_code("", allow_numeric=True)
        with pytest.raises(ValueError, match="too long"):
            canon_code("12345678901234567", allow_numeric=True)  # 17 digits
        with pytest.raises(ValueError, match="denylist"):
            canon_code("TYP", allow_numeric=True)

    def test_alpha_marks_still_pass_under_allow_numeric(self):
        assert canon_code("D4", allow_numeric=True) == "D4"
        assert canon_code("P-1A", allow_numeric=True) == "P-1A"


# ---------------------------------------------------------------------------
# _split_collided_rows (fix 1) -- centroid-drift collision split
# ---------------------------------------------------------------------------

def _collision_col_map(kind: str = "equipmentType", table_type: str = "definition") -> dict:
    """3-attribute-column tabular map used by the collision fixtures."""
    return {
        "tableTitle": "COLLISION FIXTURE",
        "kind": kind,
        "tableType": table_type,
        "layout": "tabular",
        "regionBbox": [0.0, 0.0, 300.0, 80.0],
        "headerRowCount": 1,
        "keyColumn": {"name": "item", "xLeft": 0.0, "xRight": 60.0},
        "columns": [
            {"name": "mfr", "xLeft": 60.0,  "xRight": 140.0},
            {"name": "d1",  "xLeft": 140.0, "xRight": 180.0},
            {"name": "d2",  "xLeft": 180.0, "xRight": 220.0},
            {"name": "d3",  "xLeft": 220.0, "xRight": 260.0},
        ],
    }


def _collision_spans() -> list[dict]:
    """
    Two tightly-packed code rows whose key cells are ~8pt apart, mirroring the real
    P-003 HWHP-1 / HWHP-2 collision: a run of shared data spans between the two keys
    drifts the greedy centroid so _cluster_rows stitches all three y-bands into one.
      Header  cy=10 : ITEM  MFR  D1  D2  D3
      HP-1    cy=30 : HP-1  WATTS
      data    cy=35.4:            v1  v2  v3   (physically between the two keys)
      HP-2    cy=38 : HP-2  AEGIS
    """
    return [
        _span("ITEM",        10,  5, 50, 15),
        _span("MFR",         70,  5, 130, 15),
        _span("D1",         145,  5, 175, 15),
        _span("D2",         185,  5, 215, 15),
        _span("D3",         225,  5, 255, 15),
        # code row 1 (key cy=30)
        _span("HP-1",        10, 25, 50, 35),
        _span("WATTS",       70, 25, 130, 35),
        # shared data band (cy=35.4) -- drifts the centroid
        _span("v1",         145, 30.4, 175, 40.4),
        _span("v2",         185, 30.4, 215, 40.4),
        _span("v3",         225, 30.4, 255, 40.4),
        # code row 2 (key cy=38)
        _span("HP-2",        10, 33, 50, 43),
        _span("AEGIS",       70, 33, 130, 43),
    ]


class TestCollisionRowSplit:
    """A band stitched from two code rows must split into distinct subjects."""

    def test_cluster_actually_collides(self):
        """Guard: the fixture really does stitch both keys into ONE cluster."""
        # (Everything below the header — the phenomenon the split undoes.)
        data = [s for s in _collision_spans() if (s["bbox"][1] + s["bbox"][3]) / 2 > 17]
        clusters = _cluster_rows(data)
        assert len(clusters) == 1, (
            f"fixture no longer collides ({len(clusters)} clusters) — split test is moot"
        )
        # Both key cells landed in the one cluster.
        key_texts = {s["text"] for s in clusters[0] if s["text"].startswith("HP-")}
        assert key_texts == {"HP-1", "HP-2"}

    def test_split_yields_two_subrows(self):
        cmap = _collision_col_map()
        data = [s for s in _collision_spans() if (s["bbox"][1] + s["bbox"][3]) / 2 > 17]
        band = _cluster_rows(data)[0]
        subs = _split_collided_rows(band, cmap["keyColumn"], cmap["columns"])
        assert len(subs) == 2
        # Top-to-bottom order; each sub-row carries exactly one key cell.
        assert [s["text"] for s in subs[0] if s["text"].startswith("HP-")] == ["HP-1"]
        assert [s["text"] for s in subs[1] if s["text"].startswith("HP-")] == ["HP-2"]

    def test_single_key_band_unchanged(self):
        """A well-formed single-code band is returned untouched (identity)."""
        cmap = _collision_col_map()
        band = [
            _span("HP-9", 10, 25, 50, 35),
            _span("SOLO", 70, 25, 130, 35),
        ]
        subs = _split_collided_rows(band, cmap["keyColumn"], cmap["columns"])
        assert subs == [band]

    def test_empty_key_band_never_split(self):
        """A continuation band (no key span) is returned untouched, not split."""
        cmap = _collision_col_map()
        band = [
            _span("PLANS", 70, 45, 130, 55),  # mfr column only, empty key
        ]
        subs = _split_collided_rows(band, cmap["keyColumn"], cmap["columns"])
        assert subs == [band]

    def test_ground_tabular_recovers_both_codes(self):
        cmap = _collision_col_map()
        claims, residue = _ground_tabular(
            cmap, _collision_spans(), "SET/338", "sheet:P-003", "IFC"
        )
        subjects = {c["subject"] for c in _attr_claims(claims)}
        assert "equipmentType:HP-1" in subjects
        assert "equipmentType:HP-2" in subjects
        # The pre-fix failure was a single "HP-1 HP-2" canon_code-fail; it must be gone.
        fails = [r for r in residue if "canon_code-fail" in r.get("reason", "")]
        assert fails == [], f"Unexpected canon_code-fail residue: {fails}"

    def test_split_preserves_continuation_merge(self):
        """
        A continuation row BELOW a collision band must still merge UP into the
        nearest code row (proving the split and the continuation-merge coexist).
        The collision band splits into HP-1 / HP-2; a trailing 'CONTD' in the mfr
        column (empty key, cy=50) merges into HP-2.
        """
        spans = _collision_spans() + [
            _span("CONTD", 70, 45, 130, 55),  # mfr column, empty key -> continuation
        ]
        cmap = _collision_col_map()
        claims, residue = _ground_tabular(cmap, spans, "SET/338", "sheet:P-003", "IFC")

        # No leading/continuation residue: the CONTD row merges silently.
        cont_res = [
            r for r in residue
            if r.get("reason") in (
                "leading-continuation-no-parent",
                "key-cell-empty-has-attribute-spans",
            )
        ]
        assert cont_res == [], f"Continuation mis-handled after split: {cont_res}"

        hp2_mfr = next(
            c for c in claims
            if c["subject"] == "equipmentType:HP-2" and c["predicate"] == "mfr"
        )
        assert "AEGIS" in hp2_mfr["value"] and "CONTD" in hp2_mfr["value"], (
            f"continuation did not merge into HP-2.mfr: {hp2_mfr['value']!r}"
        )


# ---------------------------------------------------------------------------
# Numeric instance keys end-to-end (fix 2)
# ---------------------------------------------------------------------------

def _numeric_key_spans() -> list[dict]:
    """Two pure-numeric key rows (door-opening numbers), like A-09's door table."""
    return [
        _span("OPENING", 10,  5, 50, 15),
        _span("ROOM",    70,  5, 180, 15),
        _span("162",     10, 25, 50, 35),
        _span("LOBBY",   70, 25, 160, 35),
        _span("180",     10, 45, 50, 55),
        _span("OFFICE",  70, 45, 160, 55),
    ]


def _numeric_key_col_map(kind: str, table_type: str) -> dict:
    return {
        "tableTitle": "DOOR AND FRAME SCHEDULE",
        "kind": kind,
        "tableType": table_type,
        "layout": "tabular",
        "regionBbox": [0.0, 0.0, 200.0, 70.0],
        "headerRowCount": 1,
        "keyColumn": {"name": "opening", "xLeft": 0.0, "xRight": 60.0},
        "columns": [{"name": "room", "xLeft": 60.0, "xRight": 200.0}],
    }


class TestNumericInstanceKeys:
    def test_instance_table_recovers_numeric_codes(self):
        cmap = _numeric_key_col_map(kind="door", table_type="instance")
        claims, residue = _ground_tabular(
            cmap, _numeric_key_spans(), "SET/12", "sheet:A-09", "IFC"
        )
        subjects = {c["subject"] for c in _attr_claims(claims)}
        assert subjects == {"door:162", "door:180"}
        # Numeric keys must NOT show up as pure-numeric residue anymore.
        pn = [r for r in residue if "pure-numeric" in r.get("reason", "")]
        assert pn == [], f"Unexpected pure-numeric residue on instance table: {pn}"
        # Instance claims carry the ambiguityClass flag.
        assert all(c.get("ambiguityClass") == "instance" for c in claims)

    def test_definition_table_still_rejects_numeric_keys(self):
        cmap = _numeric_key_col_map(kind="doorType", table_type="definition")
        claims, residue = _ground_tabular(
            cmap, _numeric_key_spans(), "SET/12", "sheet:A-09", "IFC"
        )
        subjects = {c["subject"] for c in _attr_claims(claims)}
        assert subjects == set(), "Definition table must not mint numeric subjects"
        pn = [r for r in residue if "pure-numeric" in r.get("reason", "")]
        assert len(pn) == 2, f"Expected both numeric rows flagged, got {pn}"


# ---------------------------------------------------------------------------
# Header depth (fix 3) -- arbitrary header depth, uncapped
# ---------------------------------------------------------------------------

class TestHeaderDepth:
    """headerRowCount is uncapped: a 4-tier header strips cleanly to the data rows."""

    def _spans(self) -> list[dict]:
        return [
            # 4 stacked header rows (cy = 10, 20, 30, 40)
            _span("MECHANICAL",  70, 5, 130, 15),
            _span("EQUIPMENT",   70, 15, 130, 25),
            _span("SCHEDULE",    70, 25, 130, 35),
            _span("TYPE",        10, 35, 50, 45),
            _span("DESCRIPTION", 70, 35, 190, 45),
            # data rows (cy = 60, 75)
            _span("E-1",  10, 55, 50, 65),
            _span("PUMP", 70, 55, 160, 65),
            _span("E-2",  10, 70, 50, 80),
            _span("FAN",  70, 70, 160, 80),
        ]

    def _col_map(self, header_rows: int) -> dict:
        return {
            "tableTitle": "MECHANICAL EQUIPMENT SCHEDULE",
            "kind": "equipmentType",
            "tableType": "definition",
            "layout": "tabular",
            "regionBbox": [0.0, 0.0, 220.0, 90.0],
            "headerRowCount": header_rows,
            "keyColumn": {"name": "type", "xLeft": 0.0, "xRight": 60.0},
            "columns": [{"name": "description", "xLeft": 60.0, "xRight": 220.0}],
        }

    def test_four_tier_header_stripped(self):
        claims, residue = _ground_tabular(
            self._col_map(header_rows=4), self._spans(), "SET/0", "sheet:H-01", "IFC"
        )
        subjects = {c["subject"] for c in _attr_claims(claims)}
        assert subjects == {"equipmentType:E-1", "equipmentType:E-2"}
        # No header token leaked in as a subject.
        assert not any("TYPE" in s or "SCHEDULE" in s for s in subjects)
        # E-1's description grounded from the data row, not a header row.
        desc = next(
            c for c in claims
            if c["subject"] == "equipmentType:E-1" and c["predicate"] == "description"
        )
        assert desc["value"] == "PUMP"

    def test_deeper_header_count_consumes_more_rows(self):
        """headerRowCount is honoured for any N: bumping it to 5 eats the first data row."""
        claims, _ = _ground_tabular(
            self._col_map(header_rows=5), self._spans(), "SET/0", "sheet:H-01", "IFC"
        )
        subjects = {c["subject"] for c in _attr_claims(claims)}
        # 5 header clusters strips through E-1's band; only E-2 survives -- proving the
        # count is applied mechanically with no cap at 2.
        assert subjects == {"equipmentType:E-2"}


# ---------------------------------------------------------------------------
# Wrapped-key path (PLU-309 A2, Fix 1) -- keyColumn.wrapped stacking
# ---------------------------------------------------------------------------

def _wrapped_col_map(kind: str = "equipmentType", wrapped: bool = True) -> dict:
    """Tabular map for the wrapped-key fixtures. wrapped=False omits the hint."""
    key: dict = {"name": "item", "xLeft": 0.0, "xRight": 60.0}
    if wrapped:
        key["wrapped"] = True
    return {
        "tableTitle": "WRAPPED FIXTURE",
        "kind": kind,
        "tableType": "definition",
        "layout": "tabular",
        "regionBbox": [0.0, 0.0, 300.0, 120.0],
        "headerRowCount": 1,
        "keyColumn": key,
        "columns": [
            {"name": "mfr", "xLeft": 60.0,  "xRight": 140.0},
            {"name": "cap", "xLeft": 140.0, "xRight": 220.0},
        ],
    }


def _wrapped_spans() -> list[dict]:
    """
    Two codes, each key wrapped across two stacked lines (~11pt apart), row pitch ~36pt:
      Header cy=10  : ITEM  MFR  CAP
      HP-A   cy 29.5: 'HP' over 'A'    data ACME / 40
      HP-B   cy 65.5: 'HP' over 'B'    data AEGIS / 60
    """
    return [
        _span("ITEM", 10,  5,  50, 15),
        _span("MFR",  70,  5, 130, 15),
        _span("CAP", 150,  5, 210, 15),
        # code row 1 (key wrapped: HP over A)
        _span("HP",   10, 25,  50, 34),   # cy 29.5
        _span("A",    10, 36,  50, 45),   # cy 40.5
        _span("ACME", 70, 31, 130, 41),   # cy 36 (mfr)
        _span("40",  150, 31, 210, 41),   # cy 36 (cap)
        # code row 2 (key wrapped: HP over B)
        _span("HP",   10, 61,  50, 70),   # cy 65.5
        _span("B",    10, 72,  50, 81),   # cy 76.5
        _span("AEGIS",70, 67, 130, 77),   # cy 72 (mfr)
        _span("60",  150, 67, 210, 77),   # cy 72 (cap)
    ]


class TestWrappedKey:
    """keyColumn.wrapped joins a stacked key cell into one code; absent, old behavior."""

    def test_wrapped_hint_joins_stack(self):
        claims, residue = _ground_tabular(
            _wrapped_col_map(wrapped=True), _wrapped_spans(), "SET/0", "sheet:M-01", "IFC"
        )
        subjects = {c["subject"] for c in _attr_claims(claims)}
        assert subjects == {"equipmentType:HP-A", "equipmentType:HP-B"}
        # The straddling data cells landed on the right code.
        hp_a_mfr = next(
            c for c in claims
            if c["subject"] == "equipmentType:HP-A" and c["predicate"] == "mfr"
        )
        assert hp_a_mfr["value"] == "ACME"
        fails = [r for r in residue if "canon_code-fail" in r.get("reason", "")]
        assert fails == [], f"Unexpected canon_code-fail: {fails}"

    def test_no_hint_is_unchanged_behavior(self):
        """Same fixture WITHOUT the hint must NOT join -- the row-cluster path runs."""
        claims, _ = _ground_tabular(
            _wrapped_col_map(wrapped=False), _wrapped_spans(), "SET/0", "sheet:M-01", "IFC"
        )
        subjects = {c["subject"] for c in _attr_claims(claims)}
        # No joined subject appears; the wrapped lines are read as separate keys.
        assert "equipmentType:HP-A" not in subjects
        assert "equipmentType:HP-B" not in subjects

    def test_wrapped_synthetic_key_grounds_to_real_bbox(self):
        """The joined code carries a bbox = union of the real key-line spans."""
        buckets = _wrapped_key_buckets(
            _wrapped_spans()[3:],  # data spans only (skip the 3 header spans)
            _wrapped_col_map()["keyColumn"],
            _wrapped_col_map()["columns"],
        )
        assert len(buckets) == 2
        # First bucket's synthetic key: text HP-A, bbox spanning y 25..45 of the two lines.
        synth = buckets[0][0]
        assert synth["text"] == "HP-A"
        assert synth["bbox"] == [10.0, 25.0, 50.0, 45.0]

    def test_mixed_wrapped_and_single_line_rows(self):
        """A table mixing a wrapped key row and a single-line key row grounds both."""
        spans = [
            _span("ITEM", 10,  5,  50, 15),
            _span("MFR",  70,  5, 130, 15),
            _span("CAP", 150,  5, 210, 15),
            # wrapped row: HP over A
            _span("HP",   10, 25,  50, 34),
            _span("A",    10, 36,  50, 45),
            _span("ACME", 70, 31, 130, 41),
            _span("40",  150, 31, 210, 41),
            # single-line row: P-5 (one key line)
            _span("P-5",  10, 61,  50, 70),   # cy 65.5
            _span("DIMCO",70, 61, 130, 71),   # cy 66
            _span("25",  150, 61, 210, 71),   # cy 66
        ]
        claims, residue = _ground_tabular(
            _wrapped_col_map(wrapped=True), spans, "SET/0", "sheet:M-02", "IFC"
        )
        subjects = {c["subject"] for c in _attr_claims(claims)}
        assert subjects == {"equipmentType:HP-A", "equipmentType:P-5"}
        assert [r for r in residue if "canon_code-fail" in r.get("reason", "")] == []

    def test_three_line_stack(self):
        """N>2 lines join in order: VRF / R / 1A -> VRF-R-1A."""
        spans = [
            _span("ITEM", 10,  5,  50, 15),
            _span("MFR",  70,  5, 130, 15),
            # 3-line wrapped key
            _span("VRF",  10, 25,  50, 34),   # cy 29.5
            _span("R",    10, 36,  50, 45),   # cy 40.5
            _span("1A",   10, 47,  50, 56),   # cy 51.5
            _span("XYZ",  70, 36, 130, 46),   # cy 41 (mfr, straddles the stack)
        ]
        col_map = {
            "tableTitle": "THREE LINE STACK",
            "kind": "equipmentType",
            "tableType": "definition",
            "layout": "tabular",
            "regionBbox": [0.0, 0.0, 300.0, 80.0],
            "headerRowCount": 1,
            "keyColumn": {"name": "item", "xLeft": 0.0, "xRight": 60.0, "wrapped": True},
            "columns": [{"name": "mfr", "xLeft": 60.0, "xRight": 140.0}],
        }
        claims, residue = _ground_tabular(col_map, spans, "SET/0", "sheet:M-03", "IFC")
        subjects = {c["subject"] for c in _attr_claims(claims)}
        assert subjects == {"equipmentType:VRF-R-1A"}
        mfr = next(
            c for c in claims
            if c["subject"] == "equipmentType:VRF-R-1A" and c["predicate"] == "mfr"
        )
        assert mfr["value"] == "XYZ"


class TestWrappedSplitCoexistence:
    """Distinct keys ~10.56pt apart (P-003 gap) must still split WITHOUT the wrapped
    hint -- proving the hint, not a y-threshold, discriminates wrap from collision."""

    def _distinct_key_spans(self) -> list[dict]:
        # Two distinct codes whose key y-centers are 10.56pt apart, each with its own
        # data cell on the same line as its key.
        return [
            _span("ITEM", 10,  5.0,  50, 15.0),
            _span("MFR",  70,  5.0, 130, 15.0),
            _span("DK-1", 10, 25.00, 50, 35.00),   # cy 30.00
            _span("M1",   70, 25.00, 130, 35.00),  # cy 30.00
            _span("DK-2", 10, 35.56, 50, 45.56),   # cy 40.56
            _span("M2",   70, 35.56, 130, 45.56),  # cy 40.56
        ]

    def _col_map(self) -> dict:
        return {
            "tableTitle": "DISTINCT KEYS",
            "kind": "equipmentType",
            "tableType": "definition",
            "layout": "tabular",
            "regionBbox": [0.0, 0.0, 200.0, 60.0],
            "headerRowCount": 1,
            "keyColumn": {"name": "item", "xLeft": 0.0, "xRight": 60.0},
            "columns": [{"name": "mfr", "xLeft": 60.0, "xRight": 140.0}],
        }

    def test_split_handles_p003_gap_directly(self):
        """_split_collided_rows separates a 10.56pt distinct-key band into two sub-rows."""
        band = self._distinct_key_spans()[2:]  # drop the header spans
        cmap = self._col_map()
        subs = _split_collided_rows(band, cmap["keyColumn"], cmap["columns"])
        assert len(subs) == 2
        assert [s["text"] for s in subs[0] if s["text"].startswith("DK-")] == ["DK-1"]
        assert [s["text"] for s in subs[1] if s["text"].startswith("DK-")] == ["DK-2"]

    def test_no_hint_yields_two_distinct_subjects(self):
        claims, _ = _ground_tabular(
            self._col_map(), self._distinct_key_spans(), "SET/0", "sheet:P-003", "IFC"
        )
        subjects = {c["subject"] for c in _attr_claims(claims)}
        assert subjects == {"equipmentType:DK-1", "equipmentType:DK-2"}


# ---------------------------------------------------------------------------
# canon_code Fix-2 regex branches (PLU-309 A2) -- residue-recovery families
# ---------------------------------------------------------------------------

class TestCanonCodeFix2Branches:
    """New _CODE_RE branches, validated zero-false-positive against the real residue."""

    def test_fused_lrp_ep_osp_family(self):
        for c in ("LRP4PH", "LRP2PH", "EP2PH", "EP4PH", "OSP2PH", "OSP4PH"):
            assert canon_code(c) == c

    def test_ef_pev_alpha_alpha_digit_family(self):
        for c in ("EF-T1", "EF-F1", "EF-L1", "EF-DOAS1", "EF-DOAS2", "EF-DOAS3",
                  "PEV-A1", "PEV-A2", "PEV-A3"):
            assert canon_code(c) == c

    def test_bc_fcu_mid_alpha_digit_family(self):
        for c in ("BC-R2-1", "BC-R4-1", "BC-R4-2", "BC-R6-1",
                  "FCU-1A-1", "FCU-1A-4", "FCU-1B-10", "FCU-1B-11", "FCU-1C-1", "FCU-1C-9"):
            assert canon_code(c) == c

    def test_csi_two_digit_two_letter_family(self):
        assert canon_code("27AV") == "27AV"
        assert canon_code("28FA") == "28FA"

    def test_fcu_four_segment_wrapped_key_family(self):
        """PLU-309 A3: FCU-1-1A-1 style, from a wrapped key cell on E-705."""
        for c in ("FCU-1-1A-1", "FCU-1-1A-4", "FCU-1-1B-1", "FCU-1-1B-10",
                  "FCU-1-1B-11", "FCU-1-1C-1", "FCU-1-1C-11"):
            assert canon_code(c) == c

    def test_fix2_negatives_still_rejected(self):
        """Real residue noise that must stay residue, plus prose and bare numerics."""
        for bad in (
            "3. 20% P.G. PRE-MIXED SOLUTION ONLY.",  # prose
            "LEVEL 1 - COMM",                        # spaced label
            "B05 EMR",                               # room-tag + space
            "DOOR TYPE",                             # header words
            "GLYCOL RECEIVING TANK.",                # equipment prose
            "GLYCOL",                                # long all-alpha word
            "MIRROR",                                # long all-alpha word
            "12,14",                                 # comma-combined
            "R-1-*",                                 # trailing asterisk (E-705 right panel)
        ):
            with pytest.raises(ValueError):
                canon_code(bad)

    def test_bare_numeric_definition_still_fails(self):
        with pytest.raises(ValueError, match="pure-numeric"):
            canon_code("100")
        with pytest.raises(ValueError, match="pure-numeric"):
            canon_code("28")   # 2-digit alone must NOT hit the CSI branch


# ---------------------------------------------------------------------------
# canon_code long-prefix shade-mark family (PLU-376 fourth instance / PLU-431 tail)
# ---------------------------------------------------------------------------

class TestCanonCodeShadeFamily:
    """Long-prefix (up to 6 letters) shade-mark branches, 150 Main A-10.02 shade schedule.
    All 9 real marks validated against schedule_ground_residue.json from the 2026-07-08
    tail run before this widening; must all pass now. Junk that was already correctly
    rejected must stay rejected -- no widening of any other branch."""

    def test_single_segment_shade_marks(self):
        for c in ("SHADE-1MA", "SHADE-2MA", "SHADE-1MI", "SHADE-2MI", "SHADE-3MI",
                  "SHADE-4MI", "SHADE-5MI", "SHADE-1DMI"):
            assert canon_code(c) == c

    def test_two_segment_shade_mark(self):
        assert canon_code("SHADE-1D-MA") == "SHADE-1D-MA"

    def test_all_nine_real_shade_marks(self):
        """The exact 9 codes PLU-431's tail run recorded as canon_code-fail residue."""
        marks = (
            "SHADE-1MA", "SHADE-2MA", "SHADE-1D-MA", "SHADE-1MI", "SHADE-2MI",
            "SHADE-3MI", "SHADE-4MI", "SHADE-5MI", "SHADE-1DMI",
        )
        assert len(marks) == 9
        for c in marks:
            assert canon_code(c) == c

    def test_shade_family_negatives_still_rejected(self):
        """Junk that must NOT be admitted by the widened alpha-prefix cap: the (ALT)
        class, section-header/prose phrases, and plain long alpha words -- none of
        these gets a semantics ruling from this change (PLU-376 stays open for them)."""
        for bad in (
            "2 - CASEWORK / MILLWORK",   # spaced label with digit prefix, not a mark
            "CAB-1 (ALT)",               # (ALT) suffix baked into the same span -- PLU-376
            "FOR FLT-1)",                # prose fragment, not a mark
            "NOTES",                     # plain 5-letter word, no hyphen/digit
            "MAIN STREET",               # multi-word phrase
            "GARAGE", "CLOSET", "MIRROR",  # plain >=5-letter words, no digit
        ):
            with pytest.raises(ValueError):
                canon_code(bad)

    def test_shade_family_does_not_admit_alt_suffix_variant(self):
        """A hypothetical 'SHADE-1MA (ALT)' single span (suffix fused into the same
        text run, same shape as the appliance (ALT) rows) must still fail -- the new
        branches require the string to END in 1-3 letters, not '(ALT)'."""
        with pytest.raises(ValueError):
            canon_code("SHADE-1MA (ALT)")


# ---------------------------------------------------------------------------
# numericKey flag (PLU-309 A2, Fix 2) -- bare-numeric DEFINITION keys per table
# ---------------------------------------------------------------------------

class TestNumericKeyFlag:
    """keyColumn.numericKey opens the bare-numeric gate on a definition table without
    the instance ambiguity tag; absent, definition tables still reject numeric keys."""

    def test_definition_numeric_key_flag_recovers(self):
        cmap = _numeric_key_col_map(kind="panelSchedule", table_type="definition")
        cmap["keyColumn"]["numericKey"] = True
        claims, residue = _ground_tabular(
            cmap, _numeric_key_spans(), "SET/9", "sheet:E-01", "IFC"
        )
        subjects = {c["subject"] for c in _attr_claims(claims)}
        assert subjects == {"panelSchedule:162", "panelSchedule:180"}
        pn = [r for r in residue if "pure-numeric" in r.get("reason", "")]
        assert pn == [], f"Unexpected pure-numeric residue: {pn}"
        # numericKey is NOT instance: definition claims carry no ambiguityClass.
        assert all(c.get("ambiguityClass") is None for c in claims)

    def test_definition_without_flag_still_rejects_numeric(self):
        cmap = _numeric_key_col_map(kind="panelSchedule", table_type="definition")
        claims, residue = _ground_tabular(
            cmap, _numeric_key_spans(), "SET/9", "sheet:E-01", "IFC"
        )
        subjects = {c["subject"] for c in _attr_claims(claims)}
        assert subjects == set()
        pn = [r for r in residue if "pure-numeric" in r.get("reason", "")]
        assert len(pn) == 2, f"Expected both numeric rows flagged, got {pn}"


# ---------------------------------------------------------------------------
# Wrapped-key zero-key-spans (PLU-309 A4) -- confirmed silent-drop fix
# ---------------------------------------------------------------------------

def _no_key_spans_col_map(wrapped: bool) -> dict:
    """Tabular map whose key column x-range [0, 60] never captures any span below."""
    key: dict = {"name": "item", "xLeft": 0.0, "xRight": 60.0}
    if wrapped:
        key["wrapped"] = True
    return {
        "tableTitle": "NO KEY SPANS FIXTURE",
        "kind": "equipmentType",
        "tableType": "definition",
        "layout": "tabular",
        "regionBbox": [0.0, 0.0, 300.0, 80.0],
        "headerRowCount": 1,
        "keyColumn": key,
        "columns": [
            {"name": "mfr", "xLeft": 60.0,  "xRight": 140.0},
            {"name": "cap", "xLeft": 140.0, "xRight": 220.0},
        ],
    }


def _no_key_spans_spans() -> list[dict]:
    """Two data rows whose spans all land in mfr/cap; nothing has an x-center inside
    the key column's [0, 60] range (+/- X_SLOP_PT=4), mirroring a mis-set keyColumn
    xLeft/xRight that captures zero spans in the data region."""
    return [
        _span("ITEM", 10,  5, 50, 15),
        _span("MFR",  70,  5, 130, 15),
        _span("CAP", 150,  5, 210, 15),
        # data row 1 -- no key-column span
        _span("ACME", 70, 25, 130, 35),
        _span("40",  150, 25, 210, 35),
        # data row 2 -- no key-column span
        _span("AEGIS", 70, 45, 130, 55),
        _span("60",   150, 45, 210, 55),
    ]


class TestWrappedNoKeySpans:
    """A wrapped-hint table whose key column captures zero spans must flag every data
    span as residue -- the pre-fix behavior silently returned [] from
    _wrapped_key_buckets and dropped the whole table (zero claims, zero residue)."""

    def test_wrapped_hint_zero_key_spans_flags_all_residue(self):
        claims, residue = _ground_tabular(
            _no_key_spans_col_map(wrapped=True), _no_key_spans_spans(),
            "SET/0", "sheet:M-04", "IFC",
        )
        assert claims == [], "No claims should be emitted with zero key spans"
        reasons = [r["reason"] for r in residue]
        assert reasons == ["wrapped-table-no-key-spans"], (
            f"Expected exactly one wrapped-table-no-key-spans entry, got {reasons}"
        )
        residue_texts = {s["text"] for s in residue[0]["spans"]}
        # All four DATA spans (not the header) must be present -- nothing dropped.
        assert residue_texts == {"ACME", "40", "AEGIS", "60"}

    def test_no_hint_same_fixture_uses_existing_key_cell_empty_path(self):
        """Without the wrapped hint, the same fixture runs the ordinary row-cluster
        path: each row has an empty key cell with attribute spans present, which
        already hits the pre-existing key-cell-empty-has-attribute-spans residue --
        proving the new reason is scoped to the wrapped path, not a general change."""
        claims, residue = _ground_tabular(
            _no_key_spans_col_map(wrapped=False), _no_key_spans_spans(),
            "SET/0", "sheet:M-04", "IFC",
        )
        assert claims == []
        reasons = {r["reason"] for r in residue}
        assert "wrapped-table-no-key-spans" not in reasons
        assert "key-cell-empty-has-attribute-spans" in reasons
