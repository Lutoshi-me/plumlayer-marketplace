"""
lead_pass.py: the lead's own reads and writes for the passes of a scope run.

The lead checks every pass a third time, after the reader and the runner: one `count_entries` call
for the pass, the entry count under each unit's `scopeItem:<unit id>-` prefix, taken off the record
by the lead itself. Everything around that call is bookkeeping, and bookkeeping done by hand in the
lead's own context is what grew a measured run past 850k tokens: a count call per unit, and every
runner's summary held in full. So this script does the bookkeeping, and the lead holds the few
lines it prints.

It never reads the record. The counts come from the lead, off its own `count_entries` call, and the
script compares them with the summary the pass's runner wrote; it never takes a created figure from
that summary.

Four modes:

    python lead_pass.py passes --plan <run folder>/read-plan.md [--running <pass id>,<pass id>]
        [--reported <pass id>]

        Every pass the read plan carries, in its order, two lines each:

            <pass id>: units <n>, units verified <k>, units skipped <s>, summed <yes, or no and why>
            <pass id> prefixes: ["scopeItem:<unit id>-", ...]

        then `passes <n>, finished <k>; to dispatch: <pass ids, or none>`, and what the lead does
        next, off the plan's `starts after:` lines and the ledger beside it:

            start now: <pass ids, or none>
            waiting: <pass ids, or none>

        A pass is finished where its units verified and its units skipped add up to its `units:`
        and it reads `summed: yes`. A unit is skipped where `plan_inventory.settled_units` reads it
        so, its two reads spent on failed checks; the recheck's window `r` skips none, so a unit
        there whose reads are spent leaves its pass unfinished. Those values are taken as a plan run
        would write them now, off the ledger and the summaries on file, since the plan file is
        rewritten only by a plan run; a plan with no ledger yet has nothing finished. The prefixes
        are built from the unit ids the plan block carries, in its order.

        `--running` is the passes the lead started and has not recorded. `start now:` is the passes
        not finished, not running and with every pass on their `starts after:` line finished, in
        plan order, cut to PASSES_AT_ONCE less the count running, in every window. `waiting:` is
        every other pass not finished and not running.

        `--reported` is the pass that just handed back. It prints only that pass's prefixes line,
        read off the plan at this call, so a window 3 manual part a replan put in the pass is in it,
        then the three closing lines, `passes` through `waiting:`. A pass the plan does not carry
        is refused. It counts as running until it is recorded, so it is never offered to start.

        A plan with no pass, as window 2's is where window 1 selected or left out every sheet, prints
        `passes 0, finished 0; to dispatch: none` and those two lines, each reading none.

    python lead_pass.py record <run folder>/ledger.md <window> <pass id>
        --plan <run folder>/read-plan.md --counts-json '<the counts array>'

        `--counts-json` is the `counts` array of the lead's `count_entries` answer, as it came back:
        `[{"subjectPrefix": "scopeItem:<unit id>-", "entryCount": <n>}, ...]`. Each count is paired
        with its unit by its prefix, never by its place in the list, and the prefixes have to be
        exactly the ones the plan block yields, each once. Reads the pass's summary,
        `reports/<pass id>.md` beside the ledger, and compares it unit by unit with the counts.
        The summary's `ledger lines: <n> sha256 <hash>` line has to name the first n whole lines
        of this ledger as they stand, so a summary summed off a copy of the ledger, or off a ledger
        a line was taken out of, is refused before any count is compared. A unit the summary reads
        verified whose latest `verified` line after those lines reads mismatch is refused too, since
        the summary no longer speaks for it.

        A unit the summary reads `verified skipped`, in windows 1, 2 and 3, is settled: its writes
        stay on the record, and its count is held to the `created` of its latest `verified` line as
        a floor where one is summed, and to nothing where none is. A unit it reads `verified no` is
        refused, as is a skipped unit in window `r`, since the recheck stops there. It appends one
        `pass:` line to the ledger and prints it:

            pass: <window> <pass id> units <n> created <n> updated <n> questions <n> replied <n> skipped <n> lead-verified yes
            pass: 3 <pass id> units <n> created <n> updated <n> questions <n> replied <n> skipped <n> pages-opened <n> searches <n> reports-restored <n> lead-verified yes

        The line goes on through `ledger.py`'s append, under its lock and checked, as every line
        of the ledger does.

        Under it, it prints the pass as the estimator hears it, with the new items off the summary's
        trades line, so the one line the lead says as the pass is recorded names the sheets or
        packages and the items, never the pass id or the entry count.

        `created` is the sum of the lead's own counts. `updated`, `questions` and `replied` come off
        the summary's totals line, `skipped` is the units it reads `verified skipped`, and in window
        3 `pages-opened`, `searches` and `reports-restored` off its `review:` line, each 0 where
        that line reads `review: not read, ...`, as on a pass whose every unit was skipped. A unit whose
        count on the record is above the one its runner verified is named under the line with both
        counts: an entry count under a prefix only grows, so a later write onto that unit's rows
        raises it, and nothing removes one. A count below the runner's is the record holding less
        than the runner verified: the line reads `lead-verified no`, and one
        `short: <window> <pass id> <unit id> record <n> runner <n>` line per such unit goes on in the
        same append, so the closing report names each first under what went wrong. The run goes on.

        Where the pass skipped BREAKER_FLOOR units or more and more than half its units, it prints,
        last, `breaker: <s> of <n> units skipped; stop the run` and one `skipped:` line per skipped
        unit with its note: a guard against a failure the reads did not name, which the lead stops on.

    python lead_pass.py wait <seconds>

        Waits that many seconds, at most WAIT_CAP, and prints one line saying how long it waited.
        It is the lead's wait between two tries of an operation that could not be made and between
        two polls of a job: a foreground command that returns by itself, under the 300,000
        milliseconds a Bash call allows, so no wait hangs on a notice that may never come.

    python lead_pass.py seen '<run folder>' <key> '<signature>'

        Remembers how long one answer has stood, across polls and sessions, so a bound the skill
        sets is counted by a script and not by the lead. It keeps `<run folder>/plan/seen.json`
        (Audience: machine), replaced whole through `ledger.publish` each time, holding for each
        key the signature last given, the UTC times it was first and last given unchanged, how
        many times in a row it was given, how many of the latest of those came with no ledger line
        added between one and the next, and the ledger's whole line count at the last. A key not
        on file, or given a different signature, starts again at once. A ledger line added between
        two times starts the last figure again at 1 and leaves the others, so a line another pass
        wrote never keeps a repeated refusal from reaching 2. A key not given for twenty minutes
        starts its minutes again and keeps its counts, so a later wait on a key of the same name
        does not open already standing. It prints one line:

            seen: <key> standing <m> minutes, <n> times in a row, <q> in a row with no ledger line added

        The key of a poll is the job (its id where the answer gives one, and otherwise the verb
        with the delivery or file it was asked about) and its signature the job's status and
        progress fields; the key of a refusal is the operation (the pass id, or the boundary
        step's name) and its signature the first line the script printed. A file in no shape this
        mode writes is read as empty.

The recheck, window r:

    The recheck of a new delivery runs its passes as window `r` (`record <ledger> r <pass id>`).
    Its units create nothing, so the lead's counts read 0 under every prefix, and its `pass:` line
    carries, after the figures every window carries, what its units found, copied off the
    summary's `recheck:` line, which the summary script counts off each unit's own report:

        pass: r <pass id> units <n> created <n> updated <n> questions <n> replied <n> skipped 0 recited <n> rows-changed <n> removed <n> not-found <n> retired <n> kept <n> refused <n> lead-verified yes

    A pass names its sheets as `<n> sheets rechecked (<sheet numbers>)`, and a retire pass its units
    as `<n> items checked for retiring`; the line under a recorded pass says the rows re-cited,
    changed, read as removed and not found, and the items retired, kept and not retired, never the
    entries.

    Before `record` and `passes` read the ledger, each holds it to the run's own copy through
    `ledger.py`, which puts back any line changed outside the run and appends its `repaired:` line;
    nothing here refuses or stops over such a change.

Exit codes:
  0  printed, and in record mode the `pass:` line appended.
  1  a named failure, one line on stderr: a read plan, ledger or summary file that is not there,
     a plan block with no `units verified:`, `summed:` or `starts after:` line, or one waiting on a
     pass the plan does not carry, a `--running` or `--reported` naming a pass the plan does not
     carry, counts that are not a JSON list of
     prefixes with whole numbers or whose prefixes are not exactly the plan block's, each once, a
     summary of another window or pass, one with no `ledger lines:` line or whose line does not
     name this ledger's first lines, one naming other units than the plan block carries, one
     with a unit it reads `verified no`, or in window `r` `verified skipped`, one with a unit it
     reads verified whose latest `verified` line past those lines reads mismatch, or one with no
     totals line, no trades line in its shape or one summed with no trades file, or in window 3
     no `review:` line, or in window r no `recheck:` line.
     In seen mode, a run folder that is not there, or a file that cannot be written.
  2  argparse rejected the invocation, a mode this script does not have among them.

Grounding role: reads files and copies byte values, and adds the counts it is given. Nothing here
fills a gap.
"""

