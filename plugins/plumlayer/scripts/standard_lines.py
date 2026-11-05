"""
standard_lines.py: print the standard lines one bid package's review writes, and the name and records of each.

A standard line is one a sub's price carries that the documents rarely spell out, such as tax on
what he supplies or floor prep under resilient flooring. The plugin carries them one file per trade
under `skills/scope-run/standard-lines/`, each file a `# <trade>` title, a `Numbers:` line of the
catalog code prefixes the trade answers to, a `Home:` line naming its primary catalog numbers,
comma separated, the first first, an optional `Else:` line naming the title of the file whose
package takes this one where no package claims it by its Home numbers, and one table row per
line:

    | Kind | Line | Condition | Where to Look | Row Name |

The kind is one of Pricing, Incidental, Convention or Which Trade. A line with a blank condition
has none and lands on every package its file goes to. The row name is the short subject a row the
line writes is named by, at most 36 characters and with no comma. A Which Trade line names the
trades that carry its work after `by` or `with` and the trades it keeps the work off after `Not`;
each `by` or `with` starts one half of the work, and its row name carries one name per half, in
the line's order, separated by `; `. This script reads those files and nothing else.

    python standard_lines.py --package '<tradeCode>' \
        --all '<name>=<tradeCode>,<code>,<code>; <name>=<tradeCode>; ...'

        `--all` names every live package on the project, this one among them, by its name as the
        package list shows it, then its `tradeCode` and the codes in its `codes`, catalog ids as
        the catalog spaces them (`09 65 00`, `01 71 23.16`). Each trade file goes to one live
        package, the same way for every review:
        (a) a package one of whose codes is one of the file's Home numbers, a broader code that
        holds it or a narrower one under it; where several do, the Home number listed first, then
        within one Home number a `tradeCode` before a code in `codes`, then the code nearest the
        Home number (the Home number itself, then the nearest broader code, then the nearest
        narrower one), then the lowest `tradeCode`; a whole division code (`09 00 00`) counts here
        only where it is the Home number itself (`26` for electrical); else (b) a package with a
        Home number's division as a code (`03 00 00` for a file whose Home number is in 03), the
        Home number listed first, then a `tradeCode`, then the lowest; else the package the file its
        `Else:` line names goes to; else (c) the package whose codes hold the most of the file's
        numbers, ties to the lowest `tradeCode`. A file no package claims prints nothing. A code holds a number where its digits, its trailing `00` pairs dropped and the
        last `0` of a group code such as `09 60 00` dropped too, start the number, or where its
        full digits start with the number.

        It prints a `places:` line naming each trade file that goes to a live package and that
        package, then the lines of the files that go to `--package`, each line once under the first
        file carrying it, with its kind, the row's name, its condition and where to look; a line
        with no condition also prints the instrument its entries are written with,
        `trade-convention:<file name>@<plugin version>`. The row's name is `<Row Name>, <package
        name>` where that fits in 80 characters, otherwise `<Row Name>, <tradeCode>`. A Which Trade
        line also prints the trades it involves (the trades of the files carrying it, the trades it
        names and the trades its condition names, by the same words in any case), each with the
        package it goes to, and each half with whether this package writes it and the name of its
        row. Where this package writes it, that is this package's row, with the `packageRole`
        records to write beside it. Where it does not, it prints `carried by` or `left to` the
        package that writes it and the row that package writes, named by that package's name,
        several separated by `; `, so a review the paper gives the half to cites onto that row.
        Where no file goes to the package it prints NONE_LINE alone. `--folder` reads the files from another folder.

        Who writes a half: one carrier, its package, with an `exclusion` record on each other
        involved package, counterparty the carrier's package; where the carrier has no package, the
        lowest other involved package, with an exclusion on each involved package, its own among
        them, counterparty the carrier's catalog id. Trades joined by `or`: the lowest of their
        packages, with a `candidate` record on each other one and an exclusion, no counterparty, on
        each involved package outside them. Trades joined by `and`, or `Each MEP Trade`: each of
        their packages writes its own row, with an exclusion on each involved package outside them,
        counterparty itself. Trades joined by `or` or `and` with no package among them: the lowest
        other involved package, with an exclusion on each involved package, no counterparty. The
        owner or a utility alone: the package that writes the line's other half, with an exclusion
        on its own trade, counterparty `owner`.

Exit codes:
  0  printed.
  1  a named failure, one line on stderr: a code that is not a catalog id, a package given twice or
     not on `--all`, a package with no name or no `tradeCode`, a lines folder that is missing or
     empty, a file out of shape (no title, no `Numbers:` or `Home:` line, a number that is not
     pairs of digits, a Home number
     none of the file's numbers starts or named twice, an `Else:` line naming no other file or one
     with an `Else:` line of its own, a table header other than the one above, a row of another
     number of cells, a kind outside the four, a blank line or row name, a row name over 36
     characters, with a comma or used twice, a Which Trade line naming a trade this script does
     not know or with another number of row names than halves), two files claiming one number,
     one line read two ways across files, one row name used by two lines, or a plugin version
     that cannot be read.
  2  argparse rejected the invocation.

Grounding role: reads files and copies their text, and assigns files to packages by their numbers.
Nothing here judges whether a line's condition holds on a job.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
LINES_FOLDER = HERE.parent / "skills" / "scope-run" / "standard-lines"
PLUGIN_MANIFEST = HERE.parent / ".claude-plugin" / "plugin.json"

KINDS = ("Pricing", "Incidental", "Convention", "Which Trade")
HEADER = "| Kind | Line | Condition | Where to Look | Row Name |"
NONE_LINE = "no standard lines for this package"
ROW_NAME_MAX = 36
NAME_MAX = 80

CODE_RE = re.compile(r"\d{2} \d{2} \d{2}(?:\.\d{2})?")
NUMBER_RE = re.compile(r"\d{2}(?: \d{2}){0,2}")

# The words a Which Trade line names a trade by, and the trade file each is.
TRADE_WORDS: dict[str, tuple[str, ...]] = {
    "Appliances": ("appliances",),
    "Casework": ("casework",),
    "Concrete": ("cast-in-place-concrete",),
    "Countertops": ("countertops",),
    "Waterproofing": ("dampproofing-and-waterproofing",),
    "Joint Sealants": ("joint-sealants",),
    "Demolition": ("demolition",),
    "Drywall": ("drywall",),
    "Sitework": ("earthwork-and-sitework",),
    "Earthwork": ("earthwork-and-sitework",),
    "Paving": ("paving",),
    "Site Utilities": ("site-utilities",),
    "Doors": ("doors-frames-and-hardware",),
    "Electrical": ("electrical",),
    "Elevators": ("elevators",),
    "Elevator Company": ("elevators",),
    "Elevator Vendor": ("elevators",),
    "Finish Carpentry": ("finish-carpentry",),
    "Fire Protection": ("fire-protection",),
    "Firestopping": ("firestopping",),
    "Flooring": ("flooring",),
    "Gypsum Underlayment": ("gypsum-underlayment",),
    "HVAC": ("hvac",),
    "Insulation": ("insulation",),
    "Landscaping": ("landscaping-and-site-improvements",),
    "Masonry": ("masonry",),
    "Metal Railings": ("metal-railings",),
    "Millwork": ("millwork-architectural-woodwork",),
    "Misc Metals": ("miscellaneous-metals",),
    "Plumbing": ("plumbing",),
    "Roofing": ("roofing",),
    "Framing": ("rough-carpentry",),
    "Rough Carpentry": ("rough-carpentry",),
    "Siding": ("siding-and-cladding",),
    "Specialties": ("specialties",),
    "Fireproofing": ("spray-fireproofing",),
    "Glazing": ("storefront-and-glazing",),
    "Storefront Sub": ("storefront-and-glazing",),
    "Structural Steel": ("structural-steel",),
    "Storefront": ("storefront-and-glazing",),
    "Tile": ("tiling",),
    "Tiling": ("tiling",),
    "Roof Anchors": ("roof-anchors-and-fall-protection",),
    "Window Treatments": ("window-treatments",),
    "Windows": ("windows",),
    "Each MEP Trade": ("plumbing", "hvac", "electrical", "fire-protection"),
    "MEP": ("plumbing", "hvac", "electrical", "fire-protection"),
}
OWNER_WORDS = ("Owner", "Utility")


def condition_trades(condition: str) -> list[str]:
    """
    The trade files a line's condition names, by the same words a Which Trade line names a trade
    by, in any case and as whole words, the longest first, so `fire protection` is one trade and
    `the MEP trades` four.
    """
    found: list[str] = []
    rest = condition
    for word in sorted(TRADE_WORDS, key=len, reverse=True):
        pattern = re.compile(r"(?<![\w-])" + re.escape(word) + r"(?![\w-])", re.IGNORECASE)
        if pattern.search(rest):
            found.extend(TRADE_WORDS[word])
            rest = pattern.sub(" ", rest)
    return list(dict.fromkeys(found))


class LinesError(Exception):
    """A named failure with a one-line reason, reported on stderr and exiting 1."""


def _cells(row: str) -> list[str]:
    inner = row.strip()
    if not (inner.startswith("|") and inner.endswith("|")):
        return []
    return [cell.strip() for cell in inner[1:-1].split("|")]


def _digits(code: str) -> str:
    base, _, suffix = code.partition(".")
    return base.replace(" ", "") + suffix


def parse_which_trade(line: str) -> dict:
    """
    A Which Trade line's halves and the trades it keeps the work off. After each `by`, `with` or
    `Not` the names run, joined by commas, `or` and `and`, until a piece that names none, which
    starts the next half's subject. A trade named just before `Install` at the start of the line
    (`Millwork Install with Finish Carpentry`) is named too, as a trade the work is kept off.
    """
    halves: list[dict] = []
    kept_off: list[str] = []
    parts = re.split(r"\b(by|with|Not)\b", line)
    before_install = re.fullmatch(r"(.+) Install", parts[0].strip())
    if before_install and before_install.group(1) in TRADE_WORDS:
        kept_off.extend(TRADE_WORDS[before_install.group(1)])
    for word, tail in zip(parts[1::2], parts[2::2]):
        taken: list[str] = []
        joiners: set[str] = set()
        for index, piece in enumerate(tail.split(",")):
            names = [p.strip() for p in re.split(r"\b(?:or|and)\b", piece)]
            names = [re.sub(r"^(?:the|a|an) ", "", n) for n in names if n]
            if not names or any(n not in TRADE_WORDS and n not in OWNER_WORDS for n in names):
                if index == 0:
                    raise LinesError(f"the Which Trade line {line!r} names {piece.strip()!r}, which is no trade this script knows")
                break
            joiners.update(re.findall(r"\b(or|and)\b", piece))
            taken.extend(names)
        if "or" in joiners and "and" in joiners:
            raise LinesError(f"the Which Trade line {line!r} joins one list with both `or` and `and`")
        trades = [slug for name in taken if name in TRADE_WORDS for slug in TRADE_WORDS[name]]
        owner = any(name in OWNER_WORDS for name in taken)
        if word == "Not":
            if owner:
                raise LinesError(f"the Which Trade line {line!r} keeps the work off the owner")
            kept_off.extend(trades)
            continue
        if not trades:
            shape = "owner"
        elif "or" in joiners:
            shape = "or"
        elif len(trades) > 1:
            shape = "each"
        else:
            shape = "one"
        if owner and shape not in ("owner", "or"):
            raise LinesError(f"the Which Trade line {line!r} names the owner beside a trade without `or`")
        halves.append({"by": (" or " if "or" in joiners else ", ").join(taken),
                       "shape": shape, "trades": trades, "owner": owner})
    if not halves:
        raise LinesError(f"the Which Trade line {line!r} names no trade after `by` or `with`")
    owner_halves = [h for h in halves if h["shape"] == "owner"]
    if owner_halves and (len(halves) != 2 or len(owner_halves) != 1):
        raise LinesError(f"the Which Trade line {line!r} has an owner half without exactly one other half")
    return {"halves": halves, "kept_off": kept_off}


def read_file(path: Path) -> dict:
    """One trade's file: its title, numbers, Home number and lines, refused when out of shape."""
    text = path.read_text(encoding="utf-8").splitlines()
    where = path.name
    title = next((line[2:].strip() for line in text if line.startswith("# ")), "")
    if not title:
        raise LinesError(f"{where} has no `# <trade>` title")
    numbers_line = next((line for line in text if line.startswith("Numbers:")), None)
    if numbers_line is None:
        raise LinesError(f"{where} has no `Numbers:` line")
    numbers = [n.strip() for n in numbers_line[len("Numbers:"):].split(",") if n.strip()]
    if not numbers:
        raise LinesError(f"{where} names no number on its `Numbers:` line")
    for number in numbers:
        if not NUMBER_RE.fullmatch(number):
            raise LinesError(f"{where} names {number!r}, which is not pairs of digits like `09 65`")
    home_line = next((line for line in text if line.startswith("Home:")), None)
    if home_line is None:
        raise LinesError(f"{where} has no `Home:` line")
    homes = [h.strip() for h in home_line[len("Home:"):].split(",") if h.strip()]
    if not homes:
        raise LinesError(f"{where} names no number on its `Home:` line")
    for home in homes:
        if not NUMBER_RE.fullmatch(home):
            raise LinesError(f"{where} names the Home number {home!r}, which is not pairs of digits like `09 65`")
        if not any(_digits(home).startswith(_digits(n)) for n in numbers):
            raise LinesError(f"{where} names the Home number {home}, which none of its numbers starts")
    if len(set(homes)) != len(homes):
        raise LinesError(f"{where} names one Home number twice")
    else_line = next((line for line in text if line.startswith("Else:")), None)
    otherwise = else_line[len("Else:"):].strip() if else_line is not None else None
    if else_line is not None and not otherwise:
        raise LinesError(f"{where} names no trade on its `Else:` line")
    table = [line for line in text if line.strip().startswith("|")]
    if len(table) < 2 or table[0].strip() != HEADER or not re.fullmatch(r"\|(?:-+\|){5}", table[1].strip()):
        raise LinesError(f"{where} does not open its table with `{HEADER}` and its rule")
    lines = []
    row_names: set[str] = set()
    for at, row in enumerate(table[2:], start=1):
        cells = _cells(row)
        if len(cells) != 5:
            raise LinesError(f"{where} row {at} has {len(cells)} cells, and every row has 5")
        kind, line, condition, look, row_name = cells
        if kind not in KINDS:
            raise LinesError(f"{where} row {at} has the kind {kind!r}, which is none of {', '.join(KINDS)}")
        if not line:
            raise LinesError(f"{where} row {at} has no line")
        names = [n.strip() for n in row_name.split(";")] if row_name else []
        if not names or not all(names):
            raise LinesError(f"{where} row {at} has no row name")
        for name in names:
            if len(name) > ROW_NAME_MAX:
                raise LinesError(f"{where} row {at} has the row name {name!r}, over {ROW_NAME_MAX} characters")
            if "," in name:
                raise LinesError(f"{where} row {at} has the row name {name!r}, and a row name carries no comma")
            if name.lower() in row_names:
                raise LinesError(f"{where} uses the row name {name!r} twice")
            row_names.add(name.lower())
        entry = {"kind": kind, "line": line, "condition": condition, "look": look, "names": names}
        if kind == "Which Trade":
            entry.update(parse_which_trade(line))
            entry["condition_trades"] = condition_trades(condition)
            if len(entry["halves"]) != len(names):
                raise LinesError(
                    f"{where} row {at} names {len(names)} rows for the {len(entry['halves'])} halves of {line!r}")
        elif len(names) != 1:
            raise LinesError(f"{where} row {at} names {len(names)} rows, and a {kind} line names one")
        lines.append(entry)
    if not lines:
        raise LinesError(f"{where} carries no line")
    return {"slug": path.stem, "title": title, "numbers": numbers, "homes": homes, "else": otherwise, "lines": lines}


