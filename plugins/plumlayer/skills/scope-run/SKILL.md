---
name: scope-run
description: >
  Read a Plumlayer project's drawing set into one grounded, cited, trade-agnostic scope list,
  audit it for completeness, then amend and tag trade packages. Trigger on "scope this set",
  "/scope-run". Attended: the user approves the read plan and reviews at every check-in.
  Drives the project record's read and write verbs. Does not upload drawings (drawing-upload),
  orient from scratch or draft the baseline package split (learn-project), read sub proposals
  (bid-intake), or place takeoff measurements (takeoff).
---

# Scope run

## What this is

The production scope run: it builds the project's context floor, reads the set in rounds ordered
by reference dependency, produces one grounded, cited, trade-agnostic scope list, audits it with
the completeness pass, then amends and tags the trade packages, all on the hosted project record,
with the user reviewing at every check-in. Orientation is the `learn-project` skill, which this
skill runs first when orientation hasn't happened yet; orientation also drafts and creates the
baseline package split off the spec table of contents (Phase 1), so a package already exists for
every trade before this skill's expensive read starts. This skill amends that split with what the
scope read surfaces (Phase 2) and tags. The shape, in the estimator's own order:

> First assemble one massive singular list of all the scope line items across the entire job; then
> sort through and decide which trade packages to create; assembling them is assigning one new meta
> variable on an entirely scoped line item.

One grounded, cited, trade-agnostic scope list first; trade packages are projections off it. Every
mandate below exists because skipping it produces a measured, real failure: follow all of them.

**This run is attended.** The user approves the read plan before any reading and reviews at every
check-in. Never read past a check-in without the user's go-ahead. The package split is not a gate:
this run reads the baseline packages orientation created, amends them as the scope list surfaces
what the spec TOC could not see, shows what it did, and tags; they stay editable, and a correction
is a change on the site or a tool call.

Doctrine binds every step: **agents read and judge; deterministic tooling grounds; nothing enters
untraced.** Everything a reader records is its own reading, cited, carrying its authorship trail;
it becomes working truth the moment it lands; anything a person changes wins.

## The non-negotiables

Every stage below honors these. They are restated where they apply, but read them first: a run
that relaxes any one of them reproduces a measured, named failure.

1. **Cite everything, in the uniform shape.** Every drawing-grounded record carries evidence naming
   the sheet AND a resolvable 1-based page: `evidence.page` or `evidence.pageInPdf` as a positive
   integer for the page actually read. A sheet named with no page cannot be render-verified and the
   record door refuses it. Never fabricate a page or sheet to satisfy the door.
2. **Create / update / question against the live list.** Every reader holds the current scope list
   for its content families as match-or-create context: for each thing seen, create a new item,
   update an existing one (a new citation, a note, a resolved cross-reference), or raise a Question,
   with a title and a citation. Never a parallel list, never a re-create of what exists, never
   silent skipping of what's already listed. Before raising a Question, read `list_questions`: where
   an open one already covers the same ask, reply to it instead of asking it a second time.
3. **The convention-line emit mandate.** A reader whose trade files carry convention lines for the
   content families it reads MUST emit them: create if absent from the live list, update if
   present. Silence is a violation, not a judgment call; a reader judging a convention line
   inapplicable to this project raises a Question saying so, with its reason. Convention lines never masquerade
   as sheet-cited reads: their `sourceInstrument` is `trade-convention:<trade>@<knowledge-version>`
   (the pinned version from the knowledge manifest), their evidence quotes the trade file's line and
   carries the marker `basis: "trade-convention"`, and they carry no sheet citation. Where a sheet
   corroborates one, that citation updates the same item and the convention basis stays visible
   in the trail.
4. **Store-resolution is mandatory.** A mark, tag, or code is resolved by querying the project
   record (`search`), never from memory, never inherited from another sheet's read, never assumed
   from a similar-looking mark.
5. **Capture never filters.** Capture is trade-agnostic and complete: everything seen goes into the
   one shared list. Deciding what matters, what's priced, and whose trade it is happens downstream,
   never in the reader that read it.
