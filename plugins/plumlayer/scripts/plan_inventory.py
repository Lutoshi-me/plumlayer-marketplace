"""
plan_inventory.py: turn a fetched sheet grid into plan counts, and a pass assignment into a read plan.

The scope run's lead plans the read without ever holding a sheet row. It takes the set's shape from
a summary-only `set_grid` call, sends one agent to put the grid on disk, and then runs this script
twice: once to turn the grid files into counts it can group from, and once to expand the passes it
wrote into the read plan's unit lines.

The script copies field values, counts them, and refuses. It never infers a discipline, never
guesses a page number, and never groups by meaning: the grouping is the lead's judgment, written by
hand into the pass assignment file, and everything here is a mechanical expansion of it.

Two subcommands:

  inventory  reads the grid files, refuses unless the rows total the count the lead read for
             itself, and writes `inventory.md` (one line per sheet, then the count tables and the
             sheet number digest at the tail) and `inventory.json` (the normalized rows).

  expand     reads `inventory.json` and the lead's pass assignment file, and writes `read-plan.md`
             whole: rounds, passes, legs, unit lines with page references (a pass's `units` groups
             fold several sheets into one such line, each still counted as one unit), any pass
             under three units folded into a sibling or the round's largest pass and why, what is
             left out and why, and the totals.

Usage:

    python plan_inventory.py inventory --grid <dir or file> --expect-count 209 --out-dir <dir>
    python plan_inventory.py expand --inventory <path> --assignment <path> --out <path>

Exit codes:
  0  wrote the files; one bounds line on stdout naming what it read and what it wrote.
  1  a named failure, one line on stderr: a grid file that does not parse, a row total that does
     not match `--expect-count`, a sheet claimed by two passes, a sheet no pass and no exclusion
     covers, a pattern that matches nothing, a pass carrying more than ten trade files, a pass's
     `units` group naming a sheet outside that pass, naming a sheet a sibling group already
     claimed, or naming more than four sheets, or a malformed pass assignment file.
  2  argparse rejected the invocation.

Grounding role: reads files and copies byte values. A grid file that does not parse whole is a
refusal, not a salvage: a partial recovery of a grounded read is worse than no read at all.
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

UNITS_PER_LEG = 12
MAX_TRADE_FILES = 10
MIN_PASS_UNITS = 3
MAX_UNIT_SHEETS = 4
PREFIX_GROUP_CAP = 60
TITLES_PER_PREFIX = 3
MAX_NAMED = 5

NO_DISCIPLINE = "(none)"
UNTYPED = "(untyped)"

ASSIGNMENT_KEYS = {"project", "setCount", "rounds", "excluded"}
ROUND_KEYS = {"n", "name", "note", "passes"}
PASS_KEYS = {"id", "name", "note", "trades", "select", "units"}
SELECT_KEYS = {"sheets", "patterns", "discipline", "sheetTypes"}
EXCLUSION_KEYS = {"sheets", "patterns", "discipline", "sheetTypes", "reason"}


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
# expand
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


def _select(rows: list[dict], spec, where: str) -> list[dict]:
    """
    The three selection primitives, in the precedence the plan states: an explicit sheet list, then
    sheet number patterns, then a discipline optionally narrowed by sheet type. A primitive that
    matches nothing is a refusal, because the alternative is a typo quietly pushing real sheets into
    the unassigned bucket where widening an exclusion looks like the fix.
    """
    _require_keys(spec, SELECT_KEYS, f"{where}: `select`")

    if "sheets" in spec:
        wanted = _string_list(spec["sheets"], f"{where}: `select.sheets`")
        picked: list[dict] = []
        missing: list[str] = []
        for number in wanted:
            hits = [r for r in rows if r["sheetNumber"] == number]
            if not hits:
                missing.append(number)
                continue
            picked.extend(hits)
        if missing:
            raise PlanError(f"{where}: no sheet in the inventory is numbered {_named(missing)}")
        # The lead's order is honored verbatim here; a number listed twice is read once.
        seen: set[str] = set()
        return [r for r in picked if not (r["unitKey"] in seen or seen.add(r["unitKey"]))]

    if "patterns" in spec:
        patterns = _string_list(spec["patterns"], f"{where}: `select.patterns`")
        chosen: set[str] = set()
        unmatched: list[str] = []
        for pattern in patterns:
            hits = [r for r in rows if fnmatch.fnmatchcase(r["sheetNumber"], pattern)]
            if not hits:
                unmatched.append(pattern)
                continue
            chosen.update(r["unitKey"] for r in hits)
        if unmatched:
            raise PlanError(f"{where}: no sheet number matches the pattern {_named(unmatched)}")
        return [r for r in rows if r["unitKey"] in chosen]

    if "discipline" in spec:
        discipline = spec["discipline"]
        if not isinstance(discipline, str) or not discipline:
            raise PlanError(f"{where}: `select.discipline` is not a non-empty string")
        hits = [r for r in rows if _text(r["discipline"]) == discipline]
        if "sheetTypes" in spec:
            types = _string_list(spec["sheetTypes"], f"{where}: `select.sheetTypes`")
            hits = [r for r in hits if _text(r["sheetType"]) in types]
            if not hits:
                raise PlanError(
                    f"{where}: no sheet in discipline {discipline} carries sheet type "
                    f"{', '.join(types)}"
                )
        if not hits:
            raise PlanError(f"{where}: no sheet in the inventory is in discipline {discipline}")
        return hits

    raise PlanError(f"{where}: `select` names no sheets, no patterns, and no discipline")


def _apply_pass_units(pass_id: str, rows: list[dict], groups_spec, where: str) -> list[list[dict]]:
    """
    Fold the pass's own `units` groups over its selected rows. Each group is an explicit list of
    sheet numbers, in reading order, that stay one read unit -- the multi-page-instrument case rule
    5 describes, written by hand rather than inferred. A sheet the group names must already be in
    this pass's own selection, and a sheet may sit in only one group. A sheet the pass selected but
    no group names stays its own one-sheet unit. The grouped units and the leftover solo units come
    back interleaved by each unit's earliest sheet in the pass's own (grid) order, so the pass still
    reads front to back.
    """
    if not isinstance(groups_spec, list) or not groups_spec:
        raise PlanError(f"{where}: `units` is not a non-empty list of sheet groups")

    by_sheet: dict[str, list[dict]] = {}
    for row in rows:
        by_sheet.setdefault(row["sheetNumber"], []).append(row)
    position = {row["unitKey"]: i for i, row in enumerate(rows)}

    claimed_by: dict[str, int] = {}
    groups: list[list[dict]] = []
    starts: list[int] = []
    for g_index, group in enumerate(groups_spec, 1):
        gwhere = f"{where}: `units` group {g_index}"
        if not isinstance(group, list) or not group or not all(isinstance(s, str) for s in group):
            raise PlanError(f"{gwhere} is not a non-empty list of sheet numbers")
        if len(group) > MAX_UNIT_SHEETS:
            raise PlanError(
                f"{gwhere} names {len(group)} sheets, over the {MAX_UNIT_SHEETS}-sheet cap"
            )
        member_rows: list[dict] = []
        for number in group:
            if number in claimed_by:
                raise PlanError(
                    f"{gwhere}: sheet {number} is also named in `units` group {claimed_by[number]}"
                )
            hits = by_sheet.get(number)
            if not hits:
                raise PlanError(f"{gwhere}: sheet {number} is not in pass {pass_id}")
            claimed_by[number] = g_index
            member_rows.extend(hits)
        groups.append(member_rows)
        starts.append(min(position[r["unitKey"]] for r in member_rows))

    consumed = {row["unitKey"] for group in groups for row in group}
    solo = [[row] for row in rows if row["unitKey"] not in consumed]
    solo_starts = [position[group[0]["unitKey"]] for group in solo]

    combined = sorted(
        zip(starts + solo_starts, groups + solo), key=lambda pair: pair[0]
    )
    return [group for _start, group in combined]


def _legs(pass_id: str, units: list[list[dict]]) -> list[tuple[str, list[list[dict]]]]:
    """
    A pass over twelve units is split into legs of as even a size as possible, earlier legs taking
    the remainder. Balanced and naive chunking always give the same number of legs, so balancing
    costs nothing and keeps a runner from being started for a single unit. A unit is one entry here
    whether it carries one sheet or a `units` group of several: grouping never changes how a pass
    is split.
    """
    n = len(units)
    if n <= UNITS_PER_LEG:
        return [(pass_id, units)]
    count = math.ceil(n / UNITS_PER_LEG)
    if count > len(string.ascii_lowercase):
        raise PlanError(f"pass {pass_id} holds {n} units, more legs than single letters to name them")
    base, extra = divmod(n, count)
    legs: list[tuple[str, list[list[dict]]]] = []
    start = 0
    for index in range(count):
        size = base + (1 if index < extra else 0)
        legs.append((f"{pass_id}{string.ascii_lowercase[index]}", units[start:start + size]))
        start += size
    return legs


def _unit_word(n: int) -> str:
    return "unit" if n == 1 else "units"


def _fold_small_passes(plan_rounds: list[dict]) -> list[str]:
    """
    A pass under three units still pays the runner's fixed cost -- cutting the pass knowledge,
    the convention lines, the boundary verification -- for almost no read. Fold each one into a
    sibling pass of the same round whose trade files already cover it (same set or a superset), or,
    where no sibling qualifies, into the round's largest other pass as trailing units, adding the
    small pass's trade files to that pass's cut. Where that addition would carry the receiving
    pass over the ten-trade-file cap, the small pass stays on its own and the reason is named
    instead. A round of one pass has no fold target and is left alone.

    A fold only ever reaches within the round the lead drew: the round is the unit the lead used to
    keep content families apart, and this never crosses it looking for a bigger receiving pass.

    Mutates plan_rounds in place -- a folded pass's units move onto the receiving pass (and, for
    the largest-pass rule, its trade files too), and the folded pass drops out of its round's pass
    list so nothing downstream renders it a second time. Returns the fold narrative, one line per
    outcome (folded, or kept over the cap), in round then pass order.
    """
    narrative: list[str] = []
    for plan_round in plan_rounds:
        passes = plan_round["passes"]
        kept: list[dict] = []
        for plan_pass in passes:
            units = plan_pass["units"]
            if len(units) >= MIN_PASS_UNITS or len(passes) < 2:
                kept.append(plan_pass)
                continue

            trades = set(plan_pass["obj"].get("trades", []) or [])
            others = [p for p in passes if p is not plan_pass]

            sibling = next(
                (p for p in others if trades <= set(p["obj"].get("trades", []) or [])), None
            )
            if sibling is not None:
                sibling["units"] = sibling["units"] + units
                narrative.append(
                    f"pass {plan_pass['id']} ({len(units)} {_unit_word(len(units))}) folded into "
                    f"{sibling['id']}: {sibling['id']}'s trade files already cover "
                    f"{plan_pass['id']}'s"
                )
                continue

            largest = max(others, key=lambda p: len(p["units"]))
            largest_trades = list(largest["obj"].get("trades", []) or [])
            added = [t for t in plan_pass["obj"].get("trades", []) or [] if t not in largest_trades]
            if len(largest_trades) + len(added) > MAX_TRADE_FILES:
                kept.append(plan_pass)
                narrative.append(
                    f"pass {plan_pass['id']} ({len(units)} {_unit_word(len(units))}) kept "
                    f"separate: folding into {largest['id']} would carry its trade files to "
                    f"{len(largest_trades) + len(added)}, over the cap of {MAX_TRADE_FILES}"
                )
                continue

            largest["obj"] = {**largest["obj"], "trades": largest_trades + added}
            largest["units"] = largest["units"] + units
            narrative.append(
                f"pass {plan_pass['id']} ({len(units)} {_unit_word(len(units))}) folded into "
                f"{largest['id']}: no sibling's trade files covered it, added "
                f"{', '.join(added)} to {largest['id']}'s cut"
            )
        plan_round["passes"] = kept
    return narrative


def _unit_line(number: int, row: dict, show_file: bool) -> str:
    title = _text(row["pageTitle"]) or "(no title)"
    where = f"page {row['pageInPdf']}"
    if show_file:
        # The file id only earns its place where the set spans more than one file and the page
        # number alone would not say which document to open.
        where = f"file {_text(row['fileId']) or '(no file)'}, " + where
    return f"{number}. {row['sheetNumber']}, {where}: {title}"


def _grouped_unit_line(number: int, group: list[dict], show_file: bool) -> str:
    """
    A `units` group is one unit that carries several sheets. One line still names it, sheets comma
    separated and pages listed in the same reading order, so the unit stays one entry in the plan
    even though it points at more than one page.
    """
    sheets = ", ".join(row["sheetNumber"] for row in group)
    wheres = []
    for row in group:
        where = f"page {row['pageInPdf']}"
        if show_file:
            where = f"file {_text(row['fileId']) or '(no file)'}, " + where
        wheres.append(where)
    titles = "; ".join(_text(row["pageTitle"]) or "(no title)" for row in group)
    return f"{number}. {sheets}, {', '.join(wheres)}: {titles}"


def expand(inventory_path: Path, assignment_path: Path, out: Path) -> str:
    data = _read_json(inventory_path, "the inventory file")
    if not isinstance(data, dict) or not isinstance(data.get("sheets"), list):
        raise PlanError(f"{inventory_path} is not an inventory file written by this script")
    rows = data["sheets"]
    unplaceable_count = int(data.get("counts", {}).get("unplaceable", 0) or 0)
    show_file = len({_text(r.get("fileId")) for r in rows}) > 1

    assignment = _read_json(assignment_path, "the pass assignment file")
    _require_keys(assignment, ASSIGNMENT_KEYS, "the pass assignment file")
    rounds = assignment.get("rounds")
    if not isinstance(rounds, list) or not rounds:
        raise PlanError("the pass assignment file carries no `rounds`")

    assigned: dict[str, str] = {}
    doubles: list[str] = []
    seen_pass_ids: set[str] = set()
    plan_rounds: list[dict] = []

    for round_index, round_obj in enumerate(rounds, 1):
        where = f"round {round_index}"
        _require_keys(round_obj, ROUND_KEYS, where)
        passes = round_obj.get("passes")
        if not isinstance(passes, list) or not passes:
            raise PlanError(f"{where} carries no passes")
        plan_passes: list[dict] = []
        for pass_obj in passes:
            _require_keys(pass_obj, PASS_KEYS, f"{where}: a pass")
            pass_id = pass_obj.get("id")
            if not isinstance(pass_id, str) or not pass_id:
                raise PlanError(f"{where}: a pass carries no `id`")
            if pass_id in seen_pass_ids:
                raise PlanError(f"pass id {pass_id} is used more than once")
            seen_pass_ids.add(pass_id)
            trades = pass_obj.get("trades", [])
            if not isinstance(trades, list) or not all(isinstance(t, str) for t in trades):
                raise PlanError(f"pass {pass_id}: `trades` is not a list of strings")
            if len(trades) > MAX_TRADE_FILES:
                raise PlanError(
                    f"pass {pass_id} carries {len(trades)} trade files and the cap is "
                    f"{MAX_TRADE_FILES}; split the pass"
                )
            units = _select(rows, pass_obj.get("select"), f"pass {pass_id}")
            for row in units:
                held = assigned.get(row["unitKey"])
                if held is not None and held != pass_id:
                    doubles.append(f"{row['sheetNumber']} in both {held} and {pass_id}")
                else:
                    assigned[row["unitKey"]] = pass_id
            groups_spec = pass_obj.get("units")
            if groups_spec is not None:
                unit_groups = _apply_pass_units(pass_id, units, groups_spec, f"pass {pass_id}")
            else:
                unit_groups = [[row] for row in units]
            plan_passes.append({"obj": pass_obj, "id": pass_id, "units": unit_groups})
        plan_rounds.append({"obj": round_obj, "n": round_obj.get("n", round_index), "passes": plan_passes})

    fold_lines = _fold_small_passes(plan_rounds)

    if doubles:
        raise PlanError(f"a sheet is claimed by two passes: {_named(doubles)}")

    excluded_blocks: list[dict] = []
    excluded_keys: dict[str, int] = {}
    conflicts: list[str] = []
    for index, exclusion in enumerate(assignment.get("excluded", []) or [], 1):
        _require_keys(exclusion, EXCLUSION_KEYS, f"exclusion {index}")
        reason = exclusion.get("reason")
        if not isinstance(reason, str) or not reason:
            raise PlanError(f"exclusion {index} carries no `reason`")
        spec = {k: v for k, v in exclusion.items() if k != "reason"}
        units = _select(rows, spec, f"exclusion {index}")
        for row in units:
            if row["unitKey"] in assigned:
                conflicts.append(f"{row['sheetNumber']} in pass {assigned[row['unitKey']]} and exclusion {index}")
            excluded_keys[row["unitKey"]] = index
        excluded_blocks.append({"index": index, "reason": reason, "spec": spec, "units": units})

    if conflicts:
        raise PlanError(f"a sheet is both read and left out: {_named(conflicts)}")

    unassigned = [
        r["sheetNumber"] for r in rows if r["unitKey"] not in assigned and r["unitKey"] not in excluded_keys
    ]
    if unassigned:
        raise PlanError(
            f"{len(unassigned)} sheet(s) are in no pass and in no exclusion: {_named(unassigned)}"
        )

    lines: list[str] = []
    project = assignment.get("project")
    lines.append(f"# Read plan: {project}" if project else "# Read plan")
    lines.append("")
    lines.append("Written by scripts/plan_inventory.py from the pass assignment file. The rounds, the")
    lines.append("passes, the trades each carries, and what is left out are the lead's own. The unit lines")
    lines.append("are copied from the sheet grid. Change the assignment file and run the script again")
    lines.append("rather than editing this file.")
    lines.append("")

    total_units = 0
    total_sheets = 0
    total_legs = 0
    total_passes = 0

    for plan_round in plan_rounds:
        round_obj = plan_round["obj"]
        name = round_obj.get("name")
        heading = f"## Round {plan_round['n']}"
        if name:
            heading += f". {name}"
        lines.append(heading)
        lines.append("")
        note = round_obj.get("note")
        if note:
            lines.append(str(note))
            lines.append("")
        round_units = 0
        for plan_pass in plan_round["passes"]:
            pass_obj = plan_pass["obj"]
            units = plan_pass["units"]
            legs = _legs(plan_pass["id"], units)
            total_passes += 1
            total_legs += len(legs)
            round_units += len(units)
            total_units += len(units)
            for leg_index, (leg_id, leg_units) in enumerate(legs, 1):
                leg_heading = f"### {leg_id}"
                if pass_obj.get("name"):
                    leg_heading += f". {pass_obj['name']}"
                if len(legs) > 1:
                    leg_heading += f" (leg {leg_index} of {len(legs)})"
                lines.append(leg_heading)
                lines.append("")
                trades = pass_obj.get("trades", [])
                lines.append(f"trades: {', '.join(trades) if trades else 'none'}")
                lines.append(f"units: {len(leg_units)}")
                if pass_obj.get("note"):
                    lines.append(f"note: {pass_obj['note']}")
                lines.append("")
                for number, group in enumerate(leg_units, 1):
                    if len(group) == 1:
                        lines.append(_unit_line(number, group[0], show_file))
                    else:
                        lines.append(_grouped_unit_line(number, group, show_file))
                    total_sheets += len(group)
                lines.append("")
        lines.append(f"round {plan_round['n']} units: {round_units}")
        lines.append("")

    lines.append("## Folded passes")
    lines.append("")
    if not fold_lines:
        lines.append("Nothing. No pass in this plan carried fewer than three units.")
        lines.append("")
    else:
        for fold_line in fold_lines:
            lines.append(fold_line)
        lines.append("")

    excluded_count = len(excluded_keys)
    lines.append("## Deliberately left out")
    lines.append("")
    if not excluded_blocks:
        lines.append("Nothing. Every sheet in the set is in a pass.")
        lines.append("")
    for block in excluded_blocks:
        lines.append(f"### Exclusion {block['index']}")
        lines.append("")
        lines.append(f"reason: {block['reason']}")
        lines.append(f"sheets: {len(block['units'])}")
        lines.append("")
        for number, row in enumerate(block["units"], 1):
            lines.append(_unit_line(number, row, show_file))
        lines.append("")

    folded = [line for line in fold_lines if " folded into " in line]
    kept_over_cap = [line for line in fold_lines if " kept separate" in line]

    set_count = assignment.get("setCount")
    lines.append("## Totals")
    lines.append("")
    grouped_note = "" if total_sheets == total_units else f" (covering {total_sheets} sheets)"
    lines.append(
        f"units planned {total_units}{grouped_note} + sheets left out {excluded_count} = "
        f"{len(rows)} sheets in the inventory"
    )
    lines.append(
        f"passes {total_passes}, legs {total_legs}, rounds {len(plan_rounds)}, "
        f"{len(folded)} folded, {len(kept_over_cap)} kept separate over the trade-file cap"
    )
    if unplaceable_count:
        lines.append(f"rows the grid could not place, and which no pass can read: {unplaceable_count}")
    if isinstance(set_count, int):
        match = "matches" if set_count == len(rows) + unplaceable_count else "does not match"
        lines.append(
            f"set count in the pass assignment file: {set_count}, which {match} "
            f"{len(rows) + unplaceable_count} rows in the inventory"
        )
    else:
        lines.append("set count in the pass assignment file: not given")

    payload = ("\n".join(lines) + "\n").encode("utf-8")
    _write_atomically(out, payload)

    arithmetic = f"{total_sheets} sheets + {excluded_count} left out = {len(rows)}"
    if isinstance(set_count, int):
        match = "matches" if set_count == len(rows) + unplaceable_count else "does not match"
        arithmetic += f", and the assignment's setCount {set_count} {match} the inventory"
    return (
        f"wrote {out}: {total_units} units, {total_passes} passes, {total_legs} legs, "
        f"{len(plan_rounds)} rounds, {len(folded)} folded, {len(kept_over_cap)} kept separate over "
        f"the trade-file cap, {excluded_count} sheets left out, {len(unassigned)} unassigned, "
        f"{len(rows)} sheets in the inventory; {arithmetic}; {len(payload):,} bytes"
    )


# --------------------------------------------------------------------------- #
# Entry point
# --------------------------------------------------------------------------- #

def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Turn a fetched sheet grid into plan counts, and a pass assignment into a read plan.",
    )
    sub = parser.add_subparsers(dest="mode", required=True)

    inv = sub.add_parser("inventory", help="read the grid files and write the counts")
    inv.add_argument("--grid", required=True, type=Path, help="the grid file, or the directory holding the grid pages")
    inv.add_argument(
        "--expect-count", required=True, type=int,
        help="the set count read from the summary-only set_grid call; the run refuses unless the rows total it",
    )
    inv.add_argument("--out-dir", required=True, type=Path, help="where inventory.md and inventory.json are written")

    exp = sub.add_parser("expand", help="expand the pass assignment into the read plan")
    exp.add_argument("--inventory", required=True, type=Path, help="inventory.json from the inventory mode")
    exp.add_argument("--assignment", required=True, type=Path, help="the pass assignment file the lead wrote")
    exp.add_argument("--out", required=True, type=Path, help="the read plan file to write")

    args = parser.parse_args(argv)

    try:
        if args.mode == "inventory":
            print(inventory(args.grid, args.expect_count, args.out_dir))
        else:
            print(expand(args.inventory, args.assignment, args.out))
    except PlanError as e:
        print(f"plan_inventory: {e}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
