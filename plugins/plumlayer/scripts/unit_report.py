"""
unit_report.py: hold a reader's report to its shape, hand a read the work an earlier read left,
restore a lost report of a passed package review from what the run already holds, write a unit's
trades as one set, gather the trades every read of a unit touched, keep the lists a check
confirmed off a returned message, and hold a window 1 unit's code lists to the codes on the record.

A reader writes its report to `<run folder>/reports/<unit id>.md` and returns it. A runner never
writes, completes or copies into that file. This script reads it, and writes files of its own
beside it. Every file it writes it replaces whole, through `ledger.publish`: a temporary file in
the same folder, then one atomic replace, so a stop at any point leaves the old file or the new one:
the owed file, the restored report, the trades file and its `.written` file, and the confirmed file.

Seven modes:

    sh run.sh unit_report.py check --kind <sheet|vocabulary|review|manual|standard> --report <path or -> [--owed <path or none>] [--spans '<Reads: line>']

        Holds one report to its kind's shape: a file, or with `-` the reader's returned message on
        stdin through a quoted heredoc. The kinds are the five readers of windows 1, 2 and 3: a
        window 2 sheet (`scope-reader`), a window 1 unit (`scope-vocabulary-reader`), a package
        review, a manual part and a standard lines unit (`scope-standard-lines`). Window r is
        not held here.

        - Every label of the kind's shape opens a line (SHEET_LABELS, VOCABULARY_LABELS,
          REVIEW_LABELS, MANUAL_LABELS, STANDARD_LABELS, each the agent's own report shape), with a
          whole number on `created:`, `updated:`, `questions raised:`, `questions replied:`,
          `sent:` and `landed:`, and on a window 3 unit a whole number on `searches:`. A report short of any of
          this is not whole, and so is one whose bytes are not UTF-8, read the same strict way off
          a file and off stdin.
        - The two counts every report shape makes equal to a list are held to it: `created` to
          the subjects on `created subjects:` and `questions raised` to the ids on `questions
          raised ids:`. `questions replied:` counts replies while its list names the Questions
          replied to, so it is held to at least one id where it is above 0, to `none` where it is
          0, and is never below the ids listed. A count that disagrees is a mismatch named
          `report`. `updated` is held to no list: `updated:` counts rows its list leaves off (a
          heading-only row, a retired row) and leaves off rows a list names (a citation the door
          answered duplicate). The runner finds each subject and id a report names on the record.
        - With `--owed <path>`, the `owed:` line is held to that file, the one `owed` wrote for
          this read: every `not written by read <j>: <entry>` line of it is named on `owed:`, copied
          whole, then ` | ` and one of `written <subject>`, `read, nothing to write` (a sheet or a
          window 1 unit only) or `not written, <why>`, and nothing else is named there; a list
          marker `- ` or `* ` before a line of it is read past. `written
          <subject>` counts only where the subject is on this report's `created subjects:` and not
          among the file's `held:` subjects, which an earlier read left under the prefix, or opens
          a line of this report's `field updates:` (a list marker `- ` or `* ` before the subject
          is read past), which the runner binds to the time of this read's dispatch; a citation
          alone discharges nothing. `not written, <why>` on a review or a manual part needs the
          entry on this report's `not written:` line too. Each `check read <j> failed:` line of the
          file whose check held a write an earlier read claimed on a named row (`updated`, `field
          updates`, `manual updates`, `questions linked`, `page citations`) is named on `owed:`
          too, copied whole, then ` | ` and `written <subject>` or `not needed, <why>`. There
          `written <subject>` counts where the subject is the row the failed check names and this
          report names it on its own list for that write (CLAIM_LISTS: `updated subjects:`,
          `questions linked:`, `manual updates:`, `field updates:` or `page citations:`), which the
          runner holds to the record again, so that check passing now is the proof; the row need
          not be one this read created. On a `field updates` claim naming a predicate, a
          `field updates:` line of the row names that predicate too, and on a `questions linked`
          claim naming a Question, the `questions linked:` line of that Question names the row. Any
          other `check read` line (a heading, a created subject, the rows' order and the rest)
          needs no answer, and one named on `owed:` with any answer is taken: the runner's own
          check of that kind holds this read to it again. Each `owed:` line, and the
          `not written:` line it is held to, is read with each control character as a space, as
          the ledger and so the owed file hold an entry. With `--owed none`, a first read, `owed:`
          reads `none`. A failure, an entry left unnamed among them, is a mismatch named `owed`.

        - On a window 1 unit, each entry of `code lists:` is in one of its shapes:
          `<kind> printed <n> recorded <n>`, ending with any of `, columns not read: <headers>`,
          `, <k> already recorded on <sheet>` and `, <k> not readable: <codes>`, `<k>` the number
          of codes it names; `<what the list is> none printed`; or the whole line `none`. An entry
          in no shape, and a kind named on more than one entry, are mismatches named `code lists`.

        - With `--spans`, a manual part's `Reads:` line as its dispatch named it, `spans read:` is
          held to those spans in that order, each once, a span left off only where its section
          is on `sections not checked:` as `manual removed`, `manual changed` or `not on the
          package`, and `section lines:` to one line per span read, in that order, each
          `<span> | puts: ... | rows: ... | left: ... | silence: ...`. A failure is a mismatch
          named `spans` or `section lines`.

        Exit 0: the report is whole and agrees with itself; it prints `report whole`. Exit 2: the
        report is not whole; it prints one line, `missing` or `not whole: no <labels>` or `not
        whole: <what>`, ready for the runner's note. Exit 3: the report is whole and some of it
        disagrees; it prints one line per mismatch, `<check> <value>`, ready for a `deviation` note.

    sh run.sh unit_report.py owed '<run folder>' <window> <unit id> --read <k>

        Writes `<run folder>/owed/<unit id>.read-<k>.md`, the work read k of a unit owes, off the
        ledger alone, with the subjects that stand under the unit's prefix before read k on stdin,
        one per line, or `none`:

            owed: <unit id> read <k>
            held: <subject>                                    (one per line, or `held: none`)
            not written by read <j>: <entry copied whole>
            check read <j> failed: <clause copied whole>
            no report from read <j>

        or `none` after the `held:` lines where nothing is owed. The entries are the unit's
        `anomaly not written: <entry>` notes and its `deviation ..., read <j>` notes, from the last
        read that verified ok, or the first read where none did, up to read k - 1: a read that
        verified ok took off every entry before it and noted again what it did not write, and a
        read that did not discharged nothing. Its failed checks and lost reports are those of the
        reads after it that did not verify ok. An entry two reads noted is written once, under the
        earlier.

    sh run.sh unit_report.py restore '<run folder>' 3 <unit id>

        For a window 3 unit, a package review, a manual part or a standard lines unit, whose latest `verified` line reads ok, with no
        `dispatch` line after it, and whose own report of that read is not whole, writes
        `<run folder>/reports/<unit id>.read-<k>.restored.md`, `<k>` the read that line checked,
        from the read plan, that `verified` line, the names and trades files and the unit's notes
        of that read, and appends one note to the ledger through `ledger.py`:

            note 3 <pass id> <unit id> deviation <package name> report written from the record to reports/<unit id>.read-<k>.restored.md, read <k>

        The reader's own file is never opened for writing or renamed. Run twice, it writes the same
        file and appends the note once. It refuses a unit of another window, one the read plan
        does not carry, and one whose latest `verified` line does not read ok or has a `dispatch`
        line after it: a read that failed is read again, never restored. Where the reader's report
        of that read is whole, it says so and writes nothing.

    sh run.sh unit_report.py trades '<run folder>' <pass id> <unit id> <<'EOF'
    <unit id> trade <catalog id> <count>
    <unit id> touched <catalog id>
    EOF

        Writes one unit's trades as one set: `<run folder>/trades/<pass id>.txt`, `<pass id>` the
        pass the unit's latest `verified` line names, then holds exactly the lines on stdin for the
        unit, in the file's two shapes, or none where stdin reads `none`. The unit's earlier lines
        are taken out and the new ones stand where the first of them stood, or at the end; every
        other unit's line stays as it was. The file is replaced whole. Then the unit's line on
        `<run folder>/trades/<pass id>.written` becomes `<unit id> read <k>`, one unit per line,
        `<k>` the read the unit's last `verified` line naming the pass closed, counted by the
        unit's `dispatch` lines above it. It tells a unit whose set is empty from one whose set was
        never written, and a set written for an earlier read from the latest read's; no other
        script reads it, and the trades file's shapes are unchanged. Run twice with the same lines,
        it changes nothing. It refuses a line of another unit, a line in neither shape, a catalog
        id given two counts, and a unit with no `verified` line naming the pass.

    sh run.sh unit_report.py touched '<run folder>' <window> <unit id> --kind <sheet|vocabulary|review|manual>

        Prints one `<unit id> touched <catalog id>` line per catalog id that any read of the unit
        carrying a `verified` line, ok or mismatch, named on its `trades touched:` line, each once:
        a failed read's writes stay on the record, so its trades are the unit's too. Each read's
        ids come off its own report where the report check holds it whole, and otherwise off its
        confirmed file. A read with neither is named on stderr, its trades not known, and one
        `note <window> <pass> <unit id> anomaly the trades read <k> of <unit id> wrote to are not
        known, ...` goes on the ledger through `ledger.py` for it, under the pass of the unit's
        latest `verified` line, where the ledger does not already carry that note for that read, so
        the check-in and the close-out name it and a second run appends nothing. The runner copies
        the lines on stdout into the unit's trades call.

    sh run.sh unit_report.py confirmed '<run folder>' <window> <unit id> --read <k> <<'EOF'
    updated subjects: <subjects, or none>
    questions raised ids: <ids, or none>
    questions replied ids: <ids, or none>
    trades touched: <catalog ids, one per line, or none>
    EOF

        Where the runner verified read k off the reader's returned message, the report file not
        being whole, writes the three lists its check confirmed, and the catalog ids on the
        message's `trades touched:` line as reported, to
        `<run folder>/confirmed/<unit id>.read-<k>.md`, before that read's closing append, so a
        later runner merging the unit's reads, or writing its trades set with its `touched`
        lines after a stop, has them where no whole report of the read is on file. It is the
        runner's record of its own check, not a report: its first line says so,
        and no line of it says a page was read. A file of a read with no `verified` line on the
        ledger, the runner having stopped before the closing append, is ignored.

    sh run.sh unit_report.py codes '<run folder>' <unit id> <<'EOF'
    code lists: <the report's `code lists:` line, its entries on the lines under it as the report gives them>
    subjects: <nothing, or `truncated` where the sheet's row says the scan was cut>
    <each subject the `verify_unit` row of the unit's sheet lists, one per line>
    EOF

        Holds a window 1 unit's `code lists:` line to the codes on the record citing its sheet. The
        sheet's type comes off `plan/window-1.json` (the unit's `unitKey`) and `inventory.json`.
        The subjects are counted by kind, the part before the first `:`, leaving out rows,
        Questions, the sheet's own reading and kind declarations (NOT_CODE_KINDS). It prints
        `codes <kind> printed <n> on the record <c>` for each kind whose count `c` is below the
        codes its entry says the page prints less those already recorded on another sheet and
        those not readable, and `codes none on the record on a <schedule or legend> sheet` where
        the sheet is a schedule or a legend, no code cites it, no entry reads `none printed`, and
        no kind's printed codes are all already recorded or not readable. Exit 0 prints `codes whole`,
        or `codes not held: <why>` for a repeated lines unit, a sheet with no type, or a row of
        subjects the scan cut; exit 3 prints the mismatches, one per line, ready for a `deviation`
        note under the check `codes`.

Exit codes for `owed`, `restore`, `trades`, `touched`, `confirmed` and `codes`: 0 done; 1 a named
failure, one line on stderr; 2 argparse rejected the invocation; and for `codes`, 3 a kind short
on the record.

Grounding role: reads files and copies lines. It reads no record, and no line it writes says a page
was read or a search was run.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

# Each reader's report shape, in its order, the label each line opens with, as the agent's own
# report shape gives it. The harness holds each list to its agent's shape.
SHEET_LABELS = (
    "unit", "pages read", "pages unread", "cited sheets", "page citations", "set version", "created",
    "created subjects", "updated subjects", "questions raised ids", "questions replied ids",
    "questions linked", "sent", "trades", "trades touched", "definitions kinds added",
    "schedules under rows", "sheet readings written", "anomalies", "grain questions",
    "door-owned suggestions", "owed",
)
# A window 1 unit (`scope-vocabulary-reader`) names, after the kinds it added, every code list its
# page prints, each entry in one of the shapes `code_list_entry` reads.
VOCABULARY_LABELS = (
    "unit", "pages read", "pages unread", "cited sheets", "page citations", "set version", "created",
    "created subjects", "updated subjects", "questions raised ids", "questions replied ids",
    "questions linked", "sent", "trades", "trades touched", "definitions kinds added", "code lists",
    "schedules under rows", "sheet readings written", "anomalies", "grain questions",
    "door-owned suggestions", "owed",
)
REVIEW_LABELS = (
    "unit", "harvested", "notes read", "searches", "terms too general", "pages opened", "created",
    "created subjects", "updated subjects", "manual updates", "field updates", "questions raised ids",
    "questions replied ids", "questions linked", "questions alone", "sent", "trades",
    "sheet readings written", "anomalies", "grain questions", "silent sections", "unspecified work",
    "compared", "left by the parts", "sections not checked", "families not checked",
    "standard lines found later", "headings written", "rows ordered", "rows on other packages",
    "bounds reached", "door-owned suggestions", "not written", "owed",
)
# A manual part (`scope-manual-reader`): it reads its spans and says what each left on its section
# line, and settles no heading.
MANUAL_LABELS = (
    "unit", "harvested", "notes read", "searches", "terms too general", "pages opened", "created",
    "created subjects", "updated subjects", "manual updates", "field updates", "questions raised ids",
    "questions replied ids", "questions linked", "questions alone", "sent", "trades",
    "sheet readings written", "anomalies", "grain questions", "silent sections", "unspecified work",
    "compared", "spans read", "section lines", "context pages", "carried", "sections not checked",
    "families not checked", "door-owned suggestions", "not written", "owed",
)
# The reasons a manual part leaves one of its spans off `spans read:`, named for its section on
# `sections not checked:`.
UNREAD_SPAN_REASONS = ("manual removed", "manual changed", "not on the package")
_SPAN_TEXT_RE = re.compile(r"^(\S+) p([1-9][0-9]*)-p([1-9][0-9]*) of (\S+)(?: \(section p([1-9][0-9]*)-p([1-9][0-9]*)\))?$")
_SECTION_LINE_RE = re.compile(r"^(.+?) \| puts: (.+?) \| rows: (.+?) \| left: (.+?) \| silence: (.+)$")
# A package's standard lines unit (`scope-standard-lines`): it reads no manual page and settles no
# heading, raises no Question, and names each line the script printed on `standard lines:`.
STANDARD_LABELS = (
    "unit", "searches", "pages opened", "created", "created subjects", "updated subjects",
    "manual updates", "field updates", "questions raised ids", "questions replied ids", "sent",
    "trades", "anomalies", "standard lines", "door-owned suggestions", "not written", "owed",
)
LABELS = {
    "sheet": SHEET_LABELS, "vocabulary": VOCABULARY_LABELS, "review": REVIEW_LABELS,
    "manual": MANUAL_LABELS, "standard": STANDARD_LABELS,
}
WINDOW_3_KINDS = ("review", "manual", "standard")

_CREATED_LINE_RE = re.compile(
    r"^created: (\S+)\s+updated: (\S+)\s+questions raised: (\S+)\s+questions replied: (\S+)\s*$"
)
_SENT_LINE_RE = re.compile(r"^sent: (\S+)\s+landed: (\S+)\s+conflicts:")
_SUBJECT_RE = re.compile(r"scope[A-Za-z]*:[^\s,;()]+")
_QUESTION_RE = re.compile(r"question:[^\s,;()]+")
_REPLY_RE = re.compile(r"(?:question:|clm-)[^\s,;()]+")

# The three outcomes an `owed:` entry ends with, after ` | `.
_OUTCOME_RE = re.compile(r"^(?:written (\S+)|read, nothing to write|not written, .+)$")
# The two outcomes a failed claim ends with, after ` | `.
_CLAIM_OUTCOME_RE = re.compile(r"^(?:written (\S+)|not needed, .+)$")

# The lines of an owed file, as `owed` writes them.
_OWED_ENTRY_RE = re.compile(r"^not written by read ([1-9][0-9]*): (.+)$")
_HELD_RE = re.compile(r"^held: (.+)$")
# A failed check of an earlier read, and the checks among them that held a write the read claimed
# on a named row: an update, a field update, a Question cited on a row, a manual update. The
# runner's note names the check, then the subject, then the read.
_FAILED_RE = re.compile(r"^check read ([1-9][0-9]*) failed: (.+)$")
_CLAIM_CHECK_RE = re.compile(
    r"(?:^| )(updated|field updates|manual updates|questions linked|page citations) (.*?), read [1-9][0-9]*$"
)
# An `owed` failure quotes the owed line it failed on, which can be a failed claim: its check is
# `owed`, named before the claim it quotes.
_OWED_CHECK_RE = re.compile(r"(?:^| )owed (?:check read [1-9][0-9]* failed:|not written by read [1-9][0-9]*:)")
# A predicate that carries a trade code, as `packageRole:09 21 16` does, runs on through the code's
# groups: two writes of one predicate on two trades are two writes.
_CODED_PREDICATE_RE = re.compile(r":\d{2}$")
_CODE_GROUP_RE = re.compile(r"^\d{2}(?:\.\d{2})?$")
# The report's own list each claimed write is named on, the list the runner's check holds to the
# record for that write: a read that writes the row again names it there, and the runner checks
# every row on that list against the record again.
CLAIM_LISTS = {
    "updated": "updated subjects", "questions linked": "questions linked",
    "manual updates": "manual updates", "field updates": "field updates",
    "page citations": "page citations",
}
# The lists whose lines each open with the row they name; the others name rows anywhere on a line.
_ROW_FIRST_LISTS = ("manual updates", "field updates", "page citations")

# A list marker a report line may open with, as a bulleted list under a label carries it.
_LIST_MARKER_RE = re.compile(r"^[-*]\s+")

NOT_UTF8 = "not whole: the report is not UTF-8 text"

# The ledger's notes this script reads: what a read did not write, and how a read ended.
_NOT_WRITTEN_NOTE = "not written: "
_READ_END_RE = re.compile(r", read ([1-9][0-9]*)$")
_NO_REPORT_RE = re.compile(r"(?: no report| reader stopped answering), read [1-9][0-9]*$")

OWED_FOLDER = "owed"
REPORTS_FOLDER = "reports"


class ReportError(Exception):
    """A named failure with a one-line reason, reported on stderr and exiting 1."""


# How a restored report names the kind of window 3 unit it stands in for.
UNIT_KIND_SAID = {"manual": "manual part", "standard": "standard lines unit", "review": "package review"}


def restored_name(unit: str, read: int) -> str:
    return f"{unit}.read-{read}.restored.md"


# --------------------------------------------------------------------------- #
# check
# --------------------------------------------------------------------------- #

def _label_of(line: str, labels: tuple[str, ...]) -> str | None:
    for label in sorted(labels, key=len, reverse=True):
        if line == f"{label}:" or line.startswith(f"{label}: "):
            return label
    return None


def sections(text: str, labels: tuple[str, ...]) -> dict[str, list[str]]:
    """
    Each label's text: what follows the label on its line, then each line under it up to the next
    label, blank lines dropped. A label written twice keeps its first.
    """
    found: dict[str, list[str]] = {}
    current: list[str] | None = None
    for raw in text.splitlines():
        line = raw.strip()
        if not line:
            continue
        label = _label_of(line, labels)
        if label is None:
            if current is not None:
                current.append(line)
            continue
        rest = line[len(label) + 1:].strip()
        if label in found:
            current = None
            continue
        current = found[label] = [rest] if rest else []
    return found


def _is_none(lines: list[str]) -> bool:
    return [line.strip().strip('"').lower() for line in lines] in ([], ["none"])


def _distinct(pattern: re.Pattern, lines: list[str]) -> list[str]:
    seen: list[str] = []
    for line in lines:
        for token in pattern.findall(line):
            token = token.rstrip(".")
            if token not in seen:
                seen.append(token)
    return seen


def _whole_number(text: str) -> int | None:
    return int(text) if text.isdigit() else None


def claim_of(line: str) -> tuple[str, list[str]] | None:
    """
    The check and the rows a `check read <j> failed:` line names where the failed check held a
    write the read claimed on a named row, or None for any other line.
    """
    failed = _FAILED_RE.match(line)
    if failed is None:
        return None
    check = _CLAIM_CHECK_RE.search(failed.group(2))
    if check is None or _OWED_CHECK_RE.search(failed.group(2)[: check.start() + 1]):
        return None
    subjects = _distinct(_SUBJECT_RE, [check.group(2)])
    return (check.group(1), subjects) if subjects else None


def predicate_of(words: list[str]) -> str | None:
    """
    The predicate a run of words opens with: the first word, and where it ends in a trade code's
    first group, the code's other groups after it, so `packageRole:09 21 16` is read whole.
    """
    if not words:
        return None
    first = words[0].rstrip(".,;")
    if not first:
        return None
    out = [first]
    if _CODED_PREDICATE_RE.search(first):
        for word in words[1:3]:
            group = word.rstrip(".,;")
            if _CODE_GROUP_RE.match(group) is None:
                break
            out.append(group)
    return " ".join(out)


def claimed_write(check: str, value: str, subjects: list[str]) -> dict:
    """
    What a failed claim names beside its row, where its check names one: the predicate after the
    row on a `field updates` claim, the Question on a `questions linked` claim.
    """
    if check == "questions linked":
        questions = _distinct(_QUESTION_RE, [value])
        return {"question": questions[0]} if questions else {}
    if check == "field updates":
        words = value.split()
        at = next((i for i, word in enumerate(words) if word.rstrip(".,;") in subjects), None)
        rest = words[at + 1:] if at is not None else []
        while rest and (not rest[0].rstrip(".,;") or _SUBJECT_RE.match(rest[0])):
            rest = rest[1:]
        predicate = predicate_of(rest)
        return {"predicate": predicate} if predicate else {}
    return {}


def _flat(text: str) -> str:
    """`text` with each control character a space and every run of spaces one, as the ledger holds it."""
    import ledger as ledger_script

    return " ".join(ledger_script.one_line(text).split())


def claim_subjects(line: str) -> list[str] | None:
    """The rows `claim_of` finds on a failed claim, or None."""
    claimed = claim_of(line)
    return claimed[1] if claimed else None


def listed_rows(found: dict[str, list[str]], label: str) -> set[str]:
    """
    The rows a report names on one of its lists: on `manual updates:`, `field updates:` and `page
    citations:` the row each line opens with, a list marker `- ` or `* ` read past, and on any other
    list every row it names.
    """
    lines = found.get(label)
    if not lines or _is_none(lines):
        return set()
    if label not in _ROW_FIRST_LISTS:
        return set(_distinct(_SUBJECT_RE, lines))
    rows = set()
    for line in lines:
        first = _SUBJECT_RE.match(_LIST_MARKER_RE.sub("", line, count=1))
        if first:
            rows.add(first.group(0).rstrip("."))
    return rows


def field_predicates(found: dict[str, list[str]], subject: str) -> set[str]:
    """The predicates the report's `field updates:` lines that open with `subject` name after it."""
    lines = found.get("field updates")
    if not lines or _is_none(lines):
        return set()
    out = set()
    for line in lines:
        words = _LIST_MARKER_RE.sub("", line, count=1).split()
        if len(words) > 1 and words[0].rstrip(".") == subject:
            predicate = predicate_of(words[1:])
            if predicate:
                out.add(predicate)
    return out


