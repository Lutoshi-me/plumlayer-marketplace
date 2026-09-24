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
skipped by it, so a lead figure can never reach these totals. Lines of another window or another
pass are skipped by their window and pass fields.

Usage:

    python pass_summary.py <run folder>/ledger.md <window> <pass id> [--trades <path>]

The two streams differ from the plan script's on purpose, and the difference is the point: here
stdout is the deliverable, so it carries the summary and nothing else and the runner pastes it
whole. The bounds line saying what was read goes to stderr beside it.

  --trades  the pass's own trades file, `<run folder>/trades/<pass id>.txt`, which the runner
            appends a unit at a time off its `verify_unit` results:

                <unit id> trade <catalog id> <count>
                <unit id> candidates <count>

            A catalog id carries spaces, so the count is read off the end of the line. Without this
            argument the `trades:` line says there is no trades file, which is a plain statement
            rather than a guess. `candidates <n>` is the created subjects carrying at least one
            candidate trade, each subject counted once however many candidate trades it carries.

Exit codes:
  0  the summary on stdout, one bounds line on stderr.
  1  a named failure, one line on stderr: a ledger file that is not there, a line whose first word
     is none of the three shapes, a `verified` line missing a field the shape names or carrying a
     count that is not a whole number, two `verified` lines for one unit, a `dispatch` line with no
     `sheets` field, a `note` line whose kind is outside the closed set, a window and pass with no
     lines at all, or a trades file line in neither of its two shapes.
  2  argparse rejected the invocation.

Grounding role: reads a file and copies byte values. Nothing here fills a gap. A unit dispatched
with no `verified` line prints its counts as a dash and is named on the bounds line; a note kind
the summary shape has no line for is counted on the bounds line rather than dropped in silence.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

# The closed set the runner definition declares, copied here so a kind added in one place and not
# the other is a refusal rather than a note with nowhere to go.
NOTE_KINDS = ("anomaly", "unread", "kinds", "deviation", "overlap", "grain", "door", "packet")

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
# this shape. The bounds line counts them rather than letting a note land nowhere in silence.
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
    return {"unit": parts[3], "fields": fields, "result": rest[at + 1]}


def read_pass(path: Path, window: int, pass_id: str) -> dict:
    """
    Every line of this window and this pass, in file order, as the three shapes. A line the grammar
    does not hold is a refusal rather than a line stepped over: the ledger is a fixed-shape log,
    and a line nobody can read is a line nobody is counting.
    """
    if not path.is_file():
        raise SummaryError(f"no ledger at {path}")
    try:
        text = path.read_text(encoding="utf-8")
    except Exception as e:
        raise SummaryError(f"cannot read the ledger at {path}: {e}") from e

    want_window = str(window)
    dispatched: list[str] = []
    verified: list[dict] = []
    verified_units: dict[str, int] = {}
    notes: list[dict] = []
    notes_by_kind: dict[str, int] = {kind: 0 for kind in NOTE_KINDS}
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
        if parts[1] != want_window or parts[2] != pass_id:
            other_lines += 1
            # A malformed line of another pass is still refused above, because the grammar is the
            # file's, not this pass's.
            continue

        if keyword == "dispatch":
            if len(parts) < 5 or parts[4] != "sheets":
                raise SummaryError(f"{where}: the dispatch line names no `sheets` field")
            if parts[3] not in dispatched:
                dispatched.append(parts[3])
        elif keyword == "verified":
            entry = _read_verified(parts, where)
            if entry["unit"] in verified_units:
                raise SummaryError(
                    f"{where}: unit {entry['unit']} already carries a verified line at line "
                    f"{verified_units[entry['unit']]}; one unit is verified once"
                )
            verified_units[entry["unit"]] = number
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
        "leadLines": lead_lines,
        "otherLines": other_lines,
        "totalLines": total_lines,
        "lastLine": last_line,
    }


# --------------------------------------------------------------------------- #
# The trades file
# --------------------------------------------------------------------------- #

def read_trades(path: Path) -> tuple[dict[str, int], int]:
    """
    The pass's trades file, as catalog id to item count plus the candidates total. A catalog id
    carries spaces, so the count is the last word of the line and the id is everything between the
    keyword and it.
    """
    if not path.is_file():
        raise SummaryError(f"no trades file at {path}")
    try:
        text = path.read_text(encoding="utf-8")
    except Exception as e:
        raise SummaryError(f"cannot read the trades file at {path}: {e}") from e

    by_trade: dict[str, int] = {}
    candidates = 0
    for number, raw in enumerate(text.splitlines(), 1):
        line = raw.strip()
        if not line:
            continue
        parts = line.split()
        where = f"{path} line {number}"
        if len(parts) >= 3 and parts[1] == "candidates":
            candidates += _whole_number(parts[2], "candidates", where)
            continue
        if len(parts) >= 4 and parts[1] == "trade":
            code = " ".join(parts[2:-1])
            by_trade[code] = by_trade.get(code, 0) + _whole_number(parts[-1], "trade count", where)
            continue
        raise SummaryError(
            f"{where}: the line is neither `<unit id> trade <catalog id> <count>` nor "
            f"`<unit id> candidates <count>`"
        )
    return by_trade, candidates


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


def bounds_line(pass_data: dict, window: int, pass_id: str, ledger: Path, trades: Path | None) -> str:
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
    trades_said = str(trades) if trades is not None else "none given"
    return (
        f"pass_summary: read {ledger}, {pass_data['totalLines']} lines; window {window} pass "
        f"{pass_id}: units dispatched {len(pass_data['dispatched'])}, verified "
        f"{len(pass_data['verified'])}, notes read {read} placed {placed} ({by_kind}); "
        f"lines of another window or pass {pass_data['otherLines']}, lead lines "
        f"{pass_data['leadLines']}; dispatched with no verified line: "
        f"{_named(unverified) if unverified else 'none'}; trades file {trades_said}"
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
        "--trades", type=Path,
        help="the pass's trades file, one line per trade per unit plus one candidates line per unit",
    )

    args = parser.parse_args(argv)

    try:
        pass_data = read_pass(args.ledger, args.window, args.pass_id)
        if args.trades is None:
            trades_line = "trades: no trades file for this pass"
        else:
            by_trade, candidates = read_trades(args.trades)
            trades_line = _trades_line(by_trade, candidates)
        for line in summary_lines(pass_data, args.window, args.pass_id, args.ledger, trades_line):
            print(line)
        print(bounds_line(pass_data, args.window, args.pass_id, args.ledger, args.trades), file=sys.stderr)
    except SummaryError as e:
        print(f"pass_summary: {e}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
