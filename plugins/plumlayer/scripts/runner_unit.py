"""
runner_unit.py: a pass runner's bookkeeping for one unit at a time, off the read plan, the unit's
report file and the `verify_unit` answer.

A pass runner dispatches one reader or reviewer per unit, verifies the unit with one `verify_unit`
call, and writes the ledger's fixed lines and the pass's trades, kinds and names files. Done by
hand, that bookkeeping was most of what a runner held per sheet: the report read back, every line
retyped into an append, and a search per item name and per Question. So this script does it, and
the runner holds the one line it prints per unit.

It reads no record and opens no page. Every figure it writes is one the plan, the report or the
answer already carries, copied or counted.

Two modes:

    python runner_unit.py next '<run folder>' --window <n> --pass <pass id> [--stopped <unit id>]

        Reads the pass's block of `<run folder>/read-plan.md` with the summary script's own plan
        reader, and this window's ledger lines for the units the block carries, whatever pass they
        name. Takes the first unit with no `verified ... result ok` line, appends its `dispatch`
        line unless the unit's last line on the ledger is already one, and prints one line:

            next: <unit> sheet <number> file <fileId|none> page <n> opens as <key|none> repeated <read in set <version>|not read> left out none
            next: <unit> sheet none file <fileId> page <n> opens as none repeated not read left out <sheet numbers|none>
            next: <unit> package <package id> trade <catalog id>
            next: <unit> package <package id> trade <catalog id> continues <unit id> sections <sections>
            next: none

        the first for a sheet, the second for a file's repeated lines, the third for a review and
        the fourth for a continuation of one. Where that unit already stands verified as a
        mismatch, or its reader stopped answering twice, it appends nothing and prints
        `stop: <unit> <why>`, and the runner goes to its summary. In window 3 it first binds every
        continuation the pass is owed, through `plan_inventory.py`'s own `continue` code, and
        appends the `unread section` notes a full pass is owed.

        `--stopped <unit id>` is for a reader that stopped answering and left no report. The first
        time, it appends `note <window> <pass> <unit> deviation <sheet> reader stopped answering,
        read again once` and goes on as `next` does, the unit's `dispatch` line appended again. The
        second time, decided by counting those notes, it appends `note <window> <pass> <unit> unread
        <sheet> reader stopped answering twice` and prints `stop:`.

    python runner_unit.py record '<run folder>' --window <n> --pass <pass id> --unit <unit id> <<'EOF'
    <the verify_unit answer, as it came back>
    EOF

        Reads `<run folder>/reports/<unit id>.md` and the answer on stdin, and writes, in this
        order, each part skipped where the ledger or the file already carries it:

        1. `<run folder>/names/<pass id>.txt`: one `<name>\t<unit id>` line per name on the
           report's `created names:` line, the whole unit skipped where the file names it already.
        2. `<run folder>/kinds/<pass id>.txt`: each kind on `definitions kinds added:` the file
           does not hold yet.
        3. `<run folder>/trades/<pass id>.txt`, off the answer, the whole unit skipped where the
           file names it already:
               <unit id> trade <catalog id> <count>
               <unit id> candidates <count>
               <unit id> touched <catalog id>
        4. Notes on the ledger:
               note <w> <p> <u> anomaly <each line under anomalies:, whole>
               note <w> <p> <u> grain <each line under grain questions:, whole>
               note <w> <p> <u> door <each line under door-owned suggestions:, whole>
               note <w> <p> <u> set <setVersion> file <fileId>                      (repeated lines)
               note <w> <p> <u> unread file <fileId> repeated lines not read, <reason>  (repeated lines)
               note <w> <p> <u> unread file <fileId> <b> blocks <l> lines not listed, <why>  (repeated lines)
               note <w> <p> <u> deviation reader counted <what> <a>, named <b>
               note <w> <p> <u> overlap <name> (<earlier unit>, <unit>)
               note <w> <p> <u> deviation verify <check> <value>: <reason>       (up to five)
        5. The `verified` line, last:
               verified <w> <p> <u> created <n> items <n> updated <n> questions <n> replied <n> sent <n> landed <n> conflicts <n> result <ok|mismatch>

        `created` is the answer's `entryCount`. `items` is the report's `created:` figure, and
        `sent`, `landed` and `conflicts` the first whole number on each of those fields, `none`
        reading 0 on `conflicts`. `updated` is the distinct subjects the report's `verify:` line
        names as updated, page cited or written off manual pages; `questions` and `replied` are the
        sizes of its raised and replied lists. Each is what the call checked, since the result is a
        mismatch wherever the answer's `checked` counts differ from those list sizes. A figure the
        report does not carry is written 0 on a mismatch line, and the reason names it.

        The result is a mismatch where the answer says so, where `checked` differs from the
        `verify:` line, where the `verify:` line or a count field of the report does not read, where
        the answer's `sheets` leave out a page the unit read (its own sheet, a repeated lines
        unit's `cited sheets:`, a review's `pages opened:`), or where a review's `verify:` line
        carries no `questionsAlone`. It prints `verified <unit> result ok` or `verified <unit>
        result mismatch: <the first reason>`, then the line `next` prints for the unit after it.
        Run again after an interruption, it writes nothing it already wrote; once the unit's
        `verified` line stands, it writes nothing at all.

The names match is exact: two names are one where they read the same lowercased with punctuation
taken out. A name written two ways is no overlap here, and is the reviewer's to find.

Exit codes:
  0  the line or lines above printed.
  1  a named failure, one line on stderr, nothing written: no read plan, a plan of another window,
     no block for the pass, a block over twelve units, a unit the block does not carry, a ledger
     line in none of the three shapes, no report file, an answer that is not a JSON object with a
     whole number `entryCount` and a `result`, a `--stopped` unit that is not the one `next` takes,
     carries no `dispatch` line or has its report on file.
  2  argparse rejected the invocation.

Grounding role: reads files and copies values. Nothing here fills a gap: a report that does not
read is a mismatch named in its reason, never a figure guessed.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

# The read plan's reader and the ledger grammar are the summary script's own, so the three scripts
# read a pass one way.
sys.path.insert(0, str(Path(__file__).resolve().parent))
import pass_summary  # noqa: E402
import plan_inventory  # noqa: E402

REPORTS_FOLDER = pass_summary.REPORTS_FOLDER
LEDGER_FILE = "ledger.md"
PLAN_FILE = "read-plan.md"

# The most units one runner supervises.
UNITS_PER_PASS = 12

# What one `verify_unit` call with claims takes.
SHEETS_PER_CALL = 60

# The claims `verify_unit` reads, each with what one call takes. The reader's `verify:` line is
# these keys and nothing else.
CLAIM_CAPS = {
    "updatedSubjects": 500,
    "pageCitations": 200,
    "manualUpdates": 200,
    "questionsRaised": 100,
    "questionsReplied": 100,
    "questionsLinked": 100,
    "questionsAlone": 100,
}
LINKED_SUBJECTS_CAP = 50

# The labels of each report shape. A line opening with one starts that field; any other line goes
# on under the field before it.
READER_LABELS = (
    "unit", "pages read", "pages unread", "cited sheets", "set version", "created", "verify",
    "created names", "sent", "trades", "definitions kinds added", "sheet readings written",
    "anomalies", "grain questions", "door-owned suggestions",
)
REVIEWER_LABELS = (
    "unit", "harvested", "notes read", "searches", "terms too general", "pages opened", "created",
    "verify", "created names", "sent", "trades", "sheet readings written", "anomalies",
    "grain questions", "silent sections", "unspecified work", "compared", "sections not checked",
    "families not checked", "door-owned suggestions",
)

MAX_DEVIATIONS = 5
CLAUSE_CAP = 200

STOPPED_ONCE = "reader stopped answering, read again once"
STOPPED_TWICE = "reader stopped answering twice"

_SHEET_LINE_RE = re.compile(
    r"^(?P<unit>\S+-[1-9][0-9]*)\. (?P<sheet>.+?), (?:file (?P<file>\S+), )?page (?P<page>[0-9]+)"
    r"(?:, opens as (?P<opens>\S+))?: (?P<rest>.*)$"
)
_REPEATED_LINE_RE = re.compile(
    r"^(?P<unit>\S+-[1-9][0-9]*)\. file (?P<file>\S+), from page (?P<page>[0-9]+): repeated lines"
    r"(?:, sheets left out (?P<left>.*))?$"
)
_REVIEW_LINE_RE = re.compile(
    r"^[1-9][0-9]*\. (?P<unit>\S+): (?P<name>.*), trade (?P<trade>.+?), package (?P<package>\(no id\)|\S+)"
    r"(?:, continues (?P<continues>\S+), sections (?P<sections>.*))?$"
)
_IN_SET_RE = re.compile(re.escape(plan_inventory.REPEATED_MARK) + r" in set (\S+)$")
_WHOLE_RE = re.compile(r"[0-9]+")
_COUNTS_RE = re.compile(
    r"^created: ([0-9]+)\s+updated: ([0-9]+)\s+questions raised: ([0-9]+)\s+questions replied: ([0-9]+)$"
)
_NOT_LISTED_RE = re.compile(r"^([0-9]+) blocks, ([0-9]+) lines not listed, (.+)$")
_FILE_UNREAD_RE = re.compile(r"^file (\S+?)[:,]? (.+)$")
_PAGE_RE = re.compile(r"^p[0-9]+$")


class UnitError(Exception):
    """A named failure with a one-line reason, reported on stderr and exiting 1."""


# --------------------------------------------------------------------------- #
# The read plan
# --------------------------------------------------------------------------- #

def read_block(folder: Path, window: int, pass_id: str) -> tuple[dict, list[dict]]:
    """
    The pass's plan block, read by the summary script's reader, and each unit's line read into its
    fields, in the block's order.
    """
    path = folder / PLAN_FILE
    try:
        plan = pass_summary.read_plan(path, window, pass_id)
    except pass_summary.SummaryError as e:
        raise UnitError(str(e)) from None
    if len(plan["units"]) > UNITS_PER_PASS:
        raise UnitError(
            f"{path}: pass {pass_id} carries {len(plan['units'])} units, more than the twelve one "
            f"runner supervises; the plan is wrong, so nothing is dispatched"
        )
    lines = path.read_text(encoding="utf-8").splitlines()
    found = False
    by_unit: dict[str, dict] = {}
    for line in lines:
        if line.strip() == pass_summary._LEFT_OUT_HEADING:
            break
        heading = pass_summary._PASS_HEADING_RE.match(line)
        if heading:
            if found:
                break
            found = heading.group(1) == pass_id
            continue
        if found:
            unit = _unit_fields(line, window)
            if unit is not None:
                by_unit[unit["unit"]] = unit
    units = []
    for unit_id in plan["units"]:
        if unit_id not in by_unit:
            raise UnitError(f"{path}: pass {pass_id}'s unit line for {unit_id} is in no shape this script reads")
        units.append(by_unit[unit_id])
    return plan, units


def _unit_fields(line: str, window: int) -> dict | None:
    """One plan unit line's fields, or None where the line is no unit line."""
    line = line.removesuffix(" verified")
    if window == 3:
        match = _REVIEW_LINE_RE.match(line)
        if match is None:
            return None
        return {"kind": "review", **match.groupdict()}
    match = _REPEATED_LINE_RE.match(line)
    if match is not None:
        left = [s.strip() for s in (match.group("left") or "").split(",") if s.strip()]
        return {
            "kind": "repeated", "unit": match.group("unit"), "file": match.group("file"),
            "page": match.group("page"), "left": left,
        }
    match = _SHEET_LINE_RE.match(line)
    if match is None:
        return None
    in_set = _IN_SET_RE.search(match.group("rest"))
    return {
        "kind": "sheet", "unit": match.group("unit"), "sheet": match.group("sheet"),
        "file": match.group("file"), "page": match.group("page"), "opens": match.group("opens"),
        "set": in_set.group(1) if in_set else None,
    }


