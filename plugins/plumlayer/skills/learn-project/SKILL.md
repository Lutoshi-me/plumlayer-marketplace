---
name: learn-project
description: >
  A cheap orientation pass over an already-uploaded drawing set: reads seed facts and sheet
  inventory, takes a few bounded renders (cover, index, key plans), records cited facts, writes the
  project description, and drafts and creates the baseline trade-package split off the spec table of
  contents. Trigger on "learn the project", "orient on this set", "orientation pass",
  "/learn-project". Drives search, set_grid, render_page, get_page_text, record_batch,
  update_project, directory_list_trades, solicitation_list_packages, solicitation_create_package.
  Does not upload drawings or run scope-run.
---

# Learn project: the cheap orientation pass (stage 1)

The first stage of a scope run. Before anything is read deep, one cheap pass over what's already
recognized builds the project's **context**: what it is, its structural and envelope systems, its
scope areas, the shape of the set, and what's missing. Every later pass in the scope run
gets this context instead of orienting from scratch, which is where reads get unreliable.

Doctrine binds every step: **agents read and judge; deterministic tooling grounds; nothing enters
untraced.** This is an *orientation* pass, not comprehension, it reads what upload already
recognized, takes a handful of bounded renders, and stops. Everything it emits is **your own reading**,
cited, and it becomes the project's working context the moment it lands, so what you raised a
Question about as inferred is what a person should judge. Examples in this file are generic, never put a real
project name, client data, or a real extracted value here.

## What this is, and the boundary

`learn-project` reads an already-uploaded set, records **net-new** project-level orientation entries,
compiles a packet from them, and drafts and creates the baseline trade-package split off the spec
table of contents (Phase 1 of package derivation). So it does
**not**: upload a drawing delivery (precondition, owned by `drawing-upload`); extract spec sections
itself (it reads the spec-section index if `drawing-upload`'s later spec-reading work has already
recorded one, it never extracts specs); or run any of the later scope-run stages, reading the set in
rounds, building the one scope list, amending the package split, or tagging items to a trade (all
owned by `scope-run`). Amending the split (Phase 2) is `scope-run`'s job; creating the baseline split
is this skill's.

The run-context packet this skill compiles is a **projection**, never stored as truth, the same
pattern as a trade package. It lives in the user's local run folder only, never a repo, never
the project record.

## 1. Preconditions

1. **Project exists.** Call `list_projects` and confirm with the user which project record this orientation pass
   is for, get its `projectId`. If there is no project yet, hand off to `project-setup` first, the
   same way `drawing-upload` step 1 does.
2. **The baseline set is recognized.** Orientation reads the base set shape, it does not need revisions
   or bulletins to have landed, and spec-TOC presence is optional/best-effort, not a precondition.
   What it does need is a delivery that has actually been through `recognize_sheets`. There is normally no
   retained `jobId` to poll at orientation time (that job ran, and finished, in an earlier session), so
   confirm recognition by its observable effect rather than by re-polling a job you don't hold: call
   `list_drawing_deliveries(projectId)`, if none exist, stop plainly and hand off to `drawing-upload`.
   If a delivery exists, spot-check with a small `search(projectId, predicate: "appearsOnPage", limit:
   1)`, zero rows means recognition hasn't actually recorded anything yet; stop and hand off to
   `drawing-upload` rather than orienting on an empty set.
3. **Trade knowledge present.** Read `${CLAUDE_PLUGIN_ROOT}/trade-knowledge/MANIFEST.md`; record the
   version for use in step 7's package rationale. Missing means a broken plugin install: stop and
   report rather than drafting a package split knowledge-blind.

## 2. Read the entries (identity, seeds, sheet inventory)

1. `get_project(projectId)`, the project's identity (name, description, created date).
2. **Read the `project-setup` seed entries verbatim, never re-create them.** For each of `projectType`,
   `deliveryMethod`, `location`, `grossArea`, `floorCount`, `bidDueDate`, `tradeInScope`,
   `knownExclusion`, call `search(projectId, predicate: "<predicate>")` and read what's there. These
   feed the packet's Identity section directly; where a seed is thin or missing, orientation may add a
   document-grounded entry on the same predicate later (competing entries on one slot resolve at review,
   no bespoke merge here).
