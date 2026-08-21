---
name: scope-run
description: >
  Run the scope-item-first engine on a Plumlayer project: read the drawing set in waves, produce
  one grounded, cited, trade-agnostic scope list, audit it for completeness, then derive and tag
  trade packages. Trigger on "scope this set", "run the scope engine", "/scope-run". Attended:
  the user approves each stage. Drives the project record's read and write verbs. Does not
  upload drawings (drawing-upload), orient from scratch (learn-project), read sub proposals
  (bid-intake), or place takeoff measurements (takeoff).
---

# Scope Run: the scope-item-first engine

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

## What this is

The production scope engine: it builds the project's context floor, reads the set in
reference-dependency waves through dispatched readers, produces one grounded, cited,
trade-agnostic scope list, audits it with the completeness pass, then derives and tags the trade
packages, all on the hosted project record, with the user reviewing at every wave checkpoint.
Orientation is the `learn-project` skill, which this skill runs first when orientation hasn't
happened yet. The engine's shape, in the estimator's own order:

> First assemble one massive singular list of all the scope line items across the entire job; then
> sort through and decide which trade packages to create; assembling them is assigning one new meta
> variable on an entirely scoped line item.

One grounded, cited, trade-agnostic scope list first; trade packages are projections off it. The
method was validated end to end against a real precon bid evaluation before this skill shipped
(subset acceptance run, 2026-08: recall 94.8% / precision 100% on the amended pre-registered
method), and everything this skill mandates below is what that validation proved necessary: each
mandate exists because its absence produced a measured failure.

**This run is attended.** The user approves the read plan before any reading, reviews at every
wave checkpoint, and approves the package split before any tagging. Never run waves past a
checkpoint without the user's go-ahead.

Doctrine binds every step: **agents read and judge; deterministic tooling grounds; nothing enters
untraced.** Everything a reader records is its own reading, cited, carrying its authorship trail; it
becomes working truth the moment it lands; anything a person changes wins.

## The non-negotiables

Every stage below honors these. They are restated where they apply, but read them first: a run
that relaxes any one of them reproduces a measured, named failure from the validation study.

1. **Cite everything, in the uniform shape.** Every drawing-grounded record carries evidence naming
   the sheet AND a resolvable 1-based page: `evidence.page` or `evidence.pageInPdf` as a positive
   integer for the page actually read. A sheet named with no page cannot be render-verified and the
   record door refuses it. Never fabricate a page or sheet to satisfy the door.
2. **Create / enrich / flag against the live list.** Every reader holds the current scope list as
   match-or-create context: for each thing seen, create a new item, enrich an existing one (a new
   citation, a note, a resolved cross-reference), or flag an observation. Never a parallel list,
   never a re-create of what exists, never silent skipping of what's already listed.
3. **The convention-line emit mandate.** A reader whose trade-knowledge entries carry convention
   lines for the content families it reads MUST emit them: create if absent from the live list,
   enrich if present. Silence is a violation, not a judgment call; a reader judging a convention
   entry inapplicable to this project flags that with its reason. Convention lines never masquerade
   as sheet-cited reads: their `sourceInstrument` is `trade-convention:<trade>@<knowledge-version>`
   (the pinned version from the knowledge manifest), their evidence quotes the entry's line and
   carries the marker `basis: "trade-convention"`, and they carry no sheet citation. Where a sheet
   corroborates one, that citation enriches the same item and the convention basis stays visible
   in the trail.
4. **Store-resolution is mandatory.** A mark, tag, or code is resolved by querying the project
   record (`search`), never from memory, never inherited from another sheet's read, never assumed
   from a similar-looking mark. The validation's one repaired violation came from two of eight
   inherited marks being misidentified.
5. **Capture never filters.** Capture is trade-agnostic and complete: everything seen goes into the
   one shared list. Deciding what matters, what's priced, and whose trade it is happens downstream,
   never in the reader.
