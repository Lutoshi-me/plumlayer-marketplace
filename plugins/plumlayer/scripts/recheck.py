"""
recheck.py: plan the recheck of a new delivery's scope items, check what each unit found, choose
the items to retire, and report the recheck by package.

A new delivery replaces pages the scope list cites. The carry adds every box that reads the same
onto the new page; the scope pass cites the new pages it reads; what is left is each scope item's
reference on a replaced page that nothing cited again on the new page, which the comparison names
`open`. The recheck reads those rows one sheet at a time and, for each, cites the item again on the
new page, updates the row, reads it as removed, or names it as not found. An item whose every open
row reads removed, and that holds no source on a current page, is retired as removed by the
delivery, on the estimator's approval of the plan; an item with a row not found is his to settle.

This script copies field values, counts them and refuses. It reads no record and opens no page:
the rows come off copies of `compare_delivery_status` a fresh agent put on disk byte for byte, and
what a unit found comes off its own report. It never sums a figure the lead says out loud by hand.

Files, all under `<run folder>/recheck/` except the read plan and the reports:

    rows-before/page-NNN.json   compare_delivery_status(kind: "scopeItem", limit: 200, offset: n),
                                taken once the pass's packages are folded
    rows-after/page-NNN.json    the same, taken again once every sheet unit is verified
    files.json                  list_files, which names each file's delivery
    packages.json               solicitation_list_packages, for each package's name by its trade
    plan.json                   this script's own: each unit id with the sheet or the items it
                                carries, so an id keeps on a run again
    units/<unit id>.json        a sheet unit's rows, each copied whole with its row key
    retire/<unit id>.json       a retire unit's items, each with its reason, basis and sources
    <run folder>/read-plan.md   the read plan, `# Read plan: window r`, which the runner, the
                                passes listing, the record script and the check-in read

Four modes:

    python recheck.py plan --run <run folder> --delivery-plan <plan.md> --deliveries <deliveries.json>

        Reads every page of rows-before, refuses a page of another delivery than `run.json` names,
        one measured under another rule version than the plan file names, one whose comparison is
        not complete, pages that leave a row out or carry one twice, and a row that is not a scope
        item's. A row is one reference, known by its own identity as the comparison names it: its
        subject, its entry ids, its sheet, its old page and its box; pages carrying one identity
        twice, or fewer identities than their total, are refused. Takes the rows reading `open:
        true`, one unit per sheet number, a row of a sheet the delivery no longer prints under its
        old number and a row naming no sheet under its old page, each row keyed `<unit id>.<n>`,
        its `n` bound to its identity in plan.json so rows fetched in another order keep their
        keys. Each old page's delivery is read off files.json and
        its label off the delivery list; a file of no delivery the list carries is refused, since
        the retire reason names it. Units are grouped by the letters their sheet number opens
        with, numbered `<tag>-R<letters>-<n>`, at most 12 to a pass, a pass under three folded into
        its neighbour as the plan script folds, and an id already bound to a sheet in plan.json
        keeps it while that sheet's rows read the same, identity for identity and field for field.
        A sheet whose rows changed takes a new id, never one handed out before, so a report written
        over the old rows counts for nothing. The retire passes plan.json already binds are written
        again beside them.

    python recheck.py retire --run <run folder> --delivery-plan <plan.md>

        Once every sheet unit carries a `verified r` line reading ok, reads rows-after and each
        sheet unit's report. An item each of whose open rows reads removed, none not found, and
        none of whose rows on the replaced pages reads `open: false` in rows-after, is retired:
        up to 25 to a unit, `<tag>-rt-<n>`, each with the approval's words as its basis, its
        reason `Removed by <label>: on <old sheet> in <old label>, no longer on <new sheet>`, and
        as its sources the sheets its rows name as showing the removal, at most 10. A reason past
        the REASON_MAX characters retire_scope_item takes names its old sheets by group, then only
        their count, the sources naming where the removal shows; nothing is cut. An item with a
        row not found, with more than 10 such sheets, or whose basis or reason still runs past
        REASON_MAX, is his to settle and is never retired.
        Writes the read plan with the sheet passes and the retire passes.

    python recheck.py check --report <run folder>/reports/<unit id>.md

        One unit's report against its rows file or items file: every row or item carries exactly
        one outcome line, none carries two, none names a row or an item the unit does not carry,
        a row cited again or changed names the page it was cited on and the box or the whole
        sheet, a row read as removed names the sheet that shows it the same way, and a row not
        found names no page. Prints the counts and what the runner finds back on the record: each
        subject on the page it was cited on, and each item retired. A sheet unit that cited and
        changed nothing prints `verify sheets (0): none`, and its report must read 0 created, 0
        updated, 0 Questions raised and replied, 0 sent and 0 landed, since the runner then makes
        no verify_unit call.

    python recheck.py report --run <run folder> --delivery-plan <plan.md> [--start <lines>]

        The recheck by package, off rows-before, rows-after, the unit reports and plan.md: the
        references carried forward, counted only where the plan's `carried:` line records a carry
        that ran, held against what the carry wrote and found there on scope items, off its last
        call split by kind, or, on a `carried:` line that splits no last call by kind, off the
        boxes it wrote on scope items where that call found none already there and off the rows
        alone otherwise, saying which; re-cited by the pass, a closed row that read the same with
        no carry among them; re-cited by the recheck; rows changed; rows removed, each
        named; rows left for him, each named. An item on two packages counts in each, and a line
        says how many do; a line over the project counts each row once. Its first line is the
        `phase: recheck complete` line the lead appends as it prints. Output stops before
        PRINT_CAP characters, its last line naming the command that prints the rest.

Exit codes:
  0  wrote or printed what the mode names.
  1  a named failure, one line on stderr: a file that is not there or does not parse, a page or
     row refused as above, a plan file not approved or of another delivery, a retire run while a
     sheet unit is not verified, a report whose outcome lines do not cover its unit's rows or
     items exactly once, and a partition of the open rows by outcome that does not add up.
  2  argparse rejected the invocation.

Grounding role: copies and counts. A row's outcome, an item's name and what showed its removal are
the rechecker's reading, copied off its report as it wrote them; nothing here fills a gap.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import pass_summary  # noqa: E402
import plan_inventory  # noqa: E402

PlanError = plan_inventory.PlanError

WINDOW = pass_summary.RECHECK_WINDOW
FOLDER = "recheck"
ROWS_BEFORE = "rows-before"
ROWS_AFTER = "rows-after"
PLAN_FILE = "plan.json"
UNITS_FOLDER = "units"
RETIRE_FOLDER = "retire"
READ_PLAN = "read-plan.md"
ITEMS_PER_RETIRE_UNIT = 25
SOURCES_PER_RETIRE = 10
# FIELD_VALUE_MAX, the most characters retire_scope_item's reason and basis each take, counted as
# the api counts a string's length, in UTF-16 code units.
REASON_MAX = 2000
RETIRE_PASS = "rt"
PRINT_CAP = 25_000
NO_LETTERS = "NONE"

_LETTERS_RE = re.compile(r"[A-Za-z]+")
_PAGE_FIELD_RE = re.compile(r"^(.+) (\S+) p([1-9][0-9]*)$")
_BOX_RE = re.compile(r"^box \[(-?[0-9.]+), (-?[0-9.]+), (-?[0-9.]+), (-?[0-9.]+)\] (.+)$")
_WHOLE_SHEET_RE = re.compile(r"^whole sheet: (.+)$")
_HEADER_RE = re.compile(r"^unit: (\S+)\s+pass: (\S+)\s+window: r$")
_LAST_CALL_RE = re.compile(
    r"last call: carried ([0-9]+) on scope items and [0-9]+ on Questions, already there ([0-9]+) "
    r"on scope items and [0-9]+ on Questions"
)
# The `carried:` line a sizer before the split by kind wrote: the boxes by kind over every call, and
# the last call's carried and already there over both kinds together.
_OLD_CARRIED_RE = re.compile(
    r"^[0-9]+ boxes over [0-9]+ calls, ([0-9]+) on scope items and [0-9]+ on Questions; "
    r"last call: carried [0-9]+, already there ([0-9]+),"
)
_REPORT_COUNTS_RE = re.compile(
    r"^created: ([0-9]+)\s+updated: ([0-9]+)\s+questions raised: ([0-9]+)\s+questions replied: ([0-9]+)$"
)
_REPORT_SENT_RE = re.compile(r"^sent: ([0-9]+)\s+landed: ([0-9]+)\s+conflicts: ")


def _named(items: list[str]) -> str:
    return plan_inventory._named(items)


def _write(path: Path, payload) -> int:
    data = (payload if isinstance(payload, str) else json.dumps(payload, indent=2) + "\n").encode("utf-8")
    plan_inventory._write_atomically(path, data)
    return len(data)


def _page(page) -> str:
    return "none" if page is None else f"{page['fileId']} p{page['page']}"


def _length(text: str) -> int:
    return len(text.encode("utf-16-le")) // 2


def row_identity(row: dict) -> str:
    """One reference as the comparison names it: its subject, entry ids, sheet, old page and box."""
    return json.dumps(
        [row.get("subject"), sorted(row.get("entryIds") or []), row.get("sheetNumber"), row.get("old"), row.get("box")],
        sort_keys=True,
    )


def _contents(row: dict) -> str:
    return hashlib.sha256(json.dumps(row, sort_keys=True).encode("utf-8")).hexdigest()[:16]


# --------------------------------------------------------------------------- #
# The inputs
# --------------------------------------------------------------------------- #

def _run(folder: Path) -> dict:
    run = plan_inventory._read_run(folder)
    if run is None:
        raise PlanError(f"{folder} holds no {plan_inventory.RUN_FILE}, so the recheck has no delivery or unit tag to hold to")
    return run


def read_rows(folder: Path, run: dict, plan_doc: dict) -> list[dict]:
    """Every row of the pages a fetch put in `folder`, held to the delivery and the rule version."""
    if plan_doc["ruleVersion"] is None:
        raise PlanError(f"{plan_doc['path']}: its `measured:` line names no rule version to hold the rows to")
    pages = sorted(folder.glob("page-*.json")) if folder.is_dir() else []
    if not pages:
        raise PlanError(f"no page of compare_delivery_status under {folder}; the fetch puts them there")
    rows: list[dict] = []
    seen: set[str] = set()
    total = None
    for path in pages:
        data = plan_inventory._read_json(path, "a page of the comparison")
        delivery = data.get("delivery") if isinstance(data, dict) else None
        if not isinstance(delivery, dict) or delivery.get("id") != run["deliveryId"]:
            raise PlanError(
                f"{path} is the comparison of delivery {delivery.get('id') if isinstance(delivery, dict) else 'none'}, "
                f"and this pass reads {run['deliveryId']}"
            )
        if data.get("ruleVersion") != plan_doc["ruleVersion"]:
            raise PlanError(
                f"{path} was measured under rule version {data.get('ruleVersion')}, and the plan he "
                f"approved under {plan_doc['ruleVersion']}"
            )
        if data.get("complete") is not True:
            raise PlanError(f"{path}: the comparison reads not complete, so its answers can still change")
        listed = data.get("referenceRows")
        if not isinstance(listed, dict) or not isinstance(listed.get("rows"), list):
            raise PlanError(f"{path} carries no `referenceRows` list")
        if total is None:
            total = listed.get("total")
        if listed.get("total") != total or listed.get("offset") != len(rows):
            raise PlanError(
                f"{path} starts at row {listed.get('offset')} of {listed.get('total')}, and the pages "
                f"before it hold {len(rows)} of {total}; fetch the pages again in order"
            )
        for row in listed["rows"]:
            if not isinstance(row, dict) or row.get("kind") != "scopeItem":
                raise PlanError(f"{path} carries a row that is no scope item's; fetch with kind scopeItem")
            if not isinstance(row.get("open"), bool) or not isinstance(row.get("subject"), str):
                raise PlanError(f"{path} carries a scope item's row with no `open` answer or no subject")
            identity = row_identity(row)
            if identity in seen:
                raise PlanError(
                    f"{path} carries the row of {row['subject']} on {row.get('sheetNumber') or _page(row.get('old'))} "
                    f"box {row.get('box')} twice; the comparison lists each reference once, so fetch the pages again in order"
                )
            seen.add(identity)
            rows.append(row)
    if len(rows) != total:
        raise PlanError(f"the pages under {folder} hold {len(rows)} rows of {total}; fetch the rest")
    if len(seen) != total:
        raise PlanError(f"the pages under {folder} hold {len(seen)} distinct rows of {total}; fetch the pages again in order")
    return rows


def _labels(folder: Path, deliveries_path: Path) -> dict[str, str]:
    """Each file's delivery label, off list_files and the delivery list."""
    files = plan_inventory._read_json(folder / FOLDER / "files.json", "the list_files copy")
    deliveries = plan_inventory._read_json(deliveries_path, "the delivery list")
    rows = deliveries.get("deliveries") if isinstance(deliveries, dict) else None
    files_rows = files.get("files") if isinstance(files, dict) else None
    if not isinstance(rows, list) or not isinstance(files_rows, list):
        raise PlanError("the list_files copy or the delivery list carries no array of rows")
    label_of = {d.get("id"): d.get("label") for d in rows if isinstance(d, dict)}
    return {
        f.get("id"): label_of[f.get("deliveryId")]
        for f in files_rows
        if isinstance(f, dict) and f.get("deliveryId") in label_of
    }


