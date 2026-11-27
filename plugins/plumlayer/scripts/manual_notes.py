"""
manual_notes.py: print one package's manual as its manual parts read it, for the package's review
and its standard lines unit in window 3 of a scope run.

    python manual_notes.py --run '<run folder>' --review <review unit id> [--start <n>]

Every page of a package's manual sections is read by the package's manual parts before its
review, and its standard lines are written by its standard lines unit, the last unit of the
package's chain (`plan_inventory.py`, window 3). This script reads the run folder alone, no record:

  plan/window-3.json     the package's chain and each part's spans;
  read-plan.md           its `## Manual sections not read`, each section or run of pages no unit
                         reads, with its reason, this package's lines;
  plan/spec-sections.json  the section list the lead copied from the record, for each section's
                         title and pages, and the count of sections on the project;
  plan/packages.json     the package's `manualSections`, so a section it lists that no part
                         reads still has its line;
  ledger.md             each unit's latest `verified` line and its skipped note, through
                         `unit_report.unit_history` and `plan_inventory.settled_units`;
  reports/               each unit's report of the read its latest `verified` line checked, chosen
                         as the pass summary chooses it (`pass_summary.report_of_read`).

A part's report is read only where its latest `verified` line reads ok and the report check holds
that report whole for its kind, its `spans read:` and `section lines:` held to the part's planned
spans as its runner held them. A part whose report of that read was written from the record is
printed as `not known, report written from the record`; a part whose latest `verified` line reads
mismatch, one with no `verified` line, and one skipped are printed as `not read`, with their
spans. A planned span the verified report leaves off its `spans read:` line, as a part does for a
section whose manual changed, left the package or was removed, is printed as `not read` with the
reason the part named for it on `sections not checked:`. A line in the report's shape is never
taken as proof that a section was read.

What it prints, in this order:

  sections on the project: <n>
  not read: <code> pages <a> to <b>, <the reason>              one per span or section, or `none`
  not known: <code> pages <a> to <b>, <the reason>
  left: <the part's unit id> | <its span> | <the items its section line leaves>
  silence: <the part's unit id> | <its span> | <the section, the products, the words searched>
  section <code>: <its title>, pages <a> to <b> of <fileId>   one per section the package lists,
                                                              a part's or not; one with no pages
                                                              says its pages are not known, and
                                                              one the section list lacks says so
  part <unit id>: <ok, not read or not known>
    section line: <the part's section line, whole>
    silent sections: / compared: / sections not checked: <each entry the part's report names>
  standard lines: <how the unit ended>, then each entry of its `standard lines:` line

The output stops before it passes CAP characters. Its last line then reads `cut at line <n> of <m>;
the rest: <the command with --start <n>>`, so the reader runs every continuation.

Exit codes: 0 printed; 1 a named failure, one line on stderr (no window 3 plan file, a review the
plan does not carry); 2 argparse rejected the invocation.

Grounding role: reads files and copies lines. It reads no record, and no line it prints says a
page was read that no verified report says was read.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import manual_parts  # noqa: E402
import pass_summary  # noqa: E402
import plan_inventory  # noqa: E402
import unit_report  # noqa: E402

CAP = 24_000
# A line of the read plan's `## Manual sections not read`, as plan_inventory.py writes it.
NOT_READ_LINE_RE = re.compile(r"^[1-9][0-9]*\. (\S+)(?: pages ([1-9][0-9]*) to ([1-9][0-9]*))? on (\S+), package \S+: (.+)$")
PART_ITEMS = ("silent sections", "compared", "sections not checked")
NOT_KNOWN = "not known, report written from the record"


class NotesError(Exception):
    pass


def _span_said(span: dict) -> str:
    return f"{span['code']} p{span['fromPage']}-p{span['toPage']} of {span['fileId']}" + (
        f" (section p{span['pageStart']}-p{span['pageEnd']})"
        if (span["fromPage"], span["toPage"]) != (span["pageStart"], span["pageEnd"]) else ""
    )


def _pages(span: dict) -> str:
    return f"{span['code']} pages {span['fromPage']} to {span['toPage']}"


def unit_state(run: Path, unit: str, kind: str, settled: set[str], skipped: dict[str, str],
               spans: list[str] | None = None) -> tuple[str, dict]:
    """
    `ok` with the report's sections, `not known`, `not read` or `skipped`, for one unit of the
    chain. A manual part's report is held to its planned spans, as its runner's check held it.
    """
    if unit in skipped:
        return "skipped", {}
    if unit not in settled:
        return "not read", {}
    history = unit_report.unit_history(run / pass_summary.LEDGER_NAME, "3", unit)
    if history["latest"] is None or history["latest"][1]["result"] != "ok":
        return "not read", {}
    read, _verified = history["latest"]
    path, restored, problems = pass_summary.report_of_read(
        run / pass_summary.REPORTS_FOLDER, unit, read, history["dispatches"], kind,
    )
    if problems:
        return ("not known" if restored else "not read"), {}
    text = unit_report.report_text(path.read_bytes()) or ""
    if spans is not None:
        broken, mismatches = unit_report.problems(text, kind, spans=spans)
        if broken or any(m.startswith(("spans", "section lines")) for m in mismatches):
            return "not held", {}
    return "ok", unit_report.sections(text, unit_report.LABELS[kind])


def _unread_reason(found: dict, code: str) -> str:
    """The reason a part named on `sections not checked:` for a section it left unread."""
    for entry in unit_report._report_items(found.get("sections not checked", [])):
        words = entry.split(None, 1)
        if words and words[0] == code and len(words) > 1:
            return words[1].strip()
    return "its manual part's report does not name these pages as read"


def _section_line(code: str, row: dict | None) -> str:
    """A section's title and pages off the section list, or what of them is not known."""
    if row is None:
        return f"section {code}: not on the section list, so its title and pages are not known"
    title = row.get("title") if isinstance(row.get("title"), str) and row.get("title") else None
    said = title or "no title on the section list"
    start, end, file_id = row.get("pageStart"), row.get("pageEnd"), row.get("fileId")
    if type(start) is int and type(end) is int and isinstance(file_id, str) and file_id:
        return f"section {code}: {said}, pages {start} to {end} of {file_id}"
    return f"section {code}: {said}, its pages are not known"


