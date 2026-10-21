---
name: learn-project
description: >
  A cheap orientation pass, in a fresh agent, over an uploaded set: reads seed facts and
  sheet inventory, takes a few bounded renders (cover, index, key plans), records cited
  facts, writes the project description, and drafts and creates the baseline trade-package split
  off the spec table of contents. Trigger on "learn the project", "orient on this set", "orientation pass",
  "/learn-project". Drives search, set_grid, render_page, get_page_text, record_batch,
  update_project, directory_list_trades, solicitation_list_packages, solicitation_create_package.
  Does not upload drawings or run scope-run.
---

# Learn project: the cheap orientation pass (stage 1)

The first stage of a scope run. Before anything is read deep, one cheap pass over what's already
recognized builds the project's **context**: what it is, its structural and envelope systems, its
scope areas, the shape of the set, and what's missing. Every later pass in the scope run
gets this context instead of orienting from scratch, which is where reads get unreliable.

Doctrine binds every step: agents read and judge; deterministic tooling grounds; nothing enters
untraced. This is an *orientation* pass, not comprehension, it reads what upload already
recognized, takes a handful of bounded renders, and stops. Everything it emits is your own reading,
cited, and it becomes the project's working context the moment it lands, so an inferred value says
it was inferred and cites what it was read from. Examples in this file are generic, never put a
real project name, client data, or a real extracted value here.

## What this is, and the boundary

`learn-project` reads an already-uploaded set, records net-new project-level orientation entries,
compiles a packet from them, and drafts and creates the baseline trade-package split off the spec
table of contents (Phase 1 of package derivation). So it does
not: upload a drawing delivery (precondition, owned by `drawing-upload`); extract spec sections
itself (it reads the spec-section index if `drawing-upload`'s later spec-reading work has already
recorded one, it never extracts specs); or run any of the later scope-run stages, reading the set in
rounds, building the one scope list, amending the package split, or tagging items to a trade (all
owned by `scope-run`). Amending the split (Phase 2) is `scope-run`'s job; creating the baseline split
is this skill's.

The run-context packet this skill compiles is a **projection**, never stored as truth, the same
pattern as a trade package. It lives in the user's local run folder only, never a repo, never
the project record.

## Running one level down

The steps below run in a fresh agent, never in the session that starts this skill. That agent's
renders, spec page reads, package lists and package creates would otherwise stay in the session
the user talks to for the rest of it, and on a set of a few hundred sheets with its manual they
once filled most of that session. A user typing /learn-project, `project-setup`, and `scope-run`'s
orientation stage all start it the same way:

1. Know the project. `project-setup` and `scope-run` hand you its `projectId`. When a user typed
   /learn-project, call `list_projects` and confirm with the user which project record this
   orientation pass is for. If there is no project yet, hand off to `project-setup` first, the same
   way `drawing-upload` step 1 does, and dispatch nothing.
2. Dispatch one fresh general agent with the orientation dispatch below. The call is the wait.
3. Read back only its summary. Never relay the agent's own wording to the user and never open the
   packet to retell it: what orientation learned is on the record, and the summary says where.
   Where the summary did not arrive in the message, its summary file is the summary: open that
   file rather than dispatching again.

```text
run_in_background: false
Project: <projectId>. Project folder: <~/.plumlayer/runs/<project-slug>/>.
You are the orientation agent. Run the `learn-project` skill for this project from step 1, in
full, exactly as it is written. Write your summary to <project folder>/learn-project-summary.md
in the shape its "Running one level down" section gives, then return it and end.
```

An agent whose dispatch names it the orientation agent skips this section and starts at step 1,
with the project its dispatch names. A client with no agent tool runs steps 1 to 11 itself, in the
conversation, and at step 11 tells the user what the block below says rather than returning a
summary.

The summary, written to the path the dispatch names and returned in this shape, counts and named
items only (Audience: agent; the session that started the skill words it for the user):