def read_folder(folder: Path) -> list[dict]:
    """Every trade's file, in name order, with no number claimed by two and no line read two ways."""
    if not folder.is_dir():
        raise LinesError(f"no standard lines folder at {folder}")
    files = [read_file(path) for path in sorted(folder.glob("*.md"))]
    if not files:
        raise LinesError(f"the standard lines folder at {folder} holds no file")
    claimed: list[tuple[str, str]] = []
    for item in files:
        for number in item["numbers"]:
            digits = _digits(number)
            for other_digits, other in claimed:
                if other != item["slug"] and (digits.startswith(other_digits) or other_digits.startswith(digits)):
                    raise LinesError(
                        f"{item['slug']}.md claims {number} and {other}.md claims a number that "
                        f"starts it or that it starts, so one code would match both"
                    )
            claimed.append((digits, item["slug"]))
    by_line: dict[str, tuple[str, list[str]]] = {}
    by_name: dict[str, str] = {}
    slugs = {item["slug"] for item in files}
    for item in files:
        for entry in item["lines"]:
            if by_line.setdefault(entry["line"], (entry["kind"], entry["names"])) != (entry["kind"], entry["names"]):
                raise LinesError(f"{entry['line']!r} has another kind or row name in {item['slug']}.md than in a file before it")
            for name in entry["names"]:
                if by_name.setdefault(name.lower(), entry["line"]) != entry["line"]:
                    raise LinesError(f"the row name {name!r} is used by two lines, {by_name[name.lower()]!r} and {entry['line']!r}")
            named = entry.get("kept_off", []) + [s for h in entry.get("halves", []) for s in h["trades"]]
            for slug in named + entry.get("condition_trades", []):
                if slug not in slugs:
                    raise LinesError(f"{entry['line']!r} names the trade file {slug}.md, which is not in the folder")
    titles = {item["title"]: item for item in files}
    for item in files:
        if item["else"] is None:
            continue
        target = titles.get(item["else"])
        if target is None or target is item:
            raise LinesError(f"{item['slug']}.md names {item['else']!r} on its `Else:` line, which is no other file's title")
        if target["else"] is not None:
            raise LinesError(f"{item['slug']}.md names {item['else']!r} on its `Else:` line, which has an `Else:` line of its own")
        item["else"] = target["slug"]
    return files


