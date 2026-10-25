"""
fold_report.py: read the package fold's report, for the lead's check-in and for the folder's hand-back.

The package folder folds a scope run's bid packages into what one kind of firm bids, one level down
from the lead, and appends each act it makes to `<run folder>/reports/fold.md` right after the call
that made it returns, one act per line under a closed label. This script reads that file. It reads
no record and judges nothing: it copies the lines and counts them, so the lead holds the report only
as long as a check-in needs it and the folder adds no number of its own.

Two modes:

    python fold_report.py print <run folder> [--start <lines>[:<characters>]]

        Every line of the report, as written, for the lead to say in the estimator's words at the
        check-in that ends window 2 and at close-out. Output stops before PRINT_CAP characters,
        below the 30,000 a Bash call returns, every printed line counted, the closing line
        included, and its last line names the command that prints the rest. A line longer than the
        room a call has once nothing else is printed is cut there, under a line naming where, and
        the next call prints the rest of it. `--start` is how many lines an earlier call already
        printed, and after a colon (`--start 4:23000`) how many characters of the line after them.
        A run folder that holds no report and whose ledger says its packages were folded folded
        before the folder kept a report: it prints NO_REPORT_LINE alone, which names no delete.

    python fold_report.py hand-back <run folder> --before <n> --after <n>

        The folder's final message, five lines:

            fold: packages <n> before, <n> after
            acts: folded <n>, split <n>, moved <n>, deleted <n>, kept <n>
            records: candidates sent <n> landed <n>, rows re-homed <n>, questions <n>
            phase: packages folded appended
            report: <run folder>/reports/fold.md

        `--before` and `--after` are the package counts of the folder's own two package list reads,
        the first before its first act and the second after its last. The act counts are the lines
        under each label, `candidates` the sums of the `candidates:` lines, `rows re-homed` the
        `re-homed:` lines and `questions` the `question:` lines. The fourth line is printed only once
        the ledger beside the report carries a `phase: packages folded` line.

The labels, the whole set (LABELS), each followed by a colon and a space:

    folded, split, moved, supplier, sealant kept, default, deleted, owner's work still covered,
    kept, changed, re-homed, question, candidates, fold touched

`candidates:` reads `candidates: sent <n> landed <n>`, one line per batch. `deleted:` reads
`deleted: <the package>, trade <its trade code>, package <its id>, <the reason>`, the trade and the
id as the package list the folder read gives them, since the lead leaves that trade off the general
requirements package by reading it off this line. `changed:` names a package still on the record
whose lists the folder found changed after a stop with no act to name, so no delete is claimed.

Exit codes:
  0  printed.
  1  a named failure, one line on stderr: a run folder with no report, except in print mode one
     whose ledger carries a `phase: packages folded` line, a report line under no label
     of the set, a `candidates:` or `deleted:` line in another shape, a `--start` that is not a
     count of lines and characters or names a character past its line, and in hand-back mode a
     ledger with no `phase: packages folded` line or no ledger at all.
  2  argparse rejected the invocation.

Grounding role: reads files and copies byte values. Nothing here fills a gap.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

REPORT_PATH = ("reports", "fold.md")
LEDGER_FILE = "ledger.md"
PHASE_LINE = "phase: packages folded"

# What print says for a run folder that folded before the folder kept a report.
NO_REPORT_LINE = (
    "This run folded its packages before the fold kept a report, so there is no list of what it "
    "folded or deleted."
)

# The acts the check-in that ends window 2 names, one label each, in the order it names them.
LABELS = (
    "folded", "split", "moved", "supplier", "sealant kept", "default", "deleted",
    "owner's work still covered", "kept", "changed", "re-homed", "question", "candidates",
    "fold touched",
)

# Under the 30,000 characters a Bash call returns. Every line a call prints counts against it, the
# closing line included.
PRINT_CAP = 25_000

_CANDIDATES_RE = re.compile(r"^candidates: sent (\d+) landed (\d+)$")
# A trade code carries spaces and no comma, and a package id is `pkg-` and its own characters, so a
# placeholder left in either field is no match.
_DELETED_RE = re.compile(r"^deleted: (.+?), trade ([^,<>]+), package (pkg-[^\s,<>]+), (.+)$")
DELETED_SHAPE = "`deleted: <the package>, trade <its trade code>, package <its id>, <the reason>`"


class FoldReportError(Exception):
    """A named failure with a one-line reason, reported on stderr and exiting 1."""


def _label_of(line: str) -> str | None:
    # Longest first, so `kept` never takes a line that opens `sealant kept`.
    for label in sorted(LABELS, key=len, reverse=True):
        if line.startswith(f"{label}: "):
            return label
    return None


def read_report(run_folder: Path) -> tuple[Path, list[tuple[str, str]]]:
    """Each line of the report with its label, blank lines skipped, every other line refused."""
    path = run_folder.joinpath(*REPORT_PATH)
    if not path.is_file():
        raise FoldReportError(f"no fold report at {path}; it is written as the packages are folded")
    try:
        text = path.read_text(encoding="utf-8")
    except Exception as e:
        raise FoldReportError(f"cannot read the fold report at {path}: {e}") from e
    lines: list[tuple[str, str]] = []
    for number, raw in enumerate(text.splitlines(), 1):
        line = raw.strip()
        if not line:
            continue
        label = _label_of(line)
        if label is None:
            raise FoldReportError(
                f"{path} line {number} opens with none of the fold report's labels "
                f"({', '.join(LABELS)}): {line[:80]!r}"
            )
        if label == "candidates" and _CANDIDATES_RE.match(line) is None:
            raise FoldReportError(
                f"{path} line {number} reads {line[:80]!r}, and a candidates line reads "
                f"`candidates: sent <n> landed <n>`"
            )
        if label == "deleted" and _DELETED_RE.match(line) is None:
            raise FoldReportError(
                f"{path} line {number} reads {line[:80]!r}, and a deleted line reads {DELETED_SHAPE}"
            )
        lines.append((label, line))
    return path, lines


# --------------------------------------------------------------------------- #
# print
# --------------------------------------------------------------------------- #

def _ledger_says_folded(run_folder: Path) -> bool:
    ledger = run_folder / LEDGER_FILE
    if not ledger.is_file():
        return False
    try:
        return PHASE_LINE in (raw.strip() for raw in ledger.read_text(encoding="utf-8").splitlines())
    except Exception as e:
        raise FoldReportError(f"cannot read the ledger at {ledger}: {e}") from e


def print_lines(run_folder: Path, start: tuple[int, int]) -> list[str]:
    if not run_folder.joinpath(*REPORT_PATH).is_file() and _ledger_says_folded(run_folder):
        return [NO_REPORT_LINE]
    _path, report = read_report(run_folder)
    lines = [line for _label, line in report]
    start_lines, chars = start
    if start_lines > len(lines) or (
        chars and (start_lines >= len(lines) or chars >= len(lines[start_lines]))
    ):
        raise FoldReportError(
            f"--start names character {chars + 1} of line {start_lines + 1}, and the report has no "
            f"such place; print the report again from its first call"
        )

    def closing(line_no: int, at: int) -> str:
        start_at = f"{line_no - 1}:{at}" if at else str(line_no - 1)
        return (
            f"not printed: line {line_no}" + (f" from character {at + 1}" if at else "")
            + f" on; the rest: python3 '{Path(__file__).resolve()}' print '{run_folder}' "
            f"--start {start_at}"
        )

    def cut_marker(line_no: int, at: int, length: int) -> str:
        return f"cut: line {line_no}, at character {at} of {length}; the rest is in the next call"

    longest = max((len(line) for line in lines), default=0)
    # Room for the longest closing line and cut marker this call could print, so the cap holds
    # whatever line the call stops on.
    reserve = (
        len(closing(len(lines) + 1, longest)) + len(cut_marker(len(lines) + 1, longest, longest))
        + len(f"line {len(lines) + 1}, from character {longest + 1}:") + 3
    )

    out: list[str] = []
    size = 0
    printed = 0
    for index in range(start_lines, len(lines)):
        begin = chars if index == start_lines else 0
        block = [f"line {index + 1}, from character {begin + 1}:"] if begin else []
        piece = lines[index][begin:]
        room = PRINT_CAP - reserve - size - sum(len(text) + 1 for text in block) - 1
        if len(piece) <= room:
            out.extend(block)
            out.append(piece)
            size += sum(len(text) + 1 for text in block) + len(piece) + 1
            printed += 1
            continue
        if printed:
            out.append(closing(index + 1, begin))
            return out
        # A line longer than a whole call's room is cut where the room ends, so every call prints
        # something new and nothing past the cap.
        out.extend(block)
        out.append(piece[:room])
        out.append(cut_marker(index + 1, begin + room, len(lines[index])))
        out.append(closing(index + 1, begin + room))
        return out
    out.append(f"every line printed, {printed} in this call")
    return out


# --------------------------------------------------------------------------- #
# hand-back
# --------------------------------------------------------------------------- #

def hand_back_lines(run_folder: Path, before: int, after: int) -> list[str]:
    path, report = read_report(run_folder)
    ledger = run_folder / LEDGER_FILE
    if not ledger.is_file():
        raise FoldReportError(f"no ledger at {ledger}")
    try:
        phases = [raw.strip() for raw in ledger.read_text(encoding="utf-8").splitlines()]
    except Exception as e:
        raise FoldReportError(f"cannot read the ledger at {ledger}: {e}") from e
    if PHASE_LINE not in phases:
        raise FoldReportError(
            f"{ledger} carries no `{PHASE_LINE}` line; append it once the report is complete, then "
            f"run this again"
        )
    count = {label: 0 for label in LABELS}
    sent = landed = 0
    for label, line in report:
        count[label] += 1
        if label == "candidates":
            match = _CANDIDATES_RE.match(line)
            sent += int(match.group(1))
            landed += int(match.group(2))
    return [
        f"fold: packages {before} before, {after} after",
        f"acts: folded {count['folded']}, split {count['split']}, moved {count['moved']}, "
        f"deleted {count['deleted']}, kept {count['kept']}",
        f"records: candidates sent {sent} landed {landed}, rows re-homed {count['re-homed']}, "
        f"questions {count['question']}",
        f"{PHASE_LINE} appended",
        f"report: {path}",
    ]


# --------------------------------------------------------------------------- #
# Entry point
# --------------------------------------------------------------------------- #

def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Read the package fold's report.")
    modes = parser.add_subparsers(dest="mode", required=True)

    show = modes.add_parser("print", help="every line of the fold report, under the output cap")
    show.add_argument("run_folder", type=Path, help="the run folder")
    show.add_argument(
        "--start", default="0",
        help="how many lines an earlier call already printed, and after a colon how many "
        "characters of the line after them",
    )

    back = modes.add_parser("hand-back", help="the package folder's final message")
    back.add_argument("run_folder", type=Path, help="the run folder")
    back.add_argument("--before", type=int, required=True, help="the packages before the first act")
    back.add_argument("--after", type=int, required=True, help="the packages after the last act")

    args = parser.parse_args(argv)
    try:
        if args.mode == "print":
            start = re.fullmatch(r"(\d+)(?::(\d+))?", args.start)
            if start is None:
                raise FoldReportError(
                    f"--start reads {args.start!r}, and it takes a count of lines, or lines and "
                    f"characters as <lines>:<characters>"
                )
            lines = print_lines(args.run_folder, (int(start.group(1)), int(start.group(2) or 0)))
        else:
            lines = hand_back_lines(args.run_folder, args.before, args.after)
    except FoldReportError as e:
        print(f"fold_report: {e}", file=sys.stderr)
        return 1
    for line in lines:
        print(line)
    return 0


if __name__ == "__main__":
    sys.exit(main())
