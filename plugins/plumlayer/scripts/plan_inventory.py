"""
plan_inventory.py: turn a fetched sheet grid into plan counts, and the record into a read plan.

The scope run's lead plans the read without ever holding a sheet row. It takes the set's shape from
a summary-only `set_grid` call, sends one agent to put the grid on disk, and then runs this script:
once to turn the grid files into counts it can read, and once per window to write that window's
read plan off the record's own copies on disk.

The script copies field values, counts them, and refuses. It never infers a discipline, never
guesses a page number, and never reads meaning off a title. Which sheets a window reads is decided
by the inventory alone; which packages a run reviews is decided by the packages file alone.

Three subcommands:

  issue      reads the project's run folders and its delivery list, and names in one line what
             the lead does next: resume the pass in flight, wait on a delivery still being read,
             start a pass on the latest set, or nothing (below).

  inventory  reads the grid files, refuses unless the rows total the count the lead read for
             itself, and writes `inventory.md` (one line per sheet, then the count tables and the
             sheet number digest at the tail) and `inventory.json` (the normalized rows).

  plan       reads the window's inputs and writes `read-plan.md` whole: the window's passes, the
             unit lines with their page references, what each pass reads for, what is deliberately
             left out, what a window 2 slice deferred, and the totals.

One pass per drawing issue:

  A project goes through several drawing issues, and each gets a pass of its own in a run folder
  of its own, `<project folder>/<deliveryId>/`. The lead writes `run.json` there before the plan:
  the delivery the pass reads, `readFrom`, the deliveries its sheet list comes from as `set_grid`
  named them, and `unitTag`, `i<n>`, with the count of `scopeItem:i<n>-` it took on the record.
  Every pass id and unit id the plan writes in that folder carries the tag (`i2-A1-3`,
  `i2-RS1-1`, `i2-rev-092116-1`), so no pass records under, or counts, another pass's subjects. A
  tag another run folder of the project carries, or one the record already carries rows under, is
  refused.

  The inventory holds a grid fetched by `deliveryId` to `run.json`: every page must name its
  delivery and read from exactly its deliveries, and every row must come from one of them, so a
  grid of another issue, and one fetched again after a delivery landed, are refused rather than
  planned. A pass reads the sheet list it started on. `inventory.json` then carries
  `drawingIssue`, and each window refuses an inventory whose issue differs from `run.json`.

  A folder with no `run.json` is a pass begun before passes had folders of their own: it plans
  as it always has, untagged, and a grid or an inventory naming a drawing issue is refused there,
  as is any window in a folder holding such an inventory or a ledger of tagged unit ids, since
  that folder is a pass that lost its `run.json`. A window 1 file names the tag it was planned
  under, and window 2 refuses a tag that differs.

  The issue mode resumes before anything else, before it reads the delivery list at all: a run
  folder whose ledger carries no `phase: closed out` line, or the project folder's own ledger in
  the old layout from its first `phase:` line until that line, and two of them in flight is a
  refusal. Then a delivery still being read is waited on,
  since it may yet be a new set. Then the latest set is started where no run folder names it,
  with the next tag past every tag a run folder carries. An earlier set with no pass is never
  started over a later one. Once the latest set has its pass, the earliest addendum of it no pass
  read is started, one at a time in the order they landed, each a partial pass of its own.

A number printed on more than one page:

  A drawing issue can print one sheet number on two of its pages. The grid gives the number one
  row, on its first page, and lists every page it prints on under the row's `pageOccurrences`: the
  row's own page marked `selected`, each further page of the row's own delivery with
  `deliveryId: null` and the key it opens as, `opensAs`, and each page an earlier issue printed
  that the current set keeps beside the number, with that issue's `deliveryId`. The inventory makes
  each further page a sheet of its own, right after its number's row: the row's discipline and
  number, and the page's own file, page, title, sheet type and `opensAs`, under the unit key
  `<sheet>@<fileId>#<page>`. A page of an earlier issue gets no row, since the pass reads its own
  issue; the bounds line counts and names it, as it counts and names each further page.
  `--expect-count` is the grid's `count`, which counts the number once, so it holds against the
  grid's rows. Every window reads a further page as any other sheet, and `--include`, `--exclude`
  and `--only` match the number it prints, so a pattern naming the number takes both pages. Its
  unit line names its file always, then the key it opens as
  (`A2-6. C-5.02, file <fileId>, page 4, opens as <fileId>-p004: <title>`). A dispatch line and a
  left-out list name it by that key, since the number names its first page, so a ledger written
  before further pages were read still binds the number to its first page.

  A run resumed on this script can hold files an earlier one wrote, when the number had one row.
  A window 1 file that left the number out holds its first page's unit key alone, so window 2
  leaves each further page of that number out with it and its bounds line names them, and a pass
  dispatched before a further page took it past twelve keeps its part, as the next section says.

The three windows, and what each selects:

  1  the vocabulary: every sheet whose type is schedule, legend, notes or cover-index, plus what
     `--include` names and minus what `--exclude` names, grouped into passes by discipline, with a
     pass under three units folded into the pass before or after it (below). It also writes
     `plan/window-1.json` in the run folder the `--out` path sits in, holding the unit keys it
     selected and the unit keys it left out, so window 2 subtracts this window rather than
     recomputing it from arguments it might not be given identically, and the `--include` and
     `--exclude` patterns with their reasons, so a resume can run this plan again exactly.
     Beside the vocabulary it plans the repeated lines (below): one unit per drawing file.
  2  every sheet once: every inventory row `plan/window-1.json` does not already name, grouped by
     discipline in inventory order and sorted inside a discipline by sheet type, composition ahead
     of extent, with a pass under three units folded as in window 1. The selection is a partition
     of what window 1 left, so the bounds line states the units planned against the distinct
     sheets they touch, and refuses where the two differ.
     `--only` cuts a run to a slice the user asked for first: the run plans only the sheets window
     1 left whose sheet number matches one of its patterns, and every other sheet window 1 left is
     deferred, not left out, unless the ledger holds its dispatched unit with `result ok`, in
     which case the plan lists it as read earlier. A deferred sheet carries no unit; the next
     plan run of this window without `--only` plans it again. The partition is then planned plus
     read earlier plus deferred, once each; the bounds line adds `plus read earlier <r>` only
     when nonzero, and its deferred count excludes those sheets. The lead uses that count for
     the paused line's `deferred <m>`. Grouping, the type order and the split are unchanged over the
     slice, except that a discipline the whole window would split into lettered parts is lettered
     in the slice too (`A2a` for a slice of six), so the slice's unit ids already name the part
     they sit at the front of when the whole window is planned. Every window 2 run writes
     `plan/window-2.json` beside window 1's file: the unit ids it assigned, each `--only` pattern
     with its reason and the unit keys it selected, the read-earlier keys in `readEarlierKeys`,
     and the deferred unit keys with their count.
  3  one review per package: one pass per row of the packages file, in package order, with the
     packages of one trade kept together. It reads no sheets, so it takes no inventory. In a pass
     on an addendum, whose `run.json` reads `issue: "addendum"`, it reads the pass's own
     `trades/` files beside the plan and plans only the packages covering a trade the pass wrote on, a
     row it created, updated or cited or a Question it raised, naming every other package as left
     out; a pass that wrote on no trade plans no review, and one with no `trades/` folder at all
     is refused.

The repeated lines, in windows 1 and 2:

  A drawing file prints some lines at the same spot on many of its pages: general and plan notes,
  and the fixed part of the title block. `get_page_text` reads them once for the whole file with
  `repeated: "only"`, and leaves them out of one page with `repeated: "omit"`, and it counts a
  line as repeated only where five or more of the file's pages print it. So window 1 plans one
  unit per drawing file holding five or more of the inventory rows the run reads (every row but
  the ones `--exclude` left out), in its own pass `RS1`, split at twelve like every pass and never
  folded: its units read a file, not a sheet. The unit line names the file and the first of those
  rows' pages in inventory order, `RS1-<n>. file <fileId>, from page <page>: repeated lines`,
  followed by `, sheets left out <numbers>` where `--exclude` left some of that file's sheets
  out: the file's repeated lines are read whole, and its reader records nothing from a block
  printed only on those sheets. `plan/window-1.json` carries the units as `repeatedSets`, each
  with its file id, unit id, page and `sheetsLeftOut`, apart from `selected` so window 2's
  subtraction and partition do not change. A discipline whose
  window 1 pass id would be `RS1` is refused, since its unit ids would be the repeated lines'.
  The unit ids keep across a replan as a sheet's do, bound by file id: a ledger line
  `dispatch 1 <pass> RS1-<n> sheets none purpose repeated lines of file <fileId>`, then
  `repeatedSets` in the previous window 1 file, then new numbers. The bounds line and the totals
  block count these units in their own clause, so every sheet count reads as it always has.

  Window 2 ends a unit line with `, repeated lines read in set <version>` where its file's repeated
  lines unit carries a window 1 `verified` line whose last result is `ok`, a
  `note ... set <version>` line naming the set version it read (the last one counts), and no
  `note ... unread` line: a reader on that line leaves the file's repeated lines out of its page
  where its answer names the same version, because they were read once already. Any other unit
  line carries no mark and its reader reads the page whole, so no line a reader leaves out goes
  unread.

Unit ids across a replan, in windows 1 and 2:

  A unit id is a live subject prefix on the project record. A reader records
  `scopeItem:<unit id>-<seq>`, the runner verifies that prefix, and the lead counts it, so an id
  that moved to another sheet on a replan would point at another sheet's work. The plan therefore
  names the unit id on the unit line itself rather than leaving it to be read off the line's
  position, and it keeps every id already handed out. Three tiers, in order:

  1  the run ledger beside the plan file (`ledger.md` in the folder `--out` sits in). Every
     `dispatch <window> <pass> <unit> sheets <...> purpose <...>` line of this window binds that
     unit id to those sheet numbers. Authoritative, because it is the only append-only record of
     what was actually dispatched.
  2  the previous `plan/window-<n>.json`, whose `units` array binds a unit id to an inventory unit
     key. It covers a unit that was planned and never dispatched. Windows 1 and 2 both write that
     file, so a window 2 slice keeps its ids on the next plan run whether or not any of them was
     dispatched. A unit bound by this tier alone whose sheet now plans under a different pass is
     numbered in the part it now sits in and its old id is retired: nothing was dispatched under
     that id, so no record and no run file carries it. A unit the ledger binds is refused there
     instead, since the record already carries rows under its id.
  3  new numbers: the next number after the highest any tier names for that part, taken in the
     window's own natural order. A number any tier named is never handed out again, so a sheet cut
     from the plan leaves its id retired.

  The plan file then lists each part's units by id ascending, so everything already read holds
  the front of the part in the order it was read and new work is appended after it. New units are
  placed in the window's natural order before ids are assigned, so composition still precedes
  extent among the sheets not yet read.

  A pass the ledger dispatched under its own unlettered id (`A2-1`) and that a replan takes past
  twelve, as a further page can, keeps that part: its first twelve units, the bound ones in
  front, stay under `A2`, and the rest split evenly into parts lettered from `b` (`A2b`), so no
  dispatched id changes part. Any other pass over twelve splits into `A2a`, `A2b` and on.

  A window 2 slice and the whole window: on the next full plan the slice's units are bound, so they
  sort to the front of their discipline's pass and keep the part their ids name, as long as the
  units the slices planned in one discipline fit that discipline's first part of the whole window
  (twelve units where the discipline fills its parts, fewer where it splits into smaller ones).
  Past that, a bound unit lands in the next part: one the ledger dispatched is refused rather than
  renumbered, and one the plan file alone binds is renumbered there. A slice holds the ids of its
  deferred sheets differently by tier: a dispatched one keeps its number taken and is not counted
  retired, since it comes back, and the bounds line adds `ids held <h>` when nonzero; a planned
  one is dropped, and the sheet is numbered again when the whole window is planned.

Units already verified, in every window:

  The plan also reads this window's `verified <window> <pass> <unit> ... result ok` lines off the
  same ledger. A unit line whose id carries one ends with ` verified`, and every pass block says
  `units verified: <k>` under `units: <n>`, so a pass is finished unit by unit rather than by its
  `pass:` line: a resume, or a pass that a replan grew, dispatches every pass whose two numbers
  differ, and its runner skips the units already verified. A `verified` line whose result is not
  `ok` marks nothing, and one naming an id this plan neither carries nor holds is ignored rather
  than refused. A held unit verified ok counts as read earlier in a window 2 slice.

Passes already summed, in every window:

  Every unit verified is not enough on its own, because a replan can change which units a pass
  carries after its summary was written: a fold can take in a part whose units another pass
  verified, and a cut can drop units, with the count coming out the same. So every pass block also
  says `summed: yes` or `summed: no, <why>` under `units verified:`. It reads yes when the pass's
  summary on file, `reports/<pass id>.md` in the run folder (`reports/<pass id>-pass.md` in window
  3), names on its `per unit:` lines exactly the unit ids the block carries, and the ledger's last
  `pass: <window> <pass id>` line carries that summary's figures: its units count, and the
  updated, questions and replied totals the lead copies off it. A pass reading no is summed again:
  its runner skips the units already verified and writes a new summary. The reasons it names:

      summed: no, no summary on file
      summed: no, the summary on file reads other units: without <ids>; beyond <ids>
      summed: no, the summary on file carries no totals line
      summed: no, no pass line on the ledger
      summed: no, the last pass line does not carry the summary on file

Passes under three units, in windows 1 and 2:

  A runner pays a fixed cost before its first unit, so a part under three units folds into a
  neighbouring pass rather than starting a runner of its own. Once each discipline's pass is split
  at twelve and its unit ids are bound, the window's parts are walked in plan order: a part joins
  the pass being built where either side of the join is under three units and the joined pass
  stays at twelve or fewer, and starts a new pass otherwise. So a small part joins the pass before
  it, and where that pass is full it starts a pass of its own and takes in the part after it on
  the same terms; one that fits neither reads alone, and the bounds line names it as kept. A part
  under three is always a whole discipline, since a split part holds at least six, so every fold
  makes a pass that carries more than one discipline. A pass holds at most one part of three or
  more, and that part gives the pass its id; a pass with none takes its first part's id. The fold
  groups parts and never renumbers one: a folded unit keeps the id its own discipline's part gave
  it, the parts read one after another in plan order, and the pass block names each part folded
  in. Nothing about the fold is stored; every plan run folds again from its own parts. Window 3
  never folds: a review is its own pass, and its pass id is its unit id.

Usage:

    python plan_inventory.py issue --runs <project folder> --deliveries <path>

    python plan_inventory.py inventory --grid <dir or file> --expect-count 209 --out-dir <dir>

    python plan_inventory.py plan --window 1 --inventory <path>
        [--include <pattern>:<reason>] [--exclude <pattern>:<reason>] --out <path>

    python plan_inventory.py plan --window 2 --inventory <path> --window-1 <path>
        [--only <pattern>:<reason>] --out <path>

    python plan_inventory.py plan --window 3 --packages <path> --out <path>

Input shapes, named here so a change on the record's side surfaces as a named field rather than as
an empty plan:

  --packages  a `solicitation_list_packages` response: a `packages` array whose rows carry
              `tradeCode`, and optionally `id`, `name` and `codes`. Two packages carrying one trade
              is ordinary here: both plan a review, and the plan places them one after the
              other.
  --window-1  the file window 1 wrote: `selected` and `excluded`, both arrays of inventory unit
              keys, and `repeatedSets`, which may be absent. Its other fields are this script's own
              bookkeeping and window 2 reads none. A key the inventory does not hold, or a
              repeated lines unit naming a file the inventory does not hold, is a refusal, since a
              file from some other run would leave a sheet unread with nothing said about it.
  ledger.md   found beside the plan file, never named by an argument, and absent on a first plan
              run. A flag would be a flag the lead can forget, and forgetting it is the failure
              this reading exists to prevent.
  reports/    the pass summaries the runners wrote, found beside the ledger the same way. Only a
              summary's `per unit:` lines and its `totals verified:` line are read, and a pass
              with no summary on file, or one whose summary carries no totals line, reads
              `summed: no` with that reason rather than refusing.

Exit codes:
  0  wrote the files; one bounds line on stdout naming what it read and what it wrote.
  1  a named failure, one line on stderr: a file that does not parse, a row total that does not
     match `--expect-count`, two rows folding to one unit key, a missing window input, an argument
     some other window takes, an input row with no `tradeCode`, a window 1 file naming a unit key
     the inventory does not hold or naming one as both selected and excluded, an `--include`,
     `--exclude` or `--only` with no colon or matching no sheet it may select, an inventory file
     this script did not write, a window 2 plan whose planned and deferred sheets are not a
     partition of what window 1 left, a discipline whose window 1 pass id would be `RS1`, and a
     window 1 file whose `repeatedSets` is malformed or names a file the inventory does not hold.
     Three more are about a repeated lines unit's dispatch line: one naming no file after
     `of file`, one unit id bound to two files, and one file bound to two unit ids. Six are about
     a unit id already handed out: a ledger dispatch line for this window whose unit id is not
     `<pass>-<number>`, one sheet number bound to two unit ids, one unit id bound to two sheet
     sets, a bound sheet number matching more than one inventory row, a bound unit whose sheet set
     this plan does not read as one unit of its own, and a unit the ledger binds whose sheet now
     plans under a different pass id. The rest are about a drawing issue: a `run.json` that is
     malformed, names a misshapen or taken tag, has no count of it from the record, or names a
     drawing issue another run folder names; a grid page naming another delivery, other
     deliveries, or none, or a row from a delivery the pass does not read from; a grid or an
     inventory naming a drawing issue in a folder with no `run.json`, and any window in a folder
     with no `run.json` that holds such an inventory or a ledger of tagged unit ids; an inventory
     whose issue differs from `run.json`; a window 1 file planned under another tag; a delivery
     list with no array, a delivery that is neither a set nor an addendum, or one whose
     `stillReading` is not true or false; window 3 of a pass on an addendum with no `trades/`
     folder, or a trades line of neither known shape; two passes in flight; and a run folder holding a ledger
     and no `run.json`, or a `run.json` the issue mode cannot read. Another pass's broken
     `run.json` never stops a plan. Seven are about a number printed on more than one page: a
     grid row with no `pageOccurrences` list, a list naming no page or more than one as the row's
     own, an own page that is not the row's file and page, a page with no `deliveryId` field or one
     that is neither null nor a delivery id, a further page with no file, key or page, one file and
     page listed twice, and a further page that is already another row's page.
  2  argparse rejected the invocation.

Grounding role: reads files and copies byte values. A file that does not parse whole is a refusal,
not a salvage: a partial recovery of a grounded read is worse than no read at all.
"""

