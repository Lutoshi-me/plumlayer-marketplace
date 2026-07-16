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
- `create_project` — create a new project (= a new MOSOT). Supply `name` (required) and optional
  `description`; returns the new `projectId`. Use before any propose or upload on a new bid/pursuit.

**Read**
- `set_grid` — the sheet inventory (the drawing set as a grid: discipline, sheet number,
  governing issue, open-ambiguity count per sheet).
- `ambiguities` — the open-conflict / review ledger, severity-sorted (legitimate-RFI first).
- `rfi_candidates` — drafted RFI candidates with citations.
- `search` — the raw claim ledger (ANY trust class, including `proposed`). Filter by
  subject / predicate / trustClass / text; paginated. Use this to see what's actually been
  asserted — including your own proposals.

**Drawing recognition** (cloud PDF — these work against files already uploaded to the project)
- `list_files` — list the drawing files registered to a project.
- `register_pages` — once per project, register renderable page rows for every uploaded PDF (not
  claims, just viewable pages) so uploaded files are readable even before recognition runs.
- `recognize_sheets` — start the async deterministic bulk sheet-number recognition pass over one
  uploaded PDF. Returns `{jobId, status}` immediately; poll `recognize_sheets_status` rather than
  waiting inline. Recognized sheet claims deposit server-side as `proposed` on success — never
  `propose_batch` them yourself.
- `recognize_sheets_status` — poll a `recognize_sheets` job. Returns run counts (`report`), the
  server-side deposit summary (`deposit`), and the residue tail (`residue`) for you to read and
  judge; it never carries the recognized claims themselves.
- `render_page` — render a single page of a registered PDF to an image so you can read it.
- `get_page_text` — extract the text layer from a registered PDF page (deterministic; use
  alongside `render_page` — text for tokens, render for layout/meaning).

**Delivery** (group uploaded files into a source package)
- `list_drawing_deliveries` — list a project's registered drawing deliveries (baseline sets and
  revision packages like bulletins/addenda).
- `create_drawing_delivery` — register one delivery (e.g. "2025-12-15 Conformed Set" as
  `deliveryKind: "baseline"`, or "2026-02-09 Bulletin 01" as `"revision"`). Project metadata, not a
  governing claim. Attach files with `register_file.deliveryId`, then recognize with
  `recognize_sheets.deliveryId`.
- `update_drawing_delivery` — correct a delivery's label, kind, or issue date after the fact; never
  renames or mutates the uploaded files themselves.

**Upload** (register a new delivery)
- `request_file_upload` — get a signed upload URL for a drawing PDF you want to register.
- `register_file` — after uploading, register the file to the project so it becomes available
  to `list_files` / `render_page` / `get_page_text` and the `drawing-upload` pipeline.

**Write**
- `propose` — append one `proposed` claim (`subject`, `predicate`, `value`,
  `sourceInstrument`, optional `evidence`/`ambiguityClass`). Stamped as you; never governs
  until a human promotes it.
- `propose_batch` — append an array of `proposed` claims in one atomic call (`projectId` +
  `claims` array). Atomic: a bad entry rejects the whole batch and names the index. Prefer
  this over repeated `propose` calls for bulk deposits (e.g. upload or scope deposit). Each
  call accepts up to 500 claims; stay at ≤50 per batch so each read is faithful and
  count-verifiable.

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
