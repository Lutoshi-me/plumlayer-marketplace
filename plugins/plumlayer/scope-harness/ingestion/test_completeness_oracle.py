"""
test_completeness_oracle.py -- pytest coverage for completeness_oracle.py.

Tests the pure-transform parts against synthetic fixtures. No confidential data -- all project
names, codes, sheet numbers, and scope text are fabricated.

Covers:
  - build_scope_corpus: text-predicate concatenation, evidence exclusion, non-scopeItem skip
  - contains_token: word-boundary correctness -- standalone hits, digit-run false-positive
    rejection, dash/dot-containing codes (RF-1, A-10.02-style), sentence-final punctuation
  - csi_spaced_form: 6-digit unspaced -> spaced conversion, non-CSI-shaped codes return None
  - code_referenced_by: plain and spaced-form matching against the scope corpus
  - classify_completeness: accounted / unaccounted / ambiguous partition -- cross-kind collision,
    short-code collision, the mutually-exclusive bucket sum
  - package_enrolls_code / build_package_definitions / code_enrolled_in_packages: the package-bundle
    membership primitives -- enrollment via primary trade code, via the codes[] bundle array,
    first-seen tie-break across competing bidPackageDefinition claims
  - classify_completeness_layered: falls back to classify_completeness with no packages; with
    packages, spec sections partition by bundle membership (no ambiguous-bucket treatment) while
    schedule-definition marks keep the token rule (and its ambiguous bucket) unchanged
  - render_totals / render_accounted / render_unaccounted / render_ambiguous / render_rule_per_layer:
    honest absent-layer, empty-bucket, and per-layer-rule-statement fallbacks
  - compile_report: end-to-end on a small synthetic project, with and without package claims

Stdlib + pytest only. No network, no cloud, no PDF.
"""
from __future__ import annotations

import sys
from collections import OrderedDict
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent))

from completeness_oracle import (  # noqa: E402
    build_scope_corpus,
    contains_token,
    csi_spaced_form,
    code_referenced_by,
    package_enrolls_code,
    build_package_definitions,
    code_enrolled_in_packages,
    classify_completeness,
    classify_completeness_layered,
    render_totals,
    render_accounted,
    render_unaccounted,
    render_ambiguous,
    render_rule_per_layer,
    compile_report,
)
from compile_context_packet import classify_definition_subjects  # noqa: E402


def _claim(subject, predicate, value, ambiguity_class=None, evidence=None):
    c = {
        "subject": subject,
        "predicate": predicate,
        "value": value,
        "evidence": evidence or [{"source": "fixture", "method": "test", "snippet": str(value)}],
        "trustClass": "proposed",
        "confidence": 0.9,
        "status": "current",
        "assertedBy": "test_completeness_oracle.py",
        "promotedBy": None,
    }
    if ambiguity_class:
        c["ambiguityClass"] = ambiguity_class
    return c


# ---------------------------------------------------------------------------
# build_scope_corpus
# ---------------------------------------------------------------------------

class TestBuildScopeCorpus:
    def test_concatenates_text_predicates(self):
        claims = [
            _claim("scopeItem:1", "name", "Package room refrigerator"),
            _claim("scopeItem:1", "description", "Commercial unit, key RF-1."),
            _claim("scopeItem:1", "category", "Appliances"),  # not a text predicate
            _claim("scopeItem:1", "notesInternal", "See also A-10.02."),
        ]
        corpus = build_scope_corpus(claims)
        assert corpus["scopeItem:1"]["name"] == "Package room refrigerator"
        text = corpus["scopeItem:1"]["text"]
        assert "Package room refrigerator" in text
        assert "key RF-1." in text
        assert "A-10.02" in text
        assert "Appliances" not in text  # category is not a matched predicate

    def test_evidence_snippets_excluded(self):
        claims = [
            _claim(
                "scopeItem:1", "name", "Door package",
                evidence=[{"source": "fixture", "method": "agent-read", "snippet": "RF-1 EVIDENCE ONLY TOKEN"}],
            ),
        ]
        corpus = build_scope_corpus(claims)
        assert "EVIDENCE ONLY TOKEN" not in corpus["scopeItem:1"]["text"]

    def test_non_scope_item_subjects_skipped(self):
        claims = [
            _claim("project", "projectType", "office"),
            _claim("doorType:D1", "description", "hollow metal"),
            _claim("scopeItem:1", "name", "Real scope item"),
        ]
        corpus = build_scope_corpus(claims)
        assert list(corpus.keys()) == ["scopeItem:1"]

    def test_no_name_is_honest_none(self):
        claims = [_claim("scopeItem:1", "description", "no name deposited for this one")]
        corpus = build_scope_corpus(claims)
        assert corpus["scopeItem:1"]["name"] is None


