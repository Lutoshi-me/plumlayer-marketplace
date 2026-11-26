"""
ledger.py: the one way a line reaches a scope run's ledger.

Every line of `<run folder>/ledger.md` goes on through this script: the pass runners' `dispatch`,
`verified` and `note` lines, the boundary runner's, and the lead's `pass:`, `phase:`, `short:`,
`amending:`, `amended:` and `unplaced:` lines (`lead_pass.py record` calls the same function). Nothing else writes the file, and no line
already on it is ever changed.

Usage:

    python ledger.py append '<run folder>/ledger.md' <<'EOF'
    <one line>
    <one line>
    EOF

    python ledger.py heal '<run folder>/ledger.md'

The lines come on stdin, one per line, through a quoted heredoc so an apostrophe or a dollar sign
in a copied report line arrives as written. Blank lines are skipped. `heal` holds the ledger to its
shadow copy under the lock and appends nothing of its own but the heal's line below; a pass runner
runs it before its first look at the ledger in every mode, so the closing lines of a unit that
reached the shadow and not the ledger are in place before it decides what each unit needs.

Under a lock, `<run folder>/ledger.lock`, held across the whole of read, check and write by the
rule `plan_inventory.hold_lock` gives (the operating system lets the lock go when its process
ends, however it ends), the script:

1. Holds the ledger to its shadow copy, `<run folder>/ledger.shadow`, which only this script
   writes (`heal` below).
2. Checks the whole batch in order, against the ledger and the batch's own lines before each one:
   the three runner shapes, read with `pass_summary.py`'s own parser and its closed set of note
   kinds; a deviation note is a block or an interruption only where its tail is the whole shape
   the runner writes (`blocked: <tool> <sign-in, refused by the client or server>` or
   `interrupted: no report on file`) directly before `, read <k>`, as `pass_summary.py` reads it,
   and any other note holding those words is an ordinary deviation and is taken; the lead's shapes, a
   `phase: reading started` line carrying its UTC time, and no new `checkin:` line, since a scope
   run has no check-in; and the rule that a unit carries
   another `verified` line only where a `dispatch` line for that unit sits between it and the
   unit's `verified` line before. One line that fails refuses the whole batch, and nothing is
   written; the refusal names the line and what is wrong with it.
3. Writes the batch to the shadow, then to the ledger. The shadow is published whole: the old
   shadow and the batch are written to a temporary file in the run folder, which then replaces the
   shadow in one atomic step (`publish` below), so a writer stopped at any point leaves the shadow
   as it was or with the whole batch, never part of it. The ledger then takes the batch in one
   append ending in a newline; a writer stopped partway through that leaves the ledger a byte
   prefix of the shadow, which the heal completes.

`publish(path, data)` is the one way this script and `unit_report.py` replace a file whole: a
temporary file `.<name>.<process>.tmp` beside it, flushed to disk, then `os.replace`. On Windows
the replace fails while another process holds the target open (a reader of the trades file or the
shadow at that moment); it is tried again every PUBLISH_WAIT_SECONDS for up to
PUBLISH_TRIES tries, and then the write fails with one line and the temporary file is removed. The
target is never written in place.

The heal, before every append, on `heal`, and whenever `lead_pass.py` reads the ledger:

- The ledger's bytes equal the shadow's: nothing to do.
- The ledger is a strict prefix of the shadow: a writer stopped between its two writes. The
  ledger is completed from the shadow, and nothing is said.
- The shadow is a strict prefix of the ledger, and every line past it is a whole `phase:` line,
  holding no control character, that the check of step 2 takes, as an append of
  those lines would be checked:
  the lead or the package folder appended its own standalone line by hand. Those lines are added
  to the shadow as they stand, the ledger is left as it is, and nothing is said, so a `phase:`
  line written by hand is never lost. A runner's line (`dispatch`, `verified`, `note`) or a
  `pass:` line is never adopted this way: a runner's closing lines land as one group, and the
  heal cannot tell a whole group from the first part of one, so such a line is put back below.
- Anything else (a line changed, a line taken out, a line added without this script that is not
  one the heal adopts, or a last line with no newline): the ledger is written again from the
  shadow, and one line is appended to both:

      repaired: lines differing from the run's own copy <n>, first at line <i>; the ledger was written again from that copy

  `<n>` counts the whole lines changed, taken out or added, and `<i>` is the first line, counted
  in the run's own copy, where the two differed. The closing report says it to the estimator in
  plain words.
- No shadow yet (the first append on this version, or a new run): the shadow becomes a copy of
  the ledger's whole lines, and a last line with no newline is dropped from both.
- A shadow whose last line has no newline, which no run of this script leaves, and a ledger that
  ends with a newline, begins with the shadow's bytes and completes that last line: the ledger
  holds the line the shadow lost the end of, so the shadow is rebuilt from the ledger through
  that line and the heal goes on from there, and nothing is dropped.
- Any other shadow whose last line has no newline: damage the heal cannot explain, handled as a
  changed line is. The unterminated line is dropped, the ledger is written again from the
  shadow's whole lines, and the `repaired:` line is appended to both, counting the dropped line
  where nothing else differed.

One way of splitting the file into lines serves the append, the heal and the check (`lines_of`):
a line ends at a newline, and one carriage return before it is part of that line ending, so a
line written by hand with a Windows line ending reads as the same line. In an append, each control
character or line separator inside a line (a tab, a form feed, a carriage return not part of the
line ending, U+2028 and the rest of Unicode categories Cc, Zl and Zp) is replaced by one space
before the line is checked, and the line is written that way, since text copied off a drawing or a
manual page can hold any of them. The heal never adopts a line written by hand that holds one:
readers of the ledger would split it into lines differently, so it is put back.

No reader of the ledger refuses or stops over a change the heal puts back.

Exit codes:
  0  the lines appended; one line on stdout naming how many, and the heal's line where it wrote one.
     On `heal`, the heal's line where it wrote one, or one line saying the ledger holds every line
     of its copy.
  1  a named failure, one line on stderr: a line in no shape the ledger holds, a `verified` line
     with no `dispatch` line since the unit's last one, a batch with no line, a ledger not named
     `ledger.md`, a lock a live run held past the wait, or a file that cannot be read or written.
  2  argparse rejected the invocation.

Grounding role: copies bytes and checks shapes. It reads no record and judges no line's meaning.
"""

