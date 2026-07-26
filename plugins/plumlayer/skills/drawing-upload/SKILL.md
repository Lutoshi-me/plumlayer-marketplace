---
name: drawing-upload
description: >
  Upload a construction drawing delivery in ANY packaging and turn it into cited sheet claims in the
  project's Plumlayer MOSOT — no manual conforming, no local CSV intermediate. Use
  whenever the user hands over a new drawing set, bulletin, addendum, ASI, permit/CD/conformed set,
  or any pile of drawing PDFs and wants it read, registered, indexed, or inventoried. Trigger on
  "we got a new set for <project>", "upload this set", "register the drawings", "drawing index",
  "drawing list", "sheet schedule", "sheet inventory", "list every sheet", "what's in this drawing
  set", "index this bulletin", "franken set / current set", "/drawing-upload" — and equally when
  the set is ALREADY uploaded to the project with nothing local: "read the uploaded set", "recognize
  the files already in <project>", "re-recognize the set". Drives project
  selection, delivery registration, cloud upload, bulk deterministic sheet-number recognition, agent
  residue read, sheet-type classification, and claim deposit over the hosted Plumlayer MCP verb
  surface. The primary verbs are `recognize_sheets` / `recognize_sheets_status`; older servers may
  still expose these as deprecated `ground_sheets` / `ground_sheets_status` aliases. The agent reads
  and judges; deterministic tooling grounds; nothing enters untraced. Supersedes the retired
  drawing-index / drawing-index-bulletin / drawing-index-merge skills (the export skills
  drawing-set-assemble / drawing-index-publish survive as on-demand projections off the cloud
  claims).
---

# Drawing Upload — the foundation pass, agent-driven, cloud-first

Take whatever the architect actually sent, in whatever shape, and turn it into the one canonical,
recognized set of **cited sheet claims** in the project's MOSOT. This is **Stage 0**: the first
thing that touches a delivery, before anything is split by discipline, routed, or deep-read.

Doctrine binds every stage: **agents read and judge; deterministic tooling grounds; nothing enters
untraced.** Every claim in this pipeline takes effect as soon as it lands, carrying who wrote it and
what they read from: the recognition pass records what it confirmed off the page, and what you judge
yourself records as your own reading, cited to the page you read it on. You are the reader; the MCP
recognition verbs (`recognize_sheets`, `recognize_sheets_status`, `render_page`, `get_page_text`) are
the anti-hallucination anchor, not the inference engine. There is no local pipeline and no
server-side autonomous *reader* — the server runs the deterministic bulk pass and deposits its own
output, but you still drive every job, judge every residue page, classify every sheet's type, and
author every claim that isn't the deterministic pass's own grounded output.

Design lineage: `agent-driven-ingestion.md` (who runs the read and where — the 2026-06-28 cloud-first
decision this skill implements) and `drawing-set-intake-design.md` (what a good read produces, the
packaging taxonomy). Examples in this file are generic; never put a real client or project name here.

## Narration to the user

Never let the words "grounding", "ingestion", "the ledger", or "residue pass" reach the user — a
real transcript (South Shore, 2026-07-15) showed an agent narrating all four and confusing the user
about what was actually happening. Say instead:

- "uploading" (steps 3–4)
- "recognizing sheet numbers" (step 5, while a job is running)
- "N sheets recognized" (step 5, on job success)
- "M pages need review" (step 6/6b residue and untyped sheets — never "residue pass")

## What this is, and the boundary

`drawing-upload` does exactly one thing: take a drawing delivery and register every sheet in it as
cited claims in the project's MOSOT. The canonical form is claims + provenance over the
untouched original delivery — discipline organization, by-discipline PDFs, page labels, and a
drawing-index CSV are all **projections** of that form, rendered on demand by other skills, never the
foundation. So this skill does **not**: physically split files by discipline (discipline is derived
per sheet, never from a filename); produce a CSV (the deliverable is claims in the MOSOT — export
skills `drawing-set-assemble` / `drawing-index-publish` render artifacts from the cloud claims on
request); scope, take off, or comprehend the sheets (guarded by PLU-323 / owned by PLU-274); or create
the project (`project-create`).