# ---------------------------------------------------------------------------
# contains_token -- word-boundary correctness
# ---------------------------------------------------------------------------

class TestContainsToken:
    def test_standalone_hit(self):
        assert contains_token("Commercial refrigerator, key RF-1.", "RF-1") is True

    def test_sentence_final_punctuation_still_matches(self):
        # Real 150 Main scope text ends a clause right at the code: "...Key RF-1."
        assert contains_token("Same appliance package. Key RF-1.", "RF-1") is True

    def test_not_fooled_by_longer_digit_run(self):
        assert contains_token("See RF-15 for the alternate model.", "RF-1") is False

    def test_not_fooled_by_longer_numeric_prefix(self):
        assert contains_token("spec 1042000 is unrelated", "042000") is False
        assert contains_token("spec 0420001 is unrelated", "042000") is False

    def test_dash_dot_code_standalone_hit(self):
        assert contains_token("Refer to sheet A-10.02 for the detail.", "A-10.02") is True

    def test_dash_dot_code_not_present(self):
        assert contains_token("Refer to sheet A-10.03 for the detail.", "A-10.02") is False

    def test_absent_token(self):
        assert contains_token("Nothing relevant in this description.", "RF-1") is False

    def test_parenthesized_hit(self):
        assert contains_token("Induction cooktop (RA-1) black finish.", "RA-1") is True


# ---------------------------------------------------------------------------
# csi_spaced_form
# ---------------------------------------------------------------------------

class TestCsiSpacedForm:
    def test_six_digit_code_converts(self):
        assert csi_spaced_form("042000") == "04 20 00"

    def test_non_numeric_code_returns_none(self):
        assert csi_spaced_form("RF-1") is None

    def test_wrong_length_returns_none(self):
        assert csi_spaced_form("4200") is None
        assert csi_spaced_form("0420001") is None


# ---------------------------------------------------------------------------
# code_referenced_by
# ---------------------------------------------------------------------------

class TestCodeReferencedBy:
    def test_plain_form_match(self):
        corpus = OrderedDict([
            ("scopeItem:1", {"name": "Summary of work", "text": "Per spec 011000 general requirements."}),
        ])
        hits = code_referenced_by("011000", corpus)
        assert hits == [("scopeItem:1", "Summary of work")]

    def test_spaced_form_match(self):
        corpus = OrderedDict([
            ("scopeItem:1", {"name": "Masonry restoration", "text": "Governed by spec 04 20 00 unit masonry."}),
        ])
        hits = code_referenced_by("042000", corpus)
        assert hits == [("scopeItem:1", "Masonry restoration")]

    def test_no_match(self):
        corpus = OrderedDict([
            ("scopeItem:1", {"name": "Unrelated item", "text": "No spec numbers here at all."}),
        ])
        assert code_referenced_by("042000", corpus) == []

    def test_multiple_items_match(self):
        corpus = OrderedDict([
            ("scopeItem:1", {"name": "Item one", "text": "Key RF-1."}),
            ("scopeItem:2", {"name": "Item two", "text": "Also references RF-1 here."}),
        ])
        hits = code_referenced_by("RF-1", corpus)
        assert hits == [("scopeItem:1", "Item one"), ("scopeItem:2", "Item two")]


