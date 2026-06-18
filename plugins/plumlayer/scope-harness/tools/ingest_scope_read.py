"""
ingest_scope_read.py — validate and ingest an agent-read JSON into scope-item claims.

Doctrine role (agents read and judge; deterministic tooling grounds; nothing governs unverified):
  * Deterministic GROUNDING tool — validates the agent-read contract, mints
    subject URIs, and emits claim rows. It does NOT interpret scope meaning.
  * Rejection rules (item-level, not file-level):
      - empty citations → reject item, print, continue
      - cited pageNum absent from the packet manifest → reject item, print, continue
  * Every emitted claim is trustClass="proposed". Nothing governs unverified.
  * Honest counts: prints "N items written, M rejected" — never silent truncation.

Usage:
  python ingest_scope_read.py \\
    --agent-read agent_read.json \\
    --packet-manifest output/scope/packet/packet_manifest.json \\
    --out output/scope/scope_claims.jsonl
"""

import argparse
import json
import sys
from pathlib import Path

# Sibling import — tools/ is the package root; use direct import
sys.path.insert(0, str(Path(__file__).parent))
from scope_claim_schema import (
    mint_subject,
    validate_agent_read,
    write_scope_claims,
)


# ---------------------------------------------------------------------------
# Packet manifest helpers
# ---------------------------------------------------------------------------

def _load_manifest_page_nums(manifest_path: Path) -> set[int]:
    """Return the set of pageNums present in the packet manifest."""
    with manifest_path.open("r", encoding="utf-8") as fh:
        manifest = json.load(fh)
    return {s["pageNum"] for s in manifest.get("sheets", [])}


def _load_manifest_page_to_sheet_no(manifest_path: Path) -> dict[int, str]:
    """Return mapping pageNum -> human sheet number (e.g. 76 -> 'A-400')."""
    with manifest_path.open("r", encoding="utf-8") as fh:
        manifest = json.load(fh)
    return {s["pageNum"]: s["sheetNo"] for s in manifest.get("sheets", [])}


# ---------------------------------------------------------------------------
# Per-item processing
# ---------------------------------------------------------------------------

def _shown_on_sheet_nos(citations: list[dict], page_to_sheet_no: dict[int, str]) -> list[str]:
    """
    Build the isShownOn list as human sheet numbers (e.g. "A-400"), mapped from
    each citation's pageNum via the packet manifest.  Falls back to the raw sheetId
    only if a page is somehow absent from the manifest (shouldn't happen — cited
    pages are manifest-validated upstream).  Order-preserving, de-duplicated.
    """
    seen: list[str] = []
    for c in citations:
        sheet_no = page_to_sheet_no.get(c.get("pageNum"), c.get("sheetId", ""))
        if sheet_no and sheet_no not in seen:
            seen.append(sheet_no)
    return seen


def _process_items(
    scope_items: list[dict],
    manifest_pages: set[int],
    page_to_sheet_no: dict[int, str],
    cluster_name: str,
) -> tuple[list[dict], int]:
    """
    Validate each item and return (ready_items, rejected_count).
    ready_items are dicts ready for write_scope_claims.
    """
    ready: list[dict] = []
    rejected = 0

    for idx, item in enumerate(scope_items):
        loc = f"scopeItems[{idx}]"
        citations = item.get("citations", [])

        # Rule 1: citations non-empty (schema validator already checks, but belt-and-suspenders)
        if not citations:
            print(
                f"[reject] {loc}: empty citations — item dropped: {item.get('scopeText', '')[:80]!r}",
                file=sys.stderr,
            )
            rejected += 1
            continue

        # Rule 2: every cited pageNum must be present in the manifest
        bad_pages = [
            c["pageNum"]
            for c in citations
            if c.get("pageNum") not in manifest_pages
        ]
        if bad_pages:
            print(
                f"[reject] {loc}: cited pageNum(s) {bad_pages} absent from packet manifest — "
                f"item dropped: {item.get('scopeText', '')[:80]!r}",
                file=sys.stderr,
            )
            rejected += 1
            continue

        # Mint subject using first citation's sheetId as the primary anchor
        primary_sheet_id = citations[0].get("sheetId", "")
        subject = mint_subject(item["scopeText"], primary_sheet_id, cluster_name)

        # Resolve isShownOn as human sheet numbers via the packet manifest
        shown_on = _shown_on_sheet_nos(citations, page_to_sheet_no)

        ready.append({
            "subject": subject,
            "scopeText": item["scopeText"],
            "candidateTrades": item["candidateTrades"],
            "resolvedTrade": item.get("resolvedTrade"),
            "tradeContest": item["tradeContest"],
            "furnishedBy": item.get("furnishedBy"),
            "installedBy": item.get("installedBy"),
            "isShownOn": shown_on,
            "confidence": item["confidence"],
            "citations": citations,
        })

    return ready, rejected


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Validate and ingest an agent-read JSON into scope-item claims."
    )
    parser.add_argument("--agent-read", required=True, help="Path to agent_read.json")
    parser.add_argument(
        "--packet-manifest", required=True, help="Path to packet_manifest.json"
    )
    parser.add_argument(
        "--out", required=True, help="Output path for scope_claims.jsonl"
    )
    args = parser.parse_args()

    agent_read_path = Path(args.agent_read)
    if not agent_read_path.exists():
        print(f"[error] agent-read file not found: {agent_read_path}", file=sys.stderr)
        sys.exit(1)

    manifest_path = Path(args.packet_manifest)
    if not manifest_path.exists():
        print(f"[error] packet manifest not found: {manifest_path}", file=sys.stderr)
        sys.exit(1)

    with agent_read_path.open("r", encoding="utf-8") as fh:
        agent_read = json.load(fh)

    # --- schema validation ---
    errors = validate_agent_read(agent_read)
    if errors:
        print("[error] agent-read failed schema validation:", file=sys.stderr)
        for e in errors:
            print(f"  {e}", file=sys.stderr)
        sys.exit(1)

    cluster_name = agent_read.get("clusterName", "unknown")
    scope_items = agent_read.get("scopeItems", [])

    manifest_pages = _load_manifest_page_nums(manifest_path)
    page_to_sheet_no = _load_manifest_page_to_sheet_no(manifest_path)

    # --- per-item processing ---
    ready_items, schema_rejected = _process_items(
        scope_items, manifest_pages, page_to_sheet_no, cluster_name
    )

    # --- write ---
    out_path = Path(args.out)
    written, write_rejected = write_scope_claims(ready_items, out_path)
    total_rejected = schema_rejected + write_rejected

    print(f"[ok] {written} items written, {total_rejected} rejected")
    if total_rejected > 0:
        print(
            f"     (see stderr for rejection details)",
            file=sys.stderr,
        )


if __name__ == "__main__":
    main()
