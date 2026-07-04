"""
compile_context_packet.py -- the stage-1/stage-2 context packet compiler (PLU-351).

Doctrine role (scope-package-architecture.md SS4.3 + SS4.4): a stage-3 reader's context packet has
two sections -- the orientation projection (SS4.3: identity / systems / scope areas / set shape /
hazards, compiled from the project-level claims `learn-project` deposits) and the definitions
index (SS4.4: one line per defined subject -- code -> kind -> name -> where-defined -- covering the
schedule-definitions layer and the specSection skeleton). Both are PROJECTIONS: regenerated in full
from already-deposited claims, never themselves proposed, never stored as truth, never written to
the repo or the MOSOT. This script is the deterministic tooling that performs that projection --
compiling is a mechanical scan over claim rows, not agent judgment, so no paraphrase happens here.

Transport (reused from fetch_schedule_roster.py's lineage, per the PLU-351 dispatch): this script
does NOT call the MOSOT MCP server itself. The agent fetches claims with the `search` verb
(paginating as needed -- the schedule-definitions layer alone can run ~10 pages at the 500-row
max) and writes each page's `claims` rows to a JSONL file (one claim object per line, the same flat
shape every other script in this directory reads/writes). This script only reads those files and
projects them into markdown; "the agent merely triggers it" (SS4.4).

Inputs (any subset may be absent -- an absent layer is reported honestly, never silently skipped):
  --project-claims  claims where subject == "project" (SS4.3's predicate vocabulary: projectType,
                     deliveryMethod, location, grossArea, floorCount, bidDueDate, tradeInScope,
                     knownExclusion, structuralSystem, envelopeSystem, mepDeliveryShape, scopeArea,
                     phasingNote, setShapeObservation, missingScopeFamily, hazardFlag) plus
                     `party:<slug>` subjects (hasRole / name) -- both from project-create's seed
                     table and learn-project's SS4 emit table.
  --schedule-claims schedule-layer claims (subject "<kind>:<code>"), predicates including
                     description, definedOnSheet, locatedAt, and the tableType-derived
                     ambiguityClass:"instance" tag schedule_ground.py stamps on every claim of an
                     INSTANCE-table subject (a physical door/opening/circuit), never a definition.
                     The mechanical split this script uses: a subject is a *defined* thing iff none
                     of its claims carry ambiguityClass=="instance" -- that flag is schedule_ground.py's
                     own tableType:"instance" marker (see its module docstring, "Instance tables"),
                     not a judgment invented here.
  --spec-claims     specSection-layer claims (subject "specSection:<csi>"), predicates hasTitle,
                     locatedAt, inDivision, partOfIssue (spec_inventory.py's shape).

Each --claims-family flag is repeatable (paginated fetches land in more than one file) and accepts
either a JSONL file (one claim dict per line) or a single JSON file shaped like a raw MCP `search`
response (`{"claims": [...], ...}`) -- fetch_schedule_roster.py's own input shape -- so a single-page
dump can be handed over unmodified.

Supersession / trust-tier resolution is explicitly OUT of scope here: this script projects whatever
claim rows it is given, taking the first-seen value per (subject, predicate) as a stable, named
tie-break -- resolving competing claims to the actually-governing one is the projection engine's job
(mosot-projection-logic.md), not this packet compiler's. Callers who want only currently-governing
values should filter at fetch time (e.g. `search(..., trustClass: "approved")`).

Confidential: reads only caller-supplied paths (kept outside the repo) and writes only to a
caller-supplied path. ASCII output. Stdlib only.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter, OrderedDict
from pathlib import Path
from typing import Any

INSTANCE_AMBIGUITY = "instance"


# ---------------------------------------------------------------------------
# Loading
# ---------------------------------------------------------------------------

def parse_claims_file(path: Path) -> list[dict]:
    """Read one claims dump. Accepts a JSONL file (one claim per line) or a
    single JSON object shaped like a raw MCP `search` response
    (`{"claims": [...]}`, fetch_schedule_roster.py's input shape)."""
    text = path.read_text(encoding="utf-8").strip()
    if not text:
        return []
    try:
        obj = json.loads(text)
    except json.JSONDecodeError:
        obj = None  # not a single JSON document -- fall through to JSONL
    if isinstance(obj, dict) and "claims" in obj:
        return list(obj["claims"])  # the raw MCP search-response envelope
    if isinstance(obj, dict):
        return [obj]  # a JSONL file that happens to hold exactly one claim
    claims: list[dict] = []
    for line in text.splitlines():
        line = line.strip()
        if line:
            claims.append(json.loads(line))
    return claims


def merge_claim_files(paths: list[Path]) -> list[dict]:
    """Concatenate claims across however many paginated dump files were handed over."""
    merged: list[dict] = []
    for p in paths:
        merged.extend(parse_claims_file(p))
    return merged


def index_by_subject(claims: list[dict]) -> "OrderedDict[str, list[dict]]":
    by_subject: "OrderedDict[str, list[dict]]" = OrderedDict()
    for c in claims:
        by_subject.setdefault(c["subject"], []).append(c)
    return by_subject


def first_value(claims: list[dict], predicate: str) -> Any:
    """First-seen value for a predicate on one subject's claim list (see the
    module docstring's supersession note -- this is a stable tie-break, not
    trust-tier resolution)."""
    for c in claims:
        if c.get("predicate") == predicate:
            return c.get("value")
    return None


def all_values(claims: list[dict], predicate: str) -> list[dict]:
    """Every claim for a predicate on one subject's claim list, in first-seen order."""
    return [c for c in claims if c.get("predicate") == predicate]


def flag(claim: dict) -> str:
    """The '(!)' ambiguity marker used throughout the packet (SS4.3's convention)."""
    return " (!)" if claim.get("ambiguityClass") else ""


# ---------------------------------------------------------------------------
# Orientation section (SS4.3)
# ---------------------------------------------------------------------------

PARTY_ROLE_LABELS = {
    "owner": "Owner",
    "architect-of-record": "Architect",
    "structural-engineer": "Structural",
    "mep-engineer": "MEP",
    "civil-engineer": "Civil",
    "landscape-architect": "Landscape",
    "code-consultant": "Code",
    "gc": "GC",
    "cm": "CM",
}


def compile_identity(by_subject: "OrderedDict[str, list[dict]]", project_name: str, project_id: str) -> list[str]:
    project_claims = by_subject.get("project", [])
    lines = ["## Identity", ""]
    lines.append("- **Project:** %s (`%s`)" % (project_name, project_id))

    loc = first_value(project_claims, "location")
    ptype = first_value(project_claims, "projectType")
    delivery = first_value(project_claims, "deliveryMethod")
    area = first_value(project_claims, "grossArea")
    floors = first_value(project_claims, "floorCount")
    due = first_value(project_claims, "bidDueDate")

    if ptype or loc:
        bit = "- **Type:** %s" % (ptype or "(not deposited)")
        if loc:
            bit += " -- %s" % loc
        lines.append(bit)
    if delivery:
        lines.append("- **Delivery method:** %s" % delivery)
    if area or floors:
        size_bits = [x for x in (area, ("%s floors" % floors if floors else None)) if x]
        lines.append("- **Size:** %s" % ", ".join(size_bits))
    if due:
        lines.append("- **Bid due:** %s" % due)

    # Parties: subject "party:<slug>", predicates hasRole / name.
    party_lines = []
    for subj, claims in by_subject.items():
        if not subj.startswith("party:"):
            continue
        role = first_value(claims, "hasRole")
        name = first_value(claims, "name")
        if role:
            label = PARTY_ROLE_LABELS.get(role, role)
            party_lines.append("**%s:** %s" % (label, name or "(name not deposited)"))
    if party_lines:
        lines.append("- " + ". ".join(party_lines) + ".")

    trades = all_values(project_claims, "tradeInScope")
    if trades:
        lines.append("- **Trades in scope:** " + ", ".join(str(c["value"]) + flag(c) for c in trades))

    exclusions = all_values(project_claims, "knownExclusion")
    if exclusions:
        lines.append("- **Known exclusions:** " + "; ".join(str(c["value"]) + flag(c) for c in exclusions))

    if len(lines) == 3:  # header (2 lines) + the always-present Project line only
        lines.append("- (no project-level identity claims deposited)")
    lines.append("")
    return lines


def compile_systems(by_subject: "OrderedDict[str, list[dict]]") -> list[str]:
    project_claims = by_subject.get("project", [])
    lines = ["## Systems", ""]
    structural = all_values(project_claims, "structuralSystem")
    envelope = all_values(project_claims, "envelopeSystem")
    mep = all_values(project_claims, "mepDeliveryShape")

    if structural:
        lines.append("- **Structural:** " + "; ".join(str(c["value"]) + flag(c) for c in structural))
    if envelope:
        lines.append("- **Envelope:** " + "; ".join(str(c["value"]) + flag(c) for c in envelope))
    if mep:
        bits = []
        for c in mep:
            v = c["value"] or {}
            division = v.get("division", "?") if isinstance(v, dict) else v
            shape = v.get("shape", "?") if isinstance(v, dict) else "?"
            bits.append("%s: %s%s" % (division, shape, flag(c)))
        lines.append("- **MEP delivery shape:** " + "; ".join(bits))

    if not (structural or envelope or mep):
        lines.append("- (no systems claims deposited)")
    lines.append("")
    return lines


def compile_scope_areas(by_subject: "OrderedDict[str, list[dict]]") -> list[str]:
    project_claims = by_subject.get("project", [])
    lines = ["## Scope areas", ""]
    areas = all_values(project_claims, "scopeArea")
    phasing = all_values(project_claims, "phasingNote")
    for c in areas:
        lines.append("- %s%s" % (c["value"], flag(c)))
    for c in phasing:
        lines.append("- %s%s" % (c["value"], flag(c)))
    if not (areas or phasing):
        lines.append("- (no scope-area claims deposited)")
    lines.append("")
    return lines


def compile_set_shape(by_subject: "OrderedDict[str, list[dict]]") -> list[str]:
    project_claims = by_subject.get("project", [])
    lines = ["## Set shape", ""]
    observations = all_values(project_claims, "setShapeObservation")
    missing = all_values(project_claims, "missingScopeFamily")
    for c in observations:
        lines.append("- %s%s" % (c["value"], flag(c)))
    if missing:
        lines.append("- **Missing families:** " + "; ".join(str(c["value"]) + flag(c) for c in missing))
    if not (observations or missing):
        lines.append("- (no set-shape observations deposited)")
    lines.append("")
    return lines


def compile_hazards(by_subject: "OrderedDict[str, list[dict]]") -> list[str]:
    project_claims = by_subject.get("project", [])
    lines = ["## Hazards / anomalies", ""]
    hazards = all_values(project_claims, "hazardFlag")
    for c in hazards:
        lines.append("- %s%s" % (c["value"], flag(c)))
    if not hazards:
        lines.append("- (no hazard claims deposited)")
    lines.append("")
    return lines


# ---------------------------------------------------------------------------
# Definitions index (SS4.4)
# ---------------------------------------------------------------------------

def _format_where_defined(claims: list[dict]) -> str:
    """definedOnSheet (a clean subject-reference string) wins; else locatedAt's
    sheetId; else locatedAt's page range (the spec-section shape); else absent."""
    sheet = first_value(claims, "definedOnSheet")
    if sheet:
        return str(sheet)
    located = first_value(claims, "locatedAt")
    if isinstance(located, dict):
        if located.get("sheetId"):
            return str(located["sheetId"])
        if located.get("pageStart") is not None:
            start, end = located.get("pageStart"), located.get("pageEnd")
            page_bit = "p.%s" % start if start == end or end is None else "p.%s-%s" % (start, end)
            instrument = located.get("instrument")
            return "%s %s" % (instrument, page_bit) if instrument else page_bit
    return "(not grounded)"


def classify_definition_subjects(claims: list[dict]) -> "OrderedDict[str, dict]":
    """Return one record per DEFINED subject: {code, kind, name, where, flagged}.

    A schedule subject is excluded (it is an INSTANCE, not a definition) when any
    of its claims carries ambiguityClass:"instance" -- schedule_ground.py's own
    tableType:"instance" marker (its module docstring: "Instance tables ... all
    claims carry ambiguityClass:'instance' so reviewers know these are
    opening/room instances"). specSection subjects are never instance-tagged and
    always included.
    """
    by_subject = index_by_subject(claims)
    records: "OrderedDict[str, dict]" = OrderedDict()
    for subject, subj_claims in by_subject.items():
        kind, _, code = subject.partition(":")
        if not code:
            continue  # not a "<kind>:<code>" subject -- not part of this layer
        if kind != "specSection" and any(c.get("ambiguityClass") == INSTANCE_AMBIGUITY for c in subj_claims):
            continue  # instance table, not a definition

        if kind == "specSection":
            name = first_value(subj_claims, "hasTitle")
            division = first_value(subj_claims, "inDivision")
        else:
            name = first_value(subj_claims, "description")
            division = None

        flagged = any(
            c.get("ambiguityClass") and c.get("ambiguityClass") != INSTANCE_AMBIGUITY
            for c in subj_claims
        )
        records[subject] = {
            "code": code,
            "kind": kind,
            "name": name,
            "where": _format_where_defined(subj_claims),
            "flagged": flagged,
            "division": division,
        }
    return records


def render_definitions_index(records: "OrderedDict[str, dict]", spec_present: bool, schedule_present: bool) -> list[str]:
    lines = ["## Definitions index", ""]

    schedule_records = {k: v for k, v in records.items() if v["kind"] != "specSection"}
    spec_records = {k: v for k, v in records.items() if v["kind"] == "specSection"}

    if schedule_present:
        kinds = Counter(v["kind"] for v in schedule_records.values())
        lines.append(
            "Schedule-definition layer: %d defined subjects across %d kinds."
            % (len(schedule_records), len(kinds))
        )
    else:
        lines.append("Schedule-definition layer: no schedule definitions deposited for this project.")

    if spec_present:
        divisions = sorted({r["division"] for r in spec_records.values() if r["division"]})
        div_bit = " across divisions %s" % ", ".join(divisions) if divisions else ""
        lines.append("Spec-section layer: %d sections%s." % (len(spec_records), div_bit))
    else:
        lines.append("Spec-section layer: spec ingestion hasn't run for this project.")
    lines.append("")

    if records:
        lines.append("| Code | Kind | Name | Defined at |")
        lines.append("|---|---|---|---|")
        for subj, rec in records.items():
            name = rec["name"] if rec["name"] else "(no description deposited)"
            marker = " (!)" if rec["flagged"] else ""
            lines.append(
                "| %s | %s | %s%s | %s |"
                % (rec["code"], rec["kind"], name, marker, rec["where"])
            )
        lines.append("")
    return lines


# ---------------------------------------------------------------------------
# Full packet
# ---------------------------------------------------------------------------

def compile_packet(
    project_claims: list[dict],
    schedule_claims: list[dict],
    spec_claims: list[dict],
    project_name: str,
    project_id: str,
    compiled_date: str,
) -> str:
    by_subject = index_by_subject(project_claims)

    definitions = classify_definition_subjects(list(schedule_claims) + list(spec_claims))

    header = [
        "# %s -- Orientation Packet" % project_name,
        "",
        "Compiled by compile_context_packet.py on %s from proposed, cited claims in `%s`."
        % (compiled_date, project_id),
        "This packet is a projection -- regenerate it from the claims; never edit it in place.",
        "Flags: (!) = ambiguity-flagged claim, review pending.",
        "",
    ]

    parts: list[str] = []
    parts.extend(header)
    parts.extend(compile_identity(by_subject, project_name, project_id))
    parts.extend(compile_systems(by_subject))
    parts.extend(compile_scope_areas(by_subject))
    parts.extend(compile_set_shape(by_subject))
    parts.extend(compile_hazards(by_subject))
    parts.extend(render_definitions_index(definitions, spec_present=bool(spec_claims), schedule_present=bool(schedule_claims)))

    return "\n".join(parts).rstrip() + "\n"


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def slugify(name: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")
    return slug or "project"


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--project-id", required=True)
    ap.add_argument("--project-name", required=True)
    ap.add_argument("--project-claims", action="append", default=[],
                     help="claims dump(s) for subject=='project' + 'party:<slug>' (repeatable)")
    ap.add_argument("--schedule-claims", action="append", default=[],
                     help="schedule-layer claims dump(s) (repeatable)")
    ap.add_argument("--spec-claims", action="append", default=[],
                     help="specSection-layer claims dump(s) (repeatable)")
    ap.add_argument("--compiled-date", default=None, help="override for tests; defaults to today (UTC)")
    ap.add_argument("--out", required=True, help="output markdown path")
    args = ap.parse_args()

    project_claims = merge_claim_files([Path(p) for p in args.project_claims])
    schedule_claims = merge_claim_files([Path(p) for p in args.schedule_claims])
    spec_claims = merge_claim_files([Path(p) for p in args.spec_claims])

    if args.compiled_date:
        compiled_date = args.compiled_date
    else:
        import datetime
        compiled_date = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d")

    packet = compile_packet(
        project_claims, schedule_claims, spec_claims,
        args.project_name, args.project_id, compiled_date,
    )

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(packet, encoding="utf-8")

    definitions = classify_definition_subjects(list(schedule_claims) + list(spec_claims))
    schedule_defs = [k for k, v in definitions.items() if v["kind"] != "specSection"]
    spec_defs = [k for k, v in definitions.items() if v["kind"] == "specSection"]
    schedule_subjects_seen = {c["subject"] for c in schedule_claims}
    instance_excluded = len(schedule_subjects_seen) - len(schedule_defs)

    print("[ok] %d project claims, %d schedule claims, %d spec claims -> %s"
          % (len(project_claims), len(schedule_claims), len(spec_claims), args.out))
    print("[ok] definitions index: %d schedule-definition subjects (%d instance subjects excluded) "
          "+ %d spec sections = %d rows"
          % (len(schedule_defs), instance_excluded, len(spec_defs), len(definitions)), file=sys.stderr)
    if not schedule_claims:
        print("[warn] no --schedule-claims supplied -- packet reports the layer absent", file=sys.stderr)
    if not spec_claims:
        print("[warn] no --spec-claims supplied -- packet reports spec ingestion hasn't run", file=sys.stderr)


if __name__ == "__main__":
    main()
