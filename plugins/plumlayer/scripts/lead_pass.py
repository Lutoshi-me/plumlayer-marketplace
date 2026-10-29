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

    python lead_pass.py passes --plan <run folder>/read-plan.md

        Every pass the read plan carries, in its order, two lines each:

            <pass id>: units <n>, units verified <k>, summed <the plan's summed value>
            <pass id> prefixes: ["scopeItem:<unit id>-", ...]

        and one last line, `passes <n>, finished <k>; to dispatch: <pass ids, or none>`. A pass is
        finished where its `units:` and `units verified:` agree and it reads `summed: yes`, the rule
        the skill gives. The prefixes are built from the unit ids the plan block carries, in its
        order. A plan with no pass, as window 2's is where window 1 selected or left out every
        sheet, prints only that last line, `passes 0, finished 0; to dispatch: none`.

    python lead_pass.py record <run folder>/ledger.md <window> <pass id>
        --plan <run folder>/read-plan.md --counts-json '<the counts array>'

        `--counts-json` is the `counts` array of the lead's `count_entries` answer, as it came back:
        `[{"subjectPrefix": "scopeItem:<unit id>-", "entryCount": <n>}, ...]`. Each count is paired
        with its unit by its prefix, never by its place in the list, and the prefixes have to be
        exactly the ones the plan block yields, each once. Reads the pass's summary,
        `reports/<pass id>.md` beside the ledger, and compares it unit by unit with the counts.
        Where every count holds, it appends one `pass:` line to the ledger and prints it:

            pass: <window> <pass id> units <n> created <n> updated <n> questions <n> replied <n> candidates <n> lead-verified yes
            pass: 3 <pass id> units <n> created <n> updated <n> questions <n> replied <n> candidates <n> pages-opened <n> searches <n> lead-verified yes

        Under it, it prints the pass as the estimator hears it, the line the check-in prints for
        it below, with the new items off the summary's trades line, so the one line the lead says
        as the pass is recorded names the sheets or packages and the items, never the pass id or
        the entry count.

        `created` is the sum of the lead's own counts. `updated`, `questions` and `replied` come off
        the summary's totals line, `candidates` off its trades line, and in window 3 `pages-opened`
        and `searches` off its `review:` line. A unit whose count on the record is above the one its
        runner verified is named under the line with both counts: an entry count under a prefix only
        grows, so a later write onto that unit's rows raises it, and nothing removes one. A count
        below the runner's is the record holding less than the runner verified: the script writes
        nothing, names each such unit with both counts, and exits 3, and the run stops there.

    python lead_pass.py checkin <run folder> <window> --passes <pass id>,<pass id>,...
        [--start <lines>[:<characters>]]

        What the check-in needs, off the ledger's `pass:` lines, the read plan beside them and the
        summaries on file. Each pass by what it read, the sheet numbers its block carries or in
        window 3 its packages, with its last `pass:` line's figures in the estimator's words:

            <pass id>, <n> sheets read (<sheet numbers>): new items <n>, items updated <n>, Questions raised <n>, replies <n>, new items with a candidate trade <n>
            over <n> passes: new items <n>, items updated <n>, Questions raised <n>, replies <n>, new items with a candidate trade <n>
            your own check over <n> pass lines, never said to the estimator: units <n>, entries <n>

        The new items are the summaries' `trades:` lines summed, each a subject the pass's runner
        found on the record. A pass line's `created` counts entries, every citation and trade
        written with those items, so it goes on the lead's own line and never reads as items; in
        window 3 that line adds the pages opened and the searches. Then the items by trade summed
        off the same lines, the anomalies already on the record as counts, and every other note
        line of each summary, under its pass, each copied whole under the label CHECKIN_LABELS
        gives it, less the unit id it opens with, which a window 3 note trades for its package's
        name.

        An anomaly ends with where it landed, after a comma, as the reader's and the reviewer's
        report shapes ask. One that ends `Question <id>`, `reply <id>` or `note on <subject>` is
        on a trade's page, where the estimator reads it, so it is counted rather than printed,
        where the id or subject is one the record writes: a Question's id as `ask_question`
        returns it, `question:proj-<uuid>:<uuid>`; after `reply`, that id or the reply's own
        entry id, `clm-<uuid>`; and after `note on`, a row's subject, `scopeItem:<id>`, its id
        letters, digits and hyphens. Any other ending prints whole, a placeholder such as
        `Question <id>` and words such as `note on hold` among them:

            on the record: Questions <n>, replies <n>, notes on rows <n>, in pass <pass id>
            on the record: Questions <n>, replies <n>, notes on rows <n>, in the review of <package name>, trade <catalog id>
            on the record over these passes: Questions <n>, replies <n>, notes on rows <n>

        A window 3 anomaly is counted under the review its unit id names on the read plan beside
        the ledger; any other anomaly, and one whose unit the plan does not name, under its pass.
        One that names a pair of rows carrying the same work prints whole wherever it landed,
        since the estimator retires one of the two, and so does one ending `sheet reading` or
        `run only`, or with an ending this does not read. A line under a note that opens with
        none of the summary's labels continues that note, so an anomaly carrying one prints
        whole, its continuation under it, since its last words are not where it landed. Every
        overlap, unread page, grain question, door-owned suggestion, definitions kind and
        deviation line prints whole, with any continuation under it.

        Output stops before CHECKIN_CAP characters, below the 30,000 a Bash call returns, every
        printed line counted, the closing line included, and its last line names the passes it did
        not print and the command that prints the rest. A note longer than the room a call has
        left once nothing else is printed is cut there, with a line under it naming the pass, the
        note and the character it stops at, and the next call prints the rest of it. `--start` is
        how many of the first pass's printed lines an earlier call already printed, and after a
        colon (`--start 4:23000`) how many characters of the line after them.

