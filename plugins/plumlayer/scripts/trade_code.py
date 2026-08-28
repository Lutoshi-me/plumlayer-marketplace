"""
trade_code.py: resolve a catalog trade code to the trade knowledge that covers it.

A trade file is general to its family. The masonry file is what a reader loads for any masonry
package, whether the estimator drafted that package on a narrow section or a broad one, so the map
keys one code per trade file and a package carrying some other code in the same family resolves to
it here rather than finding nothing.

Resolution is by nearest CSI ancestor: the code itself, then each broader section above it, and the
first one the map holds wins. A code with no mapped ancestor resolves to nothing, which is a package
the plan names rather than a package it guesses a trade file for.

    04 22 13  ->  04 22 00  ->  04 20 00  ->  04 00 00

This walks up only. A package drafted on a division that the map keys below (a masonry package on
04 00 00, where the map's key is 04 20 00) does not resolve, because a division holds several trade
files in the general case and picking one of them would be a guess.

Shared by plan_inventory.py, which resolves a package's trade to a sheet family, and by
cut_pass_knowledge.py, which resolves a pass's trade to the file it cuts. One resolver, so the plan
and the cut can never land on different trade files for the same package.
"""

from __future__ import annotations

# A CSI section number is six digits, in three pairs: the division, the group within it, and the
# section within that. Anything after a dot is a level 5 refinement and is not part of the section.
CSI_DIGITS = 6


def fold(code: str) -> str:
    """
    A trade code with its spaces removed, lower cased. The catalog spaces its ids and a caller may
    not, and this is the same fold the record's own catalog lookup uses, so the two agree.
    """
    return "".join(code.split()).lower()


def ancestors(code: str) -> list[str]:
    """
    The code itself, then every broader CSI section above it, nearest first: the section, the group,
    then the division. Each is returned folded. A code carrying fewer than two digits has no
    hierarchy to walk and comes back on its own.
    """
    folded = fold(code)
    digits = "".join(ch for ch in folded.split(".")[0] if ch.isdigit())
    chain = [folded]
    if len(digits) >= 2:
        padded = digits[:CSI_DIGITS].ljust(CSI_DIGITS, "0")
        for broader in (padded[:4] + "00", padded[:3] + "000", padded[:2] + "0000"):
            if broader not in chain:
                chain.append(broader)
    return chain


def resolve(code: str, keys: dict):
    """
    What the map holds for this code, and how it was found: `(value, "exact")` where the map keys
    this very code, `(value, "family")` where it keys a broader section that covers it, and None
    where it keys neither. `keys` is folded code to whatever the caller wants back.

    Nearest wins by construction, since the walk goes outward one step at a time and stops at the
    first hit: a code under both a mapped group and a mapped division lands on the group.
    """
    for step, candidate in enumerate(ancestors(code)):
        if candidate in keys:
            return keys[candidate], ("exact" if step == 0 else "family")
    return None
