"""
plan_inventory.py: turn a fetched sheet grid into plan counts, and the record into a read plan.

The scope run's lead plans the read without ever holding a sheet row. It takes the set's shape from
a summary-only `set_grid` call, sends one agent to put the grid on disk, and then runs this script:
once to turn the grid files into counts it can read, and once per window to write that window's
read plan off the record's own copies on disk.

The script copies field values, counts them, and refuses. It never infers a discipline, never
guesses a page number, and never reads meaning off a title. Which sheets a window reads is decided
by the inventory alone; which packages a run reviews is decided by the packages file alone.

Two subcommands:

  inventory  reads the grid files, refuses unless the rows total the count the lead read for
             itself, and writes `inventory.md` (one line per sheet, then the count tables and the
             sheet number digest at the tail) and `inventory.json` (the normalized rows).

  plan       reads the window's inputs and writes `read-plan.md` whole: the window's passes, the
             unit lines with their page references, what each pass reads for, what is deliberately
             left out, and the totals.

The three windows, and what each selects:

  1  the vocabulary: every sheet whose type is schedule, legend, notes or cover-index, plus what
     `--include` names and minus what `--exclude` names, grouped into passes by discipline. It also
     writes `plan/window-1.json` in the run folder the `--out` path sits in, holding the unit keys
     it selected and the unit keys it left out, so window 2 subtracts this window rather than
     recomputing it from arguments it might not be given identically.
  2  every sheet once: every inventory row `plan/window-1.json` does not already name, grouped by
     discipline in inventory order and sorted inside a discipline by sheet type, composition ahead
     of extent. The selection is a partition of what window 1 left, so the bounds line states the
     units planned against the distinct sheets they touch, and refuses where the two differ.
  3  one review per package: one pass per row of the packages file, in package order, with the
     packages of one trade kept together. It reads no sheets, so it takes no inventory.

Usage:

    python plan_inventory.py inventory --grid <dir or file> --expect-count 209 --out-dir <dir>

    python plan_inventory.py plan --window 1 --inventory <path>
        [--include <pattern>:<reason>] [--exclude <pattern>:<reason>] --out <path>

    python plan_inventory.py plan --window 2 --inventory <path> --window-1 <path> --out <path>

    python plan_inventory.py plan --window 3 --packages <path> --out <path>

Input shapes, named here so a change on the record's side surfaces as a named field rather than as
an empty plan:

  --packages  a `solicitation_list_packages` response: a `packages` array whose rows carry
              `tradeCode`, and optionally `id`, `name` and `codes`. Two packages carrying one trade
              is ordinary here: both plan a review, and the plan places them one after the
              other.
  --window-1  the file window 1 wrote: `selected` and `excluded`, both arrays of inventory unit
              keys. A key the inventory does not hold is a refusal, since a file from some other
              run would leave a sheet unread with nothing said about it.

Exit codes:
  0  wrote the files; one bounds line on stdout naming what it read and what it wrote.
  1  a named failure, one line on stderr: a file that does not parse, a row total that does not
     match `--expect-count`, two rows folding to one unit key, a missing window input, an argument
     some other window takes, an input row with no `tradeCode`, a window 1 file naming a unit key
     the inventory does not hold or naming one as both selected and excluded, an `--include` or
     `--exclude` with no colon or matching no sheet, an inventory file this script did not write,
     or a window 2 selection that is not a partition of what window 1 left.
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

PREFIX_GROUP_CAP = 60
TITLES_PER_PREFIX = 3
MAX_NAMED = 5

NO_DISCIPLINE = "(none)"
UNTYPED = "(untyped)"

# Window 1 reads what the set says its own marks mean. These four are single recognizer types, so
# the list is exact rather than a family of near names.
VOCABULARY_SHEET_TYPES = ("schedule", "legend", "notes", "cover-index")

# The name this script gives a row the recognizer left untyped, so the type order can place it.
UNTYPED_SHEET_TYPE = "untyped"

# Window 2 reads every remaining sheet once, and inside a discipline it reads in this order:
# composition before extent. A section or a detail shows what an assembly is made of, which is the
# row a subcontractor prices; a plan shows where it occurs. The first reader to see a piece of work
# creates its row and every later reader updates it, so the sheet that should create is the one
# that writes the better row. `other` and untyped go last: neither says what it holds, so neither
# is a sheet to create the vocabulary of the set from.
#
# This is a constant, never a setting a user picks and never a model's judgment.
WINDOW_2_SHEET_TYPE_ORDER = (
    "section", "detail", "elevation", "RCP", "enlarged-plan",
    "plan", "overall-plan", "schematic", "other", UNTYPED_SHEET_TYPE,
)
_WINDOW_2_TYPE_RANK = {name: index for index, name in enumerate(WINDOW_2_SHEET_TYPE_ORDER)}

SELECT_KEYS = {"discipline", "sheetTypes", "patterns"}

WINDOW_1_FILE = ("plan", "window-1.json")


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
    A trade code with its spaces removed, lower cased. The catalog spaces its ids and a package
    row may space them differently, and this is the same fold the record's own catalog lookup uses,
    so the two agree.
    """
    return "".join(code.split()).lower()