```text
sheets seen <n>   index findings <n>   spec sections <n>   packages drafted <n>   questions <n>
stopped: <the precondition that failed and why, or "no">
learned: <each fact recorded in step 6, its predicate and its value as recorded, cut at 200 characters, one per line>
reconciliation: <the gate's counts, or "not run for this set">
spec reading: <sections confirmed + listed in the table of contents only, or "not run for this project">
structure: <filled, the sheet that grounded the system + the sheet that grounded the floor counts; or blank, the half the set does not state>
description: <written, or a person's left in place>
packages: created <n>, already on the project <n>, no catalog trade <names, or "none">
furnish and install: <the supplier's package + the package that installs its items, one per line, or "none">
defaults: <package + the default it follows, one per line, or "none">
sections placed: <n> of <n>, or "count incomplete"
on no package: <section code + its reason, one per line, or "none">
questions raised: <the id of each Question raised, or "none">
renders: <n> of 6, <"covered" or "the set is too large for six">
packet: <path>
```

`questions` on the first line counts the Questions raised; `packages drafted` counts the packages
created this run.

<!-- user-facing -->
Where a user typed /learn-project, tell them, in plain terms, off that summary:
- **What was read**, the project's identity, which of the seeded project facts were present, the
  disciplines covered, and whether the project manual's table of contents was read.
- **What was learned**, by kind: systems, scope areas, set shape, hazards.
- **What the index check found**, or that it hasn't run yet for this set, never silent on which.
- **What was recorded**, how many facts, and any Question raised for a disagreement between
  documents. What was recorded is the project's working context now, carrying your name and its
  citations; anyone who changes a value later replaces it.
- **The package split**, in these words: "I split the job into N packages; here they are. Change
  any of them on the site or tell me and I will redo it." Then the packages already on the project,
  each package a supplier furnishes with the package that installs its items, each default used
  with the package that follows it and that the user can change any of them in chat, any package
  with no catalog trade and so not created, how many of the manual's sections outside Divisions 00
  and 01 are placed on a package out of how many the manual has (or that the count is incomplete),
  and each section left on no package with its reason. No approval is collected.
- **The structure**, the sheet that grounded the system and the sheet that grounded the floor
  counts when it was filled, or that it was left blank and which half the set does not state.
- **The description**, whether one was written or a person's was already in place and left alone.
- **Where the packet landed**, the full path.
- **What a person should look at**, the facts recorded, visible on plumlayer.com with the page each
  one was read from, and any Question raised for a disagreement between documents.

Close by saying orientation is done and everything it made is on the project record.
<!-- /user-facing -->

## 1. Preconditions

1. **Project exists.** It is the one your dispatch names, confirmed by the session that started
   you, so take its `projectId` from there and call no project list. Where `get_project` refuses
   it, stop and return your summary with `stopped:` naming why.
2. **The baseline set is recognized.** Orientation reads the base set shape, it does not need revisions
   or bulletins to have landed, and spec-TOC presence is optional/best-effort, not a precondition.
   What it does need is a delivery that has actually been through `recognize_sheets`. There is normally no
   retained `jobId` to poll at orientation time (that job ran, and finished, in an earlier session), so
   confirm recognition by its observable effect rather than by re-polling a job you don't hold: call
   `list_drawing_deliveries(projectId)`, if none exist, stop plainly and hand off to `drawing-upload`.
   If a delivery exists, spot-check with a small `search(projectId, predicate: "appearsOnPage", limit:
   1)`, zero rows means recognition hasn't actually recorded anything yet; stop and hand off to
   `drawing-upload` rather than orienting on an empty set. Either stop returns your summary with
   `stopped:` naming it, and the session that started you hands off.

## 2. Read the entries (identity, seeds, sheet inventory)

1. `get_project(projectId)`, the project's identity (name, description, created date).
2. **Read the `project-setup` seed entries verbatim, never re-create them.** For each of `projectType`,
   `deliveryMethod`, `location`, `grossArea`, `floorCount`, `bidDueDate`, `tradeInScope`,
   `knownExclusion`, call `search(projectId, predicate: "<predicate>")` and read what's there. These
   feed the packet's Identity section directly. Where a seed is missing, orientation may record a
   document-grounded entry on that predicate later; where a seed is thin and a document says more,
   the document-grounded entry names the seed with `supersedesId` as the record it replaces, since a
   write onto a field that already holds a value names what it replaces or is refused.