# --------------------------------------------------------------------------- #
# The ledger
# --------------------------------------------------------------------------- #

def read_ledger(path: Path, window: int, members: set[str]) -> dict:
    """
    This window's lines for the units the block carries, whatever pass they name: each unit's
    lines in file order and its `verified` line read into fields. A line in none of the three
    shapes is refused, as the summary script refuses it.
    """
    lines: list[str] = []
    if path.is_file():
        try:
            lines = path.read_text(encoding="utf-8").splitlines()
        except Exception as e:
            raise UnitError(f"cannot read the ledger at {path}: {e}") from e
    by_unit: dict[str, list[str]] = {unit: [] for unit in members}
    verified: dict[str, dict] = {}
    for number, raw in enumerate(lines, 1):
        line = raw.strip()
        if not line:
            continue
        parts = line.split()
        if parts[0].endswith(":"):
            continue
        where = f"{path} line {number}"
        if parts[0] not in ("dispatch", "verified", "note"):
            raise UnitError(f"{where}: the line starts with {parts[0]!r}, which is none of the three shapes the ledger holds")
        if len(parts) < 4:
            raise UnitError(f"{where}: the {parts[0]} line names no window, pass and unit")
        if parts[1] != str(window) or parts[3] not in members:
            continue
        by_unit[parts[3]].append(line)
        if parts[0] == "verified":
            try:
                verified[parts[3]] = pass_summary._read_verified(parts, where)
            except pass_summary.SummaryError as e:
                raise UnitError(str(e)) from None
    return {"lines": lines, "byUnit": by_unit, "verified": verified}