3. **Sheet inventory.** Call `list_drawing_deliveries(projectId)` for the registered deliveries, then
   attempt `set_grid(projectId)` once. A set_grid payload on a set of real size can be large enough to
   file-redirect instead of returning inline, if that happens, fall back to sampled
   `search(projectId, predicate: "discipline")` calls for the disciplines you need (A, S, M, P, E, C, G)
   rather than pulling the full grid. Either path gives you discipline, sheet number, and governing
   issue per sheet, plus the file/page reference each row carries, the render targets for step 5 come
   from here, not from a separate `list_files` call.

## 3. Read the spec-section index, if present

Call `search(projectId, predicate: "inDivision")` for `specSection:<csi>` subjects, **paging through
every result to the real total** rather than a sample: this is the anchor step 7's package split
drafts from, and a partial read under-declares the job the same way a silent TOC does. When spec
reading has run for a project, these entries are real and cited, `hasTitle`, `locatedAt`, `inDivision`,
and `partOfIssue` on each section (verified on at least one live project). Extraction now ships as
`drawing-upload`'s spec-TOC leg (its step 8, wired to `extract_spec_toc` / `extract_spec_toc_status`),
a project whose drawing-upload pass has run that leg will have these entries. What's still true is that
not every project has run it yet, a set uploaded before the leg shipped, or a manual that arrived
after the drawings and hasn't been filed and extracted, so **some projects won't have these entries
yet**, that is a gap in what's been run for this project, not a missing capability.

- **A section the table of contents lists but no page footer confirmed** is on the record too,
  with a `hasCompletenessStatus` saying no section text was found. It anchors the split like any
  other section (the trade is still bought), and the packet names the count of those separately
  so the split's footing is stated: "110 sections confirmed, 12 more listed in the table of
  contents only". An outline specification at schematic or design development is often all of the
  second kind; that is a complete read of that manual, not a reason to skip the split.
- **If present:** read the division spread and section count into the packet's set-shape section.
- **If absent:** write "spec reading hasn't run for this project" in the packet's set-shape section
  and continue. Never write "expected empty today," never treat absence as the norm, and never let this
  block the rest of the pass.

## 4. Read the reconciliation report, if the gate has run

The pre-read reconciliation gate (`drawing-upload` step 9) checks the delivery's drawing index
against the sheets actually present and the spec sections, before
anything reads the set for scope. Its findings are orientation-grade facts, a sheet the index lists
that never arrived, or a sheet in the set the index never mentioned, changes what "the set" means
before you read a single plan.

Call `reconcile_set(projectId)` **report-only** (never pass `record`), this step reads the gate's
findings, it never records those findings itself, and recording is not this skill's decision to make. The
bare call (no `deliveryId`) runs the ORIENTATION check: the index of record, the newest delivery
that actually has a read drawing index, against the current compiled set across every delivery,
which is what an orientation pass over the whole project wants. `result.mode` reports which
comparison ran.

- **If the gate has already run for this set:** read the report's counts, what matched, what
  the index lists that isn't in the set, what's in the set the index doesn't list, and whether the
  spec comparison ran. Fold anything real into the packet: an unmatched index entry as a
  `missingScopeFamily` or `setShapeObservation` candidate (per step 6's rules, raise a Question if inferred),
  and an unrecognized-in-index sheet as a `setShapeObservation`. Before citing anything from
  `report.declaredLedgerDrift`, check `.ran` first, it's `false`, never a hollow zero, whenever no
  index page could be read at all, or a receiving-check run had to widen its re-read to another
  delivery's pages; a drift check that didn't run is never folded into the packet as if it found
  nothing.
- **If it hasn't run yet** (no drawing index was ever parsed for any delivery in this set, `reconcile_index`
  has not been called, or `reconcile_set` reports nothing to compare), write "the reconciliation gate
  hasn't run for this set" in the packet's set-shape section and continue. Never write "no
  discrepancies found" for a check that never ran.
- **When the spec leg specifically didn't run** (no project manual read yet), the report says so
  itself, carry that distinction into the packet rather than collapsing it into the same "hasn't
  run" note as the whole gate.

## 5. Bounded renders (budget: at most 6 total)

Use the file/page references already surfaced by step 2's sheet inventory to pick `fileId` /
`pageInPdf` targets, don't call `list_files` separately for this. For every render, pair `render_page`
with `get_page_text` on the same page (render for layout and meaning, text for exact tokens).

