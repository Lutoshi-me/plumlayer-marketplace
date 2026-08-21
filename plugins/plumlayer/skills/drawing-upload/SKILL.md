---
name: drawing-upload
description: >
  Upload a drawing delivery in any packaging and turn it into cited sheet records in the project
  record. Use for a new set, bulletin, or addendum, or to read an already-uploaded set. Trigger on
  "upload this set", "register the drawings", "drawing index", "/drawing-upload". Drives delivery
  registration, cloud upload, sheet-number recognition, and sheet-type classification via
  `recognize_sheets`. Does not split by discipline, produce a CSV, scope or take off sheets
  (`scope-run` / `takeoff`), or create the project (`project-create`).
---

# Drawing upload: the foundation pass, agent-driven, cloud-first

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

Take whatever the architect actually sent, in whatever shape, and turn it into the one canonical,
recognized set of **cited sheet claims** in the project's project record. This is **Stage 0**: the first
thing that touches a delivery, before anything is split by discipline, routed, or deep-read.

Doctrine binds every stage: **agents read and judge; deterministic tooling grounds; nothing enters
untraced.** Every claim in this pipeline takes effect as soon as it lands, carrying who wrote it and
what they read from: the recognition pass records what it confirmed off the page, and what you judge
yourself records as your own reading, cited to the page you read it on. You are the reader; the MCP
recognition verbs (`recognize_sheets`, `recognize_sheets_status`, `render_page`, `get_page_text`) are
the anti-hallucination anchor, not the inference engine. There is no local pipeline and no
server-side autonomous *reader*: the server runs the deterministic bulk pass and records its own
output, but you still drive every job, judge every residue page, classify every sheet's type, and
author every claim that isn't the deterministic pass's own grounded output.

This skill runs the read cloud-first: recognition and every recorded claim come from the server or
your own read of the cloud-hosted pages, never from a local pass. Examples in this file are generic;
never put a real client or project name here.

## Narration to the user

<!-- user-facing -->
Never let the words "grounding", "ingestion", "the ledger", or "residue pass" reach the user: a
real transcript showed an agent narrating all four and confusing the user about what was actually
happening. Say instead:

- "uploading" (steps 3–4)
- "recognizing sheet numbers" (step 5, while a job is running)
- "N sheets recognized" (step 5, on job success)
- "M pages need review" (step 6/6b residue and untyped sheets, never "residue pass")
- "reading the spec book's table of contents" (step 8, while the extraction job is running)
- "N sections found" (step 8, on job success)
- "checking the drawing index against what we recognized" (step 9, while the reconciliation calls run)
<!-- /user-facing -->

## What this is, and the boundary

`drawing-upload` does exactly one thing: take a drawing delivery and register every sheet in it as
cited claims in the project's project record. The canonical form is claims + provenance over the
untouched original delivery. Discipline organization, by-discipline PDFs, and page labels
are all **projections** of that form, rendered on demand by other skills, never the foundation. So this skill does **not**: physically split files by discipline (discipline is derived
per sheet, never from a filename); produce a CSV (the deliverable is claims in the project record: the export
skill `drawing-set-assemble` renders artifacts from the cloud claims on request); scope, take off, or comprehend the sheets (`scope-run` / `takeoff` / `learn-project`); or create
the project (`project-create`).

**Retired:** `drawing-index`, `drawing-index-bulletin`, `drawing-index-merge`: they organized before
reading (hand-split into discipline PDFs, then parsed a master list), which commits a discipline guess
before any read confirms it and depends on a master list that failed on 3 of 4 characterized projects.
This skill reads first; a master list is corroboration only, never the bootstrap.

## 1. Pick the project

Call `list_projects` and confirm with the user which project record this delivery belongs to (a project is one
project record); get its `projectId`. If there is no project yet, hand off to `project-create` first; this
skill does not create projects. Confirm you also know the **issue label** for this delivery (e.g. a
generic "2025-12-22 CD Set" or "Bulletin 01"): ask the user, or plan to read it off the cover sheet
during recognition. It is load-bearing for supersession later.

## 1b. Cloud-resident entry (files already in the project, nothing local)