def linked_rows(found: dict[str, list[str]], question: str) -> set[str]:
    """The rows the report's `questions linked:` lines naming `question` name."""
    lines = found.get("questions linked")
    if not lines or _is_none(lines):
        return set()
    return {
        row for line in lines if question in _distinct(_QUESTION_RE, [line])
        for row in _distinct(_SUBJECT_RE, [line])
    }


def read_owed_file(path: Path) -> dict:
    """
    The entries an owed file names, each a `not written by read` line or a `check read` line, and
    the subjects it says were held before the read. Each entry is `{"line", "claim", "check",
    "required"}`: `claim` the rows a failed claim names, None on any other line; `required` true on
    a `not written by read` line and a failed claim, the lines `owed:` has to answer, and false on
    every other failed check, which the runner's own check of that kind holds this read to again.
    A failed claim also carries `predicate` (`field updates`) or `question` (`questions linked`)
    where its line names one.
    """
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as e:
        raise ReportError(f"cannot read the owed file {path}: {e}") from e
    entries: list[dict] = []
    held: list[str] = []
    others: list[str] = []
    for raw in text.splitlines():
        line = _flat(raw)
        if line and not _OWED_ENTRY_RE.match(line) and not _FAILED_RE.match(line):
            # Any other line of the file, a `no report from read <j>` line among them: a reader
            # that copies one onto `owed:` is not refused for it.
            others.append(line)
        if _OWED_ENTRY_RE.match(line):
            entries.append({"line": line, "claim": None, "check": None, "required": True})
        failed = _FAILED_RE.match(line)
        if failed:
            entry = {"line": line, "claim": None, "check": None, "required": False}
            claimed = claim_of(line)
            if claimed:
                value = _CLAIM_CHECK_RE.search(failed.group(2)).group(2)
                entry.update(claim=claimed[1], check=claimed[0], required=True)
                entry.update(claimed_write(claimed[0], value, claimed[1]))
            entries.append(entry)
        held_line = _HELD_RE.match(line)
        if held_line and held_line.group(1) != "none":
            held.append(held_line.group(1).strip())
    return {"entries": entries, "held": held, "others": others}


