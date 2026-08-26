---
name: drawing-upload
description: >
  Upload a drawing delivery in any packaging, or a project manual on its own, and turn it into cited
  sheet records in the project record. Use for a new set, a bulletin or addendum, a full re-issue, or
  to read an already-uploaded set. Trigger on "upload this set", "register the drawings", "here's the
  revised manual", "/drawing-upload". Drives delivery registration, cloud upload, recognize_sheets,
  sheet typing, and extract_spec_toc. Does not split by discipline, produce a CSV, scope or take off
  sheets (scope-run / takeoff), or create the project (project-setup).
---

# Drawing upload: the foundation pass, agent-driven, cloud-first

Take whatever the architect actually sent, in whatever shape, and turn it into the one canonical,
recognized set of **cited sheet entries** in the project's project record. This is **Stage 0**: the first
thing that touches a delivery, before anything is split by discipline, routed, or deep-read.

Doctrine binds every stage: **agents read and judge; deterministic tooling grounds; nothing enters
untraced.** Every entry in this pipeline takes effect as soon as it lands, carrying who wrote it and
what they read from: the recognition pass records what it confirmed off the page, and what you judge
yourself records as your own reading, cited to the page you read it on. You are the reader; the MCP
recognition verbs (`recognize_sheets`, `recognize_sheets_status`, `render_page`, `get_page_text`) are
the anti-hallucination anchor, not the inference engine. There is no local pipeline and no
server-side autonomous *reader*: the server runs the deterministic bulk pass, which also types most
sheets by a rule match, and records its own output, but you still drive every job, judge every page
the pass could not name, type the sheets the rule pass left untyped, and author every entry that
isn't the deterministic pass's own grounded output.

This skill runs the read cloud-first: recognition and every recorded entry come from the server or
your own read of the cloud-hosted pages, never from a local pass. Examples in this file are generic;
never put a real client or project name here.

This skill runs in the conversation, start to finish. No step of it is handed to a background
agent or a subagent: there is no named agent for this work, and an improvised one cannot take the
user's answers or report a job's state first-hand. A long recognition job is waited on here, in
the open, with the poll loop in step 5.

Run, or stop and report; never create a consent step. The user's decisions in this skill are:
which project this delivery belongs to, its issue label, whether it is changed sheets or a full
re-issue when the paper does not say, which files are the drawings when the packaging leaves it
genuinely unclear, and whether to send a page and type bundle again when a prior one is on file.
Ask each of those once, in plain words, and where you already have a reading (off a cover sheet,
off the file list) put it forward as the answer with its source named, so the user corrects it
rather than composes it. Everything else the skill does is its own work, recorded with its trail
and editable afterward. Never stop to collect approval for a course you have already chosen, and
never put your own next step to the user as a choice: if something is wrong, stop, say what is
wrong, and hand it over; if nothing is wrong, proceed and say what you did.

## Narration to the user

<!-- user-facing -->
How to say each thing as it happens:

- "uploading" (steps 3–4)
- "recognizing sheet numbers" (step 5, while a job is running)
- "N sheets recognized" (step 5, on job success)
- "M pages need review" (the step 6/6b unnamed pages and untyped sheets)
- "reading the spec book's table of contents" (step 8, while the extraction job is running)
- "N sections found" (step 8, on job success)
- "checking the drawing index against what we recognized" (step 9, while the reconciliation calls run)
<!-- /user-facing -->

## What this is, and the boundary

`drawing-upload` does one thing: take a drawing delivery and register every sheet in it as
cited entries in the project's project record. The canonical form is entries + provenance over the
untouched original delivery. Discipline organization, by-discipline PDFs, and page labels
are all **projections** of that form, rendered on demand by other skills, never the foundation. So this skill does **not**: physically split files by discipline (discipline is derived
per sheet, never from a filename); produce a CSV (the deliverable is entries in the project record: the export
skill `drawing-set-assemble` renders artifacts from the cloud entries on request); scope, take off, or comprehend the sheets (`scope-run` / `takeoff` / `learn-project`); or create
the project (`project-setup`).

The one door here that carries no drawings: a project manual arriving on its own is filed and its
table of contents read (step 8), with no delivery registered and no sheet recognized. Step 1b names
that leg.

