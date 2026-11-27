"""
close_report.py: write a scope run's closing report off its run folder.

A scope run goes from its read plan to its end on its own, so everything the estimator hears about
it comes at the end, in one file, `<run folder>/closing-report.md` (Audience: user), with a short
version the lead says in the session. The lead never holds a whole run's notes: this script decides
which notes appear, in what order and with what dedupe, and every id it would print becomes a name
by copy, never by a model's retelling.

Two modes:

    sh run.sh close_report.py ids '<run folder>' --project <projectId>

        Reads the ledger and the run folder and writes `<run folder>/reports/close-ids.txt`
        (Audience: agent), the calls one fresh copy agent makes, one per line:

            <file name> <verb> <arguments as one JSON object>

        Each response goes byte for byte to `<run folder>/plan/close/<file name>`. The calls: the
        project's Question counts (`list_questions` with `limit: 0`), a fresh package list, the
        general requirements package where `plan/packages.json` names one, the index's
        `codeNoLocation` and `codeOnlyOnReplacedPages` rows where the last `phase: index built`
        line counts any, the Questions a note names in batches of 20 (`questionIds`), and one
        `search(subject:, predicate: "name")` per row subject a note names that the `names/` files
        cannot name. At most MAX_IDS ids are looked up in all, and a Question is never looked up
        one by one. It prints one line counting the calls.

    sh run.sh close_report.py write '<run folder>' [--delivery-plan '<plan file>'] [--stopped '<why>']

        Writes `<run folder>/closing-report.md` whole and prints the short version, under
        SHORT_CAP characters, ending with the file's path. `--stopped` heads the file as a run
        that stopped early and why; the run is not closed. A report written again keeps the time
        a finished report first named. It never refuses for want of an input: each section says
        what is not available and why, a file in the wrong shape included, and a section that
        fails says which and why while every other section is written.

What the run could not do is one collection, `gaps`, and the report's `What I could not read` and
the short version's `Could not read` are both printed from it, so the two never disagree. It holds
every skipped unit with the reason off its last read, a schedule sheet skipped in window 1 with the
sentence that later sheets may be less complete for it, every `unread` note of every window
whatever its clause, every scanned sheet or part not read from its picture, every kind of index
leftover, the sheets left out at the start or by the delivery's plan, every manual section no
review could read, every entry of a verified review's or manual part's `sections not checked:` and
`families not checked:` lines, every standard line whose condition a review found after the line
was written or left, every word a review could not search, every window 3 unit whose pages read are
not known (its report written from the record, or no report of its last read on file), every read
whose trades are not known, every deviation note of a window boundary, and every other deviation
note with no `, read <k>` ending except the runner's three that report no failure (a check split
over several calls, a read again granted, a go on given) and a boundary's names taken off the record
so its scan could run, which the detail part names. Each entry is told apart by what it is about,
its unit, read, file, section and pages, never by the sentence it prints, except that a manual
section's sentence, which names its pages, is printed once however many entries read it.

A note is classified only by the whole shape its producer writes, the patterns beside each
producer's name below the imports, never by a few words inside it. A note of a kind the report
reads that matches no shape is printed under To look at in its own words.

Where each figure and sentence comes from (each unit counted once, off its latest `verified` line):

    | In the report                       | Its durable source                                              |
    |-------------------------------------|-----------------------------------------------------------------|
    | set label                           | `run.json` `label`                                              |
    | started                             | `phase: reading started <UTC>`; an older ledger's plan line has |
    |                                     | no time, so how long it took is said as not known               |
    | finished                            | the time the first finished report was written, kept after      |
    | sheets read of the total            | windows 1 and 2 units verified ok (not a repeated lines unit),  |
    |                                     | over `inventory.json` `sheets`                                  |
    | manual pages read                   | the `spans read:` lines of the reader-written report of a       |
    |                                     | window 3 unit's latest read verified ok, where the report check |
    |                                     | holds it whole, each span held to the unit's planned spans off  |
    |                                     | the window 3 `read-plan.md`, so a section the reader left       |
    |                                     | unread adds no page; a restored report, or none on file, is     |
    |                                     | said as pages not known                                         |
    | planned, finished, not started      | `plan/window-1.json`, `plan/window-2.json` and the window 3     |
    |                                     | `read-plan.md`, each unit reconciled against the ledger         |
    | every sheet and page read and       | said only where every window is planned, every planned unit     |
    | checked                             | verified ok, `phase: window 3 complete` is on the ledger and    |
    |                                     | the collection of what could not be done is empty               |
    | items added, by trade               | `trades/<pass>.txt` `trade` lines of each unit, the pass its    |
    |                                     | latest `verified` line names; never a `pass:` line's `created`  |
    | items updated, Questions, replies   | each unit's latest `verified` line: `updated` (windows 1 to 3), |
    |                                     | `questions`, `replied` (windows 1 to 3 and r)                   |
    | items combined                      | window 3 `anomaly` notes in SAME_WORK_RE's shape, `combined`    |
    | skipped units and their reason      | the `unread ... not read again` note, and the notes of the      |
    |                                     | unit's latest read ending `, read <k>`, by the REASONS check    |
    |                                     | named right after the sheet, otherwise in the note's own words  |
    | scanned parts not read              | `anomaly` notes carrying `not read from the picture:`           |
    |                                     | at its place, the whole note in PICTURE_RE's shape              |
    | other unread pages, files, sections | `unread` notes of any clause                                    |
    | left out of the read plan           | `plan/window-1.json` `excluded` keys and `exclude` reasons      |
    | left by the delivery's plan         | `plan/window-1.json` `leftByPlan` keys                          |
    | manual sections and pages not read  | window 3 `read-plan.md` `## Manual sections not read`, window 3 |
    |                                     | `anomaly` notes in SECTION_NOT_READ_RE's shape, window 3        |
    |                                     | `unread section` notes; a manual part's section off the report  |
    |                                     | of its latest read verified ok where that report is on file and |
    |                                     | whole, and otherwise off the part's latest anomaly for it, with |
    |                                     | the plan's pages; one sentence for one section printed once     |
    | words not searched                  | window 3 `anomaly` notes in UNSEARCHED_RE's shape               |
    | a review's bounds reached           | window 3 `anomaly` notes in BOUND_REACHED_RE's shape            |
    | standard lines not written,         | a skipped window 3 unit, by its read plan line: a standard      |
    | headings and order not settled      | lines unit, or a review                                         |
    | standard lines found later, in the  | window 3 `anomaly` notes in FOUND_LATER_RE's shape              |
    | collection                          |                                                                 |
    | sections and families a review or a | the `sections not checked:` and `families not checked:` lines   |
    | manual part did not check, in the   | of the reader-written report of each window 3 review's and      |
    | collection                          | manual part's latest read verified ok, where the report check   |
    |                                     | holds it whole, each entry by the shapes beside the reviewer's  |
    |                                     | and the manual reader's names, an entry in none in its own words|
    |                                     | and two reasons for one section both; a review's `not read` or  |
    |                                     | `not known` entry for a section of its package already named as |
    |                                     | a part's gap, a part's anomaly or a plan omission is that gap,  |
    |                                     | named once, there; the owner's work once a package's section    |
    | packages that took an item after    | window 3 `anomaly` notes in OTHER_PACKAGE_RE's shape, the item's|
    | their own review                    | trade through `plan/packages.json`, the note's own place on the |
    |                                     | ledger after that package's review's latest `verified` line     |
    |                                     | reading ok, however the writing review ended                    |
    | pages not known, trades not known   | `deviation` notes in RESTORED_RE's shape, the report check over |
    |                                     | each verified window 3 unit's report, and `anomaly` notes in    |
    |                                     | TRADES_NOT_KNOWN_RE's shape, by unit and read                   |
    | what the index left uncited         | every kind on the last `phase: index built` line                |
    | Questions by trade                  | `plan/close/questions.json` (`list_questions`, `status: "all"`, |
    |                                     | `limit: 0`): every Question on the project, open and closed     |
    | trade names                         | `plan/close/packages.json`, else `plan/packages.json`           |
    | to look at                          | `anomaly` notes that landed on no Question or reply, `grain`,   |
    |                                     | `door` and `overlap` notes, `created subjects` deviations,      |
    |                                     | `not written:` and `not needed:` notes, each `not written:`     |
    |                                     | entry while it is outstanding (below), and every note of these  |
    |                                     | kinds in no shape here, in its own words                        |
    | names for ids                       | `names/*.txt`, `plan/close/name-*.json`,                        |
    |                                     | `plan/close/questions-named-*.json`                             |
    | package changes                     | `reports/fold.md` through `fold_report.read_report`, the        |
    |                                     | `amended:` lines as made and each `amending:` line no `amended:`|
    |                                     | line of its text follows as started and not confirmed, the      |
    |                                     | `unplaced:` lines, `plan/close/general-requirements.json`,      |
    |                                     | `onNoPackage` of `plan/close/packages.json`                     |
    | the recheck                         | `recheck.report_lines` over `--delivery-plan`, where the ledger |
    |                                     | carries `phase: recheck complete`                               |
    | still open                          | `plan/close/leftover-*.json`                                    |
    | what went wrong                     | `short:` lines, `repaired:` lines, blocked and interrupted      |
    |                                     | reads, `verified` lines reading mismatch                        |
    | packages an addendum did not review | window 3 `read-plan.md` `## Nothing read for`                   |
    | newly defined                       | `kinds` notes and boundary `kinds declared` notes               |

A `not written:` entry is outstanding until a later read of its unit verified ok says it was written
or not needed: the entries kept are those of the unit's latest read that verified ok, which noted
again each one it still did not write, and of every read after it; a unit with no read verified ok,
a skipped unit among them, keeps every entry any read of it named.

Exit codes:
  0  written (ids: the calls file; write: the report file), one or more lines on stdout.
  1  write mode: the report file could not be written; one line on stdout says why, and the lead
     says no short version.
  2  argparse rejected the invocation.

Grounding role: reads files and copies byte values. It reads no record; the copy agent does.
"""

from __future__ import annotations

import argparse
import datetime
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import fold_report  # noqa: E402
import ledger as ledger_script  # noqa: E402
import pass_summary  # noqa: E402
import plan_inventory  # noqa: E402
import unit_report  # noqa: E402

REPORT_NAME = "closing-report.md"
CALLS_NAME = "close-ids.txt"
CLOSE_FOLDER = ("plan", "close")
MAX_IDS = 50
QUESTIONS_PER_CALL = 20
SHORT_CAP = 3000
SHORT_NAMED = 5
GENERAL_REQUIREMENTS_CODE = "01 11 13"
QUESTIONS_TITLE = "Every Question on the project, open and closed, by trade"
FINISHED_MARK_RE = re.compile(r"^<!-- finished (\d{4}-\d\d-\d\dT\d\d:\d\d:\d\dZ) -->$")
STARTED_RE = re.compile(r"^phase: reading started (\d{4}-\d\d-\d\dT\d\d:\d\d:\d\dZ)$")

_UUID = r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}"
QUESTION_ID_RE = re.compile(rf"question:proj-{_UUID}:{_UUID}")
REPLY_ID_RE = re.compile(rf"clm-{_UUID}")
SUBJECT_RE = re.compile(r"scopeItem:[^\s,;|()\"']+")
# Where an anomaly landed, as its last words: on a Question or a reply it is on a trade's page and is
# counted, never printed.
LANDED_RE = re.compile(rf", (?:Question {QUESTION_ID_RE.pattern}|reply (?:{QUESTION_ID_RE.pattern}|{REPLY_ID_RE.pattern}))$")
ENDING_RE = re.compile(r", (?:sheet reading|run only)$")


def _shape_of(producer) -> re.Pattern:
    """A producer's clause, whole, as a pattern: its unit as group 2 and its read as group 1."""
    text = re.escape(producer("\x01", "\x02"))
    return re.compile("^" + text.replace("\x02", "([1-9][0-9]*)", 1).replace("\x01", r"(\S+)", 1) + "$")