def dispatched_spans(reads: str) -> list[str]:
    """The spans a manual part's `Reads:` line names, `; ` between them, each as written there."""
    spans = [span.strip() for span in reads.split("; ") if span.strip()]
    for span in spans:
        if _SPAN_TEXT_RE.match(span) is None:
            raise ReportError(f"the dispatched span {span!r} is not `<code> p<a>-p<b> of <fileId>`")
    return spans


def _report_items(lines: list[str]) -> list[str]:
    """A list label's entries, one per line, a list marker read past and `none` reading nothing."""
    items = [_LIST_MARKER_RE.sub("", line.strip(), count=1).strip() for line in lines]
    items = [item for item in items if item]
    return [] if items in ([], ["none"]) else items


def span_mismatches(found: dict[str, list[str]], spans: list[str]) -> list[str]:
    """
    A manual part's `spans read:` and `section lines:` held to the spans its dispatch named: every
    span read in the dispatch's order, each once, a span left off only where its section is on
    `sections not checked:` with one of UNREAD_SPAN_REASONS, and one section line per span read,
    in the same order, opening with that span and carrying its four fields. A failure is a mismatch
    named `spans` or `section lines`.
    """
    out: list[str] = []
    unread = set()
    for line in _report_items(found.get("sections not checked", [])):
        code = line.split()[0] if line.split() else ""
        if any(reason in line for reason in UNREAD_SPAN_REASONS):
            unread.add(code)
    read = _report_items(found.get("spans read", []))
    wanted = [span for span in spans if span.split()[0] not in unread]
    if read != wanted:
        missing = [span for span in wanted if span not in read]
        extra = [span for span in read if span not in wanted]
        said = (f"without {'; '.join(missing)}" if missing else "") + (
            f"{'; ' if missing and extra else ''}beyond {'; '.join(extra)}" if extra else "")
        out.append(f"spans {said or 'read out of the dispatched order'}")
    lines = _report_items(found.get("section lines", []))
    parsed = [_SECTION_LINE_RE.match(line) for line in lines]
    for line, match in zip(lines, parsed):
        if match is None:
            out.append(f"section lines {line[:120]}, which is not `<span> | puts: | rows: | left: | silence:`")
    named = [match.group(1).strip() for match in parsed if match is not None]
    for span in wanted:
        if named.count(span) == 0:
            out.append(f"section lines {span}, with no section line")
        elif named.count(span) > 1:
            out.append(f"section lines {span}, named twice")
    for span in named:
        if span not in wanted:
            out.append(f"section lines {span}, which is no span this read read")
    if not [m for m in out if m.startswith("section lines")] and named != [s for s in wanted if s in named]:
        out.append("section lines out of the order of `spans read:`")
    return out


