---
name: scope-run
description: >
  Read a Plumlayer project's drawing set into one grounded, cited scope list, every item on its
  trade, in three windows: the vocabulary, then every sheet once, then one review per bid package.
  Trigger on "scope this set", "/scope-run". Runs on its own from the read plan to a closing
  report, and stops only where the user has to act. Drives the project record's read and write
  verbs and the citation index.
  Does not upload drawings (drawing-upload), orient from scratch or draft the baseline package
  split (learn-project), read sub proposals (bid-intake), or place takeoff measurements (takeoff).
---

# Scope run

## What this is

The production scope run: it reads the set in three windows, each of which leaves the project
record whole at its own depth, and it ends with a closing report. Orientation is the
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
   item's tag on every page of the set and cites those pages onto the items and definitions, on an
   item as pages that only show its work. After this window every trade's page is usable.
2. **Every sheet.** Every sheet the first window did not read, once each, grouped into passes by
   discipline and read composition before extent: sections and details ahead of plans, because the
   sheet showing what an assembly is made of writes the better row, and the plan that calls it out
   then cites that row as a page that only shows its work rather than creating a coarser
   duplicate beside it. A reader reads its
   sheet whole, for everything on it, whatever trade the work belongs to. This is where the scope
   is, and it is
   the bulk of the run: quantities where the set states them, the splits the vocabulary read was
   too coarse for, the Questions that clear the bar for an RFI. When the window closes the index
   runs again, so the record holds every page each row appears on before a review reads it, and
   each row's reference list holds the pages that define it.
3. **The reviews.** One review per bid package, read off the record rather than off the set: the
   package's own rows and the rows a role puts on it, the definition codes that resolve to it, the manual sections
   it lists in `manualSections`, and its catalog name and aliases. Those are the words the review searches the
   set's text for, and a hit no row carries becomes a row, cited to a page the reviewer opened for
   it. The same review finds where the manual and the drawings are silent on each other: a
   section on the package whose work no sheet shows, and work on the package's rows that no page
   of the manual names. A section none of whose work any sheet shows, after a search for its
   number and the tags a material key, legend or schedule gives it, is a Question asking the design
   team to confirm the work is not required, cited to the start of the section and on a row for
   each piece of work the section requires, with no value, so the Question shows on the trade's page. One product of a section whose other
   work the sheets show raises nothing, since bidders price what the sheets place, while a
   requirement a section puts on the work the sheets show, each piping system it insulates or the
   finish level of the board drawn, is scope however few sheets draw it, on the row of the work it
   falls on, or on a row of its own where it falls on part of that work. Work the manual
   never names is a Question, cited to a box around the callout. Each clears the Question bar
   below first, and every one that clears it is raised. A package's page is finished when its review is.

The estimator can stop a run at any pass boundary, and it resumes later with nothing lost.

A run is one pass over one drawing issue. A project goes through several sets before it is built,
and each new set gets a full pass of its own over every sheet it prints, the way a new project
does, read against the record the earlier passes built: readers update the rows the door names,
reply to the open Questions, and cite the new set's pages. The pass on the latest set also reads
every sheet that set keeps from an earlier delivery, a whole discipline it does not reissue among
them, each marked `keptFrom` with the delivery it came from, so its readers see the older drawings
beside the newer ones. A pass underway is never interrupted by
a later delivery; it finishes the issue it started on, and the later one waits for a pass of its
own. Whether a delivery is a set or an addendum is the `issue` that `list_drawing_deliveries`
gives it, never a question for the user.

An addendum that lands after its set's pass gets a partial pass over the sheets it prints, and
nothing else: window 1 over its schedules, legends and notes, so a revised schedule is read before
the plans that call it, and window 2 over the rest of its sheets, with the index after each window
that ran, then window 3 over only the packages this pass wrote rows on. The stages below say where
a pass on an addendum differs; everywhere else it runs as a set's pass does.

**The run goes to its end on its own.** It shows the read plan, starts reading in the same turn,
and goes from the first window to the closing report with no answer to wait for. It stops only
where the estimator has to do something for it to go on, each stop with a plain message saying
what, as the stops section below says, and nothing else stops it. The package split is not a stop:
this run reads the baseline packages orientation created, amends them as the scope list surfaces
what the spec TOC could not see, and names what it did in the closing report; they stay editable,
and a correction is a change on the site or a tool call.

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
   not already cite and never re-cites a page the item already carries, except a page the item
   holds only as one that shows its work, which the reader cites again where that page defines
   the work. The record holds every page a row appears on, and the row's reference list is the
   pages that define it: a citation on a row that exists says which kind it is, as the reader's
   mandate 1 says.
   A manual-grounded record cites its spec section the way a drawing-grounded one cites its
   sheet, with the section number, the file and the page read: in `source` on a new row's
   entries, and as a `kind: "spec-section"` citation on any row, a new row in the batch that
   creates it, in the two shapes the reader's mandate 2 gives. The section is what the estimator reads; the page is where the app opens
   it. Never a bare document page for a manual whose section is known.