# Each note shape this script classifies, whole, as its producer writes it. A note is classified only
# where it matches a shape whole; a note of a kind the report reads that matches none is printed
# under To look at in its own words. The producer of each is named beside it.
#   unit_report.py `touched`, its note that a read's trades are not known:
TRADES_NOT_KNOWN_RE = _shape_of(unit_report.unknown_touched_note)
#   scope-reader and scope-vocabulary-reader, their `pages unread:` words copied onto `anomalies:`:
PICTURE_RE = re.compile(r"^(\S+) p([1-9][0-9]*) not read from the picture: (.+), run only$")
#   scope-reviewer and scope-manual-reader, a section on the dispatch they did not read:
SECTION_NOT_READ_RE = re.compile(r"^section (\S+) not read: (.+), run only$")
#   scope-reviewer, a search the rate limit refused on its fifth send:
UNSEARCHED_RE = re.compile(r"^unsearched (.+), refused by the rate limit five times, run only$")
#   scope-reviewer, two rows carrying the same work, one retired (`combined`) or neither:
SAME_WORK_RE = re.compile(
    r"^\S+ p[1-9][0-9]* same work: (.+ and .+, .+, (?:combined|left for the estimator(?:\W.*)?)), run only$"
)
#   the runner, each entry of a review's or a manual part's `not written:` line, copied whole:
NOT_WRITTEN_RE = re.compile(r"^not written: ([^|]+?) \| ([^|]+?) \| ([^|]+?) \| ([^|]+)$")
#   the runner, an `owed:` answer saying a failed claim of an earlier read is not needed, copied whole:
#   (a `- ` or `* ` the reader's report listed the answer under comes along in the copy)
NOT_NEEDED_RE = re.compile(r"^not needed: (?:[-*] )?check read [1-9][0-9]* failed: (.+), read [1-9][0-9]* \| not needed, (.+)$")
#   names_scan.py, the two overlap shapes it writes:
OVERLAP_PAIR_RE = re.compile(r"^(.+) in (\S+) and (\S+)$")
OVERLAP_SCAN_RE = re.compile(r"^scan read [0-9]+ new item names, every unit of [0-9]+ in [0-9]+ passes$")
#   the boundary runner, its two kinds notes:
KINDS_NOT_WRITTEN_RE = re.compile(r"^named not written \S+$")
KINDS_DECLARED_RE = re.compile(r"^declared \S+ [0-9]+$")
#   the boundary runner, names taken off the record so the scan could run, and a scan that could not:
NAMES_FETCHED_RE = re.compile(r"^names of (\S+) written from the record at the boundary$")
SCAN_NOT_RUN_RE = re.compile(r"^overlap scan not run, names missing for ([0-9]+) units$")
#   plan_inventory.py, a manual section no pass can take:
UNREAD_SECTION_RE = re.compile(r"^section (\S+) pages ([1-9][0-9]*) to ([1-9][0-9]*) left, (.+)$")
#   the runner, a file's repeated lines not read, and blocks of them not listed:
UNREAD_FILE_RE = re.compile(r"^file (\S+) repeated lines not read, (.+)$")
UNREAD_BLOCKS_RE = re.compile(r"^file (\S+) ([0-9]+) blocks ([0-9]+) lines not listed, (.+)$")
#   unit_report.py `restore`, a review's or a manual part's report written from the record:
RESTORED_RE = re.compile(
    rf"^.+ report written from the record to {unit_report.REPORTS_FOLDER}/(\S+)\.read-([1-9][0-9]*)\.restored\.md, "
    r"read ([1-9][0-9]*)$"
)
#   the runner, each entry of a review's `bounds reached:` line, copied whole:
BOUND_REACHED_RE = re.compile(r"^bound reached: (.+?) ([0-9]+): (.+)$")
#   the runner, each entry of a review's `standard lines found later:` line, copied whole:
FOUND_LATER_RE = re.compile(r"^standard line found later: ([^|]+?) \| ([^|]+?) \| (.+)$")
#   the runner, each entry of a review's `rows on other packages:` line, copied whole:
OTHER_PACKAGE_RE = re.compile(r"^row on another package: (scopeItem:\S+) \| ([0-9]{2}(?: [0-9]{2}){2}(?:\.[0-9]+)?)$")
#   scope-reviewer, each entry of its `sections not checked:` line, by the reasons its report shape
#   names: a section the notes script named not read or not known, with the reason it printed; its
#   searches spent; the notes not read; the owner's work; no section on the package; no manual:
REVIEW_UNREAD_RE = re.compile(r"^(\S+) (not read|not known)[,:]? (.+)$")
REVIEW_SPENT_RE = re.compile(r"^(\S+) searches spent$")
REVIEW_NOTES_UNREAD_RE = re.compile(r"^(\S+) notes not read$")
OWNERS_WORK_RE = re.compile(r"^(\S+) the owner['’]s work$")
NO_SECTIONS_RE = re.compile(r"^no manual sections on this package$")
NO_MANUAL_RE = re.compile(r"^(?:the )?manual was not read in$")
#   scope-reviewer, its `families not checked:` entry for a referral its two pages did not settle:
FAMILY_REFERRAL_RE = re.compile(r"^(.+?),? see Section (\S+), two pages read$")
#   scope-manual-reader, each entry of its `sections not checked:` line, by the reasons its report
#   shape names (the owner's work is OWNERS_WORK_RE, above):
PART_UNREAD_RE = re.compile(r"^(\S+) (manual removed|manual changed|not on the package)$")
PART_UNREAD_SAID = {
    "manual removed": "its manual file is no longer on the project",
    "manual changed": "its file or pages on the record changed after the manual reading was planned",
    "not on the package": "the package no longer lists it",
}
#   the runner, a read verified off the reader's returned message:
CHECKED_OFF_RE = re.compile(r"^.+ report file .+, checked off the returned report, read [1-9][0-9]*$")
#   the runner, a review that opened no page and a sheet unit that cited no sheet:
NO_SHEET_CITED_RE = re.compile(r"^verified with no sheet, no sheet cited$")
SPAN_RE = re.compile(r"^(\S+) p([1-9][0-9]*)-p([1-9][0-9]*) of \S+(?: \(section p[1-9][0-9]*-p[1-9][0-9]*\))?$")
REVIEW_LINE_RE = re.compile(
    r"^[1-9][0-9]*\. (\S+): (.+?), trade (.+?)(?:, reads (.+?))?, package (\S+)( verified| skipped)?$"
)
PART_LINE_RE = re.compile(
    r"^[1-9][0-9]*\. (\S+): (.+?), trade (.+?), package (\S+), manual part after (\S+), reads (.+?)( verified| skipped)?$"
)
STANDARD_LINE_RE = re.compile(
    r"^[1-9][0-9]*\. (\S+): (.+?), trade (.+?), package (\S+), standard lines after (\S+)( verified| skipped)?$"
)
#   plan_inventory.py, a section or a run of its pages no unit of the window 3 plan reads, under
#   the read plan's `## Manual sections not read`, with its reason:
NOT_READ_LINE_RE = re.compile(r"^[1-9][0-9]*\. (\S+)(?: pages ([1-9][0-9]*) to ([1-9][0-9]*))? on (\S+), package \S+: (.+)$")

# What a failed check means, in plain words, longest name first so `created subjects` is never read
# as `created`. A read of the recheck is a sheet's rows; a read of window 3 a package or its manual.
REASONS = (
    ("created subjects", "it named items it created that were not under its own numbering on the record"),
    ("questions replied", "a reply it said it wrote is not on the Question"),
    ("questions raised", "a Question it said it raised is not on the project"),
    ("questions linked", "a Question it said it put on an item is not on that item"),
    ("questions alone", "a Question it raised is on no item, and it gave no reason"),
    ("recheck report refused", "its report left out an item or named one twice"),
    ("reader stopped answering", "the reading stopped answering partway"),
    ("page citations", "a page it said it cited is not on the item"),
    ("manual updates", "a manual page it said it cited is not on the item"),
    ("field updates", "a change it said it made to an item is not on the record"),
    ("rows ordered", "the order of the items under a heading did not save as it said"),
    ("no report", "it ended without a report I could check"),
    ("headings", "a heading it said it gave an item is not on that item"),
    ("created", "the count of items it said it created did not match the record"),
    ("updated", "an item it said it updated does not show the update on the record"),
    ("trades", "an item it created carries no trade"),
    ("spans", "it did not read exactly the manual pages it was given"),
    ("report", "its report's counts did not match its own lists"),
    ("owed", "it did not answer what the read before it left unwritten"),
)
REASON_FALLBACK = "the check of what it wrote did not pass, and its notes do not say which part"
_READ_END_RE = re.compile(r", read ([1-9][0-9]*)$")
# The runner's deviation notes with no read ending that report no failure, each whole with the sheet
# or package it names before it: the detail part names them, and the collection of what could not
# be done does not.
BOOKKEEPING = (
    (re.compile(r"(?:^| )verify split over ([0-9]+) calls$"), "its check took {0} calls, since it named more than twenty sheets"),
    (re.compile(r"(?:^| )verified with no sheet, no page opened$"), "its review opened no drawing page, so its check named no sheet"),
    (re.compile(r"(?:^| )read again granted for read ([0-9]+)$"), "you asked for it to be read again, and read {0} was its read"),
    (re.compile(rf"(?:^| ){re.escape(pass_summary.GO_ON_NOTE)}$"), "you said to go on after three of its reads were cut off or could not be made"),
)

# What the index of every page each item appears on leaves uncited, kind by kind, in plain words.
INDEX_KINDS = (
    ("unmatchedTag", "{n} tag{s} I could not match to any item: marks nobody placed on the sheet they sit on, which this run did not go back for.", "tag{s} not matched"),
    ("codeNoLocation", "{n} code{s} found on no page, named under Still open.", "code{s} found on no page"),
    ("codeOnlyOnReplacedPages", "{n} code{s} printed only on pages a later drawing issue replaced, named under Still open.", "code{s} on replaced pages only"),
    ("codeTooShort", "{n} code{s} of two characters or fewer, left uncited, since a match that short could be anything.", "short code{s} left uncited"),
    ("codeIsAWord", "{n} code{s} printed as ordinary words, left uncited.", "code{s} printed as words"),
    ("fragmentUnresolvable", "{n} mark{s} printed only in part, which could not be matched to an item.", "part mark{s} not matched"),
    ("pageNotASheet", "{n} match{es} on pages that are not drawing sheets, left uncited.", "match{es} off the sheets"),
    ("hitNotDrawable", "{n} match{es} that could not be placed on their sheet, left uncited.", "match{es} not placed"),
    ("overRunCap", "{n} match{es} past the most one index run cites, left uncited.", "match{es} past the index's limit"),
)
INDEX_OTHER = ("{n} match{es} the index left uncited for a reason it names otherwise.", "match{es} left uncited")

# The fold's acts, as the closing report says each label.
FOLD_SAID = {
    "folded": "Folded", "split": "Split", "moved": "Moved", "supplier": "Supplier with its installer",
    "sealant kept": "Sealant package kept", "default": "Default used", "deleted": "Deleted as the owner's work",
    "owner's work still covered": "Owner's work a kept package still covers", "kept": "Kept",
    "changed": "Changed while the fold was stopped", "re-homed": "Item moved to another trade",
    "question": "Question raised", "fold touched": "Package touched",
}
WINDOW_SAID = {
    "1": "The schedules, legends and notes", "2": "Every sheet once", "3": "The package reviews and their manual pages",
}


def _text(path: Path) -> str | None:
    try:
        return path.read_text(encoding="utf-8") if path.is_file() else None
    except (OSError, UnicodeDecodeError):
        return None


def _json(path: Path):
    text = _text(path)
    if text is None:
        return None
    try:
        return json.loads(text)
    except (json.JSONDecodeError, RecursionError):
        return None


def _plural(n: int, one: str, many: str | None = None) -> str:
    return f"{n} {one if n == 1 else (many or one + 's')}"


def _counted(template: str, n: int) -> str:
    return template.format(n=n, s="" if n == 1 else "s", es="" if n == 1 else "es")


def _cap(text: str) -> str:
    return text[:1].upper() + text[1:]


# --------------------------------------------------------------------------- #
# Reading the run folder
# --------------------------------------------------------------------------- #

def read_ledger(folder: Path) -> dict:
    """Every whole line of the ledger, sorted into what the report reads. A missing ledger is empty."""
    data = b""
    try:
        path = folder / pass_summary.LEDGER_NAME
        data = path.read_bytes() if path.is_file() else b""
    except OSError:
        pass
    text = data[: data.rfind(b"\n") + 1].decode("utf-8", "replace")
    lines = ledger_script.lines_of(text)
    led: dict = {
        "present": bool(data), "lines": lines, "phases": [], "repaired": [], "short": [],
        "amended": [], "unplaced": [], "notes": [], "dispatch": {}, "latest": {}, "results": {},
        "sheets_of": {}, "purpose_of": {}, "verified_lines": [],
    }
    for position, raw in enumerate(lines):
        line = raw.strip()
        parts = line.split()
        if not parts:
            continue
        key = parts[0]
        if key == "phase:":
            led["phases"].append(line)
        elif key == ledger_script.REPAIRED_KEYWORD:
            led["repaired"].append(line)
        elif key in ("short:", "unplaced:"):
            led[key[:-1]].append(line[len(key):].strip())
        elif key in ("amending:", "amended:"):
            led["amended"].append((key[:-1], line[len(key):].strip()))
        elif key in ("dispatch", "verified", "note") and len(parts) >= 4:
            window, unit = parts[1], parts[3]
            if key == "dispatch":
                led["dispatch"][(window, unit)] = led["dispatch"].get((window, unit), 0) + 1
                rest = parts[5:] if len(parts) > 4 and parts[4] == "sheets" else []
                if "purpose" in rest:
                    led["purpose_of"][(window, unit)] = " ".join(rest[rest.index("purpose") + 1:])
                    rest = rest[: rest.index("purpose")]
                sheets = [s.strip() for s in " ".join(rest).split(",") if s.strip() and s.strip() != "none"]
                if sheets:
                    led["sheets_of"][(window, unit)] = sheets
            elif key == "verified":
                fields = {}
                for field in pass_summary.VERIFIED_FIELDS:
                    if field in parts[4:-1]:
                        at = parts.index(field, 4)
                        fields[field] = int(parts[at + 1]) if parts[at + 1].isdigit() else 0
                result = parts[parts.index("result") + 1] if "result" in parts[:-1] else ""
                attempt = led["dispatch"].get((window, unit), 0)
                led["latest"][(window, unit)] = {"pass": parts[2], "fields": fields, "result": result, "attempt": attempt}
                led["verified_lines"].append((position, {"window": window, "unit": unit, "result": result}))
                led["results"].setdefault((window, unit), {})[attempt] = result
            elif len(parts) >= 5:
                note = {
                    "window": window, "pass": parts[2], "unit": unit, "kind": parts[4],
                    "clause": " ".join(parts[5:]), "attempt": led["dispatch"].get((window, unit), 0),
                    "at": position,
                }
                led["notes"].append(note)
    return led


