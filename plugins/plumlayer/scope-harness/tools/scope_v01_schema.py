"""
scope_v01_schema.py — contracts for per-trade fan-out routing.

(Filename is historical — the module now carries scope-decompose-**v0.3** and
trade-claim-**v0.2**; the two versions advance independently. See the constants
below.)

Doctrine role (agents read and judge; deterministic tooling grounds; nothing governs unverified):
  * Two agent-read contracts replace v0's single generalist read that
    *declared* tradeContest:
      - scope-decompose-v0.3 : a trade-AGNOSTIC read of the set -> scope items,
        each cited, with an is-it-real confidence + optional appliesTo (grouped
        instances). NO trade is assigned here.
      - trade-claim-v0.2     : one per trade lens. Each trade agent reads the
        SAME packet and declares which decomposed items are *its* scope (by
        itemId reference), with its own citations. May also raise netNewItems
        the generalist decompose missed.
  * Routing (clear/contested/unowned) is then COMPUTED from the overlap of
    these independent claims by reconcile_overlap.py — it is measured, not
    asserted. This module only validates the read contracts; it never routes.
  * Every downstream claim is trustClass="proposed". Nothing governs unverified.

Importable — pure validation, no I/O side effects. Stdlib only.
"""

from typing import Any

DECOMPOSE_SCHEMA_VERSION = "scope-decompose-v0.3"
TRADE_CLAIM_SCHEMA_VERSION = "trade-claim-v0.2"

# v0.2 adds a brief `title` alongside the detailed `scopeText` on every
# decompose item and net-new item — the brief/detailed split the per-trade
# checklists and the eventual interactive view both need. `scopeText` stays the
# canonical detailed descriptor (and the subject-hash input), so the split is
# additive: title is a new required string, scopeText is unchanged.
#
# v0.3 (read-grain doctrine) adds optional `appliesTo` on a decompose item:
# the list of instance labels (rooms / openings / locations) a single kind-of-work
# item covers. This is the load-bearing carrier for the grain rule — "one item per
# kind of work, instances grouped" — so grouping a finish across many rooms loses
# NO information (every room is still named) while the item count stays a function
# of the drawings' variety, not enumeration stamina
# (see $CLAUDE_PLUGIN_ROOT/scope-harness/reference/read-grain.md). Optional +
# additive: absent on items with no instance set (a single assembly, one detail);
# a list of strings when present.


# ---------------------------------------------------------------------------
# Shared: citation validation (same shape across both contracts and v0)
# ---------------------------------------------------------------------------

def _validate_citations(cits: Any, loc: str) -> list[str]:
    """Validate a citations list. Returns error strings (empty == valid)."""
    errors: list[str] = []
    if not isinstance(cits, list) or len(cits) == 0:
        errors.append(f"{loc}: citations must be a non-empty list")
        return errors
    for cidx, c in enumerate(cits):
        cloc = f"{loc}.citations[{cidx}]"
        if not isinstance(c.get("sheetId"), str) or not c["sheetId"]:
            errors.append(f"{cloc}: sheetId must be a non-empty string")
        if not isinstance(c.get("pageNum"), int):
            errors.append(f"{cloc}: pageNum must be an int")
        bn = c.get("bboxNorm")
        if not (isinstance(bn, list) and len(bn) == 4):
            errors.append(f"{cloc}: bboxNorm must be a 4-element list")
        if not isinstance(c.get("snippet"), str):
            errors.append(f"{cloc}: snippet must be a string")
    return errors


def _validate_confidence(conf: Any, loc: str) -> list[str]:
    if not isinstance(conf, (int, float)) or not (0.0 <= conf <= 1.0):
        return [f"{loc}: confidence must be a float 0.0-1.0, got {conf!r}"]
    return []


# ---------------------------------------------------------------------------
# Decompose-read contract
# ---------------------------------------------------------------------------