from __future__ import annotations

import argparse
import datetime
import json
import re
import sys
import time
from pathlib import Path

# The read plan's reader is the summary script's own, so the two read a pass's units one way.
sys.path.insert(0, str(Path(__file__).resolve().parent))
import ledger as ledger_script  # noqa: E402
import pass_summary  # noqa: E402
import plan_inventory  # noqa: E402

REPORTS_FOLDER = pass_summary.REPORTS_FOLDER

# The breaker: a pass that skipped at least this many units, and more than half its units, stops
# the run. It guards against a failure no read named as a block, and it guarantees nothing.
BREAKER_FLOOR = 3

# The longest the wait mode waits, under the 300 seconds a Bash call run with a timeout of
# 300,000 milliseconds allows, so the call always returns before its timeout.
WAIT_CAP = 280

# A window 3 review's unit line as the plan script writes it, its manual pages after `reads`, and
# ` verified` added once its review verified, or ` skipped` once its reads were spent.
_REVIEW_LINE_RE = re.compile(
    r"^[1-9][0-9]*\. (\S+): (.+?), trade (.+?)(?:, reads .+)?, package \S+( verified| skipped)?$"
)

# A manual part's unit line: the review's package and trade, the unit it reads on after, and each
# span it reads, `; ` between them.
_PART_LINE_RE = re.compile(
    r"^[1-9][0-9]*\. (\S+): (.+?), trade (.+?), package \S+, manual part after (\S+), reads (.+?)( verified| skipped)?$"
)
# One span as the plan script writes it: `<code> p<first>-p<last> of <fileId>`, and where it is not
# the whole section, the section's own pages after it.
_SPAN_RE = re.compile(r"^(\S+) p([1-9][0-9]*)-p([1-9][0-9]*) of \S+(?: \(section p[1-9][0-9]*-p[1-9][0-9]*\))?$")

