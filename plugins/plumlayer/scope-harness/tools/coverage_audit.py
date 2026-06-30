"""
coverage_audit.py - the COMPLETENESS ledger: cross-check the fan-out against the
COMPLETE set and surface what nobody touched.

PLU-323 guard: superseded route-first tool retained for PLU-274 history/migration only.

Doctrine role (agents read and judge; deterministic tooling grounds; nothing governs unverified):
  Fanning every trade lens across the whole set is not just parallelism - it lets
  us audit COVERAGE. Routing (reconcile_overlap.py) answers "who owns each item";
  this tool answers the orthogonal question "did anything fall through the cracks
  at all". The two are different axes:
      * grain        = how finely scope was expressed (decompose's job)
      * completeness = whether any sheet / item / symbol went unread or unclaimed

  It is a DETERMINISTIC audit - it reads no drawings and assigns no trade. It joins
  the rendered packet (the complete set), the decompose read, and the per-trade
  claims, then flags:
      * zero-trade sheet  - decomposed, but NO trade claimed a single item on it
      * unread sheet      - in the packet, but decompose produced 0 items AND no
                            agent confirmation it is non-scope-bearing
      * thin-coverage     - most of a sheet's items are unowned (coverage is sparse)
      * unowned items     - decomposed scope no trade claimed (the RFI pile)
      * net-new           - scope a trade raised that the decompose read missed
                            (itself a signal the generalist read under-covered)

  A sheet an agent EXPLICITLY confirmed non-scope-bearing (raw decompose
  sheetIsScopeBearing == false, e.g. a "NOT USED" placeholder) is OK, not a miss -
  this is why --raw-decompose matters: it separates "agent read it and said it's
  empty" from "decompose never produced anything".

  Symbol / keynote / abbreviation coverage ("this symbol means nothing to anybody")
  is NOT yet instrumented - it needs legend/keynote extraction from the comprehend
  stage. The ledger names that gap explicitly rather than pretending completeness.

  Output is an audit, not a claim - nothing here governs. It tells a human (and the
  orchestrator) where to look before trusting the scope draft.

Usage:
  python coverage_audit.py \\
    --decompose output/scope/<job>/decompose_read.json \\
    --trade-claims output/scope/<job>/trade_claims/ \\
    --packet-manifest output/scope/<job>/packet/packet_manifest.json \\
    --set-id PROJECT-DD \\
    [--raw-decompose output/scope/<job>/decompose/] \\
    --out output/scope/<job>/coverage_ledger.json \\
    [--md output/scope/<job>/coverage_ledger.md]

--trade-claims accepts any mix of files and directories (globbed for
trade_claim_*.json), matching reconcile_overlap.py.
"""

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from scope_v01_schema import (
    validate_decompose_read,
    decompose_item_ids,
    validate_trade_claim_read,
)

# A scope-bearing sheet whose unowned items are at least this fraction of its
# decomposed items is "thin" - read, but barely claimed by the fanned trades.
THIN_UNOWNED_RATIO = 0.5

# Unowned items are EXPECTED output (the RFI pile), not a completeness failure -
# so they are never red. But when one sheet hoards the pile it is a "look here"
# signal: flag amber if a sheet holds at least this many unowned items AND at
# least this share of ALL unowned items. Catches the finish-schedule case where
# many unowned items sit on one over-split sheet (grain poisoning coverage).
UNOWNED_CONCENTRATION_MIN = 10
UNOWNED_CONCENTRATION_SHARE = 0.33


