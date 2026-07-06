"""
test_compile_context_packet.py -- pytest coverage for compile_context_packet.py.

Tests the pure-transform parts against synthetic fixtures. No confidential data -- all project
names, codes, sheet numbers, and spec sections are fabricated.

Covers:
  - parse_claims_file: JSONL shape, {"claims": [...]} MCP-response shape, empty file
  - merge_claim_files: concatenation across multiple dump files, order preserved
  - index_by_subject / first_value / all_values / flag: the claim-lookup primitives
  - compile_identity / compile_systems / compile_scope_areas / compile_set_shape / compile_hazards:
    rendering + ambiguity flag + honest "nothing deposited" fallback
  - classify_definition_subjects: the instance-vs-definition split (ambiguityClass:"instance"
    exclusion), specSection handling, missing-description honesty, where-defined fallback chain
  - render_definitions_index: absent-layer honesty, table rendering, division spread
  - compile_packet: end-to-end on a small synthetic project

Stdlib + pytest only. No network, no cloud, no PDF.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent))

from compile_context_packet import (  # noqa: E402
    parse_claims_file,
    merge_claim_files,
    index_by_subject,
    first_value,
    all_values,
    flag,
    compile_identity,
    compile_systems,
    compile_scope_areas,
    compile_set_shape,
    compile_hazards,
    classify_definition_subjects,
    render_definitions_index,
    compile_packet,
    slugify,
    _format_where_defined,
)


def _claim(subject, predicate, value, ambiguity_class=None, evidence=None):
    c = {
        "subject": subject,
        "predicate": predicate,
        "value": value,
        "evidence": evidence or [{"source": "fixture", "method": "test", "snippet": str(value)}],
        "trustClass": "proposed",
        "confidence": 0.9,
        "status": "current",
        "assertedBy": "test_compile_context_packet.py",
        "promotedBy": None,
    }
    if ambiguity_class:
        c["ambiguityClass"] = ambiguity_class
    return c


# ---------------------------------------------------------------------------
# parse_claims_file / merge_claim_files
# ---------------------------------------------------------------------------

class TestParseClaimsFile:
    def test_jsonl_shape(self, tmp_path):
        p = tmp_path / "claims.jsonl"
        p.write_text(
            json.dumps(_claim("project", "projectType", "warehouse")) + "\n"
            + json.dumps(_claim("project", "grossArea", "50,000 SF")) + "\n",
            encoding="utf-8",
        )
        claims = parse_claims_file(p)
        assert len(claims) == 2
        assert claims[0]["predicate"] == "projectType"
        assert claims[1]["predicate"] == "grossArea"

    def test_mcp_search_response_shape(self, tmp_path):
        p = tmp_path / "search_result.json"
        p.write_text(json.dumps({
            "claims": [_claim("project", "projectType", "warehouse")],
            "total": 1,
        }), encoding="utf-8")
        claims = parse_claims_file(p)
        assert len(claims) == 1
        assert claims[0]["value"] == "warehouse"

    def test_empty_file(self, tmp_path):
        p = tmp_path / "empty.jsonl"
        p.write_text("", encoding="utf-8")
        assert parse_claims_file(p) == []

    def test_jsonl_skips_blank_lines(self, tmp_path):
        p = tmp_path / "claims.jsonl"
        p.write_text(
            json.dumps(_claim("project", "projectType", "office")) + "\n\n\n",
            encoding="utf-8",
        )
        assert len(parse_claims_file(p)) == 1


class TestMergeClaimFiles:
    def test_concatenates_in_order(self, tmp_path):
        p1 = tmp_path / "a.jsonl"
        p2 = tmp_path / "b.jsonl"
        p1.write_text(json.dumps(_claim("project", "projectType", "office")) + "\n", encoding="utf-8")
        p2.write_text(json.dumps(_claim("project", "grossArea", "10,000 SF")) + "\n", encoding="utf-8")
        merged = merge_claim_files([p1, p2])
        assert [c["predicate"] for c in merged] == ["projectType", "grossArea"]

    def test_empty_list(self):
        assert merge_claim_files([]) == []


# ---------------------------------------------------------------------------
# Claim-lookup primitives
# ---------------------------------------------------------------------------

class TestClaimLookup:
    def test_index_by_subject_groups(self):
        claims = [
            _claim("project", "projectType", "office"),
            _claim("doorType:D1", "description", "hollow metal single"),
            _claim("project", "grossArea", "10,000 SF"),
        ]
        by_subject = index_by_subject(claims)
        assert list(by_subject.keys()) == ["project", "doorType:D1"]
        assert len(by_subject["project"]) == 2

    def test_first_value_first_seen(self):
        claims = [
            _claim("project", "projectType", "office"),
            _claim("project", "projectType", "warehouse"),  # a competing claim
        ]
        assert first_value(claims, "projectType") == "office"

    def test_first_value_missing_predicate(self):
        assert first_value([_claim("project", "projectType", "office")], "grossArea") is None

    def test_all_values_returns_every_match_in_order(self):
        claims = [
            _claim("project", "tradeInScope", "electrical"),
            _claim("project", "projectType", "office"),
            _claim("project", "tradeInScope", "plumbing"),
        ]
        vals = [c["value"] for c in all_values(claims, "tradeInScope")]
        assert vals == ["electrical", "plumbing"]

    def test_flag_marks_ambiguous_claims_only(self):
        assert flag(_claim("project", "hazardFlag", "steep site", ambiguity_class="inferred")) == " (!)"
        assert flag(_claim("project", "hazardFlag", "steep site")) == ""


# ---------------------------------------------------------------------------
# Orientation section compilers
# ---------------------------------------------------------------------------

class TestCompileIdentity:
    def test_renders_core_fields_and_parties(self):
        claims = [
            _claim("project", "projectType", "warehouse conversion"),
            _claim("project", "location", "Anytown, XX"),
            _claim("project", "deliveryMethod", "CM-at-risk"),
            _claim("project", "grossArea", "80,000 SF"),
            _claim("project", "floorCount", "3"),
            _claim("project", "bidDueDate", "2026-08-01"),
            _claim("party:owner-co", "hasRole", "owner"),
            _claim("party:owner-co", "name", "Fixture Capital LLC"),
            _claim("project", "tradeInScope", "concrete"),
            _claim("project", "knownExclusion", "FF&E"),
        ]
        by_subject = index_by_subject(claims)
        text = "\n".join(compile_identity(by_subject, "Fixture Project", "proj-test-1"))
        assert "Fixture Project" in text
        assert "proj-test-1" in text
        assert "warehouse conversion" in text
        assert "Anytown, XX" in text
        assert "CM-at-risk" in text
        assert "80,000 SF" in text
        assert "3 floors" in text
        assert "2026-08-01" in text
        assert "Owner:" in text and "Fixture Capital LLC" in text
        assert "concrete" in text
        assert "FF&E" in text

    def test_no_claims_is_honest(self):
        by_subject = index_by_subject([])
        text = "\n".join(compile_identity(by_subject, "Empty Project", "proj-empty"))
        assert "no project-level identity claims deposited" in text


class TestCompileSystems:
    def test_renders_systems_with_flags(self):
        claims = [
            _claim("project", "structuralSystem", "steel frame", ambiguity_class="inferred"),
            _claim("project", "envelopeSystem", "brick veneer"),
            _claim("project", "mepDeliveryShape", {"division": "22", "shape": "design-build-thin"},
                   ambiguity_class="judgment"),
        ]
        by_subject = index_by_subject(claims)
        text = "\n".join(compile_systems(by_subject))
        assert "steel frame (!)" in text
        assert "brick veneer" in text
        assert "22: design-build-thin (!)" in text

    def test_absent_is_honest(self):
        text = "\n".join(compile_systems(index_by_subject([])))
        assert "no systems claims deposited" in text


class TestCompileScopeAreasSetShapeHazards:
    def test_scope_areas(self):
        claims = [
            _claim("project", "scopeArea", "below-grade parking"),
            _claim("project", "phasingNote", "phased by wing", ambiguity_class="inferred"),
        ]
        text = "\n".join(compile_scope_areas(index_by_subject(claims)))
        assert "below-grade parking" in text
        assert "phased by wing (!)" in text

    def test_scope_areas_absent(self):
        text = "\n".join(compile_scope_areas(index_by_subject([])))
        assert "no scope-area claims deposited" in text

    def test_set_shape(self):
        claims = [
            _claim("project", "setShapeObservation", "schedules live on the A-10 series"),
            _claim("project", "missingScopeFamily", "no Division 31 sections", ambiguity_class="absence"),
        ]
        text = "\n".join(compile_set_shape(index_by_subject(claims)))
        assert "schedules live on the A-10 series" in text
        assert "Missing families:" in text and "no Division 31 sections (!)" in text

    def test_set_shape_absent(self):
        text = "\n".join(compile_set_shape(index_by_subject([])))
        assert "no set-shape observations deposited" in text

    def test_hazards(self):
        claims = [_claim("project", "hazardFlag", "occupied renovation", ambiguity_class="inferred")]
        text = "\n".join(compile_hazards(index_by_subject(claims)))
        assert "occupied renovation (!)" in text

    def test_hazards_absent(self):
        text = "\n".join(compile_hazards(index_by_subject([])))
        assert "no hazard claims deposited" in text


# ---------------------------------------------------------------------------
# Definitions index (the SS4.4 core)
# ---------------------------------------------------------------------------

class TestFormatWhereDefined:
    def test_defined_on_sheet_wins(self):
        claims = [
            _claim("doorType:D1", "definedOnSheet", "sheet:A-10"),
            _claim("doorType:D1", "locatedAt", {"instrument": "x/1", "sheetId": "sheet:A-99", "bbox": [0, 0, 1, 1]}),
        ]
        assert _format_where_defined(claims) == "sheet:A-10"

    def test_located_at_sheet_id_fallback(self):
        claims = [_claim("doorType:D1", "locatedAt", {"instrument": "x/1", "sheetId": "sheet:A-10", "bbox": [0, 0, 1, 1]})]
        assert _format_where_defined(claims) == "sheet:A-10"

    def test_located_at_page_range_single_page(self):
        claims = [_claim("specSection:012345", "locatedAt", {"instrument": "proj-toc", "pageStart": 4, "pageEnd": 4})]
        assert _format_where_defined(claims) == "proj-toc p.4"

    def test_located_at_page_range_multi_page(self):
        claims = [_claim("specSection:012345", "locatedAt", {"instrument": "proj-toc", "pageStart": 4, "pageEnd": 7})]
        assert _format_where_defined(claims) == "proj-toc p.4-7"

    def test_nothing_grounded(self):
        claims = [_claim("doorType:D1", "description", "single leaf hollow metal")]
        assert _format_where_defined(claims) == "(not grounded)"


class TestClassifyDefinitionSubjects:
    def test_definition_kind_included_with_name_and_location(self):
        claims = [
            _claim("doorType:D1", "description", "single leaf hollow metal"),
            _claim("doorType:D1", "definedOnSheet", "sheet:A-10"),
        ]
        records = classify_definition_subjects(claims)
        assert "doorType:D1" in records
        rec = records["doorType:D1"]
        assert rec["code"] == "D1"
        assert rec["kind"] == "doorType"
        assert rec["name"] == "single leaf hollow metal"
        assert rec["where"] == "sheet:A-10"
        assert rec["flagged"] is False

    def test_instance_tagged_subject_excluded(self):
        claims = [
            _claim("door:101A", "roomName", "OFFICE", ambiguity_class="instance"),
            _claim("door:101A", "definedOnSheet", "sheet:A-10", ambiguity_class="instance"),
        ]
        records = classify_definition_subjects(claims)
        assert "door:101A" not in records

    def test_missing_description_is_honest_none(self):
        claims = [_claim("panelBoard:LP1", "definedOnSheet", "sheet:E-01")]
        records = classify_definition_subjects(claims)
        assert records["panelBoard:LP1"]["name"] is None

    def test_spec_section_uses_has_title_and_division(self):
        claims = [
            _claim("specSection:012345", "hasTitle", "Summary of Work"),
            _claim("specSection:012345", "inDivision", "01"),
            _claim("specSection:012345", "locatedAt", {"instrument": "proj-toc", "pageStart": 3, "pageEnd": 5}),
        ]
        records = classify_definition_subjects(claims)
        rec = records["specSection:012345"]
        assert rec["kind"] == "specSection"
        assert rec["name"] == "Summary of Work"
        assert rec["division"] == "01"
        assert rec["where"] == "proj-toc p.3-5"

    def test_non_instance_ambiguity_flags_but_keeps_subject(self):
        claims = [
            _claim("doorType:D2", "description", "double leaf, uncertain rating", ambiguity_class="reading-uncertain"),
            _claim("doorType:D2", "definedOnSheet", "sheet:A-10"),
        ]
        records = classify_definition_subjects(claims)
        assert "doorType:D2" in records
        assert records["doorType:D2"]["flagged"] is True

    def test_subject_without_colon_is_skipped(self):
        claims = [_claim("project", "projectType", "office")]
        records = classify_definition_subjects(claims)
        assert records == {}

    def test_inDivision_normalizes_int_and_str_to_zero_padded_two_digit(self):
        claims = [
            _claim("specSection:012345", "hasTitle", "Summary of Work"),
            _claim("specSection:012345", "inDivision", "00"),  # str, already zero-padded
            _claim("specSection:099000", "hasTitle", "Paints and Coatings"),
            _claim("specSection:099000", "inDivision", "9"),  # str, unpadded
            _claim("specSection:102800", "hasTitle", "Toilet Accessories"),
            _claim("specSection:102800", "inDivision", 10),  # int
            _claim("specSection:260000", "hasTitle", "Electrical"),
            _claim("specSection:260000", "inDivision", 26),  # int
        ]
        records = classify_definition_subjects(claims)
        assert records["specSection:012345"]["division"] == "00"
        assert records["specSection:099000"]["division"] == "09"
        assert records["specSection:102800"]["division"] == "10"
        assert records["specSection:260000"]["division"] == "26"


class TestRenderDefinitionsIndex:
    def test_absent_layers_are_honest(self):
        text = "\n".join(render_definitions_index({}, spec_present=False, schedule_present=False))
        assert "no schedule definitions deposited for this project" in text
        assert "spec ingestion hasn't run for this project" in text

    def test_table_rows_and_flag_marker(self):
        claims = [
            _claim("doorType:D1", "description", "single leaf hollow metal"),
            _claim("doorType:D1", "definedOnSheet", "sheet:A-10"),
            _claim("panelBoard:LP1", "definedOnSheet", "sheet:E-01"),  # no description
        ]
        records = classify_definition_subjects(claims)
        text = "\n".join(render_definitions_index(records, spec_present=False, schedule_present=True))
        assert "| D1 | doorType | single leaf hollow metal | sheet:A-10 |" in text
        assert "(no description deposited)" in text
        assert "2 defined subjects across 2 kinds" in text

    def test_division_spread_reported(self):
        claims = [
            _claim("specSection:012345", "hasTitle", "Summary of Work"),
            _claim("specSection:012345", "inDivision", "01"),
            _claim("specSection:072000", "hasTitle", "Thermal Protection"),
            _claim("specSection:072000", "inDivision", "07"),
        ]
        records = classify_definition_subjects(claims)
        text = "\n".join(render_definitions_index(records, spec_present=True, schedule_present=False))
        assert "2 sections across divisions 01, 07" in text

    def test_mixed_int_and_str_divisions_sort_and_render_without_crash(self):
        # Regression for the real-ledger bug: inDivision deposited as a zero-padded
        # str for single-digit divisions and as a plain int for double-digit ones.
        # Sorting the raw mix crashes with TypeError: '<' not supported between
        # instances of 'int' and 'str' -- normalization must land before the sort.
        claims = [
            _claim("specSection:260000", "hasTitle", "Electrical"),
            _claim("specSection:260000", "inDivision", 26),  # int
            _claim("specSection:012345", "hasTitle", "Summary of Work"),
            _claim("specSection:012345", "inDivision", "00"),  # str
            _claim("specSection:099000", "hasTitle", "Paints and Coatings"),
            _claim("specSection:099000", "inDivision", "09"),  # str
            _claim("specSection:102800", "hasTitle", "Toilet Accessories"),
            _claim("specSection:102800", "inDivision", 10),  # int
        ]
        records = classify_definition_subjects(claims)
        text = "\n".join(render_definitions_index(records, spec_present=True, schedule_present=False))
        assert "4 sections across divisions 00, 09, 10, 26" in text


# ---------------------------------------------------------------------------
# End-to-end
# ---------------------------------------------------------------------------

class TestCompilePacket:
    def test_end_to_end_small_project(self):
        project_claims = [
            _claim("project", "projectType", "office fit-out"),
            _claim("project", "location", "Anytown, XX"),
            _claim("project", "hazardFlag", "occupied floor below", ambiguity_class="inferred"),
        ]
        schedule_claims = [
            _claim("doorType:D1", "description", "single leaf hollow metal"),
            _claim("doorType:D1", "definedOnSheet", "sheet:A-10"),
            _claim("door:101A", "roomName", "OFFICE", ambiguity_class="instance"),
        ]
        spec_claims = [
            _claim("specSection:081100", "hasTitle", "Hollow Metal Doors and Frames"),
            _claim("specSection:081100", "inDivision", "08"),
            _claim("specSection:081100", "locatedAt", {"instrument": "proj-toc", "pageStart": 12, "pageEnd": 14}),
        ]
        packet = compile_packet(
            project_claims, schedule_claims, spec_claims,
            "Fixture Project", "proj-test-1", "2026-01-01",
        )
        assert "# Fixture Project -- Orientation Packet" in packet
        assert "office fit-out" in packet
        assert "occupied floor below (!)" in packet
        assert "| D1 | doorType | single leaf hollow metal | sheet:A-10 |" in packet
        assert "door:101A" not in packet  # instance subject excluded from the index
        assert "Hollow Metal Doors and Frames" in packet
        assert "This packet is a projection" in packet

    def test_absent_layers_stay_honest_end_to_end(self):
        packet = compile_packet(
            [_claim("project", "projectType", "office")], [], [],
            "Sparse Project", "proj-sparse", "2026-01-01",
        )
        assert "no schedule definitions deposited for this project" in packet
        assert "spec ingestion hasn't run for this project" in packet


class TestSlugify:
    def test_spaces_and_case(self):
        assert slugify("150 Main Street") == "150-main-street"

    def test_punctuation(self):
        assert slugify("1270 Comm. Ave!!") == "1270-comm-ave"

    def test_already_slug(self):
        assert slugify("already-a-slug") == "already-a-slug"

    def test_empty_falls_back(self):
        assert slugify("") == "project"
        assert slugify("###") == "project"