def _unit_key(row: dict) -> str:
    if row.get("sheetNumber"):
        return row["sheetNumber"]
    old = row.get("old") or {}
    return f"page {old.get('fileId')} p{old.get('page')}"


def _letters(key: str) -> str:
    if key.startswith("page "):
        return NO_LETTERS
    found = _LETTERS_RE.match(key)
    return found.group(0).upper() if found else NO_LETTERS


def _state(folder: Path) -> dict:
    path = folder / FOLDER / PLAN_FILE
    if not path.is_file():
        return {"window": WINDOW, "units": [], "retire": []}
    data = plan_inventory._read_json(path, "the recheck plan file")
    if not isinstance(data, dict) or data.get("window") != WINDOW:
        raise PlanError(f"{path} is not a recheck plan file written by this script")
    return data


def _verified(folder: Path) -> set[str]:
    return plan_inventory._read_ledger_verified(folder / plan_inventory.LEDGER_FILE, WINDOW)


# --------------------------------------------------------------------------- #
# The read plan
# --------------------------------------------------------------------------- #

def _sheet_line(unit: dict) -> str:
    news = unit["new"] or []
    new = " and ".join(f"file {p['fileId']} page {p['page']}" for p in news) if news else "file none"
    old = " and ".join(f"file {p['fileId']} page {p['page']} in {p['label']}" for p in unit["old"])
    return (
        f"{unit['id']}. {unit['sheet']}, {new}, old {old}, rows {len(unit['rows'])}"
        + (", no new page" if not news else "")
        + f", rows file {FOLDER}/{UNITS_FOLDER}/{unit['id']}.json"
    )