def plugin_version(manifest: Path) -> str:
    try:
        version = json.loads(manifest.read_text(encoding="utf-8"))["version"]
    except Exception as e:
        raise LinesError(f"cannot read the plugin version at {manifest}: {e}") from None
    if not isinstance(version, str) or not version or any(ch.isspace() for ch in version) or "@" in version:
        raise LinesError(f"the plugin version at {manifest} reads {version!r}")
    return version


def _trimmed(code: str) -> str:
    """A code's digits with its trailing `00` pairs dropped, never below its division."""
    digits = _digits(code)
    while len(digits) > 2 and digits.endswith("00"):
        digits = digits[:-2]
    return digits


def _held(code: str) -> str:
    """What a code holds: its trimmed digits, and a group code's last `0` dropped (`09 60 00` holds 096)."""
    digits = _trimmed(code)
    return digits[:-1] if len(digits) >= 4 and digits.endswith("0") else digits


def holds(code: str, number: str) -> bool:
    """Whether a catalog code holds one of a file's numbers."""
    return _digits(number).startswith(_held(code)) or _digits(code).startswith(_digits(number))


def _nearness(code: str, home: str) -> int | None:
    """How near a code is to a Home number: 0 the number itself, then broader, then narrower."""
    trimmed, number = _trimmed(code), _digits(home)
    if trimmed == number:
        return 0
    if len(trimmed) == 2:
        return None
    if number.startswith(_held(code)):
        return 1 + len(number) - len(_held(code))
    if _digits(code).startswith(number):
        return 100 + len(trimmed) - len(number)
    return None