6. **Every write is count-verified, at two boundaries.** After every batch write, the reader reads
   the record back and confirms the count that landed equals the count sent, and checks any
   conflicting rows individually, before it ends. The round runner separately re-verifies the same
   counts with its own queries before the next unit of that pass starts. A reader's report that its
   batches landed is verified at both its own boundary and the runner's; neither replaces the
   other. The lead adds a third, count-only check at the check-in, bounded by what `search` can
   actually filter on (subject, predicate, trustClass, and a `text` substring across subject,
   predicate, and value; there is no `sourceInstrument` filter, so never assert one). What the lead
   takes independently is the created count per unit: `search(text: "scopeItem:<unit-id>-",
   limit: 1)`, reading `count`, a real total over the entries whose subject carries that prefix.
   Updates and Questions land on subjects that already existed, so no prefix finds them: they are
   verified at the reader's boundary and again at the runner's, by reading the named subjects back,
   and the lead reports them as runner-verified rather than asserting a check it did not run. The
   lead never calls `list_scope_items` during the run: that verb returns the whole projected scope
   list, unbounded, and pulling it is how the lead's context stops being cheap. When the record
   grows a `sourceInstrument` filter, the lead's own check widens to the full per-unit totals.
7. **The grain bracket.** A scope item is the unit a subcontractor would include / exclude / price
   as one thing (the floor: split by type / significant distinction, never by instance) and at most
   one row on a trade's scope sheet (the ceiling: package headers are the derive stage's output,
   never the reader's). One item per sheet is a ceiling violation; one item per instance is a floor
   violation. Where the trade file's grain section is silent, create at best judgment AND raise a
   Question naming the grain question: recall never drops to grain uncertainty.
8. **Definitions before placements.** A pass reads only after the passes it references are already
   recorded (legends and schedules before the plans that tag them). The read plan encodes this
   order and the user approves it.
9. **Every round covers the scope the schedules themselves ground.** The passes reading legends and
   schedules record what a mark means, and they also own the scope items the schedules ground.
10. **Run, or stop and report; never create a consent step.** The user's decisions in this skill are
   the read plan and each check-in. Everything else the run does is its own work, recorded with its
   trail and editable afterward. Never stop to collect approval for a course you have already
   chosen, and never offer a recommended yes: if something is genuinely wrong, stop, say what is
   wrong, and hand it over; if nothing is wrong, proceed and say what you did.
11. **The completeness check runs; what is still open is named.** The enumerate-and-audit pass
    (below) is a standing stage with a closure loop, never optional, and whatever remains open at
    the end is reported by name: never assumed closed, never zeroed by hope.

Also: door-owned records (Question resolutions, questions-as-answers) are created only at their own
doors; a reader that thinks a Question should be closed says so in its report and a person acts at
the door. That door is `close_question`, and you call it only when the user settles the answer in
the session: their reason goes in `note` in their own words, and a Question you merely think looks
answered stays open. `reopen_question` puts one back when they tell you it was closed in error. Removing a scope item is different: `retire_scope_item` is the one door for that act, for a
person and an agent alike. Use it only for a row the user asked removed, put the user's ask in
`basis` in their words, one item per call; a row you merely suspect is wrong goes in the report.

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

- `ledger.md`: the run ledger, appended as the run proceeds: every read unit (round, pass, unit,
  purpose), every write batch (count sent, reader-verified, runner-verified, conflicts), the list of
  definitions kinds as they land, check-in outcomes, every deviation or repair, and the run's
  `phase:` lines, one per phase boundary, appended by the lead. The ledger is what makes the
  close-out report honest, and its `phase:` lines are what makes a run resumable. Audience: agent.
- `read-plan.md`: the read plan (stage 3): passes and the read units within each, their sheets with
  file/page references, the trade files each pass carries, round order, and what is deliberately
  excluded. Audience: agent. What the user hears at the gate is defined in stage 3.
- `context-packet.md`: the compiled context packet, regenerated between rounds (a projection off
  live records, never itself recorded). Audience: agent.
- `briefs/`: one small file per pass, written by that round's runner, carrying the pass's filled
  slot values: what the pass reads for, its content families, the knowledge version, the trade file
  paths it carries, and the subject prefix scheme. A reader opens its own pass file from here. The
  mandates are never in it. Audience: agent.
- `completeness/`: the completeness pass's enumerations, accounting output, and lists of what is
  still open. Audience: agent.
- `records/`: JSONL files for large batch writes (these do get uploaded, as the write
  mechanism). Audience: machine.

## Phases, and who holds what

