"""
names_scan.py: check that a scope run's lists of new item names are whole, then find the names two
units wrote alike.

Each pass runner writes, for every unit it verifies, one line per subject the unit's `verify_unit`
answer lists under the unit's prefix, into the pass's names file, `<run folder>/names/<pass id>.txt`:

    <unit id>\t<subject>\t<name>

and, for a unit whose prefix holds no subject on the record, one line `<unit id>\tnone`. The
names come from the record's answer, never from a reader's report. A line may be written twice; a
subject counts once, its last line's name standing.

The scan reads the names off every file in the names folder, whichever pass wrote them, since a
replan can move a unit to another pass after it was verified.

Usage:

    python names_scan.py pass <ledger> <window> <pass id> --plan <read-plan> --names-dir <dir>
    python names_scan.py boundary <ledger> <window> --names-dir <dir>

pass: every unit of the pass's plan block whose latest `verified` line in the window reads
`result ok` must have as many distinct subjects on the names files as that line's `items`. Where
one has fewer, or more, the scan refuses (exit 2) and names each unit and its two counts. Otherwise
it prints a `note` line for each unit of the pass holding a name alike with another unit of the
pass that no overlap note on the ledger joins it to yet, ready to append:

    note <window> <pass> - overlap <name> in <unit> and <unit>

boundary: the same check over every unit of the window verified ok, and every unit of the window
dispatched whose latest read did not verify ok (a mismatch, or no `verified` line) must have at
least one line, its names off the record or its `none` line, since its rows stay on the record
whatever its check found. Where any is short, the scan refuses (exit 2) and names each unit with
its pass, grouped by pass. Otherwise it prints a `note` line for each unit of the window holding
a name alike with another unit that no overlap note on the ledger joins it to yet, whichever pass
each unit ran or was verified in, so a unit a replan moved is compared with every other:

    note <window> boundary - overlap <name> in <unit> and <unit>

and last, always:

    note <window> boundary - overlap scan read <n> new item names, every unit of <u> in <p> passes

Two names are alike when they read the same in lower case with every run of characters other
than letters and digits taken as one space.

Exit codes: 0 the check passed and the lines are printed; 1 a named failure (a file missing or a
line in no shape); 2 the names are not whole, the refusal on stderr naming the units.

Grounding role: reads files and compares strings. It reads no record; the counts it holds the
names to are the ones the runner verified against the record.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

# Units one refusal names, so a run with many lists missing names a batch the runner can write.
NAMED_AT_MOST = 20
# An overlap note's clause, as this scan writes it: the name, then the two units.
_NOTED_RE = re.compile(r"^overlap (.+) in (\S+) and (\S+)$")


class ScanError(Exception):
    pass


class NotWhole(Exception):
    pass


def normal(name: str) -> str:
    return re.sub(r"[^0-9a-z]+", " ", name.lower()).strip()


def read_ledger(path: Path, window: str) -> dict:
    """Each unit of the window: its pass, its latest verified line's items and result, its reads."""
    if not path.is_file():
        raise ScanError(f"no ledger at {path}")
    units: dict[str, dict] = {}
    # Each overlap already on the ledger, as its name read alike and the two units it names.
    noted: set[tuple[str, frozenset[str]]] = set()
    # Only whole lines, each ending in a newline, as the summary script reads them, so a line still
    # being appended is not read until it is whole.
    data = path.read_bytes()
    whole = data[: data.rfind(b"\n") + 1].decode("utf-8")
    for number, raw in enumerate(whole.splitlines(), 1):
        parts = raw.split()
        if len(parts) < 4 or parts[0] not in ("dispatch", "verified", "note") or parts[1] != window:
            continue
        if parts[0] == "note":
            overlap = _NOTED_RE.match(" ".join(parts[4:]))
            if overlap:
                noted.add((normal(overlap.group(1)), frozenset((overlap.group(2), overlap.group(3)))))
            continue
        unit = units.setdefault(parts[3], {"pass": parts[2], "verified": None, "since": False})
        if parts[0] == "dispatch":
            unit["since"] = True
            if unit["verified"] is None:
                unit["pass"] = parts[2]
            continue
        rest = parts[4:]
        try:
            items = int(rest[rest.index("items") + 1])
            result = rest[rest.index("result") + 1]
        except (ValueError, IndexError):
            raise ScanError(f"{path} line {number}: a verified line with no whole `items` or no `result`") from None
        unit.update({"pass": parts[2], "verified": {"items": items, "result": result}, "since": False})
    return {"units": units, "noted": noted}


def read_names(folder: Path) -> dict[str, dict]:
    """
    Every unit's subjects and names off every names file, and the units with a `none` line. A line
    with no tab is a name alone, the shape an earlier plugin wrote, which names no unit and so
    counts for none: the scan then refuses and the runner writes the unit's lines off the record.
    """
    if not folder.is_dir():
        return {}
    found: dict[str, dict] = {}
    for path in sorted(folder.glob("*.txt")):
        for number, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            if not raw.strip() or "\t" not in raw:
                continue
            fields = raw.split("\t")
            unit = fields[0].strip()
            entry = found.setdefault(unit, {"subjects": {}, "none": False, "files": set()})
            entry["files"].add(path.name)
            if len(fields) == 2 and fields[1].strip() == "none":
                entry["none"] = True
                continue
            if len(fields) != 3:
                raise ScanError(
                    f"{path} line {number}: not `<unit id>\\t<subject>\\t<name>` or `<unit id>\\tnone`"
                )
            subject = fields[1].strip()
            if not subject.startswith(f"scopeItem:{unit}-"):
                raise ScanError(f"{path} line {number}: {subject} is not under unit {unit}'s prefix scopeItem:{unit}-")
            entry["subjects"][subject] = fields[2].strip()
    return found