def _retire_line(unit: dict) -> str:
    return f"{unit['id']}. retire, items {len(unit['subjects'])}, items file {FOLDER}/{RETIRE_FOLDER}/{unit['id']}.json"


def _render(folder: Path, sheet_units: list[dict], retire_units: list[dict], tag: str) -> tuple[str, int, list[str]]:
    """The read plan, sheet passes then retire passes, and its pass count and folds."""
    verified = _verified(folder)
    by_letters: dict[str, list[dict]] = {}
    for unit in sheet_units:
        by_letters.setdefault(unit["letters"], []).append(unit)
    plan = {"passes": [
        {"id": f"{tag}-R{letters}", "name": f"Recheck, sheets {letters}", "discipline": letters,
         "readsFor": "the recheck", "units": units}
        for letters, units in by_letters.items()
    ]}
    runner_passes = plan_inventory._fold_small_parts(plan_inventory._window_parts(plan)) if sheet_units else []
    if retire_units:
        retire_plan = {"passes": [{"id": f"{tag}-{RETIRE_PASS}", "name": "Retire the items removed",
                                   "discipline": RETIRE_PASS, "readsFor": "retiring", "units": retire_units}]}
        runner_passes += [[part] for part in plan_inventory._window_parts(retire_plan)]
    units_by_pass = {
        plan_inventory._host(rp)["id"]: [u["id"] for part in rp for u in part["units"]] for rp in runner_passes
    }
    live = plan_inventory.live_pass_state(WINDOW, units_by_pass, folder)
    lines = [
        f"# Read plan: window {WINDOW}",
        "",
        "Written by scripts/recheck.py off the comparison's rows on disk. Run the script again",
        "rather than editing this file: a unit id already planned keeps its sheet or its items.",
        "",
        f"## Window {WINDOW}",
        "",
    ]
    for rp in runner_passes:
        host = plan_inventory._host(rp)
        folded = [part for part in rp if part is not host]
        units = [u for part in rp for u in part["units"]]
        lines.append(f"### {host['id']}. {host['name']}" + (
            f", with sheets {', '.join(part['pass']['discipline'] for part in folded)}" if folded else ""))
        lines.append("")
        lines.append(f"window: {WINDOW}")
        lines.append(f"reads for: {host['pass']['readsFor']}")
        if folded:
            lines.append(f"folded in: {', '.join(part['id'] for part in folded)}")
        lines.append(f"units: {len(units)}")
        lines.append(f"units verified: {live[host['id']][0]}")
        lines.append(f"summed: {live[host['id']][1]}")
        lines.append("starts after: none")
        lines.append("")
        for unit in units:
            line = _retire_line(unit) if "subjects" in unit else _sheet_line(unit)
            lines.append(line + (" verified" if unit["id"] in verified else ""))
        lines.append("")
    lines += [
        "## Deliberately left out",
        "",
        "Nothing. The recheck plans every row the comparison reads as open.",
        "",
        "## Totals",
        "",
        f"sheet units {len(sheet_units)}, rows {sum(len(u['rows']) for u in sheet_units)}, retire units "
        f"{len(retire_units)}, items to retire {sum(len(u['subjects']) for u in retire_units)}, passes {len(runner_passes)}",
    ]
    return "\n".join(lines) + "\n", len(runner_passes), plan_inventory._folds(runner_passes)


