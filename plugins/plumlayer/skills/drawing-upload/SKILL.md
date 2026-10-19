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

Doctrine binds every stage: agents read and judge; deterministic tooling grounds; nothing enters
untraced. Every entry in this pipeline takes effect as soon as it lands, carrying who wrote it and
what they read from: the recognition pass records what it confirmed off the page, and what you judge
yourself records as your own reading, cited to the page you read it on. You are the reader; the MCP
recognition verbs (`recognize_sheets`, `recognize_sheets_status`, `render_page`, `get_page_text`) are
the anti-hallucination anchor, not the inference engine. There is no local pipeline and no
server-side autonomous *reader*: the server runs the deterministic bulk pass, which also types most
sheets by a rule match, and records its own output, but you still drive every job, judge every page
the pass could not name, type the sheets the rule pass left untyped, and author every entry that
isn't the deterministic pass's own grounded output.

Independent of recognition, every PDF this skill uploads starts having its own text read the
moment it registers; there is nothing to trigger. `set_text_status` says how much of a fresh
upload has been read, and a `scope-run` or `takeoff` pass starting right after an upload should
check it before leaning on `search_set_text`, since a page nobody has read yet cannot be found there.

This skill runs the read cloud-first: recognition and every recorded entry come from the server or
your own read of the cloud-hosted pages, never from a local pass. Examples in this file are generic;
never put a real client or project name here.

This skill runs in the conversation, start to finish. No step of it is handed to a background
agent or a subagent: there is no named agent for this work, and an improvised one cannot take the
user's answers or report a job's state first-hand. A long recognition job is waited on here, in
the open, with the poll loop in step 5.

Run, or stop and report; never create a consent step. The user's decisions in this skill are:
which project this delivery belongs to, its issue label, which files are the drawings when the packaging leaves it
genuinely unclear, and whether to send a page and type bundle again when a prior one is on file.
Ask each of those once, in plain words, and where you already have a reading (off a cover sheet,
off the file list) put it forward as the answer with its source named, so the user corrects it
rather than composes it. Everything else the skill does is its own work, recorded with who did it
and when, and editable afterward. Never stop to collect approval for a course you have already chosen, and
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
- "re-reading the N open questions on the changed sheets" (step 9b)
- "the set uses N discipline codes outside the standard list; I found the set's own name for K of
  them" (step 6d)
<!-- /user-facing -->

## What this is, and the boundary

`drawing-upload` does one thing: take a drawing delivery and register every sheet in it as
cited entries in the project's project record. The canonical form is entries + provenance over the
untouched original delivery. Discipline organization, by-discipline PDFs, and page labels
are all **projections** of that form, rendered on demand by other skills, never the foundation. So this skill does not: physically split files by discipline (discipline is derived
per sheet, never from a filename); produce a CSV (the deliverable is entries in the project record;
the app keeps discipline PDFs fresh on its own under Assembled set on Documents); scope, take off, or comprehend the sheets (`scope-run` / `takeoff` / `learn-project`); or create
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

## 1b. Set or addendum: the server's answer

You never ask the user whether a delivery is a new set or an addendum, and you never decide it
yourself. Once its sheet numbers are read (step 5), the `issue` that `list_drawing_deliveries`
gives the delivery says which it is: walking the deliveries in order, the first one holding sheets
is a set, a later one printing fewer sheet numbers than the latest set is an addendum of that set,
and any other is a new set. `issue` is null while its sheet numbers are still being read, so read
it after step 5, and steps 9b and 10 branch on it.

The server combines the deliveries by sheet number either way, and for each sheet the newest
delivery that carries it wins: a sheet an addendum does not carry keeps showing from the delivery
that last issued it, and so does a sheet an earlier set had that a new set does not carry. Step 10
reads those sheets back and reports them as a finding. Nothing is retired, here or anywhere else in
this skill.

Step 3 registers the delivery with `deliveryKind: "baseline"` where `list_drawing_deliveries`
comes back empty, the project's first delivery, and `"revision"` for any later one. That field
only orders deliveries that share an issue date and a sequence; it says nothing about whether the
delivery is a set or an addendum.

**The project's first delivery** is a set by that rule, and step 10's comparison has nothing to
compare against on this path, and says so plainly rather than reporting an empty finding.

**An already-registered delivery** (the 1c branch below): its `issue` reads off
`list_drawing_deliveries` like any other's.

**A project manual arriving on its own**, with no drawings: this is not a drawing delivery. Register
nothing, skip steps 3 through 7, and enter at step 8, which files the manual and reads its table of
contents. Step 9 still runs, and its drawing legs report as unchanged because no sheet changed.
Step 9b re-reads the open Questions citing the sections the new manual carries. Say in the closing
report that no drawings came with it.

## 1c. Cloud-resident entry (files already in the project, nothing local)

A file with no delivery attached to it needs one registered, as step 3 says, before step 5 reads
its sheet numbers; whether that delivery is a set or an addendum is the server's answer after.

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
filed into the project and read by step 8 below, not simply excluded. Genuinely out-of-scope files
(geotech reports, RFP boilerplate, transmittal emails, meeting minutes) stay excluded.

**Dual-source repackaging:** when a delivery contains both a combined PDF and a full set of per-sheet
PDFs, check page totals first. If the per-sheet PDFs' combined page count equals the combined PDF's page
count, that's duplicate repackaging of the same set, not two sources: prefer the single combined file
and don't recognize both; recognizing both wastes a full pass and risks recording the same sheets
twice under different `fileId`s. Only treat it as genuinely unclear when the totals disagree or
there's no clean 1:1 correspondence.

