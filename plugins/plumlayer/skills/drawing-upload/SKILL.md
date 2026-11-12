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
what they read from: the recognition pass records what it confirmed off the page, and what the
sheet checker judges records as its own reading, cited to the page it read it on. The recognition
verbs and the page reads are the anti-hallucination anchor, not the inference engine. There is no
local pipeline and no server-side autonomous *reader*: the server runs the deterministic bulk pass,
which also types most sheets by a rule match, and records its own output. You drive every job and
put every decision to the user; the plugin's `sheet-checker` agent, which you dispatch, judges every
page the pass could not name, types the sheets the rule pass left untyped, and authors every entry
that isn't the deterministic pass's own grounded output.

Independent of recognition, every PDF this skill uploads starts having its own text read the
moment it registers; there is nothing to trigger. `set_text_status` says how much of a fresh
upload has been read, and a `scope-run` or `takeoff` pass starting right after an upload should
check it before searching the set's text, since a page nobody has read yet cannot be found there.

This skill runs the read cloud-first: recognition and every recorded entry come from the server or
the sheet checker's read of the cloud-hosted pages, never from a local pass. Examples in this file are generic;
never put a real client or project name here.

This skill runs in the conversation, start to finish: every question to the user is put here, and
every job is waited on here, in the open, with the poll loop in step 5, so each report of a job's
state is first-hand. The one exception is the comparison of a new delivery with the pages it
replaces, at step 9a: the plugin's `delivery-sizer` agent starts that job and polls it, and hands
back the plan it sizes off it. Three parts run one level down, since none takes an answer from the
user: reading pages goes to the plugin's `sheet-checker` agent, as "Who reads the pages" says,
step 9a's sizing of a new delivery goes to its `delivery-sizer` agent, and step 9b's re-read of
the open Questions goes to its `question-checker` agent, as those steps' files say. Never hand a
question or a decision to an agent, never hand it any other job, and never improvise an agent for
any of them.

Run, or stop and report; never create a consent step. The user's decisions in this skill are:
which project this delivery belongs to, its issue label, which files are the drawings when the packaging leaves it
genuinely unclear, whether to check the pages again when an earlier run's page and type entries
are on file, and, on a project that already holds scope items or open Questions, the plan step 9a
puts to him for the new delivery's carry and scope pass, which he approves, changes or stops,
and, on a new set, whether to change the project description's sentence that names the earlier
set (step 10), an offer at the close that holds up nothing.
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
- "recognizing sheet numbers, 140 of 209 pages at 19:33" (step 5, while a job is running, off
  the poll you just made, with its time)
