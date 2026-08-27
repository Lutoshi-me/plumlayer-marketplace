---
name: project-record
description: >
  Read, search, review, or add entries to a Plumlayer project record: the drawing set, open
  questions, RFI candidates, scope items, and takeoff data. Use when the user asks "what's in my
  project" or says "/project-record". Drives the read verbs (set_grid, rfi_candidates, search,
  list_scope_items, list_questions) and write verbs (record, record_batch, record_batch_file,
  ask_question, close_question, reopen_question).
  Does not upload drawings (drawing-upload), build the scope list (scope-run), or place takeoff
  measurements (takeoff).
---

# Working a Plumlayer project record

**The project record** is the cloud, entry-based model of a
construction project's *current governing truth*. Each Plumlayer **project has one project record**.
You interact with it through the `plumlayer` MCP tools (every tool is scoped to the
signed-in user's own projects).

## The atom: an entry
`subject — predicate — value`, backed by evidence and a record of who said it. Examples:
- `sheet:A-101 — title — "First Floor Plan"`
- `door:103 — count — 6`

## Trust: the trail is the mechanism
An entry you write takes effect immediately as provisional working truth, recorded as
agent-stated with your citation. There is no promotion step to wait for. What makes it
trustworthy is the trail: author, timestamp, and the evidence it came from, so cite every
entry (an ungrounded entry is a guess; say so instead of writing it).
- The server stamps the authorship from your identity, never from what you declare. An
  agent's judgment records as `agent-stated`, a reproducible machine transcription as
  `machine-read`, a value the deterministic layer confirmed as `tool-verified`, a person's
  own gesture as `human-stated`. This door can never record an entry as human-authored or
  tool-verified.
- A field holds the latest write, by anyone, with its trail. Supersede freely, naming what your
  entry replaces with `supersedesId`, whether it's your own prior read or something a person set;
  if you're not sure your read should stand over what's there, ask instead of overwriting it blind.
- Raise a Question, with a title and a citation, for what you are unsure of. That is what
  reaches a person for judgment, and human sign-off still gates what leaves the building: an
  ITB or package send, an RFI, anything published outside, a bid. Nothing leaves unsigned;
  nothing enters untraced.

## The verbs
**Identity / discovery**
- `whoami`: confirm which account you're acting as.
- `list_projects`: the user's projects (each has a project record). Confirm the right one before acting.
- `get_project`: one project's details.
- `create_project`: create a new project (= a new project record). Supply `name` (required) and optional
  `description`; returns the new `projectId`. Use before any write or upload on a new bid/pursuit.

**Read**
- `set_grid`: the sheet inventory (the drawing set as a grid: discipline, sheet number,
  governing issue, open-question count per sheet).
- `rfi_candidates`: drafted RFI candidates with citations.
- `search`: the raw entry ledger, every entry that's ever been written, not just what's
  currently governing. Filter by subject / predicate / text; paginated. Use
  this to see what's actually been asserted, including entries you wrote yourself.
- `list_scope_items`: the live scope list (name, category, description, notes, quantity per item),
  100 rows a page by default; `categoryCounts` tallies the whole list, so filter by `category` or
  `subjectPrefix` and page with `offset: nextOffset` while `truncated` is true. `full: true` adds
  each item's records. Use this to see what's already been captured before creating or updating a
  scope item.
- `list_questions`: every question on the project, open ones first, each with its wording, the
  places it cites, its replies oldest first, the trade it's homed to, and the trail of every
  close and reopen on it. Read this before you ask, so you don't raise one that's already open,
  and before you close one, so you close the right one.

**Drawing recognition** (cloud PDF: these work against files already uploaded to the project)
- `list_files`: list the drawing files registered to a project.
- `register_pages`: once per project, register renderable page rows for every uploaded PDF (not
  entries, just viewable pages) so uploaded files are readable even before recognition runs.
- `recognize_sheets`: start the async deterministic bulk sheet-number recognition pass over one
  uploaded PDF. Returns `{jobId, status}` immediately; poll `recognize_sheets_status` rather than
  waiting inline. Recognized sheet entries land in the record automatically on success; never
  `record_batch` them yourself.
- `recognize_sheets_status`: poll a `recognize_sheets` job. Returns run counts (`report`), the
  server-side write summary (`written`), and the tail of pages it could not name (`unnamedPages`) for
  you to read and judge; it never carries the recognized entries themselves.
- `render_page`: render a single page of a registered PDF to an image so you can read it.
- `get_page_text`: extract the text layer from a registered PDF page (deterministic; use
  alongside `render_page`: text for tokens, render for layout/meaning). Returns 1500 spans a
  call; page with `offset: nextOffset` while `truncated` is true, or pass `region` in PDF points
  to read one area.

**Delivery** (group uploaded files into a source package)
- `list_drawing_deliveries`: list a project's registered drawing deliveries (baseline sets and
  revision packages like bulletins/addenda).