from __future__ import annotations

import argparse
import fnmatch
import json
import math
import os
import re
import string
import sys
from pathlib import Path

# The six grid fields the plan needs. A grid row carries about thirty; the rest are dropped here so
# nothing downstream can quietly come to depend on a field the plan never reasoned about. Its
# `pageOccurrences` is read once, for its further pages, and dropped with the rest.
ROW_FIELDS = ("discipline", "sheetNumber", "pageTitle", "sheetType", "fileId", "pageInPdf")

# The `scope-round-runner` stops a pass above twelve units, so a plan that emits a bigger pass is a
# plan defect rather than a big pass.
UNITS_PER_PASS = 12

# A runner pays a fixed cost before its first unit (its brief, the plan, its verification setup), so
# a part under this many units folds into a neighbouring pass rather than starting a runner alone.
MIN_PASS_UNITS = 3

PREFIX_GROUP_CAP = 60
TITLES_PER_PREFIX = 3
MAX_NAMED = 5

NO_DISCIPLINE = "(none)"
UNTYPED = "(untyped)"

# Window 1 reads what the set says its own marks mean. These four are single recognizer types, so
# the list is exact rather than a family of near names.
VOCABULARY_SHEET_TYPES = ("schedule", "legend", "notes", "cover-index")

# The name this script gives a row the recognizer left untyped, so the type order can place it.
UNTYPED_SHEET_TYPE = "untyped"

# Window 2 reads every remaining sheet once, and inside a discipline it reads in this order:
# composition before extent. A section or a detail shows what an assembly is made of, which is the
# row a subcontractor prices; a plan shows where it occurs. The first reader to see a piece of work
# creates its row and every later reader updates it, so the sheet that should create is the one
# that writes the better row. `other` and untyped go last: neither says what it holds, so neither
# is a sheet to create the vocabulary of the set from.
#
# This is a constant, never a setting a user picks and never a model's judgment.
WINDOW_2_SHEET_TYPE_ORDER = (
    "section", "detail", "elevation", "RCP", "enlarged-plan",
    "plan", "overall-plan", "schematic", "other", UNTYPED_SHEET_TYPE,
)
_WINDOW_2_TYPE_RANK = {name: index for index, name in enumerate(WINDOW_2_SHEET_TYPE_ORDER)}

SELECT_KEYS = {"discipline", "sheetTypes", "patterns"}

# The repeated lines pass. `get_page_text` counts a line as repeated where five or more of its
# file's pages print it, so a file with fewer rows than that plans no unit: no window 2 unit on it
# is marked, and each of its sheets is read whole.
REPEATED_PASS_ID = "RS1"
REPEATED_MIN_ROWS = 5
REPEATED_READS_FOR = "the repeated lines"
REPEATED_MARK = ", repeated lines read"
# A repeated lines unit id's pass component: the pass, or one lettered part of it, under a unit tag
# where the pass carries one.
_REPEATED_PART_RE = re.compile(r"^(?:i[1-9][0-9]*-)?RS1[a-z]?$")
# The key a repeated lines unit binds under. A sheet's unit key always joins three fields with `@`
# and `#`, so this one never meets a sheet's in the one binding it takes part in, which is its own.
_REPEATED_KEY_PREFIX = "repeated lines@"

WINDOW_1_FILE = ("plan", "window-1.json")

# The run ledger sits beside the plan file, and its `dispatch` lines are the only append-only
# record of which unit id was actually handed out.
LEDGER_FILE = "ledger.md"

# A pass on one drawing issue keeps this file in its run folder, written by the lead before the
# plan: the delivery the pass reads, the deliveries its sheet list comes from, and its unit tag.
RUN_FILE = "run.json"

# A unit tag is a lowercase `i` and a number from 1. A discipline pass id is upper case, so no
# untagged unit id starts with a tag, and the record's subject prefix match is case-sensitive.
_UNIT_TAG_RE = re.compile(r"^i[1-9][0-9]*$")

# The line a closed pass's ledger ends on, and the prefix of every line that marks a phase.
CLOSED_OUT_LINE = "phase: closed out"
PHASE_PREFIX = "phase:"

# Where a pass runner writes its summary, beside the ledger. A window 3 pass id is also its unit
# id, so its summary carries a suffix the review's own report does not.
REPORTS_FOLDER = "reports"
WINDOW_3_SUMMARY_SUFFIX = "-pass"

# The figures a `pass:` line copies off the summary, and the totals line they are read from.
PASS_LINE_FIGURES = ("units", "updated", "questions", "replied")
_SUMMARY_TOTALS_RE = re.compile(r"updated (\d+), questions (\d+) replied (\d+)")

# A unit id is a pass id, a hyphen, and a positive number. The pass id may itself carry a hyphen
# (a window 3 review id does), so the number is taken off the end.
_UNIT_ID_RE = re.compile(r"^(?P<pass>\S+)-(?P<number>[1-9][0-9]*)$")


class PlanError(Exception):
    """A named failure with a one-line reason, reported on stderr and exiting 1."""


# --------------------------------------------------------------------------- #
# Shared helpers
# --------------------------------------------------------------------------- #

def _read_json(path: Path, what: str):
    """
    Parse the whole file or refuse. There is deliberately no scan for an embedded object and no
    line-by-line salvage: a grid file that is half readable is a truncated grounded read, and the
    only safe thing to do with one is stop.
    """
    try:
        text = path.read_text(encoding="utf-8")
    except Exception as e:
        raise PlanError(f"cannot read {what} at {path}: {e}") from e
    try:
        return json.loads(text)
    except json.JSONDecodeError as e:
        raise PlanError(f"{path} is not whole JSON: {e}") from e


def _write_atomically(out: Path, payload: bytes) -> None:
    """Write beside the target and rename, so a run that dies mid-write leaves no partial file."""
    try:
        out.parent.mkdir(parents=True, exist_ok=True)
        tmp = out.with_name(out.name + ".tmp")
        tmp.write_bytes(payload)
        os.replace(tmp, out)
    except Exception as e:
        raise PlanError(f"cannot write {out}: {e}") from e


def _named(items: list[str]) -> str:
    """The first few offenders plus a count, so a refusal stays one line however many there are."""
    if len(items) <= MAX_NAMED:
        return "; ".join(items)
    return "; ".join(items[:MAX_NAMED]) + f"; and {len(items) - MAX_NAMED} more"


def _text(value) -> str:
    return "" if value is None else str(value)


def _sheet_name(row: dict) -> str:
    """
    The name a ledger line and a left-out list give a sheet: its sheet number, or for a further
    page of a number printed on more than one page, the key it opens as. An inventory written
    before further pages were read carries no `opensAs`, and every row of it is named by number.
    """
    return _text(row.get("opensAs")) or _text(row.get("sheetNumber"))


def _fold(code: str) -> str:
    """
    A trade code with its spaces removed, lower cased. The catalog spaces its ids and a package
    row may space them differently, and this is the same fold the record's own catalog lookup uses,
    so the two agree.
    """
    return "".join(code.split()).lower()


def _pack(code: str) -> str:
    """A trade code with its spaces out, its own casing kept. This is what a unit id carries."""
    return "".join(code.split())


def _tagged(pass_id: str, tag: str | None) -> str:
    """A pass id under the pass's unit tag, or as it is where the run folder carries none."""
    return f"{tag}-{pass_id}" if tag else pass_id


def _read_run(folder: Path) -> dict | None:
    """
    The run file in a run folder, or None where the folder holds none, as a run in the old layout
    does. The lead writes it before the plan, so everything here is checked rather than trusted:
    the delivery and the deliveries the sheet list comes from, which the inventory and the plan are
    held to, and the unit tag every unit id of the pass carries.

    A tag is refused where the lead's own count of `scopeItem:<tag>-` on the record is missing or
    above zero, and where another run folder of the project already carries it: either way a unit
    of this pass would record under, or be counted with, another pass's subjects.
    """
    path = folder / RUN_FILE
    if not path.is_file():
        return None
    data = _read_json(path, "the run file")
    if not isinstance(data, dict):
        raise PlanError(f"{path} is not a run file object")
    delivery_id = data.get("deliveryId")
    if not isinstance(delivery_id, str) or not delivery_id:
        raise PlanError(f"{path} names no `deliveryId`, the drawing issue the pass reads")
    if data.get("issue") not in ("set", "addendum"):
        raise PlanError(f"{path}: `issue` is {data.get('issue')!r}, not set or addendum as the delivery list reads it")
    read_from = data.get("readFrom")
    if (
        not isinstance(read_from, list)
        or not all(isinstance(d, str) and d for d in read_from)
        or len(set(read_from)) != len(read_from)
        or delivery_id not in read_from
    ):
        raise PlanError(
            f"{path}: `readFrom` is not a list of distinct delivery ids naming {delivery_id} itself"
        )
    tag = data.get("unitTag")
    if not isinstance(tag, str) or not _UNIT_TAG_RE.match(tag):
        raise PlanError(f"{path}: unit tag {tag!r} is not a lowercase i and a number from 1")
    check = data.get("unitTagCheck")
    prefix = f"scopeItem:{tag}-"
    if (
        not isinstance(check, dict)
        or check.get("subjectPrefix") != prefix
        # A JSON true or false reads as a number in Python, and neither is a count.
        or isinstance(check.get("count"), bool)
        or not isinstance(check.get("count"), int)
    ):
        raise PlanError(
            f"{path}: unit tag {tag} carries no count of `{prefix}` taken on the record before the plan"
        )
    if check["count"] != 0:
        raise PlanError(
            f"{path}: the record already carries {check['count']} rows under `{prefix}`, so unit tag "
            f"{tag} is taken; take the next number and count it again"
        )
    here = folder.resolve()
    for sibling in sorted(folder.parent.iterdir()):
        other = sibling / RUN_FILE
        if sibling.resolve() == here or not other.is_file():
            continue
        try:
            other_data = _read_json(other, "another pass's run file")
        except PlanError:
            # Another pass's broken run file is that pass's to fix, and the issue mode names it; it
            # never stops this pass, whose tag the record count already showed free.
            continue
        if not isinstance(other_data, dict):
            continue
        if other_data.get("unitTag") == tag:
            raise PlanError(
                f"unit tag {tag} is also the tag of the pass in {sibling}; each pass on the project "
                f"takes its own"
            )
        if other_data.get("deliveryId") == delivery_id:
            raise PlanError(
                f"drawing issue {delivery_id} is also the issue of the pass in {sibling}; a drawing "
                f"issue gets one pass"
            )
    return {
        "deliveryId": delivery_id,
        "label": _text(data.get("label")) or delivery_id,
        "issue": data["issue"],
        "readFrom": read_from,
        "unitTag": tag,
    }


def _require_keys(obj, allowed: set[str], where: str) -> None:
    if not isinstance(obj, dict):
        raise PlanError(f"{where} is not an object")
    unknown = sorted(set(obj) - allowed)
    if unknown:
        raise PlanError(f"{where} carries unknown key(s): {', '.join(unknown)}")


# --------------------------------------------------------------------------- #
# inventory
# --------------------------------------------------------------------------- #

def _grid_files(grid: Path) -> list[Path]:
    if grid.is_file():
        return [grid]
    if grid.is_dir():
        files = sorted(p for p in grid.iterdir() if p.is_file())
        if not files:
            raise PlanError(f"no grid files in {grid}")
        return files
    raise PlanError(f"no grid file or directory at {grid}")


def _read_grid_pages(files: list[Path]) -> list[tuple[Path, list, int | None, dict | None, dict | None]]:
    """
    Each grid file as (path, rows, offset, discipline counts, drawing issue). The drawing issue is
    what a `set_grid` call by `deliveryId` names on `delivery` and `readFrom`, and None on a call
    for the current set, which names neither.
    """
    pages: list[tuple[Path, list, int | None, dict | None, dict | None]] = []
    for path in files:
        obj = _read_json(path, "a grid file")
        if isinstance(obj, list):
            pages.append((path, obj, None, None, None))
            continue
        if not isinstance(obj, dict):
            raise PlanError(f"{path} is neither a grid response object nor an array of rows")
        rows = obj.get("sheets")
        if not isinstance(rows, list):
            raise PlanError(f"{path} is a grid response with no `sheets` array")
        offset = obj.get("offset") if isinstance(obj.get("offset"), int) else None
        reported = obj.get("disciplineCounts")
        issue = None
        if obj.get("delivery") is not None:
            delivery = obj["delivery"]
            read_from = obj.get("readFrom")
            if (
                not isinstance(delivery, dict)
                or not isinstance(delivery.get("id"), str)
                or not isinstance(read_from, list)
                or not all(isinstance(d, dict) and isinstance(d.get("id"), str) for d in read_from)
            ):
                raise PlanError(
                    f"{path} names a drawing issue with no delivery id, or no `readFrom` list of "
                    f"the deliveries its rows came from"
                )
            issue = {"deliveryId": delivery["id"], "readFrom": [d["id"] for d in read_from]}
        pages.append((path, rows, offset, reported if isinstance(reported, dict) else None, issue))
    return pages


def _grid_issue(pages: list, run: dict | None, out_dir: Path) -> dict | None:
    """
    The drawing issue the grid on disk was fetched for, held to the run file. A pass reads the
    sheet list it started on, so a grid fetched for another issue, one fetched again after a
    delivery landed since the run file was written, and one carrying a row from a delivery the
    pass does not read from are each refused rather than planned. A grid fetched for one issue
    into a folder with no run file is refused too: nothing would then tag its unit ids.
    """
    if run is None:
        named = next((page for page in pages if page[4] is not None), None)
        if named is not None:
            raise PlanError(
                f"{named[0]} was fetched for drawing issue {named[4]['deliveryId']}, and {out_dir} "
                f"holds no {RUN_FILE} naming the pass on it"
            )
        return None
    wanted = run["readFrom"]
    for path, rows, _offset, _reported, issue in pages:
        if issue is None:
            raise PlanError(
                f"{path} names no drawing issue: the pass on {run['deliveryId']} fetches its grid "
                f"with set_grid's deliveryId"
            )
        if issue["deliveryId"] != run["deliveryId"]:
            raise PlanError(
                f"{path} was fetched for drawing issue {issue['deliveryId']}, and {RUN_FILE} names "
                f"{run['deliveryId']}"
            )
        extra = [d for d in issue["readFrom"] if d not in wanted]
        missing = [d for d in wanted if d not in issue["readFrom"]]
        if extra or missing:
            differences = [f"reads from {', '.join(extra)} as well"] if extra else []
            differences += [f"does not read from {', '.join(missing)}"] if missing else []
            raise PlanError(
                f"{path} {' and '.join(differences)}, against the deliveries {RUN_FILE} names: the "
                f"deliveries changed since {RUN_FILE} was written, and a pass reads the sheet list "
                f"it started on"
            )
        for row in rows:
            source = row.get("deliveryId") if isinstance(row, dict) else None
            if source not in wanted:
                sheet = _text(row.get("sheetNumber")) if isinstance(row, dict) else ""
                came = f"comes from delivery {source}" if source else "names no delivery"
                raise PlanError(
                    f"{path}: sheet {sheet or '(no sheet number)'} {came}, which the pass on "
                    f"{run['deliveryId']} does not read from"
                )
    return {"deliveryId": run["deliveryId"], "readFrom": list(wanted)}


def _order_pages(pages: list) -> tuple[list, str]:
    """
    Grid order is the order the rows are read in, so the pages are put back in the order the grid
    handed them out: by the `offset` each response carries where every page has one, and by file
    name otherwise.
    """
    if pages and all(p[2] is not None for p in pages):
        return sorted(pages, key=lambda p: p[2]), "the `offset` each grid response carries"
    return sorted(pages, key=lambda p: p[0].name), "grid file name, since not every page carried an `offset`"


def _check_unit_keys(rows: list[dict], where: str) -> None:
    """
    Every window subtracts and selects by the unit key string, not by the three fields it is built
    from, so two rows that fold to one key are one row from there on. Window 1 puts the shared key
    in its `selected` list, and window 2's `key not in window_1_keys` filter then drops BOTH rows,
    including the one window 1 never selected. Its partition check cannot see it either, because
    neither row ever reaches the remainder for the count to disagree on. So the collision is refused
    here, before any window subtracts or selects, and both rows are named: a sheet that vanishes
    with nothing said about it is the failure this script exists to prevent.

    A collision needs a `@` or a `#` inside a sheet number or a file id, which is why nothing has
    hit it. Both are opaque strings from upstream and neither is validated anywhere, which is why
    the assumption is checked rather than trusted.
    """
    first: dict[str, str] = {}
    collisions: list[str] = []
    for row in rows:
        key = _text(row.get("unitKey"))
        described = (
            f"sheet {_text(row.get('sheetNumber')) or '(none)'}, "
            f"file {_text(row.get('fileId')) or '(none)'}, "
            f"page {_text(row.get('pageInPdf')) or '(none)'}"
        )
        if key in first:
            collisions.append(f"{key} is both [{first[key]}] and [{described}]")
        else:
            first[key] = described
    if collisions:
        raise PlanError(
            f"{where} carries {len(collisions)} colliding unit key(s), so a row would be dropped "
            f"with nothing said about it: {_named(collisions)}"
        )


