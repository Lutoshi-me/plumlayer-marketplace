"""
scope_claim_schema.py — pure schema, mint, validate, and writer for scope-item claims.

PLU-323 guard: superseded route-first support module retained for PLU-274 history/migration only.

Doctrine role (agents read and judge; deterministic tooling grounds; nothing governs unverified):
  * Deterministic GROUNDING layer — this module mints subjects and emits claim rows;
    it never infers scope meaning or trade assignments. Those come from the agent-read.
  * Every claim emitted is trustClass="proposed" unconditionally. Nothing governs
    unverified. The agent synthesises; grounding proves tokens; human reviews promote.
  * No citation → item rejected, never silently dropped.

Importable — no argparse, no I/O side effects. All I/O is in the caller.
Stdlib + no dependencies.
"""

import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Any

# ---------------------------------------------------------------------------
# Subject minting
# ---------------------------------------------------------------------------

def _normalize_scope_text(text: str) -> str:
    """Collapse whitespace and lowercase for deterministic hashing."""
    return re.sub(r"\s+", " ", text.strip().lower())


def mint_subject(scope_text: str, primary_sheet_id: str, cluster_name: str) -> str:
    """
    Mint a deterministic scope-item subject URI.

    Format: "scopeItem:<12 hex>"
    Input to sha256: "(cluster|scopeText|primarySheetId)" — normalized.
    """
    norm = _normalize_scope_text(scope_text)
    payload = f"({cluster_name}|{norm}|{primary_sheet_id})"
    digest = hashlib.sha256(payload.encode("utf-8")).hexdigest()
    return f"scopeItem:{digest[:12]}"


# ---------------------------------------------------------------------------
# Claim row shape (mirrors sheet_inventory_claims.jsonl)
# ---------------------------------------------------------------------------

def _make_claim_row(
    subject: str,
    predicate: str,
    value: Any,
    citations: list[dict],
    confidence: float,
) -> dict:
    """
    Emit one claim row.  trustClass is forced to "proposed"; assertedBy is
    "agent-read"; promotedBy is null.  evidence is built from citations list.
    """
    # source is derived from each citation's own sheetId (which already encodes
    # the set, e.g. "PROJECT-DD-p093") — never a hardcoded set tag. Falls back to
    # the bare page when a sheetId is somehow absent. This is what makes the
    # schema set-agnostic; nothing here names a specific project.
    #
    # claimedBy (v0.1): when a citation came from a specific trade lens's read
    # (vs the trade-agnostic decompose), it is carried through on the evidence so
    # a contested line can show *which trade* cited *which* region — review =
    # confirm the overlap, click each claimant's receipt.
    evidence = []
    for c in citations:
        ev = {
            "source": c.get("sheetId") or f"p{c['pageNum']}",
            "locator": {
                "frame": "normalized-page",
                "bboxPts": c["bboxNorm"],
            },
            "method": "agent-synthesis",
            "snippet": c.get("snippet", ""),
        }
        if c.get("claimedBy"):
            ev["claimedBy"] = c["claimedBy"]
        evidence.append(ev)
    return {
        "subject": subject,
        "predicate": predicate,
        "value": value,
        "evidence": evidence,
        "trustClass": "proposed",
        "confidence": round(float(confidence), 4),
        "status": "current",
        "assertedBy": "agent-read",
        "promotedBy": None,
    }


# ---------------------------------------------------------------------------
# Emit all predicate rows for one scope item
# ---------------------------------------------------------------------------

def emit_claim_rows(
    scope_text: str,
    candidate_trades: list[str],
    resolved_trade: str | None,
    trade_contest: str,
    furnished_by: str | None,
    installed_by: str | None,
    shown_on: list[str],
    confidence: float,
    citations: list[dict],
    subject: str,
    provenance: str = "decompose",
    title: str | None = None,
) -> list[dict]:
    """
    Emit one claim row per predicate for the given scope item.
    All rows share the same minted subject.

    provenance (v0.1) records HOW the item entered the scope: "decompose" (the
    trade-agnostic read emitted it) or "net-new:<trade>" (a trade lens raised
    scope the generalist decompose missed — the fan-out earning its keep).

    title (v0.2) is the brief label; scopeText is the detailed descriptor. When
    title is absent (a pre-v0.2 read), it falls back to a truncated scopeText so
    the projection always has a headline.
    """
    rows = []
    rows.append(_make_claim_row(subject, "title", title or scope_text[:80], citations, confidence))
    rows.append(_make_claim_row(subject, "scopeText", scope_text, citations, confidence))
    rows.append(_make_claim_row(subject, "belongsToTrade", resolved_trade, citations, confidence))
    rows.append(_make_claim_row(subject, "candidateTrades", candidate_trades, citations, confidence))
    rows.append(_make_claim_row(subject, "tradeContest", trade_contest, citations, confidence))
    rows.append(_make_claim_row(subject, "furnishedBy", furnished_by, citations, confidence))
    rows.append(_make_claim_row(subject, "installedBy", installed_by, citations, confidence))
    rows.append(_make_claim_row(subject, "isShownOn", shown_on, citations, confidence))
    rows.append(_make_claim_row(subject, "confidence", confidence, citations, confidence))
    rows.append(_make_claim_row(subject, "provenance", provenance, citations, confidence))
    return rows


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------