def _append(path: Path, new_lines: list[str]) -> None:
    """Append lines in one write, each ended with a newline, after one where the file lacks it."""
    if not new_lines:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = "".join(f"{line}\n" for line in new_lines)
    if path.is_file():
        existing = path.read_bytes()
        if existing and not existing.endswith(b"\n"):
            payload = "\n" + payload
    try:
        with path.open("ab") as handle:
            handle.write(payload.encode("utf-8"))
    except OSError as e:
        raise UnitError(f"cannot append to {path}: {e}") from e


# --------------------------------------------------------------------------- #
# next
# --------------------------------------------------------------------------- #

def _dispatch_line(window: int, pass_id: str, unit: dict, reads_for: str) -> str:
    head = f"dispatch {window} {pass_id} {unit['unit']} sheets"
    if unit["kind"] == "repeated":
        return f"{head} none purpose repeated lines of file {unit['file']}"
    if unit["kind"] == "review":
        if unit["continues"]:
            return f"{head} none purpose continue the {unit['name']} manual sections"
        return f"{head} none purpose review the {unit['name']} package"
    # A further page is named by the key it opens as, since its number names its first page.
    return f"{head} {unit['opens'] or unit['sheet']} purpose {reads_for}"


def _next_line(unit: dict) -> str:
    if unit["kind"] == "review":
        line = f"next: {unit['unit']} package {unit['package']} trade {unit['trade']}"
        if unit["continues"]:
            line += f" continues {unit['continues']} sections {unit['sections']}"
        return line
    if unit["kind"] == "repeated":
        left = ", ".join(unit["left"]) if unit["left"] else "none"
        return (
            f"next: {unit['unit']} sheet none file {unit['file']} page {unit['page']} opens as none "
            f"repeated not read left out {left}"
        )
    repeated = f"read in set {unit['set']}" if unit["set"] else "not read"
    return (
        f"next: {unit['unit']} sheet {unit['sheet']} file {unit['file'] or 'none'} page "
        f"{unit['page']} opens as {unit['opens'] or 'none'} repeated {repeated} left out none"
    )