def _sheet_units(folder: Path, run: dict, plan_doc: dict, labels: dict[str, str], state: dict) -> tuple[list[dict], dict]:
    """The sheet units off rows-before, with each id plan.json already binds kept."""
    rows = read_rows(folder / FOLDER / ROWS_BEFORE, run, plan_doc)
    by_key: dict[str, list[dict]] = {}
    for row in rows:
        if row["open"]:
            by_key.setdefault(_unit_key(row), []).append(row)
    bound = {entry["key"]: entry for entry in state.get("units", [])}
    # Every id ever handed out, so a sheet whose rows changed never takes back an id a report or a
    # ledger line already names.
    spent = set(state.get("spent", [])) | {entry["id"] for entry in state.get("units", [])}
    numbers: dict[str, int] = {}
    for unit_id in spent:
        stem, _dash, number = unit_id.rpartition("-")
        numbers[stem] = max(numbers.get(stem, 0), int(number))
    tag = run["unitTag"]
    units: list[dict] = []
    kept = new = replaced = 0
    for key, key_rows in by_key.items():
        letters = _letters(key)
        stem = f"{tag}-R{letters}"
        contents = {row_identity(row): _contents(row) for row in key_rows}
        held = bound.get(key)
        held_rows = {r["identity"]: r for r in (held or {}).get("rows", [])}
        if held is not None and {i: r["contents"] for i, r in held_rows.items()} == contents:
            unit_id = held["id"]
            number_of = {i: r["n"] for i, r in held_rows.items()}
            kept += 1
        else:
            numbers[stem] = numbers.get(stem, 0) + 1
            unit_id = f"{stem}-{numbers[stem]}"
            number_of = {row_identity(row): n for n, row in enumerate(key_rows, 1)}
            new += 1
            replaced += held is not None
        spent.add(unit_id)
        olds: list[dict] = []
        news: list[dict] = []
        keyed: list[dict] = []
        for row in sorted(key_rows, key=lambda r: number_of[row_identity(r)]):
            old = row.get("old")
            label = None
            # A row naming no single page has no old page, and so no delivery to name.
            if old:
                label = labels.get(old.get("fileId"))
                if label is None:
                    raise PlanError(
                        f"the row of {row['subject']} on {key} cites file {(old or {}).get('fileId')}, which "
                        f"no delivery on the list holds, so its retire reason could name no label"
                    )
            if old and {**old, "label": label} not in olds:
                olds.append({**old, "label": label})
            if row.get("new") and row["new"] not in news:
                news.append(row["new"])
            identity = row_identity(row)
            keyed.append({"key": f"{unit_id}.{number_of[identity]}", "oldLabel": label, "row": row,
                          "identity": identity, "contents": contents[identity]})
        units.append({"id": unit_id, "sheet": key, "letters": letters, "old": olds, "new": news, "rows": keyed})
    # Each group's units by number, the ones already bound first, so the order holds on a run again.
    order = {letters: i for i, letters in enumerate(dict.fromkeys(u["letters"] for u in units))}
    units.sort(key=lambda u: (order[u["letters"]], int(u["id"].rpartition("-")[2])))
    return units, {"rows": len(rows), "open": sum(len(r) for r in by_key.values()), "kept": kept, "new": new,
                   "replaced": replaced, "spent": sorted(spent)}


def plan(folder: Path, plan_path: Path, deliveries: Path) -> str:
    run = _run(folder)
    plan_doc = plan_inventory.approved_delivery_plan(plan_path, run)
    state = _state(folder)
    units, counts = _sheet_units(folder, run, plan_doc, _labels(folder, deliveries), state)
    written = 0
    for unit in units:
        written += _write(folder / FOLDER / UNITS_FOLDER / f"{unit['id']}.json", {
            "unit": unit["id"], "sheet": unit["sheet"],
            "delivery": {"id": run["deliveryId"], "label": plan_doc["label"]},
            "old": unit["old"], "new": unit["new"], "rows": unit["rows"],
        })
    retire_units = state.get("retire", [])
    state = {"window": WINDOW, "deliveryId": run["deliveryId"], "deliveryPlan": str(plan_path),
             "units": [{"id": u["id"], "key": u["sheet"], "rows": [
                 {"identity": r["identity"], "n": int(r["key"].rpartition(".")[2]), "contents": r["contents"]}
                 for r in u["rows"]]} for u in units],
             "spent": counts["spent"], "retire": retire_units}
    body, passes, folds = _render(folder, units, retire_units, run["unitTag"])
    written += _write(folder / READ_PLAN, body) + _write(folder / FOLDER / PLAN_FILE, state)
    return (
        f"wrote {folder / READ_PLAN} and {folder / FOLDER / PLAN_FILE}: window r, unit tag "
        f"{run['unitTag']} for drawing issue {run['deliveryId']}, rows read {counts['rows']}, open "
        f"{counts['open']}, units {len(units)}, passes {passes}, folds {len(folds)}"
        + (f" ({', '.join(folds)})" if folds else "")
        + f", ids kept {counts['kept']}, ids new {counts['new']}, of them for a sheet whose rows changed "
        f"{counts['replaced']}, retire units {len(retire_units)}; "
        f"{written:,} bytes"
    )


# --------------------------------------------------------------------------- #
# A unit's outcomes
# --------------------------------------------------------------------------- #

def _report_outcomes(report: Path) -> tuple[str, list[dict]]:
    try:
        first = next((line.strip() for line in report.read_text(encoding="utf-8").splitlines() if line.strip()), "")
    except OSError as e:
        raise PlanError(f"no recheck report at {report}: {e}") from None
    header = _HEADER_RE.match(first)
    if header is None:
        raise PlanError(f"{report} does not open with `unit: <unit id>   pass: <pass id>   window: r`")
    try:
        return header.group(1), pass_summary.read_outcomes(report)
    except pass_summary.SummaryError as e:
        raise PlanError(str(e)) from None


def _place(text: str, where: str) -> dict:
    page = _PAGE_FIELD_RE.match(text)
    if page is None:
        raise PlanError(f"{where}: `{text}` is no `<sheet> <fileId> p<page>`")
    return {"sheet": page.group(1), "fileId": page.group(2), "pageInPdf": int(page.group(3))}