def read_plan_3(folder: Path) -> dict:
    """The window 3 read plan's units, spans, omissions and packages left out, where it is window 3's."""
    out = {"present": False, "units": {}, "omissions": [], "left_out": [], "unnamed": False}
    text = _text(folder / "read-plan.md")
    if text is None:
        return out
    lines = text.splitlines()
    if next((line.strip() for line in lines if line.strip()), "") != "# Read plan: window 3":
        return out
    out["present"] = True
    section = None
    for raw in lines:
        line = raw.strip()
        if line.startswith("## "):
            section = line[3:]
            continue
        if section == "Manual sections not read":
            m = NOT_READ_LINE_RE.match(line)
            if m:
                out["omissions"].append({
                    "code": m.group(1), "unit": m.group(4), "reason": m.group(5),
                    "pages": (int(m.group(2)), int(m.group(3))) if m.group(2) else None,
                })
            continue
        if section == "Nothing read for":
            m = re.match(r"^[1-9][0-9]*\. (.+), trade (.+)$", line)
            if m:
                out["left_out"].append(m.group(1))
            if line.startswith("Nothing. A pass on an addendum reviews only"):
                out["unnamed"] = True
            continue
        part = PART_LINE_RE.match(line)
        if part:
            out["units"][part.group(1)] = {
                "kind": "manual", "package": part.group(2), "trade": part.group(3),
                "spans": _spans(part.group(6)),
            }
            continue
        standard = STANDARD_LINE_RE.match(line)
        if standard:
            out["units"][standard.group(1)] = {
                "kind": "standard", "package": standard.group(2), "trade": standard.group(3), "spans": [],
            }
            continue
        review = REVIEW_LINE_RE.match(line)
        if review:
            out["units"][review.group(1)] = {
                "kind": "review", "package": review.group(2), "trade": review.group(3),
                "spans": _spans(review.group(4) or ""),
            }
    return out


def _review_of(unit: str) -> str:
    """The review unit of a window 3 unit's package: a manual part or standard lines unit id less its ending."""
    return re.sub(r"(?:c-[1-9][0-9]*|s-1)$", "", unit)


def _spans(text: str) -> list[tuple[str, int, int]]:
    spans = []
    for piece in text.split("; "):
        m = SPAN_RE.match(piece.strip())
        if m:
            spans.append((m.group(1), int(m.group(2)), int(m.group(3))))
    return spans


def names_known(folder: Path) -> dict[str, str]:
    """Row subjects and Question ids with the words to say them in, off the names files and the copy."""
    names: dict[str, str] = {}
    for path in sorted((folder / "names").glob("*.txt")):
        for raw in (_text(path) or "").splitlines():
            fields = raw.split("\t")
            if len(fields) == 3 and fields[1].startswith("scopeItem:") and fields[2].strip():
                names[fields[1]] = fields[2].strip()
    close = folder.joinpath(*CLOSE_FOLDER)
    for path in sorted(close.glob("name-*.json")):
        for found in _walk(_json(path)):
            subject, value = found.get("subject"), found.get("value", found.get("name"))
            if isinstance(subject, str) and subject.startswith("scopeItem:") and isinstance(value, str) and value:
                names.setdefault(subject, value)
    for path in sorted(close.glob("questions-named-*.json")):
        for found in _walk(_json(path)):
            qid = found.get("questionId")
            if not isinstance(qid, str):
                continue
            rfi = found.get("rfiNumber")
            title = found.get("title")
            if isinstance(rfi, int):
                names[qid] = f"RFI #{rfi}"
            elif isinstance(title, str) and title.strip():
                names[qid] = f"the Question \u201c{title.strip()}\u201d"
    return names


def _walk(node):
    if isinstance(node, dict):
        yield node
        for value in node.values():
            yield from _walk(value)
    elif isinstance(node, list):
        for value in node:
            yield from _walk(value)


# --------------------------------------------------------------------------- #
# The facts
# --------------------------------------------------------------------------- #

