"""
ingest_fanout.py — ground per-lens raw trade claims into the validated contract.

Doctrine role (agents read and judge; deterministic tooling grounds; nothing governs unverified):
  * Deterministic GLUE tool. Each `trade-specialist` subagent writes a RAW claim
    file (`trade_claims/raw_<lens>.json`) that claims decompose items by `itemId`
    and raises net-new scope — but carries NO per-claim citation (a text-pass agent
    reasons over the item text, so its claim inherits the item's grounding). This
    tool performs the GROUNDING join:
      - each claim's citation := the referenced decompose item's own citation;
      - dangling itemId refs (not in the decompose read) are DROPPED + logged;
      - net-new items map pageNum -> sheetId via the packet manifest; off-packet
        net-new are DROPPED + logged (never reach reconcile's hard validator).
    Output: `trade_claims/trade_claim_<lens>.json` (trade-claim-v0.2), validated.
  * No inference: it joins grounded data and enforces the contract; it never
    decides scope or routing. Honest coverage: prints what it dropped.

Usage:
  python ingest_fanout.py \\
    --raw-dir output/scope/<job>/trade_claims/ \\
    --decompose output/scope/<job>/decompose_read.json \\
    --packet-manifest output/scope/<job>/packet/packet_manifest.json \\
    [--set-id <SETID>]
"""

import argparse
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))
import scope_v01_schema as schema  # noqa: E402


def _norm(v):
    if v is None:
        return None
    s = str(v).strip()
    return None if s.lower() in ("", "null", "none", "n/a", "tbd", "unknown") else s


def main() -> None:
    ap = argparse.ArgumentParser(description="Ground raw per-lens trade claims into the validated contract.")
    ap.add_argument("--raw-dir", required=True, help="dir with raw_<lens>.json files (also where outputs land)")
    ap.add_argument("--decompose", required=True, help="decompose_read.json")
    ap.add_argument("--packet-manifest", required=True, help="packet_manifest.json")
    ap.add_argument("--set-id", default=None, help="override setId (default: decompose read's setId)")
    args = ap.parse_args()

    decompose = json.loads(Path(args.decompose).read_text(encoding="utf-8"))
    manifest = json.loads(Path(args.packet_manifest).read_text(encoding="utf-8"))
    set_id = args.set_id or decompose.get("setId") or "unknown"

    by_id = {it["itemId"]: it for it in decompose.get("items", [])}
    known_ids = set(by_id)
    page_to_sheet = {sh["pageNum"]: sh["sheetId"] for sh in manifest.get("sheets", []) if sh.get("pageNum") is not None}
    valid_pages = set(page_to_sheet)

    def item_citation(it):
        c = (it.get("citations") or [{}])[0]
        return [{"sheetId": c.get("sheetId"), "pageNum": c.get("pageNum"),
                 "bboxNorm": c.get("bboxNorm", [0, 0, 1, 1]), "snippet": c.get("snippet", "")}]

    raw_dir = Path(args.raw_dir)
    raw_files = sorted(raw_dir.glob("raw_*.json"))
    if not raw_files:
        print(f"[error] no raw_<lens>.json files in {raw_dir}", file=sys.stderr)
        sys.exit(1)

    # wipe stale validated outputs so a removed lens never lingers
    for f in raw_dir.glob("trade_claim_*.json"):
        f.unlink()

    summary, dangling, ungrounded, invalid = [], [], [], []
    for rf in raw_files:
        raw = json.loads(rf.read_text(encoding="utf-8"))
        lens = raw.get("tradeLens") or rf.stem[len("raw_"):]

        claims_out = []
        for c in raw.get("claims", []):
            iid = c.get("itemId")
            if iid not in by_id:
                dangling.append(f"{lens}:{iid}")
                continue
            claims_out.append({
                "itemId": iid,
                "furnishedBy": _norm(c.get("furnishedBy")),
                "installedBy": _norm(c.get("installedBy")),
                "note": c.get("note", ""),
                "citations": item_citation(by_id[iid]),
            })

        netnew_out = []
        for n in raw.get("netNewItems", []):
            pg = n.get("pageNum")
            if pg not in valid_pages:
                ungrounded.append(f"{lens}:p{pg}:{str(n.get('title', ''))[:40]}")
                continue
            netnew_out.append({
                "title": n.get("title", ""),
                "scopeText": n.get("scopeText", ""),
                "confidence": round(float(n.get("confidence", 0.6)), 4),
                "citations": [{"sheetId": page_to_sheet[pg], "pageNum": pg,
                               "bboxNorm": n.get("bboxNorm", [0, 0, 1, 1]), "snippet": n.get("snippet", "")}],
            })

        out = {"schemaVersion": schema.TRADE_CLAIM_SCHEMA_VERSION, "setId": set_id, "tradeLens": lens,
               "claims": claims_out, "netNewItems": netnew_out}
        errs = schema.validate_trade_claim_read(out, known_item_ids=known_ids)
        if errs:
            invalid.append(f"{lens}: {len(errs)} error(s): {errs[:3]}")
        (raw_dir / f"trade_claim_{lens}.json").write_text(json.dumps(out, indent=2), encoding="utf-8")
        summary.append(f"{lens}: {len(claims_out)} claims, {len(netnew_out)} net-new")

    print(f"[ok] set {set_id}: ingested {len(raw_files)} lens read(s):")
    for s in summary:
        print("  " + s)
    if dangling:
        print(f"[warn] dropped {len(dangling)} dangling claim ref(s): {dangling}", file=sys.stderr)
    if ungrounded:
        print(f"[warn] dropped {len(ungrounded)} off-packet net-new: {ungrounded}", file=sys.stderr)
    if invalid:
        print(f"[error] {len(invalid)} lens output(s) FAILED contract validation:", file=sys.stderr)
        for s in invalid:
            print("  " + s, file=sys.stderr)
        sys.exit(2)


if __name__ == "__main__":
    main()
