"""
completeness_oracle.py -- the SS4.4/SS6 completeness-oracle read (PLU-351).

Doctrine role (scope-package-architecture.md SS4.4, "The completeness oracle is a query pattern
over the same layer, not the packet"): enumerate every DEFINED subject in the schedule-definitions
and/or spec-section layers, anti-join against what the canonical scope list actually references in
its text, and report the residue -- SS6's "unaccounted-defined-things list". This is a deterministic
read, re-runnable any time as a coverage check; it never proposes, deposits, or paraphrases -- it is
a mechanical scan over already-deposited claim rows, same discipline as compile_context_packet.py.

The decided rule (PLU-351, gated to the orchestrator and settled -- implemented exactly, not
re-litigated here): a defined code is **accounted for** when it appears as a word-boundary token in
a canonical scope item's `name`, `description`, `notesInternal`, or `notesExternal` claim VALUES.
Evidence snippets are excluded -- they are noisy page OCR and inflate false positives; only the
curated scope-item text counts.

Reused from compile_context_packet.py (PLU-351's sibling compiler, same directory) rather than
reimplemented: `parse_claims_file` / `merge_claim_files` (claims-dump loading, JSONL or raw MCP
`search`-response shape), `index_by_subject` / `first_value` / `all_values` (claim-lookup
primitives), and `classify_definition_subjects` (the definitions-layer subject classification --
schedule kinds are excluded when INSTANCE-tagged via `ambiguityClass:"instance"`;
specSection subjects are always definitions). This script adds only the scope-item text corpus, the
word-boundary token matcher, and the accounted/unaccounted/ambiguous partition.

Named limitations the report states honestly rather than hides (per the PLU-351 brief):
  - Kind-agnostic matching: the code STRING is what's searched, not the kind. `doorType:A-1` and
    `plumbingFixtureType:A-1` both match the token "A-1" -- a code string that collides across kinds
    cannot be cleanly attributed to one kind by token match alone, so both land in the
    ambiguous-token bucket, never counted cleanly accounted.
  - Short codes (<=2 characters) are collision-prone against ordinary prose and numbers -- always
    bucketed as ambiguous, regardless of whether they'd otherwise match.
  - "Accounted" means textually referenced, not priced. This report never claims scope coverage --
    only that the code's string appears in the scope text a human (or agent) would read.
  - Word-boundary rule: a code is found only where neither neighboring character (if any) is itself
    alphanumeric -- so `RF-1` is not fooled by `RF-15`, and a numeric CSI code is not fooled by a
    longer digit run it happens to prefix. Dashes and dots count as boundaries, not continuations, on
    EITHER side of the match -- this correctly finds a code immediately followed by sentence
    punctuation (the real 150 Main data has scope text like "...Key RF-1." with no space before the
    period), at the cost of not disambiguating a coarser code that is a literal, punctuation-joined
    prefix of a finer one (e.g. `A-10` inside `A-10.02`) -- no real 150 Main spec-section code has
    this shape (they are uniform 6-digit numerics), so it does not affect the real-run numbers below.
  - CSI codes: spec-section subjects carry 6-digit unspaced codes ("042000"); both that form and the
    standard spaced form ("04 20 00") are searched, since both appear in the wild (the PLU-351 brief's
    named open question) -- resolved here as "match either."
  - Matching is case-sensitive -- schedule/spec codes are conventionally presented in one fixed case,
    and case-insensitive matching risks colliding with ordinary prose.

Transport: same as compile_context_packet.py -- this script does NOT call the MOSOT MCP server. It
reads pre-fetched claim dumps (JSONL or a raw `search`-response JSON) from caller-supplied paths and
writes only to a caller-supplied `--out` path. Supersession / trust-tier resolution is out of scope
here for the same reason as the sibling compiler: this reads whatever claim rows it is given,
first-seen-value tie-break, not the projection engine's currently-governing resolution.

Confidential: reads only caller-supplied paths (kept outside the repo) and writes only to a
caller-supplied path. ASCII output. Stdlib only.
"""
from __future__ import annotations

import argparse
import re
import sys
from collections import Counter, OrderedDict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from compile_context_packet import (  # noqa: E402
    parse_claims_file,
    merge_claim_files,
    index_by_subject,
    first_value,
    all_values,
    classify_definition_subjects,
)