Exit codes:
  0  printed, and in record mode the `pass:` line appended.
  1  a named failure, one line on stderr: a read plan, ledger or summary file that is not there,
     a plan block with no `units verified:` or `summed:` line, counts that are not a JSON list of
     prefixes with whole numbers or whose prefixes are not exactly the plan block's, each once, a
     summary of another window or pass, one naming other units than the plan block carries, one
     with a unit it reads `verified no`, or one with no totals line, no candidates count, or in
     window 3 no `review:` line; at the check-in, a `--start` that is not a count of lines and
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
import pass_summary  # noqa: E402

REPORTS_FOLDER = pass_summary.REPORTS_FOLDER

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

# Where an anomaly landed, as its last words after a comma, for the three places a trade's page
# shows it, each with the word its count prints under. `sheet reading` and `run only` are not
# here: no trade's page shows either, so those notes print whole.
LANDED_COUNTED = {"Question": "Questions", "reply": "replies", "note on": "notes on rows"}

# The ids an ending names, in the forms the record writes them, so a placeholder or a word after
# `note on` never reads as a place on the record.
_UUID = r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}"
_QUESTION_ID = rf"question:proj-{_UUID}:{_UUID}"
_REPLY_ENTRY_ID = rf"clm-{_UUID}"
_ROW_SUBJECT = r"scopeItem:[0-9A-Za-z](?:[0-9A-Za-z-]*[0-9A-Za-z])?"
_LANDED_RE = re.compile(
    rf", (?:(Question) {_QUESTION_ID}|(reply) (?:{_QUESTION_ID}|{_REPLY_ENTRY_ID})"
    rf"|(note on) {_ROW_SUBJECT})$"
)

# Every label the summary opens a line with. A line under a note that opens with none of them
# continues that note.
SUMMARY_LABELS = tuple(CHECKIN_LABELS) + (
    "window", "units read", "per unit", "totals verified", "trades", "conflicting rows", "review",
    "ledger",
)

# A pair of rows carrying the same work, as the reviewer names it, asks the estimator to retire
# one of the two, so it prints whole wherever its sentence landed.
SAME_WORK = " same work: "

# A window 3 unit line as the plan script writes it, ` verified` added once its review verified.
_REVIEW_LINE_RE = re.compile(r"^[1-9][0-9]*\. (\S+): (.+), trade (.+), package \S+( verified)?$")

# A window 1 or 2 unit line as the plan script writes it: the unit id, then the sheet number, or
# `file <fileId>` on a repeated lines unit, then where it opens.
_PLAN_UNIT_RE = re.compile(r"^(\S+-[1-9][0-9]*)\. (.+?), (?:file |page |from page )")

# The figures of a `pass:` line, in its order, the window 3 pair included.
PASS_FIGURES = ("units", "created", "updated", "questions", "replied", "candidates")
REVIEW_FIGURES = ("pages-opened", "searches")

_SUMMARY_HEADER_RE = re.compile(r"^window: ([1-9][0-9]*)\s+pass: (\S+)$")
_PER_UNIT_RE = re.compile(r"^per unit: (\S+) created (\d+|-) .* verified (yes|no)$")
_TOTALS_RE = re.compile(r"updated (\d+), questions (\d+) replied (\d+)")
_CANDIDATES_RE = re.compile(r"; candidates (\d+)$")
_REVIEW_RE = re.compile(r"^review: pages opened (\d+), searches (\d+)$")


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