# A window 1 or 2 unit line as the plan script writes it: the unit id, then the sheet number, or
# `file <fileId>` on a repeated lines unit, then where it opens.
_PLAN_UNIT_RE = re.compile(r"^(\S+-[1-9][0-9]*)\. (.+?), (?:file |page |from page )")

# The figures of a `pass:` line, in its order, the window 3 pair included.
PASS_FIGURES = ("units", "created", "updated", "questions", "replied")
REVIEW_FIGURES = ("pages-opened", "searches", "reports-restored")

_SUMMARY_HEADER_RE = re.compile(r"^window: ([1-9][0-9]*|r)\s+pass: (\S+)$")
_PER_UNIT_RE = re.compile(r"^per unit: (\S+) created (\d+|-) .* verified (yes|no|skipped)$")
_TOTALS_RE = re.compile(r"updated (\d+), questions (\d+) replied (\d+)")
# One trade on a summary's trades line: a catalog id, which carries spaces, then ` x` and its count.
_TRADE_ENTRY_RE = re.compile(r"^(.+) x(\d+)$")
_REVIEW_RE = re.compile(r"^review: pages opened (\d+), searches (\d+), reports restored (\d+)$")
_LEDGER_LINES_RE = re.compile(r"^ledger lines: (\d+) sha256 ([0-9a-f]{64})$")
_RECHECK_RE = re.compile(
    r"^recheck: rows recited (\d+), updated (\d+), removed (\d+), not found (\d+); "
    r"items retired (\d+), kept (\d+), refused (\d+)$"
)

# The recheck's figures on its `pass:` line, in the order of the summary's `recheck:` line.
RECHECK_WINDOW = pass_summary.RECHECK_WINDOW
RECHECK_FIGURES = ("recited", "rows-changed", "removed", "not-found", "retired", "kept", "refused")

# A retire unit's line as recheck.py writes it.
_RETIRE_LINE_RE = re.compile(r"^(\S+-[1-9][0-9]*)\. retire, items ([1-9][0-9]*), ")


class LeadPassError(Exception):
    """A named failure with a one-line reason, reported on stderr and exiting 1."""


def _named(items: list[str]) -> str:
    return pass_summary._named(items)


def _summary_path(run_folder: Path, window: int, pass_id: str) -> Path:
    return run_folder / REPORTS_FOLDER / f"{pass_id}.md"


def _read_plan(path: Path, window: int, pass_id: str) -> dict:
    try:
        return pass_summary.read_plan(path, window, pass_id)
    except pass_summary.SummaryError as e:
        raise LeadPassError(str(e)) from None


# --------------------------------------------------------------------------- #
# passes
# --------------------------------------------------------------------------- #

def passes_lines(
    plan_path: Path, running: list[str] | None = None, reported: str | None = None
) -> list[str]:
    try:
        window, pass_ids = pass_summary.plan_passes(plan_path)
    except pass_summary.SummaryError as e:
        raise LeadPassError(str(e)) from None
    heal_ledger(plan_path.parent / plan_inventory.LEDGER_FILE)
    running = running or []
    not_planned = [pass_id for pass_id in running if pass_id not in pass_ids]
    if not_planned:
        raise LeadPassError(
            f"--running names {_named(not_planned)}, which {plan_path} does not carry; name the "
            f"passes you have out as the listing spells them"
        )
    if reported is not None and reported not in pass_ids:
        raise LeadPassError(
            f"--reported names {reported}, which {plan_path} does not carry; name the pass that "
            f"handed back as the listing spells it"
        )
    # A pass that handed back is out until it is recorded, so nothing offers it to start again.
    out = {*running, *([reported] if reported else [])}
    blocks: dict[str, dict] = {}
    for pass_id in pass_ids:
        blocks[pass_id] = _read_plan(plan_path, window, pass_id)
        for field in ("units verified", "summed", "starts after"):
            if field not in blocks[pass_id]["fields"]:
                raise LeadPassError(
                    f"{plan_path}: pass {pass_id}'s block carries no `{field}:` line, which the "
                    f"plan script writes; run the plan script again"
                )
    units_by_pass = {pass_id: block["units"] for pass_id, block in blocks.items()}
    try:
        live = plan_inventory.live_pass_state(window, units_by_pass, plan_path.parent)
        skipped_of = plan_inventory.live_pass_skipped(window, units_by_pass, plan_path.parent)
    except plan_inventory.PlanError as e:
        raise LeadPassError(str(e)) from None

    lines: list[str] = []
    prefixes_of: dict[str, str] = {}
    to_dispatch: list[str] = []
    for pass_id, block in blocks.items():
        verified, summed = live[pass_id]
        skipped = skipped_of[pass_id]
        lines.append(
            f"{pass_id}: units {block['fields']['units']}, units verified {verified}, units skipped "
            f"{skipped}, summed {summed}"
        )
        prefixes = [f"scopeItem:{unit}-" for unit in block["units"]]
        prefixes_of[pass_id] = f"{pass_id} prefixes: {json.dumps(prefixes)}"
        lines.append(prefixes_of[pass_id])
        # Settled is verified or skipped; a skipped unit holds its pass open nowhere but window r,
        # whose units are never skipped.
        if not (verified + skipped == len(block["units"]) and summed == "yes"):
            to_dispatch.append(pass_id)
    finished = len(pass_ids) - len(to_dispatch)
    closing = [
        f"passes {len(pass_ids)}, finished {finished}; to dispatch: "
        + (", ".join(to_dispatch) if to_dispatch else "none")
    ]

    ready: list[str] = []
    for pass_id in to_dispatch:
        waits_on = [
            other.strip() for other in blocks[pass_id]["fields"]["starts after"].split(",")
            if other.strip() and other.strip() != "none"
        ]
        gone = [other for other in waits_on if other not in blocks]
        if gone:
            raise LeadPassError(
                f"{plan_path}: pass {pass_id} waits on {_named(gone)}, which the plan does not "
                f"carry; run the plan script again"
            )
        if pass_id not in out and not any(other in to_dispatch for other in waits_on):
            ready.append(pass_id)
    out_now = len({pass_id for pass_id in out if pass_id in to_dispatch})
    ready = ready[:max(0, plan_inventory.PASSES_AT_ONCE - out_now)]

    waiting = [pass_id for pass_id in to_dispatch if pass_id not in out and pass_id not in ready]
    closing.append(f"start now: {', '.join(ready) or 'none'}")
    closing.append(f"waiting: {', '.join(waiting) or 'none'}")
    if reported is not None:
        return [prefixes_of[reported], *closing]
    return [*lines, *closing]


