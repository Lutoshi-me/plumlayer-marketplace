"""
reconcile_overlap.py - the v0.1 heart: MEASURE routing from the overlap of
independent per-trade reads.

Doctrine role (agents read and judge; deterministic tooling grounds; nothing governs unverified):
  * Deterministic RECONCILE tool. It does NOT read drawings or assign trades by
    judgment. It intersects the decompose read's scope items with each trade
    lens's independent claims and COMPUTES routing from the overlap:
      - clear     = exactly ONE trade claimed the item        -> resolvedTrade
      - contested = TWO OR MORE trades independently claimed it -> a real boundary
      - unowned   = a decomposed item NO trade claimed         -> highest-value RFI
    This is the correct realization of decompose->route: routing is measured
    evidence, not a generalist's guess.
  * Two uncertainty axes, kept separate (the design's key distinction):
      - routing  (clear/contested/unowned) - WHO owns it.
      - is-it-real (confidence-by-agreement) - DOES it exist. The more independent
        readers reference an item, the higher its is-it-real confidence, computed
        by noisy-OR over the decompose read + each claiming trade, independent of
        whether routing is clear or contested.
  * netNewItems a trade raises (scope the generalist decompose missed) are emitted
    as their own items with provenance "net-new:<trade>". v0.1 does NOT dedup
    near-duplicate net-new items across trades - that light agent merge is deferred
    and logged honestly.
  * Output is proposed scope-item claims (the existing claim schema), consumed by
    project_scope.py unchanged. Nothing governs unverified.

Usage:
  python reconcile_overlap.py \\
    --decompose output/scope/decompose_read.json \\
    --trade-claims output/scope/trade_claims/ \\
    --packet-manifest output/scope/packet/packet_manifest.json \\
    --set-id PROJECT-DD \\
    --out output/scope/scope_claims.jsonl \\
    [--summary output/scope/reconcile_summary.json]

--trade-claims accepts any mix of files and directories (directories are globbed
for trade_claim_*.json).
"""

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path

# Sibling imports - tools/ is the package root
sys.path.insert(0, str(Path(__file__).parent))
from scope_claim_schema import mint_subject, write_scope_claims
from scope_v01_schema import (
    validate_decompose_read,
    decompose_item_ids,
    validate_trade_claim_read,
)

# Each additional independent reader that says "this scope exists" knocks down
# the remaining doubt by this factor (noisy-OR corroboration weight).
CLAIMANT_WEIGHT = 0.3


# ---------------------------------------------------------------------------
# Loading
# ---------------------------------------------------------------------------