def _pack(code: str) -> str:
    """A trade code with its spaces out, its own casing kept. This is what a unit id carries."""
    return "".join(code.split())


def _require_keys(obj, allowed: set[str], where: str) -> None:
    if not isinstance(obj, dict):
        raise PlanError(f"{where} is not an object")
    unknown = sorted(set(obj) - allowed)
    if unknown:
        raise PlanError(f"{where} carries unknown key(s): {', '.join(unknown)}")


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


def _check_unit_keys(rows: list[dict], where: str) -> None:
    """
    Every window subtracts and selects by the unit key string, not by the three fields it is built
    from, so two rows that fold to one key are one row from there on. Window 1 puts the shared key
    in its `selected` list, and window 2's `key not in window_1_keys` filter then drops BOTH rows,
    including the one window 1 never selected. Its partition check cannot see it either, because
    neither row ever reaches the remainder for the count to disagree on. So the collision is refused
    here, before any window subtracts or selects, and both rows are named: a sheet that vanishes
    with nothing said about it is the failure this script exists to prevent.

    A collision needs a `@` or a `#` inside a sheet number or a file id, which is why nothing has
    hit it. Both are opaque strings from upstream and neither is validated anywhere, which is why
    the assumption is checked rather than trusted.
    """
    first: dict[str, str] = {}
    collisions: list[str] = []
    for row in rows:
        key = _text(row.get("unitKey"))
        described = (
            f"sheet {_text(row.get('sheetNumber')) or '(none)'}, "
            f"file {_text(row.get('fileId')) or '(none)'}, "
            f"page {_text(row.get('pageInPdf')) or '(none)'}"
        )
        if key in first:
            collisions.append(f"{key} is both [{first[key]}] and [{described}]")
        else:
            first[key] = described
    if collisions:
        raise PlanError(
            f"{where} carries {len(collisions)} colliding unit key(s), so a row would be dropped "
            f"with nothing said about it: {_named(collisions)}"
        )


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
    _check_unit_keys(rows, "the grid on disk")
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
# Selection
# --------------------------------------------------------------------------- #

def _select(rows: list[dict], spec: dict) -> list[dict]:
    """
    The one selection primitive the windows share: a discipline, a set of sheet number patterns, or
    both, narrowed by sheet type. Every named criterion must hold, so a spec naming a discipline and
    a sheet type selects that discipline's sheets of that type and nothing else. Returns the matching
    rows in inventory order. A spec that matches nothing returns an empty list; whether that is a
    refusal is the caller's judgment, since a lead's own pattern naming no sheet is a typo.
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


# --------------------------------------------------------------------------- #
# The window inputs
# --------------------------------------------------------------------------- #

def _read_packages(path: Path) -> list[dict]:
    """
    The `solicitation_list_packages` response, byte copied to disk. Every package row must carry a
    `tradeCode`: a package with no trade has no unit id for its review to record under, and guessing
    one from its name would be reading meaning off a title.

    Two packages carrying one trade is ordinary and plans two reviews. Nothing about a package
    collides any more: a review computes no sheet list, so there is nothing for two of them to
    compute twice.
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
        codes = row.get("codes")
        # The review carries the package's codes verbatim. A `codes` field that is not a list of
        # strings is a shape change on the record's side, named here rather than rendered as none.
        if codes is not None and (
            not isinstance(codes, list) or not all(isinstance(c, str) for c in codes)
        ):
            raise PlanError(f"{path}: package {index} carries a `codes` that is not a list of strings")
        packages.append(row)
    if not packages:
        raise PlanError(f"{path} carries no packages")
    return packages