6. **Every write is count-verified by read-back.** After every batch write, read back and confirm
   the count landed equals the count sent; check any contested rows individually. The lead
   re-verifies reader-reported counts with its own queries: a reader's summary is a claim to
   verify, not a fact to relay.
7. **The grain bracket.** A scope item is the unit a subcontractor would include / exclude / price
   as one thing (the floor: split by type / significant distinction, never by instance) and at most
   one row on a trade's scope sheet (the ceiling: package headers are the derive stage's output,
   never the reader's). One item per sheet is a ceiling violation; one item per instance is a floor
   violation. Where the trade-knowledge entry's grain section is silent, create at best judgment AND
   flag the grain as unspecced: recall never drops to grain uncertainty.
8. **Definitions before placements.** A bundle reads only after the bundles it references are
   already recorded (legends and schedules before the plans that tag them). The read plan encodes
   this order and the user approves it.
9. **Every wave carries a schedules-scope lane alongside its definitions lane.** Definitions
   readers record what a mark means; the schedules-scope lane owns the scope items the schedules
   themselves ground. The validation's single biggest capture gap was nobody owning
   schedule-grounded scope.
10. **The completeness check runs; residue is named.** The enumerate-and-audit pass (below) is a
    standing stage with a closure loop, never optional, and its final residue is reported by name:
    never assumed closed, never zeroed by hope.

Also: never author door-owned records. Retractions, flag resolutions, questions-as-answers, and
package definitions are created only at their own doors: a reader that thinks an item should be deleted
or a flag should be closed says so in its report; a person acts at the door.

## The scope item row

A newly created scope item is a full row, not a name. Every new item writes:

- **name**: the concise line the sub reads: aim under ten words, estimator wording, no code
  dump ("Interior metal-stud partitions", not a recitation of every type mark).
- **category** (required): the intrinsic work grouping an estimator would use as a checklist
  section ("Metal Stud Partitions", "Unit Casework", "Sealants & Firestopping"). Group like work
  under the same category string; never invent a fresh category per item. The review surface
  groups by this: an uncategorized list renders as a wall.
- **description**: one to three tight sentences carrying only what changes price or scope.
  Never a re-narration of the schedule: the citation points at the sheet, and the doctrine is
  cite, don't rewrite: rewriting is the telephone game the grounding exists to prevent.
- **notesExternal / notesInternal**: only when there is a real note (a bidder-facing caveat; an
  internal watch item). Most items carry neither.
- **quantity**: only where the sheet itself carries one, as `{value, unit}`.

Recorded text is user-facing prose: plain estimator words, no em dashes, no bolding, no
machinery vocabulary. A verbose row is a defect, not diligence.

## Run artifacts and the ledger

All run working files live under `~/.plumlayer/runs/<project-slug>/` (slug from the project name,
lowercase, spaces to hyphens; fall back to the projectId). Never committed to any repo, never
uploaded to the project except record files, never recorded as project entries. The set:

- `ledger.md`: the run ledger, appended as the run proceeds: every dispatch (wave, unit, model,
  purpose, and the token usage the harness reports when the worker completes), every write batch
  (count sent, count verified, contested), the definitions-kind roster as kinds land, checkpoint
  outcomes, and every deviation or repair. The ledger is what makes the close-out report honest.
  Audience: agent. Its dispatch and token-cost figures feed the close-out report's run-cost bullet;
  whatever crosses from it into that report becomes user-facing at the crossing and is translated
  there.
- `bundle-map.md`: the read plan (stage 3), user-approved before any wave runs. Audience: user,
  it is shown to the user for approval.
- `context-packet.md`: the compiled context packet, regenerated between waves (a projection off
  live records, never itself recorded). Audience: agent.
- `anti-join/`: the completeness pass's rosters, accounting output, and residue lists. Audience:
  agent.
- `records/`: JSONL files for large batch writes (these do get uploaded, as the write
  mechanism). Audience: machine.