The run is one attended conversation, and nothing in it accumulates. The project record is the
run's memory; the run folder is its bookkeeping; no level of the run holds between its units
anything a later unit needs. The user never manages context: the only decisions they make are
the read plan and each check-in, and no prompt ever mentions sessions, compaction, or usage.

The run executes at three levels. Each level is a separate agent context, bounded by construction:

- **The lead** is this skill, running in the user's session. It does the cheap work only:
  preconditions, context floor, the read plan, the check-ins, amending, tagging, close out. For
  each round it starts one round runner and receives one fixed-shape summary. It never holds a
  pass brief, a trade file, a reader's report, or a page of the set. What it keeps per round is
  the dispatch line and the summary, nothing else.
- **The round runner** (the plugin's `scope-round-runner` agent, one fresh instance per round)
  owns the round: it recompiles the definitions index into the context packet, runs the round's
  passes as read units exactly as stage 4 defines them, verifies every unit with its own queries,
  runs the round-end overlap scan, appends the ledger, returns its summary, and ends. Its context
  is bounded to one round. The completeness check (stage 5) runs the same way: one runner for the
  enumeration, the accounting, and the closure loop, including any supplemental reads.
- **The reader** (the plugin's `scope-reader` agent, one fresh instance per read unit) reads one
  unit and records, as stage 4 and the pass brief define. It ends when it has reported.

Handoff is by file and record, never by inlined text. A dispatch at any level carries only
pointers: the project id, the round or unit id, the run folder path, and the page references.
The reader opens its pass brief and the context packet from the run folder, and its trade files from
the plugin's trade-knowledge directory, all by the paths it is handed; the runner opens the read
plan and the ledger. Nothing from those files is pasted into a
dispatch, because whatever is pasted stays in the dispatcher's context for the rest of the run.

Reports travel upward in a fixed short shape, counts and named anomalies only (the shapes are
given with the brief templates below). A runner's summary is what the lead reads at the check-in,
verified against the record with the lead's own count queries, never relayed as-is.

Phase boundaries are the ledger's `phase:` lines, one appended by the lead at each of: plan
approved; round N complete; completeness closed; packages amended; tagged; closed out. On every
start this skill reads the ledger first: a run in flight resumes at the phase after the last line,
with the read plan read off disk and the packet regenerated from the record. A missing run folder
for a project that already carries scope items is named plainly and the run re-plans against the
record; the live-list mandate (non-negotiable 2) keeps a re-read from creating what is already
there. Resumption is crash and multi-day hygiene. It is never offered to the user as a way to
manage cost, and the check-in never suggests it.

## The trade knowledge base

Ships with this plugin at `${CLAUDE_PLUGIN_ROOT}/trade-knowledge/`: one file per trade
(`painting.md`, `drywall.md`, …), mined from a real subcontractor-quote corpus, carrying what the
drawings will not say: how the trade bids, scope grain rules, exclusions and counterparties,
furnish/install seams, convention work no sheet states. `MANIFEST.md` there records the knowledge
version and source snapshot: read it at run start, record the version in the ledger, and cite it
in every convention-line record (`trade-convention:<trade>@<version>`). Each pass carries the trade
files relevant to its content families as part of its brief. Where a trade file is silent, the
reader creates at best judgment and raises a Question (non-negotiable 7); the Question is a suggested
amendment to that trade file, surfaced in the close-out report.

## 1. Preconditions

1. **Project exists and is the user's intent.** `list_projects`, confirm which project with the
   user, get its `projectId`. No project → hand off to `project-setup`.
2. **Resume, if a run is already in flight.** With the `projectId` in hand and before anything else,
   read `ledger.md` from the run folder. A ledger with `phase:` lines means a run is in flight:
   resume at the phase after the last one, reading `read-plan.md` off disk and regenerating the
   context packet from the record rather than re-planning or re-reading what is already recorded.
   A project that already carries scope items but has no run folder is named plainly and re-planned
   against the record; the live-list mandate (non-negotiable 2) is what keeps a re-read from
   creating what is already there. Resumption is crash and multi-day hygiene, nothing else: never
   offer it to the user as a way to manage anything, and never raise it at a check-in.
3. **Drawings are recognized.** `list_drawing_deliveries(projectId)`: no deliveries → stop
   plainly, hand off to `drawing-upload`. Spot-check recognition actually recorded:
   `search(projectId, predicate: "appearsOnPage", limit: 1)`: zero rows → hand off to
   `drawing-upload`.
4. **Spec book, if it exists.** `search(projectId, predicate: "inDivision", limit: 1)`: spec
   sections present means the spec-TOC leg has run. Absent: ask the user whether a project manual /
   spec book exists. If one does, run it through `drawing-upload`'s spec-book leg first (upload +
   `extract_spec_toc`): the package split anchors on the spec table of contents and is
   substantially weaker without it. If the project genuinely has no spec book, proceed and name
   that in the ledger and the close-out report: orientation created no baseline packages for this
   project (no spec sections, no anchor), and section 6 below derives the whole split from
   the finished scope list instead.
5. **Trade knowledge present.** Read `${CLAUDE_PLUGIN_ROOT}/trade-knowledge/MANIFEST.md`; record
   the version in the ledger. Missing → stop and report a broken plugin install rather than running
   knowledge-blind.
6. **The user is present.**
<!-- user-facing -->
Tell them what the run will do: you read the set in rounds and build
   one scope list off it, stopping for a check-in after every round, and they can stop or change
   course at any check-in. Give a rough sense of how long this set will take from its size, and
   confirm they are staying for the check-ins.
<!-- /user-facing -->
   Where it can, the run starts from a clean conversation, but it never raises sessions,
   compaction, context, or usage with the user, at run start or at any point after it.

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
   If orientation exists, read its entries fresh instead of re-running it. **Also re-run
   `learn-project`** when the project has spec sections (`inDivision` entries present) but no
   packages on it yet (`solicitation_list_packages(projectId)` empty): orientation owns the
   baseline split, and a spec book with no packages means it hasn't drafted one yet.
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
5. **Divide each pass into read units.** Within a pass, the sheets split into read units. A read
   unit is one sheet. The exception is a multi-page instrument that cannot be understood in parts
   (a schedule continued across pages, a legend split over sheets), which stays one unit, at most
   four pages; beyond that it splits at the page break, and the later unit resolves what the
   earlier one recorded from the record. Sheets that reference each other but are not contiguous
   (a plan and the enlarged sheet its keynotes point at) are separate units; the later one resolves
   what the earlier recorded from the record. A row that continues across the split belongs to the
   unit that reads its first page, which reads the continuation page for that row only. List the
   units in each pass, in reading order.

Write `read-plan.md`: the passes and the units within each (numbers plus file/page references), the
trade files each pass carries, the order the rounds run in, and what is deliberately excluded, named
outright rather than left silent.
<!-- user-facing -->
Before any reading runs, tell the user, in a few plain sentences, not a table:

- The order: which families go first and what follows, in one sentence. No reasons; they know why
  schedules come before plans.
- What is deliberately left out, by sheet family or number. Say it plainly: anything here will not
  be scoped.
- When the first check-in will be, roughly.
- The ask: what is worth catching is a family left out that carries scope, something read before
  what defines it, or two families read together that could double count. Then: go, or cut, add,
  or reorder.

For example: "Legends and schedules first, then unit plans, then kitchens and baths, then
elevations and details, site last. I'm leaving out the ADA mounting-height sheets and the
landscape set. First check-in in about twenty minutes. Go, or change anything."

Never show passes as a table, counts of dispatches, bundle codes, lanes, model names, or anything
about how the run is executed. Never offer a recommended option.
<!-- /user-facing -->

On the go-ahead, append `phase: plan approved` to the ledger. Nothing reads before that line exists.

## 4. Read the rounds

The reading happens one level down. Per round, the lead does exactly this and holds nothing else:

1. **Start one round runner.** Dispatch a fresh `plumlayer:scope-round-runner` with the runner
   dispatch below: pointers only, no pass brief, no trade file, no read-plan text. Append the
   dispatch line to the ledger. That line and the summary that comes back are the only things this
   round leaves in the lead's context.
2. **The runner owns the round.** It recompiles the definitions index into the context packet,
   writes each pass's brief file, runs the passes as read units in reading order (one fresh
   `plumlayer:scope-reader` per unit, one unit at a time within a pass, passes that do not overlap
   running alongside each other), verifies every unit against the record with its own queries before
   the next unit of that pass starts, notes intra-pass and round-end overlaps, and appends the
   ledger. The per-unit loop lives in the `scope-round-runner` agent definition and the reader
   mandates live in the `scope-reader` agent definition. Neither is restated here, and neither is
   ever trimmed.
