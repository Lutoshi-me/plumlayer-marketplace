---
name: project-record
description: >
  Read, search, review, or add entries to a Plumlayer project record: the drawing set, flagged
  items, RFI candidates, scope items, and takeoff data. Use when the user asks "what's in my
  project" or says "/project-record". Drives the read verbs (set_grid, ambiguities,
  rfi_candidates, search, list_scope_items) and write verbs (record, record_batch,
  record_batch_file). Does not upload drawings (drawing-upload), run the scope engine
  (scope-run), or place takeoff measurements (takeoff).
---

# Working a Plumlayer project record

## Talk to your user like an estimator

Verbs, claims, and trust classes are machinery for you, never words the user reads. This covers
everything the user sees, including your closing report: a report template is user-facing text.

Speak estimator words: project record, entry, sheet, set, scale, scope item, bid response, flagged
item, trail.

Never say to the user: claim, predicate, subject, governing, trust class,
supersede, promote, reconcile, reconciliation, ledger, grounding, residue, idempotency, QA,
sheetType, or any raw verb, field, or parameter name.

Translate instead: a value you replaced is "I updated my earlier read"; a machine misread you caught
is "the automatic scan grabbed the wrong text, so I read the sheet and set it right"; cross-checking
the index is "checking the drawing list against the actual sheets"; what you could not settle is
"what is still open". Plain prose, no em dashes, no bolded emphasis words.

The full list, with translations, is in the project-record skill's Words section.

**The project record** is the cloud, claim-based model of a
construction project's *current governing truth*. Each Plumlayer **project has one project record**.
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

## Words (user-facing language)

<!-- user-facing -->
Everything above is machinery vocabulary for working the verbs, never the language the user reads.
This rule covers everything the user sees, including your closing report and any other report
template: a report template is user-facing text, not machinery, even when it summarizes
machinery-driven work. Speak estimator words in everything you say to them: **project record,
entry, sheet, set, scale, scope item, bid response, flagged item, trail**. Say "recorded 14 entries
to the project, each citing the sheet I read it from", "2 flagged for your judgment". Prefer
"project" or "the project record" in plain words the user already uses.

Never say to the user: *claim, predicate, subject, governing, trust class,
supersede, promote, reconcile, reconciliation, ledger, grounding, residue, idempotency, QA,
sheetType*. Those are machinery. If a concept has to surface, translate it: a superseded value is
"replaced my earlier read"; a contest refusal is "a person set that one, so I left it alone and
noted it"; the trust class is simply who recorded it and when.

The kill list also covers these, each with its estimator translation:

- **promote / promotion** ("promote it on plumlayer.com") → "set it right on the site" / "yours to
  correct on the site" / "I flagged it for you to fix". Never "promote".
- **QA / QA-findings / set-QA** → "set checks" / "things I found to fix in the set".
- **sheetType / typed / untyped** → "sheet type" / "what kind of sheet each is" / "I left 15 for a
  closer look".
- **reconcile / reconciliation** → "cross-checking the drawing list against the actual sheets".
- **indexDeclaresButAbsent** and similar raw field names → "sheets the index lists that aren't in
  the set" (and the inverse, for the field naming the reverse gap).
- Any raw verb name, predicate name, or field name that would otherwise appear in user narration
  → translate it to plain words before it reaches the user; never let a JSON key or MCP verb stand in
  for a sentence.

Never tell the user something is "pending review" or "awaiting approval". What you write is the
project's working record now, carrying your name, the time, and your citations; anything a person
changes wins.
<!-- /user-facing -->

## The verbs
**Identity / discovery**
- `whoami`: confirm which account you're acting as.
- `list_projects`: the user's projects (each has a project record). Confirm the right one before acting.
- `get_project`: one project's details.
- `create_project`: create a new project (= a new project record). Supply `name` (required) and optional
  `description`; returns the new `projectId`. Use before any write or upload on a new bid/pursuit.

**Read**
- `set_grid`: the sheet inventory (the drawing set as a grid: discipline, sheet number,
  governing issue, open-ambiguity count per sheet).
- `ambiguities`: the open-conflict / review ledger, severity-sorted (legitimate-RFI first).
- `rfi_candidates`: drafted RFI candidates with citations.
- `search`: the raw claim ledger (ANY trust class, including `recorded`). Filter by
  subject / predicate / trustClass / text; paginated. Use this to see what's actually been
  asserted, including your own recorded claims.
- `list_scope_items`: the live scope list (name, category, description, notes, quantity per item).
  Use this to see what's already been captured before creating or enriching a scope item.

**Drawing recognition** (cloud PDF: these work against files already uploaded to the project)
- `list_files`: list the drawing files registered to a project.
- `register_pages`: once per project, register renderable page rows for every uploaded PDF (not
  claims, just viewable pages) so uploaded files are readable even before recognition runs.
- `recognize_sheets`: start the async deterministic bulk sheet-number recognition pass over one
  uploaded PDF. Returns `{jobId, status}` immediately; poll `recognize_sheets_status` rather than
  waiting inline. Recognized sheet claims record server-side as `recorded` on success; never
  `record_batch` them yourself.
- `recognize_sheets_status`: poll a `recognize_sheets` job. Returns run counts (`report`), the
  server-side write summary (`written`), and the residue tail (`residue`) for you to read and
  judge; it never carries the recognized claims themselves.
