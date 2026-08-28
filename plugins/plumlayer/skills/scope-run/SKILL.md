---
name: scope-run
description: >
  Read a Plumlayer project's drawing set into one grounded, cited scope list, every item on its
  trade, in three windows: the vocabulary, then one pass per trade package, then what is left.
  Trigger on "scope this set", "/scope-run". Attended: the user approves the read plan and reviews
  at every check-in. Drives the project record's read and write verbs and the citation index.
  Does not upload drawings (drawing-upload), orient from scratch or draft the baseline package
  split (learn-project), read sub proposals (bid-intake), or place takeoff measurements (takeoff).
---

# Scope run

## What this is

The production scope run: it reads the set in three windows, each of which leaves the project
record whole at its own depth, and the user reviews at every check-in. Orientation is the
`learn-project` skill, which this skill dispatches first when orientation hasn't happened yet;
orientation also drafts and creates the baseline package split off the spec table of contents, so
a package exists for every trade before the first sheet is read, and readers name trades from that
split. The shape, in the estimator's own order:

> First assemble one massive singular list of all the scope line items across the entire job; then
> sort through and decide which trade packages to create; assembling them is assigning one new meta
> variable on an entirely scoped line item.

One scope list, every row cited and carrying its trade from the moment it is written. Trade
packages are projections off it. Every mandate below exists because skipping it produced a
measured, real failure: follow all of them.

The three windows:

1. **Vocabulary.** Schedules, legends, general notes, and cover and index sheets; the spec
   sections were read at orientation. Readers record what the marks mean (the definitions), the
   scope the schedules themselves ground, and every item's trade. When the window closes, the
   record's citation index runs: a mechanical pass that locates every defined code and every
   item's tag on every page of the set and cites those pages onto the items and definitions. After
   this window every trade's page is usable.
2. **Trades.** One pass per trade package, schedule or no schedule: the sheets that trade's
   knowledge says to read (the roofer reads the roof plan, wall sections and details; the site
   contractor reads civil; the painter reads the finish schedule and elevations), the sheets the
   index found that trade's codes on, and the schedules that resolve to it, read for that trade
   with that trade's knowledge alone. This is where the scope is, and it is the bulk of the run:
   quantities where the sheets carry them, the splits the vocabulary read was too coarse for, the
   Questions that clear the bar for an RFI. A trade's page is finished when its pass is.
3. **The leftover.** A printed list, not an open question: the pages no trade pass named, and the
   tags the index could match to no code. Read by discipline, and whatever is still open at the
   end is reported by name.

A run can stop at the end of any window, and inside window 2 at any package boundary, and resume
later with nothing lost.

**This run is attended.** The user approves the read plan before any reading and reviews at every
check-in. Never read past a check-in without the user's go-ahead. The package split is not a gate:
this run reads the baseline packages orientation created, amends them as the scope list surfaces
what the spec TOC could not see, shows what it did, and stops; they stay editable, and a correction
is a change on the site or a tool call.

Doctrine binds every step: **agents read and judge; deterministic tooling grounds; nothing enters
untraced.** Everything a reader records is its own reading, cited, carrying its authorship trail;
it becomes working truth the moment it lands; anything a person changes wins. The project record
is what every agent in the run reads from and writes to: definitions, sheet readings, orientation
facts, open Questions. No agent keeps its own copy of what the record already holds.

## The non-negotiables

Every stage below honors these. They are restated where they apply, but read them first: a run
that relaxes any one of them reproduces a measured, named failure.

1. **Cite everything, in the uniform shape.** Every drawing-grounded record carries evidence naming
   the sheet AND a resolvable 1-based page: `evidence.page` or `evidence.pageInPdf` as a positive
   integer for the page actually read. A sheet named with no page cannot be render-verified and the
   record door refuses it. Never fabricate a page or sheet to satisfy the door. A citation the
   index wrote is the index's own, in the trail as a text match; a reader cites what the index did
   not already cite and never re-cites a page the item already carries.
2. **Create / update / question against the live list.** Every reader holds the current scope list
   for its trade or content families as match-or-create context: for each thing seen, create a new
   item, update an existing one (a new citation, a note, a resolved cross-reference), or raise a
   Question, with a title and a citation. A Question is what clears the bar in the reader's
   mandate 1, the first inkling of an RFI, never something a sub could price as drawn. Never a
   parallel list, never a re-create of what exists, never silent skipping of what's already
   listed. Before every create, one `search` on the item's distinguishing words across the whole
   project, whatever trade the match is on: work another trade's pass already captured is updated,
   never created again. Before raising a Question, read the open Questions on the item's trade
   (`list_questions`, filtered); where an open one already covers the same ask, reply to it
   instead of asking it a second time. A Question is about the project, never about a Plumlayer
   failure; a read or write that fails is reported and handled in the run's own failure path, not
   raised as a Question. Question text is plain estimator words, per docs/plugin-text-style.md.
3. **The convention-line record mandate.** A trade's convention lines are a property of the trade,
   not of the sheet or the unit reading it: the pass runner records them once, at pass start,
   after a deterministic check that they are not already on the record
   (`search(subjectPrefix: "scopeItem:conv-092116-", limit: 1)`, reading `count`), never per
   reader and never per unit. Convention lines never masquerade as sheet-cited reads: their
   `sourceInstrument` is `trade-convention:092116@<knowledge-version>` (the pinned version from
   the knowledge manifest), their evidence quotes the trade file's line and carries the marker
   `basis: "trade-convention"`, they carry no sheet citation, and their trade is the trade whose
   file they came from. The trade is that trade's catalog code everywhere here and never the trade
   file's own name, in two forms: `belongsToTrade` carries the catalog id verbatim, exactly as the
   packages print it (`09 21 16`), and the subject, the prefix above and the instrument carry it
   with the spaces out (`092116`), because an identifier carries no spaces and the trade value is
   copied verbatim. A reader never creates or recreates one; where a sheet corroborates one,
   that citation updates the same item and the convention basis stays visible in the trail, and
   where a sheet contradicts one for this project, the reader raises a Question naming it rather
   than deciding on its own.