For any other genuinely unclear packaging (a mixed bag, or a dual-source case the page-total check
didn't resolve), use the Read tool directly on a few local candidate pages of each file to judge
title-block grammar vs spec-prose and pick which one to use. This local sampling is
file-selection judgment only: it decides which local files you upload next; it never grounds an
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

- `deliveryKind: "baseline"` for the project's first delivery and `"revision"` for any later one,
  as step 1b says; never put the question to the user.
- `label`: the human issue label from step 1.
- `issuedOn` (`YYYY-MM-DD`) and `sequence`: read these off the documents themselves (a cover sheet, a
  bulletin header). Never substitute upload time: chronology drives supersession resolution.
  **When issue-date signals disagree** (the filename says one date, a cover sheet or transmittal says
  another), the drawing set's own revision table governs `issuedOn`: it's the
  architect's own record of the issue, ahead of a filename someone typed or a transmittal cover letter.
  Note the disagreement in the packaging report rather than silently picking one.

Every file you upload in step 4 attaches to this one `deliveryId`.

## 4. Upload bytes

**A single-file delivery** keeps the existing single-file verbs:

1. `request_file_upload(projectId, filename)` → `{fileId, path, bucket, token, signedUrl}`. The server
   creates `fileId` and the storage path; you never supply either.
2. PUT the raw file bytes to `signedUrl` with a `Content-Type` header (the bytes never pass through a
   tool call):
   ```bash
   curl -X PUT "$SIGNED_URL" -H "Content-Type: application/pdf" --data-binary @"$LOCAL_PDF_PATH"
   ```
3. `register_file(projectId, fileId, filename, contentType, kind: "drawing", deliveryId)`: always pass
   `kind: "drawing"` and `deliveryId`. The kind files it as a drawing at once, so section 5 can read its
   sheets; without it the server sorts the file first. The delivery makes chronology come from the
   delivery, not upload order. Idempotent: a retried call for the same
   `fileId` returns the existing row. Rejects `not_found` (PUT didn't land), `empty`, or `oversize`
   (2 GB ceiling per file): if any of these fire, stop and report rather than retrying blindly.

**A delivery of two or more files** uses the bulk verbs instead: one signing call, one upload loop,
one recording call, rather than one round trip per file. Above 250 files, split the batch into
calls of at most 250:

1. `request_file_uploads(projectId, filenames)` → `{count, uploads}`, one `{filename, fileId, path,
   bucket, token, signedUrl}` per file, in the order you sent the filenames. All or nothing: a
   failed call returns nothing and nothing was uploaded, so send it again. The server creates every
   `fileId` and storage path; you never supply either.
2. Write the returned `uploads` list to a local JSON file once, then PUT every file's bytes in a
   single shell loop that reads `filename` and `signedUrl` back out of that file with `jq` or a
   small node one-liner, so no signed URL is ever retyped by hand per file:
   ```bash
   jq -c '.uploads[]' uploads.json | while read -r row; do
     filename=$(echo "$row" | jq -r '.filename')
     url=$(echo "$row" | jq -r '.signedUrl')
     curl -X PUT "$url" -H "Content-Type: application/pdf" --data-binary @"$LOCAL_DIR/$filename"
   done
   ```
3. `register_files(projectId, files, kind: "drawing", deliveryId)`: pass every file's `{fileId,
   filename, contentType?}`, `kind: "drawing"`, and the same `deliveryId` from step 3, so chronology comes from the delivery, not
   upload order. Answers per file, never all-or-nothing: `{registered, failed, counts}`.
   `counts.registered` must equal the number of files you sent. Anything in `failed` names its
   `fileId`, `filename`, `reason`, and `message`: re-PUT and re-register only those files, by
   `fileId`, never the whole batch again, and never blindly. A `reason` of `not_found` (the PUT
   didn't land) is worth that retry; any other reason is stopped and reported.

Either path, no local run folder and no manifest file: the project files list (`list_files`) is the
record.

## 5. Recognize sheets (async, start then poll)

Call `register_pages(projectId)` once for the project: it registers viewable page rows for every
uploaded PDF (not entries, just renderable pages) and only needs to run once per project, not per file.

Then, once per file, call `recognize_sheets(projectId, fileId, deliveryId)` to start the
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
  fix before it will recognize, and stop. A failed job is reported in the conversation, never
  written into the project as a Question: a Question is about the project, never about a
  Plumlayer failure.
- `succeeded`: the recognized sheet entries (`appearsOnPage`, `hasTitle`, `locatedAt`, `discipline`,
  `partOfIssue`) are already recorded server-side. This result never carries
  those entries and you never `record_batch` them yourself: that would double-write every sheet. Report
  the run-level counts from `report`: `pagesScanned`, `sheetsGrounded`, `highConfCount`, `flaggedCount`,
  `extractionWarningCount`, `calibrated`, `capHit`. Never assume "N pages scanned = N sheets recognized":
  state both numbers. `confidence` on individual entries (visible later via `search`/`set_grid`) is
  triage/review-priority metadata only: it tells you which sheets to check first and ranks nothing.
- On a `succeeded` pass, `written.enteredValuesKept` lists the pages where the pass read nothing but a
  sheet number, title, discipline, or type that a person or an agent entered still stands. The pass
  left each one as it is. When `pages` is above zero, name those pages to the user with the value
  kept on each, and ask whether each one is right. Never correct one yourself.
- On a `succeeded` pass, `written.laterIssueKept.sheets` counts the sheets where a newer drawing
  issue already holds the title, discipline, or type this pass read, so this pass wrote none of them.
  When it is above zero, tell the user this issue was read after a newer one and that the newer
  issue's values stand on those sheets. Do not record this issue's values over them.
- `report.pagesUnread` lists pages the pass did not read at all (each such `unnamedPages` row says
  why in `unread`). Those pages are not in `enteredValuesKept`; read them yourself in step 6.

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
  `get_page_text` returns exact spans with PDF-point bboxes; a page without a text layer is read by
  OCR and `textSource` says so, and spans are empty only when `textSource` is `none`.
- Judge the sheet number, title, and discipline from what you actually see, and handle the two cases
  differently:
  - **A confident correction of a machine misread**: you can see the reader grabbed the wrong cell (a
    tag instead of the sheet number, a boxed note instead of the title). If the recognizer already
    stored a value for that slot, write your corrected value as a supersession **edge** onto it:
    `search(projectId, subject: "sheet:<n>", predicate:
    "hasTitle"|"discipline"|"appearsOnPage")` to get the live entry's `id`, then author your corrected
    entry with `supersedesId` set to that id, cited to the crop you read. The edge is what makes your
    read the current value: the record refuses a write onto a filled slot that names nothing, which is the
    record's own rule for an occupied field. If the slot is empty (the pass
    left this page blank), just author the entry fresh: there is nothing to supersede.
    A misread sheet number itself is corrected with `renumber_sheet` (project-record skill), which
    moves what was recorded on the sheet under the right number; never author a second sheet under
    the right number beside the misread one.
  - **Genuinely unclear**: you honestly cannot tell which of two readings is right. Author your reading
    as a bare entry, cited to what you read, and name it to the user in the step 7 report, with both
    readings, so a person settles it; never silently pick. Which of two readings of our own sheet
    title is right is our reading of the set, not a Question for the design team. Name only a real
    toss-up; never a correction you are confident about (that just hands a person a title you
    already read correctly).
- **Image-only / scanned pages**: flag them honestly. Create the page as its own subject:
  `page:<fileId>:<pageInPdf>`, never `subject: null`, and never add an OCR dependency (deferred).
  Report the flagged page list; an honest "could not recognize these N pages" beats a guess.

**A number another drawing issue already prints.** Before you write a bundle, look the number up
(`set_grid`, or `search(projectId, subject: "sheet:<n>", predicate: "locatedAt")`). When an earlier or
later drawing issue already places that number, do not write `appearsOnPage`, `locatedAt` or
`partOfIssue` for it with `record`, and never name the other issue's location as the entry your write
replaces: that takes the other issue's page off the record. Call `renumber_sheet` with
`sheetNumber` set to the page row's number from `set_grid` and `newSheetNumber` set to the number
you read. The page becomes that number's page in its own drawing issue: the newest issue's page is
the current one, and the other issue's page stays on record as replaced. Then write `hasTitle` only
when the title you read differs from the number's current one, naming that entry in `supersedesId`.
When the page's own issue already places the number on another page, the verb refuses and names
that page: the two pages print the same number, so report both to the user rather than picking one.

**Two numbers on one page.** When `set_grid` shows a page carrying two numbers and you read the
title block yourself, a number the page does not print is a misread: take it off that page with
`remove_sheet_from_page(projectId, sheetNumber, fileId, pageInPdf, reason)`, the reason naming what
the page prints. `renumber_sheet` refuses there, because the right number already stands on the
page. Remove only a number you have read the page not to print, never one that also prints on that
page, and report each removal; a number that stands on other pages stays on them.

For every other page you resolve, author the full bundle of entries, mirroring the shape the
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
evidence block cites the render or text span you actually read. A bbox is a text span's own box,
never one measured off a render; a read that came off a render alone carries `locator: null`.

**Discipline convention:** derive strictly from the sheet number's own leading letter run, matching the
server's `disciplineFromSheetNumber` logic (all letters before the first digit/dash, uppercased);
never a full NCS discipline name. A prefix outside the standard list stays as its letters, and
step 6d reads the set for that code's name; a sheet with no readable prefix at all is read from
its page in step 6d.

**Gate:** every page in that tail ends up judged (a full entry bundle) or flagged (image-only or genuinely
unreadable); never silently dropped. State how many you read, corrected, and flagged.

## 6b. Type the sheets

Recognition itself now types most of the set: at `recognize_sheets` finalize, the server runs a
deterministic rule pass over every newly recognized sheet, matching its sheet-number prefix or
recognized title against the 13-value vocabulary below. A match writes a `sheetType` entry
server-side, written by the recognition pass, cited to the matched title words, with a `confidence` of
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
`supersedesId` set to it, cited to what you actually read. With that edge, your read becomes the
sheet's type the moment it lands.

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
`"agent-vision-read"` when you rendered the page to decide, its `locator` as the full bundle above
says. `value` must be one
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
edge, exactly like a confident step 6 correction:

1. `search(projectId, subject: "sheet:<n>", predicate: "hasTitle")` (or `"discipline"`) → the live
   machine entry's `id`.
2. `render_page` the title-block corner and read the real title yourself.
3. Author the corrected entry with `supersedesId` set to that id, cited to the crop you read, and pool
   it into your step 7 write.

A write onto a field that already holds a value names the record it replaces. Your corrected entry
becomes the sheet's title or discipline the moment it lands, whoever wrote the value it corrects,
and the recognizer's entry stays in the record beneath it. A corrected entry with no `supersedesId`
is refused, and the refusal names the current record. Never raise this as a question: a reading
you cannot resolve is named to the user, and asking about a title you already read correctly is
the "go set it on the site" dead end this step exists to close.

<!-- user-facing -->
Say it the way it happened: "the automatic scan grabbed the wrong text on N sheets, so I read them
and set them right".
<!-- /user-facing -->

## 6d. Name the discipline codes off the standard list

The server holds one standard discipline list (the letters the trade uses, each with its word: `A`
Architectural, `D` Demolition, `LT` Lighting, and so on), and every sheet list heading reads that
word. A code off the list (`ES`, `SI`, `X`, `FD`) reads its bare letters until the set names it.
This step reads the set for those names. A sheet whose number carries letters keeps its letters as
its discipline: never supersede it onto a standard code. Only a sheet whose number carries no
letters at all gets a per-sheet read.

1. **Find the codes.** `set_grid(projectId, limit: 0)` and read `offListLetters`: the codes the
   set's sheets carry that the standard list has no word for and that nobody has named yet. The
   list comes from the server; carry no copy of the standard list here.
2. **Read the set's word for each code.** Read the drawing index (`get_page_text` or `render_page`
   on the index sheet) and that series' sheet titles off `set_grid(projectId, discipline:
   "<code>")`. The set's word is the index heading printed directly over that series' rows. When
   the index has no heading over them, it is a discipline word every title in the series opens
   with ("SECURITY ...", "LIGHTING PLAN ..."). Otherwise leave the code unnamed. When the index
   heading and the titles disagree, take the index heading; which heading our own sheet list uses
   is ours to settle, not a Question for the design team.
3. **Record each word.** One entry per code, pooled into the step 7 batch write: subject
   `project`, predicate `disciplineName:<the code>`, value the word in sentence case (SECURITY is
   recorded as Security), `sourceInstrument: "drawing-delivery:<deliveryId>"`, and evidence
   `{"method": "agent-read", "fileId": "<fileId>", "pageInPdf": <the page that prints the word>,
   "snippet": "<the words exactly as printed>"}` (a `sheet` in place of `fileId` also cites the
   page). To change a name already recorded, name the entry it replaces with `supersedesId`. The
   record refuses a name for a code on the standard list and a name with no page. A word that
   matches a standard word ("ARCHITECTURAL" over `EX` sheets) is recorded all the same; the heading
   then joins the standard one.
4. **Never invent a name.** No write for a code the set does not name, and never a name worked
   out from the letters. An unnamed code reads its letters, and the estimator can name it.
5. **Sheets with no letters.** For each sheet `set_grid` files under `Unknown` (its number starts
   with no letter, or carries none), read the page, never the PDF file name or folder:
   `render_page` the title-block corner and/or `get_page_text` the page (`fileId` + `pageInPdf` off
   the row). Evidence that settles a discipline, strongest first: a discipline caption printed in
   the title block itself (e.g. "CIVIL"); the sheet's own title and content (a turning plan or an
   overall site plan is civil); the drawing index listing the sheet under a discipline heading,
   cited to the index page. Write a standard code (`C`, `L`, and so on): `search(projectId,
   subject: "sheet:<n>", predicate: "discipline")` for the live entry's id, then a `discipline`
   entry with `supersedesId` set to that id, `sourceInstrument: "drawing-delivery:<deliveryId>"`
   and `versionScope: "<issue label>"` (both off the row: this tag is mandatory, a write without it
   is ignored by the grid and can blank the field), and evidence `{"source":
   "<fileId>/page/<pageInPdf>", "method": "agent-vision-read", "snippet": "<the words you read>",
   "locator": {"frame": "pdf-points", "bboxPts": [...]}}` when the read came off a text span you can
   box, `locator: null` when it came off a rendered crop you judged by eye. When nothing on the
   page or in the index settles it, leave `discipline` alone and name the sheet to the user with
   what you read.

**Gate:** every code in `offListLetters` ends the step named with a citation or reported as one the
set does not name, and every sheet with no letters ends recorded with a citation or named to the
user. State the counts.
<!-- user-facing -->
"The set uses N discipline codes outside the standard list; I found the set's own name for K of
them, and J show as their letters until you name them. M sheets had no letters in their number; I
read the pages and filed K of them, and J need you."
<!-- /user-facing -->

## 7. Record the pages and types, then verify

**The recognized portion needs no write call from you.** `recognize_sheets` already wrote it
server-side once its job succeeded (step 5), and re-running `recognize_sheets` on the same
file+delivery is safe by construction: the concurrency guard returns the existing job, and the
write itself is idempotent (`alreadyWritten: true` on a poll means a prior run already wrote this
delivery's sheet entries, no duplicate was written). You still make exactly one write of your own
(pooling the step 6 bundle, the sheetType entries from step 6b, any mis-bind
corrections from step 6c, and step 6d's discipline names and corrections, the edges carrying their
`supersedesId`), plus one verification pass:

1. **Record the page + type bundle.** Before recording, check whether you've already recorded
   these pages or types for this delivery in a prior run of this skill (e.g. `search(projectId,
   predicate: "partOfIssue", text: <deliveryId or label>)` and `search(projectId, predicate:
   "sheetType")`), and confirm with the user before sending it again; the server's recognized-entry
   idempotency does not cover entries you authored and sent yourself. Once clear, pool the full entry
   bundles you authored in steps 6, 6b, and 6c (recognized pages you did not correct contribute
   nothing here: do not re-send them) into one array per project.

   **For a small bundle, call `record_batch(projectId, entries)` directly.** It accepts 1–500
   entries and is atomic (one bad entry rejects the whole batch, naming the index); transport every
   entry verbatim, never re-typed from memory. **Verify**: the returned `count` must equal the
   number of entries you sent. If it doesn't, stop and report the discrepancy rather than retrying
   with a guessed correction.

   **For a large bundle you write (a deep set with thousands of page and type entries), use
   `record_batch_file` instead of chaining many `record_batch` calls.** The path: write the full
   entry array as JSONL, `request_file_upload(projectId, filename)` for a signed URL, PUT the JSONL
   bytes to it, `register_file(projectId, fileId, filename, contentType: "application/jsonl", kind:
   "batch")`, then call `record_batch_file(projectId, fileId)` to write straight from the
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
   you saw>")` calls. That spot-check is this step's verify. What to avoid here is a bare,
   unpaged `set_grid` call: on a set with hundreds of sheet rows it returns on the order of 600 KB
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

Report any pages still unresolved or flagged image-only, by page number, in the conversation
rather than raising them as Questions on the project record, and report the plain untyped
count: a person resolves them, not something this skill resolves itself.
<!-- user-facing -->
Report: the
project and delivery; the recognition run's counts (pages scanned, sheets recognized, how many were
high-confidence, how many were flagged for a closer look); how many sheet records were saved and how
many were already on file; the count of sheet records you added yourself for the sheets you reviewed and
typed, confirmed against what you sent; whether every recognized sheet in this delivery now carries a
type or an honest skip-count, naming the gap plainly if there is one; any sheet title left between
two readings, with both readings and the sheet named, for them to settle; and that the set is now readable
on plumlayer.com with each sheet's source page behind it.
<!-- /user-facing -->

