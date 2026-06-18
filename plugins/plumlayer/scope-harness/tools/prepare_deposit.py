"""
prepare_deposit.py — map scope_claims.jsonl → MOSOT `propose`-ready argument objects.

The scope harness already emits claims in the MOSOT Claim shape (subject — predicate —
value + evidence, trustClass "proposed"). This tool flattens that JSONL into a list of
argument objects ready to hand to the `propose` MCP verb, ONE object per `propose` call:

    { "subject", "predicate", "value", "sourceInstrument", "evidence"?, "ambiguityClass"? }

It does NOT call the MCP itself (a local script has no auth token). The orchestrating
agent — which holds the authenticated Plumlayer MCP connection — reads this file and
issues one `propose(projectId=…, **arg)` call per entry. This tool is the deterministic
transform; the deposit itself is the agent's job (see the scope-run skill, stage 7).

Rules (grounded in the `propose` contract: projectId/subject/predicate/sourceInstrument
required, value required non-null, evidence/ambiguityClass optional):
  * Drop rows whose value is null — `propose` requires a non-null value, and a null
    (e.g. `belongsToTrade` on an unowned/contested item) carries meaning by its absence.
  * sourceInstrument comes from the claim's first evidence source (the sheetId, which
    encodes the set + page, e.g. "<SET>-p006"); falls back to --source.
  * A scope item whose tradeContest is "contested" or "unowned" is flagged with
    ambiguityClass on every one of its rows, so it surfaces in the `ambiguities` review
    ledger — these are the RFI pile, the highest-value human-review surface.

Importable + CLI. Stdlib only.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any


def _contest_by_subject(rows: list[dict]) -> dict[str, str]:
    """Map each scope item's subject → its tradeContest value (clear/contested/unowned)."""
    out: dict[str, str] = {}
    for r in rows:
        if r.get("predicate") == "tradeContest" and isinstance(r.get("value"), str):
            out[r["subject"]] = r["value"]
    return out


def prepare(
    rows: list[dict],
    default_source: str = "scope-harness",
    version_scope: str | None = None,
) -> tuple[list[dict], int]:
    """Transform claim rows → propose-ready args. Returns (deposit, dropped_null_count)."""
    contest = _contest_by_subject(rows)
    deposit: list[dict] = []
    dropped_null = 0

    for r in rows:
        value = r.get("value")
        if value is None:
            dropped_null += 1
            continue

        evidence = r.get("evidence") or []
        source = default_source
        if isinstance(evidence, list) and evidence and evidence[0].get("source"):
            source = evidence[0]["source"]

        arg: dict[str, Any] = {
            "subject": r["subject"],
            "predicate": r["predicate"],
            "value": value,
            "sourceInstrument": source,
        }
        if evidence:
            arg["evidence"] = evidence

        c = contest.get(r["subject"])
        if c in ("contested", "unowned"):
            arg["ambiguityClass"] = c

        if version_scope:
            arg["versionScope"] = version_scope

        deposit.append(arg)

    return deposit, dropped_null


def main() -> None:
    ap = argparse.ArgumentParser(description="Map scope_claims.jsonl → propose-ready args.")
    ap.add_argument("--claims", required=True, help="scope_claims.jsonl from reconcile_overlap")
    ap.add_argument("--out", required=True, help="deposit.json (array of propose args)")
    ap.add_argument("--source", default="scope-harness",
                    help="fallback sourceInstrument when a claim has no evidence source")
    ap.add_argument("--version-scope", default=None,
                    help="optional versionScope tag (the document issue these claims apply to)")
    args = ap.parse_args()

    rows: list[dict] = []
    with open(args.claims, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line:
                rows.append(json.loads(line))

    deposit, dropped = prepare(rows, args.source, args.version_scope)

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8") as fh:
        json.dump(deposit, fh, indent=2)

    subjects = {d["subject"] for d in deposit}
    flagged = {d["subject"] for d in deposit if d.get("ambiguityClass")}
    preds = Counter(d["predicate"] for d in deposit)
    print(f"[ok] {len(deposit)} claims across {len(subjects)} scope items -> {args.out}")
    print(f"[ok] dropped {dropped} null-value rows (not depositable)", file=sys.stderr)
    print(f"[ok] {len(flagged)} items flagged ambiguous (contested/unowned)", file=sys.stderr)
    print(f"[info] predicate counts: {dict(preds)}", file=sys.stderr)


if __name__ == "__main__":
    main()
