---
name: scope-run
description: >
  Read a Plumlayer project's drawing set into one grounded, cited, trade-agnostic scope list,
  audit it for completeness, then derive and tag trade packages. Trigger on "scope this set",
  "/scope-run". Attended: the user approves the read plan, every check-in, and the package split.
  Drives the project record's read and write verbs. Does not upload drawings (drawing-upload),
  orient from scratch (learn-project), read sub proposals (bid-intake), or place takeoff
  measurements (takeoff).
---

# Scope run

## What this is

The production scope run: it builds the project's context floor, reads the set in rounds ordered
by reference dependency, produces one grounded, cited, trade-agnostic scope list, audits it with
the completeness pass, then derives and tags the trade packages, all on the hosted project record,
with the user reviewing at every check-in. Orientation is the `learn-project` skill, which this
skill runs first when orientation hasn't happened yet. The shape, in the estimator's own order:

> First assemble one massive singular list of all the scope line items across the entire job; then
> sort through and decide which trade packages to create; assembling them is assigning one new meta
> variable on an entirely scoped line item.

One grounded, cited, trade-agnostic scope list first; trade packages are projections off it. The
method was validated end to end against a real precon bid evaluation before this skill shipped
(subset acceptance run, 2026-08: recall 94.8% / precision 100% on the amended pre-registered
method), and everything this skill mandates below is what that validation proved necessary: each
mandate exists because its absence produced a measured failure.

**This run is attended.** The user approves the read plan before any reading, reviews at every
check-in, and approves the package split before any tagging. Never read past a check-in without
the user's go-ahead.

Doctrine binds every step: **agents read and judge; deterministic tooling grounds; nothing enters
untraced.** Everything a pass records is its own reading, cited, carrying its authorship trail; it
becomes working truth the moment it lands; anything a person changes wins.

## The non-negotiables

Every stage below honors these. They are restated where they apply, but read them first: a run
that relaxes any one of them reproduces a measured, named failure from the validation study.

1. **Cite everything, in the uniform shape.** Every drawing-grounded record carries evidence naming
   the sheet AND a resolvable 1-based page: `evidence.page` or `evidence.pageInPdf` as a positive
   integer for the page actually read. A sheet named with no page cannot be render-verified and the
   record door refuses it. Never fabricate a page or sheet to satisfy the door.
2. **Create / update / flag against the live list.** Every pass holds the current scope list as
   match-or-create context: for each thing seen, create a new item, update an existing one (a new
   citation, a note, a resolved cross-reference), or flag an observation. Never a parallel list,
   never a re-create of what exists, never silent skipping of what's already listed.
3. **The convention-line emit mandate.** A pass whose trade files carry convention lines for the
   content families it reads MUST emit them: create if absent from the live list, update if
   present. Silence is a violation, not a judgment call; a pass judging a convention line
   inapplicable to this project flags that with its reason. Convention lines never masquerade
   as sheet-cited reads: their `sourceInstrument` is `trade-convention:<trade>@<knowledge-version>`
   (the pinned version from the knowledge manifest), their evidence quotes the trade file's line and
   carries the marker `basis: "trade-convention"`, and they carry no sheet citation. Where a sheet
   corroborates one, that citation updates the same item and the convention basis stays visible
   in the trail.
4. **Store-resolution is mandatory.** A mark, tag, or code is resolved by querying the project
   record (`search`), never from memory, never inherited from another sheet's read, never assumed
   from a similar-looking mark. The validation's one repaired violation came from two of eight
   inherited marks being misidentified.
5. **Capture never filters.** Capture is trade-agnostic and complete: everything seen goes into the
   one shared list. Deciding what matters, what's priced, and whose trade it is happens downstream,
   never in the pass that read it.
6. **Every write is count-verified.** After every batch write, read the record back and confirm the
   count that landed equals the count sent; check any contested rows individually. The lead
   re-verifies the counts a pass reports with its own queries: a pass's summary is something to
   verify, not a fact to relay.
7. **The grain bracket.** A scope item is the unit a subcontractor would include / exclude / price
   as one thing (the floor: split by type / significant distinction, never by instance) and at most
   one row on a trade's scope sheet (the ceiling: package headers are the derive stage's output,
   never the pass's). One item per sheet is a ceiling violation; one item per instance is a floor
   violation. Where the trade file's grain section is silent, create at best judgment AND flag the
   grain question: recall never drops to grain uncertainty.
