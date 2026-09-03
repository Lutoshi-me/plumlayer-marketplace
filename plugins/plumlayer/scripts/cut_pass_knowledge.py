"""
cut_pass_knowledge.py: cut the shipped hints files down to one pass knowledge file.

A scope reader needs the hints for every trade its pass carries, and it reads them before it looks
at a drawing page. This script writes one pass knowledge file holding those hints files, whole and
copied byte for byte, with the knowledge version at the top.

The cut is deterministic and the hints are verbatim because a paraphrase would be an unrecorded
rewrite of knowledge that every convention-line record cites by version.

What is carried, per trade:
  - `hints/<slug>.md`, whole. The file opens with its own title line, so the block is the file.

The convention rows are not carried and are not the reader's: they live in `conventions/<slug>.md`,
the pass runner records them from the table once per pass, and the reader never opens them. This
script refuses a trade whose conventions file is missing anyway, because resolving a catalog code to
a slug happens here and nowhere else, so this is the only cheap place to catch it before a runner
opens a path that is not there.

`--trades` takes a hints file slug or a catalog trade code, since a window 2 pass is named for the
package's catalog code and a window 1 pass for the trades it carries. A code is resolved through
trade-knowledge/trade-sheets.json by nearest CSI ancestor, since a trade's knowledge is general to
its family: the code itself where the map keys it, else the nearest broader section the map does
key. A token that is neither a slug nor a covered code refuses naming both lookups tried.

Usage:

    python cut_pass_knowledge.py --trade-knowledge <dir> --trades a,b,c --pass-id A2 --out <path>

Exit codes:
  0  wrote the file; one line per carried trade naming its slug, its hints file, its two counts and
     how the token resolved, then one bounds line naming what it wrote.
  1  a named failure, one line on stderr: the manifest is unreadable or carries no knowledge
     version or no trade list; a token is neither a slug in the manifest's list nor a trade id in
     the sheet family map; a hints file is missing; a conventions file is missing; a hints file is
     over budget; the output path cannot be written.
  2  argparse rejected the invocation.

Grounding role: reads files and copies them whole. It never summarizes, reflows, or infers.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path

# The shared resolver sits beside this file. Running the script as a script already puts
# that directory on the path; this makes the import work the same way when it is loaded
# some other way, so the cut and the plan can never resolve a code differently.
sys.path.insert(0, str(Path(__file__).resolve().parent))

import trade_code

TRADE_SHEETS_FILE = "trade-sheets.json"
HINTS_DIR = "hints"
CONVENTIONS_DIR = "conventions"

# Twenty physical hint lines between the title and the coverage line, and 2,400 characters for the
# whole file. The same two numbers the source repo's exit check applies, counted the same way, so a
# file that passed the gate cannot fail here.
HINT_LINE_BUDGET = 20
HINT_CHARACTER_BUDGET = 2400

_VERSION_RE = re.compile(r"\*\*Knowledge version:\s*`([^`]+)`\*\*")
_TRADE_FILES_HEADING = "## Trade files"


class CutError(Exception):
    """A named failure with a one-line reason, reported on stderr and exiting 1."""


def _read_text(path: Path, what: str) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except Exception as e:
        raise CutError(f"cannot read {what} at {path}: {e}") from e


def _manifest_version(manifest_text: str, manifest_path: Path) -> str:
    """
    The knowledge version, read off the manifest every run. Hardcoding it here would let a
    corpus refresh move the pin while the excerpt kept citing the old one.
    """
    m = _VERSION_RE.search(manifest_text)
    if not m:
        raise CutError(f"no `Knowledge version` line in {manifest_path}")
    return m.group(1).strip()


def _manifest_trades(manifest_text: str, manifest_path: Path) -> list[str]:
    """
    The trade slugs the manifest itself lists, in manifest order. This is the authoritative record
    of what the pinned corpus holds, so a slug that is not on it is a caller mistake, not a file to
    go looking for on disk.
    """
    lines = manifest_text.splitlines()
    heading_idx = None
    for i, line in enumerate(lines):
        if line.strip() == _TRADE_FILES_HEADING:
            heading_idx = i
            break
    if heading_idx is None:
        raise CutError(f"no `{_TRADE_FILES_HEADING}` section in {manifest_path}")

    entry_lines: list[str] = []
    started = False
    for line in lines[heading_idx + 1:]:
        if line.strip() == "":
            if started:
                break
            continue
        if line.startswith("#"):
            break
        entry_lines.append(line.strip())
        started = True

    names = [n.strip() for n in " ".join(entry_lines).split(",") if n.strip()]
    if not names:
        raise CutError(f"the `{_TRADE_FILES_HEADING}` list in {manifest_path} is empty")
    return names


def hint_line_count(text: str) -> int:
    """
    The hint lines between the title line and the coverage line: every line of the file less the
    title, its blank, the coverage line's blank and the coverage line. A hint is exactly one
    physical line, so a hint written across two lines counts twice.
    """
    lines = text.split("\n")
    if len(lines) > 1 and lines[-1] == "":
        lines.pop()
    return max(len(lines) - 4, 0)


def _catalog_slugs(trade_knowledge: Path) -> dict[str, str]:
    """
    Catalog trade code to trade slug, read off trade-sheets.json beside the manifest, keyed by
    the folded code. A window 2 pass is named for the package's catalog code, so the cut has to
    take either that code or the slug and land on the same files.
    """
    path = trade_knowledge / TRADE_SHEETS_FILE
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception as e:
        raise CutError(f"cannot read the trade to sheet family map at {path}: {e}") from e
    trades = data.get("trades")
    if not isinstance(trades, dict):
        raise CutError(f"{path.name} carries no `trades` object")
    index: dict[str, str] = {}
    for trade_id, entry in trades.items():
        knowledge = entry.get("knowledge") if isinstance(entry, dict) else None
        if isinstance(knowledge, str) and knowledge:
            index["".join(trade_id.split()).lower()] = knowledge
    return index


def _dedupe(slugs: list[str]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for s in slugs:
        if s not in seen:
            seen.add(s)
            out.append(s)
    return out


def cut(trade_knowledge: Path, trades: list[str], pass_id: str, out: Path) -> str:
    """
    Write the pass knowledge file and return the report: one line per carried trade, then the
    bounds line. Always overwrites: the excerpt is a projection off the shipped files, and a later
    part of the same pass that found a stale one would carry a stale version pin.
    """
    manifest_path = trade_knowledge / "MANIFEST.md"
    manifest_text = _read_text(manifest_path, "the trade knowledge manifest")
    version = _manifest_version(manifest_text, manifest_path)
    known = _manifest_trades(manifest_text, manifest_path)

    # A token is a trade slug or a catalog trade id. The map is only opened where a token is not
    # already a slug, so a seat with no map still cuts every pass named by slug.
    catalog: dict[str, str] | None = None
    resolved: list[str] = []
    how_resolved: dict[str, str] = {}
    for token in _dedupe(trades):
        if token in known:
            resolved.append(token)
            continue
        if catalog is None:
            catalog = _catalog_slugs(trade_knowledge)
        found = trade_code.resolve(token, catalog)
        if found is None:
            raise CutError(
                f"`{token}` is not in {manifest_path.name}'s trade list, and neither it nor any "
                f"broader CSI section above it is a trade in {TRADE_SHEETS_FILE}"
            )
        slug, how = found
        if slug not in known:
            raise CutError(
                f"{TRADE_SHEETS_FILE} maps `{token}` to `{slug}`, which is not in "
                f"{manifest_path.name}'s trade list"
            )
        resolved.append(slug)
        how_resolved[slug] = f"from {token}" + (" by family" if how == "family" else "")
    slugs = _dedupe(resolved)

    blocks: list[str] = []
    carried: list[str] = []

    for slug in slugs:
        hints_path = trade_knowledge / HINTS_DIR / f"{slug}.md"
        if not hints_path.is_file():
            raise CutError(f"{manifest_path.name} lists `{slug}` but {hints_path} is not on disk")

        # The runner opens the conventions file from the slug this loop resolved, and this is the
        # only place a catalog code becomes a slug, so a missing table is caught here rather than
        # mid-pass at the runner's own read.
        conventions_path = trade_knowledge / CONVENTIONS_DIR / f"{slug}.md"
        if not conventions_path.is_file():
            raise CutError(
                f"{manifest_path.name} lists `{slug}` but {conventions_path} is not on disk"
            )

        text = _read_text(hints_path, f"the {slug} hints file")

        lines = hint_line_count(text)
        characters = len(text)
        if lines > HINT_LINE_BUDGET:
            raise CutError(
                f"{HINTS_DIR}/{slug}.md carries {lines} hint lines, over the budget of "
                f"{HINT_LINE_BUDGET}"
            )
        if characters > HINT_CHARACTER_BUDGET:
            raise CutError(
                f"{HINTS_DIR}/{slug}.md is {characters} characters, over the budget of "
                f"{HINT_CHARACTER_BUDGET}"
            )

        blocks.append(text.rstrip("\n"))
        note = how_resolved.get(slug)
        carried.append(
            f"{slug}  {HINTS_DIR}/{slug}.md  {lines} hint lines, {characters:,} characters"
            + (f"  ({note})" if note else "")
        )

    header = (
        f"# Pass knowledge: {pass_id}\n"
        "\n"
        f"knowledge version: {version}\n"
        f"trades carried: {', '.join(slugs)}\n"
        "carried: each trade's hints file, whole and verbatim, and nothing else. Where a grain or\n"
        "trade-ownership question turns on something not here, raise a Question rather than\n"
        "guessing.\n"
        "generated by scripts/cut_pass_knowledge.py\n"
    )
    body = header + "\n---\n\n" + "\n\n---\n\n".join(blocks) + "\n"
    payload = body.encode("utf-8")

    _write_atomically(out, payload)

    bounds = f"wrote {out}: {len(slugs)} trades, {len(payload):,} bytes, knowledge version {version}"
    return "\n".join(carried + [bounds])


def _write_atomically(out: Path, payload: bytes) -> None:
    """Write beside the target and rename, so a run that dies mid-write leaves no partial file."""
    try:
        out.parent.mkdir(parents=True, exist_ok=True)
        tmp = out.with_name(out.name + ".tmp")
        tmp.write_bytes(payload)
        os.replace(tmp, out)
    except Exception as e:
        raise CutError(f"cannot write {out}: {e}") from e


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Cut the shipped hints files down to one pass knowledge file.",
    )
    parser.add_argument(
        "--trade-knowledge", required=True, type=Path,
        help="the plugin's trade-knowledge directory",
    )
    parser.add_argument(
        "--trades", required=True,
        help="the trades the pass carries, comma separated, each a trade slug or a catalog trade id",
    )
    parser.add_argument("--pass-id", required=True, help="the pass id, or the pass part id where a pass was split")
    parser.add_argument("--out", required=True, type=Path, help="the pass knowledge file to write")
    args = parser.parse_args(argv)

    trades = [t.strip() for t in args.trades.split(",") if t.strip()]
    if not trades:
        print("cut_pass_knowledge: --trades named no trades", file=sys.stderr)
        return 1

    try:
        print(cut(args.trade_knowledge, trades, args.pass_id, args.out))
    except CutError as e:
        print(f"cut_pass_knowledge: {e}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