def assign(files: list[dict], packages: dict[str, list[str]]) -> dict[str, str | None]:
    """Each trade file's one live package, by its `tradeCode`, or None where no package claims it."""
    out: dict[str, str | None] = {}
    order = sorted(packages)
    # A file with an `Else:` line is placed after the file it names, which has none of its own.
    for item in sorted(files, key=lambda f: f["else"] is not None):
        best: tuple | None = None
        for at, home in enumerate(item["homes"]):
            for trade_code in order:
                for code in packages[trade_code]:
                    near = _nearness(code, home)
                    if near is not None:
                        key = (at, 0 if code == trade_code else 1, near, trade_code)
                        best = key if best is None or key < best else best
        if best is not None:
            out[item["slug"]] = best[3]
            continue
        by_division = [(at, 0 if code == tc else 1, tc) for at, home in enumerate(item["homes"]) for tc in order
                       for code in packages[tc] if code == f"{_digits(home)[:2]} 00 00"]
        if by_division:
            out[item["slug"]] = min(by_division)[2]
            continue
        if item["else"] is not None and out.get(item["else"]):
            out[item["slug"]] = out[item["else"]]
            continue
        counts = []
        for trade_code in order:
            held = sum(1 for n in item["numbers"] if any(holds(code, n) for code in packages[trade_code]))
            if held:
                counts.append((-held, trade_code))
        out[item["slug"]] = min(counts)[1] if counts else None
    return out