4. **Store-resolution is mandatory.** A mark, tag, or code is resolved by querying the project
   record (`search`, `list_definitions`), never from memory, never inherited from another sheet's
   read, never assumed from a similar-looking mark. Where a code appears in the set is a question
   for the corpus (`search_set_text`), never for memory either.
5. **Capture everything; name the trade as you write.** Capture is complete: everything seen goes
   into the one shared list, whatever trade it belongs to, even in a pass reading for one trade.
   The reader that writes the row sets its trade right then, from the packages orientation
   created, and moves on; a wrong trade is moved later by a person or a later read, never held
   back. Where the reader cannot tell which of two or more trades owns the work, it names its best
   single trade as the home and tags every other candidate, and keeps moving. The record door
   refuses a new scope item with no trade and no candidate, and refuses a trade the catalog does
   not carry, on `belongsToTrade` and inside `packageRole:<trade>` alike. `record_batch` is atomic
   and order free, so the trade rides in the same batch as the name; `record` carries one entry, so
   there the trade entry is written first. Whether an item is an exclusion, a general requirement,
   or an alternate is still a person's call at the package surface.
6. **Every write is count-verified, at two boundaries.** After every batch write, the reader reads
   the record back and confirms the count that landed equals the count sent, and checks any
   conflicting rows individually, before it ends. The pass runner separately re-verifies the same
   unit with one `verify_unit` call before the next unit of that pass starts: the entry count and
   distinct subject count under the unit's prefix, and for each of the unit's sheets the subjects
   whose citations name it, which is how an update and a new citation on a pre-existing subject
   are found back. A reader's report that its batches landed is verified at both its own boundary
   and the runner's; neither replaces the other. The lead adds a third, count-only check at the
   check-in: `search(subjectPrefix: "scopeItem:<unit-id>-", limit: 1)`, reading `count`, per unit,
   never a row list. Updates and Questions the lead reports as runner-verified rather than
   asserting a check it did not run. The lead never calls the unfiltered `list_scope_items` during
   the run: that verb walks the whole scope list, and pulling it is how the lead's context stops
   being cheap. Counts only, `limit: 0`, is the one call the lead makes on it.
7. **The grain bracket.** A scope item is the unit a subcontractor would include / exclude / price
   as one thing (the floor: split by type / significant distinction, never by instance) and at most
   one row on a trade's scope sheet (the ceiling: package headers are never the reader's). One
   item per sheet is a ceiling violation; one item per instance is a floor violation. Where the
   pass knowledge's grain rules are silent, create at best judgment AND raise a Question naming the
   grain question: recall never drops to grain uncertainty.
8. **Vocabulary, then the trades, then the leftover.** A trade pass reads only after the
   vocabulary is recorded and indexed; the leftover reads only after the trades. Two trades with
   a known seam between them (drywall and painting, plumbing and fire protection, concrete and
   waterproofing) run one after the other, never together. The read plan encodes this order and
   the user approves it.
9. **The vocabulary window covers the scope the schedules themselves ground.** The passes reading
   legends and schedules record what a mark means, and they also own the scope items the
   schedules ground, on their trades.
10. **Run, or stop and report; never create a consent step.** The user's decisions in this skill
    are the read plan and each check-in. Everything else the run does is its own work, recorded
    with its trail and editable afterward. Never stop to collect approval for a course you have
    already chosen, and never offer a recommended yes: if something is genuinely wrong, stop, say
    what is wrong, and hand it over; if nothing is wrong, proceed and say what you did.
11. **The index runs, and what it left open is read or named.** The citation index is a standing
    step between the first two windows and again after the third, never optional; the leftover
    window reads what it left open, and whatever is still open at the end is reported by name:
    never assumed closed, never zeroed by hope.
12. **A remark about spend never trims a mandate.** Every verification in this file stands whatever
    the user says about what the run is costing them. If they raise it, say plainly what is running
    and that the next natural stopping point is the end of the current package or window, and stop
    there if they ask; never answer it by doing less of the work you then report on. A
    verification that did not run is named as not run, by name, in the ledger and out loud, in the
    same breath as the numbers it would have covered. Never offer to trim, and never put the
    question of whether to continue back to them in terms of what it costs.

Also: door-owned records (Question resolutions, questions-as-answers) are created only at their own
doors; a reader that thinks a Question should be closed says so in its report and a person acts at
the door. That door is `close_question`, and you call it only when the user settles the answer in
the session: their reason goes in `note` in their own words, and a Question you merely think looks
answered stays open. `reopen_question` puts one back when they tell you it was closed in error.
Removing a scope item is different: `retire_scope_item` is the one door for that act, for a person
and an agent alike. Use it only for a row the user asked removed, put the user's ask in `basis` in
their words, one item per call; a row you merely suspect is wrong goes in the report.

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
- **trade** (required): the catalog trade id of the package that owns the work, read off the
  packages orientation created (`solicitation_list_packages`), recorded as `belongsToTrade`. It is
  the catalog id copied verbatim, exactly as the package prints it, spaces and all (`09 21 16`).
  Never a trade file's name and never a word for the trade, so `drywall` is refused, and never a
  respelling of the code either, so `09-21-16` and `092116` are refused too, with a hint naming the
  exact id. Browse the codes with `directory_list_trades` where a package's own `tradeCode` does
  not answer it. Where the work straddles packages, the best single
  home goes here and each other candidate gets a `packageRole:<trade>` record with role `candidate`
  and a note in the shape "confirm trade responsibility: could be `<home>` or `<this trade>`"
  (internal only, never bidder-facing), written in the same batch. The `<trade>` in that predicate
  is the same catalog code, and the door reads it there too.
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

A row's text never carries another item's subject id or a hand-written SUPERSEDED or date tag,
per docs/plugin-text-style.md. Splitting one item into two is `retire_scope_item` naming why, plus
a fresh CREATE for each half, never a tag written into the description.