# --------------------------------------------------------------------------- #
# record
# --------------------------------------------------------------------------- #

def _parse_counts(text: str, pass_id: str, units: list[str]) -> dict[str, int]:
    """Each unit's count, keyed by the prefix the `count_entries` answer gives it, never by place."""
    to_pass = "; pass the `counts` array of the `count_entries` answer as it came back"
    try:
        answer = json.loads(text)
    except json.JSONDecodeError as e:
        raise LeadPassError(f"--counts-json is not JSON ({e.msg}){to_pass}") from None
    if not isinstance(answer, list):
        raise LeadPassError(f"--counts-json is not a list{to_pass}")
    by_prefix: dict[str, int] = {}
    twice: list[str] = []
    for at, count in enumerate(answer, 1):
        prefix = count.get("subjectPrefix") if isinstance(count, dict) else None
        number = count.get("entryCount") if isinstance(count, dict) else None
        if not isinstance(prefix, str) or type(number) is not int or number < 0:
            raise LeadPassError(
                f"--counts-json count {at} reads {json.dumps(count)}, which is not a "
                f"`subjectPrefix` with a whole number `entryCount`{to_pass}"
            )
        if prefix in by_prefix and prefix not in twice:
            twice.append(prefix)
        by_prefix[prefix] = number
    wanted = {f"scopeItem:{unit}-": unit for unit in units}
    missing = [prefix for prefix in wanted if prefix not in by_prefix]
    extra = [prefix for prefix in by_prefix if prefix not in wanted]
    if missing or extra or twice:
        differences = [f"missing {_named(missing)}"] if missing else []
        differences += [f"not in the pass {_named(extra)}"] if extra else []
        differences += [f"given twice {_named(twice)}"] if twice else []
        raise LeadPassError(
            f"--counts-json names other prefixes than pass {pass_id}'s plan block: "
            + "; ".join(differences)
            + "; take the counts again with the prefixes the passes listing prints for the pass"
        )
    return {unit: by_prefix[prefix] for prefix, unit in wanted.items()}


def read_summary(path: Path, window: int, pass_id: str) -> dict:
    """The figures `record` compares and copies, off the summary the pass's runner wrote."""
    if not path.is_file():
        raise LeadPassError(f"no summary on file at {path}; the pass's runner writes it")
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except Exception as e:
        raise LeadPassError(f"cannot read the summary at {path}: {e}") from e

    header = _SUMMARY_HEADER_RE.match(lines[0].strip()) if lines else None
    if header is None:
        raise LeadPassError(f"{path} does not open with `window: <n>   pass: <pass id>`")
    if pass_summary._window_of(header.group(1)) != window or header.group(2) != pass_id:
        raise LeadPassError(
            f"{path} is the summary of window {header.group(1)} pass {header.group(2)}, and this is "
            f"window {window} pass {pass_id}"
        )

    per_unit: dict[str, tuple[str, str]] = {}
    totals = review = trades = recheck = ledger_lines = trades_text = None
    for raw in lines:
        line = raw.strip()
        unit = _PER_UNIT_RE.match(line)
        if unit:
            per_unit[unit.group(1)] = (unit.group(2), unit.group(3))
        elif line.startswith("totals verified:"):
            totals = _TOTALS_RE.search(line)
        elif line.startswith("trades:"):
            trades_text = line
            trades = _trades_of(line)
        elif line == pass_summary.REVIEW_NOT_READ_LINE:
            # No review of the pass read ok, as where every unit was skipped: no pages and no
            # searches were measured, and the pass is recorded with its skipped count all the same.
            review = _REVIEW_RE.match("review: pages opened 0, searches 0, reports restored 0")
        elif line.startswith("review:"):
            review = _REVIEW_RE.match(line)
        elif line.startswith("recheck:"):
            recheck = _RECHECK_RE.match(line)
        elif line.startswith("ledger lines:"):
            ledger_lines = _LEDGER_LINES_RE.match(line)
    if ledger_lines is None:
        raise LeadPassError(
            f"{path} carries no `ledger lines: <n> sha256 <hash>` line, so nothing shows which "
            f"ledger it was summed off; the pass is summed again off the run folder's ledger"
        )
    if totals is None:
        raise LeadPassError(f"{path} carries no totals line")
    if trades_text is None:
        raise LeadPassError(f"{path} carries no trades line")
    if trades_text == pass_summary.TRADES_NO_FILE_LINE:
        raise LeadPassError(
            f"{path}: its trades line reads `{trades_text}`, so the runner summed the pass with no "
            f"trades file and the pass has no item count"
        )
    if trades is None:
        raise LeadPassError(
            f"{path}: its trades line reads {trades_text[:80]!r}, and the summary script writes "
            f"`trades: <catalog id> x<n>, ...` or `{pass_summary.TRADES_NONE_LINE}`"
        )
    if window == 3 and review is None:
        raise LeadPassError(
            f"{path} carries no `review: pages opened <n>, searches <n>, reports restored <n>` line"
        )
    if window == RECHECK_WINDOW and recheck is None:
        raise LeadPassError(f"{path} carries no `recheck: rows ...; items ...` line, the counts its units found")
    return {
        "perUnit": per_unit,
        "updated": totals.group(1),
        "questions": totals.group(2),
        "replied": totals.group(3),
        "items": sum(trades.values()),
        "pagesOpened": review.group(1) if review else None,
        "searches": review.group(2) if review else None,
        "reportsRestored": review.group(3) if review else None,
        "recheck": dict(zip(RECHECK_FIGURES, recheck.groups())) if recheck else None,
        "ledgerLines": int(ledger_lines.group(1)),
        "ledgerHash": ledger_lines.group(2),
    }