def _further_pages(
    path: Path, row: dict, raw: dict, owner: dict[tuple[str, str], str]
) -> tuple[list[dict], list[dict]]:
    """
    A grid row's further pages, each a row of its own, and the pages of an earlier issue it lists.

    `pageOccurrences` lists every page the row's number prints on, the row's own page marked
    `selected`, once the number prints on more than one. A further page of the row's own delivery
    carries `deliveryId: null` and is a sheet of its own: it takes the row's discipline and number,
    and its own file, page, title, sheet type and the key it opens as. A page an earlier issue
    printed carries that issue's `deliveryId`; the pass reads its own issue, so that page gets no
    row and is named instead. `owner` maps each page some row already stands on to who stands on
    it, and takes in each further page as it is placed.
    """
    number = _text(row["sheetNumber"]) or "(no sheet number)"
    occurrences = raw.get("pageOccurrences")
    if not isinstance(occurrences, list) or not all(isinstance(o, dict) for o in occurrences):
        raise PlanError(
            f"{path}: sheet {number} carries no `pageOccurrences` list, so nothing says whether its "
            f"number prints on another page"
        )
    if not occurrences:
        return [], []
    own = [o for o in occurrences if o.get("selected") is True]
    if len(own) != 1:
        raise PlanError(
            f"{path}: sheet {number} lists {len(occurrences)} pages under `pageOccurrences` and "
            f"{len(own) or 'none'} of them as its own page; one page is the number's own"
        )
    here = (_text(row["fileId"]), _text(row["pageInPdf"]))
    named = (_text(own[0].get("fileId")), _text(own[0].get("pageInPdf")))
    if named != here:
        raise PlanError(
            f"{path}: sheet {number} is on file {here[0] or '(none)'}, page {here[1] or '(none)'}, and "
            f"`pageOccurrences` names file {named[0] or '(none)'}, page {named[1] or '(none)'} as its "
            f"own page"
        )

    listed = {here}
    further: list[dict] = []
    carried: list[dict] = []
    for occurrence in occurrences:
        if occurrence is own[0]:
            continue
        file_id = occurrence.get("fileId")
        page = occurrence.get("pageInPdf")
        # The field says whose page this is, so it is read and never defaulted: null is the row's
        # own issue, a delivery id is an earlier issue's, and anything else names neither.
        where = f"file {_text(file_id) or '(none)'}, page {_text(page) or '(none)'}"
        if "deliveryId" not in occurrence:
            raise PlanError(
                f"{path}: sheet {number} lists {where} under `pageOccurrences` with no `deliveryId`, "
                f"so nothing says whether that page is of this issue or an earlier one"
            )
        delivery = occurrence["deliveryId"]
        if delivery is not None and (not isinstance(delivery, str) or not delivery.strip()):
            raise PlanError(
                f"{path}: sheet {number} lists {where} under `pageOccurrences` with a `deliveryId` "
                f"that is neither null nor a delivery id: {delivery!r}"
            )
        if delivery is None:
            missing = [
                what for what, ok in (
                    ("file", isinstance(file_id, str) and file_id != ""),
                    ("key it opens as", isinstance(occurrence.get("opensAs"), str) and occurrence["opensAs"] != ""),
                    # A JSON true reads as a number in Python, and it is no page.
                    ("page number", isinstance(page, int) and not isinstance(page, bool) and page > 0),
                ) if not ok
            ]
            if missing:
                raise PlanError(
                    f"{path}: sheet {number} prints on a further page with no "
                    f"{' and no '.join(missing)}, so that page cannot be read as a sheet of its own"
                )
        place = (_text(file_id), _text(page))
        if place in listed:
            raise PlanError(
                f"{path}: sheet {number} lists file {place[0] or '(none)'}, page {place[1] or '(none)'} "
                f"twice under `pageOccurrences`"
            )
        listed.add(place)
        if delivery is not None:
            carried.append(
                {"sheetNumber": number, "fileId": file_id, "pageInPdf": page, "deliveryId": delivery}
            )
            continue
        if place in owner:
            raise PlanError(
                f"{path}: sheet {number} prints on file {place[0]}, page {place[1]}, which is already "
                f"the page of {owner[place]}; a page is read once"
            )
        owner[place] = f"a further page of sheet {number}"
        further.append(
            {
                "discipline": row["discipline"],
                "sheetNumber": row["sheetNumber"],
                "pageTitle": occurrence.get("title"),
                "sheetType": occurrence.get("sheetType"),
                "fileId": file_id,
                "pageInPdf": page,
                "unitKey": f"{_text(row['sheetNumber'])}@{file_id}#{page}",
                "opensAs": occurrence["opensAs"],
            }
        )
    return further, carried


def _normalize_rows(pages: list) -> tuple[list[dict], list[str], list[dict], list[dict]]:
    """
    The grid's rows in grid order with duplicates dropped, each further page of a number printed on
    more than one page right after its number's row (`_further_pages`). Returns the rows, the
    duplicates, the further pages, and the pages of an earlier issue left out.
    """
    seen: set[tuple[str, str, str]] = set()
    grid_rows: list[tuple[Path, dict, dict]] = []
    duplicates: list[str] = []
    for path, page_rows, _offset, _reported, _issue in pages:
        for raw in page_rows:
            if not isinstance(raw, dict):
                raise PlanError(f"{path} carries a row that is not an object")
            row = {field: raw.get(field) for field in ROW_FIELDS}
            key = (_text(row["sheetNumber"]), _text(row["fileId"]), _text(row["pageInPdf"]))
            if key in seen:
                duplicates.append(f"{_text(row['sheetNumber']) or '(no sheet number)'} in {path.name}")
                continue
            seen.add(key)
            row["unitKey"] = f"{key[0]}@{key[1]}#{key[2]}"
            row["opensAs"] = None
            grid_rows.append((path, row, raw))

    # Every page a grid row stands on, so a further page that is already a row's page is refused
    # rather than read twice under two unit keys.
    owner: dict[tuple[str, str], str] = {}
    for _path, row, _raw in grid_rows:
        place = (_text(row["fileId"]), _text(row["pageInPdf"]))
        if all(place):
            owner.setdefault(place, f"sheet {_text(row['sheetNumber']) or '(no sheet number)'}")

    rows: list[dict] = []
    further: list[dict] = []
    carried: list[dict] = []
    for path, row, raw in grid_rows:
        rows.append(row)
        row_further, row_carried = _further_pages(path, row, raw, owner)
        rows.extend(row_further)
        further.extend(row_further)
        carried.extend(row_carried)
    _check_unit_keys(rows, "the grid on disk")
    return rows, duplicates, further, carried


def _placeable(row: dict) -> bool:
    return _text(row["sheetNumber"]) != "" and _text(row["pageInPdf"]) != ""


def _stem(sheet_number: str) -> str:
    """
    The literal string before the last dot group, with nothing read into it. A sheet number with no
    dot in it is its own stem, which is why the digest names the disciplines where that produced one
    group per sheet rather than letting the lead read structure into a list that has none.
    """
    return sheet_number.rsplit(".", 1)[0] if "." in sheet_number else sheet_number