# ---------------------------------------------------------------------------
# classify_completeness -- the partition
# ---------------------------------------------------------------------------

class TestClassifyCompleteness:
    def test_accounted_when_token_found(self):
        # Code is 3+ chars so the short-code rule doesn't also fire -- this
        # isolates the plain accounted path (see test_short_code_is_ambiguous_
        # even_when_matched for the <=2-char case).
        definitions = classify_definition_subjects([
            _claim("doorType:D101", "description", "single leaf hollow metal"),
            _claim("doorType:D101", "definedOnSheet", "sheet:A-10"),
        ])
        corpus = build_scope_corpus([
            _claim("scopeItem:1", "name", "Unit entry door"),
            _claim("scopeItem:1", "description", "Hollow metal single leaf, type D101."),
        ])
        buckets = classify_completeness(definitions, corpus)
        assert "doorType:D101" in buckets["accounted"]
        assert buckets["accounted"]["doorType:D101"]["matchedBy"] == [("scopeItem:1", "Unit entry door")]
        assert buckets["unaccounted"] == {}
        assert buckets["ambiguous"] == {}

    def test_unaccounted_when_token_absent(self):
        definitions = classify_definition_subjects([
            _claim("doorType:D109", "description", "double leaf fire-rated"),
        ])
        corpus = build_scope_corpus([
            _claim("scopeItem:1", "name", "Unrelated appliance item"),
        ])
        buckets = classify_completeness(definitions, corpus)
        assert "doorType:D109" in buckets["unaccounted"]
        assert buckets["accounted"] == {}

    def test_cross_kind_collision_is_ambiguous_not_accounted(self):
        definitions = classify_definition_subjects([
            _claim("doorType:A-1", "description", "storefront door"),
            _claim("plumbingFixtureType:A-1", "description", "ADA lavatory"),
        ])
        corpus = build_scope_corpus([
            _claim("scopeItem:1", "name", "Lobby fixture package"),
            _claim("scopeItem:1", "description", "Includes fixture A-1 per schedule."),
        ])
        buckets = classify_completeness(definitions, corpus)
        assert "doorType:A-1" in buckets["ambiguous"]
        assert "plumbingFixtureType:A-1" in buckets["ambiguous"]
        assert buckets["accounted"] == {}
        assert "also defined as kind(s): plumbingFixtureType" in buckets["ambiguous"]["doorType:A-1"]["reason"]

    def test_short_code_is_ambiguous_even_when_matched(self):
        definitions = classify_definition_subjects([
            _claim("doorType:A", "description", "generic door mark"),
        ])
        corpus = build_scope_corpus([
            _claim("scopeItem:1", "name", "Door package"),
            _claim("scopeItem:1", "description", "Type A door throughout."),
        ])
        buckets = classify_completeness(definitions, corpus)
        assert "doorType:A" in buckets["ambiguous"]
        assert "short code" in buckets["ambiguous"]["doorType:A"]["reason"]
        assert buckets["accounted"] == {}

    def test_buckets_partition_every_definition_exactly_once(self):
        definitions = classify_definition_subjects([
            _claim("doorType:D1", "description", "hollow metal"),
            _claim("doorType:D2", "description", "wood single leaf"),
            _claim("doorType:A-1", "description", "storefront"),
            _claim("plumbingFixtureType:A-1", "description", "ADA lavatory"),
            _claim("doorType:X", "description", "short mark"),
        ])
        corpus = build_scope_corpus([
            _claim("scopeItem:1", "name", "Unit doors"),
            _claim("scopeItem:1", "description", "All D1 unit entry doors."),
        ])
        buckets = classify_completeness(definitions, corpus)
        total = len(buckets["accounted"]) + len(buckets["unaccounted"]) + len(buckets["ambiguous"])
        assert total == len(definitions)


# ---------------------------------------------------------------------------
# Package-bundle membership primitives
# ---------------------------------------------------------------------------