TEXT_PREDICATES = ("name", "description", "notesInternal", "notesExternal")
SHORT_CODE_MAX_LEN = 2


# ---------------------------------------------------------------------------
# Scope-item text corpus
# ---------------------------------------------------------------------------

def build_scope_corpus(scope_claims: list[dict]) -> "OrderedDict[str, dict]":
    """One record per scopeItem subject: {name, text}. `text` concatenates every
    value seen for TEXT_PREDICATES (claim VALUES only -- evidence snippets are
    never included, per the decided rule). Subjects not shaped "scopeItem:<id>"
    are skipped -- this corpus only ever holds canonical scope items."""
    by_subject = index_by_subject(scope_claims)
    corpus: "OrderedDict[str, dict]" = OrderedDict()
    for subject, claims in by_subject.items():
        kind, _, _code = subject.partition(":")
        if kind != "scopeItem":
            continue
        name = first_value(claims, "name")
        text_parts = []
        for predicate in TEXT_PREDICATES:
            for c in all_values(claims, predicate):
                text_parts.append(str(c["value"]))
        corpus[subject] = {"name": name, "text": "\n".join(text_parts)}
    return corpus


# ---------------------------------------------------------------------------
# Word-boundary token matching
# ---------------------------------------------------------------------------

_ALNUM = re.compile(r"[A-Za-z0-9]")


def contains_token(text: str, token: str) -> bool:
    """True if `token` appears in `text` as a word-boundary token -- neither
    neighboring character (if any) is alphanumeric. See the module docstring's
    word-boundary-rule note for the punctuation tradeoff this makes."""
    pattern = re.compile(r"(?<![A-Za-z0-9])" + re.escape(token) + r"(?![A-Za-z0-9])")
    return bool(pattern.search(text))


def csi_spaced_form(code: str) -> "str | None":
    """A 6-digit unspaced CSI code ("042000") also appears in prose in its
    standard spaced form ("04 20 00"); return that alternate, else None."""
    if re.fullmatch(r"\d{6}", code):
        return "%s %s %s" % (code[0:2], code[2:4], code[4:6])
    return None


def code_referenced_by(code: str, corpus: "OrderedDict[str, dict]") -> list[tuple[str, "str | None"]]:
    """Every scope item (subject, name) whose text contains `code` as a
    word-boundary token, in either its plain or (for 6-digit CSI codes) spaced
    form. Returns matches in corpus order."""
    spaced = csi_spaced_form(code)
    hits: list[tuple[str, "str | None"]] = []
    for subject, rec in corpus.items():
        if contains_token(rec["text"], code) or (spaced and contains_token(rec["text"], spaced)):
            hits.append((subject, rec["name"]))
    return hits


# ---------------------------------------------------------------------------
# Accounted / unaccounted / ambiguous partition
# ---------------------------------------------------------------------------

def classify_completeness(
    definitions: "OrderedDict[str, dict]",
    corpus: "OrderedDict[str, dict]",
) -> "OrderedDict[str, OrderedDict[str, dict]]":
    """Partition every defined subject into exactly one of accounted /
    unaccounted / ambiguous (mutually exclusive -- the three buckets sum to
    len(definitions)).

    A subject's code is diverted to `ambiguous` -- never counted cleanly
    accounted or residue -- when its code string collides across kinds (the
    A-1-as-doorType-and-plumbingFixtureType case) or is short (<= 2 chars,
    collision-prone against ordinary prose). Otherwise it is `accounted` when
    the code is found as a word-boundary token in the scope-item corpus, else
    `unaccounted` -- the SS6 residue.
    """
    code_kinds: dict[str, set[str]] = {}
    for rec in definitions.values():
        code_kinds.setdefault(rec["code"], set()).add(rec["kind"])

    accounted: "OrderedDict[str, dict]" = OrderedDict()
    unaccounted: "OrderedDict[str, dict]" = OrderedDict()
    ambiguous: "OrderedDict[str, dict]" = OrderedDict()

    for subject, rec in definitions.items():
        code = rec["code"]
        reasons = []
        other_kinds = code_kinds[code] - {rec["kind"]}
        if other_kinds:
            reasons.append("code %r also defined as kind(s): %s" % (code, ", ".join(sorted(other_kinds))))
        if len(code) <= SHORT_CODE_MAX_LEN:
            reasons.append("short code (<=%d chars), collision-prone" % SHORT_CODE_MAX_LEN)

        if reasons:
            ambiguous[subject] = dict(rec, reason="; ".join(reasons))
            continue

        hits = code_referenced_by(code, corpus)
        if hits:
            accounted[subject] = dict(rec, matchedBy=hits)
        else:
            unaccounted[subject] = rec

    return OrderedDict([("accounted", accounted), ("unaccounted", unaccounted), ("ambiguous", ambiguous)])