**Retired:** `drawing-index`, `drawing-index-bulletin`, `drawing-index-merge` — they organized before
reading (hand-split into discipline PDFs, then parsed a master list), which commits a discipline guess
before any read confirms it and depends on a master list that failed on 3 of 4 characterized projects.
This skill reads first; a master list is corroboration only, never the bootstrap. The vendored
`scope-harness/` tree in this plugin is no longer used by this skill (removal is a separate PLU-274
phase) — do not resolve `$PLUGIN` or run anything under it; every step below is an MCP tool call.

## 1 · Pick the project

Call `list_projects` and confirm with the user which MOSOT this delivery belongs to (a project is one
MOSOT) — get its `projectId`. If there is no project yet, hand off to `project-create` first; this
skill does not create projects. Confirm you also know the **issue label** for this delivery (e.g. a
generic "2025-12-22 CD Set" or "Bulletin 01") — ask the user, or plan to read it off the cover sheet
during recognition. It is load-bearing for supersession later.

## 1b · Cloud-resident entry (files already in the project, nothing local)

Not every run starts from a local delivery. When the user points you at a project whose set is
already in cloud storage — uploaded in a prior session, or they ask you to "read the uploaded set"
or "(re)recognize" it — there is nothing to recognize locally and nothing to upload. Detect it before
asking for paths: if the user hands you no local files, call `list_files(projectId)`; if the
drawings are there, run this branch. When it's genuinely ambiguous (some files uploaded, the user
also holding local files), ask — never assume which delivery the user means.

The branch substitutes the local-only stages and reuses everything else unchanged:

- **Enumerate instead of recognize packaging (replaces step 2).** `list_files(projectId)` is your
  source list — each row carries `fileId`, `filename`, `sizeBytes`, and its `deliveryId` (or null).
  Apply step 2's judgment to that list: which files are drawings and which aren't. When a filename
  doesn't decide, sample a page or two with `render_page` / `get_page_text` — on this branch even the
  file-selection sampling is cloud-side, since there are no local bytes. Emit the same packaging
  report: which files you will recognize, which you're excluding and why.
- **Delivery attribution instead of registration (replaces steps 3–4).** Read each drawing file's
  `deliveryId` from `list_files`, cross-referenced against `list_drawing_deliveries(projectId)`:
  - **Attributed** — the file already carries its delivery. Reuse it; never register a duplicate
    delivery for the same issue.
  - **Unattributed** (`deliveryId: null`) — surface the gap to the user; never invent attribution.
    Establish which issue the files belong to (ask, or read it off a cover sheet via
    `render_page`), register the delivery per step 3 if it doesn't exist yet, and pass its id as
    `recognize_sheets.deliveryId` in step 5 — that is the supported attach mechanism for an
    already-registered file (a `register_file` retry returns the existing row; it does not
    re-attribute). Chronology still comes from the documents: `issuedOn` off a cover sheet or
    revision table, never upload time.
  - **Mixed attribution** across files is legitimate (files from different deliveries live in one
    project) — recognize each file against its own delivery; what you must not do is guess a delivery
    for the unattributed ones or pass a `deliveryId` that disagrees with a file's registered one
    (the server refuses the mismatch).

From here the pipeline is identical: step 5 (`register_pages` once, then `recognize_sheets` per file —
pass `deliveryId` explicitly for any file whose registration doesn't carry it), step 6 (residue
read), step 6b (sheet-type classification), step 7 (residue + type deposit, verify). Every gate
applies unchanged.

**Re-recognize semantics (the honest limits).** Re-running `recognize_sheets` on a file+delivery is
always safe: a `stale` or `failed` job restarts; a `succeeded` one returns the existing job and the
deposit stays idempotent. That also means this branch cannot force a fresh read of a file+delivery
that already succeeded — a corrected re-read after a bad run needs the force-re-recognize path
(PLU-338, not built). Say so plainly rather than re-running and implying new output.

## 2 · Recognize the delivery's packaging

Steps 2–4 are the local-delivery path; a set already in cloud storage enters at 1b above and skips
them. A delivery arrives in one of four packaging classes — recognize the class before uploading
anything:

| Class | What it looks like | How you read it |
|---|---|---|
| **Combined PDF** | the whole set in one file, often mixed with specs/schedules/geotech/emails | the one drawing PDF is the source; exclude the rest |
| **By-discipline folder** | one PDF per discipline (`...Architectural.pdf`, `...Structural.pdf`) | every PDF is a source; never trust the filename for discipline — derive it per sheet |
| **Sequence splits** | arbitrary `Sequence 1 / Sequence 2` PDFs ignoring discipline | every PDF is a source; sheets carry their own discipline prefix |
| **Mixed bag** | drawings + specs + reports as separate files, no naming convention | judge each file to find which are drawings |

Filenames and folder shape *orient* you; they never *decide*. A drawing sheet has sparse text and a
sheet-number token in the bottom-right title block (`A-101`, `S-201`); a spec/geotech/narrative page has
dense body text and no corner title block.

**Dual-source repackaging:** when a delivery contains both a combined PDF and a full set of per-sheet
PDFs, check page totals first. If the per-sheet PDFs' combined page count equals the combined PDF's page
count, that's duplicate repackaging of the same set, not two sources — **prefer the single combined file
and don't recognize both**; recognizing both wastes a full pass and risks depositing the same sheets
twice under different `fileId`s. Only treat it as genuinely ambiguous when the totals disagree or
there's no clean 1:1 correspondence.

For any other genuinely ambiguous packaging (a mixed bag, or a dual-source case the page-total check
didn't resolve), use the **Read tool** directly on a few local candidate pages of each file to judge
title-block grammar vs spec-prose and pick the authoritative source. This local sampling is
**file-selection judgment only** — it decides which local files you upload next; it never grounds a
claim, and no claim's evidence ever cites a local read (every claim's evidence comes from the cloud
recognition tools in steps 5–6).

Emit a short packaging report before uploading: the class, which file(s) are the drawings and why,
page counts, which files you are excluding (specs, geotech, emails) and why, and the picked source if
there was a dual-source quirk.

## 3 · Register the delivery

Call `list_drawing_deliveries(projectId)` first — if a delivery with this issue label already exists,
reuse it rather than registering a duplicate. Otherwise call `create_drawing_delivery`:

- `deliveryKind: "baseline"` for a full/conformed re-issue; `"revision"` for a bulletin/addendum/ASI
  (changed sheets only).
- `label` — the human issue label from step 1.
- `issuedOn` (`YYYY-MM-DD`) and `sequence` — read these off the documents themselves (a cover sheet, a
  bulletin header). **Never substitute upload time** — chronology drives supersession resolution.
  **When issue-date signals disagree** (the filename says one date, a cover sheet or transmittal says
  another), the **drawing set's own revision table is authoritative** for `issuedOn` — it's the
  architect's own record of the issue, ahead of a filename someone typed or a transmittal cover letter.
  Note the disagreement in the packaging report rather than silently picking one.

Every file you upload in step 4 attaches to this one `deliveryId`.

## 4 · Upload bytes

For each drawing PDF you identified in step 2:

1. `request_file_upload(projectId, filename)` → `{fileId, path, bucket, token, signedUrl}`. The server
   mints `fileId` and the storage path; you never supply either.
2. PUT the raw file bytes to `signedUrl` with a `Content-Type` header (the bytes never pass through a
   tool call):
   ```bash
   curl -X PUT "$SIGNED_URL" -H "Content-Type: application/pdf" --data-binary @"$LOCAL_PDF_PATH"
   ```