class TestPackageEnrollsCode:
    def test_enrolled_via_codes_bundle(self):
        package = {"projectId": "p1", "trade": "04 00 00", "codes": ["042000", "042613"], "name": "Masonry"}
        assert package_enrolls_code(package, "042613") is True

    def test_enrolled_via_primary_trade_code(self):
        # Single-section package: "codes" carries just the primary, but the
        # primary-trade match must also work standalone (package-identity-
        # design.md SS4: "absent = single-section package").
        package = {"projectId": "p1", "trade": "02 41 00", "codes": [], "name": "Demolition"}
        assert package_enrolls_code(package, "024100") is True

    def test_primary_trade_code_match_ignores_spacing(self):
        package = {"projectId": "p1", "trade": "07 84 00", "codes": [], "name": "Firestopping"}
        assert package_enrolls_code(package, "078400") is True

    def test_not_enrolled(self):
        package = {"projectId": "p1", "trade": "04 00 00", "codes": ["042000"], "name": "Masonry"}
        assert package_enrolls_code(package, "099000") is False

    def test_empty_codes_and_unrelated_trade(self):
        package = {"projectId": "p1", "trade": "31 00 00", "codes": [], "name": "Earthwork"}
        assert package_enrolls_code(package, "260000") is False


class TestBuildPackageDefinitions:
    def test_extracts_one_value_per_subject(self):
        claims = [
            _claim(
                "bidPackage:p1:04 00 00", "bidPackageDefinition",
                {"projectId": "p1", "trade": "04 00 00", "codes": ["042000"], "name": "Masonry"},
            ),
            _claim(
                "bidPackage:p1:26 00 00", "bidPackageDefinition",
                {"projectId": "p1", "trade": "26 00 00", "codes": ["260000"], "name": "Electrical"},
            ),
        ]
        packages = build_package_definitions(claims)
        assert len(packages) == 2
        assert {p["name"] for p in packages} == {"Masonry", "Electrical"}

    def test_first_seen_tie_break_on_competing_claims(self):
        claims = [
            _claim(
                "bidPackage:p1:04 00 00", "bidPackageDefinition",
                {"projectId": "p1", "trade": "04 00 00", "codes": ["042000"], "name": "Masonry (first)"},
            ),
            _claim(
                "bidPackage:p1:04 00 00", "bidPackageDefinition",
                {"projectId": "p1", "trade": "04 00 00", "codes": ["042000", "044200"], "name": "Masonry (second)"},
            ),
        ]
        packages = build_package_definitions(claims)
        assert len(packages) == 1
        assert packages[0]["name"] == "Masonry (first)"

    def test_empty_input(self):
        assert build_package_definitions([]) == []


class TestCodeEnrolledInPackages:
    def test_returns_subject_name_tuples(self):
        packages = [
            {"projectId": "p1", "trade": "04 00 00", "codes": ["042000", "044200"], "name": "Masonry"},
            {"projectId": "p1", "trade": "26 00 00", "codes": ["260000"], "name": "Electrical"},
        ]
        assert code_enrolled_in_packages("044200", packages) == [("04 00 00", "Masonry")]

    def test_no_match_returns_empty(self):
        packages = [{"projectId": "p1", "trade": "26 00 00", "codes": ["260000"], "name": "Electrical"}]
        assert code_enrolled_in_packages("042000", packages) == []


# ---------------------------------------------------------------------------
# classify_completeness_layered -- the package-bundle mode
# ---------------------------------------------------------------------------