def _load_json(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def _resolve_trade_claim_paths(inputs: list[str]) -> list[Path]:
    """Expand a mix of files and directories into a sorted list of claim files."""
    paths: list[Path] = []
    for raw in inputs:
        p = Path(raw)
        if p.is_dir():
            paths.extend(sorted(p.glob("trade_claim_*.json")))
        elif p.exists():
            paths.append(p)
        else:
            print(f"[warn] trade-claims path not found, skipped: {p}", file=sys.stderr)
    return paths


def _page_to_sheet_no(manifest_path: Path) -> dict[int, str]:
    manifest = _load_json(manifest_path)
    return {s["pageNum"]: s["sheetNo"] for s in manifest.get("sheets", []) if s.get("sheetNo")}


def _manifest_pages(manifest_path: Path) -> set[int]:
    """ALL pages in the rendered packet - the grounding gate's allow-list. Uses
    every manifest page (NOT the sheetNo-filtered map), so a rendered-but-
    unnumbered page still counts as grounded (expected on weakly-grounded sets)."""
    manifest = _load_json(manifest_path)
    return {s["pageNum"] for s in manifest.get("sheets", []) if s.get("pageNum") is not None}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _real_confidence(decompose_conf: float, n_claimants: int) -> float:
    """Noisy-OR corroboration: the decompose read is the base voter; each
    claiming trade is an independent corroborator. Monotonic in n_claimants,
    always < 1. n_claimants=0 (unowned) returns the bare decompose confidence."""
    doubt = (1.0 - decompose_conf) * (1.0 - CLAIMANT_WEIGHT) ** n_claimants
    return round(1.0 - doubt, 4)


def _shown_on(citations: list[dict], page_to_sheet: dict[int, str]) -> list[str]:
    """Human sheet numbers from cited pages (order-preserving, de-duplicated).
    Falls back to the citation's sheetId when a page lacks an inventory sheetNo
    (expected on weakly-grounded sets)."""
    seen: list[str] = []
    for c in citations:
        label = page_to_sheet.get(c.get("pageNum")) or c.get("sheetId", "")
        if label and label not in seen:
            seen.append(label)
    return seen


def _tag_citations(citations: list[dict], claimed_by: str | None) -> list[dict]:
    """Return copies of citations tagged with claimedBy (None for the decompose read)."""
    out = []
    for c in citations:
        tagged = dict(c)
        if claimed_by:
            tagged["claimedBy"] = claimed_by
        out.append(tagged)
    return out


# ---------------------------------------------------------------------------
# Reconcile
# ---------------------------------------------------------------------------

def reconcile(
    decompose: dict,
    trade_reads: list[dict],
    page_to_sheet: dict[int, str],
    set_id: str,
    manifest_pages: set[int] | None = None,
) -> tuple[list[dict], dict]:
    """
    Return (ready_items, summary). ready_items are dicts for write_scope_claims.

    GROUNDING GATE: when manifest_pages is given, every citation must cite a page
    that is in the rendered packet - an agent read cannot ground a claim on a page
    that was never rendered. Citations to out-of-packet pages are dropped; an item
    or claim left with NO grounded citation is rejected (honest counts, never
    silently kept). This is reconcile's anti-hallucination anchor.
    """
    def _grounded(cits: list[dict]) -> list[dict]:
        if manifest_pages is None:
            return list(cits)
        return [c for c in cits if c.get("pageNum") in manifest_pages]

    drops = {"ungroundedItems": 0, "ungroundedClaims": 0, "ungroundedNetNew": 0}

    # decompose items, restricted to grounded citations
    items_by_id: dict[str, dict] = {}
    for it in decompose["items"]:
        g = _grounded(it["citations"])
        if not g:
            drops["ungroundedItems"] += 1
            print(f"[reject] decompose item {it['itemId']!r}: all citations cite pages "
                  f"absent from the packet - dropped", file=sys.stderr)
            continue
        items_by_id[it["itemId"]] = {**it, "citations": g}

    # itemId -> {trade: {citations, furnishedBy, installedBy}}
    claims_by_item: dict[str, dict[str, dict]] = defaultdict(dict)
    net_new: list[tuple[str, dict]] = []  # (trade, item)
    for read in trade_reads:
        trade = read["tradeLens"]
        for claim in read.get("claims", []):
            iid = claim["itemId"]
            g = _grounded(claim.get("citations", []))
            if not g:
                drops["ungroundedClaims"] += 1
                print(f"[warn] {trade} claim on {iid!r}: citations cite pages absent from "
                      f"the packet - claim dropped (not counted as a claimant)", file=sys.stderr)
                continue
            # last claim for a (trade, item) wins; validator already forbade dupes
            claims_by_item[iid][trade] = {
                "citations": g,
                "furnishedBy": claim.get("furnishedBy"),
                "installedBy": claim.get("installedBy"),
            }
        for item in read.get("netNewItems", []):
            g = _grounded(item.get("citations", []))
            if not g:
                drops["ungroundedNetNew"] += 1
                print(f"[warn] {trade} net-new item cites pages absent from the packet - "
                      f"dropped", file=sys.stderr)
                continue
            net_new.append((trade, {**item, "citations": g}))

    ready: list[dict] = []
    counts = {"clear": 0, "contested": 0, "unowned": 0}

    # --- decomposed items ---
    for iid, item in items_by_id.items():
        claimants = sorted(claims_by_item.get(iid, {}).keys())
        n = len(claimants)
        decompose_conf = float(item["confidence"])
        real_conf = _real_confidence(decompose_conf, n)

        if n == 0:
            contest, resolved, candidates = "unowned", None, []
            furnished = installed = None
        elif n == 1:
            contest, resolved, candidates = "clear", claimants[0], claimants
            c = claims_by_item[iid][claimants[0]]
            furnished, installed = c["furnishedBy"], c["installedBy"]
        else:
            contest, resolved, candidates = "contested", None, claimants
            furnished = installed = None

        counts[contest] += 1

        # merge citations: decompose evidence first, then each claimant's
        merged = _tag_citations(item["citations"], None)
        for trade in claimants:
            merged += _tag_citations(claims_by_item[iid][trade]["citations"], trade)

        primary_sheet_id = merged[0].get("sheetId", "") if merged else ""
        ready.append({
            "subject": mint_subject(item["scopeText"], primary_sheet_id, set_id),
            "title": item.get("title") or item["scopeText"][:80],
            "scopeText": item["scopeText"],
            "candidateTrades": candidates,
            "resolvedTrade": resolved,
            "tradeContest": contest,
            "furnishedBy": furnished,
            "installedBy": installed,
            "isShownOn": _shown_on(merged, page_to_sheet),
            "confidence": real_conf,
            "citations": merged,
            "provenance": "decompose",
        })

    # --- net-new items (one claimant by construction; flagged by provenance) ---
    net_new_count = 0
    for trade, item in net_new:
        net_new_count += 1
        decompose_conf = float(item["confidence"])
        real_conf = _real_confidence(decompose_conf, 1)  # the raising trade corroborates
        merged = _tag_citations(item["citations"], trade)
        primary_sheet_id = merged[0].get("sheetId", "") if merged else ""
        counts["clear"] += 1
        ready.append({
            "subject": mint_subject(item["scopeText"], primary_sheet_id, set_id),
            "title": item.get("title") or item["scopeText"][:80],
            "scopeText": item["scopeText"],
            "candidateTrades": [trade],
            "resolvedTrade": trade,
            "tradeContest": "clear",
            "furnishedBy": item.get("furnishedBy"),
            "installedBy": item.get("installedBy"),
            "isShownOn": _shown_on(merged, page_to_sheet),
            "confidence": real_conf,
            "citations": merged,
            "provenance": f"net-new:{trade}",
        })

    summary = {
        "setId": set_id,
        "decomposedItems": len(items_by_id),
        "tradeLenses": sorted(r["tradeLens"] for r in trade_reads),
        "routing": counts,
        "netNewItems": net_new_count,
        "claimantWeight": CLAIMANT_WEIGHT,
        "groundingDrops": drops,
    }
    return ready, summary


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Reconcile per-trade claims against the decompose read by overlap."
    )
    parser.add_argument("--decompose", required=True, help="Path to decompose_read.json")
    parser.add_argument(
        "--trade-claims", required=True, nargs="+",
        help="Trade-claim JSON files and/or directories (globbed for trade_claim_*.json)",
    )
    parser.add_argument("--packet-manifest", required=True, help="Path to packet_manifest.json")
    parser.add_argument("--set-id", required=True, help="Per-set identifier (subject namespace)")
    parser.add_argument("--out", required=True, help="Output scope_claims.jsonl path")
    parser.add_argument("--summary", default=None, help="Optional reconcile_summary.json path")
    args = parser.parse_args()

    decompose_path = Path(args.decompose)
    manifest_path = Path(args.packet_manifest)
    for p, label in [(decompose_path, "decompose"), (manifest_path, "packet-manifest")]:
        if not p.exists():
            print(f"[error] {label} not found: {p}", file=sys.stderr)
            sys.exit(1)

    decompose = _load_json(decompose_path)
    derrs = validate_decompose_read(decompose)
    if derrs:
        print("[error] decompose read failed validation:", file=sys.stderr)
        for e in derrs:
            print(f"  {e}", file=sys.stderr)
        sys.exit(1)
    known_ids = decompose_item_ids(decompose)

    trade_paths = _resolve_trade_claim_paths(args.trade_claims)
    if not trade_paths:
        print("[error] no trade-claim files resolved", file=sys.stderr)
        sys.exit(1)

    trade_reads: list[dict] = []
    for tp in trade_paths:
        read = _load_json(tp)
        terrs = validate_trade_claim_read(read, known_ids)
        if terrs:
            print(f"[error] {tp.name} failed validation:", file=sys.stderr)
            for e in terrs:
                print(f"  {e}", file=sys.stderr)
            sys.exit(1)
        trade_reads.append(read)

    page_to_sheet = _page_to_sheet_no(manifest_path)
    manifest_pages = _manifest_pages(manifest_path)
    ready, summary = reconcile(
        decompose, trade_reads, page_to_sheet, args.set_id, manifest_pages
    )

    written, rejected = write_scope_claims(ready, Path(args.out))

    r = summary["routing"]
    print(
        f"[ok] {written} scope items written ({rejected} rejected) | "
        f"clear {r['clear']}  contested {r['contested']}  unowned {r['unowned']}  "
        f"| net-new {summary['netNewItems']}  | lenses {len(summary['tradeLenses'])}"
    )
    d = summary["groundingDrops"]
    if any(d.values()):
        print(
            f"     grounding gate dropped: {d['ungroundedItems']} item(s), "
            f"{d['ungroundedClaims']} claim(s), {d['ungroundedNetNew']} net-new "
            f"(cited pages absent from the packet)",
            file=sys.stderr,
        )
    if summary["netNewItems"]:
        print(
            f"     note: {summary['netNewItems']} net-new item(s) emitted un-deduped "
            f"(cross-trade merge deferred - v0.1)",
            file=sys.stderr,
        )

    if args.summary:
        with Path(args.summary).open("w", encoding="utf-8") as fh:
            json.dump(summary, fh, indent=2)
        print(f"     summary -> {args.summary}")


if __name__ == "__main__":
    main()