def _read_window_1(path: Path, rows: list[dict]) -> tuple[set[str], int, int]:
    """
    The file window 1 wrote: the unit keys it selected and the unit keys its `--exclude` patterns
    left out. Window 2 subtracts both. An excluded sheet was left out by the lead with a reason
    recorded, and reading it in window 2 would override that judgment with nothing said about it.

    A key the inventory does not hold is a refusal rather than a key skipped: a window 1 file from
    some other run would silently leave a sheet of this one unread.
    """
    data = _read_json(path, "the window 1 file")
    if not isinstance(data, dict) or data.get("window") != 1:
        raise PlanError(f"{path} is not a window 1 file written by this script")
    lists: dict[str, list[str]] = {}
    for field in ("selected", "excluded"):
        value = data.get(field)
        if not isinstance(value, list) or not all(isinstance(v, str) for v in value):
            raise PlanError(f"{path}: `{field}` is not a list of unit keys")
        lists[field] = value

    # The two lists are a partition of what window 1 saw, and window 2 only ever reads their union,
    # so a key in both would leave the bounds line reporting a sheet as both selected and left out
    # with nothing catching it. The partition would still be right; the count said out loud would
    # not be.
    both = sorted(set(lists["selected"]) & set(lists["excluded"]))
    if both:
        raise PlanError(
            f"{path} names {len(both)} unit key(s) as both selected and excluded "
            f"({_named(both)}); the two lists are a partition of what window 1 saw"
        )

    known = {r["unitKey"] for r in rows}
    keys = set(lists["selected"]) | set(lists["excluded"])
    strangers = sorted(k for k in keys if k not in known)
    if strangers:
        raise PlanError(
            f"{path} names {len(strangers)} unit key(s) the inventory does not hold "
            f"({_named(strangers)}); it was written off some other inventory"
        )
    return keys, len(lists["selected"]), len(lists["excluded"])


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


def _review_line(number: int, review: dict) -> str:
    """A window 3 unit is a review of a package, not a sheet, so it carries no page reference."""
    return f"{number}. {review['id']}: {review['name']}"


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


def _sheet_type_of(row: dict) -> str:
    return _text(row.get("sheetType")) or UNTYPED_SHEET_TYPE


def _by_sheet_type(rows: list[dict]) -> list[dict]:
    """
    One discipline's rows in the fixed sheet type order, inventory order kept inside a type. A type
    the order does not name sorts after all of them rather than ahead of one it was never ranked
    against; the caller names those types on the bounds line.
    """
    return sorted(
        rows,
        key=lambda row: _WINDOW_2_TYPE_RANK.get(_sheet_type_of(row), len(WINDOW_2_SHEET_TYPE_ORDER)),
    )


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