from __future__ import annotations

import argparse
import difflib
import os
import re
import sys
import time
import unicodedata
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import pass_summary  # noqa: E402
import plan_inventory  # noqa: E402

LEDGER_NAME = pass_summary.LEDGER_NAME
SHADOW_NAME = "ledger.shadow"
LOCK_NAME = "ledger.lock"

# The heal's own line. Only this script writes it, so a batch carrying one is refused.
REPAIRED_KEYWORD = "repaired:"
REPAIRED_LINE = (
    "repaired: lines differing from the run's own copy {count}, first at line {first}; "
    "the ledger was written again from that copy"
)
REPAIRED_RE = re.compile(
    r"^repaired: lines differing from the run's own copy (\d+), first at line (\d+); "
    r"the ledger was written again from that copy$"
)

# The lead's own line shapes. The `pass:` figures after `replied` differ by window, so any number of
# `<figure> <n>` pairs may stand between it and `lead-verified`: `skipped <n>` in every window, then
# window 3's and window r's own.
_PASS_RE = re.compile(
    r"^pass: (?:[1-9][0-9]*|r) \S+ units \d+ created \d+ updated \d+ questions \d+ replied \d+"
    r"(?: [a-z][a-z-]* \d+)* lead-verified (?:yes|no)$"
)
_PHASE_RE = re.compile(r"^phase: \S.*$")
# The line the lead appends when reading starts carries the time in UTC, which the closing report
# measures the run from. An older ledger's `phase: plan approved` line is still read.
READING_STARTED = "phase: reading started"
_READING_STARTED_RE = re.compile(r"^phase: reading started \d{4}-\d\d-\d\dT\d\d:\d\d:\d\dZ$")
# What the lead writes down when it happens, for the closing report: a unit the record holds fewer
# entries under than its runner verified (written by `lead_pass.py record`), a package amendment
# with its reason, and a manual section left on no package with why.
_SHORT_RE = re.compile(r"^short: (?:[1-9][0-9]*|r) \S+ \S+ record \d+ runner \d+$")
# A package amendment is written twice: `amending:` before its calls, and `amended:` with the same
# text once they succeed, so the closing report says a change was made only once it was.
_AMENDING_RE = re.compile(r"^amending: \S.*$")
_AMENDED_RE = re.compile(r"^amended: \S.*$")
_UNPLACED_RE = re.compile(r"^unplaced: \S+ \S.*$")
LEAD_SHAPES = {
    "pass:": _PASS_RE, "phase:": _PHASE_RE, "short:": _SHORT_RE, "amending:": _AMENDING_RE,
    "amended:": _AMENDED_RE, "unplaced:": _UNPLACED_RE,
}
# A scope run has no check-in. A ledger written before still holds `checkin:` lines, and every
# script reads past them, but no new one goes on.
RETIRED_KEYWORDS = {"checkin:": "a scope run has no check-in, so no `checkin:` line goes on the ledger"}
# The lines the heal adopts when they were appended by hand: the lead's and the package folder's
# standalone `phase:` lines. A runner's lines land as one closing group and a `pass:` line goes on
# through the lead's record script, so neither is adopted.
ADOPTED_KEYWORDS = ("phase:",)

