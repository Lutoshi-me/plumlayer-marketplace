"""
merge_decompose.py — merge per-sheet decompose reads into one decompose_read.json.

PLU-323 guard: superseded route-first tool retained for PLU-274 history/migration only.

Doctrine role (agents read and judge; deterministic tooling grounds; nothing governs unverified):
  * Deterministic GLUE tool. The decompose stage dispatches ONE `scope-decomposer`
    subagent per scope-bearing sheet; each writes a RAW per-sheet read
    (`decompose/raw_<sheetId>.json`) carrying items with title / scopeText /
    confidence / bboxNorm / snippet — but NO itemId and NO pageNum (the agent
    reads pixels, it does not mint identity or know page numbers).
  * This tool performs the deterministic merge: mint a UNIQUE itemId per item
    (`<sheetId>-i<NN>`, per-sheet 1-based), attach pageNum + the citation
    (sheetId + pageNum + bboxNorm + snippet) from the packet manifest, and
    concatenate into `decompose_read.json` (scope-decompose-v0.3), then validate.
    Carries the optional v0.3 `appliesTo` (grouped instance labels) through.
  * The itemId-uniqueness invariant the whole fan-out rests on is enforced HERE
    (a collision would silently merge two scope items) — see scope_v01_schema.
  * Honest coverage: prints per-sheet counts and flags genuinely-empty sheets the
    agent marked (placeholder / NOT USED), never hiding a zero behind a total.

Usage:
  python merge_decompose.py \\
    --raw-dir output/scope/<job>/decompose/ \\
    --packet-manifest output/scope/<job>/packet/packet_manifest.json \\
    --set-id <SETID> \\
    --out output/scope/<job>/decompose_read.json
"""

import argparse
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))
import scope_v01_schema as schema  # noqa: E402


def main() -> None:
    ap = argparse.ArgumentParser(description="Merge per-sheet decompose reads into decompose_read.json.")
    ap.add_argument("--raw-dir", required=True, help="dir with raw_<sheetId>.json per-sheet reads")
    ap.add_argument("--packet-manifest", required=True, help="packet_manifest.json")
    ap.add_argument("--set-id", required=True, help="set identifier (e.g. PROJECT-DD)")
    ap.add_argument("--out", required=True, help="decompose_read.json output path")
    args = ap.parse_args()

    manifest = json.loads(Path(args.packet_manifest).read_text(encoding="utf-8"))
    page_of = {sh["sheetId"]: sh.get("pageNum") for sh in manifest.get("sheets", [])}
    # stable sheet order = packet manifest order (page order), so itemIds are deterministic
    sheet_order = [sh["sheetId"] for sh in manifest.get("sheets", [])]

    raw_dir = Path(args.raw_dir)
    raws = {}
    for rf in raw_dir.glob("raw_*.json"):
        d = json.loads(rf.read_text(encoding="utf-8"))
        sid = d.get("sheetId") or rf.stem[len("raw_"):]
        raws[sid] = d

    items, per_sheet, empty_sheets = [], [], []
    # iterate in manifest order; append any extra sheets not in the manifest at the end
    ordered = [s for s in sheet_order if s in raws] + [s for s in raws if s not in sheet_order]
    for sid in ordered:
        d = raws[sid]
        pg = page_of.get(sid)
        sheet_items = d.get("items", []) or []
        if not sheet_items:
            empty_sheets.append((sid, d.get("note", "(no note)")))
        for i, it in enumerate(sheet_items, start=1):
            item_id = f"{sid}-i{i:02d}"
            merged_item = {
                "itemId": item_id,
                "title": it.get("title", ""),
                "scopeText": it.get("scopeText", ""),
                "confidence": it.get("confidence", 0.6),
                "citations": [{
                    "sheetId": sid,
                    "pageNum": pg,
                    "bboxNorm": it.get("bboxNorm", [0, 0, 1, 1]),
                    "snippet": it.get("snippet", ""),
                }],
            }
            # v0.3: carry the grouped-instance list through if the agent emitted it
            applies = it.get("appliesTo")
            if isinstance(applies, list) and applies:
                merged_item["appliesTo"] = [str(a) for a in applies]
            # v0.5: carry optional motif-grounded count fields through (omit when absent)
            if it.get("groundedCount") is not None:
                merged_item["groundedCount"] = it["groundedCount"]
            if it.get("motifRef") is not None:
                merged_item["motifRef"] = it["motifRef"]
            items.append(merged_item)
        per_sheet.append((sid, len(sheet_items)))

    out = {"schemaVersion": schema.DECOMPOSE_SCHEMA_VERSION, "setId": args.set_id, "items": items}
    errs = schema.validate_decompose_read(out)
    if errs:
        print(f"[error] merged decompose FAILED contract validation ({len(errs)}):", file=sys.stderr)
        for e in errs[:10]:
            print("  " + e, file=sys.stderr)
        sys.exit(2)

    Path(args.out).write_text(json.dumps(out, indent=2), encoding="utf-8")
    print(f"[ok] set {args.set_id}: merged {len(items)} items from {len(raws)} sheet read(s)")
    for sid, n in per_sheet:
        print(f"  {sid}: {n} items")
    if empty_sheets:
        print(f"[note] {len(empty_sheets)} sheet(s) returned 0 items (agent-flagged empty/placeholder):")
        for sid, note in empty_sheets:
            print(f"  {sid}: {note}")


if __name__ == "__main__":
    main()