def validate_decompose_read(data: dict) -> list[str]:
    """
    Validate a parsed scope-decompose-v0.3 read.

    Invariant the whole fan-out rests on: itemId is non-empty and UNIQUE within
    the read (per-trade claims reference items by itemId; a collision would
    silently merge two distinct scope items). Returns error strings.
    """
    errors: list[str] = []

    if data.get("schemaVersion") != DECOMPOSE_SCHEMA_VERSION:
        errors.append(
            f"schemaVersion must be {DECOMPOSE_SCHEMA_VERSION!r}, got {data.get('schemaVersion')!r}"
        )
    if not isinstance(data.get("setId"), str) or not data.get("setId"):
        errors.append("setId must be a non-empty string")

    items = data.get("items")
    if not isinstance(items, list):
        errors.append("items must be a list")
        return errors

    seen_ids: set[str] = set()
    for idx, item in enumerate(items):
        loc = f"items[{idx}]"
        item_id = item.get("itemId")
        if not isinstance(item_id, str) or not item_id.strip():
            errors.append(f"{loc}: itemId must be a non-empty string")
        elif item_id in seen_ids:
            errors.append(f"{loc}: duplicate itemId {item_id!r} (must be unique within the read)")
        else:
            seen_ids.add(item_id)

        if not isinstance(item.get("title"), str) or not item["title"].strip():
            errors.append(f"{loc}: title must be a non-empty string (brief label)")
        if not isinstance(item.get("scopeText"), str) or not item["scopeText"].strip():
            errors.append(f"{loc}: scopeText must be a non-empty string (detailed descriptor)")

        errors.extend(_validate_confidence(item.get("confidence"), loc))
        errors.extend(_validate_citations(item.get("citations"), loc))

        # v0.3: appliesTo — optional list of instance labels (rooms/openings/...)
        applies = item.get("appliesTo")
        if applies is not None and not (
            isinstance(applies, list) and all(isinstance(a, str) for a in applies)
        ):
            errors.append(f"{loc}: appliesTo must be a list of strings when present")

    return errors


def decompose_item_ids(data: dict) -> set[str]:
    """Return the set of itemIds declared in a (validated) decompose read."""
    return {it["itemId"] for it in data.get("items", []) if isinstance(it.get("itemId"), str)}


# ---------------------------------------------------------------------------
# Trade-claim contract
# ---------------------------------------------------------------------------

def validate_trade_claim_read(data: dict, known_item_ids: set[str] | None = None) -> list[str]:
    """
    Validate a parsed trade-claim-v0.2 read.

    If known_item_ids is given (the decompose read's itemIds), each claim's
    itemId MUST be present in it — a dangling reference is a hard error (the
    claim points at a scope item that does not exist). netNewItems are exempt:
    they are, by definition, scope the decompose read did not emit.
    """
    errors: list[str] = []

    if data.get("schemaVersion") != TRADE_CLAIM_SCHEMA_VERSION:
        errors.append(
            f"schemaVersion must be {TRADE_CLAIM_SCHEMA_VERSION!r}, got {data.get('schemaVersion')!r}"
        )
    if not isinstance(data.get("setId"), str) or not data.get("setId"):
        errors.append("setId must be a non-empty string")
    if not isinstance(data.get("tradeLens"), str) or not data.get("tradeLens"):
        errors.append("tradeLens must be a non-empty string")

    claims = data.get("claims")
    if not isinstance(claims, list):
        errors.append("claims must be a list")
        return errors

    seen_claim_ids: set[str] = set()
    for idx, claim in enumerate(claims):
        loc = f"claims[{idx}]"
        item_id = claim.get("itemId")
        if not isinstance(item_id, str) or not item_id.strip():
            errors.append(f"{loc}: itemId must be a non-empty string")
        else:
            if item_id in seen_claim_ids:
                errors.append(f"{loc}: trade claims itemId {item_id!r} more than once")
            seen_claim_ids.add(item_id)
            if known_item_ids is not None and item_id not in known_item_ids:
                errors.append(
                    f"{loc}: itemId {item_id!r} not in the decompose read (dangling claim reference)"
                )
        # citations are this trade's OWN evidence for the claim
        errors.extend(_validate_citations(claim.get("citations"), loc))

    # netNewItems — optional; same shape as decompose items minus itemId
    net_new = data.get("netNewItems", [])
    if not isinstance(net_new, list):
        errors.append("netNewItems must be a list when present")
    else:
        for idx, item in enumerate(net_new):
            loc = f"netNewItems[{idx}]"
            if not isinstance(item.get("title"), str) or not item["title"].strip():
                errors.append(f"{loc}: title must be a non-empty string (brief label)")
            if not isinstance(item.get("scopeText"), str) or not item["scopeText"].strip():
                errors.append(f"{loc}: scopeText must be a non-empty string (detailed descriptor)")
            errors.extend(_validate_confidence(item.get("confidence"), loc))
            errors.extend(_validate_citations(item.get("citations"), loc))

    return errors