# A character no ledger line holds: a control character (a tab and a carriage return among them) or
# a line or paragraph separator. An append writes each as a space; the heal adopts no line holding one.
_NOT_IN_A_LINE = ("Cc", "Zl", "Zp")


class LedgerError(Exception):
    """A named failure with a one-line reason, reported on stderr and exiting 1."""


def lines_of(text: str) -> list[str]:
    """
    The lines of ledger text, the one way the append, the heal and the check split it: a line ends
    at a newline, and one carriage return before that newline is part of the line ending. A last
    line with no newline is kept as a line; the heal and the readers that need whole lines cut it
    off the bytes first.
    """
    lines = text.split("\n")
    if lines and lines[-1] == "":
        lines.pop()
    return [line[:-1] if line.endswith("\r") else line for line in lines]


def control_character(line: str) -> str | None:
    """The first character of `line` that no ledger line holds, or None."""
    return next((c for c in line if unicodedata.category(c) in _NOT_IN_A_LINE), None)


def one_line(line: str) -> str:
    """`line` with each character no ledger line holds replaced by one space, as an append writes it."""
    return "".join(" " if unicodedata.category(c) in _NOT_IN_A_LINE else c for c in line)


def _shown(line: str) -> str:
    """A line as a refusal names it: its first 80 characters, each control character as `?`."""
    return "".join("?" if unicodedata.category(c) in _NOT_IN_A_LINE else c for c in line[:80])


def _paths(ledger: Path) -> tuple[Path, Path]:
    if ledger.name != LEDGER_NAME:
        raise LedgerError(f"{ledger} is not a run folder's {LEDGER_NAME}; lines go on that file alone")
    return ledger.parent / SHADOW_NAME, ledger.parent / LOCK_NAME


def _read(path: Path) -> bytes | None:
    try:
        return path.read_bytes() if path.is_file() else None
    except OSError as e:
        raise LedgerError(f"cannot read {path}: {e}") from e


def _write(path: Path, data: bytes, mode: str) -> None:
    try:
        with path.open(mode) as handle:
            handle.write(data)
    except OSError as e:
        raise LedgerError(f"cannot write {path}: {e}") from e


PUBLISH_TRIES = 100
PUBLISH_WAIT_SECONDS = 0.05


def _remove(path: Path) -> None:
    try:
        path.unlink()
    except OSError:
        pass