def _shown(what: str, where: str) -> dict:
    box = _BOX_RE.match(what)
    if box:
        return {"bboxPts": [float(n) for n in box.groups()[:4]], "words": box.group(5)}
    whole = _WHOLE_SHEET_RE.match(what)
    if whole:
        return {"bboxPts": None, "words": whole.group(1)}
    raise PlanError(f"{where}: `{what[:80]}` is neither `box [x0, y0, x1, y1] <words read>` nor `whole sheet: <what it shows>`")


def unit_outcomes(report: Path) -> dict:
    """One unit's outcome lines held to its rows or items, each exactly once."""
    unit_id, outcomes = _report_outcomes(report)
    folder = report.resolve().parent.parent
    rows_file = folder / FOLDER / UNITS_FOLDER / f"{unit_id}.json"
    items_file = folder / FOLDER / RETIRE_FOLDER / f"{unit_id}.json"
    if rows_file.is_file():
        unit = plan_inventory._read_json(rows_file, "the unit's rows file")
        wanted = [row["key"] for row in unit["rows"]]
        kind, field = "row", "key"
    elif items_file.is_file():
        unit = plan_inventory._read_json(items_file, "the unit's items file")
        wanted = [item["subject"] for item in unit["items"]]
        kind, field = "item", "subject"
    else:
        raise PlanError(f"unit {unit_id} has no rows file and no items file under {folder / FOLDER}")
    seen: dict[str, dict] = {}
    for outcome in outcomes:
        where = f"{report}, {kind} {outcome.get(field)}"
        if outcome["kind"] != kind:
            raise PlanError(f"{report} carries a `{outcome['kind']}:` line, and unit {unit_id} is a {kind} unit")
        if outcome[field] not in wanted:
            raise PlanError(f"{where}: unit {unit_id} carries no such {kind}")
        if outcome[field] in seen:
            raise PlanError(f"{where}: the {kind} has two outcome lines; one {kind} has one outcome")
        if kind == "row":
            if outcome["outcome"] == "not found":
                if outcome["page"] != "none":
                    raise PlanError(f"{where}: a row not found names no page, and this one names {outcome['page']}")
            else:
                outcome["place"] = _place(outcome["page"], where)
                outcome["shown"] = _shown(outcome["what"], where)
        seen[outcome[field]] = outcome
    missing = [key for key in wanted if key not in seen]
    if missing:
        raise PlanError(f"{report} carries no outcome line for {kind} {_named(missing)} of unit {unit_id}")
    return {"unit": unit_id, "kind": kind, "file": unit, "outcomes": [seen[key] for key in wanted]}


def _claimed_writes(report: Path) -> list[str]:
    """The writes a report's count lines claim, each named, or a refusal where a line is missing,
    repeated, or out of shape: a second line could say what the first one hides."""
    lines = [line.strip() for line in report.read_text(encoding="utf-8").splitlines()]
    found = []
    for prefix, pattern in (("created:", _REPORT_COUNTS_RE), ("sent:", _REPORT_SENT_RE)):
        held = [line for line in lines if line.startswith(prefix)]
        if len(held) > 1:
            raise PlanError(f"{report} carries {len(held)} `{prefix}` lines; a report has one, so which it wrote is unknown")
        found.append(pattern.match(held[0]) if held else None)
    counts, sent = found
    if counts is None or sent is None:
        raise PlanError(
            f"{report} carries no `created: <n>   updated: <n>   questions raised: <n>   questions "
            f"replied: <n>` line or no `sent: <n>   landed: <n>   conflicts:` line to show it wrote nothing"
        )
    named = zip(("created", "updated", "questions raised", "questions replied", "sent", "landed"),
                (*counts.groups(), sent.group(1), sent.group(2)))
    return [f"{label} {value}" for label, value in named if value != "0"]


def check(report: Path) -> list[str]:
    found = unit_outcomes(report)
    counts: dict[str, int] = {}
    for outcome in found["outcomes"]:
        counts[outcome["outcome"]] = counts.get(outcome["outcome"], 0) + 1
    names = pass_summary.ROW_OUTCOMES if found["kind"] == "row" else pass_summary.ITEM_OUTCOMES
    lines = [f"unit {found['unit']}: {found['kind']}s {len(found['outcomes'])}, "
             + ", ".join(f"{name} {counts.get(name, 0)}" for name in names)]
    if found["kind"] == "row":
        subject_of = {row["key"]: row["row"]["subject"] for row in found["file"]["rows"]}
        sheets: list[dict] = []
        pairs: list[str] = []
        for outcome in found["outcomes"]:
            if outcome["outcome"] not in ("recited", "updated"):
                continue
            if outcome["place"] not in sheets:
                sheets.append(outcome["place"])
            pair = f"find back: {subject_of[outcome['key']]} on {outcome['page']}"
            if pair not in pairs:
                pairs.append(pair)
        if sheets:
            lines.append(f"verify sheets ({len(sheets)}): {json.dumps(sheets)}")
        else:
            claimed = _claimed_writes(report)
            if claimed:
                raise PlanError(
                    f"{report}: every row reads removed or not found, which write nothing, and the report "
                    f"reads {', '.join(claimed)}; no verify_unit call could find those writes back"
                )
            lines.append("verify sheets (0): none; the unit wrote nothing, so no verify_unit call")
        lines.extend(pairs)
    else:
        label = found["file"]["delivery"]["label"]
        lines.extend(
            f"find back: {o['subject']} retired, versionScope {label}"
            for o in found["outcomes"] if o["outcome"] == "retired"
        )
    return lines


# --------------------------------------------------------------------------- #
# The retire step
# --------------------------------------------------------------------------- #

def _sheet_outcomes(folder: Path, sheet_units: list[dict]) -> dict[str, dict]:
    """Every sheet unit's row outcomes by row key."""
    found: dict[str, dict] = {}
    for unit in sheet_units:
        result = unit_outcomes(folder / plan_inventory.REPORTS_FOLDER / f"{unit['id']}.md")
        for outcome in result["outcomes"]:
            found[outcome["key"]] = outcome
    return found