- "N sheets recognized" (step 5, on job success)
- "M pages need review" (step 6's unnamed pages and untyped sheets)
- "reading the spec book's table of contents, queued as of 19:30" (step 8, while the extraction
  job is running, off the poll you just made, with its time)
- "N sections found" (step 8, on job success)
- "checking the drawing index against what we recognized" (step 9, while the reconciliation calls run)
- "measuring what this delivery changed against the sheets it replaces" (step 9a, while the
  sizing runs)
- "re-reading the N open questions against the new paper" (step 9b)
- "the set uses N discipline codes outside the standard list; I found the set's own name for K of
  them" (step 6)
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

## Who reads the pages

Every page this skill reads, it reads through the plugin's `sheet-checker` agent, one fresh
instance per unit. A page image or a page's text read in this conversation stays in it for the
rest of the session, and a set of a few hundred sheets once filled most of a session's context
that way. The agent's definition holds how a page is read, judged and recorded; none of it is
restated here, and you never read a page yourself, a local PDF's included. A unit runs in one of
five modes:

- `earlier`, once per delivery before the set unit (step 6): reads the record for entries an
  earlier run already wrote on this delivery's sheets.
- `set`, once per delivery after recognition (step 6): reads the pages the pass could not name off
  the recognition jobs, reads the whole sheet list, types what the titles decide, names the codes
  off the standard discipline list, and writes the pages file, one line per page that needs a look.
- `pages`, one per twelve lines of a pages file: reads those pages and records what it reads. A
  pages file you write yourself, for the local sampling in step 2, the file sampling in 1c, a
  manual's opening pages in step 8, a sheet left untyped in step 6 or a page check in step 9,
  takes the line shape the set unit writes, one line per page, so you never open the agent's
  definition for it:

  ```text
  <sheet:<number> or page:<fileId>:<pageInPdf>> | <fileId> | <pageInPdf> | <deliveryId, or none> | <delivery label, or none> | <reasons> | <the recognized title, or none>
  ```

  A line for a local PDF not yet uploaded puts `local` first and the file's local path in place of
  the `fileId`, with `none` for the delivery: `local | <local path> | <page> | none | none | local
  file | none`.
- `index`, at step 9: reads the drawing index.
- `left`, after the last pages unit: reads back what is still untyped.

The re-read of the open Questions at step 9b runs one level down the same way, in the plugin's
`question-checker` agent, as `reread-questions.md` says: page units one at a time, questions units
up to four at once. No Question's thread reaches this conversation either. Step 9a's sizing of a
new delivery runs in the plugin's `delivery-sizer` agent, as `size-delivery.md` says, and only its
summary reaches this conversation.

The upload folder is `<runs root>/<projectId>/upload/<deliveryId>/`, or
`<runs root>/<projectId>/upload/manual/` for a project manual that came on its own, where
`<runs root>` is `~/.plumlayer/runs` with the home directory written out: inside the project folder
`scope-run` uses, named for the project id and never for the project's name, so two projects of one
name never write over each other's upload files. It holds the pages file `pages.txt`,
written by the set unit, which you count with `awk 'END{print NR}'` and never read (Audience:
agent), any small pages file of your own, and `reports/`, one report per unit, written by the unit
before it returns (Audience: agent). It is never committed to any repo, never uploaded, and never
recorded as project entries.

A dispatch is one Agent call. Where the Agent tool takes `run_in_background`, as in a headless
session, send it `false`, as the template does: the call is then the wait, because a headless
session stops a background agent after ten idle minutes. Where the call comes back with an agent id
instead, the agent's report arrives later as its own message: end the turn with one line naming
what is running, and take the report when it arrives. That is the case in a terminal, the desktop
app or an editor, and page units still go one at a time there: dispatch a unit, end the turn,
and when its report arrives read it and dispatch the next. The line you end the turn on names the
unit. Where it also says where one of this skill's jobs stands, such as a manual's contents read that
filing started while the drawings were recognized, call that job's status verb just before you
write the line and quote that read with its time, as step 5 says; a state read before the unit
went out never goes on it. Wait by ending the turn and nothing else: no
sleep, no shell loop, no look in `reports/` or at an agent's output file, and no message to the
agent. A dispatch carries pointers and nothing else:

```text
subagent_type: plumlayer:sheet-checker
run_in_background: false
Project: <projectId>. Mode: <earlier, set, pages, index, or left>.
Delivery: <deliveryId>, label <issue label>, issued <issuedOn>, sequence <sequence>, issue <set, addendum, or none>.
Jobs: <for set, each recognition jobId with the fileId of the drawing file it reads, as "<jobId> on <fileId>", one per drawing file; otherwise "none">.
Pages file: <for pages, the path and the lines <a>-<b>; otherwise "none">.
Index pages: <for index, the fileId and page of each index page you know, or "none">.
Since: <for a unit sent again, the time its first dispatch was sent; otherwise "none">.
Upload folder: <path>. Report: <upload folder>/reports/<mode>[-<pages file name>-<a>-<b>].md.
Check your unit as your definition says, write your report to that path, then return it.
```

Read the report that comes back and nothing else: the record holds what the unit wrote. Dispatch
page units one after another, never two at once, since two units can reach the same sheet. Before
each dispatch, note the time with a local command (`date -u +%Y-%m-%dT%H:%M:%SZ`). Where a unit's
report did not arrive in the message, its report file is the report: open that file rather than
dispatching the unit again. Where the file is absent too, dispatch that unit once more, against the
live record, with `Since:` set to the time you noted before its first dispatch: the first copy's
writes may already have landed, and the second copy counts them off the record as its own, so its
report carries the whole unit. A second miss stops the run here, reported with the pages it covered.

A client that ships this plugin's skills without its agents has no agent to dispatch. There, read
`agents/sheet-checker.md` from the plugin's own folder, beside its `skills/` folder, and run each
unit yourself in this conversation, exactly as the definition says, writing the same report file.
Say once in the closing report that the pages were read in this conversation.

## 1. Pick the project

Where your client loads a verb's schema before its first call, load it when you are about to call
that verb, that verb alone, here and at every later step; never load a batch of verbs for steps
you may not reach, such as the single-file upload verbs beside the bulk ones, or the cloud entry's
and the re-read's verbs on a first delivery.

Call `list_projects` and confirm with the user which project record this delivery belongs to (a project is one
project record); get its `projectId`. When `project-setup` runs this skill it hands you the
`projectId` it just created: that project is confirmed, so skip `list_projects`. If there is no project yet, hand off to `project-setup` first; this
skill does not create projects. Confirm you also know the **issue label** for this delivery (e.g. a
generic "2025-12-22 CD Set" or "Bulletin 01"): ask the user, or plan to read it off the cover sheet
during recognition. It is load-bearing for supersession later.

## 1b. Set or addendum: you state it

Whether a delivery is a new set or an addendum is a statement on the delivery, made by the
estimator or by you for him. He picks New Set or Addendum when he uploads drawings on Documents, or
in the set's Drawing Set dialog; you state it with `create_drawing_delivery` or
`update_drawing_delivery`, always saying where it comes from (step 5b). `list_drawing_deliveries`
gives each delivery's `issue`, `"set"` or `"addendum"`, and `issueStated`: who stated it, when,
and from what. Where nobody has stated it, `issue` is null: the delivery belongs to no set, ends no
sheet, and the sheet list read by its id refuses it, so step 5b states it before step 6. Steps 9a, 9b
and 10 branch on it. The sheet count never decides it.

An addendum belongs to the latest stated new set before it in delivery order. Each sheet it prints
replaces the sheet with the same number, and the rest are added: a sheet an addendum does not carry
keeps showing from the delivery that last issued it. A stated new set ends each sheet an earlier delivery printed in a discipline the set
reissues and the set leaves out, once the set is dated or sequenced after that delivery: an ended
sheet leaves the current set and stays readable in its own delivery. A sheet it would have ended
that holds takeoff marks or a scale someone set stays current, and so does every sheet of a
discipline the set leaves out entirely. Step 10 reads both kinds back and reports them as a
finding. Nothing is retired by this skill, here or anywhere else in it.

**The project's first delivery** has no new set before it: step 5b reads what its package calls it,
and step 10's comparison has nothing to compare against on this path, and says so plainly rather
than reporting an empty finding.

**An already-registered delivery** (the 1c branch below): its `issue` reads off
`list_drawing_deliveries` like any other's, and where it is null, step 5b states it.

**A project manual arriving on its own**, with no drawings: this is not a drawing delivery. Register
nothing, skip steps 3 through 7, and enter at step 8, which files the manual and reads its table of
contents. Step 9 still runs, and its drawing legs report as unchanged because no sheet changed.
Step 9b re-reads the open Questions citing the sections the new manual carries. Say in the closing
report that no drawings came with it.

## 1c. Cloud-resident entry (files already in the project, nothing local)

A file with no delivery attached to it needs one registered, as step 3 says, before step 5 reads
its sheet numbers. A cloud-resident delivery whose `issue` is null goes through step 5b, like any
other.

Not every run starts from a local delivery. When the user points you at a project whose set is
already in cloud storage (uploaded in a prior session, or they ask you to "read the uploaded set"
or "(re)recognize" it), there is nothing to recognize locally and nothing to upload. Detect it before
asking for paths: if the user hands you no local files, call `list_files(projectId)`; if the
drawings are there, read `cloud-entry.md` beside this file, in this skill's own folder, and run
that branch in place of steps 2 to 4. When it's genuinely ambiguous (some files uploaded, the user
also holding local files), ask; never assume which delivery the user means.

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
didn't resolve), write a small pages file naming a few local candidate pages of each file, each
line with `local` first, the file's local path, the page and the reason `local file`, and dispatch
a pages unit over it. Its `files:` line says for each page whether it carries title-block grammar
or spec prose, and what a cover sheet prints for the issue, so you pick which file to use without a
page in this conversation. This local sampling is file-selection judgment only: it decides which
local files you upload next; it never grounds an entry, and no entry's evidence ever cites a local
read (every entry's evidence comes from the cloud reads in steps 5 and 6).

<!-- user-facing -->
Emit a short packaging report before uploading: the class, which file(s) are the drawings and why,
page counts, which file(s) (if any) are the project manual / spec book headed to step 8, which files
you are excluding (geotech, emails, unrelated attachments) and why, and the picked source if there was
a dual-source quirk.
<!-- /user-facing -->

## 3. Register the delivery

Call `list_drawing_deliveries(projectId)` first. If a delivery with this issue label already exists,
reuse it rather than registering a duplicate. Otherwise call `create_drawing_delivery`:

- `label`: the human issue label from step 1.
- `issuedOn` (`YYYY-MM-DD`) and `sequence`: read these off the documents themselves (a cover sheet, a
  bulletin header), as a `local file` or `file` unit's `files:` line gives them with the page and
  the words printed; a value it says is not printed is asked of the user, never guessed. Never
  substitute upload time: chronology drives supersession resolution.
  **When issue-date signals disagree** (the filename says one date, a cover sheet or transmittal says
  another), the drawing set's own revision table governs `issuedOn`: it's the
  architect's own record of the issue, ahead of a filename someone typed or a transmittal cover letter.
  Note the disagreement in the packaging report rather than silently picking one.
- `issue`: pass it here only when the estimator already said which, with `issueSource.asked`
  carrying his words exactly as he wrote them. Otherwise leave it out: step 5b states it once the
  delivery's pages are read.

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
3. `register_file(projectId, fileId, filename, contentType, deliveryId)`: always pass `deliveryId`
   and leave `kind` out, so the server sorts the file by its page sizes (see "Wait for the sort"
   below). The delivery makes chronology come from the delivery, not upload order. Idempotent: a
   retried call for the same
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
3. `register_files(projectId, files, deliveryId)`: pass every file's `{fileId, filename,
   contentType?}` and the same `deliveryId` from step 3, so chronology comes from the delivery, not
   upload order, and leave `kind` out, so the server sorts each file by its page sizes (see "Wait
   for the sort" below). Answers per file, never all-or-nothing: `{registered, failed, counts}`.
   `counts.registered` must equal the number of files you sent. Anything in `failed` names its
   `fileId`, `filename`, `reason`, and `message`: re-PUT and re-register only those files, by
   `fileId`, never the whole batch again, and never blindly. A `reason` of `not_found` (the PUT
   didn't land) is worth that retry; any other reason is stopped and reported.

**Wait for the sort.** A file registered with no `kind` reads `unsorted` in `list_files` until the
server has measured it. A PDF whose pages are mostly large-format sheets becomes `drawing`, and
because it carries the `deliveryId`, the server starts its sheet read itself; any other file becomes
`document`. Call `list_files(projectId)` every ~5s until none of the files you just registered reads
`unsorted`, and never decide a file's kind yourself while it is unsorted. A sort that fails leaves
the file `unsorted`, and nothing an agent calls starts it again, so the wait has one exit of your
own: a file still `unsorted` after 10 minutes of polls with no file changing kind. Stop there, carry
on with the files already sorted, and tell the user:

<!-- user-facing -->
These files have not been sorted yet: <filenames>. On the Documents page, each one has Retry on its
row under New Uploads. Once it is filed, I can read its sheets.
<!-- /user-facing -->

Then:

- Every file now `drawing` goes on to step 5.
- A file now `document` that step 2 judged a project manual, a spec book or another non-drawing:
  leave it out of steps 5 to 7 and name it in the packaging report. A manual or spec book goes to
  step 8 from item 2 on; it is already filed, so do not upload it again. Its spec section read has
  started, unless the file is not a PDF or could not be opened; `extract_spec_toc` then starts the
  read or fails with the reason, and step 8 reports that failure.
- A file now `document` that step 2 judged a drawing (a set printed mostly on letter paper, say):
  put it to the user. If the user confirms it is drawings, `update_file(projectId, fileId, kind:
  "drawing")` files it as one, and it goes on to step 5, where `recognize_sheets` with the
  `deliveryId` reads its sheets. If not, treat it as a document as above.

Name `kind: "drawing"` on the register call only for a file step 2 judged a drawing that is printed
on letter or legal paper (a sketch with a title block), which the sort would file as a document.
`register_files` applies one kind to every file in the call, so register such a file in a call of
its own. Never name it for a whole delivery: a project manual misjudged in step 2 then gets a
drawing page for every one of its pages.

Either path, no local run folder and no manifest file: the project files list (`list_files`) is the
record.

## 5. Recognize sheets (async, start then poll)

Call `register_pages(projectId)` once for the project: it registers viewable page rows for every
uploaded PDF (not entries, just renderable pages) and only needs to run once per project, not per file.

Then, once per file, call `recognize_sheets(projectId, fileId, deliveryId)` to start the
deterministic server-side pass over that PDF. It returns immediately (it does not scan inline) with
`{jobId, status: "queued"|"succeeded", deliveryId, alreadyActive?}`. `alreadyActive: true` means a job
for this file+delivery is already in flight or done; poll the returned `jobId` rather than starting a
second one. A drawing the server sorted in step 4 already has its read started, so for it this call
answers with that job and `alreadyActive: true`.
Run `recognize_sheets` once per file, never twice for the same file+delivery.

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
  state both numbers. `confidence` on individual entries (visible later on the sheet list) is
  triage/review-priority metadata only: it tells the sheet checker which sheets to look at first and
  ranks nothing.
- On a `succeeded` pass, `written.enteredValuesKept` lists the pages where the pass read nothing but a
  sheet number, title, discipline, or type that a person or an agent entered still stands. The pass
  left each one as it is. When `pages` is above zero, name those pages to the user with the value
  kept on each, and ask whether each one is right. Never correct one yourself.
- On a `succeeded` pass, `written.laterIssueKept.sheets` counts the sheets where a newer drawing
  issue already holds the title, discipline, or type this pass read, so this pass wrote none of them.
  When it is above zero, tell the user this issue was read after a newer one and that the newer
  issue's values stand on those sheets. Do not record this issue's values over them.
- On a `succeeded` pass, `written.numbersReplaced` lists the pages where this pass read a different
  sheet number from the one the page carried, and the page now carries the new number. Each item
  has `pageInPdf`, `from`, and `to`. When `pages` is above zero, tell the user each one: page
  {pageInPdf} was {from} and now reads {to}, and the marks, scale, packages, citations, and any
  title, discipline, or type entered on {from} are now on {to}. A number a person or an agent
  entered is replaced only by a number the reader had not read on that page before.
- On a `succeeded` pass, `written.numbersKept` lists the pages where a number stays although this
  pass read another number there, or none (`read` is null). Each item has `pageInPdf`,
  `sheetNumber`, and `read`. The number stays because work sits on it (takeoff marks, a scale, a
  package, a citation from a scope item or a Question, or a title, discipline, or type someone
  entered) or because another number already holds the page. When `pages` is above zero, tell the
  user {sheetNumber} stays on page {pageInPdf} although the drawing now reads {read} there (or no
  number), and ask whether to move that work and take {sheetNumber} off the page with
  `remove_sheet_from_page`. Never take a number off yourself without the user's answer.
- `report.pagesUnread` lists pages the pass did not read at all (each such `unnamedPages` row says
  why in `unread`). Those pages are not in `enteredValuesKept`; the set unit in step 6 sends them
  to be read.

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

## 5b. State the issue

Run this once this delivery's recognition jobs have ended, before step 6, wherever
`list_drawing_deliveries` gives this delivery `issue` null. Where it already gives `"set"` or
`"addendum"`, because the estimator picked it on upload or told you at step 3, read its
`issueStated`, name it to the user, and go on to step 6; change it only where the reads below
disagree with it, by asking him as point 4 says.

1. Find the latest new set before this delivery: the last delivery before it in
   `list_drawing_deliveries` whose `issue` is `"set"`. On the project's first delivery there is
   none.
2. Read what the delivery shows it is, each with the file and page it is on:
   - its name: its label, and the transmittal where one came with it;
   - its cover and the revision marks and dates in its title blocks: write a small pages file
     naming the cover and two or three title-block pages with the reason `file`, in the line
     shape "Who reads the pages" gives, dispatch one pages unit over it, and read the label, the
     date and the sequence its `files:` line gives for each page, against the latest new
     set's dates;
   - its sheet list: the `sheetCount` `list_drawing_deliveries` gives it, against the latest new
     set's, `set_grid(projectId, deliveryId: <that set's id>, limit: 0)`, by discipline.
3. Where they agree, call `update_drawing_delivery(projectId, deliveryId, issue, issueSource: {
   read: { fileId, page, sheet } })`, naming the plainest page that shows it, such as a cover that
   reads "Addendum 1" or a revision row naming the addendum, and pass `replaces` where a kind is
   already held. On the project's first delivery, a package whose name and cover call it a set, or
   name no addendum, is a new set read off its cover.
4. Where they disagree or say nothing, ask the estimator in chat, naming what each shows, for
   example: "The package is named Addendum 1 and its revision rows name Addendum 1, but it carries
   all 212 sheets of the bid set. Is it an addendum to the bid set, or a new set?" Then record his
   answer with `issueSource.asked`, his words exactly as he wrote them.

The sheet count never decides it: an architect hands out an addendum as a full reissue, and a new
set can print fewer sheets than the one before it. Where `update_drawing_delivery` refuses a
change naming who stated the kind and when, someone stated it since you read the list: read it
again, and ask the estimator before stating it over his.

## 6. Check the pages, one level down

The recognition pass grounds the tokens it reads, but it leaves a tail: pages it could not name,
sheets its rule pass could not type, titles where it grabbed the wrong cell (a boxed note in place
of the title-block cell), discipline codes off the standard list, and sheet numbers with no
letters. The sheet checker reads all of it, unit by unit, as "Who reads the pages" says, and you
hold only what each unit returns. How a page is read, judged and recorded is in the agent's
definition and is not restated here.

This step runs on every door this skill supports: a fresh baseline, a bulletin or revision, and the
cloud-resident branch (1c) all converge here before the skill reports done. A delivery, or an
earlier delivery in the same project, that went through recognition and was never typed, from a
session that predates the server-side rule pass or one that stopped short, is closed out by this
run, not left for later.

1. **Check for an earlier run's entries first.** The server's idempotency covers the entries the
   recognition pass recorded, not the ones an agent authored, and an earlier run may have been on
   another machine, so the upload folder alone never answers it. Before this run dispatches any
   unit for this delivery, look in the upload folder's `reports/` with a local command (`ls`):
   any report already there is an earlier run's, since this run has written none yet. Then
   dispatch one earlier unit. Confirm with the user before checking the pages again where that
   look found a report, where the earlier unit found any `sheetType` or `partOfIssue` entry an
   agent wrote on this delivery, or where its read says `finished: no`: a read that did not finish
   never stands for no earlier run.
2. **The set unit.** First read this delivery's `issue` off `list_drawing_deliveries(projectId)`,
   the read step 1b names, now that its jobs have ended: the recognition status carries no
   `issue`, so the delivery list is where you read it. `issue` null means step 5b has not run:
   run it first. Where the estimator has not answered its question yet, the dispatch says
   `none`. Dispatch one set unit, naming each recognition job id of
   this delivery with the `fileId` of the drawing file it reads, and that `issue`. It reads the
   pages the pass could not name off the jobs, reads the whole sheet list, types every leftover
   sheet whose title decides it, names the codes off the standard list from the set's own index,
   and writes the pages file: one line per page that needs a look, with its reason. Start from
   `recognize_sheets_status`'s `written.sheetTyping` summary, `{sheetsConsidered, typed,
   highConfidence, mediumConfidence, untyped, typedWritten}`, which you already hold from step 5.
<!-- user-facing -->
   Narrate the split in estimator words: "the recognition pass sorted N of M sheets by type; I'm
   looking at the K it left."
<!-- /user-facing -->
3. **The pages units.** Count the pages file's lines with `awk 'END{print NR}' <pages file>`,
   which counts a last line with no newline too. The file holds this delivery's pages to look at
   and, on an addendum, the earlier deliveries' too, so compare that count with the set unit's
   `pages to look at` plus the `pages to look at` on its `earlier deliveries:` line, where that
   line carries one. Where they differ, stop the run there and name the file's count and both
   figures. Otherwise dispatch one pages unit per
   twelve lines, in order (lines 1 to 12, then 13 to 24, and so on), one after another, until the
   last line is covered. Sum each unit's counts as it returns, this delivery's apart from earlier
   deliveries'.
4. **The left unit.** After the last pages unit, read this delivery's `issue` off
   `list_drawing_deliveries(projectId)` again and decide on that read, never on point 2's: a page
   a pages unit gave a number to can give a delivery recognition left with no number its first
   sheet. Where this read gives `sheetCount` 0 with `stillReading` false, the delivery still holds
   no sheet number, and the sheet list read by its `deliveryId` has no row to count; where it gives
   `issue` null, step 5b has not run, and the sheet list refuses it. Skip only what needs that read: dispatch no left unit and skip step 7's coverage
   comparison. Every other step runs as usual, step 7's other points, the project manual in step 8
   and the index check in step 9 among them, and step 10's handoff names the delivery with no sheet
   number. Otherwise dispatch one left unit, with the `issue` this read gave. Its two lists are the
   sheets still without a type and the sheets still filed under no discipline letters, read back
   from the record. A sheet on its `this delivery:` untyped list that no pages unit named on its
   `left untyped:` line was never reached: write it to a small pages file of its own with the
   reason `type` and dispatch one more pages unit over it, then the left unit again. On an
   addendum, the same goes for a sheet on its `earlier deliveries:` untyped list that no pages unit
   named on its `earlier deliveries:` line. On a new set, the earlier deliveries' rows are the
   sheets this set does not print: they are left alone, never sent for typing, and step 10 names
   them.

**Gate:** every page in the tail ends up judged (a full entry bundle) or flagged (image-only or
genuinely unreadable), never silently dropped; every code on the off-list ends named with a
citation or reported as one the set does not name; and every sheet with no letters ends recorded
with a citation or named to the user. State the counts.

<!-- user-facing -->
Say what the units found the way it happened:

- Corrections: "the automatic scan grabbed the wrong text on N sheets, so I read them and set them
  right".
- Toss-ups: name each sheet with both readings, so a person settles it. Which of two readings of
  our own sheet title is right is ours to settle, not a question for the design team.
- Two pages printing one number: name both pages rather than picking one.
- The discipline codes: "The set uses N discipline codes outside the standard list; I found the
  set's own name for K of them, and J show as their letters until you name them. M sheets had no
  letters in their number; I read the pages and filed K of them, and J need you."
- The untyped sheets: "N sheets sorted by type, M I left for a closer look"; never imply full
  coverage when some sheets were skipped. Name the M by sheet number, off the left unit's list, and
  say what the list is: the sheets left without a type. It is a different list from the title
  disagreements in the index check, even when most numbers repeat; if you mention that earlier
  list, say which sheets are in both and which are in only one, never "the same".
- Flagged pages: name them by page number, "could not recognize these N pages", in the
  conversation rather than as Questions on the project record.
<!-- /user-facing -->

## 7. Verify

The recognized portion needs no write from you. `recognize_sheets` already wrote it server-side
once its job succeeded (step 5), and re-running `recognize_sheets` on the same file+delivery is
safe by construction: the concurrency guard returns the existing job, and the write itself is
idempotent (`alreadyWritten: true` on a poll means a prior run already wrote this delivery's sheet
entries, and no duplicate was written). Every entry the sheet checker authored was written by the
unit that read it, in one count-verified write per unit. You verify:

1. **Each unit's write.** Its `sent:` equals its `landed:`. A mismatch stops the run and gets
   reported, never retried with a guessed correction.
2. **The recognized portion, with a targeted check.** Compare the succeeded job's `write` summary
   (`{written, alreadyWritten, byPredicate}`) against its `report` (`sheetsGrounded` and the rest)
   for rough correspondence, then spot-check with a handful of `search(projectId, predicate:
   "appearsOnPage", text: "<a sheet number you saw>")` calls. That spot-check is this step's verify.
   The sheet list's rows are the units' to read, never this conversation's.
3. **Typing coverage, from two reads of the record.** Only where step 6 point 4's second read of
   the delivery list gave this delivery a stated `issue` and a `sheetCount` above 0 and the left
   unit was dispatched; a delivery whose `sheetCount` is 0 with `stillReading` false holds no
   sheet number, and it skips this point and goes on to step 8. Right after the left
   unit returns, call
   `set_grid(projectId, deliveryId: <this delivery's id>, limit: 0)` and read its `count`. The left
   unit's `this delivery:` typed count plus its untyped count must equal it. Both read the same
   grid at the same time, so a unit sent again, an earlier run's corrections and a page the checker
   named all count once. Where the two differ, the left unit's read was incomplete: dispatch it once
   more and compare again, and where they still differ, tell the user both counts and stop. Name
   every sheet on the left unit's untyped list to the user, which is what keeps a sheet from being
   skipped silently. The left unit's `earlier deliveries:` counts are reported on their own line,
   never folded into this delivery's.

Report any pages still unresolved or flagged image-only, by page number, in the conversation
rather than raising them as Questions on the project record, and report the plain untyped count:
a person resolves them, not something this skill resolves itself.
<!-- user-facing -->
Report: the
project and delivery; the recognition run's counts (pages scanned, sheets recognized, how many were
high-confidence, how many were flagged for a closer look); how many sheet records were saved and how
many were already on file; the count of sheet records added for the sheets reviewed and typed,
confirmed against what was sent; whether every recognized sheet in this delivery now carries a
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
   `register_file(projectId, fileId, filename, contentType, kind: "document", deliveryId)`; two or
   more (a folder-of-divisions manual) uses `request_file_uploads`, the same PUT loop, then
   `register_files(projectId, files, kind: "document", deliveryId)`, with the same
   `counts.registered` check and the same per-`fileId` retry on anything in `failed`. Pass the
   `deliveryId` of step 3 where the manual came with this delivery's drawings: the comparison of the
   delivery reads those files as its manual and holds each scope item citing an earlier manual
   against them, and a document filed under a delivery starts no sheet read. A manual uploaded on
   its own, with no drawings, is filed with no `deliveryId`. A manual step 4 sorted as a document
   keeps the one it was registered with, and that is fine. Misfiled earlier as a drawing? Fix it in
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
   opening pages: say so, and before reporting any section count, write a small pages file naming
   the manual's opening pages with the reason `opening pages` and dispatch a pages unit over it;
   its `files:` line says whether those pages print a table of contents and how many sections it
   lists. A table of contents the read could not take whole ends the job `failed`,
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
   sum over every read that wrote: completeness and could-not-read findings ride fields of their
   own (`hasListingNote`, `hasNumberNote`, `hasTitleNote`, `hasSectionStartsNote`, `hasPageNote`;
   a manual read before those fields existed keeps them on `hasCompletenessStatus`) and never
   appear in this read. A mismatch stops the run and
   gets reported, never a guessed correction.