def _sheet_named(unit: dict) -> str:
    """What a stopped reader's notes name the unit's page by."""
    if unit["kind"] == "repeated":
        return f"file {unit['file']}"
    if unit["kind"] == "review":
        return f"package {unit['package']}"
    return unit["opens"] or unit["sheet"]


def _first_open(units: list[dict], ledger: dict) -> dict | None:
    for unit in units:
        entry = ledger["verified"].get(unit["unit"])
        if entry is None or entry["result"] != "ok":
            return unit
    return None


def _pending(folder: Path, window: int, pass_id: str) -> None:
    """
    In window 3, bind every continuation the pass is owed and append the `unread section` notes a
    full pass is owed, through the plan script's own code, before a unit is chosen.
    """
    try:
        said = plan_inventory.continue_pending(folder, pass_id)
    except plan_inventory.PlanError as e:
        raise UnitError(f"binding the pass's continuations: {e}") from None
    ledger = folder / LEDGER_FILE
    have = ledger.read_text(encoding="utf-8").splitlines() if ledger.is_file() else []
    _append(ledger, [line for line in said if line.startswith("note ") and line not in have])


def next_unit(folder: Path, window: int, pass_id: str, stopped: str | None = None) -> list[str]:
    plan, units = read_block(folder, window, pass_id)
    if window == 3:
        _pending(folder, window, pass_id)
        plan, units = read_block(folder, window, pass_id)
    ledger_path = folder / LEDGER_FILE
    ledger = read_ledger(ledger_path, window, set(plan["units"]))
    unit = _first_open(units, ledger)
    prefix = f"note {window} {pass_id}"

    if stopped is not None:
        if unit is None or unit["unit"] != stopped:
            raise UnitError(
                f"{stopped} is not the unit this pass reads next "
                f"({unit['unit'] if unit else 'none, every unit verified'}), so no stopped reader is noted"
            )
        lines = ledger["byUnit"][stopped]
        if not any(line.startswith(f"dispatch {window} ") for line in lines):
            raise UnitError(f"{stopped} carries no dispatch line on {ledger_path}, so no reader of it stopped")
        report = folder / REPORTS_FOLDER / f"{stopped}.md"
        if report.is_file():
            raise UnitError(f"{report} is on file; verify the unit off it and record it")
        once = sum(1 for line in lines if line.startswith("note ") and line.endswith(STOPPED_ONCE))
        twice = any(line.startswith("note ") and line.endswith(STOPPED_TWICE) for line in lines)
        named = _sheet_named(unit)
        if once == 0:
            _append(ledger_path, [f"{prefix} {stopped} deviation {named} {STOPPED_ONCE}"])
        else:
            if not twice:
                _append(ledger_path, [f"{prefix} {stopped} unread {named} {STOPPED_TWICE}"])
            return [f"stop: {stopped} {STOPPED_TWICE}"]
        ledger = read_ledger(ledger_path, window, set(plan["units"]))

    if unit is None:
        return ["next: none"]
    lines = ledger["byUnit"][unit["unit"]]
    if unit["unit"] in ledger["verified"]:
        return [f"stop: {unit['unit']} stands verified as a mismatch"]
    if any(line.startswith("note ") and line.endswith(STOPPED_TWICE) for line in lines):
        return [f"stop: {unit['unit']} {STOPPED_TWICE}"]
    # A unit whose last line is its dispatch is dispatched and not yet back, so a `next` run again
    # appends nothing.
    if not lines or not lines[-1].startswith("dispatch "):
        _append(ledger_path, [_dispatch_line(window, pass_id, unit, plan["fields"].get("reads for", ""))])
    return [_next_line(unit)]


# --------------------------------------------------------------------------- #
# The report
# --------------------------------------------------------------------------- #

