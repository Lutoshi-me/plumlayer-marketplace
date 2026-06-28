"""
fetch_schedule_roster.py -- write the schedule roster JSONL for schedule_inventory.py.

Reads the sheetType='schedule' claims from the cloud project and writes one
ScheduleEntry per line (subject, page_idx, source_instrument) to the output file.

Entries with agent-vision-crop source instruments (no numeric page ref) are
written with page_idx=-1 and flagged -- they need the appearsOnPage claim to
resolve the actual page index.

Usage:
  python fetch_schedule_roster.py \\
    --search-result path/to/search_result.json \\  (pre-fetched from MCP search verb)
    --out path/to/schedule_roster.jsonl

Or import parse_roster_from_search() directly if calling from another script.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path


def parse_roster_from_search(search_result: dict) -> list[dict]:
    """Parse a MCP search response dict into roster entries.

    Returns list of dicts: {subject, page_idx, source_instrument}.
    page_idx is -1 for entries without a numeric page reference.
    """
    entries: list[dict] = []
    seen: set[str] = set()

    for claim in search_result.get("claims", []):
        subj = claim.get("subject", "")
        if not subj or subj in seen:
            continue
        seen.add(subj)

        src = claim.get("sourceInstrument", "")
        m = re.search(r"/(\d+)$", src)
        page_idx = int(m.group(1)) if m else -1

        entries.append({
            "subject": subj,
            "page_idx": page_idx,
            "source_instrument": src,
        })

    return sorted(entries, key=lambda e: e["page_idx"])


def main() -> None:
    ap = argparse.ArgumentParser(
        description="Convert a sheetType:schedule MCP search result to roster JSONL.")
    ap.add_argument("--search-result", required=True,
                    help="JSON file containing the MCP search response.")
    ap.add_argument("--out", required=True,
                    help="Output JSONL file (one entry per line).")
    args = ap.parse_args()

    with open(args.search_result, encoding="utf-8") as fh:
        search_result = json.load(fh)

    entries = parse_roster_from_search(search_result)

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8") as fh:
        for e in entries:
            fh.write(json.dumps(e) + "\n")

    no_page = [e for e in entries if e["page_idx"] < 0]
    print(f"[ok] {len(entries)} schedule entries -> {args.out}")
    if no_page:
        print(f"[warn] {len(no_page)} entries have no numeric page ref "
              f"(agent-vision-crop source): {[e['subject'] for e in no_page]}")


if __name__ == "__main__":
    main()
