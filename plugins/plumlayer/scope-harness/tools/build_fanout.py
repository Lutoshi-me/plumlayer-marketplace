"""
build_fanout.py — prepare per-trade-lens fan-out inputs (DATA, not code).

PLU-323 guard: superseded route-first tool retained for PLU-274 history/migration only.

Doctrine role (agents read and judge; deterministic tooling grounds; nothing governs unverified):
  * Deterministic GLUE tool. The fan-out is not a hand-baked per-run script. This
    tool reads the merged decompose read + the committed trade lenses + the packet
    manifest and writes, PER LENS, a self-contained DATA input
    (`fanout/input_<lens>.json`) that the `trade-specialist` subagent reads.
  * Separation that answers "what is a trade-specialist?": the agent carries the
    METHOD (how to read a lens — its system prompt) and is STABLE; this tool
    injects the per-run DATA (which items, which lens fields). Trade KNOWLEDGE
    lives in `$CLAUDE_PLUGIN_ROOT/scope-harness/trade-lenses.json` — the single
    inspectable iteration surface — and is *loaded*, never baked into the agent.
    Sharpen the oracle by editing the lens file; nothing here or in the agent changes.
  * No semantic inference: this tool only joins + reshapes grounded data. It never
    decides scope or routing.

Per-project delta is the cluster config + this generated input — never code.

Usage:
  python build_fanout.py \\
    --decompose output/scope/<job>/decompose_read.json \\
    --packet-manifest output/scope/<job>/packet/packet_manifest.json \\
    --out-dir output/scope/<job>/fanout/ \\
    [--lenses <path-to-trade-lenses.json>] \\
    [--set-id <SETID>]
"""

import argparse
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
DEFAULT_LENSES = HERE.parent / "trade-lenses.json"
FANOUT_INPUT_SCHEMA = "fanout-input-v0.2"
CLAIM_CONTRACT = "trade-claim-v0.2"


def _sheet_maps(manifest: dict) -> dict[int, dict]:
    """pageNum -> {sheetId, sheetNo, title} from the packet manifest."""
    by_page: dict[int, dict] = {}
    for sh in manifest.get("sheets", []):
        pg = sh.get("pageNum")
        if pg is None:
            continue
        by_page[int(pg)] = {
            "sheetId": sh.get("sheetId"),
            "sheetNo": sh.get("sheetNo"),
            "title": sh.get("title"),
        }
    return by_page


def main() -> None:
    ap = argparse.ArgumentParser(description="Prepare per-lens fan-out DATA inputs.")
    ap.add_argument("--decompose", required=True, help="decompose_read.json (scope-decompose-v0.3)")
    ap.add_argument("--packet-manifest", required=True, help="packet_manifest.json")
    ap.add_argument("--out-dir", required=True, help="fan-out output dir (e.g. output/scope/<job>/fanout/)")
    ap.add_argument("--lenses", default=str(DEFAULT_LENSES), help=f"trade-lenses.json (default {DEFAULT_LENSES})")
    ap.add_argument("--set-id", default=None, help="override setId (default: decompose read's setId)")
    args = ap.parse_args()

    decompose = json.loads(Path(args.decompose).read_text(encoding="utf-8"))
    manifest = json.loads(Path(args.packet_manifest).read_text(encoding="utf-8"))
    lenses_doc = json.loads(Path(args.lenses).read_text(encoding="utf-8"))
    lenses = lenses_doc.get("lenses", [])
    if not lenses:
        print(f"[error] no lenses in {args.lenses}", file=sys.stderr)
        sys.exit(1)

    set_id = args.set_id or decompose.get("setId") or "unknown"
    by_page = _sheet_maps(manifest)

    # Sheet list for net-new grounding (sheetNo=pageNum the agent can cite).
    sheets = [
        {"sheetNo": v["sheetNo"], "pageNum": pg, "sheetId": v["sheetId"], "title": v["title"]}
        for pg, v in sorted(by_page.items())
    ]

    # Trade-agnostic item list every lens reads (same for all lenses).
    items = []
    for it in decompose.get("items", []):
        c = (it.get("citations") or [{}])[0]
        pg = c.get("pageNum")
        sheet_no = by_page.get(pg, {}).get("sheetNo") or c.get("sheetId", "?")
        items.append({
            "itemId": it["itemId"],
            "sheetNo": sheet_no,
            "pageNum": pg,
            "title": it.get("title", ""),
            "scopeText": it.get("scopeText", ""),
        })

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    # wipe stale lens inputs so a re-run never leaves a removed lens behind
    for f in out_dir.glob("input_*.json"):
        f.unlink()

    manifest_lenses = []
    for lens in lenses:
        name = lens["lens"]
        out_path = f"trade_claims/raw_{name}.json"
        payload = {
            "schemaVersion": FANOUT_INPUT_SCHEMA,
            "setId": set_id,
            "tradeLens": name,
            "claimContract": CLAIM_CONTRACT,
            "lens": {
                "scope": lens.get("scope", []),
                "excludes": lens.get("excludes", []),
                "furnishInstallSplits": lens.get("furnishInstallSplits", []),
                "netNewProbes": lens.get("netNewProbes", []),
            },
            "sheets": sheets,
            "items": items,
            "writeRawTo": out_path,
        }
        in_path = out_dir / f"input_{name}.json"
        in_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        manifest_lenses.append({"lens": name, "inputPath": str(in_path).replace("\\", "/"), "rawOut": out_path})

    fanout_manifest = {
        "schemaVersion": FANOUT_INPUT_SCHEMA,
        "setId": set_id,
        "decomposeItems": len(items),
        "lensCount": len(lenses),
        "lenses": manifest_lenses,
    }
    (out_dir / "fanout_manifest.json").write_text(json.dumps(fanout_manifest, indent=2), encoding="utf-8")

    print(f"[ok] set {set_id}: {len(items)} items x {len(lenses)} lenses")
    for ml in manifest_lenses:
        print(f"  -> {ml['inputPath']}  (raw -> {ml['rawOut']})")
    print(f"  -> {out_dir / 'fanout_manifest.json'}")


if __name__ == "__main__":
    main()