def read_report(path: Path, labels: tuple[str, ...]) -> dict[str, list[str]]:
    """
    Each field of a report as its entries: the rest of the label's own line where it carries any,
    then each line under it up to the next label, a leading `- ` taken off. A field reading `none`
    has no entries.
    """
    try:
        text = path.read_text(encoding="utf-8")
    except Exception as e:
        raise UnitError(f"cannot read the report at {path}: {e}") from e
    ordered = sorted(labels, key=len, reverse=True)
    fields: dict[str, list[str]] = {}
    current: str | None = None
    for raw in text.splitlines():
        line = raw.strip()
        if not line:
            continue
        label = next((l for l in ordered if line == f"{l}:" or line.startswith(f"{l}: ")), None)
        if label is not None:
            current = label
            fields.setdefault(label, [])
            rest = line[len(label) + 1:].strip()
            if rest:
                fields[label].append(rest)
            continue
        if current is not None:
            fields[current].append(line.removeprefix("- ").strip())
    for label, entries in fields.items():
        if [entry.lower() for entry in entries] == ["none"]:
            fields[label] = []
    return fields


def _first_whole(text: str) -> int | None:
    match = _WHOLE_RE.search(text)
    return int(match.group(0)) if match else None


def _inline(fields: dict[str, list[str]], label: str, name: str) -> str | None:
    """The value of `name:` on the line a label opens, up to the next run of three spaces."""
    entries = fields.get(label)
    if not entries:
        return None
    line = f"{label}: {entries[0]}"
    match = re.search(rf"(?:^|\s){re.escape(name)}: (.*?)(?:\s{{3,}}|$)", line)
    return match.group(1).strip() if match else None


def parse_claims(text: str | None, window: int) -> tuple[dict | None, str | None]:
    """The `verify:` line's claims, or the one reason it does not read."""
    if text is None:
        return None, "the report carries no `verify:` line"
    try:
        claims = json.loads(text)
    except json.JSONDecodeError as e:
        return None, f"the `verify:` line is not one line of JSON ({e.msg})"
    if not isinstance(claims, dict):
        return None, "the `verify:` line is not a JSON object"
    for key, value in claims.items():
        if key not in CLAIM_CAPS:
            return None, f"the `verify:` line carries `{key}`, which is no claim the call reads"
        if not isinstance(value, list):
            return None, f"the `verify:` line's `{key}` is not a list"
        if len(value) > CLAIM_CAPS[key]:
            return None, f"the `verify:` line's `{key}` holds {len(value)}, over the {CLAIM_CAPS[key]} one call takes"
        for item in value:
            reason = _claim_item(key, item)
            if reason:
                return None, f"the `verify:` line's `{key}` holds {reason}"
    if window == 3 and "questionsAlone" not in claims:
        return None, "a review's `verify:` line carries no `questionsAlone`, empty where every Question is on a row"
    return claims, None


def _claim_item(key: str, item) -> str | None:
    """Why one item of a claims list is not in its shape, or None."""
    def text(value) -> bool:
        return isinstance(value, str) and bool(value.strip())

    def page(value) -> bool:
        return isinstance(value, int) and not isinstance(value, bool) and value >= 1

    if key in ("updatedSubjects", "questionsRaised", "questionsReplied", "questionsAlone"):
        return None if text(item) else "an item that is not an id"
    if not isinstance(item, dict):
        return "an item that is not an object"
    if key == "pageCitations":
        if set(item) != {"subject", "fileId", "pageInPdf"}:
            return "an item whose keys are not `subject`, `fileId` and `pageInPdf`"
        ok = text(item["subject"]) and text(item["fileId"]) and page(item["pageInPdf"])
        return None if ok else "an item with an empty subject or file or a page that is not a whole number"
    if key == "manualUpdates":
        if not {"subject", "specSection", "pageInPdf"} <= set(item) <= {"subject", "specSection", "pageInPdf", "fileId"}:
            return "an item whose keys are not `subject`, `specSection`, `pageInPdf` and an optional `fileId`"
        ok = text(item["subject"]) and text(item["specSection"]) and page(item["pageInPdf"])
        ok = ok and ("fileId" not in item or text(item["fileId"]))
        return None if ok else "an item with an empty subject or section or a page that is not a whole number"
    # questionsLinked
    if set(item) != {"question", "subjects"}:
        return "an item whose keys are not `question` and `subjects`"
    subjects = item["subjects"]
    if not text(item["question"]) or not isinstance(subjects, list) or not subjects:
        return "an item with no Question id or no subjects"
    if len(subjects) > LINKED_SUBJECTS_CAP:
        return f"an item naming {len(subjects)} subjects, over the {LINKED_SUBJECTS_CAP} one call takes"
    return None if all(text(s) for s in subjects) else "an item with a subject that is not a subject"


def _named_updates(claims: dict) -> int:
    """The distinct subjects the claims name as updated, page cited or written off manual pages."""
    subjects = set(claims.get("updatedSubjects", []))
    subjects |= {item["subject"] for item in claims.get("pageCitations", [])}
    subjects |= {item["subject"] for item in claims.get("manualUpdates", [])}
    return len(subjects)