**If `extract_spec_toc` / `extract_spec_toc_status` don't appear in your tool list**, a
freshly-shipped verb may not appear until the session reloads the plugin or reconnects to the
server. Start a fresh session rather than assuming the manual can't be read.

**No project manual in this delivery?** Say so plainly in the report and move on to step 9: nothing
here blocks the reconciliation gate; it only means the gate's spec leg reports as not having run (step
9 already covers that honestly).

## 9. Reconcile the index against the set

This is the pre-read reconciliation gate. Before anything downstream reads this set for scope, run
one deterministic check: does the delivery's own drawing index agree with what actually got
recognized, and with the spec sections read from the project
manual. Catching a set-level mismatch here keeps it from poisoning every read that follows.

1. **Read the index as stated.** Dispatch one index unit. It runs the parse of the delivery's
   drawing index page(s), which records each listed sheet as a cited `declaredInIndex` entry,
   reading from the sheets typed `cover-index` in step 6; where none were typed, name the index
   page(s) you know about in its dispatch. Report its `declared:` count, and whether its backstop
   came back: that means the parse could not stand as the declared register (no text layer, too
   few sheets found, a column structure that did not resolve), and the unit rendered the index
   page and counted the sheets it lists. Say both counts before trusting either.
2. **Run the diff, report-only.** Call `reconcile_set(projectId)` without `record`. The bare call
   runs the ORIENTATION check: the index of record (the newest delivery that actually has a read
   drawing index) against the current compiled set across every delivery, not just one. Pass
   `deliveryId` instead to run the per-delivery RECEIVING check: that one delivery's own drawing
   index against only the sheets delivered in it. `result.mode` reports which comparison ran. Either
   way it compares three sides: what the index declares, what sheets are actually in the set, and
   what the spec sections say. The bare call answers the counts, the warnings, and one line per open
   item in `report.openItems.lines`, each saying what the item is and who settles it; pass
   `full: true` for the whole report with each finding's evidence. It writes nothing on this call.
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
   - What couldn't be read: `report.counts.parseRejected` counts the index tokens this run could
     not read as sheet numbers (a warning says so, and `full: true` lists the first 25), and
     `report.openItems.unparsedPages` names the index pages it could not read whole; state those
     counts out loud rather than folding them into "no problems found."
   - Whether the index re-read agreed with the stored records: check `report.declaredLedgerDrift.ran`
     first. It's `false`, never a hollow zero, whenever no index page could be read at all, or a
     receiving-check run had to widen its re-read to another delivery's pages; the drift arrays are
     empty in that case too, and that's a check that didn't run, not a check that found nothing.
   - Whether the spec comparison ran at all: when step 8 found no project manual to extract for
     this delivery, the spec leg is reported as not having run. Say exactly that; never present it
     as a finding of zero.