def _window_1(rows: list[dict], includes, excludes) -> dict:
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

    passes: list[dict] = []
    for discipline, group in _by_discipline(chosen):
        passes.append(
            {
                "id": _pass_id_for_discipline(discipline, 1),
                "name": f"Vocabulary, discipline {discipline}",
                "readsFor": "the vocabulary",
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
        "selectedKeys": [r["unitKey"] for r in chosen],
        "excludedKeys": [r["unitKey"] for r in rows if r["unitKey"] in excluded_keys],
        "unassigned": unassigned,
        "notes": [],
    }


# --------------------------------------------------------------------------- #
# Window 2: every remaining sheet, once
# --------------------------------------------------------------------------- #

def _window_2(rows: list[dict], window_1_keys: set[str], selected: int, excluded: int) -> dict:
    remaining = [r for r in rows if r["unitKey"] not in window_1_keys]

    passes: list[dict] = []
    for discipline, group in _by_discipline(remaining):
        passes.append(
            {
                "id": _pass_id_for_discipline(discipline, 2),
                "name": f"Every sheet, discipline {discipline}",
                "readsFor": "the sheet",
                "units": _by_sheet_type(group),
            }
        )

    planned = [r["unitKey"] for plan_pass in passes for r in plan_pass["units"]]
    distinct = len(set(planned))
    # The selection is a partition of what window 1 left. Grouping and sorting can only reorder it,
    # so a run where the planned units are not exactly those rows, once each, is a defect in this
    # script rather than a set that reads twice.
    if len(planned) != distinct or len(planned) != len(remaining):
        raise PlanError(
            f"window 2 planned {len(planned)} unit(s) over {distinct} distinct sheet(s) from the "
            f"{len(remaining)} row(s) window 1 left; the selection is a partition and this run is "
            f"a script defect"
        )

    by_type: dict[str, int] = {}
    for row in remaining:
        sheet_type = _sheet_type_of(row)
        by_type[sheet_type] = by_type.get(sheet_type, 0) + 1
    ordered_types = [t for t in WINDOW_2_SHEET_TYPE_ORDER if t in by_type]
    unordered_types = [t for t in by_type if t not in _WINDOW_2_TYPE_RANK]

    return {
        "passes": passes,
        "includes": [],
        "excludes": [],
        "excludedCount": 0,
        "unassigned": [],
        "units": len(planned),
        "distinctSheets": distinct,
        "disciplines": len(passes),
        "byType": [(t, by_type[t]) for t in ordered_types + sorted(unordered_types)],
        "otherOrUntyped": by_type.get("other", 0) + by_type.get(UNTYPED_SHEET_TYPE, 0),
        "unorderedTypes": sorted(unordered_types),
        "window1Selected": selected,
        "window1Excluded": excluded,
        "notes": [],
    }


# --------------------------------------------------------------------------- #
# Window 3: one review per package
# --------------------------------------------------------------------------- #

def _window_3(packages: list[dict]) -> dict:
    """
    One review per package, in package order, with the packages of one trade kept together. The
    order is the order the packages were bought in: the first package of each trade holds that
    trade's place, and any later package on the same trade follows it there rather than where it
    sat in the file.

    Two packages carrying one trade both plan, one after the other, and their unit ids differ by the
    ordinal each carries. The runner's overlap scan sees them side by side, which is how two passes
    over the same work are kept from doubling it.
    """
    ordinals: dict[str, int] = {}
    reviews: list[dict] = []
    for package in packages:
        code = _text(package.get("tradeCode")).strip()
        key = _fold(code)
        ordinals[key] = ordinals.get(key, 0) + 1
        reviews.append(
            {
                # Always numbered, even where the trade carries one package: a bare `rev-092116-`
                # would be a prefix of `rev-092116-2-`, and the runner verifies a review by prefix.
                "id": f"rev-{_pack(code)}-{ordinals[key]}",
                "tradeCode": code,
                "tradeKey": key,
                "name": _text(package.get("name")) or code,
                "package": package,
                "codes": list(package.get("codes") or []),
            }
        )

    # Grouped by folded trade code in first-seen order, so two packages on one trade review one
    # after the other and everything else keeps the order the packages were bought in.
    order: list[str] = []
    members: dict[str, list[dict]] = {}
    for review in reviews:
        key = review["tradeKey"]
        if key not in members:
            members[key] = []
            order.append(key)
        members[key].append(review)

    passes: list[dict] = []
    for key in order:
        for review in members[key]:
            plan_pass = {
                "id": review["id"],
                "name": review["name"],
                "readsFor": review["tradeCode"],
                "units": [review],
                "extra": [
                    ("package", _text(review["package"].get("id")) or "(no id)"),
                    ("codes", ", ".join(review["codes"]) if review["codes"] else "none"),
                ],
            }
            passes.append(plan_pass)

    shared = [r for r in reviews if len(members[r["tradeKey"]]) > 1]

    def distinct_codes(rows: list[dict]) -> list[str]:
        seen: list[str] = []
        for row in rows:
            if row["tradeCode"] not in seen:
                seen.append(row["tradeCode"])
        return seen

    return {
        "passes": passes,
        "includes": [],
        "excludes": [],
        "excludedCount": 0,
        "unassigned": [],
        "reviews": len(reviews),
        "trades": len(order),
        "sharedCount": len(shared),
        "sharedCodes": distinct_codes(shared),
        "notes": [],
    }


# --------------------------------------------------------------------------- #
# The read plan file
# --------------------------------------------------------------------------- #

def _render(window: int, plan: dict, rows: list[dict], show_file: bool) -> tuple[str, int, int]:
    lines: list[str] = []
    lines.append(f"# Read plan: window {window}")
    lines.append("")
    lines.append("Written by scripts/plan_inventory.py off this window's inputs.")
    lines.append("The unit lines are copied from the sheet grid and the packages file. Run the")
    lines.append("script again rather than editing this file.")
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
            for label, value in plan_pass.get("extra", []):
                lines.append(f"{label}: {value}")
            lines.append(f"units: {len(part_units)}")
            lines.append("")
            for number, unit in enumerate(part_units, 1):
                lines.append(
                    _review_line(number, unit) if window == 3 else _unit_line(number, unit, show_file)
                )
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
    if window == 3:
        lines.append("Nothing. Every package on the project plans a review.")
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
            f"every sheet once (units {plan['units']} equals distinct sheets "
            f"{plan['distinctSheets']})"
        )
        lines.append(
            f"sheets window 1 selected {plan['window1Selected']}, sheets window 1 left out "
            f"{plan['window1Excluded']}, sheets in the inventory {len(rows)}"
        )
        lines.append(
            "sheets by type: " + ", ".join(f"{name} {count}" for name, count in plan["byType"])
        )
        lines.append(f"sheets typed other or untyped {plan['otherOrUntyped']}")
        if plan["unorderedTypes"]:
            lines.append(
                "sheet types the reading order does not name, read after every type it does: "
                + ", ".join(plan["unorderedTypes"])
            )
    if window == 3:
        lines.append(f"reviews {plan['reviews']}, trades {plan['trades']}")
        lines.append(
            f"packages sharing a trade: {plan['sharedCount']} "
            f"({_named(plan['sharedCodes']) if plan['sharedCodes'] else 'none'})"
        )
    for note in plan["notes"]:
        lines.append(note)

    return "\n".join(lines) + "\n", total_units, total_passes