## The trade knowledge base

Ships with this plugin at `${CLAUDE_PLUGIN_ROOT}/trade-packages/`: one entry per trade
(`painting.md`, `drywall.md`, …), mined from a real subcontractor-quote corpus, carrying what the
drawings will not say: how the trade bids, scope grain rules, exclusions and counterparties,
furnish/install seams, convention work no sheet states. `MANIFEST.md` there records the knowledge
version and source snapshot: read it at run start, record the version in the ledger, and cite it
in every convention-line record (`trade-convention:<trade>@<version>`). Readers receive the entries
relevant to their bundle's content families as part of their brief. Where an entry is silent, the
reader creates at best judgment and flags (non-negotiable 7); the flag is a suggested amendment to the
entry, surfaced in the close-out report.

## 1. Preconditions

1. **Project exists and is the user's intent.** `list_projects`, confirm which project with the
   user, get its `projectId`. No project → hand off to `project-create`.
2. **Drawings are recognized.** `list_drawing_deliveries(projectId)`: no deliveries → stop
   plainly, hand off to `drawing-upload`. Spot-check recognition actually recorded:
   `search(projectId, predicate: "appearsOnPage", limit: 1)`: zero rows → hand off to
   `drawing-upload`.
3. **Spec book, if it exists.** `search(projectId, predicate: "inDivision", limit: 1)`: spec
   sections present means the spec-TOC leg has run. Absent: ask the user whether a project manual /
   spec book exists. If one does, run it through `drawing-upload`'s spec-book leg first (upload +
   `extract_spec_toc`): the package derivation anchors on the spec table of contents and is
   substantially weaker without it. If the project genuinely has no spec book, proceed, name that
   in the ledger and the close-out report, and derive packages from the drawing disciplines plus
   the trade knowledge base's market conventions instead (an explicitly weaker anchor, said so to
   the user).
4. **Trade knowledge present.** Read `${CLAUDE_PLUGIN_ROOT}/trade-packages/MANIFEST.md`; record
   the version in the ledger. Missing → stop and report a broken plugin install rather than running
   knowledge-blind.
5. **The user is present.**
<!-- user-facing -->
Say what the run will do, roughly what it costs (a real read of a
   full set is a multi-hour, many-dispatch run: share the dispatch shape from the ledger of record:
   a ~36%-of-set validation run took ~26 worker dispatches), and confirm they're staying for the
   checkpoints.
<!-- /user-facing -->

## 2. Context floor

Run these in order; each is read-or-run, never re-created (net-new facts only, everywhere).

1. **The reconciliation gate, read.** Call `reconcile_set(projectId)` report-only (never pass
   `record`, never pass a `deliveryId`: the bare call is the orientation check). Fold what it
   reports into the context packet. Check `.ran` flags before citing any drift number: a check
   that did not run is named as not-run, never folded in as "found nothing". Genuine document
   inconsistencies it surfaces are design-team question material, not blockers; extraction-miss
   residue is noted for the record.
2. **Orientation.** If the project has no orientation facts yet (`search(projectId, predicate:
   "structuralSystem", limit: 1)` and siblings empty), run the `learn-project` skill now, in full.
   If orientation exists, read its claims fresh instead of re-running it.
3. **Compile the context packet** (`context-packet.md`): identity and seed facts; systems; scope
   areas; set shape (disciplines, deliveries, spec-TOC status, reconciliation findings); hazards;
   and the definitions index section (empty before the first definitions wave; recompiled after
   every wave). The packet is a projection: regenerate whole, never patch, never record it.

## 3. The read plan (bundle map), user-approved

Compile the set into content-keyed bundles and sequence them by reference dependency. Pull the
sheet inventory (`set_grid`, falling back to sampled `search(predicate: "discipline")` reads if the
grid file-redirects), then:

1. **Group by content**, not by trade and not by page order: schedule/legend families, assembly
   and partition legends, envelope assemblies, enlarged plan families (units, kitchens, baths),
   finish/millwork details, elevations/sections, civil/site, landscape, each MEP discipline's
   legend+schedule family and its placement family, and so on. A bundle is sheets a reader should
   hold together because they explain each other.
2. **Sequence by reference dependency**: a bundle reads only after the bundles it references are
   recorded. Definitions parents first: schedules, legends, assembly sheets, then placements
   that tag them. Structural general notes before framing plans; MEP legends/schedules before
   distribution.
3. **Assign each bundle a lane and a lens**: definitions lane (extracting what marks mean;
   these readers also carry the schedules-scope duty, non-negotiable 9), or placement lane
   (capturing scope where it's shown). Name the trade-knowledge entries each bundle's reader will
   carry (by content family: a kitchens bundle carries appliances, casework, countertops, tiling,
   millwork…).
4. **Assign model tier**: schedule-dense and cross-discipline-conflict bundles read on the
   strongest available model; ordinary capture reads on the standard tier. Never the light tier
   for reading.
5. **Wave the bundles**: a wave is a set of bundles whose reads can run together. Bundles that
   plausibly see the same scope (kitchens and unit plans, say) go in different waves or run
   serially: two parallel readers creating the same work create it twice. Content-disjoint bundles may
   run in parallel within a wave.

Write `bundle-map.md`: bundles, sheets per bundle (numbers + file/page references), lane, lenses,
knowledge entries, model tier, wave order, and what's deliberately excluded (name it: exclusions
are named residue, never silence).
<!-- user-facing -->
**Show the user the plan in estimator terms and get their
approval before any wave runs.**
<!-- /user-facing -->
The read plan is a reviewable artifact; the user may cut,
add, or resequence.

## 4. Wave reads

Per wave, in this exact loop:

1. **Recompile the definitions index** into the context packet: one line per defined thing:
   code, kind, one-line name, where defined, compiled from the record (`search` per known kind,
   paged to the real total; the ledger's kind roster tracks which kinds exist so far). Depth stays
   in the record: readers resolve full definitions on demand mid-read (`search(subject:
   "<kind>:<code>")`), never from a paraphrase.
2. **Dispatch the wave's readers** with the reader brief (template below), each carrying: its
   bundle's sheets with file/page references, its lane and lenses, the context packet, its
   trade-knowledge entries, and the mandates verbatim. Assign each dispatch a unique run-prefix
   (the bundle or unit id) when filling the brief's subject scheme, so parallel readers can never
   collide on a created subject. Parallel only across content-disjoint bundles. Record each
   dispatch in the ledger (unit, model, purpose).
3. **Readers read deep and record directly**: render + text per sheet (`render_page` +
   `get_page_text`), create/enrich/flag against the live list (readers pull it fresh via
   `list_scope_items` + targeted `search` at start), record via `record_batch` (≤500 per call,
   atomic) or `record_batch_file` for larger runs, read back and count-verify, report counts and
   anomalies.
4. **The lead verifies**: re-run the counts with your own queries (`search` filtered to the
   reader's sourceInstrument or subjects; `list_scope_items` delta), check contested rows, and
   record verified counts in the ledger. A mismatch stops the wave and gets investigated, never
   papered over. When the wave ran readers in parallel, also scan the wave's new items for
   cross-reader overlaps: the same work captured from two sides, convention lines especially,
   since parallel readers cannot see each other's new items. List any overlap as a flag for the
   user at the checkpoint; merging is a person's call at the review surface, never the
   lead's.
5. **Checkpoint with the user** (format below). Proceed to the next wave only on their
   go-ahead.

Token accounting: when the harness reports a completed worker's token usage, record it in the
ledger against that dispatch. Where the harness doesn't surface a number, record the dispatch with
usage unknown: never estimate and never leave the row out.

## 5. The completeness check (standing, with a closure loop)

The definitions layer is the checklist: every defined thing must be accounted for by the scope
list. Run this after the placement waves complete (and any time coverage is in doubt):

1. **Enumerate the defined things**: page through the record per definitions kind (the ledger's
   kind roster; `search` with the kind prefix, compact rows, to the real total) into a roster
   file under `anti-join/`.
2. **Pull the scope list**: `list_scope_items`: names, descriptions, notes per item.
3. **Account deterministically**: write and run a small local script: word-boundary token
   reference of each defined code in scope-item text (name / description / notes; evidence
   snippets excluded); kind-collisions and codes ≤2 characters divert to an ambiguous bucket for
   agent adjudication rather than string-match guessing. "Accounted" means textually referenced,
   not priced. This is a script's job, not an eyeball's: the judgment lives in adjudicating the
   ambiguous bucket and classifying the residue, not in the matching.
4. **Classify the residue**, every row: accounted / plausibly-carried (inside an existing coarse
   item: name which) / not-scope (a definition with no work attached: say why) / unaccounted.
5. **Close the loop**: cluster the unaccounted rows into capture gaps, define supplemental
   schedule-grounded capture units for them, dispatch those reads (same brief template, same
   mandates), re-run the accounting. The validation run's first pass found 269 of 564 defined
   things unaccounted, closed 267 with one supplemental wave, and named a residue of 2: that
   loop is the designed behavior, not a recovery.
6. **Name the final residue** in the ledger and the close-out report, row by row.

Spec sections account differently (estimators never write CSI digit strings into scope text): a
spec section is accounted when the approved package split (stage 6) bundles it into a package.
After the split is approved, list every TOC section not bundled anywhere: that list is the
TOC-coverage residue, reported the same way.

## 6. Derive the packages: spec-TOC-anchored, two-phase, user-approved

The estimator-judgment stage. Packages are bundles of spec sections grouped by how subcontractors
actually split themselves in the market, not by the book's divisions.

1. **Phase 1: baseline split.** Draft the package structure from the spec TOC plus the trade
   knowledge base's market conventions: which sections bundle into which package, which get carved
   out, a primary CSI section per package. Probe the usually-present families the TOC is silent
   on (site/civil, SOE, landscaping/exterior improvements, thin design-build MEP divisions) and
   draft estimator-declared packages for them.
<!-- user-facing -->
Present the split as a reviewable artifact:
   package name, primary section, bundled sections, catalog trade (id + name, from step 3),
   one-line market rationale each, and **get the user's approval before any tagging**.
<!-- /user-facing -->
   Tagging happens into an approved structure, never an inferred one.
2. **Phase 2: scope-driven amendments.** Where the scope list surfaces what the TOC cannot see
   (a specialty assembly that wants its own bidder, an either-or item probed as an alternate, a
   package that should collapse into another once scale is understood), draft amendments the
   same way: named, rationaled, user-approved.
3. **Resolve every package to the trade catalog.** The trade tag and the live package speak the
   curated CSI trade catalog's vocabulary, not the spec book's. Before presenting the split, look
   up each drafted package's home trade via `directory_list_trades`: exact `code` lookup first,
   then a `query` by trade name or alias ("tile", "sheetrock"), and record the catalog trade id
   verbatim (the spaced form, e.g. `09 21 16`) in the split artifact alongside the primary
   section. The primary section and bundled sections keep their spec-TOC granularity: the finer
   spec-section reading lives there and in each item's category and description, never in the
   trade tag. A package with no reasonable catalog match may keep its raw primary section as its
   tag value, but only as a deliberate, named choice: mark it "no catalog trade" in the split
   artifact so the user approves that knowingly. An unresolved tag is never the silent
   default, and a catalog id is never guessed from memory: every id in the split comes from a
   `directory_list_trades` result in this run (store-resolution, non-negotiable 4, applies to the
   catalog too).

Creating live bid packages on the project (the outward-facing objects the solicitation flow uses)
is the user's call at their door. Offer it after approval, one `solicitation_create_package`
per package they want live (tradeCode = the package's catalog trade id from the approved split,
or its raw primary section only for a package the split explicitly marked "no catalog trade";
name = the package's display name, notes carrying the bundled sections), and skip it cleanly if
they'd rather create packages when soliciting. The approved split
artifact, not the package rows, is what tagging needs.

## 7. Tag

Assign each scope item its home trade off the approved split: one `belongsToTrade` record per item
(value: the package's catalog trade id, verbatim from the approved split, a raw spec section only
for a package the split explicitly marked "no catalog trade", never as an unmarked default),
recorded in batches with the same read-back verification. Where an item genuinely straddles a package boundary, flag it as a package-boundary
question instead of force-tagging: the validation run tagged 275 of 283 and flagged 8, and those
8 flags were correct output, not failure. Boundary enrollments (exclusions, general requirements,
alternates on other packages) are manual-first doctrine: the engine does not auto-author them;
the user authors boundary lines on the package surface, and anything the read suggested as a
boundary rides in flags and notes. Sheet-to-package assignment (`assign_sheet_packages`) is
a user-approved override: offer it only when the user asks; the derived relevant-pages
list already falls out of the citations.

## 8. Close out

<!-- user-facing -->
Report to the user, in estimator terms:

- **The scope list**: how many items, by category family; where to review it (the project's Scope
  view on plumlayer.com), and that every line shows the sheet and page it was read from.
- **Their review points**: how many flagged items, the leading ones by name: unspecced grain,
  package-boundary questions, document defects found (contradictions, missing schedule entries,
  duplicate sheets), convention entries judged inapplicable. Document defects worth sending to
  the design team are named as question candidates.
- **The count check**: what was enumerated, what closed, what is still open.
- **The package split**: approved packages, amendments, TOC sections deliberately unbundled.
- **The run cost**: dispatches by wave and model, token totals where the harness reported
  them, unknowns stated as unknown: honest bounds, never estimates presented as measurements.
- **Knowledge amendments**: entry-silent flags and inapplicability flags, offered as amendments
  to the trade knowledge base.
<!-- /user-facing -->

## The reader brief (template: every reader dispatch carries this, mechanically)

Fill the slots; never trim the mandates. A brief that omits a mandate reproduces a measured
failure.

```text
You are a scope reader for a construction drawing set, reading for a Plumlayer project record.
Project: <projectId>. Your read unit: <bundle name> — sheets <numbers, with fileId + 1-based
pageInPdf for each>. Lane: <definitions + schedules-scope | placement>. Lenses: <content lenses>.

Context: the run context packet is below <or attached>. It carries the project's identity,
systems, scope areas, set shape, hazards, and the definitions index (code → kind → name → where
defined). Resolve any mark's full definition on demand from the record:
search(subject: "<kind>:<code>"). Never resolve a mark from memory or from another sheet's
pattern — query the record (store-resolution is mandatory).

Trade knowledge: the entries below <or attached> carry grain rules, seams, and convention lines
for your content families. Knowledge version: <version from MANIFEST.md>.

Read every sheet in your unit deep: render_page + get_page_text on each page (render for layout
and meaning, text for exact tokens). Then emit against the live scope list, which you pull fresh
at start (list_scope_items, plus targeted search):

1. CREATE a new scope item for work not on the list; ENRICH an existing item (new citation, note,
   resolved reference) for work already listed; FLAG an observation (a gap, an anomaly, an
   ungrounded reference you will not create, a grain question where the knowledge entry is silent).
   Never a parallel list; never re-create; never silently skip.
2. CONVENTION LINES: for each convention entry in your trade knowledge that applies to your
   content families, create it if absent from the live list or enrich if present —
   sourceInstrument "trade-convention:<trade>@<version>", evidence quoting the entry's line and
   carrying basis: "trade-convention", NO sheet citation. If you judge an entry inapplicable to
   this project, FLAG that with your reason. Silence on a convention entry is a violation.
3. CITATION SHAPE: every drawing-grounded record's evidence names the sheet AND carries
   evidence.pageInPdf (1-based integer) for the page you actually read. Never a sheet without a
   page; never a fabricated page. The record door refuses pageless sheet citations — if it
   refuses something, fix the citation to what you actually read; never game the shape.
4. CAPTURE NEVER FILTERS: capture everything you see, trade-agnostic, at the grain of one row on
   a trade's scope sheet — split by type or significant distinction, never by instance (floor);
   never one item per sheet or package headers (ceiling). Distinctions that don't earn a row ride
   in the description and notes.
5. THE ROW: every new item writes the full row — name (concise, under ~10 words, estimator wording),
   category (REQUIRED: the checklist-section grouping an estimator would use; reuse category
   strings across like work, never one per item), description (1-3 tight sentences, only what
   changes price or scope — never a re-narration of the schedule; the citation does the
   explaining), notesExternal/notesInternal only when there is a real note, quantity only where
   the sheet carries one as {value, unit}. Recorded text is user-facing: plain estimator
   prose, no em dashes, no bolding, no machinery words. Verbose rows are defects.
6. GRAIN: follow your entries' grain sections; where silent, create at best judgment AND flag the
   grain as unspecced.
7. RECORD directly: record_batch (≤500 per call; subjects scopeItem:<run-prefix>-<seq> for
   new items; the item's existing subject for enrichments), or upload a JSONL and record_batch_file
   for large runs. After every batch, READ BACK and verify the count landed equals the count
   sent; recheck any contested ids individually. Report exact counts.
8. Definitions lane only: also record what the schedules define (extending the existing subject
   kinds you see in the definitions index — never creating a parallel vocabulary), AND own the
   scope items the schedules themselves ground (the schedules-scope duty): a schedule row family
   that is real priced work becomes scope items at the grain bracket, cited to the schedule
   sheet + page.

Report back: counts (created / enriched / flagged, recorded / verified / contested), the
definitions kinds you added (if any), anomalies and document defects you flagged, convention
entries emitted and any judged inapplicable (with reasons), and anything you could not read
(refused tokens, unreadable pages) stated honestly — an unread page is named, never silently
skipped. Your reading is your word: it lands under your authorship and governs provisionally,
so flag what you're unsure of rather than smoothing it.
```

## The wave checkpoint (what the user sees)

<!-- user-facing -->
After each wave, before the next dispatch, in estimator terms:

- What was read (units, sheets), what landed (items added, items enriched, flags raised): verified
  counts, not reader-reported ones.
- The flags worth their eyes now: document defects, grain questions, anomalies, each with its
  sheet reference, reviewable on plumlayer.com.
- What changed in the definitions index (new kinds, new codes) and anything the next wave depends
  on.
- Anything that deviated: a count mismatch and its repair, an unreadable page, a reader that
  stopped, named plainly.
- The next wave's plan, and the ask: proceed, adjust, or pause.
<!-- /user-facing -->

## What this skill does not do

- **Upload or recognize drawings** (`drawing-upload`), **create projects** (`project-create`),
  **read sub proposals** (`bid-intake`), **place takeoff measurements** (`takeoff`).
- **Author boundary enrollments**: manual-first doctrine; the user authors boundary lines at
  the package surface.
- **Score itself against a bid eval**: the acceptance harness was repo-side study machinery, not
  product.
- **Delete, resolve, or approve anything on the user's behalf**: door-owned acts stay at
  their doors.
- **Run unattended**: wave checkpoints are load-bearing until the user has enough cold runs
  behind them to decide otherwise, and that is their decision to make out loud, per run, never
  this skill's default.

## Historical note

The route-first harness (per-trade fan-out, reconcile-by-overlap) is retired doctrine. Do not
restore or run route-first machinery from git history as a scope path, and never present it as
current.
