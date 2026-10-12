"""
pass_summary.py: sum one pass of a scope run off the run ledger, into the pass summary shape.

A pass runner verifies each unit against the record and appends that unit's `verified` line to the
ledger as it goes. Everything the pass summary says about counts is already on those lines, so the
runner does not add them up a second time: it runs this script, writes what comes back, and stops.
A number worked out beside the ledger is a second answer to a settled question, and on a real run
the two answers differed.

The script copies fields and adds them. It reads no record, opens no page, and judges nothing. The
three runner line shapes are the whole grammar it knows:

    dispatch <window> <pass> <unit> sheets <sheet numbers, comma separated> purpose <words>
    verified <window> <pass> <unit> created <n> items <n> updated <n> questions <n> replied <n> sent <n> landed <n> conflicts <n> result <ok|mismatch>
    note <window> <pass> <unit-or-dash> <kind> <one clause>

The lead's own lines (`dispatch:`, `pass:`, `phase:`) carry a colon after the keyword and are
skipped by it, so a lead figure can never reach these totals.

Which lines are the pass's own comes off the read plan, not off the pass field. A replan can fold a
discipline's part into another pass, and a unit the runner already verified under the part's own
pass id keeps its unit id and its `verified` line, and is skipped rather than read again. So the
script reads the pass's block in the read plan, and counts every line of this window whose unit
the block carries, whatever pass the line names, each unit verified once. A note on no unit (`-`)
counts when it names this pass or a part the block's `folded in:` line names. A line naming this
pass for a unit the block no longer carries reaches no total and is named on the bounds line.

Usage:

    python pass_summary.py <run folder>/ledger.md <window> <pass id> --plan <read plan>
        [--trades <path>]

The two streams differ from the plan script's on purpose, and the difference is the point: here
stdout is the deliverable, so it carries the summary and nothing else and the runner pastes it
whole. The bounds line saying what was read goes to stderr beside it.

  --plan    the read plan the pass runs off, `<run folder>/read-plan.md`. The pass's block there
            lists the units it carries, under a heading `### <pass id>. <name>`, one unit line each:
            `<unit id>. <sheet number>, ...` in windows 1 and 2, `<n>. <unit id>: <name>` in window
            3, where the unit id is the pass id.

  --trades  the pass's own trades file, `<run folder>/trades/<pass id>.txt`, which the runner
            appends a unit at a time off its `verify_unit` results:

                <unit id> trade <catalog id> <count>
                <unit id> candidates <count>

            A catalog id carries spaces, so the count is read off the end of the line. Without this
            argument the `trades:` line says there is no trades file, which is a plain statement
            rather than a guess. `candidates <n>` is the created subjects carrying at least one
            candidate trade, each subject counted once however many candidate trades it carries.
            A unit's trades are read off the file of the pass its `verified` line names: this file
            for a unit verified under this pass, and `<pass id>.txt` beside it for a unit verified
            under another. A line here for a unit the summary does not count is named on the
            bounds line.

Exit codes:
  0  the summary on stdout, one bounds line on stderr.
  1  a named failure, one line on stderr: a read plan or ledger file that is not there, a read plan
     of another window, one with no block for the pass, or a block whose unit lines are not its
     `units:` count, a line whose first word is none of the three shapes, a `verified` line missing
     a field the shape names or carrying a count that is not a whole number, two `verified` lines
     for one unit under any passes, a `dispatch` line with no `sheets` field, a `note` line whose
     kind is outside the closed set, a pass with no lines at all, a trades file that is not there,
     or a trades file line in neither of its two shapes.
  2  argparse rejected the invocation, a summary with no read plan among them.

Grounding role: reads a file and copies byte values. Nothing here fills a gap. A unit dispatched
with no `verified` line prints its counts as a dash and is named on the bounds line; a note kind
the summary shape has no line for is counted on the bounds line rather than dropped in silence.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

# The closed set the runner definition declares, copied here so a kind added in one place and not
# the other is a refusal rather than a note with nowhere to go.
NOTE_KINDS = ("anomaly", "unread", "kinds", "deviation", "overlap", "grain", "door", "packet", "set")

# Which summary line each note kind lands on, one line per note. The `kinds` notes land too, as
# the union on the definitions line, so they are counted as placed alongside these four.
NOTE_LINES = {
    "overlap": "overlap notes",
    "anomaly": "anomalies",
    "unread": "unread pages",
    "deviation": "deviations and repairs",
}

KINDS_LINE = "definitions kinds added"

# The kinds `grain`, `door` and `packet` reach the lead in the unit reports and have no line in
# this shape, and `set` is the set version a repeated lines unit read, which the window 2 plan
# reads off the ledger. The bounds line counts them rather than letting a note land nowhere in
# silence.
PLACED_KINDS = set(NOTE_LINES) | {"kinds"}

# The `verified` line's count fields, in the order the shape names them.
VERIFIED_FIELDS = (
    "created", "items", "updated", "questions", "replied", "sent", "landed", "conflicts",
)

# The five that reach the summary. `sent`, `landed` and `conflicts` are read for the bounds line
# and for the conflicting rows line.
SUMMARY_FIELDS = ("created", "items", "updated", "questions", "replied")

MAX_NAMED = 5


class SummaryError(Exception):
    """A named failure with a one-line reason, reported on stderr and exiting 1."""


def _named(items: list[str]) -> str:
    """The first few offenders plus a count, so a refusal stays one line however many there are."""
    if len(items) <= MAX_NAMED:
        return ", ".join(items)
    return ", ".join(items[:MAX_NAMED]) + f", and {len(items) - MAX_NAMED} more"


def _whole_number(text: str, field: str, where: str) -> int:
    try:
        return int(text)
    except ValueError:
        raise SummaryError(
            f"{where}: `{field}` reads {text!r}, which is not a whole number; the summary adds "
            f"these up and will not guess at one"
        ) from None


# --------------------------------------------------------------------------- #
# Reading the read plan
# --------------------------------------------------------------------------- #

# The shapes plan_inventory.py writes. A sheet unit line leads with its unit id, a part id and a
# number; a review unit line leads with an ordinal and carries the unit id after it.
_PLAN_HEADER_RE = re.compile(r"^# Read plan: window ([1-9][0-9]*)$")
_PASS_HEADING_RE = re.compile(r"^### (\S+?)\.\s")
_SHEET_UNIT_RE = re.compile(r"^(\S+-[1-9][0-9]*)\. ")
_REVIEW_UNIT_RE = re.compile(r"^[1-9][0-9]*\. (\S+): ")
_PLAN_FIELD_RE = re.compile(r"^([a-z][a-z ]*): (.*)$")
# The left-out entries share the sheet unit line's shape behind a plain ordinal, and every planned
# block sits above them, so reading stops there.
_LEFT_OUT_HEADING = "## Deliberately left out"


def read_plan(path: Path, window: int, pass_id: str) -> dict:
    """The unit ids the pass's block carries, in the plan's order, and the parts it folded in."""
    if not path.is_file():
        raise SummaryError(f"no read plan at {path}")
    try:
        text = path.read_text(encoding="utf-8")
    except Exception as e:
        raise SummaryError(f"cannot read the read plan at {path}: {e}") from e

    lines = text.splitlines()
    first = next((line.strip() for line in lines if line.strip()), "")
    header = _PLAN_HEADER_RE.match(first)
    if header is None:
        raise SummaryError(f"{path} does not open with `# Read plan: window <n>`, so it is no read plan")
    if int(header.group(1)) != window:
        raise SummaryError(
            f"{path} is the read plan for window {header.group(1)}, and this summary is for window "
            f"{window}"
        )

    unit_re = _REVIEW_UNIT_RE if window == 3 else _SHEET_UNIT_RE
    found = False
    units: list[str] = []
    fields: dict[str, str] = {}
    for line in lines:
        if line.strip() == _LEFT_OUT_HEADING:
            break
        heading = _PASS_HEADING_RE.match(line)
        if heading:
            if found:
                break
            found = heading.group(1) == pass_id
            continue
        if not found:
            continue
        unit = unit_re.match(line)
        if unit:
            if unit.group(1) in units:
                raise SummaryError(f"{path}: pass {pass_id}'s block lists unit {unit.group(1)} twice")
            units.append(unit.group(1))
            continue
        field = _PLAN_FIELD_RE.match(line)
        if field:
            fields[field.group(1)] = field.group(2).strip()

    if not found:
        raise SummaryError(f"{path} carries no pass {pass_id} in window {window}")
    if "units" not in fields:
        raise SummaryError(f"{path}: pass {pass_id}'s block names no `units` line")
    if fields["units"] != str(len(units)):
        raise SummaryError(
            f"{path}: pass {pass_id}'s block names units {fields['units']} and lists "
            f"{len(units)} unit lines"
        )
    folded_in = [part.strip() for part in fields.get("folded in", "").split(",") if part.strip()]
    return {"path": path, "units": units, "foldedIn": folded_in}


# --------------------------------------------------------------------------- #
# Reading the ledger
# --------------------------------------------------------------------------- #

def _read_verified(parts: list[str], where: str) -> dict:
    """The keyword and value pairs of one `verified` line, every field the shape names required."""
    fields: dict[str, int] = {}
    rest = parts[4:]
    for field in VERIFIED_FIELDS:
        if field not in rest:
            raise SummaryError(f"{where}: the verified line names no `{field}` field")
        at = rest.index(field)
        if at + 1 >= len(rest):
            raise SummaryError(f"{where}: the verified line ends after `{field}` with no count")
        fields[field] = _whole_number(rest[at + 1], field, where)
    if "result" not in rest:
        raise SummaryError(f"{where}: the verified line names no `result` field")
    at = rest.index("result")
    if at + 1 >= len(rest):
        raise SummaryError(f"{where}: the verified line ends after `result` with no verdict")
    return {"unit": parts[3], "pass": parts[2], "fields": fields, "result": rest[at + 1]}


def read_pass(path: Path, window: int, pass_id: str, plan: dict) -> dict:
    """
    Every line of this window whose unit the pass's plan block carries, whatever pass it names, in
    file order, as the three shapes, plus each note on no unit that names this pass or a part it
    folded in. A line the grammar does not hold is a refusal rather than a line stepped over: the
    ledger is a fixed-shape log, and a line nobody can read is a line nobody is counting.
    """
    if not path.is_file():
        raise SummaryError(f"no ledger at {path}")
    try:
        text = path.read_text(encoding="utf-8")
    except Exception as e:
        raise SummaryError(f"cannot read the ledger at {path}: {e}") from e

    want_window = str(window)
    members = set(plan["units"])
    parts_named = {pass_id, *plan["foldedIn"]}
    dispatched: list[str] = []
    verified: list[dict] = []
    verified_units: dict[str, tuple[int, str]] = {}
    notes: list[dict] = []
    notes_by_kind: dict[str, int] = {kind: 0 for kind in NOTE_KINDS}
    left_behind: dict[str, int] = {}
    lead_lines = 0
    other_lines = 0
    total_lines = 0
    last_line = ""

    for number, raw in enumerate(text.splitlines(), 1):
        line = raw.strip()
        if not line:
            continue
        total_lines += 1
        parts = line.split()
        keyword = parts[0]
        if keyword.endswith(":"):
            lead_lines += 1
            continue
        where = f"{path} line {number}"
        if keyword not in ("dispatch", "verified", "note"):
            raise SummaryError(
                f"{where}: the line starts with {keyword!r}, which is none of the three shapes the "
                f"ledger holds"
            )
        if len(parts) < 4:
            raise SummaryError(f"{where}: the {keyword} line names no window, pass and unit")
        # A malformed line of another pass is still refused above, because the grammar is the
        # file's, not this pass's.
        unit = parts[3]
        if parts[1] != want_window:
            other_lines += 1
            continue
        if unit == "-":
            if parts[2] not in parts_named:
                other_lines += 1
                continue
        elif unit not in members:
            if parts[2] == pass_id:
                left_behind[unit] = left_behind.get(unit, 0) + 1
            else:
                other_lines += 1
            continue

        if keyword == "dispatch":
            if len(parts) < 5 or parts[4] != "sheets":
                raise SummaryError(f"{where}: the dispatch line names no `sheets` field")
            if unit not in dispatched:
                dispatched.append(unit)
        elif keyword == "verified":
            entry = _read_verified(parts, where)
            if unit in verified_units:
                at, under = verified_units[unit]
                raise SummaryError(
                    f"{where}: unit {unit} already carries a verified line at line {at}, under "
                    f"pass {under}; one unit is verified once"
                )
            verified_units[unit] = (number, parts[2])
            verified.append(entry)
        else:
            if len(parts) < 5:
                raise SummaryError(f"{where}: the note line carries no kind and no clause")
            kind = parts[4]
            if kind not in NOTE_KINDS:
                raise SummaryError(
                    f"{where}: `{kind}` is not one of the note kinds the ledger holds "
                    f"({', '.join(NOTE_KINDS)})"
                )
            notes_by_kind[kind] += 1
            notes.append({"unit": parts[3], "kind": kind, "clause": " ".join(parts[5:])})
        last_line = line

    if not dispatched and not verified and not notes:
        raise SummaryError(
            f"{path} carries no dispatch, verified or note line for window {window} pass {pass_id}"
        )

    return {
        "dispatched": dispatched,
        "verified": verified,
        "notes": notes,
        "notesByKind": notes_by_kind,
        "leftBehind": left_behind,
        "leadLines": lead_lines,
        "otherLines": other_lines,
        "totalLines": total_lines,
        "lastLine": last_line,
    }


# --------------------------------------------------------------------------- #
# The trades file
# --------------------------------------------------------------------------- #

def read_trades(path: Path) -> dict[str, list[tuple[str | None, int]]]:
    """
    One trades file, as each unit's lines: (catalog id, item count) for a trade line and (None,
    count) for its candidates line. A catalog id carries spaces, so the count is the last word of
    the line and the id is everything between the keyword and it.
    """
    if not path.is_file():
        raise SummaryError(f"no trades file at {path}")
    try:
        text = path.read_text(encoding="utf-8")
    except Exception as e:
        raise SummaryError(f"cannot read the trades file at {path}: {e}") from e

    by_unit: dict[str, list[tuple[str | None, int]]] = {}
    for number, raw in enumerate(text.splitlines(), 1):
        line = raw.strip()
        if not line:
            continue
        parts = line.split()
        where = f"{path} line {number}"
        if len(parts) >= 3 and parts[1] == "candidates":
            by_unit.setdefault(parts[0], []).append(
                (None, _whole_number(parts[2], "candidates", where))
            )
            continue
        if len(parts) >= 4 and parts[1] == "trade":
            by_unit.setdefault(parts[0], []).append(
                (" ".join(parts[2:-1]), _whole_number(parts[-1], "trade count", where))
            )
            continue
        raise SummaryError(
            f"{where}: the line is neither `<unit id> trade <catalog id> <count>` nor "
            f"`<unit id> candidates <count>`"
        )
    return by_unit


def sum_trades(pass_data: dict, pass_id: str, path: Path) -> tuple[dict[str, int], int, dict]:
    """
    The trades of every unit the summary counts, each read off the file of the pass its `verified`
    line names, plus what the bounds line says about the files: the other passes' files read and
    the lines of this file for a unit the summary does not count.
    """
    files: dict[Path, dict] = {path: read_trades(path)}
    by_trade: dict[str, int] = {}
    candidates = 0
    read_here: set[str] = set()
    for entry in pass_data["verified"]:
        source = path if entry["pass"] == pass_id else path.parent / f"{entry['pass']}.txt"
        if source not in files:
            files[source] = read_trades(source)
        if source == path:
            read_here.add(entry["unit"])
        for code, count in files[source].get(entry["unit"], []):
            if code is None:
                candidates += count
            else:
                by_trade[code] = by_trade.get(code, 0) + count
    left_out = {
        unit: len(lines) for unit, lines in files[path].items() if unit not in read_here
    }
    return by_trade, candidates, {
        "beside": [source for source in files if source != path],
        "leftOut": left_out,
    }


def _trades_line(by_trade: dict[str, int], candidates: int) -> str:
    """Ordered by item count, highest first, then by catalog id, so the reading is stable."""
    if not by_trade:
        return f"trades: no trade on any unit of this pass; candidates {candidates}"
    ordered = sorted(by_trade.items(), key=lambda pair: (-pair[1], pair[0]))
    return "trades: " + ", ".join(f"{code} x{count}" for code, count in ordered) + f"; candidates {candidates}"


# --------------------------------------------------------------------------- #
# The summary
# --------------------------------------------------------------------------- #

def summary_lines(pass_data: dict, window: int, pass_id: str, ledger: Path, trades_line: str) -> list[str]:
    by_unit = {entry["unit"]: entry for entry in pass_data["verified"]}
    # A unit verified with no dispatch line is still this pass's work, so it is read in the order
    # its verified line arrived rather than left out of the list.
    order = list(pass_data["dispatched"])
    for entry in pass_data["verified"]:
        if entry["unit"] not in order:
            order.append(entry["unit"])

    lines = [f"window: {window}   pass: {pass_id}"]
    lines.append("units read: " + (", ".join(order) if order else "none"))

    for unit in order:
        entry = by_unit.get(unit)
        if entry is None:
            counts = " ".join(f"{field} -" for field in SUMMARY_FIELDS)
            lines.append(f"per unit: {unit} {counts} verified no")
            continue
        counts = " ".join(f"{field} {entry['fields'][field]}" for field in SUMMARY_FIELDS)
        verdict = "yes" if entry["result"] == "ok" else "no"
        lines.append(f"per unit: {unit} {counts} verified {verdict}")

    totals = {
        field: sum(entry["fields"][field] for entry in pass_data["verified"])
        for field in VERIFIED_FIELDS
    }
    lines.append(
        f"totals verified: created {totals['created']} (entry count under the unit prefixes), "
        f"items {totals['items']} (reader's own item count), updated {totals['updated']}, "
        f"questions {totals['questions']} replied {totals['replied']}"
    )

    lines.append(trades_line)

    conflicted = [entry["unit"] for entry in pass_data["verified"] if entry["fields"]["conflicts"]]
    if totals["conflicts"]:
        lines.append(f"conflicting rows: {totals['conflicts']}, on units {', '.join(conflicted)}")
    else:
        lines.append("conflicting rows: none")

    for kind in ("overlap", "anomaly", "unread"):
        lines.extend(_note_lines(pass_data["notes"], kind))

    kinds: list[str] = []
    for note in pass_data["notes"]:
        if note["kind"] != "kinds":
            continue
        for word in note["clause"].split():
            if word not in kinds:
                kinds.append(word)
    lines.append(f"{KINDS_LINE}: " + (", ".join(kinds) if kinds else "none"))

    lines.extend(_note_lines(pass_data["notes"], "deviation"))

    through = pass_data["lastLine"] or "nothing"
    lines.append(f"ledger: {ledger}, appended through {through}")
    return lines


def _note_lines(notes: list[dict], kind: str) -> list[str]:
    label = NOTE_LINES[kind]
    of_kind = [note for note in notes if note["kind"] == kind]
    if not of_kind:
        return [f"{label}: none"]
    out: list[str] = []
    for note in of_kind:
        where = "" if note["unit"] == "-" else f"{note['unit']} "
        out.append(f"{label}: {where}{note['clause']}")
    return out


def _lines_named(counts: dict[str, int]) -> str:
    if not counts:
        return "none"
    return _named([f"{unit} ({n} line{'' if n == 1 else 's'})" for unit, n in counts.items()])


def bounds_line(
    pass_data: dict, plan: dict, window: int, pass_id: str, ledger: Path, trades: Path | None,
    trades_read: dict | None,
) -> str:
    placed = sum(
        count for kind, count in pass_data["notesByKind"].items() if kind in PLACED_KINDS
    )
    read = sum(pass_data["notesByKind"].values())
    by_kind = ", ".join(
        f"{kind} {pass_data['notesByKind'][kind]}"
        + ("" if kind in PLACED_KINDS else " with no summary line")
        for kind in NOTE_KINDS
    )
    verified_units = {entry["unit"] for entry in pass_data["verified"]}
    unverified = [unit for unit in pass_data["dispatched"] if unit not in verified_units]
    moved = [
        f"{entry['unit']} ({entry['pass']})"
        for entry in pass_data["verified"] if entry["pass"] != pass_id
    ]
    folded_in = ", ".join(plan["foldedIn"]) if plan["foldedIn"] else "none"
    if trades is None or trades_read is None:
        trades_said = "none given"
    else:
        beside = trades_read["beside"]
        trades_said = (
            f"{trades}"
            + (f", and beside it {_named([str(p) for p in beside])}" if beside else "")
            + f"; trades lines for a unit this summary does not count: "
            + _lines_named(trades_read["leftOut"])
        )
    return (
        f"pass_summary: read {ledger}, {pass_data['totalLines']} lines, and the read plan "
        f"{plan['path']}; window {window} pass {pass_id} carries units {len(plan['units'])}, "
        f"folded in {folded_in}: units dispatched {len(pass_data['dispatched'])}, verified "
        f"{len(pass_data['verified'])}, notes read {read} placed {placed} ({by_kind}); "
        f"lines of another window or pass {pass_data['otherLines']}, lead lines "
        f"{pass_data['leadLines']}; dispatched with no verified line: "
        f"{_named(unverified) if unverified else 'none'}; verified under another pass: "
        f"{_named(moved) if moved else 'none'}; lines naming this pass for a unit its plan block "
        f"does not carry: {_lines_named(pass_data['leftBehind'])}; trades file {trades_said}"
    )


# --------------------------------------------------------------------------- #
# Entry point
# --------------------------------------------------------------------------- #

def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Sum one pass of a scope run off the run ledger, into the pass summary shape.",
    )
    parser.add_argument("ledger", type=Path, help="the run folder's ledger.md")
    parser.add_argument("window", type=int, help="the window the pass belongs to")
    parser.add_argument("pass_id", metavar="pass", help="the pass id, exactly as the ledger spells it")
    parser.add_argument(
        "--plan", type=Path, required=True,
        help="the read plan the pass runs off, whose block for the pass lists the units it carries",
    )
    parser.add_argument(
        "--trades", type=Path,
        help="the pass's trades file, one line per trade per unit plus one candidates line per unit",
    )

    args = parser.parse_args(argv)

    try:
        plan = read_plan(args.plan, args.window, args.pass_id)
        pass_data = read_pass(args.ledger, args.window, args.pass_id, plan)
        trades_read = None
        if args.trades is None:
            trades_line = "trades: no trades file for this pass"
        else:
            by_trade, candidates, trades_read = sum_trades(pass_data, args.pass_id, args.trades)
            trades_line = _trades_line(by_trade, candidates)
        for line in summary_lines(pass_data, args.window, args.pass_id, args.ledger, trades_line):
            print(line)
        print(
            bounds_line(
                pass_data, plan, args.window, args.pass_id, args.ledger, args.trades, trades_read,
            ),
            file=sys.stderr,
        )
    except SummaryError as e:
        print(f"pass_summary: {e}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
