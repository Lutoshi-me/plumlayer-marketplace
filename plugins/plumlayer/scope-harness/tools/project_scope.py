"""
project_scope.py — project scope-item claims into trade checklists and the gap log.

PLU-323 guard: superseded route-first tool retained for PLU-274 history/migration only.

Doctrine role (agents read and judge; deterministic tooling grounds; nothing governs unverified):
  * Deterministic PROJECTION tool — reads proposed scope-item claims, groups by
    subject, resolves predicate map, routes to output files.
  * Does NOT assign trades or interpret scope meaning; that is the agent-read.
  * Contested and unowned items → cross_trade_gap_log.md (regardless of
    belongsToTrade). "clear" items → scope_checklist_<trade>.md.
  * Every output document carries a mandatory header warning: proposed claims,
    not governing truth.
  * Honest counts: prints trade count, contested, unowned.

Usage:
  python project_scope.py \\
    --claims output/scope/scope_claims.jsonl \\
    --out-dir output/scope/
"""

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path


HEADER_WARNING = """\
> **Proposed claims — not governing truth. The drawings govern; this checklist
> assists. Verify every line against the source; citations may be
> agent-estimated regions.**

"""


# ---------------------------------------------------------------------------
# Claims loading and grouping
# ---------------------------------------------------------------------------