def publish(path: Path, data: bytes) -> None:
    """
    Replace `path` with `data` whole: a temporary file in the same folder, flushed to disk, then one
    atomic replace, so a reader, or a writer stopped at any point, finds the old bytes or the new
    ones and never part of them. A replace refused because another process holds the target open,
    as Windows refuses it, is tried again within the bound, then fails with one line; the target is
    never written in place.
    """
    temp = path.parent / f".{path.name}.{os.getpid()}.tmp"
    try:
        with open(temp, "wb") as handle:
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
    except OSError as e:
        _remove(temp)
        raise LedgerError(f"cannot write {temp}: {e}") from e
    for _ in range(PUBLISH_TRIES):
        try:
            os.replace(temp, path)
            return
        except PermissionError:
            time.sleep(PUBLISH_WAIT_SECONDS)
        except OSError as e:
            _remove(temp)
            raise LedgerError(f"cannot replace {path}: {e}") from e
    _remove(temp)
    raise LedgerError(
        f"cannot replace {path}: another process held it open for "
        f"{PUBLISH_TRIES * PUBLISH_WAIT_SECONDS:g} seconds; run it again once that process ends"
    )


def _whole(data: bytes) -> bytes:
    """The bytes up to and through the last newline, so a last line with none is left out."""
    return data[: data.rfind(b"\n") + 1]


def _difference(shadow: bytes, ledger: bytes) -> tuple[int, int]:
    """How many whole lines differ between the two, and the first line of the shadow that does."""
    # Each side split at its newlines as the bytes stand, so a line that differs only by a carriage
    # return still counts as a line that differs, and a last line with no newline is a line of its own.
    ours = shadow.decode("utf-8", "replace").split("\n")
    theirs = ledger.decode("utf-8", "replace").split("\n")
    for side in (ours, theirs):
        if side and side[-1] == "":
            side.pop()
    count = 0
    first = None
    for tag, i1, i2, j1, j2 in difflib.SequenceMatcher(a=ours, b=theirs, autojunk=False).get_opcodes():
        if tag == "equal":
            continue
        count += max(i2 - i1, j2 - j1)
        if first is None:
            first = i1 + 1
    return count, first or 1


def _adoptable(shadow: bytes, extra: bytes) -> bool:
    """
    Whether the lines past the shadow are whole, not blank, each a `phase:` line holding no
    control character, and taken by the check of an append.
    """
    if not extra.endswith(b"\n"):
        return False
    try:
        lines = lines_of(extra.decode("utf-8"))
        if any(not line.strip() or line != line.strip() or control_character(line) for line in lines):
            return False
        if any(line.split()[0] not in ADOPTED_KEYWORDS for line in lines):
            return False
        check_batch(shadow.decode("utf-8", "replace"), lines)
    except (UnicodeDecodeError, LedgerError):
        return False
    return True


def _completed(shadow: bytes, data: bytes) -> bytes | None:
    """
    Where the shadow's last line has no newline and the ledger, whole and beginning with the
    shadow's bytes, completes that line with a line an append would take, the shadow rebuilt from
    the ledger through that line; otherwise None, and the tail is damage.
    """
    if not data.endswith(b"\n") or not data.startswith(shadow):
        return None
    end = data.index(b"\n", len(shadow)) + 1
    start = shadow.rfind(b"\n") + 1
    try:
        before = data[:start].decode("utf-8")
        line = lines_of(data[start:end].decode("utf-8"))[0]
    except UnicodeDecodeError:
        return None
    if not line.strip() or line != line.strip() or control_character(line) is not None:
        return None
    if REPAIRED_RE.match(line) is None:
        try:
            check_batch(before, [line])
        except LedgerError:
            return None
    return data[:end]