# A window 1 report's `code lists:` entries, one per line or `; ` between them: one entry per kind
# the page's lists print, `<kind> printed <n> recorded <n>`, `<n>` counting each code once however
# many of the page's lists print it, then `, columns not read: <headers>` where cells were left
# blank, `, <k> already recorded on <sheet>` for codes of the same meaning the page adds no column
# to, and `, <k> not readable: <codes>` for codes whose every other cell is blank or unreadable; a
# legend of drawn symbols only, `<what the list is> none printed`; or the whole line `none` where
# the page prints no list.
_CODE_LIST_RE = re.compile(r"^([a-z][A-Za-z0-9]*) printed ([0-9]+) recorded ([0-9]+)((?:, .+)?)$")
_CODE_LIST_COLUMNS_RE = re.compile(r"^columns not read: \S.*$")
_CODE_LIST_ALREADY_RE = re.compile(r"^([0-9]+) already recorded on \S.*$")
_CODE_LIST_UNREADABLE_RE = re.compile(r"^([1-9][0-9]*) not readable: (\S.*)$")
_CODE_LIST_ENDING_RE = re.compile(r", (?=[0-9]+ already recorded on |[0-9]+ not readable: |columns not read: )")
_NONE_PRINTED_RE = re.compile(r"^\S.* none printed$")


def code_list_entry(entry: str) -> dict | None:
    """
    One `code lists:` entry read: `{kind, printed, recorded, already, unreadable}` for a kind's
    codes, `{none: True}` for a legend of drawn symbols only, or None where the entry is in neither
    shape, a `not readable` count that is not the number of codes it names among them, or a code
    named not readable twice.
    """
    if _NONE_PRINTED_RE.match(entry):
        return {"none": True}
    shaped = _CODE_LIST_RE.match(entry)
    if shaped is None:
        return None
    already = 0
    unreadable: set[str] = set()
    rest = shaped.group(4)
    if rest:
        # The endings, in any order: `columns not read:` and `not readable:` run to the next ending
        # or the end.
        for part in _CODE_LIST_ENDING_RE.split(rest[2:]):
            if _CODE_LIST_COLUMNS_RE.match(part):
                continue
            already_part = _CODE_LIST_ALREADY_RE.match(part)
            if already_part is not None:
                already += int(already_part.group(1))
                continue
            unreadable_part = _CODE_LIST_UNREADABLE_RE.match(part)
            if unreadable_part is None:
                return None
            named = [code for code in re.split(r",\s*", unreadable_part.group(2).strip()) if code]
            if len(named) != int(unreadable_part.group(1)) or len(set(named)) != len(named) or unreadable & set(named):
                return None
            unreadable |= set(named)
    return {"kind": shaped.group(1), "printed": int(shaped.group(2)), "recorded": int(shaped.group(3)),
            "already": already, "unreadable": len(unreadable)}


def code_list_entries(lines: list[str]) -> tuple[list[dict], list[str], list[str]]:
    """
    The `code lists:` line's entries read, each entry in no shape, copied whole, and each kind named
    on more than one entry, where the page's lists of one kind take one entry between them.
    """
    if [line.strip().strip('"').lower() for line in lines] == ["none"]:
        return [], [], []
    entries: list[str] = []
    for line in lines:
        entries.extend(part.strip() for part in _LIST_MARKER_RE.sub("", line.strip()).split("; ") if part.strip())
    if not entries:
        return [], ["no entry, and not none"], []
    read, unshaped, repeated = [], [], []
    for entry in entries:
        shaped = code_list_entry(entry)
        if shaped is None:
            unshaped.append(entry)
            continue
        if "kind" in shaped and any(e.get("kind") == shaped["kind"] for e in read):
            if shaped["kind"] not in repeated:
                repeated.append(shaped["kind"])
            continue
        read.append(shaped)
    return read, unshaped, repeated


def problems(text: str, kind: str, owed: dict | None = None, owed_given: bool = False,
             spans: list[str] | None = None) -> tuple[list[str], list[str]]:
    """
    What keeps a report from being whole, and the mismatches of a whole one, `<check> <value>`
    each. `owed` is the owed file read, or None with `owed_given` for `--owed none`. `spans` are
    a manual part's dispatched spans, which its `spans read:` and `section lines:` are held to.
    """
    labels = LABELS[kind]
    found = sections(text, labels)
    missing = [label for label in labels if label not in found]
    if missing:
        # A few labels and a count, so the runner's note on it stays one short clause.
        named = ", ".join(missing[:4]) + (f" and {len(missing) - 4} more" if len(missing) > 4 else "")
        return [f"not whole: no {named}"], []
    created_line = _CREATED_LINE_RE.match("created: " + " ".join(found["created"][:1]))
    if created_line is None:
        return ["not whole: the created line is not `created: <n>   updated: <n>   questions raised: <n>   questions replied: <n>`"], []
    counts = [_whole_number(value) for value in created_line.groups()]
    if None in counts:
        return ["not whole: a count on the created line is not a whole number"], []
    created, _updated, raised, replied = counts
    sent_line = _SENT_LINE_RE.match("sent: " + " ".join(found["sent"][:1]))
    if sent_line is None or None in (_whole_number(sent_line.group(1)), _whole_number(sent_line.group(2))):
        return ["not whole: the sent line carries no whole `sent:` and `landed:` numbers"], []
    if kind in WINDOW_3_KINDS and re.search(r"\d+", " ".join(found["searches"][:1])) is None:
        return ["not whole: the `searches:` line carries no whole number"], []

    # A count every report shape makes equal to its list is held to it: each scope item created has
    # one subject on `created subjects:`, and each Question raised one id on `questions raised
    # ids:`. `questions replied:` counts replies while its list names the Questions replied to, so
    # two replies to one Question count 2 and list 1: the count is held to at least one id where it
    # is above 0, to `none` where it is 0, and never below the ids listed. `updated:` counts rows
    # its list leaves off (a heading-only row, a retired row) and leaves off rows a list names (a
    # citation the door answered duplicate), so it is compared with no list; the runner finds each
    # subject and id a report names on the record.
    mismatches: list[str] = []
    created_subjects = [] if _is_none(found["created subjects"]) else _distinct(_SUBJECT_RE, found["created subjects"])
    if len(created_subjects) != created:
        mismatches.append(f"report created {created} and created subjects {len(created_subjects)}")
    raised_ids = [] if _is_none(found["questions raised ids"]) else _distinct(_QUESTION_RE, found["questions raised ids"])
    if len(raised_ids) != raised:
        mismatches.append(f"report questions raised {raised} and questions raised ids {len(raised_ids)}")
    replied_ids = [] if _is_none(found["questions replied ids"]) else _distinct(_REPLY_RE, found["questions replied ids"])
    if (replied == 0) != (not replied_ids) or replied < len(replied_ids):
        mismatches.append(f"report questions replied {replied} and questions replied ids {len(replied_ids)}")

    if kind == "vocabulary":
        _, unshaped, repeated = code_list_entries(found["code lists"])
        mismatches.extend(f"code lists {entry}" for entry in unshaped)
        mismatches.extend(f"code lists {kind} named on more than one entry" for kind in repeated)

    if owed is not None or owed_given:
        mismatches.extend(_owed_mismatches(found, kind, owed, created_subjects))
    if spans is not None and kind == "manual":
        mismatches.extend(span_mismatches(found, spans))
    return [], mismatches