def plan_units(plan: Path, window: str, pass_id: str) -> list[str]:
    """The unit ids of the pass's block in the read plan, read as pass_summary reads them."""
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    import pass_summary  # noqa: E402

    try:
        block = pass_summary.read_plan(plan, pass_summary.parse_window(window), pass_id)
    except pass_summary.SummaryError as e:
        raise ScanError(str(e)) from e
    return list(block["units"])


def short_units(units: dict[str, dict], names: dict[str, dict], wanted: list[str], whole_only: bool) -> list[str]:
    """Each unit of `wanted` whose names are not whole, as one clause naming its counts."""
    short: list[str] = []
    for unit_id in wanted:
        unit = units.get(unit_id)
        if unit is None:
            continue
        held = names.get(unit_id, {"subjects": {}, "none": False})
        count = len(held["subjects"])
        verified = unit["verified"]
        if verified is not None and verified["result"] == "ok" and not unit["since"]:
            if count != verified["items"]:
                short.append(f"{unit_id} (pass {unit['pass']}): {count} names of {verified['items']} items")
        elif not whole_only and count == 0 and not held["none"]:
            why = "its latest check read mismatch" if verified is not None else "it has no verified line"
            short.append(f"{unit_id} (pass {unit['pass']}): no names, {why}")
    return short


def overlaps(scope: list[str], names: dict[str, dict], noted: set[tuple[str, frozenset[str]]], window: str, where: str) -> list[str]:
    """
    Notes enough that every unit in scope holding a name alike is named beside another holder,
    through the ledger's overlap notes or these. Holders already joined by notes, whichever scan
    wrote them, are one group; each other group gets one note joining it to the first.
    """
    holders: dict[str, list[tuple[str, str]]] = {}
    for unit_id in sorted(set(scope)):
        seen: set[str] = set()
        for name in names.get(unit_id, {"subjects": {}})["subjects"].values():
            key = normal(name)
            if key and key not in seen:
                seen.add(key)
                holders.setdefault(key, []).append((unit_id, name))
    lines: list[str] = []
    for key in sorted(holders):
        held = holders[key]
        if len(held) < 2:
            continue
        # Every unit the ledger's notes join on this name, in scope or not, so two holders joined
        # through a unit outside the scope count as joined.
        group = {unit: unit for unit, _ in held}
        for noted_key, pair in noted:
            if noted_key == key:
                for unit in pair:
                    group.setdefault(unit, unit)

        def root(unit: str) -> str:
            while group[unit] != unit:
                unit = group[unit]
            return unit

        for noted_key, pair in noted:
            if noted_key == key and len(pair) == 2:
                a, b = sorted(pair)
                group[root(b)] = root(a)
        first_unit, first_name = held[0]
        joined = {root(first_unit)}
        for unit, _ in held[1:]:
            if root(unit) in joined:
                continue
            joined.add(root(unit))
            lines.append(f"note {window} {where} - overlap {first_name} in {first_unit} and {unit}")
    return lines


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Check a scope run's new item names are whole, then find names alike.")
    sub = parser.add_subparsers(dest="mode", required=True)
    one = sub.add_parser("pass")
    one.add_argument("ledger", type=Path)
    one.add_argument("window")
    one.add_argument("pass_id")
    one.add_argument("--plan", type=Path, required=True)
    one.add_argument("--names-dir", type=Path, required=True)
    edge = sub.add_parser("boundary")
    edge.add_argument("ledger", type=Path)
    edge.add_argument("window")
    edge.add_argument("--names-dir", type=Path, required=True)
    args = parser.parse_args(argv)

    try:
        if args.window not in ("1", "2", "3"):
            raise ScanError(f"window {args.window!r}: the names scan runs in windows 1, 2 and 3")
        ledger = read_ledger(args.ledger, args.window)
        names = read_names(args.names_dir)
        units = ledger["units"]
        if args.mode == "pass":
            wanted = plan_units(args.plan, args.window, args.pass_id)
            short = short_units(units, names, wanted, whole_only=True)
            if short:
                raise NotWhole(
                    f"pass {args.pass_id}: the names of {len(short)} unit(s) are not whole; write each unit's "
                    f"lines off its verify_unit answer and run this again: " + "; ".join(short)
                )
            for line in overlaps([u for u in wanted if u in units], names, ledger["noted"], args.window, args.pass_id):
                print(line)
            return 0

        wanted = sorted(units)
        short = short_units(units, names, wanted, whole_only=False)
        if short:
            by_pass: dict[str, list[str]] = {}
            for clause in short:
                pass_id = clause.split("(pass ", 1)[1].split(")", 1)[0]
                by_pass.setdefault(pass_id, []).append(clause)
            named = short[:NAMED_AT_MOST]
            more = f"; and {len(short) - len(named)} more, named once these are written" if len(short) > len(named) else ""
            raise NotWhole(
                f"window {args.window}: the names of {len(short)} unit(s) in {len(by_pass)} pass(es) are not whole: "
                + "; ".join(named) + more
            )
        for line in overlaps(wanted, names, ledger["noted"], args.window, "boundary"):
            print(line)
        total = sum(len(names.get(u, {"subjects": {}})["subjects"]) for u in wanted)
        passes = len({units[u]["pass"] for u in wanted})
        print(
            f"note {args.window} boundary - overlap scan read {total} new item names, every unit of "
            f"{len(wanted)} in {passes} passes"
        )
        return 0
    except NotWhole as e:
        print(f"names_scan: {e}", file=sys.stderr)
        return 2
    except ScanError as e:
        print(f"names_scan: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