def _heal_locked(ledger: Path, shadow_path: Path) -> str | None:
    """
    Hold the ledger to its shadow, with the lock already held. Returns the heal's own line where it
    wrote one, and None where the two agreed or the ledger only lacked a stopped writer's lines.
    """
    data = _read(ledger)
    shadow = _read(shadow_path)
    if shadow is None:
        whole = _whole(data or b"")
        publish(shadow_path, whole)
        if data is not None and data != whole:
            publish(ledger, whole)
        return None
    data = data or b""
    torn = not shadow.endswith(b"\n") and shadow != b""
    if torn:
        # The shadow lost the end of its last line, and the ledger may still hold that line whole.
        rebuilt = _completed(shadow, data)
        if rebuilt is not None:
            publish(shadow_path, rebuilt)
            shadow, torn = rebuilt, False
    if not torn:
        if data == shadow:
            return None
        if len(data) < len(shadow) and shadow.startswith(data):
            _write(ledger, shadow[len(data):], "ab")
            return None
        if len(data) > len(shadow) and data.startswith(shadow) and _adoptable(shadow, data[len(shadow):]):
            # Whole lines a writer appended by hand, each one an append would take: kept as the run's.
            publish(shadow_path, data)
            return None
    copy = _whole(shadow)
    count, first = _difference(copy, data)
    if torn and count == 0:
        # The ledger holds the shadow's whole lines alone: the dropped line is the one difference.
        count, first = 1, copy.count(b"\n") + 1
    line = REPAIRED_LINE.format(count=count, first=first)
    repaired = copy + f"{line}\n".encode("utf-8")
    # The run's copy first, so a stop between the two leaves the ledger to the next heal.
    publish(shadow_path, repaired)
    publish(ledger, repaired)
    return line


def heal(ledger: Path) -> str | None:
    """
    Hold the ledger to its shadow under the lock, as `lead_pass.py` does before it reads the
    ledger. A run folder with neither file yet is left as it is.
    """
    shadow_path, lock_path = _paths(ledger)
    if not ledger.is_file() and not shadow_path.is_file():
        return None
    with plan_inventory.hold_lock(lock_path, "ledger", LedgerError):
        return _heal_locked(ledger, shadow_path)


# --------------------------------------------------------------------------- #
# Checking a batch
# --------------------------------------------------------------------------- #

class _State:
    """Each unit's last `dispatch` or `verified` line, by window and unit, as the batch is read."""

    def __init__(self) -> None:
        self.last: dict[tuple[str, str], str] = {}

    def take(self, parts: list[str]) -> None:
        if len(parts) >= 4 and parts[0] in ("dispatch", "verified"):
            self.last[(parts[1], parts[3])] = parts[0]


def _state_of(text: str) -> _State:
    """What the ledger already says, read leniently: a line already on it is adopted as found."""
    state = _State()
    for raw in lines_of(text):
        state.take(raw.strip().split())
    return state