def _summed_off(ledger: Path, summary_path: Path, summary: dict) -> bytes:
    """
    The summary was summed off this ledger: its first lines, as many as the summary counted, hash
    as the summary says. The ledger is only ever appended, so the lines a runner summed stay as
    they were while later passes write after them. Returns the ledger's bytes.
    """
    if not ledger.is_file():
        raise LeadPassError(f"no ledger at {ledger}")
    try:
        data = ledger.read_bytes()
    except OSError as e:
        raise LeadPassError(f"cannot read the ledger at {ledger}: {e}") from e
    digest = pass_summary.ledger_digest(data, summary["ledgerLines"])
    if digest != summary["ledgerHash"]:
        raise LeadPassError(
            f"{summary_path} was summed from another ledger: its first {summary['ledgerLines']} "
            f"lines are not the first lines of {ledger}; the pass is summed again off that ledger, "
            f"and nothing was written to it"
        )
    return data


def _mismatched_since(data: bytes, lines: int, window: int, units: list[str]) -> list[str]:
    """
    The units, of those given, whose latest `verified` line of this window past the ledger's first
    `lines` lines reads anything but `result ok`: a unit checked again after its summary was
    written, and found wanting, which that summary cannot speak for. Only whole lines, each ending
    in a newline, are read, as the summary script reads them, so a line another runner is still
    appending is not read until it is whole.
    """
    whole = data[: data.rfind(b"\n") + 1]
    later = whole.split(b"\n")[lines:]
    latest: dict[str, bool] = {}
    for raw in later:
        parts = raw.decode("utf-8", errors="replace").strip().split()
        if len(parts) >= 4 and parts[0] == "verified" and parts[1] == str(window) and parts[3] in units:
            latest[parts[3]] = "result" in parts and parts[parts.index("result") + 1:][:1] == ["ok"]
    return [unit for unit in units if latest.get(unit) is False]


def heal_ledger(ledger: Path) -> list[str]:
    """
    Hold the ledger to the run's own copy before reading it, as `ledger.py` does before every
    append, and say in the estimator's words where it put lines back.
    """
    try:
        healed = ledger_script.heal(ledger)
    except ledger_script.LedgerError as e:
        raise LeadPassError(str(e)) from None
    return [] if healed is None else [repaired_said(healed)]


def repaired_said(line: str) -> str:
    """A `repaired:` line as the estimator hears it."""
    match = ledger_script.REPAIRED_RE.match(line.strip())
    if match is None:
        return f"the run's log: {line.strip()}"
    count, first = match.groups()
    if count == "1":
        return f"the run's log: 1 line of it was changed outside the run and was put back, line {first}"
    return (
        f"the run's log: {count} lines of it were changed outside the run and were put back, the "
        f"first at line {first}"
    )