3. **Read the summary and verify what you can yourself.** The runner returns one fixed-shape summary
   (shape below). Before you say a number out loud, take the created count for each of the round's
   units with your own `search(text: "scopeItem:<unit-id>-", limit: 1)`, reading `count`. That is
   the third boundary of non-negotiable 6, and it is count-only: never a row list, never
   `list_scope_items`. It reaches creates and not updates or Questions, because those land on subjects
   that already existed and `search` has no `sourceInstrument` filter to reach them by. Say the
   update and Question counts as the runner verified them, and the created counts as your own. A
   mismatch stops the run and gets investigated, never papered over.
4. **Append `phase: round N complete` to the ledger**, with the verified totals.
5. **Check in with the user** (format below). Move to the next round only on their go-ahead, and
   start the next round with a fresh runner.

## 5. The completeness check (standing, with a closure loop)

The definitions layer is the checklist: every defined thing must be accounted for by the scope
list. Run this after the placement rounds complete (and any time coverage is in doubt). It runs the
same way a round does, one level down:

1. **Start one round runner in completeness mode.** Same runner dispatch as stage 4, with
   `completeness` in place of the round id. It enumerates the defined things per kind, pulls the
   scope list, accounts deterministically with a small local script it writes, classifies every
   leftover row (accounted, plausibly-carried, not-scope, unaccounted), clusters the unaccounted
   rows into capture gaps, defines and runs supplemental schedule-grounded passes for them through
   the same readers, and re-runs the accounting. The loop lives in the `scope-round-runner` agent
   definition. The validation run's first pass found 269 of 564 defined things unaccounted, closed
   267 with one supplemental round, and named 2 still open: that loop is the designed behavior, not
   a recovery.