8. **Definitions before placements.** A pass reads only after the passes it references are already
   recorded (legends and schedules before the plans that tag them). The read plan encodes this
   order and the user approves it.
9. **Every round covers the scope the schedules themselves ground.** The passes reading legends and
   schedules record what a mark means, and they also own the scope items the schedules ground. The
   validation's single biggest capture gap was nobody owning schedule-grounded scope.
10. **The completeness check runs; what is still open is named.** The enumerate-and-audit pass
    (below) is a standing stage with a closure loop, never optional, and whatever remains open at
    the end is reported by name: never assumed closed, never zeroed by hope.

Also: never author door-owned records. Retractions, flag resolutions, questions-as-answers, and
package definitions are created only at their own doors: a pass that thinks an item should be deleted
or a flag should be closed says so in its report; a person acts at the door.

## The scope item row

A newly created scope item is a full row, not a name. Every new item writes:

- **name**: the concise line the sub reads: aim under ten words, the way a sub would say it, no code
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

Recorded text is what the bidder reads: plain sentences, no em dashes, no bolding. A verbose row
is a defect, not diligence.

## Run artifacts and the ledger

All run working files live under `~/.plumlayer/runs/<project-slug>/` (slug from the project name,
lowercase, spaces to hyphens; fall back to the projectId). Never committed to any repo, never
uploaded to the project except record files, never recorded as project entries. The set:

- `ledger.md`: the run ledger, appended as the run proceeds: every pass (round, unit, purpose, and
  the token usage the harness reports when the pass completes), every write batch (count sent,
  count verified, contested), the list of definitions kinds as they land, check-in outcomes, and
  every deviation or repair. The ledger is what makes the close-out report honest.
  Audience: agent. Its cost figures feed the close-out report's cost line; whatever crosses from
  it into that report becomes user-facing at the crossing and is translated there.
- `read-plan.md`: the read plan (stage 3), user-approved before any reading runs. Audience: user,
  it is shown to the user for approval.
- `context-packet.md`: the compiled context packet, regenerated between rounds (a projection off
  live records, never itself recorded). Audience: agent.
- `completeness/`: the completeness pass's enumerations, accounting output, and lists of what is
  still open. Audience: agent.
- `records/`: JSONL files for large batch writes (these do get uploaded, as the write
  mechanism). Audience: machine.

## The trade knowledge base

Ships with this plugin at `${CLAUDE_PLUGIN_ROOT}/trade-packages/`: one file per trade
(`painting.md`, `drywall.md`, …), mined from a real subcontractor-quote corpus, carrying what the
drawings will not say: how the trade bids, scope grain rules, exclusions and counterparties,
furnish/install seams, convention work no sheet states. `MANIFEST.md` there records the knowledge
version and source snapshot: read it at run start, record the version in the ledger, and cite it
in every convention-line record (`trade-convention:<trade>@<version>`). Each pass carries the trade
files relevant to its content families as part of its brief. Where a trade file is silent, the pass
creates at best judgment and flags the question (non-negotiable 7); the flag is a suggested
amendment to that trade file, surfaced in the close-out report.

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
Tell them what the run will do: you read the set in rounds and build
   one scope list off it, stopping for a check-in after every round, and they can stop or change
   course at any check-in. Give a rough sense of how long this set will take from its size, and
   confirm they are staying for the check-ins.
<!-- /user-facing -->

## 2. Context floor

Run these in order; each is read-or-run, never re-created (net-new facts only, everywhere).

1. **The reconciliation gate, read.** Call `reconcile_set(projectId)` report-only (never pass
   `record`, never pass a `deliveryId`: the bare call is the orientation check). Fold what it
   reports into the context packet. Check `.ran` flags before citing any drift number: a check
   that did not run is named as not-run, never folded in as "found nothing". Genuine document
   inconsistencies it surfaces are design-team question material, not blockers; pages the
   extraction missed are noted for the record.
2. **Orientation.** If the project has no orientation facts yet (`search(projectId, predicate:
   "structuralSystem", limit: 1)` and siblings empty), run the `learn-project` skill now, in full.
   If orientation exists, read its claims fresh instead of re-running it.