def record(ledger: Path, window: int, pass_id: str, plan_path: Path, counts_text: str) -> list[str]:
    healed = heal_ledger(ledger)
    plan = _read_plan(plan_path, window, pass_id)
    units = plan["units"]
    counts = _parse_counts(counts_text, pass_id, units)
    summary_path = _summary_path(ledger.parent, window, pass_id)
    summary = read_summary(summary_path, window, pass_id)
    data = _summed_off(ledger, summary_path, summary)

    named = list(summary["perUnit"])
    without = [unit for unit in units if unit not in named]
    beyond = [unit for unit in named if unit not in units]
    if without or beyond:
        differences = [f"without {', '.join(without)}"] if without else []
        differences += [f"beyond {', '.join(beyond)}"] if beyond else []
        raise LeadPassError(
            f"{summary_path} reads other units than the plan block carries: "
            + "; ".join(differences) + "; the pass is dispatched again for a new summary"
        )
    # A skipped unit is settled in windows 1, 2 and 3: its writes stay on the record and its pass is
    # finished without it. In window r no unit is skipped, and one whose reads are spent stops the
    # recheck, so it is refused here as any unit not verified is.
    skipped = [
        unit for unit in units
        if summary["perUnit"][unit][1] == "skipped" and window != RECHECK_WINDOW
    ]
    unverified = [unit for unit in units if summary["perUnit"][unit][1] != "yes" and unit not in skipped]
    if unverified:
        raise LeadPassError(
            f"{summary_path} reads verified no for {_named(unverified)}, so the pass gets no "
            f"pass line until its runner verifies every unit"
            + (", and in the recheck a unit whose reads are spent stops it" if window == RECHECK_WINDOW else "")
        )
    checked_again = _mismatched_since(data, summary["ledgerLines"], window, [u for u in units if u not in skipped])
    if checked_again:
        raise LeadPassError(
            f"{summary_path} reads verified yes for {_named(checked_again)}, and a later verified "
            f"line on {ledger} reads mismatch for it, so the pass gets no pass line until its "
            f"runner verifies every unit"
        )

    below: list[tuple[str, int, int]] = []
    above: list[str] = []
    for unit in units:
        count = counts[unit]
        summed = summary["perUnit"][unit][0]
        # A skipped unit whose last read carries no verified line has no count to hold it to.
        if summed == "-":
            continue
        verified = int(summed)
        # A skipped unit's last check found a mismatch, so its count is a floor and never more.
        if count < verified:
            below.append((unit, count, verified))
        elif count > verified and unit not in skipped:
            above.append(f"{unit} {count} on the record, {verified} when its runner verified it")

    if not ledger.is_file():
        raise LeadPassError(f"no ledger at {ledger}")
    figures = [
        ("units", str(len(units))),
        ("created", str(sum(counts.values()))),
        ("updated", summary["updated"]),
        ("questions", summary["questions"]),
        ("replied", summary["replied"]),
        ("skipped", str(len(skipped))),
    ]
    if window == 3:
        figures += [
            ("pages-opened", summary["pagesOpened"]), ("searches", summary["searches"]),
            ("reports-restored", summary["reportsRestored"]),
        ]
    if window == RECHECK_WINDOW:
        figures += list(summary["recheck"].items())
    line = f"pass: {window} {pass_id} " + " ".join(f"{k} {v}" for k, v in figures)
    # The record holding less than a runner verified is written down where it is found, and the run
    # goes on; the closing report names it first under what went wrong.
    line += " lead-verified no" if below else " lead-verified yes"
    shorts = [f"short: {window} {pass_id} {unit} record {count} runner {verified}" for unit, count, verified in below]

    # Through the ledger script, as every line goes on: under its lock, checked, its shadow first.
    try:
        ledger_script.append_lines(ledger, [line, *shorts])
    except ledger_script.LedgerError as e:
        raise LeadPassError(f"cannot append to the ledger at {ledger}: {e}") from None

    # The pass as the estimator hears it, for the one line the lead says as each pass is recorded.
    reads = _plan_reads(plan_path, window, _verified_ok(ledger, window) if window == 3 else frozenset())[0]
    said = {field: int(value) for field, value in figures if field in PASS_FIGURES + RECHECK_FIGURES}
    words = _said_recheck(said) if window == RECHECK_WINDOW else _said_figures(summary["items"], said)
    if skipped:
        words += f", read twice and not confirmed {len(skipped)}, named in the closing report"
    out = [line, *shorts, f"{reads.get(pass_id, 'nothing planned')}: {words}"]
    out.extend(f"above the runner's count: {entry}" for entry in above)
    out.extend(healed)
    if len(skipped) >= BREAKER_FLOOR and 2 * len(skipped) > len(units):
        notes = plan_inventory.settled_units(ledger, window)[1]
        out.append(f"breaker: {len(skipped)} of {len(units)} units skipped; stop the run")
        out.extend(f"skipped: {unit} {notes.get(unit, 'read twice, not read again')}" for unit in skipped)
    return out


# --------------------------------------------------------------------------- #
# What a pass read, in the estimator's words
# --------------------------------------------------------------------------- #

def _trades_of(line: str) -> dict[str, int] | None:
    """
    A summary's trades line as item counts by catalog id, empty where its units created no item on
    any trade, or None where it was summed with no trades file or is in no shape the summary writes.
    """
    if line == pass_summary.TRADES_NONE_LINE:
        return {}
    by_trade: dict[str, int] = {}
    for entry in line[len("trades: "):].split(", "):
        match = _TRADE_ENTRY_RE.match(entry)
        if match is None:
            return None
        by_trade[match.group(1)] = by_trade.get(match.group(1), 0) + int(match.group(2))
    return by_trade


def _verified_ok(ledger: Path, window: int) -> set[str]:
    """
    This window's unit ids whose latest `verified` line reads `result ok`, whatever pass it names,
    the way the plan script reads them: a unit read again carries a line for each check, and the
    last one says whether it is finished. The ledger is where a runner writes it; the read plan
    carries it only once the window is planned again, which the lead does not do between passes.
    """
    try:
        text = ledger.read_text(encoding="utf-8")
    except OSError:
        return set()
    last_ok: dict[str, bool] = {}
    for raw in text.splitlines():
        parts = raw.strip().split()
        if len(parts) >= 4 and parts[0] == "verified" and parts[1] == str(window):
            last_ok[parts[3]] = "result" in parts and parts[parts.index("result") + 1:][:1] == ["ok"]
    return {unit for unit, ok in last_ok.items() if ok}


def _counts_off_restored(run_folder: Path, unit: str) -> bool:
    """
    Whether a window 3 unit's latest verified read counts off its restored report, by the summary
    script's own selection: the reader's report of that read where the report check holds it
    whole, and the restored one of that read only where it does not. An earlier read's restored
    report says nothing about a later read that left a whole report.
    """
    try:
        history = pass_summary.unit_report_script.unit_history(run_folder / pass_summary.LEDGER_NAME, "3", unit)
    except pass_summary.unit_report_script.ReportError:
        return False
    if history["latest"] is None:
        return False
    read, _verified = history["latest"]
    _path, restored, _problems = pass_summary.report_of_read(
        run_folder / REPORTS_FOLDER, unit, read, history["dispatches"], "manual",
    )
    return restored


