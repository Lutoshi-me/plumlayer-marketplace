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

Three modes:

    python lead_pass.py passes --plan <run folder>/read-plan.md [--running <pass id>,<pass id>]
        [--reported <pass id>]

        Every pass the read plan carries, in its order, two lines each:

            <pass id>: units <n>, units verified <k>, summed <yes, or no and why>
            <pass id> prefixes: ["scopeItem:<unit id>-", ...]

        then `passes <n>, finished <k>; to dispatch: <pass ids, or none>`, and what the lead does
        next, off the plan's `starts after:` lines and the ledger beside it:

            start now: <pass ids, or none>
            waiting: <pass ids, or none>
            since the last check-in: <pass ids, or none>
            check-in due: <yes or no>

        A pass is finished where its `units:` and `units verified:` agree and it reads `summed: yes`,
        the rule the skill gives. Those two values are taken as a plan run would write them now, off
        the ledger and the summaries on file, since the plan file is rewritten only by a plan run; a
        plan with no ledger yet has nothing finished. The prefixes are built from the unit ids the
        plan block carries, in its order.

        `--running` is the passes the lead started and has not recorded. `start now:` is the passes
        not finished, not running and with every pass on their `starts after:` line finished, in
        plan order, cut to PASSES_AT_ONCE less the count running, in every window. `waiting:` is
        every other pass not finished and not running.

        `--reported` is the pass that just handed back. It prints only that pass's prefixes line,
        read off the plan at this call, so a window 3 manual part a replan put in the pass is in it,
        then the five closing lines, `passes` through `check-in due:`. A pass the plan does not carry
        is refused. It counts as running until it is recorded, so it is never offered to start.

        `since the last check-in:` is what the lead hands to `checkin --passes`: the passes with a
        `pass:` line of this window since the last check-in was shown, last recorded last. A
        `checkin:` line is appended when the user answers, so a pass recorded while the check-in
        stood open sits above it; the line's second field names the last pass recorded when it was
        shown, and this reads from that pass's line, from the window's first line where the field
        reads `none`, and from the `checkin:` line itself otherwise. With no `checkin:` line of this
        window it reads every `pass:` line of the window.

        `check-in due:` is yes in windows 2 and 3 where CHECK_IN_EVERY `pass:` lines or more of this
        window sit after its last `checkin:` line, a pass run again counted at each of its lines, and
        always no in window 1, which has no check-in inside it. Where one is due, `start now:` reads
        `none, a check-in is due`, and every pass not finished and not running goes on `waiting:`.

        A plan with no pass, as window 2's is where window 1 selected or left out every sheet, prints
        `passes 0, finished 0; to dispatch: none` and those four lines, each reading none or no.

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
        Where every count holds, it appends one `pass:` line to the ledger and prints it:

            pass: <window> <pass id> units <n> created <n> updated <n> questions <n> replied <n> lead-verified yes
            pass: 3 <pass id> units <n> created <n> updated <n> questions <n> replied <n> pages-opened <n> searches <n> reports-restored <n> lead-verified yes

        The line goes on through `ledger.py`'s append, under its lock and checked, as every line
        of the ledger does.

        Under it, it prints the pass as the estimator hears it, the line the check-in prints for
        it below, with the new items off the summary's trades line, so the one line the lead says
        as the pass is recorded names the sheets or packages and the items, never the pass id or
        the entry count.

        `created` is the sum of the lead's own counts. `updated`, `questions` and `replied` come off
        the summary's totals line, and in window 3 `pages-opened`, `searches` and
        `reports-restored` off its `review:` line. A unit whose count on the record is above the one its
        runner verified is named under the line with both counts: an entry count under a prefix only
        grows, so a later write onto that unit's rows raises it, and nothing removes one. A count
        below the runner's is the record holding less than the runner verified: the script writes
        nothing, names each such unit with both counts, and exits 3, and the run stops there.

    python lead_pass.py checkin <run folder> <window> --passes <pass id>,<pass id>,...
        [--start <lines>[:<characters>]]

        What the check-in needs, off the ledger's `pass:` lines, the read plan beside them and the
        summaries on file. Each pass by what it read, the sheet numbers its block carries or in
        window 3 its packages, with its last `pass:` line's figures in the estimator's words, and
        its id only on the lead's own line:

            window <n>, <n> passes
            <n> sheets read (<sheet numbers>): new items <n>, items updated <n>, Questions raised <n>, replies <n>
            over <n> passes: new items <n>, items updated <n>, Questions raised <n>, replies <n>
            your own check over <n> pass lines (<pass ids>), never said to the estimator: units <n>, entries <n>

        The new items are the summaries' `trades:` lines summed, each a subject the pass's runner
        found on the record. A pass line's `created` counts entries, every citation and trade
        written with those items, so it goes on the lead's own line and never reads as items; in
        window 3 that line adds the pages opened and the searches. Then the items by trade summed
        off the same lines, the anomalies already on the record as counts, and every other note
        line of each summary, under its pass, each copied whole under the label CHECKIN_LABELS
        gives it, less the unit id it opens with, which a window 3 note trades for its package's
        name.

        An anomaly ends with where it landed, after a comma, as the reader's and the reviewer's
        report shapes ask. One that ends `Question <id>` or `reply <id>` is on a trade's
        page, where the estimator reads it, so it is counted rather than printed, where the id is
        one the record writes: a Question's id as `ask_question` returns it,
        `question:proj-<uuid>:<uuid>`; and after `reply`, that id or the reply's own entry id,
        `clm-<uuid>`. No agent of the run writes a note on a row, so no ending names one. Any
        other ending prints whole, a placeholder such as `Question <id>` and a row's subject
        among them:

            on the record: Questions <n>, replies <n>, in pass <pass id>
            on the record: Questions <n>, replies <n>, in the review of <package name>, trade <catalog id>
            on the record over these passes: Questions <n>, replies <n>

        A window 3 anomaly is counted under the review its unit id names on the read plan beside
        the ledger; any other anomaly, and one whose unit the plan does not name, under its pass.
        One that names a pair of rows carrying the same work prints whole, ending `run only`,
        since the estimator reads which row a review kept, and so does one ending `sheet reading` or
        `run only`, or with an ending this does not read. A line under a note that opens with
        none of the summary's labels continues that note, so an anomaly carrying one prints
        whole, its continuation under it, since its last words are not where it landed. Every
        overlap, unread page, grain question, door-owned suggestion, definitions kind and
        deviation line prints whole, with any continuation under it.

        In window 3 the pass is named by the manual pages its manual parts read, each part's spans
        once its `verified` line reads ok (`manual pages read (230000 pages 900 to 915 for HVAC)`),
        beside the packages it reviewed; a part not verified is not named there, and a part whose
        latest verified read counts off a report the run restored from the record, by the summary
        script's own selection, is named under `manual pages whose report was written from the
        record`. A manual part's counts fall under its package's review.

        Each `repaired:` line `ledger.py` appended since the last `checkin:` line prints in the
        estimator's words, `the run's log: <n> lines of it were changed outside the run and were
        put back, the first at line <i>`.

    Before `record`, `passes` and `checkin` read the ledger, each holds it to the run's own copy
    through `ledger.py`, which puts back any line changed outside the run and appends its
    `repaired:` line; nothing here refuses or stops over such a change.

        Output stops before CHECKIN_CAP characters, below the 30,000 a Bash call returns, every
        printed line counted, the closing line included, and its last line names the passes it did
        not print and the command that prints the rest. A note longer than the room a call has
        left once nothing else is printed is cut there, with a line under it naming the pass, the
        note and the character it stops at, and the next call prints the rest of it. `--start` is
        how many of the first pass's printed lines an earlier call already printed, and after a
        colon (`--start 4:23000`) how many characters of the line after them.

The recheck, window r:

    The recheck of a new delivery runs its passes as window `r` (`record <ledger> r <pass id>`,
    `checkin <run folder> r`). Its units create nothing, so the lead's counts read 0 under every
    prefix, and its `pass:` line carries, after the figures every window carries, what its units
    found, copied off the summary's `recheck:` line, which the summary script counts off each
    unit's own report:

        pass: r <pass id> units <n> created <n> updated <n> questions <n> replied <n> recited <n> rows-changed <n> removed <n> not-found <n> retired <n> kept <n> refused <n> lead-verified yes

    A pass names its sheets as `<n> sheets rechecked (<sheet numbers>)`, and a retire pass its units
    as `<n> items checked for retiring`; the line under a recorded pass, and each pass of a
    check-in, says the rows re-cited, changed, read as removed and not found, and the items
    retired, kept and not retired, never the entries.

Exit codes:
  0  printed, and in record mode the `pass:` line appended.
  1  a named failure, one line on stderr: a read plan, ledger or summary file that is not there,
     a plan block with no `units verified:`, `summed:` or `starts after:` line, or one waiting on a
     pass the plan does not carry, a `--running` or `--reported` naming a pass the plan does not
     carry, counts that are not a JSON list of
     prefixes with whole numbers or whose prefixes are not exactly the plan block's, each once, a
     summary of another window or pass, one with no `ledger lines:` line or whose line does not
     name this ledger's first lines, one naming other units than the plan block carries, one
     with a unit it reads `verified no`, one with a unit it reads verified whose latest
     `verified` line past those lines reads mismatch, or one with no totals line, no trades line in
     its shape or one summed with no trades file, or in
     window 3 no `review:` line, or in window r no `recheck:` line; at the check-in, a `--start` that is not a count of lines and
     characters or names a character past its line, and pass lines and totals that alone leave no
     room under the cap.
  2  argparse rejected the invocation.
  3  record mode only: a count below the one its runner verified. Nothing was written.

Grounding role: reads files and copies byte values, and adds the counts it is given. Nothing here
fills a gap: a pass with no `pass:` line or no summary on file is named as one at the check-in.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

# The read plan's reader is the summary script's own, so the two read a pass's units one way.
sys.path.insert(0, str(Path(__file__).resolve().parent))
import ledger as ledger_script  # noqa: E402
import pass_summary  # noqa: E402
import plan_inventory  # noqa: E402

REPORTS_FOLDER = pass_summary.REPORTS_FOLDER

# How many `pass:` lines land between check-ins inside windows 2 and 3.
CHECK_IN_EVERY = 4

# Under the 30,000 characters a Bash call returns. Every line a check-in call prints counts
# against it, the closing line included.
CHECKIN_CAP = 25_000

# The summary lines a check-in carries, in the order the summary prints them, each with the label
# the check-in prints it under, in the estimator's words, since the person watching reads what it
# prints. The note behind the label is copied whole, as the reader wrote it, less the unit id it
# opens with.
CHECKIN_LABELS = {
    "overlap notes": "maybe the same work twice",
    "anomalies": "to look at",
    "unread pages": "pages not read",
    "grain questions": "how finely to split",
    "door-owned suggestions": "for the estimator to decide",
    "definitions kinds added": "kinds of marks defined",
    "deviations and repairs": "what went wrong and how it was fixed",
}

# Where an anomaly landed, as its last words after a comma, for the two places a trade's page
# shows it, each with the word its count prints under. `sheet reading` and `run only` are not
# here: no trade's page shows either, so those notes print whole.
LANDED_COUNTED = {"Question": "Questions", "reply": "replies"}

# The ids an ending names, in the forms the record writes them, so a placeholder never reads as a
# place on the record.
_UUID = r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}"
_QUESTION_ID = rf"question:proj-{_UUID}:{_UUID}"
_REPLY_ENTRY_ID = rf"clm-{_UUID}"
_LANDED_RE = re.compile(
    rf", (?:(Question) {_QUESTION_ID}|(reply) (?:{_QUESTION_ID}|{_REPLY_ENTRY_ID}))$"
)

# Every label the summary opens a line with. A line under a note that opens with none of them
# continues that note.
SUMMARY_LABELS = tuple(CHECKIN_LABELS) + (
    "window", "units read", "per unit", "totals verified", "trades", "conflicting rows", "review",
    "ledger", "ledger lines",
)

# A pair of rows carrying the same work, as the reviewer names it, tells the estimator which row
# was kept and whether the other was retired, so it prints whole.
SAME_WORK = " same work: "

# A window 3 review's unit line as the plan script writes it, its manual pages after `reads`, and
# ` verified` added once its review verified.
_REVIEW_LINE_RE = re.compile(
    r"^[1-9][0-9]*\. (\S+): (.+?), trade (.+?)(?:, reads .+)?, package \S+( verified)?$"
)

# A manual part's unit line: the review's package and trade, the unit it reads on after, and each
# span it reads, `; ` between them.
_PART_LINE_RE = re.compile(
    r"^[1-9][0-9]*\. (\S+): (.+?), trade (.+?), package \S+, manual part after (\S+), reads (.+?)( verified)?$"
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
_PER_UNIT_RE = re.compile(r"^per unit: (\S+) created (\d+|-) .* verified (yes|no)$")
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


class CountMismatch(Exception):
    """The record holds fewer entries under a unit's prefix than its runner verified."""


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

def _since_checkin(ledger: Path, window: int) -> tuple[list[str], int]:
    """
    The passes the next check-in reports, each once, last recorded last, and how many `pass:` lines
    sit after the last `checkin:` line, both of this window. No ledger yet is nothing reported.
    """
    if not ledger.is_file():
        return [], 0
    try:
        text = ledger.read_text(encoding="utf-8")
    except Exception as e:
        raise LeadPassError(f"cannot read the ledger at {ledger}: {e}") from e
    recorded: list[tuple[int, str]] = []
    checkin: tuple[int, str] | None = None
    for at, raw in enumerate(text.splitlines()):
        parts = raw.strip().split()
        if len(parts) >= 3 and parts[1] == str(window):
            if parts[0] == "pass:":
                recorded.append((at, parts[2]))
            elif parts[0] == "checkin:":
                checkin = (at, parts[2])
    line_at, read_from = -1, -1
    if checkin is not None:
        line_at, shown_with = checkin
        named = [at for at, pass_id in recorded if pass_id == shown_with and at < line_at]
        read_from = -1 if shown_with == "none" else (named[-1] if named else line_at)
    since: dict[str, int] = {}
    for at, pass_id in recorded:
        if at > read_from:
            # Taken out and put back, so a pass recorded a second time sits at its last line.
            since.pop(pass_id, None)
            since[pass_id] = at
    return list(since), sum(1 for at, _pass_id in recorded if at > line_at)


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
    try:
        live = plan_inventory.live_pass_state(
            window, {pass_id: block["units"] for pass_id, block in blocks.items()}, plan_path.parent,
        )
    except plan_inventory.PlanError as e:
        raise LeadPassError(str(e)) from None

    lines: list[str] = []
    prefixes_of: dict[str, str] = {}
    to_dispatch: list[str] = []
    for pass_id, block in blocks.items():
        verified, summed = live[pass_id]
        lines.append(f"{pass_id}: units {block['fields']['units']}, units verified {verified}, summed {summed}")
        prefixes = [f"scopeItem:{unit}-" for unit in block["units"]]
        prefixes_of[pass_id] = f"{pass_id} prefixes: {json.dumps(prefixes)}"
        lines.append(prefixes_of[pass_id])
        if not (verified == len(block["units"]) and summed == "yes"):
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

    since, after_line = _since_checkin(plan_path.parent / plan_inventory.LEDGER_FILE, window)
    due = window != 1 and after_line >= CHECK_IN_EVERY
    if due:
        ready = []
        start_now = "none, a check-in is due"
    else:
        start_now = ", ".join(ready) or "none"
    waiting = [pass_id for pass_id in to_dispatch if pass_id not in out and pass_id not in ready]
    closing.append(f"start now: {start_now}")
    closing.append(f"waiting: {', '.join(waiting) or 'none'}")
    closing.append(f"since the last check-in: {', '.join(since) or 'none'}")
    closing.append(f"check-in due: {'yes' if due else 'no'}")
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
    unverified = [unit for unit in units if summary["perUnit"][unit][1] != "yes"]
    if unverified:
        raise LeadPassError(
            f"{summary_path} reads verified no for {_named(unverified)}, so the pass gets no "
            f"pass line until its runner verifies every unit"
        )
    checked_again = _mismatched_since(data, summary["ledgerLines"], window, units)
    if checked_again:
        raise LeadPassError(
            f"{summary_path} reads verified yes for {_named(checked_again)}, and a later verified "
            f"line on {ledger} reads mismatch for it, so the pass gets no pass line until its "
            f"runner verifies every unit"
        )

    below: list[str] = []
    above: list[str] = []
    for unit in units:
        count = counts[unit]
        verified = int(summary["perUnit"][unit][0])
        if count < verified:
            below.append(f"{unit} {count} on the record, {verified} when its runner verified it")
        elif count > verified:
            above.append(f"{unit} {count} on the record, {verified} when its runner verified it")
    if below:
        raise CountMismatch(
            f"the record holds less under these units of window {window} pass {pass_id} than "
            f"their runner verified: " + "; ".join(below) + f"; nothing was written to {ledger}"
        )

    if not ledger.is_file():
        raise LeadPassError(f"no ledger at {ledger}")
    figures = [
        ("units", str(len(units))),
        ("created", str(sum(counts.values()))),
        ("updated", summary["updated"]),
        ("questions", summary["questions"]),
        ("replied", summary["replied"]),
    ]
    if window == 3:
        figures += [
            ("pages-opened", summary["pagesOpened"]), ("searches", summary["searches"]),
            ("reports-restored", summary["reportsRestored"]),
        ]
    if window == RECHECK_WINDOW:
        figures += list(summary["recheck"].items())
    line = f"pass: {window} {pass_id} " + " ".join(f"{k} {v}" for k, v in figures)
    line += " lead-verified yes"

    # Through the ledger script, as every line goes on: under its lock, checked, its shadow first.
    try:
        ledger_script.append_lines(ledger, [line])
    except ledger_script.LedgerError as e:
        raise LeadPassError(f"cannot append to the ledger at {ledger}: {e}") from None

    # The pass as the estimator hears it, for the one line the lead says as each pass is recorded.
    reads = _plan_reads(plan_path, window, _verified_ok(ledger, window) if window == 3 else frozenset())[0]
    said = {field: int(value) for field, value in figures if field in PASS_FIGURES + RECHECK_FIGURES}
    words = _said_recheck(said) if window == RECHECK_WINDOW else _said_figures(summary["items"], said)
    out = [line, f"{reads.get(pass_id, 'nothing planned')}: {words}"]
    out.extend(f"above the runner's count: {entry}" for entry in above)
    out.extend(healed)
    return out


# --------------------------------------------------------------------------- #
# checkin
# --------------------------------------------------------------------------- #

def _last_pass_lines(ledger: Path, window: int) -> dict[str, str]:
    if not ledger.is_file():
        raise LeadPassError(f"no ledger at {ledger}")
    try:
        text = ledger.read_text(encoding="utf-8")
    except Exception as e:
        raise LeadPassError(f"cannot read the ledger at {ledger}: {e}") from e
    last: dict[str, str] = {}
    for raw in text.splitlines():
        parts = raw.strip().split()
        if len(parts) >= 3 and parts[0] == "pass:" and parts[1] == str(window):
            last[parts[2]] = raw.strip()
    return last


def _repaired_since_checkin(ledger: Path) -> list[str]:
    """
    The ledger script's `repaired:` lines after the last `checkin:` line of any window, each a time
    lines of the run's log were changed outside the run and put back, which the next check-in says.
    """
    try:
        lines = [raw.strip() for raw in ledger.read_text(encoding="utf-8").splitlines()]
    except OSError:
        return []
    found: list[str] = []
    for line in lines:
        if line.startswith("checkin:"):
            found = []
        elif line.startswith(ledger_script.REPAIRED_KEYWORD):
            found.append(line)
    return found


def _figure(line: str, field: str) -> int | None:
    parts = line.split()
    if field not in parts:
        return None
    at = parts.index(field)
    if at + 1 >= len(parts) or not parts[at + 1].isdigit():
        return None
    return int(parts[at + 1])


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


def _reviews_of(plan_path: Path) -> dict[str, str]:
    """
    Each window 3 review unit's place for its counts, `the review of <package name>, trade
    <catalog id>`, off the read plan's unit lines; empty where the plan is not window 3's or is not
    there, so every count falls under its pass.
    """
    try:
        lines = plan_path.read_text(encoding="utf-8").splitlines()
    except OSError:
        return {}
    first = next((line.strip() for line in lines if line.strip()), "")
    if first != "# Read plan: window 3":
        return {}
    reviews: dict[str, str] = {}
    for line in lines:
        # A manual part reads for its review's package, so its counts fall under that package.
        unit = _PART_LINE_RE.match(line.strip()) or _REVIEW_LINE_RE.match(line.strip())
        if unit:
            reviews[unit.group(1)] = f"the review of {unit.group(2)}, trade {unit.group(3)}"
    return reviews


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
    What each pass of the read plan beside the ledger read, in the words a check-in says it in, and
    what each unit id names: a sheet's number, the file a repeated lines unit reads, or a review's
    package. Both are empty where the plan is not this window's or is not there, and the check-in
    then names passes by id alone. A window 3 pass names the manual pages each of its manual
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


def _without_unit(note: str, named: dict[str, str], window: int) -> str:
    """
    A summary note without the unit id it opens with. A sheet's note names its sheet and page right
    after it, so the id goes; a review's note names its package in the id's place.
    """
    unit, _space, rest = note.partition(" ")
    if unit not in named or not rest:
        return note
    return f"{named[unit]}: {rest}" if window == 3 else rest


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


def _landed(note: str) -> str | None:
    """The place an anomaly says it landed where a trade's page shows it, or None to print it."""
    if SAME_WORK in note:
        return None
    ending = _LANDED_RE.search(note)
    return next(word for word in ending.groups() if word) if ending else None


def _summary_label(line: str) -> str | None:
    """The summary label a line opens with, or None where it continues the line above it."""
    return next((label for label in SUMMARY_LABELS if line.startswith(f"{label}:")), None)


def _on_record_figures(counts: dict[str, int]) -> str:
    return ", ".join(f"{word} {counts[landed]}" for landed, word in LANDED_COUNTED.items())


def checkin_lines(
    run_folder: Path, window: int, pass_ids: list[str], start: tuple[int, int],
) -> list[str]:
    ledger = run_folder / "ledger.md"
    heal_ledger(ledger)
    last = _last_pass_lines(ledger, window)
    reads, named = _plan_reads(
        run_folder / "read-plan.md", window, _verified_ok(ledger, window) if window == 3 else frozenset()
    )

    by_trade: dict[str, int] = {}
    items_of: dict[str, int] = {}
    notes: list[tuple[str, str]] = []
    no_trades: list[str] = []
    no_summary: list[str] = []
    reviews = _reviews_of(run_folder / "read-plan.md") if window == 3 else {}
    # The anomalies already on the record, counted by where each landed, under its review or pass.
    on_record: dict[str, dict[str, int]] = {}
    for pass_id in pass_ids:
        path = _summary_path(run_folder, window, pass_id)
        if not path.is_file():
            no_summary.append(pass_id)
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except Exception as e:
            raise LeadPassError(f"cannot read the summary at {path}: {e}") from e
        trades = None
        # Each note line, its label, and the unlabelled lines under it that continue it.
        entries: list[tuple[str, str, list[str]]] = []
        in_note = False
        for raw in text.splitlines():
            line = raw.strip()
            if not line:
                continue
            label = _summary_label(line)
            if label is None:
                if in_note:
                    entries[-1][2].append(line)
                continue
            if label == "trades":
                trades = _trades_of(line)
            in_note = label in CHECKIN_LABELS
            if in_note:
                entries.append((label, line, []))
        for label, line, continued in entries:
            if line == f"{label}: none" and not continued:
                continue
            landed = _landed(line) if label == "anomalies" and not continued else None
            if landed is None:
                body = _without_unit(line[len(label) + 2:], named, window)
                notes.append((pass_id, f"{CHECKIN_LABELS[label]}: {body}"))
                notes.extend((pass_id, more) for more in continued)
                continue
            unit = line[len("anomalies: "):].split(" ", 1)[0]
            where = reviews[unit] if unit in reviews else f"pass {pass_id}"
            counts = on_record.setdefault(where, {key: 0 for key in LANDED_COUNTED})
            counts[landed] += 1
        if trades is None:
            no_trades.append(pass_id)
            continue
        for code, count in trades.items():
            by_trade[code] = by_trade.get(code, 0) + count
        items_of[pass_id] = sum(trades.values())

    # Each pass by what it read, with its figures in the estimator's words. The new items are the
    # pass's trades summed, every one a subject its runner found on the record; `created` on a pass
    # line counts entries, every citation and trade written with those items, and is never an item
    # count, so it goes on the lead's own line below and never on these.
    head: list[str] = [f"window {window}, {len(pass_ids)} pass{'' if len(pass_ids) == 1 else 'es'}"]
    totals = {field: 0 for field in PASS_FIGURES + REVIEW_FIGURES + RECHECK_FIGURES}
    with_line: list[str] = []
    items: int | None = 0
    for pass_id in pass_ids:
        line = last.get(pass_id)
        name = reads.get(pass_id, pass_id)
        if line is None:
            head.append(f"{name}: no pass line on the ledger")
            continue
        with_line.append(pass_id)
        for field in totals:
            totals[field] += _figure(line, field) or 0
        figures = {field: _figure(line, field) or 0 for field in PASS_FIGURES + RECHECK_FIGURES}
        head.append(
            f"{name}: "
            + (_said_recheck(figures) if window == RECHECK_WINDOW else _said_figures(items_of.get(pass_id), figures))
        )
        items = None if items is None or pass_id not in items_of else items + items_of[pass_id]
    head.append(
        f"over {len(with_line)} pass{'' if len(with_line) == 1 else 'es'}: "
        + (_said_recheck(totals) if window == RECHECK_WINDOW else _said_figures(items, totals))
    )
    head.append(
        f"your own check over {len(with_line)} pass line{'' if len(with_line) == 1 else 's'} ({', '.join(with_line) or 'none'}), "
        f"never said to the estimator: units {totals['units']}, entries {totals['created']}"
        + (
            f", pages opened {totals['pages-opened']}, searches {totals['searches']}, reports "
            f"restored {totals['reports-restored']}" if window == 3 else ""
        )
    )
    ordered = sorted(by_trade.items(), key=lambda pair: (-pair[1], pair[0]))
    head.append(
        "items by trade: "
        + (", ".join(f"{code} x{count}" for code, count in ordered) if ordered else "none")
    )
    totals_on_record = {key: 0 for key in LANDED_COUNTED}
    for where, counts in on_record.items():
        head.append(f"on the record: {_on_record_figures(counts)}, in {where}")
        for key, count in counts.items():
            totals_on_record[key] += count
    head.append(f"on the record over these passes: {_on_record_figures(totals_on_record)}")
    if no_trades:
        head.append(f"summaries with no trades count: {', '.join(no_trades)}")
    if no_summary:
        head.append(f"no summary on file: {', '.join(no_summary)}")
    head.extend(repaired_said(line) for line in _repaired_since_checkin(ledger))

    # Each note's place among its own pass's lines, which is what `--start` and the markers count.
    first_of: dict[str, int] = {}
    for index, (pass_id, _line) in enumerate(notes):
        first_of.setdefault(pass_id, index)

    # The first pass's first `start` lines, and `chars` characters of the line after them, were
    # printed by the call before this one.
    start_lines, chars = start
    skipped = 0
    while skipped < start_lines and skipped < len(notes) and notes[skipped][0] == pass_ids[0]:
        skipped += 1
    if chars and (
        skipped >= len(notes) or notes[skipped][0] != pass_ids[0] or chars >= len(notes[skipped][1])
    ):
        raise LeadPassError(
            f"--start names character {chars + 1} of line {start_lines + 1} of pass {pass_ids[0]}, "
            f"and that line is not that long; run the check-in again from its first call"
        )

    def closing(cut_pass: str, line_no: int, at: int) -> str:
        rest = pass_ids[pass_ids.index(cut_pass):]
        start_at = f"{line_no - 1}:{at}" if at else (str(line_no - 1) if line_no > 1 else "")
        command = (
            f"python3 '{Path(__file__).resolve()}' checkin '{run_folder}' {window} "
            f"--passes {','.join(rest)}" + (f" --start {start_at}" if start_at else "")
        )
        return (
            f"not printed: {cut_pass} from its line {line_no}"
            + (f", character {at + 1}" if at else "")
            + (f", and {', '.join(rest[1:])}" if len(rest) > 1 else "")
            + f"; the rest: {command}"
        )

    def cut_marker(pass_id: str, line_no: int, at: int, length: int) -> str:
        return f"cut: pass {pass_id}, line {line_no}, at character {at} of {length}; the rest is in the next call"

    # Room for the longest closing line and cut marker this call could print, so the cap holds
    # whatever line the call stops on.
    longest_id = max(pass_ids, key=len)
    longest_note = max((len(line) for _pass_id, line in notes), default=0)
    reserve = (
        len(closing(pass_ids[0], len(notes) + 1, longest_note)) + len(longest_id) - len(pass_ids[0])
        + len(cut_marker(longest_id, len(notes) + 1, longest_note, longest_note)) + 2
    )

    widest_block = (
        len(f"pass {longest_id}:") + 1
        + len(f"pass {longest_id}, line {len(notes) + 1}, from character {longest_note + 1}:") + 1
    )

    out = list(head)
    size = sum(len(line) + 1 for line in out)
    # The first line a call prints always gets at least one character of room.
    if size + reserve + widest_block + 2 > CHECKIN_CAP:
        raise LeadPassError(
            f"the pass lines and totals of {len(pass_ids)} passes alone leave no room under the "
            f"{CHECKIN_CAP} characters one call prints; name fewer passes with --passes"
        )
    stopped: tuple[int, int] | None = None
    current = None
    printed = 0
    for index in range(skipped, len(notes)):
        pass_id, line = notes[index]
        line_no = index - first_of[pass_id] + 1
        begin = chars if index == skipped else 0
        block = [] if pass_id == current else [f"pass {pass_id}:"]
        if begin:
            block.append(f"pass {pass_id}, line {line_no}, from character {begin + 1}:")
        piece = line[begin:]
        room = CHECKIN_CAP - reserve - size - sum(len(text) + 1 for text in block) - 1
        if len(piece) <= room:
            out.extend(block)
            out.append(piece)
            size += sum(len(text) + 1 for text in block) + len(piece) + 1
            current = pass_id
            printed += 1
            continue
        if printed:
            stopped = (index, begin)
            break
        # A note longer than a whole call's room is cut where the room ends, so every call prints
        # something new and nothing past the cap.
        out.extend(block)
        out.append(piece[:room])
        out.append(cut_marker(pass_id, line_no, begin + room, len(line)))
        stopped = (index, begin + room)
        break

    if stopped is None:
        out.append(f"every line printed, {printed} in this call")
        return out

    index, at = stopped
    cut_pass = notes[index][0]
    out.append(closing(cut_pass, index - first_of[cut_pass] + 1, at))
    return out


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
        help="the pass that just handed back; prints only its prefixes and the five closing lines",
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

    check = modes.add_parser("checkin", help="what a check-in needs, off the pass lines and summaries")
    check.add_argument("run_folder", type=Path, help="the run folder")
    check.add_argument("window", type=pass_summary.parse_window, help="the window the passes belong to: 1, 2, 3, or r")
    check.add_argument("--passes", required=True, help="the pass ids, comma separated")
    check.add_argument(
        "--start", default="0",
        help="how many of the first pass's lines an earlier call already printed, and after a "
        "colon how many characters of the line after them",
    )

    args = parser.parse_args(argv)

    try:
        if args.mode == "passes":
            lines = passes_lines(
                args.plan, [pass_id.strip() for pass_id in args.running.split(",") if pass_id.strip()],
                args.reported,
            )
        elif args.mode == "record":
            lines = record(args.ledger, args.window, args.pass_id, args.plan, args.counts_json)
        else:
            pass_ids = [pass_id.strip() for pass_id in args.passes.split(",") if pass_id.strip()]
            if not pass_ids:
                raise LeadPassError("--passes names no pass")
            start = re.fullmatch(r"(\d+)(?::(\d+))?", args.start)
            if start is None:
                raise LeadPassError(
                    f"--start reads {args.start!r}, and it takes a count of lines, or lines and "
                    f"characters as <lines>:<characters>"
                )
            lines = checkin_lines(
                args.run_folder, args.window, pass_ids, (int(start.group(1)), int(start.group(2) or 0)),
            )
    except CountMismatch as e:
        print(f"lead_pass: {e}", file=sys.stderr)
        return 3
    except LeadPassError as e:
        print(f"lead_pass: {e}", file=sys.stderr)
        return 1
    for line in lines:
        print(line)
    return 0


if __name__ == "__main__":
    sys.exit(main())