<!-- /user-facing -->
4. **Record the findings.** A sheet the index lists and the set lacks goes straight to its
   Question once every page of the delivery is recognized, that is once no unit's `flagged:` line
   names a page of it: read no sheet list rows, run no search, and open no agent file to check it
   first. Where the index lists a number with a letter (`A-501A`, `A-501B`) and two pages print
   the number less its letter (`A-501`), recording raises that one Question itself. Only while flagged pages remain can the sheet be on one of them: write those pages to a
   pages file with the reason `unnamed`, in the line shape "Who reads the pages" gives, and
   dispatch pages units over it before you record, twelve lines to a unit as step 6 batches them. Once you have shown the report, note
   the time with `date -u +%Y-%m-%dT%H:%M:%SZ`, which step 9b passes on as `Asked before:`. Where a
   prior delivery existed, take the two counts step 9a reads next: the `count` of
   `search(projectId, subjectPrefix: "scopeItem:", limit: 1)`, and the `openCount` of
   `list_questions(projectId, limit: 0)`. Then call
   `reconcile_set(projectId, record: true)` and say what landed. Two things land: the sheet findings
   that stay with you to settle, and, for the side the design team has to answer, Questions on
   the board, each citing the index page and the sheets it is about. Those Questions are grouped by
   discipline series, not one per sheet, and a class spanning more than three series becomes a single
   project-wide Question naming the series and their counts. Where some pages print no sheet
   number, the sheets the index lists that no page prints are one Question instead, naming those
   sheets and pages and asking the design team which sheet each page is. Read them back with
   `list_questions`.
   This is internal work: it needs no go-ahead, and the user corrects anything wrong on the site.