## 8. Extract the spec book's table of contents

When step 2's packaging pass turned up a project manual / spec book, file it and read its table of
contents now, before the reconciliation gate below. The gate's spec-comparison leg needs this layer to
run against; reconciling first always reports the spec leg as not having run, even when a manual sat on
disk the whole time.

1. **File it as a document.** Run the same upload mechanics as step 4 for the manual PDF(s) step 2
   identified: a single manual PDF uses `request_file_upload`, PUT the bytes to `signedUrl`, then
   `register_file(projectId, fileId, filename, contentType, kind: "document")`; two or more (a
   folder-of-divisions manual) uses `request_file_uploads`, the same PUT loop, then
   `register_files(projectId, files, kind: "document")`, with the same `counts.registered` check and
   the same per-`fileId` retry on anything in `failed`. A project manual is a project record, not a
   drawing sheet, so it does not attach to a `deliveryId`. Misfiled earlier as a drawing? Fix it in
   place with `update_file(projectId, fileId, kind: "document")` rather than re-uploading:
   reclassifying away from `drawing` sweeps its stray page rows in the same call.
2. **Filing starts the read; ask for its job one file at a time.** `register_file`, `register_files`,
   or `update_file` to `kind: "document"` starts one spec section read per document PDF on the server,
   held about two minutes so drawing recognition filed alongside it goes first. For each filed file,
   call `extract_spec_toc(projectId, fileIds: [<that one fileId>])`: it returns the read filing
   started (`alreadyActive: true`) rather than starting another, and that is the `jobId` to poll.
   Never pass several `fileIds` together. A folder-of-divisions manual (`Division 01.pdf`,
   `Division 02.pdf`, ... instead of one bound manual) is one read per division file, each with its
   own `jobId`; nothing joins them, and two files holding the same section follow latest write like
   any other slot. A file that is not a PDF gets no read. A failed or stale read starts again on the
   same call. You repeat a finished read only when the user asks to read a manual again, by passing
   `reread: true` with that one `fileId`: a value the user entered on a section stays unless you now
   read that section differently than the last read did, and the status's `written.reread` counts
   say what you replaced, kept, and no longer found. Report those counts to the user.