class TestClassifyCompletenessLayered:
    def test_no_packages_falls_back_to_token_rule(self):
        definitions = classify_definition_subjects([
            _claim("specSection:042000", "hasTitle", "Unit Masonry"),
        ])
        corpus = build_scope_corpus([
            _claim("scopeItem:1", "name", "Masonry item"),
            _claim("scopeItem:1", "description", "Governed by spec 04 20 00."),
        ])
        without_packages = classify_completeness_layered(definitions, corpus, packages=None)
        via_token_rule = classify_completeness(definitions, corpus)
        assert list(without_packages["accounted"]) == list(via_token_rule["accounted"])
        assert list(without_packages["unaccounted"]) == list(via_token_rule["unaccounted"])

        with_empty_list = classify_completeness_layered(definitions, corpus, packages=[])
        assert list(with_empty_list["accounted"]) == list(via_token_rule["accounted"])

    def test_spec_section_accounted_via_bundle_ignores_absent_scope_text(self):
        definitions = classify_definition_subjects([
            _claim("specSection:042000", "hasTitle", "Unit Masonry"),
        ])
        corpus = build_scope_corpus([
            _claim("scopeItem:1", "name", "Unrelated item"),
            _claim("scopeItem:1", "description", "Nothing about masonry here."),
        ])
        packages = [{"projectId": "p1", "trade": "04 00 00", "codes": ["042000"], "name": "Masonry"}]
        buckets = classify_completeness_layered(definitions, corpus, packages)
        assert "specSection:042000" in buckets["accounted"]
        assert buckets["accounted"]["specSection:042000"]["matchedBy"] == [("04 00 00", "Masonry")]

    def test_spec_section_unbundled_is_residue_even_if_token_matches(self):
        # Scope text DOES reference "09 90 00", but with packages supplied the
        # spec layer no longer uses the token rule -- unbundled means residue.
        definitions = classify_definition_subjects([
            _claim("specSection:099000", "hasTitle", "Painting and Coating"),
        ])
        corpus = build_scope_corpus([
            _claim("scopeItem:1", "name", "Paint item"),
            _claim("scopeItem:1", "description", "Per spec 09 90 00."),
        ])
        packages = [{"projectId": "p1", "trade": "04 00 00", "codes": ["042000"], "name": "Masonry"}]
        buckets = classify_completeness_layered(definitions, corpus, packages)
        assert "specSection:099000" in buckets["unaccounted"]
        assert buckets["accounted"] == {}

    def test_spec_section_short_code_is_not_ambiguous_in_package_mode(self):
        # A hypothetical 2-char specSection code would be ambiguous-bucketed
        # under the token rule, but package mode is a structural lookup, not
        # a text search -- the short-code caveat does not apply to it.
        definitions = classify_definition_subjects([
            _claim("specSection:01", "hasTitle", "General"),
        ])
        corpus = build_scope_corpus([])
        packages = [{"projectId": "p1", "trade": "01", "codes": ["01"], "name": "General Conditions"}]
        buckets = classify_completeness_layered(definitions, corpus, packages)
        assert "specSection:01" in buckets["accounted"]
        assert buckets["ambiguous"] == {}

    def test_schedule_marks_keep_token_rule_and_ambiguous_bucket_in_package_mode(self):
        definitions = classify_definition_subjects([
            _claim("doorType:D101", "description", "single leaf hollow metal"),
            _claim("doorType:A", "description", "short mark"),
            _claim("specSection:042000", "hasTitle", "Unit Masonry"),
        ])
        corpus = build_scope_corpus([
            _claim("scopeItem:1", "name", "Unit entry doors"),
            _claim("scopeItem:1", "description", "Type D101 doors and type A doors throughout."),
        ])
        packages = [{"projectId": "p1", "trade": "04 00 00", "codes": ["042000"], "name": "Masonry"}]
        buckets = classify_completeness_layered(definitions, corpus, packages)
        assert "doorType:D101" in buckets["accounted"]
        assert buckets["accounted"]["doorType:D101"]["matchedBy"] == [("scopeItem:1", "Unit entry doors")]
        assert "doorType:A" in buckets["ambiguous"]  # short-code rule still applies to schedule marks
        assert "specSection:042000" in buckets["accounted"]
        assert buckets["accounted"]["specSection:042000"]["matchedBy"] == [("04 00 00", "Masonry")]

    def test_buckets_still_partition_every_definition_exactly_once(self):
        definitions = classify_definition_subjects([
            _claim("doorType:D101", "description", "hollow metal"),
            _claim("doorType:A", "description", "short mark"),
            _claim("specSection:042000", "hasTitle", "Unit Masonry"),
            _claim("specSection:099000", "hasTitle", "Painting and Coating"),
        ])
        corpus = build_scope_corpus([])
        packages = [{"projectId": "p1", "trade": "04 00 00", "codes": ["042000"], "name": "Masonry"}]
        buckets = classify_completeness_layered(definitions, corpus, packages)
        total = len(buckets["accounted"]) + len(buckets["unaccounted"]) + len(buckets["ambiguous"])
        assert total == len(definitions)


