# Drawing upload: the cloud-resident entry

Read from `drawing-upload` step 1c, only when the drawings are already in the project and the user
handed you no local files. Every step this file names is a step of `drawing-upload`'s own
`SKILL.md`, and every gate there applies here unchanged.

The branch substitutes the local-only stages and reuses everything else unchanged:

- **Enumerate instead of recognize packaging (replaces step 2).** `list_files(projectId)` is your
  source list: each row carries `fileId`, `filename`, `sizeBytes`, and its `deliveryId` (or null).
  Apply step 2's judgment to that list: which files are drawings and which aren't. When a filename
  doesn't decide, write a small pages file naming the file's first page or two with the reason
  `file` and dispatch a pages unit over it: on this branch even the file-selection sampling is
  cloud-side, since there are no local bytes, and the unit's `files:` line says what each page is.
<!-- user-facing -->
Emit the same packaging
  report: which files you will recognize, which you're excluding and why.
<!-- /user-facing -->
- **Delivery attribution instead of registration (replaces steps 3–4).** Read each drawing file's
  `deliveryId` from `list_files`, cross-referenced against `list_drawing_deliveries(projectId)`:
  - **Attributed**: the file already carries its delivery. Reuse it; never register a duplicate
    delivery for the same issue.
  - **Unattributed** (`deliveryId: null`): surface the gap to the user; never invent attribution.
    Establish which issue the files belong to (ask, or have a pages unit read the cover sheet with
    the reason `file`: its `files:` line gives the issue label, date and sequence the cover prints,
    each with its page and the words as printed, and says which it does not print), register the
    delivery per step 3 if it doesn't exist yet, and pass its id as
    `recognize_sheets.deliveryId` in step 5: that is the supported attach mechanism for an
    already-registered file (a `register_file` retry returns the existing row; it does not
    re-attribute). Chronology still comes from the documents: `issuedOn` off a cover sheet or
    revision table, never upload time.
  - **Mixed attribution** across files is legitimate (files from different deliveries live in one
    project): recognize each file against its own delivery; what you must not do is guess a delivery
    for the unattributed ones or pass a `deliveryId` that disagrees with a file's registered one
    (the server refuses the mismatch).

From here the pipeline is identical: step 5 (`register_pages` once, then `recognize_sheets` per file,
pass `deliveryId` explicitly for any file whose registration doesn't carry it), step 6 (the sheet
checker's units: the pages the pass could not name, the sheet typing, the corrections), step 7
(verify). Every gate applies unchanged.

**Re-recognize semantics (the honest limits).** Re-running `recognize_sheets` on a file+delivery is
always safe: a `stale` or `failed` job restarts; a `succeeded` one returns the existing job and the
write stays idempotent. That also means this branch cannot force a fresh read of a file+delivery
that already succeeded: a corrected re-read after a bad run needs a force-re-recognize path, which
is not built yet. Say so plainly rather than re-running and implying new output.

**Idempotent recognition is not evidence of typing coverage.** A `succeeded` job returning
unchanged tells you nothing about whether step 6 ever ran for these sheets. A delivery recognized
before this skill carried a typing stage, or one whose earlier run stopped short of it, looks
identical from `recognize_sheets_status` alone to a fully typed one. Before this branch reports
done, check typing coverage directly (as in step 7's verify) rather than inferring it from the
job's idempotent success. The force-re-recognize gap above is a recognition-fidelity limit only;
it is never license to skip the typing check, which does not depend on it.