def _owed_mismatches(found: dict[str, list[str]], kind: str, owed: dict | None, created_subjects: list[str]) -> list[str]:
    # A list marker before an entry is read past, as on `field updates:`, and each line is read as
    # the ledger holds it, a control character a space, as the owed file was written off it.
    lines = [] if _is_none(found["owed"]) else [_flat(_LIST_MARKER_RE.sub("", line, count=1)) for line in found["owed"]]
    if owed is None:
        return [] if not lines else [f"owed {lines[0][:120]}, and this read was handed nothing owed"]
    held = set(owed["held"])
    own = [subject for subject in created_subjects if subject not in held]
    field_subjects = listed_rows(found, "field updates")
    not_written = _flat(" ".join(found.get("not written", [])))
    out: list[str] = []
    named: set[int] = set()
    for line in lines:
        at = next(
            (i for i, entry in enumerate(owed["entries"])
             if line == entry["line"] or line.startswith(f"{entry['line']} |")), None,
        )
        if at is None:
            if any(line == other or line.startswith(f"{other} |") for other in owed.get("others", [])):
                continue
            out.append(f"owed {line[:120]}, which the Owed file does not name")
            continue
        if not owed["entries"][at]["required"]:
            # A failed check that held no claimed write: put right in this read, and the runner's
            # check of that kind holds this read to it again, so any answer, or none, is taken.
            continue
        claim = owed["entries"][at]["claim"]
        entry = owed["entries"][at]["line"]
        answer = line[len(entry):].strip().removeprefix("|").strip()
        if at in named:
            out.append(f"owed {entry[:120]}, named twice")
            continue
        named.add(at)
        if claim is not None:
            # A write an earlier read claimed and its check did not find: written now, the row named
            # on this read's own list for that write, which the runner's check holds to the record
            # again, or said not to be needed. The row need not be one this read created. Where
            # the failed claim names the predicate or the Question, this read's line names it too.
            outcome = _CLAIM_OUTCOME_RE.match(answer)
            label = CLAIM_LISTS[owed["entries"][at]["check"]]
            if outcome is None:
                out.append(f"owed {entry[:120]}, with no outcome of written or not needed")
            elif outcome.group(1) is not None:
                subject = outcome.group(1).rstrip(".,")
                predicate = owed["entries"][at].get("predicate")
                question = owed["entries"][at].get("question")
                if subject not in claim:
                    out.append(f"owed {entry[:120]}, written {subject}, which is not the row the failed check names")
                elif subject not in listed_rows(found, label):
                    out.append(f"owed {entry[:120]}, written {subject}, which this report's `{label}:` line does not name")
                elif predicate and predicate not in field_predicates(found, subject):
                    out.append(
                        f"owed {entry[:120]}, written {subject}, which no line of this report's "
                        f"`field updates:` names with the predicate {predicate}"
                    )
                elif question and subject not in linked_rows(found, question):
                    out.append(
                        f"owed {entry[:120]}, written {subject}, which this report's `questions linked:` "
                        f"line for {question} does not name"
                    )
            continue
        outcome = _OUTCOME_RE.match(answer)
        if outcome is None:
            out.append(f"owed {entry[:120]}, with no outcome of written, read or not written")
        elif outcome.group(1) is not None:
            subject = outcome.group(1).rstrip(".,")
            if subject not in own and subject not in field_subjects:
                out.append(f"owed {entry[:120]}, written {subject}, which is no row this read created or wrote a field on")
        elif outcome.group(0).startswith("read, nothing"):
            if kind in WINDOW_3_KINDS:
                out.append(f"owed {entry[:120]}, read with nothing to write, which only a sheet's unread part may say")
        else:
            body = _OWED_ENTRY_RE.match(entry).group(2)
            if kind in WINDOW_3_KINDS and body not in not_written:
                out.append(f"owed {entry[:120]}, not written and not on this report's `not written:` line")
    for i, entry in enumerate(owed["entries"]):
        if entry["required"] and i not in named:
            out.append(f"owed {entry['line'][:120]}, not named on the `owed:` line")
    return out


def report_text(data: bytes) -> str | None:
    """
    A report's bytes as text, strictly UTF-8, or None where they are not: one decoding for a report
    file and for a returned message on stdin, so the two are held alike.
    """
    try:
        return data.decode("utf-8")
    except UnicodeDecodeError:
        return None


def problems_of_file(path: Path, kind: str) -> list[str]:
    """Why the report at `path` is no usable report, or nothing where it is whole and agrees."""
    if not path.is_file():
        return ["missing"]
    try:
        data = path.read_bytes()
    except OSError as e:
        return [f"not whole: cannot be read ({e})"]
    text = report_text(data)
    if text is None:
        return [NOT_UTF8]
    broken, mismatches = problems(text, kind)
    return broken or mismatches


# --------------------------------------------------------------------------- #
# The ledger, as this script reads it
# --------------------------------------------------------------------------- #

def unit_history(ledger: Path, window: str, unit: str) -> dict:
    """
    One unit's lines of one window, by read: each read's notes and its `verified` line, a read
    being the unit's `dispatch` lines above. Only whole lines are read.
    """
    import ledger as ledger_script

    try:
        data = ledger.read_bytes()
    except OSError as e:
        raise ReportError(f"cannot read the ledger at {ledger}: {e}") from e
    text = data[: data.rfind(b"\n") + 1].decode("utf-8", "replace")
    dispatches = 0
    reads: dict[int, dict] = {}
    latest = None
    for number, raw in enumerate(ledger_script.lines_of(text), 1):
        parts = raw.strip().split()
        if len(parts) < 4 or parts[0] not in ("dispatch", "verified", "note"):
            continue
        if parts[1] != window or parts[3] != unit:
            continue
        if parts[0] == "dispatch":
            dispatches += 1
            latest = None
            continue
        read = reads.setdefault(dispatches, {"notes": [], "verified": None})
        if parts[0] == "verified":
            result = parts[parts.index("result") + 1] if "result" in parts[:-1] else None
            read["verified"] = {"line": number, "pass": parts[2], "result": result, "text": raw.strip()}
            latest = (dispatches, read["verified"])
        else:
            read["notes"].append({"pass": parts[2], "kind": parts[4] if len(parts) > 4 else "", "clause": " ".join(parts[5:]), "text": raw.strip()})
    return {"dispatches": dispatches, "reads": reads, "latest": latest}


# --------------------------------------------------------------------------- #
# owed
# --------------------------------------------------------------------------- #

def owed_lines(history: dict, unit: str, read: int, held: list[str]) -> list[str]:
    reads = history["reads"]
    passed = [j for j in range(1, read) if (reads.get(j) or {}).get("verified") and reads[j]["verified"]["result"] == "ok"]
    since = passed[-1] if passed else 1
    entries: list[str] = []
    seen: set[str] = set()
    for j in range(since, read):
        for note in (reads.get(j) or {}).get("notes", []):
            if note["kind"] == "anomaly" and note["clause"].startswith(_NOT_WRITTEN_NOTE):
                body = note["clause"][len(_NOT_WRITTEN_NOTE):].strip()
                if body and body not in seen:
                    seen.add(body)
                    entries.append(f"not written by read {j}: {body}")
    ended: list[str] = []
    for j in range(since + 1 if passed else 1, read):
        here = reads.get(j) or {}
        if here.get("verified") and here["verified"]["result"] == "ok":
            continue
        # Each note of a read that did not pass, ending `, read <j>`, says how that read ended.
        for note in here.get("notes", []):
            if note["kind"] != "deviation":
                continue
            end = _READ_END_RE.search(note["clause"])
            if end is None or int(end.group(1)) != j:
                continue
            if _NO_REPORT_RE.search(note["clause"]):
                line = f"no report from read {j}"
            else:
                line = f"check read {j} failed: {note['clause']}"
            if line not in ended:
                ended.append(line)
    out = [f"owed: {unit} read {read}"]
    out += [f"held: {subject}" for subject in held] or ["held: none"]
    out += entries + ended or ["none"]
    return out


def write_owed(run_folder: Path, window: str, unit: str, read: int, held_text: str) -> Path:
    if window not in ("1", "2", "3"):
        raise ReportError(f"window {window!r}: owed work is handed on in windows 1, 2 and 3")
    ledger = run_folder / "ledger.md"
    history = unit_history(ledger, window, unit)
    if read < 2 or read - 1 > history["dispatches"] or read < history["dispatches"]:
        raise ReportError(
            f"unit {unit} carries {history['dispatches']} dispatch lines in window {window}, so read "
            f"{read} is not its next read; a first read is handed `Owed: none`"
        )
    held = [line.strip() for line in held_text.splitlines() if line.strip() and line.strip() != "none"]
    path = run_folder / OWED_FOLDER / f"{unit}.read-{read}.md"
    _publish(path, "".join(f"{line}\n" for line in owed_lines(history, unit, read, held)).encode("utf-8"))
    return path


# --------------------------------------------------------------------------- #
# trades
# --------------------------------------------------------------------------- #

TRADES_FOLDER = "trades"
TRADES_WRITTEN_SUFFIX = ".written"


def _publish(path: Path, data: bytes) -> None:
    import ledger as ledger_script

    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        ledger_script.publish(path, data)
    except (OSError, ledger_script.LedgerError) as e:
        raise ReportError(str(e)) from None