# ---------------------------------------------------------------------------
# Rendering -- honesty fallbacks
# ---------------------------------------------------------------------------

class TestRenderTotals:
    def test_reports_absent_layers(self):
        text = "\n".join(render_totals(OrderedDict(), OrderedDict([
            ("accounted", {}), ("unaccounted", {}), ("ambiguous", {}),
        ]), 0, schedule_present=False, spec_present=False))
        assert "Schedule-definition layer: not supplied" in text
        assert "Spec-section layer: not supplied" in text

    def test_kind_breakdown(self):
        definitions = classify_definition_subjects([
            _claim("doorType:D1", "description", "hollow metal"),
            _claim("specSection:012345", "hasTitle", "Summary of Work"),
        ])
        buckets = classify_completeness(definitions, OrderedDict())
        text = "\n".join(render_totals(definitions, buckets, 0, schedule_present=True, spec_present=True))
        assert "doorType: 1" in text
        assert "specSection: 1" in text


class TestRenderAccounted:
    def test_empty_is_honest(self):
        text = "\n".join(render_accounted(OrderedDict()))
        assert "(none accounted)" in text

    def test_row_rendered_with_match(self):
        accounted = OrderedDict([
            ("doorType:D1", {
                "code": "D1", "kind": "doorType", "name": "hollow metal", "where": "sheet:A-10",
                "flagged": False, "division": None,
                "matchedBy": [("scopeItem:1", "Unit entry door")],
            }),
        ])
        text = "\n".join(render_accounted(accounted))
        assert "| D1 | doorType | hollow metal | Unit entry door (scopeItem:1) |" in text


class TestRenderUnaccounted:
    def test_empty_is_honest(self):
        text = "\n".join(render_unaccounted(OrderedDict()))
        assert "none unaccounted" in text

    def test_row_rendered(self):
        unaccounted = OrderedDict([
            ("doorType:D9", {
                "code": "D9", "kind": "doorType", "name": None, "where": "sheet:A-11",
                "flagged": False, "division": None,
            }),
        ])
        text = "\n".join(render_unaccounted(unaccounted))
        assert "| D9 | doorType | (no description deposited) | sheet:A-11 |" in text


class TestRenderAmbiguous:
    def test_empty_is_honest(self):
        text = "\n".join(render_ambiguous(OrderedDict()))
        assert "none ambiguous" in text

    def test_row_rendered_with_reason(self):
        ambiguous = OrderedDict([
            ("doorType:A-1", {
                "code": "A-1", "kind": "doorType", "name": "storefront", "where": "sheet:A-10",
                "flagged": False, "division": None,
                "reason": "code 'A-1' also defined as kind(s): plumbingFixtureType",
            }),
        ])
        text = "\n".join(render_ambiguous(ambiguous))
        assert "| A-1 | doorType | storefront | code 'A-1' also defined as kind(s): plumbingFixtureType |" in text


class TestRenderRulePerLayer:
    def test_no_packages_states_token_rule_for_spec_layer(self):
        text = "\n".join(render_rule_per_layer(package_mode_active=False, package_count=0))
        assert "Spec-section layer: scope-text token rule (no --package-claims supplied)." in text
        assert "Schedule-definition layer: scope-text token rule, unchanged either way." in text

    def test_packages_active_states_bundle_rule_with_count(self):
        text = "\n".join(render_rule_per_layer(package_mode_active=True, package_count=44))
        assert "Spec-section layer: package-bundle membership (44 package definitions supplied" in text
        assert "Schedule-definition layer: scope-text token rule, unchanged either way." in text