# ---------------------------------------------------------------------------
# Report rendering
# ---------------------------------------------------------------------------

def render_totals(
    definitions: "OrderedDict[str, dict]",
    buckets: "OrderedDict[str, OrderedDict[str, dict]]",
    scope_items_scanned: int,
    schedule_present: bool,
    spec_present: bool,
) -> list[str]:
    lines = ["## Totals", ""]
    kinds = Counter(rec["kind"] for rec in definitions.values())
    kind_bits = ", ".join("%s: %d" % (k, n) for k, n in sorted(kinds.items()))
    lines.append("- Defined subjects: %d total across %d kinds (%s)" % (len(definitions), len(kinds), kind_bits or "none"))
    if not schedule_present:
        lines.append("- Schedule-definition layer: not supplied for this run.")
    if not spec_present:
        lines.append("- Spec-section layer: not supplied for this run.")
    lines.append("- Scope items scanned: %d" % scope_items_scanned)
    lines.append("- Accounted (referenced by scope text): %d" % len(buckets["accounted"]))
    lines.append("- Unaccounted (the SS6 residue): %d" % len(buckets["unaccounted"]))
    lines.append("- Ambiguous-token bucket: %d" % len(buckets["ambiguous"]))
    lines.append("")
    return lines


def render_accounted(accounted: "OrderedDict[str, dict]") -> list[str]:
    lines = ["## Accounted -- referenced by scope text", ""]
    lines.append("Textually referenced, not priced -- this section is not a coverage claim.")
    lines.append("")
    if not accounted:
        lines.append("- (none accounted)")
        lines.append("")
        return lines
    lines.append("| Code | Kind | Name | Matched by |")
    lines.append("|---|---|---|---|")
    for rec in accounted.values():
        name = rec["name"] if rec["name"] else "(no description deposited)"
        matched_by = "; ".join(
            "%s (%s)" % (item_name, item_subject) if item_name else item_subject
            for item_subject, item_name in rec["matchedBy"]
        )
        lines.append("| %s | %s | %s | %s |" % (rec["code"], rec["kind"], name, matched_by))
    lines.append("")
    return lines


def render_unaccounted(unaccounted: "OrderedDict[str, dict]") -> list[str]:
    lines = ["## Unaccounted -- the SS6 residue", ""]
    if not unaccounted:
        lines.append("- (none unaccounted -- every non-ambiguous defined subject is referenced)")
        lines.append("")
        return lines
    lines.append("| Code | Kind | Name | Defined at |")
    lines.append("|---|---|---|---|")
    for rec in unaccounted.values():
        name = rec["name"] if rec["name"] else "(no description deposited)"
        lines.append("| %s | %s | %s | %s |" % (rec["code"], rec["kind"], name, rec["where"]))
    lines.append("")
    return lines


def render_ambiguous(ambiguous: "OrderedDict[str, dict]") -> list[str]:
    lines = ["## Ambiguous-token bucket", ""]
    lines.append("Collision-prone codes -- reported, never counted cleanly accounted or as residue.")
    lines.append("")
    if not ambiguous:
        lines.append("- (none ambiguous)")
        lines.append("")
        return lines
    lines.append("| Code | Kind | Name | Reason |")
    lines.append("|---|---|---|---|")
    for rec in ambiguous.values():
        name = rec["name"] if rec["name"] else "(no description deposited)"
        lines.append("| %s | %s | %s | %s |" % (rec["code"], rec["kind"], name, rec["reason"]))
    lines.append("")
    return lines