1. **Cover sheet (1 render).** Find it via `search(projectId, predicate: "hasTitle", text: "cover")` or
   `text: "title sheet"`. If neither turns up a match, fall back to the lowest G-series sheet number in
   the inventory; if there's no G series either, fall back to the lowest sheet number in the set overall.
   Whenever you use a fallback, record a `setShapeObservation` entry naming the substitution (e.g. "no
   hasTitle match for a cover/title sheet; used the lowest G-series sheet instead").
2. **Drawing-index page (1 render).** Find it via `search(projectId, predicate: "hasTitle", text:
   "index")`, `"drawing list"`, or `"sheet list"`. If none of these match, **skip the render** and note
   the absence in the report, never synthesize an index page that isn't there.
3. **Key plans (up to 4 renders).** For each series in this order, **A**, then **S**, then **M/P/E**
   (one representative render for whichever of M, P, E exists first, in that order, it counts as one
   slot, not three), then **C**, render the lowest-numbered sheet you judge, from its title and
   position in the inventory, to actually be a plan (not a detail, schedule, or elevation) in that
   series, and only if the series exists in the inventory at all. A series that is genuinely absent from
   the inventory renders nothing for that slot and instead becomes a `missingScopeFamily` candidate in
   step 6, don't force a render to fill the slot.

If the set is large enough that six renders plainly can't cover it (many buildings, many phases, an
unusually deep set), say so explicitly in the report rather than quietly rendering more.

## 6. Emit orientation entries

All net-new, subject `project` unless noted, recorded via **one** `record_batch(projectId, entries)`
call:

| Predicate | Value shape | Question rule |
|---|---|---|
| `structuralSystem` | free text, one entry per system (e.g. "post-tensioned concrete flat plate") | raise a Question if inferred rather than labeled on the drawings |
| `envelopeSystem` | free text, one entry per system (e.g. "unitized curtain wall") | raise a Question if inferred |
| `mepDeliveryShape` | `{division, shape}`, `shape` ∈ `full-design` \| `design-build-thin`, one entry per MEP division present | **always raises a Question**, this is a judgment entry |
| `scopeArea` | free text, one entry per area (e.g. "below-grade parking", "amenity terrace") | raise a Question if the boundary was inferred rather than labeled |
| `phasingNote` | free text (e.g. "occupied renovation, phased by wing") | raise a Question if inferred |
| `setShapeObservation` | free text (e.g. "schedules live on the A-10 series") | usually no Question, a direct observation |
| `missingScopeFamily` | free text (e.g. "no Division 31 Earthwork/SOE sections in the TOC") | **always raises a Question**, an absence entry is defeasible |
| `hazardFlag` | free text (e.g. "occupied renovation, coordinate around active tenants") | raise a Question when inferred from context rather than stated outright |

**Question text is plain estimator words, not the table above.** Whichever column above triggers
the raise, what actually lands in `ask_question`'s title and body states what was seen and what
needs deciding, in a sentence a person on the job site would write. It never names a predicate, an
internal step, a field, or another question by its internal name, and it carries no em dash
(docs/plugin-text-style.md states the same rule for every other piece of user-facing text).

Good: "The electrical drawings show a full design, stamped and dimensioned, but no electrical spec
section confirms it. Is this trade full design or design-build?"

Bad:
```text
mepDeliveryShape classified as full-design for Division 26 — no Division 26 spec section
was footer-confirmed in the spec-section index (see the related missingScopeFamily
question). Please confirm this delivery-shape classification.
```

**`sourceInstrument` is per-entry, not one batch label.** For an entry grounded
in a specific page or render, cite the specific source file/instrument name, the same convention
`drawing-upload` and `project-setup`'s Mode B (reading in existing docs) use. Reserve the label
`learn-project-orientation`
only for derived or absence observations with no single source page: `missingScopeFamily` and any
set-level `setShapeObservation`. Every entry's `evidence` cites the exact page/render or query of entries
that produced it, never a fabricated locator.

Call `record_batch` once with the full array. **Verify:** the returned `count` must equal the number of
entries sent; a mismatch stops the run and gets reported, never a guessed correction.

## 7. Draft the baseline package split and create the packages

Phase 1 of package derivation: the cheap, high-value baseline split, drafted here so a package
already exists for every trade before the expensive scope read starts. Phase 2, the scope-driven
amendments, stays in `scope-run`.

