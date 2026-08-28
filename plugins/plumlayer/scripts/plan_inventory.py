"""
plan_inventory.py: turn a fetched sheet grid into plan counts, and the record into a read plan.

The scope run's lead plans the read without ever holding a sheet row. It takes the set's shape from
a summary-only `set_grid` call, sends one agent to put the grid on disk, and then runs this script:
once to turn the grid files into counts it can read, and once per window to write that window's
read plan off the record's own copies on disk.

The script copies field values, counts them, and refuses. It never infers a discipline, never
guesses a page number, and never reads meaning off a title: which sheets a trade reads comes from
the shipped trade-knowledge/trade-sheets.json map, which schedules reach a trade comes from that
map's definition kinds, and what a trade's codes were located on comes from the citation index. A
kind, a package or a code this script cannot place is named in the output, never assigned.

Two subcommands:

  inventory  reads the grid files, refuses unless the rows total the count the lead read for
             itself, and writes `inventory.md` (one line per sheet, then the count tables and the
             sheet number digest at the tail) and `inventory.json` (the normalized rows).

  plan       reads `inventory.json` plus the window's inputs and writes `read-plan.md` whole: the
             window's passes, the unit lines with their page references, what each pass reads for
             and which trade files it carries, what is deliberately left out, what nothing reads,
             and the totals.

The three windows, and what each selects:

  1  the vocabulary: every sheet whose type is schedule, legend, notes or cover-index, plus what
     `--include` names and minus what `--exclude` names, grouped into passes by discipline.
  2  one pass per package in `--packages`, reading for that package's trade: the sheets that
     trade's families name, the sheets that define a kind the trade claims, and the sheets the
     index located that trade's codes on.
  3  the leftover: every sheet no window 2 pass reads, grouped by discipline, each carrying a count
     of the entries the index left open on it. It recomputes window 2's selection from the same
     inputs rather than parsing window 2's plan file, so it needs the same inputs window 2 needs.

Usage:

    python plan_inventory.py inventory --grid <dir or file> --expect-count 209 --out-dir <dir>

    python plan_inventory.py plan --window 1 --inventory <path> --packages <path>
        --trade-knowledge <dir> [--include <pattern>:<reason>] [--exclude <pattern>:<reason>]
        --out <path>

    python plan_inventory.py plan --window 2 --inventory <path> --packages <path>
        --kinds <path> --index <dir> --trade-knowledge <dir> --out <path>

    python plan_inventory.py plan --window 3 --inventory <path> --packages <path>
        --kinds <path> --index <dir> --trade-knowledge <dir> --out <path>

Input shapes, named here so a change on the record's side surfaces as a named field rather than as
an empty plan:

  --packages  a `solicitation_list_packages` response: a `packages` array whose rows carry
              `tradeCode`, and optionally `name` and `codes`.
  --kinds     a `list_definitions` response or an array of its rows: each row carries `kind`, and
              carries `sheetNumber` where the record knows which sheet defines it.
  --index     a directory of `index_citations_status` pages: each page carries `openEntries`
              (rows with `sheetNumber`), or `locations` (rows with `kind` and `sheetNumber`), or
              both. A page carrying neither is a refusal. Where no page carries `locations` at all,
              that input did not run, and the bounds line says so rather than reporting a clean
              number.

Exit codes:
  0  wrote the files; one bounds line on stdout naming what it read and what it wrote.
  1  a named failure, one line on stderr: a file that does not parse, a row total that does not
     match `--expect-count`, a missing window input, an input row with no `tradeCode` or no `kind`,
     an index page carrying neither array, an `--include` or `--exclude` with no colon or matching
     no sheet, a trade map that fails its own shape checks, or an inventory file this script did
     not write.
  2  argparse rejected the invocation.

Grounding role: reads files and copies byte values. A file that does not parse whole is a refusal,
not a salvage: a partial recovery of a grounded read is worse than no read at all.
"""

from __future__ import annotations

import argparse
import fnmatch
import json
import math
import os
import string
import sys
from pathlib import Path

# The six grid fields the plan needs. A grid row carries about thirty; the rest are dropped here so
# nothing downstream can quietly come to depend on a field the plan never reasoned about.
ROW_FIELDS = ("discipline", "sheetNumber", "pageTitle", "sheetType", "fileId", "pageInPdf")

# The `scope-round-runner` stops a pass above twelve units, so a plan that emits a bigger pass is a
# plan defect rather than a big pass.
UNITS_PER_PASS = 12
# The cut script carries at most ten trade files into one pass knowledge file.
MAX_TRADE_FILES_WINDOW_1 = 10
# A window 2 pass reads for exactly one trade, with that trade's knowledge alone.
MAX_TRADE_FILES_WINDOW_2 = 1

PREFIX_GROUP_CAP = 60
TITLES_PER_PREFIX = 3
MAX_NAMED = 5

NO_DISCIPLINE = "(none)"
UNTYPED = "(untyped)"

# Window 1 reads what the set says its own marks mean. These four are single recognizer types, so
# the list is exact rather than a family of near names.
VOCABULARY_SHEET_TYPES = ("schedule", "legend", "notes", "cover-index")

TRADE_SHEETS_FILE = "trade-sheets.json"

TRADE_SHEETS_KEYS = {"note", "sheetTypes", "unmapped", "trades", "seams"}
TRADE_ENTRY_KEYS = {"knowledge", "families", "definitionKinds", "note"}
FAMILY_KEYS = {"discipline", "sheetTypes", "patterns"}
SELECT_KEYS = {"discipline", "sheetTypes", "patterns"}


class PlanError(Exception):
    """A named failure with a one-line reason, reported on stderr and exiting 1."""


# --------------------------------------------------------------------------- #
# Shared helpers
# --------------------------------------------------------------------------- #

def _read_json(path: Path, what: str):
    """
    Parse the whole file or refuse. There is deliberately no scan for an embedded object and no
    line-by-line salvage: a grid file that is half readable is a truncated grounded read, and the
    only safe thing to do with one is stop.
    """
    try:
        text = path.read_text(encoding="utf-8")
    except Exception as e:
        raise PlanError(f"cannot read {what} at {path}: {e}") from e
    try:
        return json.loads(text)
    except json.JSONDecodeError as e:
        raise PlanError(f"{path} is not whole JSON: {e}") from e


def _write_atomically(out: Path, payload: bytes) -> None:
    """Write beside the target and rename, so a run that dies mid-write leaves no partial file."""
    try:
        out.parent.mkdir(parents=True, exist_ok=True)
        tmp = out.with_name(out.name + ".tmp")
        tmp.write_bytes(payload)
        os.replace(tmp, out)
    except Exception as e:
        raise PlanError(f"cannot write {out}: {e}") from e