# --------------------------------------------------------------------------- #
# The sheets the call had to carry
# --------------------------------------------------------------------------- #

def expected_sheets(unit: dict, fields: dict[str, list[str]]) -> tuple[list[tuple[str, str | None]], str | None]:
    """
    The sheets the unit's `verify_unit` call had to name, each with its file where the unit names
    one: a sheet unit's own number, a repeated lines unit's `cited sheets:` on its file, and the
    sheet pages on a review's `pages opened:`. A manual page, a line naming `section <code>`, is no
    sheet. Returns the reason where a line does not read.
    """
    if unit["kind"] == "sheet":
        return [(unit["sheet"], unit["file"])], None
    if unit["kind"] == "repeated":
        sheets: list[tuple[str, str | None]] = []
        for entry in fields.get("cited sheets", []):
            for sheet in entry.split(","):
                if sheet.strip() and (sheet.strip(), unit["file"]) not in sheets:
                    sheets.append((sheet.strip(), unit["file"]))
        return sheets, None
    sheets = []
    for entry in fields.get("pages opened", []):
        words = entry.split()
        if words and words[0] == "section":
            continue
        if len(words) < 3 or not _PAGE_RE.match(words[2]):
            return sheets, f"the `pages opened:` line `{entry[:80]}` names no sheet, file and page"
        if (words[0], words[1]) not in sheets:
            sheets.append((words[0], words[1]))
    return sheets, None


def _missing_sheets(expected: list[tuple[str, str | None]], answer: dict) -> list[str]:
    rows = answer.get("sheets") if isinstance(answer.get("sheets"), list) else []
    have = {
        (row.get("sheet"), row.get("fileId")) for row in rows if isinstance(row, dict)
    }
    have_sheet = {sheet for sheet, _file in have}
    missing = []
    for sheet, file_id in expected:
        if (file_id is not None and (sheet, file_id) not in have) or (file_id is None and sheet not in have_sheet):
            missing.append(f"{sheet} on {file_id}" if file_id else sheet)
    return missing


# --------------------------------------------------------------------------- #
# record
# --------------------------------------------------------------------------- #

def read_answer(text: str) -> dict:
    try:
        answer = json.loads(text)
    except json.JSONDecodeError as e:
        raise UnitError(f"the answer on stdin is not JSON ({e.msg}); pass the verify_unit answer as it came back") from None
    if not isinstance(answer, dict):
        raise UnitError("the answer on stdin is not a JSON object; pass the verify_unit answer as it came back")
    count = answer.get("entryCount")
    if not isinstance(count, int) or isinstance(count, bool) or count < 0:
        raise UnitError("the answer on stdin carries no whole number `entryCount`, so it is no verify_unit answer")
    if answer.get("result") not in ("ok", "mismatch"):
        raise UnitError("the answer on stdin carries no `result` of ok or mismatch; send the call with the report's claims")
    return answer


def _clause(text: str) -> str:
    return text if len(text) <= CLAUSE_CAP else text[: CLAUSE_CAP - 3] + "..."


def _normal(name: str) -> str:
    return " ".join(re.sub(r"[^\w\s]", "", name.lower()).split())


def _file_lines(path: Path) -> list[str]:
    if not path.is_file():
        return []
    try:
        return path.read_text(encoding="utf-8").splitlines()
    except Exception as e:
        raise UnitError(f"cannot read {path}: {e}") from e


