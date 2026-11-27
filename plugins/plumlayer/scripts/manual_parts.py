"""
manual_parts.py: how window 3 divides each package's manual sections into the manual parts that
read them, planned before any of them runs.

`plan_inventory.py` imports this for its window 3 plan. Nothing here reads the record or a report:
it takes the packages list and the manual's section list `list_spec_sections` gave (byte copied to
`plan/spec-sections.json`), and returns each manual part's spans and every section no unit can read.

A span is one section's run of pages one unit reads, `{code, fileId, fromPage, toPage, pageStart,
pageEnd}`, `pageStart` and `pageEnd` being the section's own first and last page. The manual parts
take every page of a package's sections in its `manualSections` order, PART_PAGES to a part, and
the package's review reads none of them. A section that fits a part is never split: where it does
not fit the room left, it starts the next part. A section longer than a whole part is split at page
boundaries, and a part that starts partway into a section leaves CONTEXT_RESERVE pages of its room
for the section's opening pages, which it reads first for what Part 1 says.

The plan is made once: `plan_inventory.py` divides afresh only until window 3's first dispatch, and
from then on keeps the parts it wrote, so nothing here is asked what was already handed out.
"""

from __future__ import annotations

from typing import Iterable

# The pages one manual part reads at most. A part reader spends about half of what it can hold
# on its rules before it opens a page, and each page costs it the page's text, the rows it reads
# for that page and what it writes, so a part is sized for the reader to finish well inside it.
PART_PAGES = 10
# Room a unit that starts partway into a section keeps for that section's opening pages.
CONTEXT_RESERVE = 2
# A unit with fewer pages of room than this left is closed rather than handed a sliver of a section,
# and a section split across units never leaves fewer pages than this for the unit after.
MIN_SPLIT = 3

NO_PAGE_RANGE = "no page range"
NOT_ON_RECORD = "not on the record"


class SectionError(ValueError):
    """The section list cannot be planned from; the message says why in one line."""


def read_inventory(data: object, where: str) -> dict[str, dict]:
    """
    The `list_spec_sections` answer as {packed code: {fileId, pageStart, pageEnd, title}}. A
    truncated answer is refused, since a range in it may be out of date and a section missing from
    it may be on the record.
    """
    if not isinstance(data, dict) or not isinstance(data.get("sections"), list):
        raise SectionError(f"{where} carries no `sections` array from list_spec_sections")
    if data.get("truncated") is not False:
        raise SectionError(
            f"{where} reads truncated: true (or carries no truncated field), so its list is incomplete "
            f"and no manual reading can be planned from it"
        )
    sections: dict[str, dict] = {}
    for index, row in enumerate(data["sections"], 1):
        code = row.get("csi") if isinstance(row, dict) else None
        if not isinstance(code, str) or not code:
            raise SectionError(f"{where}: section {index} carries no `csi`")
        if code in sections:
            raise SectionError(f"{where}: section {code} is listed twice")
        file_id, start, end = row.get("fileId"), row.get("pageStart"), row.get("pageEnd")
        usable = (
            isinstance(file_id, str) and bool(file_id)
            and type(start) is int and type(end) is int and 1 <= start <= end
        )
        sections[code] = {
            "fileId": file_id if usable else None,
            "pageStart": start if usable else None,
            "pageEnd": end if usable else None,
            "title": row.get("title") if isinstance(row.get("title"), str) else None,
        }
    return sections


def package_sections(package: dict, inventory: dict[str, dict]) -> tuple[list[dict], list[dict]]:
    """
    The package's sections that have pages, in its `manualSections` order, each once, and every
    section it lists that no unit can read, with the reason: `no page range` (a section read only
    from the table of contents, or a location without a usable range) or `not on the record`.
    """
    readable: list[dict] = []
    omitted: list[dict] = []
    for code in dict.fromkeys(_codes(package)):
        section = inventory.get(code)
        if section is None:
            omitted.append({"code": code, "reason": NOT_ON_RECORD})
        elif section["fileId"] is None:
            omitted.append({"code": code, "reason": NO_PAGE_RANGE})
        else:
            readable.append({"code": code, **section})
    return readable, omitted


def section_codes(package: dict) -> list[str]:
    """The sections a package lists in its `manualSections`, in its order, each once."""
    return list(dict.fromkeys(_codes(package)))


def _codes(package: dict) -> list[str]:
    raw = package.get("manualSections")
    if raw is None:
        return []
    if not isinstance(raw, list) or not all(isinstance(code, str) and code for code in raw):
        raise SectionError(f"package {package.get('id')} carries a `manualSections` that is not a list of section numbers")
    return raw


def span_valid(span: dict, inventory: dict[str, dict]) -> bool:
    """A dispatched span still names its section's file and falls inside its range as the record
    gives it now, so a range corrected at one end keeps the pages already read."""
    section = inventory.get(span["code"])
    return (
        section is not None and section["fileId"] is not None and section["fileId"] == span["fileId"]
        and section["pageStart"] <= span["fromPage"] <= span["toPage"] <= section["pageEnd"]
    )


def divide(sections: list[dict]) -> list[list[dict]]:
    """
    Each manual part's spans for one package, in order, covering every page of its sections once.
    """
    units: list[list[dict]] = []
    current: list[dict] = []
    room = PART_PAGES

    def close() -> None:
        nonlocal current, room
        units.append(current)
        current = []
        room = PART_PAGES

    runs = [(section, section["pageStart"], section["pageEnd"]) for section in sections]
    index = 0
    while index < len(runs):
        section, start, end = runs[index]
        pages = end - start + 1
        if not current and start > section["pageStart"]:
            # A part opening partway into a section reads its opening pages first.
            room = PART_PAGES - CONTEXT_RESERVE
        if pages <= room:
            current.append(_span(section, start, end))
            room -= pages
            index += 1
            continue
        fresh_room = PART_PAGES - (CONTEXT_RESERVE if start > section["pageStart"] else 0)
        if current and (pages <= fresh_room or room < MIN_SPLIT):
            # A section that fits a fresh part, or a sliver of room, starts the next part.
            close()
            continue
        take = room
        left = pages - take
        if left < MIN_SPLIT and take - (MIN_SPLIT - left) >= MIN_SPLIT:
            # Leave the part after a few pages to read rather than one or two.
            take -= MIN_SPLIT - left
        current.append(_span(section, start, start + take - 1))
        runs[index] = (section, start + take, end)
        close()
    if current:
        close()
    return [unit for unit in units if unit]


def _span(section: dict, start: int, end: int) -> dict:
    return {
        "code": section["code"],
        "fileId": section["fileId"],
        "fromPage": start,
        "toPage": end,
        "pageStart": section["pageStart"],
        "pageEnd": section["pageEnd"],
    }


def pages_of(spans: Iterable[dict]) -> int:
    return sum(span["toPage"] - span["fromPage"] + 1 for span in spans)


def span_text(span: dict) -> str:
    """How a unit line and a dispatch name one span: `260519 p1201-p1214 of file-x`, and, where the
    span is not the whole section, the section's own range after it."""
    text = f"{span['code']} p{span['fromPage']}-p{span['toPage']} of {span['fileId']}"
    if (span["fromPage"], span["toPage"]) != (span["pageStart"], span["pageEnd"]):
        text += f" (section p{span['pageStart']}-p{span['pageEnd']})"
    return text