- `create_drawing_delivery`: register one delivery (e.g. "2025-12-15 Conformed Set" as
  `deliveryKind: "baseline"`, or "2026-02-09 Bulletin 01" as `"revision"`). Project metadata, not a
  governing entry. Attach files with `register_file.deliveryId`, then recognize with
  `recognize_sheets.deliveryId`.
- `update_drawing_delivery`: correct a delivery's label, kind, or issue date after the fact; never
  renames or mutates the uploaded files themselves.

**Upload** (register a new delivery)
- `request_file_upload`: get a signed upload URL for a drawing PDF you want to register.
- `register_file`: after uploading, register the file to the project so it becomes available
  to `list_files` / `render_page` / `get_page_text` and the `drawing-upload` pipeline.

**Write**
- `record`: append one entry (`subject`, `predicate`, `value`, `sourceInstrument`, `evidence`,
  optional `supersedesId`). A scope item and a schedule definition must both be cited, on a create
  and on an update alike: their `evidence` has to name what you read, a sheet with the 1-based page
  you read it on, a file, or a spec section, and evidence that names none of the three is refused.
  Work no sheet states carries `sourceInstrument` `trade-convention:<trade>@<sha>` instead, and the
  two derived trade tags (`belongsToTrade`, `packageRole:<trade>`) need no citation. Stamped as you,
  and it takes effect immediately as provisional working truth recorded as agent-stated.
  `supersedesId` is the correction edge: see "Correcting a machine misread" below.
- `ask_question`: raise ONE open item a person has to answer or resolve, with a title and the
  citations it's about (a sheet, a spec section, or a record you read). This is how a
  disagreement between sources, or a reading you genuinely cannot resolve yourself, reaches a
  person's judgment. `supersedesId` revises your own prior wording. A Question is about the
  project, never about a Plumlayer failure. The drawings, the specs, the scope, who carries
  what, a conflict between sources, something missing, a project decision, or a value on the
  record you cannot resolve from what you read belongs in a Question; a job that failed or
  timed out, a verb that refused a write, a server limit, a retry decision, confusion about how
  to run a workflow, or a report that something now works belongs in the conversation and in
  the skill's own failure path, never here.
- `record_batch`: append an array of entries in one atomic call (`projectId` + `entries`
  array). Atomic: a bad entry rejects the whole batch and names the index. Prefer this over
  repeated `record` calls for bulk writes (e.g. upload or scope writes). Each call
  accepts up to 500 entries; stay at ≤50 per batch so each read is faithful and
  count-verifiable.
- `record_batch_file`: like `record_batch`, but for a run whose entries are too large to send
  inline: upload a JSONL file of entries, then write from it in one atomic call. Use this instead
  of `record_batch` for large runs (e.g. a scope-run pass recording hundreds of items).
- `retire_scope_item`: remove ONE scope item from the scope list (`projectId`, `subject`,
  `basis`, optional `reason`). Appends a retirement record; nothing is deleted and a later
  record can bring the item back. Same door a person uses; the trail names you. Call it only
  for a row the user asked removed and put their ask in `basis` in their words. A row you
  merely suspect is wrong is reported, not retired. The generic write doors refuse the
  `scopeItemRetraction` predicate; this verb and `restore_scope_item` are its only doors.
- `restore_scope_item`: put a retired scope item back (`projectId`, `subject`, `basis`,
  optional `reason`). Same door for a person and an agent, and it takes effect whoever retired
  the item, so if a person retired it, ask them before you put it back.
- `close_question`: close ONE question (`projectId`, `questionId`, optional `note`,
  `sourceInstrument`), when the user has told you it's settled. It stops showing as open and its
  pins come off the sheets; nothing is deleted, and the ask, every reply, and your close all stay
  in the question's trail with your name. Put their reason in `note` in their own words, or leave
  `note` off rather than writing a reason nobody gave. A question you merely think looks answered
  is reported or replied to, not closed. Refused if the question is already closed.
- `reopen_question`: put a closed question back (`projectId`, `questionId`, optional `note`,
  `sourceInstrument`), when the user says it was closed too early or has come up again. The
  earlier close stays in the trail with the name of whoever made it. Refused if the question
  isn't closed. The generic write doors refuse the `questionClosed` predicate; these two verbs
  and their door on plumlayer.com are the only way to settle or unsettle a question.

Both write doors refuse the takeoff-domain predicates (`hasTakeoffCount`, `hasTakeoffRollup`,
`hasScale`, `hasTakeoffLength`, `hasTakeoffArea`, `hasTakeoffCountMark`, `hasTakeoffCondition`,
`instanceVerdict`, `hasHumanInstance`). Those belong to the takeoff door on plumlayer.com, the
only one that enforces their value shapes, subject identity, and unit immutability. Do not try
to write a measurement, a count, or a sheet scale through `record`.