def assess(unit: dict, fields: dict[str, list[str]], answer: dict, window: int, unit_id: str) -> dict:
    """Every figure and reason the unit's lines carry, worked out before anything is written."""
    reasons: list[str] = []
    deviations: list[str] = []

    head = (fields.get("unit") or [""])[0]
    if not head.startswith(f"{unit_id} ") and head != unit_id:
        reasons.append(f"the report opens with `unit: {head[:60]}`, not with unit {unit_id}")

    claims, claims_reason = parse_claims((fields.get("verify") or [None])[0], window)
    if claims_reason:
        reasons.append(claims_reason)

    if answer["result"] != "ok":
        rows = answer.get("mismatches") if isinstance(answer.get("mismatches"), list) else []
        named = [
            f"verify {row.get('check')} {row.get('value')}: {row.get('reason')}"
            for row in rows if isinstance(row, dict)
        ]
        reasons.extend(named or ["the answer reads mismatch and names none"])
        deviations.extend(named[:MAX_DEVIATIONS])

    checked = answer.get("checked")
    if claims is not None:
        if not isinstance(checked, dict):
            reasons.append("the answer carries no `checked` counts, so the claims were not sent")
        else:
            for key in CLAIM_CAPS:
                want = len(claims.get(key, []))
                got = checked.get(key, 0)
                if got != want:
                    reasons.append(f"the call checked {got} of `{key}` where the report names {want}")

    expected, sheets_reason = expected_sheets(unit, fields)
    if sheets_reason:
        reasons.append(sheets_reason)
    if len(expected) > SHEETS_PER_CALL:
        reasons.append(f"the unit names {len(expected)} sheets, over the {SHEETS_PER_CALL} one call checks")
        deviations.append(f"verify sheets cut at {SHEETS_PER_CALL} of {len(expected)}")
    else:
        missing = _missing_sheets(expected, answer)
        if missing:
            reasons.append(f"the call left out {pass_summary._named(missing)}")

    counts = _COUNTS_RE.match(f"created: {(fields.get('created') or [''])[0]}")
    if counts is None:
        reasons.append("the report's `created:` line does not read as its four counts")
    items, updated_counted, raised_counted, replied_counted = (
        (int(g) for g in counts.groups()) if counts else (0, None, None, None)
    )
    figures = {}
    for name in ("sent", "landed"):
        value = _inline(fields, "sent", name)
        number = _first_whole(value) if value is not None else None
        if number is None:
            reasons.append(f"the report's `{name}:` field carries no whole number")
        figures[name] = number or 0
    conflicts_text = _inline(fields, "sent", "conflicts")
    if conflicts_text is not None and conflicts_text.lower() == "none":
        figures["conflicts"] = 0
    elif conflicts_text is not None and re.match(r"^[0-9]+\b", conflicts_text):
        figures["conflicts"] = int(re.match(r"^[0-9]+", conflicts_text).group(0))
    else:
        reasons.append("the report's `conflicts:` field opens with no count")
        figures["conflicts"] = 0

    named_updates = _named_updates(claims) if claims else 0
    raised = len(claims.get("questionsRaised", [])) if claims else 0
    replied = len(claims.get("questionsReplied", [])) if claims else 0
    drift = []
    if claims is not None and counts is not None:
        for what, counted, named in (
            ("updated", updated_counted, named_updates),
            ("questions raised", raised_counted, raised),
            ("questions replied", replied_counted, replied),
        ):
            if counted != named:
                drift.append(f"deviation reader counted {what} {counted}, named {named}")

    names_entry = (fields.get("created names") or ["[]"])[0]
    try:
        names = json.loads(names_entry)
        if not isinstance(names, list) or not all(isinstance(n, str) and n.strip() for n in names):
            raise ValueError
    except (json.JSONDecodeError, ValueError):
        names = []
        drift.append("deviation the report's created names line does not read as a list, no name matched")
    if counts is not None and names and len(names) != items:
        drift.append(f"deviation reader counted created {items}, named {len(names)}")

    return {
        "reasons": reasons,
        "deviations": deviations[:MAX_DEVIATIONS],
        "drift": drift,
        "names": [n.strip() for n in names],
        "figures": {
            "created": answer["entryCount"], "items": items, "updated": named_updates,
            "questions": raised, "replied": replied, **figures,
        },
    }


def _repeated_notes(unit: dict, fields: dict[str, list[str]]) -> list[str]:
    """A repeated lines unit's `set` or `unread` notes, off its `set version:` and `pages unread:`."""
    notes: list[str] = []
    file_unread = None
    for entry in fields.get("pages unread", []):
        not_listed = _NOT_LISTED_RE.match(entry)
        if not_listed:
            blocks, lines, why = not_listed.groups()
            notes.append(f"unread file {unit['file']} {blocks} blocks {lines} lines not listed, {why}")
            continue
        named = _FILE_UNREAD_RE.match(entry)
        if named and named.group(1) == unit["file"]:
            file_unread = named.group(2)
    if file_unread is not None:
        return [f"unread file {unit['file']} repeated lines not read, {file_unread}"] + notes
    version = (fields.get("set version") or [None])[0]
    if version and re.fullmatch(r"\S+", version):
        return [f"set {version} file {unit['file']}"] + notes
    return [f"deviation {unit['file']} the report names no set version, so its sheets are read whole"] + notes


