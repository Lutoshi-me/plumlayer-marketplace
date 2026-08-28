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
skill dispatches first when orientation hasn't happened yet; orientation also drafts and creates the
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
   an open one already covers the same ask, reply to it instead of asking it a second time. A
   Question is about the project, never about a Plumlayer failure; a read or write that fails is
   reported and handled in the run's own failure path, not raised as a Question. Question text is
   plain estimator words, per docs/plugin-text-style.md.
3. **The convention-line record mandate.** A trade's convention lines are a property of the trade,
   not of the sheet or the unit reading it: the pass runner records them once, at pass start,
   after a deterministic check that they are not already on the record
   (`search(subjectPrefix: "scopeItem:conv-<trade>-", limit: 1)`, reading `count`), never per
   reader and never per unit. Convention lines never masquerade as sheet-cited reads: their
   `sourceInstrument` is `trade-convention:<trade>@<knowledge-version>` (the pinned version from
   the knowledge manifest), their evidence quotes the trade file's line and carries the marker
   `basis: "trade-convention"`, and they carry no sheet citation. A reader never creates or
   recreates one; where a sheet corroborates one, that citation updates the same item and the
   convention basis stays visible in the trail, and where a sheet contradicts one for this
   project, the reader raises a Question naming it rather than deciding on its own.
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
   actually filter on (subject, subject prefix, predicate, and a `text` substring across subject,
   predicate, and value). What the lead takes independently is the created count per unit:
   `search(subjectPrefix: "scopeItem:<unit-id>-", limit: 1)`, reading `count`, which follows the
   filter, so it is a real total over the entries whose subject starts with that prefix. That count
   is never copied from a reader's report; the reader's own item count travels separately, as
   `items` on the runner's `verified` ledger line.
   Updates and Questions land on subjects that already existed, so no prefix finds them: they are
   verified at the reader's boundary and again at the runner's, by reading the named subjects back,
   and the lead reports them as runner-verified rather than asserting a check it did not run.
   Convention-line writes are the runner's own, verified at its own boundary the same way; report
   their counts as the runner verified them too. The
   lead never calls the unfiltered `list_scope_items` during the run: that verb walks the whole
   projected scope list, and pulling it is how the lead's context stops being cheap. It belongs to
   the completeness accounting and to nothing else. When the record grows a `sourceInstrument`
   filter, the lead's own check widens to the full per-unit totals.
7. **The grain bracket.** A scope item is the unit a subcontractor would include / exclude / price
   as one thing (the floor: split by type / significant distinction, never by instance) and at most
   one row on a trade's scope sheet (the ceiling: package headers are the derive stage's output,
   never the reader's). One item per sheet is a ceiling violation; one item per instance is a floor
   violation. Where the pass knowledge's grain rules are silent, create at best judgment AND raise
   a Question naming the grain question: recall never drops to grain uncertainty.
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
12. **A remark about spend never trims a mandate.** Every verification in this file stands whatever
    the user says about what the run is costing them. If they raise it, say plainly what is running
    and where the next natural stopping point is, and stop there if they ask; never answer it by
    doing less of the work you then report on. A verification that did not run is named as not run,
    by name, in the ledger and out loud, in the same breath as the numbers it would have covered.
    Never offer to trim, never put the question of whether to continue back to them in terms of
    what it costs, and never offer resumption as a way to manage it.

Also: door-owned records (Question resolutions, questions-as-answers) are created only at their own
doors; a reader that thinks a Question should be closed says so in its report and a person acts at
the door. That door is `close_question`, and you call it only when the user settles the answer in
the session: their reason goes in `note` in their own words, and a Question you merely think looks
answered stays open. `reopen_question` puts one back when they tell you it was closed in error. Removing a scope item is different: `retire_scope_item` is the one door for that act, for a
person and an agent alike. Use it only for a row the user asked removed, put the user's ask in
`basis` in their words, one item per call; a row you merely suspect is wrong goes in the report.

