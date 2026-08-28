"""
cut_pass_knowledge.py: cut the shipped trade files down to one pass knowledge file.

A scope reader needs the grain rules and the structural gap list of every trade its pass carries,
and it reads them before it looks at a drawing page. It does not need the whole trade file. This
script writes one pass knowledge file holding just the sections the reader's mandates act on,
copied byte for byte out of the shipped trade files, with the knowledge version at the top.

The cut is deterministic and the sections are verbatim because a paraphrase would be an unrecorded
rewrite of knowledge that every convention-line record cites by version.

Sections carried, per trade:
  - `## 3. Scope grain rules`, always, whole.
  - `## 7. Quantity and pricing conventions`, whole, only where the phrase `structural gap list`
    does not occur inside that trade's section 3. Some trade files keep their gap list at the tail
    of section 7 instead, and a rule keyed on the phrase picks that up mechanically rather than
    dropping it silently.

`--trades` takes a trade file slug or a catalog trade code, since a window 2 pass is named for the
package's catalog code and a window 1 pass for the trade files it carries. A code is resolved
through trade-knowledge/trade-sheets.json by nearest CSI ancestor, since a trade file is general
to its family: the code itself where the map keys it, else the nearest broader section the map
does key. A token that is neither a slug nor a covered code refuses naming both lookups tried.

Usage:

    python cut_pass_knowledge.py --trade-knowledge <dir> --trades a,b,c --pass-id A2 --out <path>

Exit codes:
  0  wrote the file; one bounds line on stdout naming what it carried and what it did not find.
  1  a named failure, one line on stderr: the manifest is unreadable or carries no knowledge
     version or no trade list; a token is neither a slug in the manifest's list nor a trade id in
     the sheet family map; a named trade file is missing; a trade file has no section 3; the output
     path cannot be written.
  2  argparse rejected the invocation.

Grounding role: reads files and copies byte ranges. It never summarizes, reflows, or infers.
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

SECTION_GRAIN = 3
SECTION_PRICING = 7
GAP_LIST_PHRASE = "structural gap list"
TRADE_SHEETS_FILE = "trade-sheets.json"

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


def _section(text: str, number: int) -> str | None:
    """
    The whole `## <number>. ...` section: the heading line through the byte before the next
    top-level heading, trailing blank lines trimmed. Every shipped trade file carries the same
    eight top-level headings and none of them sits inside a fenced block, so a line-start match is
    unambiguous here.
    """
    m = re.search(rf"^## {number}\. .*$", text, re.M)
    if m is None:
        return None
    nxt = re.search(r"^## ", text[m.end():], re.M)
    end = m.end() + nxt.start() if nxt else len(text)
    return text[m.start():end].rstrip("\n")


def _title(text: str, slug: str) -> str:
    """The trade file's own H1, so the block heading reads the way the file names itself."""
    for line in text.splitlines():
        if line.startswith("# "):
            return line[2:].strip()
    return slug


def _catalog_slugs(trade_knowledge: Path) -> dict[str, str]:
    """
    Catalog trade code to trade file slug, read off trade-sheets.json beside the manifest, keyed by
    the folded code. A window 2 pass is named for the package's catalog code, so the cut has to
    take either that code or the slug and land on the same file.
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
    Write the pass knowledge file and return the one-line bounds summary. Always overwrites: the
    excerpt is a projection off the shipped files, and a later part of the same pass that found a
    stale one would carry a stale version pin.
    """
    manifest_path = trade_knowledge / "MANIFEST.md"
    manifest_text = _read_text(manifest_path, "the trade knowledge manifest")
    version = _manifest_version(manifest_text, manifest_path)
    known = _manifest_trades(manifest_text, manifest_path)

    # A token is a trade file slug or a catalog trade id. The map is only opened where a token is
    # not already a slug, so a seat with no map still cuts every pass named by slug.
    catalog: dict[str, str] | None = None
    resolved: list[str] = []
    from_catalog: list[str] = []
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
        from_catalog.append(f"{token} to {slug}" + (" by family" if how == "family" else ""))
    slugs = _dedupe(resolved)

    blocks: list[str] = []
    took_pricing: list[str] = []
    no_gap_list: list[str] = []

    for slug in slugs:
        path = trade_knowledge / f"{slug}.md"
        if not path.is_file():
            raise CutError(f"{manifest_path.name} lists `{slug}` but {path} is not on disk")
        text = _read_text(path, f"the {slug} trade file")

        grain = _section(text, SECTION_GRAIN)
        if grain is None:
            raise CutError(f"{path.name} has no `## {SECTION_GRAIN}.` section")

        sections = [grain]
        if GAP_LIST_PHRASE not in grain:
            pricing = _section(text, SECTION_PRICING)
            if pricing is not None:
                sections.append(pricing)
                took_pricing.append(slug)
        if GAP_LIST_PHRASE not in text:
            no_gap_list.append(slug)

        blocks.append(f"# {_title(text, slug)}\n\n" + "\n\n".join(sections))

    header = (
        f"# Pass knowledge: {pass_id}\n"
        "\n"
        f"knowledge version: {version}\n"
        f"trades carried: {', '.join(slugs)}\n"
        "sections carried, verbatim and whole: 3. Scope grain rules; and 7. Quantity and pricing\n"
        "conventions where the structural gap list is not in section 3.\n"
        "sections not carried: 1, 2, 4, 5, 6, 8. This is an excerpt, not the trade file. Where a\n"
        "grain or furnish-and-install question turns on something not here, raise a Question rather\n"
        "than guessing.\n"
        "generated by scripts/cut_pass_knowledge.py\n"
    )
    body = header + "\n---\n\n" + "\n\n---\n\n".join(blocks) + "\n"
    payload = body.encode("utf-8")

    _write_atomically(out, payload)

    pricing_names = ", ".join(took_pricing) if took_pricing else "none"
    gapless_names = ", ".join(no_gap_list) if no_gap_list else "none"
    catalog_names = ", ".join(from_catalog) if from_catalog else "none"
    return (
        f"wrote {out}: {len(slugs)} trades, {len(payload):,} bytes, knowledge version {version}; "
        f"sections carried: 3 (all), 7 ({len(took_pricing)} of {len(slugs)}: {pricing_names}); "
        f"no gap list found in: {gapless_names}; resolved from a trade id: {catalog_names}"
    )


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
        description="Cut the shipped trade files down to one pass knowledge file.",
    )
    parser.add_argument(
        "--trade-knowledge", required=True, type=Path,
        help="the plugin's trade-knowledge directory",
    )
    parser.add_argument(
        "--trades", required=True,
        help="the trade files the pass carries, comma separated, each a trade file slug or a catalog trade id",
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
