---
name: scope-run
description: >
  Read a Plumlayer project's drawing set into one grounded, cited scope list, every item on its
  trade, in three windows: the vocabulary, then every sheet once, then one review per bid package.
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
a package exists for every trade the manual names before the first sheet is read. Readers name
each row's trade by the work itself, and the run folds the packages into what one kind of firm
bids before the reviews. The shape, in the estimator's own order:

> First assemble one massive singular list of all the scope line items across the entire job; then
> sort through and decide which trade packages to create; assembling them is assigning one new meta
> variable on an entirely scoped line item.

One scope list, every row cited and carrying its trade from the moment it is written. Trade
packages are projections off it. Every mandate below exists because skipping it produced a
measured, real failure: follow all of them.

The three windows:

1. **Vocabulary.** Schedules, legends, general notes, and cover and index sheets; the spec
   sections were read at orientation. Readers record what the marks mean (the definitions), the
   scope the schedules themselves ground, and every item's trade. Beside them, one reader per
   drawing file reads the lines that file prints at the same spot on many of its sheets, its
   general and plan notes and the fixed part of its title block, once for the whole file, so no
   sheet reader in the next window reads them again. When the window closes, the
   record's citation index runs: a mechanical pass that locates every defined code and every
   item's tag on every page of the set and cites those pages onto the items and definitions. After
   this window every trade's page is usable.
2. **Every sheet.** Every sheet the first window did not read, once each, grouped into passes by
   discipline and read composition before extent: sections and details ahead of plans, because the
   sheet showing what an assembly is made of writes the better row, and the plan that calls it out
   then updates that row rather than creating a coarser duplicate beside it. A reader reads its
   sheet whole, for everything on it, whatever trade the work belongs to. This is where the scope
   is, and it is
   the bulk of the run: quantities where the sheets carry them, the splits the vocabulary read was
   too coarse for, the Questions that clear the bar for an RFI. When the window closes the index
   runs again, so every row cites every page it appears on before a review reads it.
3. **The reviews.** One review per bid package, read off the record rather than off the set: the
   package's own rows and candidates, the definition codes that resolve to it, the manual sections
   it lists in `manualSections`, and its catalog name and aliases. Those are the words the review searches the
   set's text for, and a hit no row carries becomes a row, cited to a page the reviewer opened for
   it. The same review finds where the manual and the drawings are silent on each other: a
   section on the package whose work no sheet shows, and work on the package's rows that no page
   of the manual names. Each that could move the price materially or stop a bidder pricing the
   work is a Question, cited to the start of the section or a box around the callout, and cited
   on the rows it affects; a product the manual specifies and no sheet shows also gets its own
   row with no value, so the Question shows on the trade's page. A low-cost one is left open for
   bidders. A package's page is finished when its review is.

A run can stop at the end of any window, inside window 2 at any pass boundary, and inside window 3
at any pass boundary, and resume later with nothing lost.

A run is one pass over one drawing issue. A project goes through several sets before it is built,
and each new set gets a full pass of its own over every sheet it prints, the way a new project
does, read against the record the earlier passes built: readers update the rows the door names,
reply to the open Questions, and cite the new set's pages. A pass underway is never interrupted by
a later delivery; it finishes the issue it started on, and the later one waits for a pass of its
own. Whether a delivery is a set or an addendum is the `issue` that `list_drawing_deliveries`
gives it, never a question for the user.

An addendum that lands after its set's pass gets a partial pass over the sheets it prints, and
nothing else: window 1 over its schedules, legends and notes, so a revised schedule is read before
the plans that call it, and window 2 over the rest of its sheets, with the index after each window
that ran, then window 3 over only the packages this pass wrote rows on. The stages below say where
a pass on an addendum differs; everywhere else it runs as a set's pass does.

**This run is attended.** The user approves the read plan before any reading and reviews at every
check-in. Never read past a check-in without the user's go-ahead. The package split is not a gate:
this run reads the baseline packages orientation created, amends them as the scope list surfaces
what the spec TOC could not see, shows what it did, and stops; they stay editable, and a correction
is a change on the site or a tool call.

Doctrine binds every step: agents read and judge; deterministic tooling grounds; nothing enters
untraced. Everything a reader records is its own reading, cited, carrying who wrote it and when;
it becomes the field's current value the moment it lands; anyone replaces it later by naming it.
The project record
is what every agent in the run reads from and writes to: definitions, sheet readings, orientation
facts, open Questions. No agent keeps its own copy of what the record already holds.

## The non-negotiables

Every stage below honors these. They are restated where they apply, but read them first: a run
that relaxes any one of them reproduces a measured, named failure.

1. **Cite everything, in the uniform shape.** Every drawing-grounded record carries evidence naming
   the sheet AND a resolvable 1-based page: `evidence.page` or `evidence.pageInPdf` as a positive
   integer for the page actually read. A sheet named with no page cannot be render-verified and the
   record door refuses it. Never fabricate a page or sheet to satisfy the door. A citation the
   index wrote is the index's own, recorded as a text match; a reader cites what the index did
   not already cite and never re-cites a page the item already carries.
   A manual-grounded record cites its spec section the way a drawing-grounded one cites its
   sheet, with the section number, the file and the page read: in `source` on a new row and as
   `kind: "spec-section"` on a row that already exists, in the two shapes the reader's mandate 2
   gives. The section is what the estimator reads; the page is where the app opens
   it. Never a bare document page for a manual whose section is known.
2. **Create / update / question against the live list.** Every reader holds the current scope list
   for its trade or content families as match-or-create context: for each thing seen, create a new
   item, update an existing one (a new citation, a note, a resolved cross-reference), or raise a
   Question, with a title and a citation. A Question is what clears the bar in the reader's
   mandate 1, a draft RFI. Never a
   parallel list, never a re-create of what exists, never silent skipping of what's already
   listed. The record refuses a create whose name the project already carries, on any trade and
   under any category, and names the row that holds it: work another trade's pass already captured
   is updated, never created again, and the reader turns that refusal into an update on the named
   row and sends again. Before raising a Question, read every Question on the project, closed
   ones included: `list_questions` with `status: "all"` and no trade filter, paged until it comes
   back whole. A trade filter drops the Questions that name other trades and the ones still at not
   known yet, and the reader's own page read carries only the open ones on its own trades. Where an
   open one already covers the same ask, reply to it instead of
   asking it a second time; a closed one is never asked again. A Question is about the project,
   never about a Plumlayer failure; a read or write that fails is reported and handled in the run's
   own failure path, not raised as a Question. Question text is plain estimator words, and every
   Question meets the standard the `ask_question` verb states: a title, a citation for every place
   it names, and only what is worth the design team's time. Every Question raised or replied to,
   by a reader, a reviewer or this run itself, is cited on each live row its answer would change,
   as the reader's mandate 1 decides those rows, so the estimator sees it on the trade's scope
   page, and it never carries an assumption, a value or a basis to price to: what to carry until
   it is answered is the estimator's call.
3. **Store-resolution is mandatory.** A mark, tag, or code is resolved by querying the project
   record, never from memory, never inherited from another sheet's read, never assumed from a
   similar-looking mark. For a code the page in front of a reader prints, its own
   `read_sheet_context` answer is that read; `search` and `list_definitions` answer for a code that
   answer does not carry. Where a code appears in the set is a question for the corpus
   (`search_set_text`), never for memory either.