1. **Read what's already on the project.** Call `solicitation_list_packages(projectId)` first. This
   step is match-or-create: never create a package whose catalog trade id already has one on the
   project. Report existing packages as "already on the project" rather than re-drafting them.
2. **No spec sections, no split.** If step 3 found no `inDivision` entries for this project, create
   no packages. Drawing disciplines are never used as an anchor for a split. Say plainly, in the
   packet and the report: spec reading hasn't run for this project
   (the remedy is to upload the project manual through `drawing-upload`'s spec-book leg and re-run
   this skill); if the project genuinely has no spec book, the scope run derives the packages from
   the finished scope list instead. No question asked, no branch beyond this sentence.
3. **Draft the split** from the spec TOC (step 3) plus the trade knowledge base's market
   conventions: which sections bundle into which package, which get carved out, a primary CSI
   section per package. Probe the usually-present families the TOC is silent on (site/civil, SOE,
   landscaping/exterior improvements, thin design-build MEP divisions), the same probe that already
   produces `missingScopeFamily` entries (step 6): a silent family becomes a `missingScopeFamily`
   entry AND, where the trade knowledge says the trade is usually present, a package.
4. **Resolve every package to the trade catalog** via `directory_list_trades`: exact `code` lookup
   first, then a `query` by trade name or alias. Record the catalog trade id verbatim; never guess
   an id from memory (store-resolution). A package with no reasonable catalog match cannot be
   created (the verb requires a catalog code): name it in the report as "no catalog trade, not
   created," never force a wrong code.
5. **Create each missing package** with `solicitation_create_package(projectId, tradeCode, name,
   codes, notes)`: name = the package display name; `tradeCode` is the package's primary section;
   `codes` lists the other sections bundled into it (verbatim catalog ids from the same
   `directory_list_trades` resolution as step 4, never repeating `tradeCode`); `notes` carries a
   one-line rationale in plain prose, no fixed shape. Count-verify: re-list packages
   (`solicitation_list_packages`) and confirm every created one landed.
<!-- user-facing -->
6. **Show the split as what you did, not as a question**, mirroring `scope-run`'s wording: "I split
   the job into N packages; here they are. Change any of them on the site or tell me and I will
   redo it." No approval is collected.
<!-- /user-facing -->

## 8. Write the project description

`get_project`'s `description` field answers "what is this job?" for someone opening the project
cold. This is the first pass with enough of a read on the set to write one, so it writes it here,
once, after the entries above are recorded and before the report.

1. **Leave a person's description alone.** Re-check the `description` read in step 2.
   `get_project` exposes no trail for this field, no author, no write time, so a Learn run cannot
   tell its own past write from a person's edit. Treat any non-empty description as a person's:
   leave it as is and say so in the report. Only an empty description gets written below.
2. **Write what the job is.** What the building is, what work is being done, for whom, where, and
   whatever makes this job different from a typical one, in plain estimator prose. Every statement
   traces to something read this run, a render, a page, a seed entry, or an entry recorded in step
   6; a genuine differentiator you would otherwise infer instead of read gets raised as a Question
   the same way any other orientation judgment is, not folded into the description unconfirmed.
3. **Leave out what already has a field.** Total SF, floor count, bid due date, status, structural
   or envelope system, and any sheet or spec bookkeeping already live as their own entries;
   restating them here duplicates the record instead of orienting a reader. Leave out narration of
   how the set was read too, this is what the job is, not how it was learned.
4. **No length target.** As long as the job needs and no longer.
5. Call `update_project(projectId, description: "<text>")`. This is the only field on the project
   row this skill ever writes.

## 9. Compile the run-context packet

A projection compiled fresh from the entries read in step 2 and recorded in step 6, **never itself
recorded as an entry, never stored as truth.** Sections, in order:

1. **Identity**, name, type, delivery method, location, size, key dates (from the seed entries).
2. **Systems**, structural and envelope systems, MEP delivery shape per division.
3. **Scope areas**, the `scopeArea` and `phasingNote` entries.
4. **Set shape**, disciplines present, issue labels seen, `setShapeObservation` entries,
   `missingScopeFamily` entries, the spec-TOC status (division spread + count, or the "hasn't run
   yet" note from step 3), and the reconciliation-gate status (its report counts, or "hasn't run yet"
   from step 4).