class Facts:
    """Everything the report says, gathered once off the run folder. No input stops it."""

    def __init__(self, folder: Path, delivery_plan: Path | None):
        self.folder = folder
        self.delivery_plan = delivery_plan
        self.unavailable: list[str] = []
        self.unnamed: dict[str, int] = {}
        self.led = self._guard("the run's log", lambda: read_ledger(folder), None)
        if self.led is None:
            self.led = {
                "present": False, "lines": [], "phases": [], "repaired": [], "short": [], "amended": [],
                "unplaced": [], "notes": [], "dispatch": {}, "latest": {}, "results": {}, "sheets_of": {},
                "purpose_of": {},
            }
        self.run = self._shaped("run.json", _json(folder / "run.json"), dict, {})
        self.inventory = self._shaped("inventory.json", _json(folder / "inventory.json"), dict, None)
        self.packages = _json(folder / "plan" / "packages.json")
        self.window_1 = self._shaped("plan/window-1.json", _json(folder / "plan" / "window-1.json"), dict, None)
        self.window_2 = self._shaped("plan/window-2.json", _json(folder / "plan" / "window-2.json"), dict, None)
        empty3 = {"present": False, "units": {}, "omissions": [], "left_out": [], "unnamed": False}
        self.plan3 = self._guard("the window 3 read plan", lambda: read_plan_3(folder), empty3) or empty3
        self.names = self._guard("the names files", lambda: names_known(folder), {}) or {}
        self.ok: dict[str, set[str]] = {}
        self.skipped: dict[str, dict[str, str]] = {}
        for window in ("1", "2", "3", "r"):
            settled = self._guard(f"window {window}'s settled units",
                                  lambda w=window: plan_inventory.settled_of_lines(self.led["lines"], w), (set(), {}))
            self.ok[window], self.skipped[window] = settled or (set(), {})

    def _guard(self, what: str, read, fallback):
        try:
            return read()
        except Exception as e:  # an input that cannot be read is said, never a stop
            self.unavailable.append(f"{what} could not be read ({type(e).__name__}: {str(e)[:160]})")
            return fallback

    def _shaped(self, name: str, data, kind: type, fallback):
        """A file's JSON where it is in its shape; otherwise the fallback, and the file named as not available."""
        if data is None:
            return fallback
        if not isinstance(data, kind):
            self.unavailable.append(f"{name} is not in its shape (a {type(data).__name__} where an object belongs)")
            return fallback
        return data

    # ---- names of units ------------------------------------------------- #

    def unit_name(self, window: str, unit: str) -> str:
        if window == "3":
            planned = self.plan3["units"].get(unit)
            if planned:
                return {
                    "review": f"the {planned['package']} review",
                    "standard": f"the {planned['package']} standard lines",
                }.get(planned["kind"], f"the {planned['package']} manual pages")
            return "a package review"
        if plan_inventory._is_repeated_unit(unit):
            return "the notes one drawing file repeats"
        sheets = self.led["sheets_of"].get((window, unit))
        return ", ".join(sheets) if sheets else "a sheet"

    def reviewed_then_written(self) -> list[str]:
        """
        Each package that took an item from another package's review after its own review was
        verified, off the `row on another package` notes: the item's trade names the package,
        through the package list's `tradeCode` and `codes`, and the note's own place on the ledger
        says which came first, after the receiving package's review's latest `verified` line
        reading ok. How the writing review itself ended does not matter: a review skipped after it
        wrote the item leaves the item on the record all the same. A package whose review was never
        verified took nothing after it.
        """
        verified_at: dict[str, int] = {}
        review_of: dict[str, str] = {}
        for unit, planned in self.plan3["units"].items():
            if planned["kind"] == "review":
                review_of[unit] = planned["package"]
        for line_no, line in self.led.get("verified_lines", []):
            if line["window"] == "3" and line["unit"] in review_of and line["result"] == "ok":
                verified_at[line["unit"]] = line_no
        rows = self.packages.get("packages") if isinstance(self.packages, dict) else None
        by_trade: dict[str, str] = {}
        for row in rows or []:
            if isinstance(row, dict):
                for code in [row.get("tradeCode"), *(row.get("codes") or [])]:
                    if isinstance(code, str):
                        by_trade.setdefault(code, str(row.get("name") or row.get("id")))
        unit_of_package = {name: unit for unit, name in review_of.items()}
        out: list[str] = []
        for note in self.led["notes"]:
            other = OTHER_PACKAGE_RE.match(note["clause"]) if note["window"] == "3" and note["kind"] == "anomaly" else None
            if not other:
                continue
            package = by_trade.get(other.group(2))
            review = unit_of_package.get(package or "")
            written_at = note.get("at")
            if review and review != note["unit"] and review in verified_at and written_at is not None \
                    and verified_at[review] < written_at:
                said = f"{package}: an item from the {review_of.get(note['unit'], 'another')} review, written after its own review"
                if said not in out:
                    out.append(said)
        return out

    def package_of_unit(self, unit: str) -> str:
        """The package a window 3 unit id belongs to, by its review's unit, where the plan names it."""
        planned = self.plan3["units"].get(_review_of(unit))
        return planned["package"] if planned else "its package"

    def manual_name(self, unit: str) -> str:
        """A window 3 unit as a gap names it: a manual part by its package, sections and page range."""
        planned = self.plan3["units"].get(unit)
        if planned and planned["kind"] == "manual":
            spans = "; ".join(f"section {c}, pages {a} to {b}" for c, a, b in planned["spans"])
            return f"Manual pages for {planned['package']}" + (f" ({spans})" if spans else "")
        return self.unit_name("3", unit)

    def group_name(self, window: str, unit: str) -> str:
        if window == "3":
            planned = self.plan3["units"].get(unit)
            return planned["package"] if planned else "a package review"
        return self.unit_name(window, unit)

    def say(self, text: str, group: str) -> str:
        """A note's words with every id it names as a name, or a plain phrase where none is known."""
        def row(match: re.Match) -> str:
            subject = match.group(0).rstrip(".")
            if subject in self.names:
                return f"\u201c{self.names[subject]}\u201d"
            self.unnamed[group] = self.unnamed.get(group, 0) + 1
            return "an item"

        def question(match: re.Match) -> str:
            qid = match.group(1)
            if qid in self.names:
                return self.names[qid]
            self.unnamed[group] = self.unnamed.get(group, 0) + 1
            return "a Question"

        # A note names a Question as `Question <id>`; the name stands for both words.
        text = re.sub(rf"(?:\bQuestion )?({QUESTION_ID_RE.pattern})", question, text)
        text = REPLY_ID_RE.sub("a reply", text)
        return SUBJECT_RE.sub(row, text)

    def file_said(self, file_id: str) -> str:
        """One drawing file named by the first and last sheet numbers it prints, never by its id."""
        sheets = self.inventory.get("sheets") if isinstance(self.inventory, dict) else None
        numbers = [
            str(row.get("sheetNumber")) for row in sheets or []
            if isinstance(row, dict) and row.get("fileId") == file_id and row.get("sheetNumber")
        ] if isinstance(sheets, list) else []
        if not numbers:
            return "one drawing file"
        return f"the drawing file of {numbers[0]}" if len(numbers) == 1 else f"the drawing file of {numbers[0]} to {numbers[-1]}"

    # ---- figures -------------------------------------------------------- #

    def started(self) -> str | None:
        for line in self.led["phases"]:
            m = STARTED_RE.match(line)
            if m:
                return m.group(1)
        return None

    def items_by_trade(self) -> dict[str, int]:
        by_trade: dict[str, int] = {}
        files: dict[str, dict] = {}
        for (window, unit), latest in self.led["latest"].items():
            if window not in ("1", "2", "3"):
                continue
            pass_id = latest["pass"]
            if pass_id not in files:
                try:
                    files[pass_id] = pass_summary.read_trades(self.folder / "trades" / f"{pass_id}.txt")
                except Exception:
                    files[pass_id] = {}
            for code, count in files[pass_id].get(unit, []):
                by_trade[code] = by_trade.get(code, 0) + count
        return by_trade

    def summed(self, field: str, windows: tuple[str, ...]) -> int:
        return sum(
            latest["fields"].get(field, 0) for (window, _unit), latest in self.led["latest"].items()
            if window in windows
        )

    def sheets_read(self) -> tuple[int, int | None]:
        read = sum(
            1 for window in ("1", "2") for unit in self.ok[window] if not plan_inventory._is_repeated_unit(unit)
        )
        sheets = self.inventory.get("sheets") if isinstance(self.inventory, dict) else None
        return read, len(sheets) if isinstance(sheets, list) else None

    def report_state(self, unit: str, kind: str) -> tuple[str, Path | None]:
        """
        Whose report a window 3 unit's latest read counts off, by the summary's own selection, and
        its path: `reader` where the reader's report of that read is on file and the report check
        holds it whole, `restored` where the run's restored report of that read stands in, and
        `none` where neither is on file. Only `reader` says which pages were read.
        """
        try:
            history = pass_summary.unit_report_script.unit_history(self.folder / pass_summary.LEDGER_NAME, "3", unit)
            if history["latest"] is None:
                return "none", None
            read, _verified = history["latest"]
            path, restored, problems = pass_summary.report_of_read(
                self.folder / pass_summary.REPORTS_FOLDER, unit, read, history["dispatches"], kind,
            )
        except Exception:
            return "none", None
        if not problems:
            return "reader", path
        return ("restored" if restored else "none"), None

    def spans_read(self, path: Path, kind: str, planned: list[tuple[str, int, int]]) -> list[tuple[str, int, int]]:
        """
        The spans a reader's own report says it read, off its `spans read:` lines, each held to the
        spans the plan gave the unit: a span the plan did not give is not counted. A section the
        reader left unread, as its runner allows where the manual was removed or the section left
        the package, is on no `spans read:` line, so its pages are never counted.
        """
        text = unit_report.report_text(path.read_bytes()) or ""
        lines = unit_report.sections(text, unit_report.LABELS[kind]).get("spans read", [])
        said = _spans("; ".join(re.sub(r"^[-*]\s+", "", line.strip()) for line in lines))
        return [span for span in planned if span in said]

    def manual_pages(self) -> tuple[int, dict[str, str], dict[str, list[str]]]:
        """
        Pages read off the `spans read:` lines of reports the readers wrote, held to the plan, each
        unit verified ok whose pages are not known with why (`restored` or `none`), and the sections
        read by package.
        """
        pages = 0
        not_known: dict[str, str] = {}
        by_package: dict[str, list[str]] = {}
        for unit, planned in self.plan3["units"].items():
            if unit not in self.ok["3"] or not planned["spans"]:
                continue
            state, path = self.report_state(unit, planned["kind"])
            if state != "reader" or path is None:
                not_known[unit] = state
                continue
            try:
                read = self.spans_read(path, planned["kind"], planned["spans"])
            except (OSError, unit_report.ReportError):
                not_known[unit] = "none"
                continue
            pages += sum(last - first + 1 for _code, first, last in read)
            by_package.setdefault(planned["package"], []).extend(
                f"{code} pages {first} to {last}" for code, first, last in read
            )
        return pages, not_known, by_package

    def not_checked(self) -> list[dict]:
        """
        Each entry of the `sections not checked:` and `families not checked:` lines of the report
        each window 3 review's and manual part's latest read verified ok counts off, where the
        reader's own report is on file and whole, with the unit, its kind, its label and, for a
        manual part, the planned spans its `spans read:` lines leave off. A restored report, or
        none on file, is named elsewhere as pages not known.
        """
        out: list[dict] = []
        for unit, planned in self.plan3["units"].items():
            if planned["kind"] not in ("review", "manual") or unit not in self.ok["3"]:
                continue
            state, path = self.report_state(unit, planned["kind"])
            if state != "reader" or path is None:
                continue
            try:
                text = unit_report.report_text(path.read_bytes()) or ""
                found = unit_report.sections(text, unit_report.LABELS[planned["kind"]])
                read = self.spans_read(path, planned["kind"], planned["spans"]) if planned["spans"] else []
            except (OSError, unit_report.ReportError):
                continue
            unread = [span for span in planned["spans"] if span not in read]
            for label in ("sections not checked", "families not checked"):
                for entry in unit_report._report_items(found.get(label, [])):
                    out.append({"unit": unit, "kind": planned["kind"], "label": label, "entry": entry,
                                "unread": unread, "package": planned["package"]})
        return out

    def note_sheet(self, window: str, unit: str) -> str | None:
        """The sheet, or on a review its package's name, that the runner writes first in a unit's notes."""
        if window == "3":
            planned = self.plan3["units"].get(unit)
            return planned["package"] if planned else None
        sheets = self.led["sheets_of"].get((window, unit))
        return sheets[0] if sheets else None

    def failure_said(self, note: dict) -> str:
        """One read's deviation note in plain words, by the check its runner names after the sheet."""
        clause = note["clause"]
        blocked = pass_summary.BLOCKED_NOTE_RE.search(clause)
        if blocked:
            why = {"sign-in": "the Plumlayer sign-in had expired", "refused by the client": "Claude Code did not allow a call",
                   "server": "Plumlayer did not answer"}[blocked.group(2)]
            return f"it stopped because {why}"
        if pass_summary.INTERRUPTED_NOTE_RE.search(clause):
            return "it was cut off when the session stopped"
        if CHECKED_OFF_RE.match(clause):
            return "its report file was not whole, so its check was made off the report the reading returned"
        end = _READ_END_RE.search(clause)
        body = clause[: end.start()] if end else clause
        found = _check_of(body, self.note_sheet(note["window"], note["unit"]))
        if found:
            return found
        group = self.group_name(note["window"], note["unit"])
        return f"its check noted “{self.say(body, group)}”"

    def skip_reason(self, window: str, unit: str) -> str:
        """The plain words for how a skipped unit's latest read failed, off that read's own lines."""
        attempt = self.led["dispatch"].get((window, unit), 0)
        notes = [
            note for note in self.led["notes"]
            if note["window"] == window and note["unit"] == unit and note["kind"] == "deviation"
            and (m := _READ_END_RE.search(note["clause"])) and int(m.group(1)) == attempt
            and not CHECKED_OFF_RE.match(note["clause"]) and not RESTORED_RE.match(note["clause"])
        ]
        found: list[str] = []
        for note in notes:
            words = self.failure_said(note)
            if words not in found:
                found.append(words)
        return "; ".join(found) if found else REASON_FALLBACK

    # ---- what was planned, and what was finished ------------------------ #

    def planned(self, window: str) -> tuple[list[str] | None, int]:
        """The unit ids a window's plan carries, None where it has not been planned, and sheets held back."""
        if window == "1":
            if self.window_1 is None:
                return ([] if any(p.startswith("phase: window 1 skipped") for p in self.led["phases"]) else None), 0
            units = [u.get("id") for u in self.window_1.get("units", []) if isinstance(u, dict)]
            units += [u.get("unitId") for u in self.window_1.get("repeatedSets", []) if isinstance(u, dict)]
            return [u for u in units if isinstance(u, str)], 0
        if window == "2":
            if self.window_2 is None:
                return None, 0
            units = [u.get("id") for u in self.window_2.get("units", []) if isinstance(u, dict)]
            held = self.window_2.get("deferredCount", 0)
            return [u for u in units if isinstance(u, str)], held if isinstance(held, int) else 0
        if not self.plan3["present"]:
            return None, 0
        return list(self.plan3["units"]), 0

    def progress(self) -> tuple[list[dict], bool, bool]:
        """
        Each window's planned units reconciled one by one against the ledger, whether every window
        is planned and finished, and whether every planned unit verified ok.
        """
        rows: list[dict] = []
        complete = True
        all_ok = True
        for window in ("1", "2", "3"):
            units, held = self.planned(window)
            if units is None:
                rows.append({"window": window, "planned": None})
                complete = all_ok = False
                continue
            dispatched = {unit for (w, unit) in self.led["dispatch"] if w == window}
            ok = [u for u in units if u in self.ok[window]]
            skipped = [u for u in units if u in self.skipped[window]]
            started = [u for u in units if u in dispatched and u not in self.ok[window] and u not in self.skipped[window]]
            not_started = [u for u in units if u not in dispatched]
            rows.append({"window": window, "planned": units, "ok": ok, "skipped": skipped,
                         "started": started, "not_started": not_started, "held": held})
            if started or not_started or held:
                complete = False
            if skipped or started or not_started or held:
                all_ok = False
        if not any(p.startswith("phase: window 3 complete") for p in self.led["phases"]):
            complete = all_ok = False
        return rows, complete, all_ok


def note_body(note: dict) -> str:
    return ENDING_RE.sub("", note["clause"])


def amendments(led: dict) -> tuple[list[str], list[str]]:
    """
    The package amendments made, and those started and not confirmed. The lead appends
    `amending: <text>` before an amendment's calls and `amended: <the same text>` once they
    succeed, so an `amended:` line is a change made, and an `amending:` line no `amended:` line of
    the same text follows is one that may or may not have reached the packages. An older ledger's
    `amended:` lines, with no `amending:` line before them, are changes made.
    """
    made: list[str] = []
    pending: list[str] = []
    for kind, text in led["amended"]:
        if kind == "amending":
            pending.append(text)
            continue
        if text in pending:
            pending.remove(text)
        made.append(text)
    return made, pending


def _check_parts(body: str, sheet: str | None) -> tuple[str, str] | None:
    """
    The check a runner's failure note names, `<sheet> <check> <value>` with its read ending taken
    off, and the value after it: the check is the words right after the sheet, whole. Where the note
    does not open with the unit's sheet, the first place after a space where a check's name stands
    whole is taken. A note naming no check there is None, and is said in its own words.
    """
    if sheet and body.startswith(f"{sheet} "):
        places = [body[len(sheet) + 1:]]
    else:
        places = [body[at.end():] for at in re.finditer(" ", body)]
    for rest in places:
        for name, _words in REASONS:
            if rest == name:
                return name, ""
            if rest.startswith(f"{name} "):
                return name, rest[len(name) + 1:]
    return None


def _check_of(body: str, sheet: str | None) -> str | None:
    """The plain words for the check a runner's failure note names, or None."""
    parts = _check_parts(body, sheet)
    return dict(REASONS)[parts[0]] if parts else None


def _claim_of(facts: "Facts", note: dict) -> tuple[str, str] | None:
    """The check and value of a deviation note that ends `, read <k>`, by its place after the sheet."""
    end = _READ_END_RE.search(note["clause"])
    if end is None:
        return None
    return _check_parts(note["clause"][: end.start()], facts.note_sheet(note["window"], note["unit"]))


# A write an earlier read claimed on a named row, as the estimator reads it: the five claims an
# `owed:` answer may call not needed (unit_report.CLAIM_LISTS).
CLAIM_SAID = {
    "updated": "an update to {row}", "field updates": "a change to {row}",
    "manual updates": "a manual page cited on {row}", "questions linked": "a Question put on {row}",
    "page citations": "a page cited on {row}",
}


def _claim_said(facts: "Facts", note: dict, failed: str) -> str:
    """What a failed check said an earlier read claimed, off the clause it failed with, in plain words."""
    group = facts.group_name(note["window"], note["unit"])
    parts = _check_parts(failed, facts.note_sheet(note["window"], note["unit"]))
    if parts and parts[0] in CLAIM_SAID:
        subject = SUBJECT_RE.search(parts[1])
        row = facts.say(subject.group(0), group) if subject else "an item"
        return CLAIM_SAID[parts[0]].format(row=row)
    if parts:
        return dict(REASONS)[parts[0]]
    return facts.say(failed, group)


def anomaly_gap(note: dict) -> bool:
    """Whether an anomaly note is one the collection of what could not be done prints, by its shape."""
    clause = note["clause"]
    if note["window"] == "3" and (SECTION_NOT_READ_RE.match(clause) or UNSEARCHED_RE.match(clause)
                                  or BOUND_REACHED_RE.match(clause)):
        return True
    if note["window"] == "3" and (FOUND_LATER_RE.match(clause) or OTHER_PACKAGE_RE.match(clause)):
        return True
    trades = TRADES_NOT_KNOWN_RE.match(clause)
    return bool(PICTURE_RE.match(clause) or (trades and trades.group(2) == note["unit"]))


# --------------------------------------------------------------------------- #
# What the run could not do: one collection
# --------------------------------------------------------------------------- #