**Retired:** `drawing-index`, `drawing-index-bulletin`, `drawing-index-merge`: they organized before
reading (hand-split into discipline PDFs, then parsed a master list), which commits a discipline guess
before any read confirms it and depends on a master list that failed on 3 of 4 characterized projects.
This skill reads first; a master list is corroboration only, never the bootstrap.

## 1. Pick the project

Call `list_projects` and confirm with the user which project record this delivery belongs to (a project is one
project record); get its `projectId`. If there is no project yet, hand off to `project-setup` first; this
skill does not create projects. Confirm you also know the **issue label** for this delivery (e.g. a
generic "2025-12-22 CD Set" or "Bulletin 01"): ask the user, or plan to read it off the cover sheet
during recognition. It is load-bearing for supersession later.

## 1b. What kind of delivery is this

Settle this before anything is registered: is this **changed sheets only** (a bulletin, an addendum,
an ASI) or a **full re-issue** (a permit set, a conformed set, a re-issued CD set)? The answer
decides how the delivery registers in step 3 and what step 10 has to report, and it is nearly always
printed on the paper. Read the cover sheet or the bulletin header first and put your reading
forward as the answer, naming where you read it; never ask cold when the document says it.

<!-- user-facing -->
Ask it in plain words, "is this a set of changed sheets, or a full re-issue of the whole set?", and
say which one you think it is and what you read that off.
<!-- /user-facing -->

**Changed sheets only** registers as `deliveryKind: "revision"` in step 3. The server combines the
deliveries by sheet number, and for each sheet the newest delivery that carries it wins, so the set
stays whole: a sheet this delivery doesn't carry keeps showing from the delivery that last issued
it, which is the right outcome for a bulletin.

**A full re-issue** registers as `deliveryKind: "baseline"`. Name the consequence up front, before
the upload, rather than letting it surface as a surprise afterwards: a baseline combines the same
way, so every sheet the prior set had that this delivery does not carry keeps showing as part of the
set. Step 10 reads those sheets back and reports them as a finding. Nothing is retired, here or
anywhere else in this skill.

**The project's first delivery**, meaning `list_drawing_deliveries(projectId)` comes back empty: it
is a baseline by construction. Don't put the question to the user; there is no prior set for a
re-issue to replace. Step 10's comparison has nothing to compare against on this path, and says so
plainly rather than reporting an empty finding.

**An already-registered delivery** (the 1c branch below): its kind is already recorded. Read it off
`list_drawing_deliveries` rather than re-asking, and check it against the cover sheet. A
disagreement between the two is a finding for the user; don't change the registered kind to match
your own read.

**A project manual arriving on its own**, with no drawings: this is not a drawing delivery. Register
nothing, skip steps 3 through 7, and enter at step 8, which files the manual and reads its table of
contents. Step 9 still runs, and its drawing legs report as unchanged because no sheet changed. Say
in the closing report that no drawings came with it.

## 1c. Cloud-resident entry (files already in the project, nothing local)

Step 1b's question still applies on this branch: a file with no delivery attached to it needs its
kind settled before step 3 can register anything for it.

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
pass `deliveryId` explicitly for any file whose registration doesn't carry it), step 6 (read the
pages the pass could not name), step 6b (sheet-type classification), step 7 (page + type write,
verify). Every gate
applies unchanged.

**Re-recognize semantics (the honest limits).** Re-running `recognize_sheets` on a file+delivery is
always safe: a `stale` or `failed` job restarts; a `succeeded` one returns the existing job and the
write stays idempotent. That also means this branch cannot force a fresh read of a file+delivery
that already succeeded: a corrected re-read after a bad run needs a force-re-recognize path, which
is not built yet. Say so plainly rather than re-running and implying new output.

