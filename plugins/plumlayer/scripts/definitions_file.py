"""
definitions_file.py: turn one code list a schedule or legend prints into the batch file
`record_batch_file` takes, so a long list goes on the record whole in one call.

    sh run.sh definitions_file.py '<run folder>' <unit id> <kind> [<part>] <<'EOF'
    kind <kind>
    sheet <sheet number>
    file <fileId>
    page <pageInPdf>
    columns <column>	<column>	...
    <code>	<cell>	<cell>	...	<x0,y0,x1,y1 or ->
    EOF

The first four lines name the list's kind (the same kind as the argument), the sheet and page it
is printed on and the drawing file of that page. The `columns` line names each column the list
prints, in order, each one word in camel case as the reader writes a definition's column, a tab
between each. Then one line per code: the code, its cells in the columns' order, and last the box
of the schedule row or legend line it was read from, its four page points as the page text gave
them, or `-` where no line of the page's text carries it. Tabs separate the fields. A blank cell is
not written, and a row may stop short of the last columns where those cells are blank. A code
whose every cell is blank or unreadable has nothing to write: the reader leaves it out of the table
and names it on the kind's `code lists:` entry as `<n> not readable: <codes>`.

Writes `<run folder>/batches/<unit id>-<kind>.jsonl`, or `<unit id>-<kind>-<part>.jsonl` for one
part of a list too long for one file, replaced whole: one entry per cell that is not blank, its
subject `<kind>:<code>`, its column as written, the cell's text, the reader's instrument, and the
page as evidence, with the box where the line gave one. A kind's declaration and its trade stay
in the reader's own batch. Prints one line, `entries <n> codes <m> file <path>`.

Refuses, in one line on stderr and with nothing written: a header line missing or given twice, a
kind other than the argument's, a page that is not a whole number above 0, a column that is not
one word in camel case or is named twice, a code given twice, a row with more cells than columns,
a code with no cell to write (its refusal says to leave it out and name it as not readable), a box
that is not four numbers or `-`, and a file of more than 20,000 entries, the most one
`record_batch_file` call takes.

Exit codes: 0 written; 1 a refusal, one line on stderr; 2 the call itself was malformed.

Grounding role: copies what the reader read off the page into the record's entry shape. It reads
no record and no page, and no line it writes says a page was read.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

import ledger

INSTRUMENT = "scope-vocabulary-reader"
MAX_ENTRIES = 20_000
HEADERS = ("kind", "sheet", "file", "page")
BATCHES_FOLDER = "batches"
_CAMEL_RE = re.compile(r"^[a-z][A-Za-z0-9]*$")
_NUMBER_RE = re.compile(r"^-?[0-9]+(?:\.[0-9]+)?$")


class DefinitionsError(Exception):
    """A refusal with a one-line reason, reported on stderr and exiting 1."""


def _number(text: str) -> int | float:
    # Sent as the page text gave it: a whole number stays whole.
    return int(text) if re.fullmatch(r"-?[0-9]+", text) else float(text)


def _box(text: str, code: str) -> list[int | float] | None:
    if text == "-":
        return None
    parts = [p.strip() for p in text.split(",")]
    if len(parts) != 4 or not all(_NUMBER_RE.match(p) for p in parts):
        raise DefinitionsError(f"the box for code {code} is not four numbers or -: {text}")
    box = [_number(p) for p in parts]
    if box[0] > box[2] or box[1] > box[3]:
        raise DefinitionsError(f"the box for code {code} does not run from its lower corner to its upper one: {text}")
    return box


def entries_of(text: str, kind: str) -> tuple[list[dict], int]:
    """The entries the list on stdin writes, and how many codes it holds."""
    header: dict[str, str] = {}
    columns: list[str] | None = None
    page = 0
    entries: list[dict] = []
    codes: set[str] = set()
    for number, raw in enumerate(text.splitlines(), 1):
        line = raw.rstrip("\r")
        if not line.strip():
            continue
        if columns is None:
            words = re.split(r"[ \t]", line.strip(), maxsplit=1)
            key, value = words[0], (words[1].strip() if len(words) > 1 else "")
            if key == "columns":
                missing = [h for h in HEADERS if h not in header]
                if missing:
                    raise DefinitionsError(f"the list names no {', '.join(missing)} line before its columns")
                if header["kind"] != kind:
                    raise DefinitionsError(f"the list's kind is {header['kind']} and the call names {kind}")
                if not re.fullmatch(r"[1-9][0-9]*", header["page"]):
                    raise DefinitionsError(f"the page {header['page']} is not a whole number above 0")
                page = int(header["page"])
                columns = [c.strip() for c in re.split(r"[ \t]+", value)] if value else []
                if not columns:
                    raise DefinitionsError("the columns line names no column")
                for column in columns:
                    if not _CAMEL_RE.match(column):
                        raise DefinitionsError(f"the column {column!r} is not one word in camel case")
                    if columns.count(column) > 1:
                        raise DefinitionsError(f"the column {column} is named twice")
                continue
            if key not in HEADERS:
                raise DefinitionsError(f"line {number} is none of the kind, sheet, file, page or columns lines: {line.strip()[:60]}")
            if key in header:
                raise DefinitionsError(f"the {key} line is given twice")
            if not value:
                raise DefinitionsError(f"the {key} line is empty")
            header[key] = value
            continue
        fields = line.split("\t")
        code = fields[0].strip()
        if not code:
            raise DefinitionsError(f"line {number} has no code")
        if len(fields) < 2:
            raise DefinitionsError(f"code {code} has no box, or - for none, as its last field")
        if code in codes:
            raise DefinitionsError(f"code {code} is given twice")
        codes.add(code)
        cells = [c.strip() for c in fields[1:-1]]
        if len(cells) > len(columns):
            raise DefinitionsError(f"code {code} has {len(cells)} cells and the list {len(columns)} columns")
        box = _box(fields[-1].strip(), code)
        evidence: dict = {"sheet": header["sheet"], "pageInPdf": page, "fileId": header["file"]}
        if box is not None:
            evidence["locator"] = {"pageInPdf": page, "frame": "page-points", "bboxPts": box}
        written = 0
        for column, cell in zip(columns, cells):
            if not cell:
                continue
            entries.append({
                "subject": f"{kind}:{code}", "predicate": column, "value": cell,
                "sourceInstrument": INSTRUMENT, "evidence": evidence,
            })
            written += 1
        if not written:
            raise DefinitionsError(
                f"code {code} has no cell to write; leave it out of the table and name it on the "
                "kind's `code lists:` entry as not readable")
        if len(entries) > MAX_ENTRIES:
            raise DefinitionsError(
                f"the list comes to more than {MAX_ENTRIES} entries, the most one file takes; "
                "split its codes across parts and run once per part")
    if columns is None:
        raise DefinitionsError("the list has no columns line")
    if not codes:
        raise DefinitionsError("the list names no code")
    return entries, len(codes)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Write one code list as the batch file record_batch_file takes.")
    parser.add_argument("run_folder", type=Path)
    parser.add_argument("unit")
    parser.add_argument("kind")
    parser.add_argument("part", nargs="?", type=int)
    args = parser.parse_args(argv)
    try:
        if not _CAMEL_RE.match(args.kind):
            raise DefinitionsError(f"the kind {args.kind!r} is not one word in camel case")
        if args.part is not None and args.part < 1:
            raise DefinitionsError("a part is a whole number above 0")
        if not args.run_folder.is_dir():
            raise DefinitionsError(f"there is no run folder at {args.run_folder}")
        data = sys.stdin.buffer.read()
        try:
            text = data.decode("utf-8")
        except UnicodeDecodeError:
            raise DefinitionsError("the list on stdin is not UTF-8 text") from None
        if text.startswith("﻿"):
            text = text[1:]
        entries, count = entries_of(text, args.kind)
        path = args.run_folder / BATCHES_FOLDER / (
            f"{args.unit}-{args.kind}.jsonl" if args.part is None else f"{args.unit}-{args.kind}-{args.part}.jsonl")
        path.parent.mkdir(parents=True, exist_ok=True)
        body = "".join(json.dumps(entry, ensure_ascii=False) + "\n" for entry in entries)
        ledger.publish(path, body.encode("utf-8"))
    except (DefinitionsError, ledger.LedgerError) as e:
        print(f"definitions_file: {e}; nothing was written", file=sys.stderr)
        return 1
    print(f"entries {len(entries)} codes {count} file {path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
