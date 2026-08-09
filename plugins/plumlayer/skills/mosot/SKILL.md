---
name: mosot
description: Work with a Plumlayer MOSOT — the cloud source of truth for a construction project's claims. Use when the user wants to read, search, review, or propose claims on their Plumlayer projects (sheet/set grid, ambiguities, RFI candidates, scope/door takeoffs), or asks "what's in my MOSOT / project". Explains the verb surface and the trust model: what an agent writes governs provisionally as agent-stated, carrying its author, timestamp, and evidence.
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

## Trust: the trail is the mechanism
A claim you write takes effect immediately as provisional working truth, recorded as
agent-stated with your citation. There is no promotion step to wait for. What makes it
trustworthy is the trail: author, timestamp, and the evidence it came from, so cite every
claim (an ungrounded claim is a guess; say so instead of writing it).
- The server stamps the register from your identity, never from what you declare. An
  agent's judgment records as `agent-stated`, a reproducible machine transcription as
  `machine-read`, a value the deterministic layer confirmed as `tool-verified`, a person's
  own gesture as `human-stated`. This door can never record a claim as human-authored or
  tool-verified.
- A person's word outranks yours on the same slot. You supersede your own prior reads
  freely, but a write against something a human said lands as a visible contest, and their
  value keeps governing.
- Flag what you are unsure of. Self-flagged uncertainty is what reaches a person for
  judgment, and human sign-off still gates what leaves the building: an ITB or package
  send, an RFI, anything published outside, a bid. Nothing leaves unsigned; nothing enters
  untraced.
- The stored trust class on what you write still reads `proposed`. That is a compatibility
  field, not a gate, and does not mean the claim is waiting on anyone.

## Words (operator-facing language)

Everything above is machinery vocabulary for working the verbs — it is never the language the user
reads. Speak estimator words in everything you say to them: **project record, entry, sheet, set,
scale, scope item, bid response, flagged item, trail**. Say "recorded 14 entries to the project,
each citing the sheet I read it from", "2 flagged for your judgment". Prefer "project" over
"MOSOT" unless the user uses the word. Plain prose, no em dashes, no bolded emphasis words.

Never say to the user: *claim, deposit, predicate, subject, proposed, governing, trust class,
supersede, ledger, grounding, residue*. Those are machinery. If a concept has to surface, translate it: a
superseded value is "replaced my earlier read"; a contest refusal is "a person set that one, so I
left it alone and noted it"; the trust class is simply who recorded it and when.

The kill list also covers these, each with its estimator translation:

- **promote / promotion** ("promote it on plumlayer.com") → "set it right on the site" / "yours to
  correct on the site" / "I flagged it for you to fix". Never "promote".
- **QA / QA-findings / set-QA** → "set checks" / "things I found to fix in the set".
- **sheetType / typed / untyped** → "sheet type" / "what kind of sheet each is" / "I left 15 for a
  closer look".
- **reconcile / reconciliation** → "cross-checking the drawing list against the actual sheets".
- **indexDeclaresButAbsent** and similar raw field names → "sheets the index lists that aren't in
  the set" (and the inverse, for the field naming the reverse gap).
- Any raw verb name, predicate name, or field name that would otherwise appear in operator narration
  → translate it to plain words before it reaches the user; never let a JSON key or MCP verb stand in
  for a sentence.

Never tell the user something is "pending review" or "awaiting approval". What you write is the
project's working record now, carrying your name, the time, and your citations; anything a person
changes wins.

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
- `propose` — append one claim (`subject`, `predicate`, `value`, `sourceInstrument`,
  optional `evidence`/`ambiguityClass`). Stamped as you, and it takes effect immediately as
  provisional working truth recorded as agent-stated.
- `propose_batch` — append an array of claims in one atomic call (`projectId` + `claims`
  array). Atomic: a bad entry rejects the whole batch and names the index. Prefer this over
  repeated `propose` calls for bulk deposits (e.g. upload or scope deposit). Each call
  accepts up to 500 claims; stay at ≤50 per batch so each read is faithful and
  count-verifiable.

Both write doors refuse the takeoff-domain predicates (`hasTakeoffCount`, `hasTakeoffRollup`,
`hasScale`, `hasTakeoffLength`, `hasTakeoffArea`, `hasTakeoffCountMark`, `hasTakeoffCondition`,
`instanceVerdict`, `hasHumanInstance`). Those belong to the takeoff door on plumlayer.com, the
only one that enforces their value shapes, subject identity, and unit immutability. Do not try
to write a measurement, a count, or a sheet scale through `propose`.

### How to shape a citation

Your citation becomes a clickable chip on the scope surface, parsed deterministically from
`evidence`. An entry the parser cannot read renders **nothing**, silently and with no error:
an unreadable reference is treated as no citation rather than as a fake one. So a claim can
land perfectly well and still show no source, purely from a malformed `evidence` entry. Shape
it like this:

```json
"evidence": [
  {
    "source": "A-746 — millwork elevation at leasing desk",
    "locator": {
      "pageInPdf": 165,
      "frame": "page-points-rendered",
      "bboxPts": [1180, 640, 1890, 1120]
    }
  }
]
```

- `evidence` may be one entry or an array of them; both are read. What fails is an **empty**
  `{}`, which carries no source and so cites nothing.
- `source` **must lead with the document reference** — a sheet number (`A-746`, `S-201.1`) or
  a spec section (`09 21 16`). That leading reference is what becomes the chip. An internal id
  like `bidPackage:proj-…`, or a prose sentence, is not a document reference and renders
  nothing by design.
- After the reference, add ` — ` and what you read there. A bare reference on its own is
  accepted and renders, so never pad it with a filler phrase just to satisfy the format; write
  the suffix when you have something real to say about what you saw, since it becomes the
  chip's tooltip.
- `locator.bboxPts` with `frame: "page-points-rendered"` is what makes the chip land on the
  **region** you actually read instead of the top of the sheet. Supply them whenever you know
  where on the page you looked. Omit them and the chip still works, just sheet-level.
- A `citedRegion` claim needs its **own** evidence entry. Putting the sheet and box only in
  the claim's `value` records the region but cites nothing, so no chip appears for it.

Cite the sheet you genuinely read. A citation is a document reference, never a warrant that
the tokens there mean what you concluded. That judgment is yours, recorded as yours.

## Typical flows
- **"What's in my project / MOSOT?"** → `list_projects` → pick one → `set_grid` for the
  drawing set, `ambiguities` for open issues, `rfi_candidates` for drafted RFIs; `search`
  to inspect specific subjects/claims.
- **"Scope something"** → read the relevant sheets/claims, judge, then `propose`
  grounded claims (`sourceInstrument` = where it came from, plus `evidence`). Tell the user
  what you wrote and that it reads as your judgment with your citations behind it. Drawn
  measurements and sheet scale are not this door's to write (see Write, above).
- **"Find conflicts / RFIs"** → `ambiguities` + `rfi_candidates`; where you spot a real
  conflict, `propose` an ambiguity-flagged claim (`ambiguityClass`), cited.

## Discipline
- Be honest about your own claims: they govern provisionally as your reading, not as a
  person's word, and a human correction outranks them.
- Always cite, and shape the citation so it actually renders (see "How to shape a citation").
  Separate what's grounded from what's inferred.
- One project = one MOSOT; always act within the correct `projectId`.