def gaps(facts: Facts) -> list[dict]:
    """
    Everything the run could not read, match, search or check, each once, with the few words the
    short version names it by. The report's `What I could not read` and the short version's
    `Could not read` both print this list. Each entry is told apart from another by what it is
    about, its unit, read, file, section and pages, and by what was found, left or given as the
    reason, never by the sentence it prints, so two gaps whose sentences read alike are both named.
    The one exception is a manual section not read: each such sentence names the pages the part's
    report or the plan gives, and one that reads word for word as one already printed is not
    printed again.
    """
    out: list[dict] = []
    seen: set[tuple] = set()
    led = facts.led

    def add(key: tuple, name: str, line: str) -> None:
        if key not in seen:
            seen.add(key)
            out.append({"name": name, "line": line})

    # Each skipped unit, with the reason off its last read.
    for window in ("1", "2", "3"):
        for unit, clause in facts.skipped[window].items():
            times = re.search(r"read ([1-9][0-9]*) times", clause)
            k = times.group(1) if times else "two"
            name = facts.manual_name(unit) if window == "3" else facts.unit_name(window, unit)
            line = (
                f"{_cap(name)}: I read it {k} times and could not confirm what I wrote. "
                f"The last time, {facts.skip_reason(window, unit)}. Anything it wrote stays on the scope "
                f"list. Check {'this sheet' if window in ('1', '2') else 'it'} yourself."
            )
            if window == "1" and not plan_inventory._is_repeated_unit(unit):
                line += (
                    " It was read first for the marks and terms the later sheets use, and it was not "
                    "read again with them, so those sheets may be less complete for it."
                )
            planned = facts.plan3["units"].get(unit) if window == "3" else None
            if planned and planned["kind"] == "standard":
                line += f" Some of {planned['package']}'s standard lines may be missing, and its review added none."
            elif planned and planned["kind"] == "review":
                line += f" The headings and the order of the items on {planned['package']} were not settled."
            add(("skipped", window, unit), name, line)
    # The recheck skips no unit: a sheet whose reads were spent stops it, and is named until read again.
    for note in led["notes"]:
        if (note["window"] == "r" and note["kind"] == "unread" and note["unit"] not in facts.ok["r"]
                and plan_inventory.SKIPPED_NOTE_RE.search(" " + note["clause"])):
            name = facts.unit_name("r", note["unit"])
            times = re.search(r" read ([1-9][0-9]*) times, not read again$", " " + note["clause"])
            add(("skipped", "r", note["unit"]), name,
                f"{_cap(name)}: the recheck read its rows {times.group(1) if times else 'two'} times "
                f"and could not confirm what it wrote, and it was not read again before this report.")
    # Every other `unread` note, whatever its clause.
    for note in led["notes"]:
        if note["kind"] != "unread" or plan_inventory.SKIPPED_NOTE_RE.search(" " + note["clause"]):
            continue
        clause = note["clause"]
        group = facts.group_name(note["window"], note["unit"]) if note["unit"] != "-" else "the sheets"
        repeated = UNREAD_FILE_RE.match(clause)
        listed = UNREAD_BLOCKS_RE.match(clause)
        section = UNREAD_SECTION_RE.match(clause) if note["window"] == "3" else None
        if repeated:
            where = facts.file_said(repeated.group(1))
            add(("repeated lines", repeated.group(1)), f"the notes {where} repeats",
                f"The notes repeated across the sheets of {where} were not read once for the file: "
                f"{facts.say(repeated.group(2), group)}. Its sheets were planned to be read whole instead.")
        elif listed:
            where = facts.file_said(listed.group(1))
            add(("blocks not listed", listed.group(1)), f"notes {where} repeats",
                f"{_plural(int(listed.group(2)), 'block')} of the notes repeated across the sheets of {where}, "
                f"{_plural(int(listed.group(3)), 'line')}, were not listed: {facts.say(listed.group(4), group)}. "
                f"Its sheets were planned to be read whole instead.")
        elif section:
            add(("section", note["unit"], section.group(1), section.group(2), section.group(3)),
                f"section {section.group(1)}", f"For {group}, {facts.say(clause, group)}.")
        else:
            add(("unread", note["window"], note["unit"], clause), group,
                f"{_cap(group)}: not read: {facts.say(clause, group)}.")
    # Each scanned sheet, or part of one, not read from its picture.
    for note in led["notes"]:
        picture = PICTURE_RE.match(note["clause"]) if note["kind"] == "anomaly" else None
        if picture:
            group = facts.group_name(note["window"], note["unit"])
            body = facts.say(note_body(note), group)
            add(("picture", picture.group(1), picture.group(2), picture.group(3)), f"{picture.group(1)} (a scan)",
                f"{body}. It is a scan, and I could not read that part from its picture, so some of what is drawn there may not be on an item.")
    # What the index left uncited, every kind it counts, off the last index line.
    index_lines = [line for line in led["phases"] if line.startswith("phase: index built")]
    if index_lines:
        figures = dict(re.findall(r"([A-Za-z]+) (\d+)", index_lines[-1]))
        known = {kind for kind, _line, _name in INDEX_KINDS}
        for kind, line, name in INDEX_KINDS:
            n = int(figures.get(kind, 0))
            if n:
                add(("index", kind), _counted(f"{{n}} {name}", n), _counted(line, n))
        other = sum(int(n) for kind, n in figures.items() if kind not in known)
        if other:
            add(("index", "other"), _counted(f"{{n}} {INDEX_OTHER[1]}", other), _counted(INDEX_OTHER[0], other))
    # Sheets left out at the start, or by the delivery's plan.
    window_1 = facts.window_1 or {}
    excluded = [key.split("@")[0] for key in window_1.get("excluded", []) or [] if isinstance(key, str)]
    if excluded:
        reasons = "; ".join(f"{e.get('pattern')}: {e.get('reason')}" for e in window_1.get("exclude", []) or [] if isinstance(e, dict))
        add(("left out",), "sheets left out at the start",
            f"Left out of the read plan at the start: {', '.join(dict.fromkeys(excluded))}" + (f" ({reasons})" if reasons else "") + ".")
    left_by_plan = window_1.get("leftByPlan") or []
    left_sheets = [key.split("@")[0] for key in left_by_plan if isinstance(key, str)]
    if left_sheets:
        add(("left by plan",), "sheets the delivery's plan left",
            f"Left unread by the plan you approved for this delivery: {', '.join(dict.fromkeys(left_sheets))}.")
    # Manual sections, or runs of their pages, no unit of the plan reads. A skipped manual part's
    # pages are named with the part, by its sections and pages, above.
    for item in facts.plan3["omissions"]:
        if item["reason"] == plan_inventory.NOT_READ_SKIPPED:
            continue
        package = facts.plan3["units"].get(item["unit"], {}).get("package") or facts.package_of_unit(item["unit"])
        pages = f" pages {item['pages'][0]} to {item['pages'][1]}" if item.get("pages") else ""
        add(("omitted", item["unit"], item["code"], item.get("pages")), f"section {item['code']}{pages}",
            f"Section {item['code']}{pages} for {package}: no unit read it, because {item['reason']}.")
    # A manual part's section not read is named once for that part. Where the part's latest read
    # verified ok and its own report of that read is on file and whole, the entry built from that
    # report, below, is the one: it holds the current reason and the pages left. Otherwise (the part
    # skipped, never verified ok, or its report lost or not on file) the part's latest `section ...
    # not read` anomaly is, with the pages the plan gave the part, so two parts of one section are
    # told apart by their pages; an earlier anomaly of that part and section is history.
    _read, part_known, _by_package = facts.manual_pages()
    standing = {
        unit for unit, planned in facts.plan3["units"].items()
        if planned["kind"] == "manual" and unit in facts.ok["3"] and unit not in part_known
        and facts.report_state(unit, "manual")[0] == "reader"
    }
    section_notes: dict[tuple[str, str], re.Match] = {}
    for note in led["notes"]:
        section = SECTION_NOT_READ_RE.match(note["clause"]) if note["kind"] == "anomaly" and note["window"] == "3" else None
        if section:
            section_notes.pop((note["unit"], section.group(1)), None)
            section_notes[(note["unit"], section.group(1))] = section
    section_said: set[str] = set()

    def add_section(key: tuple, name: str, line: str) -> None:
        """A manual section's gap, where no gap already printed reads the same sentence."""
        if line not in section_said:
            section_said.add(line)
            add(key, name, line)

    used_notes: set[tuple[str, str]] = set()
    for (unit, code), section in section_notes.items():
        if unit in standing:
            continue
        planned = facts.plan3["units"].get(unit, {})
        used_notes.add((unit, code))
        pages = "; ".join(f"pages {a} to {b}" for c, a, b in planned.get("spans", []) if c == code) \
            if planned.get("kind") == "manual" else ""
        group = facts.group_name("3", unit)
        add_section(("not read", unit, code), f"section {code}",
                    f"{group}: section {code}{f' ({pages})' if pages else ''} not read: "
                    f"{facts.say(section.group(2), group)}.")
    # Each section and family a verified review or manual part did not check, off its own report, by
    # the shapes its producer writes, and an entry in none in its own words. A manual part's section
    # left unread is named here, with its pages, and its anomaly above adds nothing. Each entry's key
    # holds its reason, so two reasons for one section are both named.
    no_sections: list[str] = []
    no_manual = False
    checked = facts.not_checked()
    # A review's `not read` or `not known` entry copies the notes script's line for a gap of its
    # package's section: where the collection already names that section of that package as a part's
    # gap (a skipped part, or one whose report was lost or is not on file), a part's anomaly or a
    # plan omission, it is the same gap, named once, there.
    named_sections = {
        (_review_of(part), code)
        for part, planned in facts.plan3["units"].items()
        if planned["kind"] == "manual" and (part in facts.skipped["3"] or part in part_known)
        for code, _first, _last in planned["spans"]
    }
    named_sections |= {(_review_of(item["unit"]), item["code"]) for item in facts.plan3["omissions"]}
    named_sections |= {
        (_review_of(unit), code) for unit, code in used_notes
        if facts.plan3["units"].get(unit, {}).get("kind") == "manual"
    }
    named_sections |= {
        (_review_of(item["unit"]), part.group(1)) for item in checked
        if item["kind"] == "manual" and (part := PART_UNREAD_RE.match(item["entry"]))
    }
    for item in checked:
        unit, package, entry = item["unit"], item["package"], item["entry"]
        said = facts.say(entry, package)
        if item["label"] == "families not checked":
            referral = FAMILY_REFERRAL_RE.match(entry)
            if referral:
                add(("family", unit, entry), f"{referral.group(1)} for {package}",
                    f"{package}: {facts.say(referral.group(1), package)} was not checked against the manual. Section "
                    f"{referral.group(2)} was named for it, and the first two pages read there did not settle it.")
            else:
                add(("family", unit, entry), f"a family of items for {package}",
                    f"{package}: a family of items was not checked against the manual: {said}.")
            continue
        unread = REVIEW_UNREAD_RE.match(entry) if item["kind"] == "review" else None
        spent = REVIEW_SPENT_RE.match(entry) if item["kind"] == "review" else None
        notes_unread = REVIEW_NOTES_UNREAD_RE.match(entry) if item["kind"] == "review" else None
        part = PART_UNREAD_RE.match(entry) if item["kind"] == "manual" else None
        owners = OWNERS_WORK_RE.match(entry)
        if part:
            code = part.group(1)
            pages = "; ".join(f"pages {a} to {b}" for c, a, b in item["unread"] if c == code)
            add_section(("not read", unit, code), f"section {code} for {package}",
                        f"Manual pages for {package} (section {code}{', ' + pages if pages else ''}): not read, because "
                        f"{PART_UNREAD_SAID[part.group(2)]}.")
        elif unread and (_review_of(unit), unread.group(1)) in named_sections:
            continue
        elif unread:
            why = facts.say(re.sub(r"^not known, ", "", unread.group(3)), package)
            add(("checked", unit, unread.group(1), unread.group(2), unread.group(3)), f"section {unread.group(1)} for {package}",
                f"{package}: section {unread.group(1)} was not checked against the drawings, since "
                + (f"its manual pages were not read ({why})." if unread.group(2) == "not read" else
                   f"which of its manual pages were read is not known ({why})."))
        elif spent:
            add(("checked", unit, spent.group(1), "searches spent"), f"section {spent.group(1)} for {package}",
                f"{package}: section {spent.group(1)} was not checked for work no sheet shows, because the "
                f"review's searches ran out first.")
        elif notes_unread:
            add(("checked", unit, notes_unread.group(1), "notes not read"), f"section {notes_unread.group(1)} for {package}",
                f"{package}: section {notes_unread.group(1)} was not checked, because the review did not read "
                f"the part of the manual notes that holds it.")
        elif owners:
            # Each part of the section, and its review, names the owner's work: one entry a package's section.
            add(("owner's work", _review_of(unit), owners.group(1)), f"section {owners.group(1)} for {package}",
                f"{package}: section {owners.group(1)} is work the owner contracts for, so it was not checked "
                f"as this package's work.")
        elif NO_SECTIONS_RE.match(entry):
            no_sections.append(package)
        elif NO_MANUAL_RE.match(entry):
            no_manual = True
        else:
            add(("checked", unit, entry), f"a section for {package}",
                f"{package}: a section was not checked: {said}.")
    if no_sections:
        add(("no sections",), "packages with no manual section",
            f"No manual section is on {', '.join(dict.fromkeys(no_sections))}, so no section was checked for "
            f"{'it' if len(set(no_sections)) == 1 else 'them'}.")
    if no_manual:
        add(("no manual",), "the project manual",
            "No project manual was read in, so no review checked the drawings against one.")
    # Each standard line whose condition a review found after the line was written or left: the
    # review writes nothing for it, so the estimator decides.
    for note in led["notes"]:
        later = FOUND_LATER_RE.match(note["clause"]) if note["kind"] == "anomaly" and note["window"] == "3" else None
        if later:
            group = facts.group_name("3", note["unit"])
            line, where, what = (facts.say(part.strip(), group) for part in later.groups())
            add(("found later", note["unit"], *(part.strip() for part in later.groups())),
                f"the standard line {line} for {group}",
                f"{group}: the review found the condition of the standard line {line} at {where} after the "
                f"line was written or left ({what}), and wrote nothing for it. Check the line yourself.")
    # A review that reached one of its bounds: the limit, then what it left, in the review's words.
    for note in led["notes"]:
        bound = BOUND_REACHED_RE.match(note["clause"]) if note["kind"] == "anomaly" and note["window"] == "3" else None
        if bound:
            group = facts.group_name("3", note["unit"])
            add(("bound", note["unit"], bound.group(1), bound.group(3)), f"{group}: {bound.group(1)}",
                f"{_cap(group)}: the review stopped at its limit of {bound.group(2)} {bound.group(1)}. What the "
                f"review left, in its report's words: “{facts.say(bound.group(3), group)}”.")
    # Words a review could not search.
    unsearched: dict[str, list[str]] = {}
    for note in led["notes"]:
        words = UNSEARCHED_RE.match(note["clause"]) if note["kind"] == "anomaly" and note["window"] == "3" else None
        if words:
            found = unsearched.setdefault(facts.group_name("3", note["unit"]), [])
            if words.group(1) not in found:
                found.append(words.group(1))
    for package, words in unsearched.items():
        add(("unsearched", package), f"searches for {package}",
            f"{package}: I could not search for {', '.join(words)}, so I may have missed work for this "
            f"package. Search them in the drawings on plumlayer.com.")
    # Window 3 units whose pages read are not known: a report written from the record, or none on file.
    _pages, not_known, _by_package = facts.manual_pages()
    restored_units = [
        note["unit"] for note in led["notes"]
        if note["window"] == "3" and note["kind"] == "deviation"
        and (m := RESTORED_RE.match(note["clause"])) and m.group(1) == note["unit"]
    ]
    for unit in [*restored_units, *[u for u, state in not_known.items() if state == "restored"]]:
        name = facts.manual_name(unit)
        add(("pages", unit), f"{name}'s pages",
            f"{_cap(name)}: its reader's report was lost, so I wrote it from the record; which pages it "
            f"opened and what it searched are not known.")
    for unit, state in not_known.items():
        if state == "none" and unit not in restored_units:
            name = facts.manual_name(unit)
            add(("pages", unit), f"{name}'s pages",
                f"{_cap(name)}: it was checked, but no report of its last read is on file, so which pages "
                f"it read is not known.")
    # Reads whose trades are not known, each by its unit and read.
    for note in led["notes"]:
        trades = TRADES_NOT_KNOWN_RE.match(note["clause"]) if note["kind"] == "anomaly" else None
        if trades and trades.group(2) == note["unit"]:
            name = facts.manual_name(note["unit"]) if note["window"] == "3" else facts.unit_name(note["window"], note["unit"])
            add(("trades", note["window"], note["unit"], trades.group(1)), f"{name}'s trades",
                f"{_cap(name)}, read {trades.group(1)}: the trades it wrote to are not known, so a later "
                f"pass on an addendum may leave out a package it wrote to.")
    # Deviation notes of a window's boundary, and any other deviation with no read ending. Names a
    # boundary took off the record so its scan could run are history, in the detail part.
    for note in led["notes"]:
        if note["kind"] != "deviation" or _READ_END_RE.search(note["clause"]):
            continue
        clause = note["clause"]
        if note["unit"] == "-" or note["pass"] == "boundary":
            when = f"the end of window {note['window']}"
            scan = SCAN_NOT_RUN_RE.match(clause)
            if scan:
                add(("scan", note["window"]), f"the check for work written twice at {when}",
                    f"At {when}, the check for the same work written by two groups of sheets read side "
                    f"by side was not run: the names of {_plural(int(scan.group(1)), 'reading')}' items were missing.")
            elif not NAMES_FETCHED_RE.match(clause):
                add(("boundary", note["window"], clause), f"a note at {when}",
                    f"At {when}: {facts.say(clause, 'the sheets')}.")
            continue
        if any(pattern.search(clause) for pattern, _words in BOOKKEEPING):
            continue
        name = facts.unit_name(note["window"], note["unit"])
        if NO_SHEET_CITED_RE.match(clause):
            add(("no sheet", note["window"], note["unit"]), name,
                f"{_cap(name)}: its reading cited no sheet, so nothing it wrote is tied to the sheet. Check it yourself.")
        else:
            add(("deviation", note["window"], note["unit"], clause), name,
                f"{_cap(name)}: {facts.say(clause, facts.group_name(note['window'], note['unit']))}.")
    return out