### How to shape a citation

Your citation becomes a clickable chip on the scope surface, parsed deterministically from
`evidence`. An entry the parser cannot read renders **nothing**, silently and with no error:
an unreadable reference is treated as no citation rather than as a fake one. So an entry can
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
  `{}`: it carries no source, so on a scope item or a definition the record refuses it outright,
  and on any other entry it cites nothing.
- `source` **must lead with the document reference**: a sheet number (`A-746`, `S-201.1`) or
  a spec section (`09 21 16`). That leading reference is what becomes the chip. An internal id
  like `bidPackage:proj-…`, or a prose sentence, is not a document reference and renders
  nothing by design.
- After the reference, add ` — ` and what you read there. A bare reference on its own is
  accepted and renders, so never pad it with a filler phrase just to satisfy the format; write
  the suffix when you have something real to say about what you saw, since it becomes the
  chip's tooltip.
- `locator.pageInPdf` is required wherever the reference is a sheet: the 1-based page you
  actually read it on. A sheet named with no page is refused on a scope item and on a definition,
  so there is no pageless chip to fall back to.
- `locator.bboxPts` with `frame: "page-points-rendered"` is what makes the chip land on the
  **region** you actually read instead of the top of the sheet. Supply them whenever you know
  where on the page you looked. Omit them and the chip still works, at page level.
- A `citedRegion` entry needs its **own** item in `evidence`. Putting the sheet and box only in
  the entry's `value` records the region but cites nothing, so no chip appears for it.

Cite the sheet you genuinely read. A citation is a document reference, never a warrant that
the tokens there mean what you concluded. That judgment is yours, recorded as yours.

### Correcting a machine misread (a mis-bound title or discipline)

The deterministic recognizer grounds the tokens it reads, but *which* cell fills a semantic slot
(`hasTitle`, `discipline`) is its fallible positional guess, recorded as `machine-read`. When you read
a sheet and can see it grabbed the wrong cell (a boxed drawing note recorded as the title, say),
correct it with a supersession **edge**, not a bare competing entry:

1. `search(projectId, subject: "sheet:<n>", predicate: "hasTitle")` (or `"discipline"`) → the live
   entry's `id`.
2. `record` (or a `record_batch` entry) with `supersedesId` set to that id, `value` = what you read,
   cited to the sheet you read it from.

The edge is what makes your read govern the grid: an agent edge onto a `machine-read` value is honored
regardless of who or what originally produced it, as long as it names what it replaces with
`supersedesId`. If a person already set the value and you think it's wrong, ask them rather than
overwrite it. A **bare** competing entry (no `supersedesId`) does not win; it stays a candidate
beneath the machine value, which is the anti-hallucination anchor working as intended. So reserve `ask_question` for a reading
you genuinely cannot resolve, never as the way to fix a title you already read correctly (that is
the "go set it on the site" dead end).
<!-- user-facing -->
To the user this is plain: "the automatic scan grabbed the wrong
text on those sheets, so I read them and set them right."
<!-- /user-facing -->

## Typical flows
- **"What's in my project / project record?"** → `list_projects` → pick one → `set_grid` for the
  drawing set, `list_questions` for the open items, `rfi_candidates` for drafted RFIs; `search`
  to inspect specific subjects/entries.
- **"Scope something"** → read the relevant sheets/entries, judge, then `record`
  grounded entries (`sourceInstrument` = where it came from, plus `evidence`).
<!-- user-facing -->
Tell the user
  what you wrote and that it reads as your judgment with your citations behind it.
<!-- /user-facing -->
Drawn
  measurements and sheet scale are not this door's to write (see Write, above).
- **"Find conflicts / RFIs"** → `list_questions` for the open items, `rfi_candidates` for drafted
  RFIs; where you spot a disagreement between sources, or something you genuinely can't resolve,
  `ask_question` with a title and the citations it's about, after checking `list_questions`, so
  you reply to an open one covering the same ask rather than raising it twice. Where instead you can see the
  recognizer grabbed the wrong cell for a title or discipline, correct it with a supersession
  edge (see "Correcting a machine misread"), not a Question.

## Discipline
- A Question is about the project, never about a Plumlayer failure; a failed job, a refused
  write, or any other tool problem is reported in the conversation, not raised here.
- Question text is plain estimator words, per docs/plugin-text-style.md.
- Be honest about your own entries: they govern provisionally as your reading, not as a
  person's own entry, and a later correction from a person supersedes them the same way any
  write does.
- Always cite, and shape the citation so it actually renders (see "How to shape a citation").
  Separate what's grounded from what's inferred.
- One project = one project record; always act within the correct `projectId`.
