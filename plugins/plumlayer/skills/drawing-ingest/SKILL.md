---
name: drawing-ingest
description: >
  Ingest a construction drawing delivery in ANY packaging and turn it into cited, proposed sheet
  claims in the project's Plumlayer MOSOT — no manual conforming, no local CSV intermediate. Use
  whenever the user hands over a new drawing set, bulletin, addendum, ASI, permit/CD/conformed set,
  or any pile of drawing PDFs and wants it read, registered, indexed, or inventoried. Trigger on
  "we got a new set for <project>", "ingest this set", "register the drawings", "drawing index",
  "drawing list", "sheet schedule", "sheet inventory", "list every sheet", "what's in this drawing
  set", "index this bulletin", "franken set / current set", "/drawing-ingest". Drives project
  selection, delivery registration, cloud upload, bulk deterministic grounding, agent residue read,
  and claim deposit over the hosted Plumlayer MCP verb surface. The agent reads and judges;
  deterministic tooling grounds; nothing governs unverified. Supersedes the retired drawing-index /
  drawing-index-bulletin / drawing-index-merge skills (the export skills drawing-set-assemble /
  drawing-index-publish survive as on-demand projections off the cloud claims).
---

# Drawing Ingest — the foundation pass, agent-driven, cloud-first

Take whatever the architect actually sent, in whatever shape, and turn it into the one canonical,
grounded set of **proposed sheet claims** in the project's MOSOT. This is **Stage 0**: the first thing
that touches a delivery, before anything is split by discipline, routed, or deep-read.

Doctrine binds every stage: **agents read and judge; deterministic tooling grounds; nothing governs
unverified.** Every claim you deposit is `proposed` — a human promotes it later on plumlayer.com. You
are the reader; the MCP grounding verbs (`ground_sheets`, `render_page`, `get_page_text`) are the
anti-hallucination anchor, not the inference engine. There is no local pipeline and no server-side
autonomous reader — everything runs cloud-side over MCP, driven by you, the connected agent.

Design lineage: `agent-driven-ingestion.md` (who runs the read and where — the 2026-06-28 cloud-first
decision this skill implements) and `drawing-set-intake-design.md` (what a good read produces, the
packaging taxonomy). Examples in this file are generic; never put a real client or project name here.

## What this is, and the boundary

`drawing-ingest` does exactly one thing: take a drawing delivery and register every sheet in it as
cited, proposed claims in the project's MOSOT. The canonical form is claims + provenance over the
untouched original delivery — discipline organization, by-discipline PDFs, page labels, and a
drawing-index CSV are all **projections** of that form, rendered on demand by other skills, never the
foundation. So this skill does **not**: physically split files by discipline (discipline is derived
per sheet, never from a filename); produce a CSV (the deliverable is claims in the MOSOT — export
skills `drawing-set-assemble` / `drawing-index-publish` render artifacts from the cloud claims on
request); scope, take off, or comprehend the sheets (guarded by PLU-323 / owned by PLU-274); or create
the project (`project-create`) or promote anything (a human does, on plumlayer.com).

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

## 2 · Recognize the delivery

A delivery arrives in one of four packaging classes — recognize the class before uploading anything:

| Class | What it looks like | How you read it |
|---|---|---|
| **Combined PDF** | the whole set in one file, often mixed with specs/schedules/geotech/emails | the one drawing PDF is the source; exclude the rest |
| **By-discipline folder** | one PDF per discipline (`...Architectural.pdf`, `...Structural.pdf`) | every PDF is a source; never trust the filename for discipline — derive it per sheet |
| **Sequence splits** | arbitrary `Sequence 1 / Sequence 2` PDFs ignoring discipline | every PDF is a source; sheets carry their own discipline prefix |
| **Mixed bag** | drawings + specs + reports as separate files, no naming convention | judge each file to find which are drawings |

Filenames and folder shape *orient* you; they never *decide*. A drawing sheet has sparse text and a
sheet-number token in the bottom-right title block (`A-101`, `S-201`); a spec/geotech/narrative page has
dense body text and no corner title block. When the packaging is genuinely ambiguous (a mixed bag, or a
dual-source quirk where a combined PDF **and** a full set of per-sheet PDFs both exist), use the
**Read tool** directly on a few local candidate pages of each file to judge title-block grammar vs
spec-prose and pick the authoritative source. This local sampling is **file-selection judgment only** —
it decides which local files you upload next; it never grounds a claim, and no claim's evidence ever
cites a local read (every claim's evidence comes from the cloud grounding tools in steps 5–6).

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

## 5 · Ground

Call `register_pages(projectId)` **once** for the project — it registers viewable page rows for every
uploaded PDF (not claims, just renderable pages) and only needs to run once per project, not per file.

Then call `ground_sheets(projectId, fileId, deliveryId)` **once per file** — the deterministic
server-side pass that grounds the title-block sheet number + title on most pages of that PDF. Report
the real counts from the result: `pagesScanned`, `sheetsGrounded`, `highConfCount`, `flaggedCount`,
`extractionWarningCount`, `calibrated`, `capHit`. Never assume "N pages scanned = N sheets grounded" —
state both numbers. `confidence` on individual claims is triage/review-priority metadata only, never a
trust tier; every claim here is already `proposed`.

For a multi-file delivery, ground every file separately (each call returns its own `residue` and
`depositClaims`); there is no merge step and no `SET_TAG` — everything pools at deposit time (step 7)
because it all shares one `deliveryId` in one project.

## 6 · Residue read

`ground_sheets` returns `residue`: the tail where the deterministic pass is least sure (low confidence,
no sheet number found, or a degraded text layer). Read and judge every residue row yourself:

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
  PLU-186). Report the flagged page list; an honest "could not ground these N pages" beats a guess.