def _trade_lines(unit: str, text: str) -> list[str]:
    """A unit's set of trades lines off stdin, each in one of the file's two shapes, or none."""
    lines = [" ".join(raw.split()) for raw in text.splitlines() if raw.strip()]
    if lines == ["none"]:
        return []
    if not lines:
        raise ReportError("no line on stdin; give the unit's trade and touched lines, or none")
    out: list[str] = []
    counts: dict[str, str] = {}
    for line in lines:
        parts = line.split(" ")
        if parts[0] != unit:
            raise ReportError(f"the line {line!r} names unit {parts[0]}, and this call writes unit {unit}'s set alone")
        if len(parts) >= 4 and parts[1] == "trade" and parts[-1].isdigit():
            code = " ".join(parts[2:-1])
            if counts.get(code, parts[-1]) != parts[-1]:
                raise ReportError(f"catalog id {code} carries two counts, {counts[code]} and {parts[-1]}; a set names each once")
            counts[code] = parts[-1]
        elif not (len(parts) >= 3 and parts[1] == "touched"):
            raise ReportError(
                f"the line {line!r} is neither `<unit id> trade <catalog id> <count>` nor "
                f"`<unit id> touched <catalog id>`"
            )
        if line not in out:
            out.append(line)
    return out


def trades_read(run_folder: Path, pass_id: str, unit: str) -> int:
    """
    The read whose set a trades write is: the read the unit's last `verified` line naming the pass
    closed, counted by the unit's `dispatch` lines of that window above it.
    """
    import ledger as ledger_script

    ledger = run_folder / "ledger.md"
    try:
        data = ledger.read_bytes()
    except OSError as e:
        raise ReportError(f"cannot read the ledger at {ledger}: {e}; a unit's trades are written after its verified line") from e
    dispatches: dict[str, int] = {}
    read = None
    for raw in ledger_script.lines_of(data[: data.rfind(b"\n") + 1].decode("utf-8", "replace")):
        parts = raw.split()
        if len(parts) < 4 or parts[3] != unit:
            continue
        if parts[0] == "dispatch":
            dispatches[parts[1]] = dispatches.get(parts[1], 0) + 1
        elif parts[0] == "verified" and parts[2] == pass_id:
            read = dispatches.get(parts[1], 0)
    if read is None:
        raise ReportError(
            f"the ledger carries no verified line of unit {unit} naming pass {pass_id}; a unit's "
            f"trades are written after its read is verified, under the pass that line names"
        )
    return read


def written_read(run_folder: Path, pass_id: str, unit: str) -> int | None:
    """The read whose trades set the marker `<pass id>.written` says was written for the unit."""
    written = run_folder / TRADES_FOLDER / f"{pass_id}{TRADES_WRITTEN_SUFFIX}"
    try:
        lines = written.read_bytes().decode("utf-8").splitlines() if written.is_file() else []
    except (OSError, UnicodeDecodeError) as e:
        raise ReportError(f"cannot read {written}: {e}") from e
    for line in lines:
        parts = line.split()
        if len(parts) == 3 and parts[0] == unit and parts[1] == "read" and parts[2].isdigit():
            return int(parts[2])
    return None


def write_trades(run_folder: Path, pass_id: str, unit: str, text: str) -> list[str]:
    """
    Make the pass's trades file hold exactly the unit's set on stdin: the unit's earlier lines taken
    out, the new ones put where the first of them stood or at the end, every other line as it was,
    published whole. Then the unit's line on `<pass id>.written` beside it becomes `<unit id> read
    <k>`, `<k>` the read the unit's last `verified` line naming the pass closed, which says that
    read's set was written, an empty set included. The same set written twice changes nothing.
    """
    read = trades_read(run_folder, pass_id, unit)
    new = _trade_lines(unit, text)
    path = run_folder / TRADES_FOLDER / f"{pass_id}.txt"
    try:
        old = path.read_bytes().decode("utf-8") if path.is_file() else ""
    except (OSError, UnicodeDecodeError) as e:
        raise ReportError(f"cannot read the trades file {path}: {e}") from e
    kept: list[str] = []
    at = None
    for raw in old.splitlines():
        if raw.split()[:1] == [unit]:
            at = len(kept) if at is None else at
            continue
        kept.append(raw)
    at = len(kept) if at is None else at
    lines = kept[:at] + new + kept[at:]
    data = "".join(f"{line}\n" for line in lines).encode("utf-8")
    out = []
    if not path.is_file() or path.read_bytes() != data:
        _publish(path, data)
        out.append(f"unit_report: wrote unit {unit}'s {len(new)} trades lines to {path}")
    else:
        out.append(f"unit_report: {path} already holds unit {unit}'s {len(new)} trades lines")
    written = path.parent / f"{pass_id}{TRADES_WRITTEN_SUFFIX}"
    try:
        marks = written.read_bytes().decode("utf-8").splitlines() if written.is_file() else []
    except (OSError, UnicodeDecodeError) as e:
        raise ReportError(f"cannot read {written}: {e}") from e
    mark = f"{unit} read {read}"
    if mark not in marks:
        kept_marks = [line for line in marks if line.split()[:1] != [unit]]
        _publish(written, "".join(f"{line}\n" for line in [*kept_marks, mark]).encode("utf-8"))
    out.append(f"unit_report: {written} names unit {unit}'s set of read {read}")
    return out


def touched_of_reads(run_folder: Path, window: str, unit: str, kind: str) -> tuple[list[str], list[int]]:
    """
    The catalog ids every read of the unit that carries a `verified` line, ok or mismatch, named on
    its `trades touched:` line, each once in read order: off the read's own report where the report
    check holds it whole, and otherwise off the confirmed file the runner wrote for that read. A
    failed read's writes stay on the record, so its trades count. Returns the ids and the reads
    whose trades are not known, neither file being on file.
    """
    import pass_summary

    if window not in ("1", "2", "3"):
        raise ReportError(f"window {window!r}: a unit's touched trades are gathered in windows 1, 2 and 3")
    history = unit_history(run_folder / "ledger.md", window, unit)
    ids: list[str] = []
    unknown: list[int] = []
    for read in sorted(j for j in history["reads"] if j >= 1):
        if history["reads"][read].get("verified") is None:
            continue
        report = pass_summary.unit_report(run_folder / REPORTS_FOLDER, unit, read, history["dispatches"])
        text = None
        if report.is_file():
            try:
                text = report_text(report.read_bytes())
            except OSError:
                text = None
        if text is not None and not problems(text, kind)[0]:
            lines = sections(text, LABELS[kind]).get("trades touched", [])
            codes = [] if _is_none(lines) else _catalog_ids(lines)
        elif (run_folder / CONFIRMED_FOLDER / confirmed_name(unit, read)).is_file():
            codes = confirmed_touched(run_folder / CONFIRMED_FOLDER / confirmed_name(unit, read))
        else:
            unknown.append(read)
            continue
        ids.extend(code for code in codes if code not in ids)
    return ids, unknown


def unknown_touched_note(unit: str, read: int) -> str:
    """The clause of the anomaly note that says a read's touched trades are not known."""
    return (
        f"the trades read {read} of {unit} wrote to are not known, since neither a whole report of "
        f"that read nor the runner's record of its check is on file, run only"
    )


def note_unknown_touched(run_folder: Path, window: str, unit: str, unknown: list[int]) -> list[str]:
    """
    Append one anomaly note through the ledger script for each read whose touched trades are not
    known, under the pass of the unit's latest `verified` line, so the check-in names it. A read the
    ledger already carries that note for is left alone, so a second run appends nothing.
    """
    import ledger as ledger_script

    if not unknown:
        return []
    history = unit_history(run_folder / "ledger.md", window, unit)
    said = {note["clause"] for read in history["reads"].values() for note in read["notes"] if note["kind"] == "anomaly"}
    last = max(j for j, read in history["reads"].items() if read.get("verified"))
    pass_id = history["reads"][last]["verified"]["pass"]
    notes = [
        f"note {window} {pass_id} {unit} anomaly {unknown_touched_note(unit, read)}"
        for read in unknown if unknown_touched_note(unit, read) not in said
    ]
    if not notes:
        return []
    try:
        return ledger_script.append_lines(run_folder / "ledger.md", notes)
    except ledger_script.LedgerError as e:
        raise ReportError(str(e)) from None


# --------------------------------------------------------------------------- #
# confirmed
# --------------------------------------------------------------------------- #

CONFIRMED_FOLDER = "confirmed"
CONFIRMED_LABELS = ("updated subjects", "questions raised ids", "questions replied ids", "trades touched")
_CONFIRMED_TOKENS = {
    "updated subjects": _SUBJECT_RE, "questions raised ids": _QUESTION_RE,
    "questions replied ids": _REPLY_RE,
}


def _catalog_ids(lines: list[str]) -> list[str]:
    """The catalog ids of a `trades touched:` list, one per line or comma separated, each once."""
    ids: list[str] = []
    for line in lines:
        for part in _LIST_MARKER_RE.sub("", line, count=1).split(","):
            code = " ".join(part.split())
            if code and code not in ids:
                ids.append(code)
    return ids


def confirmed_touched(path: Path) -> list[str]:
    """The catalog ids on a confirmed file's `trades touched:` line, for the unit's `touched` lines."""
    try:
        found = sections(path.read_bytes().decode("utf-8"), CONFIRMED_LABELS)
    except (OSError, UnicodeDecodeError) as e:
        raise ReportError(f"cannot read the confirmed file {path}: {e}") from e
    lines = found.get("trades touched", [])
    return [] if _is_none(lines) else _catalog_ids(lines)


def confirmed_name(unit: str, read: int) -> str:
    return f"{unit}.read-{read}.md"