def retire_reason(label: str, olds: list[tuple[str, str | None, bool]]) -> str | None:
    """
    The reason a retire carries, under REASON_MAX: each old sheet on its own where that fits, else
    the sheets named together by the delivery they came in, else only their count, the sources
    naming where the removal shows. Each old sheet is its number, its delivery's label or None,
    and whether the new delivery still prints it. None where even the count runs past.
    """
    def gone(printed: bool, many: bool) -> str:
        return (f"no longer on {'them' if many else 'it'}" if printed else f"which {label} no longer prints")

    head = f"Removed by {label}: "
    each = head + "; ".join(
        f"on {sheet}" + (f" in {old}" if old else "") + (f", no longer on {sheet}" if printed else f", {gone(False, False)}")
        for sheet, old, printed in olds
    )
    if _length(each) <= REASON_MAX:
        return each
    groups: dict[tuple[str | None, bool], list[str]] = {}
    for sheet, old, printed in olds:
        groups.setdefault((old, printed), []).append(sheet)
    together = head + "; ".join(
        f"on {', '.join(sheets)}" + (f" in {old}" if old else "") + f", {gone(printed, len(sheets) > 1)}"
        for (old, printed), sheets in groups.items()
    )
    if _length(together) <= REASON_MAX:
        return together
    labels = list(dict.fromkeys(old for old, _printed in groups if old))
    counted = head + f"on {len(olds)} sheets" + (f" in {' and '.join(labels)}" if labels else "") + "; its sources are the sheets that show the removal"
    return counted if _length(counted) <= REASON_MAX else None


def _selection(folder: Path, run: dict, plan_doc: dict, sheet_units: list[dict]) -> dict:
    """Each item of the open rows, sorted into retired, his to settle, and kept."""
    outcomes = _sheet_outcomes(folder, sheet_units)
    after = read_rows(folder / FOLDER / ROWS_AFTER, run, plan_doc)
    current = {row["subject"] for row in after if not row["open"]}
    items: dict[str, list[tuple[dict, dict, dict]]] = {}
    for unit in sheet_units:
        for row in unit["rows"]:
            items.setdefault(row["row"]["subject"], []).append((unit, row, outcomes[row["key"]]))
    retire: list[dict] = []
    his: dict[str, str] = {}
    kept: dict[str, str] = {}
    for subject, rows in items.items():
        read = [outcome["outcome"] for _unit, _row, outcome in rows]
        if "not found" in read:
            his[subject] = "a row not found"
            continue
        if any(o != "removed" for o in read):
            continue
        if subject in current:
            kept[subject] = "cited on a current page"
            continue
        sources: list[dict] = []
        olds: list[tuple[str, str | None, bool]] = []
        for unit, row, outcome in rows:
            place, shown = outcome["place"], outcome["shown"]
            source = {"kind": "sheet-region" if shown["bboxPts"] else "sheet", **place}
            if shown["bboxPts"]:
                source.update({"bboxPts": shown["bboxPts"], "frame": "page-points"})
            if source not in sources:
                sources.append(source)
            old = (row["row"].get("sheetNumber") or unit["sheet"], row["oldLabel"], bool(row["row"].get("new")))
            if old not in olds:
                olds.append(old)
        if len(sources) > SOURCES_PER_RETIRE:
            his[subject] = f"its removal shows on {len(sources)} sheets, more than one retire carries"
            continue
        reason = retire_reason(plan_doc["label"], olds)
        if _length(plan_doc["approvedWords"]) > REASON_MAX or reason is None:
            his[subject] = f"its retire's basis or reason runs past the {REASON_MAX:,} characters a retire carries"
            continue
        retire.append({
            "subject": subject,
            "name": rows[0][2]["name"],
            "basis": plan_doc["approvedWords"],
            "reason": reason,
            "sources": sources,
            "rows": [row["key"] for _unit, row, _outcome in rows],
            "oldPages": [row["row"]["old"] for _unit, row, _outcome in rows if row["row"].get("old")],
        })
    return {"retire": retire, "his": his, "kept": kept, "items": items, "outcomes": outcomes, "after": after}


def _sheet_units_from_disk(folder: Path, state: dict) -> list[dict]:
    units = []
    for entry in state.get("units", []):
        unit = plan_inventory._read_json(folder / FOLDER / UNITS_FOLDER / f"{entry['id']}.json", "a unit's rows file")
        units.append({"id": entry["id"], "sheet": unit["sheet"], "letters": _letters(unit["sheet"]),
                      "old": unit["old"], "new": unit["new"], "rows": unit["rows"]})
    return units


def retire(folder: Path, plan_path: Path) -> str:
    run = _run(folder)
    plan_doc = plan_inventory.approved_delivery_plan(plan_path, run)
    state = _state(folder)
    sheet_units = _sheet_units_from_disk(folder, state)
    if not sheet_units:
        return f"nothing to retire: the recheck of {run['deliveryId']} planned no sheet unit, since no row read open"
    verified = _verified(folder)
    waiting = [u["id"] for u in sheet_units if u["id"] not in verified]
    if waiting:
        raise PlanError(
            f"sheet units {_named(waiting)} carry no `verified r` line reading ok; the retire step "
            f"reads what every sheet unit found"
        )
    chosen = _selection(folder, run, plan_doc, sheet_units)
    by_subject = {item["subject"]: item for item in chosen["retire"]}
    tag = run["unitTag"]
    units: list[dict] = []
    bound: set[str] = set()
    for entry in state.get("retire", []):
        subjects = [s for s in entry["subjects"] if s in by_subject]
        if subjects:
            units.append({"id": entry["id"], "subjects": subjects})
            bound.update(subjects)
    number = max((int(entry["id"].rpartition("-")[2]) for entry in state.get("retire", [])), default=0)
    left = [item["subject"] for item in chosen["retire"] if item["subject"] not in bound]
    for start in range(0, len(left), ITEMS_PER_RETIRE_UNIT):
        number += 1
        units.append({"id": f"{tag}-{RETIRE_PASS}-{number}", "subjects": left[start:start + ITEMS_PER_RETIRE_UNIT]})
    written = 0
    for unit in units:
        written += _write(folder / FOLDER / RETIRE_FOLDER / f"{unit['id']}.json", {
            "unit": unit["id"], "delivery": {"id": run["deliveryId"], "label": plan_doc["label"]},
            "items": [by_subject[s] for s in unit["subjects"]],
        })
    state["retire"] = units
    body, passes, _folds = _render(folder, sheet_units, units, tag)
    written += _write(folder / READ_PLAN, body) + _write(folder / FOLDER / PLAN_FILE, state)
    return (
        f"wrote {folder / READ_PLAN} and {folder / FOLDER / PLAN_FILE}: window r, items to retire "
        f"{len(chosen['retire'])} in {len(units)} units, items his to settle {len(chosen['his'])}, items "
        f"kept on a current page {len(chosen['kept'])}, passes {passes}; {written:,} bytes"
    )