For every residue subject you *do* resolve, author the **full bundle** of claims, mirroring the shape
`depositClaims` produces for the pages the deterministic pass already grounded (matching predicate and
value shapes keeps every sheet's claim set uniform regardless of which stage grounded it):

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

## 7 · Deposit + verify

Before your first deposit call for this delivery, check whether it already holds deposited sheet
claims — e.g. `search(projectId, predicate: "partOfIssue", text: <deliveryId or label>)`, or check
whether `set_grid` rows already resolve to this `deliveryId`. If claims already exist for this
delivery, **stop and confirm with the user** before depositing again — never silently re-ingest the
same package twice.

Once clear, deposit via `propose_batch(projectId, claims)`:

- **Deposit `depositClaims` only — never also the raw `claims` array.** `depositClaims` (present on the
  `ground_sheets` result whenever a delivery is known) already contains normalized copies of every raw
  claim plus `locatedAt` / `discipline` / `partOfIssue`; depositing both would double-write every sheet.
- Pool this file's `depositClaims` with the residue bundles you authored in step 6 into one array per
  project (across every file in a multi-file delivery — no separate merge artifact).
- `propose_batch` accepts 1–500 entries per call and is atomic (one bad entry rejects the whole batch,
  naming the index). Chunk the pooled array into consecutive slices of ≤500 and call it once per slice,
  transporting each slice **verbatim** — an exact array slice of what `ground_sheets` returned or what
  you authored, never re-typed from memory.
- **Verify every call**: the returned `count` must equal the number of entries you sent in that call. If
  it does not, stop and report the discrepancy rather than retrying with a guessed correction.

After the last batch, call `set_grid(projectId)` to confirm the sheets now resolve under this delivery,
and name any that don't (unresolved residue, still-flagged image-only pages). Point remaining
ambiguities at `ambiguities(projectId)` — the review queue, not something this skill resolves itself.
Report: project, delivery, total claims deposited (sum of count-verified batches), residue read vs.
flagged, and that the claims are visible for review/promotion on plumlayer.com.

## Gates (non-negotiable)

- Every deposited claim's evidence is grounded **cloud-side** — a `ground_sheets` output or a
  `render_page`/`get_page_text` read you just made. A local read (step 2) may inform the packaging
  report; it never grounds a claim.
- Discipline is derived from the sheet's own number prefix, never a filename or folder.
- Residue is judged-or-flagged, never silently dropped; image-only pages are named, not guessed.
- Everything deposited is `proposed`. This skill never promotes.
- Deposit is verbatim, count-verified transport — a count mismatch stops the run, never triggers a
  reconstructed or invented entry.
- Before any deposit, check for an already-ingested delivery and confirm with the user rather than
  double-depositing.
- Honest coverage at every stage — pages skipped, files excluded, or residue left unread are named, not
  buried in a total.

## Cost (cheapest tier first)

`ground_sheets` (the deterministic bulk pass) is free server-side compute — it grounds the large
majority of sheets in seconds. Your token cost is fenced to the residue tail: the pages the pass
couldn't ground, read once each. The local packaging-recognition sampling (step 2) is small, bounded to
a few pages per ambiguous candidate file, and named in the packaging report — not a hidden cost. No
GPU or model hosting on this path.

## Deferred (named, not skipped silently)

- **OCR for image-only/scanned pages (PLU-186).** No text layer means both the bulk pass and your own
  read come up empty; flag, don't guess.
- **Scale auto-detect at intake (PLU-277).** Not built into this skill yet.
- **Master-list reconciliation as corroboration only.** A full diff against an architect drawing list
  (to surface RFI-worthy discrepancies) is a corroboration layer, never the bootstrap for this skill.
- **Discipline-uncertainty compensation.** The server's prefix-based discipline derivation has a known
  gap for unusual prefixes (PLU-334); this skill does not add client-side heuristics to cover it.