2. **Read the summary and verify what you can yourself**, the same way stage 4 step 3 does: the
   created counts for any supplemental units, by `search(text: "scopeItem:<unit-id>-", limit: 1)`,
   `count` only, no row list and no `list_scope_items`. The accounting figures (enumerated,
   accounted, plausibly carried, not scope, unaccounted, before and after the closure loop) come
   from the runner's summary, and the still-open rows you check by name, reading back the ones the
   runner named. Report the accounting as the runner's, the created counts as your own.
3. **Name what is still open**, row by row, in the ledger and in the close-out report, then append
   `phase: completeness closed`. Never assumed closed, never zeroed by hope.

Spec sections account differently (estimators never write CSI digit strings into scope text): a
TOC section is accounted when it appears as a package's `tradeCode` or in its `codes`, read fresh
via `solicitation_list_packages`, not a local artifact. After stage 6's amendments are applied,
list every TOC section that appears on no package's `tradeCode` or `codes`: those are the TOC
sections still open, reported the same way.

## 6. Amend the packages: scope-driven (Phase 2)

The estimator-judgment stage. Packages are bundles of spec sections grouped by how subcontractors
actually split themselves in the market, not by the book's divisions. The baseline split (Phase 1)
was drafted and created at orientation (`learn-project`): read it fresh via
`solicitation_list_packages(projectId)` rather than re-drafting it.

1. **Phase 2: scope-driven amendments.** Where the scope list surfaces what the TOC cannot see (a
   specialty assembly that wants its own bidder, an either-or item probed as an alternate, a
   package that should collapse into another once scale is understood), apply the amendment live:
   `solicitation_create_package` for a genuinely new package, `solicitation_update_package` to
   fold, split, or rename an existing one. Resolve the amendment's trade the same way as
   orientation (`directory_list_trades`, exact `code` first then `query` by name/alias; the
   catalog trade id recorded verbatim, store-resolution, non-negotiable 4), and set `codes` to the
   other sections the package now covers (verbatim catalog ids, never repeating the package's own
   `tradeCode`), with a one-line rationale in `notes` (plain prose, no fixed shape).
   `solicitation_update_package(packageId, codes)` replaces the whole list, so a fold or split
   rewrites the lists of every package involved. A package with no reasonable catalog match cannot
   be created or amended into one: name it "no catalog trade, not created" in the report.