2. **Create / update / question against the live list.** Every reader holds the current scope list
   for its trade or content families as match-or-create context: for each thing seen, create a new
   item, update an existing one (a new citation, a corrected value, a resolved cross-reference), or raise a
   Question, with a title and a citation. A Question is what clears the bar in the reader's
   mandate 1, a draft RFI. Never a
   parallel list, never a re-create of what exists, never silent skipping of what's already
   listed. The record refuses a create whose name the project already carries, on any trade and
   under any category, and names the row that holds it: work another trade's pass already captured
   is updated, never created again, and the reader turns that refusal into an update on the named
   row and sends again, except where the named row is different work on another trade, which
   takes a name saying how it differs, and except an exclusion row, whose name ends with who carries the
   work, so it shares no name with the row that carries it, as the reader's mandate 1 says. Before raising a Question, read every Question on the project, closed
   ones included: `list_questions` with `status: "all"` and no trade filter, paged until it comes
   back whole. A trade filter drops the Questions that name other trades and the ones still at not
   known yet, and the reader's own page read carries only the open ones on its own trades. A
   manual part, and a review on a project of more than 40 Questions, read them another way, since
   the whole list is more than they can hold: by the package's trades, by each section read and
   by a sheet the ask cites, and by a search of the Questions for what the ask turns on, as their
   definitions say. Where an
   open one already covers the same ask, reply to it instead of
   asking it a second time; a closed one is never asked again. A Question is about the project,
   never about a Plumlayer failure; a read or write that fails is reported and handled in the run's
   own failure path, not raised as a Question. Question text is plain estimator words, and every
   Question meets the standard the `ask_question` verb states: a title, a citation for every place
   it names, and only what is worth the design team's time. Its first sentence is the ask, written
   as the answer to confirm where the set points to one ("Please confirm X and not Y") or as the
   value to provide where it does not, and it asks one thing; finds share a Question only where one
   answer settles them all. It gives only the values that conflict, each in plain words and never as the set's words copied out in quotation marks, one short line per source where
   three or more disagree, and leaves to its citations what they show, with no recital of a
   section's contents; it names each item once, in the words the cited sheet uses, with no clause
   re-describing what that sheet shows or where the item is; a sentence names at most three tags,
   only the ones with the problem; a parenthesis holds a short qualifier, never a sentence; every
   sheet it names is one of its citations, boxed on the entry it names there, and cited as the whole
   sheet only where the point is that the sheet lacks it or no line of the page's read carries the
   entry; a sheet the set lacks is cited at the spot that names it; and it carries no colon without
   the list it announces, no sentence repeating the title, and no sentence on why we need the
   answer. Every Question
   raised or replied to, by a
   reader, a reviewer or this run
   itself, is
   cited on each live row its answer would change, as the reader's mandate 1 decides those rows, so
   the estimator sees it on the trade's scope page, and it never carries an assumption, a value or a
   basis to price to: what to carry until it is answered is the estimator's call.
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
   back. Where the reader cannot tell which of two or more trades owns the work, it puts the row on
   the one trade most likely to carry it, writes nothing on the row about the other, and keeps
   moving. The record door refuses a new scope item with no trade, and refuses a trade the catalog does
   not carry, on `belongsToTrade` and inside `packageRole:<trade>` alike. `record_batch` is atomic
   and order free, so the trade rides in the same batch as the name; `record` carries one entry, so
   there the trade entry is written first. Work the paper says is by others is an exclusion row, and
   a trade's own general costs are general requirement rows, and an alternate the set names is a
   row of its own marked as an alternate, as the reader's mandate 4 says.
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
6. **Grain.** A row is the largest piece of work a bidder answers with one yes or no, written as
   one line on the trade's scope sheet, and a reader settles its rows before it writes one,
   holding each piece of work against three tests in this order, as the reader's mandate 6 says
   in full. One row where things differ only in size, capacity, model, finish, mounting or place,
   named for the kind ("Exhaust fans") with every code written out in its description; equipment
   that works as one system and that one sub buys together is one row for the system; and the
   hardware or the accessories a schedule lists together for one kind of door or room and one
   supplier furnishes as a group are one row for the group, named for it and its place ("Door
   hardware", "Unit bathroom accessories") with what it holds in its description, and a row
   each where the schedule lists the group apart for the units and for the common areas. Work
   made to order for its place, which the documents detail for the one place it goes (a steel
   frame, a canopy, a stair, a piece of millwork), is a row for each piece, named for what it is
   and where it stands, one row however many plans and levels show it and one row for pieces
   made alike at several places; a product put in many places is never split this way. No row
   for the parts every bid that carries a row carries with it, and a typical detail or a general
   note is a citation on the row it details or governs. A row of its own where bids on the trade
   carry the rest and leave this out or price it apart, for one of five reasons: a different kind
   of thing, one whose count and specification a bid is checked on by itself, a difference in
   what a thing is made of or how it is built among them and a group never split this way; a
   version of the work under a requirement the rest is not under; work another trade could carry;
   work bidders often leave out or qualify; or a separate price the set asks for. A variant, a
   group or a part is a row of its own only by the second to the fifth reason, and where the tests leave one row or two open, it is two where bidders on
   the trade do in practice carry one and leave out or qualify the other. Instances are
   never rows: one towel bar
   TA-04 in twenty bathrooms is one row, and neither are the levels, floors or plans that show it;
   where the set states how many there are, that figure is its quantity, and a count the run
   makes of them never is. One product is two rows only where the
   drawings or the manual separate its supply from its install, on a finish trade by area, or
   where one trade leaves out work another trade carries, which takes an exclusion row beside the
   carrying row, or where those tests make it two rows, as the reader's mandates 1 and 6 say. A schedule of places, such as a room finish schedule or a door schedule,
   is read for the products and types it calls for ("Luxury vinyl tile flooring, LVT"), never
   one row for the whole schedule. A schedule of one assembly's types that differ only in size or
   spacing (shear walls, footings, lintels) stays one row for the assembly, with every code
   written out in its description. Windows and doors are never such an assembly: the reader's
   mandate 6 lists how
   each common schedule of types lands on every run, a row per window type and per balcony door
   type beside the rows for the window work every type shares, and one row per family, every code
   written out in its description, for interior doors, partitions and panelboards. Never copy a schedule's columns into a row: the row names its product and cites
   the schedule row that defines it, with a box on that schedule row built from the page's text
   read, never from a render, or the sheet with no box where no line of the read carries that
   row, named on the reader's `anomalies:` line. A row is never a whole sheet
   and never a package header, and a row whose only fitting name is its trade's, its package's
   or a whole manual section's holds more than one piece of work and is written as a row for
   each, while a name the tests give a kind, a group, a family or a system is never such a
   name. A general note that states only the standards a trade's work meets makes no row. Where the reader or the reviewer cannot tell how finely the work in
   front of it splits, and neither the set nor a rule of its mandates settles it, it creates at best
   judgment and names it on its `grain questions:` report line, which the closing report carries
   to the user; how finely our own scope sheet splits is ours to settle, and nobody on
   the design team answers it. Recall never drops to grain uncertainty.
7. **The vocabulary, then every sheet, then the reviews.** A window 2 pass reads only after the
   vocabulary is recorded and indexed; a review reads only after every sheet has been read and
   indexed. Inside window 3, two packages carrying the same catalog trade run one after the other,
   never at once. The read plan encodes this order.
8. **The vocabulary window covers the scope the schedules themselves ground.** The passes reading
   legends and schedules record what a mark means, and they also own the scope items the
   schedules ground, on their trades.
9. **Run, or stop and report; never create a consent step.** The run stops only at the stops the
   section below names, each with what the estimator has to do. Everything else the run does is
   its own work, recorded with who did it and when, and editable afterward. Never stop to collect approval for a course you have
   already chosen, and never offer a recommended yes: if something is genuinely wrong, stop, say
   what is wrong, and hand it over; if nothing is wrong, proceed and say what you did.
10. **The index runs three times, and what it left open is named.** The citation index is a
    standing step after each of the three windows, never optional; in a pass on an addendum, it
    runs after each window that ran. Nothing chases what it left
    open: a tag no reader could resolve on its own sheet is reported in the closing report, by count and
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
their words, one item per call; a row you merely suspect is wrong goes in the report. An approved
recheck plan, which retires the rows the new delivery removed, is that ask: the recheck's retire
step puts the words the user approved the plan with in `basis`, and nothing else it retires.
Starting the scope run is that ask for one more act, as the first message tells the user: a
package review retires the other row of two rows on its package that carry the same work, once
the kept row cites every page the other did that is not marked `shownOnly`, and every manual page,
with `The scope run you started has each package review combine rows that carry the same work.`
in `basis`, and names the pair for the closing report. Where the user asks for a combined row back, `restore_scope_item` puts it back:
name the row you restored.

## The scope item row

A newly created scope item is a full row, not a name. Every new item writes:

- **name** (required): the short line an estimator writes on a scope sheet, so one reading a
  package's names top to bottom takes each in at a glance: the work, the way a sub would say it,
  and at most one qualifier, the kind, the material or the place, only where it tells the row
  apart from the row beside it or changes the price, read off a page the row cites ("Repoint
  brick masonry at facade", "Install lintels above CMU openings", "Moisture resistant gypsum
  board ceilings at unit baths"). About six words is usual and ten the most, never past
  the door's 80 characters. Sizes, capacities, makers, model numbers and lists of
  tags go in the description, and bar sizes are left to the citation; a size or a tag is in the
  name only where it alone tells two rows
  apart, and the title of the sheet the work was read on is never a place.
- **category** (required): the heading the row sits under on its trade's scope sheet, in Title Case,
  with a, an, and, as, at, by, for, from, in, into, of, on, or, the, to and with lowercase after the
  first word. On a structure, envelope, site or MEP trade it names the kind of work or the system
  the row is part of, the way a sub groups his own scope ("Foundations", "Slabs and Flatwork",
  "Piping", "Fixtures", "Equipment", "Fire Alarm", "Low Voltage"). On a finish trade (flooring,
  tile, painting and wall coverings, acoustical ceilings, toilet accessories, casework, countertops,
  appliances, window treatments and finish carpentry) it names the area the row is in where the job
  has more than one, in the job's own words for it off the finish schedule or the plans ("Units",
  "Common Area", "Amenity", "Back of House"), and otherwise the kind of work ("Toilet Accessories",
  "Medicine Cabinets", "Postal Specialties", "Kitchen Casework", "Countertops", "Resilient
  Flooring", "Floor Prep and Underlayment"). For a row whose home is the general requirements
  package's trade, `01 11 13`, it is one of seven, written exactly so, in this order: `Utilities`, `Field Office`,
  `Temporary Services Equipment/Rental`, `Labor`, `Waste Removal Cleaning`, `Site Logistics`,
  `Miscellaneous`, the last only for a row that fits none of the other six, as the reader's
  mandate 5 maps each kind of cost to one; that package's headings take this order, never the
  way the work is built, each heading only where a home row goes under it.
  No heading, package name or row says General Conditions. A phase or
  building heading only where the drawings or
  the manual separate the work by phase or by building; a product used in two buildings is
  otherwise one row under one heading. Never the sheet, room or drawing it was read on, never
  another trade's name, never a heading for specifications, products or references, and never two
  unrelated kinds of work joined into one heading. Every row under one heading sits on the same
  trade. Take a heading from the page's context read where its rows are the same kind of work, or in
  the same area, as yours. The door refuses a heading
  that is one of the record's internal names, read in any casing and with a hyphen or underscore
  as a space, such as `scope`, `trade boundary`, `trade convention`, `convention`, `boundary`,
  `candidate`, `claim`, `contested`, `ambiguity`, `register`, `kind`, `family`,
  `uncategorized`, `other`, `misc` or `tbd`; and it refuses a heading that is a lowercase token
  joined by hyphens or underscores with no spaces (`metal-studs`, `toilet_accessories`); write a
  short heading an estimator would put on a scope sheet, naming the class of work, spelled out
  with spaces. The review surface groups by this: an uncategorized list renders as a wall.
- **trade** (required), recorded as `belongsToTrade`: the catalog trade that names the work as
  the firm that installs it, the finest such trade the catalog carries. Where the manual specifies
  the work in a numbered section, use the catalog trade for that section. Otherwise use the trade
  whose catalog name, not an alias, says what the item is, found with
  `directory_list_trades(query: <the item's own noun>)`. A trade whose name names only a supplier,
  a material supply or a rep holds only an item bought furnish-only, and a trade whose name names
  the work as well as its supplier names the work only where no trade names that work alone.
  Where the catalog's only trade for an item that is not bought furnish-only names its supplier or
  rep, the item takes the `tradeCode` of the package whose firm installs it, or the catalog trade
  that names that firm's work where no package holds it yet.
  Never the trade a sheet's title names, never a trade because its package happens to
  exist, except work a package's `notes` say it installs or carries, which takes the package's
  `tradeCode`, never `01 11 13` because no package fits. Which sub bids the work is the package's
  business, settled when the run folds packages before the reviews (stage 6 step 5). It is the
  catalog id copied verbatim, exactly as the catalog prints it, spaces and all (`09 21 16`).
  Never a word for the trade, so `drywall` is refused, and never a
  respelling of the code either, so `09-21-16` and `092116` are refused too, with a hint naming the
  exact id. Where the work straddles trades, the one trade most
  likely to carry it goes here, the row under the heading it takes on that trade's package, and
  nothing on the row names the other trade, as the reader's mandate 4 says; no record puts the row
  on a second package for that doubt. A
  `packageRole:<trade>` record puts a row in one section of its own trade's package, on that
  row's own trade: the run writes its value as an object holding a `role` alone, and
  `{ retracted: true, reason? }` is the only other value the door takes. The run writes
  `exclusion` on the exclusion row of work the paper says is by others, and `general-requirement`
  for a trade's own general costs, and the reviews write both for the standard lines; and
  `ve-alternate` on the row of each alternate the set names, as the reader's mandate 4 says. A
  bare word is refused and the batch is atomic,
  so it costs every entry in the batch.
  The `<trade>` in that predicate is the same catalog code, and the door reads it there too.
- **description**: the detail a bidder prices that the name leaves out, written wherever the row
  has any: the tags or codes the row covers, the sizes, thicknesses or capacities that tell its
  types apart, the maker and model where the set names one, the product or method, the extent or
  limits, a rated or special condition, each with a page the row cites showing where it comes
  from. Short phrases an estimator would write, sizes as the drawing prints them, about thirty
  words the most, not counting the codes the row names. A row whose name says all a bidder prices
  has none, and so does an exclusion row, whose name ends with who carries the work, as the
  reader's mandate 4 says. Never a detail the name already shows, except for a finish's
  whole extent that the name cannot hold, the reader's mandate 1's two products in a disagreement,
  an allowance's amount and what it covers, an assembly's full code list, or a row whose name is
  fixed by its kind (a grouped requirement row or a standard line), which carries in its description
  the products, sections, amounts and the job's own words its mandate lists, whole, an exclusion
  row aside; never a spec
  article number, a schedule's columns copied out whole or a tag the row is not for, since the
  citation carries them. The description says the work in plain words of the reader's own: never
  a note or a schedule line copied out or set in quotation marks, never the sheet, detail, note
  or section the words are printed on, and never a pointer to another page, since the estimator
  opens the citation and reads the place itself. Two rows still name a source: a row two places
  disagree about names each product with the sheet or section that calls for it, and a row a
  package review writes for several sections at once, such as its mockups, names each section
  it covers.
  On a finish row the extent is the rooms or
  room types the room finish schedule lists it in ("Unit kitchens and baths", "Corridors, levels 2
  to 5"), read off the finish schedule and never off a material key or legend alone, which says
  what a finish is and not where it goes, except where the key's entry names the rooms it goes in
  ("unit bathrooms, east building"). The extent ends the name where it fits ("Porcelain floor
  tile PT-1, unit kitchens and baths"); where the schedule lists more rooms than the name holds,
  the name names the finish alone and the description carries the whole extent, never cut short.
  The reader's mandate 1 names the two products of a disagreement in the description, and a
  fixed-name row carries its whole list there; both run past the sentence and word limits, within
  the field's 400 characters. The citation
  points at the sheet, and the doctrine is cite, don't rewrite: never transcribe a schedule's
  columns, the detail, or the bar sizes into the row. How a schedule becomes rows is
  non-negotiable 6.
- **notesInternal**: the row's note, one estimator's word to the next about buying out the
  row, read in the Notes column. An agent of the run writes `notesInternal` only by the NOTES
  rule of the reader's mandate 5: the note rests on what this job's documents show or leave
  out, tells the estimator what the row does not, and is one he would act on. Most rows take
  none.
- **notesExternal**: the estimator's own note to bidders. No agent of the run writes
  `notesExternal`, on any row, in any case. A note already on a row, in either field, is never
  written over, added to or moved to another row. Work by others and an alternate
  are each a row of their own, as the reader's mandate 4 says; a Question a row waits on is cited
  on it; a conflict between two documents is a Question where it clears the Question bar below
  and nothing on the row where it does not; and a correction of a value on the record is the
  write onto that field naming what it replaces (`supersedesId`), cited to a box around what shows
  the right value with the words read there as the evidence snippet, and nothing more. A
  correction is never a Question.
- **quantity**: only where a schedule, a table, a note or the manual states the count, area or
  length of exactly the row's work, as `{value, unit}`, its evidence boxing the words that print
  the figure, as the reader's mandate 5 says. Never a count or measurement the run makes off a
  plan, which is takeoff. Where two pages state different figures, it is a Question, and no figure
  is chosen between them until the answer comes, except where a sheet kept from an earlier delivery
  and a newer sheet state them: there the newer sheet's figure goes on the row, as the reader's
  mandate 5 says.
- **mark** (optional): the tag a drawing prints for this one item's product or type (`A1`,
  `IW.A`, `TA-07`), copied as printed with no word such as Type or Mark in front, at most 24
  characters, and cited with a box around the schedule row, legend line or plan tag it was read
  from. Only where a drawing tags the item itself: a row carrying several codes, or none, has no
  mark, and a mark is never taken out of the row's name or made up. The tag stays in the name or
  description as the name rule above and non-negotiable 6 write it. A mark on the record that a
  sheet shows misread is corrected like any other value; two drawings tagging one item
  differently is a Question only where the two tags define different work and clear the bar.

A row's text never carries another item's subject id or a hand-written SUPERSEDED or date tag,
per docs/plugin-text-style.md. Splitting one item into two is `retire_scope_item` naming why, plus
a fresh CREATE for each half, never a tag written into the description.

Recorded text is what the bidder reads: plain sentences, no em dashes, no bolding, never a
sheet-by-sheet narration. The door refuses text over its bound (`name` 80 characters, `mark` 24,
`category` 60, `description` 400); a row shaped by these rules
never comes near them. A verbose row is a defect, not diligence.

## The Question bar

A Question is a draft RFI, and it meets the standard the `ask_question` verb states. What this
run adds to that standard is where it applies here. A Question clears the bar when the documents
disagree about a work requirement, or leave open a requirement or a pricing basis a bidder needs,
and nothing in the set settles it, and the run raises each one it finds, however many. Unequal
words alone are not a disagreement: the two places must ask for different work. These clear it:
two documents naming different products, sizes or extents for one assembly with no third
document settling them, two options the set defines and places neither, a dimension the sheets
contradict, a tag the set defines nowhere or a product a schedule leaves TBD, a rock elevation above
the excavation where neither the sheets nor the manual say how its removal is paid (unclassified
excavation, a unit price, an allowance). Rock or water above an excavation is a row either way.
On a schematic or design development set, a tag missing from a schedule, a blank schedule cell, a
keynote with no text, a detail titled and not drawn, or a sheet not yet issued is the set still
being drawn and raises no Question, unless the item cannot be priced at all without the answer
and the answer moves the price materially: a deliberate exception to the bar above, since the
next issue fills in what a set still being drawn leaves open. A
follow-up reply adds sources and never argues which document governs. It does
not clear the bar:

- when the answer is elsewhere in the set or the manual, on a sheet the run has not read among
  them: `search_set_text` first, across the drawings and with `kind: document` across the manual,
  and the answer's page opened;
- when another trade's row already carries the work: that settles who carries it and that it
  is not written twice, and never a disagreement or a gap about that work;
- when the drawing's own words explain a tag, or the page's own context settles a misprint;
- when requirements stack, from separate programs or set area by area, so that meeting the
  strictest meets them all: each is carried where it applies, in the description where a bidder
  needs it, the strictest where two apply at once;
- when the documents allow either: an "or equal", a list of acceptable makers that holds both, a
  basis of design with equals allowed;
- when a section offers an option only where shown or selected and no sheet shows or selects it:
  no row and no Question;
- when the documents leave a choice to a named party and it still leaves a bidder a basis to
  price, as a color the architect selects from the maker's standard range; a choice that leaves
  none, as a premium finish family the documents never name, is a gap and a Question;
- when a sheet's own note says what to assume, allow or carry, and no other page prints a
  different allowance, amount or product for the same work: that note is the pricing basis;
- when an open Question asks about the same subject for the same trade and its answer settles the
  find too: the find is a reply on it;
- when a Question already asks it: read every Question on the project first, closed ones
  included, with no trade filter (non-negotiable 2);
- when it is a grain call: that is a report line (non-negotiable 6);
- when it is something for the estimator alone: that is a note on the row where the reader's
  mandate 5 NOTES rule passes it, and otherwise a report line;
- when it is about a scope row: the row is what is wrong, and it is corrected on the record;
- when it is which subcontractor or trade the contractor gives work to, labor, or means and
  methods; documents that disagree about who is contractually responsible for work, as where one
  has the owner hire the testing agency and another the contractor, are a disagreement and a
  Question;
- when no manual is read in and the find is a section the upload lacks: a missing specification
  is not known to be missing, so it is named on the anomaly line ending `run only`.

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
- the orientation facts (identity, structure, phasing, site conditions, scope areas): `get_project` and `search` on
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
  at stage 3 step 1 and never changed once reading has started. The delivery's id, label, issue
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
  the lead reads its `phase:` and `pass:` lines with a local command (a filter on the line
  prefix), the closing report's script reads it whole (stage 9), and a runner reads only its own filtered look
  for a unit's `verified` line and `anomaly` notes, as the runner definition says. A unit carries
  one `verified` line, or after a mismatch one per check, the runner having read the unit again
  with its `dispatch` line between the two, and the latest line counts. The summary script sums a
  pass off this file alone, and the lead's record script holds the summary to its first lines, so
  nobody copies it, filters it into another file, or edits a line of it. Audience: agent, and it feeds the closing report, so whatever crosses into that
  report becomes user-facing at the crossing and is translated there.

  Every line reaches the ledger through one script, yours as much as a runner's: each `phase:`,
  `amended:`, `unplaced:` and `note` line this skill tells you to append goes on with

  ```bash
  python3 '<plugin root>/scripts/ledger.py' append '<run folder>/ledger.md' <<'EOF'
  <the line>
  EOF
  ```

  and `lead_pass.py record` writes each `pass:` line through the same script. It holds
  `ledger.lock` in the run folder while it reads, checks and writes, writes each control character
  inside a line (a tab, a form feed, a line separator and the rest) as one space, refuses a batch
  with a line in no shape the ledger holds and writes none of it, and keeps `ledger.shadow` beside
  the ledger, the run's own copy, which only it writes, replacing it whole each time so a stop
  leaves it as it was or with the whole batch. Before every append, whenever `lead_pass.py` reads the ledger, and
  when a runner runs `ledger.py heal` before its first look at the ledger, the ledger is held to
  that copy. Whole `phase:` lines added at the end outside the script, each one the script would
  have taken, are kept and added to the copy. The script refuses a new `checkin:` line, which no
  scope run writes now, and every script reads past the ones an older ledger holds. Where a line was changed or taken out,
  or a line added outside the script is a runner's line, a `pass:` line, one the script would
  refuse, one holding a control character or one with no line ending, the
  ledger is written again from the copy and one line is appended, `repaired: lines
  differing from the run's own copy <n>, first at line <i>; the ledger was written again from that
  copy`. Nothing stops for it and nobody puts a line back by hand. A refused line is sent again,
  correct, as a new line. The run's scripts replace a file whole by writing
  `.<file name>.<process>.tmp` beside it first; one left behind by a stopped script is never read.
  Audience of `ledger.shadow`, `ledger.lock` and those temporary files: machine.

  The lead's own line shapes, which the runner never writes:

  ```text
  pass: <window> <pass id> units <n> created <n> updated <n> questions <n> replied <n> skipped <n> lead-verified <yes|no>
  pass: 3 <pass id> units <n> created <n> updated <n> questions <n> replied <n> skipped <n> pages-opened <n> searches <n> reports-restored <n> lead-verified <yes|no>
  pass: r <pass id> units <n> created <n> updated <n> questions <n> replied <n> skipped 0 recited <n> rows-changed <n> removed <n> not-found <n> retired <n> kept <n> refused <n> lead-verified <yes|no>
  short: <window> <pass id> <unit id> record <n> runner <n>
  phase: <boundary name>
  phase: reading started <UTC time, as 2026-01-31T22:10:00Z>
  amending: <package name>: <what you did>; <the reason, in the estimator's words>
  amended: <the same text>
  unplaced: <section code> <what kept it off every package, in the estimator's words>
  ```

  `lead_pass.py record` writes each `pass:` line and, where the record holds fewer entries under a
  unit than its runner verified, a `short:` line for it in the same append. `phase: reading started`
  carries the time reading began, which the closing report measures the run from; an older ledger's
  `phase: plan approved` line stands for it, with no time. `amended:` and `unplaced:` write down,
  when they happen, what the closing report says about the packages and the sections on none.

  Every figure on a `pass:` line is written by `lead_pass.py record` (stage 4 step 3) off the
  pass's summary file and your own count call, never typed by hand: `created` is the sum of your
  counts, `updated`, `questions` and `replied` come off the summary's totals line, and `skipped`
  is the units the summary reads skipped, in every window. A window 3 line carries three fields more, `pages-opened`, `searches` and
  `reports-restored`, off the summary's `review:` line, which the summary script reads off the
  reviewer's own `pages opened:` and `searches:` lines, each report counted only where the report
  script holds it whole, and counts on `reports-restored` each unit whose report was restored from
  the record, its pages and searches not known. Those fields are what make the run countable from the
  ledger afterwards.

- `grid/`, `inventory.md`, `inventory.json`: the sheet grid as the fetch agent put it on disk, and
  the plan script's counts off it. The lead reads the count tables and the sheet number digest,
  never a sheet line. Audience: machine, and the tables for the lead.
- `plan/`: byte-for-byte copies of a verb's response, paged to disk by a fresh agent, never
  retyped and never read by a model. `packages.json` (`solicitation_list_packages`) is the plan
  script's window 3 input, copied again at the start of window 3, and `spec-sections.json`
  (`list_spec_sections`) its other window 3 input, the manual's sections with their pages, copied
  at the start of window 3. `window-3.json` is what the last window 3 plan run wrote, each
  review's id and each package's chain of manual parts and standard lines unit, made once and
  kept from the window's first dispatch, so a replan never adds, moves or divides a manual page. `window-1.json` is what the window 1 plan run wrote, the unit keys it
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
  passes, the units within each with their sheets, files and pages in windows 1 and 2, and in
  window 3 each package's manual parts with their pages and its standard lines unit, in passes
  before the passes of reviews, and each review, and what is deliberately excluded. Audience: agent; a
  runner opens its own pass only.
- `briefs/`: one small file per pass, written by that pass's runner, carrying the pass's filled
  slot values (what the pass reads for, its content families, the subject prefix scheme). It is the
  whole of what a reader or a reviewer opens off disk. The mandates are never in the brief.
  Audience: agent.
- `reports/`: one file per read unit and per review, the report in its fixed shape, written by the
  reader or reviewer before it returns, so a dispatch that returns without the report in hand loses
  nothing. A unit read again after a mismatch keeps its earlier report here as
  `<unit id>.read-<k>.md` beside the new one. A review also writes `<unit id>-terms.txt` here, the words it harvested, so it ranks
  them on disk rather than in its context. One file per pass holds the pass summary, written by
  the summary script the runner runs, and the runner returns only the hand-back; `lead_pass.py`
  and the plan script read the summary here. The package folder writes `fold.md` here, one act
  of the fold per line, which you read only through `fold_report.py print`. Nobody but its reader
  ever writes, completes or copies into a reader's report. Beside a window 3 unit's report, where
  that unit passed its check and its own report was missing or not whole, the report script
  writes `<unit id>.read-<k>.restored.md`, the report of read `<k>` restored from what the run
  already holds off the record; it says on its first line that the run's script wrote it, and no
  line of it says a page was read or a search was run. Audience: agent, and
  `fold.md` feeds the closing report, so whatever crosses from it into that becomes user-facing at
  the crossing and is translated there. `reports/close-ids.txt` is the closing report's calls for
  its copy agent, written by `close_report.py ids` (Audience: agent).
- `closing-report.md`: the closing report, written whole by `close_report.py write` at stage 9, or
  when the run stops early, headed as a run that stopped. Audience: user.
- `plan/close/`: byte-for-byte copies of the closing report's lookups, the Question counts, a fresh
  package list, the general requirements package, the index's leftovers and the names of the rows
  and Questions its notes name, each by the copy agent stage 9 sends. Audience: machine.
- `owed/`: one file per read after a unit's first in windows 1, 2 and 3, `<unit id>.read-<k>.md`,
  written by the report script off the ledger alone: the rows under the unit's prefix before that
  read, what earlier reads noted they did not write, the checks they failed and the reads that
  ended with no report. The runner names it on the reader's `Owed:` line. Audience: agent.
- `confirmed/`: one file per read the runner verified off the reader's returned message because
  the report file was not whole, `<unit id>.read-<k>.md`, written by the report script before
  that read's closing append: the `updated subjects:`, `questions raised ids:` and `questions
  replied ids:` the runner's check confirmed, and the `trades touched:` catalog ids as the reader
  reported them. It is the runner's record of its own check, not a report, and no line of it says
  a page was read. A later runner of the unit merges that read's lists from it, and writes the
  unit's `touched` trades lines off it after a stop, where no whole report of the read is on file,
  and ignores it where the read has no `verified` line. Audience: agent.
- `names/`: one file per pass, each unit's new items as its runner's check read them off the
  record, one line per item (`<unit id>`, its subject and its name, tab separated), checked whole
  against each unit's verified item count and matched for overlaps by `names_scan.py`, in the pass
  and across passes at the window boundary. Audience: machine.
- `kinds/`: one file per pass, the definition kinds each unit's reader named, one per line,
  appended a unit at a time, and the window boundary takes their union with a local command to
  find every kind a reader named without holding any of them itself. Audience: machine.
- `trades/`: one file per pass, the trades each unit's own verification read, written a unit at a
  time by the report script's `trades` command, which replaces the unit's earlier lines with its
  latest set: one line per trade as `<unit id> trade <catalog id> <count>`, that count being the
  unit's created subjects on that trade, and one line per trade it touched as `<unit id> touched
  <catalog id>`. The pass summary script sums this file, so no runner adds the trades up itself.
  Beside it, `<pass id>.written` names each unit whose set was written and the read it was written
  for, `<unit id> read <k>` one unit per line, so a unit with no trades is told from one whose
  trades were never written, and the latest read's set from an earlier read's. A unit's `touched`
  lines are every trade any of its verified reads touched, ok or mismatch, gathered by the report
  script's `touched` command. Audience: machine.
- `records/`: JSONL files for large batch writes (these do get uploaded, as the write
  mechanism). Audience: machine.

## Windows, and who holds what

The run is one conversation that goes to its end on its own, and nothing in it accumulates. The
project record is the run's memory; the run folder is its bookkeeping; no level of the run holds
between its units anything a later unit needs. The user never manages context: nothing waits on
them but the stops, and no prompt ever mentions sessions, compaction, or usage.

The run executes at three levels. Each level is a separate agent context, bounded by construction:

- **The lead** is this skill, running in the user's session. It does the cheap work only:
  preconditions, orientation, the read plan, starting the index and waiting on its status,
  amending, the closing report. For each pass it starts one runner and receives one short
  hand-back; what it keeps per pass is that hand-back and, once it has taken its own count, the
  one `pass:` line `lead_pass.py` writes to the ledger. It never holds a pass summary, a pass
  brief, a reader's report, the sheet grid, the index report, or a page of the set.
- **The pass runner** (the plugin's `scope-round-runner` agent, one fresh instance per pass) owns
  one pass: it writes the pass brief, runs the pass's units exactly as the window's stage defines
  them, verifies every unit with one `verify_unit` call, notes overlaps inside the pass, appends
  the ledger in its fixed line shapes, writes its summary to disk, returns its hand-back, and
  ends. Its context is bounded to one pass of at most twelve units, ten in window 3, and it never
  grows with the size of the window. Two further
  instances run in their own modes: one closes each window at its boundary (the cross-pass overlap
  scan and the declaration of any kind a reader named and did not declare), and in window 3 each
  pass runner runs up to ten manual parts and standard lines units, or up to eight review units,
  or every package of one trade where that trade has more, one at a time.
- **The readers**, one fresh instance per read unit, each read over the corpus and record, as the
  window's stage and the pass brief define: in window 1 the plugin's `scope-vocabulary-reader`
  agent reads one sheet for the vocabulary, or one drawing file's repeated lines, and in window 2
  its `scope-reader` agent reads one sheet for the sheet itself. Each writes its report to
  `reports/` and ends.
- **The package folder** (the plugin's `scope-package-folder` agent, one fresh instance per
  dispatch) folds the packages into what one kind of firm bids once window 2 is read and indexed,
  writes each act to `reports/fold.md`, and returns a five-line hand-back; dispatched again, it
  deletes a package for the owner's own work that a later write made again.
- **The reviewer** (the plugin's `scope-reviewer` agent, one fresh instance per package) reviews
  one package in window 3: it harvests that package's own words off the record, searches the set's
  text for them, opens only the pages a hit sends it to, takes what the package's manual parts
  left through a script, records what no row carries, and settles the package's headings and row
  order. Each writes its report to `reports/` and ends.
- **The manual reader** (the plugin's `scope-manual-reader` agent, one fresh instance per manual
  part) reads the pages of a package's manual sections the plan gives one manual part, before the
  package's review, and records what they put in the package's scope. Each writes its report to
  `reports/` and ends.
- **The standard lines writer** (the plugin's `scope-standard-lines` agent, one fresh instance per
  package) writes the package's standard lines after its manual parts and before its review. Each
  writes its report to `reports/` and ends.

Handoff is by file and record, never by inlined text. A dispatch at any level carries only
pointers: the project id, the window, the pass or unit id, the run folder path, and the page or
package references. A reader and a reviewer open the pass brief from the path they are handed, a
reviewer the reader definition whose mandates it works under too, and everything else from the
record; the runner opens the read plan for its
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
your runner dispatched or another session, is not your report: never relay its counts, and answer
it where it asks something. One turn can carry several hand-backs: take each in turn. No rule ends
your turn on its own. Whatever wakes you, a hand-back, a notice from an agent you did not dispatch,
a completion notice for one you already took, or the user writing while agents run, finish by
taking the passes listing and doing what it shows: start what can start, go to the window's
boundary when nothing is left, or stop at one of the stops below. A turn ends with nothing running
only at one of those stops, before reading starts where a precondition asks the user something,
or once the closing report is given.

Several dispatches sit partway through a stage: the copy of the delivery list (precondition 3),
orientation (stage 2 step 2), the copy of the packages (stage 2 step 4), the grid fetch and a fetch
sent again (stage 3 step 2), the package folder (stage 6 step 5), and the copy of the packages at
window 3 (stage 7 step 1). Where the call comes back with an agent id, end the turn after that
dispatch and continue at the next step when its report arrives.

Where a runner has ended and its hand-back did not arrive in the message, as with a completion
notice that carries no hand-back, dispatch its pass again: the new runner skips every unit already
verified and writes what the one before it left. A missing or stub report of a reader or a reviewer
is never a reason to read a unit again. The runner holds every report to the report script's
check, verifies off the reader's returned message where the file is not whole, and in window 3
restores the lost report of a unit that passed its check from what the run already holds. You
restore one yourself the same way, for a window 3 unit whose latest `verified` line reads ok, with
no page read:

```bash
python3 '<plugin root>/scripts/unit_report.py' restore '<run folder>' 3 <unit id>
```

A unit is read again only where its check found a mismatch or no check could be made, against the
live list, so nothing is created twice.

An agent that stops answering partway is ended by the client within about ten minutes, and its
dispatch comes back as an error whose whole text is `[Request interrupted by user for tool use]`.
While the caller is still running, that is never the user: their interrupt would have stopped the
caller too. It is an agent that stopped answering. A reader that stops ends one read, and its
runner reads the unit again as the runner's definition counts its reads: a unit whose two reads
both failed their check is skipped, and the pass goes on. A waiting runner is never ended for its
reader's silence, so a runner that comes back this way stopped on its own reply: dispatch its pass
again; its runner skips every unit already settled, and a read it cut off spends nothing.

Reports travel upward in a fixed short shape, counts and named anomalies only (the shapes are
given with the dispatch templates below). A runner returns its hand-back, a few lines of counts
naming its summary file, and the summary stays on disk. When the hand-back arrives the lead takes
its own count off the record, and `lead_pass.py record` compares that count with the summary file
and writes the pass's `pass:` line, so the lead never reads a summary, never relays one, and works
from that line once it is written.

Phase boundaries are the ledger's `phase:` lines, one appended by the lead at each of: reading
started; window 1 complete, or window 1 skipped where a pass on an addendum planned no window 1
unit; index built; window 2 complete, or window 2 paused where a slice deferred sheets; packages
folded; recheck complete, on a pass whose delivery was sized; window 3 complete; packages amended;
closed out. Inside a window the `pass:` lines are the boundaries: one per pass in every window. A
pass run again to finish it carries a second `pass:` line, and its last one carries the whole pass:
every total taken over a window, and the closing report, counts that one, for each pass the
window's read plan now carries. A part a replan folded into another pass after its own `pass:`
line was written is counted in the pass that took it in, and never twice.

On every start, and whenever the estimator says go on after a stop or a pause, read the ledger's
`phase:` and `pass:` lines first, with a local filter, never the file, and pick up from what is on
disk. An older ledger's `checkin:` lines are read past, and its `phase: plan approved` is the
reading started line. Where the active window, the operation in flight and the operations
finished stand:

| What the ledger and the run folder show | Where you pick up |
|---|---|
| no `phase:` line | stage 3 from step 1 in that folder |
| reading started; window 1 passes, some not finished, one out or none | window 1: its plan again, then the listing (below) |
| every window 1 pass finished, no `window 1 complete` | stage 4 step 4: the boundary runner, then the line |
| `window 1 complete` and no `index built` after it | stage 5 |
| `index built` after window 1, or `window 1 skipped` | stage 6 step 1 |
| window 2 passes, some not finished, one out or none | window 2: its plan again, then the listing |
| every pass of a slice finished, no `window 2 paused` | stage 6 step 4: boundary, the paused line, then the index |
| `window 2 paused` and no `index built` after it | stage 5, then stage 6 step 1 |
| `index built` after `window 2 paused`, no window 2 `dispatch` after it | stage 6 step 1, the plan without `--only` |
| every window 2 pass finished, no `window 2 complete` | stage 6 step 4: boundary, then the line |
| `window 2 complete` and no `index built` after it | stage 5 |
| `index built` after window 2, no `packages folded` | stage 6 step 5: the folder in mode fold, mid-fold included |
| `packages folded` on a sized delivery, no `recheck complete` | `recheck.md` step 7 |
| `packages folded` on an unsized delivery, or `recheck complete` | stage 7 step 1, the folder's recheck mode first where the fold deleted a package on a rechecked pass |
| a window 3 `dispatch` line, no `window 3 complete` | window 3: its plan again with the same files, then the listing, which holds the passes of reviews until every pass of manual parts and standard lines is finished; step 1's start steps are not run again |
| every window 3 pass finished, no `index built` after them | stage 7 step 4: boundary, then the index |
| `index built` after window 3's passes, no `window 3 complete` | append `window 3 complete` |
| `window 3 complete`, no `packages amended` | stage 8 from its start; each `amending:` line no `amended:` line follows is finished against the live packages, its `amended:` appended |
| `packages amended`, no `closing-report.md` or one headed as stopped | stage 9 step 1 |
| `closing-report.md` finished, no `closed out` | stage 9 step 2: say the short version again, then append |

"Its plan again" is that window's plan script, run exactly as its stage wrote it, with the same
arguments: window 1's `--include` and `--exclude` and a slice's `--only`, each with its reason, are
on that window's `plan/window-<n>.json`, taken off it with a local filter. The script keeps every
id the ledger and the plan file already hold and marks the units already settled. Then take the
one `lead_pass.py passes` call stage 4 step 1 gives, with no `--running`, since a resume has no
pass out, and carry on from what it names: a pass out when the session stopped is not finished, so
it is started again, and its runner picks up at the unit it stopped on. A pass is finished when its
units verified and skipped add up to its `units:` and it reads `summed: yes`. Window 1's repeated
lines pass is a pass like any other here. It reads `summed: yes` only while the pass's summary on
file names exactly the unit ids the block now carries and the pass's last `pass:` line carries that
summary's figures, so a replan that changes which units a pass carries, by a fold or a cut, leaves
it unfinished even where the count comes out the same. Any other pass is not finished, whether or
not a `pass:` line for it is on the ledger: when the listing names it, its runner skips the units
already settled and writes a new summary. Each step a resume runs again is safe to run twice: a
boundary runner adds no overlap note twice, the index cites no page twice, the folder keeps every
act its report carries, and the general requirements package is updated where it exists. A pass on
a later drawing issue starts in a run folder of its own on a project that already carries scope
items, and the live-list mandate (non-negotiable 2) keeps its readers from creating what is
already there. A run folder lost from this seat leaves its rows on the record under its tag: the
tag check moves past that tag, and the pass on that issue starts again in a new folder, against the
live list. Resumption is how a run continues after a stop, and crash and multi-day hygiene. It is
never offered to the user as a way to manage cost.

## When the run stops

The run stops only where it cannot go on without the estimator. Before reading starts, the
preconditions below can stop it or ask him something: an old client, which project, no Python, run
folders mixed with another project's, whether a project manual exists, the plan for a new delivery
not approved, and drawings whose text is not read. Once reading has started, these are the only
stops, and nothing else waits on him:

1. **A call that could not be made.** A runner's hand-back names it on `stopped:`, a boundary
   runner, the package folder or a copy agent returns a `blocked:` line, or a call of your own
   errors. Try the same operation again yourself, up to three times over about fifteen minutes,
   before each try running the wait mode as a foreground Bash command with a timeout of 300000
   milliseconds, single quoted; it returns by itself, and nothing else wakes you:

   ```sh
   python3 '<plugin root>/scripts/lead_pass.py' wait 280
   ```

   A pass is tried again by dispatching it again, and its runner skips every unit settled. A `whoami` that
   answers does not clear it; only the operation that failed succeeding does. Where the third try
   still fails, stop with the message for its class: on `stopped:` the class its note names; on a
   call of your own, sign-in where its error names signing in or authorisation, refused by the
   client where Claude Code denied it, and server otherwise. An index job reading `failed` is
   started once more, then handled as a call that could not be made, class server. A `stopped:`
   line naming the third read in a row is stop 2, never tried again.
2. **One unit cut off or blocked three reads in a row**, which a hand-back's `stopped:` line names
   as the third read in a row, whatever ended the last: stop at once with the message for the
   class of its last note, or where that read was cut off, the interrupted message. When he says to
   go on, first append
   `note <window> <pass id> <unit id> deviation <sheet> go on given after three reads that spent nothing`,
   for a blocked unit exactly as for one cut off, which lets its runner read it once more, then
   dispatch the pass again.
3. **The breaker.** Where `lead_pass.py record` prints `breaker:`, a pass skipped three units or
   more and more than half of them. It guards against a failure no read named, and it guarantees
   nothing: stop with the breaker message. The report so far names each skipped unit with the
   reason off its last read; say the reasons it gives, in a few words each.
4. **A window that cannot be planned**: the window 3 plan refusing because the section list reads
   truncated or because window 3 was started under an earlier plugin, the inventory refusing the
   grid after a second fetch, the recheck's plan refusing after its rows are copied again, and the
   recheck's comparison not finishing (`recheck.md` step 1). Say in plain words what is wrong and
   what he would do about it.
5. **In the recheck of a new delivery, a sheet whose two reads both failed their check**, as
   `recheck.md` step 4 says.
6. **The same refusal twice.** When a pass, a boundary step or the package folder returns a
   script refusal or a failure, run `lead_pass.py seen '<run folder>' <pass id or step name> '<its
   first line>'`. At `2 in a row with no ledger line added` or more, stop, and tell him what the
   script printed, in his words where this skill gives them and as printed otherwise.

After each poll of a job (a delivery's recognition, the set's text, the index, the recheck's
comparison), run `lead_pass.py seen '<run folder>' <the job's id, or the verb and the delivery or
file it names> '<its status and progress fields>'`, then `lead_pass.py wait 60`. At `standing` 30
minutes or more, it is a call that could not be made, class server.

At every stop, first write the closing report so far, `close_report.py write` as stage 9 step 1
gives it with `--stopped '<why, in plain words>'` and no copy, and link the file in the message the
way stage 9 links it, where that call exits 0. The run is not closed. When he says to go on, pick up
at the operation that stopped, as the windows section's table reads the run folder.

<!-- user-facing -->
The messages, each with what you finished named in plain words and the link to the report so far:

- Sign-in: "Your Plumlayer sign-in has expired, so I stopped after <what finished>. Type /mcp,
  choose plumlayer, pick Re-authenticate, then tell me to go on."
- Refused by the client: "Claude Code did not allow <what the call does, in plain words>, so I
  stopped after <what finished>. Allow it when it asks, then tell me to go on."
- Server: "Plumlayer is not answering, so I stopped after <what finished>. Tell me to go on once
  plumlayer.com loads, and I'll pick up where I stopped."
- Interrupted: "Reading <sheet or package> was cut off three times in a row, so I stopped after
  <what finished>. Tell me to go on and I'll read it again."
- Breaker: "In <what the pass read>, I could not confirm <n> of the <m> sheets after two reads
  each: <the reasons>. That many can mean something outside the reading went wrong, though you may
  find nothing wrong. Look at the report so far, then tell me to go on."
- The same refusal twice: "<What the run was doing> was refused the same way twice: <what the
  script printed>. I stopped after <what finished>. Tell me to go on once that is settled."
<!-- /user-facing -->

At the plan's usage limit, Claude Code waits in the open session and goes on by itself once the
limit resets, while this session stays open and the computer stays awake: that is no stop, and you
say nothing about it. Where the estimator says stop or
pause, start nothing new, record each pass already out as it reports, and say in one sentence what
the run does next. A pause writes no line: his go-ahead, or the skill started again, is the resume.

<!-- user-facing -->
Say so plainly in one sentence: "What I've already started will finish first, then I'll stop."
<!-- /user-facing -->

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
     `phase:` and `pass:` lines of that folder's `ledger.md` with a local filter on the line
     prefix; never open the file whole, and pick up where the windows section's table says, so
     nothing already settled is read again. Where the ledger carries no `phase:` line yet, reading
     never started: take stage 3 again from step 1 in that folder. Once reading has started, never
     fetch the grid of a pass you resume: its `inventory.json` is its sheet list, and the plan script refuses a grid
     or an inventory whose deliveries differ from its `run.json`. A pass begun before passes had
     folders of their own resumes in the project folder itself, exactly as it always has. A run is
     never resumed past a boundary that did not run. Never offer resumption to the user as a way to
     manage anything.
   - `wait <deliveryId>`: that delivery's sheet numbers are still being read, and it may yet be a
     new set. Run the wait mode, then copy the delivery list again and run the issue mode again, a
     poll bounded as the stops section says.
   - `start <deliveryId>`: the latest set, which no pass has read, or, once the set has its pass,
     the earliest addendum of it that landed after that pass; the line says which, and names the
     addenda still waiting behind this one. Each of those gets a pass of its own, one at a time,
     in the order they landed. The line names its run folder
     and its unit tag. Make the folder, and check the tag on the record:
     `search(projectId, subjectPrefix: "scopeItem:i<n>-", limit: 1)`, reading `count`. A tag is
     free where no subject starts `scopeItem:<unit tag>-`; a count above zero is rows from a pass
     whose run folder is not on this seat, so take the next number and count again until one reads
     zero. That count goes into `run.json` at stage 3 step 1. The pass on a set is a full pass over
     every sheet the set and its addenda print, and on the latest set over every sheet it keeps
     from an earlier delivery too, each marked `keptFrom`; the pass on an addendum is a partial pass over the
     sheets it prints, since `set_grid` by an addendum's `deliveryId` gives only those. Where the line ends by saying the earlier pass in the
     project folder names no drawing issue, a pass from before passes had folders of their own is
     closed out there, and nothing records which set it read: start all the same, never guess
     which set that was, and say so in the first message.
   - `none`: there is nothing to start, and the run stops here.
<!-- user-facing -->
   Say what the line says, plainly: you already ran a scope pass on the latest set, naming it,
     and on every addendum of it since. Where no delivery is stated as a new set yet, say the drawings are
     not in, and hand off to `drawing-upload`.
<!-- /user-facing -->
4. **Drawings are recognized, and their text is read.** Spot-check recognition actually
   recorded: `search(projectId, predicate: "appearsOnPage", limit: 1)`: zero rows → hand off to
   `drawing-upload`. On a set that just landed, poll `set_text_status(projectId)`, bounded as the
   stops section says, until it shows the set read: a page nobody has read yet cannot be found by `search_set_text`, so a
   fresh delivery still being read would otherwise look like a missing corpus. The corpus itself
   is confirmed once the inventory is on disk, at stage 3 step 3.
5. **Spec book, if it exists.** `search(projectId, predicate: "inDivision", limit: 1)`: spec
   sections present means the spec-TOC leg has run. Absent: ask the user whether a project manual /
   spec book exists. If one does, run it through `drawing-upload`'s spec-book leg first (upload +
   `extract_spec_toc`): the package split anchors on the spec table of contents and is
   substantially weaker without it. If the project genuinely has no spec book, proceed and name
   that in the ledger and the closing report: orientation created no baseline packages for this
   project (no spec sections, no anchor), and stage 8 below derives the whole split from the
   finished scope list instead.
6. **The start-up calls, while the user is there.** Before the first message (stage 3), make one
   `whoami`, the Python probe of precondition 2 if this session has not made it, and one
   `search(projectId, subjectPrefix: "scopeItem:", limit: 1)`, so a permission prompt for any of
   them comes up while the user is at the keyboard. A `whoami` that errors naming signing in is the
   sign-in stop before any reading.
   Take the first message's rough time off what runs have measured: window 1 about 5 to 6 minutes
   a sheet and window 2 about 3 minutes a sheet, with six passes running at once, so divide the
   sheet minutes by six; window 3 took about 45 minutes of reading a package with its manual
   pages on the last measured run, six at once, so give it as a range of 5 to 15 minutes a package.
   Where it can, the run starts from a clean conversation, but it never raises sessions,
   compaction, context, or usage with the user, at run start or at any point after it.
7. **The plan the user approved for the delivery.** On `start <deliveryId>`, and on a resume whose
   ledger carries no `phase: reading started`, nor an older `phase: plan approved`, yet, look for the delivery's plan file,
   `<runs root>/<projectId>/upload/<deliveryId>/plan.md`, with a local command (`ls`), the file
   `drawing-upload`'s step 9a writes and appends to as its `size-delivery.md` says. Read its
   `status:`, `carry:`, `carried:` and `stopped:` lines with a local filter on the line prefix and
   never the file whole (Audience: agent).
   - Its last `status:` line reads `approved`, and a `carried:` line follows it or its `carry:`
     line reads `left out`: go on. The pass reads what the plan says, and the recheck runs after
     the pass's packages are folded (stage 6 step 6). Their approval of that plan is the ask the
     recheck's retires rest on, and stays the one question before reading starts on a new delivery.
   - Its last `status:` line reads `approved` and no `carried:` line follows it: the carry has not
     run. Dispatch the delivery sizer in carry mode first, with the dispatch `size-delivery.md`
     step 3 gives and `Change: none`, and say its result in one line as its step 5 does. Where the
     sizer appends a `stopped:` line instead, the run ends here: say why in one sentence, and that
     the pass starts once the references are carried.
   - Its last `status:` line reads `shown` or `stopped`, or there is no plan file where
     `size-delivery.md` step 2 says the delivery is sized, its counts taken now: dispatch the
     sizer in plan mode as its step 3 says, with `Change: none`, put the plan to the user in its
     step 4's words, and take their answer as its step 5 does, each line it appends included. Where
     they stop it again, the run ends with no pass: say so in one sentence.
   - Where no plan file is there and `size-delivery.md` step 2 does not size the delivery, as on a
     project with no scope item and no open Question, the pass runs as a first pass does, with no
     plan file and no recheck.

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
   no spec-section text. The orientation agent runs its own definition (`agents/orientation.md`)
   exactly as written and returns its summary in the shape that definition gives. Read back only that summary: its first line (sheets
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
   `agents/orientation.md` step 8 sub-step 6 yourself now, placing each listed section on the package that
   buys it, before window 1 starts. Each manual reader that step sends carries a `Refused so far:`
   line: put on it each call the user refused in this session, or `none`. Read `manualSectionPlacement.truncated` whatever
   `onNoPackage` holds: when it is true the placement count is incomplete, and the closing report
   says so. For each section still on `onNoPackage` after that, append one
   `unplaced: <section code> <what stopped its placing>` line, which the closing report names. Then send one fresh agent to copy the final `solicitation_list_packages` response
   to `<run folder>/plan/packages.json`, byte for byte, returning one line; the plan script reads
   it from there, and you never hold it.

## 3. The read plan

The plan for window 1 is written here and shown to the user as reading starts; the plans for
windows 2 and 3 are written by the same script at each boundary from what the record then holds.
A pass is a set of read units read together for one purpose; a read unit is one sheet.

You never read a sheet row. The grid is fetched to disk by a fresh agent, a script turns it into
counts and into the plan's unit lines, and what you read is the counts and the script's bounds
lines.

1. **Take the set's shape, and nothing else.** `set_grid(projectId, deliveryId, includeKept: true, limit: 0)`,
   with the delivery precondition 3 named. That is a summary-only call: metadata, `disciplineCounts`,
   the `delivery` you asked for and `readFrom`, the deliveries its rows come from, the earlier
   deliveries of the sheets the latest set keeps among them, and zero rows.
   Read `count` and the discipline distribution off it. These are the only `set_grid` calls the
   run makes, at any set size: this one, taken again only where step 3 sends you back to it
   before reading starts, and the fetch agent's paged calls in step 2, sent again where the
   inventory refuses the grid. Never call it for rows yourself, never page it, and never fall back
   to sampled `search` reads for the inventory: whatever you pull that way stays in your context
   for the rest of the run.

   Then write `<run folder>/run.json` in the shape the run folder section shows, off that answer
   and the tag check: each id copied character for character. The inventory refuses a grid whose
   deliveries differ from this file, so a slip costs one more fetch and never a wrong plan. Write
   it again only before reading starts: where the inventory refuses the grid because a
   delivery landed since, take this call again, write `run.json` again from it, and fetch again.
   Once `phase: reading started` is on the ledger it never changes, and the pass reads the sheet
   list it started on.
2. **Send one agent for the grid.** Dispatch a fresh general agent, whose whole job is this and
   which then ends, with the fetch below. It pages the grid, puts it on disk under
   `<run folder>/grid/`, and returns one line. Read that line and nothing else.

   ```text
   run_in_background: false
   Fetch the sheet grid for project <projectId> to disk. This is your whole job. Do nothing else,
   and end when it is done.

   1. Call set_grid(projectId: "<projectId>", deliveryId: "<deliveryId>", includeKept: true, limit: 500, offset: 0),
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
   5. Where a call cannot be made, because Claude Code refused it, your sign-in failed, or
      Plumlayer did not answer after one try more, stop and return exactly one line instead:
      `blocked: <tool> <sign-in, refused by the client or server>`.
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
   step 1 again first. A refusal that comes back after the second fetch is a window that cannot be
   planned, a stop. Read only its bounds line, which names the drawing issue and the first
   sheet, then read from `inventory.md` only the count tables and the sheet number digest at its
   tail. Never the sheet lines above them. The inventory can list more sheets than the grid's
   `count`: where one number prints on more than one page of the issue, each further page is a
   sheet of its own, as is a set's page of a number its addendum reprints on fewer pages, and the
   bounds line names those pages and any page of an issue the pass does not read from that the
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
     [--delivery-plan '<plan file>'] \
     --out '<run folder>/read-plan.md'
   ```

   Where precondition 7 found the delivery's plan approved, pass its plan file as
   `--delivery-plan`, on every window 1 plan run of the pass. A plan reading `pass: partial` reads
   only the sheets on its `read:` line, and the script names every other sheet of the pass as `left
   by the plan he approved`, apart from what `--exclude` leaves out; window 2 reads its window 1
   file and leaves them out too. A plan reading `pass: full` leaves nothing out. The script refuses
   a plan whose last status line is not approved, one naming another delivery, and one reading a
   sheet this pass does not carry: take the plan again at precondition 7, never plan around it.

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

Then, in the same turn, append `phase: reading started <the time now in UTC>` to the ledger,
the time off `date -u +%Y-%m-%dT%H:%M:%SZ`, start window 1 as stage 4 says, and give the first
message. Nothing reads before that line exists, and nothing waits on an answer to the message.

<!-- user-facing -->
The first message, in a few plain sentences, never a table:

- The order: schedules and legends first, by discipline, and the notes each drawing file repeats
  across its sheets, read once, then every sheet once, then each package reviewed on its own
  against what landed, several at a time, in one sentence. No reasons; they know why schedules come before plans.
- What is deliberately left out, by sheet family or number. Say it plainly: anything here will not
  be scoped.
- About how long the whole run takes, off precondition 6.
- That reading has started and the run goes to its end on its own, with one line here as each
  group of sheets or packages finishes.
- That each package review combines items that carry the same work into one, and the closing
  report names each item it combined, so they can have any put back.
- That while the schedules and legends are being read they can tell you to leave out or add a
  family, or say stop, and what you already started finishes first.
- That the closing report comes as a file, with a short version here.
- That the run stops only if their Plumlayer sign-in expires, Plumlayer stops answering, or the
  next part cannot be planned, and that at the usage limit Claude Code waits and goes on by itself
  while this session stays open and the computer stays awake.
- Every run, these two plain sentences: "If Claude asks you to approve a tool while the run works,
  the run waits until you answer; starting Claude in auto mode, or always allowing Plumlayer's
  tools and scripts the first time each asks, means the run rarely has to ask. Keep this computer
  on and awake until the run finishes, since a sleeping computer stops it."
- On a pass on an addendum: you read only the sheets the addendum prints, naming how many, its
  schedules and legends first where it has any, and afterward you review only the packages this
  pass writes rows on.
- Where precondition 7 found the delivery's plan approved: that you read what the plan they
  approved says, and only where you added an `--include` or an `--exclude` of your own, that
  change, which they can undo while the schedules are read.
- Only where precondition 3's line said an earlier pass names no drawing issue: you scoped this
  project before, the earlier run did not record which set it read, and this pass may read a set
  that was already scoped. Name no set for it.

For example: "I'm reading the architectural schedules and legends first, then every sheet once,
then each package on its own. I'm leaving out the landscape set. It should take about seven hours,
and I've started: tell me now if a family should be left out, or say stop. Each package review
combines items that carry the same work, and the closing report names each one."

Never show passes as a table, counts of dispatches, bundle codes, lanes, model names, or anything
about how the run is executed. Never offer a recommended option.
<!-- /user-facing -->

A family the user leaves out or adds while window 1 runs is a plan run again with that
`--exclude` or `--include`, once the passes out have reported; window 2 subtracts window 1's file,
so it is cut there too.

## 4. Window 1: vocabulary

A pass on an addendum whose window 1 plan reads `units 0` and plans no repeated lines unit has no
vocabulary of its own to read: its sheets print no schedule, legend, notes or index, and no file
of five of them. Window 1 does not run and no index runs after it. Append
`phase: window 1 skipped` to the ledger and go straight to stage 6 step 1.

The reading happens one level down, one runner per pass. The lead does exactly this and holds
nothing else:

1. **Start one runner per pass, as the listing says.** At the window's start, and each time the
   plan script has run again, a resume among them, list the window's passes whole with one call,
   single quoted as every script call is:

   ```sh
   python3 '<plugin root>/scripts/lead_pass.py' passes --plan '<run folder>/read-plan.md'
   ```

   It prints two lines per pass: its id with its `units`, `units verified`
   and `summed` values as the ledger and the summaries now have them,
   and its prefixes, the `scopeItem:<unit id>-` of each unit id its plan block carries, in plan
   order. A line then names the passes
   not finished, after `to dispatch:`, and two more say what you do next: `start now:`, the
   passes to start, and `waiting:`, the passes held back. You act on those three closing lines and
   keep no prefix: step 3's call prints a pass's prefixes when it reports.

   You start what `start now:` names, a fresh `plumlayer:scope-round-runner` for each with the
   runner dispatch below: pointers only, no pass brief and no read-plan text. When a pass hands back,
   step 3 takes its count, records it and lists again, and you start what that last listing names. The
   listing holds you to six at once in every window, because Claude Code stops agents past 20
   running together and each pass runs a runner and its reader or reviewer. It holds a discipline's
   later kinds of sheet until the passes holding its earlier ones finish, so the sheet that should create a row
   is the first to see its work. You never pick a pass yourself, and you wait by ending the turn, as
   the windows section says. A pass the listing names is started whole even
   when it already carries a `pass:` line, as a
   pass is once a replan adds sheets to it, folds a part into it or cuts a sheet it read: its
   runner skips the units already verified, and its new `pass:` line carries the whole pass. The
   repeated lines pass, `RS1` and any lettered part of it, waits for nothing, nothing waits for it,
   and it takes the same runner dispatch. A unit whose two reads both failed their check is
   skipped, and its pass still finishes. What a pass leaves in the lead's context is its
   dispatch, its hand-back, the prefixes line and the closing lines of step 3's two calls, its count
   answer, and its `pass:` line with the line under it, nothing else.
2. **The runner owns the pass.** It writes the pass brief if it is not already on disk, runs the
   pass's units in reading order (one fresh reader per unit, one unit at a time,
   `plumlayer:scope-vocabulary-reader` in window 1 and `plumlayer:scope-reader` in window 2), appends each unit's dispatch line
   before that unit starts, verifies every unit with one `verify_unit` call before the next unit
   starts, notes overlaps inside the pass, and appends the ledger in its fixed line shapes. The
   per-unit loop lives in the `scope-round-runner` agent definition and the reader mandates live
   in the `scope-vocabulary-reader` and `scope-reader` agent definitions. Neither is restated here, and neither is ever trimmed.
3. **Take a pass's count when it reports, then record it.** A runner returns one short hand-back
   (shape below) that names the pass's summary file. Read its `stopped:`, `skipped:` and
   `unverified:` lines first. A `stopped:` line is a call that could not be made or one unit cut
   off three reads in a row: handle it as the stops section says. A `skipped:` line names a unit
   whose two reads both failed their check: its writes stay on the record, the closing report names
   it with the reason off its last read, and its pass is finished without it; you never dispatch it
   again, and where the user asks for it to be read again, say it is named in the closing report
   and go on. A pass with a unit on `unverified:` and nothing on `stopped:` is a runner that
   stopped partway: dispatch the pass again. Only a runner writes a `verified` line, never you by
   hand, and nobody copies the ledger, filters it into a file or edits it to get a pass through: a
   mismatch gets investigated, never papered over.

   Otherwise, before you say a number out loud, list that pass with one call, the pass that handed
   back after `--reported` and every other pass you started and have not recorded after `--running`,
   which you leave off where there is none:

   ```sh
   python3 '<plugin root>/scripts/lead_pass.py' passes --plan '<run folder>/read-plan.md' --reported '<pass id>' --running '<pass id>,<pass id>'
   ```

   It prints that pass's `<pass id> prefixes:` line, read off the plan as it stands now, and the three
   closing lines, and it refuses a pass the plan does not carry. A pass on `--reported` counts as out
   until it is recorded, so `start now:` does not name it, and those closing lines do not yet count
   it. Take the pass's counts off the record yourself with one call,
   `count_entries(projectId, subjectPrefixes: [<those prefixes>])`, reading each `entryCount`. That
   is the third boundary of non-negotiable 5,
   and it is count-only: never a row list, and never a prefix or a count taken off the hand-back.
   Then record the pass, passing the answer's `counts` array through as it came back, single
   quoted:

   ```sh
   python3 '<plugin root>/scripts/lead_pass.py' record '<run folder>/ledger.md' <window> <pass id> \
     --plan '<run folder>/read-plan.md' --counts-json '<the counts array of the answer>'
   ```

   It pairs each count with its unit by its `subjectPrefix`, never by its place in the array, and
   refuses an array whose prefixes are not exactly the pass's, each once, writing nothing. It
   compares your counts unit by unit with the summary file, copies the updated, questions and
   replied figures off that file, and in window 3 the pages opened and searches off
   its `review:` line, appends the pass's one `pass:` line to the ledger, and prints it, with a
   line under it naming the pass by the sheets it read, or in window 3 the packages it reviewed,
   and its new items, items updated and Questions as the user hears them. Work from those lines
   from then on. A unit it names as above the runner's count carries entries written
   since its runner verified it, by a later write onto its rows, and stops nothing. Where the
   record holds fewer entries under a unit's prefix than its runner verified, the line reads
   `lead-verified no` and a `short:` line under it names the unit and both counts, which the closing
   report names first under what went wrong; the run goes on. Where it prints `breaker:`, stop as
   the stops section says. Any refusal names what is wrong with the call: fix the call and run it
   again. The `created` figure on the `pass:` line counts entries, every citation
   and trade written with the new items, and is your own check: say the new items, the items
   updated and the Questions as the line under it gives them, and never the entry count.

   Once the pass is recorded, make the `--reported` call again, with the same passes. Its closing
   lines now count the pass you recorded, and they are the ones you act on: start what `start now:`
   names, and where nothing is left, close the window.
<!-- user-facing -->
   As each pass is recorded, tell the user one line naming what it read in plain words: "I've
   read the fire alarm sheets, 48 new items." Keep the rest for the closing report.
<!-- /user-facing -->
4. **Close the window at its boundary.** When every pass of the window has reported and carries
   its `pass:` line, dispatch one more runner with `boundary` in place of the pass id. It scans the
   window's new items for the same work captured by two passes that ran alongside each other,
   declares any kind a reader named and did not declare, and ends. It copies no definition to disk:
   no window plans off the definitions, so a copy of them would be a file with no reader, and a
   reader asks the record. The only file it writes beside its summary is the names of any unit whose
   names its pass left unwritten, off the record. Then append
   `phase: window 1 complete` to the ledger with the window's verified totals,
   and go straight to stage 5: the index runs before window 2, so every trade's page carries every
   sheet before the sheets are read.

## 5. The citation index

After each of the three windows, and never skipped. It runs after window 1 so every trade's page is
usable before the sheets are read, after window 2 so every reviewer works from a record that holds
every page each row appears on, and after window 3 so the rows the reviews created carry
every page too. In a pass on an addendum it runs the index after each window that ran: a window 1
that was skipped has none, and a window 3 that planned no review has none:

1. **Start it.** `index_citations(projectId)`. It walks the corpus for every definition code and
   every item's tag or mark on the record and cites every page each appears on, onto the definition
   and onto the items that resolve to it, as the record's own text match. It writes citations only,
   never a value; an item that already cites a page is not cited there again; a match on a code of
   two characters or fewer, or with no digit and no hyphen between two letters or digits (a code
   that prints as an ordinary word), is left open rather than cited.
2. **Wait for it.** Poll `index_citations_status(projectId)` until its `state` is `succeeded` or
   `failed`, with the wait mode between polls, bounded as the stops section says. On `failed`, start it once
   more and wait again; a second `failed` is a call that could not be made, as the stops section
   says. On `succeeded` its `report`
   carries `codesTotal`, `codesMatched`, `citationsWritten` and the rest of the run's counts, and
   `leftoverCounts` carries the true count per kind of what it could not cite, with
   `truncatedKinds` naming the kinds whose rows were cut for size. Read the counts; never the
   pages. `queued` and `stale` are both safe to wait through. Where `wordCodesSetAside` is false,
   the report comes from a pass that ran before codes printing as ordinary words were set aside:
   say so on the `phase: index built` line, since its counts include them.
3. **Keep what it left open as counts.** No agent is dispatched for those rows and nothing is
   paged to disk: `leftoverCounts` is the whole of what the run keeps, and it rides onto the
   ledger's `phase: index built` line at step 4, where the closing report reads it. The kinds are
   `unmatchedTag`, `codeNoLocation`, `codeOnlyOnReplacedPages`, `codeTooShort`, `codeIsAWord`,
   `fragmentUnresolvable`, `pageNotASheet`, `hitNotDrawable` and `overRunCap`, and
   each is reported by its count alone. The two exceptions are `codeNoLocation` and
   `codeOnlyOnReplacedPages`: where either count on the last `phase: index built` line is above
   zero, the closing report's copy step takes one `index_citations_leftover(projectId, kind: ...)`
   read of that kind, so the report can name the codes found nowhere, and the codes a later
   drawing issue dropped with the earlier sheets that printed them. One read returns up to 50
   rows; where the count is higher, the report names those 50 and says how many more there are. A
   row on the record that still names a dropped code is work the revision may have taken out; the
   report says so. Nothing in the run chases those rows: they are what the closing report names as
   still open, by count and with those codes named. A tag no
   reader resolved on its own sheet is named as a loss rather than attached by guesswork to
   whichever package it might belong to.
4. Append `phase: index built` to the ledger with the counts off the status, each kind of
   `leftoverCounts` and its count as a pair, as
   `phase: index built unmatchedTag <n> codeNoLocation <n> codeOnlyOnReplacedPages <n> ...`,
   which the closing report reads. After window 1, go to
   stage 6 step 1; after window 2 complete, fold the packages (stage 6 step 5); after window 2
   paused, stage 6 step 1 with the plan run without `--only`; after window 3, append
   `phase: window 3 complete` (stage 7 step 4).

## 6. Window 2: every sheet once

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
   `verify_unit` per sheet, your one count call, one `pass:` line each.
   After a slice, the full plan's part that holds the slice's units holds new ones beside them: it shows `units verified` below `units` and is dispatched like any unfinished
   pass, its runner skips the slice's finished units, and its new `pass:` line carries the whole
   part. A plan with no pass, as where window 1 selected or left out every sheet, lists
   `passes 0, finished 0; to dispatch: none`: no runner starts, and the window goes straight to
   step 4. You start what the listing's `start now:` names, up to six at once, and when a pass hands
   back you take its count, record it and list again as stage 4 step 3 says, then start what that
   names. Every reader reads its sheet whole, for everything
   on it, whatever trade
   the work belongs to (non-negotiable 4); the runner's overlap scan and the record's refusal of a
   create whose name the project already carries are what keep two passes running alongside each
   other from creating the same work twice.
3. **A skipped sheet stays skipped.** A sheet whose two reads both failed is named in the closing
   report and never read again in this run. A schedule or legend sheet skipped in window 1 is not
   read in window 2 either, since window 2 reads only what window 1's file does not name; the
   closing report says that later sheets may be less complete for it.
4. **Close the window** with a boundary runner, as in stage 4 step 4, then append
   `phase: window 2 complete` with the window's verified totals, run the index (stage 5, steps 1 to
   4) so the record holds every page each row appears on before any review reads it, and fold the
   packages (step 5).
   When the plan deferred sheets, the window is not closed. After the slice's passes, run the
   boundary runner, append `phase: window 2 paused units <n> ... deferred <m>` in place of
   `phase: window 2 complete`, the same verified totals the complete line carries with
   `deferred <m>` added, and then run the index, in that order, as for a complete window. The window
   picks up again at step 1 straight away, with a plan run without `--only`, which the plan script
   refuses until a `phase: index built` line follows the paused line.
   A slice whose bounds line reads `plus deferred 0` is the window's last slice: after its passes,
   run the plan once more without `--only`. Every unit in it shows verified, but that plan can fold
   one slice's part into another's pass, so before you total or close anything, start each pass
   in it that is not finished as its listing names it, as step 2 runs them, each with its own
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
   already carries; one that returns a `blocked:` line is a call that could not be made. What the
   fold did goes to the closing report, which reads `reports/fold.md` itself. Where a step needs
   the fold's `deleted:` lines, read them with one call, single quoted:

   ```sh
   python3 '<plugin root>/scripts/fold_report.py' print '<run folder>'
   ```

   It prints every line of `reports/fold.md`, one act each under its label, and stops before
   Bash's output limit; where its last line names what it did not print, run the command that
   line gives for the rest. A run whose fold ran before the folder kept a report prints one line
   saying so, and that line is no `deleted:` line. A later write can make a package for the
   owner's own work again, so where the report carries a `deleted:` line, dispatch the folder
   again with mode `recheck` before window 3 is planned on a pass whose delivery was rechecked, and
   at stage 8, and read back only its hand-back.

6. **Recheck the scope items on a new delivery.** On a pass whose delivery precondition 7 found
   sized, once the fold is done, read `recheck.md` beside this file and run it: the comparison's
   open rows copied to disk, one rechecker per sheet, the retire step for the rows the new
   delivery removed, and `phase: recheck complete`. Then go to stage 7. A pass whose delivery was
   not sized runs no recheck and goes from the fold to stage 7.

## 7. Window 3: one review per package

1. **Write the window 3 plan.** The steps before the plan run below, from the general requirements
   package to the copies, run once: on a resume after the window's first `dispatch 3` line, run
   the plan again with the files already copied and skip them. Where the fold deleted a package on
   a pass whose delivery was rechecked, dispatch the folder in mode `recheck` first, as stage 6
   step 5 says. The packages may have changed since window 1: a scope item written
   on a trade with no package makes that trade's package as it lands, so windows 1 and 2 can have
   made packages the plan has not seen. In a pass on a set, first place the general requirements:
   the Division 01 sections are on no package, since orientation places only the sections outside
   Divisions 00 and 01, and what they require still costs money. Read them with one paged
   `search(projectId, subjectPrefix: "specSection:01", predicate: "hasTitle")`. Where the project
   has no Division 01 section, skip this. Otherwise `solicitation_create_package` one package
   named `General Requirements` whose `tradeCode` is `01 11 13`, the catalog's General Contractor
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
   to `<run folder>/plan/packages-start.json` with a local command, since stage 8 compares the two,
   only where `packages-start.json` is not there yet: a baseline already moved is never written
   over.
   Then send one fresh agent to copy a fresh
   `solicitation_list_packages` response over `<run folder>/plan/packages.json`, byte for byte,
   returning one line, and one more to copy a fresh `list_spec_sections(projectId)` response, with
   no `sections` filter, over `<run folder>/plan/spec-sections.json` the same way. Then run the
   plan script for window 3. It reads no sheets and takes no inventory, and plans the window in
   two stages. Stage A is each package's chain: its manual sections, in its `manualSections`
   order, divided into manual parts of up to ten pages each, then its standard lines unit last,
   in passes `W3-M<n>` of up to ten units, the trade with the most units first and one trade's
   chains together, a trade longer than one pass running on in lettered passes (`W3-M1b`), each
   waiting for the one before it. Stage B is one review per package in passes `W3-<n>`: the
   general requirements package's review alone in the first, then up to eight reviews a pass,
   every package of one catalog trade in the same pass, a trade of more than eight packages a pass
   of its own and one of more than ten refused. Every pass of stage B starts after every pass of
   stage A, and every pass after the first after the first too. The manual plan is made once: from
   the window's first `dispatch 3` line on, a replan adds, moves and divides no manual page, and
   lists what changed since under `Manual sections not read` with its reason, a section added to a
   package, a package deleted with pages still owed, a part read twice and not confirmed. Read
   back only its bounds line. Where it refuses because the section list reads truncated, stop,
   saying the manual has more sections than one read returns, so no manual reading can be planned;
   where it refuses because window 3 of this run folder was started under an earlier plugin, stop
   and say so. Each is a window that cannot be planned. Never run the window 3 plan while a pass
   of the window is out: every replan waits until no pass is running.

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
     --sections '<run folder>/plan/spec-sections.json' \
     --out '<run folder>/read-plan.md'
   ```

2. **Run the passes** as stage 4 runs its passes, with `review-<pass id>` in place of the pass
   id, so the runner dispatches a `plumlayer:scope-manual-reader` for each manual part, a
   `plumlayer:scope-standard-lines` for each standard lines unit and a `plumlayer:scope-reviewer`
   for each review, in turn, rather than a reader. The runner's `verify_unit` against the pages
   each unit opened, your one count call over the pass's prefixes, one `pass:` line each. You
   start what `start now:` names, up to six at once, as stage 4 step 1 says: the listing holds
   each pass of reviews until every pass it starts after is finished, a unit read twice and not
   confirmed counting as finished, so no review starts before its package's manual parts and
   standard lines are settled. A manual part and a standard lines unit are units of their pass
   like any review, so the prefixes it prints for the pass carry them, and the record script
   refuses a count that leaves one out. You never read a manual section yourself, and never send an agent
   to read one outside the plan. Each manual part records what its pages put in scope and says
   what it left on its section lines; each standard lines unit writes the lines whose condition it
   finds on this job's own drawings or manual, each cited to where it found it; each review takes
   what the parts left through a script, settles its package's headings in the order the work is
   built, or on the general requirements package in the order of its seven headings, and puts the
   rows under every heading in the order the estimator reads the work.
3. **Keep the rest for the closing report.** Between passes you say only each pass's one line.
   The manual pages each manual part read, each pair of rows a review found carrying the same
   work, combined or left, and each section the read plan lists under Manual sections not read go
   to the closing report, which reads them off the run folder.

4. **Close the window.** Where every pass is finished, close with a boundary runner, then run the
   index once more (stage 5, steps 1 to 4) so the rows the reviews created carry every sheet too,
   then append
   `phase: window 3 complete` with the window's verified totals and what the third index left
   open, by count and named where it is a code found nowhere.

Spec sections account differently, since estimators never write CSI digit strings into scope
text: a manual section is accounted when a package lists it in `manualSections`. After stage 8's
amendments are applied, read `manualSectionPlacement` off a fresh `solicitation_list_packages`
call, never a local artifact: its `onNoPackage` sections are the manual sections still open,
reported the same way: append one `unplaced: <section code> <the reason you left it off>` line
for each, and where its `truncated` is true the count is incomplete, which the closing report says
off its own copy of the package list.

## 8. Amend the packages

The estimator-judgment stage. Packages are bundles of spec sections grouped by how subcontractors
actually split themselves in the market, not by the book's divisions. The baseline split was
drafted and created at orientation (`learn-project`) and folded into what one kind of firm bids
before the reviews (stage 6 step 5): read it fresh via `solicitation_list_packages(projectId)`
rather than re-drafting it. This stage is for the splits and folds a review surfaces.

First, where the fold's report carries a `deleted:` line, dispatch the folder in mode `recheck`,
as stage 6 step 5 says. In a pass on an addendum the rest of this stage runs only where the pass
made a package: one whose `id` is in
`plan/packages.json` and in no row of `plan/packages-start.json`, found with a local comparison of
the two. A pass that made none appends `phase: packages amended` with no amendment and goes to
close out; the split the earlier passes settled stands.

1. **Scope-driven amendments.** Where the scope list surfaces what the TOC cannot see (a
   specialty assembly that wants its own bidder, an alternate the set names that needs its own
   package, a package that should collapse into another once scale is understood), apply the
   amendment live:
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
   Before each amendment's calls, append `amending: <package name>: <what you did>; <the reason>`
   in the estimator's words, naming each package by its name and each trade or section it moves,
   and once they succeed, `amended:` with that text. On resume, hold each `amending:` line no
   `amended:` line follows to a fresh `solicitation_list_packages`, finish what is missing, then
   append its `amended:` line: a create is done where a live package carries the new name and its
   trade; a split where every package the line names is live with the trades and sections the line
   gives it; a collapse where the folded package is gone and the keeping package carries its trade
   as its `tradeCode` or in its `codes`; a rename where a live package carries the new name and
   none the old. No approval
   is collected: the amendment governs as applied and stays editable; a correction is a tool call.
   Once the amendments are applied, append `phase: packages amended` to the ledger.
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

Trade responsibility is already on the record: every item carries its one trade from the moment
it was written, the one most likely to carry it where the reader was unsure.
Sheet-to-package assignment (`assign_sheet_packages`)
is the user's call: offer it only when the user asks; the relevant-pages list already falls out of
the citations.

## 9. Close out

The close-out is three facts, in this order, and a session that stops between two of them
resumes at the next: the report file is written; you have said its short version with the link;
`phase: closed out` is appended. A session that stops after the short version and before the line
says the short version again, which is accepted.

1. **Write the closing report.** Run, single quoted:

   ```sh
   python3 '<plugin root>/scripts/close_report.py' ids '<run folder>' --project <projectId>
   ```

   It writes `<run folder>/reports/close-ids.txt`, one call a line, `<file name> <verb>
   <arguments>`, and prints one line. Send one fresh agent to make the calls, with the copy below,
   and read its one line and nothing else. Then run, single quoted, with `--delivery-plan` only on
   a pass whose delivery was sized:

   ```sh
   python3 '<plugin root>/scripts/close_report.py' write '<run folder>' [--delivery-plan '<plan file>']
   ```

   It writes `<run folder>/closing-report.md` whole and prints its short version. It never refuses
   for want of an input: where the copy failed, or the fold, the recheck or the general
   requirements package left nothing on file, the report says what is not available and why, and
   names items it could not look up as a count by package. Where it exits 1, the file could not be
   written: say no short version, and run it again; where it exits 1 again, say in one sentence
   that the report could not be written, with what it printed. Say the short version only after it
   exits 0. You never write the report yourself,
   and never read the run's notes to retell them: the script chooses what appears, in what order,
   once each, and every id it prints is a name off a copy.

   ```text
   run_in_background: false
   Copy the closing report's lookups for project <projectId> to disk. This is your whole job. Do
   nothing else, and end when it is done.

   1. Read <run folder>/reports/close-ids.txt. Each line is `<file name> <verb> <arguments>`, the
      arguments one JSON object.
   2. For each line, call the plugin's tool of that verb with those arguments, exactly as written.
   3. Where a call's result came back as a path to a file on disk, copy that file to
      `<run folder>/plan/close/<file name>` with the Bash tool. Copy it. Never retype it. Where it
      came back inline, write the whole response object there yourself, as JSON, and say so in your
      returned line.
   4. Where a call cannot be made, because Claude Code refused it, your sign-in failed, or
      Plumlayer did not answer after one try more, skip it and go on to the next.
   5. Return exactly one line: calls made, files on disk, calls skipped and why. No account of what
      the responses hold.
   ```

2. **Say the short version, with the link.**

<!-- user-facing -->
   Say the short version in your own words, a few plain sentences: that the run finished and how
   long it took, the sheets read, the items added with the trades that got the most, the
   Questions raised, how many things could not be read and up to five of them by name, how many
   items are flagged to look at, how many package changes, and the link to the full report, the
   way `size-delivery.md` links its plan. Never paste the script's lines as they printed.
<!-- /user-facing -->

3. **Append `phase: closed out`.**

The report the script writes reads, in this order, a short body and then the detail:

<!-- user-facing -->
```text
Scope run on <set label>: finished <date and time>, <h> hours <m> minutes after reading started.

I read <n> of the <m> sheets and <p> pages of the project manual. I added <a> items and updated <u>.
The package reviews combined <c> items into another item that carries the same work. I raised <q>
Questions and replied on <r>. Each trade's page on plumlayer.com shows its items, and every item
lists the sheets that say what it is.

What I could not read
- <sheet>: I read it <k> times and could not confirm what I wrote. The last time, <plain reason>.
  Anything it wrote stays on the scope list. Check this sheet yourself.
- The <package> review, or manual pages for <package> (section <code>, pages <a> to <b>): the same.
- <sheet>, <part>: it is a scan, and I could not read that part from its picture.
- Left out of the read plan at the start: <sheets> (<the reason given>).
- Section <code>, or its pages <a> to <b>, for <package>: no unit read it, because <reason>.
- <package>: I could not search for <words>. Search them in the drawings on plumlayer.com.

Questions, by trade
- <trade>: <n>; ... Every trade: <n>. Trade not known yet: <n>. <q> raised by this run.

To look at
- <sheet or package>: <note>.
- Items I was not sure how finely to split: ...
- For you to decide: ...
- Items that may be the same work twice: ...
- Items that carry the same work: Combined: <kept> and <other>. Tell me to put the retired item back.
  Left for you: <kept> and <other>. Retire one on the site or tell me to.
- Requirements read and not written: ...

Package changes
- <one sentence per fold act, then each amendment, then the general requirements package>

The recheck of the new drawings (only on a new delivery)
- <by package: carried forward, cited again, changed, removed, left for you>

Still open
- <n> tags I could not match to any item, and <n> codes found on no page. Codes found nowhere: ...
- Codes a later drawing issue dropped: ...

What went wrong along the way
- <counts in plain words, a count the record held short of first>

In detail: the manual sections read by package, each check that failed and how it was fixed, each
fold act and how to undo it, the packages a pass on an addendum did not review, what was newly
defined, and the items added by trade.
```
<!-- /user-facing -->

The report's figures each come off the run folder, as the table in `close_report.py` names: items
added off the trades files, each unit once, never off a `pass:` line's `created`, which counts
entries; the time off `phase: reading started`; the Questions by trade off the copy of
`list_questions` with `limit: 0`; the manual sections and pages no unit read off the window 3 read
plan's `## Manual sections not read`, each package's standard lines not written where its standard
lines unit was skipped, its headings and row order not settled where its review was skipped, and
each package that took a row from another package's review after its own review finished, off the
ledger, and the scanned sheets off the `anomaly` notes that carry
`not read from the picture:`, each sheet and part once. Every item a reader was not sure how finely
to split goes under its own heading, all of them, and the short version gives their count. On a
pass on an addendum it names the packages it did not review and why, off the window 3 read plan.
What I could not read and the short version's count of it are printed from one list, and the
report says every sheet and manual page planned was read and checked only where each window's
planned units, held one by one to the ledger, all verified ok and that list is empty; on an early
stop it says what was planned, what was finished and what was not started.

## The dispatches and the report shapes

Every dispatch carries pointers and nothing else. Whatever is pasted into a dispatch stays in the
dispatcher's context for the rest of the run, so the read plan and the brief values are opened by
the agent that needs them, from the paths it is handed, and the record is read by the agent that
needs it. Every template below names `run_in_background: false` for the session whose Agent tool
takes it, where the call is then the wait, because a headless session stops a background agent
after ten idle minutes. Where the call comes back with an agent id, you wait as the windows section
says, by ending the turn.

The mandates are not in these templates. They live in the six agent definitions the plugin ships
for this run, `scope-round-runner`, `scope-vocabulary-reader`, `scope-reader`, `scope-reviewer`,
`scope-rechecker` and `scope-package-folder`,
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
Read again: none.
Run your pass as your definition says.
```

`Read again:` reads `none` in windows 1, 2 and 3: a skipped unit is never read again by this run.
The recheck's runners take the dispatch `recheck.md` step 4 gives, with window `r`. The runner's
definition owns every path under the run folder: the read plan is always
`<run folder>/read-plan.md`, and the summary file and the hand-back it returns are its own to
write. The `Scripts:` line is the plugin's own scripts directory, the path you already resolved for
your plan script calls: the runner sums its pass with the script that sits there, and a runner
handed no path would have to guess one.

**Package folder dispatch** (the lead writes this, once when window 2 closes with mode `fold`, and
with mode `recheck` where the fold report carries a `deleted:` line, before window 3 is planned on
a pass whose delivery was rechecked and at stage 8):

```text
subagent_type: plumlayer:scope-package-folder
run_in_background: false
Project: <projectId>. Mode: <fold or recheck>.
Run folder: <path>. Plugin root: <path to the plugin directory>.
Run your mode as your definition says.
```

The `Plugin root:` line is the plugin directory you already resolved for your script calls: the
folder reads `agents/orientation.md` step 8's default carries there and prints its hand-back with the
script beside yours.

**The package folder's hand-back** is printed by `fold_report.py` and is the whole of what the
fold puts in your context; the acts stay in `reports/fold.md`:

```text
fold: packages <n> before, <n> after
acts: folded <n>, split <n>, moved <n>, deleted <n>, kept <n>
records: rows re-homed <n>, questions <n>
phase: packages folded appended
report: <run folder>/reports/fold.md
```

**Reader dispatch** (the runner writes this, once per read unit, in windows 1 and 2):

```text
subagent_type: <plumlayer:scope-vocabulary-reader in window 1, plumlayer:scope-reader in window 2>
run_in_background: false
Project: <projectId>. Window: <n>. Pass: <pass id>. Unit: <unit id>.
Read: <the number of this read of the unit, its own dispatch line counted>.
Owed: <run folder>/owed/<unit id>.read-<k>.md on a read after the first, or none.
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
Read: <the number of this read of the unit, its own dispatch line counted>.
Owed: <run folder>/owed/<unit id>.read-<k>.md on a read after the first, or none.
Reviewing: <the package's catalog trade id>. Package: <the package id>.
Run folder: <path>. Pass brief: <path to briefs/<pass-id>.md>.
Reader definition: <scripts path>/../agents/scope-reader.md, written out in full.
Review your package as your definition says, write your report to
<run folder>/reports/<unit id>.md, then return it.
```

The package's `codes`, `manualSections` and `notes` are not in that dispatch: the reviewer reads
them off the record with `solicitation_get_package`, so the manual sections it checks and the work
the notes put on the package have one source and are the ones the record holds when the review
runs.

**Manual part dispatch** (the runner writes this for a manual part unit, with its `After:` and
`Reads:` lines copied off the unit line, `After: none` for a package's first part):

```text
subagent_type: plumlayer:scope-manual-reader
run_in_background: false
Project: <projectId>. Window: 3. Pass: <pass id>. Unit: <manual part unit id>.
Read: <the number of this read of the unit, its own dispatch line counted>.
Owed: <run folder>/owed/<unit id>.read-<k>.md on a read after the first, or none.
Reviewing: <the package's catalog trade id>. Package: <the package id>.
After: <the unit id after "manual part after" on the unit line>.
Reads: <the spans after "reads" on the unit line, as written there>.
Run folder: <path>. Pass brief: <path to briefs/<pass-id>.md>.
Reader definition: <scripts path>/../agents/scope-reader.md, written out in full.
Reviewer definition: <scripts path>/../agents/scope-reviewer.md, written out in full.
Read your pages as your definition says, write your report to
<run folder>/reports/<unit id>.md, then return it.
```

A manual part reads exactly the pages its `Reads:` line names, and the opening pages of a section
it starts partway into, for what that section's Part 1 says, and it reads what the part before it
carried over in `<run folder>/carry/<the unit after After>.md`.

**Standard lines dispatch** (the runner writes this for a standard lines unit, the one whose line
carries `, standard lines after `):

```text
subagent_type: plumlayer:scope-standard-lines
run_in_background: false
Project: <projectId>. Window: 3. Pass: <pass id>. Unit: <standard lines unit id>.
Read: <the number of this read of the unit, its own dispatch line counted>.
Owed: <run folder>/owed/<unit id>.read-<k>.md on a read after the first, or none.
Reviewing: <the package's catalog trade id>. Package: <the package id>.
Review: <the unit id less its s-1>.
Run folder: <path>. Pass brief: <path to briefs/<pass-id>.md>. Scripts: <scripts path>.
Reader definition: <scripts path>/../agents/scope-reader.md, written out in full.
Reviewer definition: <scripts path>/../agents/scope-reviewer.md, written out in full.
Write your package's standard lines as your definition says, write your report to
<run folder>/reports/<unit id>.md, then return it.
```

**The reader's report** comes back in this shape, counts and named anomalies only:

```text
unit: <unit id>   pass: <pass id>   window: <n>
pages read: <sheet number + pageInPdf, renders taken and the reason for each, and `read from the picture` with why the text was thin where you read it from a render, one per page>
pages unread: <sheet number + pageInPdf + reason, each page or part of one not read from the picture as `<sheet> p<page> not read from the picture: <what is left>, <why>`, or "none">
cited sheets: <for the repeated lines, every sheet the unit's rows and citations name, comma separated; otherwise "none">
page citations: <for the repeated lines, subject + fileId + pageInPdf of every update cited to a page with no sheet number, one per line; otherwise "none">
set version: <for the repeated lines, the setVersion the unit's walk ended on; otherwise "none">
created: <n>   updated: <n>   questions raised: <n>   questions replied: <n>
created subjects: <the subject of every scope item created, each under the unit's prefix, or "none">
updated subjects: <the subject of every item updated or newly cited, except a row cited only to a Question, or "none">
questions raised ids: <the id of every Question raised, or "none">
questions replied ids: <the id of every Question replied to, or "none">
questions linked: <the id of every Question raised or replied to + the subject of every row it was cited on, one Question per line, or "none">
sent: <n>   landed: <n>   conflicts: <ids and how each resolved, or "none">
trades: <trade id + item count, one per trade>
trades touched: <the catalog id of every pre-existing row the reader updated or newly cited, and of every trade a Question it raised names, one per line, or "none">
definitions kinds added: <kinds, or "none">
schedules under rows: <each kind the reader put under a row + that row's subject, one per line, or "none">
sheet readings written: <sheet number, one per sheet whose reading was recorded, or "none">
anomalies: <one line each, with sheet and page, ending with a comma and where it landed, one of Question <id>, reply <id>, sheet reading, or run only, the Question named by the full id `ask_question` returned (its `question:` subject) and a reply by the id `reply_question` returned, never shortened; or "none">
grain questions: <one line each, with sheet and page, or "none">
door-owned suggestions: <one line each, or "none">
owed: <each `not written by read` line of the Owed file, copied whole, then ` | ` and `written <subject>`, `read, nothing to write` or `not written, <why>`, and each `check read` line of an update, a field update, a Question on a row, a manual update or a page citation, copied whole, then ` | ` and `written <subject>` or `not needed, <why>`, one per line, or "none">
```

`cited sheets:` is what the runner verifies a repeated lines unit against, since that unit reads a
file and has no sheet of its own; `page citations:` names the updates it cited to a page with no
sheet number, which no sheet verifies, so the runner finds each back by its subject; and `set
version:` is what the runner puts on the ledger for the window 2 plan to mark that file's sheets by. `created:` is the reader's own item count, not the entries under those items. `updated:` counts
every pre-existing item the reader wrote anything onto, a value or a citation alike.
`sent:` and `landed:` count every write the reader made for the unit, across every call, not only
its first batch.

The `updated subjects:`, `questions raised ids:` and `questions replied ids:` lines are what let
the runner find those writes back: a create is findable by its `scopeItem:<unit-id>-` prefix, an
update lands on a subject that already existed, a raise on a fresh Question id and a reply on the
id of a Question somebody else raised, and nothing else in the report names them. The
`created subjects:` line names each create, which the runner holds to the unit's prefix and finds
back by name among the subjects the record lists under it; a report without it reads as a
mismatch. The runner holds every report of windows 1, 2 and 3 to the report script's check before
it verifies: every line of the shape there, `created:` and `questions raised:` each equal to its
own list, `questions replied:` above 0 with at least one id on its list and never fewer replies
than ids, and 0 with none, and on a read after
the first, `owed:` answering the Owed file. The file is the report; where it is missing or not
whole, the runner checks the reader's returned message the same way and verifies off that, and
where neither is whole the read ended with no report.

**The runner's summary** is written in this shape by the summary script the runner runs, to
`<run folder>/reports/<pass id>.md`, where `lead_pass.py` reads it when you record the pass; you
never read it yourself. `created` is an entry count under each unit's prefix,
never the reader's own item count, which travels separately as `items`. The `review:` line is
window 3's only, the pages opened and the searches run added up over the reports of the pass's
units verified ok, and beside them the units whose report was restored from the record:

```text
window: <n>   pass: <pass id>
units read: <unit ids, in reading order>
per unit: <unit id> created <n> items <n> updated <n> questions <n> replied <n> <"read twice" where its runner read it again> verified <yes/no/skipped>
totals verified: created <n> (entry count under the unit prefixes), items <n> (reader's own item count), updated <n>, questions <n> replied <n>
trades: <trade id + item count, one per trade>
conflicting rows: <n>, on units <unit ids>, or "none"
overlap notes: <item name + the two units, one per line, or "none">
anomalies: <one line each, with sheet and page, or "none">
unread pages: <sheet + page + reason, one per line, or "none">
grain questions: <one line each, as the report wrote it, or "none">
door-owned suggestions: <one line each, as the report wrote it, or "none">
definitions kinds added: <kinds, or "none">
deviations and repairs: <one line each, or "none">
review: pages opened <n>, searches <n>, reports restored <n>
ledger: <path>, appended through <last line written>
ledger lines: <whole lines read> sha256 <the hash of those lines>
```

**The runner's hand-back** is what the runner returns to you, printed by the same script, and the
whole of what a pass's report puts in your context. The `review:` line is window 3's only:

```text
window: <n>   pass: <pass id>
units: <n>, verified <k>
unverified: <unit id + mismatch | read <k> no verified line, one per line, or "none">
skipped: <unit id + its unread note, one per line, or "none">
stopped: <unit id + the note that stopped it, one per line, or "none">
unread: <each other unread note verbatim, or "none">
notes: anomalies <n>, overlaps <n>, deviations <n>, kinds <n>
review: pages opened <n>, searches <n>, reports restored <n>
report: <run folder>/reports/<pass id>.md
```

**The reviewer's report** comes back in this shape, and the summary script reads its
`pages opened:` and `searches:` lines into the summary's `review:` line, which is where the
`pass:` line's `pages-opened` and `searches` fields come from:

```text
unit: <unit id>   package: <package name>   trade: <catalog id>   window: 3
harvested: rows <n>, definition codes <n>, spec sections <n>, aliases <n>
notes read: <each item the package notes name + the row that carries it, created or found, or `shown nowhere`, one per line, or "none">
searches: <n> run, <n> returned nothing
terms too general: <term + its page count, one per line, or "none">
pages opened: <sheet number + fileId + page + the term that sent it + what it did, one per line, or "none">
created: <n>   updated: <n>   questions raised: <n>   questions replied: <n>
created subjects: <the subject of every row created, each under the unit's prefix, or "none">
updated subjects: <the subject of every row updated or newly cited, except a row cited only to a Question, or "none">
manual updates: <each new citation of a manual page made in the review on a row on `updated subjects:`: the subject + the section code + the page, one per line, or "none">
field updates: <each write made in the review onto a row on `updated subjects:` that carries no new citation, a heading aside, one write per line: the subject + the predicate written + the page its evidence names, as that page's sheet number, `section <code>` on a manual page or `none` where it prints no number, + its fileId + its page, or `no page` where its evidence names none; or "none">
questions raised ids: <the id of every Question raised, or "none">
questions replied ids: <the id of every Question replied to, or "none">
questions linked: <the id of every Question raised or replied to + the subject of every row it was cited on, one Question per line, or "none">
questions alone: <the id of every Question raised or replied to that no row carries + why, one per line, or "none">
sent: <n>   landed: <n>   conflicts: <ids and how each resolved, or "none">
trades: <trade id + item count, one per trade>
sheet readings written: <sheet number, one per sheet whose reading was recorded, or "none">
anomalies: <one line each, with sheet and page, ending with a comma and where it landed, one of Question <id>, reply <id>, sheet reading, or run only, the Question named by the full id `ask_question` returned (its `question:` subject) and a reply by the id `reply_question` returned, never shortened; or "none">
grain questions: <one line each, naming the grain and the rows, or "none">
silent sections: <section code + the Question id, or `left open` + its reason, `the sheets select none of it` or `closed Question <id>`, + the words searched, one per line, or "none">
unspecified work: <row family + the Question id, or `left open, closed Question <id>`, + the words searched, one per line, or "none">
compared: <subject + the sources compared + what you found + how it ended: Question <id>, `agree`, `closed Question <id>`, `not settled`, or `not reached`, one per line, or "none">
left by the parts: <each `left` item the notes script printed, + `written <subject>` or `not written, <why>`, one per line, or "none">
sections not checked: <one per line, the section code + the reason: "not read" or "not known" with the reason the notes script printed, "searches spent", "notes not read", "the owner's work", "no manual sections on this package", "the manual was not read in"; or "none">
families not checked: <row family + the reason, one per line, or "none">
standard lines found later: <each line as `<the line's row name> | <sheet and page, or section and page> | <what you found>`, one per line, or "none">
headings written: <the headings in their order on the first line, then each row whose heading was written + its subject + the heading, one per line, or "none">
rows ordered: <each heading on the first line of `headings written:`, in that order + its count of home rows + `changed`, `as it stood`, `one row`, `over 500 rows` or `refused`, one per line, or "none">
rows on other packages: <the full subject of every row on another package's trade created or written onto + that trade's catalog id, as `<subject> | <catalog id>`, one per line, or "none">
bounds reached: <each read whose limit was reached, as `<the read> <its limit>: <what it left>`, one per line, or "none">
door-owned suggestions: <one line each, or "none">
not written: <each requirement a page gives the package that was not written, as `<section code + page, or sheet + page> | <what the page gives> | <the subject of the row it belongs on, or no row> | <why>`, one per line, or "none">
owed: <each `not written by read` line of the Owed file, copied whole, then ` | ` and `written <subject>` or `not written, <why>`, and each `check read` line of an update, a field update, a Question on a row, a manual update or a page citation, copied whole, then ` | ` and `written <subject>` or `not needed, <why>`, one per line, or "none">
```

A boundary runner returns this shape instead, or the one line `blocked: <tool> <class>` where a
call of its own could not be made:

```text
window: <n>   pass: boundary
cross-pass overlaps: <item name + the two units, one per line, or "none", or "not checked, names missing for <n> units" + the passes>
names scanned: <the figures off the scan's last line: new item names read, units, passes>
kinds declared: <n>
ledger: <path>, appended through <last line written>
```

## The words the user reads

Everything you say to the user, between passes, at a stop, in the closing report or anywhere else
in the run, names things the way an estimator does. The scripts, the ledger, the reports and the
record name them by id. Those ids stay in the run's files and in what only the agents read, and
you never say one. For each kind:

| The run's own name | What you say |
|---|---|
| A pass id (`A2a`, `i1-E2c`, `i1-W3-4`) | What it read, as the line under its `pass:` line gives it: "the fire alarm sheets", "the first architectural sheets, the A3 sections and the A6 roof details", or the packages it reviewed, by name. |
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

When you say who put something on the record, a row or a Question the run wrote, it is
the user's work, credited to them, and you never name an agent as its author ("by the agent's
judgment", "the reader put it on"). What you chose on your own reading, you say as your own
choice: "I put it on Plumbing; move it if it belongs elsewhere."

## What this skill does not do

- **Upload or recognize drawings** (`drawing-upload`), **create projects** (`project-setup`),
  **read sub proposals** (`bid-intake`), **place takeoff measurements** (`takeoff`), **get the
  invitations ready** (`prepare-invitations`, which does not wait for this run), **draft the
  baseline package split** (owned by `learn-project`).
- **Author value engineering enrollments**: whether an item is a value engineering option stays
  the user's call at the package surface. The run marks each alternate the set names as an
  alternate. The run writes exclusions where the paper says work is by others, and every trade except `01 11 13` has its general items in its General
  Requirements section. On `01 11 13`, there is no `General Items` row and no `general-requirement`
  role; a general cost the contractor carries there is a home row under one of the seven headings.
  Exclusion rows keep their Exclusions section on this package as on every package. A row shared
  with another package keeps its category there; the seven apply to rows whose home is `01 11 13`.
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
- **Read a skipped unit again**: a sheet, review or manual part whose two reads both failed is
  named in the closing report, and this run never reads it again.
- **Write or read a settings file, or approve its own tools**: what Claude Code asks the user to
  allow is the user's to answer.

## What this skill never runs

Do not restore or run per-trade fan-out / reconcile-by-overlap machinery as a scope path, and never
present it as current: every pass writes onto the one shared list against the live record, and
nothing is reconciled afterward. Do not restore rounds, legs, or the completeness accounting as
stages; the index and the reviews are what replaced them. Do not restore a window that reads
sheets for one trade: the set is read once, sheet by sheet, and a package is reached through its
review.