def _named(items: list[str]) -> str:
    """The first few offenders plus a count, so a refusal stays one line however many there are."""
    if len(items) <= MAX_NAMED:
        return "; ".join(items)
    return "; ".join(items[:MAX_NAMED]) + f"; and {len(items) - MAX_NAMED} more"


def _text(value) -> str:
    return "" if value is None else str(value)


def _fold(code: str) -> str:
    """
    A catalog id with its spaces removed, lower cased. The catalog spaces its ids and a caller may
    not, and this is the same fold the record's own catalog lookup uses, so the two agree.
    """
    return "".join(code.split()).lower()


# --------------------------------------------------------------------------- #
# inventory
# --------------------------------------------------------------------------- #

def _grid_files(grid: Path) -> list[Path]:
    if grid.is_file():
        return [grid]
    if grid.is_dir():
        files = sorted(p for p in grid.iterdir() if p.is_file())
        if not files:
            raise PlanError(f"no grid files in {grid}")
        return files
    raise PlanError(f"no grid file or directory at {grid}")


def _read_grid_pages(files: list[Path]) -> list[tuple[Path, list, int | None, dict | None]]:
    pages: list[tuple[Path, list, int | None, dict | None]] = []
    for path in files:
        obj = _read_json(path, "a grid file")
        if isinstance(obj, list):
            pages.append((path, obj, None, None))
            continue
        if not isinstance(obj, dict):
            raise PlanError(f"{path} is neither a grid response object nor an array of rows")
        rows = obj.get("sheets")
        if not isinstance(rows, list):
            raise PlanError(f"{path} is a grid response with no `sheets` array")
        offset = obj.get("offset") if isinstance(obj.get("offset"), int) else None
        reported = obj.get("disciplineCounts")
        pages.append((path, rows, offset, reported if isinstance(reported, dict) else None))
    return pages


def _order_pages(pages: list) -> tuple[list, str]:
    """
    Grid order is the order the rows are read in, so the pages are put back in the order the grid
    handed them out: by the `offset` each response carries where every page has one, and by file
    name otherwise.
    """
    if pages and all(p[2] is not None for p in pages):
        return sorted(pages, key=lambda p: p[2]), "the `offset` each grid response carries"
    return sorted(pages, key=lambda p: p[0].name), "grid file name, since not every page carried an `offset`"


def _normalize_rows(pages: list) -> tuple[list[dict], list[str]]:
    seen: set[tuple[str, str, str]] = set()
    rows: list[dict] = []
    duplicates: list[str] = []
    for path, page_rows, _offset, _reported in pages:
        for raw in page_rows:
            if not isinstance(raw, dict):
                raise PlanError(f"{path} carries a row that is not an object")
            row = {field: raw.get(field) for field in ROW_FIELDS}
            key = (_text(row["sheetNumber"]), _text(row["fileId"]), _text(row["pageInPdf"]))
            if key in seen:
                duplicates.append(f"{_text(row['sheetNumber']) or '(no sheet number)'} in {path.name}")
                continue
            seen.add(key)
            row["unitKey"] = f"{key[0]}@{key[1]}#{key[2]}"
            rows.append(row)
    return rows, duplicates


def _placeable(row: dict) -> bool:
    return _text(row["sheetNumber"]) != "" and _text(row["pageInPdf"]) != ""


def _stem(sheet_number: str) -> str:
    """
    The literal string before the last dot group, with nothing read into it. A sheet number with no
    dot in it is its own stem, which is why the digest names the disciplines where that produced one
    group per sheet rather than letting the lead read structure into a list that has none.
    """
    return sheet_number.rsplit(".", 1)[0] if "." in sheet_number else sheet_number