# ---------------------------------------------------------------------------
# End-to-end
# ---------------------------------------------------------------------------

class TestCompileReport:
    def test_end_to_end_small_project(self):
        schedule_claims = [
            _claim("doorType:D101", "description", "single leaf hollow metal"),
            _claim("doorType:D101", "definedOnSheet", "sheet:A-10"),
            _claim("doorType:D109", "description", "double leaf fire-rated"),
            _claim("doorType:D109", "definedOnSheet", "sheet:A-10"),
            _claim("door:101A", "roomName", "OFFICE", ambiguity_class="instance"),
        ]
        spec_claims = [
            _claim("specSection:081100", "hasTitle", "Hollow Metal Doors and Frames"),
            _claim("specSection:081100", "inDivision", "08"),
        ]
        scope_claims = [
            _claim("scopeItem:1", "name", "Unit entry doors"),
            _claim("scopeItem:1", "description", "Hollow metal single leaf, type D101, per 08 11 00."),
        ]
        report = compile_report(
            schedule_claims, spec_claims, scope_claims, [],
            "Fixture Project", "proj-test-1", "2026-01-01",
        )
        assert "# Fixture Project -- Completeness Oracle Report" in report
        assert "This report is a projection" in report
        assert "| D101 | doorType | single leaf hollow metal | Unit entry doors (scopeItem:1) |" in report
        assert "| D109 | doorType | double leaf fire-rated | sheet:A-10 |" in report  # unaccounted
        assert "081100" in report  # accounted via spaced-form match on "08 11 00"
        assert "door:101A" not in report  # instance subject excluded upstream
        assert "Spec-section layer: scope-text token rule (no --package-claims supplied)." in report

    def test_absent_layers_and_no_scope_items_stay_honest(self):
        report = compile_report([], [], [], [], "Sparse Project", "proj-sparse", "2026-01-01")
        assert "Schedule-definition layer: not supplied" in report
        assert "Spec-section layer: not supplied" in report
        assert "(none accounted)" in report
        assert "none unaccounted" in report
        assert "none ambiguous" in report

    def test_package_bundle_mode_end_to_end(self):
        # Same door/spec fixture as above, but with a package that enrolls
        # 081100 via its codes[] bundle -- spec sections should now partition
        # by package membership, not scope-text token match, while the door
        # marks (schedule-definition kind) are untouched.
        schedule_claims = [
            _claim("doorType:D101", "description", "single leaf hollow metal"),
            _claim("doorType:D101", "definedOnSheet", "sheet:A-10"),
        ]
        spec_claims = [
            _claim("specSection:081100", "hasTitle", "Hollow Metal Doors and Frames"),
            _claim("specSection:081100", "inDivision", "08"),
            _claim("specSection:079200", "hasTitle", "Joint Sealants"),
            _claim("specSection:079200", "inDivision", "07"),
        ]
        scope_claims = [
            _claim("scopeItem:1", "name", "Unit entry doors"),
            _claim("scopeItem:1", "description", "Hollow metal single leaf, type D101."),
        ]
        package_claims = [
            _claim(
                "bidPackage:proj-test-1:08 10 00", "bidPackageDefinition",
                {"projectId": "proj-test-1", "trade": "08 10 00", "codes": ["081100"], "name": "Doors, Frames & Hardware"},
            ),
        ]
        report = compile_report(
            schedule_claims, spec_claims, scope_claims, package_claims,
            "Fixture Project", "proj-test-1", "2026-01-01",
        )
        assert "package-bundle membership (1 package definitions supplied" in report
        assert "| 081100 | specSection | Hollow Metal Doors and Frames | Doors, Frames & Hardware (08 10 00) |" in report
        assert "| 079200 | specSection | Joint Sealants | (not grounded) |" in report  # unbundled residue
        assert "| D101 | doorType | single leaf hollow metal | Unit entry doors (scopeItem:1) |" in report
