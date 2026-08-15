---
name: drawing-set-assemble
description: >
  Assemble the project's current drawing set into fresh PDFs off the cloud project record's set grid:
  one PDF per discipline, plus an optional combined PDF. Trigger on "assemble the set", "current
  set", "merged PDFs", "discipline split", "give me the latest PDFs", "combine into one pdf", or
  "/assemble-set". Drives the async assemble_current_set and assemble_current_set_status MCP tools,
  a pure export that records nothing new. Does not publish the Master Drawing Index workbook
  (drawing-index-publish) or upload drawings (drawing-upload).
---

# Drawing set assemble: current-set PDF export

## Talk to your user like an estimator

Verbs, claims, and trust classes are machinery for you, never words the user reads. This covers
everything the user sees, including your closing report: a report template is user-facing text.

Speak estimator words: project record, entry, sheet, set, scale, scope item, bid response, flagged
item, trail.

Never say to the user: claim, deposit, predicate, subject, proposed, governing, trust class,
supersede, promote, reconcile, reconciliation, ledger, grounding, residue, idempotency, QA,
sheetType, or any raw verb, field, or parameter name.

Translate instead: a value you replaced is "I updated my earlier read"; a machine misread you caught
is "the automatic scan grabbed the wrong text, so I read the sheet and set it right"; cross-checking
the index is "checking the drawing list against the actual sheets"; what you could not settle is
"what is still open". Plain prose, no em dashes, no bolded emphasis words.

The full list, with translations, is in the project-record skill's Words section.

Take the project's current governing sheet set and turn it into fresh, ready-to-use PDFs, one per
discipline, and, by default, a single combined PDF of the whole set. This is an on-demand projection
off the project record's set grid, not a new source of truth: it records nothing new, and it never changes which
sheet is current for a subject.

## What this is, and the boundary

The canonical form is the project's project record (built by `drawing-upload`). This
skill renders one view of that record as physical PDFs, for people who need to print, share, or
browse a set outside plumlayer.com. It does not read drawings, decide which sheet is current, or
record anything new, `assemble_current_set` is a pure export off the current set grid.

## 1. Pick the project

Call `list_projects` and confirm with the user which project (project record) to assemble. Get its
`projectId`. If the project has no drawings uploaded yet, hand off to `drawing-upload` first.

## 2. Start the assembly job

Call `assemble_current_set(projectId, combined?)`. `combined` defaults to true (also produce a single
"Current Set - Combined.pdf"); pass `combined: false` to skip it and only get the per-discipline PDFs,
which are always produced regardless.

It returns immediately: `{ jobId, status: "queued" | "running", alreadyActive? }`. A full set can
exceed the request window, so this never blocks inline. `alreadyActive: true` means a job for this
project is already queued or running, poll the returned `jobId` rather than starting a second one.
Each fresh run mints new output files; prior exports are left in place, so re-running doesn't
overwrite or lose anything.

## 3. Poll until done

Call `assemble_current_set_status(projectId, jobId)` every 3-5 seconds until `state` settles:

- `queued` / `running`, still working, poll again shortly.
- `stale`, the executor died mid-run; re-call `assemble_current_set` on the same project to restart.
- `failed`, read `error`, stop, and report it rather than retrying blindly.
- `succeeded`, the PDFs are assembled and registered as project files.

## 4. Report the result

On `succeeded`, tell the user:

- **The outputs**, one entry per file: filename (`Current Set - <Discipline>.pdf`, or
  `Current Set - Combined.pdf` if requested), size, page count, discipline.
- **The counts** from `report`: how many sheets were considered, how many were included, and how many
  were excluded (the two add up to the total considered).
- **What still needs a look**, always relay this, never suppress it: review-status sheets that were
  still included in the assembled PDFs (flagged, not omitted), and sheets excluded because they had
  no locatable source page. Both are the tail a human should look at before treating the set as
  final.
- **Where to get the files**, the assembled PDFs live on the project on plumlayer.com; there is
  deliberately no download link served here, so point the user there rather than looking for a path
  or URL in the tool result.

## Failure modes

- **`failed` job**, read the `error` field and report it plainly; don't retry blindly or guess a fix.
- **`alreadyActive: true`**, someone (or an earlier call in this same session) already started a
  job; poll the existing `jobId`, don't start a duplicate.
- **`stale`**, the executor died mid-run with no progress; re-calling `assemble_current_set`
  restarts cleanly.
- **High excluded count**, if the excluded count is large relative to the total considered, say so plainly
  rather than only reporting the PDFs, it usually means a chunk of the set has no locatable page yet
  and needs a `drawing-upload` residue pass.
