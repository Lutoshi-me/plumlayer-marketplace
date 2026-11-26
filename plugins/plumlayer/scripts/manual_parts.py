"""
manual_parts.py: how window 3 divides each package's manual sections between its review and the
manual parts that follow it, planned before any of them runs.

`plan_inventory.py` imports this for its window 3 plan. Nothing here reads the record or a report:
it takes the packages list, the manual's section list `list_spec_sections` gave (byte copied to
`plan/spec-sections.json`), and what the plan file and the ledger say was already handed out, and
returns each review's spans, each manual part's spans and every section no unit can read.

A span is one section's run of pages one unit reads, `{code, fileId, fromPage, toPage, pageStart,
pageEnd}`, `pageStart` and `pageEnd` being the section's own first and last page. The review takes
whole sections in the package's `manualSections` order up to REVIEW_PAGES pages, and the manual
parts take the rest, PART_PAGES to a part. A section that fits a unit is never split: where it does
not fit the room left, it starts the next unit, so a first section longer than the review's pages
and no longer than a part's goes whole to the first part. A section longer than a whole unit is split at page
boundaries, and a unit that starts partway into a section leaves CONTEXT_RESERVE pages of its room
for the section's opening pages, which it reads first for what Part 1 says.

A unit already dispatched keeps the spans it was dispatched with, so a replan never changes the
pages a reader was sent for: its pages count as covered where the section still sits on the same
file and they still fall inside its range, and the planner divides only what is left. A dispatched
part whose pages no longer fall on its section is retired, and its pages are planned again.
"""

from __future__ import annotations

from typing import Iterable

# The pages a review reads of its own package's manual, before its manual parts.
REVIEW_PAGES = 20
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


def _remaining(sections: list[dict], covered: Iterable[dict]) -> list[tuple[dict, int, int]]:
    """Each section's runs of pages no covered span reads, in section order."""
    taken: dict[str, set[int]] = {}
    for span in covered:
        taken.setdefault(span["code"], set()).update(range(span["fromPage"], span["toPage"] + 1))
    runs: list[tuple[dict, int, int]] = []
    for section in sections:
        done = taken.get(section["code"], set())
        start = None
        for page in range(section["pageStart"], section["pageEnd"] + 2):
            inside = page <= section["pageEnd"] and page not in done
            if inside and start is None:
                start = page
            elif not inside and start is not None:
                runs.append((section, start, page - 1))
                start = None
    return runs


def divide(
    sections: list[dict],
    review_frozen: list[dict] | None,
    parts_frozen: list[list[dict]],
) -> tuple[list[dict], list[list[dict]]]:
    """
    The review's spans and each new manual part's spans for one package. `review_frozen` is the
    spans a dispatched review was sent with (None where the review is not dispatched yet), and
    `parts_frozen` the spans of each dispatched part still valid; their pages count as covered and
    are never handed out again. The review's spans come back as frozen where it was dispatched.
    """
    covered = list(review_frozen or []) + [span for part in parts_frozen for span in part]
    runs = _remaining(sections, covered)
    capacities = [] if review_frozen is not None else [REVIEW_PAGES]
    units: list[list[dict]] = []
    current: list[dict] = []
    capacity = capacities[0] if capacities else PART_PAGES
    room = capacity

    def close() -> None:
        nonlocal current, capacity, room
        units.append(current)
        current = []
        capacity = PART_PAGES
        room = capacity

    index = 0
    while index < len(runs):
        section, start, end = runs[index]
        pages = end - start + 1
        if not current and start > section["pageStart"]:
            # A unit opening partway into a section reads its opening pages first.
            room = capacity - CONTEXT_RESERVE
        if pages <= room:
            current.append(_span(section, start, end))
            room -= pages
            index += 1
            continue
        fresh_room = PART_PAGES - (CONTEXT_RESERVE if start > section["pageStart"] else 0)
        opening_review = not units and review_frozen is None
        if (current or opening_review) and (pages <= fresh_room or room < MIN_SPLIT):
            # A section that fits a fresh part, or a sliver of room, starts the next unit; the
            # review, empty, reads no page of a section a part can hold whole.
            close()
            continue
        take = room
        left = pages - take
        if left < MIN_SPLIT and take - (MIN_SPLIT - left) >= MIN_SPLIT:
            # Leave the unit after a few pages to read rather than one or two.
            take -= MIN_SPLIT - left
        current.append(_span(section, start, start + take - 1))
        runs[index] = (section, start + take, end)
        close()
    if current or (capacities and not units):
        close()

    if review_frozen is not None:
        return review_frozen, [unit for unit in units if unit]
    review, parts = units[0], units[1:]
    return review, [unit for unit in parts if unit]


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