## 9a. Size the new delivery, then carry the unchanged references

Wherever a prior delivery or manual existed, read `size-delivery.md` beside this file, in this
skill's own folder, and run it before step 9b. On the project's first delivery skip it and leave
that file unread. Its first step waits for the read of the new paper's text, on every path that
reads it, since the comparison and the re-read both search that text; step 9b takes that wait's
result. Its later steps size the delivery only on a project that already held a scope item or an
open Question before step 9's recording call, and only for a drawing delivery whose kind is stated
and whose sheet count is above 0: the plugin's `delivery-sizer` agent measures it and writes the
plan, the user approves, changes or stops it, and on his approval the agent carries forward each
reference that reads the same. The carry runs before step 9b's re-read, so a place it adds on a
Question is the one the re-read finds there. Nothing is carried and nothing is read before he
approves the plan.

## 9b. Re-read the open Questions this delivery touches

A revised sheet can answer a Question somebody raised against the one it replaces, or move the
callout the Question points at. This step reads every open Question on what changed against the
new paper: it closes each one the new paper answers, with one line naming where, rewrites each one
nobody has sent that the new paper changed, and points the rest at the new pages, replying once on
a sent one it changed. It runs whenever a prior delivery or manual existed:
an addendum, a new set, or a manual on its own. There, read `reread-questions.md` beside this
file, in this skill's own folder, and run it, once step 9a has run, with the result of step 9a's
text read. Where step 8 filed a project manual in this upload beside a drawing delivery, the same
re-read also reads each open Question citing a section of the new manual, so hold the `fileId` of
each file step 8 filed for it. On the project's first delivery there is nothing earlier on the
board to re-read, so skip it and leave that file unread.

