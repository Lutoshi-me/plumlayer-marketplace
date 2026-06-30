"""
select_cluster.py — select sheets from the Arch PDF that match a trade cluster.

PLU-323 guard: superseded route-first tool retained for PLU-274 history/migration only.

Doctrine role (agents read and judge; deterministic tooling grounds; nothing governs unverified):
  * Deterministic grounding tool — resolves sheetId→(pageNum, sheetNo, title)
    from the sheet inventory, then matches title keywords.
  * No semantic inference: keyword matching is exact case-insensitive substring.
  * Coverage is honest: prints N/total and the matched set; never silently truncates.

Usage:
  python select_cluster.py \\
    --pdf <arch.pdf> \\
    --cluster-config <cluster.json> \\
    [--inventory-jsonl <path>] \\
    --out selected_sheets.json

If --inventory-jsonl is not given, runs sheet_inventory.py via subprocess to
produce one on the fly and writes it to output/sheet_inventory_claims.jsonl.
"""

import argparse
import json
import subprocess
import sys
from pathlib import Path


# ---------------------------------------------------------------------------
# Inventory loading
# ---------------------------------------------------------------------------

def _load_inventory_from_jsonl(jsonl_path: Path, set_id: str) -> dict[str, dict]:
    """
    Read sheet_inventory_claims.jsonl and return a map of
    sheetNo -> {pageNum, sheetNo, title}.  Only 'appearsOnPage' and 'hasTitle'
    predicates are consumed; 'hasTitle' fills the title field.

    set_id is the per-set identifier (e.g. "PROJECT-DD") used to build the
    sheetId that downstream tools (packet, citations) key on. It is NEVER
    hardcoded — every set names its own. The reliable join key is the page
    number; sheetNo / title are best-effort labels from the inventory.
    """
    sheets: dict[str, dict] = {}
    with jsonl_path.open("r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            claim = json.loads(line)
            subject = claim.get("subject", "")
            if not subject.startswith("sheet:"):
                continue
            sheet_no = subject[len("sheet:"):]
            predicate = claim.get("predicate")
            if predicate == "appearsOnPage":
                entry = sheets.setdefault(sheet_no, {"sheetNo": sheet_no, "pageNum": None, "title": None})
                entry["pageNum"] = int(claim["value"])
            elif predicate == "hasTitle":
                entry = sheets.setdefault(sheet_no, {"sheetNo": sheet_no, "pageNum": None, "title": None})
                if entry["title"] is None:
                    entry["title"] = str(claim["value"])
    # Build the sheetId the packet / anchor store keys on: "<set_id>-p<NNN>"
    # (page zero-padded to 3 digits), e.g. "PROJECT-DD-p093". The set_id is the
    # per-set parameter — no project is named here.
    result: dict[str, dict] = {}
    for sheet_no, entry in sheets.items():
        page = entry["pageNum"]
        sheet_id = f"{set_id}-p{page:03d}" if page is not None else None
        result[sheet_no] = {
            "sheetId": sheet_id,
            "sheetNo": sheet_no,
            "pageNum": page,
            "title": entry["title"],
        }
    return result


def _run_sheet_inventory(pdf_path: Path, out_jsonl: Path) -> None:
    """Run sheet_inventory.py from the plugin's ingestion bundle via subprocess
    to produce a claims JSONL."""
    # The ingestion script is bundled in the plugin at scope-harness/ingestion/
    inventory_script = (
        Path(__file__).parent.parent / "ingestion" / "sheet_inventory.py"
    )
    if not inventory_script.exists():
        print(
            f"[error] sheet_inventory.py not found at {inventory_script}",
            file=sys.stderr,
        )
        sys.exit(1)
    env_override = {"INGEST_PDF": str(pdf_path)}
    import os
    env = {**os.environ, **env_override}
    out_jsonl.parent.mkdir(parents=True, exist_ok=True)
    result = subprocess.run(
        [sys.executable, str(inventory_script)],
        env=env,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        print("[error] sheet_inventory.py failed:", file=sys.stderr)
        print(result.stderr, file=sys.stderr)
        sys.exit(1)
    # The script writes to ./output/ relative to its own location; copy/link path:
    default_out = inventory_script.parent / "output" / "sheet_inventory_claims.jsonl"
    if default_out.exists() and default_out != out_jsonl:
        import shutil
        out_jsonl.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(default_out, out_jsonl)


# ---------------------------------------------------------------------------
# Sheet selection
# ---------------------------------------------------------------------------

def select_sheets(
    inventory: dict[str, dict],
    keywords: list[str],
) -> list[dict]:
    """
    Return inventory entries selected for the cluster.

    Whole-set mode: an empty keyword list selects EVERY inventoried sheet
    (matchedKeyword="*") — this is the v0.1 default, since per-trade fan-out
    reads the whole set, not a single keyword cluster.

    Cluster mode: a non-empty keyword list returns entries whose title matches
    any keyword (case-insensitive substring); entries with no title are skipped.
    """
    if not keywords:
        return [
            {**entry, "matchedKeyword": "*"}
            for _, entry in sorted(inventory.items())
        ]
    matched = []
    keywords_upper = [k.upper() for k in keywords]
    for sheet_no, entry in sorted(inventory.items()):
        title = entry.get("title") or ""
        title_upper = title.upper()
        for kw in keywords_upper:
            if kw in title_upper:
                matched.append({**entry, "matchedKeyword": kw})
                break
    return matched


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Select sheets matching a trade cluster's title keywords."
    )
    parser.add_argument("--pdf", required=True, help="Path to the drawing PDF")
    parser.add_argument(
        "--set-id",
        required=True,
        help="Per-set identifier used to build sheetIds, e.g. PROJECT-DD (never hardcoded)",
    )
    parser.add_argument(
        "--cluster-config", required=True, help="Path to cluster JSON config"
    )
    parser.add_argument(
        "--inventory-jsonl",
        default=None,
        help="Path to pre-built sheet_inventory_claims.jsonl; if absent, runs sheet_inventory.py",
    )
    parser.add_argument(
        "--out", required=True, help="Output path for selected_sheets.json"
    )
    args = parser.parse_args()

    pdf_path = Path(args.pdf)
    if not pdf_path.exists():
        print(f"[error] PDF not found: {pdf_path}", file=sys.stderr)
        sys.exit(1)

    cluster_path = Path(args.cluster_config)
    if not cluster_path.exists():
        print(f"[error] cluster config not found: {cluster_path}", file=sys.stderr)
        sys.exit(1)

    with cluster_path.open("r", encoding="utf-8") as fh:
        cluster = json.load(fh)

    cluster_name = cluster["clusterName"]
    trades = cluster["trades"]
    # titleKeywords may be empty/absent → whole-set mode (v0.1 fan-out default).
    keywords = cluster.get("titleKeywords") or []

    # --- resolve inventory ---
    if args.inventory_jsonl:
        inv_path = Path(args.inventory_jsonl)
        if not inv_path.exists():
            print(f"[error] inventory JSONL not found: {inv_path}", file=sys.stderr)
            sys.exit(1)
    else:
        inv_path = (
            Path(__file__).parent.parent / "ingestion" / "output"
            / "sheet_inventory_claims.jsonl"
        )
        if not inv_path.exists():
            print(
                "[info] no inventory JSONL found — running sheet_inventory.py (this may take a minute)...",
                file=sys.stderr,
            )
            _run_sheet_inventory(pdf_path, inv_path)
        else:
            # Offender guard: the default cache is reused AS-IS — it is NOT rebuilt for this --pdf.
            # A cache left over from a different set would silently mis-select. Make the reuse loud.
            print(
                f"[warn] REUSING cached inventory {inv_path} — not rebuilt for this --pdf "
                f"(run set-id {args.set_id!r}). If this cache is from a different set, delete it or "
                f"pass --inventory-jsonl built for THIS set.",
                file=sys.stderr,
            )

    inventory = _load_inventory_from_jsonl(inv_path, args.set_id)
    total = len(inventory)

    # --- selection (whole-set when keywords empty, else keyword cluster) ---
    selected = select_sheets(inventory, keywords)

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    result = {
        "clusterName": cluster_name,
        "trades": trades,
        "selectedSheets": selected,
    }
    with out_path.open("w", encoding="utf-8") as fh:
        json.dump(result, fh, indent=2)

    print(f"[ok] selected {len(selected)}/{total}")
    for s in selected:
        title_str = s.get("title") or "(no title)"
        print(f"  p{s['pageNum']:03d}  {s['sheetNo']:<12}  {title_str}  [{s['matchedKeyword']}]")


if __name__ == "__main__":
    main()