- `render_page`: render a single page of a registered PDF to an image so you can read it.
- `get_page_text`: extract the text layer from a registered PDF page (deterministic; use
  alongside `render_page`: text for tokens, render for layout/meaning).

**Delivery** (group uploaded files into a source package)
- `list_drawing_deliveries`: list a project's registered drawing deliveries (baseline sets and
  revision packages like bulletins/addenda).
- `create_drawing_delivery`: register one delivery (e.g. "2025-12-15 Conformed Set" as
  `deliveryKind: "baseline"`, or "2026-02-09 Bulletin 01" as `"revision"`). Project metadata, not a
  governing claim. Attach files with `register_file.deliveryId`, then recognize with
  `recognize_sheets.deliveryId`.
- `update_drawing_delivery`: correct a delivery's label, kind, or issue date after the fact; never
  renames or mutates the uploaded files themselves.

**Upload** (register a new delivery)
- `request_file_upload`: get a signed upload URL for a drawing PDF you want to register.
- `register_file`: after uploading, register the file to the project so it becomes available
  to `list_files` / `render_page` / `get_page_text` and the `drawing-upload` pipeline.

**Write**
- `record`: append one claim (`subject`, `predicate`, `value`, `sourceInstrument`,
  optional `evidence`/`ambiguityClass`/`supersedesId`). Stamped as you, and it takes effect
  immediately as provisional working truth recorded as agent-stated. `supersedesId` is the
  correction edge: see "Correcting a machine misread" below.
- `record_batch`: append an array of claims in one atomic call (`projectId` + `claims`
  array). Atomic: a bad entry rejects the whole batch and names the index. Prefer this over
  repeated `record` calls for bulk writes (e.g. upload or scope writes). Each call
  accepts up to 500 claims; stay at ≤50 per batch so each read is faithful and
  count-verifiable.
- `record_batch_file`: like `record_batch`, but for a run whose claims are too large to send
  inline: upload a JSONL file of claims, then write from it in one atomic call. Use this instead
  of `record_batch` for large runs (e.g. a scope-run wave recording hundreds of items).

Both write doors refuse the takeoff-domain predicates (`hasTakeoffCount`, `hasTakeoffRollup`,
`hasScale`, `hasTakeoffLength`, `hasTakeoffArea`, `hasTakeoffCountMark`, `hasTakeoffCondition`,
`instanceVerdict`, `hasHumanInstance`). Those belong to the takeoff door on plumlayer.com, the
only one that enforces their value shapes, subject identity, and unit immutability. Do not try
to write a measurement, a count, or a sheet scale through `record`.

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
- `source` **must lead with the document reference**: a sheet number (`A-746`, `S-201.1`) or
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

### Correcting a machine misread (a mis-bound title or discipline)

The deterministic recognizer grounds the tokens it reads, but *which* cell fills a semantic slot
(`hasTitle`, `discipline`) is its fallible positional guess, recorded as `machine-read`. When you read
a sheet and can see it grabbed the wrong cell (a boxed drawing note recorded as the title, say),
correct it with a supersession **edge**, not a bare competing claim:

1. `search(projectId, subject: "sheet:<n>", predicate: "hasTitle")` (or `"discipline"`) → the live
   claim's `id`.
2. `record` (or a `record_batch` entry) with `supersedesId` set to that id, `value` = what you read,
   cited to the sheet you read it from.

The edge is what makes your read govern the grid: an agent edge onto a `machine-read` value is honored
regardless of its register. Only a person's word outranks you. A **bare** competing claim (no
`supersedesId`) does not win; it stays a candidate beneath the machine value, which is the
anti-hallucination anchor working as intended. So reserve the `ambiguityClass` flag for a reading you
genuinely cannot resolve, never as the way to fix a title you already read correctly (that is the
"go set it on the site" dead end).
<!-- user-facing -->
To the user this is plain: "the automatic scan grabbed the wrong
text on those sheets, so I read them and set them right."
<!-- /user-facing -->

## Typical flows
- **"What's in my project / project record?"** → `list_projects` → pick one → `set_grid` for the
  drawing set, `ambiguities` for open issues, `rfi_candidates` for drafted RFIs; `search`
  to inspect specific subjects/claims.
- **"Scope something"** → read the relevant sheets/claims, judge, then `record`
  grounded claims (`sourceInstrument` = where it came from, plus `evidence`).
<!-- user-facing -->
Tell the user
  what you wrote and that it reads as your judgment with your citations behind it.
<!-- /user-facing -->
Drawn
  measurements and sheet scale are not this door's to write (see Write, above).
- **"Find conflicts / RFIs"** → `ambiguities` + `rfi_candidates`; where you spot genuine ambiguity
  you cannot resolve, `record` an ambiguity-flagged claim (`ambiguityClass`), cited. Where instead
  you can see the recognizer grabbed the wrong cell for a title or discipline, correct it with a
  supersession edge (see "Correcting a machine misread"), not a flag.

## Discipline
- Be honest about your own claims: they govern provisionally as your reading, not as a
  person's word, and a human correction outranks them.
- Always cite, and shape the citation so it actually renders (see "How to shape a citation").
  Separate what's grounded from what's inferred.
- One project = one project record; always act within the correct `projectId`.