Recorded text is what the bidder reads: plain sentences, no em dashes, no bolding, never a
sheet-by-sheet narration. The door refuses text over its bound (`name` 80 characters, `category`
60, `description` 400, `notesExternal` and `notesInternal` 300 each); a row shaped by these rules
never comes near them. A verbose row is a defect, not diligence.

## The Question bar

A Question is what a person will answer, and in a bid it is what becomes an RFI. It clears the bar
when a bidder could not price the work without the answer, or when two sources disagree about the
work: a schedule row with no matching plan tag, a detail called where none is drawn, a spec
section and a sheet naming different products for one assembly, a dimension the sheets contradict.
It does not clear the bar when the answer is on another sheet the reader has not opened yet (the
corpus answers that: `search_set_text` first), when it is a grain question (that is a Question
naming the grain, raised for the trade file, per non-negotiable 7), or when it is a note to the
estimator (that is `notesInternal`). Every Question names its trade, the same way an item does, so
it sits on that trade's page; a Question about the set as a whole names no trade and sits on the
project.

## What the record holds, and what stays on disk

Everything an agent in this run needs to know about the project is on the project record, and is
read from there by the agent that needs it, when it needs it:

- the orientation facts (identity, systems, scope areas, hazards): `get_project` and `search` on
  their predicates;
- the packages and their catalog trades: `solicitation_list_packages`;
- the definitions: `list_definition_kinds` for the kinds, `list_definitions(kind)` for the codes
  under one, `search(subject: "<kind>:<code>")` for one code's full definition;
- what a sheet is, which legend its tags resolve to, and what it references: the sheet's own
  reading, written once by the first reader that reads it (`sheet:<sheet number>`);
- where a code or phrase appears in the set: `search_set_text`, over the corpus every page was
  read into at upload;
- the open Questions on a trade: `list_questions`, filtered;
- the sheet inventory: `set_grid`, taken once to disk for the plan script and never held.

No packet, no definitions files, no per-run copy of any of it: a reader that wants to know what a
door type is asks the record, and a second reader on the same sheet finds the first one's reading
there.

The run folder, `~/.plumlayer/runs/<project-slug>/` (slug from the project name, lowercase, spaces
to hyphens; fall back to the projectId), holds only the run's own bookkeeping. Never committed to
any repo, never uploaded to the project except record files, never recorded as project entries:

- `ledger.md`: the run ledger, appended as the run proceeds, one line per entry in the fixed shapes
  the `scope-round-runner` definition gives, plus the lead's own `pass:` and `phase:` lines.
  Nothing else goes in the ledger: no headings, no bullets, no paragraphs, no re-telling of a
  report. It is appended, never rewritten and never reformatted, and never read whole by anyone:
  the lead reads its `phase:` lines with a local command (a filter on the line prefix), the
  close-out report is written off its `pass:` and `phase:` lines the same way, and a runner reads
  none of it. Audience: agent, and it feeds the close-out report, so whatever crosses into that
  report becomes user-facing at the crossing and is translated there.

  The lead's own two line shapes, which the runner never writes:

  ```text
  pass: <window> <pass id> units <n> created <n> updated <n> questions <n> replied <n> lead-verified <yes|no>
  phase: <boundary name>
  ```

- `grid/`, `inventory.md`, `inventory.json`: the sheet grid as the fetch agent put it on disk, and
  the plan script's counts off it. The lead reads the count tables and the sheet number digest,
  never a sheet line. Audience: machine, and the tables for the lead.