<!-- user-facing -->
Show what you did in plain words, mirroring orientation's wording: name the amendments made
   (packages created, split, collapsed, or renamed), each with its one-line rationale. Say it as
   what you did, not as a question: "I amended the split: two packages, here's why. Change any of
   them on the site or tell me and I will redo it."
<!-- /user-facing -->
   No approval is collected: the amendment governs as applied and stays editable; a correction is
   a tool call. Tagging (section 7) happens into the split as amended, never into one you kept to
   yourself. Once the amendments are applied, append `phase: packages amended` to the ledger.
2. **Empty-baseline case.** When `solicitation_list_packages` returned no packages because the
   project has no spec sections (precondition 4), this stage derives the whole split from the
   finished scope list instead of amending a baseline: same bundling logic as orientation, same catalog
   resolution, same `solicitation_create_package` calls and `codes`/`notes` usage. Say so plainly in
   the report: the split was derived here, from the scope list, because there was no spec book to
   anchor an earlier baseline.

## 7. Tag

Assign each scope item its home trade off the live packages: one `belongsToTrade` record per item
(value: the package's catalog trade id, read fresh via `solicitation_list_packages`), recorded in
batches with the same count verification. An item whose work falls under a spec section no live
package bundles (the completeness check's list of unbundled TOC sections, which is where a "no
catalog trade, not created" bundle ends up) gets that raw spec section as its tag value, as a
deliberate choice named in the close-out report, never as an unmarked default. Where an item genuinely straddles a package
boundary, never hold it as a question: tag it to every candidate trade and keep moving.
`belongsToTrade` carries the best single guess as the home trade; each other candidate trade gets
a `packageRole:<trade>` record with role `candidate` and a note in the shape "confirm trade
responsibility: could be `<home>` or `<this trade>`" (internal only, never bidder-facing). Record
these alongside the `belongsToTrade` batch, with the same count verification. The candidate
placement is the one enrollment kind this run authors; exclusions, general requirements, and
VE/alternates stay manual-first doctrine: the run does not auto-author them, the user authors
those boundary lines on the package surface, and anything the read suggested toward one rides in
Questions and notes. Sheet-to-package assignment (`assign_sheet_packages`) is the user's
call: offer it only when the user asks; the derived relevant-pages list already falls out of
the citations. When the tag batches are verified, append `phase: tagged` to the ledger.

## 8. Close out

<!-- user-facing -->
Report to the user, in plain words:

- **The scope list**: how many items, by category family; where to review it (the project's Scope
  view on plumlayer.com), and that every line shows the sheet and page it was read from.
- **What you would like them to look at**: the items you weren't sure how finely to split, the
  document defects found (contradictions, missing schedule rows, duplicate sheets), and the
  assumed items that don't fit this job, each counted by kind and the leading ones named.
  Document defects worth sending to the design team are named as question candidates.
- **Trade responsibility to confirm**: how many items you placed in more than one trade's package
  (count each item once, however many packages it sits in), the leading trades named, and where
  to review them (the "Trade responsibility to confirm" section in each affected trade's package
  on plumlayer.com).
- **The count check**: what was enumerated, what closed, what is still open.
- **The package split**: the amendments made this run (created / split / collapsed / renamed,
  each with its rationale), the packages derived here from scratch only in the no-spec-book case,
  and TOC sections deliberately unbundled.
- **How long it took**: wall-clock from the read plan's approval to this report.
- **What the trade files should learn**: cases the trade file doesn't cover, and things in it that
  don't apply to this job.
<!-- /user-facing -->

The report is written off the ledger, not off memory: the wall-clock, the counts, the deviations,
and what is still open are all there. When it has been given, append `phase: closed out`.

## The dispatches and the report shapes

Every dispatch carries pointers and nothing else. Whatever is pasted into a dispatch stays in the
dispatcher's context for the rest of the run, so the packet, the trade files, the read plan, and the
brief values are opened by the agent that needs them, from the paths it is handed.

The mandates are not in these templates. They live in the two agent definitions the plugin ships,
`scope-round-runner` and `scope-reader`, where each dispatched instance reads them fresh. They are
never trimmed there and never restated here: a run that relaxes one reproduces a measured failure.

**Runner dispatch** (the lead writes this, once per round and once for the completeness pass):

```text
subagent_type: plumlayer:scope-round-runner
Project: <projectId>. Round: <round number, or "completeness">.
Run folder: <path>. Read plan: <path to read-plan.md>.
Run your round as your definition says, then return your summary.
```

**Reader dispatch** (the runner writes this, once per read unit):

```text
subagent_type: plumlayer:scope-reader
Project: <projectId>. Round: <round number>. Pass: <pass name>. Unit: <unit id>.
Pages: <sheet number + fileId + 1-based pageInPdf, one per page>.
Run folder: <path>. Context packet: <path>. Pass brief: <path to briefs/<pass-id>.md>.
Trade files: <paths>.
Read your unit as your definition says, then return your report.
```

**The reader's report** comes back in this shape, counts and named anomalies only:

```text
unit: <unit id>   pass: <pass name>   round: <n>
pages read: <sheet number + pageInPdf, one per page read>
pages unread: <sheet number + pageInPdf + reason, or "none">
created: <n>   updated: <n>   questions: <n>
updated subjects: <the subject of every item updated, or "none">
sent: <n>   landed: <n>   conflicts: <ids and how each resolved, or "none">
definitions kinds added: <kinds, or "none">
convention lines: emitted <n>; inapplicable: <line + reason, one per line, or "none">
anomalies: <one line each, with sheet and page, or "none">
grain questions: <one line each, with sheet and page, or "none">
door-owned suggestions: <one line each, or "none">
```

The `updated subjects:` line is what lets the runner find an update back: a create is findable by
its `scopeItem:<unit-id>-` prefix, an update lands on a subject that already existed and nothing
else in the report names it.

**The runner's summary** comes back in this shape, and is what the lead reads at the check-in,
after taking the round's created counts off the record itself:

```text
round: <n, or "completeness">   passes: <pass names>
units read: <unit ids, in reading order>
per unit: <unit id> created <n> updated <n> questions <n> verified <yes/no>
totals verified: created <n> (entry count under the unit prefixes), updated <n>, questions <n>
conflicting rows: <id + how each resolved, or "none">
overlap notes: <item name + the two units, one per line, or "none">
anomalies: <one line each, with sheet and page, or "none">
unread pages: <sheet + page + reason, one per line, or "none">
definitions kinds added: <kinds, or "none">
deviations and repairs: <one line each, or "none">
ledger: <path>, appended through <last line written>
```

In completeness mode the summary carries these lines as well, which are where the close-out
report's "what was enumerated, what closed" figures come from:

```text
enumerated: <n>
first pass: accounted <n>, plausibly carried <n>, not scope <n>, unaccounted <n>
after closure: accounted <n>, plausibly carried <n>, not scope <n>, unaccounted <n>
supplemental units run: <unit ids, or "none">
still open: <one line per unaccounted row, naming it, or "none">
spec sections bundled: <n>; TOC sections seen unbundled so far: <n>
```

## The check-in (what the user sees)

<!-- user-facing -->
After each round, before the next one starts, name the round you finished and what it covered,
then cover, in plain sentences:

- What you read and what landed: sheets read, items added, items updated, and what you raised as
  Questions, by kind. Your own verified counts, never the ones reported up to you.
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

- **Upload or recognize drawings** (`drawing-upload`), **create projects** (`project-setup`),
  **read sub proposals** (`bid-intake`), **place takeoff measurements** (`takeoff`), **draft the
  baseline package split** (Phase 1, owned by `learn-project`).
- **Author boundary enrollments other than trade-responsibility candidates**: exclusions, general
  requirements, and VE/alternates stay manual-first doctrine; the user authors those boundary
  lines at the package surface.
- **Score itself against a bid eval**: the acceptance harness was repo-side study machinery, not
  product.
- **Resolve or approve anything on the user's behalf**: door-owned acts stay at their doors.
  (Removing a scope item the user asked removed is not this: see `retire_scope_item` above.)
- **Manage the user's session or context**: the run is bounded by its own structure. Each round and
  each read unit runs in a fresh agent that ends when it has reported, so nothing accumulates and
  there is nothing for the user to manage.
- **Run unattended**: check-ins are load-bearing until the user has enough cold runs
  behind them to decide otherwise, and that is their decision to make out loud, per run, never
  this skill's default.

## What this skill never runs

Do not restore or run per-trade fan-out / reconcile-by-overlap machinery as a scope path, and never
present it as current.