3. **Compile the context packet** (`context-packet.md`): identity and seed facts; systems; scope
   areas; set shape (disciplines, deliveries, spec-TOC status, reconciliation findings); hazards;
   and the definitions index section (empty before the first round; recompiled after every round).
   The packet is a projection: regenerate whole, never patch, never record it.

## 3. The read plan, user-approved

Group the set into passes and sequence them by reference dependency. A pass is a set of sheets read
together because they explain each other. Pull the sheet inventory (`set_grid`, falling back to
sampled `search(predicate: "discipline")` reads if the grid file-redirects), then:

1. **Group by content**, not by trade and not by page order: schedule/legend families, assembly
   and partition legends, envelope assemblies, enlarged plan families (units, kitchens, baths),
   finish/millwork details, elevations/sections, civil/site, landscape, each MEP discipline's
   legend+schedule family and its placement family, and so on.
2. **Sequence by reference dependency**: a pass reads only after the passes it references are
   recorded. Legends and schedules first, then the plans that reference them: schedules, legends,
   assembly sheets, then the placements that tag them. Structural general notes before framing
   plans; MEP legends/schedules before distribution.
3. **Say what each pass is for.** A pass that reads legends and schedules records what the marks
   mean and the scope the schedules themselves ground (non-negotiable 9). A pass that reads plans
   records scope where it is shown. Name the trade files each pass will carry, by content family:
   a kitchens pass carries appliances, casework, countertops, tiling, millwork, and so on.
4. **Group the passes into rounds**: a round is a set of passes that can run together. Passes that
   plausibly see the same scope (kitchens and unit plans, say) go in different rounds or run one
   after the other: two passes running at once on the same work create it twice. Passes with no
   content overlap may run together inside a round.

Write `read-plan.md`: the passes, the sheets in each (numbers plus file/page references), the trade
files each pass carries, the order the rounds run in, and what is deliberately excluded, named
outright rather than left silent.
<!-- user-facing -->
**Show the user the plan and get their approval before any
   reading runs.** Say it as a sentence, not a table of jargon: "six passes, legends and schedules
   first, then the plans that reference them; change anything before I start."
<!-- /user-facing -->
The read plan is a reviewable artifact; the user may cut, add, or resequence.

## 4. Read the rounds

Per round, in this exact loop:

1. **Recompile the definitions index** into the context packet: one line per defined thing:
   code, kind, one-line name, where defined, compiled from the record (`search` per known kind,
   paged to the real total; the ledger's list of kinds tracks which exist so far). Depth stays
   in the record: a pass resolves full definitions on demand mid-read (`search(subject:
   "<kind>:<code>")`), never from a paraphrase.
2. **Start the round's passes** with the pass brief (template below), each carrying: its sheets
   with file/page references, what it is reading for, the context packet, its trade files, and the
   mandates verbatim. Give each pass a unique run-prefix (its unit id) when filling the brief's
   subject scheme, so passes running at the same time can never collide on a created subject. Run
   passes at the same time only where their content does not overlap. Record each pass in the
   ledger (unit, purpose).
3. **Each pass reads deep and records directly**: render plus text per sheet (`render_page` +
   `get_page_text`), create/update/flag against the live list (pulled fresh via `list_scope_items`
   + targeted `search` at start), record via `record_batch` (≤500 per call, atomic) or
   `record_batch_file` for larger runs, verify the counts, report counts and anomalies.
4. **The lead verifies**: re-run the counts with your own queries (`search` filtered to the pass's
   sourceInstrument or subjects; `list_scope_items` delta), check contested rows, and record
   verified counts in the ledger. A mismatch stops the round and gets investigated, never
   papered over. When passes ran at the same time, also scan the round's new items for overlaps
   between them: the same work captured from two sides, convention lines especially, since passes
   running together cannot see each other's new items. List any overlap as a flag for the user at
   the check-in; merging is a person's call at the review surface, never the lead's.
5. **Check in with the user** (format below). Move to the next round only on their go-ahead.

Token accounting: when the harness reports a completed pass's token usage, record it in the ledger
against that pass. Where the harness doesn't surface a number, record the pass with usage unknown:
never estimate and never leave the row out.

## 5. The completeness check (standing, with a closure loop)

The definitions layer is the checklist: every defined thing must be accounted for by the scope
list. Run this after the placement rounds complete (and any time coverage is in doubt):

1. **Enumerate the defined things**: page through the record per definitions kind (the ledger's
   list of kinds; `search` with the kind prefix, compact rows, to the real total) into a file
   under `completeness/`.
2. **Pull the scope list**: `list_scope_items`: names, descriptions, notes per item.
3. **Account deterministically**: write and run a small local script: word-boundary token
   reference of each defined code in scope-item text (name / description / notes; evidence
   snippets excluded); kind-collisions and codes ≤2 characters divert to an ambiguous bucket for
   agent adjudication rather than string-match guessing. "Accounted" means textually referenced,
   not priced. This is a script's job, not an eyeball's: the judgment lives in adjudicating the
   ambiguous bucket and classifying what is left over, not in the matching.
4. **Classify every row that is left over**: accounted / plausibly-carried (inside an existing
   coarse item: name which) / not-scope (a definition with no work attached: say why) /
   unaccounted.
5. **Close the loop**: cluster the unaccounted rows into capture gaps, define supplemental
   schedule-grounded passes for them, run those reads (same brief template, same mandates), re-run
   the accounting. The validation run's first pass found 269 of 564 defined things unaccounted,
   closed 267 with one supplemental round, and named 2 still open: that loop is the designed
   behavior, not a recovery.
6. **Name what is still open**, in the ledger and in the close-out report, row by row.

Spec sections account differently (estimators never write CSI digit strings into scope text): a
spec section is accounted when the approved package split (stage 6) bundles it into a package.
After the split is approved, list every TOC section not bundled anywhere: those are the TOC
sections still open, reported the same way.

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
recorded in batches with the same count verification. Where an item genuinely straddles a package boundary, flag it as a package-boundary
question instead of force-tagging: the validation run tagged 275 of 283 and flagged 8, and those
8 flags were correct output, not failure. Boundary enrollments (exclusions, general requirements,
alternates on other packages) are manual-first doctrine: the run does not auto-author them;
the user authors boundary lines on the package surface, and anything the read suggested as a
boundary rides in flags and notes. Sheet-to-package assignment (`assign_sheet_packages`) is
a user-approved override: offer it only when the user asks; the derived relevant-pages
list already falls out of the citations.

## 8. Close out

<!-- user-facing -->
Report to the user, in plain words:

- **The scope list**: how many items, by category family; where to review it (the project's Scope
  view on plumlayer.com), and that every line shows the sheet and page it was read from.
- **What you would like them to look at**: the items you weren't sure how finely to split, the
  package-boundary questions, the document defects found (contradictions, missing schedule rows,
  duplicate sheets), and the assumed items that don't fit this job, each counted by kind and the
  leading ones named. Document defects worth sending to the design team are named as question
  candidates.
- **The count check**: what was enumerated, what closed, what is still open.
- **The package split**: approved packages, amendments, TOC sections deliberately unbundled.
- **What the run cost them**: how long it took, and the token totals where the harness reported
  them. Where a number was never reported, say it is unknown rather than presenting an estimate
  as a measurement.
- **What the trade files should learn**: cases the trade file doesn't cover, and things in it that
  don't apply to this job.
<!-- /user-facing -->

## The pass brief (template: every pass carries this, mechanically)

Fill the slots; never trim the mandates. A brief that omits a mandate reproduces a measured
failure.

```text
You are reading a construction drawing set for scope, for a Plumlayer project record.
Project: <projectId>. Round: <round number>. Your pass: <pass name> — sheets <numbers, with
fileId + 1-based pageInPdf for each>. You are reading for: <legends and schedules, recording what
the marks mean and the scope the schedules ground | plans, recording scope where it is shown>.
Content: <content families>.

Context: the run context packet is below <or attached>. It carries the project's identity,
systems, scope areas, set shape, hazards, and the definitions index (code → kind → name → where
defined). Resolve any mark's full definition on demand from the record:
search(subject: "<kind>:<code>"). Never resolve a mark from memory or from another sheet's
pattern — query the record (store-resolution is mandatory).

Trade knowledge: the trade files below <or attached> carry grain rules, seams, and convention
lines for your content families. Knowledge version: <version from MANIFEST.md>.

Read every sheet in your pass deep: render_page + get_page_text on each page (render for layout
and meaning, text for exact tokens). Then emit against the live scope list, which you pull fresh
at start (list_scope_items, plus targeted search):

1. CREATE a new scope item for work not on the list; UPDATE an existing item (new citation, note,
   resolved reference) for work already listed; FLAG an observation (a gap, an anomaly, an
   ungrounded reference you will not create, a grain question where the trade file is silent).
   Never a parallel list; never re-create; never silently skip.
2. CONVENTION LINES: for each convention line in your trade files that applies to your content
   families, create it if absent from the live list or update it if present —
   sourceInstrument "trade-convention:<trade>@<version>", evidence quoting the trade file's line
   and carrying basis: "trade-convention", NO sheet citation. If you judge a convention line
   inapplicable to this project, FLAG that with your reason. Silence on a convention line is a
   violation.
3. CITATION SHAPE: every drawing-grounded record's evidence names the sheet AND carries
   evidence.pageInPdf (1-based integer) for the page you actually read. Never a sheet without a
   page; never a fabricated page. The record door refuses pageless sheet citations — if it
   refuses something, fix the citation to what you actually read; never game the shape.
4. CAPTURE NEVER FILTERS: capture everything you see, trade-agnostic, at the grain of one row on
   a trade's scope sheet — split by type or significant distinction, never by instance (floor);
   never one item per sheet or package headers (ceiling). Distinctions that don't earn a row ride
   in the description and notes.
5. THE ROW: every new item writes the full row — name (concise, under ~10 words, the way a sub
   would say it),
   category (REQUIRED: the checklist-section grouping an estimator would use; reuse category
   strings across like work, never one per item), description (1-3 tight sentences, only what
   changes price or scope — never a re-narration of the schedule; the citation does the
   explaining), notesExternal/notesInternal only when there is a real note, quantity only where
   the sheet carries one as {value, unit}. Recorded text is what the bidder reads: plain
   sentences, no em dashes, no bolding. Verbose rows are defects.
6. GRAIN: follow your trade files' grain sections; where a trade file is silent, create at best
   judgment AND flag the grain question.
7. RECORD directly: record_batch (≤500 per call; subjects scopeItem:<run-prefix>-<seq> for
   new items; the item's existing subject for updates), or upload a JSONL and record_batch_file
   for large runs. After every batch, VERIFY: read the record back and confirm the count that
   landed equals the count sent; recheck any contested ids individually. Report exact counts.
8. Legends-and-schedules passes only: also record what the schedules define (extending the
   existing subject kinds you see in the definitions index — never creating a parallel
   vocabulary), AND own the scope items the schedules themselves ground: a schedule row family
   that is real priced work becomes scope items at the grain bracket, cited to the schedule
   sheet + page.

Report back: counts (created / updated / flagged, recorded / verified / contested), the
definitions kinds you added (if any), anomalies and document defects you flagged, convention
lines emitted and any you judged inapplicable (with reasons), and anything you could not read
(refused tokens, unreadable pages) stated honestly — an unread page is named, never silently
skipped. Your reading is your word: it lands under your authorship and governs provisionally,
so flag what you're unsure of rather than smoothing it.
```

## The check-in (what the user sees)

<!-- user-facing -->
After each round, before the next one starts, name the round you finished and what it covered,
then cover, in plain sentences:

- What you read and what landed: sheets read, items added, items updated, and what you flagged, by
  kind. Your own verified counts, never the ones a pass reported about itself.
- What you would like them to look at now: document defects, items you weren't sure how finely to
  split, anomalies, each with its sheet reference, reviewable on plumlayer.com.
- What is defined now that wasn't before, and anything the next round depends on.
- Anything that went sideways: a count that didn't match and how you fixed it, a page you couldn't
  read, a pass that stopped. Say it plainly.
- The plan for the next round, and the ask: proceed, adjust, or pause.

For example: "I've finished round one, the legends and schedules. Here is what landed, what I'd
like you to look at, and the plan for round two. Proceed, adjust, or pause?"
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
- **Run unattended**: check-ins are load-bearing until the user has enough cold runs
  behind them to decide otherwise, and that is their decision to make out loud, per run, never
  this skill's default.

## Historical note

The route-first harness (per-trade fan-out, reconcile-by-overlap) is retired doctrine. Do not
restore or run route-first machinery from git history as a scope path, and never present it as
current.