def write_confirmed(run_folder: Path, window: str, unit: str, read: int, text: str) -> Path:
    """
    The lists a runner's check confirmed for one read verified off the reader's returned message,
    and the catalog ids on its `trades touched:` line as the reader reported them, written to
    `<run folder>/confirmed/<unit id>.read-<k>.md` before that read's closing append, so a later
    runner merges the lists, and writes the unit's whole trades set, `touched` lines included,
    where no whole report of the read is on file.
    """
    if window not in ("1", "2", "3"):
        raise ReportError(f"window {window!r}: a check's lists are kept in windows 1, 2 and 3")
    if read < 1:
        raise ReportError(f"read {read} is no read; reads count from 1")
    found = sections(text, CONFIRMED_LABELS)
    missing = [label for label in CONFIRMED_LABELS if label not in found]
    if missing:
        raise ReportError(
            f"no {', '.join(f'`{label}:`' for label in missing)} line on stdin; give the four "
            f"lists, each `none` where it names none"
        )
    body = [
        f"confirmed: {unit} read {read}, the lists the runner's check confirmed off the reader's "
        f"returned message; no line below says a page was read or a search was run",
    ]
    for label in CONFIRMED_LABELS:
        if _is_none(found[label]):
            body.append(f"{label}: none")
            continue
        if label == "trades touched":
            body.append(f"{label}: {', '.join(_catalog_ids(found[label]))}")
            continue
        tokens = _distinct(_CONFIRMED_TOKENS[label], found[label])
        if not tokens:
            raise ReportError(f"the `{label}:` list names nothing in its shape and is not `none`")
        body.append(f"{label}: {' '.join(tokens)}")
    path = run_folder / CONFIRMED_FOLDER / confirmed_name(unit, read)
    _publish(path, "".join(f"{line}\n" for line in body).encode("utf-8"))
    return path


# --------------------------------------------------------------------------- #
# restore
# --------------------------------------------------------------------------- #

_PLAN_UNIT_RE = re.compile(r"^[1-9][0-9]*\. (\S+): (.+?), trade (.+?), (?:reads (.+?), )?package (\S+)(.*)$")
_PART_RE = re.compile(r"^, manual part after (\S+), reads (.+?)(?: verified| skipped)?$")
_STANDARD_RE = re.compile(r"^, standard lines after (\S+)(?: verified| skipped)?$")


def _plan_unit(plan: Path, unit: str) -> dict:
    """The unit's line in the window 3 read plan and the pass whose block holds it."""
    try:
        lines = plan.read_text(encoding="utf-8").splitlines()
    except OSError as e:
        raise ReportError(f"cannot read the read plan at {plan}: {e}") from e
    first = next((line.strip() for line in lines if line.strip()), "")
    if first != "# Read plan: window 3":
        raise ReportError(f"{plan} is no window 3 read plan; a report is restored in window 3 alone")
    current = None
    for raw in lines:
        if raw.strip() == "## Deliberately left out":
            break
        heading = re.match(r"^### (\S+?)\.\s", raw)
        if heading:
            current = heading.group(1)
            continue
        match = _PLAN_UNIT_RE.match(raw.strip())
        if match and match.group(1) == unit and current is not None:
            part = _PART_RE.match(match.group(6))
            standard = _STANDARD_RE.match(match.group(6))
            spans = part.group(2) if part else (match.group(4) or "no manual pages")
            after = part.group(1) if part else standard.group(1) if standard else None
            return {
                "pass": current, "name": match.group(2), "trade": match.group(3),
                "package": match.group(5), "kind": "manual" if part else "standard" if standard else "review",
                "spans": spans.removesuffix(" verified").removesuffix(" skipped"),
                "after": None if after == "none" else after,
            }
    raise ReportError(f"{plan} carries no unit {unit}; a unit the read plan does not carry is not restored")


def _names_of(run_folder: Path, unit: str) -> tuple[list[str], list[str]]:
    lines: list[str] = []
    files: list[str] = []
    seen: dict[str, str] = {}
    folder = run_folder / "names"
    for path in sorted(folder.glob("*.txt")) if folder.is_dir() else []:
        for raw in path.read_text(encoding="utf-8").splitlines():
            fields = raw.split("\t")
            if len(fields) == 3 and fields[0].strip() == unit:
                seen[fields[1].strip()] = fields[2].strip()
                if path.name not in files:
                    files.append(path.name)
    lines = [f"{subject}\t{name}" for subject, name in seen.items()]
    return lines, files


def _trades_of(run_folder: Path, pass_id: str, unit: str) -> tuple[str | None, Path]:
    import pass_summary

    path = run_folder / "trades" / f"{pass_id}.txt"
    if not path.is_file():
        return None, path
    try:
        trades = pass_summary.read_trades(path).get(unit, [])
    except pass_summary.SummaryError:
        return None, path
    ordered = sorted(trades, key=lambda pair: (-pair[1], pair[0]))
    return (", ".join(f"{code} x{count}" for code, count in ordered) or "none"), path


def restore(run_folder: Path, window: str, unit: str) -> list[str]:
    import ledger as ledger_script
    import pass_summary

    if window != "3":
        raise ReportError(
            f"window {window!r}: a lost report is restored for a package review or a manual part, "
            f"in window 3 alone"
        )
    ledger = run_folder / "ledger.md"
    planned = _plan_unit(run_folder / "read-plan.md", unit)
    history = unit_history(ledger, window, unit)
    if history["latest"] is None:
        raise ReportError(
            f"unit {unit}'s latest dispatch line has no verified line after it, so no check passed "
            f"the read; that read is read again, never restored"
        )
    read, verified = history["latest"]
    if verified["result"] != "ok":
        raise ReportError(
            f"unit {unit}'s latest verified line, ledger line {verified['line']}, reads "
            f"{verified['result']}; a read that failed its check is read again, never restored"
        )
    reports = run_folder / REPORTS_FOLDER
    own = pass_summary.unit_report(reports, unit, read, history["dispatches"])
    why = problems_of_file(own, planned["kind"])
    if not why:
        return [f"unit_report: the report of read {read} at {own} is whole; nothing restored"]
    state = "missing" if why == ["missing"] else why[0]
    if state.startswith("report ") or state.startswith("owed "):
        state = f"whole and disagreeing with itself: {state}"

    fields = pass_summary._read_verified(verified["text"].split(), f"{ledger} line {verified['line']}")["fields"]
    names, name_files = _names_of(run_folder, unit)
    trades, trades_path = _trades_of(run_folder, verified["pass"], unit)
    name = restored_name(unit, read)
    # The unit's own notes of that read, the runner's copies of the reader's lines among them, less
    # the note this script appends, so a second run writes the same file.
    notes = [
        note["text"] for note in history["reads"].get(read, {}).get("notes", [])
        if note["kind"] in ("anomaly", "grain", "door", "deviation")
        and f"report written from the record to {REPORTS_FOLDER}/{name}" not in note["clause"]
    ]
    body = [
        f"restored: {unit}, read {read}, written by the run's report script from the record and the "
        f"run folder; the reader's report {own} is {state}",
        "no line below says a page was read or a search was run",
        f"unit kind: {UNIT_KIND_SAID[planned['kind']]}"
        + (f", read after {planned['after']}" if planned["after"] else ""),
        f"package: {planned['name']}, trade {planned['trade']}, package id {planned['package']}",
        f"manual pages the read plan gave it: {planned['spans']}",
        f"what the run's check found, its verified line at ledger line {verified['line']}: "
        f"entries under the unit's prefix {fields['created']}, items as the check carried them "
        f"{fields['items']}, rows updated {fields['updated']}, Questions raised {fields['questions']}, "
        f"replies {fields['replied']}, writes sent {fields['sent']}, landed {fields['landed']}, "
        f"conflicts {fields['conflicts']}",
    ]
    if names:
        body.append(f"rows under the unit's prefix, off the names written from the record ({', '.join(name_files)}):")
        body.extend(names)
    else:
        body.append("rows under the unit's prefix: not restored, no names on file")
    if trades is None:
        body.append(f"items by trade: not restored, no trades on file at {trades_path}")
    else:
        body.append(f"items by trade, off {trades_path}: {trades}")
    body.append(f"notes on the ledger for read {read}:" if notes else f"notes on the ledger for read {read}: none")
    body.extend(notes)
    body.append(
        "not known: the pages opened, the searches run, the rows updated by subject, the Questions by "
        "id, the headings and the rows' order; the record does not show which read wrote an "
        "update, ran a search or opened a page"
    )
    path = reports / name
    _publish(path, "".join(f"{line}\n" for line in body).encode("utf-8"))

    note = (
        f"note 3 {planned['pass']} {unit} deviation {planned['name']} report written from the record "
        f"to {REPORTS_FOLDER}/{name}, read {read}"
    )
    # As the ledger holds it, so a second restore finds the note the first one appended.
    note = ledger_script.one_line(note).strip()
    out = [f"unit_report: wrote {path}"]
    if note in {item["text"] for item in history["reads"].get(read, {}).get("notes", [])}:
        out.append(f"unit_report: the ledger already carries: {note}")
        return out
    try:
        out.extend(ledger_script.append_lines(ledger, [note]))
    except ledger_script.LedgerError as e:
        raise ReportError(str(e)) from None
    return out