def _ordered_counts(rows: list[dict]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for row in rows:
        key = _text(row["discipline"]) or NO_DISCIPLINE
        counts[key] = counts.get(key, 0) + 1
    return counts


def _cross_tab(rows: list[dict]) -> tuple[dict[str, dict[str, int]], list[str]]:
    table: dict[str, dict[str, int]] = {}
    types: list[str] = []
    for row in rows:
        discipline = _text(row["discipline"]) or NO_DISCIPLINE
        sheet_type = _text(row["sheetType"]) or UNTYPED
        if sheet_type not in types:
            types.append(sheet_type)
        table.setdefault(discipline, {})
        table[discipline][sheet_type] = table[discipline].get(sheet_type, 0) + 1
    return table, types


def _prefix_digest(rows: list[dict]) -> tuple[list[dict], bool, list[str]]:
    """
    Per discipline, the distinct sheet number stems with their counts and a few verbatim titles.
    This is a projection, not a summary: it decides nothing and paraphrases nothing.
    """
    groups: dict[tuple[str, str], dict] = {}
    for row in rows:
        discipline = _text(row["discipline"]) or NO_DISCIPLINE
        number = _text(row["sheetNumber"])
        key = (discipline, _stem(number))
        group = groups.setdefault(key, {"discipline": discipline, "stem": key[1], "count": 0, "titles": []})
        group["count"] += 1
        title = _text(row["pageTitle"])
        if title and title not in group["titles"] and len(group["titles"]) < TITLES_PER_PREFIX:
            group["titles"].append(title)

    ordered = list(groups.values())
    capped = len(ordered) > PREFIX_GROUP_CAP

    per_discipline_rows = _ordered_counts(rows)
    per_discipline_groups: dict[str, int] = {}
    for group in ordered:
        per_discipline_groups[group["discipline"]] = per_discipline_groups.get(group["discipline"], 0) + 1
    # A discipline whose stems number one per sheet carries no stem structure to group on. Named so
    # the lead reads that plainly instead of reading structure into a list that has none. A
    # single-sheet discipline is not evidence of that either way, so it is left out.
    ungrouped = [
        d for d, n in per_discipline_groups.items()
        if n == per_discipline_rows.get(d) and per_discipline_rows.get(d, 0) > 1
    ]

    return ordered[:PREFIX_GROUP_CAP], capped, ungrouped


def _inventory_markdown(
    rows: list[dict],
    unplaceable: list[dict],
    order_rule: str,
    reported: dict[str, list[int]],
    digest: list[dict],
    capped: bool,
    ungrouped: list[str],
) -> str:
    counts = _ordered_counts(rows)
    table, types = _cross_tab(rows)
    lines: list[str] = []

    lines.append("# Plan inventory")
    lines.append("")
    lines.append("Written by scripts/plan_inventory.py off the grid files the fetch put on disk.")
    lines.append(f"Rows are in grid order, ordered across pages by {order_rule}.")
    lines.append("The count tables and the sheet number digest are at the tail of this file.")
    lines.append("")
    lines.append("## Sheets")
    lines.append("")
    lines.append("discipline | sheet number | title | sheet type | file | page")
    lines.append("")
    for row in rows:
        lines.append(
            " | ".join(
                [
                    _text(row["discipline"]) or NO_DISCIPLINE,
                    _text(row["sheetNumber"]),
                    _text(row["pageTitle"]),
                    _text(row["sheetType"]) or UNTYPED,
                    _text(row["fileId"]),
                    _text(row["pageInPdf"]),
                ]
            )
        )

    if unplaceable:
        lines.append("")
        lines.append("## Rows the grid could not place")
        lines.append("")
        lines.append("A row with no sheet number or no page number. Named here rather than guessed at,")
        lines.append("and left out of the tables and out of inventory.json's sheet list.")
        lines.append("")
        for row in unplaceable:
            lines.append(
                " | ".join(
                    [
                        _text(row["discipline"]) or NO_DISCIPLINE,
                        _text(row["sheetNumber"]) or "(no sheet number)",
                        _text(row["pageTitle"]),
                        _text(row["fileId"]),
                        _text(row["pageInPdf"]) or "(no page)",
                    ]
                )
            )

    lines.append("")
    lines.append("## Sheets by discipline")
    lines.append("")
    lines.append("discipline | rows | reported by the grid")
    for discipline, n in counts.items():
        said = reported.get(discipline)
        said_text = "not reported" if not said else " / ".join(str(v) for v in said)
        lines.append(f"{discipline} | {n} | {said_text}")
    lines.append(f"total | {len(rows)} |")
    lines.append("")
    lines.append("Where the two columns differ, both are shown. Nothing here reconciles them.")

    lines.append("")
    lines.append("## Sheets by discipline and sheet type")
    lines.append("")
    lines.append("discipline | " + " | ".join(types))
    for discipline in counts:
        row_counts = table.get(discipline, {})
        lines.append(discipline + " | " + " | ".join(str(row_counts.get(t, 0)) for t in types))

    lines.append("")
    lines.append("## Sheet number digest")
    lines.append("")
    lines.append("Per discipline, the distinct sheet number stems: the literal string before the last")
    lines.append("dot group, with nothing read into it. A sheet number carrying no dot is its own stem.")
    lines.append(f"Titles are verbatim, at most {TITLES_PER_PREFIX} per stem.")
    if capped:
        lines.append(f"Capped at {PREFIX_GROUP_CAP} stems; the set has more, and the rest are not shown here.")
    else:
        lines.append(f"Cap is {PREFIX_GROUP_CAP} stems and this set did not reach it.")
    if ungrouped:
        lines.append(
            "One stem per sheet, so the numbering carries no stem structure to group on, in: "
            + ", ".join(ungrouped)
        )
    lines.append("")
    for group in digest:
        titles = "; ".join(group["titles"]) if group["titles"] else "(no titles)"
        lines.append(f"{group['discipline']} | {group['stem']} | {group['count']} | {titles}")

    return "\n".join(lines) + "\n"


def inventory(grid: Path, expect_count: int, out_dir: Path) -> str:
    files = _grid_files(grid)
    pages, order_rule = _order_pages(_read_grid_pages(files))
    rows, duplicates = _normalize_rows(pages)

    if len(rows) != expect_count:
        raise PlanError(
            f"the grid on disk holds {len(rows):,} rows after dedupe and --expect-count says "
            f"{expect_count:,}; nothing written. The fetch dropped a page, truncated one, or "
            f"copied a stale file"
        )

    placeable = [r for r in rows if _placeable(r)]
    unplaceable = [r for r in rows if not _placeable(r)]

    reported: dict[str, list[int]] = {}
    for _path, _rows, _offset, page_reported in pages:
        if not page_reported:
            continue
        for key, value in page_reported.items():
            if not isinstance(value, int):
                continue
            seen = reported.setdefault(str(key), [])
            if value not in seen:
                seen.append(value)

    digest, capped, ungrouped = _prefix_digest(placeable)

    md_path = out_dir / "inventory.md"
    json_path = out_dir / "inventory.json"

    md = _inventory_markdown(placeable, unplaceable, order_rule, reported, digest, capped, ungrouped)
    counts = _ordered_counts(placeable)
    table, _types = _cross_tab(placeable)
    untyped = sum(1 for r in placeable if not _text(r["sheetType"]))

    payload = {
        "expectCount": expect_count,
        "gridFiles": [p.name for p in files],
        "gridOrder": order_rule,
        "counts": {
            "rows": len(rows),
            "sheets": len(placeable),
            "duplicates": len(duplicates),
            "unplaceable": len(unplaceable),
            "untyped": untyped,
            "byDiscipline": counts,
            "reportedByDiscipline": reported,
            "byDisciplineAndSheetType": table,
        },
        "sheets": [
            {
                "unitKey": r["unitKey"],
                "discipline": _text(r["discipline"]) or None,
                "sheetNumber": _text(r["sheetNumber"]),
                "pageTitle": _text(r["pageTitle"]) or None,
                "sheetType": _text(r["sheetType"]) or None,
                "fileId": _text(r["fileId"]) or None,
                "pageInPdf": r["pageInPdf"],
            }
            for r in placeable
        ],
        "unplaceable": [
            {field: r[field] for field in ROW_FIELDS} for r in unplaceable
        ],
    }

    md_bytes = md.encode("utf-8")
    json_bytes = (json.dumps(payload, indent=2) + "\n").encode("utf-8")
    _write_atomically(md_path, md_bytes)
    _write_atomically(json_path, json_bytes)

    cap_text = f"cap {PREFIX_GROUP_CAP} reached" if capped else f"cap {PREFIX_GROUP_CAP} not reached"
    duplicate_text = f"{len(duplicates)} duplicates" + (f" ({_named(duplicates)})" if duplicates else "")
    return (
        f"wrote {md_path} and {json_path}: {len(rows):,} rows from {len(files)} grid "
        f"file{'' if len(files) == 1 else 's'}, {duplicate_text}, {len(unplaceable)} rows the grid "
        f"could not place, {len(counts)} disciplines, {len(digest)} sheet number stems "
        f"({cap_text}), {untyped} untyped, {len(md_bytes) + len(json_bytes):,} bytes written"
    )


# --------------------------------------------------------------------------- #
# The trade to sheet family map
# --------------------------------------------------------------------------- #

def _require_keys(obj, allowed: set[str], where: str) -> None:
    if not isinstance(obj, dict):
        raise PlanError(f"{where} is not an object")
    unknown = sorted(set(obj) - allowed)
    if unknown:
        raise PlanError(f"{where} carries unknown key(s): {', '.join(unknown)}")


def _string_list(value, where: str) -> list[str]:
    if not isinstance(value, list) or not value or not all(isinstance(v, str) for v in value):
        raise PlanError(f"{where} is not a non-empty list of strings")
    return value


def _load_trade_sheets(trade_knowledge: Path) -> dict:
    """
    The shipped trade to sheet family map, validated whole before any selection runs. A typo in a
    sheet type refuses here rather than selecting nothing later, which is why the file pins the
    recognizer's own sheet type list at its top and every family is checked against it.
    """
    path = trade_knowledge / TRADE_SHEETS_FILE
    data = _read_json(path, "the trade to sheet family map")
    _require_keys(data, TRADE_SHEETS_KEYS, f"{path.name}")

    types = _string_list(data.get("sheetTypes"), f"{path.name}: `sheetTypes`")
    known_types = set(types)

    trades = data.get("trades")
    if not isinstance(trades, dict) or not trades:
        raise PlanError(f"{path.name} carries no `trades` object")

    folded: dict[str, str] = {}
    for trade_id, entry in trades.items():
        where = f"{path.name}: trade {trade_id}"
        _require_keys(entry, TRADE_ENTRY_KEYS, where)
        knowledge = entry.get("knowledge")
        if not isinstance(knowledge, str) or not knowledge:
            raise PlanError(f"{where}: `knowledge` is not a non-empty string")
        families = entry.get("families")
        if not isinstance(families, list):
            raise PlanError(f"{where}: `families` is not a list")
        if not families and not entry.get("note"):
            raise PlanError(f"{where}: `families` is empty and no `note` says why")
        for index, family in enumerate(families, 1):
            fwhere = f"{where}: family {index}"
            _require_keys(family, FAMILY_KEYS, fwhere)
            if "discipline" not in family and "patterns" not in family:
                raise PlanError(f"{fwhere} names neither `discipline` nor `patterns`")
            if "discipline" in family and not isinstance(family["discipline"], str):
                raise PlanError(f"{fwhere}: `discipline` is not a string")
            if "patterns" in family:
                _string_list(family["patterns"], f"{fwhere}: `patterns`")
            for sheet_type in family.get("sheetTypes", []) or []:
                if sheet_type not in known_types:
                    raise PlanError(
                        f"{fwhere}: `sheetTypes` names {sheet_type}, which is not in "
                        f"{path.name}'s own `sheetTypes` list"
                    )
        kinds = entry.get("definitionKinds", [])
        if not isinstance(kinds, list) or not all(isinstance(k, str) for k in kinds):
            raise PlanError(f"{where}: `definitionKinds` is not a list of strings")
        key = _fold(trade_id)
        if key in folded:
            raise PlanError(f"{path.name}: trade {trade_id} and {folded[key]} fold to one id")
        folded[key] = trade_id

    seams = data.get("seams", []) or []
    if not isinstance(seams, list):
        raise PlanError(f"{path.name}: `seams` is not a list")
    for index, pair in enumerate(seams, 1):
        where = f"{path.name}: seam {index}"
        if not isinstance(pair, list) or len(pair) != 2 or not all(isinstance(p, str) for p in pair):
            raise PlanError(f"{where} is not a pair of trade ids")
        if pair[0] == pair[1]:
            raise PlanError(f"{where} names {pair[0]} twice")
        for member in pair:
            if member not in trades:
                raise PlanError(f"{where} names {member}, which is not a key of `trades`")

    unmapped = data.get("unmapped", {}) or {}
    if not isinstance(unmapped, dict):
        raise PlanError(f"{path.name}: `unmapped` is not an object")
    for slug, reason in unmapped.items():
        if not isinstance(reason, str) or not reason:
            raise PlanError(f"{path.name}: `unmapped` entry {slug} carries no reason")

    return {
        "path": path,
        "sheetTypes": types,
        "trades": trades,
        "folded": folded,
        "seams": [tuple(pair) for pair in seams],
        "unmapped": unmapped,
    }


def _trade_entry(trade_map: dict, trade_code: str) -> tuple[str, dict] | None:
    """The map entry for a catalog id, taking the id verbatim or space stripped and lower cased."""
    trades = trade_map["trades"]
    if trade_code in trades:
        return trade_code, trades[trade_code]
    trade_id = trade_map["folded"].get(_fold(trade_code))
    if trade_id is None:
        return None
    return trade_id, trades[trade_id]


# --------------------------------------------------------------------------- #
# Selection
# --------------------------------------------------------------------------- #

def _select(rows: list[dict], spec: dict) -> list[dict]:
    """
    The one selection primitive the windows share: a discipline, a set of sheet number patterns, or
    both, narrowed by sheet type. Every named criterion must hold, so a spec naming a discipline and
    a sheet type selects that discipline's sheets of that type and nothing else. Returns the matching
    rows in inventory order. A spec that matches nothing returns an empty list; whether that is a
    refusal is the caller's judgment, since a shipped family naming no sheet in this set is ordinary
    and a lead's own pattern naming no sheet is a typo.
    """
    _require_keys(spec, SELECT_KEYS, "a selection")
    discipline = spec.get("discipline")
    patterns = spec.get("patterns")
    sheet_types = spec.get("sheetTypes")

    picked: list[dict] = []
    for row in rows:
        if discipline is not None and _text(row.get("discipline")) != discipline:
            continue
        if sheet_types is not None and _text(row.get("sheetType")) not in sheet_types:
            continue
        if patterns is not None and not any(
            fnmatch.fnmatchcase(_text(row.get("sheetNumber")), p) for p in patterns
        ):
            continue
        picked.append(row)
    return picked


def _family_sheets(rows: list[dict], entry: dict) -> list[dict]:
    """Every sheet any of the trade's families names, once each, in inventory order."""
    chosen: set[str] = set()
    for family in entry.get("families", []) or []:
        chosen.update(r["unitKey"] for r in _select(rows, family))
    return [r for r in rows if r["unitKey"] in chosen]


# --------------------------------------------------------------------------- #
# The window inputs
# --------------------------------------------------------------------------- #

def _read_packages(path: Path) -> list[dict]:
    """
    The `solicitation_list_packages` response, byte copied to disk. Every package row must carry a
    `tradeCode`: a package with no trade is a package this script cannot plan a read for, and
    guessing one from its name would be reading meaning off a title.
    """
    data = _read_json(path, "the packages file")
    rows = data.get("packages") if isinstance(data, dict) else data
    if not isinstance(rows, list):
        raise PlanError(f"{path} carries no `packages` array")
    packages: list[dict] = []
    for index, row in enumerate(rows, 1):
        if not isinstance(row, dict):
            raise PlanError(f"{path}: package {index} is not an object")
        trade_code = row.get("tradeCode")
        if not isinstance(trade_code, str) or not trade_code.strip():
            raise PlanError(f"{path}: package {index} carries no `tradeCode`")
        packages.append(row)
    if not packages:
        raise PlanError(f"{path} carries no packages")
    return packages


def _read_kinds(path: Path) -> tuple[list[dict], int]:
    """
    The record's definition kinds, byte copied to disk. Every row must carry a `kind`; a row that
    carries one and no `sheetNumber` names no defining sheet, which is counted and reported rather
    than guessed at.
    """
    data = _read_json(path, "the definition kinds file")
    if isinstance(data, dict):
        rows = data.get("kinds")
        if rows is None:
            rows = data.get("definitions")
    else:
        rows = data
    if not isinstance(rows, list):
        raise PlanError(f"{path} carries no `kinds` array")
    kinds: list[dict] = []
    without_sheet = 0
    for index, row in enumerate(rows, 1):
        if not isinstance(row, dict):
            raise PlanError(f"{path}: row {index} is not an object")
        kind = row.get("kind")
        if not isinstance(kind, str) or not kind.strip():
            raise PlanError(f"{path}: row {index} carries no `kind`")
        if not _text(row.get("sheetNumber")):
            without_sheet += 1
        kinds.append(row)
    return kinds, without_sheet


def _read_index(index_dir: Path) -> dict:
    """
    What the citation index left open, and where it located each code, byte copied to disk one page
    per file. A page carrying neither array is a refusal naming both fields tried, so a shape change
    on the record's side surfaces here rather than as an empty leftover window.
    """
    if not index_dir.is_dir():
        raise PlanError(f"no index directory at {index_dir}")
    files = sorted(p for p in index_dir.iterdir() if p.is_file())
    if not files:
        raise PlanError(f"no index pages in {index_dir}")

    open_by_sheet: dict[str, int] = {}
    open_total = 0
    open_without_sheet = 0
    locations: list[dict] = []
    locations_seen = False

    for path in files:
        page = _read_json(path, "an index page")
        if not isinstance(page, dict):
            raise PlanError(f"{path} is not an index page object")
        entries = page.get("openEntries")
        located = page.get("locations")
        if entries is None and located is None:
            raise PlanError(
                f"{path} carries neither an `openEntries` array nor a `locations` array"
            )
        if entries is not None:
            if not isinstance(entries, list):
                raise PlanError(f"{path}: `openEntries` is not an array")
            for row in entries:
                if not isinstance(row, dict):
                    raise PlanError(f"{path}: an `openEntries` row is not an object")
                open_total += 1
                sheet = _text(row.get("sheetNumber"))
                if not sheet:
                    open_without_sheet += 1
                    continue
                open_by_sheet[sheet] = open_by_sheet.get(sheet, 0) + 1
        if located is not None:
            locations_seen = True
            if not isinstance(located, list):
                raise PlanError(f"{path}: `locations` is not an array")
            for row in located:
                if not isinstance(row, dict):
                    raise PlanError(f"{path}: a `locations` row is not an object")
                locations.append(row)

    return {
        "openBySheet": open_by_sheet,
        "openTotal": open_total,
        "openWithoutSheet": open_without_sheet,
        "locations": locations,
        "locationsPresent": locations_seen,
        "pages": len(files),
    }


# --------------------------------------------------------------------------- #
# Passes
# --------------------------------------------------------------------------- #

def _split_pass(pass_id: str, units: list[dict]) -> list[tuple[str, list[dict]]]:
    """
    A pass over twelve units is split into parts of as even a size as possible, earlier parts taking
    the remainder. Balanced and naive chunking always give the same number of parts, so balancing
    costs nothing and keeps a runner from being started for a single unit.
    """
    n = len(units)
    if n <= UNITS_PER_PASS:
        return [(pass_id, units)]
    count = math.ceil(n / UNITS_PER_PASS)
    if count > len(string.ascii_lowercase):
        raise PlanError(f"pass {pass_id} holds {n} units, more parts than single letters to name them")
    base, extra = divmod(n, count)
    parts: list[tuple[str, list[dict]]] = []
    start = 0
    for index in range(count):
        size = base + (1 if index < extra else 0)
        parts.append((f"{pass_id}{string.ascii_lowercase[index]}", units[start:start + size]))
        start += size
    return parts


def _unit_line(number: int, row: dict, show_file: bool) -> str:
    title = _text(row["pageTitle"]) or "(no title)"
    where = f"page {row['pageInPdf']}"
    if show_file:
        # The file id only earns its place where the set spans more than one file and the page
        # number alone would not say which document to open.
        where = f"file {_text(row.get('fileId')) or '(no file)'}, " + where
    return f"{number}. {row['sheetNumber']}, {where}: {title}"


def _by_discipline(rows: list[dict]) -> list[tuple[str, list[dict]]]:
    """
    Rows grouped by discipline in inventory order. A row with no discipline is its own group, never
    merged into another: a set that could not place a sheet's discipline is not evidence that it
    belongs with any particular one.
    """
    order: list[str] = []
    groups: dict[str, list[dict]] = {}
    for row in rows:
        key = _text(row.get("discipline")) or NO_DISCIPLINE
        if key not in groups:
            groups[key] = []
            order.append(key)
        groups[key].append(row)
    return [(key, groups[key]) for key in order]


def _pass_id_for_discipline(discipline: str, window: int) -> str:
    """A discipline pass is named for its discipline and its window, so `A1` reads as A, window 1."""
    stem = "NONE" if discipline == NO_DISCIPLINE else discipline
    return f"{stem}{window}"


# --------------------------------------------------------------------------- #
# Window 1: the vocabulary
# --------------------------------------------------------------------------- #

def _split_pattern_argument(raw: str, flag: str) -> tuple[str, str]:
    """
    `<pattern>:<reason>`, split on the first colon only so a reason may carry one. Both halves are
    required: an include or exclude with no reason is a judgment with nothing recorded behind it.
    """
    pattern, sep, reason = raw.partition(":")
    if not sep or not pattern.strip() or not reason.strip():
        raise PlanError(f"{flag} {raw!r} is not `<pattern>:<reason>`")
    return pattern.strip(), reason.strip()


def _window_1(rows: list[dict], packages: list[dict], trade_map: dict, includes, excludes) -> dict:
    selected: dict[str, dict] = {
        r["unitKey"]: r for r in rows if _text(r.get("sheetType")) in VOCABULARY_SHEET_TYPES
    }

    include_blocks: list[dict] = []
    for pattern, reason in includes:
        hits = _select(rows, {"patterns": [pattern]})
        if not hits:
            raise PlanError(f"--include: no sheet number matches the pattern {pattern}")
        for row in hits:
            selected[row["unitKey"]] = row
        include_blocks.append({"pattern": pattern, "reason": reason, "sheets": hits})

    exclude_blocks: list[dict] = []
    excluded_keys: set[str] = set()
    for pattern, reason in excludes:
        hits = _select(rows, {"patterns": [pattern]})
        if not hits:
            raise PlanError(f"--exclude: no sheet number matches the pattern {pattern}")
        for row in hits:
            selected.pop(row["unitKey"], None)
            excluded_keys.add(row["unitKey"])
        exclude_blocks.append({"pattern": pattern, "reason": reason, "sheets": hits})

    chosen = [r for r in rows if r["unitKey"] in selected]

    # Only the trades this project actually bought a package for are candidates: a pass carrying a
    # trade file for a trade with no package would cut knowledge nobody is reading for.
    candidates: list[tuple[str, dict]] = []
    seen_ids: set[str] = set()
    for package in packages:
        found = _trade_entry(trade_map, package["tradeCode"])
        if found is None or found[0] in seen_ids:
            continue
        seen_ids.add(found[0])
        candidates.append(found)

    passes: list[dict] = []
    for discipline, group in _by_discipline(chosen):
        keys = {r["unitKey"] for r in group}
        scored: list[tuple[int, str, str]] = []
        for trade_id, entry in candidates:
            matched = sum(1 for r in _family_sheets(group, entry) if r["unitKey"] in keys)
            if matched:
                scored.append((matched, trade_id, entry["knowledge"]))
        scored.sort(key=lambda s: (-s[0], s[1]))
        carried = [s[2] for s in scored[:MAX_TRADE_FILES_WINDOW_1]]
        dropped = [f"{s[2]} ({s[1]})" for s in scored[MAX_TRADE_FILES_WINDOW_1:]]
        passes.append(
            {
                "id": _pass_id_for_discipline(discipline, 1),
                "name": f"Vocabulary, discipline {discipline}",
                "readsFor": "the vocabulary",
                "trades": carried,
                "dropped": dropped,
                "units": group,
            }
        )

    unassigned = [
        r for r in rows if r["unitKey"] not in selected and r["unitKey"] not in excluded_keys
    ]
    return {
        "passes": passes,
        "includes": include_blocks,
        "excludes": exclude_blocks,
        "excludedCount": len(excluded_keys),
        "unassigned": unassigned,
        "notes": [],
    }


# --------------------------------------------------------------------------- #
# Window 2: one pass per trade
# --------------------------------------------------------------------------- #

def _window_2_selection(rows: list[dict], packages: list[dict], trade_map: dict, kinds, index) -> dict:
    """
    One selection per package, in package order. Window 3 calls this too, over the same inputs, so
    the leftover is the inventory minus what this returned rather than a second reading of the same
    rule that could drift from it.
    """
    by_number: dict[str, list[dict]] = {}
    for row in rows:
        by_number.setdefault(_text(row.get("sheetNumber")), []).append(row)

    kind_sheets: dict[str, set[str]] = {}
    # Kinds are folded to compare and kept verbatim to report: the record's own spelling is what the
    # lead has to go looking for when a kind reaches no trade.
    named_kinds: dict[str, str] = {}
    for row in kinds:
        kind = row["kind"].strip().lower()
        sheet = _text(row.get("sheetNumber"))
        named_kinds.setdefault(kind, row["kind"].strip())
        for hit in by_number.get(sheet, []):
            kind_sheets.setdefault(kind, set()).add(hit["unitKey"])

    located_by_kind: dict[str, set[str]] = {}
    locations_without_field = 0
    for row in index["locations"]:
        kind = _text(row.get("kind")).strip().lower()
        sheet = _text(row.get("sheetNumber"))
        if not kind or not sheet:
            locations_without_field += 1
            continue
        for hit in by_number.get(sheet, []):
            located_by_kind.setdefault(kind, set()).add(hit["unitKey"])

    claimed_kinds: set[str] = set()
    selections: list[dict] = []
    for package in packages:
        trade_code = package["tradeCode"]
        found = _trade_entry(trade_map, trade_code)
        if found is None:
            selections.append({"tradeCode": trade_code, "package": package, "entry": None, "units": []})
            continue
        trade_id, entry = found
        keys: set[str] = {r["unitKey"] for r in _family_sheets(rows, entry)}
        for kind in entry.get("definitionKinds", []) or []:
            folded_kind = kind.strip().lower()
            claimed_kinds.add(folded_kind)
            keys |= kind_sheets.get(folded_kind, set())
            keys |= located_by_kind.get(folded_kind, set())
        selections.append(
            {
                "tradeCode": trade_code,
                "tradeId": trade_id,
                "package": package,
                "entry": entry,
                "units": [r for r in rows if r["unitKey"] in keys],
            }
        )

    return {
        "selections": selections,
        "unnamedKinds": [named_kinds[k] for k in sorted(set(named_kinds) - claimed_kinds)],
        "locationsWithoutField": locations_without_field,
    }


def _apply_seams(passes: list[dict], trade_map: dict) -> None:
    """
    Move the later trade's passes to sit immediately after the earlier trade's last pass, one seam
    pair at a time in the map's own file order, so the result is the same on every run. The moved
    pass carries the seam on its own block, which is what the lead reads to run the two one after
    another rather than alongside each other.
    """
    for first, second in trade_map["seams"]:
        first_at = [i for i, p in enumerate(passes) if p.get("tradeId") == first]
        second_at = [i for i, p in enumerate(passes) if p.get("tradeId") == second]
        if not first_at or not second_at:
            continue
        moving = [passes[i] for i in second_at]
        for plan_pass in moving:
            plan_pass["seamWith"] = first
        remaining = [p for i, p in enumerate(passes) if i not in set(second_at)]
        anchor = max(i for i, p in enumerate(remaining) if p.get("tradeId") == first)
        passes[:] = remaining[: anchor + 1] + moving + remaining[anchor + 1:]


def _window_2(rows: list[dict], packages: list[dict], trade_map: dict, kinds, index) -> dict:
    selection = _window_2_selection(rows, packages, trade_map, kinds, index)

    passes: list[dict] = []
    no_family: list[str] = []
    no_sheet: list[str] = []
    for item in selection["selections"]:
        if item["entry"] is None:
            no_family.append(item["tradeCode"])
            continue
        if not item["units"]:
            no_sheet.append(item["tradeCode"])
            continue
        knowledge = item["entry"]["knowledge"]
        passes.append(
            {
                "id": knowledge,
                "tradeId": item["tradeId"],
                # The package's own name where it has one, so the pass reads the way the user named
                # the package rather than the way the trade file is filed.
                "name": _text(item["package"].get("name")) or knowledge,
                "readsFor": item["tradeCode"],
                "trades": [knowledge][:MAX_TRADE_FILES_WINDOW_2],
                "dropped": [],
                "units": item["units"],
            }
        )
    _apply_seams(passes, trade_map)

    counted: dict[str, int] = {}
    for plan_pass in passes:
        for row in plan_pass["units"]:
            counted[row["unitKey"]] = counted.get(row["unitKey"], 0) + 1
    read_twice = sum(1 for n in counted.values() if n > 1)
    unread = [r for r in rows if r["unitKey"] not in counted]

    return {
        "passes": passes,
        "includes": [],
        "excludes": [],
        "excludedCount": 0,
        "unassigned": [],
        "noFamily": no_family,
        "noSheet": no_sheet,
        "readTwice": read_twice,
        "unread": unread,
        "unnamedKinds": selection["unnamedKinds"],
        "locationsWithoutField": selection["locationsWithoutField"],
        "notes": [],
    }


# --------------------------------------------------------------------------- #
# Window 3: the leftover
# --------------------------------------------------------------------------- #

def _window_3(rows: list[dict], packages: list[dict], trade_map: dict, kinds, index) -> dict:
    selection = _window_2_selection(rows, packages, trade_map, kinds, index)
    read_keys: set[str] = set()
    for item in selection["selections"]:
        read_keys.update(r["unitKey"] for r in item["units"])

    leftover = [r for r in rows if r["unitKey"] not in read_keys]
    open_by_sheet = index["openBySheet"]

    passes: list[dict] = []
    for discipline, group in _by_discipline(leftover):
        passes.append(
            {
                "id": _pass_id_for_discipline(discipline, 3),
                "name": f"Leftover, discipline {discipline}",
                "readsFor": "the leftover",
                "trades": [],
                "dropped": [],
                "units": group,
                "openEntries": sum(open_by_sheet.get(_text(r["sheetNumber"]), 0) for r in group),
            }
        )

    return {
        "passes": passes,
        "includes": [],
        "excludes": [],
        "excludedCount": 0,
        "unassigned": [],
        "openEntries": sum(
            open_by_sheet.get(_text(r["sheetNumber"]), 0) for r in leftover
        ),
        "leftover": leftover,
        "notes": [],
    }


# --------------------------------------------------------------------------- #
# The read plan file
# --------------------------------------------------------------------------- #

def _render(window: int, plan: dict, rows: list[dict], show_file: bool) -> tuple[str, int, int]:
    lines: list[str] = []
    lines.append(f"# Read plan: window {window}")
    lines.append("")
    lines.append("Written by scripts/plan_inventory.py off the inventory and this window's inputs.")
    lines.append("The unit lines are copied from the sheet grid. Run the script again rather than")
    lines.append("editing this file.")
    lines.append("")
    lines.append(f"## Window {window}")
    lines.append("")

    total_units = 0
    total_passes = 0

    for plan_pass in plan["passes"]:
        parts = _split_pass(plan_pass["id"], plan_pass["units"])
        total_passes += len(parts)
        total_units += len(plan_pass["units"])
        for part_index, (part_id, part_units) in enumerate(parts, 1):
            heading = f"### {part_id}. {plan_pass['name']}"
            if len(parts) > 1:
                heading += f" (part {part_index} of {len(parts)})"
            lines.append(heading)
            lines.append("")
            lines.append(f"window: {window}")
            lines.append(f"reads for: {plan_pass['readsFor']}")
            trades = plan_pass["trades"]
            lines.append(f"trades: {', '.join(trades) if trades else 'none'}")
            lines.append(f"units: {len(part_units)}")
            if plan_pass.get("seamWith"):
                lines.append(f"seam with: {plan_pass['seamWith']}")
            if plan_pass.get("openEntries") is not None:
                lines.append(
                    "open entries: "
                    + str(
                        sum(
                            plan.get("openBySheet", {}).get(_text(r["sheetNumber"]), 0)
                            for r in part_units
                        )
                    )
                )
            if plan_pass["dropped"]:
                lines.append(
                    f"trades not carried, over the cap of {MAX_TRADE_FILES_WINDOW_1}: "
                    + ", ".join(plan_pass["dropped"])
                )
            lines.append("")
            for number, row in enumerate(part_units, 1):
                lines.append(_unit_line(number, row, show_file))
            lines.append("")

    lines.append("## Deliberately left out")
    lines.append("")
    if not plan["excludes"]:
        lines.append("Nothing. This window left nothing out by pattern.")
        lines.append("")
    for block in plan["excludes"]:
        lines.append(f"### Left out: {block['pattern']}")
        lines.append("")
        lines.append(f"reason: {block['reason']}")
        lines.append(f"sheets: {len(block['sheets'])}")
        lines.append("")
        for number, row in enumerate(block["sheets"], 1):
            lines.append(_unit_line(number, row, show_file))
        lines.append("")

    lines.append("## Nothing read for")
    lines.append("")
    if window == 2:
        if not plan["noFamily"] and not plan["noSheet"]:
            lines.append("Nothing. Every package's trade is mapped and named at least one sheet.")
        for trade_code in plan["noFamily"]:
            lines.append(f"{trade_code}: no sheet family mapped")
        for trade_code in plan["noSheet"]:
            lines.append(f"{trade_code}: its sheet families named no sheet in this set")
    else:
        lines.append("Nothing. This window plans off the inventory, not off the packages.")
    lines.append("")

    lines.append("## Totals")
    lines.append("")
    lines.append(f"units planned {total_units}, passes {total_passes}")
    if window == 1:
        lines.append(
            f"sheets left out {plan['excludedCount']}, sheets this window does not read "
            f"{len(plan['unassigned'])}, sheets in the inventory {len(rows)}"
        )
        lines.append(
            f"sheets added by include patterns {sum(len(b['sheets']) for b in plan['includes'])}"
        )
    if window == 2:
        lines.append(
            f"sheets read for more than one trade {plan['readTwice']}, sheets no trade reads "
            f"{len(plan['unread'])}, sheets in the inventory {len(rows)}"
        )
        if plan["unnamedKinds"]:
            lines.append(
                "definition kinds no trade in the map names: " + ", ".join(plan["unnamedKinds"])
            )
    if window == 3:
        lines.append(
            f"open entries on these sheets {plan['openEntries']}, sheets in the inventory {len(rows)}"
        )
    for note in plan["notes"]:
        lines.append(note)

    return "\n".join(lines) + "\n", total_units, total_passes


# --------------------------------------------------------------------------- #
# plan
# --------------------------------------------------------------------------- #

def _require_argument(value, flag: str, window: int):
    if value is None:
        raise PlanError(f"window {window} needs {flag} and it was not given")
    return value


def plan(args) -> str:
    window = args.window
    data = _read_json(args.inventory, "the inventory file")
    if not isinstance(data, dict) or not isinstance(data.get("sheets"), list):
        raise PlanError(f"{args.inventory} is not an inventory file written by this script")
    rows = data["sheets"]
    show_file = len({_text(r.get("fileId")) for r in rows}) > 1

    _require_argument(args.packages, "--packages", window)
    _require_argument(args.trade_knowledge, "--trade-knowledge", window)
    if window != 1 and (args.include or args.exclude):
        # Dropping them quietly would lose the lead's judgment with nothing said about it.
        raise PlanError(f"--include and --exclude are window 1 arguments and window {window} was asked for")
    if window in (2, 3):
        _require_argument(args.kinds, "--kinds", window)
        _require_argument(args.index, "--index", window)

    trade_map = _load_trade_sheets(args.trade_knowledge)
    packages = _read_packages(args.packages)

    notes: list[str] = []
    if window == 1:
        includes = [_split_pattern_argument(raw, "--include") for raw in (args.include or [])]
        excludes = [_split_pattern_argument(raw, "--exclude") for raw in (args.exclude or [])]
        result = _window_1(rows, packages, trade_map, includes, excludes)
    else:
        kinds, kinds_without_sheet = _read_kinds(args.kinds)
        index = _read_index(args.index)
        if not index["locationsPresent"]:
            notes.append("index locations not present")
        if kinds_without_sheet:
            notes.append(f"definition kinds with no defining sheet {kinds_without_sheet}")
        if index["openWithoutSheet"]:
            notes.append(f"open entries naming no sheet {index['openWithoutSheet']}")
        if window == 2:
            result = _window_2(rows, packages, trade_map, kinds, index)
            if result["locationsWithoutField"]:
                notes.append(
                    f"index locations naming no kind or no sheet {result['locationsWithoutField']}"
                )
        else:
            result = _window_3(rows, packages, trade_map, kinds, index)
            result["openBySheet"] = index["openBySheet"]
            result["indexOpenTotal"] = index["openTotal"]

    result["notes"] = notes
    body, total_units, total_passes = _render(window, result, rows, show_file)
    payload = body.encode("utf-8")
    _write_atomically(args.out, payload)

    tail = f"{len(payload):,} bytes"
    partial = ("; " + "; ".join(notes)) if notes else ""

    if window == 1:
        return (
            f"wrote {args.out}: window 1, units {total_units}, passes {total_passes}, "
            f"excluded {result['excludedCount']}, unassigned {len(result['unassigned'])}"
            f"{partial}; {tail}"
        )
    if window == 2:
        no_family = result["noFamily"]
        no_sheet = result["noSheet"]
        return (
            f"wrote {args.out}: window 2, trades {len(packages)}, passes {total_passes}, "
            f"sheets read for more than one trade {result['readTwice']}, "
            f"sheets no trade reads {len(result['unread'])}, "
            f"packages with no sheet family mapped {len(no_family)} "
            f"({', '.join(no_family) if no_family else 'none'}), "
            f"packages whose families named no sheet {len(no_sheet)} "
            f"({', '.join(no_sheet) if no_sheet else 'none'}), "
            f"definition kinds no trade names {len(result['unnamedKinds'])}"
            f"{partial}; {tail}"
        )
    return (
        f"wrote {args.out}: window 3, sheets {total_units}, passes {total_passes}, "
        f"open entries {result['openEntries']} of {result['indexOpenTotal']} in the index"
        f"{partial}; {tail}"
    )


# --------------------------------------------------------------------------- #
# Entry point
# --------------------------------------------------------------------------- #

def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Turn a fetched sheet grid into plan counts, and the record into a read plan.",
    )
    sub = parser.add_subparsers(dest="mode", required=True)

    inv = sub.add_parser("inventory", help="read the grid files and write the counts")
    inv.add_argument("--grid", required=True, type=Path, help="the grid file, or the directory holding the grid pages")
    inv.add_argument(
        "--expect-count", required=True, type=int,
        help="the set count read from the summary-only set_grid call; the run refuses unless the rows total it",
    )
    inv.add_argument("--out-dir", required=True, type=Path, help="where inventory.md and inventory.json are written")

    win = sub.add_parser("plan", help="write one window's read plan")
    win.add_argument("--window", required=True, type=int, choices=(1, 2, 3), help="which window to plan")
    win.add_argument("--inventory", required=True, type=Path, help="inventory.json from the inventory mode")
    win.add_argument("--packages", type=Path, help="the solicitation_list_packages response on disk")
    win.add_argument("--kinds", type=Path, help="the record's definition kinds on disk")
    win.add_argument("--index", type=Path, help="the directory holding the citation index pages")
    win.add_argument("--trade-knowledge", type=Path, help="the plugin's trade-knowledge directory")
    win.add_argument(
        "--include", action="append", metavar="PATTERN:REASON",
        help="window 1 only: a sheet number pattern to read anyway, and why; repeatable",
    )
    win.add_argument(
        "--exclude", action="append", metavar="PATTERN:REASON",
        help="window 1 only: a sheet number pattern to leave out, and why; repeatable",
    )
    win.add_argument("--out", required=True, type=Path, help="the read plan file to write")

    args = parser.parse_args(argv)

    try:
        if args.mode == "inventory":
            print(inventory(args.grid, args.expect_count, args.out_dir))
        else:
            print(plan(args))
    except PlanError as e:
        print(f"plan_inventory: {e}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