Not every run starts from a local delivery. When the user points you at a project whose set is
already in cloud storage (uploaded in a prior session, or they ask you to "read the uploaded set"
or "(re)recognize" it), there is nothing to recognize locally and nothing to upload. Detect it before
asking for paths: if the user hands you no local files, call `list_files(projectId)`; if the
drawings are there, run this branch. When it's genuinely ambiguous (some files uploaded, the user
also holding local files), ask; never assume which delivery the user means.

The branch substitutes the local-only stages and reuses everything else unchanged:

- **Enumerate instead of recognize packaging (replaces step 2).** `list_files(projectId)` is your
  source list: each row carries `fileId`, `filename`, `sizeBytes`, and its `deliveryId` (or null).
  Apply step 2's judgment to that list: which files are drawings and which aren't. When a filename
  doesn't decide, sample a page or two with `render_page` / `get_page_text`: on this branch even the
  file-selection sampling is cloud-side, since there are no local bytes.
<!-- user-facing -->
Emit the same packaging
  report: which files you will recognize, which you're excluding and why.
<!-- /user-facing -->
- **Delivery attribution instead of registration (replaces steps 3–4).** Read each drawing file's
  `deliveryId` from `list_files`, cross-referenced against `list_drawing_deliveries(projectId)`:
  - **Attributed**: the file already carries its delivery. Reuse it; never register a duplicate
    delivery for the same issue.
  - **Unattributed** (`deliveryId: null`): surface the gap to the user; never invent attribution.
    Establish which issue the files belong to (ask, or read it off a cover sheet via
    `render_page`), register the delivery per step 3 if it doesn't exist yet, and pass its id as
    `recognize_sheets.deliveryId` in step 5: that is the supported attach mechanism for an
    already-registered file (a `register_file` retry returns the existing row; it does not
    re-attribute). Chronology still comes from the documents: `issuedOn` off a cover sheet or
    revision table, never upload time.
  - **Mixed attribution** across files is legitimate (files from different deliveries live in one
    project): recognize each file against its own delivery; what you must not do is guess a delivery
    for the unattributed ones or pass a `deliveryId` that disagrees with a file's registered one
    (the server refuses the mismatch).

From here the pipeline is identical: step 5 (`register_pages` once, then `recognize_sheets` per file,
pass `deliveryId` explicitly for any file whose registration doesn't carry it), step 6 (residue
read), step 6b (sheet-type classification), step 7 (residue + type write, verify). Every gate
applies unchanged.

**Re-recognize semantics (the honest limits).** Re-running `recognize_sheets` on a file+delivery is
always safe: a `stale` or `failed` job restarts; a `succeeded` one returns the existing job and the
write stays idempotent. That also means this branch cannot force a fresh read of a file+delivery
that already succeeded: a corrected re-read after a bad run needs the force-re-recognize path,
which is not built yet. Say so plainly rather than re-running and implying new output.


## 2. Recognize the delivery's packaging

Steps 2–4 are the local-delivery path; a set already in cloud storage enters at 1b above and skips
them. A delivery arrives in one of four packaging classes. Recognize the class before uploading
anything:

| Class | What it looks like | How you read it |
|---|---|---|
| **Combined PDF** | the whole set in one file, often mixed with specs/schedules/geotech/emails | the one drawing PDF is the source; exclude the rest |
| **By-discipline folder** | one PDF per discipline (`...Architectural.pdf`, `...Structural.pdf`) | every PDF is a source; never trust the filename for discipline: derive it per sheet |
| **Sequence splits** | arbitrary `Sequence 1 / Sequence 2` PDFs ignoring discipline | every PDF is a source; sheets carry their own discipline prefix |
| **Mixed bag** | drawings + specs + reports as separate files, no naming convention | judge each file to find which are drawings |

Filenames and folder shape *orient* you; they never *decide*. A drawing sheet has sparse text and a
sheet-number token in the bottom-right title block (`A-101`, `S-201`); a spec/geotech/narrative page has
dense body text and no corner title block.