3. **Sheet inventory.** Call `list_drawing_deliveries(projectId)` for the registered deliveries, then
   attempt `set_grid(projectId)` once. A set_grid payload on a set of real size can be large enough to
   file-redirect instead of returning inline, if that happens, fall back to sampled
   `search(projectId, predicate: "discipline")` calls for the disciplines you need (A, S, M, P, E, C, G)
   rather than pulling the full grid. Either path gives you discipline, sheet number, and governing
   issue per sheet, plus the file/page reference each row carries, the render targets for step 5 come
   from here, not from a separate `list_files` call.

## 3. Read the spec-section index, if present

Call `search(projectId, predicate: "inDivision")` for `specSection:<csi>` subjects, paging through
every result to the real total rather than a sample: this is the anchor step 8's package split
drafts from, and a partial read under-declares the job the same way a silent TOC does. When spec
reading has run for a project, these entries are real and cited, `hasTitle`, `locatedAt`, `inDivision`,
and `partOfIssue` on each section (verified on at least one live project). Extraction now ships as
`drawing-upload`'s spec-TOC leg (its step 8, wired to `extract_spec_toc` / `extract_spec_toc_status`),
a project whose drawing-upload pass has run that leg will have these entries. What's still true is that
not every project has run it yet, a set uploaded before the leg shipped, or a manual that arrived
after the drawings and hasn't been filed and extracted, so some projects won't have these entries
yet, that is a gap in what's been run for this project, not a missing capability.

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

Call `reconcile_set(projectId)` report-only (never pass `record`), this step reads the gate's
findings, it never records those findings itself, and recording is not this skill's decision to make. The
bare call (no `deliveryId`) runs the ORIENTATION check: the index of record, the newest delivery
that actually has a read drawing index, against the current compiled set across every delivery,
which is what an orientation pass over the whole project wants. `result.mode` reports which
comparison ran.