# --------------------------------------------------------------------------- #
# Entry point
# --------------------------------------------------------------------------- #

# --------------------------------------------------------------------------- #
# codes
# --------------------------------------------------------------------------- #

# The sheet types whose page is a list of codes: one of them with no code on the record citing it
# is short whatever its report says. (plan_inventory.VOCABULARY_SHEET_TYPES holds notes and
# cover-index sheets too, which may print no list.)
CODE_SHEET_TYPES = ("schedule", "legend")
# The subjects citing a sheet that are no code: its rows, its Questions, its own reading and the
# declaration of a kind.
NOT_CODE_KINDS = ("scopeItem", "question", "sheet", "definitionKind")


def _json_file(path: Path) -> dict:
    import json

    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as e:
        raise ReportError(f"{path} cannot be read ({e.__class__.__name__})") from None
    if not isinstance(data, dict):
        raise ReportError(f"{path} is not the file the plan script writes")
    return data


def sheet_type_of(run_folder: Path, unit: str) -> tuple[str | None, str | None]:
    """
    The sheet type of a window 1 unit's sheet off `plan/window-1.json` and `inventory.json`, and
    why its codes are not held where they are not: a repeated lines unit, or a sheet with no type.
    """
    plan = _json_file(run_folder / "plan" / "window-1.json")
    for entry in plan.get("repeatedSets") or []:
        if isinstance(entry, dict) and entry.get("unitId") == unit:
            return None, "a repeated lines unit"
    key = next((u.get("unitKey") for u in plan.get("units") or [] if isinstance(u, dict) and u.get("id") == unit), None)
    if key is None:
        raise ReportError(f"unit {unit} is not a unit of the window 1 plan")
    inventory = _json_file(run_folder / "inventory.json")
    row = next((s for s in inventory.get("sheets") or [] if isinstance(s, dict) and s.get("unitKey") == key), None)
    if row is None:
        raise ReportError(f"the sheet of unit {unit} is not in the inventory")
    sheet_type = row.get("sheetType")
    if not isinstance(sheet_type, str) or not sheet_type.strip():
        return None, "the sheet has no type"
    return sheet_type.strip(), None


def codes_mismatches(run_folder: Path, unit: str, text: str) -> tuple[list[str], str | None]:
    """
    What the record holds short of a window 1 unit's `code lists:` line: one
    `codes <kind> printed <n> on the record <c>` per kind whose codes citing the sheet come to fewer
    than it printed less those already recorded on another sheet and those not readable, and
    `codes none on the record on a <type> sheet` for a schedule or legend no code cites where no
    entry accounts for that: none reads `none printed`, and none is a kind whose printed codes are
    all already recorded or not readable. Also why the codes are not held, where they are not.
    """
    lines = [raw.strip() for raw in text.splitlines()]
    at = next((i for i, line in enumerate(lines) if line == "subjects:" or line.startswith("subjects: ")), None)
    if at is None:
        raise ReportError("stdin carries no `subjects:` line")
    found = sections("\n".join(lines[:at]), ("code lists",))
    if "code lists" not in found:
        raise ReportError("stdin carries no `code lists:` line before its `subjects:` line")
    entries, unshaped, repeated = code_list_entries(found["code lists"])
    if unshaped:
        raise ReportError(f"the `code lists:` entry {unshaped[0]!r} is in none of the report's shapes")
    if repeated:
        raise ReportError(f"the `code lists:` line names {repeated[0]} on more than one entry, and a kind takes one")
    sheet_type, not_held = sheet_type_of(run_folder, unit)
    if not_held:
        return [], not_held
    if lines[at][len("subjects:"):].strip().lower() == "truncated":
        return [], "the sheet's row of subjects was cut"
    on_record: dict[str, set[str]] = {}
    for line in lines[at + 1:]:
        for subject in re.split(r"[\s,]+", _LIST_MARKER_RE.sub("", line)):
            subject = subject.strip('"')
            kind, colon, code = subject.partition(":")
            if not colon or not code or kind in NOT_CODE_KINDS:
                continue
            on_record.setdefault(kind, set()).add(subject)
    mismatches = []
    accounted = False
    for entry in entries:
        if "kind" not in entry:
            accounted = True
            continue
        owed = entry["printed"] - entry["already"] - entry["unreadable"]
        if owed <= 0:
            accounted = True
        count = len(on_record.get(entry["kind"], ()))
        if count < owed:
            mismatches.append(f"codes {entry['kind']} printed {entry['printed']} on the record {count}")
    if sheet_type in CODE_SHEET_TYPES and not on_record and not accounted:
        mismatches.append(f"codes none on the record on a {sheet_type} sheet")
    return mismatches, None


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Hold a reader's report to its shape, hand on owed work, restore a lost report.")
    modes = parser.add_subparsers(dest="mode", required=True)
    one = modes.add_parser("check", help="hold one report to its kind's shape")
    one.add_argument("--kind", required=True, choices=tuple(LABELS))
    one.add_argument("--report", required=True, help="the report file, or - for the returned message on stdin")
    one.add_argument("--owed", help="the owed file this read was handed, or none on a first read")
    one.add_argument("--spans", help="a manual part's `Reads:` line as its dispatch named it")
    owe = modes.add_parser("owed", help="write the owed file for a unit's next read")
    owe.add_argument("run_folder", type=Path)
    owe.add_argument("window")
    owe.add_argument("unit")
    owe.add_argument("--read", type=int, required=True)
    back = modes.add_parser("restore", help="restore a lost report of a passed window 3 unit")
    back.add_argument("run_folder", type=Path)
    back.add_argument("window")
    back.add_argument("unit")
    sets = modes.add_parser("trades", help="write one unit's set of trades lines, on stdin, as the pass's file's only lines for it")
    sets.add_argument("run_folder", type=Path)
    sets.add_argument("pass_id")
    sets.add_argument("unit")
    union = modes.add_parser("touched", help="print a unit's touched lines, over every read of it that carries a verified line")
    union.add_argument("run_folder", type=Path)
    union.add_argument("window")
    union.add_argument("unit")
    union.add_argument("--kind", required=True, choices=tuple(LABELS))
    kept = modes.add_parser("confirmed", help="keep the lists a check confirmed off a returned message")
    kept.add_argument("run_folder", type=Path)
    kept.add_argument("window")
    kept.add_argument("unit")
    kept.add_argument("--read", type=int, required=True)
    held = modes.add_parser("codes", help="hold a window 1 unit's code lists to the codes on the record citing its sheet")
    held.add_argument("run_folder", type=Path)
    held.add_argument("unit")
    args = parser.parse_args(argv)

    try:
        if args.mode == "check":
            owed = None
            if args.owed is not None and args.owed != "none":
                owed = read_owed_file(Path(args.owed))
            if args.report == "-":
                data = sys.stdin.buffer.read()
            else:
                path = Path(args.report)
                if not path.is_file():
                    print("missing")
                    return 2
                try:
                    data = path.read_bytes()
                except OSError as e:
                    print(f"not whole: cannot be read ({e})")
                    return 2
            text = report_text(data)
            if text is None:
                print(NOT_UTF8)
                return 2
            spans = dispatched_spans(args.spans) if args.spans is not None else None
            broken, mismatches = problems(text, args.kind, owed, owed_given=args.owed is not None, spans=spans)
            if broken:
                print(broken[0])
                return 2
            if mismatches:
                for line in mismatches:
                    print(line)
                return 3
            print("report whole")
            return 0
        if args.mode == "owed":
            path = write_owed(args.run_folder, args.window, args.unit, args.read, sys.stdin.read())
            print(f"unit_report: wrote {path}")
            return 0
        if args.mode == "touched":
            ids, unknown = touched_of_reads(args.run_folder, args.window, args.unit, args.kind)
            for code in ids:
                print(f"{args.unit} touched {code}")
            for read in unknown:
                print(
                    f"unit_report: read {read} of unit {args.unit} carries a verified line, and neither "
                    f"a whole report of it nor its confirmed file is on file; the trades it touched are not known",
                    file=sys.stderr,
                )
            for line in note_unknown_touched(args.run_folder, args.window, args.unit, unknown):
                print(line, file=sys.stderr)
            return 0
        if args.mode == "codes":
            stdin = report_text(sys.stdin.buffer.read())
            if stdin is None:
                raise ReportError("the lines on stdin are not UTF-8 text")
            mismatches, not_held = codes_mismatches(args.run_folder, args.unit, stdin)
            if not_held:
                print(f"codes not held: {not_held}")
                return 0
            if mismatches:
                for line in mismatches:
                    print(line)
                return 3
            print("codes whole")
            return 0
        if args.mode in ("trades", "confirmed"):
            stdin = report_text(sys.stdin.buffer.read())
            if stdin is None:
                raise ReportError("the lines on stdin are not UTF-8 text; nothing was written")
            if args.mode == "trades":
                for line in write_trades(args.run_folder, args.pass_id, args.unit, stdin):
                    print(line)
                return 0
            path = write_confirmed(args.run_folder, args.window, args.unit, args.read, stdin)
            print(f"unit_report: wrote {path}")
            return 0
        for line in restore(args.run_folder, args.window, args.unit):
            print(line)
        return 0
    except ReportError as e:
        print(f"unit_report: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