def _ordered_counts(rows: list[dict]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for row in rows:
        key = _text(row["discipline"]) or NO_DISCIPLINE
        counts[key] = counts.get(key, 0) + 1
    return counts


def _cross_tab(rows: list[dict]) -> tuple[dict[str, dict[str, int]], list[str]]:
    table: dict[str, dict[str, int]] = {}
    types: list[str] = []
    for row in rows:
        discipline = _text(row["discipline"]) or NO_DISCIPLINE
        sheet_type = _text(row["sheetType"]) or UNTYPED
        if sheet_type not in types:
            types.append(sheet_type)
        table.setdefault(discipline, {})
        table[discipline][sheet_type] = table[discipline].get(sheet_type, 0) + 1
    return table, types


def _prefix_digest(rows: list[dict]) -> tuple[list[dict], bool, list[str]]:
    """
    Per discipline, the distinct sheet number stems with their counts and a few verbatim titles.
    This is a projection, not a summary: it decides nothing and paraphrases nothing.
    """
    groups: dict[tuple[str, str], dict] = {}
    for row in rows:
        discipline = _text(row["discipline"]) or NO_DISCIPLINE
        number = _text(row["sheetNumber"])
        key = (discipline, _stem(number))
        group = groups.setdefault(key, {"discipline": discipline, "stem": key[1], "count": 0, "titles": []})
        group["count"] += 1
        title = _text(row["pageTitle"])
        if title and title not in group["titles"] and len(group["titles"]) < TITLES_PER_PREFIX:
            group["titles"].append(title)

    ordered = list(groups.values())
    capped = len(ordered) > PREFIX_GROUP_CAP

    per_discipline_rows = _ordered_counts(rows)
    per_discipline_groups: dict[str, int] = {}
    for group in ordered:
        per_discipline_groups[group["discipline"]] = per_discipline_groups.get(group["discipline"], 0) + 1
    # A discipline whose stems number one per sheet carries no stem structure to group on. Named so
    # the lead reads that plainly instead of reading structure into a list that has none. A
    # single-sheet discipline is not evidence of that either way, so it is left out.
    ungrouped = [
        d for d, n in per_discipline_groups.items()
        if n == per_discipline_rows.get(d) and per_discipline_rows.get(d, 0) > 1
    ]

    return ordered[:PREFIX_GROUP_CAP], capped, ungrouped


def _inventory_markdown(
    rows: list[dict],
    unplaceable: list[dict],
    order_rule: str,
    reported: dict[str, list[int]],
    digest: list[dict],
    capped: bool,
    ungrouped: list[str],
    further: int,
) -> str:
    counts = _ordered_counts(rows)
    table, types = _cross_tab(rows)
    lines: list[str] = []

    lines.append("# Plan inventory")
    lines.append("")
    lines.append("Written by scripts/plan_inventory.py off the grid files the fetch put on disk.")
    lines.append(f"Rows are in grid order, ordered across pages by {order_rule}.")
    lines.append("The count tables and the sheet number digest are at the tail of this file.")
    lines.append("")
    lines.append("## Sheets")
    lines.append("")
    lines.append("discipline | sheet number | title | sheet type | file | page")
    lines.append("")
    for row in rows:
        lines.append(
            " | ".join(
                [
                    _text(row["discipline"]) or NO_DISCIPLINE,
                    _text(row["sheetNumber"]),
                    _text(row["pageTitle"]),
                    _text(row["sheetType"]) or UNTYPED,
                    _text(row["fileId"]),
                    _text(row["pageInPdf"]),
                ]
            )
        )

    if unplaceable:
        lines.append("")
        lines.append("## Rows the grid could not place")
        lines.append("")
        lines.append("A row with no sheet number or no page number. Named here rather than guessed at,")
        lines.append("and left out of the tables and out of inventory.json's sheet list.")
        lines.append("")
        for row in unplaceable:
            lines.append(
                " | ".join(
                    [
                        _text(row["discipline"]) or NO_DISCIPLINE,
                        _text(row["sheetNumber"]) or "(no sheet number)",
                        _text(row["pageTitle"]),
                        _text(row["fileId"]),
                        _text(row["pageInPdf"]) or "(no page)",
                    ]
                )
            )

    lines.append("")
    lines.append("## Sheets by discipline")
    lines.append("")
    lines.append("discipline | rows | reported by the grid")
    for discipline, n in counts.items():
        said = reported.get(discipline)
        said_text = "not reported" if not said else " / ".join(str(v) for v in said)
        lines.append(f"{discipline} | {n} | {said_text}")
    lines.append(f"total | {len(rows)} |")
    # The grid counts a number printed on more than one page once, so the two columns differ by
    # these pages, and this line says how many.
    lines.append(
        "The counts take each further page of a number printed on more than one page as a sheet of "
        f"its own: {further} further page{'' if further == 1 else 's'}."
    )
    lines.append("")
    lines.append("Where the two columns differ, both are shown. Nothing here reconciles them.")

    lines.append("")
    lines.append("## Sheets by discipline and sheet type")
    lines.append("")
    lines.append("discipline | " + " | ".join(types))
    for discipline in counts:
        row_counts = table.get(discipline, {})
        lines.append(discipline + " | " + " | ".join(str(row_counts.get(t, 0)) for t in types))

    lines.append("")
    lines.append("## Sheet number digest")
    lines.append("")
    lines.append("Per discipline, the distinct sheet number stems: the literal string before the last")
    lines.append("dot group, with nothing read into it. A sheet number carrying no dot is its own stem.")
    lines.append(f"Titles are verbatim, at most {TITLES_PER_PREFIX} per stem.")
    if capped:
        lines.append(f"Capped at {PREFIX_GROUP_CAP} stems; the set has more, and the rest are not shown here.")
    else:
        lines.append(f"Cap is {PREFIX_GROUP_CAP} stems and this set did not reach it.")
    if ungrouped:
        lines.append(
            "One stem per sheet, so the numbering carries no stem structure to group on, in: "
            + ", ".join(ungrouped)
        )
    lines.append("")
    for group in digest:
        titles = "; ".join(group["titles"]) if group["titles"] else "(no titles)"
        lines.append(f"{group['discipline']} | {group['stem']} | {group['count']} | {titles}")

    return "\n".join(lines) + "\n"


def inventory(grid: Path, expect_count: int, out_dir: Path) -> str:
    files = _grid_files(grid)
    pages, order_rule = _order_pages(_read_grid_pages(files))
    issue = _grid_issue(pages, _read_run(out_dir), out_dir)
    rows, duplicates, further, carried = _normalize_rows(pages)

    # `--expect-count` is the grid's own `count`, which counts a number printed on more than one
    # page once, so it is held against the grid's rows and never against the further pages.
    grid_rows = len(rows) - len(further)
    if grid_rows != expect_count:
        raise PlanError(
            f"the grid on disk holds {grid_rows:,} rows after dedupe and --expect-count says "
            f"{expect_count:,}; nothing written. The fetch dropped a page, truncated one, or "
            f"copied a stale file"
        )

    placeable = [r for r in rows if _placeable(r)]
    unplaceable = [r for r in rows if not _placeable(r)]

    reported: dict[str, list[int]] = {}
    for _path, _rows, _offset, page_reported, _issue in pages:
        if not page_reported:
            continue
        for key, value in page_reported.items():
            if not isinstance(value, int):
                continue
            seen = reported.setdefault(str(key), [])
            if value not in seen:
                seen.append(value)

    digest, capped, ungrouped = _prefix_digest(placeable)

    md_path = out_dir / "inventory.md"
    json_path = out_dir / "inventory.json"

    md = _inventory_markdown(
        placeable, unplaceable, order_rule, reported, digest, capped, ungrouped, len(further)
    )
    counts = _ordered_counts(placeable)
    table, _types = _cross_tab(placeable)
    untyped = sum(1 for r in placeable if not _text(r["sheetType"]))

    payload = {
        "expectCount": expect_count,
        "gridFiles": [p.name for p in files],
        "gridOrder": order_rule,
        "counts": {
            "rows": grid_rows,
            "sheets": len(placeable),
            "furtherPages": len(further),
            "duplicates": len(duplicates),
            "unplaceable": len(unplaceable),
            "untyped": untyped,
            "byDiscipline": counts,
            "reportedByDiscipline": reported,
            "byDisciplineAndSheetType": table,
        },
        "sheets": [
            {
                "unitKey": r["unitKey"],
                "discipline": _text(r["discipline"]) or None,
                "sheetNumber": _text(r["sheetNumber"]),
                "pageTitle": _text(r["pageTitle"]) or None,
                "sheetType": _text(r["sheetType"]) or None,
                "fileId": _text(r["fileId"]) or None,
                "pageInPdf": r["pageInPdf"],
                # The key a further page opens as, and the name its dispatch line gives it; null on
                # every other row, which a dispatch line names by its sheet number.
                "opensAs": r["opensAs"],
            }
            for r in placeable
        ],
        "unplaceable": [
            {field: r[field] for field in ROW_FIELDS} for r in unplaceable
        ],
    }
    if issue is not None:
        # Only a grid fetched for one drawing issue carries this, so an inventory of the current
        # set is written as it always was.
        payload["drawingIssue"] = issue

    md_bytes = md.encode("utf-8")
    json_bytes = (json.dumps(payload, indent=2) + "\n").encode("utf-8")
    _write_atomically(md_path, md_bytes)
    _write_atomically(json_path, json_bytes)

    cap_text = f"cap {PREFIX_GROUP_CAP} reached" if capped else f"cap {PREFIX_GROUP_CAP} not reached"
    duplicate_text = f"{len(duplicates)} duplicates" + (f" ({_named(duplicates)})" if duplicates else "")
    issue_text = (
        f"drawing issue {issue['deliveryId']} read from {len(issue['readFrom'])} "
        f"deliver{'y' if len(issue['readFrom']) == 1 else 'ies'}, "
        if issue is not None
        else ""
    )
    # The lead reads no sheet line, so the sheet number it probes the set's text with is named here.
    first_text = f"first sheet {placeable[0]['sheetNumber']}, " if placeable else ""
    # Each further page and each page of an earlier issue is named, so neither is a page that left
    # the plan or joined it with nothing said.
    further_named = [_text(r["sheetNumber"]) + " page " + _text(r["pageInPdf"]) for r in further]
    carried_named = [
        c["sheetNumber"] + " page " + _text(c["pageInPdf"]) + " of delivery " + c["deliveryId"]
        for c in carried
    ]
    further_text = (
        f"{len(further)} further page{'' if len(further) == 1 else 's'} of a number printed on more "
        f"than one page" + (f" ({_named(further_named)})" if further else "")
    )
    carried_text = (
        f"{len(carried)} page{'' if len(carried) == 1 else 's'} of an earlier issue left out"
        + (f" ({_named(carried_named)})" if carried else "")
    )
    return (
        f"wrote {md_path} and {json_path}: {issue_text}{grid_rows:,} rows from {len(files)} grid "
        f"file{'' if len(files) == 1 else 's'}, {duplicate_text}, {len(unplaceable)} rows the grid "
        f"could not place, {further_text}, {carried_text}, {len(placeable):,} sheets to read, "
        f"{len(counts)} disciplines, {len(digest)} sheet number stems "
        f"({cap_text}), {untyped} untyped, {first_text}{len(md_bytes) + len(json_bytes):,} bytes written"
    )


# --------------------------------------------------------------------------- #
# Selection
# --------------------------------------------------------------------------- #

def _select(rows: list[dict], spec: dict) -> list[dict]:
    """
    The one selection primitive the windows share: a discipline, a set of sheet number patterns, or
    both, narrowed by sheet type. Every named criterion must hold, so a spec naming a discipline and
    a sheet type selects that discipline's sheets of that type and nothing else. Returns the matching
    rows in inventory order. A spec that matches nothing returns an empty list; whether that is a
    refusal is the caller's judgment, since a lead's own pattern naming no sheet is a typo.
    """
    _require_keys(spec, SELECT_KEYS, "a selection")
    discipline = spec.get("discipline")
    patterns = spec.get("patterns")
    sheet_types = spec.get("sheetTypes")

    picked: list[dict] = []
    for row in rows:
        if discipline is not None and _text(row.get("discipline")) != discipline:
            continue
        if sheet_types is not None and _text(row.get("sheetType")) not in sheet_types:
            continue
        if patterns is not None and not any(
            fnmatch.fnmatchcase(_text(row.get("sheetNumber")), p) for p in patterns
        ):
            continue
        picked.append(row)
    return picked


# --------------------------------------------------------------------------- #
# The window inputs
# --------------------------------------------------------------------------- #

def _read_packages(path: Path) -> list[dict]:
    """
    The `solicitation_list_packages` response, byte copied to disk. Every package row must carry a
    `tradeCode`: a package with no trade has no unit id for its review to record under, and guessing
    one from its name would be reading meaning off a title.

    Two packages carrying one trade is ordinary and plans two reviews. Nothing about a package
    collides any more: a review computes no sheet list, so there is nothing for two of them to
    compute twice.
    """
    data = _read_json(path, "the packages file")
    rows = data.get("packages") if isinstance(data, dict) else data
    if not isinstance(rows, list):
        raise PlanError(f"{path} carries no `packages` array")
    packages: list[dict] = []
    for index, row in enumerate(rows, 1):
        if not isinstance(row, dict):
            raise PlanError(f"{path}: package {index} is not an object")
        trade_code = row.get("tradeCode")
        if not isinstance(trade_code, str) or not trade_code.strip():
            raise PlanError(f"{path}: package {index} carries no `tradeCode`")
        codes = row.get("codes")
        # The review carries the package's codes verbatim. A `codes` field that is not a list of
        # strings is a shape change on the record's side, named here rather than rendered as none.
        if codes is not None and (
            not isinstance(codes, list) or not all(isinstance(c, str) for c in codes)
        ):
            raise PlanError(f"{path}: package {index} carries a `codes` that is not a list of strings")
        packages.append(row)
    if not packages:
        raise PlanError(f"{path} carries no packages")
    return packages


def _read_repeated_sets(path: Path, data: dict) -> list[dict]:
    """
    A window 1 file's `repeatedSets`: each repeated lines unit with its file id, unit id and page.
    Absent is none, as on a file written before window 1 planned these units, so nothing on it is
    marked and every sheet reads whole.
    """
    value = data.get("repeatedSets")
    if value is None:
        return []
    if not isinstance(value, list):
        raise PlanError(f"{path}: `repeatedSets` is not a list of repeated lines units")
    sets: list[dict] = []
    for index, entry in enumerate(value, 1):
        unit_id = entry.get("unitId") if isinstance(entry, dict) else None
        parsed = _parse_unit_id(unit_id) if isinstance(unit_id, str) else None
        if (
            parsed is None
            or not _REPEATED_PART_RE.match(parsed[0])
            or not isinstance(entry.get("fileId"), str)
            or not entry["fileId"]
        ):
            raise PlanError(
                f"{path}: `repeatedSets` entry {index} carries no `fileId` and no repeated lines "
                f"unit id of the shape RS1-<number>"
            )
        sets.append({"fileId": entry["fileId"], "unitId": unit_id, "page": entry.get("page")})
    return sets


def _read_window_1(
    path: Path, rows: list[dict], tag: str | None = None
) -> tuple[set[str], int, int, list[dict], list[dict]]:
    """
    The file window 1 wrote: the unit keys it selected and the unit keys its `--exclude` patterns
    left out, with the further pages of a number it left out by its first page alone. Window 2 subtracts both. An excluded sheet was left out by the lead with a reason
    recorded, and reading it in window 2 would override that judgment with nothing said about it.
    It also carries the repeated lines units window 1 planned, which window 2 marks its units by.

    A key the inventory does not hold is a refusal rather than a key skipped: a window 1 file from
    some other run would silently leave a sheet of this one unread. So is a repeated lines unit on
    a file the inventory does not hold, which would mark nothing it means to. So is a file planned
    under another unit tag than the run file names now, whose window 2 ids would sit under a tag
    the vocabulary's do not.
    """
    data = _read_json(path, "the window 1 file")
    if not isinstance(data, dict) or data.get("window") != 1:
        raise PlanError(f"{path} is not a window 1 file written by this script")
    if data.get("unitTag") != tag:
        raise PlanError(
            f"{path} was planned under unit tag {data.get('unitTag') or 'none'}, and this plan is "
            f"under {tag or 'none'}; a pass keeps one tag from window 1 on"
        )
    lists: dict[str, list[str]] = {}
    for field in ("selected", "excluded"):
        value = data.get(field)
        if not isinstance(value, list) or not all(isinstance(v, str) for v in value):
            raise PlanError(f"{path}: `{field}` is not a list of unit keys")
        lists[field] = value

    # The two lists are a partition of what window 1 saw, and window 2 only ever reads their union,
    # so a key in both would leave the bounds line reporting a sheet as both selected and left out
    # with nothing catching it. The partition would still be right; the count said out loud would
    # not be.
    both = sorted(set(lists["selected"]) & set(lists["excluded"]))
    if both:
        raise PlanError(
            f"{path} names {len(both)} unit key(s) as both selected and excluded "
            f"({_named(both)}); the two lists are a partition of what window 1 saw"
        )

    known = {r["unitKey"] for r in rows}
    keys = set(lists["selected"]) | set(lists["excluded"])
    strangers = sorted(k for k in keys if k not in known)
    if strangers:
        raise PlanError(
            f"{path} names {len(strangers)} unit key(s) the inventory does not hold "
            f"({_named(strangers)}); it was written off some other inventory"
        )

    repeated_sets = _read_repeated_sets(path, data)
    files = {_text(r.get("fileId")) for r in rows}
    stranger_files = sorted({s["fileId"] for s in repeated_sets if s["fileId"] not in files})
    if stranger_files:
        raise PlanError(
            f"{path} plans the repeated lines of {len(stranger_files)} file(s) the inventory does "
            f"not hold ({_named(stranger_files)}); it was written off some other inventory"
        )

    # A window 1 file written before further pages were read left a number out by its first page's
    # unit key alone, since that was the number's one row. `--exclude` matches the number, so each
    # further page of a number it left out stays out with it rather than reading in window 2. The
    # inventory puts every further page right after its number's row.
    excluded = set(lists["excluded"])
    left_with_number: list[dict] = []
    first_page: dict | None = None
    for row in rows:
        if not _text(row.get("opensAs")):
            first_page = row
        elif (
            first_page is not None
            and first_page["unitKey"] in excluded
            and _text(first_page.get("sheetNumber")) == _text(row.get("sheetNumber"))
            and row["unitKey"] not in keys
        ):
            left_with_number.append(row)
    keys |= {row["unitKey"] for row in left_with_number}
    return (
        keys, len(lists["selected"]), len(lists["excluded"]) + len(left_with_number), repeated_sets,
        left_with_number,
    )


# --------------------------------------------------------------------------- #
# Unit ids already handed out
# --------------------------------------------------------------------------- #

def _parse_unit_id(unit_id: str) -> tuple[str, int] | None:
    """The pass component and the number, or None where the string is not a unit id."""
    m = _UNIT_ID_RE.match(unit_id)
    if m is None:
        return None
    return m.group("pass"), int(m.group("number"))


def _window_file(out_parent: Path, window: int) -> Path:
    return out_parent / "plan" / f"window-{window}.json"


def _read_ledger_units(path: Path, window: int) -> dict[str, tuple[str, ...]]:
    """
    This window's `dispatch` lines, as unit id -> the sheet numbers the line names. A missing file
    is no bindings, which is right for the first plan run of a window: the ledger's own
    `phase: plan approved` line is only appended after the window 1 plan is written.

    The lead's own lines (`dispatch:`, `pass:`, `phase:`) are skipped by the colon after the
    keyword; another window's lines are skipped by the window field. The same unit dispatched twice
    on the same sheets is a resume and binds once.
    """
    if not path.is_file():
        return {}
    try:
        text = path.read_text(encoding="utf-8")
    except Exception as e:
        raise PlanError(f"cannot read the run ledger at {path}: {e}") from e

    by_unit: dict[str, tuple[str, ...]] = {}
    owner_of_sheet: dict[str, str] = {}
    two_owners: list[str] = []
    want = str(window)

    for raw in text.splitlines():
        parts = raw.strip().split()
        if len(parts) < 5 or parts[0] != "dispatch":
            continue
        if parts[1] != want:
            continue
        unit_id = parts[3]
        if window == 1 and _is_repeated_unit(unit_id):
            # A repeated lines unit reads a file, not a sheet, and binds by its file id instead.
            continue
        if parts[4] != "sheets":
            raise PlanError(
                f"{path}: a window {window} dispatch line names no `sheets` field, so its unit id "
                f"binds to nothing: {raw.strip()[:120]}"
            )
        if _parse_unit_id(unit_id) is None:
            raise PlanError(
                f"{path}: the window {window} dispatch line for {unit_id!r} does not carry a unit "
                f"id of the shape <pass>-<number>, so the sheets it read cannot be bound to an id"
            )
        rest = parts[5:]
        if "purpose" in rest:
            rest = rest[: rest.index("purpose")]
        sheets = tuple(sorted({s.strip() for s in " ".join(rest).split(",") if s.strip()}))
        if unit_id in by_unit and by_unit[unit_id] != sheets:
            raise PlanError(
                f"{path}: unit {unit_id} is dispatched on {', '.join(by_unit[unit_id]) or 'no sheet'} "
                f"and on {', '.join(sheets) or 'no sheet'}; one unit id reads one set of sheets"
            )
        by_unit[unit_id] = sheets
        for sheet in sheets:
            first = owner_of_sheet.setdefault(sheet, unit_id)
            if first != unit_id:
                two_owners.append(f"{sheet} under {first} and {unit_id}")

    if two_owners:
        raise PlanError(
            f"{path}: {len(two_owners)} sheet number(s) dispatched under two unit ids in window "
            f"{window} ({_named(two_owners)}); the record carries a subject prefix for each"
        )
    return by_unit


def _is_repeated_unit(unit_id: str) -> bool:
    """Whether a unit id is a repeated lines unit's: `RS1-<n>`, or one in a lettered part."""
    parsed = _parse_unit_id(unit_id)
    return parsed is not None and _REPEATED_PART_RE.match(parsed[0]) is not None


def _read_ledger_repeated(path: Path) -> dict[str, str]:
    """
    Window 1's repeated lines dispatch lines, as unit id -> the file id the line names, read off
    `dispatch 1 <pass> RS1-<n> sheets none purpose repeated lines of file <fileId>`. The pass field
    is whatever pass the runner ran it under; the unit id is what binds. One unit id on two files,
    or one file under two unit ids, is a refusal: the record carries rows under each id.
    """
    if not path.is_file():
        return {}
    try:
        text = path.read_text(encoding="utf-8")
    except Exception as e:
        raise PlanError(f"cannot read the run ledger at {path}: {e}") from e

    file_of: dict[str, str] = {}
    unit_of: dict[str, str] = {}
    for raw in text.splitlines():
        parts = raw.strip().split()
        if len(parts) < 5 or parts[0] != "dispatch" or parts[1] != "1":
            continue
        unit_id = parts[3]
        if not _is_repeated_unit(unit_id):
            continue
        purpose = parts[parts.index("purpose") + 1:] if "purpose" in parts else []
        at = len(purpose) - 1 - purpose[::-1].index("file") if "file" in purpose else -1
        if at < 0 or at + 2 != len(purpose):
            raise PlanError(
                f"{path}: the window 1 dispatch line for {unit_id} names no file after `of file`, "
                f"so the repeated lines unit binds to nothing: {raw.strip()[:120]}"
            )
        file_id = purpose[at + 1]
        if file_of.setdefault(unit_id, file_id) != file_id:
            raise PlanError(
                f"{path}: unit {unit_id} is dispatched on file {file_of[unit_id]} and on file "
                f"{file_id}; one repeated lines unit reads one file"
            )
        if unit_of.setdefault(file_id, unit_id) != unit_id:
            raise PlanError(
                f"{path}: the repeated lines of file {file_id} are dispatched under "
                f"{unit_of[file_id]} and {unit_id}; the record carries a subject prefix for each"
            )
    return file_of


def _read_repeated_read(path: Path, repeated_sets: list[dict]) -> dict[str, str]:
    """
    The files whose repeated lines window 1 read, each with the set version its unit read: the
    unit's last window 1 `verified` line reads `result ok`, its last `note ... set <version>` line
    names the version, and no window 1 `note` line names it `unread`. A unit a runner could not
    read the file's lines for is noted unread, and a unit with no version on the ledger gives a
    window 2 reader nothing to compare its page against, so either file's sheets are read whole.
    """
    if not repeated_sets or not path.is_file():
        return {}
    try:
        text = path.read_text(encoding="utf-8")
    except Exception as e:
        raise PlanError(f"cannot read the run ledger at {path}: {e}") from e
    last: dict[str, str | None] = {}
    version: dict[str, str] = {}
    unread: set[str] = set()
    for raw in text.splitlines():
        parts = raw.strip().split()
        if len(parts) < 5 or parts[1] != "1":
            continue
        if parts[0] == "verified":
            last[parts[3]] = _figure(parts, "result")
        elif parts[0] == "note" and parts[4] == "unread":
            unread.add(parts[3])
        elif parts[0] == "note" and parts[4] == "set" and len(parts) > 5:
            version[parts[3]] = parts[5]
    return {
        s["fileId"]: version[s["unitId"]] for s in repeated_sets
        if last.get(s["unitId"]) == "ok" and s["unitId"] not in unread and s["unitId"] in version
    }


def _read_previous_repeated_sets(path: Path) -> list[dict]:
    """The repeated lines units the last window 1 plan run wrote, or none where it wrote no file."""
    if not path.is_file():
        return []
    data = _read_json(path, "the window 1 plan file")
    if not isinstance(data, dict) or data.get("window") != 1:
        raise PlanError(f"{path} is not a window 1 file written by this script")
    return _read_repeated_sets(path, data)


def _read_plan_file_units(path: Path, window: int) -> dict[str, str]:
    """
    The `units` array the last plan run of this window wrote: unit id -> inventory unit key. A
    missing file, or one from a window that does not write one, is no bindings.
    """
    if not path.is_file():
        return {}
    data = _read_json(path, f"the window {window} plan file")
    if not isinstance(data, dict) or data.get("window") != window:
        raise PlanError(f"{path} is not a window {window} file written by this script")
    units = data.get("units")
    if units is None:
        return {}
    if not isinstance(units, list):
        raise PlanError(f"{path}: `units` is not a list of unit id and unit key pairs")
    bindings: dict[str, str] = {}
    for index, entry in enumerate(units, 1):
        if not isinstance(entry, dict):
            raise PlanError(f"{path}: `units` entry {index} is not an object")
        unit_id = entry.get("id")
        unit_key = entry.get("unitKey")
        if not isinstance(unit_id, str) or _parse_unit_id(unit_id) is None:
            raise PlanError(f"{path}: `units` entry {index} carries no unit id of the shape <pass>-<number>")
        if not isinstance(unit_key, str) or not unit_key:
            raise PlanError(f"{path}: `units` entry {index} carries no `unitKey`")
        bindings[unit_id] = unit_key
    return bindings


def _read_ledger_verified(path: Path, window: int) -> set[str]:
    """
    This window's unit ids that carry a `verified <window> <pass> <unit> ... result ok` line: the
    units a runner already finished, which the plan marks so a pass is finished unit by unit rather
    than by its `pass:` line. A line whose result is anything but `ok` marks nothing, and an id no
    planned or held unit carries is ignored here, since the pass summary is where a `verified`
    line is judged. A missing ledger is nothing verified.
    """
    if not path.is_file():
        return set()
    try:
        text = path.read_text(encoding="utf-8")
    except Exception as e:
        raise PlanError(f"cannot read the run ledger at {path}: {e}") from e
    finished: set[str] = set()
    for raw in text.splitlines():
        parts = raw.strip().split()
        if len(parts) < 4 or parts[0] != "verified" or parts[1] != str(window):
            continue
        if "result" in parts and parts[parts.index("result") + 1:][:1] == ["ok"]:
            finished.add(parts[3])
    return finished


def _read_ledger_pass_lines(path: Path, window: int) -> dict[str, list[str]]:
    """Each pass's last `pass: <window> <pass id> ...` line of this window, split into fields."""
    if not path.is_file():
        return {}
    try:
        text = path.read_text(encoding="utf-8")
    except Exception as e:
        raise PlanError(f"cannot read the run ledger at {path}: {e}") from e
    last: dict[str, list[str]] = {}
    for raw in text.splitlines():
        parts = raw.strip().split()
        if len(parts) >= 3 and parts[0] == "pass:" and parts[1] == str(window):
            last[parts[2]] = parts
    return last


def _figure(parts: list[str], field: str) -> str | None:
    """The word after a field name on a split line, or None where the line names no such field."""
    if field not in parts:
        return None
    at = parts.index(field)
    return parts[at + 1] if at + 1 < len(parts) else None


def _summed(
    window: int, runner_passes: list[list[dict]], run_folder: Path, pass_lines: dict[str, list[str]]
) -> dict[str, str]:
    """
    Each pass's `summed:` value: `yes` where its summary on file names exactly the unit ids it now
    carries and its last `pass:` line carries that summary's figures, otherwise `no` and why.
    """
    summed: dict[str, str] = {}
    for runner_pass in runner_passes:
        pass_id = _host(runner_pass)["id"]
        unit_ids = [
            unit["id"] if window == 3 else unit["unitId"]
            for part in runner_pass for unit in part["units"]
        ]
        suffix = WINDOW_3_SUMMARY_SUFFIX if window == 3 else ""
        path = run_folder / REPORTS_FOLDER / f"{pass_id}{suffix}.md"
        if not path.is_file():
            summed[pass_id] = "no, no summary on file"
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except Exception as e:
            raise PlanError(f"cannot read the pass summary at {path}: {e}") from e
        named: list[str] = []
        totals = None
        for line in text.splitlines():
            parts = line.split()
            if parts[:2] == ["per", "unit:"] and len(parts) > 2 and parts[2] not in named:
                named.append(parts[2])
            elif line.startswith("totals verified:"):
                totals = _SUMMARY_TOTALS_RE.search(line)
        without = [unit_id for unit_id in unit_ids if unit_id not in named]
        beyond = [unit_id for unit_id in named if unit_id not in unit_ids]
        if without or beyond:
            # A pass holds at most twelve units, so every id is named rather than a count.
            differences = [f"without {', '.join(without)}"] if without else []
            differences += [f"beyond {', '.join(beyond)}"] if beyond else []
            summed[pass_id] = "no, the summary on file reads other units: " + "; ".join(differences)
            continue
        if totals is None:
            summed[pass_id] = "no, the summary on file carries no totals line"
            continue
        line = pass_lines.get(pass_id)
        if line is None:
            summed[pass_id] = "no, no pass line on the ledger"
            continue
        wanted = dict(zip(PASS_LINE_FIGURES, [str(len(named)), *totals.groups()]))
        if any(_figure(line, field) != value for field, value in wanted.items()):
            summed[pass_id] = "no, the last pass line does not carry the summary on file"
            continue
        summed[pass_id] = "yes"
    return summed


def _bind_unit_ids(
    passes: list[dict],
    rows: list[dict],
    ledger_units: dict[str, tuple[str, ...]],
    plan_file_units: dict[str, str],
    ledger_path: Path,
    deferred_keys: set[str],
    verified: set[str],
) -> dict:
    """
    Put a unit id on every planned unit, keeping every id either tier already handed out and
    numbering the rest after the highest number that pass has ever carried. Returns the counts the
    bounds line and the totals block both say out loud, along with held units' sheet keys and
    whether the ledger shows each verified ok.

    Every planned unit is one sheet, which is what makes the binding decidable: a ledger unit whose
    sheet set resolves to exactly one planned sheet keeps its id, one that resolves to none is
    retired, and one that resolves to more than one, or to some of its sheets and not all, is a
    refusal. There is no honest way to split an id whose prefix already carries rows.

    A window 2 slice defers sheets rather than cutting them. A ledger unit whose sheets are all
    deferred is held: its number stays taken and it is not counted retired, since it comes back on
    the next full plan. A plan file id on a deferred sheet is dropped: nothing was dispatched under
    it, the slice's own plan file no longer names it, and the sheet is numbered again when the
    whole window is planned.
    """
    planned_keys = {row["unitKey"] for plan_pass in passes for row in plan_pass["units"]}

    # A dispatch line names a further page by the key it opens as, since its number is its first
    # page's; so a line naming the number binds that first page, as it did before further pages.
    rows_by_sheet: dict[str, list[dict]] = {}
    for row in rows:
        rows_by_sheet.setdefault(_sheet_name(row), []).append(row)

    key_of_id: dict[str, str] = {}
    id_of_key: dict[str, str] = {}
    source_of_id: dict[str, str] = {}
    named_ids: set[str] = set()
    held: set[str] = set()
    held_units: list[dict] = []

    for unit_id, sheets in ledger_units.items():
        named_ids.add(unit_id)
        matched: list[str] = []
        for sheet in sheets:
            hits = rows_by_sheet.get(sheet, [])
            if len(hits) > 1:
                raise PlanError(
                    f"{ledger_path}: unit {unit_id} was dispatched on sheet {sheet}, which the "
                    f"inventory holds {len(hits)} times; a sheet number alone cannot say which row "
                    f"that unit read"
                )
            if hits:
                matched.append(hits[0]["unitKey"])
        in_cut = [key for key in matched if key in planned_keys]
        if not in_cut:
            if matched and all(key in deferred_keys for key in matched):
                held.add(unit_id)
                held_units.append({"id": unit_id, "sheetKeys": matched, "verified": unit_id in verified})
            continue
        if len(in_cut) != len(sheets):
            raise PlanError(
                f"{ledger_path}: unit {unit_id} was dispatched on {', '.join(sheets)} and this plan "
                f"reads {len(in_cut)} of them as its own unit; the record already carries rows "
                f"under that id, so the id can be neither split nor kept"
            )
        if len(in_cut) > 1:
            # Every sheet the line named is still in the cut, but the plan now reads them as
            # separate units, so keeping the id would point it at one of them and hand the rest
            # fresh numbers, which is the silent repointing this binding exists to prevent.
            raise PlanError(
                f"{ledger_path}: unit {unit_id} was dispatched on {', '.join(sheets)} and this plan "
                f"reads them as {len(in_cut)} separate units ({', '.join(in_cut)}); the record "
                f"already carries rows under that id for every one of those sheets, so the id can "
                f"be neither split nor kept, and the lead re-cuts the window"
            )
        key_of_id[unit_id] = in_cut[0]
        id_of_key[in_cut[0]] = unit_id
        source_of_id[unit_id] = "ledger"

    for unit_id, unit_key in plan_file_units.items():
        if unit_key in deferred_keys:
            continue
        named_ids.add(unit_id)
        if unit_id in key_of_id or unit_key in id_of_key or unit_key not in planned_keys:
            continue
        key_of_id[unit_id] = unit_key
        id_of_key[unit_key] = unit_id
        source_of_id[unit_id] = "plan file"

    high_water: dict[str, int] = {}
    for unit_id in named_ids:
        parsed = _parse_unit_id(unit_id)
        if parsed is None:
            continue
        pass_component, number = parsed
        high_water[pass_component] = max(high_water.get(pass_component, 0), number)

    kept_by_source = {"ledger": 0, "plan file": 0}
    new_count = 0
    carried: set[str] = set()

    for plan_pass in passes:
        units = plan_pass["units"]
        bound = [row for row in units if row["unitKey"] in id_of_key]
        unbound = [row for row in units if row["unitKey"] not in id_of_key]
        bound.sort(key=lambda row: _parse_unit_id(id_of_key[row["unitKey"]]))
        plan_pass["units"] = bound + unbound
        # A unit dispatched under the pass's own unlettered id keeps that part, so a pass that grew
        # past twelve after it was dispatched, as one does when a further page joins it, keeps its
        # first part's id and reads what does not fit in parts after it (`_split_pass`).
        plan_pass["keepsPart"] = any(
            source_of_id[id_of_key[row["unitKey"]]] == "ledger"
            and _parse_unit_id(id_of_key[row["unitKey"]])[0] == plan_pass["id"]
            for row in bound
        )

        for part_id, part_units in _split_pass(
            plan_pass["id"], plan_pass["units"], plan_pass.get("lettered", False),
            plan_pass["keepsPart"],
        ):
            next_number = high_water.get(part_id, 0) + 1
            for row in part_units:
                existing = id_of_key.get(row["unitKey"])
                if existing is not None and _parse_unit_id(existing)[0] != part_id:
                    if source_of_id[existing] == "ledger":
                        raise PlanError(
                            f"unit {existing} read sheet {_text(row.get('sheetNumber'))} and this "
                            f"plan puts that sheet in pass {part_id}; a dispatched unit cannot "
                            f"change pass, so re-cut the window rather than renumbering it"
                        )
                    # Planned and never dispatched, so no record and no run file carries this id:
                    # the unit is numbered in the part it now sits in, and the old id is retired.
                    existing = None
                if existing is not None:
                    row["unitId"] = existing
                    kept_by_source[source_of_id[existing]] += 1
                else:
                    row["unitId"] = f"{part_id}-{next_number}"
                    next_number += 1
                    new_count += 1
                carried.add(row["unitId"])

    return {
        "kept": kept_by_source["ledger"] + kept_by_source["plan file"],
        "ledger": kept_by_source["ledger"],
        "planFile": kept_by_source["plan file"],
        "new": new_count,
        "retired": len(named_ids - carried - held),
        "held": len(held),
        "heldUnits": held_units,
    }


# --------------------------------------------------------------------------- #
# Passes
# --------------------------------------------------------------------------- #

def _split_pass(
    pass_id: str, units: list[dict], lettered: bool = False, keeps_part: bool = False
) -> list[tuple[str, list[dict]]]:
    """
    A pass over twelve units is split into parts of as even a size as possible, earlier parts taking
    the remainder. Balanced and naive chunking always give the same number of parts, so balancing
    costs nothing and keeps a runner from being started for a single unit.

    `lettered` names even a single part with its letter. A window 2 slice sets it where the whole
    window would split the discipline, so the slice's part is `A2a` rather than `A2`: its unit ids
    then name the part they sit at the front of when the whole window is planned.

    `keeps_part` is set where the ledger dispatched a unit under the pass's own unlettered id. The
    record already carries rows under `<pass>-<n>`, so the first twelve units, the bound ones at
    their front, stay in the part `<pass>`, and the rest split evenly into parts lettered from `b`,
    the part `<pass>` standing first. A pass that never grew past twelve reads as it always did.
    """
    n = len(units)
    if keeps_part:
        head, rest = units[:UNITS_PER_PASS], units[UNITS_PER_PASS:]
        parts = [(pass_id, head)]
        if rest:
            count = math.ceil(len(rest) / UNITS_PER_PASS)
            if count + 1 > len(string.ascii_lowercase):
                raise PlanError(f"pass {pass_id} holds {n} units, more parts than single letters to name them")
            base, extra = divmod(len(rest), count)
            start = 0
            for index in range(count):
                size = base + (1 if index < extra else 0)
                parts.append((f"{pass_id}{string.ascii_lowercase[index + 1]}", rest[start:start + size]))
                start += size
        return parts
    if n <= UNITS_PER_PASS and not lettered:
        return [(pass_id, units)]
    count = math.ceil(n / UNITS_PER_PASS)
    if count > len(string.ascii_lowercase):
        raise PlanError(f"pass {pass_id} holds {n} units, more parts than single letters to name them")
    base, extra = divmod(n, count)
    parts: list[tuple[str, list[dict]]] = []
    start = 0
    for index in range(count):
        size = base + (1 if index < extra else 0)
        parts.append((f"{pass_id}{string.ascii_lowercase[index]}", units[start:start + size]))
        start += size
    return parts


def _window_parts(plan: dict) -> list[dict]:
    """
    Every part a window reads, in plan order: each pass split at twelve, with the name its heading
    carries and the pass it came from.
    """
    parts: list[dict] = []
    for plan_pass in plan["passes"]:
        split = _split_pass(
            plan_pass["id"], plan_pass["units"], plan_pass.get("lettered", False),
            plan_pass.get("keepsPart", False),
        )
        for index, (part_id, part_units) in enumerate(split, 1):
            name = plan_pass["name"]
            if len(split) > 1:
                name += f" (part {index} of {len(split)})"
            parts.append({"id": part_id, "name": name, "units": part_units, "pass": plan_pass})
    return parts


def _fold_small_parts(parts: list[dict]) -> list[list[dict]]:
    """
    Group a window's parts into runner passes. Walking the parts in plan order, a part joins the
    pass being built where either side of the join is under MIN_PASS_UNITS and the joined pass stays
    at UNITS_PER_PASS or fewer, and starts a new pass otherwise. Two parts of MIN_PASS_UNITS or more
    never join, so a pass holds at most one.

    There is no same-discipline neighbour to prefer: a part under MIN_PASS_UNITS is always a whole
    discipline, since a split part holds at least six units, so every fold carries more than one
    discipline. Only part sizes and adjacency decide; no part is reordered, split or renumbered.
    """
    passes: list[list[dict]] = []
    for part in parts:
        if passes:
            built = sum(len(member["units"]) for member in passes[-1])
            size = len(part["units"])
            if min(built, size) < MIN_PASS_UNITS and built + size <= UNITS_PER_PASS:
                passes[-1].append(part)
                continue
        passes.append([part])
    return passes


def _host(runner_pass: list[dict]) -> dict:
    """The part a runner pass is named for: its one part of MIN_PASS_UNITS or more, or its first."""
    return next(
        (part for part in runner_pass if len(part["units"]) >= MIN_PASS_UNITS), runner_pass[0]
    )


def _runner_passes(window: int, plan: dict) -> list[list[dict]]:
    """The passes a runner is started for, each a list of the parts it reads in order."""
    parts = _window_parts(plan)
    if window == 3:
        # A review is its own pass and its pass id is its unit id, so nothing folds.
        return [[part] for part in parts]
    return _fold_small_parts(parts)


def _folds(runner_passes: list[list[dict]]) -> list[str]:
    """Each folded part, as `<part> into <pass>`, in plan order."""
    return [
        f"{part['id']} into {_host(runner_pass)['id']}"
        for runner_pass in runner_passes
        for part in runner_pass
        if part is not _host(runner_pass)
    ]


def _fold_clause(runner_passes: list[list[dict]]) -> str:
    """The bounds line's account of the fold: every fold named, and every small pass that stayed."""
    folds = _folds(runner_passes)
    clause = f"folds {len(folds)} ({', '.join(folds)})" if folds else "folds 0"
    kept = [
        _host(runner_pass)["id"]
        for runner_pass in runner_passes
        if sum(len(part["units"]) for part in runner_pass) < MIN_PASS_UNITS
    ]
    if kept:
        clause += f", passes under three units kept {len(kept)} ({', '.join(kept)})"
    return clause


def _unit_line(label: str, row: dict, show_file: bool) -> str:
    """
    A planned unit's label is its unit id, which is what the runner puts on the ledger line and in
    the `verify_unit` prefix. A left-out sheet has no unit, so its label is a plain ordinal. A
    repeated lines unit reads a file from any of its pages, so it names the file always.
    """
    if row.get("repeatedSet"):
        line = f"{label}. file {row['fileId']}, from page {row['pageInPdf']}: repeated lines"
        if row.get("sheetsLeftOut"):
            line += ", sheets left out " + ", ".join(row["sheetsLeftOut"])
        return line
    title = _text(row["pageTitle"]) or "(no title)"
    where = f"page {row['pageInPdf']}"
    opens_as = _text(row.get("opensAs"))
    if show_file or opens_as:
        # The file id only earns its place where the set spans more than one file and the page
        # number alone would not say which document to open, or on a further page, which its
        # number alone never names.
        where = f"file {_text(row.get('fileId')) or '(no file)'}, " + where
    if opens_as:
        where += f", opens as {opens_as}"
    return f"{label}. {row['sheetNumber']}, {where}: {title}"


def _review_line(number: int, review: dict) -> str:
    """A window 3 unit is a review of a package, not a sheet, so it carries no page reference."""
    return f"{number}. {review['id']}: {review['name']}"


def _by_discipline(rows: list[dict]) -> list[tuple[str, list[dict]]]:
    """
    Rows grouped by discipline in inventory order. A row with no discipline is its own group, never
    merged into another: a set that could not place a sheet's discipline is not evidence that it
    belongs with any particular one.
    """
    order: list[str] = []
    groups: dict[str, list[dict]] = {}
    for row in rows:
        key = _text(row.get("discipline")) or NO_DISCIPLINE
        if key not in groups:
            groups[key] = []
            order.append(key)
        groups[key].append(row)
    return [(key, groups[key]) for key in order]


def _sheet_type_of(row: dict) -> str:
    return _text(row.get("sheetType")) or UNTYPED_SHEET_TYPE


def _by_sheet_type(rows: list[dict]) -> list[dict]:
    """
    One discipline's rows in the fixed sheet type order, inventory order kept inside a type. A type
    the order does not name sorts after all of them rather than ahead of one it was never ranked
    against; the caller names those types on the bounds line.
    """
    return sorted(
        rows,
        key=lambda row: _WINDOW_2_TYPE_RANK.get(_sheet_type_of(row), len(WINDOW_2_SHEET_TYPE_ORDER)),
    )


def _pass_id_for_discipline(discipline: str, window: int, tag: str | None = None) -> str:
    """
    A discipline pass is named for its discipline and its window, so `A1` reads as A, window 1, and
    `i2-A1` reads as the same pass of the drawing issue whose pass carries unit tag i2.
    """
    stem = "NONE" if discipline == NO_DISCIPLINE else discipline
    return _tagged(f"{stem}{window}", tag)


# --------------------------------------------------------------------------- #
# Window 1: the vocabulary
# --------------------------------------------------------------------------- #

def _split_pattern_argument(raw: str, flag: str) -> tuple[str, str]:
    """
    `<pattern>:<reason>`, split on the first colon only so a reason may carry one. Both halves are
    required: an include, exclude or only with no reason is a judgment with nothing recorded behind
    it.
    """
    pattern, sep, reason = raw.partition(":")
    if not sep or not pattern.strip() or not reason.strip():
        raise PlanError(f"{flag} {raw!r} is not `<pattern>:<reason>`")
    return pattern.strip(), reason.strip()


def _window_1(rows: list[dict], includes, excludes, tag: str | None = None) -> dict:
    selected: dict[str, dict] = {
        r["unitKey"]: r for r in rows if _text(r.get("sheetType")) in VOCABULARY_SHEET_TYPES
    }

    include_blocks: list[dict] = []
    for pattern, reason in includes:
        hits = _select(rows, {"patterns": [pattern]})
        if not hits:
            raise PlanError(f"--include: no sheet number matches the pattern {pattern}")
        for row in hits:
            selected[row["unitKey"]] = row
        include_blocks.append({"pattern": pattern, "reason": reason, "sheets": hits})

    exclude_blocks: list[dict] = []
    excluded_keys: set[str] = set()
    for pattern, reason in excludes:
        hits = _select(rows, {"patterns": [pattern]})
        if not hits:
            raise PlanError(f"--exclude: no sheet number matches the pattern {pattern}")
        for row in hits:
            selected.pop(row["unitKey"], None)
            excluded_keys.add(row["unitKey"])
        exclude_blocks.append({"pattern": pattern, "reason": reason, "sheets": hits})

    chosen = [r for r in rows if r["unitKey"] in selected]

    passes: list[dict] = []
    for discipline, group in _by_discipline(chosen):
        if _pass_id_for_discipline(discipline, 1, tag) == _tagged(REPEATED_PASS_ID, tag):
            raise PlanError(
                f"discipline {discipline} would read its window 1 sheets as pass "
                f"{_tagged(REPEATED_PASS_ID, tag)}, which is the repeated lines pass, so its unit "
                f"ids would be theirs; nothing written"
            )
        passes.append(
            {
                "id": _pass_id_for_discipline(discipline, 1, tag),
                "discipline": discipline,
                "name": f"Vocabulary, discipline {discipline}",
                "readsFor": "the vocabulary",
                "units": group,
            }
        )

    unassigned = [
        r for r in rows if r["unitKey"] not in selected and r["unitKey"] not in excluded_keys
    ]
    return {
        "passes": passes,
        "repeatedPasses": _repeated_passes(
            [r for r in rows if r["unitKey"] not in excluded_keys],
            [r for r in rows if r["unitKey"] in excluded_keys],
            tag,
        ),
        "includes": include_blocks,
        "excludes": exclude_blocks,
        "excludedCount": len(excluded_keys),
        "selectedKeys": [r["unitKey"] for r in chosen],
        "excludedKeys": [r["unitKey"] for r in rows if r["unitKey"] in excluded_keys],
        "unassigned": unassigned,
        "notes": [],
    }


def _repeated_passes(
    read_rows: list[dict], left_out_rows: list[dict], tag: str | None = None
) -> list[dict]:
    """
    The repeated lines pass: one unit per file holding REPEATED_MIN_ROWS or more of the rows the
    run reads, in the order each file first appears in the inventory, at the page of that first
    row. A row with no file id names no file to read, so it counts toward none.

    `repeated: "only"` reads the whole file, the sheets `--exclude` left out included, so each unit
    carries its file's left-out sheet numbers: its reader records nothing from a block printed only
    on those sheets.
    """
    by_file: dict[str, list[dict]] = {}
    for row in read_rows:
        file_id = _text(row.get("fileId"))
        if file_id:
            by_file.setdefault(file_id, []).append(row)
    left_out: dict[str, list[str]] = {}
    for row in left_out_rows:
        left_out.setdefault(_text(row.get("fileId")), []).append(_sheet_name(row))
    units = [
        {
            "unitKey": _REPEATED_KEY_PREFIX + file_id,
            # The binding resolves a ledger line through the unit's sheet number, and a repeated
            # lines line names a file, so the file id stands in that field.
            "sheetNumber": file_id,
            "fileId": file_id,
            "pageInPdf": file_rows[0]["pageInPdf"],
            "sheetsLeftOut": left_out.get(file_id, []),
            "repeatedSet": True,
        }
        for file_id, file_rows in by_file.items()
        if len(file_rows) >= REPEATED_MIN_ROWS
    ]
    if not units:
        return []
    return [
        {
            "id": _tagged(REPEATED_PASS_ID, tag),
            "discipline": None,
            "name": "Repeated lines, read once",
            "readsFor": REPEATED_READS_FOR,
            "units": units,
            "repeatedSets": True,
        }
    ]


# --------------------------------------------------------------------------- #
# Window 2: every remaining sheet, once
# --------------------------------------------------------------------------- #

def _window_2(
    rows: list[dict], window_1_keys: set[str], selected: int, excluded: int, only,
    tag: str | None = None,
) -> dict:
    remaining = [r for r in rows if r["unitKey"] not in window_1_keys]

    # A slice the user asked for first. Each pattern selects among the sheets window 1 left only,
    # so a pattern naming nothing this window reads is a typo, refused as an include's is.
    only_blocks: list[dict] = []
    sliced: set[str] = set()
    for pattern, reason in only:
        hits = _select(remaining, {"patterns": [pattern]})
        if not hits:
            raise PlanError(f"--only: no sheet number window 2 reads matches the pattern {pattern}")
        sliced.update(r["unitKey"] for r in hits)
        only_blocks.append({"pattern": pattern, "reason": reason, "sheets": hits})
    chosen = [r for r in remaining if r["unitKey"] in sliced] if only else remaining
    deferred = [r for r in remaining if r["unitKey"] not in sliced] if only else []

    # Lettering follows the whole window, not the slice, so a slice's part id is the one its units
    # keep at the front of that discipline when the whole window is planned.
    whole = {discipline: len(group) for discipline, group in _by_discipline(remaining)}
    passes: list[dict] = []
    for discipline, group in _by_discipline(chosen):
        passes.append(
            {
                "id": _pass_id_for_discipline(discipline, 2, tag),
                "discipline": discipline,
                "name": f"Every sheet, discipline {discipline}",
                "readsFor": "the sheet",
                "units": _by_sheet_type(group),
                "lettered": whole[discipline] > UNITS_PER_PASS,
            }
        )

    planned = [r["unitKey"] for plan_pass in passes for r in plan_pass["units"]]
    deferred_keys = [r["unitKey"] for r in deferred]
    together = planned + deferred_keys
    distinct = len(set(together))
    # Planned plus deferred is a partition of what window 1 left. Selecting, grouping and sorting
    # can only divide and reorder it, so a run where the two together are not exactly those rows,
    # once each, is a defect in this script rather than a set that reads twice.
    if len(together) != distinct or set(together) != {r["unitKey"] for r in remaining}:
        deferred_clause = f" and deferred {len(deferred_keys)}" if deferred_keys else ""
        raise PlanError(
            f"window 2 planned {len(planned)} unit(s){deferred_clause} over {distinct} distinct "
            f"sheet(s) from the {len(remaining)} row(s) window 1 left; the selection is a "
            f"partition and this run is a script defect"
        )

    by_type: dict[str, int] = {}
    for row in chosen:
        sheet_type = _sheet_type_of(row)
        by_type[sheet_type] = by_type.get(sheet_type, 0) + 1
    ordered_types = [t for t in WINDOW_2_SHEET_TYPE_ORDER if t in by_type]
    unordered_types = [t for t in by_type if t not in _WINDOW_2_TYPE_RANK]

    return {
        "passes": passes,
        "includes": [],
        "excludes": [],
        "excludedCount": 0,
        "unassigned": [],
        "only": only_blocks,
        "deferred": deferred,
        "units": len(planned),
        "distinctSheets": distinct,
        "disciplines": len(passes),
        "byType": [(t, by_type[t]) for t in ordered_types + sorted(unordered_types)],
        "otherOrUntyped": by_type.get("other", 0) + by_type.get(UNTYPED_SHEET_TYPE, 0),
        "unorderedTypes": sorted(unordered_types),
        "window1Selected": selected,
        "window1Excluded": excluded,
        "notes": [],
    }


# --------------------------------------------------------------------------- #
# Window 3: one review per package
# --------------------------------------------------------------------------- #

def _code_covers(package_code: str, written: str) -> bool:
    """
    Whether a package's code covers a trade a pass wrote on, the way the server reads a package's
    coverage: a code's trailing zeros say how broad it is. "AA 00 00" covers its division, "AA BC 00"
    its section, "AA B0 00" every "AA Bx" section under it (09 60 00 covers 09 65 19), and any other
    code only itself.
    """
    if _fold(package_code) == _fold(written):
        return True
    code = re.sub(r"\D", "", package_code)
    target = re.sub(r"\D", "", written)
    if not re.fullmatch(r"\d{4}00", code) or not re.fullmatch(r"\d{6}", target):
        return False
    aa, b, c = code[:2], code[2], code[3]
    if b == "0" and c == "0":
        return target.startswith(aa)
    if c != "0":
        return target.startswith(aa + b + c)
    return target.startswith(aa + b)


def _window_3(
    packages: list[dict], tag: str | None = None, written_on: set[str] | None = None
) -> dict:
    """
    One review per package, in package order, with the packages of one trade kept together. The
    order is the order the packages were bought in: the first package of each trade holds that
    trade's place, and any later package on the same trade follows it there rather than where it
    sat in the file.

    Two packages carrying one trade both plan, one after the other, and their unit ids differ by the
    ordinal each carries. The runner's overlap scan sees them side by side, which is how two passes
    over the same work are kept from doubling it.

    `written_on`, the folded trades an addendum's pass wrote on, keeps only the reviews of
    the packages covering those trades (as their own trade or one of their `codes`), and every
    other package is named as left out. Ids are numbered over the
    whole list first, so a package's review id is the same whichever packages plan beside it.
    """
    ordinals: dict[str, int] = {}
    reviews: list[dict] = []
    for package in packages:
        code = _text(package.get("tradeCode")).strip()
        key = _fold(code)
        ordinals[key] = ordinals.get(key, 0) + 1
        reviews.append(
            {
                # Always numbered, even where the trade carries one package: a bare `rev-092116-`
                # would be a prefix of `rev-092116-2-`, and the runner verifies a review by prefix.
                "id": _tagged(f"rev-{_pack(code)}-{ordinals[key]}", tag),
                "tradeCode": code,
                "tradeKey": key,
                "name": _text(package.get("name")) or code,
                "package": package,
                "codes": list(package.get("codes") or []),
            }
        )
    left_out: list[dict] = []
    if written_on is not None:
        # A package covers its own trade, every trade folded into its `codes`, and every trade
        # under a broad code of either, so a pass that wrote only on one of those still reviews the
        # package that bids it.
        def covers(review: dict) -> bool:
            own = [review["tradeCode"], *(_text(code) for code in review["codes"])]
            return any(_code_covers(code, written) for code in own for written in written_on)

        left_out = [review for review in reviews if not covers(review)]
        reviews = [review for review in reviews if covers(review)]

    # Grouped by folded trade code in first-seen order, so two packages on one trade review one
    # after the other and everything else keeps the order the packages were bought in.
    order: list[str] = []
    members: dict[str, list[dict]] = {}
    for review in reviews:
        key = review["tradeKey"]
        if key not in members:
            members[key] = []
            order.append(key)
        members[key].append(review)

    passes: list[dict] = []
    for key in order:
        for review in members[key]:
            plan_pass = {
                "id": review["id"],
                "name": review["name"],
                "readsFor": review["tradeCode"],
                "units": [review],
                "extra": [
                    ("package", _text(review["package"].get("id")) or "(no id)"),
                    ("codes", ", ".join(review["codes"]) if review["codes"] else "none"),
                ],
            }
            passes.append(plan_pass)

    shared = [r for r in reviews if len(members[r["tradeKey"]]) > 1]

    def distinct_codes(rows: list[dict]) -> list[str]:
        seen: list[str] = []
        for row in rows:
            if row["tradeCode"] not in seen:
                seen.append(row["tradeCode"])
        return seen

    return {
        "passes": passes,
        "includes": [],
        "excludes": [],
        "excludedCount": 0,
        "unassigned": [],
        "reviews": len(reviews),
        "trades": len(order),
        "sharedCount": len(shared),
        "sharedCodes": distinct_codes(shared),
        "leftOut": [{"name": review["name"], "tradeCode": review["tradeCode"]} for review in left_out],
        "partial": written_on is not None,
        "notes": [],
    }


_WHOLE_NUMBER_RE = re.compile(r"^[0-9]+$")


def _read_pass_trades(folder: Path) -> tuple[set[str], set[str]]:
    """
    The folded trades an addendum's pass wrote on, and the units that named a trade they touched.
    The trades are every catalog id on a `<unit id> trade <catalog id> <count>` line of the pass's
    trades files, which the runners append off each unit's own verification, and on a `<unit id>
    touched <catalog id>` line, the home trade of a row the unit updated or cited and a trade a
    Question it raised names, which the runners carry off the reader's report. An addendum that
    only changes existing scope still has its packages reviewed. A candidates line names no trade.

    The grammar is the one `pass_summary.py` reads the same files by, held as strictly: a count
    that is not a whole number is refused, as it is there. The folder is found beside the plan, so
    it is never an argument; a pass with no trades folder at all is refused, since planning no
    review off a folder that was never written would read as a pass that wrote nothing.
    """
    trades_dir = folder / "trades"
    if not trades_dir.is_dir():
        raise PlanError(
            f"{trades_dir} does not exist; window 3 of a pass on an addendum reviews the packages its "
            f"trades files name, and the runners write them as each unit verifies"
        )
    written_on: set[str] = set()
    touched_units: set[str] = set()
    for path in sorted(trades_dir.glob("*.txt")):
        try:
            text = path.read_text(encoding="utf-8")
        except Exception as e:
            raise PlanError(f"cannot read the trades file at {path}: {e}") from e
        for number, raw in enumerate(text.splitlines(), 1):
            parts = raw.split()
            if not parts:
                continue
            if len(parts) >= 3 and parts[1] == "candidates":
                if not _WHOLE_NUMBER_RE.match(parts[2]):
                    raise PlanError(f"{path} line {number}: the candidates count {parts[2]!r} is not a whole number")
                continue
            # A catalog id carries spaces, so the count is the last word and the id sits before it.
            if len(parts) >= 4 and parts[1] == "trade":
                if not _WHOLE_NUMBER_RE.match(parts[-1]):
                    raise PlanError(f"{path} line {number}: the trade count {parts[-1]!r} is not a whole number")
                written_on.add(_fold(" ".join(parts[2:-1])))
                continue
            if len(parts) >= 3 and parts[1] == "touched":
                written_on.add(_fold(" ".join(parts[2:])))
                touched_units.add(parts[0])
                continue
            raise PlanError(
                f"{path} line {number} is neither `<unit id> trade <catalog id> <count>`, "
                f"`<unit id> candidates <count>` nor `<unit id> touched <catalog id>`"
            )
    return written_on, touched_units


def _units_touching_unnamed_trades(ledger: Path, touched_units: set[str]) -> list[str]:
    """
    The units whose last `verified` line in windows 1 and 2 shows a row updated or a Question
    raised, and that carry no `touched` line: their reader named no trade it touched, so the trades
    this pass wrote on are not all known, and no package can be left out as untouched.
    """
    if not ledger.is_file():
        return []
    try:
        text = ledger.read_text(encoding="utf-8")
    except Exception as e:
        raise PlanError(f"cannot read the run ledger at {ledger}: {e}") from e
    last: dict[str, list[str]] = {}
    for raw in text.splitlines():
        parts = raw.split()
        if len(parts) >= 4 and parts[0] == "verified" and parts[1] in ("1", "2"):
            last[parts[3]] = parts
    unnamed: list[str] = []
    for unit_id, parts in last.items():
        wrote = any(
            _WHOLE_NUMBER_RE.match(_figure(parts, field) or "") and int(_figure(parts, field)) > 0
            for field in ("updated", "questions")
        )
        if wrote and unit_id not in touched_units:
            unnamed.append(unit_id)
    return unnamed


# --------------------------------------------------------------------------- #
# The read plan file
# --------------------------------------------------------------------------- #

def _every_sheet_once(plan: dict) -> str:
    """
    The window 2 partition said out loud. A slice names its deferred sheets beside the units it
    plans, and the sheets an earlier slice already read and verified as read earlier, so the line
    still accounts for every sheet window 1 left; a whole window reads as it always has.
    """
    read_earlier = plan["readEarlier"]
    earlier_clause = f" plus read earlier {len(read_earlier)}" if read_earlier else ""
    deferred_clause = (
        f" plus deferred {len(plan['deferred'])}" if plan["deferred"] or read_earlier else ""
    )
    return (
        f"every sheet once (units {plan['units']}{earlier_clause}{deferred_clause} equals "
        f"distinct sheets {plan['distinctSheets']})"
    )


def _render_slice(plan: dict, show_file: bool) -> list[str]:
    """
    What a window 2 slice read and what it deferred. Each pattern's sheets are listed as a left-out
    block lists its sheets, a plain ordinal on each; the deferred sheets are counted by discipline
    rather than listed, since they are the rest of the window and the next full plan lists them.
    """
    lines: list[str] = []
    lines.append("## Read now, the rest deferred")
    lines.append("")
    lines.append("This run plans only the sheets an --only pattern names. A deferred sheet is not left")
    lines.append("out: the next plan run of this window without --only plans it again.")
    lines.append("")
    for block in plan["only"]:
        lines.append(f"### Only: {block['pattern']}")
        lines.append("")
        lines.append(f"reason: {block['reason']}")
        lines.append(f"sheets: {len(block['sheets'])}")
        lines.append("")
        for number, row in enumerate(block["sheets"], 1):
            lines.append(_unit_line(str(number), row, show_file))
        lines.append("")
    if plan["readEarlier"]:
        lines.append("### Read earlier")
        lines.append("")
        lines.append(f"sheets: {len(plan['readEarlier'])}")
        lines.append("")
        for number, row in enumerate(plan["readEarlier"], 1):
            lines.append(_unit_line(str(number), row, show_file))
        lines.append("")
    lines.append("### Deferred")
    lines.append("")
    reasons: list[str] = []
    for block in plan["only"]:
        if block["reason"] not in reasons:
            reasons.append(block["reason"])
    for reason in reasons:
        lines.append(f"reason: {reason}")
    lines.append(f"sheets: {len(plan['deferred'])}")
    lines.append("")
    if plan["deferred"]:
        lines.append("discipline | sheets")
        for discipline, group in _by_discipline(plan["deferred"]):
            lines.append(f"{discipline} | {len(group)}")
    elif plan["readEarlier"]:
        lines.append("Nothing. Every sheet window 1 left is planned now or was read earlier.")
    else:
        lines.append("Nothing. Every sheet window 1 left matches an --only pattern.")
    lines.append("")
    return lines


def _left_with_number_clause(plan: dict) -> str:
    """
    The further pages window 2 leaves out because an earlier window 1 file left their number out by
    its first page alone, named, or nothing where there are none.
    """
    rows = plan.get("leftWithNumber") or []
    if not rows:
        return ""
    named = [_text(row["sheetNumber"]) + " page " + _text(row["pageInPdf"]) for row in rows]
    return f", further pages left out with their number {len(rows)} ({_named(named)})"


def _is_repeated_pass(runner_pass: list[dict]) -> bool:
    """Whether a runner pass is a repeated lines pass, which reads files and never folds."""
    return bool(runner_pass[0]["pass"].get("repeatedSets"))


def _repeated_clause(plan: dict, units: int, runner_passes: list[list[dict]]) -> str:
    """Window 1's account of its repeated lines units, the same on the bounds line and the totals."""
    ids = plan["repeatedIds"]
    passes = sum(1 for runner_pass in runner_passes if _is_repeated_pass(runner_pass))
    return (
        f"repeated lines read once: files {units}, passes {passes}, their ids kept {ids['kept']} "
        f"(ledger {ids['ledger']}, plan file {ids['planFile']}), new {ids['new']}, retired "
        f"{ids['retired']}"
    )


def _marked_clause(plan: dict) -> str:
    """Window 2's account of the sheets whose readers leave their file's repeated lines out."""
    marked = plan["repeatedRead"]
    sheets = sum(
        1 for plan_pass in plan["passes"] for row in plan_pass["units"]
        if _text(row.get("fileId")) in marked
    )
    files = len({s["fileId"] for s in plan["repeatedSets"]})
    return (
        f"sheets read without their file's repeated lines {sheets}, files whose repeated lines "
        f"were read {len(marked)} of {files} planned"
    )


def _render(
    window: int, plan: dict, rows: list[dict], show_file: bool, runner_passes: list[list[dict]]
) -> tuple[str, int, int]:
    lines: list[str] = []
    lines.append(f"# Read plan: window {window}")
    lines.append("")
    lines.append("Written by scripts/plan_inventory.py off this window's inputs.")
    lines.append("The unit lines are copied from the sheet grid and the packages file. Run the")
    lines.append("script again rather than editing this file: a unit id already dispatched keeps")
    lines.append("its number, and a new sheet is numbered after the highest id its discipline's")
    lines.append("part carries.")
    lines.append("")
    lines.append(f"## Window {window}")
    lines.append("")

    # The repeated lines passes are counted on their own line, so every sheet count reads as it did.
    total_units = 0
    total_passes = sum(1 for runner_pass in runner_passes if not _is_repeated_pass(runner_pass))
    repeated_units = 0
    marked = plan.get("repeatedRead", {})

    for runner_pass in runner_passes:
        host = _host(runner_pass)
        folded = [part for part in runner_pass if part is not host]
        pass_units = [unit for part in runner_pass for unit in part["units"]]
        if _is_repeated_pass(runner_pass):
            repeated_units += len(pass_units)
        else:
            total_units += len(pass_units)
        heading = f"### {host['id']}. {host['name']}"
        if folded:
            # The lead finds a discipline's passes by their headings, so a folded pass names every
            # discipline it carries.
            disciplines = [part["pass"]["discipline"] for part in folded]
            heading += (
                f", with discipline{'s' if len(disciplines) > 1 else ''} {', '.join(disciplines)}"
            )
        lines.append(heading)
        lines.append("")
        lines.append(f"window: {window}")
        lines.append(f"reads for: {host['pass']['readsFor']}")
        if folded:
            lines.append(f"folded in: {', '.join(part['id'] for part in folded)}")
        for label, value in host["pass"].get("extra", []):
            lines.append(f"{label}: {value}")
        lines.append(f"units: {len(pass_units)}")
        unit_ids = [unit["id"] if window == 3 else unit["unitId"] for unit in pass_units]
        lines.append(f"units verified: {sum(1 for u in unit_ids if u in plan['verified'])}")
        lines.append(f"summed: {plan['summed'][host['id']]}")
        lines.append("")
        for number, (unit, unit_id) in enumerate(zip(pass_units, unit_ids), 1):
            line = (
                _review_line(number, unit)
                if window == 3
                else _unit_line(unit_id, unit, show_file)
            )
            if window == 2 and _text(unit.get("fileId")) in marked:
                # The version the file's unit read, which the reader compares its page against.
                line += f"{REPEATED_MARK} in set {marked[_text(unit.get('fileId'))]}"
            lines.append(line + (" verified" if unit_id in plan["verified"] else ""))
        lines.append("")

    lines.append("## Deliberately left out")
    lines.append("")
    if not plan["excludes"]:
        lines.append("Nothing. This window left nothing out by pattern.")
        lines.append("")
    for block in plan["excludes"]:
        lines.append(f"### Left out: {block['pattern']}")
        lines.append("")
        lines.append(f"reason: {block['reason']}")
        lines.append(f"sheets: {len(block['sheets'])}")
        lines.append("")
        for number, row in enumerate(block["sheets"], 1):
            lines.append(_unit_line(str(number), row, show_file))
        lines.append("")

    if plan.get("only"):
        lines.extend(_render_slice(plan, show_file))

    lines.append("## Nothing read for")
    lines.append("")
    if window == 3 and plan.get("unnamed"):
        lines.append("Nothing. A pass on an addendum reviews only the packages covering a trade it wrote on,")
        lines.append("but these units updated a row or raised a Question and named no trade they touched,")
        lines.append("so which packages the pass wrote on is not known and every package plans a review:")
        lines.append("")
        for number, unit_id in enumerate(plan["unnamed"], 1):
            lines.append(f"{number}. {unit_id}")
    elif window == 3 and plan.get("leftOut"):
        lines.append("A pass on an addendum reviews only the packages covering a trade it wrote on: a row it")
        lines.append("created, a row it updated or cited, or a Question it raised. It wrote on none of")
        lines.append("these, so no review reads for them:")
        lines.append("")
        for number, package in enumerate(plan["leftOut"], 1):
            lines.append(f"{number}. {package['name']}, trade {package['tradeCode']}")
    elif window == 3:
        lines.append("Nothing. Every package on the project plans a review.")
    else:
        lines.append("Nothing. This window plans off the inventory, not off the packages.")
    lines.append("")

    lines.append("## Totals")
    lines.append("")
    if window in (1, 2):
        lines.append(
            f"units planned {total_units}, passes {total_passes}, "
            f"folds {len(_folds(runner_passes))}"
        )
    else:
        lines.append(f"units planned {total_units}, passes {total_passes}")
    if window in (1, 2):
        ids = plan["unitIds"]
        lines.append(
            f"unit ids kept {ids['kept']}, new {ids['new']}, retired {ids['retired']}"
            + (f", ids held {ids['held']}" if ids["held"] else "")
        )
    if window == 1:
        lines.append(_repeated_clause(plan, repeated_units, runner_passes))
    if window == 2:
        lines.append(_marked_clause(plan))
    if window == 1:
        lines.append(
            f"sheets left out {plan['excludedCount']}, sheets this window does not read "
            f"{len(plan['unassigned'])}, sheets in the inventory {len(rows)}"
        )
        lines.append(
            f"sheets added by include patterns {sum(len(b['sheets']) for b in plan['includes'])}"
        )
    if window == 2:
        lines.append(_every_sheet_once(plan))
        if plan["deferred"]:
            lines.append(f"sheets deferred {len(plan['deferred'])} by --only")
        lines.append(
            f"sheets window 1 selected {plan['window1Selected']}, sheets window 1 left out "
            f"{plan['window1Excluded']}{_left_with_number_clause(plan)}, sheets in the inventory "
            f"{len(rows)}"
        )
        lines.append(
            "sheets by type: " + ", ".join(f"{name} {count}" for name, count in plan["byType"])
        )
        lines.append(f"sheets typed other or untyped {plan['otherOrUntyped']}")
        if plan["unorderedTypes"]:
            lines.append(
                "sheet types the reading order does not name, read after every type it does: "
                + ", ".join(plan["unorderedTypes"])
            )
    if window == 3:
        lines.append(f"reviews {plan['reviews']}, trades {plan['trades']}")
        lines.append(
            f"packages sharing a trade: {plan['sharedCount']} "
            f"({_named(plan['sharedCodes']) if plan['sharedCodes'] else 'none'})"
        )
    for note in plan["notes"]:
        lines.append(note)

    return "\n".join(lines) + "\n", total_units, total_passes


# --------------------------------------------------------------------------- #
# plan
# --------------------------------------------------------------------------- #

# Which window each argument belongs to. An argument some other window takes is refused rather than
# dropped quietly: dropping it would lose the caller's intent with nothing said about it.
ALLOWED_BY_WINDOW = {
    1: ("--inventory", "--include", "--exclude"),
    2: ("--inventory", "--window-1", "--only"),
    3: ("--packages",),
}
REQUIRED_BY_WINDOW = {
    1: ("--inventory",),
    2: ("--inventory", "--window-1"),
    3: ("--packages",),
}
# Arguments no window takes any more, kept so the old invocation refuses in one readable line
# instead of an argparse dump.
RETIRED_ARGUMENTS = {
    "--kinds": "the record's definitions reach a review through the record, not through the plan",
    "--index": "no window plans off the citation index",
}


def _check_arguments(args, window: int) -> None:
    values = {
        "--inventory": args.inventory,
        "--window-1": args.window_1,
        "--packages": args.packages,
        "--kinds": args.kinds,
        "--index": args.index,
        "--include": args.include,
        "--exclude": args.exclude,
        "--only": args.only,
    }
    for flag, reason in RETIRED_ARGUMENTS.items():
        if values[flag]:
            raise PlanError(f"{flag} is no longer an argument of any window: {reason}")
    allowed = ALLOWED_BY_WINDOW[window]
    for flag, value in values.items():
        if flag in RETIRED_ARGUMENTS or flag in allowed or not value:
            continue
        takes = [str(w) for w, flags in ALLOWED_BY_WINDOW.items() if flag in flags]
        raise PlanError(
            f"{flag} is a window {' and '.join(takes)} argument and window {window} was asked for"
        )
    for flag in REQUIRED_BY_WINDOW[window]:
        if not values[flag]:
            raise PlanError(f"window {window} needs {flag} and it was not given")


def _read_inventory(path: Path, run: dict | None, run_folder: Path) -> list[dict]:
    """
    The inventory's rows, once its drawing issue agrees with the run file: an inventory taken for
    another issue, one taken for the current set in a pass on one issue, and one taken for an issue
    in a folder with no run file are each refused, since the plan would read a sheet list that is
    not the pass's own.
    """
    data = _read_json(path, "the inventory file")
    if not isinstance(data, dict) or not isinstance(data.get("sheets"), list):
        raise PlanError(f"{path} is not an inventory file written by this script")
    issue = data.get("drawingIssue")
    if issue is not None and (
        not isinstance(issue, dict)
        or not isinstance(issue.get("deliveryId"), str)
        or not isinstance(issue.get("readFrom"), list)
    ):
        raise PlanError(f"{path}: `drawingIssue` is not a delivery id and the deliveries it read from")
    if run is None and issue is not None:
        raise PlanError(
            f"{path} was taken for drawing issue {issue['deliveryId']}, and {run_folder} holds no "
            f"{RUN_FILE} naming the pass on it"
        )
    if run is not None and issue is None:
        raise PlanError(
            f"{path} was taken for the current set, and {RUN_FILE} names drawing issue "
            f"{run['deliveryId']}: fetch its grid with set_grid's deliveryId and take the inventory again"
        )
    if run is not None and (
        issue["deliveryId"] != run["deliveryId"] or sorted(issue["readFrom"]) != sorted(run["readFrom"])
    ):
        raise PlanError(
            f"{path} was taken for drawing issue {issue['deliveryId']} read from "
            f"{', '.join(issue['readFrom'])}, and {RUN_FILE} names {run['deliveryId']} read from "
            f"{', '.join(run['readFrom'])}"
        )
    rows = data["sheets"]
    # Checked again here, not only where the file was written: a window plans off whatever
    # inventory.json is on disk, and a hand-edited one is still a file this script would subtract by
    # key.
    _check_unit_keys(rows, str(path))
    return rows


_TAGGED_UNIT_RE = re.compile(r"^i[1-9][0-9]*-")


def _refuse_lost_run_file(folder: Path) -> None:
    """
    A folder with no run file plans untagged, as the old layout does, so a pass folder that lost
    its run file would plan ids another pass already records under. Window 3 reads no inventory,
    so the folder is judged by what else it holds: an inventory taken for one drawing issue, or a
    ledger whose dispatch lines carry tagged unit ids.
    """
    inventory_path = folder / "inventory.json"
    if inventory_path.is_file():
        data = _read_json(inventory_path, "the inventory file")
        issue = data.get("drawingIssue") if isinstance(data, dict) else None
        if isinstance(issue, dict):
            raise PlanError(
                f"{folder} holds the inventory of drawing issue {issue.get('deliveryId')} and no "
                f"{RUN_FILE}, so this plan would carry no unit tag; put the pass's {RUN_FILE} back"
            )
    ledger = folder / LEDGER_FILE
    if ledger.is_file():
        try:
            text = ledger.read_text(encoding="utf-8")
        except Exception as e:
            raise PlanError(f"cannot read the run ledger at {ledger}: {e}") from e
        for raw in text.splitlines():
            parts = raw.split()
            if len(parts) >= 4 and parts[0] == "dispatch" and _TAGGED_UNIT_RE.match(parts[3]):
                raise PlanError(
                    f"{ledger} dispatched tagged unit {parts[3]} and {folder} holds no {RUN_FILE}, "
                    f"so this plan would carry no unit tag; put the pass's {RUN_FILE} back"
                )


def plan(args) -> str:
    window = args.window
    _check_arguments(args, window)

    # The run file sits in the run folder beside the ledger, so neither is an argument the lead can
    # forget. A folder in the old layout holds none, and its unit ids carry no tag.
    run = _read_run(args.out.parent)
    tag = run["unitTag"] if run else None
    if run is None:
        _refuse_lost_run_file(args.out.parent)

    rows: list[dict] = []
    show_file = False
    if window in (1, 2):
        rows = _read_inventory(args.inventory, run, args.out.parent)
        # A tagged pass's runner dispatches each sheet's file and verifies the unit on it, so the
        # line names the file even in a set of one file. The old layout names it only across several.
        show_file = len({_text(r.get("fileId")) for r in rows}) > 1 or tag is not None

    window_1_path: Path | None = None
    if window == 1:
        includes = [_split_pattern_argument(raw, "--include") for raw in (args.include or [])]
        excludes = [_split_pattern_argument(raw, "--exclude") for raw in (args.exclude or [])]
        result = _window_1(rows, includes, excludes, tag)
        # The run folder is the folder the plan file sits in; window 2 subtracts this file rather
        # than recomputing window 1's selection from arguments it might not be given identically.
        window_1_path = args.out.parent.joinpath(*WINDOW_1_FILE)
    elif window == 2:
        keys, selected, excluded, repeated_sets, left_with_number = _read_window_1(
            args.window_1, rows, tag
        )
        only = [_split_pattern_argument(raw, "--only") for raw in (args.only or [])]
        result = _window_2(rows, keys, selected, excluded, only, tag)
        result["repeatedSets"] = repeated_sets
        result["leftWithNumber"] = left_with_number
        result["repeatedRead"] = _read_repeated_read(args.out.parent / LEDGER_FILE, repeated_sets)
    else:
        packages = _read_packages(args.packages)
        # A pass on an addendum reviews only the packages it wrote on; a set's pass reviews them all,
        # and so does an addendum's pass where a unit wrote on a trade it did not name.
        written_on: set[str] | None = None
        unnamed: list[str] = []
        if run is not None and run["issue"] == "addendum":
            written_on, touched_units = _read_pass_trades(args.out.parent)
            unnamed = _units_touching_unnamed_trades(args.out.parent / LEDGER_FILE, touched_units)
        result = _window_3(packages, tag, None if unnamed else written_on)
        result["packages"] = len(packages)
        result["unnamed"] = unnamed

    ledger_path = args.out.parent / LEDGER_FILE
    result["verified"] = _read_ledger_verified(ledger_path, window)
    if window in (1, 2):
        # Both tiers sit in the run folder the plan file is written into, so neither is an argument
        # the lead can forget. A window 3 review id is derived from its own trade code and ordinal
        # and is already the same string on every run, so nothing here touches it.
        result["unitIds"] = _bind_unit_ids(
            result["passes"],
            rows,
            _read_ledger_units(ledger_path, window),
            _read_plan_file_units(_window_file(args.out.parent, window), window),
            ledger_path,
            {row["unitKey"] for row in result.get("deferred", [])},
            result["verified"],
        )
    if window == 1:
        # The same binding a sheet's id takes, over the repeated lines units alone, with the file
        # id standing for the sheet: so their ids keep, number and retire as a sheet's do.
        repeated_rows = [row for plan_pass in result["repeatedPasses"] for row in plan_pass["units"]]
        result["repeatedIds"] = _bind_unit_ids(
            result["repeatedPasses"],
            repeated_rows,
            {unit_id: (file_id,) for unit_id, file_id in _read_ledger_repeated(ledger_path).items()},
            {
                entry["unitId"]: _REPEATED_KEY_PREFIX + entry["fileId"]
                for entry in _read_previous_repeated_sets(_window_file(args.out.parent, 1))
            },
            ledger_path,
            set(),
            set(),
        )
    if window == 2:
        read_earlier_keys = {
            key for unit in result["unitIds"]["heldUnits"] if unit["verified"]
            for key in unit["sheetKeys"]
        }
        # Move only verified held sheets, preserving the partition and inventory order.
        result["readEarlier"] = [
            row for row in result["deferred"] if row["unitKey"] in read_earlier_keys
        ]
        result["deferred"] = [
            row for row in result["deferred"] if row["unitKey"] not in read_earlier_keys
        ]

    # The repeated lines passes read after the vocabulary's, each part a runner pass of its own.
    runner_passes = _runner_passes(window, result) + [
        [part] for part in _window_parts({"passes": result.get("repeatedPasses", [])})
    ]
    sheet_passes = [p for p in runner_passes if not _is_repeated_pass(p)]
    repeated_count = sum(len(p["units"]) for p in result.get("repeatedPasses", []))
    result["summed"] = _summed(
        window, runner_passes, args.out.parent, _read_ledger_pass_lines(ledger_path, window)
    )
    body, total_units, total_passes = _render(window, result, rows, show_file, runner_passes)
    payload = body.encode("utf-8")
    _write_atomically(args.out, payload)

    ids_clause = ""
    if window in (1, 2):
        ids = result["unitIds"]
        ids_clause = (
            f", ids kept {ids['kept']} (ledger {ids['ledger']}, plan file {ids['planFile']}), "
            f"ids new {ids['new']}, ids retired {ids['retired']}"
            + (f", ids held {ids['held']}" if ids["held"] else "")
        )

    written = len(payload)
    tag_clause = f", unit tag {tag} for drawing issue {run['deliveryId']}" if run else ""
    # What this run assigned, so a replan that the ledger cannot answer for still keeps a unit id
    # that was planned and never dispatched.
    assigned = (
        [
            {"id": row["unitId"], "unitKey": row["unitKey"]}
            for plan_pass in result["passes"]
            for row in plan_pass["units"]
        ]
        if window in (1, 2)
        else []
    )
    if window == 1:
        window_1_payload = (
            json.dumps(
                {
                    "window": 1,
                    "selected": result["selectedKeys"],
                    "excluded": result["excludedKeys"],
                    "units": assigned,
                    # The arguments this plan was written with, so a resume can run it again
                    # exactly rather than from whatever the lead still holds.
                    "include": [
                        {"pattern": block["pattern"], "reason": block["reason"]}
                        for block in result["includes"]
                    ],
                    "exclude": [
                        {"pattern": block["pattern"], "reason": block["reason"]}
                        for block in result["excludes"]
                    ],
                    # Kept apart from `selected`: window 2 subtracts sheets, and these are files.
                    "repeatedSets": [
                        {
                            "fileId": row["fileId"],
                            "unitId": row["unitId"],
                            "page": row["pageInPdf"],
                            "sheetsLeftOut": row["sheetsLeftOut"],
                        }
                        for plan_pass in result["repeatedPasses"]
                        for row in plan_pass["units"]
                    ],
                    # Only a tagged pass names its tag, so a window 1 file in the old layout is
                    # written as it always was; window 2 refuses a tag that differs.
                    **({"unitTag": tag} if tag else {}),
                },
                indent=2,
            )
            + "\n"
        ).encode("utf-8")
        _write_atomically(window_1_path, window_1_payload)
        written += len(window_1_payload)
        return (
            f"wrote {args.out} and {window_1_path}: window 1{tag_clause}, units {total_units}, passes "
            f"{total_passes}, {_fold_clause(sheet_passes)}, excluded {result['excludedCount']}, "
            f"unassigned {len(result['unassigned'])}{ids_clause}, "
            f"{_repeated_clause(result, repeated_count, runner_passes)}; "
            f"{written:,} bytes"
        )

    if window == 2:
        # Written on every window 2 run, a whole window as well as a slice, so the next run's plan
        # file tier always reads what this one assigned.
        window_2_path = _window_file(args.out.parent, 2)
        window_2_payload = (
            json.dumps(
                {
                    "window": 2,
                    "units": assigned,
                    "only": [
                        {
                            "pattern": block["pattern"],
                            "reason": block["reason"],
                            "sheets": [row["unitKey"] for row in block["sheets"]],
                        }
                        for block in result["only"]
                    ],
                    "deferredKeys": [row["unitKey"] for row in result["deferred"]],
                    "deferredCount": len(result["deferred"]),
                    "readEarlierKeys": [row["unitKey"] for row in result["readEarlier"]],
                },
                indent=2,
            )
            + "\n"
        ).encode("utf-8")
        _write_atomically(window_2_path, window_2_payload)
        written += len(window_2_payload)
        by_type = ", ".join(f"{name} {count}" for name, count in result["byType"])
        unordered = (
            "; sheet types the reading order does not name: " + ", ".join(result["unorderedTypes"])
            if result["unorderedTypes"]
            else ""
        )
        deferred = (
            f", sheets deferred {len(result['deferred'])} by --only" if result["deferred"] else ""
        )
        return (
            f"wrote {args.out} and {window_2_path}: window 2{tag_clause}, sheets {total_units}, passes "
            f"{total_passes}, {_fold_clause(sheet_passes)}, disciplines {result['disciplines']}, "
            f"{_every_sheet_once(result)}"
            f"{deferred}, sheets window 1 selected "
            f"{result['window1Selected']}, sheets window 1 left out {result['window1Excluded']}"
            f"{_left_with_number_clause(result)}, "
            f"sheets in the inventory {len(rows)}, sheets by type {by_type}, sheets typed other or "
            f"untyped {result['otherOrUntyped']}{ids_clause}, {_marked_clause(result)}{unordered}; "
            f"{written:,} bytes"
        )

    return (
        f"wrote {args.out}: window 3{tag_clause}, packages {result['packages']}, reviews {result['reviews']}, "
        f"passes {total_passes}, trades {result['trades']}, "
        f"packages sharing a trade: {result['sharedCount']} "
        f"({_named(result['sharedCodes']) if result['sharedCodes'] else 'none'})"
        + (f", packages left out {len(result['leftOut'])}, nothing this pass wrote on their trade"
           if result["partial"] else "")
        + (f", every package reviewed: units {', '.join(result['unnamed'])} updated a row or raised a "
           f"Question and named no trade they touched" if result["unnamed"] else "")
        + f"; {written:,} bytes"
    )


# --------------------------------------------------------------------------- #
# issue: which pass the lead resumes or starts
# --------------------------------------------------------------------------- #

def _read_deliveries(path: Path) -> list[dict]:
    """
    The `list_drawing_deliveries` answer, copied to disk, in delivery order. Each delivery's
    `issue` is read as the server gives it: set, addendum, or null while its sheet numbers are
    still being read or where it holds none. Anything else is a shape change, refused by name.
    """
    data = _read_json(path, "the deliveries file")
    listed = data.get("deliveries") if isinstance(data, dict) else None
    if not isinstance(listed, list):
        raise PlanError(f"{path} carries no `deliveries` array")
    deliveries: list[dict] = []
    for index, row in enumerate(listed, 1):
        if not isinstance(row, dict) or not isinstance(row.get("id"), str) or not row["id"]:
            raise PlanError(f"{path}: delivery {index} carries no `id`")
        if row.get("issue") not in ("set", "addendum", None):
            raise PlanError(
                f"{path}: delivery {row['id']} reads as {row.get('issue')!r}, which is neither a set "
                f"nor an addendum"
            )
        if not isinstance(row.get("stillReading"), bool):
            raise PlanError(
                f"{path}: delivery {row['id']} says {row.get('stillReading')!r} for `stillReading`, "
                f"which is neither true nor false"
            )
        deliveries.append(row)
    return deliveries


def _phase_lines(ledger: Path) -> list[str] | None:
    """A ledger's `phase:` lines, or None where the folder holds no ledger."""
    if not ledger.is_file():
        return None
    try:
        text = ledger.read_text(encoding="utf-8")
    except Exception as e:
        raise PlanError(f"cannot read the run ledger at {ledger}: {e}") from e
    return [line.strip() for line in text.splitlines() if line.strip().startswith(PHASE_PREFIX)]


def _label(row: dict) -> str:
    return _text(row.get("label")) or _text(row.get("id"))


def issue(runs: Path, deliveries_path: Path) -> str:
    """
    One line naming what the lead does next on this project, read off the project's run folders
    and its delivery list:

      resume  a pass in flight, whatever has landed since, since a later delivery never interrupts
              a pass. A pass on one drawing issue is in flight from its run file until its ledger
              closes out; the old layout's own ledger, in the project folder itself, is in flight
              from its first `phase:` line until it closes out. Two in flight is a refusal.
      wait    a delivery still being read for its sheet numbers, which may yet be a new set.
      start   the latest set, where no pass names it, or else the earliest addendum of it no pass
              read, with the run folder and the next unit tag.
      none    nothing to start: no delivery reads as a set, or the latest set and every addendum of
              it have their pass.

    Only the latest set is started. An earlier set with no pass of its own stays unread unless the
    estimator asks for it, since a later set already prints its sheets.

    The pass in flight is named before the delivery list is read at all, so a delivery the list
    gives in a shape this script does not know never holds a pass up.
    """
    root_phases = _phase_lines(runs / LEDGER_FILE)
    root_state = None
    if root_phases:
        closed = any(line == CLOSED_OUT_LINE for line in root_phases)
        root_state = "closed" if closed else "open"

    passes: list[tuple[Path, dict, bool]] = []
    if runs.is_dir():
        for child in sorted(runs.iterdir()):
            if not child.is_dir():
                continue
            run = _read_run(child)
            if run is None:
                if (child / LEDGER_FILE).is_file():
                    raise PlanError(
                        f"{child} holds a run ledger and no {RUN_FILE}, so nothing says which "
                        f"drawing issue its pass read"
                    )
                continue
            phases = _phase_lines(child / LEDGER_FILE) or []
            passes.append((child, run, any(line == CLOSED_OUT_LINE for line in phases)))

    in_flight = [f"{run['deliveryId']} in {child}" for child, run, closed in passes if not closed]
    if root_state == "open":
        in_flight.insert(0, f"the pass in {runs} with no drawing issue named")
    if len(in_flight) > 1:
        raise PlanError(
            f"{len(in_flight)} passes are in flight on this project ({'; '.join(in_flight)}); a "
            f"project runs one pass at a time"
        )
    if root_state == "open":
        return f"resume {runs}: the pass in this folder's own ledger, which names no drawing issue"
    for child, run, closed in passes:
        if not closed:
            return (
                f"resume {child}: the pass on drawing issue {run['deliveryId']}, {run['label']}, "
                f"a {run['issue']}, unit tag {run['unitTag']}"
            )

    deliveries = _read_deliveries(deliveries_path)
    reading = next((row for row in deliveries if row["stillReading"]), None)
    if reading is not None:
        return (
            f"wait {reading['id']}: {_label(reading)} is still being read for its sheet numbers, so "
            f"it is neither a set nor an addendum yet"
        )
    sets = [row for row in deliveries if row.get("issue") == "set"]
    if not sets:
        return "none: no drawing delivery reads as a set yet"
    latest = sets[-1]
    covered = {d for _child, run, _closed in passes for d in [run["deliveryId"], *run["readFrom"]]}
    earlier = f"; the earlier pass in {runs} names no drawing issue" if root_state == "closed" else ""
    number = 1 + max((int(run["unitTag"][1:]) for _child, run, _closed in passes), default=0)
    if latest["id"] not in covered:
        count = latest.get("sheetCount")
        return (
            f"start {latest['id']}: {_label(latest)}, a set of {count} sheet"
            f"{'' if count == 1 else 's'}; run folder {runs / latest['id']}, unit tag i{number}{earlier}"
        )
    # An addendum of the latest set that landed after the set's pass gets a partial pass of its own,
    # the earliest first, so a later addendum's pass reads the record the earlier one left.
    waiting = [
        row for row in deliveries
        if row.get("issue") == "addendum" and row.get("setId") == latest["id"] and row["id"] not in covered
    ]
    if waiting:
        row = waiting[0]
        count = row.get("sheetCount")
        more = f"; {len(waiting) - 1} more addenda of it after this one" if len(waiting) > 1 else ""
        # No note about a pass in the old layout: that pass read some set, and an addendum's pass
        # reads only the addendum's own sheets, so nothing it reads can be a set already scoped.
        return (
            f"start {row['id']}: {_label(row)}, an addendum of {_label(latest)} printing {count} "
            f"sheet{'' if count == 1 else 's'}; run folder {runs / row['id']}, unit tag i{number}"
            f"{more}"
        )
    return (
        f"none: the latest set {latest['id']}, {_label(latest)}, has its pass, and every addendum "
        f"of it was read in a pass"
    )


# --------------------------------------------------------------------------- #
# Entry point
# --------------------------------------------------------------------------- #

def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Turn a fetched sheet grid into plan counts, and the record into a read plan.",
    )
    sub = parser.add_subparsers(dest="mode", required=True)

    inv = sub.add_parser("inventory", help="read the grid files and write the counts")
    inv.add_argument("--grid", required=True, type=Path, help="the grid file, or the directory holding the grid pages")
    inv.add_argument(
        "--expect-count", required=True, type=int,
        help="the set count read from the summary-only set_grid call; the run refuses unless the rows total it",
    )
    inv.add_argument("--out-dir", required=True, type=Path, help="where inventory.md and inventory.json are written")

    win = sub.add_parser("plan", help="write one window's read plan")
    win.add_argument("--window", required=True, type=int, choices=(1, 2, 3), help="which window to plan")
    win.add_argument("--inventory", type=Path, help="windows 1 and 2: inventory.json from the inventory mode")
    win.add_argument(
        "--window-1", type=Path,
        help="window 2 only: plan/window-1.json, the unit keys window 1 selected and left out",
    )
    win.add_argument("--packages", type=Path, help="window 3 only: the solicitation_list_packages response on disk")
    win.add_argument("--kinds", type=Path, help=argparse.SUPPRESS)
    win.add_argument("--index", type=Path, help=argparse.SUPPRESS)
    win.add_argument(
        "--include", action="append", metavar="PATTERN:REASON",
        help="window 1 only: a sheet number pattern to read anyway, and why; repeatable",
    )
    win.add_argument(
        "--exclude", action="append", metavar="PATTERN:REASON",
        help="window 1 only: a sheet number pattern to leave out, and why; repeatable",
    )
    win.add_argument(
        "--only", action="append", metavar="PATTERN:REASON",
        help=(
            "window 2 only: a sheet number pattern to read in this run, and why; every other sheet "
            "is deferred to the next window 2 plan run without it; repeatable"
        ),
    )
    win.add_argument("--out", required=True, type=Path, help="the read plan file to write")

    nxt = sub.add_parser("issue", help="name the pass to resume, or the drawing issue to start a pass on")
    nxt.add_argument("--runs", required=True, type=Path, help="the project's folder, holding one run folder per pass")
    nxt.add_argument(
        "--deliveries", required=True, type=Path,
        help="the list_drawing_deliveries answer on disk, in delivery order",
    )

    args = parser.parse_args(argv)

    try:
        if args.mode == "inventory":
            print(inventory(args.grid, args.expect_count, args.out_dir))
        elif args.mode == "issue":
            print(issue(args.runs, args.deliveries))
        else:
            print(plan(args))
    except PlanError as e:
        print(f"plan_inventory: {e}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