VALID_TRADE_CONTESTS = {"clear", "contested", "unowned"}


def validate_agent_read(data: dict) -> list[str]:
    """
    Validate a parsed agent-read JSON dict against the scope-read-v0 contract.
    Returns a list of error strings; empty list means valid.
    """
    errors: list[str] = []

    if data.get("schemaVersion") != "scope-read-v0":
        errors.append(
            f"schemaVersion must be 'scope-read-v0', got {data.get('schemaVersion')!r}"
        )

    items = data.get("scopeItems")
    if not isinstance(items, list):
        errors.append("scopeItems must be a list")
        return errors

    for idx, item in enumerate(items):
        loc = f"scopeItems[{idx}]"

        # scopeText
        if not isinstance(item.get("scopeText"), str) or not item["scopeText"].strip():
            errors.append(f"{loc}: scopeText must be a non-empty string")

        # candidateTrades
        ct = item.get("candidateTrades")
        if not isinstance(ct, list) or len(ct) == 0:
            errors.append(f"{loc}: candidateTrades must be a non-empty list")

        # tradeContest
        tc = item.get("tradeContest")
        if tc not in VALID_TRADE_CONTESTS:
            errors.append(
                f"{loc}: tradeContest must be one of {sorted(VALID_TRADE_CONTESTS)}, got {tc!r}"
            )

        # resolvedTrade — must be null unless tradeContest == "clear"
        rt = item.get("resolvedTrade")
        if tc == "clear" and rt is None:
            errors.append(f"{loc}: resolvedTrade must be set when tradeContest='clear'")
        if tc != "clear" and rt is not None:
            errors.append(
                f"{loc}: resolvedTrade must be null when tradeContest is {tc!r}, got {rt!r}"
            )

        # confidence
        conf = item.get("confidence")
        if not isinstance(conf, (int, float)) or not (0.0 <= conf <= 1.0):
            errors.append(f"{loc}: confidence must be a float 0.0–1.0, got {conf!r}")

        # citations
        cits = item.get("citations")
        if not isinstance(cits, list) or len(cits) == 0:
            errors.append(f"{loc}: citations must be a non-empty list")
        else:
            for cidx, c in enumerate(cits):
                cloc = f"{loc}.citations[{cidx}]"
                if not isinstance(c.get("sheetId"), str):
                    errors.append(f"{cloc}: sheetId must be a string")
                if not isinstance(c.get("pageNum"), int):
                    errors.append(f"{cloc}: pageNum must be an int")
                bn = c.get("bboxNorm")
                if not (isinstance(bn, list) and len(bn) == 4):
                    errors.append(f"{cloc}: bboxNorm must be a 4-element list")
                if not isinstance(c.get("snippet"), str):
                    errors.append(f"{cloc}: snippet must be a string")

    return errors


# ---------------------------------------------------------------------------
# Writer
# ---------------------------------------------------------------------------

def write_scope_claims(
    items: list[dict],
    out_path: Path,
) -> tuple[int, int]:
    """
    Write scope-item claim rows to a JSONL file.

    Each item in `items` is expected to be a processed dict with keys:
      subject, scopeText, candidateTrades, resolvedTrade, tradeContest,
      furnishedBy, installedBy, isShownOn, confidence, citations.

    Rejects (and prints) any item with empty citations.
    Returns (written_count, rejected_count).
    """
    written = 0
    rejected = 0

    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    with out_path.open("w", encoding="utf-8") as fh:
        for item in items:
            citations = item.get("citations", [])
            if not citations:
                print(
                    f"[reject] no citations — item dropped: {item.get('scopeText', '')[:80]!r}",
                    file=sys.stderr,
                )
                rejected += 1
                continue

            rows = emit_claim_rows(
                scope_text=item["scopeText"],
                candidate_trades=item["candidateTrades"],
                resolved_trade=item["resolvedTrade"],
                trade_contest=item["tradeContest"],
                furnished_by=item.get("furnishedBy"),
                installed_by=item.get("installedBy"),
                shown_on=item.get("isShownOn", []),
                confidence=item["confidence"],
                citations=citations,
                subject=item["subject"],
                provenance=item.get("provenance", "decompose"),
                title=item.get("title"),
            )
            for row in rows:
                fh.write(json.dumps(row) + "\n")
            written += 1

    return written, rejected