## 10. Close out

Step 9b's re-read of the open Questions is reported before any of this. Point 3 runs on every path
through this skill. Points 1, 2 and 4 run only where this delivery is stated as a new set.

1. **The new-set finding.** Run this where `list_drawing_deliveries` gives this delivery `issue:
   "set"`, and only when a prior delivery existed; on the project's first delivery there is nothing
   to compare against (step 1b), so say that instead of reporting an empty finding. Read the set
   back from the record:
   `set_grid(projectId, limit: 0)` first for `count` and `disciplineCounts`, then page with
   `discipline` + `limit`/`offset` until the rows you hold cover the count. Never a bare call: its
   default first page is not the set. Every row carries the delivery governing it (`deliveryId`,
   `label`, `kind`). The lingering sheets are the rows whose governing delivery is not this one:
   sheets an earlier delivery printed that this new set did not end, because the set leaves their
   discipline out entirely, they hold takeoff, or the set is not yet dated after them. Report
   `currentSetStatus` / `currentSetNotes` for any row the resolver could not settle rather than
   folding it into the list. If the paging could not be completed, say so and say how far it got; a
   partial list is never put up as a complete one. Then read this delivery's row on
   `list_drawing_deliveries` for the sheets the set ended: its `ends`, which left the current set,
   and its `keptForTakeoff`, which it would have ended and which stay current for their takeoff.
