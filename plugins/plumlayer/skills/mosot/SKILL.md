---
name: mosot
description: Work with a Plumlayer MOSOT — the cloud source of truth for a construction project's claims. Use when the user wants to read, search, review, or propose claims on their Plumlayer projects (sheet/set grid, ambiguities, RFI candidates, scope/door takeoffs), or asks "what's in my MOSOT / project". Explains the verb surface and the propose-only, human-promotes doctrine.
---

# Working a Plumlayer MOSOT

A **MOSOT** (Machine-Optimized Source of Truth) is the cloud, claim-based model of a
construction project's *current governing truth*. Each Plumlayer **project is one MOSOT**.
You interact with it through the `plumlayer` MCP tools (every tool is scoped to the
signed-in user's own projects).

## The atom: a Claim
`subject — predicate — value` + evidence + trust class. Examples:
- `sheet:A-101 — title — "First Floor Plan"`
- `door:103 — count — 6`

## Trust + the non-negotiable rule
Trust tiers: `approved > authoritative > derived`; **`proposed` never governs.**
- **You (the agent) read and judge, and write ONLY `proposed` claims.** You never promote.
- **A human reviews and promotes** on plumlayer.com. `propose` is the only write door —
  there is no promote verb here, by design.
- **Ground every claim you propose with evidence** (the source it came from). Nothing
  governs unverified — an ungrounded claim is a guess; say so.

## The verbs
**Identity / discovery**
- `whoami` — confirm which account you're acting as.
- `list_projects` — the user's projects (each is a MOSOT). Confirm the right one before acting.
- `get_project` — one project's details.

**Read**
- `set_grid` — the sheet inventory (the drawing set as a grid: discipline, sheet number,
  governing issue, open-ambiguity count per sheet).
- `ambiguities` — the open-conflict / review ledger, severity-sorted (legitimate-RFI first).
- `rfi_candidates` — drafted RFI candidates with citations.
- `search` — the raw claim ledger (ANY trust class, including `proposed`). Filter by
  subject / predicate / trustClass / text; paginated. Use this to see what's actually been
  asserted — including your own proposals.

**Write**
- `propose` — append one `proposed` claim (`subject`, `predicate`, `value`,
  `sourceInstrument`, optional `evidence`/`ambiguityClass`). Stamped as you; never governs
  until a human promotes it.

## Typical flows
- **"What's in my project / MOSOT?"** → `list_projects` → pick one → `set_grid` for the
  drawing set, `ambiguities` for open issues, `rfi_candidates` for drafted RFIs; `search`
  to inspect specific subjects/claims.
- **"Take off / scope something"** → read the relevant sheets/claims, judge, then `propose`
  grounded claims (`sourceInstrument` = where it came from, plus `evidence`). Tell the user
  they're *proposed* and that review/promotion happens on plumlayer.com.
- **"Find conflicts / RFIs"** → `ambiguities` + `rfi_candidates`; where you spot a real
  conflict, `propose` an ambiguity-flagged claim (`ambiguityClass`), cited.

## Discipline
- Never present a `proposed` claim as settled truth — it's a candidate for human review.
- Always cite. Separate what's grounded from what's inferred.
- One project = one MOSOT; always act within the correct `projectId`.