def record_unit(folder: Path, window: int, pass_id: str, unit_id: str, answer_text: str) -> list[str]:
    plan, units = read_block(folder, window, pass_id)
    unit = next((u for u in units if u["unit"] == unit_id), None)
    if unit is None:
        raise UnitError(f"pass {pass_id}'s block in {folder / PLAN_FILE} carries no unit {unit_id}")
    report = folder / REPORTS_FOLDER / f"{unit_id}.md"
    if not report.is_file():
        raise UnitError(f"no report at {report}; a unit with no report is read again")
    answer = read_answer(answer_text)
    fields = read_report(report, REVIEWER_LABELS if window == 3 else READER_LABELS)
    ledger_path = folder / LEDGER_FILE
    ledger = read_ledger(ledger_path, window, set(plan["units"]))
    seen = assess(unit, fields, answer, window, unit_id)
    result = "mismatch" if seen["reasons"] else "ok"
    said = f"verified {unit_id} result {result}" + (f": {seen['reasons'][0]}" if seen["reasons"] else "")

    if unit_id in ledger["verified"]:
        # The unit's lines are complete; nothing is written again.
        return [said, *next_unit(folder, window, pass_id)]

    # 1. Names, the whole unit at once.
    names_path = folder / "names" / f"{pass_id}.txt"
    names_lines = _file_lines(names_path)
    others = [line.split("\t", 1) for line in names_lines if "\t" in line]
    if not any(owner == unit_id for _name, owner in others):
        _append(names_path, [f"{name}\t{unit_id}" for name in seen["names"]])

    # 2. Kinds, each once.
    kinds_path = folder / "kinds" / f"{pass_id}.txt"
    have_kinds = set(_file_lines(kinds_path))
    kinds: list[str] = []
    for entry in fields.get("definitions kinds added", []):
        for kind in re.split(r"[,\s]+", entry):
            if kind and kind not in have_kinds and kind not in kinds:
                kinds.append(kind)
    _append(kinds_path, kinds)

    # 3. Trades, the whole unit at once.
    trades_path = folder / "trades" / f"{pass_id}.txt"
    if not any(line.split(" ", 1)[0] == unit_id for line in _file_lines(trades_path)):
        trade_lines = [
            f"{unit_id} trade {row['trade']} {row['count']}"
            for row in answer.get("trades") or []
            if isinstance(row, dict) and row.get("trade") and isinstance(row.get("count"), int)
        ]
        candidates = answer.get("candidates")
        trade_lines.append(f"{unit_id} candidates {candidates if isinstance(candidates, int) else 0}")
        trade_lines += [f"{unit_id} touched {trade}" for trade in answer.get("tradesTouched") or [] if trade]
        _append(trades_path, trade_lines)

    # 4. Notes, each as often as this unit's lines carry it and the ledger does not yet.
    prefix = f"note {window} {pass_id} {unit_id}"
    notes = [f"{prefix} anomaly {line}" for line in fields.get("anomalies", [])]
    notes += [f"{prefix} grain {line}" for line in fields.get("grain questions", [])]
    notes += [f"{prefix} door {line}" for line in fields.get("door-owned suggestions", [])]
    if unit["kind"] == "repeated":
        notes += [f"{prefix} {_clause(note)}" for note in _repeated_notes(unit, fields)]
    notes += [f"{prefix} {_clause(note)}" for note in seen["drift"]]
    earlier: dict[str, str] = {}
    for name, owner in others:
        if owner != unit_id:
            earlier.setdefault(_normal(name), owner)
    matched: set[str] = set()
    for name in seen["names"]:
        key = _normal(name)
        if key in earlier and key not in matched:
            matched.add(key)
            notes.append(f"{prefix} overlap {_clause(f'{name} ({earlier[key]}, {unit_id})')}")
    notes += [f"{prefix} deviation {_clause(line)}" for line in seen["deviations"]]
    on_ledger = list(ledger["byUnit"][unit_id])
    to_write: list[str] = []
    for note in notes:
        if note in on_ledger:
            on_ledger.remove(note)
        else:
            to_write.append(note)

    # 5. The verified line, last.
    f = seen["figures"]
    to_write.append(
        f"verified {window} {pass_id} {unit_id} created {f['created']} items {f['items']} updated "
        f"{f['updated']} questions {f['questions']} replied {f['replied']} sent {f['sent']} landed "
        f"{f['landed']} conflicts {f['conflicts']} result {result}"
    )
    _append(ledger_path, to_write)
    return [said, *next_unit(folder, window, pass_id)]


# --------------------------------------------------------------------------- #
# Entry point
# --------------------------------------------------------------------------- #

def main(argv: list[str] | None = None, stdin: str | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="A pass runner's bookkeeping for one unit at a time.",
    )
    sub = parser.add_subparsers(dest="mode", required=True)
    for mode in ("next", "record"):
        command = sub.add_parser(mode)
        command.add_argument("folder", type=Path, help="the run folder")
        command.add_argument("--window", type=int, required=True, choices=(1, 2, 3))
        command.add_argument("--pass", dest="pass_id", required=True, help="the pass id the plan gives")
        if mode == "next":
            command.add_argument("--stopped", help="the unit whose reader stopped answering and left no report")
        else:
            command.add_argument("--unit", required=True, help="the unit whose report and answer to record")
    args = parser.parse_args(argv)

    try:
        if not args.folder.is_dir():
            raise UnitError(f"no run folder at {args.folder}")
        if args.pass_id.startswith("review-"):
            raise UnitError(f"`{args.pass_id}` names the mode; give the bare pass id the plan gives")
        if args.mode == "next":
            lines = next_unit(args.folder, args.window, args.pass_id, args.stopped)
        else:
            text = stdin if stdin is not None else sys.stdin.buffer.read().decode("utf-8")
            lines = record_unit(args.folder, args.window, args.pass_id, args.unit, text)
    except UnitError as e:
        print(f"runner_unit: {e}", file=sys.stderr)
        return 1
    for line in lines:
        print(line)
    return 0


if __name__ == "__main__":
    sys.exit(main())