def notes(run: Path, review: str) -> list[str]:
    plan_path = run / "plan" / "window-3.json"
    try:
        plan = json.loads(plan_path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as e:
        raise NotesError(f"no window 3 plan file to read at {plan_path}: {e}") from e
    chain = next((c for c in plan.get("chains", []) if c.get("review") == review), None)
    if chain is None:
        raise NotesError(f"the window 3 plan carries no chain for {review}")
    try:
        listed = json.loads((run / "plan" / "spec-sections.json").read_text(encoding="utf-8"))
        sections = {row["csi"]: row for row in listed.get("sections", []) if isinstance(row, dict)}
    except (OSError, ValueError, KeyError):
        listed, sections = {}, {}
    settled, skipped = plan_inventory.settled_units(run / pass_summary.LEDGER_NAME, 3)

    not_read: list[str] = []
    not_known: list[str] = []
    left: list[str] = []
    silence: list[str] = []
    body: list[str] = []
    codes: list[str] = []
    # Every section the package lists, a part's or not: its `manualSections` off the package list
    # the plan was made from, then each section of this package's not read lines.
    listed_codes: list[str] = []
    try:
        packages = json.loads((run / "plan" / "packages.json").read_text(encoding="utf-8"))
        rows = packages.get("packages", []) if isinstance(packages, dict) else packages
        package = next((row for row in rows if isinstance(row, dict) and row.get("id") == chain.get("packageId")), None)
        listed_codes += manual_parts.section_codes(package) if package else []
    except (OSError, ValueError, AttributeError, TypeError, manual_parts.SectionError):
        pass
    # The read plan's own list of what no unit reads, this package's lines; a skipped part's pages
    # are named off the ledger below.
    try:
        plan_text = (run / "read-plan.md").read_text(encoding="utf-8")
    except OSError:
        plan_text = ""
    listing = plan_text.split("## Manual sections not read", 1)[-1].split("\n## ", 1)[0] if plan_text else ""
    for line in listing.splitlines():
        found = NOT_READ_LINE_RE.match(line.strip())
        own = found and re.fullmatch(re.escape(review) + r"(?:c-[1-9][0-9]*|s-1)?", found.group(4))
        if own and found.group(1) not in listed_codes:
            listed_codes.append(found.group(1))
        if own and found.group(5) != plan_inventory.NOT_READ_SKIPPED:
            pages = f" pages {found.group(2)} to {found.group(3)}" if found.group(2) else ""
            not_read.append(f"not read: {found.group(1)}{pages}, {found.group(5)}")
    standard = None
    for unit in chain["units"]:
        if unit["kind"] == plan_inventory.STANDARD_LINES_KIND:
            standard = unit["id"]
            continue
        spans = unit.get("sections", [])
        codes += [span["code"] for span in spans if span["code"] not in codes]
        planned = [manual_parts.span_text(span) for span in spans]
        state, found = unit_state(run, unit["id"], "manual", settled, skipped, planned)
        if state in ("not read", "skipped", "not held"):
            why = {
                "skipped": "its manual part was read twice and not confirmed",
                "not held": "its manual part's report does not hold its pages to the plan",
            }.get(state, "its manual part has no verified read")
            not_read += [f"not read: {_pages(span)}, {why}" for span in spans]
            body.append(f"part {unit['id']}: not read")
            continue
        if state == "not known":
            not_known += [f"not known: {_pages(span)}, {NOT_KNOWN}" for span in spans]
            body.append(f"part {unit['id']}: {NOT_KNOWN}")
            continue
        # A planned span the verified report did not read, as the part's definition has it leave a
        # section whose manual changed, left the package or was removed, is not read, with the
        # reason the part named for it.
        read = unit_report._report_items(found.get("spans read", []))
        unread = [span for span, text in zip(spans, planned) if text not in read]
        not_read += [f"not read: {_pages(span)}, {_unread_reason(found, span['code'])}" for span in unread]
        body.append(f"part {unit['id']}: ok" + (", and it read none of the pages named not read above" if unread else ""))
        for line in unit_report._report_items(found.get("section lines", [])):
            body.append(f"  section line: {line}")
            fields = unit_report._SECTION_LINE_RE.match(line)
            if fields and fields.group(4).strip() != "none":
                left.append(f"left: {unit['id']} | {fields.group(1)} | {fields.group(4).strip()}")
            if fields and fields.group(5).strip() != "none":
                silence.append(f"silence: {unit['id']} | {fields.group(1)} | {fields.group(5).strip()}")
        for label in PART_ITEMS:
            for entry in unit_report._report_items(found.get(label, [])):
                body.append(f"  {label}: {entry}")
    body = [_section_line(code, sections.get(code)) for code in dict.fromkeys([*listed_codes, *codes])] + body
    if standard is not None:
        state, found = unit_state(run, standard, "standard", settled, skipped)
        if state == "ok":
            entries = unit_report._report_items(found.get("standard lines", []))
            body.append(f"standard lines: written by {standard}" + ("" if entries else ", none printed"))
            body += [f"  {entry}" for entry in entries]
        elif state == "skipped":
            body.append("standard lines: not written, the standard lines unit was read twice and not confirmed")
        elif state == "not known":
            body.append(f"standard lines: {NOT_KNOWN}")
        else:
            body.append("standard lines: not known, the standard lines unit has no verified read")
    head = [f"sections on the project: {len(listed.get('sections', [])) if isinstance(listed, dict) else 0}"]
    head += not_read or ["not read: none"]
    head += not_known or ["not known: none"]
    head += left or ["left: none"]
    head += silence or ["silence: none"]
    return head + body


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Print a package's manual as its manual parts read it.")
    parser.add_argument("--run", required=True, type=Path)
    parser.add_argument("--review", required=True)
    parser.add_argument("--start", type=int, default=1)
    args = parser.parse_args(argv)
    try:
        lines = notes(args.run, args.review)
    except (NotesError, plan_inventory.PlanError, unit_report.ReportError) as e:
        print(f"manual_notes: {e}", file=sys.stderr)
        return 1
    size = 0
    start = max(1, args.start)
    for number in range(start, len(lines) + 1):
        line = lines[number - 1]
        if size + len(line) + 1 > CAP and number > start:
            print(
                f"cut at line {number} of {len(lines)}; the rest: python3 '{Path(__file__).resolve()}' "
                f"--run '{args.run}' --review {args.review} --start {number}"
            )
            return 0
        print(line)
        size += len(line) + 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