def passes_lines(plan_path: Path) -> list[str]:
    try:
        window, pass_ids = pass_summary.plan_passes(plan_path)
    except pass_summary.SummaryError as e:
        raise LeadPassError(str(e)) from None
    lines: list[str] = []
    to_dispatch: list[str] = []
    for pass_id in pass_ids:
        block = _read_plan(plan_path, window, pass_id)
        fields = block["fields"]
        for field in ("units verified", "summed"):
            if field not in fields:
                raise LeadPassError(
                    f"{plan_path}: pass {pass_id}'s block carries no `{field}:` line, which the "
                    f"plan script writes; run the plan script again"
                )
        lines.append(
            f"{pass_id}: units {fields['units']}, units verified {fields['units verified']}, "
            f"summed {fields['summed']}"
        )
        prefixes = [f"scopeItem:{unit}-" for unit in block["units"]]
        lines.append(f"{pass_id} prefixes: {json.dumps(prefixes)}")
        if not (fields["units"] == fields["units verified"] and fields["summed"] == "yes"):
            to_dispatch.append(pass_id)
    finished = len(pass_ids) - len(to_dispatch)
    lines.append(
        f"passes {len(pass_ids)}, finished {finished}; to dispatch: "
        + (", ".join(to_dispatch) if to_dispatch else "none")
    )
    return lines


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
    if int(header.group(1)) != window or header.group(2) != pass_id:
        raise LeadPassError(
            f"{path} is the summary of window {header.group(1)} pass {header.group(2)}, and this is "
            f"window {window} pass {pass_id}"
        )

    per_unit: dict[str, tuple[str, str]] = {}
    totals = candidates = review = trades = None
    for raw in lines:
        line = raw.strip()
        unit = _PER_UNIT_RE.match(line)
        if unit:
            per_unit[unit.group(1)] = (unit.group(2), unit.group(3))
        elif line.startswith("totals verified:"):
            totals = _TOTALS_RE.search(line)
        elif line.startswith("trades:"):
            candidates = _CANDIDATES_RE.search(line)
            trades = _trades_of(line)
        elif line.startswith("review:"):
            review = _REVIEW_RE.match(line)
    if totals is None:
        raise LeadPassError(f"{path} carries no totals line")
    if candidates is None:
        raise LeadPassError(
            f"{path}: its trades line carries no candidates count, so the runner summed the pass "
            f"with no trades file"
        )
    if window == 3 and review is None:
        raise LeadPassError(f"{path} carries no `review: pages opened <n>, searches <n>` line")
    return {
        "perUnit": per_unit,
        "updated": totals.group(1),
        "questions": totals.group(2),
        "replied": totals.group(3),
        "candidates": candidates.group(1),
        "items": sum(trades[0].values()) if trades else None,
        "pagesOpened": review.group(1) if review else None,
        "searches": review.group(2) if review else None,
    }


def record(ledger: Path, window: int, pass_id: str, plan_path: Path, counts_text: str) -> list[str]:
    plan = _read_plan(plan_path, window, pass_id)
    units = plan["units"]
    counts = _parse_counts(counts_text, pass_id, units)
    summary_path = _summary_path(ledger.parent, window, pass_id)
    summary = read_summary(summary_path, window, pass_id)

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
        ("candidates", summary["candidates"]),
    ]
    if window == 3:
        figures += [("pages-opened", summary["pagesOpened"]), ("searches", summary["searches"])]
    line = f"pass: {window} {pass_id} " + " ".join(f"{k} {v}" for k, v in figures)
    line += " lead-verified yes"

    try:
        existing = ledger.read_bytes()
        with ledger.open("ab") as handle:
            if existing and not existing.endswith(b"\n"):
                handle.write(b"\n")
            handle.write(f"{line}\n".encode("utf-8"))
    except OSError as e:
        raise LeadPassError(f"cannot append to the ledger at {ledger}: {e}") from e

    # The pass as the estimator hears it, for the one line the lead says as each pass is recorded.
    reads = _plan_reads(plan_path, window)[0]
    said = {field: int(value) for field, value in figures if field in PASS_FIGURES}
    out = [line, f"{pass_id}, {reads.get(pass_id, 'nothing planned')}: {_said_figures(summary['items'], said)}"]
    out.extend(f"above the runner's count: {entry}" for entry in above)
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


def _figure(line: str, field: str) -> int | None:
    parts = line.split()
    if field not in parts:
        return None
    at = parts.index(field)
    if at + 1 >= len(parts) or not parts[at + 1].isdigit():
        return None
    return int(parts[at + 1])


def _trades_of(line: str) -> tuple[dict[str, int], int] | None:
    """A summary's trades line as item counts by catalog id and its candidates, or None without one."""
    candidates = _CANDIDATES_RE.search(line)
    if candidates is None:
        return None
    body = line[len("trades: "):candidates.start()]
    by_trade: dict[str, int] = {}
    if not body.startswith("no trade on any unit"):
        for entry in body.split(", "):
            code, _x, count = entry.rpartition(" x")
            if code and count.isdigit():
                by_trade[code] = by_trade.get(code, 0) + int(count)
    return by_trade, int(candidates.group(1))


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
        unit = _REVIEW_LINE_RE.match(line.strip())
        if unit:
            reviews[unit.group(1)] = f"the review of {unit.group(2)}, trade {unit.group(3)}"
    return reviews