def _catalog_id(home: str) -> str:
    pairs = home.split(" ")
    return " ".join(pairs + ["00"] * (3 - len(pairs)))


def involved_trades(entry: dict, carriers: list[str]) -> list[str]:
    """
    The trade files a Which Trade line involves: those carrying it, then those its line names, then
    those its condition names.
    """
    named = entry["kept_off"] + [s for h in entry["halves"] for s in h["trades"]]
    return list(dict.fromkeys(carriers + named + entry["condition_trades"]))


def halves_for(entry: dict, involved: list[str], places: dict[str, str | None], homes: dict[str, str]) -> list[dict]:
    """
    Who writes each half of a Which Trade line and the records each writer puts beside its row,
    as (role, the package the record is for, the counterparty), from each trade file's package.
    """
    plans: list[dict] = []
    for half in entry["halves"]:
        own = half["trades"]
        live = sorted({places[s] for s in own if places.get(s)})
        others = sorted({places[s] for s in involved if s not in own and places.get(s)} - set(live))
        writers: dict[str, list[tuple[str, str, str]]] = {}
        if half["shape"] == "one" and live:
            writers[live[0]] = [("exclusion", p, live[0]) for p in others]
        elif half["shape"] == "one" and others:
            counterparty = _catalog_id(homes[own[0]])
            writers[others[0]] = [("exclusion", p, counterparty) for p in others]
        elif half["shape"] == "or" and live:
            writers[live[0]] = [("candidate", p, "") for p in live[1:]] + [("exclusion", p, "none") for p in others]
        elif half["shape"] == "each" and live:
            for writer in live:
                writers[writer] = [("exclusion", p, writer) for p in others]
        elif half["shape"] in ("or", "each") and others:
            writers[others[0]] = [("exclusion", p, "none") for p in others]
        plans.append({"half": half, "writers": writers, "left": half["shape"] == "or" or not live})
    for at, plan in enumerate(plans):
        if plan["half"]["shape"] == "owner":
            plan["writers"] = {writer: [("exclusion", writer, "owner")] for writer in plans[1 - at]["writers"]}
            plan["left"] = False
    return plans