3. `register_file(projectId, fileId, filename, contentType, deliveryId)` — always pass `deliveryId` so
   chronology comes from the delivery, not upload order. Idempotent: a retried call for the same
   `fileId` returns the existing row. Rejects `not_found` (PUT didn't land), `empty`, or `oversize`
   (2 GB ceiling per file) — if any of these fire, stop and report rather than retrying blindly.

Repeat for every file in the delivery; each one registers to the **same** `deliveryId`. No local run
folder, no manifest file — the project files list (`list_files`) is the record.

## 5 · Recognize sheets (async — start, then poll)

Call `register_pages(projectId)` **once** for the project — it registers viewable page rows for every
uploaded PDF (not claims, just renderable pages) and only needs to run once per project, not per file.

Then, **once per file**, call `recognize_sheets(projectId, fileId, deliveryId)` to start the
deterministic server-side pass over that PDF. It returns immediately — it does not scan inline — with
`{jobId, status: "queued"|"succeeded", deliveryId, alreadyActive?}`. `alreadyActive: true` means a job
for this file+delivery is already in flight or done; poll the returned `jobId` rather than starting a
second one. Run `recognize_sheets` once per file, never twice for the same file+delivery.

Poll `recognize_sheets_status(projectId, jobId)` every ~3-5s until `state` settles:

- `queued` / `running` — still working; poll again in a few seconds.
- `stale` — no progress for 15 minutes; re-call `recognize_sheets` on the same file/delivery to
  self-heal (it restarts the job).
- `failed` — read `error`, stop, and report it; don't retry blindly.
- `succeeded` — the recognized sheet claims (`appearsOnPage`, `hasTitle`, `locatedAt`, `discipline`,
  `partOfIssue`) are **already deposited server-side.** This result never carries
  those claims and you never `propose_batch` them yourself — that would double-write every sheet. Report
  the run-level counts from `report`: `pagesScanned`, `sheetsGrounded`, `highConfCount`, `flaggedCount`,
  `extractionWarningCount`, `calibrated`, `capHit`. Never assume "N pages scanned = N sheets recognized" —
  state both numbers. `confidence` on individual claims (visible later via `search`/`set_grid`) is
  triage/review-priority metadata only, never a trust tier.

For a multi-file delivery, start and poll a separate job per file; there is no merge step and no
`SET_TAG` — each file's recognized claims land under the shared `deliveryId` as soon as its own job
succeeds, with no pooling step required.

## 6 · Residue read

A `succeeded` `recognize_sheets_status` result carries `residue`: the tail where the deterministic
pass is least sure (low confidence, no sheet number found, or a degraded text layer). Read and judge
every residue row yourself:

- Use `residue[].pageNum` or `pageInPdf` (both 1-based) with `render_page` and `get_page_text` — never
  the legacy 0-based `residue[].page` field. `render_page` returns the PNG inline (pass a normalized
  `region` like `{x0:0.74, y0:0.80, x1:1.0, y1:1.0}` to zoom the title-block corner at higher DPI);
  `get_page_text` returns exact spans with PDF-point bboxes, and `hasTextLayer:false` is the honest
  image-only-page signal (no vector text to read).
- Judge the sheet number, title, and discipline from what you actually see. When you override a reader
  pick (it grabbed a tag, not the sheet number), author your corrected claim and tag it with
  `ambiguityClass` so both readings surface for human review in `ambiguities` — never silently pick.
- **Image-only / scanned pages**: flag them honestly. Mint the page as its own subject —
  `page:<fileId>:<pageInPdf>` — never `subject: null`, and never add an OCR dependency (deferred,
  PLU-186). Report the flagged page list; an honest "could not recognize these N pages" beats a guess.

For every residue subject you *do* resolve, author the **full bundle** of claims, mirroring the shape the
server deposits for the pages the deterministic pass already recognized (matching predicate and value
shapes keeps every sheet's claim set uniform regardless of which stage grounded it):

```json
{"subject": "sheet:S-501", "predicate": "appearsOnPage", "value": 412,
 "sourceInstrument": "drawing-delivery:<deliveryId>", "versionScope": "<issue label>",
 "evidence": {"source": "<fileId>/page/412", "method": "agent-vision-read", "snippet": "S-501",
   "locator": {"frame": "pdf-points", "bboxPts": [2890.1, 2080.4, 2986.2, 2132.1]}}}
```
Alongside `appearsOnPage`, add `hasTitle` (value = the title text you read), `locatedAt` (value =
`{pdf, sourcePdf, fileId, page, pageInPdf, deliveryId, issueLabel, issuedOn, deliveryKind}`),
`discipline` (value = the sheet number's leading letter run, uppercased — e.g. `A-101` → `"A"`,
`AD-101` → `"AD"`), and
`partOfIssue` (value = the delivery's ref: `{id, label, deliveryKind, issuedOn, sequence}`). Each
evidence block cites the render or text span you actually read — never a fabricated bbox.

**Discipline convention:** derive strictly from the sheet number's own leading letter run, matching the
server's `disciplineFromSheetNumber` logic (all letters before the first digit/dash, uppercased) —
never a full NCS discipline name. Do **not** add client-side compensation for prefixes the server can't
classify; that gap is tracked as PLU-334, not this skill's problem to solve.

**Gate:** every residue row ends up judged (a full claim bundle) or flagged (image-only or genuinely
unreadable) — never silently dropped. State how many you read, corrected, and flagged.

## 6b · Type the sheets (PLU-567)

After residue is judged, classify every recognized sheet — the deterministic pass's own output and
your residue corrections alike — into the project's 13-value `sheetType` vocabulary, and deposit a
claim per sheet. This is agent judgment only: the deterministic recognizer never binds a type, and
an unclear sheet stays untyped rather than getting a guess.

**The vocabulary (exactly these 13 values, no others):**

```
schedule, plan, overall-plan, enlarged-plan, section, elevation, detail, RCP, schematic, legend,
notes, cover-index, other
```

**Efficiency — an 850-sheet set must not require 850 renders.** Classify from the sheet number and
title you already have from steps 5–6 wherever the mapping is unambiguous — no new render needed,
cite the recognized title as your evidence:

- Title contains "FLOOR PLAN" / "SITE PLAN" / "FOUNDATION PLAN" → `plan`
- Title contains "OVERALL" and "PLAN" → `overall-plan`
- Title contains "ENLARGED" and "PLAN" → `enlarged-plan`
- Title contains "ELEVATION" → `elevation`
- Title contains "SECTION" → `section`
- Title contains "SCHEDULE" → `schedule`
- Title contains "DETAIL" / "DETAILS" → `detail`
- Title contains "REFLECTED CEILING" or the sheet reads "RCP" → `RCP`
- Title contains "SCHEMATIC" or "DIAGRAM" → `schematic`
- Title contains "LEGEND" / "SYMBOLS" / "ABBREVIATIONS" → `legend`
- Title contains "GENERAL NOTES" / "NOTES" → `notes`
- The sheet is the set's cover page or a sheet index → `cover-index`
- A real sheet that doesn't map to any of the above → `other`

Only reach for `render_page` when the number and title genuinely leave the type unclear (a sparse or
cryptic title, a discipline whose naming convention you haven't seen yet) — render that one sheet,
judge it, move on. Do not render sheets whose type is already obvious from what recognition gave you.

**Claim shape** — one `sheetType` claim per sheet you classify, matching the residue bundle's shape:

```json
{"subject": "sheet:S-501", "predicate": "sheetType", "value": "schedule",
 "sourceInstrument": "drawing-delivery:<deliveryId>", "versionScope": "<issue label>",
 "evidence": {"source": "<fileId>/page/412", "method": "agent-read",
   "snippet": "DOOR SCHEDULE", "locator": null}}
```

Use `evidence.method: "agent-read"` when the number/title alone decided it (no new render); use
`"agent-vision-read"` with a `locator` bbox when you rendered the page to decide. `value` must be one
of the 13 literal strings above — never invent a fourteenth value, and never write a discipline name,
a partial phrase, or a full title as the value.

**Unsure → leave untyped.** Do not deposit a `sheetType` claim for a sheet you can't confidently place
in the vocabulary; skip it and count it. Narrate: "N sheets typed, M left untyped for review" — never
imply full coverage when some sheets were skipped.

## 7 · Deposit residue and types, then verify

**The recognized portion needs no deposit call from you.** `recognize_sheets` already wrote it
server-side once its job succeeded (step 5), and re-running `recognize_sheets` on the same
file+delivery is safe by construction: the concurrency guard returns the existing job, and the
deposit itself is idempotent (`alreadyDeposited: true` on a poll means a prior run already wrote this
delivery's sheet claims — no duplicate was written). You still make exactly one write of your own
(pooling both the residue bundle from step 6 and the sheetType claims from step 6b), plus one
verification pass:

1. **Deposit the residue + type bundle.** Before depositing, check whether you've already deposited
   residue or types for this delivery in a prior run of this skill — e.g. `search(projectId,
   predicate: "partOfIssue", text: <deliveryId or label>)` and `search(projectId, predicate:
   "sheetType")` — and confirm with the user before sending it again; the server's recognized-claim
   idempotency does not cover claims you authored and sent yourself. Once clear, pool the full claim
   bundles you authored in steps 6 and 6b (recognized pages contribute nothing here — do not re-send
   them) into one array per project and call `propose_batch(projectId, claims)`. It accepts 1–500
   entries and is atomic (one bad entry rejects the whole batch, naming the index); transport every
   entry **verbatim**, never re-typed from memory. **Verify**: the returned `count` must equal the
   number of entries you sent. If it doesn't, stop and report the discrepancy rather than retrying
   with a guessed correction.

2. **Verify the recognized portion against the report — never a full-grid read.** Compare the
   succeeded job's `deposit` summary (`{deposited, alreadyDeposited, byPredicate}`) against its
   `report` (`sheetsGrounded` and the rest) for rough correspondence, then spot-check with a handful
   of targeted `search(projectId, predicate: "appearsOnPage", text: "<a sheet number you saw>")`
   calls. **Do not call `set_grid` to verify a delivery of real size** — on a set with hundreds of
   sheet rows it returns on the order of 600 KB of JSON, large enough that you get a file redirect
   back instead of the payload inline, a poor substitute for a targeted check that also wastes the
   round trip. Reserve `set_grid` for a small project or a later session that genuinely needs the
   whole grid, not this verify step.

Point any unresolved residue, flagged image-only pages, or untyped sheets at `ambiguities(projectId)`
or the plain untyped count — the review queue, not something this skill resolves itself. Report:
project, delivery, the job's `report` counts, its `deposit` summary, your residue-and-type bundle's
count-verified deposit, and that the set is now readable on plumlayer.com with each sheet's source
page behind it.

## Gates (non-negotiable)

- Every claim's evidence is grounded **cloud-side** — a succeeded `recognize_sheets` job (deposited by
  the server) or a `render_page`/`get_page_text` read you just made. A local read (step 2) may inform
  the packaging report; it never grounds a claim.
- Discipline is derived from the sheet's own number prefix, never a filename or folder.
- Residue is judged-or-flagged, never silently dropped; image-only pages are named, not guessed.
- `sheetType` is agent judgment only — never a deterministic guess, never a value outside the
  13-value vocabulary, never assigned to a sheet you're not confident about.
- The residue and type claims are your own reading, cited to the page you read; never present them as
  the deterministic pass's confirmed output.
- Your own deposit (the residue + type bundle) is verbatim, count-verified transport — a count
  mismatch stops the run, never triggers a reconstructed or invented entry.
- Before depositing your residue/type bundle, check for a prior deposit on this delivery and confirm
  with the user rather than double-depositing; the recognized portion is server-idempotent by
  construction (re-running `recognize_sheets` on the same file+delivery is always safe).
- Honest coverage at every stage — pages skipped, files excluded, residue left unread, or sheets left
  untyped are named, not buried in a total.

## Cost (cheapest tier first)

`recognize_sheets` (the deterministic bulk pass) is free server-side compute — it recognizes the
large majority of sheets in seconds to low minutes depending on set size (that's why it runs as a job
you poll, not an inline call). Your token cost is fenced to the residue tail (the pages the pass
couldn't recognize, read once each) plus the sheet-typing pass (mostly free — reused from the
recognized title, with renders reserved for genuinely unclear sheets), plus the small, fixed cost of
polling `recognize_sheets_status` every few seconds while a job runs. The local packaging-recognition
sampling (step 2) is small, bounded to a few pages per ambiguous candidate file, and named in the
packaging report — not a hidden cost. No GPU or model hosting on this path.

## Deferred (named, not skipped silently)

- **OCR for image-only/scanned pages (PLU-186).** No text layer means both the bulk pass and your own
  read come up empty; flag, don't guess.
- **Scale auto-detect at intake (PLU-277).** Not built into this skill yet.
- **Master-list reconciliation as corroboration only.** A full diff against an architect drawing list
  (to surface RFI-worthy discrepancies) is a corroboration layer, never the bootstrap for this skill.
- **Discipline-uncertainty compensation.** The server's prefix-based discipline derivation has a known
  gap for unusual prefixes (PLU-334); this skill does not add client-side heuristics to cover it.
- **Server-side auto-typing for the web-only upload door (PLU-567 web door).** A website-only upload
  has no agent in the loop; a server-side classification job is a separate architecture decision, not
  this skill's problem.