<!-- user-facing -->
   Give the user the list with the criterion that produced it said out loud: these are the sheets
   still showing as part of the set that came in on an earlier delivery, not on this one. Name them
   by sheet number, and say which of them stay only for their takeoff, which leave the set once
   someone deletes that takeoff. Then name the ended sheets by sheet number: they no longer show as
   part of the set, and the user still opens each one in the delivery that printed it.
<!-- /user-facing -->
2. **It is a report, nothing more.** This skill does not retire, replace, or write anything about
   those sheets, on any path.
<!-- user-facing -->
   Say plainly that the lingering sheets still show as part of the set and that you changed or
   removed none of them, and that the ended sheets are out of the set because the new set is dated
   after them, with nothing written about them, rather than wording it so it sounds like the run
   acted on them.
<!-- /user-facing -->
3. **The handoff.** For a drawing delivery, read its `issue` off `list_drawing_deliveries` and
   name the scope pass for it, which `scope-run` runs: a new set gets a full pass over every sheet
   it prints, against the record the earlier passes built, and an addendum a partial pass over the
   sheets it prints, reviewing only the packages that pass writes on. A scope pass already underway
   on this project finishes first, and this delivery's pass comes after it. Two paths name no pass.
   No scope pass reads a project manual on its own: it registered no delivery, and the package
   reviews of the next pass read the sections it carries. A delivery whose `sheetCount` is 0 with
   `stillReading` false holds no sheet number, so a pass would have no sheet to read: name it, say
   no pass reads it, and point back at what step 5 and step 6 found on its pages. A delivery whose
   `issue` is still null, its question at step 5b unanswered, gets no pass until the estimator
   answers: name it and say so. Where step 9a sized the delivery, the pass is the plan he
   approved there, and the plan file names its sheets for `scope-run`; where he stopped the plan,
   or the sizing stopped with no plan, no pass is planned until he asks for one.
<!-- user-facing -->
   Name what comes next in one sentence: for a new set, a full scope pass over it; for an
   addendum, a partial scope pass over the sheets it prints. Where you sized the delivery, name
   the pass he approved instead: the sheets it re-reads, or a full scope pass, then the recheck.
   Where he stopped the plan, or you could not make one, say no scope pass is planned until he
   asks for one. Say that `scope-run` starts it, and
   where a pass is already underway, that it finishes first. For a manual on its own, say no scope
   pass reads it alone, and that the package reviews of the next pass read its sections. For a
   delivery with no sheet number read, name it and say no scope pass can read it until its sheet
   numbers are read.
<!-- /user-facing -->
4. **The project description.** Where this new set follows a prior delivery, read `description`
   off `get_project(projectId)`. Where it names the earlier set as the job's drawings (its
   deliverable, such as 100% Design Development, or its issue date), the description now reads as
   of a set this one replaced. Write nothing on your own: the description may be a person's words.
   The new sentence names this set by its `label` on `list_drawing_deliveries` and, where that row
   gives one, its issue date, and by nothing you did not read there. Put the offer once, after
   point 3; it holds up nothing, and the scope pass he approved goes ahead whatever he answers.
   Where he says yes, call `update_project(projectId, description: "<the description with that
   sentence replaced by the one you offered>")`, changing only that sentence.