3. **Poll `extract_spec_toc_status(projectId, jobId)`** every ~3-5s under the same loop rule as
   step 5: the only exits are `succeeded`, `failed`, or `stale`, never the clock or your own
   judgment. On `failed`, read `error`, report it, and retry only when the error names something a
   retry changes. On `stale`, re-call `extract_spec_toc` on that one `fileId` to restart. Any report
   of where the job stands quotes the last payload received and its time.
4.
<!-- user-facing -->
**Report the counts honestly, not just "N sections found."** One line per filed file, from its
   succeeded job's `report`: sections found, and the completeness-diff, mismatch, and could-not-read
   counts. A single-file read that could not open its file never reaches `succeeded`: it fails with
   the reason, which is a finding for the user, never a silent retry loop. `sectionsFound` counts only
   footer-confirmed sections (the per-page CSI-code footer read). The reader also reads the
   manual's own table of contents: `tocDeclaredCount` is what it lists, `tocPagesRead` the pages it
   read, and `tocOnlyCount` the sections the table of contents names that no page footer confirmed.
   Those are recorded as sections too, cited to the line of the table of contents they came from,
   with a status saying no section text was found; say them as their own number ("110 confirmed,
   12 more listed in the table of contents with no section text found"), never folded into the
   confirmed count and never dropped. An outline specification with no footers at all, common at
   schematic and design development, comes back as `sectionsFound` 0 with every section in
   `tocOnlyCount`; that is a complete read of that manual, not a failure. `tocBackstop.requested`
   true means no page footer printed a section number and no table of contents was found in the
   opening pages: say so, and read the opening pages yourself with `render_page` before reporting
   any section count. A table of contents the read could not take whole ends the job `failed`,
   with the reason in `error` naming its pages, and saves no section from that file: report the
   reason as a finding and do not retry, since a second read fails the same way. A section declared solely in the PDF bookmark
   tree, with no confirming footer, does NOT add to any count; it surfaces through the completeness
   findings, never as a silent gap in the number you report.
<!-- /user-facing -->
5. **Verify, per file.** For each read that succeeded with `written.alreadyWritten: false`, confirm
   `written.byPredicate.inDivision` equals that job's `sectionsFound` plus `tocOnlyCount` exactly
   (`tocOnlyCount` is 0 when the report does not carry it). A read whose `sectionsFound` plus
   `tocOnlyCount` is 0 found no spec sections in that file and wrote nothing: report that file as
   not a spec book, not as a failure. Then `search(projectId, predicate: "inDivision")` returns the
   sum over every read that wrote: completeness and could-not-read findings ride their own
   predicate (`hasCompletenessStatus`) and never appear in this read. A mismatch stops the run and
   gets reported, never a guessed correction.

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
     recognized, this stays with you to settle (the sheet may be on one of them); once every
     page is recognized, it becomes a question for the design team.
   - What's in the set the index doesn't list: checked first against the index page's own raw
     text (a table-reading miss on our side stays with you to settle; a genuine absence becomes a
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
   `reconcile_set(projectId, record: true)` and say what landed. Two things land: the sheet findings
   that stay with you to settle, and, for the side the design team has to answer, Questions on
   the board, each citing the index page and the sheets it is about. Those Questions are grouped by
   discipline series, not one per sheet, and a class spanning more than three series becomes a single
   project-wide Question naming the series and their counts. Read them back with `list_questions`.
   This is internal work: it needs no go-ahead, and the user corrects anything wrong on the site.

## 9b. Re-read the open Questions this delivery touches

A revised sheet can answer a Question somebody raised against the one it replaces, or move the
callout the Question points at. This step reads every open Question on what changed against the
new paper and says what it found on each one. It runs whenever a prior delivery or manual existed:
an addendum, a new set, or a manual on its own. On the project's first delivery there is
nothing earlier on the board to re-read, so skip it.

1. **Which sheets changed.** For a manual on its own, the sections step 8 read out of the new
   manual. For a drawing delivery, first read its `issue` off `list_drawing_deliveries`. Where it
   is null with `stillReading` false, the delivery holds no sheet number: `set_grid` refuses it and
   no sheet is known to have changed, so skip the rest of this step and go to step 10, whose
   handoff names it. Otherwise the changed sheets are the ones this delivery itself prints, each
   on its own page of it, read by its own id and never off the current set: an addendum uploaded
   after a later one is not the current set's page for any sheet the later one reprints, and it
   still changed that sheet. Take `set_grid(projectId, deliveryId: <this delivery's id>, limit: 0)`
   for the counts, then pages with `discipline` + `limit`/`offset`.
   - For an addendum, every row is a sheet it prints, on its own page.
   - For a new set, the grid joins the set with its addenda and gives each sheet the newest page
     that prints it. A row whose `deliveryId` is this delivery's is a sheet the set prints, on its
     own page. A row from one of its addenda is a sheet the addendum reprinted or added: find
     whether the set prints it too with
     `search_set_text(projectId, query: "<sheet number>", deliveryId: <this delivery's id>, wholeWord: true)`,
     which searches this delivery's pages only and names each hit's sheet number as this delivery
     printed it. A hit whose `sheetNumber` is that number is the set's own page of the sheet, by
     its `fileId` and `page`, and the sheet changed; with none, the addendum added the sheet and
     this set does not print it.
   Each changed sheet's `fileId` and `pageInPdf` are this delivery's page of it, which points 3
   and 4 read.
2. **Which Questions.** The `sheet` and `section` filters on `list_questions` read only the places
   the ask itself cites, and a reader that meets the same callout on a second sheet cites it in a
   reply, so a filtered read misses a Question that names a changed sheet only in a reply. Read the
   open Questions whole instead: `list_questions(projectId, full: true, limit: 10)`, paged with
   `offset: nextOffset` until `nextOffset` is absent. Keep every one whose ask or any reply cites a
   changed sheet (`sheet:<n>`) or a section the new manual carries (`specSection:<packed code>`).
   A place somebody took off the ask still sits in `sources`, one for one with `sourceRemovals`,
   which is null where the place still stands and names who took it off where it is gone. Skip
   every ask source whose `sourceRemovals` entry is not null, here and in point 3: a Question whose
   only citation of a changed sheet was taken off on purpose is not this step's, and never gets a
   new box put back. Reply citations are read as they are. That read also carries each kept
   Question's ask and every place it and its replies cite, which the points below work from.
3. **On a changed sheet, point the Question at this delivery's page too.** A source that names its
   drawing file opens on the page it was cited on, whatever later issue reprints the sheet; a
   source with no file opens on the page the current set shows for the sheet, at its old
   coordinates, which a moved layout leaves on nothing. Keep every existing source, either way,
   since taking one off is the estimator's call. For each `sheet-region` box or `sheet-point` on a
   changed sheet, in the ask (a standing source only) or in a reply, that names no file or another
   file than this delivery's: find the callout on this delivery's page, the `fileId` and
   `pageInPdf` on that sheet's row from point 1, with `search_set_text` its tag with `deliveryId`
   set to this delivery, whose hits carry boxes in the same PDF points, then `get_page_text(fileId,
   pageNum: <that pageInPdf>, region: <around the hit>)`. A whole-page `render_page(fileId,
   pageNum: <that pageInPdf>)` answers with `pageWidthPt` and `pageHeightPt`, for rendering a
   region where the callout is in the linework. Then `add_question_source` a `sheet-region` box
   around the callout there, built from the boxes `get_page_text` gave you for the callout's words,
   with `frame: "page-points"` and this delivery's `fileId`, so the Question opens on the new paper
   as well as the page it was raised on; the reply in point 5 says so. A render shows you where the
   callout is and never gives the box: where no word of the page's read carries the callout, add
   the sheet with no box (`{ "type": "sheet", "sheet": "sheet:<n>" }` with this delivery's
   `fileId`) and tell the user that sheet's text did not carry the callout.
   `add_question_source` is refused once a Question holds ten places. Never take one off to make
   room: cite the new box in the reply instead, and name that Question to the user as one with no
   room for another place on it.
4. **Re-read each one against the new paper.**
   - On a changed sheet: read the callout's text on this delivery's page, and search the ask's own
     tags and words with `search_set_text` and `deliveryId` set to this delivery, after
     `set_text_status` says the new pages have been read. Render further only where the change is
     in the linework, a cloud or a delta the text does not carry.
   - On a section of the new manual: a spec citation has no box and no sheet. Read the section's
     pages off its `locatedAt` (`search(projectId, subject: "specSection:<packed code>", predicate:
     "locatedAt")`), with `get_page_text` on the part the ask is about, and search the ask's words
     with `search_set_text` and `kind: document`.
5. **Three outcomes, and no fourth.**
   - The new paper answers it: work it as project-record's "When an answer arrives" says.
     `reply_question` saying what the revised sheet or section shows, citing it; tell the user
     what changed and that the reply may answer it, so he can have it pinned; and name the scope
     rows that cite the Question (`questions` on each `list_scope_items` row). Update
     those rows' values, citing the Question, only when he asks in this session; otherwise they
     are the scope pass's in step 10, which reads this delivery's sheets.
   - The new paper changed on the point without answering it: `reply_question` saying what
     changed.
   - Unchanged on the point: no reply, and it is counted in the report, unless point 3 added a
     box, when a reply says only where the callout sits on the new paper.
   A reply on a sheet cites a `sheet-region` box around what it read there, with this delivery's
   `fileId`, built as point 3 builds one, or the sheet with no box where point 3 says. A reply on a section cites the section, `{ "type": "spec", "section":
   "specSection:<packed code>" }`.
6. **Never close one, and never raise one here.** Closing is the estimator's: `close_question`
   only when the user settles it in this session, with their reason in `note`. No new Question
   comes out of this step; what the delivery changes in the scope list is still the handoff in
   step 10.

<!-- user-facing -->
Report: how many open Questions cite a changed sheet or section, how many got a reply, the ones
the new paper may answer with the scope rows each one moves, the ones you pointed at the new paper
too, any with no room for another place on it, and how many were unchanged on the point. Name each
Question by its title, or by its RFI number ("RFI 22") once it holds one. Say plainly that none
was closed and that settling one is theirs.
<!-- /user-facing -->

## 10. Close out

Step 9b's re-read of the open Questions is reported before any of this. Point 3 runs on every path
through this skill. Points 1 and 2 run only where the server reads this delivery as a new set.

1. **The new-set finding.** Run this where `list_drawing_deliveries` gives this delivery `issue:
   "set"`, and only when a prior delivery existed; on the project's first delivery there is nothing
   to compare against (step 1b), so say that instead of reporting an empty finding. Read the set
   back from the record:
   `set_grid(projectId, limit: 0)` first for `count` and `disciplineCounts`, then page with
   `discipline` + `limit`/`offset` until the rows you hold cover the count. Never a bare call: its
   default first page is not the set. Every row carries the delivery governing it (`deliveryId`,
   `label`, `kind`). The lingering sheets are the rows whose governing delivery is not this one:
   sheets the prior set carried, this new set did not, and the server still shows as part of the
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
3. **The handoff.** For a drawing delivery, read its `issue` off `list_drawing_deliveries` and
   name the scope pass for it, which `scope-run` runs: a new set gets a full pass over every sheet
   it prints, against the record the earlier passes built, and an addendum a partial pass over the
   sheets it prints, reviewing only the packages that pass writes on. A scope pass already underway
   on this project finishes first, and this delivery's pass comes after it. Two paths name no pass.
   No scope pass reads a project manual on its own: it registered no delivery, and the package
   reviews of the next pass read the sections it carries. A delivery whose `issue` is null with
   `stillReading` false holds no sheet number, so a pass would have no sheet to read: name it, say
   no pass reads it, and point back at what step 5 and step 6 found on its pages.
<!-- user-facing -->
   Name what comes next in one sentence: for a new set, a full scope pass over it; for an
   addendum, a partial scope pass over the sheets it prints. Say that `scope-run` starts it, and
   where a pass is already underway, that it finishes first. For a manual on its own, say no scope
   pass reads it alone, and that the package reviews of the next pass read its sections. For a
   delivery with no sheet number read, name it and say no scope pass can read it until its sheet
   numbers are read.
<!-- /user-facing -->

## Gates (non-negotiable)

- **The whole skill runs in the conversation.** No step is handed to a background agent or a
  subagent; a job is polled here until the server ends it, and every report of a job's state
  quotes the last payload received and its time.
- **Run, or stop and report; never create a consent step.** The user's decisions are the ones
  named at the top of this file; everything else is the skill's own work. A failure is reported
  with its error, retried only when the error names what a retry changes, and never put to the
  user as a choice of retry strategy. A failure is reported in the conversation, never written
  into the project as a Question: a Question is about the project, never about a Plumlayer
  failure. Question text is plain estimator words, and every Question meets the standard the
  `ask_question` verb states: a title, a citation for every place it names, and only what is worth
  the design team's time.
- **Sheet typing is unskippable, on every door this skill supports.** A run through this skill
  (a fresh baseline, a bulletin or partial revision, the cloud-resident re-recognition branch in
  1c, or a corrected re-read once a force-re-recognize path exists) never reaches its closing
  report while a recognized sheet in scope has had no typing attempt at all. "Unsure, so left
  untyped and counted" is a valid outcome; "never looked at" is not, on any path, including one
  where `recognize_sheets` came back already-succeeded with nothing new to write. Step 6b is where
  every door converges before this skill calls a delivery done, not an optional refinement bolted
  onto recognition.
- Every entry's evidence is grounded cloud-side: a succeeded `recognize_sheets` job (recorded by
  the server) or a `render_page`/`get_page_text` read you just made. A local read (step 2) may inform
  the packaging report; it never grounds an entry.
- Discipline is derived from the sheet's own number prefix, never a filename or folder. A prefix
  off the standard list keeps its letters and 6d records the set's own name for it, cited to the
  page that prints it, or leaves it unnamed; a number with no letters is read from its page in 6d,
  still never a filename or folder guess.
- Every page the pass could not name is judged or flagged, never silently dropped; image-only pages
  are named, not guessed.
- `sheetType` typing splits across two authors: the server's deterministic rule pass types with a
  citation at recognition, and the agent types the sheets it left untyped. Never a value outside
  the 13-value vocabulary; never assigned to a sheet you're not confident about; never a bare
  re-record over a rule-typed sheet (correct it by supersession edge, per 6b); unsure stays untyped.
- A confident correction of a machine misread (a mis-grabbed title or discipline, in that tail or on an
  already-recognized sheet) is a supersession edge onto the stored entry (`supersedesId` from
  `search`), never an entry that names nothing and never a question raised with `ask_question`. A
  reading you cannot resolve is named to the user.
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
- The spec-book leg (step 8) reads each manual file on its own, one `fileId` per call, and its counts are
  read back with `search` and verified against the job's own `report`, never assumed. A named
  `failedFiles` entry is a finding for the user, never a silent retry loop.
- The reconciliation gate (step 9) is honest about its own bounds: no classified index page, a
  backstop, or an unread spec manual are named as what didn't run, never paraphrased into "no
  problems found." `reconcile_set` findings are recorded without asking, and the report says what
  landed: sheet findings for our own queue, and Questions on the board for the design team's side.
- **An open Question on a changed sheet is re-read and replied to, never closed by this skill.**
  Step 9b replies where the new paper answers it or changes on its point, adds a box where its
  callout moved, and raises no new Question.
- **The step 10 lingering-sheet list is a complete paged read, not a first page.** It comes from
  `set_grid(limit: 0)` followed by pages until the rows cover the count, and its criterion (the
  sheet's governing delivery is not this delivery) is stated with the list. Paging that could not be
  completed is reported as incomplete, never presented as the whole set.
- **This skill never retires or supersedes a sheet the delivery did not carry.** A new set
  that drops sheets produces the step 10 finding and nothing else: no retirement, no supersession
  edge, and no entry authored about the dropped sheets, on any path.

## Deferred (named, not skipped silently)

- **OCR for image-only/scanned pages.** No text layer means both the bulk pass and your own read come
  up empty; flag, don't guess.
- **Scale auto-detect at intake.** Not built into this skill yet.
- **Master-list reconciliation as corroboration only.** A full diff against an architect drawing list
  (to surface RFI-worthy discrepancies) is a corroboration layer, never the bootstrap for this skill.
- **Backfill typing for sets recognized before the server-side rule pass.** Server-side typing now
  runs at recognition for every door, including the web-only upload door (a website-only upload has
  no agent in the loop, but the rule pass runs regardless). What remains deferred is typing the
  sheets from deliveries recognized before this pass existed, tracked separately, not this skill's problem to
  solve on its own.