def row_name(name: str, package_name: str, trade_code: str) -> str:
    full = f"{name}, {package_name}"
    return full if len(full) <= NAME_MAX else f"{name}, {trade_code}"


def lines_for(package: str, names: dict[str, str], packages: dict[str, list[str]], files: list[dict], version: str) -> list[str]:
    name = names[package]
    places = assign(files, packages)
    homes = {item["slug"]: item["homes"][0] for item in files}
    titles = {item["slug"]: item["title"] for item in files}
    carriers: dict[str, list[str]] = {}
    for item in files:
        for entry in item["lines"]:
            carriers.setdefault(entry["line"], []).append(item["slug"])
    printed: set[str] = set()
    out: list[str] = []
    for item in [f for f in files if places[f["slug"]] == package]:
        fresh = [entry for entry in item["lines"] if entry["line"] not in printed]
        if not fresh:
            continue
        out.append(f"trade: {item['title']}")
        for entry in fresh:
            printed.add(entry["line"])
            out.append(f"line: {entry['line']}")
            out.append(f"  kind: {entry['kind']}")
            if entry["kind"] != "Which Trade":
                out.append(f"  name: {row_name(entry['names'][0], name, package)}")
            if entry["condition"]:
                out.append(f"  condition: {entry['condition']}")
                out.append(f"  where to look: {entry['look'] or 'not named'}")
            else:
                out.append("  condition: none")
                out.append(f"  instrument: trade-convention:{item['slug']}@{version}")
            if entry["kind"] != "Which Trade":
                continue
            involved = involved_trades(entry, carriers[entry["line"]])
            out.append("  trades: " + "; ".join(
                f"{titles[s]} on {places[s]}" if places.get(s) else f"{titles[s]}, no package" for s in involved))
            for half_name, plan in zip(entry["names"], halves_for(entry, involved, places, homes)):
                out.append(f"  half: {half_name}, by {plan['half']['by']}")
                records = plan["writers"].get(package)
                if records is None:
                    word = "left to" if plan["left"] else "carried by"
                    writers = sorted(plan["writers"])
                    out.append(f"    you write it: no, {word} {', '.join(writers) or 'no package'}")
                    if writers:
                        # The rows the writers write, which a review the paper gives the half to cites.
                        out.append("    name: " + "; ".join(row_name(half_name, names[w], w) for w in writers))
                    continue
                out.append("    you write it: yes")
                out.append(f"    name: {row_name(half_name, name, package)}")
                for role, target, counterparty in records:
                    if role == "candidate":
                        could = " or ".join(titles[s] for s in plan["half"]["trades"])
                        could += " or the owner" if plan["half"]["owner"] else ""
                        out.append(f"    candidate on: {target}, note: confirm trade responsibility: could be {could}")
                    elif counterparty == "none":
                        out.append(f"    exclusion on: {target}, no counterparty")
                    else:
                        out.append(f"    exclusion on: {target}, counterparty: {counterparty}")
    if not out:
        return [NONE_LINE]
    placed = [f"{item['title']} on {places[item['slug']]}" for item in files if places[item["slug"]]]
    return [f"standard lines for {package} {name}: {len(printed)} lines", "places: " + "; ".join(placed)] + out