<!-- user-facing -->
   Quote the sentence that names the earlier set, say it still describes the earlier set, and give
   the sentence you would put in its place, naming this set as its delivery is labeled. Offer to
   make that change. Where the description names no set, say nothing about it.
<!-- /user-facing -->

## Gates (non-negotiable)

- **The questions and the jobs stay in the conversation.** Every question to the user is put
  here, every job is polled here until the server ends it, and every report of a job's state
  quotes the last payload received and its time. The one exception is the comparison of a new
  delivery at step 9a, which the delivery sizer starts and polls. Page reads go to the sheet
  checker, the sizing of a new delivery and its carry to the delivery sizer, and the re-read of
  the open Questions to the question checker, page units one at a time and questions units up to
  four at once, and nothing else leaves this conversation.
- **Run, or stop and report; never create a consent step.** The user's decisions are the ones
  named at the top of this file; everything else is the skill's own work. A failure is reported
  with its error, retried only when the error names what a retry changes, and never put to the
  user as a choice of retry strategy. A failure is reported in the conversation, never written
  into the project as a Question: a Question is about the project, never about a Plumlayer
  failure. Question text is plain estimator words, and every Question meets the standard the
  `ask_question` verb states: a title, a citation for every place it names, and only what is worth
  the design team's time. Its first sentence states the problem, and it asks one thing; finds share
  a Question only where one answer settles them all. It names each item once, in the words the cited
  sheet uses, with no clause re-describing what that sheet shows or where the item is; a sentence
  names at most three tags, only the ones with the problem; a parenthesis holds a short qualifier,
  never a sentence; every sheet it names is one of its citations, boxed on the entry it names there,
  and cited as the whole sheet only where the point is that the sheet lacks it or no line of the
  page's read carries the entry; a sheet the set lacks is cited at the spot that names it; and it
  carries no colon without the list it announces, no sentence repeating the title, and no sentence
  on why we need the answer. A Question that needs that sentence to be worth sending is not raised.
- **Sheet typing is unskippable, on every door this skill supports.** A run through this skill
  (a fresh baseline, a bulletin or partial revision, the cloud-resident re-recognition branch in
  1c, or a corrected re-read once a force-re-recognize path exists) never reaches its closing
  report while a recognized sheet in scope has had no typing attempt at all. "Unsure, so left
  untyped and counted" is a valid outcome; "never looked at" is not, on any path, including one
  where `recognize_sheets` came back already-succeeded with nothing new to write. Step 6 is where
  every door converges before this skill calls a delivery done, not an optional refinement bolted
  onto recognition.
- Every entry's evidence is grounded cloud-side: a succeeded `recognize_sheets` job (recorded by
  the server) or a page read the sheet checker made in the unit that writes the entry. A local read
  (step 2) may inform the packaging report; it never grounds an entry.
- Discipline is derived from the sheet's own number prefix, never a filename or folder. A prefix
  off the standard list keeps its letters and the set unit records the set's own name for it, cited
  to the page that prints it, or leaves it unnamed; a number with no letters is read from its page
  by a pages unit, still never a filename or folder guess.
- Every page the pass could not name is judged or flagged, never silently dropped; image-only pages
  are named, not guessed.
- `sheetType` typing splits across two authors: the server's deterministic rule pass types with a
  citation at recognition, and the sheet checker types the sheets it left untyped. Never a value
  outside the 13-value vocabulary; never assigned to a sheet the checker is not confident about;
  never a bare re-record over a rule-typed sheet (it is corrected by a supersession edge, as the
  checker's definition says); unsure stays untyped.
- A confident correction of a machine misread (a mis-grabbed title or discipline, in that tail or on an
  already-recognized sheet) is a supersession edge onto the stored entry (`supersedesId` from
  `search`), never an entry that names nothing and never a question raised with `ask_question`. A
  reading you cannot resolve is named to the user.
- The page entries and type entries the sheet checker writes (the leftover sheets and any
  correction) are its own reading, cited to the page it read; never present them as the
  deterministic pass's confirmed output, and never present a rule-typed sheet as the checker's read.
- Each unit's write is verbatim, count-verified transport: a count mismatch stops the run, never
  triggers a reconstructed or invented entry.
- Before the set unit, check for an earlier run's entries on this delivery and confirm with the
  user rather than double-recording; the recognized portion is server-idempotent by construction
  (re-running `recognize_sheets` on the same file+delivery is always safe).
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
- **An open Question on what changed has three outcomes, and step 9b raises no new one.** Where
  the new paper answers it, it is closed with one line naming where, and the user reviews those
  closes first. Where the new paper changes on its point without answering it, a Question nobody
  has sent is reworded to read as of the new paper, and a sent one gets one reply saying what
  changed. Where it is unchanged on the point, it is pointed at the new pages and nothing else is
  written.
- **The step 10 lingering-sheet list is a complete paged read, not a first page.** It comes from
  `set_grid(limit: 0)` followed by pages until the rows cover the count, and its criterion (the
  sheet's governing delivery is not this delivery) is stated with the list. Paging that could not be
  completed is reported as incomplete, never presented as the whole set.
- **This skill never retires or supersedes a sheet the delivery did not carry.** A new set
  that drops sheets produces the step 10 finding and nothing else: no retirement, no supersession
  edge, and no entry authored about the dropped sheets, on any path.

## Deferred (named, not skipped silently)

- **OCR for image-only/scanned pages.** No text layer means both the bulk pass and the sheet
  checker's read come up empty; flag, don't guess.
- **Scale auto-detect at intake.** Not built into this skill yet.
- **Master-list reconciliation as corroboration only.** A full diff against an architect drawing list
  (to surface RFI-worthy discrepancies) is a corroboration layer, never the bootstrap for this skill.
- **Backfill typing for sets recognized before the server-side rule pass.** Server-side typing now
  runs at recognition for every door, including the web-only upload door (a website-only upload has
  no agent in the loop, but the rule pass runs regardless). What remains deferred is typing the
  sheets from deliveries recognized before this pass existed, tracked separately, not this skill's problem to
  solve on its own.