**Idempotent recognition is not evidence of typing coverage.** A `succeeded` job returning
unchanged tells you nothing about whether step 6b ever ran for these sheets. A delivery recognized
before this skill carried a typing stage, or one whose earlier run stopped short of it, looks
identical from `recognize_sheets_status` alone to a fully typed one. Before this branch reports
done, check typing coverage directly (as in step 7's verify) rather than inferring it from the
job's idempotent success. The force-re-recognize gap above is a recognition-fidelity limit only;
it is never license to skip the typing check, which does not depend on it.

## 2. Recognize the delivery's packaging

Steps 2–4 are the local-delivery path; a set already in cloud storage enters at 1c above and skips
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
twice under different `fileId`s. Only treat it as genuinely unclear when the totals disagree or
there's no clean 1:1 correspondence.

For any other genuinely unclear packaging (a mixed bag, or a dual-source case the page-total check
didn't resolve), use the **Read tool** directly on a few local candidate pages of each file to judge
title-block grammar vs spec-prose and pick which one to use. This local sampling is
**file-selection judgment only**: it decides which local files you upload next; it never grounds an
entry, and no entry's evidence ever cites a local read (every entry's evidence comes from the cloud
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
  another), the **drawing set's own revision table governs** `issuedOn`: it's the
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
uploaded PDF (not entries, just renderable pages) and only needs to run once per project, not per file.

Then, **once per file**, call `recognize_sheets(projectId, fileId, deliveryId)` to start the
deterministic server-side pass over that PDF. It returns immediately (it does not scan inline) with
`{jobId, status: "queued"|"succeeded", deliveryId, alreadyActive?}`. `alreadyActive: true` means a job
for this file+delivery is already in flight or done; poll the returned `jobId` rather than starting a
second one. Run `recognize_sheets` once per file, never twice for the same file+delivery.

Poll `recognize_sheets_status(projectId, jobId)` every ~3-5s. The loop has exactly two exits, and
both are the server's: `state` is `succeeded` or `failed`, or `state` is `stale`. Nothing else ends
it. Not the clock (a big set can run many minutes and still be working), not a poll that looks the
same as the last one, not a connection drop (reconnect and poll again with the same `jobId`), and
not a second `recognize_sheets` call that answers `alreadyActive: true` (that is the same job,
still running; keep polling it). If you stop polling for any other reason, that is your own
decision: say so in those words, and never describe the job as hung, stuck, or dead, because you
did not observe that. What the server says on each poll:

- `queued` / `running`: still working; poll again in a few seconds.
- `stale`: the server saw no progress for 15 minutes; re-call `recognize_sheets` on the same
  file/delivery to self-heal (it restarts the job).
- `failed`: read `error` and report it. A retry is your call only when the error names something a
  retry changes: a stale restart, a transient fetch. A job that failed at a server limit (a timeout
  at the worker's ceiling) fails the same way again on the same file; do not run it again, and do
  not put "how should I retry?" to the user. Report the error, say that the file needs a server-side
  fix before it will recognize, and stop.
- `succeeded`: the recognized sheet entries (`appearsOnPage`, `hasTitle`, `locatedAt`, `discipline`,
  `partOfIssue`) are **already recorded server-side.** This result never carries
  those entries and you never `record_batch` them yourself: that would double-write every sheet. Report
  the run-level counts from `report`: `pagesScanned`, `sheetsGrounded`, `highConfCount`, `flaggedCount`,
  `extractionWarningCount`, `calibrated`, `capHit`. Never assume "N pages scanned = N sheets recognized":
  state both numbers. `confidence` on individual entries (visible later via `search`/`set_grid`) is
  triage/review-priority metadata only, never a trust tier.

For a multi-file delivery, start and poll a separate job per file; there is no merge step and no
`SET_TAG`: each file's recognized entries land under the shared `deliveryId` as soon as its own job
succeeds, with no pooling step required.

<!-- user-facing -->
Whenever you tell the user where a job stands, mid-run or at the end, quote the last status
payload you actually received and when you received it: the `state`, the progress fields it
carried, and the time of that poll. Never a summary, never a duration you did not measure from
two polls you hold, and never a state you inferred. "Last poll at 19:33:10, running, 140 of 209
pages scanned" is a report; "it has been hanging for an hour" is not.
<!-- /user-facing -->

## 6. Read the pages the pass could not name

A `succeeded` `recognize_sheets_status` result carries `unnamedPages`: the tail where the deterministic
pass is least sure (low confidence, no sheet number found, or a degraded text layer). Read and judge
every page in that tail yourself:

- Use `unnamedPages[].pageNum` or `pageInPdf` (both 1-based) with `render_page` and `get_page_text`; never
  the legacy 0-based `unnamedPages[].page` field. `render_page` returns the PNG inline (pass a normalized
  `region` like `{x0:0.74, y0:0.80, x1:1.0, y1:1.0}` to zoom the title-block corner at higher DPI);
  `get_page_text` returns exact spans with PDF-point bboxes, and `hasTextLayer:false` is the honest
  image-only-page signal (no vector text to read).
- Judge the sheet number, title, and discipline from what you actually see, and handle the two cases
  differently:
  - **A confident correction of a machine misread**: you can see the reader grabbed the wrong cell (a
    tag instead of the sheet number, a boxed note instead of the title). If the recognizer already
    stored a value for that slot, write your corrected value as a supersession **edge** onto it, not a
    bare competing entry: `search(projectId, subject: "sheet:<n>", predicate:
    "hasTitle"|"discipline"|"appearsOnPage")` to get the live entry's `id`, then author your corrected
    entry with `supersedesId` set to that id, cited to the crop you read. The edge is what makes your
    read govern: a bare competing entry loses to the machine value on authorship rank, which is the
    anti-hallucination anchor working as designed. If the slot is empty (the pass
    left this page blank), just author the entry fresh: there is nothing to supersede.
  - **Genuinely unclear**: you honestly cannot tell which of two readings is right. Author your reading
    as a bare entry, cited to what you read, and raise it as a question with `ask_question` so a person
    resolves it; never silently pick. Ask only for a real toss-up; never for a correction you are
    confident about (that just hands a person a title you already read correctly).
- **Image-only / scanned pages**: flag them honestly. Create the page as its own subject:
  `page:<fileId>:<pageInPdf>`, never `subject: null`, and never add an OCR dependency (deferred).
  Report the flagged page list; an honest "could not recognize these N pages" beats a guess.

For every one of those pages you *do* resolve, author the **full bundle** of entries, mirroring the shape the
server records for the pages the deterministic pass already recognized (matching predicate and value
shapes keeps every sheet's entry set uniform regardless of which stage grounded it):

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
never a full NCS discipline name. Do not add client-side compensation for prefixes the server can't
classify; that gap is a known limitation, not this skill's problem to solve.

**Gate:** every page in that tail ends up judged (a full entry bundle) or flagged (image-only or genuinely
unreadable); never silently dropped. State how many you read, corrected, and flagged.

## 6b. Type the sheets

Recognition itself now types most of the set: at `recognize_sheets` finalize, the server runs a
deterministic rule pass over every newly recognized sheet, matching its sheet-number prefix or
recognized title against the 13-value vocabulary below. A match writes a `sheetType` entry
server-side, authored as `machine-read`, cited to the matched title words, with a `confidence` of
`high` or `medium`. A sheet the rules can't place gets nothing: those leftover sheets, never `other` (the
rule pass never writes `other`), is what you read here. So this step is the backstop to the
server's typing, not the whole of it: type the leftover sheets the rules left untyped, plus any rule-typed
sheet you judge to be wrong; an unclear sheet still stays untyped rather than getting a guess.

Start from `recognize_sheets_status`'s `written.sheetTyping` summary: `{sheetsConsidered, typed,
highConfidence, mediumConfidence, untyped, typedWritten}`. `typed` is how many the rules placed on
this run; `untyped` is the leftover set you're about to read.
<!-- user-facing -->
Narrate the split in estimator words: "the recognition pass sorted N of M sheets by type; I'm
looking at the K it left."
<!-- /user-facing -->

Find the leftover sheets from `set_grid` rows carrying no `sheetType`, or `search(projectId, predicate:
"sheetType")` against the recognized set to see what's already covered. Apply the keyword/judgment
guidance and render-only-when-unclear rule below to those leftover sheets only, and record an entry per sheet
you can confidently place.

**Correcting a rule-typed sheet.** When you judge a rule-typed sheet wrong, correct it the same way
you'd correct any recognizer-set value (step 6c): never a bare re-record. A bare entry with no
`supersedesId` onto an occupied slot is refused, naming the record it would have to replace.
`search(projectId, subject: "sheet:<n>", predicate: "sheetType")`, take the id of the current row
(the most recent one search returns for that slot), and author your corrected entry with
`supersedesId` set to it, cited to what you actually read. That edge is what makes your read govern.

This step runs on every door this skill supports: a fresh baseline, a bulletin or revision, and the
cloud-resident re-recognition branch (1c) all converge here before the skill reports done. If this
delivery, or an earlier delivery in the same project, already went through recognition but was
never typed (from a session that predates the server-side rule pass, or one that stopped short),
closing that gap is this run's job, not something to leave for later. A recognized sheet with no
`sheetType` entry, whether rule-typed or agent-typed, and no honest skip-count is never a valid
resting state for any path through this skill.

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

### Entry shape

One `sheetType` entry per sheet you classify, matching the step 6 bundle's shape:

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

Do not record a `sheetType` entry for a sheet you can't confidently place in the vocabulary; skip it
and count it. Build the skipped list from the record, not from memory: `search(projectId,
predicate: "sheetType")` against the recognized sheet list gives the exact set with no type entry.
<!-- user-facing -->
Narrate: "N sheets sorted by type, M I left for a closer look"; never imply full
coverage when some sheets were skipped. Name the M by sheet number and say what the list is: the
sheets left without a type. It is a different list from the title disagreements in the index check,
even when most numbers repeat; if you mention that earlier list, say which sheets are in both and
which are in only one, never "the same".
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
**edge**, exactly like a confident step 6 correction:

1. `search(projectId, subject: "sheet:<n>", predicate: "hasTitle")` (or `"discipline"`) → the live
   machine entry's `id`.
2. `render_page` the title-block corner and read the real title yourself.
3. Author the corrected entry with `supersedesId` set to that id, cited to the crop you read, and pool
   it into your step 7 write.

The edge is what makes your read govern the grid: the recognizer's binding is `machine-read`, and an
agent edge onto it is honored regardless of who wrote the value it corrects, as long as your entry
names what it replaces with `supersedesId`. If a person already set the value and you think it's
wrong, ask them rather than overwrite it. A **bare** corrected entry with no `supersedesId` does NOT
win; it sits as a candidate beneath the machine value. Never raise this as a question here: reserve
`ask_question` for genuine uncertainty, and asking about a title you already read correctly is the
"go set it on the site" dead end this step exists to close.

<!-- user-facing -->
Say it the way it happened: "the automatic scan grabbed the wrong text on N sheets, so I read them
and set them right".
<!-- /user-facing -->

## 7. Record the pages and types, then verify

**The recognized portion needs no write call from you.** `recognize_sheets` already wrote it
server-side once its job succeeded (step 5), and re-running `recognize_sheets` on the same
file+delivery is safe by construction: the concurrency guard returns the existing job, and the
write itself is idempotent (`alreadyWritten: true` on a poll means a prior run already wrote this
delivery's sheet entries, no duplicate was written). You still make exactly one write of your own
(pooling the step 6 bundle, the sheetType entries from step 6b, and any mis-bind
corrections from step 6c, the edges carrying their `supersedesId`), plus one verification pass:

1. **Record the page + type bundle.** Before recording, check whether you've already recorded
   these pages or types for this delivery in a prior run of this skill (e.g. `search(projectId,
   predicate: "partOfIssue", text: <deliveryId or label>)` and `search(projectId, predicate:
   "sheetType")`), and confirm with the user before sending it again; the server's recognized-entry
   idempotency does not cover entries you authored and sent yourself. Once clear, pool the full entry
   bundles you authored in steps 6, 6b, and 6c (recognized pages you did not correct contribute
   nothing here: do not re-send them) into one array per project.

   **For a small bundle, call `record_batch(projectId, entries)` directly.** It accepts 1–500
   entries and is atomic (one bad entry rejects the whole batch, naming the index); transport every
   entry **verbatim**, never re-typed from memory. **Verify**: the returned `count` must equal the
   number of entries you sent. If it doesn't, stop and report the discrepancy rather than retrying
   with a guessed correction.

   **For a large agent-authored bundle (a deep set with thousands of page and type entries), use
   `record_batch_file` instead of chaining many `record_batch` calls.** The path: write the full
   entry array as JSONL, `request_file_upload(projectId, filename)` for a signed URL, PUT the JSONL
   bytes to it, `register_file(projectId, fileId, filename, contentType: "application/jsonl", kind:
   "document")`, then call `record_batch_file(projectId, fileId)` to write straight from the
   registered file. Verify the same way: read back a count and confirm it matches what you wrote to
   the file, never assume the upload landed intact. Keep `record_batch` for small inline batches;
   reach for `record_batch_file` only once a single bundle is large enough that chaining
   `record_batch` calls would be the wrong shape.

   **A freshly-shipped verb may not appear until the session reloads the plugin / reconnects MCP.**
   If `record_batch_file` (or any verb you expect) is missing from your tool list, reload the
   session before concluding it doesn't exist.

2. **Verify the recognized portion against the report, with a targeted check rather than the whole
   grid.** Compare the succeeded job's `write` summary (`{written, alreadyWritten, byPredicate}`)
   against its `report` (`sheetsGrounded` and the rest) for rough correspondence, then spot-check
   with a handful of targeted `search(projectId, predicate: "appearsOnPage", text: "<a sheet number
   you saw>")` calls. That spot-check is this step's verify. **What to avoid here is a bare,
   unpaged `set_grid` call**: on a set with hundreds of sheet rows it returns on the order of 600 KB
   of JSON, large enough that you get a file redirect back instead of the payload inline, and its
   default first page is not the set anyway. A paged read is a different thing and is fine:
   `set_grid(projectId, limit: 0)` for the counts, then pages with `discipline` + `limit`/`offset`,
   which is exactly what step 10 does when it needs every row. Reach for that when you genuinely
   need the whole grid, not to verify this write.
3. **Verify typing coverage against the recognized count, not just pages.** Sum `sheetsGrounded`
   across every file's succeeded job for this delivery (from step 5) to get the recognized sheet
   count in scope. Compare it against the sum of the server's rule-typed count (`written.sheetTyping.
   typed` from step 6b's status read) plus your own agent-typed-plus-skipped count from step 6b: the
   sheets you assigned a `sheetType` entry to, plus the ones you counted as honestly unsure. The
   three should reconcile: recognized count = rule-typed + agent-typed + honestly-skipped. A gap
   between them, sheets neither typed by either author nor counted as skipped, means step 6b did not
   actually reach every sheet in scope: go back and close it before this run reports done, the same
   way a count mismatch in point 1 stops the run rather than getting waved through.

Raise any pages still unresolved or flagged image-only pages as questions with `ask_question`, and
report the plain untyped count: a person resolves them, not something this skill resolves itself.
<!-- user-facing -->
Report: the
project and delivery; the recognition run's counts (pages scanned, sheets recognized, how many were
high-confidence, how many were flagged for a closer look); how many sheet records were saved and how
many were already on file; the count of entries you added yourself for the sheets you reviewed and
typed, confirmed against what you sent; whether every recognized sheet in this delivery now carries a
type or an honest skip-count, naming the gap plainly if there is one; and that the set is now readable
on plumlayer.com with each sheet's source page behind it.
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
3. **Poll `extract_spec_toc_status(projectId, jobId)`** every ~3-5s under the same loop rule as
   step 5: the only exits are `succeeded`, `failed`, or `stale`, never the clock or your own
   judgment. On `failed`, read `error`, report it, and retry only when the error names something a
   retry changes. On `stale`, re-call `extract_spec_toc` on the same file set to restart. Any report
   of where the job stands quotes the last payload received and its time.
4.
<!-- user-facing -->
**Report the counts honestly, not just "N sections found."** From the succeeded job's `report`:
   sections found, files opened vs failed (a multi-file run can succeed overall while still naming one
   corrupt division PDF in `failedFiles`: that's a finding for the user, never a silent retry
   loop), and the completeness-diff, mismatch, and could-not-read counts. **`sectionsFound` counts only
   footer-confirmed sections** (the per-page CSI-code footer read). The reader also reads the
   manual's own table of contents: `tocDeclaredCount` is what it lists, `tocPagesRead` the pages it
   read, and `tocOnlyCount` the sections the table of contents names that no page footer confirmed.
   Those are recorded as sections too, cited to the line of the table of contents they came from,
   with a status saying no section text was found; say them as their own number ("110 confirmed,
   12 more listed in the table of contents with no section text found"), never folded into the
   confirmed count and never dropped. An outline specification with no footers at all, common at
   schematic and design development, comes back as `sectionsFound` 0 with every section in
   `tocOnlyCount`; that is a complete read of that manual, not a failure. `tocBackstop.requested`
   true means the table of contents could not be read as a list and `tocRejectedCount` says how
   many lines were refused: say so, and read the table of contents pages yourself with
   `render_page` before trusting any section count. A section declared solely in the PDF bookmark
   tree, with no confirming footer, does NOT add to any count; it surfaces through the completeness
   findings, never as a silent gap in the number you report.
<!-- /user-facing -->
5. **Verify.** Call `search(projectId, predicate: "inDivision")` and confirm the recorded row
   count equals the job's `sectionsFound` plus `tocOnlyCount` exactly (`tocOnlyCount` is 0 when
   the report does not carry it): completeness and
   could-not-read findings ride their own predicate (`hasCompletenessStatus`) and never appear in
   this read. A mismatch stops the run and gets reported, never a guessed correction.

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
   index page(s) and record each listed sheet as a cited `declaredInIndex` entry. It reads from
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
   - What couldn't be read: `report.openItems.parseRejectedSample` and
     `report.openItems.unparsedPages` name the tokens and pages this run could not account for; state
     those counts out loud rather than folding them into "no problems found."
   - Whether the index re-read agreed with the stored records: check `report.declaredLedgerDrift.ran`
     first. It's `false`, never a hollow zero, whenever no index page could be read at all, or a
     receiving-check run had to widen its re-read to another delivery's pages; the drift arrays are
     empty in that case too, and that's a check that didn't run, not a check that found nothing.
   - Whether the spec comparison ran at all: when step 8 found no project manual to extract for
     this delivery, the spec leg is reported as not having run. Say exactly that; never present it
     as a finding of zero.
<!-- /user-facing -->
4. **Record the findings.** Once you have shown the report, call
   `reconcile_set(projectId, record: true)` to record the sheet findings and the grouped questions
   for the design team (grouped by discipline series, not one per sheet), and say what landed. This
   is the project's own review queue, internal work: it needs no go-ahead, and the user corrects
   anything wrong on the site.

## 10. Close out

Point 3 runs on every path through this skill. Points 1 and 2 run on the full-re-issue path only.

1. **The full-re-issue finding.** Run this on the baseline path, and only when a prior delivery
   existed; on the project's first delivery there is nothing to compare against (step 1b), so say
   that instead of reporting an empty finding. Read the set back from the record:
   `set_grid(projectId, limit: 0)` first for `count` and `disciplineCounts`, then page with
   `discipline` + `limit`/`offset` until the rows you hold cover the count. Never a bare call: its
   default first page is not the set. Every row carries the delivery governing it (`deliveryId`,
   `label`, `kind`). The lingering sheets are the rows whose governing delivery is not this one:
   sheets the prior set carried, this re-issue did not, and the server still shows as part of the
   current set. Report `currentSetStatus` / `currentSetNotes` for any row the resolver could not
   settle rather than folding it into the list. If the paging could not be completed, say so and say
   how far it got; a partial list is never put up as a complete one.
<!-- user-facing -->
   Give the user the list with the criterion that produced it said out loud: these are the sheets
   still showing as part of the set that came in on an earlier delivery, not on this one. Name them
   by sheet number.
<!-- /user-facing -->
2. **It is a report, nothing more.** This skill does not retire, replace, or write anything about
   those sheets, on any path.
<!-- user-facing -->
   Say plainly that they still show as part of the set and that nothing here changed or removed
   them, rather than wording it so it sounds like the run acted on them.
<!-- /user-facing -->
3. **The handoff.**
<!-- user-facing -->
   Name what comes next: reading what this delivery changes in the scope list. Say plainly that it
   is not available yet, rather than leaving the user waiting on it.
<!-- /user-facing -->

## Gates (non-negotiable)

- **The whole skill runs in the conversation.** No step is handed to a background agent or a
  subagent; a job is polled here until the server ends it, and every report of a job's state
  quotes the last payload received and its time.
- **Run, or stop and report; never create a consent step.** The user's decisions are the ones
  named at the top of this file; everything else is the skill's own work. A failure is reported
  with its error, retried only when the error names what a retry changes, and never put to the
  user as a choice of retry strategy.
- **Sheet typing is unskippable, on every door this skill supports.** A run through this skill
  (a fresh baseline, a bulletin or partial revision, the cloud-resident re-recognition branch in
  1c, or a corrected re-read once a force-re-recognize path exists) never reaches its closing
  report while a recognized sheet in scope has had no typing attempt at all. "Unsure, so left
  untyped and counted" is a valid outcome; "never looked at" is not, on any path, including one
  where `recognize_sheets` came back already-succeeded with nothing new to write. Step 6b is where
  every door converges before this skill calls a delivery done, not an optional refinement bolted
  onto recognition.
- Every entry's evidence is grounded **cloud-side**: a succeeded `recognize_sheets` job (recorded by
  the server) or a `render_page`/`get_page_text` read you just made. A local read (step 2) may inform
  the packaging report; it never grounds an entry.
- Discipline is derived from the sheet's own number prefix, never a filename or folder.
- Every page the pass could not name is judged or flagged, never silently dropped; image-only pages
  are named, not guessed.
- `sheetType` typing splits across two authors: the server's deterministic rule pass types with a
  citation at recognition, and the agent types the sheets it left untyped. Never a value outside
  the 13-value vocabulary; never assigned to a sheet you're not confident about; never a bare
  re-record over a rule-typed sheet (correct it by supersession edge, per 6b); unsure stays untyped.
- A confident correction of a machine misread (a mis-grabbed title or discipline, in that tail or on an
  already-recognized sheet) is a supersession **edge** onto the stored entry (`supersedesId` from
  `search`), never a bare competing entry and never a question raised with `ask_question`: reserve
  that for a reading you genuinely cannot resolve.
- The page entries and your own type entries (the leftover sheets and any correction) are your own reading,
  cited to the page you read; never present them as the deterministic pass's confirmed output, and
  never present a rule-typed sheet as your own read.
- Your own write (the page + type bundle) is verbatim, count-verified transport: a count
  mismatch stops the run, never triggers a reconstructed or invented entry.
- Before recording your page/type bundle, check for a prior write on this delivery and confirm
  with the user rather than double-recording; the recognized portion is server-idempotent by
  construction (re-running `recognize_sheets` on the same file+delivery is always safe).
- Honest coverage at every stage: pages skipped, files excluded, unnamed pages left unread, or sheets left
  untyped are named, not buried in a total.
- Every list of sheets you put in front of the user names the criterion that produced it (left
  untyped, index title disagrees with the title block, delivered but not listed) and is read back
  from the record, never recomposed from an earlier report. Two lists built on different criteria
  are different lists: when a later one overlaps an earlier one, say which sheets are in both and
  which are in only one. Never call them "the same" from memory. A private judgment that resolves a
  difference you noticed is still a finding the user has not seen; report the difference, not your
  resolution of it. (A close-out once named a sheet among five title disagreements, then the next
  report named it among five untyped sheets and called the two lists "the exact same 5"; both lists
  were right on their own terms and the narration was wrong.)
- The spec-book leg (step 8) extracts a file set once, never once per division file, and its counts are
  read back with `search` and verified against the job's own `report`, never assumed. A named
  `failedFiles` entry is a finding for the user, never a silent retry loop.
- The reconciliation gate (step 9) is honest about its own bounds: no classified index page, a
  backstop, or an unread spec manual are named as what didn't run, never paraphrased into "no
  problems found." `reconcile_set` findings are recorded without asking, and the report says what landed.
- **The step 10 lingering-sheet list is a complete paged read, not a first page.** It comes from
  `set_grid(limit: 0)` followed by pages until the rows cover the count, and its criterion (the
  sheet's governing delivery is not this delivery) is stated with the list. Paging that could not be
  completed is reported as incomplete, never presented as the whole set.
- **This skill never retires or supersedes a sheet the delivery did not carry.** A full re-issue
  that drops sheets produces the step 10 finding and nothing else: no retirement, no supersession
  edge, and no entry authored about the dropped sheets, on any path.

## Deferred (named, not skipped silently)

- **OCR for image-only/scanned pages.** No text layer means both the bulk pass and your own read come
  up empty; flag, don't guess.
- **Scale auto-detect at intake.** Not built into this skill yet.
- **Master-list reconciliation as corroboration only.** A full diff against an architect drawing list
  (to surface RFI-worthy discrepancies) is a corroboration layer, never the bootstrap for this skill.
- **Discipline-uncertainty compensation.** The server's prefix-based discipline derivation has a known
  gap for unusual prefixes; this skill does not add client-side heuristics to cover it.
- **Backfill typing for sets recognized before the server-side rule pass.** Server-side typing now
  runs at recognition for every door, including the web-only upload door (a website-only upload has
  no agent in the loop, but the rule pass runs regardless). What remains deferred is typing the
  sheets from deliveries recognized before this pass existed, tracked separately, not this skill's problem to
  solve on its own.