def _plan_reads(
    plan_path: Path, window: int, verified: set[str] | frozenset[str] = frozenset(),
) -> tuple[dict[str, str], dict[str, str]]:
    """
    What each pass of the read plan beside the ledger read, in the words the lead says it in as the
    pass is recorded, and what each unit id names: a sheet's number, the file a repeated lines unit
    reads, or a review's package. Both are empty where the plan is not this window's or is not
    there, and the pass is then named by id alone. A window 3 pass names the manual pages each of its manual
    parts read, once the part is in `verified`, this window's units verified ok on the ledger.
    """
    try:
        lines = plan_path.read_text(encoding="utf-8").splitlines()
    except OSError:
        return {}, {}
    first = next((line.strip() for line in lines if line.strip()), "")
    if first != f"# Read plan: window {window}":
        return {}, {}
    sheets: dict[str, list[str]] = {}
    files: dict[str, int] = {}
    retire_items: dict[str, int] = {}
    packages: dict[str, list[str]] = {}
    read_on: dict[str, list[str]] = {}
    restored_on: dict[str, list[str]] = {}
    named: dict[str, str] = {}
    current = None
    for raw in lines:
        line = raw.strip()
        if line == pass_summary._LEFT_OUT_HEADING:
            break
        heading = pass_summary._PASS_HEADING_RE.match(raw)
        if heading:
            current = heading.group(1)
            sheets[current], files[current], packages[current], read_on[current] = [], 0, [], []
            restored_on[current] = []
            retire_items[current] = 0
            continue
        if current is None:
            continue
        # A manual part names the pages it read, for its package, once it verified ok; the
        # file is the runner's, and the estimator hears the section and its pages.
        part = _PART_LINE_RE.match(line) if window == 3 else None
        if part:
            if part.group(1) in verified:
                # A part whose latest verified read counts off a report the run restored from the
                # record is named apart: no reader's report says which of its pages were read.
                restored = _counts_off_restored(plan_path.parent, part.group(1))
                (restored_on if restored else read_on)[current].extend(
                    f"{span.group(1)} pages {span.group(2)} to {span.group(3)} for {part.group(2)}"
                    for span in map(_SPAN_RE.match, part.group(5).split("; ")) if span
                )
            named[part.group(1)] = part.group(2)
            continue
        review = _REVIEW_LINE_RE.match(line) if window == 3 else None
        if review:
            packages[current].append(f"{review.group(2)}, trade {review.group(3)}")
            named[review.group(1)] = review.group(2)
            continue
        retire = _RETIRE_LINE_RE.match(line) if window == RECHECK_WINDOW else None
        if retire:
            retire_items[current] += int(retire.group(2))
            named[retire.group(1)] = "the items checked for retiring"
            continue
        unit = _PLAN_UNIT_RE.match(line)
        if unit is None:
            continue
        if unit.group(2).startswith("file ") and ", from page " in line:
            files[current] += 1
            named[unit.group(1)] = "the repeated lines of one drawing file"
        else:
            sheets[current].append(unit.group(2))
            named[unit.group(1)] = unit.group(2)
    reads: dict[str, str] = {}
    for pass_id in sheets:
        parts = []
        if packages[pass_id]:
            parts.append(
                f"{len(packages[pass_id])} package{'' if len(packages[pass_id]) == 1 else 's'} reviewed "
                f"({'; '.join(packages[pass_id])})"
            )
        if read_on[pass_id]:
            parts.append(f"manual pages read ({'; '.join(read_on[pass_id])})")
        if restored_on[pass_id]:
            parts.append(
                f"manual pages whose report was written from the record ({'; '.join(restored_on[pass_id])})"
            )
        if sheets[pass_id]:
            parts.append(
                f"{len(sheets[pass_id])} sheet{'' if len(sheets[pass_id]) == 1 else 's'} "
                f"{'rechecked' if window == RECHECK_WINDOW else 'read'} ({', '.join(sheets[pass_id])})"
            )
        if retire_items[pass_id]:
            parts.append(
                f"{retire_items[pass_id]} item{'' if retire_items[pass_id] == 1 else 's'} checked for retiring"
            )
        if files[pass_id]:
            parts.append(
                f"the repeated lines of {files[pass_id]} drawing file{'' if files[pass_id] == 1 else 's'} read"
            )
        reads[pass_id] = " and ".join(parts) or "nothing planned"
    return reads, named


def _said_figures(items: int | None, figures: dict[str, int]) -> str:
    """A pass line's figures as the estimator hears them, the new items off the summaries' trades."""
    return (
        (f"new items {items}" if items is not None else "new items not counted, a summary or its trades count missing")
        + f", items updated {figures['updated']}, Questions raised {figures['questions']}, "
        f"replies {figures['replied']}"
    )


def _said_recheck(figures: dict[str, int]) -> str:
    """A recheck pass line's figures as the estimator hears them, rows and items apart."""
    return (
        f"rows cited again {figures['recited']}, rows changed {figures['rows-changed']}, rows read "
        f"as removed {figures['removed']}, rows not found {figures['not-found']}, items retired "
        f"{figures['retired']}, items kept on a current sheet {figures['kept']}, items not retired "
        f"{figures['refused']}, Questions raised {figures['questions']}, replies {figures['replied']}"
    )


# --------------------------------------------------------------------------- #
# seen: how long one answer has stood
# --------------------------------------------------------------------------- #

SEEN_NAME = "seen.json"
_STAMP = "%Y-%m-%dT%H:%M:%SZ"
# Polls of one job are a minute apart; a key not given for this long belongs to an earlier wait.
SEEN_GAP_SECONDS = 20 * 60


