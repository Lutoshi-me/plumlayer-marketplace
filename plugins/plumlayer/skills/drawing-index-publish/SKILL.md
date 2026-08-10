---
name: drawing-index-publish
description: >
  Publish the project's Master Drawing Index Excel workbook straight off the cloud project record's set grid —
  a Current Set tab, one tab per drawing delivery (chronological), and a trailing Review tab of
  sheets that still need a look. Use whenever the user asks to publish, build, or generate the Master Drawing Index, the
  drawing index workbook, or an xlsx/Excel version of the drawing index. Trigger on "master drawing
  index", "publish the drawing index", "drawing index workbook", "drawing index xlsx", or
  "/publish-drawing-index". Drives project selection and the `publish_master_index` /
  `publish_master_index_status` hosted MCP verbs — an async job you start then poll. The verb is a
  read-only PROJECTION off the set grid: it records nothing new and changes no selection policy, it
  only registers the workbook as a project file. The workbook's Open links jump straight to the sheet in
  the plumlayer.com viewer. Output is downloaded from the project on plumlayer.com; there is no
  download verb. Do NOT use this skill to assemble the PDFs — that is `drawing-set-assemble`.
  Requires a project whose drawings were already registered via `drawing-upload`.
---

# Drawing Index Publish — Master Drawing Index.xlsx

## Talk to your user like an estimator

Verbs, claims, and trust classes are machinery for you, never words the user reads. Speak estimator
words to them: project record, entry, sheet, set, scale, scope item, bid response, flagged item,
trail. Never say to the user: claim, deposit, predicate, subject, proposed, governing, trust class,
supersede, promote, reconcile, QA, sheet type as "sheetType", grounding, residue, or any raw verb or
field name. Translate instead: a value you replaced is "I updated my earlier read"; a machine
mis-read you caught is "the automatic scan grabbed the wrong text, so I read the sheet and flagged
it for you to set on the site"; cross-checking the index is "checking the drawing list against the
actual sheets". Plain prose, no em dashes, no bolded emphasis words. Full guidance is in the
project-record skill's Words section.

Publish a single Excel workbook that lays out the project's whole drawing history: the current set,
every delivery in order, and the sheets that still need review. This is an on-demand projection off
the project record's set grid, not a new source of truth: it records nothing new, and it never changes which
sheet is current for a subject.

## What this is, and the boundary

The canonical form is the project's project record (built by `drawing-upload`). This
skill renders one view of that record as a workbook, for people who want a spreadsheet to browse or
share. It does not read drawings or decide anything — `publish_master_index` is a pure export off the
current set grid.

## 1 · Pick the project

Call `list_projects` and confirm with the user which project (project record) to publish. Get its
`projectId`. If the project has no drawings uploaded yet, hand off to `drawing-upload` first.

## 2 · Start the publish job

Call `publish_master_index(projectId)`. It returns immediately: `{ jobId, status: "queued" |
"running", alreadyActive? }`. A full index can exceed the request window, so this never blocks
inline. `alreadyActive: true` means a job for this project is already queued or running — poll the
returned `jobId` rather than starting a second one. This is independent of `assemble_current_set` —
the two use different job slots, so one may run while the other is active. Each fresh run mints a new
workbook file; prior publishes are left in place.

## 3 · Poll until done

Call `publish_master_index_status(projectId, jobId)` every 3-5 seconds until `state` settles:

- `queued` / `running` — still working, poll again shortly.
- `stale` — the executor died mid-run; re-call `publish_master_index` on the same project to restart.
- `failed` — read `error`, stop, and report it rather than retrying blindly.
- `succeeded` — the workbook is built and registered as a project file.

## 4 · Report the result

On `succeeded`, tell the user:

- **The workbook** — filename (`Master Drawing Index.xlsx`), size, and its tabs from `report`: a
  Current Set tab, one tab per drawing delivery in chronological order, and a trailing Review tab —
  each with its row count.
- **What still needs a look** — always relay this, never suppress it: the Review tab holds
  review-status sheets still in the current set, and sheets excluded from the current set for having
  no locatable page. Say how many rows are in that tab, not just that it exists.
- **The Open links** — every sheet row's Open link jumps straight to that sheet in the plumlayer.com
  viewer, not a local file path — clicking it takes the user into the live project, not a PDF page.
- **Where to get the file** — the workbook lives on the project on plumlayer.com; there is
  deliberately no download link served here, so point the user there rather than looking for a path
  or URL in the tool result.

## Failure modes

- **`failed` job** — read the `error` field and report it plainly; don't retry blindly or guess a fix.
- **`alreadyActive: true`** — someone (or an earlier call in this same session) already started a
  job; poll the existing `jobId`, don't start a duplicate.
- **`stale`** — the executor died mid-run with no progress; re-calling `publish_master_index`
  restarts cleanly.
- **Large Review tab** — if the Review tab's row count is large relative to the Current Set tab, say
  so plainly — it usually means a chunk of the set still needs a `drawing-upload` residue pass before
  the index is trustworthy as a full picture.