- `plan/`: the plan script's other inputs, each a byte-for-byte copy of a verb's response paged to
  disk by a fresh agent, never retyped and never read by a model: `kinds/` (one file per response,
  `list_definition_kinds` for the kinds and `list_definitions` for each kind's codes),
  `packages.json` (`solicitation_list_packages`), and `index/` (one file per response,
  `index_citations_leftover`, what the index left open, one kind at a time). Audience: machine.
- `read-plan.md`: the read plan, one per window, written by the plan script, never by hand: the
  passes, the units within each with their sheets, files and pages, the trade each pass reads for,
  and what is deliberately excluded. Audience: agent; a runner opens its own pass only.
- `briefs/`: one small file per pass, written by that pass's runner, carrying the pass's filled
  slot values (what the pass reads for, its trade or content families, the knowledge version, the
  subject prefix scheme), and beside it `<pass-id>-knowledge.md`, the pass knowledge: the carried
  trade's grain sections cut verbatim from the shipped trade files by the plugin's script. The
  knowledge is plugin-shipped, not project knowledge, which is why it is the one thing a reader
  reads from disk. The mandates are never in it. Audience: agent.
- `reports/`: one file per read unit and per pass, the report in its fixed shape, written by the
  reader or runner before it returns, so a dispatch that returns without the report in hand loses
  nothing. Audience: agent.
- `names/`: one file per pass, the new item names each unit created, one per line, matched
  against themselves and each other with a local command for overlaps. Audience: machine.
- `records/`: JSONL files for large batch writes (these do get uploaded, as the write
  mechanism). Audience: machine.

## Windows, and who holds what

The run is one attended conversation, and nothing in it accumulates. The project record is the
run's memory; the run folder is its bookkeeping; no level of the run holds between its units
anything a later unit needs. The user never manages context: the only decisions they make are
the read plan and each check-in, and no prompt ever mentions sessions, compaction, or usage.

The run executes at three levels. Each level is a separate agent context, bounded by construction:

- **The lead** is this skill, running in the user's session. It does the cheap work only:
  preconditions, orientation, the read plan, starting the index and waiting on its status, the
  check-ins, amending, close out. For each pass it starts one runner and receives one fixed-shape
  summary; what it keeps per pass is the dispatch line and, once it has taken its own counts, one
  `pass:` line in the ledger. It never holds a pass brief, a trade file, a reader's report, the
  sheet grid, the index report, or a page of the set.
- **The pass runner** (the plugin's `scope-round-runner` agent, one fresh instance per pass) owns
  one pass: it writes the pass brief, cuts the pass knowledge, records the trade's convention
  lines, runs the pass's read units exactly as the window's stage defines them, verifies every
  unit with one `verify_unit` call, notes overlaps inside the pass, appends the ledger in its
  fixed line shapes, returns its summary, and ends. Its context is bounded to one pass of at most
  twelve units, and it never grows with the size of the window. One further instance closes each
  window at its boundary: the cross-pass overlap scan, the declaration of any kind a reader named
  and did not declare, and the copies of the record the next window's plan script reads.
- **The reader** (the plugin's `scope-reader` agent, one fresh instance per read unit) reads one
  sheet, for the vocabulary, for one trade, or for the leftover, over the corpus, and records, as
  the window's stage and the pass brief define. It writes its report to `reports/` and ends.

Handoff is by file and record, never by inlined text. A dispatch at any level carries only
pointers: the project id, the window, the pass or unit id, the run folder path, and the page
references. The reader opens its pass brief and knowledge file from the run folder by the paths it
is handed and everything else from the record; the runner opens the read plan for its own pass and
appends the ledger without reading it. Nothing from those files is pasted into a dispatch, because
whatever is pasted stays in the dispatcher's context for the rest of the run.

A dispatch is one Agent tool call and the call is the wait. On a seat where the call returns at
once with an agent id instead of the report, the report arrives later as its own message: wait for
it, making no other call in between, and never dispatch a second agent to wait for the first, and
never a placeholder agent to fill a turn. Where a reader or runner has ended and its report did not
arrive in the message, its report file under `reports/` is the report, written before it returned;
open that file rather than re-running the unit. A unit whose report file is also absent is re-run
on its own unit, against the live list, so nothing is created twice.

Reports travel upward in a fixed short shape, counts and named anomalies only (the shapes are
given with the dispatch templates below). A runner's summary is what the lead reads when that pass
reports, verified against the record with the lead's own count queries and written down as one
`pass:` line, never relayed as-is and never held past that line.

Phase boundaries are the ledger's `phase:` lines, one appended by the lead at each of: plan
approved; window 1 complete; index built; window 2 complete; window 3 complete; packages amended;
closed out. Inside window 2 the `pass:` lines are the boundaries: one per package. On every start
this skill reads the ledger's `phase:` and `pass:` lines first, with a local filter, never the
file: a run in flight resumes at the phase after the last line, or at the next package of window 2
not yet carrying a `pass:` line, with the read plan read off disk. A missing run folder for a
project that already carries scope items is named plainly and the run re-plans against the record;
the live-list mandate (non-negotiable 2) keeps a re-read from creating what is already there.
Resumption is how a run continues after a stop at a boundary, and crash and multi-day hygiene. It
is never offered to the user as a way to manage cost, and the check-in never suggests it.

## The trade knowledge base

Ships with this plugin at `${CLAUDE_PLUGIN_ROOT}/trade-knowledge/`: one file per trade
(`painting.md`, `drywall.md`, …), mined from a real subcontractor-quote corpus, carrying what the
drawings will not say: how the trade bids, scope grain rules, exclusions and counterparties,
furnish/install seams, convention work no sheet states. Beside them, `trade-sheets.json` maps
each catalog trade to its knowledge file and to the sheet families that trade reads, and names
the seams between trades; the plan script reads it, and no model does.
`MANIFEST.md` there records the knowledge version and source snapshot: read it at run start,
record the version in the ledger, and cite it in every convention-line record
(`trade-convention:092116@<version>`, the trade's catalog code with the spaces out). Each pass's
runner cuts the trade file its pass reads for
(in window 1, the files its content families touch, at most ten) into one knowledge file beside
its brief, verbatim, and the reader reads that. Where the knowledge is silent, the reader creates
at best judgment and raises a Question (non-negotiable 7); the Question is a suggested amendment to
that trade file, surfaced in the close-out report.

## 1. Preconditions

1. **Project exists and is the user's intent.** `list_projects`, confirm which project with the
   user, get its `projectId`. No project → hand off to `project-setup`.
2. **Resume, if a run is already in flight.** With the `projectId` in hand and before anything else,
   read the `phase:` and `pass:` lines of `ledger.md` from the run folder with a local filter on
   the line prefix; never open the file whole. A `phase:` line means a run is in flight: resume at
   the phase after the last one, or at the next window 2 package with no `pass:` line, reading
   `read-plan.md` off disk rather than re-planning or re-reading what is already recorded. A
   project that already carries scope items but has no run folder is named plainly and re-planned
   against the record; the live-list mandate (non-negotiable 2) is what keeps a re-read from
   creating what is already there. Where the last `phase:` line is `window 1 complete` with no
   `index built` after it, the index step (stage 5) runs first. A run is never resumed past a
   boundary that did not run. Never offer resumption to the user as a way to manage anything, and
   never raise it at a check-in.
3. **Drawings are recognized, and the corpus exists.** `list_drawing_deliveries(projectId)`: no
   deliveries → stop plainly, hand off to `drawing-upload`. Spot-check recognition actually
   recorded: `search(projectId, predicate: "appearsOnPage", limit: 1)`: zero rows → hand off to
   `drawing-upload`. On a set that just landed, check `set_text_status(projectId)` first: a page
   nobody has read yet cannot be found by `search_set_text`, so a fresh delivery still being read
   would otherwise look like a missing corpus. Once the status shows the set read, confirm the
   corpus itself with `search_set_text(projectId, query: "<the project's first sheet number off
   set_grid's limit: 0 summary>", limit: 1)`: a corpus that answers nothing for a sheet number the
   set carries has not been built, and the run stops and hands the delivery back to
   `drawing-upload` for its text read rather than reading page by page without it.
4. **Spec book, if it exists.** `search(projectId, predicate: "inDivision", limit: 1)`: spec
   sections present means the spec-TOC leg has run. Absent: ask the user whether a project manual /
   spec book exists. If one does, run it through `drawing-upload`'s spec-book leg first (upload +
   `extract_spec_toc`): the package split anchors on the spec table of contents and is
   substantially weaker without it. If the project genuinely has no spec book, proceed and name
   that in the ledger and the close-out report: orientation created no baseline packages for this
   project (no spec sections, no anchor), and stage 8 below derives the whole split from the
   finished scope list instead.
5. **Trade knowledge present.** Read `${CLAUDE_PLUGIN_ROOT}/trade-knowledge/MANIFEST.md`; record
   the version in the ledger. Missing → stop and report a broken plugin install rather than running
   knowledge-blind. Then probe the seat for a Python interpreter, `python3 --version` falling back
   to `python --version`: the pass knowledge every reader loads and the read plan of every window
   are both written by scripts. Neither name present is a stop for this run: say so plainly and
   hand over, since a plan written by hand has been the measured failure every time.
6. **The user is present.**
<!-- user-facing -->
Tell them what the run will do: you read the set in three windows, the schedules and legends
   first, then one trade at a time across the whole set, then whatever is left, and you stop for
   a check-in after the first window and every few trades after that; after the first window every
   trade's page already has its items. They can stop or change course at any check-in. Give a
   rough sense of how long this set will take from its size, and confirm they are staying for the
   check-ins.
<!-- /user-facing -->
   Where it can, the run starts from a clean conversation, but it never raises sessions,
   compaction, context, or usage with the user, at run start or at any point after it.

## 2. Orientation

Run these in order; each is read-or-run, never re-created (net-new facts only, everywhere).

1. **Decide whether orientation needs to run.** `search(projectId, predicate: "structuralSystem",
   limit: 1)` and siblings: empty means the project has no orientation facts yet. Also run
   orientation when the project has spec sections (`inDivision` entries present) but no packages on
   it yet (`solicitation_list_packages(projectId)` empty): orientation owns the baseline split, and
   a spec book with no packages means it hasn't drafted one yet. Readers name every item's trade
   off that split, so a run never reads before it exists.
2. **Orientation runs one level down.** Where step 1 finds orientation needs to run, dispatch one
   fresh general agent with the orientation dispatch below, the way a pass is dispatched to a
   runner: pointers only, no seed facts, no inventory rows, no spec-section text. It runs the
   `learn-project` skill exactly as written and returns one fixed-shape line. Read back only that
   line: sheets seen, index findings, spec sections, packages drafted, questions raised. Never
   relay the dispatched agent's own user-facing report text. What orientation learned is on the
   record, which is where every reader reads it.
<!-- user-facing -->
   Tell the user what orientation found, in a few plain sentences, in your own words off that line:
   roughly what was learned, how many questions it raised for their judgment, and the package
   split it drafted. Say it as what happened, not as a question.
<!-- /user-facing -->
   Where step 1 finds orientation already exists, skip the dispatch and call
   `reconcile_set(projectId)` report-only yourself (never pass `record`, never pass a
   `deliveryId`: the bare call is the orientation check), checking `.ran` flags before citing any
   drift number, a check that did not run is named as not-run, never folded in as "found nothing".
3. **The packages are catalog-resolved.** `solicitation_list_packages(projectId)`: every package
   carries a catalog `tradeCode`. A package with none is resolved now (`directory_list_trades`,
   exact `code` first then `query` by name or alias, the id recorded verbatim) or named "no catalog
   trade" in the ledger; readers may only choose trades the catalog knows, since the door checks
   them. Then send one fresh agent to copy that response to `<run folder>/plan/packages.json`,
   byte for byte, returning one line; the plan script reads it from there, and you never hold it.

## 3. The read plan, user-approved

The plan for window 1 is written here and approved once; the plans for windows 2 and 3 are written
by the same script at each boundary from what the record then holds, and the check-in before each
window is where the user sees them. A pass is a set of read units read together for one purpose;
a read unit is one sheet.

You never read a sheet row. The grid is fetched to disk by a fresh agent, a script turns it into
counts and into the plan's unit lines, and what you read is the counts and the script's bounds
lines.

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
4. **Write the window 1 plan.** Run the plan mode of the same script for window 1. It selects the
   vocabulary sheets by sheet type (schedule, legend, notes, cover and index), groups them into
   passes by discipline, names the trade files each pass carries off the trade map (at most ten
   per pass), splits a pass over twelve
   units at the twelve, and names what it left out and why. Families you want read anyway, or
   left out, go in as `--include` and `--exclude` patterns with a reason each; that is where your
   judgment lives, and it carries no sheet titles and no page numbers.

   ```sh
   python3 '<plugin root>/scripts/plan_inventory.py' plan --window 1 \
     --inventory '<run folder>/inventory.json' \
     --packages '<run folder>/plan/packages.json' \
     --trade-knowledge '<plugin root>/trade-knowledge' \
     --out '<run folder>/read-plan.md'
   ```

   Read back only its bounds line: units, passes, excluded, unassigned. A refusal is a one-line
   reason and a fix to your arguments, never a reason to write the plan by hand. Never open
   `read-plan.md` yourself; the runners open their own pass.

<!-- user-facing -->
Before any reading runs, tell the user, in a few plain sentences, not a table:

- The order: schedules and legends first, by discipline, then one trade at a time across the
  set, then what is left, in one sentence. No reasons; they know why schedules come before plans.
- What is deliberately left out, by sheet family or number. Say it plainly: anything here will not
  be scoped.
- When the first check-in will be, roughly.
- The ask: what is worth catching is a family left out that carries scope, or a schedule family
  the plan did not recognize as one. Then: go, or cut, add, or reorder.

For example: "Architectural schedules and legends first, then structural notes, then the
mechanical, electrical and plumbing schedules. I'm leaving out the ADA mounting-height sheets and
the landscape set. First check-in in about twenty minutes. Go, or change anything."

Never show passes as a table, counts of dispatches, bundle codes, lanes, model names, or anything
about how the run is executed. Never offer a recommended option.
<!-- /user-facing -->

On the go-ahead, append `phase: plan approved` to the ledger. Nothing reads before that line exists.

## 4. Window 1: vocabulary

The reading happens one level down, one runner per pass. The lead does exactly this and holds
nothing else:

1. **Start one runner per pass.** For each pass in the window, dispatch a fresh
   `plumlayer:scope-round-runner` with the runner dispatch below: pointers only, no pass brief, no
   trade file, no read-plan text. Append that pass's dispatch line to the ledger before you
   dispatch it, never after. Passes of different disciplines start together; passes the plan marks
   as seeing the same work start one after another. What a pass leaves in the lead's context is
   its dispatch line and its summary, nothing else.
2. **The runner owns the pass.** It writes the pass brief if it is not already on disk, records the
   carried trades' convention lines once, runs the pass's units in reading order (one fresh
   `plumlayer:scope-reader` per unit, one unit at a time), appends each unit's dispatch line
   before that unit starts, verifies every unit with one `verify_unit` call before the next unit
   starts, notes overlaps inside the pass, and appends the ledger in its fixed line shapes. The
   per-unit loop lives in the `scope-round-runner` agent definition and the reader mandates live
   in the `scope-reader` agent definition. Neither is restated here, and neither is ever trimmed.
3. **Take a pass's counts when it reports, then let its summary go.** A runner returns one
   fixed-shape summary (shape below). Before you say a number out loud, take the created count for
   each of that pass's units with your own `search(subjectPrefix: "scopeItem:<unit-id>-", limit: 1)`,
   reading `count`. That is the third boundary of non-negotiable 6, and it is count-only: never a
   row list. Say the update and Question counts as the runner verified them, and the created
   counts as your own. Append one `pass:` line to the ledger carrying that pass's verified totals,
   and work from that line from then on rather than from the summary. A mismatch stops the run and
   gets investigated, never papered over.
4. **Close the window at its boundary.** When every pass of the window has reported and carries
   its `pass:` line, dispatch one more runner with `boundary` in place of the pass id. It scans the
   window's new items for the same work captured by two passes that ran alongside each other,
   declares any kind a reader named and did not declare, copies the record's definitions
   (`list_definition_kinds`, then `list_definitions` paged for each kind) to
   `<run folder>/plan/kinds/` for the plan script, one file per response, and ends. Then append
   `phase: window 1 complete` to the ledger with the window's verified totals,
   and go straight to stage 5: the index runs before the check-in, so the trade pages the user
   opens at the check-in already carry every sheet.

## 5. The citation index

Between windows 1 and 2, again after window 3, and never skipped:

1. **Start it.** `index_citations(projectId)`. It walks the corpus for every definition code and
   every item's tag or mark on the record and cites every page each appears on, onto the definition
   and onto the items that resolve to it, as the record's own text match. It writes citations only,
   never a value; an item that already cites a page is not cited there again; a match on a code of
   two characters or fewer is left open rather than cited.
2. **Wait for it.** Poll `index_citations_status(projectId)` until its `state` is `succeeded` or
   `failed`, waiting between polls rather than polling back to back. On `succeeded` its `report`
   carries `codesTotal`, `codesMatched`, `citationsWritten` and the rest of the run's counts, and
   `leftoverCounts` carries the true count per kind of what it could not cite, with
   `truncatedKinds` naming the kinds whose rows were cut for size. Read the counts; never the
   pages. `queued` and `stale` are both safe to wait through.
3. **Put what it left open on disk.** Dispatch a fresh general agent whose whole job is to page
   what the index left open into `<run folder>/plan/index/`, copied never retyped, and return one
   line: pages fetched, rows on disk. It calls `index_citations_leftover(projectId, kind, offset,
   limit)` once per kind that `leftoverCounts` shows above zero, paging each kind until a response
   comes back with no rows, and writes each response to its own file the way the grid was fetched.
   A kind the pass cut for size has fewer rows to page through than its `total`, which stays the
   true count either way, so the end of the rows is what stops the paging. The kinds are
   `unmatchedTag`, `codeNoLocation`, `codeTooShort`, `fragmentUnresolvable`, `pageNotASheet`,
   `codeOverCap`, `hitNotDrawable` and `overRunCap`. Those files are what the plan script and the
   leftover runners read; you never do.
4. Append `phase: index built` to the ledger with the counts off the status, then check in
   (format below).

<!-- user-facing -->
At this check-in, name the window you finished and what it covered, then say plainly that every
item and every definition now shows every sheet it appears on, plans included, and that each
trade's page is ready to look at.
<!-- /user-facing -->

## 6. Window 2: one pass per trade

On the go-ahead:

1. **Write the window 2 plan.** Run the plan script for window 2. For every package in
   `plan/packages.json` it writes one pass, reading for that trade: the sheet families that
   trade's knowledge file names, selected off the inventory by discipline and sheet type; the
   schedules whose kinds resolve to it; and the sheets the index located that trade's codes on
   where that input is on disk. A pass over twelve sheets splits at the twelve into lettered passes
   of the same trade. It orders the passes so that two trades the knowledge files name as a seam
   run one after the other, and names what no trade reads. Read back only its bounds line: trades,
   passes, sheets read for more than one trade, sheets no trade reads, and any partial input it was
   given. `index locations not present` is one of those and is expected today: the index reports
   what it left open, not where it placed what it cited, so a trade's sheets come from its families
   and its schedules. Say it in the ledger rather than reading past it.

   ```sh
   python3 '<plugin root>/scripts/plan_inventory.py' plan --window 2 \
     --inventory '<run folder>/inventory.json' \
     --packages '<run folder>/plan/packages.json' --kinds '<run folder>/plan/kinds' \
     --index '<run folder>/plan/index' --trade-knowledge '<plugin root>/trade-knowledge' \
     --out '<run folder>/read-plan.md'
   ```

2. **Run the passes** exactly as stage 4 runs them: one runner per pass, dispatch line first, the
   runner's `verify_unit` per sheet, your own created counts per unit, one `pass:` line each, in
   the plan's order. The plan marks each seam group (trades whose work meets at a boundary,
   drywall with painting, insulation, fireproofing and ceilings, say); the passes of one group
   run one after the other, never two at once, and passes in no group may run together. A pass
   labelled as not next to one of its seam partners is still in that group and still runs
   serially with it. A pass's readers read
   for one trade with that trade's knowledge, and still capture everything they see on every
   trade (non-negotiable 5); the runner's overlap scan and the reader's search-before-create are
   what keep two trade passes from creating the same work twice.
3. **Check in every few trades.** After every fourth `pass:` line of the window, or sooner when
   the plan says a seam is next, check in (format below): the trades finished, their pages ready,
   what was raised. A pause here is at a package boundary and loses nothing.
4. **Close the window** with a boundary runner, as in stage 4 step 4, then append
   `phase: window 2 complete` with the window's verified totals and check in.

## 7. Window 3: the leftover

On the go-ahead:

1. **Write the window 3 plan.** Run the plan script for window 3. It writes the sheets no window 2
   pass read, grouped by discipline into passes of at most twelve, each sheet carrying the open
   entries the index left on it (a tag on the sheet matching no code on the record, a code the read
   returned in pieces, a code found on the sheet with no box to point at, a citation the pass had
   ready when it reached its ceiling for one run), and names what it left out. Read back only its
   bounds line: sheets, passes, open entries. A bounds line of zero sheets and zero open entries
   means the window has nothing to read: append `phase: window 3 complete` and go on.

   ```sh
   python3 '<plugin root>/scripts/plan_inventory.py' plan --window 3 \
     --inventory '<run folder>/inventory.json' \
     --packages '<run folder>/plan/packages.json' --kinds '<run folder>/plan/kinds' \
     --index '<run folder>/plan/index' --trade-knowledge '<plugin root>/trade-knowledge' \
     --out '<run folder>/read-plan.md'
   ```

2. **Run the passes** as stage 4 runs them, with `leftover-<pass id>` in place of the pass id, so
   the runner gives each reader the open entries for its sheet alongside the sheet itself.
3. **Close the window** with a boundary runner, then run the index once more (stage 5, steps 1 to
   3) so the items this window created carry every sheet too, then append
   `phase: window 3 complete` with the window's verified totals and what the second index left
   open, by count and named where it is a code found nowhere, and check in.

Spec sections account differently, since estimators never write CSI digit strings into scope
text: a TOC section is accounted when it appears as a package's `tradeCode` or in its `codes`,
read fresh via `solicitation_list_packages`, not a local artifact. After stage 8's amendments are
applied, list every TOC section that appears on no package's `tradeCode` or `codes`: those are the
TOC sections still open, reported the same way.

## 8. Amend the packages

The estimator-judgment stage. Packages are bundles of spec sections grouped by how subcontractors
actually split themselves in the market, not by the book's divisions. The baseline split was
drafted and created at orientation (`learn-project`): read it fresh via
`solicitation_list_packages(projectId)` rather than re-drafting it.

1. **Scope-driven amendments.** Where the scope list surfaces what the TOC cannot see (a
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
   be created or amended into one: name it "no catalog trade, not created" in the report. Where an
   amendment moves work between packages, the items on the moved trade are re-homed in one
   `record_batch` of `belongsToTrade` records, count-verified, and the move is named in the
   report; never leave an item on a package that no longer exists.
<!-- user-facing -->
Show what you did in plain words, mirroring orientation's wording: name the amendments made
   (packages created, split, collapsed, or renamed), each with its one-line rationale. Say it as
   what you did, not as a question: "I amended the split: two packages, here's why. Change any of
   them on the site or tell me and I will redo it."
<!-- /user-facing -->
   No approval is collected: the amendment governs as applied and stays editable; a correction is
   a tool call. Once the amendments are applied, append `phase: packages amended` to the ledger.
2. **Empty-baseline case.** When `solicitation_list_packages` returned no packages because the
   project has no spec sections (precondition 4), orientation could draft no split and readers
   named trades off the catalog alone; this stage derives the split from the finished scope list
   instead of amending a baseline: same bundling logic as orientation, same catalog resolution,
   same `solicitation_create_package` calls and `codes`/`notes` usage. Say so plainly in the
   report: the split was derived here, from the scope list, because there was no spec book to
   anchor an earlier baseline.

Trade responsibility is already on the record: every item carries its home trade and any
candidates from the moment it was written. Sheet-to-package assignment (`assign_sheet_packages`)
is the user's call: offer it only when the user asks; the relevant-pages list already falls out of
the citations.

## 9. Close out

<!-- user-facing -->
Report to the user, in plain words:

- **The scope list**: how many items, by trade and by category family; where to review it (each
  trade's page and the project's Scope view on plumlayer.com), and that every line shows every
  sheet it appears on, plans included.
- **What you would like them to look at**: the items you weren't sure how finely to split, the
  document defects found (contradictions, missing schedule rows, duplicate sheets), and the
  assumed items that don't fit this job, each counted by kind and the leading ones named.
  Document defects worth sending to the design team are the open Questions on each trade's page.
- **Trade responsibility to confirm**: how many items sit in more than one trade's package
  (count each item once, however many packages it sits in), the leading trades named, and where
  to review them (the "Trade responsibility to confirm" section in each affected trade's package
  on plumlayer.com).
- **What is still open**: what the index could match to nothing, by count, with the codes found
  nowhere named; the sheets no trade read; and the TOC sections on no package.
- **The package split**: the amendments made this run (created / split / collapsed / renamed,
  each with its rationale), the packages derived here from scratch only in the no-spec-book case,
  and TOC sections deliberately unbundled.
- **How long it took**: wall-clock from the read plan's approval to this report.
- **What the trade files should learn**: cases the trade file doesn't cover, and things in it that
  don't apply to this job.
<!-- /user-facing -->

The report is written off the ledger's `pass:` and `phase:` lines, read with a local filter, never
off memory and never off the whole file: the wall-clock, the counts, the deviations, and what is
still open are all there. When it has been given, append `phase: closed out`.

## The dispatches and the report shapes

Every dispatch carries pointers and nothing else. Whatever is pasted into a dispatch stays in the
dispatcher's context for the rest of the run, so the read plan and the brief values are opened by
the agent that needs them, from the paths it is handed, and the record is read by the agent that
needs it.

The mandates are not in these templates. They live in the two agent definitions the plugin ships,
`scope-round-runner` and `scope-reader`, where each dispatched instance reads them fresh. They are
never trimmed there and never restated here: a run that relaxes one reproduces a measured failure.

**Orientation dispatch** (the lead writes this, once, only when stage 2 finds orientation needs to
run):

```text
Project: <projectId>.
Run the `learn-project` skill for this project, in full, exactly as it is written. Then return
your summary and end.
```

**The orientation summary** comes back in this shape, and is all the lead reads:

```text
sheets seen <n>   index findings <n>   spec sections <n>   packages drafted <n>   questions <n>
```

**Runner dispatch** (the lead writes this, once per pass, and once per window boundary):

```text
subagent_type: plumlayer:scope-round-runner
Project: <projectId>. Window: <1, 2, or 3>.
Pass: <pass id, or "leftover-<pass id>", or "boundary">.
Run folder: <path>. Read plan: <path to read-plan.md>.
Run your pass as your definition says, write your summary to <run folder>/reports/<pass id>.md,
then return it.
```

**Reader dispatch** (the runner writes this, once per read unit):

```text
subagent_type: plumlayer:scope-reader
Project: <projectId>. Window: <n>. Pass: <pass id>. Unit: <unit id>.
Reading for: <"the vocabulary", or a catalog trade id, or "the leftover">.
Pages: <sheet number + fileId + 1-based pageInPdf, one per page>.
Open entries: <path to the unit's open-entry file under plan/index/, window 3 only>.
Run folder: <path>. Pass brief: <path to briefs/<pass-id>.md>.
Knowledge: <path to briefs/<pass-id>-knowledge.md>.
Read your unit as your definition says, write your report to <run folder>/reports/<unit id>.md,
then return it.
```

**The reader's report** comes back in this shape, counts and named anomalies only:

```text
unit: <unit id>   pass: <pass id>   window: <n>
pages read: <sheet number + pageInPdf, renders taken and the reason for each, one per page>
pages unread: <sheet number + pageInPdf + reason, or "none">
created: <n>   updated: <n>   questions raised: <n>   questions replied: <n>
updated subjects: <the subject of every item updated or newly cited, or "none">
questions raised ids: <the id of every Question raised, or "none">
questions replied ids: <the id of every Question replied to, or "none">
sent: <n>   landed: <n>   conflicts: <ids and how each resolved, or "none">
trades: <trade id + item count, one per trade; candidates <n>>
definitions kinds added: <kinds, or "none">
sheet readings written: <sheet number, one per sheet whose reading was recorded, or "none">
convention lines: contradicted <n> (subject + reason, one per line, or "none")
anomalies: <one line each, with sheet and page, or "none">
grain questions: <one line each, with sheet and page, or "none">
door-owned suggestions: <one line each, or "none">
```

`created:` is the reader's own item count, not the entries under those items. `updated:` counts
every pre-existing item the reader wrote anything onto, a note, a value, or a citation alike.
`sent:` and `landed:` count every write the reader made for the unit, across every call, not only
its first batch.

The `updated subjects:`, `questions raised ids:` and `questions replied ids:` lines are what let
the runner find those writes back: a create is findable by its `scopeItem:<unit-id>-` prefix, an
update lands on a subject that already existed, a raise on a fresh Question id and a reply on the
id of a Question somebody else raised, and nothing else in the report names them.

**The runner's summary** comes back in this shape, and is what the lead reads when a pass reports,
after taking that pass's created counts off the record itself: an entry count under each unit's
prefix, never the reader's own item count, which travels separately as `items`:

```text
window: <n>   pass: <pass id>
units read: <unit ids, in reading order>
per unit: <unit id> created <n> items <n> updated <n> questions <n> replied <n> verified <yes/no>
totals verified: created <n> (entry count under the unit prefixes), items <n> (reader's own item count), updated <n>, questions <n> replied <n>
trades: <trade id + item count, one per trade; candidates <n>>
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
window: <n>   pass: boundary
cross-pass overlaps: <item name + the two units, one per line, or "none">
kinds declared: <n>
definitions copied: <n> kinds, <n> codes
ledger: <path>, appended through <last line written>
```

## The check-in (what the user sees)

<!-- user-facing -->
At each check-in, name the window, or the trades, you finished and what they covered, then cover,
in plain sentences:

- What you read and what landed: sheets read, items added, items updated, by trade, and what you
  raised as Questions, by trade. Your own verified counts, never the ones reported up to you.
- What you would like them to look at now: document defects, items you weren't sure how finely to
  split, anomalies, each with its sheet reference, reviewable on each trade's page on
  plumlayer.com.
- What is defined now that wasn't before, and anything the next window depends on.
- Anything that went sideways: a count that didn't match and how you fixed it, a page you couldn't
  read, a pass that stopped. Say it plainly.
- What comes next in one sentence, what it will leave out, and the ask: proceed, adjust, or pause.
  A pause here loses nothing; the run picks up where it stopped.

For example: "I've finished the first window, the schedules and legends. Here is what landed by
trade, what I'd like you to look at, and what the next window reads. Proceed, adjust, or pause?"
<!-- /user-facing -->

## What this skill does not do

- **Upload or recognize drawings** (`drawing-upload`), **create projects** (`project-setup`),
  **read sub proposals** (`bid-intake`), **place takeoff measurements** (`takeoff`), **draft the
  baseline package split** (owned by `learn-project`).
- **Author boundary enrollments other than trade-responsibility candidates**: exclusions, general
  requirements, and VE/alternates stay manual-first doctrine; the user authors those boundary
  lines at the package surface.
- **Tag trades after the fact.** There is no tagging stage: an item's trade is written with the
  row. An item with no trade is a door refusal, never a backlog.
- **Keep a copy of the record on disk.** No packet, no definitions files: a reader asks the record.
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
present it as current: a trade pass writes onto the one shared list against the live record, and
nothing is reconciled afterward. Do not restore rounds, legs, folds, or the completeness accounting
as stages; the index and the leftover window are what replaced them.