- **If the gate has already run for this set:** read the report's counts, what matched, what
  the index lists that isn't in the set, what's in the set the index doesn't list, and whether the
  spec comparison ran. Read `list_questions(projectId)` as well: a gate run that recorded its
  findings raised the design team's side as Questions on the board, each citing the index page and
  the sheets, and those are the standing ones rather than a fresh comparison's. Fold anything real
  into the packet: an unmatched index entry as a `missingScopeFamily` or `setShapeObservation`
  candidate, recorded as a fact (the gate's own Questions already carry the design team's side, so
  this pass raises none for it), and an unrecognized-in-index sheet as a `setShapeObservation`.
  Before citing anything from
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
   "index")`, `"drawing list"`, or `"sheet list"`. If none of these match, skip the render and note
   the absence in your summary, never synthesize an index page that isn't there.
3. **Key plans (up to 4 renders).** For each series in this order, **A**, then **S**, then **M/P/E**
   (one representative render for whichever of M, P, E exists first, in that order, it counts as one
   slot, not three), then **C**, render the lowest-numbered sheet you judge, from its title and
   position in the inventory, to actually be a plan (not a detail, schedule, or elevation) in that
   series, and only if the series exists in the inventory at all. A series that is genuinely absent from
   the inventory renders nothing for that slot and instead becomes a `missingScopeFamily` candidate in
   step 6, don't force a render to fill the slot.

If the set is large enough that six renders plainly can't cover it (many buildings, many phases, an
unusually deep set), say so explicitly in your summary rather than quietly rendering more.

## 6. Emit orientation entries

All net-new, subject `project` unless noted, recorded via one `record_batch(projectId, entries)`
call. Each predicate holds one value on the project, so a batch carries at most one entry per
predicate, and a second one is refused:

| Predicate | Value shape |
|---|---|
| `structuralSystem` | free text, one entry naming every system (e.g. "post-tensioned concrete flat plate over a cast-in-place podium") |
| `envelopeSystem` | free text, one entry naming every system (e.g. "unitized curtain wall; brick veneer at the podium") |
| `scopeArea` | free text, one entry naming every area (e.g. "below-grade parking; amenity terrace") |
| `phasingNote` | free text (e.g. "occupied renovation, phased by wing") |
| `setShapeObservation` | free text (e.g. "schedules live on the A-10 series") |
| `missingScopeFamily` | free text (e.g. "no Division 31 Earthwork/SOE sections in the TOC"), cited to the table of contents |
| `hazardFlag` | free text (e.g. "occupied renovation, coordinate around active tenants") |

This pass raises no Question for its own reading. What you judge about the project goes on the
record as a fact, cited to what you read it from, and where it was inferred rather than labeled it
says what it was read from. A family the table of contents is silent on is a `missingScopeFamily`
fact at this point, an expectation drawn from what a job of this kind usually carries before any
sheet is read; the package review, which holds the drawing evidence, is where a manual silent on
work the drawings show becomes a Question.

The one Question this pass raises is a disagreement between two documents it read, cited to both,
and only when it meets the standard. Read `list_questions(projectId, status: "all")` first, with
no trade filter, paged with `offset: nextOffset` until it comes back whole: an
open one on the same topic gets a reply rather than a second Question, and a closed one is not
asked again. A Question is about the project, never about a Plumlayer failure. Question text is
plain estimator words, and every Question meets the standard the `ask_question` verb states: a
title, a citation for every place it names, and only what is worth the design team's time. It
never names a predicate from the table above, an internal step, or a field, and it carries no em
dash.

Good: title "Story count differs between cover and sections"; "The cover sheet lists four
stories; building sections A-301 and A-302 show five. Please confirm five stories." Bad: a
Question asking the design team to confirm your own reading of the structure, the envelope, the
phasing, or what a trade's drawings look like.

**`sourceInstrument` is per-entry, not one batch label.** For an entry grounded
in a specific page or render, cite the specific source file/instrument name, the same convention
`drawing-upload` and `project-setup`'s Mode B (reading in existing docs) use. Reserve the label
`learn-project-orientation`
only for derived or absence observations with no single source page: `missingScopeFamily` and any
set-level `setShapeObservation`. Every entry's `evidence` cites the exact page/render or query of entries
that produced it, never a fabricated locator.

Call `record_batch` once with the full array. **Verify:** the returned `count` must equal the number of
entries sent; a mismatch stops the run and gets reported, never a guessed correction.

## 7. Fill the structure value, only when the drawings state it

The project row carries one structure value that both the Structure type line and the massing
diagram are drawn from: buildings, each a stack of bands listed ground floor first going up, each
band a floor count and one of concrete, steel, wood, or lgmf, plus an optional podium shared under
every building.

Fill it only when the set states both halves outright: the structural system labeled on the S
sheets, and the floor counts readable on the plans or elevations. Partly stated is not stated. If
the system is labeled but the floor count is not, or the count is there and the system is inferred
from what the details look like, leave the value alone.

There is nothing to ask about here and this step raises no Question: an unfilled structure value is
a blank the estimator can fill later.

When both halves are stated, call `update_project(projectId, structureDiagram: {...})`, and name in
your summary the sheet that grounded each half.

The `structuralSystem` entries from step 6 are not replaced by this. They stay as the cited
evidence; this step reads them and writes the one structured value the surfaces draw from.

## 8. Draft the baseline package split and create the packages

Phase 1 of package derivation: the cheap, high-value baseline split, drafted here so a package
already exists for every trade before the expensive scope read starts. Phase 2, the scope-driven
amendments, stays in `scope-run`.

1. **Read what's already on the project.** Call `solicitation_list_packages(projectId)` first. This
   step is match-or-create: never create a package whose catalog trade id already has one on the
   project. Report existing packages as "already on the project" rather than re-drafting them.
2. **No spec sections, no split.** If step 3 found no `inDivision` entries for this project, create
   no packages. Drawing disciplines are never used as an anchor for a split. Say plainly, in the
   packet and your summary: spec reading hasn't run for this project
   (the remedy is to upload the project manual through `drawing-upload`'s spec-book leg and re-run
   this skill); if the project genuinely has no spec book, the scope run derives the packages from
   the finished scope list instead. No question asked, no branch beyond this sentence.
3. **Draft the split** from the spec TOC (step 3), by how the firms that bid this work split it in
   this market: which sections bundle into which package, which get carved out, a primary CSI
   section per package. A package is what one kind of firm bids: a supplier who furnishes the item,
   an installer who installs what another firm furnishes, or a sub who furnishes and installs it.
   Work two kinds of firm bid goes on two packages. Where the set or the manual shows an item
   furnished by one firm and installed by another, its section goes on both packages'
   `manualSections`, the furnishing package's `notes` name the package that installs it, and the
   installing package's `notes` name what it installs. A supplier's item never sits on a package
   with no installer: where no document says who installs it, the furnishing package's `notes` name
   the package you judge does, and that package takes the section on its `manualSections` and names
   the item in its own `notes`, as for a documented pair. Toilet accessories a specialties supplier
   furnishes and the finish carpenter installs, for example, are two packages, each naming the
   other. Where the supplier and the installer resolve to the same catalog trade, keep one package,
   and its `notes` name the furnish and install split, for the bid form.

   Every section step 3 read outside Divisions 00 and 01 goes to the package whose bidder buys it:
   you place the manual section by section, by what its Part 1 summary says it covers. A section's
   title never settles where it goes, except a section the manual carries only in its table of
   contents, placed by its title as below. Before you place a section, read its first page:
   `search(projectId, subjectPrefix: "specSection:", predicate: "locatedAt", full: true, limit: 100)`,
   paged with `offset` to the end, gives each section's `fileId` and `pageStart`, and
   `get_page_text` on that page carries the summary article; read the next page only where the
   summary runs onto it. These are page text reads, not renders, and step 5's budget does not count
   them. A section read from the table of contents alone carries `declaredOnPage` and no page
   range: place it by its title, and its package's `notes` say the manual's text for it was not
   read in.

   Probe the usually-present families the TOC is silent on (site/civil, SOE, landscaping/exterior
   improvements), the same probe that already produces `missingScopeFamily` entries (step 6): a
   silent family becomes a `missingScopeFamily` entry AND, where a job of this kind would normally
   carry the trade, a package. It raises no Question.

   A section a firm of another package carries goes on that package's `manualSections`, and its
   trade on that package's `codes`, never a package of its own. Walk-off mats, an acoustic
   underlayment laid under the finish floor, and floor prep go on the flooring package; a poured
   gypsum topping and the sound mat under it on the package of the sub who pours it; finish
   hardware and door operators on doors, frames and hardware; reinforcing on cast-in-place
   concrete; steel deck on structural steel. Joint sealants and penetration firestopping go with
   the work they seal or pass through: the sealant section on the `manualSections` of every
   package whose joints it seals, the firestopping section on every package whose pipe, duct or
   conduit passes through a rated wall or floor, and neither on a package of its own unless the
   estimator asks for one, for the building envelope joints or for a firestop specialist. Where
   the catalog has no trade for an item, ask the same question, which kind of firm bids it, and
   put it on that firm's package, never on the package of its nearest neighbor in the division. A
   package's `tradeCode` is never a heading no sub bids here, such as `09 00 00` Finishes; a broad
   code one sub bids on this job, such as `22 00 00` Plumbing, is a package's trade like any
   other. Work the owner contracts for directly gets no package: where the manual says the owner
   hires the agency (special inspections, testing), in Division 01 or in a technical section's
   quality control article, or the owner furnishes and installs the item, draft no package for it.

   On a wood-over-podium job, start the split from what the common subs normally carry on one.
   That is a job where the set states wood-framed floors over a concrete or steel podium, on the
   cover or code sheet's construction type (Type III or V over Type I) or on the structural
   sheets, as your `structuralSystem` entry from step 6 records it. On any other job, or where the
   set does not state both, use none of these lines. Each is a default the estimator can change in
   chat, and the set or the manual overrides any of them: where the manual has the window supplier
   install its windows, the windows package installs them. Where a package follows a line, its
   `notes` name it as the default for this kind of job, as in this note:
<!-- user-facing -->
   "Wood framing, sheathing and trusses, with the air barrier and the window installation at the
   wood levels, the default for a wood-over-podium job."
<!-- /user-facing -->

   - The wood framer carries the air barrier or WRB and the window installation, both at the
     wood levels.
   - The electrician carries fire alarm, tel/data, the intercom and the radio amplifier. CCTV and
     access control can stand apart.
   - On an urban site where the building covers most of the lot, one site contractor carries
     earthwork, utilities, paving and curb, and the landscape is its own package. The site
     package's `notes` name the breakouts to ask for on the bid form.
   - The drywaller does not carry the acoustical ceilings or the sprayed acoustic finish.
   - Spray fireproofing is its own sub on a steel podium.
   - Cabinets are bought supply only, countertops furnished and installed, and the finish
     carpenter installs the cabinets, the doors, the hardware and the accessories.
4. **Resolve every package to the trade catalog** via `directory_list_trades`: exact `code` lookup
   first, then a `query` by trade name or alias. Record the catalog trade id verbatim; never guess
   an id from memory (store-resolution). A package with no reasonable catalog match cannot be
   created (the verb requires a catalog code): name it in your summary as "no catalog trade, not
   created," never force a wrong code.

   A package carries two lists, and they hold different things. `codes` holds catalog trades: the
   other trades the package buys, which decide which companies get invited. `manualSections`
   holds the manual's own sections the package buys, by the numbers the manual prints. The
   manual's numbers and the catalog's often differ (a manual's residential appliances section at
   `11 30 13` against the catalog's `11 31 00`, or a glazing section at `08 80 00` the catalog
   only splits finer). So a package's catalog trades are resolved by trade name through
   `directory_list_trades`, and the manual's section numbers go into `manualSections` exactly as
   step 3 read them. Never write the nearest catalog code in place of a manual section, and never
   put a manual section number into `codes`.
5. **Create each missing package** with `solicitation_create_package(projectId, tradeCode, name,
   codes, manualSections, notes)`: name = the package display name; `tradeCode` is the package's
   primary catalog trade; `codes` lists the other catalog trades bundled into it (verbatim catalog
   ids from the same `directory_list_trades` resolution as step 4, never repeating `tradeCode`);
   `manualSections` lists every manual section the package buys; `notes` carries a one-line
   rationale in plain prose, no fixed shape. A package already on the project (sub-step 1) gets
   the sections your draft gives it the way sub-step 6 adds a section to a package.
6. **Place every section, then count.** Re-list packages with `solicitation_list_packages` and
   confirm every created one landed. The same answer carries `manualSectionPlacement`:
   `sectionsOutsideFrontEnd`, how many sections outside Divisions 00 and 01 are on the record,
   and `onNoPackage`, each one no package lists. For each section on `onNoPackage`, find the
   package whose bidder buys it the way sub-steps 3 to 5 do, creating that package when the
   project lacks it and the catalog has its trade. To add a section to a package, read the
   package's current `manualSections`, then send `solicitation_update_package(packageId,
   manualSections)` with that list plus the new sections, each number once:
   `solicitation_update_package` replaces the whole list, and it refuses two spellings of one
   section. Re-read the package before each later change to it. Re-list until `onNoPackage` is
   empty, or every section left on it is one of two kinds, each named in your summary with its
   reason: work you leave off on purpose because no subcontractor bids it here, such as
   owner-furnished work with no installer or an agency the owner hires, or a section whose buying trade has no catalog
   match, named with the trade you looked for. Always read `manualSectionPlacement.truncated`:
   when it is true the count is incomplete, even with `onNoPackage` empty, and your summary says
   so. When it is false, the sections placed are `sectionsOutsideFrontEnd` less the length of
   `onNoPackage`. This sub-step is also how a project whose packages predate the manual, or were
   drafted without placing every section, gets its sections placed; `scope-run` runs it before
   any package review reads.
7. **Put the split in your summary.** Its `packages:`, `furnish and install:`, `defaults:`,
   `sections placed:` and `on no package:` lines carry it, and the session that started you says
   it to the user in the words "Running one level down" gives. No approval is collected.

## 9. Write the project description

`get_project`'s `description` field answers "what is this job?" for someone opening the project
cold. This is the first pass with enough of a read on the set to write one, so it writes it here,
once, after the entries above are recorded and before the summary.

1. **Leave a person's description alone.** Re-check the `description` read in step 2.
   `get_project` carries no author and no write time for this field, so a Learn run cannot
   tell its own past write from a person's edit. Treat any non-empty description as a person's:
   leave it as is and say so in your summary. Only an empty description gets written below.
2. **Write what the job is.** What the building is, what work is being done, for whom, where, and
   whatever makes this job different from a typical one, in plain estimator prose. Every statement
   traces to something read this run, a render, a page, a seed entry, or an entry recorded in step
   6; a differentiator you would only infer is left out of the description.
3. **Leave out what already has a field.** Total SF, floor count, bid due date, status, structural
   or envelope system, and any sheet or spec bookkeeping already live as their own entries;
   restating them here duplicates the record instead of orienting a reader. Leave out narration of
   how the set was read too, this is what the job is, not how it was learned.
4. **No length target.** As long as the job needs and no longer.
5. Call `update_project(projectId, description: "<text>")`. The description and the structure value
   from step 7 are the only fields on the project row this skill ever writes.

## 10. Compile the run-context packet

A projection compiled fresh from the entries read in step 2 and recorded in step 6, never itself
recorded as an entry, never stored as truth. Sections, in order:

1. **Identity**, name, type, delivery method, location, size, key dates (from the seed entries).
2. **Systems**, structural and envelope systems.
3. **Scope areas**, the `scopeArea` and `phasingNote` entries.
4. **Set shape**, disciplines present, issue labels seen, `setShapeObservation` entries,
   `missingScopeFamily` entries, the spec-TOC status (division spread + count, or the "hasn't run
   yet" note from step 3), and the reconciliation-gate status (its report counts, or "hasn't run yet"
   from step 4).
5. **Hazards**, the `hazardFlag` entries.
6. **Packages**, the packages on the project after step 8: name, catalog trade id, the other
   catalog trades it buys, and the manual sections it buys, per package; then the manual sections
   on no package with each one's reason, or the "spec reading hasn't run for this project" note
   when step 8 created none.
7. `[PLACEHOLDER, definitions-as-context envelope]`, a clearly marked final section; this
   skill does not design that envelope, it only reserves the slot.

Write it to `~/.plumlayer/runs/<project-slug>/learn-project-packet.md` (the same local run folder
the `scope-run` skill uses), derive `<project-slug>` from the project name (lowercase, spaces to
hyphens) or fall back to the `projectId` if the name doesn't produce a clean slug. Never write it
into a repo, and never record it as an entry. Regenerate it in full the next time this skill runs for the project, it is a projection,
not a document to patch. Audience: agent. Its path is handed to the user at run end (step 11) and
its content orients later readers; whatever crosses from it into user-facing text becomes
user-facing at the crossing and is translated there. The session that started you reads its path
off your summary and never its content.

## 11. Return the summary

Write your summary to the path your dispatch names, in the shape "Running one level down" gives,
then return it and end. Every count on it is read from what this run did and the record holds:
the facts step 6 recorded and the count `record_batch` returned, the packages step 8 created and
the re-list's `manualSectionPlacement`, the structure and description steps 7 and 9 wrote. Where
no spec sections exist, `spec reading:` says spec reading hasn't run for this project and
`packages:` says none were created. The packet's definitions-as-context section is a stub, not yet
designed, and the summary does not name it.

## Gates (non-negotiable)

- **The steps run one level down.** The session that starts this skill dispatches the orientation
  agent and reads its summary; it never runs a render, a page read, or a package call of steps 1 to
  11 itself, except on a client with no agent tool.
- **Cite everything.** No citation → don't emit the entry.
- **Net-new facts only.** Never re-create a seed entry `project-setup` already recorded, or a sheet /
  spec-section entry `drawing-upload` already recorded.
- **Judgment entries are cited and raise no Question.** The one raise is a disagreement between two
  documents, per step 6.
- **A Question is about the project, never about a Plumlayer failure.** A render or read that
  fails is reported in the conversation, not raised as a Question.
- **Say it is your reading.** These entries become the project's working context immediately, so an
  inferred value that reads as a documented one is the failure to avoid.
- **Orientation, not comprehension.** Respect the ≤6 render budget, if the set is too large for it to
  cover meaningfully, say so in your summary rather than silently exceeding it.
- **The reconciliation gate is read, never run or recorded, by this skill.** Step 4 reads
  `reconcile_set` report-only; a gate that hasn't run for this set is named as not having run, never
  paraphrased into "no discrepancies."
- **The packet is a projection only.** Never recorded as an entry, never written to the repo, always
  regenerated in full on the next run rather than patched.
- **The split anchors on the spec table of contents, never on drawing disciplines.** No spec
  sections on the project means no packages, and your summary says so plainly.
- **Complete step 8's placement check before reporting the split.**
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
