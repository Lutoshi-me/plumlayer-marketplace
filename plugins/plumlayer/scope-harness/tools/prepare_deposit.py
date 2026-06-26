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
  * A row that already carries its OWN ambiguityClass (e.g. a "discipline-uncertain"
    discipline claim from derive_set_claims.py) keeps it — the marker is passed through to
    the propose arg so it counts toward openAmbiguities. The tradeContest-derived class
    takes precedence when a row somehow has both (they do not collide in practice: scope
    rows have no row-level class, ingestion rows have no tradeContest).

Batch output (--batch-dir / --batch-size):
  * Writes the deposit list split into pretty-printed JSON array files of <=batch_size
    entries, zero-padded 3 digits: deposit_batch_000.json, deposit_batch_001.json, …
  * Writes deposit_manifest.json with exact per-batch counts, so the deposit agent can
    verify the inserted count against the manifest and stop instead of inventing.
  * Stale batches from a prior, larger run are cleared before writing.

Importable + CLI. Stdlib only.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any


# ---------------------------------------------------------------------------
# Batch types
# ---------------------------------------------------------------------------

class BatchEntry:
    """One entry in the manifest's batches list."""
    def __init__(self, file: str, count: int) -> None:
        self.file = file
        self.count = count

    def to_dict(self) -> dict:
        return {"file": self.file, "count": self.count}


class BatchManifest:
    """Typed wrapper around the manifest written to deposit_manifest.json."""
    def __init__(
        self,
        total_claims: int,
        batch_size: int,
        batch_count: int,
        batches: list[BatchEntry],
    ) -> None:
        self.total_claims = total_claims
        self.batch_size = batch_size
        self.batch_count = batch_count
        self.batches = batches

    def to_dict(self) -> dict:
        return {
            "totalClaims": self.total_claims,
            "batchSize": self.batch_size,
            "batchCount": self.batch_count,
            "batches": [b.to_dict() for b in self.batches],
        }


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

        # Pass through a row's own ambiguityClass (e.g. "discipline-uncertain" from
        # derive_set_claims.py) so the marker reaches the MOSOT and counts toward
        # openAmbiguities. Without this it would be silently dropped here.
        row_amb = r.get("ambiguityClass")
        if isinstance(row_amb, str) and row_amb:
            arg["ambiguityClass"] = row_amb

        # tradeContest-derived ambiguity (scope harness): contested/unowned items surface
        # in the ambiguities ledger. Takes precedence when both are present.
        c = contest.get(r["subject"])
        if c in ("contested", "unowned"):
            arg["ambiguityClass"] = c

        if version_scope:
            arg["versionScope"] = version_scope

        deposit.append(arg)

    return deposit, dropped_null


def write_batches(
    deposit: list[dict],
    batch_dir: Path,
    batch_size: int = 50,
) -> BatchManifest:
    """Write deposit list as numbered batch files + a manifest into batch_dir.

    Contract:
      - Clears any existing deposit_batch_*.json and deposit_manifest.json in batch_dir
        before writing (prevents stale batches from a prior, larger run lingering).
      - Creates batch_dir if it does not exist.
      - Writes deposit_batch_NNN.json files (zero-padded 3 digits), each a JSON array
        of <=batch_size entries, indent=2 (pretty-printed — single-line is what truncates
        in agent reads and causes fabrication of the missing tail).
      - Writes deposit_manifest.json with exact per-batch counts.
      - Returns a BatchManifest whose invariants hold:
          sum(b.count for b in manifest.batches) == manifest.total_claims == len(deposit)
          each batch count <= batch_size
          manifest.batch_count == len(manifest.batches) == number of files written
    """
    batch_dir.mkdir(parents=True, exist_ok=True)

    # Clear stale batches from any prior run.
    for stale in batch_dir.glob("deposit_batch_*.json"):
        stale.unlink()
    stale_manifest = batch_dir / "deposit_manifest.json"
    if stale_manifest.exists():
        stale_manifest.unlink()

    entries: list[BatchEntry] = []
    idx = 0
    written = 0

    while written < len(deposit) or (written == 0 and len(deposit) == 0):
        chunk = deposit[written: written + batch_size]
        fname = f"deposit_batch_{idx:03d}.json"
        fpath = batch_dir / fname
        with fpath.open("w", encoding="utf-8") as fh:
            json.dump(chunk, fh, indent=2)
        entries.append(BatchEntry(file=fname, count=len(chunk)))
        written += len(chunk)
        idx += 1
        if written >= len(deposit):
            break

    manifest = BatchManifest(
        total_claims=len(deposit),
        batch_size=batch_size,
        batch_count=len(entries),
        batches=entries,
    )
    manifest_path = batch_dir / "deposit_manifest.json"
    with manifest_path.open("w", encoding="utf-8") as fh:
        json.dump(manifest.to_dict(), fh, indent=2)

    return manifest


def main() -> None:
    ap = argparse.ArgumentParser(description="Map scope_claims.jsonl → propose-ready args.")
    ap.add_argument("--claims", required=True, help="scope_claims.jsonl from reconcile_overlap")
    ap.add_argument("--out", required=True, help="deposit.json (array of propose args)")
    ap.add_argument("--source", default="scope-harness",
                    help="fallback sourceInstrument when a claim has no evidence source")
    ap.add_argument("--version-scope", default=None,
                    help="optional versionScope tag (the document issue these claims apply to)")
    ap.add_argument("--batch-dir", default=None,
                    help="directory for batch files + manifest (default: deposit_batches/ "
                         "alongside --out)")
    ap.add_argument("--batch-size", type=int, default=50,
                    help="max claims per batch file (default: 50)")
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
    print(f"[ok] {len(flagged)} items flagged ambiguous (ambiguityClass set: "
          f"contested/unowned or discipline-uncertain)", file=sys.stderr)
    print(f"[info] predicate counts: {dict(preds)}", file=sys.stderr)

    batch_dir = Path(args.batch_dir) if args.batch_dir else out_path.parent / "deposit_batches"
    manifest = write_batches(deposit, batch_dir, args.batch_size)
    print(
        f"[ok] wrote {manifest.batch_count} batch files (<={args.batch_size} claims each)"
        f" + deposit_manifest.json -> {batch_dir}"
    )


if __name__ == "__main__":
    main()