# --------------------------------------------------------------------------- #
# The report
# --------------------------------------------------------------------------- #

def _package_names(folder: Path) -> dict[str | None, str]:
    data = plan_inventory._read_json(folder / FOLDER / "packages.json", "the packages copy")
    packages = data.get("packages") if isinstance(data, dict) else None
    if not isinstance(packages, list):
        raise PlanError(f"{folder / FOLDER / 'packages.json'} carries no `packages` array")
    names: dict[str | None, list[str]] = {}
    for package in packages:
        if isinstance(package, dict) and package.get("tradeCode"):
            names.setdefault(package["tradeCode"], []).append(package.get("name") or package["tradeCode"])
    out: dict[str | None, str] = {code: " and ".join(n) for code, n in names.items()}
    out[None] = "No Package"
    return out


def carry_of(plan_doc: dict) -> dict:
    """
    Whether the carry ran, and what it wrote and found there on scope items with where that figure
    comes from, off the plan's `carried:` line. A line split by kind gives the last call's two
    figures; a line a sizer wrote before that split gives the boxes the carry wrote on scope items
    over every call where its last call found none already there, and no figure otherwise, so the
    rows alone count what was carried.
    """
    carried = plan_doc["carried"]
    if plan_doc.get("carry") == "left out" or carried is None or carried.startswith("none"):
        return {"ran": False, "figure": None, "from": None}
    last = _LAST_CALL_RE.search(carried)
    if last:
        return {"ran": True, "figure": int(last.group(1)) + int(last.group(2)), "from": "last call"}
    old = _OLD_CARRIED_RE.match(carried)
    if old is None:
        raise PlanError(
            f"{plan_doc['path']}: its `carried:` line is in neither shape the delivery sizer writes, "
            f"so what the carry wrote on scope items cannot be read off it"
        )
    if int(old.group(2)) == 0:
        return {"ran": True, "figure": int(old.group(1)), "from": "every call"}
    return {"ran": True, "figure": None, "from": "rows"}


CATEGORIES = (
    ("carried", "carried forward"),
    ("pass", "re-cited by the pass"),
    ("recited", "re-cited by the recheck"),
    ("updated", "rows changed"),
    ("removed", "rows removed"),
    ("left", "rows left for you"),
    ("kept", "rows read removed, the item kept on a current page"),
    ("held", "rows read removed, the item on your list"),
    ("refused", "rows read removed, the retire refused"),
)