def _load_json(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def _resolve_trade_claim_paths(inputs: list[str]) -> list[Path]:
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


def _item_sheets(item: dict, page_to_sheet: dict[int, str]) -> list[str]:
    """The sheetIds an item's evidence lands on (order-preserving, de-duped).
    Prefer the citation's own sheetId; fall back to pageNum->sheetId from the
    manifest for citations that carry only a page."""
    seen: list[str] = []
    for c in item.get("citations", []):
        sid = c.get("sheetId") or page_to_sheet.get(c.get("pageNum"))
        if sid and sid not in seen:
            seen.append(sid)
    return seen


def _raw_scope_bearing(raw_dir: Path | None) -> dict[str, dict]:
    """sheetId -> {sheetIsScopeBearing, note} from the per-sheet raw decompose
    files, when available. Lets the audit tell an agent-confirmed placeholder
    apart from a sheet decompose simply never produced items for."""
    out: dict[str, dict] = {}
    if raw_dir is None:
        return out
    for fp in sorted(raw_dir.glob("raw_*.json")):
        try:
            d = _load_json(fp)
        except (OSError, json.JSONDecodeError):
            continue
        sid = d.get("sheetId")
        if sid:
            out[sid] = {
                "sheetIsScopeBearing": d.get("sheetIsScopeBearing"),
                "note": d.get("note"),
            }
    return out


def audit(
    decompose: dict,
    trade_reads: list[dict],
    manifest: dict,
    set_id: str,
    raw_meta: dict[str, dict],
) -> dict:
    sheets = manifest.get("sheets", [])
    page_to_sheet = {
        s["pageNum"]: s["sheetId"]
        for s in sheets
        if s.get("pageNum") is not None and s.get("sheetId")
    }
    sheet_meta = {
        s["sheetId"]: {"sheetNo": s.get("sheetNo"), "pageNum": s.get("pageNum"),
                       "title": s.get("title")}
        for s in sheets if s.get("sheetId")
    }

    # item -> sheets it cites
    item_sheets: dict[str, list[str]] = {}
    for it in decompose["items"]:
        item_sheets[it["itemId"]] = _item_sheets(it, page_to_sheet)

    # item -> set(trades that claimed it)
    item_trades: dict[str, set[str]] = defaultdict(set)
    net_new_by_trade: dict[str, int] = defaultdict(int)
    for read in trade_reads:
        trade = read["tradeLens"]
        for claim in read.get("claims", []):
            item_trades[claim["itemId"]].add(trade)
        net_new_by_trade[trade] += len(read.get("netNewItems", []))

    # ---- per-sheet roll-up ----
    sheet_rows: list[dict] = []
    for sid, meta in sheet_meta.items():
        items_here = [iid for iid, sl in item_sheets.items() if sid in sl]
        trades_here: set[str] = set()
        unowned_here = 0
        for iid in items_here:
            t = item_trades.get(iid, set())
            trades_here |= t
            if not t:
                unowned_here += 1

        n_items = len(items_here)
        rb = raw_meta.get(sid, {})
        scope_bearing = rb.get("sheetIsScopeBearing")

        if n_items == 0:
            if scope_bearing is False:
                status, level = "non-scope-bearing", "ok"
            else:
                status, level = "unread", "red"
        elif not trades_here:
            status, level = "zero-trade", "red"
        elif n_items and unowned_here / n_items >= THIN_UNOWNED_RATIO:
            status, level = "thin-coverage", "amber"
        else:
            status, level = "covered", "ok"

        sheet_rows.append({
            "sheetId": sid,
            "sheetNo": meta["sheetNo"],
            "pageNum": meta["pageNum"],
            "title": meta["title"],
            "decomposedItems": n_items,
            "claimingTrades": sorted(trades_here),
            "unownedItems": unowned_here,
            "status": status,
            "level": level,
            "note": rb.get("note") if status in ("non-scope-bearing", "unread") else None,
        })

    sheet_rows.sort(key=lambda r: (r["pageNum"] if r["pageNum"] is not None else 1e9))

    # ---- item-level coverage ----
    total_items = len(item_sheets)
    unowned_ids = [iid for iid in item_sheets if not item_trades.get(iid)]
    unowned_by_sheet: dict[str, int] = defaultdict(int)
    for iid in unowned_ids:
        for sid in item_sheets[iid] or ["(uncited)"]:
            unowned_by_sheet[sid] += 1

    # ---- headline flags ----
    flags: list[dict] = []
    for r in sheet_rows:
        if r["level"] == "red":
            msg = ("decomposed but NO trade claimed any item on it"
                   if r["status"] == "zero-trade"
                   else "in the packet but decompose produced 0 items and no agent "
                        "confirmation it is non-scope-bearing")
            flags.append({"level": "red", "scope": "sheet", "sheetId": r["sheetId"],
                          "sheetNo": r["sheetNo"], "message": msg})
        elif r["level"] == "amber":
            flags.append({"level": "amber", "scope": "sheet", "sheetId": r["sheetId"],
                          "sheetNo": r["sheetNo"],
                          "message": f"thin coverage - {r['unownedItems']}/"
                                     f"{r['decomposedItems']} items unowned"})

    # unowned-concentration flags (amber, informational - not a completeness fail)
    total_unowned = len(unowned_ids)
    if total_unowned:
        by_sheet = {r["sheetId"]: r for r in sheet_rows}
        for sid, n in unowned_by_sheet.items():
            if n >= UNOWNED_CONCENTRATION_MIN and n / total_unowned >= UNOWNED_CONCENTRATION_SHARE:
                row = by_sheet.get(sid, {})
                share = round(100 * n / total_unowned)
                flags.append({"level": "amber", "scope": "unowned-concentration",
                              "sheetId": sid, "sheetNo": row.get("sheetNo"),
                              "message": f"holds {n} of {total_unowned} unowned items "
                                         f"({share}% of the pile) - go here first"})

    n_red = sum(1 for f in flags if f["level"] == "red")
    n_amber = sum(1 for f in flags if f["level"] == "amber")

    return {
        "setId": set_id,
        "complete": n_red == 0,
        "sheetCoverage": {
            "totalSheets": len(sheet_rows),
            "covered": sum(1 for r in sheet_rows if r["status"] == "covered"),
            "nonScopeBearing": sum(1 for r in sheet_rows if r["status"] == "non-scope-bearing"),
            "thinCoverage": sum(1 for r in sheet_rows if r["status"] == "thin-coverage"),
            "zeroTrade": sum(1 for r in sheet_rows if r["status"] == "zero-trade"),
            "unread": sum(1 for r in sheet_rows if r["status"] == "unread"),
            "sheets": sheet_rows,
        },
        "itemCoverage": {
            "totalItems": total_items,
            "claimed": total_items - len(unowned_ids),
            "unowned": len(unowned_ids),
            "unownedBySheet": dict(sorted(unowned_by_sheet.items(),
                                          key=lambda kv: -kv[1])),
        },
        "netNew": {
            "total": sum(net_new_by_trade.values()),
            "byTrade": dict(net_new_by_trade),
            "note": "scope trades raised that the decompose read missed - a "
                    "completeness signal on the generalist read",
        },
        "symbolCoverage": {
            "status": "not-yet-instrumented",
            "note": "legend / keynote / abbreviation coverage ('this symbol means "
                    "nothing to anybody') requires extraction from the comprehend "
                    "stage - not yet built. Named here so the ledger does not assert "
                    "a completeness it has not checked.",
        },
        "flags": flags,
        "summary": {"red": n_red, "amber": n_amber},
    }


def render_md(ledger: dict) -> str:
    icon = {"ok": "[ok]", "amber": "[!]", "red": "[RED]"}
    L = []
    L.append(f"# Coverage ledger - {ledger['setId']}")
    s = ledger["summary"]
    verdict = "COMPLETE (no red flags)" if ledger["complete"] else f"{s['red']} RED flag(s)"
    L.append("")
    L.append(f"**Verdict:** {verdict}  -  {s['red']} red, {s['amber']} amber. "
             "This is a completeness audit of the fan-out against the complete set, "
             "not a scope claim.")
    L.append("")

    sc = ledger["sheetCoverage"]
    L.append("## Sheet coverage")
    L.append("")
    L.append(f"{sc['totalSheets']} sheets - {sc['covered']} covered, "
             f"{sc['thinCoverage']} thin, {sc['zeroTrade']} zero-trade, "
             f"{sc['unread']} unread, {sc['nonScopeBearing']} non-scope-bearing.")
    L.append("")
    L.append("| Sheet | Items | Claiming trades | Unowned | Status |")
    L.append("|---|---|---|---|---|")
    for r in sc["sheets"]:
        trades = ", ".join(r["claimingTrades"]) or "-"
        L.append(f"| {icon[r['level']]} {r['sheetNo'] or r['sheetId']} | "
                 f"{r['decomposedItems']} | {trades} | {r['unownedItems']} | {r['status']} |")
    L.append("")

    ic = ledger["itemCoverage"]
    L.append("## Item coverage")
    L.append("")
    L.append(f"{ic['totalItems']} items - {ic['claimed']} claimed, "
             f"{ic['unowned']} unowned (the RFI pile). Unowned concentration by sheet:")
    L.append("")
    for sid, n in ic["unownedBySheet"].items():
        L.append(f"- `{sid}` - {n} unowned")
    L.append("")

    nn = ledger["netNew"]
    L.append("## Net-new (decompose under-coverage)")
    L.append("")
    L.append(f"{nn['total']} item(s) trades raised that the decompose read missed.")
    for t, n in nn["byTrade"].items():
        if n:
            L.append(f"- {t}: {n}")
    L.append("")

    L.append("## Symbol / keynote coverage")
    L.append("")
    L.append(f"_{ledger['symbolCoverage']['status']}_ - {ledger['symbolCoverage']['note']}")
    L.append("")

    if ledger["flags"]:
        L.append("## Flags (look here first)")
        L.append("")
        for f in ledger["flags"]:
            tag = "RED" if f["level"] == "red" else "AMBER"
            label = f.get("sheetNo") or f.get("sheetId")
            L.append(f"- **{tag}** [{f['scope']} {label}] {f['message']}")
        L.append("")
    return "\n".join(L)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Audit fan-out coverage against the complete set."
    )
    parser.add_argument("--decompose", required=True)
    parser.add_argument("--trade-claims", required=True, nargs="+")
    parser.add_argument("--packet-manifest", required=True)
    parser.add_argument("--set-id", required=True)
    parser.add_argument("--raw-decompose", default=None,
                        help="Optional dir of per-sheet raw decompose files "
                             "(reads sheetIsScopeBearing to spare confirmed placeholders)")
    parser.add_argument("--out", required=True, help="coverage_ledger.json path")
    parser.add_argument("--md", default=None, help="Optional coverage_ledger.md path")
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

    manifest = _load_json(manifest_path)
    raw_meta = _raw_scope_bearing(Path(args.raw_decompose) if args.raw_decompose else None)

    ledger = audit(decompose, trade_reads, manifest, args.set_id, raw_meta)

    with Path(args.out).open("w", encoding="utf-8") as fh:
        json.dump(ledger, fh, indent=2)

    s = ledger["summary"]
    sc = ledger["sheetCoverage"]
    ic = ledger["itemCoverage"]
    print(
        f"[{'ok' if ledger['complete'] else 'FLAG'}] coverage: "
        f"{sc['totalSheets']} sheets ({sc['covered']} covered, {sc['thinCoverage']} thin, "
        f"{sc['zeroTrade']} zero-trade, {sc['unread']} unread, "
        f"{sc['nonScopeBearing']} non-scope-bearing) | "
        f"items {ic['claimed']}/{ic['totalItems']} claimed, {ic['unowned']} unowned | "
        f"red {s['red']}  amber {s['amber']}"
    )
    for f in ledger["flags"]:
        tag = "RED" if f["level"] == "red" else "amber"
        label = f.get("sheetNo") or f.get("sheetId")
        print(f"     [{tag}] {f['scope']} {label}: {f['message']}", file=sys.stderr)

    if args.md:
        with Path(args.md).open("w", encoding="utf-8") as fh:
            fh.write(render_md(ledger))
        print(f"     ledger -> {args.out}  |  md -> {args.md}")
    else:
        print(f"     ledger -> {args.out}")


if __name__ == "__main__":
    main()