def _plan_reads(plan_path: Path, window: int) -> tuple[dict[str, str], dict[str, str]]:
    """
    What each pass of the read plan beside the ledger read, in the words a check-in says it in, and
    what each unit id names: a sheet's number, the file a repeated lines unit reads, or a review's
    package. Both are empty where the plan is not this window's or is not there, and the check-in
    then names passes by id alone.
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
    packages: dict[str, list[str]] = {}
    named: dict[str, str] = {}
    current = None
    for raw in lines:
        line = raw.strip()
        if line == pass_summary._LEFT_OUT_HEADING:
            break
        heading = pass_summary._PASS_HEADING_RE.match(raw)
        if heading:
            current = heading.group(1)
            sheets[current], files[current], packages[current] = [], 0, []
            continue
        if current is None:
            continue
        review = _REVIEW_LINE_RE.match(line) if window == 3 else None
        if review:
            packages[current].append(f"{review.group(2)}, trade {review.group(3)}")
            named[review.group(1)] = review.group(2)
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
        if sheets[pass_id]:
            parts.append(
                f"{len(sheets[pass_id])} sheet{'' if len(sheets[pass_id]) == 1 else 's'} read "
                f"({', '.join(sheets[pass_id])})"
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
        f"replies {figures['replied']}, new items with a candidate trade {figures['candidates']}"
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
    last = _last_pass_lines(ledger, window)
    reads, named = _plan_reads(run_folder / "read-plan.md", window)

    by_trade: dict[str, int] = {}
    items_of: dict[str, int] = {}
    candidates = 0
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
        for code, count in trades[0].items():
            by_trade[code] = by_trade.get(code, 0) + count
        items_of[pass_id] = sum(trades[0].values())
        candidates += trades[1]

    # Each pass by what it read, with its figures in the estimator's words. The new items are the
    # pass's trades summed, every one a subject its runner found on the record; `created` on a pass
    # line counts entries, every citation and trade written with those items, and is never an item
    # count, so it goes on the lead's own line below and never on these.
    head: list[str] = [f"window {window}, passes {', '.join(pass_ids)}"]
    totals = {field: 0 for field in PASS_FIGURES + REVIEW_FIGURES}
    with_line = 0
    items: int | None = 0
    for pass_id in pass_ids:
        line = last.get(pass_id)
        name = f"{pass_id}, {reads[pass_id]}" if pass_id in reads else pass_id
        if line is None:
            head.append(f"{name}: no pass line on the ledger")
            continue
        with_line += 1
        for field in totals:
            totals[field] += _figure(line, field) or 0
        figures = {field: _figure(line, field) or 0 for field in PASS_FIGURES}
        head.append(f"{name}: {_said_figures(items_of.get(pass_id), figures)}")
        items = None if items is None or pass_id not in items_of else items + items_of[pass_id]
    head.append(f"over {with_line} pass{'' if with_line == 1 else 'es'}: " + _said_figures(items, totals))
    head.append(
        f"your own check over {with_line} pass line{'' if with_line == 1 else 's'}, never said to "
        f"the estimator: units {totals['units']}, entries {totals['created']}"
        + (f", pages opened {totals['pages-opened']}, searches {totals['searches']}" if window == 3 else "")
    )
    ordered = sorted(by_trade.items(), key=lambda pair: (-pair[1], pair[0]))
    head.append(
        "items by trade: "
        + (", ".join(f"{code} x{count}" for code, count in ordered) if ordered else "none")
        + f"; candidates {candidates}"
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

    rec = modes.add_parser("record", help="compare a pass's counts and append its pass line")
    rec.add_argument("ledger", type=Path, help="the run folder's ledger.md")
    rec.add_argument("window", type=int, help="the window the pass belongs to")
    rec.add_argument("pass_id", metavar="pass", help="the pass id, exactly as the plan spells it")
    rec.add_argument("--plan", type=Path, required=True, help="the window's read-plan.md")
    rec.add_argument(
        "--counts-json", required=True,
        help="the `counts` array of the `count_entries` answer for the pass, as it came back",
    )

    check = modes.add_parser("checkin", help="what a check-in needs, off the pass lines and summaries")
    check.add_argument("run_folder", type=Path, help="the run folder")
    check.add_argument("window", type=int, help="the window the passes belong to")
    check.add_argument("--passes", required=True, help="the pass ids, comma separated")
    check.add_argument(
        "--start", default="0",
        help="how many of the first pass's lines an earlier call already printed, and after a "
        "colon how many characters of the line after them",
    )

    args = parser.parse_args(argv)

    try:
        if args.mode == "passes":
            lines = passes_lines(args.plan)
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