5. **Hazards**, the `hazardFlag` entries.
6. **Packages**, the packages on the project after step 7: name, catalog trade id, primary section,
   bundled sections, per package, or the "spec reading hasn't run for this project" note when step 7
   created none.
7. `[PLACEHOLDER, definitions-as-context envelope]`, a clearly marked final section; this
   skill does not design that envelope, it only reserves the slot.

Write it to `~/.plumlayer/runs/<project-slug>/learn-project-packet.md` (the same local run folder
the `scope-run` skill uses), derive `<project-slug>` from the project name (lowercase, spaces to
hyphens) or fall back to the `projectId` if the name doesn't produce a clean slug. Never write it
into a repo, and never record it as an entry. Regenerate it in full the next time this skill runs for the project, it is a projection,
not a document to patch. Audience: agent. Its path is handed to the user at run end (step 10) and
its content orients later readers; whatever crosses from it into user-facing text becomes
user-facing at the crossing and is translated there.

## 10. Report

<!-- user-facing -->
Tell the user, in plain terms:
- **What was read**, identity, which of the seeded project facts were present, the sheet-inventory
  scope (disciplines covered, set_grid vs. sampled search), and the spec-TOC status.
- **What was learned**, per checklist category, systems, MEP delivery shape, scope areas, set shape,
  hazards.
- **What the reconciliation gate found**, or that it hasn't run yet for this set, never silent on
  which.
- **What was recorded**, how many entries, and how many raised a Question for a person's judgment,
  for example "recorded 14 project facts, 3 questions for your judgment". What you recorded is the
  project's working context now, carrying your name and citations; anything a person changes wins.
- **The package split**, packages created, packages already present on the project, any package
  named "no catalog trade, not created," TOC sections deliberately unbundled, or the "spec reading
  hasn't run for this project" note when no spec sections exist.
- **The description**, whether you wrote one or found a person's already in place and left it, say
  which.
- **Where the packet landed**, the full path.
- **The placeholder note**, the definitions-as-context section is a stub, not yet designed.
- **What a person should look at**, the entries with Questions raised, visible on plumlayer.com with the
  page each one was read from.

Close by saying orientation is done and everything it made is on the project record.
<!-- /user-facing -->

## Gates (non-negotiable)

- **Cite everything.** No citation → don't emit the entry.
- **Net-new facts only.** Never re-create a seed entry `project-setup` already recorded, or a sheet /
  spec-section entry `drawing-upload` already recorded.
- **Judgment entries are cited and raise a Question.** `mepDeliveryShape` always does; the rest raise
  one whenever the value was inferred rather than read off a label.
- **A Question is about the project, never about a Plumlayer failure.** A render or read that
  fails is reported in the conversation, not raised as a Question.
- **Say it is your reading.** These entries become the project's working context immediately, so an
  inferred value that reads as a documented one is the failure to avoid.
- **Orientation, not comprehension.** Respect the ≤6 render budget, if the set is too large for it to
  cover meaningfully, say so in the report rather than silently exceeding it.
- **The reconciliation gate is read, never run or recorded, by this skill.** Step 4 reads
  `reconcile_set` report-only; a gate that hasn't run for this set is named as not having run, never
  paraphrased into "no discrepancies."
- **The packet is a projection only.** Never recorded as an entry, never written to the repo, always
  regenerated in full on the next run rather than patched.
- **The split anchors on the spec table of contents, never on drawing disciplines.** No spec
  sections on the project means no packages, and the report says so plainly.
- **Packages are match-or-create; a re-run never duplicates one.** Read `solicitation_list_packages`
  first and skip any catalog trade id already represented on the project.
- **Status is a person's categorization; no skill sets it.** Orientation's only write to the
  project row is `description`, and only when a person hadn't already written one.

## Deferred (named, not skipped silently)

- **The definitions-as-context envelope.** The packet's final section is a placeholder only; how
  orientation and definitions-first context share one envelope's context window is a design question
  for a future skill, not this one's.
- **Spec-section extraction as a packaged skill.** Extraction now
  lives in `drawing-upload`'s spec-TOC leg (step 8); step 3 above still only reads spec-section entries
  if they already exist, it never extracts them itself. A project whose drawing-upload pass predates
  that leg, or whose manual hasn't been run through it yet, still hits the "hasn't run yet" branch in
  step 3.