def report_lines(folder: Path, plan_path: Path) -> list[str]:
    run = _run(folder)
    plan_doc = plan_inventory.approved_delivery_plan(plan_path, run)
    state = _state(folder)
    before = read_rows(folder / FOLDER / ROWS_BEFORE, run, plan_doc)
    sheet_units = _sheet_units_from_disk(folder, state)
    names = _package_names(folder)
    chosen = _selection(folder, run, plan_doc, sheet_units) if sheet_units else {
        "items": {}, "outcomes": {}, "his": {}, "kept": {}, "after": [], "retire": []}
    retired: dict[str, str] = {}
    refused: dict[str, str] = {}
    for unit in state.get("retire", []):
        result = unit_outcomes(folder / plan_inventory.REPORTS_FOLDER / f"{unit['id']}.md")
        for outcome in result["outcomes"]:
            {"retired": retired, "refused": refused, "kept": chosen["kept"]}[outcome["outcome"]][outcome["subject"]] = outcome["what"]
    unplanned = [item["subject"] for item in chosen["retire"]
                 if item["subject"] not in retired and item["subject"] not in refused and item["subject"] not in chosen["kept"]]
    if unplanned:
        raise PlanError(f"items {_named(unplanned)} were chosen to retire and no retire unit's report names them; run the retire passes first")

    carry = carry_of(plan_doc)

    def category(row: dict, outcome: dict | None) -> str:
        if not row["open"]:
            # A row that read the same is carried forward only where a carry ran; with none, the
            # pass cited the item on its new page.
            return "carried" if row["answer"] == "same" and carry["ran"] else "pass"
        found = outcome["outcome"]
        if found in ("recited", "updated"):
            return found
        if found == "not found":
            return "left"
        subject = row["subject"]
        if subject in retired:
            return "removed"
        if subject in refused:
            return "refused"
        if subject in chosen["his"]:
            return "held"
        return "kept"

    # The rows on disk in each unit file are copies of rows-before's open rows, matched by identity
    # and held to read the same.
    open_keys = {row_identity(k["row"]): (k, u) for u in sheet_units for k in u["rows"]}
    by_package: dict[str | None, dict[str, int]] = {}
    over: dict[str, int] = {key: 0 for key, _ in CATEGORIES}
    named: list[str] = []
    still_open: list[str] = []
    after_open = {(r["subject"], json.dumps(r.get("new")), json.dumps(r.get("box"))) for r in chosen["after"] if r["open"]}
    packages_of: dict[str, set] = {}
    for row in before:
        outcome = None
        keyed = None
        if row["open"]:
            match = open_keys.get(row_identity(row))
            if match is None or _contents(match[0]["row"]) != _contents(row):
                raise PlanError(
                    f"an open row of {row['subject']} in rows-before sits in no unit's rows file, or reads "
                    f"otherwise than its unit's copy; plan the recheck again"
                )
            keyed, unit = match
            outcome = chosen["outcomes"][keyed["key"]]
        cat = category(row, outcome)
        over[cat] += 1
        packages = row.get("packages") or [None]
        packages_of.setdefault(row["subject"], set()).update(packages)
        for package in packages:
            by_package.setdefault(package, {key: 0 for key, _ in CATEGORIES})[cat] += 1
        if outcome is None:
            continue
        where = f"on {row.get('sheetNumber') or unit['sheet']}" + (f" in {keyed['oldLabel']}" if keyed["oldLabel"] else "")
        name = json.dumps(outcome["name"])
        in_packages = ", ".join(names.get(p, p) for p in packages)
        if cat == "removed":
            gone = f"no longer on {row['sheetNumber']}" if row.get("new") else f"which {plan_doc['label']} no longer prints"
            named.append(f"removed: {name} {where}, {gone}, shown on {outcome['page']}; {in_packages}")
        elif cat == "left":
            named.append(f"left for you: {name} {where}: {outcome['what']}; {in_packages}")
        elif cat == "kept":
            named.append(f"read removed, kept on a current page: {name} {where}; {in_packages}")
        elif cat == "held":
            named.append(f"read removed, held with the item on your list: {name} {where}; {in_packages}")
        elif cat == "refused":
            named.append(f"read removed, not retired: {name} {where}: {refused[row['subject']]}; {in_packages}")
        elif (cat in ("recited", "updated") and row.get("new") and outcome["place"]["fileId"] == row["new"]["fileId"]
              and outcome["place"]["pageInPdf"] == row["new"]["page"]
              and (row["subject"], json.dumps(row.get("new")), json.dumps(row.get("box"))) in after_open):
            still_open.append(f"re-cited on its new page and still open: {name} {where}")
    open_count = sum(1 for r in before if r["open"])
    answered = sum(over[key] for key, _ in CATEGORIES if key not in ("carried", "pass"))
    if answered != open_count:
        raise PlanError(f"the recheck sorted {answered} rows of the {open_count} open in rows-before; the partition does not add up")
    left_lines = sum(1 for o in chosen["outcomes"].values() if o["outcome"] == "not found")
    if over["left"] != left_lines:
        raise PlanError(f"the report lists {over['left']} rows left for you and the units read {left_lines} rows not found")

    phase = "phase: recheck complete " + " ".join(f"{key} {over[key]}" for key, _ in CATEGORIES)
    lines = [phase, f"recheck of {plan_doc['label']}: rows on the replaced pages {len(before)}, open when the recheck began {open_count}, in {len(sheet_units)} sheets"]
    figure = carry["figure"]
    same = "" if figure is None else ("equal" if figure == over["carried"] else f"differ by {abs(figure - over['carried'])}")
    if not carry["ran"]:
        lines.append(f"carried forward {over['carried']}; the carry was left out of the plan or carried nothing")
    elif carry["from"] == "last call":
        lines.append(f"carried forward {over['carried']}, against {figure} the carry wrote and found there on scope items: {same}")
    elif carry["from"] == "every call":
        lines.append(
            f"carried forward {over['carried']}, against {figure} the carry wrote on scope items over every call, "
            f"off a carried line that splits no last call by kind, whose last call found none already there: {same}"
        )
    else:
        lines.append(
            f"carried forward {over['carried']}, counted off the rows alone: the plan's carried line splits "
            f"neither its last call nor what it found already there by kind"
        )
    for package, counts in by_package.items():
        lines.append(
            f"package {names.get(package, package)} ({package or 'none'}): "
            + ", ".join(f"{label} {counts[key]}" for key, label in CATEGORIES if counts[key] or key in dict(CATEGORIES[:6]))
        )
    shared = sum(1 for packages in packages_of.values() if len(packages) > 1)
    lines.append(
        f"an item on two or more packages counts in each package: {shared} "
        + ("item does" if shared == 1 else "items do")
    )
    lines.append("over the project, each row once: " + ", ".join(f"{label} {over[key]}" for key, label in CATEGORIES))
    lines.extend(named)
    lines.extend(still_open)
    return lines


def _print_capped(lines: list[str], start: int, command: str) -> list[str]:
    out: list[str] = []
    size = 0
    for index in range(start, len(lines)):
        if size + len(lines[index]) + 1 > PRINT_CAP - 400 and out:
            out.append(f"not printed: from line {index + 1}; the rest: {command} --start {index}")
            return out
        out.append(lines[index])
        size += len(lines[index]) + 1
    out.append(f"every line printed, {len(out)} in this call")
    return out


# --------------------------------------------------------------------------- #
# Entry point
# --------------------------------------------------------------------------- #

def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Plan, check, retire and report the recheck of a new delivery.")
    modes = parser.add_subparsers(dest="mode", required=True)
    p = modes.add_parser("plan", help="plan one unit per sheet over the open rows")
    p.add_argument("--run", type=Path, required=True, help="the run folder")
    p.add_argument("--delivery-plan", type=Path, required=True, help="the delivery's plan file he approved")
    p.add_argument("--deliveries", type=Path, required=True, help="the delivery list on disk, deliveries.json")
    r = modes.add_parser("retire", help="choose the items to retire once every sheet unit is verified")
    r.add_argument("--run", type=Path, required=True, help="the run folder")
    r.add_argument("--delivery-plan", type=Path, required=True, help="the delivery's plan file he approved")
    c = modes.add_parser("check", help="one unit's outcome lines against its rows or items")
    c.add_argument("--report", type=Path, required=True, help="the unit's report, <run folder>/reports/<unit id>.md")
    o = modes.add_parser("report", help="the recheck by package")
    o.add_argument("--run", type=Path, required=True, help="the run folder")
    o.add_argument("--delivery-plan", type=Path, required=True, help="the delivery's plan file he approved")
    o.add_argument("--start", type=int, default=0, help="how many lines an earlier call already printed")
    args = parser.parse_args(argv)
    try:
        if args.mode == "plan":
            lines = [plan(args.run, args.delivery_plan, args.deliveries)]
        elif args.mode == "retire":
            lines = [retire(args.run, args.delivery_plan)]
        elif args.mode == "check":
            lines = check(args.report)
        else:
            command = (
                f"python3 '{Path(__file__).resolve()}' report --run '{args.run}' "
                f"--delivery-plan '{args.delivery_plan}'"
            )
            lines = _print_capped(report_lines(args.run, args.delivery_plan), args.start, command)
    except PlanError as e:
        print(f"recheck: {e}", file=sys.stderr)
        return 1
    for line in lines:
        print(line)
    return 0


if __name__ == "__main__":
    sys.exit(main())