**A non-drawing file is not automatically dead weight.** Judge each one: a project manual / spec book
(a bound, CSI-numbered document, often named "Project Manual", "Specifications", or "Spec Book", with
a Division 00-49 table of contents, whether it's one combined PDF or a folder of per-division PDFs) is
**filed into the project and read by step 8 below, not simply excluded.** Genuinely out-of-scope files
(geotech reports, RFP boilerplate, transmittal emails, meeting minutes) stay excluded.

**Dual-source repackaging:** when a delivery contains both a combined PDF and a full set of per-sheet
PDFs, check page totals first. If the per-sheet PDFs' combined page count equals the combined PDF's page
count, that's duplicate repackaging of the same set, not two sources: **prefer the single combined file
and don't recognize both**; recognizing both wastes a full pass and risks recording the same sheets
twice under different `fileId`s. Only treat it as genuinely ambiguous when the totals disagree or
there's no clean 1:1 correspondence.

For any other genuinely ambiguous packaging (a mixed bag, or a dual-source case the page-total check
didn't resolve), use the **Read tool** directly on a few local candidate pages of each file to judge
title-block grammar vs spec-prose and pick the authoritative source. This local sampling is
**file-selection judgment only**: it decides which local files you upload next; it never grounds a
claim, and no claim's evidence ever cites a local read (every claim's evidence comes from the cloud
recognition tools in steps 5–6).

<!-- user-facing -->
Emit a short packaging report before uploading: the class, which file(s) are the drawings and why,
page counts, which file(s) (if any) are the project manual / spec book headed to step 8, which files
you are excluding (geotech, emails, unrelated attachments) and why, and the picked source if there was
a dual-source quirk.
<!-- /user-facing -->

## 3. Register the delivery

Call `list_drawing_deliveries(projectId)` first. If a delivery with this issue label already exists,
reuse it rather than registering a duplicate. Otherwise call `create_drawing_delivery`:

- `deliveryKind: "baseline"` for a full/conformed re-issue; `"revision"` for a bulletin/addendum/ASI
  (changed sheets only).
- `label`: the human issue label from step 1.
- `issuedOn` (`YYYY-MM-DD`) and `sequence`: read these off the documents themselves (a cover sheet, a
  bulletin header). **Never substitute upload time**: chronology drives supersession resolution.
  **When issue-date signals disagree** (the filename says one date, a cover sheet or transmittal says
  another), the **drawing set's own revision table is authoritative** for `issuedOn`: it's the
  architect's own record of the issue, ahead of a filename someone typed or a transmittal cover letter.
  Note the disagreement in the packaging report rather than silently picking one.

Every file you upload in step 4 attaches to this one `deliveryId`.

## 4. Upload bytes

For each drawing PDF you identified in step 2:

1. `request_file_upload(projectId, filename)` → `{fileId, path, bucket, token, signedUrl}`. The server
   creates `fileId` and the storage path; you never supply either.
2. PUT the raw file bytes to `signedUrl` with a `Content-Type` header (the bytes never pass through a
   tool call):
   ```bash
   curl -X PUT "$SIGNED_URL" -H "Content-Type: application/pdf" --data-binary @"$LOCAL_PDF_PATH"
   ```
3. `register_file(projectId, fileId, filename, contentType, deliveryId)`: always pass `deliveryId` so
   chronology comes from the delivery, not upload order. Idempotent: a retried call for the same
   `fileId` returns the existing row. Rejects `not_found` (PUT didn't land), `empty`, or `oversize`
   (2 GB ceiling per file): if any of these fire, stop and report rather than retrying blindly.

Repeat for every file in the delivery; each one registers to the **same** `deliveryId`. No local run
folder, no manifest file: the project files list (`list_files`) is the record.

## 5. Recognize sheets (async, start then poll)

Call `register_pages(projectId)` **once** for the project: it registers viewable page rows for every
uploaded PDF (not claims, just renderable pages) and only needs to run once per project, not per file.

Then, **once per file**, call `recognize_sheets(projectId, fileId, deliveryId)` to start the
deterministic server-side pass over that PDF. It returns immediately (it does not scan inline) with
`{jobId, status: "queued"|"succeeded", deliveryId, alreadyActive?}`. `alreadyActive: true` means a job
for this file+delivery is already in flight or done; poll the returned `jobId` rather than starting a
second one. Run `recognize_sheets` once per file, never twice for the same file+delivery.

Poll `recognize_sheets_status(projectId, jobId)` every ~3-5s until `state` settles:

- `queued` / `running`: still working; poll again in a few seconds.
- `stale`: no progress for 15 minutes; re-call `recognize_sheets` on the same file/delivery to
  self-heal (it restarts the job).
- `failed`: read `error`, stop, and report it; don't retry blindly.
- `succeeded`: the recognized sheet claims (`appearsOnPage`, `hasTitle`, `locatedAt`, `discipline`,
  `partOfIssue`) are **already recorded server-side.** This result never carries
  those claims and you never `record_batch` them yourself: that would double-write every sheet. Report
  the run-level counts from `report`: `pagesScanned`, `sheetsGrounded`, `highConfCount`, `flaggedCount`,
  `extractionWarningCount`, `calibrated`, `capHit`. Never assume "N pages scanned = N sheets recognized":
  state both numbers. `confidence` on individual claims (visible later via `search`/`set_grid`) is
  triage/review-priority metadata only, never a trust tier.

For a multi-file delivery, start and poll a separate job per file; there is no merge step and no
`SET_TAG`: each file's recognized claims land under the shared `deliveryId` as soon as its own job
succeeds, with no pooling step required.

## 6. Residue read

A `succeeded` `recognize_sheets_status` result carries `residue`: the tail where the deterministic
pass is least sure (low confidence, no sheet number found, or a degraded text layer). Read and judge
every residue row yourself:

- Use `residue[].pageNum` or `pageInPdf` (both 1-based) with `render_page` and `get_page_text`; never
  the legacy 0-based `residue[].page` field. `render_page` returns the PNG inline (pass a normalized
  `region` like `{x0:0.74, y0:0.80, x1:1.0, y1:1.0}` to zoom the title-block corner at higher DPI);
  `get_page_text` returns exact spans with PDF-point bboxes, and `hasTextLayer:false` is the honest
  image-only-page signal (no vector text to read).
- Judge the sheet number, title, and discipline from what you actually see, and handle the two cases
  differently:
  - **A confident correction of a machine misread**: you can see the reader grabbed the wrong cell (a
    tag instead of the sheet number, a boxed note instead of the title). If the recognizer already
    stored a value for that slot, write your corrected value as a supersession **edge** onto it, not a
    bare competing claim: `search(projectId, subject: "sheet:<n>", predicate:
    "hasTitle"|"discipline"|"appearsOnPage")` to get the live claim's `id`, then author your corrected
    claim with `supersedesId` set to that id, cited to the crop you read. The edge is what makes your
    read govern: a bare competing claim loses to the machine value on authorship rank, which is the
    anti-hallucination anchor working as designed. If the slot is empty (the pass
    left this page blank), just author the claim fresh: there is nothing to supersede.
  - **Genuine ambiguity**: you honestly cannot tell which of two readings is right. Author your reading
    as a bare claim tagged with `ambiguityClass` so both surface for a person in `ambiguities`; never
    silently pick. Reserve the flag for real ambiguity; never use it for a correction you are confident
    about (that just hands a person a title you already read correctly).
- **Image-only / scanned pages**: flag them honestly. Create the page as its own subject:
  `page:<fileId>:<pageInPdf>`, never `subject: null`, and never add an OCR dependency (deferred).
  Report the flagged page list; an honest "could not recognize these N pages" beats a guess.

For every residue subject you *do* resolve, author the **full bundle** of claims, mirroring the shape the
server records for the pages the deterministic pass already recognized (matching predicate and value
shapes keeps every sheet's claim set uniform regardless of which stage grounded it):

```json
{"subject": "sheet:S-501", "predicate": "appearsOnPage", "value": 412,
 "sourceInstrument": "drawing-delivery:<deliveryId>", "versionScope": "<issue label>",
 "evidence": {"source": "<fileId>/page/412", "method": "agent-vision-read", "snippet": "S-501",
   "locator": {"frame": "pdf-points", "bboxPts": [2890.1, 2080.4, 2986.2, 2132.1]}}}
```
Alongside `appearsOnPage`, add `hasTitle` (value = the title text you read), `locatedAt` (value =
`{pdf, sourcePdf, fileId, page, pageInPdf, deliveryId, issueLabel, issuedOn, deliveryKind}`),
`discipline` (value = the sheet number's leading letter run, uppercased, e.g. `A-101` → `"A"`,
`AD-101` → `"AD"`), and
`partOfIssue` (value = the delivery's ref: `{id, label, deliveryKind, issuedOn, sequence}`). Each
evidence block cites the render or text span you actually read; never a fabricated bbox.

**Discipline convention:** derive strictly from the sheet number's own leading letter run, matching the
server's `disciplineFromSheetNumber` logic (all letters before the first digit/dash, uppercased);
never a full NCS discipline name. Do **not** add client-side compensation for prefixes the server can't
classify; that gap is a known limitation, not this skill's problem to solve.

**Gate:** every residue row ends up judged (a full claim bundle) or flagged (image-only or genuinely
unreadable); never silently dropped. State how many you read, corrected, and flagged.

## 6b. Type the sheets

After residue is judged, classify every recognized sheet, the deterministic pass's own output and
your residue corrections alike, into the project's 13-value `sheetType` vocabulary, and record a
claim per sheet. This is agent judgment only: the deterministic recognizer never binds a type, and
an unclear sheet stays untyped rather than getting a guess.

### The vocabulary

Exactly these 13 values, no others:

```
schedule, plan, overall-plan, enlarged-plan, section, elevation, detail, RCP, schematic, legend,
notes, cover-index, other
```

### Efficiency

An 850-sheet set must not require 850 renders. Classify from the sheet number and title you already
have from steps 5-6 wherever the mapping is unambiguous, no new render needed, citing the recognized
title as your evidence:

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
cryptic title, a discipline whose naming convention you haven't seen yet): render that one sheet,
judge it, move on. Do not render sheets whose type is already obvious from what recognition gave you.

### Claim shape

One `sheetType` claim per sheet you classify, matching the residue bundle's shape:

```json
{"subject": "sheet:S-501", "predicate": "sheetType", "value": "schedule",
 "sourceInstrument": "drawing-delivery:<deliveryId>", "versionScope": "<issue label>",
 "evidence": {"source": "<fileId>/page/412", "method": "agent-read",
   "snippet": "DOOR SCHEDULE", "locator": null}}
```

Use `evidence.method: "agent-read"` when the number/title alone decided it (no new render); use
`"agent-vision-read"` with a `locator` bbox when you rendered the page to decide. `value` must be one
of the 13 literal strings above; never invent a fourteenth value, and never write a discipline name,
a partial phrase, or a full title as the value.

### Unsure sheets

Do not record a `sheetType` claim for a sheet you can't confidently place in the vocabulary; skip it
and count it.
<!-- user-facing -->
Narrate: "N sheets sorted by type, M I left for a closer look"; never imply full
coverage when some sheets were skipped.
<!-- /user-facing -->

## 6c. Correct a mis-bound recognized title or discipline

The deterministic pass grounds the *tokens* it reads, but *which* cell fills the title or discipline
slot is its reproducible-but-fallible guess: it can grab a boxed drawing note instead of the
title-block cell. So a sheet can come through recognition "successfully" and still carry a wrong title.
(For example, a sheet recognized with the title "SEE NOTE 3 FOR TYPICAL MOUNTING HEIGHT" instead of
"PLUMBING ENLARGED RESTROOM PLANS - LEVEL 3 PART A".) You are not re-reading every recognized title: recognition is
trusted for the bulk. This is for the mis-grabs you actually notice: you will usually catch them in
step 6b, where a recognized "title" that reads like a note, a general instruction, or a bare fragment
rather than a sheet name is the tell, or when the user points one out.

When you are confident a recognized title or discipline is a mis-grab, correct it with a supersession
**edge**, exactly like a confident residue correction (step 6):

1. `search(projectId, subject: "sheet:<n>", predicate: "hasTitle")` (or `"discipline"`) → the live
   machine claim's `id`.
2. `render_page` the title-block corner and read the real title yourself.
3. Author the corrected claim with `supersedesId` set to that id, cited to the crop you read, and pool
   it into your step 7 write.

The edge is what makes your read govern the grid: the recognizer's binding is `machine-read`, and an
agent edge onto it is honored regardless of that register; only a person's later word outranks you.
A **bare** corrected claim with no `supersedesId` does NOT win; it sits as a
candidate beneath the machine value. Never reach for the `ambiguityClass` flag here: a flag is for
genuine ambiguity, and flagging a title you already read correctly is the "go set it on the site" dead
end this step exists to close.

<!-- user-facing -->
Narrate it in estimator words: "the automatic scan grabbed the wrong text on N sheets, so I read them
and set them right"; never "supersede", "claim", or "edge".
<!-- /user-facing -->

## 7. Record residue and types, then verify

**The recognized portion needs no write call from you.** `recognize_sheets` already wrote it
server-side once its job succeeded (step 5), and re-running `recognize_sheets` on the same
file+delivery is safe by construction: the concurrency guard returns the existing job, and the
write itself is idempotent (`alreadyWritten: true` on a poll means a prior run already wrote this
delivery's sheet claims, no duplicate was written). You still make exactly one write of your own
(pooling the residue bundle from step 6, the sheetType claims from step 6b, and any mis-bind
corrections from step 6c, the edges carrying their `supersedesId`), plus one verification pass:

1. **Record the residue + type bundle.** Before recording, check whether you've already recorded
   residue or types for this delivery in a prior run of this skill (e.g. `search(projectId,
   predicate: "partOfIssue", text: <deliveryId or label>)` and `search(projectId, predicate:
   "sheetType")`), and confirm with the user before sending it again; the server's recognized-claim
   idempotency does not cover claims you authored and sent yourself. Once clear, pool the full claim
   bundles you authored in steps 6, 6b, and 6c (recognized pages you did not correct contribute
   nothing here: do not re-send them) into one array per project.

   **For a small bundle, call `record_batch(projectId, claims)` directly.** It accepts 1–500
   entries and is atomic (one bad entry rejects the whole batch, naming the index); transport every
   entry **verbatim**, never re-typed from memory. **Verify**: the returned `count` must equal the
   number of entries you sent. If it doesn't, stop and report the discrepancy rather than retrying
   with a guessed correction.

   **For a large agent-authored bundle (a deep set with thousands of residue/type entries), use
   `record_batch_file` instead of chaining many `record_batch` calls.** The path: write the full
   claim array as JSONL, `request_file_upload(projectId, filename)` for a signed URL, PUT the JSONL
   bytes to it, `register_file(projectId, fileId, filename, contentType: "application/jsonl", kind:
   "document")`, then call `record_batch_file(projectId, fileId)` to write straight from the
   registered file. Verify the same way: read back a count and confirm it matches what you wrote to
   the file, never assume the upload landed intact. Keep `record_batch` for small inline batches;
   reach for `record_batch_file` only once a single bundle is large enough that chaining
   `record_batch` calls would be the wrong shape.

   **A freshly-shipped verb may not appear until the session reloads the plugin / reconnects MCP.**
   If `record_batch_file` (or any verb you expect) is missing from your tool list, reload the
   session before concluding it doesn't exist.

2. **Verify the recognized portion against the report; never a full-grid read.** Compare the
   succeeded job's `write` summary (`{written, alreadyWritten, byPredicate}`) against its
   `report` (`sheetsGrounded` and the rest) for rough correspondence, then spot-check with a handful
   of targeted `search(projectId, predicate: "appearsOnPage", text: "<a sheet number you saw>")`
   calls. **Do not call `set_grid` to verify a delivery of real size**: on a set with hundreds of
   sheet rows it returns on the order of 600 KB of JSON, large enough that you get a file redirect
   back instead of the payload inline, a poor substitute for a targeted check that also wastes the
   round trip. Reserve `set_grid` for a small project or a later session that genuinely needs the
   whole grid, not this verify step.

Point any unresolved residue, flagged image-only pages, or untyped sheets at `ambiguities(projectId)`
or the plain untyped count: the review queue, not something this skill resolves itself.
<!-- user-facing -->
Report: the
project and delivery; the recognition run's counts (pages scanned, sheets recognized, how many were
high-confidence, how many were flagged for a closer look); how many sheet records were saved and how
many were already on file; the count of entries you added yourself for the sheets you reviewed and
typed, confirmed against what you sent; and that the set is now readable on plumlayer.com with each
sheet's source page behind it.
<!-- /user-facing -->

## 8. Extract the spec book's table of contents

When step 2's packaging pass turned up a project manual / spec book, file it and read its table of
contents now, before the reconciliation gate below. The gate's spec-comparison leg needs this layer to
run against; reconciling first always reports the spec leg as not having run, even when a manual sat on
disk the whole time.

1. **File it as a document.** Run the same upload mechanics as step 4 (`request_file_upload`, PUT the
   bytes to `signedUrl`, then `register_file(projectId, fileId, filename, contentType, kind:
   "document")`) for the manual PDF(s) step 2 identified. A project manual is a project record, not a
   drawing sheet, so it does not attach to a `deliveryId`. Misfiled earlier as a drawing? Fix it in
   place with `update_file(projectId, fileId, kind: "document")` rather than re-uploading:
   reclassifying away from `drawing` sweeps its stray page rows in the same call.
2. **Start the extraction: one job, never N.** Call `extract_spec_toc(projectId, fileIds, issueLabel?)`.
   Pass the single manual's `fileId` for a combined-manual delivery. For a folder-of-divisions delivery
   (`Division 01.pdf`, `Division 02.pdf`, ... instead of one bound manual), pass every division PDF's
   `fileId` together in the SAME call: the extraction unions across them into one section set; never
   call it once per division file. It returns `{jobId, status}` immediately.
3. **Poll `extract_spec_toc_status(projectId, jobId)`** every ~3-5s until `state` is `succeeded` or
   `failed`: the same queued/running/stale rhythm as `recognize_sheets_status` in step 5. On `failed`,
   read `error`, stop, and report it; don't retry blindly. On `stale`, re-call `extract_spec_toc` on the
   same file set to restart.
4.
<!-- user-facing -->
**Report the counts honestly, not just "N sections found."** From the succeeded job's `report`:
   sections found, files opened vs failed (a multi-file run can succeed overall while still naming one
   corrupt division PDF in `failedFiles`: that's a finding for the user, never a silent retry
   loop), and the completeness-diff / mismatch / residue counts. **`sectionsFound` counts only
   footer-confirmed sections** (the per-page CSI-code footer read): a section declared solely in the
   PDF bookmark tree, with no confirming footer, does NOT add to that count; it surfaces instead through
   the completeness findings, never as a silent gap in the number you report.
<!-- /user-facing -->
5. **Read-back verify.** Call `search(projectId, predicate: "inDivision")` and confirm the recorded row
   count matches the job's `sectionsFound` exactly: completeness/residue findings ride their own
   predicate (`hasCompletenessStatus`) and never appear in this read. A mismatch stops the run and gets
   reported, never a guessed correction.

**If `extract_spec_toc` / `extract_spec_toc_status` don't appear in your tool list**, the same
session-reload rule from step 7 applies. Start a fresh session rather than
assuming the manual can't be read.

**No project manual in this delivery?** Say so plainly in the report and move on to step 9: nothing
here blocks the reconciliation gate; it only means the gate's spec leg reports as not having run (step
9 already covers that honestly).

## 9. Reconcile the index against the set

This is the pre-read reconciliation gate. Before anything downstream reads this set for scope, run
one deterministic check: does the delivery's own drawing index agree with what actually got
recognized, and with the spec sections read from the project
manual. Catching a set-level mismatch here keeps it from poisoning every read that follows.

1. **Read the index as stated.** Call `reconcile_index(projectId)` to parse the delivery's drawing
   index page(s) and record each listed sheet as a cited `declaredInIndex` claim. It reads from
   sheets the set grid classified `cover-index` in step 6b; if none were classified, pass `pages`
   yourself, pointing at the index page(s) you know about. Report `declaredCount`, and whether
   `backstop.requested` came back true: that means the parse could not stand as the declared
   register (no text layer, too few sheets found, a column structure that did not resolve), and you
   should read the rendered index page yourself with `render_page` before trusting the count.
2. **Run the diff, report-only.** Call `reconcile_set(projectId)` without `record`. The bare call
   runs the ORIENTATION check: the index of record (the newest delivery that actually has a read
   drawing index) against the current compiled set across every delivery, not just one. Pass
   `deliveryId` instead to run the per-delivery RECEIVING check: that one delivery's own drawing
   index against only the sheets delivered in it. `result.mode` reports which comparison ran. Either
   way it compares three sides: what the index declares, what sheets are actually in the set, and
   what the spec sections say. It returns a full report; it writes nothing on this call.
3.
<!-- user-facing -->
**Walk the user through the report** before recording anything:
   - What matched: the overlap between the index and the set.
   - What the index lists that isn't in the set: while the delivery still holds pages nobody has
     recognized, this sits in your own review queue (the sheet may be on one of them); once every
     page is recognized, it becomes a question for the design team.
   - What's in the set the index doesn't list: checked first against the index page's own raw
     text (a table-reading miss on our side lands in your review queue; a genuine absence becomes a
     question for the design team).
   - What couldn't be read: `report.residue.parseRejectedSample` and
     `report.residue.unparsedPages` name the tokens and pages this run could not account for; state
     those counts out loud rather than folding them into "no problems found."
   - Whether the index re-read agreed with the stored records: check `report.declaredLedgerDrift.ran`
     first. It's `false`, never a hollow zero, whenever no index page could be read at all, or a
     receiving-check run had to widen its re-read to another delivery's pages; the drift arrays are
     empty in that case too, and that's a check that didn't run, not a check that found nothing.
   - Whether the spec comparison ran at all: when step 8 found no project manual to extract for
     this delivery, the spec leg is reported as not having run. Say exactly that; never present it
     as a finding of zero.
<!-- /user-facing -->
4. **Offer to record the residue.** Once the user has seen the report, offer
   `reconcile_set(projectId, record: true)` to record the sheet findings and the grouped questions
   for the design team (grouped by discipline series, not one per sheet). Only run it on the
   user's go-ahead: this is where the residue becomes part of the review queue.

## Gates (non-negotiable)

- Every claim's evidence is grounded **cloud-side**: a succeeded `recognize_sheets` job (recorded by
  the server) or a `render_page`/`get_page_text` read you just made. A local read (step 2) may inform
  the packaging report; it never grounds a claim.
- Discipline is derived from the sheet's own number prefix, never a filename or folder.
- Residue is judged-or-flagged, never silently dropped; image-only pages are named, not guessed.
- `sheetType` is agent judgment only: never a deterministic guess, never a value outside the
  13-value vocabulary, never assigned to a sheet you're not confident about.
- A confident correction of a machine misread (a mis-grabbed title or discipline, in residue or on an
  already-recognized sheet) is a supersession **edge** onto the stored claim (`supersedesId` from
  `search`), never a bare competing claim and never an `ambiguityClass` flag: the flag is reserved for
  a reading you genuinely cannot resolve.
- The residue and type claims are your own reading, cited to the page you read; never present them as
  the deterministic pass's confirmed output.
- Your own write (the residue + type bundle) is verbatim, count-verified transport: a count
  mismatch stops the run, never triggers a reconstructed or invented entry.
- Before recording your residue/type bundle, check for a prior write on this delivery and confirm
  with the user rather than double-recording; the recognized portion is server-idempotent by
  construction (re-running `recognize_sheets` on the same file+delivery is always safe).
- Honest coverage at every stage: pages skipped, files excluded, residue left unread, or sheets left
  untyped are named, not buried in a total.
- The spec-book leg (step 8) extracts a file set once, never once per division file, and its counts are
  read back with `search` and verified against the job's own `report`, never assumed. A named
  `failedFiles` entry is a finding for the user, never a silent retry loop.
- The reconciliation gate (step 9) is honest about its own bounds: no classified index page, a
  backstop, or an unread spec manual are named as what didn't run, never paraphrased into "no
  problems found." `reconcile_set` residue is recorded only on the user's go-ahead.

## Cost (cheapest tier first)

`recognize_sheets` (the deterministic bulk pass) is free server-side compute: it recognizes the
large majority of sheets in seconds to low minutes depending on set size (that's why it runs as a job
you poll, not an inline call). Your token cost is fenced to the residue tail (the pages the pass
couldn't recognize, read once each) plus the sheet-typing pass (mostly free: reused from the
recognized title, with renders reserved for genuinely unclear sheets), plus the small, fixed cost of
polling `recognize_sheets_status` every few seconds while a job runs. The local packaging-recognition
sampling (step 2) is small, bounded to a few pages per ambiguous candidate file, and named in the
packaging report; not a hidden cost. No GPU or model hosting on this path.

## Deferred (named, not skipped silently)

- **OCR for image-only/scanned pages.** No text layer means both the bulk pass and your own read come
  up empty; flag, don't guess.
- **Scale auto-detect at intake.** Not built into this skill yet.
- **Master-list reconciliation as corroboration only.** A full diff against an architect drawing list
  (to surface RFI-worthy discrepancies) is a corroboration layer, never the bootstrap for this skill.
- **Discipline-uncertainty compensation.** The server's prefix-based discipline derivation has a known
  gap for unusual prefixes; this skill does not add client-side heuristics to cover it.
- **Server-side auto-typing for the web-only upload door.** A website-only upload has no agent in the
  loop; a server-side classification job is a separate architecture decision, not this skill's
  problem.