def parse_all(text: str) -> tuple[dict[str, list[str]], dict[str, str]]:
    """Every live package's codes, its `tradeCode` first, and its name, each keyed by its `tradeCode`."""
    packages: dict[str, list[str]] = {}
    names: dict[str, str] = {}
    for part in [p.strip() for p in text.split(";") if p.strip()]:
        # The codes follow the last `=`, since a code never holds one and a name might.
        name, sep, codes = part.rpartition("=")
        name = " ".join(name.split())
        if not sep:
            raise LinesError(f"--all names {part!r}, and each package reads `<name>=<tradeCode>,<code>`")
        listed = [c.strip() for c in codes.split(",") if c.strip()]
        if not listed:
            raise LinesError(f"--all names {part!r} with no tradeCode after its `=`")
        for code in listed:
            if not CODE_RE.fullmatch(code):
                raise LinesError(f"{code!r} is not a catalog id spaced as the catalog spaces it, like `09 65 00`")
        trade_code = listed[0]
        if not name:
            raise LinesError(f"--all names the package {trade_code} with no name before its `=`")
        if trade_code in packages:
            raise LinesError(f"--all names the package {trade_code} twice")
        packages[trade_code] = list(dict.fromkeys(listed))
        names[trade_code] = name
    return packages, names


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Print the standard lines one package's review writes.")
    parser.add_argument("--package", required=True, help="this package's tradeCode")
    parser.add_argument("--all", required=True,
                        help="every live package as name=tradeCode,code,...; separated by ;")
    parser.add_argument("--folder", type=Path, default=LINES_FOLDER, help="the folder of the lines files")
    args = parser.parse_args(argv)
    try:
        package = args.package.strip()
        if not CODE_RE.fullmatch(package):
            raise LinesError(f"{package!r} is not a catalog id spaced as the catalog spaces it, like `09 65 00`")
        packages, names = parse_all(args.all)
        if package not in packages:
            raise LinesError(f"--all does not name the package {package}")
        files = read_folder(args.folder)
        version = plugin_version(PLUGIN_MANIFEST)
        lines = lines_for(package, names, packages, files, version)
    except LinesError as e:
        print(f"standard_lines: {e}", file=sys.stderr)
        return 1
    for line in lines:
        print(line)
    return 0


if __name__ == "__main__":
    sys.exit(main())