def mark_outstanding(facts: Facts) -> None:
    """
    Mark each `not written:` note still outstanding: the entries of a unit's latest read that
    verified ok, which noted again each one it still did not write, and of every read after it; and
    of every read where none verified ok, a skipped unit among them. A read that verified ok answered
    every earlier entry, written or not needed, so an earlier read's entries are history.
    """
    led = facts.led
    for note in led["notes"]:
        if note["kind"] != "anomaly" or not NOT_WRITTEN_RE.match(note["clause"]):
            continue
        ok_reads = [k for k, result in led["results"].get((note["window"], note["unit"]), {}).items() if result == "ok"]
        note["outstanding"] = not ok_reads or note["attempt"] >= max(ok_reads)


# --------------------------------------------------------------------------- #
# The report
# --------------------------------------------------------------------------- #

def _now() -> str:
    return datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _duration(start: str | None, end: str) -> str | None:
    if start is None:
        return None
    try:
        a = datetime.datetime.strptime(start, "%Y-%m-%dT%H:%M:%SZ")
        b = datetime.datetime.strptime(end, "%Y-%m-%dT%H:%M:%SZ")
    except ValueError:
        return None
    minutes = max(0, int((b - a).total_seconds() // 60))
    return f"{_plural(minutes // 60, 'hour')} {_plural(minutes % 60, 'minute')}"


def _when(stamp: str) -> str:
    return stamp.replace("T", " ").replace("Z", " UTC")


def _guarded(title: str, write) -> list[str]:
    """One section of the report; a section that fails says so and why, and the rest are written."""
    try:
        return write()
    except Exception as e:
        return [f"## {title}", "", f"- This section is not available: it failed ({type(e).__name__}: {str(e)[:200]}).", ""]


def _progress_lines(rows: list[dict]) -> list[str]:
    lines: list[str] = []
    for row in rows:
        said = WINDOW_SAID[row["window"]]
        if row["planned"] is None:
            lines.append(f"- {said}: not planned when this report was written, so none of it was read.")
            continue
        parts = [
            f"{len(row['planned'])} planned",
            f"{len(row['ok'])} read and checked",
        ]
        if row["skipped"]:
            parts.append(f"{len(row['skipped'])} read and not confirmed, named above")
        parts.append(f"{len(row['started'])} started and not finished")
        parts.append(f"{len(row['not_started'])} not started")
        if row["held"]:
            parts.append(f"{_plural(row['held'], 'sheet')} held back for later and not yet planned")
        lines.append(f"- {said}: {', '.join(parts)}.")
    return lines


def build(facts: Facts, stopped: str | None, finished: str) -> tuple[list[str], dict]:
    """The report's lines (body, then detail), and the figures the short version says."""
    led = facts.led
    short: dict = {"could_not": [], "look": 0, "changes": 0, "grain": 0}
    lines: list[str] = []
    collection: list[dict] = []
    progress: tuple[list[dict], bool, bool] = ([], False, False)
    by_trade: dict[str, int] = {}
    by_package: dict[str, list[str]] = {}
    fold_said: list[str] = []
    fold_lines: list[tuple[str, str]] = []
    raised = replied = 0

    def headline() -> list[str]:
        nonlocal by_trade, by_package, raised, replied
        label = facts.run.get("label") if isinstance(facts.run.get("label"), str) else None
        out: list[str] = []
        took = _duration(facts.started(), finished)
        what = f"Scope run on {label}" if label else "Scope run on a drawing set whose label is not available"
        if stopped:
            out += [f"# {what}: stopped {_when(finished)}", "",
                    f"The run stopped before its end: {stopped}. This report covers what it read until then."]
        else:
            out += [f"# {what}: finished {_when(finished)}", "",
                    f"Finished {_when(finished)}, " + (f"{took} after reading started." if took else
                                                      "and how long it took is not known: this run's log does not say when reading started.")]
        out.append("")
        read, total = facts.sheets_read()
        pages, not_known, by_package = facts.manual_pages()
        by_trade = facts.items_by_trade()
        added = sum(by_trade.values())
        updated = facts.summed("updated", ("1", "2", "3"))
        raised = facts.summed("questions", ("1", "2", "3", "r"))
        replied = facts.summed("replied", ("1", "2", "3", "r"))
        combined = sum(
            1 for note in led["notes"]
            if note["window"] == "3" and note["kind"] == "anomaly"
            and (pair := SAME_WORK_RE.match(note["clause"])) and pair.group(1).endswith(", combined")
        )
        manual = f" and {pages} pages of the project manual" if pages else ""
        if not_known:
            manual += (f"; {_plural(len(not_known), 'review or manual part', 'reviews or manual parts')} "
                       f"{'was' if len(not_known) == 1 else 'were'} checked whose pages read are not known")
        out.append(
            f"I read {read} of the {total if total is not None else 'planned'} sheets{manual}. "
            f"I added {added} items and updated {updated}. "
            f"The package reviews combined {_plural(combined, 'item')} into another item that carries the same work. "
            f"I raised {raised} Questions and replied on {replied}. Each trade's page on plumlayer.com "
            f"shows its items, and every item lists the sheets that say what it is."
        )
        trade_said = _trade_names(facts.folder)
        short.update(
            read=read, total=total, added=added, raised=raised,
            by_trade={trade_said.get(code, code): n for code, n in by_trade.items()},
        )
        out.append("")
        return out

    lines += _guarded("The run", headline)

    def could_not_read() -> list[str]:
        nonlocal collection, progress
        collection = gaps(facts)
        short["could_not"] = [entry["name"] for entry in collection]
        progress = facts.progress()
        rows, complete, all_ok = progress
        out = ["## What I could not read", ""]
        if collection:
            out += [f"- {entry['line']}" for entry in collection]
        elif complete and all_ok:
            out.append("Nothing. Every sheet and manual page planned was read and checked.")
        else:
            out.append("Nothing is named here, but the run did not finish everything it planned: how far it got is below.")
        out.append("")
        if stopped or not complete:
            out += ["## How far the run got", ""]
            out += _progress_lines(rows)
            out.append("")
        return out

    lines += _guarded("What I could not read", could_not_read)

    def questions() -> list[str]:
        # The copy counts every Question on the project, open and closed (`status: "all"`), and
        # the server gives no count of the open ones by trade, so none is called open here.
        out = [f"## {QUESTIONS_TITLE}", ""]
        counts = _json(facts.folder.joinpath(*CLOSE_FOLDER, "questions.json"))
        trade_names = _trade_names(facts.folder)
        every = counts.get("everyTradeCount") if isinstance(counts, dict) else None
        untraded = counts.get("untradedCount") if isinstance(counts, dict) else None
        trades = counts.get("tradeCounts") if isinstance(counts, dict) else None
        if isinstance(trades, dict) and isinstance(every, int) and isinstance(untraded, int):
            # Each trade's count, as the server gives it, already includes the every-trade
            # Questions. It is printed as it stands, the figure the trade's page holds, and said so,
            # so the every-trade figure beside it never reads as one to add.
            out.append("- These count every Question on the project, open and closed. Each trade's figure "
                       "includes the Questions that apply to every trade.")
            per = [
                f"{trade_names.get(code, code)}: {n}"
                for code, n in sorted(((c, n) for c, n in trades.items() if isinstance(n, int)), key=lambda pair: (-pair[1], pair[0]))
                if n > 0
            ]
            out.append("- " + ("; ".join(per) if per else "no trade has a figure of its own"))
            out.append(f"- Of those, on every trade: {every}, already in each trade's figure. Trade not known yet: {untraded}.")
        elif counts is None:
            out.append("- The Questions by trade are not available: the copy of the project's Question counts is not on file.")
        else:
            out.append("- The Questions by trade are not available: the copy of the project's Question counts is not in its shape.")
        out.append("- The open ones are on each trade's page on plumlayer.com.")
        out.append(f"- {raised} raised by this run, and replies on {replied}.")
        out.append("")
        return out

    lines += _guarded(QUESTIONS_TITLE, questions)

    def to_look_at() -> list[str]:
        look: dict[str, list[str]] = {}
        grain: list[str] = []
        door: list[str] = []
        overlap: list[str] = []
        pairs: list[str] = []
        not_written: list[str] = []
        not_needed: list[str] = []
        on_question = 0
        mark_outstanding(facts)
        for note in led["notes"]:
            window, unit, kind, clause = note["window"], note["unit"], note["kind"], note["clause"]
            group = facts.group_name(window, unit) if unit != "-" else "the sheets"
            if kind == "anomaly":
                if LANDED_RE.search(clause):
                    on_question += 1
                    continue
                pair = SAME_WORK_RE.match(clause) if window == "3" else None
                written = NOT_WRITTEN_RE.match(clause)
                needed = NOT_NEEDED_RE.match(clause)
                if pair:
                    said = facts.say(pair.group(1), group)
                    if pair.group(1).endswith(", combined"):
                        pairs.append(f"Combined: {said.rsplit(', combined', 1)[0]}. Tell me to put the retired item back.")
                    else:
                        pairs.append(f"Left for you: {said}. Retire one on the site or tell me to.")
                elif written:
                    if note.get("outstanding"):
                        where, what, row, why = (facts.say(part.strip(), group) for part in written.groups())
                        said = f"{group}: {where}: {what}, for {row}, not written because {why}. No later read wrote it."
                        if said not in not_written:
                            not_written.append(said)
                elif needed:
                    not_needed.append(f"{group}: {_claim_said(facts, note, needed.group(1))}; {facts.say(needed.group(2), group)}")
                elif not anomaly_gap(note):
                    look.setdefault(group, []).append(facts.say(note_body(note), group))
            elif kind == "grain":
                grain.append(f"{group}: {facts.say(clause, group)}")
            elif kind == "door":
                door.append(f"{group}: {facts.say(clause, group)}")
            elif kind == "overlap" and not OVERLAP_SCAN_RE.match(clause):
                m = OVERLAP_PAIR_RE.match(clause)
                if m:
                    overlap.append(
                        f"\u201c{m.group(1)}\u201d on {facts.unit_name(window, m.group(2))} and on {facts.unit_name(window, m.group(3))}"
                    )
                else:
                    look.setdefault(group, []).append(facts.say(clause, group))
            elif kind == "deviation" and (made := _claim_of(facts, note)) and made[0] == "created subjects":
                subject = SUBJECT_RE.search(made[1])
                if subject:
                    look.setdefault(group, []).append(
                        f"{facts.say(subject.group(0), group)} was written under another reading's numbering; check which sheet it belongs to"
                    )
        out = ["## To look at", ""]
        count_look = 0
        for group, entries in look.items():
            for entry in dict.fromkeys(entries):
                out.append(f"- {group}: {entry}.")
                count_look += 1
        for title, entries in (
            ("Items I was not sure how finely to split", grain),
            ("For you to decide", door),
            ("Items that may be the same work twice", overlap),
            ("Items that carry the same work", pairs),
            ("Requirements read and not written", not_written),
            ("Writes a read said it made that its check did not find, which the next read said were not needed", not_needed),
            ("Packages that took an item after their own review, so their headings and order may need a look",
             facts.reviewed_then_written()),
        ):
            unique = list(dict.fromkeys(entries))
            if unique:
                out.append(f"- {title}:")
                out.extend(f"  - {entry}" for entry in unique)
                count_look += len(unique)
        if count_look == 0:
            out.append("Nothing beyond what is on a Question.")
        if on_question:
            out.append(
                f"- {on_question} more {'note already sits' if on_question == 1 else 'notes already sit'} on a "
                f"Question or a reply, on each trade's page on plumlayer.com."
            )
        short["look"] = count_look
        short["grain"] = len(dict.fromkeys(grain))
        out.append("")
        return out

    lines += _guarded("To look at", to_look_at)

    def package_changes() -> list[str]:
        nonlocal fold_said, fold_lines
        close = facts.folder.joinpath(*CLOSE_FOLDER)
        out = ["## Package changes", ""]
        changes: list[str] = []
        try:
            _path, fold_lines = fold_report.read_report(facts.folder)
        except fold_report.FoldReportError as e:
            if "no fold report" in str(e):
                changes.append(
                    "The fold's report is not on file, so the packages folded are not listed here."
                    if "phase: packages folded" in led["phases"]
                    else "The fold of the packages before the reviews is not on file: the run did not reach it."
                )
            else:
                changes.append(f"The fold's report could not be read: {e}.")
        fold_said = [_fold_said(facts, label_, line) for label_, line in fold_lines]
        changes.extend(f"{said}." for said in fold_said)
        made, started = amendments(led)
        changes.extend(f"Amended: {entry}." for entry in made)
        changes.extend(
            f"Started and not confirmed: {entry}. The package on plumlayer.com may or may not show this change."
            for entry in started
        )
        gr = _json(close / "general-requirements.json")
        package = gr.get("package", gr) if isinstance(gr, dict) else None
        sections = package.get("manualSections") if isinstance(package, dict) else None
        if isinstance(sections, list):
            codes = [s if isinstance(s, str) else str(s.get("code") or s.get("section") or "") if isinstance(s, dict) else "" for s in sections]
            changes.append(
                f"General requirements: the package carries {_plural(len(codes), 'Division 01 section')}"
                + (f" ({', '.join(c for c in codes if c)})" if any(codes) else "") + "."
            )
        else:
            packages_file = _json(facts.folder / "plan" / "packages.json")
            rows = packages_file.get("packages", []) if isinstance(packages_file, dict) else packages_file
            has_gr = isinstance(rows, list) and any(
                isinstance(p, dict) and p.get("tradeCode") == GENERAL_REQUIREMENTS_CODE for p in rows
            )
            changes.append(
                ("General requirements: the package's sections are not available, since its copy is not on file."
                 if gr is None else "General requirements: the package's sections are not available, since its copy is not in its shape.")
                if has_gr else "General requirements: this run made no general requirements package."
            )
        for entry in led["unplaced"]:
            changes.append(f"On no package: {entry}.")
        fresh = _json(close / "packages.json")
        placement = fresh.get("manualSectionPlacement") if isinstance(fresh, dict) else None
        if isinstance(placement, dict):
            open_sections = placement.get("onNoPackage") or []
            if isinstance(open_sections, list) and open_sections:
                codes = [s if isinstance(s, str) else str(s.get("code") or s.get("section") or s.get("number") or "") if isinstance(s, dict) else "" for s in open_sections]
                changes.append(f"Manual sections still on no package: {', '.join(c for c in codes if c)}.")
            if placement.get("truncated"):
                changes.append("The count of manual sections on no package is incomplete: one read did not reach them all.")
        out.extend(f"- {entry}" for entry in changes) if changes else out.append("None.")
        short["changes"] = len(fold_lines) + len(made)
        out.append("")
        return out

    lines += _guarded("Package changes", package_changes)

    def recheck_section() -> list[str]:
        if not (any(line.startswith("phase: recheck complete") for line in led["phases"]) or any(
            key[0] == "r" for key in led["dispatch"]
        )):
            return []
        return ["## The recheck of the new drawings", "", *(f"- {entry}" for entry in _recheck_lines(facts)), ""]

    lines += _guarded("The recheck of the new drawings", recheck_section)

    def still_open() -> list[str]:
        close = facts.folder.joinpath(*CLOSE_FOLDER)
        out = ["## Still open", ""]
        index_lines = [line for line in led["phases"] if line.startswith("phase: index built")]
        if index_lines:
            figures = dict(re.findall(r"([A-Za-z]+) (\d+)", index_lines[-1]))
            nowhere = int(figures.get("codeNoLocation", 0))
            dropped = int(figures.get("codeOnlyOnReplacedPages", 0))
            found = _leftover_lines(close / "leftover-codeNoLocation.json", "Codes found nowhere", nowhere)
            if dropped:
                found += _leftover_lines(close / "leftover-codeOnlyOnReplacedPages.json", "Codes a later drawing issue dropped", dropped)
                found.append("- An item that still names a dropped code is work the revision may have taken out. Check it.")
            out += found or ["- Nothing the index left uncited is named by code; what it left is counted above."]
        else:
            out.append("- The index of every page each item appears on had not run when this report was written.")
        out.append("")
        return out

    lines += _guarded("Still open", still_open)

    def what_went_wrong() -> list[str]:
        out = ["## What went wrong along the way", ""]
        wrong: list[str] = []
        for entry in led["short"]:
            m = re.match(r"^(\S+) (\S+) (\S+) record (\d+) runner (\d+)$", entry)
            if m:
                wrong.append(
                    f"The record holds fewer entries for {facts.unit_name(m.group(1), m.group(3))} than the "
                    f"check of it found ({m.group(4)} against {m.group(5)}). Look at its items."
                )
        for line in led["repaired"]:
            m = ledger_script.REPAIRED_RE.match(line)
            if m:
                count = int(m.group(1))
                wrong.append(f"{_plural(count, 'line')} of the run's log {'was' if count == 1 else 'were'} changed outside the run and put back.")
        blocked = sum(1 for n in led["notes"] if n["kind"] == "deviation" and pass_summary.BLOCKED_NOTE_RE.search(n["clause"]))
        cut = sum(1 for n in led["notes"] if n["kind"] == "deviation" and pass_summary.INTERRUPTED_NOTE_RE.search(n["clause"]))
        if blocked:
            wrong.append(f"{_plural(blocked, 'read')} stopped because a call to Plumlayer could not be made; none counted against its sheet or package.")
        if cut:
            wrong.append(f"{_plural(cut, 'read')} cut off when the session stopped; none counted against its sheet or package.")
        # The failed checks are the reads whose `verified` line reads mismatch, each once.
        again = last_skipped = waiting = 0
        for (window, unit), results in led["results"].items():
            reads = led["dispatch"].get((window, unit), 0)
            for attempt, result in results.items():
                if result != "mismatch":
                    continue
                if attempt < reads:
                    again += 1
                elif unit in facts.skipped.get(window, {}):
                    last_skipped += 1
                else:
                    waiting += 1
        if again:
            wrong.append(f"{_plural(again, 'check')} of a read did not pass, and each of those was read again.")
        if last_skipped:
            wrong.append(f"{_plural(last_skipped, 'check')} did not pass on a last read, and each of those was skipped and is named above.")
        if waiting:
            wrong.append(f"{_plural(waiting, 'check')} did not pass on a read that was not yet read again when this report was written.")
        out.extend(f"- {entry}" for entry in wrong) if wrong else out.append("Nothing.")
        out.append("")
        if facts.unavailable:
            out.append("Not available for this report: " + "; ".join(facts.unavailable) + ".")
            out.append("")
        return out

    lines += _guarded("What went wrong along the way", what_went_wrong)

    # ---- the detail part ---------------------------------------------------
    lines += ["---", "", "## In detail", ""]

    def detail_manual() -> list[str]:
        out = ["### Manual sections read, by package", ""]
        if by_package:
            out.extend(f"- {package}: {', '.join(spans)}" for package, spans in by_package.items())
        else:
            out.append("None read yet." if facts.plan3["present"] else "The package reviews had not been planned when this report was written.")
        out.append("")
        return out

    lines += _guarded("Manual sections read, by package", detail_manual)

    def detail_reads() -> list[str]:
        out = ["### What failed and how it was fixed", ""]
        said = _reads_said(facts)
        out += said if said else ["Nothing failed."]
        out.append("")
        return out

    lines += _guarded("What failed and how it was fixed", detail_reads)

    def detail_progress() -> list[str]:
        rows, complete, _all_ok = progress if progress[0] else facts.progress()
        if stopped or not complete:
            return []
        return ["### What was planned and what was finished", "", *_progress_lines(rows), ""]

    lines += _guarded("What was planned and what was finished", detail_progress)

    def detail_fold() -> list[str]:
        out = ["### Each fold act, and how to undo it", ""]
        if fold_lines:
            out.extend(f"- {said}. To undo it, tell me, or change the package on plumlayer.com." for said in fold_said)
        else:
            out.append("No fold acts are on file.")
        out.append("")
        if facts.plan3["left_out"] or facts.plan3["unnamed"]:
            out += ["### Packages this pass on an addendum did not review", ""]
            if facts.plan3["unnamed"]:
                out.append("Every package was reviewed: a reading changed items on trades it did not name.")
            out.extend(
                f"- {name}: this pass wrote no item on its trade, so the addendum's sheets changed nothing it prices that the readers found."
                for name in facts.plan3["left_out"]
            )
            out.append("")
        return out

    lines += _guarded("Each fold act, and how to undo it", detail_fold)

    def detail_defined() -> list[str]:
        out = ["### Newly defined", ""]
        kinds: list[str] = []
        declared: list[str] = []
        for n in led["notes"]:
            if n["kind"] != "kinds" or KINDS_NOT_WRITTEN_RE.match(n["clause"]):
                continue
            if KINDS_DECLARED_RE.match(n["clause"]):
                declared.append(n["clause"])
            else:
                kinds.extend(n["clause"].split())
        kinds = list(dict.fromkeys(kinds))
        out.append(f"- Kinds of marks defined: {', '.join(kinds)}." if kinds else "- No new kind of mark was defined.")
        if declared:
            out.append(f"- {_plural(len(declared), 'kind')} declared at a window's end, off the record's own entries.")
        out.append("")
        if by_trade:
            names = _trade_names(facts.folder)
            out += ["### What I added, by trade", ""]
            out.extend(
                f"- {names.get(code, code)}: {n}" for code, n in sorted(by_trade.items(), key=lambda pair: (-pair[1], pair[0]))
            )
            out.append("")
        return out

    lines += _guarded("Newly defined", detail_defined)

    if facts.unnamed:
        lines.append(
            "Some notes above name an item or a Question I could not look up by name: "
            + "; ".join(f"{_plural(n, 'name')} for {group}" for group, n in facts.unnamed.items()) + "."
        )
        lines.append("")
    return lines, short


def _reads_said(facts: Facts) -> list[str]:
    """Each read that did not pass or stopped, said once with what followed it, and the run's other notes on its reads."""
    led = facts.led
    by_read: dict[tuple[str, str, int], list[str]] = {}
    other: list[str] = []
    for note in led["notes"]:
        if note["kind"] != "deviation" or RESTORED_RE.match(note["clause"]):
            continue
        fetched = NAMES_FETCHED_RE.match(note["clause"])
        if fetched and (note["unit"] == "-" or note["pass"] == "boundary"):
            # Recovered at the boundary: the names were fetched again and the scan then ran.
            other.append(
                f"- At the end of window {note['window']}, the names of the items "
                f"{facts.unit_name(note['window'], fetched.group(1))} wrote were missing, so I took them off "
                f"the record before checking for the same work written twice."
            )
            continue
        if note["unit"] == "-":
            continue
        end = _READ_END_RE.search(note["clause"])
        if end is None:
            for pattern, words in BOOKKEEPING:
                found = pattern.search(note["clause"])
                if found:
                    other.append(f"- {_cap(facts.unit_name(note['window'], note['unit']))}: {words.format(*found.groups())}.")
                    break
            continue
        key = (note["window"], note["unit"], int(end.group(1)))
        said = facts.failure_said(note)
        if said not in by_read.setdefault(key, []):
            by_read[key].append(said)
    for (window, unit), results in led["results"].items():
        for attempt, result in results.items():
            if result == "mismatch" and (window, unit, attempt) not in by_read:
                by_read[(window, unit, attempt)] = [REASON_FALLBACK]
    out: list[str] = []
    for (window, unit, attempt), said in by_read.items():
        reads = led["dispatch"].get((window, unit), 0)
        if unit in facts.ok.get(window, set()):
            after = "read again and confirmed" if attempt < reads else "confirmed"
        elif unit in facts.skipped.get(window, {}):
            after = "read again, and in the end skipped, named above" if attempt < reads else "skipped, named above"
        else:
            after = "read again, and not yet confirmed" if attempt < reads else "not settled when this report was written"
        out.append(f"- {_cap(facts.unit_name(window, unit))}, read {attempt}: {'; '.join(said)}; {after}.")
    return out + list(dict.fromkeys(other))


def _fold_said(facts: Facts, label: str, line: str) -> str:
    """One fold act as the estimator reads it: its label in words, and no package id."""
    rest = line[len(label) + 2:]
    if label == "deleted":
        m = re.match(r"^(.+?), trade [^,]+, package pkg-[^\s,]+, (.+)$", rest)
        rest = f"{m.group(1)}: {m.group(2)}" if m else rest
    rest = re.sub(r",? package pkg-[^\s,]+", "", rest)
    return f"{FOLD_SAID.get(label, label)}: {facts.say(rest, 'the packages')}"


def _trade_names(folder: Path) -> dict[str, str]:
    for path in (folder.joinpath(*CLOSE_FOLDER, "packages.json"), folder / "plan" / "packages.json"):
        data = _json(path)
        rows = data.get("packages") if isinstance(data, dict) else data
        if isinstance(rows, list):
            return {
                row["tradeCode"]: row["name"] for row in rows
                if isinstance(row, dict) and isinstance(row.get("tradeCode"), str) and isinstance(row.get("name"), str)
            }
    return {}


def _leftover_lines(path: Path, title: str, count: int) -> list[str]:
    data = _json(path)
    rows = data.get("rows") if isinstance(data, dict) else None
    if not isinstance(rows, list):
        return [f"- {title}: {count}; the list of them is not available, since its copy is not on file."] if count else []
    codes = []
    for row in rows:
        if isinstance(row, dict):
            code = row.get("code") or row.get("tag") or row.get("text")
            sheets = row.get("sheets") or row.get("sheetNumbers")
            if code:
                codes.append(f"{code}" + (f" (on {', '.join(map(str, sheets))})" if isinstance(sheets, list) and sheets else ""))
    more = count - len(codes)
    return [f"- {title}: {', '.join(codes)}" + (f", and {more} more" if more > 0 else "") + "."] if codes else []


def _recheck_lines(facts: Facts) -> list[str]:
    if not any(line.startswith("phase: recheck complete") for line in facts.led["phases"]):
        return ["The recheck did not finish, so its figures are not available."]
    if facts.delivery_plan is None:
        return ["The recheck's figures are not available: the closing step was not given the delivery's plan."]
    try:
        import recheck
        lines = recheck.report_lines(facts.folder, facts.delivery_plan)
    except Exception as e:  # the recheck's own refusal, named and never a stop
        return [f"The recheck's figures are not available: {str(e)[:200]}."]
    # The first line is the ledger's own; package ids stay in the run's files.
    return [re.sub(r" \((?:pkg-[^)\s]+|none)\):", ":", line) for line in lines[1:]]


def short_version(short: dict, stopped: str | None, finished: str, took: str | None, report: Path) -> list[str]:
    out = [
        (f"The scope run stopped {_when(finished)}: {stopped}." if stopped else
         f"The scope run finished {_when(finished)}" + (f", {took} after it started." if took else "."))
    ]
    out.append(f"Sheets read: {short.get('read', 0)} of {short.get('total') or 'the planned'}.")
    top = sorted(short.get("by_trade", {}).items(), key=lambda pair: (-pair[1], pair[0]))[:SHORT_NAMED]
    out.append(f"Items added: {short.get('added', 0)}" + (f", most on {', '.join(f'{c} ({n})' for c, n in top)}." if top else "."))
    out.append(f"Questions raised: {short.get('raised', 0)}.")
    could = short.get("could_not", [])
    if could:
        named = ", ".join(could[:SHORT_NAMED]) + (f", and {len(could) - SHORT_NAMED} more" if len(could) > SHORT_NAMED else "")
        out.append(f"Could not read: {len(could)} ({named}).")
    else:
        out.append("Could not read: none.")
    out.append(f"Flagged to look at: {short.get('look', 0)}, of them not sure how finely to split: {short.get('grain', 0)}.")
    out.append(f"Package changes: {short.get('changes', 0)}.")
    out.append(f"The full report: {report}")
    text = "\n".join(out)
    while len(text) > SHORT_CAP and len(out) > 2:
        out.pop(-2)
        text = "\n".join(out)
    if len(text) > SHORT_CAP:
        out = [out[0][: SHORT_CAP - len(out[-1]) - 2], out[-1]]
    return out


# --------------------------------------------------------------------------- #
# Modes
# --------------------------------------------------------------------------- #

def write(folder: Path, delivery_plan: Path | None, stopped: str | None) -> tuple[int, list[str]]:
    report = folder / REPORT_NAME
    finished = None
    old = _text(report)
    if old is not None and not stopped:
        for raw in old.splitlines()[:3]:
            m = FINISHED_MARK_RE.match(raw.strip())
            if m:
                finished = m.group(1)
    finished = finished or _now()
    facts = Facts(folder, delivery_plan)
    body, short = build(facts, stopped, finished)
    lines = ["<!-- Audience: user. Written by close_report.py off the run folder; write it again rather than editing it. -->"]
    if not stopped:
        lines.append(f"<!-- finished {finished} -->")
    lines.extend(body)
    data = ("\n".join(lines).rstrip() + "\n").encode("utf-8")
    try:
        ledger_script.publish(report, data)
    except (OSError, ledger_script.LedgerError) as e:
        return 1, [f"close_report: the report could not be written: {e}"]
    took = _duration(facts.started(), finished)
    return 0, short_version(short, stopped, finished, took, report)


def ids(folder: Path, project: str) -> list[str]:
    led = read_ledger(folder)
    names = names_known(folder)
    rows: list[str] = []
    questions: list[str] = []
    for note in led["notes"]:
        if note["kind"] not in ("anomaly", "grain", "door", "deviation"):
            continue
        clause = note["clause"]
        if note["kind"] == "anomaly" and LANDED_RE.search(clause):
            continue
        for qid in QUESTION_ID_RE.findall(clause):
            if qid not in names and qid not in questions:
                questions.append(qid)
        for subject in SUBJECT_RE.findall(clause):
            subject = subject.rstrip(".")
            if subject not in names and subject not in rows:
                rows.append(subject)
    room = MAX_IDS
    rows = rows[:room]
    room -= len(rows)
    questions = questions[:max(0, room)]
    calls: list[str] = []

    def call(name: str, verb: str, args: dict) -> None:
        calls.append(f"{name} {verb} {json.dumps(args)}")

    call("questions.json", "list_questions", {"projectId": project, "status": "all", "limit": 0})
    call("packages.json", "solicitation_list_packages", {"projectId": project})
    packages = _json(folder / "plan" / "packages.json")
    package_rows = packages.get("packages") if isinstance(packages, dict) else packages
    for row in package_rows if isinstance(package_rows, list) else []:
        if isinstance(row, dict) and row.get("tradeCode") == GENERAL_REQUIREMENTS_CODE and isinstance(row.get("id"), str):
            call("general-requirements.json", "solicitation_get_package", {"packageId": row["id"]})
            break
    index_lines = [line for line in led["phases"] if line.startswith("phase: index built")]
    if index_lines:
        figures = dict(re.findall(r"([A-Za-z]+) (\d+)", index_lines[-1]))
        for kind in ("codeNoLocation", "codeOnlyOnReplacedPages"):
            if int(figures.get(kind, 0)) > 0:
                call(f"leftover-{kind}.json", "index_citations_leftover", {"projectId": project, "kind": kind, "limit": 50})
    for at in range(0, len(questions), QUESTIONS_PER_CALL):
        call(
            f"questions-named-{at // QUESTIONS_PER_CALL:03d}.json", "list_questions",
            {"projectId": project, "questionIds": questions[at: at + QUESTIONS_PER_CALL]},
        )
    for number, subject in enumerate(rows):
        call(f"name-{number:03d}.json", "search", {"projectId": project, "subject": subject, "predicate": "name"})
    path = folder / "reports" / CALLS_NAME
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        ledger_script.publish(path, "".join(f"{line}\n" for line in calls).encode("utf-8"))
    except (OSError, ledger_script.LedgerError) as e:
        return [f"close_report: the calls file could not be written: {e}; write the report without the copy"]
    return [f"close_report: {len(calls)} calls written to {path}, ids looked up {len(rows) + len(questions)}"]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Write a scope run's closing report off its run folder.")
    modes = parser.add_subparsers(dest="mode", required=True)
    one = modes.add_parser("ids", help="write the calls the copy agent makes for the report's names and counts")
    one.add_argument("run_folder", type=Path)
    one.add_argument("--project", required=True, help="the project id")
    two = modes.add_parser("write", help="write closing-report.md and print the short version")
    two.add_argument("run_folder", type=Path)
    two.add_argument("--delivery-plan", type=Path, help="the delivery's plan file, where the recheck ran")
    two.add_argument("--stopped", help="why the run stopped early, in plain words")
    args = parser.parse_args(argv)
    code = 0
    try:
        if args.mode == "ids":
            lines = ids(args.run_folder, args.project)
        else:
            code, lines = write(args.run_folder, args.delivery_plan, args.stopped)
    except Exception as e:  # nothing raises to the top: the lead reads one line and the exit code
        code, lines = (1 if args.mode == "write" else 0), [f"close_report: {args.mode} failed: {type(e).__name__}: {str(e)[:200]}"]
    for line in lines:
        print(line)
    return code


if __name__ == "__main__":
    sys.exit(main())