def check_line(line: str, state: _State, where: str) -> None:
    """Refuse a line in no shape the ledger holds, or a `verified` line the rule refuses."""
    parts = line.split()
    keyword = parts[0]
    if keyword.endswith(":"):
        if keyword == REPAIRED_KEYWORD:
            raise LedgerError(f"{where}: a `repaired:` line is written by this script alone")
        if keyword in RETIRED_KEYWORDS:
            raise LedgerError(f"{where}: {RETIRED_KEYWORDS[keyword]}")
        shape = LEAD_SHAPES.get(keyword)
        if shape is None:
            raise LedgerError(
                f"{where}: the line starts with {keyword!r}, and the lead's lines start with "
                f"{', '.join(f'`{k}`' for k in LEAD_SHAPES)}"
            )
        if shape.match(line) is None:
            raise LedgerError(f"{where}: the {keyword} line is not in the shape the skill gives it")
        if line.startswith(READING_STARTED) and _READING_STARTED_RE.match(line) is None:
            raise LedgerError(
                f"{where}: `{READING_STARTED}` carries the time reading started in UTC, as "
                f"`{READING_STARTED} 2026-01-31T22:10:00Z`"
            )
        return
    try:
        parsed = pass_summary.parse_runner_line(parts, where)
    except pass_summary.SummaryError as e:
        raise LedgerError(str(e)) from None
    if parsed["window"] not in ("1", "2", "3", pass_summary.RECHECK_WINDOW):
        raise LedgerError(f"{where}: {parsed['window']!r} is not a window: 1, 2, 3 or r")
    if keyword == "dispatch" and "purpose" not in parts[6:-1]:
        raise LedgerError(f"{where}: the dispatch line names no `purpose` with words after it")
    if keyword == "note" and len(parts) < 6:
        raise LedgerError(f"{where}: the note line carries a kind and no clause")
    # A deviation note is a block or an interruption only by its whole tail, as `pass_summary.py`
    # reads it; a note that holds the words anywhere else, or a near miss of the shape, is an
    # ordinary deviation, so nothing here refuses one for the words it carries.
    if keyword == "verified":
        if parsed["result"] not in ("ok", "mismatch"):
            raise LedgerError(f"{where}: the verified line's result reads {parsed['result']!r}, not ok or mismatch")
        if state.last.get((parts[1], parts[3])) == "verified":
            raise LedgerError(
                f"{where}: unit {parts[3]} already carries a verified line and no dispatch line for "
                f"it since; a unit is verified again only after it is read again, its dispatch "
                f"line first"
            )
    state.take(parts)


def check_batch(ledger_text: str, lines: list[str]) -> None:
    state = _state_of(ledger_text)
    if not lines:
        raise LedgerError("no line to append; give the lines on stdin, one per line")
    for number, line in enumerate(lines, 1):
        check_line(line, state, f"batch line {number} ({_shown(line)})")


def append_lines(ledger: Path, lines: list[str]) -> list[str]:
    """
    Check the batch and append it, healing first, all under the lock. Returns what to print: the
    heal's line where it wrote one, then the count appended.
    """
    lines = [line for line in (one_line(raw).strip() for raw in lines) if line]
    shadow_path, lock_path = _paths(ledger)
    out: list[str] = []
    with plan_inventory.hold_lock(lock_path, "ledger", LedgerError):
        healed = _heal_locked(ledger, shadow_path)
        if healed:
            out.append(healed)
        current = _read(ledger) or b""
        check_batch(current.decode("utf-8", "replace"), lines)
        batch = "".join(f"{line}\n" for line in lines).encode("utf-8")
        # The heal left the shadow equal to the ledger, so the new shadow is the old bytes and the
        # batch, published whole before the ledger takes the batch.
        publish(shadow_path, (_read(shadow_path) or b"") + batch)
        _write(ledger, batch, "ab")
    out.append(f"ledger: appended {len(lines)} line{'' if len(lines) == 1 else 's'} to {ledger}")
    return out


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Append lines to a scope run's ledger, checked, under its lock.")
    modes = parser.add_subparsers(dest="mode", required=True)
    add = modes.add_parser("append", help="append the lines on stdin, one per line")
    add.add_argument("ledger", type=Path, help="the run folder's ledger.md")
    held = modes.add_parser("heal", help="hold the ledger to its shadow copy and append nothing else")
    held.add_argument("ledger", type=Path, help="the run folder's ledger.md")
    args = parser.parse_args(argv)
    if args.mode == "heal":
        try:
            healed = heal(args.ledger)
        except LedgerError as e:
            print(f"ledger: {e}", file=sys.stderr)
            return 1
        print(healed or f"ledger: {args.ledger} holds every line of the run's own copy")
        return 0
    try:
        raw = sys.stdin.buffer.read().decode("utf-8")
        out = append_lines(args.ledger, lines_of(raw))
    except UnicodeDecodeError:
        print("ledger: the lines on stdin are not UTF-8 text; no line of the batch was written", file=sys.stderr)
        return 1
    except LedgerError as e:
        print(f"ledger: {e}; no line of the batch was written", file=sys.stderr)
        return 1
    for line in out:
        print(line)
    return 0


if __name__ == "__main__":
    sys.exit(main())