def _load_claims(claims_path: Path) -> list[dict]:
    claims = []
    with claims_path.open("r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            claims.append(json.loads(line))
    return claims


def _group_by_subject(claims: list[dict]) -> dict[str, dict]:
    """
    Group claims by subject → predicate map.
    If a subject has multiple rows for the same predicate, the last one wins
    (the JSONL is presumed to be chronological / re-assertion order).
    """
    subjects: dict[str, dict] = defaultdict(dict)
    for claim in claims:
        subj = claim.get("subject", "")
        pred = claim.get("predicate", "")
        if subj and pred:
            subjects[subj][pred] = claim
    return dict(subjects)


# ---------------------------------------------------------------------------
# Evidence formatting
# ---------------------------------------------------------------------------

def _format_evidence(claim: dict) -> str:
    """
    Build a compact citation string for one claim row.
    Prefers the trade-agnostic (decompose) evidence — the entry with no
    claimedBy — so the headline citation is the neutral one; falls back to the
    first entry.
    """
    evs = claim.get("evidence", [])
    if not evs:
        return "(no citation)"
    ev = next((e for e in evs if not e.get("claimedBy")), evs[0])
    source = ev.get("source", "")
    snippet = ev.get("snippet", "")
    if snippet:
        return f"{source} — \"{snippet}\""
    return source


def _format_claimant_evidence(claim: dict) -> list[str]:
    """
    v0.1: list EVERY claimant's citation on a contested item, labelled by the
    trade that cited it (claimedBy). This is what lets review confirm the overlap
    by clicking each claimant's own receipt rather than re-reading the sheet.
    Returns one formatted line per claimant-tagged evidence entry.
    """
    lines: list[str] = []
    for ev in claim.get("evidence", []):
        claimed_by = ev.get("claimedBy")
        if not claimed_by:
            continue  # the decompose evidence is the headline, shown separately
        source = ev.get("source", "")
        snippet = ev.get("snippet", "")
        cite = f"{source} — \"{snippet}\"" if snippet else source
        lines.append(f"  - **{claimed_by}** cites: {cite}")
    return lines


# ---------------------------------------------------------------------------
# Scope-item dict from predicate map
# ---------------------------------------------------------------------------

def _resolve_item(predicate_map: dict) -> dict:
    """Extract a flat scope-item record from a subject's predicate map."""

    def val(pred):
        claim = predicate_map.get(pred)
        return claim["value"] if claim else None

    return {
        "title": val("title"),
        "scopeText": val("scopeText"),
        "belongsToTrade": val("belongsToTrade"),
        "candidateTrades": val("candidateTrades") or [],
        "tradeContest": val("tradeContest"),
        "furnishedBy": val("furnishedBy"),
        "installedBy": val("installedBy"),
        "isShownOn": val("isShownOn") or [],
        "confidence": val("confidence"),
        "provenance": val("provenance") or "decompose",
        # Evidence is read off the scopeText claim. This is safe ONLY because
        # emit_claim_rows writes the SAME merged citation list (decompose + every
        # claimant, each tagged with claimedBy) onto every predicate row — so the
        # scopeText row carries the full claimant breakdown _format_claimant_evidence
        # needs. If a future change ever emits predicate-specific citation subsets,
        # the gap-log claimant rendering must stop relying on scopeText here.
        "_evidenceClaim": predicate_map.get("scopeText"),
    }


# ---------------------------------------------------------------------------
# Rendering helpers
# ---------------------------------------------------------------------------

def _checklist_line(item: dict) -> str:
    ev_claim = item.get("_evidenceClaim") or {}
    citation = _format_evidence(ev_claim)
    conf = item.get("confidence")
    conf_str = f" [conf={conf:.2f}]" if conf is not None else ""
    fb = item.get("furnishedBy")
    ib = item.get("installedBy")
    scope = item.get("scopeText") or "(no scope text)"
    title = item.get("title") or scope
    # Brief title is the headline; the detailed scopeText is the sub-line beneath
    # (the v0.2 brief/detailed split — also what the interactive view renders).
    parts = [f"- **{title}**{conf_str}"]
    if scope and scope.strip() != title.strip():
        parts.append(f"  - {scope}")
    # net-new = a trade surfaced scope the generalist decompose missed (the
    # fan-out earning its keep). Mark it so the reviewer sees it wasn't scheduled.
    provenance = item.get("provenance") or "decompose"
    if provenance.startswith("net-new"):
        raiser = provenance.split(":", 1)[1] if ":" in provenance else "a trade"
        parts.append(f"  - Surfaced by **{raiser}** — not itemized on the schedule (decompose missed it)")
    if fb:
        parts.append(f"  - Furnished by: {fb}")
    if ib:
        parts.append(f"  - Installed by: {ib}")
    parts.append(f"  - Citation: {citation}")
    shown = item.get("isShownOn") or []
    if shown:
        parts.append(f"  - Shown on: {', '.join(shown)}")
    return "\n".join(parts)


def _gap_log_row(item: dict, subject: str) -> str:
    ev_claim = item.get("_evidenceClaim") or {}
    citation = _format_evidence(ev_claim)
    contest = item.get("tradeContest") or "unknown"
    candidates = item.get("candidateTrades") or []
    scope = item.get("scopeText") or "(no scope text)"
    title = item.get("title") or scope
    conf = item.get("confidence")
    conf_str = f" [conf={conf:.2f}]" if conf is not None else ""
    candidate_str = ", ".join(candidates) if candidates else "none"
    shown = item.get("isShownOn") or []
    shown_str = ", ".join(shown) if shown else "—"
    # status gloss: unowned = no trade claimed (highest-value RFI); contested =
    # >=2 trades independently claimed it (a measured boundary).
    gloss = {
        "contested": ">=2 trades independently claimed this — a measured boundary",
        "unowned": "no trade claimed this — highest-value RFI candidate",
    }.get(contest, "")
    gloss_str = f"  _({gloss})_" if gloss else ""
    row = f"### {title}{conf_str}\n"
    if scope and scope.strip() != title.strip():
        row += f"- **Scope:** {scope}\n"
    row += (
        f"- **Status:** {contest}{gloss_str}\n"
        f"- **Claimed by:** {candidate_str}\n"
        f"- **Shown on:** {shown_str}\n"
        f"- **Decompose citation:** {citation}\n"
    )
    claimant_lines = _format_claimant_evidence(ev_claim)
    if claimant_lines:
        row += "- **Claimant citations:**\n" + "\n".join(claimant_lines) + "\n"
    row += f"- **Subject:** `{subject}`\n"
    return row


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Project scope-item claims into trade checklists and the gap log."
    )
    parser.add_argument(
        "--claims", required=True, help="Path to scope_claims.jsonl"
    )
    parser.add_argument(
        "--out-dir", required=True, help="Output directory for checklists and gap log"
    )
    args = parser.parse_args()

    claims_path = Path(args.claims)
    if not claims_path.exists():
        print(f"[error] claims file not found: {claims_path}", file=sys.stderr)
        sys.exit(1)

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    claims = _load_claims(claims_path)
    subjects = _group_by_subject(claims)

    # --- route items ---
    # trade -> list of items (clear only)
    trade_items: dict[str, list[tuple[str, dict]]] = defaultdict(list)
    gap_items: list[tuple[str, dict]] = []  # (subject, item) for contested + unowned

    for subject, pred_map in subjects.items():
        item = _resolve_item(pred_map)
        contest = item.get("tradeContest")
        if contest in ("contested", "unowned"):
            gap_items.append((subject, item))
        elif contest == "clear":
            trade = item.get("belongsToTrade") or "unknown-trade"
            trade_items[trade].append((subject, item))
        else:
            # unknown contest value — route to gap log defensively
            print(
                f"[warn] subject {subject!r} has unexpected tradeContest={contest!r} — "
                f"routing to gap log",
                file=sys.stderr,
            )
            gap_items.append((subject, item))

    contested_count = sum(
        1 for _, item in gap_items if item.get("tradeContest") == "contested"
    )
    unowned_count = sum(
        1 for _, item in gap_items if item.get("tradeContest") == "unowned"
    )

    # --- write per-trade checklists ---
    for trade, items in sorted(trade_items.items()):
        safe_trade = trade.replace(" ", "_").replace("/", "-").lower()
        out_path = out_dir / f"scope_checklist_{safe_trade}.md"
        lines = [
            f"# Scope Checklist — {trade}\n",
            HEADER_WARNING,
            f"**Items: {len(items)}**\n\n",
        ]
        for subject, item in items:
            lines.append(_checklist_line(item))
            lines.append(f"\n  *(subject: `{subject}`)*\n")
        out_path.write_text("\n".join(lines), encoding="utf-8")

    # --- write cross-trade gap log ---
    gap_path = out_dir / "cross_trade_gap_log.md"
    gap_lines = [
        "# Cross-Trade Gap Log\n",
        HEADER_WARNING,
        f"**Contested: {contested_count}  |  Unowned: {unowned_count}**\n\n",
    ]
    if gap_items:
        gap_lines.append("---\n")
        for subject, item in gap_items:
            gap_lines.append(_gap_log_row(item, subject))
            gap_lines.append("---\n")
    gap_path.write_text("\n".join(gap_lines), encoding="utf-8")

    n_trades = len(trade_items)
    print(
        f"[ok] {n_trades} trade{'s' if n_trades != 1 else ''}, "
        f"{contested_count} contested, {unowned_count} unowned"
    )
    for trade in sorted(trade_items):
        print(f"  -> scope_checklist_{trade.replace(' ', '_').replace('/', '-').lower()}.md")
    print(f"  -> cross_trade_gap_log.md")


if __name__ == "__main__":
    main()