# --------------------------------------------------------------------------- #
# plan
# --------------------------------------------------------------------------- #

# Which window each argument belongs to. An argument some other window takes is refused rather than
# dropped quietly: dropping it would lose the caller's intent with nothing said about it.
ALLOWED_BY_WINDOW = {
    1: ("--inventory", "--include", "--exclude"),
    2: ("--inventory", "--window-1"),
    3: ("--packages",),
}
REQUIRED_BY_WINDOW = {
    1: ("--inventory",),
    2: ("--inventory", "--window-1"),
    3: ("--packages",),
}
# Arguments no window takes any more, kept so the old invocation refuses in one readable line
# instead of an argparse dump.
RETIRED_ARGUMENTS = {
    "--kinds": "the record's definitions reach a review through the record, not through the plan",
    "--index": "no window plans off the citation index",
}


def _check_arguments(args, window: int) -> None:
    values = {
        "--inventory": args.inventory,
        "--window-1": args.window_1,
        "--packages": args.packages,
        "--kinds": args.kinds,
        "--index": args.index,
        "--include": args.include,
        "--exclude": args.exclude,
    }
    for flag, reason in RETIRED_ARGUMENTS.items():
        if values[flag]:
            raise PlanError(f"{flag} is no longer an argument of any window: {reason}")
    allowed = ALLOWED_BY_WINDOW[window]
    for flag, value in values.items():
        if flag in RETIRED_ARGUMENTS or flag in allowed or not value:
            continue
        takes = [str(w) for w, flags in ALLOWED_BY_WINDOW.items() if flag in flags]
        raise PlanError(
            f"{flag} is a window {' and '.join(takes)} argument and window {window} was asked for"
        )
    for flag in REQUIRED_BY_WINDOW[window]:
        if not values[flag]:
            raise PlanError(f"window {window} needs {flag} and it was not given")