4. **Capture everything; name the trade as you write.** Capture is complete: everything seen goes
   into the one shared list, whatever trade it belongs to. The reader that writes the row sets its
   trade right then, the catalog trade that names the work (the row's trade, below), and moves on;
   a wrong trade is moved later by a person or a later read, never held
   back. Where the reader cannot tell which of two or more trades owns the work, it names its best
   single trade as the home and tags every other candidate, and keeps moving. The record door
   refuses a new scope item with no trade and no candidate, and refuses a trade the catalog does
   not carry, on `belongsToTrade` and inside `packageRole:<trade>` alike. `record_batch` is atomic
   and order free, so the trade rides in the same batch as the name; `record` carries one entry, so
   there the trade entry is written first. Whether an item is an exclusion, a general requirement,
   or an alternate is still a person's call at the package surface.
5. **Every write is count-verified, at two boundaries.** After every batch write, the reader reads
   the record back and confirms the count that landed equals the count sent, and checks any
   conflicting rows individually, before it ends. The pass runner separately re-verifies the same
   unit with one `verify_unit` call before the next unit of that pass starts: the entry count and
   distinct subject count under the unit's prefix, and for each of the unit's sheets the subjects
   whose citations name it, which is how an update and a new citation on a pre-existing subject
   are found back. A reader's report that its batches landed is verified at both its own boundary
   and the runner's; neither replaces the other. The lead adds a third, count-only check when each
   pass reports: one `count_entries` call for the pass, its `subjectPrefixes` the
   `scopeItem:<unit id>-` of each unit id that pass's block in the read plan carries, never built
   from the runner's report, reading each `entryCount`, never a row list. Updates and Questions the
   lead reports as runner-verified rather than asserting a check it did not run. The lead never calls the unfiltered `list_scope_items` during
   the run: that verb walks the whole scope list, and pulling it is how the lead's context stops
   being cheap. Counts only, `limit: 0`, is the one call the lead makes on it.
6. **Grain.** One row per product type, and one row per product where the set names the product. A
   product type is a thing a sub buys and installs as its own line: a towel bar, a robe hook, a
   medicine cabinet, a walk-off mat, an acoustic underlayment. Where the set names products by a
   model number, or by a legend or schedule code that stands for one product, each product is its
   own row, named with its code and what it is ("Towel bar TA-04, 24 inch", "Medicine cabinet
   MC-2, 16 by 22 inch"), with the model in the description. Instances are never rows: one towel
   bar TA-04 in twenty bathrooms is one row, and where the set counts them the count is its
   quantity. A schedule of places, such as a room finish schedule or a door schedule, is read for
   the products and types it calls for, one row each ("Luxury vinyl tile flooring, LVT"), never
   one row for the whole schedule. A schedule of one assembly's types that differ only in size or
   spacing (shear walls, footings, lintels) stays one row for the assembly, with every code
   written out. Never copy a schedule's columns into a row: the row names its product and cites
   the schedule row that defines it, with a box on that schedule row built from the page's text
   read, never from a render, or the sheet with no box where no line of the read carries that
   row, named on the reader's `anomalies:` line. A row is never a whole sheet
   and never a package header. Where the reader or the reviewer cannot tell how finely the work in
   front of it splits, it creates at best
   judgment and names it on its `grain questions:` report line, which the check-in and the close
   out carry to the user; how finely our own scope sheet splits is ours to settle, and nobody on
   the design team answers it. Recall never drops to grain uncertainty.
7. **The vocabulary, then every sheet, then the reviews.** A window 2 pass reads only after the
   vocabulary is recorded and indexed; a review reads only after every sheet has been read and
   indexed. Inside window 3, two packages carrying the same catalog trade run one after the other,
   never at once. The read plan encodes this order and the user approves it.
8. **The vocabulary window covers the scope the schedules themselves ground.** The passes reading
   legends and schedules record what a mark means, and they also own the scope items the
   schedules ground, on their trades.
9. **Run, or stop and report; never create a consent step.** The user's decisions in this skill
   are the read plan and each check-in. Everything else the run does is its own work, recorded
   with who did it and when, and editable afterward. Never stop to collect approval for a course you have
   already chosen, and never offer a recommended yes: if something is genuinely wrong, stop, say
   what is wrong, and hand it over; if nothing is wrong, proceed and say what you did.
10. **The index runs three times, and what it left open is named.** The citation index is a
    standing step after each of the three windows, never optional; in a pass on an addendum, it
    runs after each window that ran. Nothing chases what it left
    open: a tag no reader could resolve on its own sheet is reported at close out, by count and
    with the codes found nowhere named, and that is a loss the report says out loud rather than
    a gap it fills by inference. Never assumed closed, never zeroed by hope.
11. **A remark about spend never trims a mandate.** Every verification in this file stands whatever
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
- **category** (required): the heading the row sits under on its trade's scope sheet, naming what
  its items are in the words a sub uses ("Toilet accessories", "Medicine cabinets", "Postal
  specialties", "Kitchen casework", "Countertops", "Resilient flooring"). Never the sheet, room or
  drawing it was read on, never another trade's name, and never two kinds of work joined into one
  heading. Every row under one heading sits on the same trade. Take a heading from the page's
  context read only where its rows are the same kind of work as yours. The review surface groups
  by this: an uncategorized list renders as a wall.
- **trade** (required), recorded as `belongsToTrade`: the catalog trade that names the work
  itself, the finest the catalog carries. Where the manual specifies the work in a numbered
  section, use the catalog trade for that section. Otherwise use the trade whose catalog name, not
  an alias, says what the item is, found with `directory_list_trades(query: <the item's own
  noun>)`. Never the trade a sheet's title names, never a trade because its package happens to
  exist, except work a package's `notes` say it installs or carries, which takes the package's
  `tradeCode`, never `01 11 13` because no package fits. Which sub bids the work is the package's
  business, settled when the run folds packages before the reviews (stage 6 step 5). It is the
  catalog id copied verbatim, exactly as the catalog prints it, spaces and all (`09 21 16`).
  Never a word for the trade, so `drywall` is refused, and never a
  respelling of the code either, so `09-21-16` and `092116` are refused too, with a hint naming the
  exact id. Where the work straddles trades, the best single
  home goes here and each other candidate gets a `packageRole:<trade>` record whose value is the
  object `{ role: "candidate", note: "confirm trade responsibility: could be <home> or <this
  trade>" }`, the note internal only and never bidder-facing, written in the same batch. The roles
  the door takes are `exclusion`, `general-requirement`, `ve-alternate` and `candidate`, each with
  an optional `counterparty` and `note`, and `{ retracted: true, reason? }` is the only other value
  it takes. A bare word is refused and the batch is atomic, so it costs every entry in the batch.
  The `<trade>` in that predicate is the same catalog code, and the door reads it there too.
- **description** (optional, zero to three sentences): only what a bidder must know to price the
  line that the name and citation do not already say: the product or method the drawings call
  for, the extent or limits, a rated or special condition. A simple item has none. The citation
  points at the sheet, and the doctrine is cite, don't rewrite: never transcribe a schedule's
  columns, the detail, or the bar sizes into the row. How a schedule becomes rows is
  non-negotiable 6.
- **notesExternal** (optional, one sentence): an instruction to the bidder about the line: what is
  by others, what to break out, what to confirm, what is an alternate.
- **notesInternal** (optional, one sentence): either a watch item for the estimator, an open
  Question on the row, or how the row's count or grouping was reached
  and what a correction replaced. Never a citation audit, and never a conflict between two
  documents: that is a Question. A correction of a value on the record is two things: the write
  onto that field naming what it replaces (`supersedesId`), cited to a box around what shows the
  right value with the words read there as the evidence snippet; and this note, one plain sentence
  saying how the value was reached and what it replaced, never an id or a hand-written tag,
  placed after any text there that asks something or names an open Question, as the reader's
  definition says for every sentence added to `notesInternal`. That
  note is what lets a later reader correct the row rather than doubt the drawings. A correction is
  never a Question.
- **quantity**: only where the sheet itself carries one, as `{value, unit}`.

A row's text never carries another item's subject id or a hand-written SUPERSEDED or date tag,
per docs/plugin-text-style.md. Splitting one item into two is `retire_scope_item` naming why, plus
a fresh CREATE for each half, never a tag written into the description.

Recorded text is what the bidder reads: plain sentences, no em dashes, no bolding, never a
sheet-by-sheet narration. The door refuses text over its bound (`name` 80 characters, `category`
60, `description` 400, `notesExternal` and `notesInternal` 300 each); a row shaped by these rules
never comes near them. A verbose row is a defect, not diligence.

## The Question bar

A Question is a draft RFI, and it meets the standard the `ask_question` verb states. What this
run adds to that standard is where it applies here. A Question clears the bar when the answer
could move the price materially or stop a bidder pricing the work, or when two documents disagree
about the work: a schedule row with no matching plan tag, a detail called where none is drawn, a
spec section and a sheet naming different products for one assembly, a dimension the sheets
contradict, a tag the set defines nowhere, a product a schedule leaves TBD, a rock elevation above
the excavation where neither the sheets nor the manual say how its removal is paid (unclassified
excavation, a unit price, an allowance). Rock or water above an excavation is a row either way. A
follow-up reply adds sources and never argues which document governs. It does
not clear the bar:

- when the answer is elsewhere in the set or the manual, on a sheet the run has not read among
  them: `search_set_text` first, across the drawings and with `kind: document` across the manual,
  and the answer's page opened;
- when requirements stack, from separate programs or set area by area, so that meeting the
  strictest meets them all: each is carried where it applies, the strictest where two apply at
  once;
- when either answer is built and priced about the same, which includes what the sub settles in
  its shop drawings when that holds: that is a qualification on the row;
- when a sheet's own note says what to assume, allow or carry, and no other page prints a
  different allowance, amount or product for the same work: that note is the pricing basis;
- when an open Question asks about the same subject for the same trade: the find is a reply on it;
- when a Question already asks it: read every Question on the project first, closed ones
  included, with no trade filter (non-negotiable 2);
- when it is a low-cost gap in a small trade: it is left open for bidders, with no Question and no
  assumption written for it;
- when it is a grain call: that is a report line (non-negotiable 6);
- when it is a note to the estimator: that is `notesInternal`;
- when it is about a scope row: the row is what is wrong, and it is corrected on the record.

Every Question says which trades it affects, and there are three honest answers. It names the
trades that would have to answer or price it: `trades` with the catalog codes, one or several, or
`trade` for a single code. It takes `everyTrade: true` where it spans the job and belongs to no one
package, as with a sheet or a schedule the set lacks or a general note that binds packages created
later, never a hand-picked list of the packages that exist now. Where nobody can tell which trade
owns it, none of the three is sent, and the Question sits at not known yet rather than being
guessed into a package; `set_question_trades` answers it later, once someone knows.

## What the record holds, and what stays on disk

Everything an agent in this run needs to know about the project is on the project record, and is
read from there by the agent that needs it, when it needs it:

- everything the above holds about one page of the drawings, in one call:
  `read_sheet_context(projectId, fileId, pageInPdf)`, which a sheet reader takes once per page. It
  is cut to fit rather than paged, and it names every list it did not carry whole, so the verb that
  owns that list reads it;
- the orientation facts (identity, systems, scope areas, hazards): `get_project` and `search` on
  their predicates;
- the packages and their catalog trades: `solicitation_list_packages`;
- the definitions: `list_definition_kinds` for the kinds, `list_definitions(kind)` for the codes
  under one, `search(subject: "<kind>:<code>")` for one code's full definition;
- what a sheet is, which legend its tags resolve to, and what it references: the sheet's own
  reading, written once by the first reader that reads it (`sheet:<sheet number>`);
- where a code or phrase appears in the set: `search_set_text`, over the corpus every page was
  read into at upload, the drawings by default; `kind: document` asks the project manual instead,
  `kind: all` every file at once, and every answer names the `kind` it covered;
- the open Questions that name a trade or affect every trade: `list_questions` with `trade`;
- the sheet inventory: `set_grid` with the pass's `deliveryId`, taken once to disk for the plan
  script and never held.

No packet, no definitions files, no per-run copy of any of it: a reader that wants to know what a
door type is asks the record, and a second reader on the same sheet finds the first one's reading
there.

The project folder, `<runs root>/<projectId>/`, where `<runs root>` is `~/.plumlayer/runs` with
the home directory written out, is named for the project id and never for the project's name, so
two projects of one name never share a folder. It holds `deliveries.json`, the delivery list the
lead chooses a pass from, copied byte for byte from `list_drawing_deliveries` and read only by the
plan script (Audience: machine), and one run folder per pass, named for the delivery the pass
reads: `<project folder>/<deliveryId>/`. Projects once had folders named for the project's name. A
project whose passes began in such a folder keeps them there: the plan script's issue mode finds
that folder by the deliveries its passes read, and resumes and starts the project's passes in it,
naming it on its line, so every pass of one project stays in one folder. A pass begun before passes
had folders of their own keeps its files in the folder of the project itself, and resumes there as
it always has. A run folder holds only the run's own bookkeeping. Never committed to any repo, never uploaded to the project except
record files, never recorded as project entries:

- `run.json`: the drawing issue the pass reads and the tag its unit ids carry, written by the lead
  at stage 3 step 1 and never changed once the plan is approved. The delivery's id, label, issue
  and set come off the `delivery` the shape call names, `readFrom` is the id of every delivery its
  `readFrom` lists, in that order, and `unitTagCheck` is the count of rows the record carried under
  the tag before the plan:

  ```json
  {
    "deliveryId": "deliv-7d1e4b20-5c3a-4f8e-9b61-0a2c8e5f3d14",
    "label": "Permit set",
    "issue": "set",
    "setId": "deliv-7d1e4b20-5c3a-4f8e-9b61-0a2c8e5f3d14",
    "readFrom": [
      "deliv-7d1e4b20-5c3a-4f8e-9b61-0a2c8e5f3d14",
      "deliv-c90a6f13-2e7b-4d58-8a04-6b3f1e9d7c22"
    ],
    "unitTag": "i2",
    "unitTagCheck": { "subjectPrefix": "scopeItem:i2-", "count": 0 }
  }
  ```

  The plan script reads it from the folder the plan sits in. Every unit id of the pass carries the
  tag (`i2-A2-3`, `i2-RS1-1`, `i2-rev-092116-1`), so no pass records under, or counts, another
  pass's subjects. It refuses a grid or an inventory whose delivery, or the deliveries its rows
  came from, differ from this file, a tag another run folder of the project carries, and a tag the
  record already carries rows under. Audience: machine.
- `ledger.md`: the run ledger, appended as the run proceeds, one line per entry in the fixed shapes
  the `scope-round-runner` definition gives, plus the lead's own `pass:` and `phase:` lines.
  Nothing else goes in the ledger: no headings, no bullets, no paragraphs, no re-telling of a
  report, except the `anomaly` notes, each a report's line copied whole, as the runner definition
  says. It is appended, never rewritten and never reformatted, and never read whole by anyone:
  the lead reads its `phase:`, `pass:` and `checkin:` lines with a local command (a filter on the
  line prefix), the
  close-out report is written off its `pass:` and `phase:` lines the same way, and off the window 3
  `anomaly` notes that carry `same work:` (stage 9), and a runner reads only its own filtered look
  for a unit's `verified` line and `anomaly` notes, as the runner definition says. Audience: agent, and it feeds the close-out report, so whatever crosses into that
  report becomes user-facing at the crossing and is translated there.

  The lead's own three line shapes, which the runner never writes:

  ```text
  pass: <window> <pass id> units <n> created <n> updated <n> questions <n> replied <n> candidates <n> lead-verified <yes|no>
  pass: 3 <pass id> units <n> created <n> updated <n> questions <n> replied <n> candidates <n> pages-opened <n> searches <n> lead-verified <yes|no>
  phase: <boundary name>
  checkin: <window> <window, the id of the last pass recorded before it, or none> <go|pause>
  ```

  A `checkin:` line says a check-in was shown and how the user answered it, appended as the
  check-in section says. Its second field is `window` for the check-in that follows a window's
  closing lines (window 1's after its index, window 2's after the fold or after a paused slice's
  index), the id of the last pass recorded before it for one inside a window, a check-in on a
  sheet that stopped answering included, and `none` for one inside a window before any pass of that
  window is recorded, as a check-in on a sheet that stopped answering in the window's first pass.
  Its last field is `go` where the user sent the run on and
  `pause` where they stopped it there.

  Every figure on a `pass:` line is written by `lead_pass.py record` (stage 4 step 3) off the
  pass's summary file and your own count call, never typed by hand: `created` is the sum of your
  counts, and `updated`, `questions`, `replied` and `candidates` come off the summary's totals and
  trades lines, in every window. A window 3 line carries two fields more, `pages-opened` and
  `searches`, off the summary's `review:` line, which the summary script reads off the reviewer's
  own `pages opened:` and `searches:` lines. Those fields are what make the run countable from the
  ledger afterwards.

- `grid/`, `inventory.md`, `inventory.json`: the sheet grid as the fetch agent put it on disk, and
  the plan script's counts off it. The lead reads the count tables and the sheet number digest,
  never a sheet line. Audience: machine, and the tables for the lead.
- `plan/`: byte-for-byte copies of a verb's response, paged to disk by a fresh agent, never
  retyped and never read by a model. `packages.json` (`solicitation_list_packages`) is the plan
  script's window 3 input, copied again at the start of window 3. `window-1.json` is what the window 1 plan run wrote, the unit keys it
  selected and the unit keys it left out with its `--include` and `--exclude` patterns and their
  reasons, and its repeated lines units in `repeatedSets`, and it is the window 2 plan run's
  input, so that window subtracts window 1 rather than recomputing it. `window-2.json` is what the last window 2 plan run wrote, the unit ids it
  assigned and, for a slice, each `--only` pattern, the unit keys it deferred and the unit keys an
  earlier slice already read and verified; the next window 2
  plan run reads its ids back, so a slice's ids stay where they are. A resume takes a window's
  patterns off its file to run that plan again exactly. `packages-at-fold.json` is the package
  list as the package folder found it at the fold's first start, written by the folder before any
  act; a folder sent again after a stop compares the record with it, since windows 1 and 2 can make
  packages `packages.json` never held, and you never read it.
  Nothing else is copied here: the definitions are on the record and no window plans off them.
  Audience: machine.
- `read-plan.md`: the read plan, one per window, written by the plan script, never by hand: the
  passes, the units within each with their sheets, files and pages in windows 1 and 2 and the
  package each review reads for in window 3, and what is deliberately excluded. Audience: agent; a
  runner opens its own pass only.
- `briefs/`: one small file per pass, written by that pass's runner, carrying the pass's filled
  slot values (what the pass reads for, its content families, the subject prefix scheme). It is the
  whole of what a reader or a reviewer opens off disk. The mandates are never in the brief.
  Audience: agent.
- `reports/`: one file per read unit and per review, the report in its fixed shape, written by the
  reader or reviewer before it returns, so a dispatch that returns without the report in hand loses
  nothing. A review also writes `<unit id>-terms.txt` here, the words it harvested, so it ranks
  them on disk rather than in its context. One file per pass holds the pass summary, written by
  the summary script the runner runs, and the runner returns only the hand-back; `lead_pass.py`
  and the plan script read the summary here. The package folder writes `fold.md` here, one act
  of the fold per line, which you read only through `fold_report.py print`. Audience: agent, and
  `fold.md` feeds the check-in that ends window 2 and the close-out, so whatever crosses from it
  into those becomes user-facing at the crossing and is translated there.
- `names/`: one file per pass, the new item names each unit created, one per line, matched
  against themselves and each other with a local command for overlaps. Audience: machine.
- `kinds/`: one file per pass, the definition kinds each unit's reader named, one per line,
  appended a unit at a time, and the window boundary takes their union with a local command to
  find every kind a reader named without holding any of them itself. Audience: machine.
- `trades/`: one file per pass, the trades each unit's own verification read, appended a unit at a
  time: one line per trade as `<unit id> trade <catalog id> <count>`, and one line as
  `<unit id> candidates <count>`, that count being the unit's created subjects carrying at least
  one candidate trade, each subject counted once however many candidate trades it carries. The
  pass summary script sums this file, so no runner adds the trades up itself. Audience: machine.
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
  check-ins, amending, close out. For each pass it starts one runner and receives one short
  hand-back; what it keeps per pass is that hand-back and, once it has taken its own count, the
  one `pass:` line `lead_pass.py` writes to the ledger. It never holds a pass summary, a pass
  brief, a reader's report, the sheet grid, the index report, or a page of the set.
- **The pass runner** (the plugin's `scope-round-runner` agent, one fresh instance per pass) owns
  one pass: it writes the pass brief, runs the pass's units exactly as the window's stage defines
  them, verifies every unit with one `verify_unit` call, notes overlaps inside the pass, appends
  the ledger in its fixed line shapes, writes its summary to disk, returns its hand-back, and
  ends. Its context is bounded to one pass of at most twelve units, and it never grows with the
  size of the window. Two further
  instances run in their own modes: one closes each window at its boundary (the cross-pass overlap
  scan and the declaration of any kind a reader named and did not declare), and in window 3 each
  pass runner runs up to four review units, or every package of one trade where that trade has
  more, one at a time.
- **The reader** (the plugin's `scope-reader` agent, one fresh instance per read unit) reads one
  sheet, for the vocabulary or for the sheet itself, over the corpus, and records, as the window's
  stage and the pass brief define. It writes its report to `reports/` and ends.
- **The package folder** (the plugin's `scope-package-folder` agent, one fresh instance per
  dispatch) folds the packages into what one kind of firm bids once window 2 is read and indexed,
  writes each act to `reports/fold.md`, and returns a five-line hand-back; dispatched again, it
  deletes a package for the owner's own work that a later write made again.
- **The reviewer** (the plugin's `scope-reviewer` agent, one fresh instance per package) reviews
  one package in window 3: it harvests that package's own words off the record, searches the set's
  text for them, opens only the pages a hit sends it to, and records what no row carries. It writes
  its report to `reports/` and ends.

Handoff is by file and record, never by inlined text. A dispatch at any level carries only
pointers: the project id, the window, the pass or unit id, the run folder path, and the page or
package references. A reader and a reviewer open the pass brief from the path they are handed and
everything else from the record; the runner opens the read plan for its
own pass and appends the ledger without reading it. Nothing from those files is pasted into a
dispatch, because whatever is pasted stays in the dispatcher's context for the rest of the run.

A dispatch is one Agent tool call, and how you wait on it depends on the session. Where the Agent
tool takes `run_in_background`, as in a headless session, send it `false`, as every template below
does: the call is then the wait and returns only once the agent has ended and reported, because a
headless session stops a background agent after ten idle minutes. Where the call comes back with an
agent id instead, the agent's report arrives later as its own message: end the turn with one line
naming what is running, and take the report when it arrives. That is the case in a terminal, the
desktop app or an editor. There, make every dispatch the plan allows now, then end the turn with
that one line. Wait on an agent by ending the turn and nothing else: no sleep, no shell loop, no
look in `reports/` or at an agent's output file, no Monitor, no message to the agent, never a second
agent to wait for the first, and never a placeholder agent to fill a turn.

Match each report that arrives to a dispatch of yours: a runner's hand-back by its `pass:` field,
the package folder's by its `fold:` line, and any other by the one dispatch of its kind you have
running. A hand-back, a notice or a message from an agent you did not dispatch, such as a reader
your runner dispatched or another session, is not your report: never relay its counts, answer it
where it asks something, then end the turn again. One turn can carry several hand-backs: take each
in turn. A completion notice for an agent whose hand-back you already took changes nothing. Where
the user writes while agents run, answer them and end the turn again. A turn ends with nothing
running only where you speak to the user and wait on their answer: a check-in, the read plan's
among them, a question this skill puts to them, or the close-out.

Several dispatches sit partway through a stage: the copy of the delivery list (precondition 3),
orientation (stage 2 step 2), the copy of the packages (stage 2 step 4), the grid fetch and a fetch
sent again (stage 3 step 2), the package folder (stage 6 step 5), and the copy of the packages at
window 3 (stage 7 step 1). Where the call comes back with an agent id, end the turn after that
dispatch and continue at the next step when its report arrives.

Where a reader, a reviewer or a runner has ended and its report did not arrive in the message, as
with a completion notice that carries no hand-back, its report file under `reports/` is the report,
written before it returned; open that file rather than re-running the unit. A unit whose report
file is also absent is re-run on its own unit, against the live list, so nothing is created twice.

An agent that stops answering partway is ended by the client within about ten minutes, and its
dispatch comes back as an error whose whole text is `[Request interrupted by user for tool use]`.
While the caller is still running, that is never the user: their interrupt would have stopped the
caller too. It is an agent that stopped answering. A reader that stops is read again once by its
runner, as the runner's definition says, and a second stop ends that pass. A waiting runner is
never ended for its reader's silence, so a runner that comes back this way stopped on its own
reply: start no further pass and check in at once, naming the pass and its sheets. On the
go-ahead, dispatch that pass again; its runner skips every unit already verified. Every further
read of a sheet that stopped waits for the user's go-ahead.

Reports travel upward in a fixed short shape, counts and named anomalies only (the shapes are
given with the dispatch templates below). A runner returns its hand-back, a few lines of counts
naming its summary file, and the summary stays on disk. When the hand-back arrives the lead takes
its own count off the record, and `lead_pass.py record` compares that count with the summary file
and writes the pass's `pass:` line, so the lead never reads a summary, never relays one, and works
from that line once it is written.

Phase boundaries are the ledger's `phase:` lines, one appended by the lead at each of: plan
approved; window 1 complete, or window 1 skipped where a pass on an addendum planned no window 1
unit; index built; window 2 complete, or window 2 paused where a slice
deferred sheets; packages folded; window 3 complete; packages amended; closed out. Inside a window the `pass:`
lines are the boundaries: one per pass in every window. A pass run
again to finish it carries a second `pass:` line, and its last one carries the whole pass: every
total taken over a window, and the close-out report, counts that one, for each pass the window's
read plan now carries. A part a replan folded into another pass after its own `pass:` line was
written is counted in the pass that took it in, and never twice. On every start this skill
reads the ledger's `phase:`, `pass:` and `checkin:` lines first, with a local filter, never the
file: a run in flight resumes at the phase after the last line. A check-in a `checkin:` line
records was shown and answered, and is never shown again:

- Where the last of those lines is a `checkin:` line reading `go`, start the step that follows
  that check-in: after window 1's, stage 6 step 1, the window 2 plan; after window 2's, stage 7
  step 1, or stage 6 step 1 again after a paused slice; after one inside a window, its second field
  a pass id or `none`, the passes that are not finished.
- Where it reads `pause`, the user stopped the run there: say in one sentence what the run does
  next, and start it on their go-ahead, with a `checkin:` line reading `go` for the same check-in
  first.
- Where the last line is the one a check-in follows (`phase: index built` after window 1 or after
  a paused slice, `phase: packages folded`, or the `pass:` line that made a fourth since the last
  check-in) and no `checkin:` line follows it, that check-in was never answered: gather it and
  show it.

Inside the window in flight, run that window's
plan script again first, exactly as its stage wrote it, with the same arguments: window 1's
`--include` and `--exclude` and a slice's `--only`, each with its reason, are on that window's
`plan/window-<n>.json`, taken off it with a local filter, and after `phase: window 2 paused` the run
is the one without `--only` that stage 6 step 4 names. The script keeps every id the ledger and the
plan file already hold and marks the units already verified. Then dispatch the first pass of the
window that is not finished, found with the one `lead_pass.py passes` call stage 4 step 1 gives,
which reads the pass headings and their `units:`, `units verified:` and `summed:` lines and names
the passes to dispatch on its last line. A pass is finished when its block shows the same count on
its `units:` and `units verified:` lines and shows `summed: yes`. Window 1's repeated lines pass is
a pass like any other here: it carries the same three lines and is finished, or dispatched, the
same way. The plan script writes that
only while the pass's summary on file names exactly the unit ids the block now carries and the
pass's last `pass:` line carries that summary's figures, so a replan that changes which units a
pass carries, by a fold or a cut, leaves it unfinished even where the count comes out the same.
Any other pass is dispatched, whether or not a `pass:` line for it is on the ledger: its runner
skips the units already verified and writes a new summary. A pass on a later drawing issue starts
in a run folder of its own on a project that already carries scope items, and the live-list
mandate (non-negotiable 2) keeps its readers from creating what is already there. A run folder
lost from this seat leaves its rows on the record under its tag: the tag check moves past that
tag, and the pass on that issue starts again in a new folder, against the live list.
Resumption is how a run continues after a stop at a boundary, and crash and multi-day hygiene. It
is never offered to the user as a way to manage cost, and the check-in never suggests it.

## 1. Preconditions

Before any of these, a resume included, run `claude --version`. The run leans on the client to end
an agent that stops answering: an older client has been seen waiting over an hour on one reader,
with the whole run waiting behind it. Below 2.1.283, stop and ask the user to update Claude Code
first. Where the command is not found, ask the user once to confirm their Claude Code is up to date
before going on.

1. **Project exists and is the user's intent.** `list_projects`, confirm which project with the
   user, get its `projectId`. No project → hand off to `project-setup`.
2. **A Python interpreter on the seat.** Probe for one, `python3 --version` falling back
   to `python --version`: which pass runs, and the read plan of every window, are written by a
   script. Neither name present is a stop for this run: say so plainly and
   hand over, since a plan written by hand has been the measured failure every time.
3. **Resume the pass in flight, or choose the drawing issue to start one on.** With the
   `projectId` in hand and before anything else, send one fresh agent to copy
   `list_drawing_deliveries(projectId)` to `<project folder>/deliveries.json` byte for byte, by the
   rules of the grid fetch in stage 3 step 2, returning one line. Then run the plan script's issue
   mode the way stage 3 runs its other modes, and read its one line and nothing else:

   ```sh
   python3 '<plugin root>/scripts/plan_inventory.py' issue \
     --runs '<project folder>' --deliveries '<project folder>/deliveries.json' \
     --runs-root '<runs root>'
   ```

   Its first word is what you do. Every run folder you work in from here is the one the line names.
   Where the line ends by naming the folder this project's passes are in, the project began its
   passes in a folder named for the project, and they all stay there; never move a file out of it.
   A refusal naming a folder two projects shared, or this project's passes in two folders, stops
   the run. Tell the user in plain words that this project's earlier run files are mixed with
   another project's and the run stops until they are separated, or that they are kept in two
   places and the run stops until they are moved into one, and hand over. The folders stay in the script's line; never say a folder path.
   - `resume <run folder>`: a pass is in flight, and it finishes before another starts, whatever
     has landed since; a later delivery gets a pass of its own once this one closes out. Read the
     `phase:`, `pass:` and `checkin:` lines of that folder's `ledger.md` with a local filter on the
     line prefix; never open the file whole. Resume at the phase after the last one, never showing
     again a check-in a `checkin:` line records, and inside the window in flight run its plan
     script again and dispatch the first pass that is not finished, as the windows section above
     says, so nothing already verified is read again. Where the last
     `phase:` line is `window 1 complete` with no `index built` after it, the index step (stage 5)
     runs first. Where the ledger carries no `phase:` line yet, the plan was never approved: take
     stage 3 again from step 1 in that folder. Once the plan is approved, never fetch the grid of a
     pass you resume: its `inventory.json` is its sheet list, and the plan script refuses a grid
     or an inventory whose deliveries differ from its `run.json`. A pass begun before passes had
     folders of their own resumes in the project folder itself, exactly as it always has. A run is
     never resumed past a boundary that did not run. Never offer resumption to the user as a way to
     manage anything, and never raise it at a check-in.
   - `wait <deliveryId>`: that delivery's sheet numbers are still being read, and it may yet be a
     new set. Wait, then copy the delivery list again and run the issue mode again, waiting between
     tries rather than trying back to back.
   - `start <deliveryId>`: the latest set, which no pass has read, or, once the set has its pass,
     the earliest addendum of it that landed after that pass; the line says which, and names the
     addenda still waiting behind this one. Each of those gets a pass of its own, one at a time,
     in the order they landed. The line names its run folder
     and its unit tag. Make the folder, and check the tag on the record:
     `search(projectId, subjectPrefix: "scopeItem:i<n>-", limit: 1)`, reading `count`. A tag is
     free where no subject starts `scopeItem:<unit tag>-`; a count above zero is rows from a pass
     whose run folder is not on this seat, so take the next number and count again until one reads
     zero. That count goes into `run.json` at stage 3 step 1. The pass on a set is a full pass over
     every sheet the set and its addenda print; the pass on an addendum is a partial pass over the
     sheets it prints, since `set_grid` by an addendum's `deliveryId` gives only those. Where the line ends by saying the earlier pass in the
     project folder names no drawing issue, a pass from before passes had folders of their own is
     closed out there, and nothing records which set it read: start all the same, never guess
     which set that was, and say so at the read plan's check-in.
   - `none`: there is nothing to start, and the run stops here.
<!-- user-facing -->
   Say what the line says, plainly: you already ran a scope pass on the latest set, naming it,
     and on every addendum of it since. Where no delivery reads as a set yet, say the drawings are
     not in, and hand off to `drawing-upload`.
<!-- /user-facing -->
4. **Drawings are recognized, and their text is read.** Spot-check recognition actually
   recorded: `search(projectId, predicate: "appearsOnPage", limit: 1)`: zero rows → hand off to
   `drawing-upload`. On a set that just landed, check `set_text_status(projectId)` and wait until
   it shows the set read: a page nobody has read yet cannot be found by `search_set_text`, so a
   fresh delivery still being read would otherwise look like a missing corpus. The corpus itself
   is confirmed once the inventory is on disk, at stage 3 step 3.
5. **Spec book, if it exists.** `search(projectId, predicate: "inDivision", limit: 1)`: spec
   sections present means the spec-TOC leg has run. Absent: ask the user whether a project manual /
   spec book exists. If one does, run it through `drawing-upload`'s spec-book leg first (upload +
   `extract_spec_toc`): the package split anchors on the spec table of contents and is
   substantially weaker without it. If the project genuinely has no spec book, proceed and name
   that in the ledger and the close-out report: orientation created no baseline packages for this
   project (no spec sections, no anchor), and stage 8 below derives the whole split from the
   finished scope list instead.
6. **The user is present.**
<!-- user-facing -->
Tell them what the run will do: you read the set in three windows, the schedules and legends
   first, then every sheet once, then each package reviewed on its own against what landed,
   several at a time, and you stop for a check-in after the first window and at regular points
   through the sheets and the packages after that; after the first window
   every trade's page already has its items. They can stop or change course at any check-in. Give a
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
2. **Orientation runs one level down.** Where step 1 finds orientation needs to run, start it as
   `learn-project`'s own "Running one level down" section says, with the orientation dispatch it
   gives, the way a pass is dispatched to a runner: pointers only, no seed facts, no inventory rows,
   no spec-section text. The agent runs the `learn-project` skill exactly as written and returns its
   summary in the shape that section gives. Read back only that summary: its first line (sheets
   seen, index findings, spec sections, packages drafted, questions raised) and the lines under it.
   Never relay the dispatched agent's own user-facing report text. What orientation learned is on
   the record, which is where every reader reads it.
<!-- user-facing -->
   Tell the user what orientation found, in a few plain sentences, in your own words off that line:
   roughly what was learned, any Question it raised, and the package split it drafted. Say it as what happened, not as a question.
<!-- /user-facing -->
   Where step 1 finds orientation already exists, skip the dispatch and call
   `reconcile_set(projectId)` report-only yourself (never pass `record`, never pass a
   `deliveryId`: the bare call is the orientation check), checking `.ran` flags before citing any
   drift number, a check that did not run is named as not-run, never folded in as "found nothing".
3. **The packages are catalog-resolved.** `solicitation_list_packages(projectId)`: every package
   carries a catalog `tradeCode`. A package with none is resolved now (`directory_list_trades`,
   exact `code` first then `query` by name or alias, the id recorded verbatim) or named "no catalog
   trade" in the ledger; readers may only choose trades the catalog knows, since the door checks
   them.
4. **The manual's sections are placed.** The same `solicitation_list_packages` answer carries
   `manualSectionPlacement`. A package review reads only the manual sections its package lists in
   `manualSections`, so a section on no package is a section no review checks. Where
   `onNoPackage` is not empty, the packages were drafted before every section was placed: run
   `learn-project` step 8 sub-step 6 yourself now, placing each listed section on the package that
   buys it, before window 1 starts. Read `manualSectionPlacement.truncated` whatever
   `onNoPackage` holds: when it is true the placement count is incomplete, and close-out says so.
   A section still on `onNoPackage` after that is placing this run did not finish: close-out
   names it with what stopped its placing. Then send one fresh agent to copy the final `solicitation_list_packages` response
   to `<run folder>/plan/packages.json`, byte for byte, returning one line; the plan script reads
   it from there, and you never hold it.

## 3. The read plan, user-approved

The plan for window 1 is written here and approved once; the plans for windows 2 and 3 are written
by the same script at each boundary from what the record then holds, and the check-in before each
window is where the user sees them. A pass is a set of read units read together for one purpose;
a read unit is one sheet.

You never read a sheet row. The grid is fetched to disk by a fresh agent, a script turns it into
counts and into the plan's unit lines, and what you read is the counts and the script's bounds
lines.

1. **Take the set's shape, and nothing else.** `set_grid(projectId, deliveryId, limit: 0)`, with
   the delivery precondition 3 named. That is a summary-only call: metadata, `disciplineCounts`,
   the `delivery` you asked for and `readFrom`, the deliveries its rows come from, and zero rows.
   Read `count` and the discipline distribution off it. These are the only `set_grid` calls the
   run makes, at any set size: this one, taken again only where step 3 sends you back to it
   before the plan is approved, and the fetch agent's paged calls in step 2, sent again where the
   inventory refuses the grid. Never call it for rows yourself, never page it, and never fall back
   to sampled `search` reads for the inventory: whatever you pull that way stays in your context
   for the rest of the run.

   Then write `<run folder>/run.json` in the shape the run folder section shows, off that answer
   and the tag check: each id copied character for character. The inventory refuses a grid whose
   deliveries differ from this file, so a slip costs one more fetch and never a wrong plan. Write
   it again only before the plan is approved: where the inventory refuses the grid because a
   delivery landed since, take this call again, write `run.json` again from it, and fetch again.
   Once `phase: plan approved` is on the ledger it never changes, and the pass reads the sheet list
   it started on.
2. **Send one agent for the grid.** Dispatch a fresh general agent, whose whole job is this and
   which then ends, with the fetch below. It pages the grid, puts it on disk under
   `<run folder>/grid/`, and returns one line. Read that line and nothing else.

   ```text
   run_in_background: false
   Fetch the sheet grid for project <projectId> to disk. This is your whole job. Do nothing else,
   and end when it is done.

   1. Call set_grid(projectId: "<projectId>", deliveryId: "<deliveryId>", limit: 500, offset: 0),
      then again at offset 500, 1000, and so on, until the rows you have seen cover the response's
      own `count`.
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
   you read in step 1 as `--expect-count`. Run it with the Bash tool, single quoted. Resolve
   `${CLAUDE_PLUGIN_ROOT}` here and pass the plugin directory itself: that variable is interpolated
   in this skill but is not set inside a shell call, so the script is handed the directory and
   never the variable. Use `python3`, or `python` on a seat that has only that name.

   ```sh
   python3 '<plugin root>/scripts/plan_inventory.py' inventory \
     --grid '<run folder>/grid' --expect-count <count> --out-dir '<run folder>'
   ```

   It writes `inventory.md` and `inventory.json` into the run folder. A refusal here means the grid
   on disk is not the whole set, or not this pass's sheet list: send the fetch again rather than
   planning off a partial grid, and where the refusal names a delivery `run.json` does not, take
   step 1 again first. Read only its bounds line, which names the drawing issue and the first
   sheet, then read from `inventory.md` only the count tables and the sheet number digest at its
   tail. Never the sheet lines above them. The inventory can list more sheets than the grid's
   `count`: where one number prints on more than one page of the issue, each further page is a
   sheet of its own, and the bounds line names those pages and any page of an earlier issue the
   grid keeps beside a number, which the pass leaves out.

   Then confirm the corpus: `search_set_text(projectId, query: "<the first sheet the inventory's
   bounds line names>", limit: 1)`. A corpus that answers nothing for a sheet number the set
   carries has not been built, and the run stops and hands the delivery back to `drawing-upload`
   for its text read rather than reading page by page without it.
4. **Write the window 1 plan.** Run the plan mode of the same script for window 1. It selects the
   vocabulary sheets by sheet type (schedule, legend, notes, cover and index), groups them into
   passes by discipline, splits a pass over twelve units at the twelve, folds a pass under three
   units into the pass before or after it, and names what it left out and why. Families you want
   read anyway, or left out, go in as `--include` and `--exclude` patterns with a reason each; that
   is where your judgment lives, and it carries no sheet titles and no page numbers. This window
   takes no packages: nothing in it is chosen per trade, and the script refuses that argument in
   one line rather than accepting and ignoring it.

   ```sh
   python3 '<plugin root>/scripts/plan_inventory.py' plan --window 1 \
     --inventory '<run folder>/inventory.json' \
     --out '<run folder>/read-plan.md'
   ```

   It also plans the repeated lines: one unit per drawing file holding five or more of the sheets
   the run reads, in its own pass `RS1`, which never folds, each unit reading that file's repeated
   lines once with `get_page_text` and `repeated: "only"`. Sheets an `--exclude` left out do not
   count toward the five, and since that read covers the whole file, a unit line names its file's
   left-out sheets (`, sheets left out <numbers>`): its reader records nothing from a block printed
   only on them.

   Read back only its bounds line: units, passes, folds, excluded, unassigned, and the repeated
   lines clause, which counts those units apart from the sheets. Each fold reads
   `<part> into <pass>`, and a pass under three that fits beside no other is named as kept. It also
   writes `<run folder>/plan/window-1.json`, the unit keys it selected and the ones it left out,
   which is window 2's input and is what makes every sheet once provable rather than inferred. A
   refusal is a one-line reason and a fix to your arguments, never a reason to write the plan by
   hand. Never open `read-plan.md` yourself; the runners open their own pass.

   Running it again is how a plan changes, and it is safe to run again: it reads the ledger's
   dispatch lines and the unit ids it wrote last time, keeps every id already dispatched on the
   same sheet, numbers what is new after the highest id its discipline's part already carries,
   whichever pass the fold puts that part in, and never hands an id out twice, so the record's own
   `scopeItem:<unit id>-` prefixes stay where they are. Every id carries the unit tag off
   `run.json`, and every window's bounds line names it.

<!-- user-facing -->
Before any reading runs, tell the user, in a few plain sentences, not a table:

- The order: schedules and legends first, by discipline, and the notes each drawing file repeats
  across its sheets, read once, then every sheet once, then each package reviewed on its own
  against what landed, several at a time, in one sentence. No reasons; they know why schedules come before plans.
- What is deliberately left out, by sheet family or number. Say it plainly: anything here will not
  be scoped.
- When the first check-in will be, roughly.
- On a pass on an addendum: you read only the sheets the addendum prints, naming how many, its
  schedules and legends first where it has any, and afterward you review only the packages this
  pass writes rows on.
- Only where precondition 3's line said an earlier pass names no drawing issue: you scoped this
  project before, the earlier run did not record which set it read, and this pass may read a set
  that was already scoped. Name no set for it.
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

A pass on an addendum whose window 1 plan reads `units 0` and plans no repeated lines unit has no
vocabulary of its own to read: its sheets print no schedule, legend, notes or index, and no file
of five of them. Window 1 does not run and no index runs after it. Append
`phase: window 1 skipped` to the ledger and go straight to stage 6 step 1; the plan's approval is
that window's go-ahead.

The reading happens one level down, one runner per pass. The lead does exactly this and holds
nothing else:

1. **Start one runner per pass.** At the window's start, and on every resume once the plan script
   has run again, list the window's passes with one call, single quoted as every script call is:

   ```sh
   python3 '<plugin root>/scripts/lead_pass.py' passes --plan '<run folder>/read-plan.md'
   ```

   It prints two lines per pass: its id with its `units`, `units verified` and `summed` values,
   and its prefixes, the `scopeItem:<unit id>-` of each unit id its plan block carries, in plan
   order, which is what your count call takes when the pass reports. Its last line names the
   passes to dispatch. For each pass to dispatch, dispatch
   a fresh `plumlayer:scope-round-runner` with the runner dispatch below: pointers only, no pass
   brief and no read-plan text. A finished pass, as the windows section above says, is not
   dispatched. Any other is dispatched whole even when it already carries a `pass:` line, as a
   pass is once a replan adds sheets to it, folds a part into it or cuts a sheet it read: its
   runner skips the units already verified, and its new `pass:` line carries the whole pass.
   Passes that share no discipline
   start together, and a folded pass's heading names every discipline it carries; passes the plan
   marks as seeing the same work start one after another. The repeated lines pass, `RS1` and any
   lettered part of it, shares no discipline and starts alongside the vocabulary passes, with the
   same runner dispatch. What a pass leaves in the lead's context is its dispatch, its hand-back
   and its `pass:` line, nothing else.
2. **The runner owns the pass.** It writes the pass brief if it is not already on disk, runs the
   pass's units in reading order (one fresh
   `plumlayer:scope-reader` per unit, one unit at a time), appends each unit's dispatch line
   before that unit starts, verifies every unit with one `verify_unit` call before the next unit
   starts, notes overlaps inside the pass, and appends the ledger in its fixed line shapes. The
   per-unit loop lives in the `scope-round-runner` agent definition and the reader mandates live
   in the `scope-reader` agent definition. Neither is restated here, and neither is ever trimmed.
3. **Take a pass's count when it reports, then record it.** A runner returns one short hand-back
   (shape below) that names the pass's summary file. Read its `unverified:` and `unread:` lines
   first. A pass with a unit on `unverified:` gets no `pass:` line, and the record script refuses
   it. Where that unit reads `mismatch`, the run stops and gets investigated, never papered over.
   Where the `unread:` line names it as stopped answering twice, start no further pass, check in at
   once naming that sheet, and on the go-ahead dispatch that pass again, which starts at that sheet
   and reads the ones after it; once that unit reads verified, the earlier stop is history and
   stops nothing. A unit with no verified line and no such stop is a runner that stopped partway,
   handled as the windows section says.

   Otherwise, before you say a number out loud, take the pass's counts off the record yourself
   with one call, `count_entries(projectId, subjectPrefixes: [<the prefixes on that pass's listing
   line>])`, reading each `entryCount`. That is the third boundary of non-negotiable 5,
   and it is count-only: never a row list, and never a prefix or a count taken off the hand-back.
   Then record the pass, passing the answer's `counts` array through as it came back, single
   quoted:

   ```sh
   python3 '<plugin root>/scripts/lead_pass.py' record '<run folder>/ledger.md' <window> <pass id> \
     --plan '<run folder>/read-plan.md' --counts-json '<the counts array of the answer>'
   ```

   It pairs each count with its unit by its `subjectPrefix`, never by its place in the array, and
   refuses an array whose prefixes are not exactly the pass's, each once, writing nothing. It
   compares your counts unit by unit with the summary file, copies the updated, questions,
   replied and candidates figures off that file, and in window 3 the pages opened and searches off
   its `review:` line, appends the pass's one `pass:` line to the ledger, and prints it, with a
   line under it naming the pass by the sheets it read, or in window 3 the packages it reviewed,
   and its new items, items updated and Questions as the user hears them. Work from those lines
   from then on. A unit it names as above the runner's count carries entries written
   since its runner verified it, by a later write onto its rows, and stops nothing. Exit 3 is a
   mismatch: the record holds fewer entries under a unit's prefix than its runner verified. The
   script wrote nothing and names each such unit with both counts, and the run stops and gets
   investigated, never papered over. Any other refusal names what is wrong with the call: fix the
   call and run it again. The `created` figure on the `pass:` line counts entries, every citation
   and trade written with the new items, and is your own check: say the new items, the items
   updated and the Questions as the line under it gives them, and never the entry count.
<!-- user-facing -->
   Between check-ins, tell the user at most one line per pass as it is recorded, naming what it
   read in plain words: "I've read the fire alarm sheets, 48 new items." Keep the rest for the
   check-in.
<!-- /user-facing -->
4. **Close the window at its boundary.** When every pass of the window has reported and carries
   its `pass:` line, dispatch one more runner with `boundary` in place of the pass id. It scans the
   window's new items for the same work captured by two passes that ran alongside each other,
   declares any kind a reader named and did not declare, and ends. It copies nothing to disk: no
   window plans off the definitions, so a copy of them would be a file with no reader, and a reader
   asks the record. Then append
   `phase: window 1 complete` to the ledger with the window's verified totals,
   and go straight to stage 5: the index runs before the check-in, so the trade pages the user
   opens at the check-in already carry every sheet.

## 5. The citation index

After each of the three windows, and never skipped. It runs after window 1 so every trade's page is
usable at the first check-in, after window 2 so every reviewer works from a record whose rows
already cite every page they appear on, and after window 3 so the rows the reviews created carry
every page too. In a pass on an addendum it runs the index after each window that ran: a window 1
that was skipped has none, and a window 3 that planned no review has none:

1. **Start it.** `index_citations(projectId)`. It walks the corpus for every definition code and
   every item's tag or mark on the record and cites every page each appears on, onto the definition
   and onto the items that resolve to it, as the record's own text match. It writes citations only,
   never a value; an item that already cites a page is not cited there again; a match on a code of
   two characters or fewer, or with no digit and no hyphen between two letters or digits (a code
   that prints as an ordinary word), is left open rather than cited.
2. **Wait for it.** Poll `index_citations_status(projectId)` until its `state` is `succeeded` or
   `failed`, waiting between polls rather than polling back to back. On `succeeded` its `report`
   carries `codesTotal`, `codesMatched`, `citationsWritten` and the rest of the run's counts, and
   `leftoverCounts` carries the true count per kind of what it could not cite, with
   `truncatedKinds` naming the kinds whose rows were cut for size. Read the counts; never the
   pages. `queued` and `stale` are both safe to wait through. Where `wordCodesSetAside` is false,
   the report comes from a pass that ran before codes printing as ordinary words were set aside:
   say so on the `phase: index built` line and in the close-out, since its counts include them.
3. **Keep what it left open as counts.** No agent is dispatched for those rows and nothing is
   paged to disk: `leftoverCounts` is the whole of what the run keeps, and it rides onto the
   ledger's `phase: index built` line at step 4, where the close-out report reads it. The kinds are
   `unmatchedTag`, `codeNoLocation`, `codeOnlyOnReplacedPages`, `codeTooShort`, `codeIsAWord`,
   `fragmentUnresolvable`, `pageNotASheet`, `codeOverCap`, `hitNotDrawable` and `overRunCap`, and
   each is reported by its count alone. The two exceptions are `codeNoLocation` and
   `codeOnlyOnReplacedPages`: where either count is above zero, take one
   `index_citations_leftover(projectId, kind: ...)` read of that kind yourself, so the close out
   can name the codes found nowhere, and the codes a later drawing issue dropped with the earlier
   sheets that printed them. One read returns up to 50 rows; where the count is higher, the close
   out names those 50 and says how many more there are. A row on the record that still names a dropped code is work the
   revision may have taken out; the close out says so. Nothing in the run chases those rows: they
   are what the close-out reports as still open, by count and with those codes named. A tag no
   reader resolved on its own sheet is named as a loss rather than attached by guesswork to
   whichever package it might belong to.
4. Append `phase: index built` to the ledger with the counts off the status. After window 1,
   check in (format below); after window 2 complete, fold the packages first (stage 6 step 5),
   then check in; after window 3 the close out is the next step.

<!-- user-facing -->
At this check-in, name the window you finished and what it covered, then say plainly that every
item and every definition now shows every sheet it appears on, plans included, and that each
trade's page is ready to look at.
<!-- /user-facing -->

## 6. Window 2: every sheet once

On the go-ahead:

1. **Write the window 2 plan.** Run the plan script for window 2. It takes every row of the
   inventory that `plan/window-1.json` does not already name, selected or left out, groups them
   into passes by discipline in inventory order, sorts inside a discipline by sheet type with
   composition ahead of extent, splits a pass over twelve units at the twelve into lettered
   passes, and folds a pass under three units into the pass before or after it, as in window 1. The
   reading order inside a discipline is a constant in the script, never a setting and never a
   judgment made at run time. Read back only its bounds line: sheets, passes, folds, disciplines,
   the sheets by type, and `every sheet once`, which states the units planned against the distinct
   sheets they touch and refuses where the two differ. A user who wants a slice of the window first
   names the sheets and why: `--only` plans that slice and records the rest as deferred, and the
   next plan run without it brings them back and keeps every id already handed out. Read back the
   deferred count with the bounds line. A `plus read earlier <r>` clause counts the sheets an
   earlier slice already read and verified; the deferred count leaves them out, and it is the
   number the paused line's `deferred <m>` carries. This window takes no packages and no kinds; the
   script refuses either in one line.

   A unit line ends with `, repeated lines read in set <version>` where its file's repeated lines
   unit carries a window 1 `verified` line whose last result is `ok`, a `set` note naming the set
   version it read, and no `unread` note: that sheet's reader leaves the file's repeated lines out
   of its page with `repeated: "omit"`, because they were read once already, but only where its
   answer names that same set version, and reads the page whole otherwise. Every other sheet is
   read whole. The bounds line counts the sheets read without
   their file's repeated lines and the files whose repeated lines were read; a file planned in
   window 1 and not read there is one whose sheets are all read whole.

   ```sh
   python3 '<plugin root>/scripts/plan_inventory.py' plan --window 2 \
     --inventory '<run folder>/inventory.json' \
     --window-1 '<run folder>/plan/window-1.json' \
     [--only '<pattern>:<reason>']... \
     --out '<run folder>/read-plan.md'
   ```

2. **Run the passes** exactly as stage 4 runs them: one runner per pass, the runner's
   `verify_unit` per sheet, your one count call, one `pass:` line each, in the plan's order.
   After a slice, the full plan's part that holds the slice's units holds new ones beside them: it shows `units verified` below `units` and is dispatched like any unfinished
   pass, its runner skips the slice's finished units, and its new `pass:` line carries the whole
   part. A plan with no pass, as where window 1 selected or left out every sheet, lists
   `passes 0, finished 0; to dispatch: none`: no runner starts, and the window goes straight to
   step 4. Passes that share no discipline start together, and a folded pass's heading names every
   discipline it carries. Every reader reads its sheet whole, for everything on it, whatever trade
   the work belongs to (non-negotiable 4); the runner's overlap scan and the record's refusal of a
   create whose name the project already carries are what keep two passes running alongside each
   other from creating the same work twice.
3. **Check in every few passes.** After every fourth `pass:` line of the window, check in (format
   below): the sheets read, what landed by trade, what was raised. A pause here is at a pass
   boundary and loses nothing.
4. **Close the window** with a boundary runner, as in stage 4 step 4, then append
   `phase: window 2 complete` with the window's verified totals, run the index (stage 5, steps 1 to
   4) so every row cites every page it appears on before any review reads it, fold the packages
   (step 5), and check in.
   When the plan deferred sheets, the window is not closed. After the slice's passes, run the
   boundary runner and the index the same way, but append
   `phase: window 2 paused units <n> ... deferred <m>` in place of `phase: window 2 complete`: the
   same verified totals the complete line carries, with `deferred <m>` added. The window picks up
   again at step 1, with a plan run without `--only`, and a resume after that line starts there.
   A slice whose bounds line reads `plus deferred 0` is the window's last slice: after its passes,
   run the plan once more without `--only`. Every unit in it shows verified, but that plan can fold
   one slice's part into another's pass, so before you total or close anything, dispatch every pass
   in it that is not finished, as the windows section says and step 2 runs them, each with its own
   `pass:` line: their runners read nothing and write new summaries. Then the window closes from
   that plan with `phase: window 2 complete`, its totals taken over the passes that plan carries.
5. **Fold the packages into what one kind of firm bids.** This runs once the window is complete and
   its index built, never after a paused line, and before the window 3 plan, and it runs one level
   down: dispatch one fresh `plumlayer:scope-package-folder` with the package folder dispatch
   below, mode `fold`, pointers only. How a package is folded, split, moved, or deleted as the
   owner's own work lives in that agent's definition, which appends `phase: packages folded` to
   the ledger as its last step; you hold none of it, and no package list, row or manual page of
   the fold reaches your context. Read back only its hand-back (shape below). A folder that comes
   back with no hand-back stopped partway: dispatch it again, and it keeps every act its report
   already carries. Then gather what the check-in below names about the packages with one call,
   single quoted:

   ```sh
   python3 '<plugin root>/scripts/fold_report.py' print '<run folder>'
   ```

   It prints every line of `reports/fold.md`, one act each under its label, and stops before
   Bash's output limit; where its last line names what it did not print, run the command that
   line gives for the rest. A run whose fold ran before the folder kept a report prints one line
   saying so, and that line is no `deleted:` line, here, at the general requirements step or at
   close-out. What it prints is for you to read: say what it names in the
   estimator's words, and never paste a line as it printed. A later write can make a package for
   the owner's own work again, so before each later check-in and at stage 8, where the report
   carries a `deleted:` line, dispatch the folder again with mode `recheck`, and read back only its
   hand-back.

<!-- user-facing -->
At this check-in, when nothing was deferred, say plainly that every sheet in the set has now been
read, once each, and that nothing was left unread except what was deliberately left out at the
start. Name what landed by trade, say each trade's page carries its items and shows every sheet
each one appears on, and say what comes next in one sentence: each package reviewed on its own
against what landed, several at a time. Name each package you folded into another, with the reason in one sentence, and each
package you split into the ones its subs bid, each package a supplier furnishes with the package
that installs its items, each sealant or firestopping package you kept with the packages whose
work its rows seal or pass through, and that the estimator can keep it or have its rows moved to
those trades, each trade you moved from one package to another, each default you used with the
package that follows it, and that the estimator can change any of them in chat,
and each package you deleted because the owner hires that work, with the manual section or the
sheet and note that says so. Name as the owner's work any of its items a package you kept still covers. Name each package
whose trades or sections changed while the fold was stopped, with what changed. When sheets were deferred, say which sheets were read and what landed from them by trade,
that the rest of the set, <m> sheets, is still waiting, and that the next go-ahead reads it. Never
say every sheet has been read while any is waiting.
<!-- /user-facing -->

## 7. Window 3: one review per package

On the go-ahead:

1. **Write the window 3 plan.** The packages may have changed since window 1: a scope item written
   on a trade with no package makes that trade's package as it lands, so windows 1 and 2 can have
   made packages the plan has not seen. In a pass on a set, first place the general requirements:
   the Division 01 sections are on no package, since orientation places only the sections outside
   Divisions 00 and 01, and what they require still costs money. Read them with one paged
   `search(projectId, subjectPrefix: "specSection:01", predicate: "hasTitle")`. Where the project
   has no Division 01 section, skip this. Otherwise `solicitation_create_package` one package
   named `General requirements` whose `tradeCode` is `01 11 13`, the catalog's General Contractor
   trade, since the catalog carries no general requirements code and this is the estimator's own
   work; whose `manualSections` are every Division 01 section on no package on a fresh
   `solicitation_list_packages`, except forms, so no section sits on two packages, and none where
   every one is placed already; and whose `codes` are those sections' own trades
   (`directory_list_trades(code: <the number spaced as the catalog spaces it>)`, then by its
   title's noun), leaving out each trade the fold deleted as the owner's work and each trade
   another package carries as its `tradeCode` or in its `codes`. The fold's deletes are the
   `deleted:` lines of one `fold_report.py print` call, as stage 6 step 5 gathers them, its
   recheck deletes included; each carries the deleted package's `tradeCode` after `trade` and its
   id after `package`, and the trade to leave out is the one after `trade`, read off the line
   itself. Its `notes` say the
   estimator carries the general costs the Division 01 sections require, so every review puts
   them on this package's `tradeCode`. The package is made even where it holds no section, so an
   estimator cost read on any package has it to land on. A project holds one live package per
   trade, so where one with `tradeCode` `01 11 13` already exists, `solicitation_update_package`
   it instead, sending its `manualSections`, `codes` and `notes` whole with these added, since the
   door replaces each list it is sent. The `hasTitle` read still lists a section whose manual file
   was deleted, and the door holds a list to the sections the record keeps, so it refuses such a
   section by number: take each one it names off and send again. Its review reads its sections
   for their cost. In a pass on an addendum, first move the copy stage 2 made
   to `<run folder>/plan/packages-start.json` with a local command, since stage 8 compares the two.
   Then send one fresh agent to copy a fresh
   `solicitation_list_packages` response over `<run folder>/plan/packages.json`, byte for byte,
   returning one line. Then run the plan script for window 3. It plans one review unit per package
   in `plan/packages.json`, in package order, and puts up to four reviews in each pass, every
   package of one catalog trade in the same pass, one after the other, so no two passes share a
   trade; a trade of more than four packages is a pass of its own. It reads no sheets and takes
   no inventory. Read back only its bounds line: packages,
   reviews, passes, reviews per pass, trades, and the packages sharing a trade.

   In a pass on an addendum, the script reads the pass's own `trades/` files beside the plan and
   plans a review only for a package covering a trade this pass wrote on (its `tradeCode`, a
   trade in its `codes`, or a trade under a broad code of either): a row it created, a row
   that already existed and that it updated or cited, or a Question it raised naming that trade.
   Its bounds line counts the packages it left out, and the read plan names each. Where a unit's
   `verified` line shows a row updated or a Question raised and its reader named no trade it
   touched, which packages the pass wrote on is not known: the plan reviews every package, and its
   bounds line names those units. A pass that
   wrote on no trade plans no review: append `phase: window 3 complete` with zero totals and go to stage 8. The
   reviews of an addendum's pass search only the deliveries its `run.json` reads from, so they find
   what the readers missed on the addendum's own pages without finding the whole set again.

   ```sh
   python3 '<plugin root>/scripts/plan_inventory.py' plan --window 3 \
     --packages '<run folder>/plan/packages.json' \
     --out '<run folder>/read-plan.md'
   ```

2. **Run the reviews** as stage 4 runs its passes, with `review-<pass id>` in place of the pass id,
   so the runner dispatches one `plumlayer:scope-reviewer` per unit in turn rather than a reader.
   The runner's `verify_unit` against the pages each review opened, your one count call over the
   pass's prefixes, one `pass:` line each. No two passes share a trade, so all of them may start
   together.
3. **Check in every few packages.** After every fourth `pass:` line of the window, check in (format
   below): the packages finished, their pages ready, what was raised. A pause here is at a pass
   boundary and loses nothing.

<!-- user-facing -->
At each of these check-ins, name the packages you finished, say their pages are ready to look at,
and name what you raised on them and what you would like them to look at. Name each pair of rows
the reviews found carrying the same work, the row that now carries every sheet and the one left
to retire, and say they retire it on the site or tell you to. Then say which packages come next,
in one sentence. A pause here loses nothing.
<!-- /user-facing -->

4. **Close the window** with a boundary runner, then run the index once more (stage 5, steps 1 to
   4) so the rows the reviews created carry every sheet too, then append
   `phase: window 3 complete` with the window's verified totals and what the third index left
   open, by count and named where it is a code found nowhere.

Spec sections account differently, since estimators never write CSI digit strings into scope
text: a manual section is accounted when a package lists it in `manualSections`. After stage 8's
amendments are applied, read `manualSectionPlacement` off a fresh `solicitation_list_packages`
call, never a local artifact: its `onNoPackage` sections are the manual sections still open,
reported the same way, each with the reason you left it off, and where its `truncated` is true
the count is incomplete and is reported as incomplete.

## 8. Amend the packages

The estimator-judgment stage. Packages are bundles of spec sections grouped by how subcontractors
actually split themselves in the market, not by the book's divisions. The baseline split was
drafted and created at orientation (`learn-project`) and folded into what one kind of firm bids
before the reviews (stage 6 step 5): read it fresh via `solicitation_list_packages(projectId)`
rather than re-drafting it. This stage is for the splits and folds a review surfaces.

In a pass on an addendum this stage runs only where the pass made a package: one whose `id` is in
`plan/packages.json` and in no row of `plan/packages-start.json`, found with a local comparison of
the two. A pass that made none appends `phase: packages amended` with no amendment and goes to
close out; the split the earlier passes settled stands.

1. **Scope-driven amendments.** Where the scope list surfaces what the TOC cannot see (a
   specialty assembly that wants its own bidder, an either-or item probed as an alternate, a
   package that should collapse into another once scale is understood), apply the amendment live:
   `solicitation_create_package` for a genuinely new package, `solicitation_update_package` to
   fold, split, or rename an existing one. A fold here runs the same update-then-delete sequence as
   the package folder's fold mode, in `<plugin root>/agents/scope-package-folder.md`: the keeping
   package takes the folded package's trade, `codes` and
   `manualSections`, then `solicitation_delete_package` removes the folded one, so no two packages
   cover the same work. A trade an item already sits on has its package
   already, so amend that package rather than creating one. Resolve the amendment's trade the same way as
   orientation (`directory_list_trades`, exact `code` first then `query` by name/alias; the
   catalog trade id recorded verbatim, store-resolution, non-negotiable 3), set `codes` to the
   other catalog trades the package now buys (verbatim catalog ids, never repeating the package's
   own `tradeCode`), and set `manualSections` to the manual sections it now buys, by the manual's
   own numbers, with a one-line rationale in `notes` (plain prose, no fixed shape).
   `solicitation_update_package` replaces each list it is sent whole, so a fold or split rewrites
   both lists of every package involved, and a section moved off one package lands on another
   in the same amendment. A package with no reasonable catalog match cannot
   be created or amended into one: name it "no catalog trade, not created" in the report. A fold
   moves no row: the folded trade goes on the keeping package's `codes`, and its rows keep their
   trade. A row is re-homed only where its trade is wrong, to the catalog trade that names its
   work, in one `record_batch` of `belongsToTrade` records, each naming the trade record it
   replaces in `supersedesId` (the id `list_scope_items(full: true)` returns), count-verified, and the move is named
   in the report; never leave a trade that carries rows on no package's `tradeCode` or `codes`,
   except work the owner contracts for directly, which stage 6 step 5 leaves on no package.
<!-- user-facing -->
Show what you did in plain words, mirroring orientation's wording: name the amendments made
   (packages created, split, collapsed, or renamed, and any package for the owner's own work
   deleted again), each with its one-line rationale. Say it as
   what you did, not as a question: "I amended the split: two packages, here's why. Change any of
   them on the site or tell me and I will redo it."
<!-- /user-facing -->
   No approval is collected: the amendment governs as applied and stays editable; a correction is
   a tool call. Once the amendments are applied, append `phase: packages amended` to the ledger.
2. **Empty-baseline case.** When `solicitation_list_packages` returned no packages because the
   project has no spec sections (precondition 5), orientation could draft no split and readers
   named trades off the catalog alone. Every trade an item landed on already has a package under
   its catalog name, made as the item was written, so this stage shapes that split from the
   finished scope list instead of amending a baseline: same bundling logic as orientation, its
   default carries under the same condition included, same catalog resolution,
   `solicitation_update_package` to fold, bundle and rename those packages with the same
   `codes`/`notes` usage, and `solicitation_create_package` only for a package whose trade no item
   carries. Say so plainly in the
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
  assumed items that don't fit this job, each counted by kind and the leading ones named. Name
  each pair of rows the reviews found carrying the same work, the row that now carries every sheet
  and the one left to retire, and say they retire it on the site or tell you to.
  Document defects worth sending to the design team are the open Questions, by the trades they
  name, with the every-trade ones and the not-known-yet ones apart, among them the sections of the manual no sheet shows and the work on the sheets the manual never
  names, and the silences left open for bidders, by count.
- **Trade responsibility to confirm**: how many items sit in more than one trade's package
  (count each item once, however many packages it sits in), the leading trades named, and where
  to review them (the "Trade responsibility to confirm" section in each affected trade's package
  on plumlayer.com).
- **What is still open**: the tags and codes the index could match to nothing, by count, with the
  codes found nowhere named, and said plainly as what it is: those are marks nobody placed on the
  sheet they sit on, and this run did not go back for them. Name apart the codes a later drawing
  issue dropped, each with the earlier sheets that printed it, and say that any scope item still
  naming one is work the revision may have taken out, for you to check. Also the sheets left out of the read
  plan at the start, and the manual sections on no package, each with what stopped its placing,
  or that the count of them is incomplete when it was cut short. Name each manual section a
  review left unread or read only in part, with the reason and the pages left unread. On a pass
  on an addendum, also name the packages you did not review, and say why: this pass wrote no row
  on their trade, so the addendum's sheets changed nothing they price that the readers found.
- **The package split**: the packages folded into another before the reviews, and the amendments
  made this run (created / split / collapsed / renamed), each with its rationale, the packages derived here from scratch only in the no-spec-book case,
  and how many manual sections you placed on a package at the start of the run, if any, and the
  general requirements package with the Division 01 sections it carries.
- **How long it took**: wall-clock from the read plan's approval to this report.
<!-- /user-facing -->

The report is written off the ledger's `pass:` and `phase:` lines, and the `grain`, `same work:`
and `not read:` notes named below, read with a local filter, and the one package read named below,
never off memory and never off the whole file. Everything the report needs is on those lines: the
wall-clock between the first and last of them, the counts, the deviations, and what is still open.
Read them with one filter each and count them locally: the sheet reads are the `dispatch` lines,
the distinct sheets are the sheet numbers on them, the rows created and the items are the `created`
and `items` fields of the `verified` lines, and the candidates, the pages a review re-opened and
the searches it ran are the `candidates`, `pages-opened` and `searches` fields of the `pass:`
lines, the last one of a pass that carries two. The items you weren't sure how finely to split are
the ledger's `note` lines of kind `grain`, in every window, the notes each check-in printed as how
finely to split, each item named once. The pairs of rows carrying the same work are the
window 3 `note` lines of kind `anomaly` that carry `same work:`, each pair named once, and the
manual sections a review left unread or read in part are the window 3 `anomaly` notes that carry
`not read:`, each section named once. What the index left open comes off the
`phase: index built` lines, which carry its counts, and the codes found nowhere and the codes a
later issue dropped are the `codeNoLocation` and `codeOnlyOnReplacedPages` reads the index step
took, the only leftover rows the run holds. The package split's folds, splits, moves and
deletes before the reviews come off one `fold_report.py print` call, as stage 6 step 5 gathers
them, its recheck deletes included. The general requirements package's Division 01
sections come off one fresh `solicitation_get_package` of the package whose `tradeCode` is
`01 11 13`, its id taken from `<run folder>/plan/packages.json` with a local filter. When the
report has been given, append `phase: closed out`.

## The dispatches and the report shapes

Every dispatch carries pointers and nothing else. Whatever is pasted into a dispatch stays in the
dispatcher's context for the rest of the run, so the read plan and the brief values are opened by
the agent that needs them, from the paths it is handed, and the record is read by the agent that
needs it. Every template below names `run_in_background: false` for the session whose Agent tool
takes it, where the call is then the wait, because a headless session stops a background agent
after ten idle minutes. Where the call comes back with an agent id, you wait as the windows section
says, by ending the turn.

The mandates are not in these templates. They live in the four agent definitions the plugin ships
for this run, `scope-round-runner`, `scope-reader`, `scope-reviewer` and `scope-package-folder`,
where each dispatched instance reads them fresh. They are never trimmed there and never restated here: a run that relaxes one reproduces
a measured failure.

The orientation dispatch and its summary are `learn-project`'s own, in its "Running one level
down" section, since every session that starts orientation sends the same one; stage 2 sends it
once, only when it finds orientation needs to run.

**Runner dispatch** (the lead writes this, once per pass and once per window boundary):

```text
subagent_type: plumlayer:scope-round-runner
run_in_background: false
Project: <projectId>. Window: <1, 2, or 3>.
Pass: <pass id, or "review-<pass id>", or "boundary">.
Run folder: <path>. Scripts: <path to the plugin's scripts directory>.
Run your pass as your definition says.
```

The runner's definition owns every path under the run folder: the read plan is always
`<run folder>/read-plan.md`, and the summary file and the hand-back it returns are its own to
write. The `Scripts:` line is the plugin's own scripts directory, the path you already resolved for
your plan script calls: the runner sums its pass with the script that sits there, and a runner
handed no path would have to guess one.

**Package folder dispatch** (the lead writes this, once when window 2 closes with mode `fold`, and
once with mode `recheck` before each later check-in and at stage 8 where the fold report carries a
`deleted:` line):

```text
subagent_type: plumlayer:scope-package-folder
run_in_background: false
Project: <projectId>. Mode: <fold or recheck>.
Run folder: <path>. Plugin root: <path to the plugin directory>.
Run your mode as your definition says.
```

The `Plugin root:` line is the plugin directory you already resolved for your script calls: the
folder reads `learn-project` step 8's default carries there and prints its hand-back with the
script beside yours.

**The package folder's hand-back** is printed by `fold_report.py` and is the whole of what the
fold puts in your context; the acts stay in `reports/fold.md`:

```text
fold: packages <n> before, <n> after
acts: folded <n>, split <n>, moved <n>, deleted <n>, kept <n>
records: candidates sent <n> landed <n>, rows re-homed <n>, questions <n>
phase: packages folded appended
report: <run folder>/reports/fold.md
```

**Reader dispatch** (the runner writes this, once per read unit, in windows 1 and 2):

```text
subagent_type: plumlayer:scope-reader
run_in_background: false
Project: <projectId>. Window: <n>. Pass: <pass id>. Unit: <unit id>.
Reading for: <"the vocabulary", "the sheet", or "the repeated lines">.
Pages: <sheet number + fileId + 1-based pageInPdf, one per page>.
Repeated lines: <"read in set <version>" or "not read">.
Left out: <the sheet numbers on the unit line's "sheets left out", or "none">.
Run folder: <path>. Pass brief: <path to briefs/<pass-id>.md>.
Read your unit as your definition says, write your report to <run folder>/reports/<unit id>.md,
then return it.
```

`Reading for:` is `the repeated lines` on a unit of the repeated lines pass, whose `Pages:` line
then carries the file's `fileId` and the page its unit line names, and whose `Left out:` line
carries the file's left-out sheets. `Repeated lines:` is `read in set <version>` where the unit
line ends with `, repeated lines read in set <version>`, and `not read` on every other unit.

**Reviewer dispatch** (the runner writes this, once per review unit, in window 3):

```text
subagent_type: plumlayer:scope-reviewer
run_in_background: false
Project: <projectId>. Window: 3. Pass: <pass id>. Unit: <unit id>.
Reviewing: <the package's catalog trade id>. Package: <the package id>.
Run folder: <path>. Pass brief: <path to briefs/<pass-id>.md>.
Review your package as your definition says, write your report to
<run folder>/reports/<unit id>.md, then return it.
```

The package's `codes`, `manualSections` and `notes` are not in that dispatch: the reviewer reads
them off the record with `solicitation_get_package`, so the manual sections it checks and the work
the notes put on the package have one source and are the ones the record holds when the review
runs.

**The reader's report** comes back in this shape, counts and named anomalies only:

```text
unit: <unit id>   pass: <pass id>   window: <n>
pages read: <sheet number + pageInPdf, renders taken and the reason for each, one per page>
pages unread: <sheet number + pageInPdf + reason, or "none">
cited sheets: <for the repeated lines, every sheet the unit's rows and citations name, comma separated; otherwise "none">
page citations: <for the repeated lines, subject + fileId + pageInPdf of every update cited to a page with no sheet number, one per line; otherwise "none">
set version: <for the repeated lines, the setVersion the unit's walk ended on; otherwise "none">
created: <n>   updated: <n>   questions raised: <n>   questions replied: <n>
updated subjects: <the subject of every item updated or newly cited, except a row cited only to a Question, or "none">
questions raised ids: <the id of every Question raised, or "none">
questions replied ids: <the id of every Question replied to, or "none">
questions linked: <the id of every Question raised or replied to + the subject of every row it was cited on, one Question per line, or "none">
sent: <n>   landed: <n>   conflicts: <ids and how each resolved, or "none">
trades: <trade id + item count, one per trade; candidates <n>>
trades touched: <the catalog id of every pre-existing row the reader updated or newly cited, and of every trade a Question it raised names, one per line, or "none">
definitions kinds added: <kinds, or "none">
sheet readings written: <sheet number, one per sheet whose reading was recorded, or "none">
anomalies: <one line each, with sheet and page, ending with a comma and where it landed, one of Question <id>, reply <id>, note on <subject>, sheet reading, or run only, the Question named by the full id `ask_question` returned (its `question:` subject), a reply by the id `reply_question` returned, a row by its full subject, never shortened; or "none">
grain questions: <one line each, with sheet and page, or "none">
door-owned suggestions: <one line each, or "none">
```

`cited sheets:` is what the runner verifies a repeated lines unit against, since that unit reads a
file and has no sheet of its own; `page citations:` names the updates it cited to a page with no
sheet number, which no sheet verifies, so the runner finds each back by its subject; and `set
version:` is what the runner puts on the ledger for the window 2 plan to mark that file's sheets by. `created:` is the reader's own item count, not the entries under those items. `updated:` counts
every pre-existing item the reader wrote anything onto, a note, a value, or a citation alike.
`sent:` and `landed:` count every write the reader made for the unit, across every call, not only
its first batch.

The `updated subjects:`, `questions raised ids:` and `questions replied ids:` lines are what let
the runner find those writes back: a create is findable by its `scopeItem:<unit-id>-` prefix, an
update lands on a subject that already existed, a raise on a fresh Question id and a reply on the
id of a Question somebody else raised, and nothing else in the report names them.

**The runner's summary** is written in this shape by the summary script the runner runs, to
`<run folder>/reports/<pass id>.md`, where `lead_pass.py` reads it when you record the pass and
at the check-in; you never read it yourself. `created` is an entry count under each unit's prefix,
never the reader's own item count, which travels separately as `items`. The `review:` line is
window 3's only, the pages opened and the searches run added up over the pass's verified reviews:

```text
window: <n>   pass: <pass id>
units read: <unit ids, in reading order>
per unit: <unit id> created <n> items <n> updated <n> questions <n> replied <n> verified <yes/no>
totals verified: created <n> (entry count under the unit prefixes), items <n> (reader's own item count), updated <n>, questions <n> replied <n>
trades: <trade id + item count, one per trade; candidates <n>>
conflicting rows: <n>, on units <unit ids>, or "none"
overlap notes: <item name + the two units, one per line, or "none">
anomalies: <one line each, with sheet and page, or "none">
unread pages: <sheet + page + reason, one per line, or "none">
grain questions: <one line each, as the report wrote it, or "none">
door-owned suggestions: <one line each, as the report wrote it, or "none">
definitions kinds added: <kinds, or "none">
deviations and repairs: <one line each, or "none">
review: pages opened <n>, searches <n>
ledger: <path>, appended through <last line written>
```

**The runner's hand-back** is what the runner returns to you, printed by the same script, and the
whole of what a pass's report puts in your context. The `review:` line is window 3's only:

```text
window: <n>   pass: <pass id>
units: <n>, verified <k>
unverified: <unit id + mismatch | no verified line, one per line, or "none">
unread: <each unread note verbatim, or "none">
notes: anomalies <n>, overlaps <n>, deviations <n>, kinds <n>
review: pages opened <n>, searches <n>
report: <run folder>/reports/<pass id>.md
```

**The reviewer's report** comes back in this shape, and the summary script reads its
`pages opened:` and `searches:` lines into the summary's `review:` line, which is where the
`pass:` line's two extra fields come from:

```text
unit: <unit id>   package: <package name>   trade: <catalog id>   window: 3
harvested: rows <n>, definition codes <n>, spec sections <n>, aliases <n>
notes read: <each item the package notes name + the row that carries it, created or found, or `shown nowhere`, one per line, or "none">
searches: <n> run, <n> returned nothing
terms too general: <term + its page count, one per line, or "none">
pages opened: <sheet number + fileId + page + the term that sent it + what it did, one per line, or "none">
created: <n>   updated: <n>   questions raised: <n>   questions replied: <n>
updated subjects: <the subject of every row updated or newly cited, except a row cited only to a Question, or "none">
manual updates: <each subject on `updated subjects:` whose writes cite manual pages only + the section code + the page, one per line, or "none">
questions raised ids: <the id of every Question raised, or "none">
questions replied ids: <the id of every Question replied to, or "none">
questions linked: <the id of every Question raised or replied to + the subject of every row it was cited on, one Question per line, or "none">
questions alone: <the id of every Question raised or replied to that no row carries + why, one per line, or "none">
sent: <n>   landed: <n>   conflicts: <ids and how each resolved, or "none">
trades: <trade id + item count, one per trade; candidates <n>>
sheet readings written: <sheet number, one per sheet whose reading was recorded, or "none">
anomalies: <one line each, with sheet and page, ending with a comma and where it landed, one of Question <id>, reply <id>, note on <subject>, sheet reading, or run only, the Question named by the full id `ask_question` returned (its `question:` subject), a reply by the id `reply_question` returned, a row by its full subject, never shortened; or "none">
grain questions: <one line each, naming the grain and the rows, or "none">
silent sections: <section code + the Question id, or `left open` + why it is low cost, + the words searched, one per line, or "none">
unspecified work: <row family + the Question id, or `left open` + why it is low cost, + the words searched, one per line, or "none">
compared: <subject + the sources compared + what you found + how it ended: Question <id>, qualification on <subject>, `agree`, `low cost, not asked`, `closed Question <id>`, `not settled`, or `not reached`, one per line, or "none">
sections not checked: <section code + the reason, one per line, "Part 2 read in part" or "not reached" with the pages left, "Part 2 not found", "manual removed", "the owner's work", "no manual sections on this package", "the manual was not read in", or "none">
families not checked: <row family, one per line, or "none">
door-owned suggestions: <one line each, or "none">
```

A boundary runner returns this shape instead:

```text
window: <n>   pass: boundary
cross-pass overlaps: <item name + the two units, one per line, or "none">
kinds declared: <n>
ledger: <path>, appended through <last line written>
```

## The check-in (what the user sees)

Gather a check-in with two calls, and nothing else for it. The first covers the passes recorded
since the last check-in:

```sh
python3 '<plugin root>/scripts/lead_pass.py' checkin '<run folder>' <window> --passes <pass id>,<pass id>
```

It prints each pass by the sheets it read, or in window 3 the packages it reviewed, with its new
items, items updated, Questions raised, replies and new items with a candidate trade, then those
figures over all the passes, then your own check apart, the units and the entry count off your
`pass:` lines, which you never say. Then the items by trade summed off their
summaries' `trades:` lines, and the anomalies already on the record as counts: each anomaly line
ends with where it landed, and one that ends `Question <id>`, `reply <id>` or `note on <subject>`
is counted on an `on the record:` line, one per pass, or in window 3 one per review naming its
package and trade, with one more line over them all. Then it prints every other note line of those
summaries, each copied whole under its pass, less the unit id it opens with, under a label in the
estimator's words: every anomaly that landed nowhere on a trade's page
(`sheet reading`, `run only`, or an ending it cannot read), every pair of rows carrying the same
work wherever its sentence landed, and every overlap, unread page, grain question, door-owned
suggestion, definitions kind and deviation line. A sheet reading is on the record and on no
trade's page, so it is named in full. It stops before Bash's output limit, cutting a note too
long for one call where the call's room ends and naming where, and where its last line names what
it did not print, run the command that line gives for the rest. What it prints is for you to read:
say what it names in the estimator's words, as the next section names them, and never paste a
note or a label as it printed. The second is `list_questions(projectId, limit: 0)`,
whose `tradeCounts`, `everyTradeCount` and `untradedCount` give the project's Questions by the
trades they name, the every-trade ones and the not-known-yet ones, with no rows to page through.

<!-- user-facing -->
At each check-in, name the window, or the packages, you finished and what they covered, then cover,
in plain sentences:

- What you read and what landed: sheets read, items added, items updated, by trade, and what you
  raised as Questions, by the trades they name, with the every-trade ones and the not-known-yet
  ones counted apart. The counts the check-in prints, never the ones reported up to you.
- What you would like them to look at now: each document defect and anomaly that is not on a
  Question or a row yet, with its sheet reference, the items you weren't sure how finely to split,
  and what is theirs to decide. Give the ones already on a Question or a row as a count, and say
  where to see them: each trade's page on plumlayer.com.
- What is defined now that wasn't before, and anything the next window depends on.
- Anything that went sideways: a count that didn't match and how you fixed it, a page you couldn't
  read, a pass that stopped. Say it plainly. A sheet whose reading stopped partway is named with
  what happened to it: "Reading A-5.01 stopped partway, so I read it again from the start and it
  finished", or, where it stopped twice, "Reading A-5.01 stopped partway twice, so I stopped there.
  Everything before it is in. Go ahead and I'll try that sheet again."
- What comes next in one sentence, what it will leave out, and the ask: proceed, adjust, or pause.
  A pause here loses nothing; the run picks up where it stopped.

For example: "I've finished the first window, the schedules and legends. Here is what landed by
trade, what I'd like you to look at, and what the next window reads. Proceed, adjust, or pause?"
<!-- /user-facing -->

When the user answers a check-in, append its one `checkin:` line to the ledger, in the shape the
run folder section gives: `go` once every change they asked for at that check-in is made and the
next step is about to start, or `pause` where they stop the run there. A session that starts
later reads that line and never shows that check-in again. The read plan's check-in is recorded
by `phase: plan approved` instead.

## The words the user reads

Everything you say to the user, at a check-in, between passes, at the close-out or anywhere else
in the run, names things the way an estimator does. The scripts, the ledger, the reports and the
record name them by id. Those ids stay in the run's files and in what only the agents read, and
you never say one. For each kind:

| The run's own name | What you say |
|---|---|
| A pass id (`A2a`, `i1-E2c`, `i1-W3-4`) | What it read, as the line under its `pass:` line and the check-in give it: "the fire alarm sheets", "the first architectural sheets, the A3 sections and the A6 roof details", or the packages it reviewed, by name. |
| A unit or a review | The sheet ("E1.02"), the drawing file's repeated notes, or the package. |
| A scope row's id or subject (`i1-H2a-1-8`, `scopeItem:...`) | The item by its name and its sheet: "the corridor light tags on E1.02". Where a note gives a row by its subject alone, take its name with one `search(projectId, subject: "<subject>", predicate: "name")` first. |
| A Question's id, whole or cut short ("Question 39ed216b") | The Question by its title: "the Question on the stormwater structure". Where a note gives the id alone, take the title off its `question` entry with one `search(projectId, subject: "<the full id>", predicate: "question")` first. |
| A reply's id (`clm-...`) | The reply on the Question it answers, by that Question's title. |
| `created`, an entry, an entry count | Nothing. Count items: "285 new items", "69 items updated". |
| A trade's catalog code alone (`28 30 00`) | The trade's name, its code after it where it helps: "fire alarm (28 30 00)". |
| The runner, a reader, a reviewer, the package folder, a dispatch, a hand-back | "I": "I read the fire alarm sheets", "I folded fences and gates into Landscape". |
| The ledger, a report, the read plan, a summary, a brief, the run folder, a file path | Nothing; say what it holds: "I noted it for the end of the run". |
| A prefix, a unit tag, a rollup, the grain | Nothing: "the items those sheets added", "the full item list", "how finely to split". |
| A field, a definition kind or a verb (`lateldepth`, `feederSymbol`, `notesInternal`, `list_scope_items`) | What it holds or does: "two misspelled lintel depth entries on the CMU lintel definitions", "the item's internal note", "a full list of the items". |

When you say who put something on the record, a row, a note or a Question the run wrote, it is
the user's work, credited to them, and you never name an agent as its author ("by the agent's
judgment", "the reader put it on"). What you chose on your own reading, you say as your own
choice: "I put it on Plumbing; move it if it belongs elsewhere."

## What this skill does not do

- **Upload or recognize drawings** (`drawing-upload`), **create projects** (`project-setup`),
  **read sub proposals** (`bid-intake`), **place takeoff measurements** (`takeoff`), **get the
  invitations ready** (`prepare-invitations`, which does not wait for this run), **draft the
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
- **Manage the user's session or context**: the run is bounded by its own structure. Each pass,
  each read unit and each review runs in a fresh agent that ends when it has reported, so nothing
  accumulates and there is nothing for the user to manage.
- **Run unattended**: check-ins are load-bearing until the user has enough cold runs
  behind them to decide otherwise, and that is their decision to make out loud, per run, never
  this skill's default.

## What this skill never runs

Do not restore or run per-trade fan-out / reconcile-by-overlap machinery as a scope path, and never
present it as current: every pass writes onto the one shared list against the live record, and
nothing is reconciled afterward. Do not restore rounds, legs, or the completeness accounting as
stages; the index and the reviews are what replaced them. Do not restore a window that reads
sheets for one trade: the set is read once, sheet by sheet, and a package is reached through its
review.