def compile_report(
    schedule_claims: list[dict],
    spec_claims: list[dict],
    scope_claims: list[dict],
    project_name: str,
    project_id: str,
    compiled_date: str,
) -> str:
    definitions = classify_definition_subjects(list(schedule_claims) + list(spec_claims))
    corpus = build_scope_corpus(scope_claims)
    buckets = classify_completeness(definitions, corpus)

    header = [
        "# %s -- Completeness Oracle Report" % project_name,
        "",
        "Compiled by completeness_oracle.py on %s from proposed, cited claims in `%s`."
        % (compiled_date, project_id),
        "This report is a projection -- regenerate it from the claims; never edit it in place.",
        "Doctrine: scope-package-architecture.md SS4.4 (a query pattern over the definitions layer, "
        "not the packet) and SS6 (the unaccounted-defined-things residue).",
        "",
        "## Rule",
        "",
        "A defined code is accounted for when it appears as a word-boundary token in a canonical "
        "scope item's `name`, `description`, `notesInternal`, or `notesExternal` claim values. "
        "Evidence snippets are excluded (noisy page OCR, inflates false positives).",
        "",
        "Caveats: kind-agnostic matching (a code string shared across kinds cannot be cleanly "
        "attributed by token match alone) and short codes (<=%d chars, collision-prone) both divert "
        "to the ambiguous-token bucket below rather than counting cleanly accounted. \"Accounted\" "
        "means textually referenced, not priced. CSI 6-digit codes are matched in both the unspaced "
        "and standard spaced (\"04 20 00\") forms. Matching is case-sensitive." % SHORT_CODE_MAX_LEN,
        "",
    ]

    parts: list[str] = []
    parts.extend(header)
    parts.extend(render_totals(definitions, buckets, len(corpus), bool(schedule_claims), bool(spec_claims)))
    parts.extend(render_accounted(buckets["accounted"]))
    parts.extend(render_unaccounted(buckets["unaccounted"]))
    parts.extend(render_ambiguous(buckets["ambiguous"]))

    return "\n".join(parts).rstrip() + "\n"


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--project-id", required=True)
    ap.add_argument("--project-name", required=True)
    ap.add_argument("--schedule-claims", action="append", default=[],
                     help="schedule-layer definition claims dump(s) (repeatable)")
    ap.add_argument("--spec-claims", action="append", default=[],
                     help="specSection-layer claims dump(s) (repeatable)")
    ap.add_argument("--scope-claims", action="append", default=[],
                     help="canonical scope-item claims dump(s) (repeatable)")
    ap.add_argument("--compiled-date", default=None, help="override for tests; defaults to today (UTC)")
    ap.add_argument("--out", required=True, help="output markdown path")
    args = ap.parse_args()

    schedule_claims = merge_claim_files([Path(p) for p in args.schedule_claims])
    spec_claims = merge_claim_files([Path(p) for p in args.spec_claims])
    scope_claims = merge_claim_files([Path(p) for p in args.scope_claims])

    if args.compiled_date:
        compiled_date = args.compiled_date
    else:
        import datetime
        compiled_date = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d")

    report = compile_report(
        schedule_claims, spec_claims, scope_claims,
        args.project_name, args.project_id, compiled_date,
    )

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(report, encoding="utf-8")

    definitions = classify_definition_subjects(list(schedule_claims) + list(spec_claims))
    corpus = build_scope_corpus(scope_claims)
    buckets = classify_completeness(definitions, corpus)

    print("[ok] %d defined subjects (%d schedule claims, %d spec claims), %d scope items -> %s"
          % (len(definitions), len(schedule_claims), len(spec_claims), len(corpus), args.out))
    print("[ok] accounted=%d unaccounted=%d ambiguous=%d"
          % (len(buckets["accounted"]), len(buckets["unaccounted"]), len(buckets["ambiguous"])),
          file=sys.stderr)
    if not schedule_claims:
        print("[warn] no --schedule-claims supplied -- report treats the layer as not present", file=sys.stderr)
    if not spec_claims:
        print("[warn] no --spec-claims supplied -- report treats the layer as not present", file=sys.stderr)
    if not scope_claims:
        print("[warn] no --scope-claims supplied -- every defined subject reports unaccounted", file=sys.stderr)


if __name__ == "__main__":
    main()