def _read_inventory(path: Path) -> list[dict]:
    data = _read_json(path, "the inventory file")
    if not isinstance(data, dict) or not isinstance(data.get("sheets"), list):
        raise PlanError(f"{path} is not an inventory file written by this script")
    rows = data["sheets"]
    # Checked again here, not only where the file was written: a window plans off whatever
    # inventory.json is on disk, and a hand-edited one is still a file this script would subtract by
    # key.
    _check_unit_keys(rows, str(path))
    return rows


def plan(args) -> str:
    window = args.window
    _check_arguments(args, window)

    rows: list[dict] = []
    show_file = False
    if window in (1, 2):
        rows = _read_inventory(args.inventory)
        show_file = len({_text(r.get("fileId")) for r in rows}) > 1

    window_1_path: Path | None = None
    if window == 1:
        includes = [_split_pattern_argument(raw, "--include") for raw in (args.include or [])]
        excludes = [_split_pattern_argument(raw, "--exclude") for raw in (args.exclude or [])]
        result = _window_1(rows, includes, excludes)
        # The run folder is the folder the plan file sits in; window 2 subtracts this file rather
        # than recomputing window 1's selection from arguments it might not be given identically.
        window_1_path = args.out.parent.joinpath(*WINDOW_1_FILE)
    elif window == 2:
        keys, selected, excluded = _read_window_1(args.window_1, rows)
        result = _window_2(rows, keys, selected, excluded)
    else:
        packages = _read_packages(args.packages)
        result = _window_3(packages)
        result["packages"] = len(packages)

    body, total_units, total_passes = _render(window, result, rows, show_file)
    payload = body.encode("utf-8")
    _write_atomically(args.out, payload)

    written = len(payload)
    if window == 1:
        window_1_payload = (
            json.dumps(
                {
                    "window": 1,
                    "selected": result["selectedKeys"],
                    "excluded": result["excludedKeys"],
                },
                indent=2,
            )
            + "\n"
        ).encode("utf-8")
        _write_atomically(window_1_path, window_1_payload)
        written += len(window_1_payload)
        return (
            f"wrote {args.out} and {window_1_path}: window 1, units {total_units}, passes "
            f"{total_passes}, excluded {result['excludedCount']}, unassigned "
            f"{len(result['unassigned'])}; {written:,} bytes"
        )

    if window == 2:
        by_type = ", ".join(f"{name} {count}" for name, count in result["byType"])
        unordered = (
            "; sheet types the reading order does not name: " + ", ".join(result["unorderedTypes"])
            if result["unorderedTypes"]
            else ""
        )
        return (
            f"wrote {args.out}: window 2, sheets {total_units}, passes {total_passes}, "
            f"disciplines {result['disciplines']}, every sheet once (units {result['units']} "
            f"equals distinct sheets {result['distinctSheets']}), sheets window 1 selected "
            f"{result['window1Selected']}, sheets window 1 left out {result['window1Excluded']}, "
            f"sheets in the inventory {len(rows)}, sheets by type {by_type}, sheets typed other or "
            f"untyped {result['otherOrUntyped']}{unordered}; {written:,} bytes"
        )

    return (
        f"wrote {args.out}: window 3, packages {result['packages']}, reviews {result['reviews']}, "
        f"passes {total_passes}, trades {result['trades']}, "
        f"packages sharing a trade: {result['sharedCount']} "
        f"({_named(result['sharedCodes']) if result['sharedCodes'] else 'none'}); {written:,} bytes"
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
    win.add_argument("--inventory", type=Path, help="windows 1 and 2: inventory.json from the inventory mode")
    win.add_argument(
        "--window-1", type=Path,
        help="window 2 only: plan/window-1.json, the unit keys window 1 selected and left out",
    )
    win.add_argument("--packages", type=Path, help="window 3 only: the solicitation_list_packages response on disk")
    win.add_argument("--kinds", type=Path, help=argparse.SUPPRESS)
    win.add_argument("--index", type=Path, help=argparse.SUPPRESS)
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