def _stamp_of(value: object) -> datetime.datetime | None:
    try:
        return datetime.datetime.strptime(str(value), _STAMP).replace(tzinfo=datetime.timezone.utc)
    except ValueError:
        return None


def _utc_now() -> datetime.datetime:
    return datetime.datetime.now(datetime.timezone.utc).replace(microsecond=0)


def _ledger_line_count(run_folder: Path) -> int:
    """The ledger's whole lines, a last line with no newline left out; a missing ledger is 0."""
    path = run_folder / pass_summary.LEDGER_NAME
    try:
        data = path.read_bytes() if path.is_file() else b""
    except OSError as e:
        raise LeadPassError(f"cannot read {path}: {e}") from e
    return data.count(b"\n")


def seen(run_folder: Path, key: str, signature: str) -> str:
    """Record one more time `key` was given `signature`, and say how long and how often it has stood."""
    if not run_folder.is_dir():
        raise LeadPassError(f"{run_folder} is not a run folder")
    path = run_folder / "plan" / SEEN_NAME
    try:
        kept = json.loads(path.read_text(encoding="utf-8")) if path.is_file() else {}
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        kept = {}
    if not isinstance(kept, dict):
        kept = {}
    now = _utc_now()
    lines = _ledger_line_count(run_folder)
    entry = kept.get(key)
    first = last = None
    if isinstance(entry, dict) and entry.get("signature") == signature:
        first = _stamp_of(entry.get("first"))
        last = _stamp_of(entry.get("last")) or first
    if first is not None and isinstance(entry.get("times"), int) and isinstance(entry.get("ledgerLines"), int):
        quiet = entry.get("quiet") if isinstance(entry.get("quiet"), int) else 1
        # The streak with no ledger line between two times starts again whenever a line was added,
        # so it reaches two as soon as two refusals in a row have no line between them; lines
        # other passes keep writing put that off and never rule it out.
        quiet = quiet + 1 if lines == entry["ledgerLines"] else 1
        # A key left for longer than polls are ever apart is a new wait: its minutes start again.
        if (now - last).total_seconds() > SEEN_GAP_SECONDS:
            first = now
        times = entry["times"] + 1
    else:
        first = now
        times = quiet = 1
    entry = {
        "signature": signature, "first": first.strftime(_STAMP), "last": now.strftime(_STAMP),
        "times": times, "quiet": quiet, "ledgerLines": lines,
    }
    kept[key] = entry
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        ledger_script.publish(path, (json.dumps(kept, indent=2, sort_keys=True) + "\n").encode("utf-8"))
    except (OSError, ledger_script.LedgerError) as e:
        raise LeadPassError(f"cannot write {path}: {e}") from e
    minutes = max(0, int((now - first).total_seconds() // 60))
    return (
        f"seen: {key} standing {minutes} minute{'' if minutes == 1 else 's'}, {times} "
        f"time{'' if times == 1 else 's'} in a row, {quiet} in a row with no ledger line added"
    )


# --------------------------------------------------------------------------- #
# Entry point
# --------------------------------------------------------------------------- #

def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="The lead's own reads and writes for the passes of a scope run.",
    )
    modes = parser.add_subparsers(dest="mode", required=True)

    passes = modes.add_parser("passes", help="every pass the read plan carries and its prefixes")
    passes.add_argument("--plan", type=Path, required=True, help="the window's read-plan.md")
    passes.add_argument(
        "--running", default="",
        help="the passes you started and have not recorded, comma separated",
    )
    passes.add_argument(
        "--reported",
        help="the pass that just handed back; prints only its prefixes and the three closing lines",
    )

    rec = modes.add_parser("record", help="compare a pass's counts and append its pass line")
    rec.add_argument("ledger", type=Path, help="the run folder's ledger.md")
    rec.add_argument("window", type=pass_summary.parse_window, help="the window the pass belongs to: 1, 2, 3, or r")
    rec.add_argument("pass_id", metavar="pass", help="the pass id, exactly as the plan spells it")
    rec.add_argument("--plan", type=Path, required=True, help="the window's read-plan.md")
    rec.add_argument(
        "--counts-json", required=True,
        help="the `counts` array of the `count_entries` answer for the pass, as it came back",
    )

    wait = modes.add_parser("wait", help=f"wait up to {WAIT_CAP} seconds, then print one line")
    wait.add_argument("seconds", type=int, help=f"how long to wait, at most {WAIT_CAP}")

    held = modes.add_parser("seen", help="say how long and how often one answer has stood, and remember it")
    held.add_argument("run_folder", type=Path, help="the run folder")
    held.add_argument("key", help="the job polled, or the operation refused")
    held.add_argument("signature", help="the job's status and progress fields, or the first line the script printed")

    args = parser.parse_args(argv)

    if args.mode == "wait":
        seconds = max(0, min(args.seconds, WAIT_CAP))
        time.sleep(seconds)
        print(f"waited {seconds} seconds" + (", the most this waits" if args.seconds > WAIT_CAP else ""))
        return 0

    try:
        if args.mode == "passes":
            lines = passes_lines(
                args.plan, [pass_id.strip() for pass_id in args.running.split(",") if pass_id.strip()],
                args.reported,
            )
        elif args.mode == "record":
            lines = record(args.ledger, args.window, args.pass_id, args.plan, args.counts_json)
        elif args.mode == "seen":
            lines = [seen(args.run_folder, args.key, args.signature)]
    except LeadPassError as e:
        print(f"lead_pass: {e}", file=sys.stderr)
        return 1
    for line in lines:
        print(line)
    return 0


if __name__ == "__main__":
    sys.exit(main())