## The scope item row

A newly created scope item is a full row, not a name. Every new item writes:

- **name** (required): the line as it reads on a scope sheet: what is done, to what, where, under
  about twelve words, the way a sub would say it ("Repoint brick masonry at facade", "Install
  lintels above CMU openings"; not a recitation of every type mark). A mark or tag belongs here
  when it is how the sub finds the work.
- **category** (required): the section heading on the checklist an estimator would use ("Metal
  Stud Partitions", "Unit Casework", "Sealants & Firestopping"). Group like work under the same
  category string; never invent a fresh category per item. The review surface groups by this: an
  uncategorized list renders as a wall.
- **description** (optional, zero to three sentences): only what a bidder must know to price the
  line that the name and citation do not already say: the product or method the drawings call
  for, the extent or limits, a rated or special condition. A simple item has none. The citation
  points at the sheet, and the doctrine is cite, don't rewrite: never transcribe the schedule,
  the detail, or the bar sizes into the row, and when the scope is a schedule the row is the
  schedule's name and its citation, not its contents.
- **notesExternal** (optional, one sentence): an instruction to the bidder about the line: what is
  by others, what to break out, what to confirm, what is an alternate.
- **notesInternal** (optional, one sentence): a watch item for the estimator: an open Question, a
  conflict between sheets, an assumption to check. Never a citation audit or a correction of an
  earlier write; that is a Question.
- **quantity**: only where the sheet itself carries one, as `{value, unit}`.

Recorded text is what the bidder reads: plain sentences, no em dashes, no bolding, never a
sheet-by-sheet narration. The door refuses text over its bound (`name` 80 characters, `category`
60, `description` 400, `notesExternal` and `notesInternal` 300 each); a row shaped by these rules
never comes near them. A verbose row is a defect, not diligence.

## Run artifacts and the ledger

All run working files live under `~/.plumlayer/runs/<project-slug>/` (slug from the project name,
lowercase, spaces to hyphens; fall back to the projectId). Never committed to any repo, never
uploaded to the project except record files, never recorded as project entries. The set:

- `ledger.md`: the run ledger, appended as the run proceeds, one line per entry in the fixed shapes
  the `scope-round-runner` definition gives, plus the lead's own `pass:` and `phase:` lines.
  Nothing else goes in the ledger: no headings, no bullets, no paragraphs, no re-telling of a
  report. It is appended, never rewritten and never reformatted. The ledger is what makes the
  close-out report honest, and its `phase:` lines are what makes a run resumable. Audience: agent,
  and it feeds the close-out report, so whatever crosses into that report becomes user-facing at
  the crossing and is translated there.

  The lead's own two line shapes, which the runner never writes:

  ```text
  pass: <round> <pass or leg id> units <n> created <n> updated <n> questions <n> lead-verified <yes|no>
  phase: <boundary name>
  ```

- `grid/`: the sheet grid as the fetch agent put it on disk in stage 3, one file per page, copied
  byte for byte where the payload came back as a file. Nothing above the script reads it.
  Audience: machine.
- `inventory.md`: one line per sheet, then the count tables and the sheet number digest at the tail.
  Written by the plugin's plan script off `grid/`. The lead reads the tables and the digest, never
  the sheet lines. Audience: agent. Alongside it, `inventory.json`, the same rows normalized for the
  script's own expand step. Audience: machine.
- `pass-assignment.json`: the lead's grouping, sequencing, and exclusions, written by hand in stage
  3: rounds, passes, trade files, how each pass selects its sheets, and each exclusion's reason. It
  carries no sheet titles and no page numbers. Audience: agent.
- `read-plan.md`: the read plan (stage 3): passes, their legs, and the read units within each, their
  sheets with file/page references, the trade files each pass carries, round order, any pass under
  three units the script folded into a sibling or the round's largest pass and why, and what is
  deliberately excluded. Written by the plugin's plan script from `pass-assignment.json`, never by
  hand. Audience: agent. What the user hears at the gate is defined in stage 3.
- `context-packet.md`: the orientation packet every reader loads whole, regenerated between rounds
  (a projection off live records, never itself recorded): identity, systems, scope areas, set
  shape, hazards, the open anomalies a reader must know, and the kinds list, one line per kind
  giving its name, plain label, count, and the sheet it is defined on. No definition entries in
  it, and it does not grow with the number of definitions. Audience: agent.
- `definitions/`: one file per kind, `<kind>.md`, one line per code giving the code, its plain
  name, and where it is defined, written by the boundary runner from the same recompile that
  produces the kinds list. A reader opens the file for each kind its pass brief names, plus any
  kind it meets on a sheet that the packet's kinds list carries and its brief did not name.
  Audience: agent.
- `briefs/`: one small file per pass, written by that pass's runner, carrying the pass's filled
  slot values: what the pass reads for, its content families, the knowledge version, the trades it
  carries, the subject prefix scheme, and the kinds this pass reads. A reader opens its own pass
  file from here. The mandates are never in it. Audience: agent. Alongside each brief,
  `<pass-id>-knowledge.md`, the pass knowledge: the carried trades' grain sections cut verbatim
  from the shipped trade files by the plugin's script, with the knowledge version at the top.
  Audience: agent.
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
  each pass it starts one runner and receives one fixed-shape summary; what it keeps per pass is
  the dispatch line and, once it has taken its own counts, one `pass:` line in the ledger. It never
  holds a pass brief, a trade file, a reader's report, or a page of the set.
- **The pass runner** (the plugin's `scope-round-runner` agent, one fresh instance per pass or pass
  leg) owns one pass: it writes the pass brief, runs the pass's read units exactly as stage 4
  defines them, verifies every unit with its own queries, notes overlaps inside the pass, appends
  the ledger in its fixed line shapes, returns its summary, and ends. Its context is bounded to one
  pass of at most twelve units, and it never grows with the size of the round. One further instance
  closes each round at its boundary: the cross-pass overlap scan and the definitions recompile.
  The completeness check (stage 5) is bounded the same way: one instance for the
  enumeration and the accounting, one per supplemental read leg.
- **The reader** (the plugin's `scope-reader` agent, one fresh instance per read unit) reads one
  unit and records, as stage 4 and the pass brief define. It ends when it has reported.

Handoff is by file and record, never by inlined text. A dispatch at any level carries only
pointers: the project id, the round or unit id, the run folder path, and the page references.
The reader opens its pass brief, its pass knowledge and the context packet from the run folder, all
by the paths it is handed; the runner opens the read plan for its own pass and appends the ledger
without reading it whole. Nothing from those files is pasted into a dispatch, because whatever is
pasted stays in the dispatcher's context for the rest of the run.

Reports travel upward in a fixed short shape, counts and named anomalies only (the shapes are
given with the brief templates below). A runner's summary is what the lead reads when that pass
reports, verified against the record with the lead's own count queries and written down as one
`pass:` line, never relayed as-is and never held past that line.

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
in every convention-line record (`trade-convention:<trade>@<version>`). Each pass's runner cuts the
trade files relevant to its content families into one pass knowledge file beside its brief,
verbatim, and the reader reads that. Where the knowledge is silent, the reader creates at best
judgment and raises a Question (non-negotiable 7); the Question is a suggested amendment to that
trade file, surfaced in the close-out report.

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
   Where the run folder predates the current shape, no `definitions/` directory, or the context
   packet still carries definition entries instead of the kinds list, dispatch one boundary runner
   for the completed round before dispatching the next one: pointers only, `boundary` in place of
   the pass id, so the packet and the definitions files come up to the current shape. Append its
   lines to the ledger, then continue.
3. **Drawings are recognized.** `list_drawing_deliveries(projectId)`: no deliveries → stop
   plainly, hand off to `drawing-upload`. Spot-check recognition actually recorded:
   `search(projectId, predicate: "appearsOnPage", limit: 1)`: zero rows → hand off to
   `drawing-upload`. On a set that just landed, check `set_text_status(projectId)` too, because
   `search_set_text` is the fast way to find where a mark, keynote, tag, or spec phrase appears
   across the set (during planning, cross-checks, and the completeness audit), and a page nobody
   has read yet cannot be found that way.
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
   knowledge-blind. Then probe the seat for a Python interpreter, `python3 --version` falling back
   to `python --version`, since the pass knowledge every reader loads is cut by a script the runner
   shells out to. Neither name present is not a stop: the run goes ahead with readers carrying whole
   trade files, the runner writes a `note ... deviation ...` line saying the cut did not run, and
   you say so plainly at the first check-in. No interpreter has a second consequence, in stage 3:
   the read plan cannot be script-written either. You group from the `disciplineCounts` your
   `limit: 0` call already gives you, without the cross-tab and the sheet number digest, and the
   agent that fetched the grid expands your pass assignment file into `read-plan.md` itself and
   returns one line. That deviation is noted the same way, and you still never hold a sheet row.
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

1. **Decide whether orientation needs to run.** `search(projectId, predicate: "structuralSystem",
   limit: 1)` and siblings: empty means the project has no orientation facts yet. Also run
   orientation when the project has spec sections (`inDivision` entries present) but no packages on
   it yet (`solicitation_list_packages(projectId)` empty): orientation owns the baseline split, and
   a spec book with no packages means it hasn't drafted one yet.
2. **Orientation runs one level down.** Where step 1 finds orientation needs to run, dispatch one
   fresh general agent with the orientation dispatch below, the way a pass is dispatched to a
   runner: pointers only, no seed facts, no inventory rows, no spec-section text. It runs the
   `learn-project` skill exactly as written (its own reconciliation-gate read and its own packet are
   unchanged), additionally writes the reconciliation report it read to disk, and returns one
   fixed-shape line. Read back only that line: sheets seen, index findings, spec sections, packages
   drafted, questions raised, the packet path, and the reconciliation report path. Never open the
   packet or the reconciliation report yourself, and never relay the dispatched agent's own
   user-facing report text.
<!-- user-facing -->
   Tell the user what orientation found, in a few plain sentences, in your own words off that line:
   roughly what was learned, how many questions it raised for their judgment, the package split it
   drafted, and where the packet landed. Say it as what happened, not as a question.
<!-- /user-facing -->
   Where step 1 finds orientation already exists, skip the dispatch: read its entries fresh instead,
   and call `reconcile_set(projectId)` report-only yourself (never pass `record`, never pass a
   `deliveryId`: the bare call is the orientation check), checking `.ran` flags before citing any
   drift number, a check that did not run is named as not-run, never folded in as "found nothing".
3. **Compile the context packet** (`context-packet.md`): identity and seed facts; systems; scope
   areas; set shape (disciplines, deliveries, spec-TOC status); hazards; the open anomalies a
   reader must know (the reconciliation gate's genuine document inconsistencies: read directly when
   step 2 took the skip path, or the count plus the reconciliation report's path for a reader to
   open on demand when step 2 dispatched orientation); and the kinds list (empty before the first
   round; recompiled after every round from `list_definition_kinds`, one line per kind giving its
   name, plain label, count, and the sheet it is defined on, no definition entries). The packet is
   the orientation every reader loads whole, bounded regardless of how many definitions exist; the
   definitions themselves live one file per kind under `definitions/`, written by the boundary
   runner from the same recompile. The packet is a projection: regenerate whole, never patch, never
   record it.

## 3. The read plan, user-approved

Group the set into passes and sequence them by reference dependency. A pass is a set of sheets read
together because they explain each other.

You never read a sheet row. The grid is fetched to disk by a fresh agent, a script turns it into
counts and, later, into this plan's unit lines, and what you read is the counts and the script's
bounds lines.

1. **Take the set's shape, and nothing else.** `set_grid(projectId, limit: 0)`. That is a
   summary-only call: metadata and `disciplineCounts`, zero rows. Read `count` and the discipline
   distribution off it. This is the only `set_grid` call you make in this run, at any set size.
   Never call it for rows, never page it, and never fall back to sampled `search` reads for the
   inventory: whatever you pull that way stays in your context for the rest of the run.
2. **Send one agent for the grid.** Dispatch a fresh general agent, whose whole job is this and
   which then ends, with the fetch below. It pages the grid, puts it on disk under
   `<run folder>/grid/`, and returns one line. Read that line and nothing else.

   ```text
   Fetch the sheet grid for project <projectId> to disk. This is your whole job. Do nothing else,
   and end when it is done.

   1. Call set_grid(projectId: "<projectId>", limit: 500, offset: 0), then again at offset 500,
      1000, and so on, until the rows you have seen cover the response's own `count`.
   2. Where a call's result came back as a path to a file on disk, copy that file into
      `<run folder>/grid/` with the Bash tool, named `page-000.json`, `page-001.json`, and so on
      in call order. Copy it. Never retype it: a model retyping a grounded read is an unrecorded
      rewrite of it.
   3. Where a call's result came back inline instead, write the whole response object to the same
      place yourself, as JSON, and say so in your returned line.
   4. Return exactly one line: pages fetched, rows on disk, bytes, and copied or transcribed for
      each page. No account of what the sheets are, no sheet numbers, no titles.
   ```

3. **Turn it into counts.** Run the inventory mode of the plugin's plan script, with the `count`
   you read in step 1 as `--expect-count`. Run it with the Bash tool, single quoted. Pass the
   plugin directory as the path you resolved at precondition 5 to read the manifest for the
   version: `${CLAUDE_PLUGIN_ROOT}` is interpolated in this skill but is not set inside a shell
   call, so the script is handed the directory itself and never the variable. Use `python3`, or
   `python` on a seat that has only that name.

   ```sh
   python3 '<plugin root>/scripts/plan_inventory.py' inventory \
     --grid '<run folder>/grid' --expect-count <count> --out-dir '<run folder>'
   ```

   It writes `inventory.md` and `inventory.json` into the run folder. A refusal here means the grid
   on disk is not the whole set: send the fetch again rather than planning off a partial grid. Read
   only its bounds line, then read from `inventory.md` only the count tables and the sheet number
   digest at its tail. Never the sheet lines above them.
4. **Group, sequence, and split, in your own words.** Working from the count tables and the digest,
   apply the six rules below and write `pass-assignment.json`: the rounds, their passes, each
   pass's trade files, how each pass selects its sheets, by discipline (optionally narrowed by
   sheet type), by sheet number pattern, or by an explicit list, and, where rule 5's multi-page
   instrument exception applies, that pass's `units` groups. Name the exclusions with their
   reasons. This file is where your judgment lives, and it carries no sheet titles and no page
   numbers. Its shape:

   ```json
   {
     "project": "...", "setCount": 209,
     "rounds": [
       { "n": 1, "name": "definitions", "note": "no content overlap between these passes",
         "passes": [
           { "id": "A1", "name": "architectural legends and schedules",
             "trades": ["dfh", "glazing", "casework"],
             "select": { "patterns": ["A-0.*"] },
             "units": [ ["A-0.03", "A-0.04"] ] },
           { "id": "S1", "name": "structural notes and schedules",
             "trades": ["concrete", "misc-metals"],
             "select": { "discipline": "S", "sheetTypes": ["legend", "schedule"] } }
         ] }
     ],
     "excluded": [ { "patterns": ["L-*"], "reason": "landscape set, not scoped" } ]
   }
   ```

5. **Expand it.** Run the expand mode of the same script:

   ```sh
   python3 '<plugin root>/scripts/plan_inventory.py' expand \
     --inventory '<run folder>/inventory.json' \
     --assignment '<run folder>/pass-assignment.json' \
     --out '<run folder>/read-plan.md'
   ```

   Read back only its bounds line: units, passes, legs, excluded, unassigned. A refusal is a
   one-line reason and a fix to your assignment file, never a reason to write the plan by hand.
   Never open `read-plan.md` yourself; the runners open their own pass.

Step 4 applies these six rules.

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
   a kitchens pass carries appliances, casework, countertops, tiling, millwork, and so on. A pass
   carries at most ten trade files; a pass whose content families reach further than that is split
   at plan time, the same way a pass longer than twelve read units is.
4. **Group the passes into rounds**: a round is a set of passes that can run together. Passes that
   plausibly see the same scope (kitchens and unit plans, say) go in different rounds or run one
   after the other: two passes running at once on the same work create it twice. Passes with no
   content overlap may run together inside a round.
5. **Divide each pass into read units.** Within a pass, the sheets split into read units. A read
   unit is one sheet. The exception is a multi-page instrument that cannot be understood in parts
   (a schedule continued across pages, a legend split over sheets), which stays one unit, at most
   four pages; beyond that it splits at the page break, and the later unit resolves what the
   earlier one recorded from the record. Write that exception into the pass's assignment as a
   `units` group: an explicit list of the sheet numbers, in reading order, at most four, all
   selected by that same pass. The script expands a group into one unit carrying every sheet's page
   reference; a sheet the pass selects but no group names still stays its own one-sheet unit.
   Sheets that reference each other but are not contiguous (a plan and the enlarged sheet its
   keynotes point at) are separate units; the later one resolves what the earlier recorded from the
   record. A row that continues across the split belongs to the unit that reads its first page,
   which reads the continuation page for that row only. List the units in each pass, in reading
   order.
6. **Split a long pass into legs.** A pass longer than about twelve read units is divided here, at
   plan time, into legs of at most twelve units each, lettered in reading order (`S2a`, `S2b`,
   `S2c`). A leg is what one runner supervises. The legs of a pass run one after another, and the
   later leg resolves what the earlier one recorded from the record, exactly as one unit does with
   the unit before it. Splitting costs no reading time, because the units of a pass are read one at
   a time either way. Name the legs in the read plan alongside the units each one carries.

Step 5 turns that into `read-plan.md`: the passes, their legs, and the units within each leg
(numbers plus file/page references), the trade files each pass carries, the order the rounds run in,
and what is deliberately excluded, named outright rather than left silent.
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

The reading happens one level down, one runner per pass. Per round, the lead does exactly this and
holds nothing else:

1. **Start one runner per pass.** For each pass in the round, and for each leg the read plan split a
   long pass into, dispatch a fresh `plumlayer:scope-round-runner` with the runner dispatch below:
   pointers only, no pass brief, no trade file, no read-plan text. Append that pass's dispatch line
   to the ledger before you dispatch it, never after. Passes the read plan marks as having no
   content overlap start together; passes that plausibly see the same work, and the legs of one
   pass, start one after another. What a pass leaves in the lead's context is its dispatch line and
   its summary, nothing else.
2. **The runner owns the pass.** It writes the pass brief if it is not already on disk, runs the
   pass's units in reading order (one fresh `plumlayer:scope-reader` per unit, one unit at a time),
   appends each unit's dispatch line before that unit starts, verifies every unit against the record
   with its own queries before the next unit starts, notes overlaps inside the pass, and appends the
   ledger in its fixed line shapes. The per-unit loop lives in the `scope-round-runner` agent
   definition and the reader mandates live in the `scope-reader` agent definition. Neither is
   restated here, and neither is ever trimmed.
3. **Take a pass's counts when it reports, then let its summary go.** A runner returns one
   fixed-shape summary (shape below). Before you say a number out loud, take the created count for
   each of that pass's units with your own `search(subjectPrefix: "scopeItem:<unit-id>-", limit: 1)`,
   reading `count`. That is the third boundary of non-negotiable 6, and it is count-only: never a
   row list, never the unfiltered `list_scope_items`. It reaches creates and not updates or
   Questions, because those land on subjects that already existed and `search` has no
   `sourceInstrument` filter to reach them by. Say
   the update and Question counts as the runner verified them, and the created counts as your own.
   Append one `pass:` line to the ledger carrying that pass's verified totals, and work from that
   line from then on rather than from the summary. A mismatch stops the run and gets investigated,
   never papered over.
4. **Close the round at its boundary.** When every pass of the round has reported and carries its
   `pass:` line, dispatch one more runner with `boundary` in place of the pass id. It scans the
   round's new items for the same work captured by two passes that ran alongside each other,
   recompiles the kinds list into the context packet and the per-kind definitions files for the
   next round, appends its lines, and ends. Then append `phase: round N complete` to the ledger
   with the round's verified totals.
5. **Check in with the user** (format below), written off the round's `pass:` lines in the ledger
   rather than off the summaries you received. Move to the next round only on their go-ahead.

## 5. The completeness check (standing, with a closure loop)

The definitions layer is the checklist: every defined thing must be accounted for by the scope
list. Run this after the placement rounds complete (and any time coverage is in doubt). It runs one
level down, bounded the same way a pass is:

1. **Start one runner for the enumeration and the accounting.** Same runner dispatch as stage 4,
   with `completeness-account` in place of the pass id. It enumerates the defined things per kind,
   pulls the scope list, accounts deterministically with a small local script it writes, classifies
   every leftover row (accounted, plausibly-carried, not-scope, unaccounted), clusters the
   unaccounted rows into capture gaps, writes those gaps under `completeness/` as supplemental read
   legs of at most twelve units each, and ends. The loop lives in the `scope-round-runner` agent
   definition.
2. **Run each supplemental leg in its own runner**, dispatched exactly as a pass leg is in stage 4,
   with `completeness-<leg id>` in place of the pass id, its dispatch line appended first and its
   `pass:` line appended when it reports.
3. **Re-run the accounting in a fresh runner**, the same `completeness-account` dispatch, once every
   supplemental leg has reported. Its summary carries the accounting before and after the
   supplemental reads, which is where the close-out figures come from. The validation run's first
   accounting found 269 of 564 defined things unaccounted, closed 267 with one supplemental round,
   and named 2 still open: that loop is the designed behavior, not a recovery.
4. **Read the summaries and verify what you can yourself**, the same way stage 4 step 3 does: the
   created counts for any supplemental units, by
   `search(subjectPrefix: "scopeItem:<unit-id>-", limit: 1)`, `count` only, no row list and no
   unfiltered `list_scope_items`. The accounting figures come from the runner's summary, and the
   still-open rows you check by name, reading back the ones it named.
   Report the accounting as the runner's and the created counts as your own.
5. **Name what is still open**, row by row, in the ledger and in the close-out report, then append
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
dispatcher's context for the rest of the run, so the packet, the read plan, and the brief values
are opened by the agent that needs them, from the paths it is handed: the runner opens the trade
files it cuts, and the reader opens its pass knowledge.

The mandates are not in these templates. They live in the two agent definitions the plugin ships,
`scope-round-runner` and `scope-reader`, where each dispatched instance reads them fresh. They are
never trimmed there and never restated here: a run that relaxes one reproduces a measured failure.

**Orientation dispatch** (the lead writes this, once, only when context floor step 2 finds
orientation needs to run):

```text
Project: <projectId>. Run folder: <path>.
Run the `learn-project` skill for this project, in full, exactly as it is written. When it is
done, write the reconciliation report you read in its own reconciliation step to
<run folder>/reconciliation-report.md, the findings in full. Then return your summary and end.
```

**The orientation summary** comes back in this shape, and is all the lead reads: counts and paths,
never the packet or the reconciliation report themselves.

```text
sheets seen <n>   index findings <n>   spec sections <n>   packages drafted <n>   questions <n>
packet: <path>
reconciliation report: <path>
```

**Runner dispatch** (the lead writes this, once per pass or leg, once per round boundary, and twice
for the completeness accounting):

```text
subagent_type: plumlayer:scope-round-runner
Project: <projectId>. Round: <round number>.
Pass: <pass or leg id, or "boundary", or "completeness-account", or "completeness-<leg id>">.
Run folder: <path>. Read plan: <path to read-plan.md>.
Run your pass as your definition says, then return your summary.
```

**Reader dispatch** (the runner writes this, once per read unit):

```text
subagent_type: plumlayer:scope-reader
Project: <projectId>. Round: <round number>. Pass: <pass name>. Unit: <unit id>.
Pages: <sheet number + fileId + 1-based pageInPdf, one per page>.
Run folder: <path>. Context packet: <path>. Pass brief: <path to briefs/<pass-id>.md>.
Pass knowledge: <path to briefs/<pass-id>-knowledge.md>.
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
convention lines: contradicted <n> (subject + reason, one per line, or "none")
anomalies: <one line each, with sheet and page, or "none">
grain questions: <one line each, with sheet and page, or "none">
door-owned suggestions: <one line each, or "none">
```

`created:` is the reader's own item count, not the entries under those items. `sent:` and
`landed:` count every write the reader made for the unit, across every call, not only its first
batch.

The `updated subjects:` line is what lets the runner find an update back: a create is findable by
its `scopeItem:<unit-id>-` prefix, an update lands on a subject that already existed and nothing
else in the report names it.

**The runner's summary** comes back in this shape, and is what the lead reads when a pass reports,
after taking that pass's created counts off the record itself: an entry count under each unit's
prefix, never the reader's own item count, which travels separately as `items`:

```text
round: <n>   pass: <pass or leg id>
units read: <unit ids, in reading order>
per unit: <unit id> created <n> items <n> updated <n> questions <n> verified <yes/no>
totals verified: created <n> (entry count under the unit prefixes), items <n> (reader's own item count), updated <n>, questions <n>
conflicting rows: <id + how each resolved, or "none">
overlap notes: <item name + the two units, one per line, or "none">
anomalies: <one line each, with sheet and page, or "none">
unread pages: <sheet + page + reason, one per line, or "none">
definitions kinds added: <kinds, or "none">
deviations and repairs: <one line each, or "none">
ledger: <path>, appended through <last line written>
```

A boundary runner returns this shape instead:

```text
round: <n>   pass: boundary
cross-pass overlaps: <item name + the two units, one per line, or "none">
packet: regenerated, <n> definitions across <n> kinds
definitions files: <n>
definitions kinds now: <kinds>
ledger: <path>, appended through <last line written>
```

In completeness mode the summary carries these lines as well, which are where the close-out
report's "what was enumerated, what closed" figures come from:

```text
enumerated: <n>
first pass: accounted <n>, plausibly carried <n>, not scope <n>, unaccounted <n>
after closure: accounted <n>, plausibly carried <n>, not scope <n>, unaccounted <n>
supplemental legs: <leg ids, or "none">
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
- **Manage the user's session or context**: the run is bounded by its own structure. Each pass and
  each read unit runs in a fresh agent that ends when it has reported, so nothing accumulates and
  there is nothing for the user to manage.
- **Run unattended**: check-ins are load-bearing until the user has enough cold runs
  behind them to decide otherwise, and that is their decision to make out loud, per run, never
  this skill's default.

## What this skill never runs

Do not restore or run per-trade fan-out / reconcile-by-overlap machinery as a scope path, and never
present it as current.
