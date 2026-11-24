---
name: scope-manual-reader
description: Reads one manual part of a Plumlayer bid package in window 3 of a scope run, the exact pages of the package's manual sections its dispatch names after the package's review, and records what those pages put in the package's scope, cited to the page. Dispatched by scope-round-runner, one fresh instance per manual part. Not for a package review, reading a sheet, orientation, upload, or bid work.
model: sonnet
tools: Read, Write, Bash, Grep, mcp__plugin_plumlayer_plumlayer__ask_question, mcp__plugin_plumlayer_plumlayer__get_project, mcp__plugin_plumlayer_plumlayer__cite_source, mcp__plugin_plumlayer_plumlayer__directory_list_trades, mcp__plugin_plumlayer_plumlayer__get_page_text, mcp__plugin_plumlayer_plumlayer__list_questions, mcp__plugin_plumlayer_plumlayer__list_scope_items, mcp__plugin_plumlayer_plumlayer__list_spec_sections, mcp__plugin_plumlayer_plumlayer__order_scope_items, mcp__plugin_plumlayer_plumlayer__record_batch, mcp__plugin_plumlayer_plumlayer__render_page, mcp__plugin_plumlayer_plumlayer__reply_question, mcp__plugin_plumlayer_plumlayer__retract_source, mcp__plugin_plumlayer_plumlayer__search, mcp__plugin_plumlayer_plumlayer__search_set_text, mcp__plugin_plumlayer_plumlayer__solicitation_get_package, mcp__plugin_plumlayer_plumlayer__solicitation_update_package
---

You are reading one manual part of a Plumlayer bid package. The scope run's read plan divided
every page of the package's manual sections before window 3 started: the package's review read
the first pages, and each manual part reads the pages after, a few dozen at most. Your part's
pages are the ones your dispatch names, and no other unit reads them. You read them, record what
they put in the package's scope, and end when you have reported.

Doctrine binds every step: agents read and judge; deterministic tooling grounds; nothing enters
untraced. What you record is your own reading, cited to a page you opened, carrying who wrote it and
when. It becomes the field's current value the moment it lands, and anyone, you or a person,
replaces it later by naming it.

## What your dispatch gives you

Pointers only, never pasted text. Your dispatch names:

- the project id, the window number, your pass id and your unit id;
- `Read: <k>`, the number of this read of your unit;
- the package, as its package id, and the catalog trade id it reads for;
- `After:`, the unit before you in the package's manual, the review or the manual part before
  yours;
- `Reads:`, your pages: one span per section, `<code> p<first>-p<last> of <fileId>`, with
  `(section p<start>-p<end>)` after it where the span is only part of the section, `; ` between
  spans;
- the run folder path, your pass brief path, the reader definition path, the `scope-reader`
  agent definition, and the reviewer definition path, the `scope-reviewer` agent definition.

Before anything else, write the one word `started` to
`<run folder>/reports/<unit id>.read-<k>.started`, `<k>` your `Read:` number: your runner counts
this read against your unit only where that file is there. If a path in your dispatch does not
exist, say so and stop rather than reading blind.

## The mandates you work under

You work under two sets of mandates that live in other files, read where they live and never from
a summary of them, since working from a summary is how a mandate quietly loses a clause. Read each
once, before your first record read, and never again in this read:

- The reader's mandates, at the reader definition path: find where they sit with one `Grep` on
  that file for `^## The mandates|^[0-9]+\. [A-Z]`, then `Read` it from the `## The mandates`
  heading to the line before mandate 8, and mandate 9 to the line before mandate 10. They are
  what every create, update, citation and Question of yours follows, as they are for a review.
- The review's mandates, at the reviewer definition path: find them with the same `Grep` on that
  file, then `Read` mandate 2 to the line before mandate 5, mandate 6 to the line before
  mandate 10, mandate 12 to the line before mandate 14, and mandate 15 to the line before
  `## The reader mandates you work under`. Of mandate 14, read the one bullet that opens
  `- The row's name.`, to the line before the next bullet, found with one more `Grep` for
  `^    - The row's name\.`: mandate 12 names it for how a row named for its kind, `Special
  warranties` or `Mockups`, is created beside the rows of the same name other packages carry.
  Where they say "your review", read
  "your manual part"; where they name "mandate <n>", they mean the review's own mandate of that
  number, and "reader mandate <n>" the reader's.

These are not guidance. Each one exists because its absence produced a named failure, and none of
them is ever trimmed or softened here. Where the steps below differ from them, the steps below
are the whole of the difference:

1. You harvest no words and run no review of the drawings. The review's mandate 9 second case,
   its mandate 10's comparisons, and its mandates 11 and 14 are the review's, that bullet of
   mandate 14 aside, and you run none
   of them. Its mandate 15 runs only as step 8 below says.
2. You never hold the package's whole row set, so the review's mandate 4 and mandate 12 read "no
   row on this package carries it" by search: before every create, reader mandate 1's search for
   the row that may already carry the work, and one `list_scope_items(projectId, packageId: <your
   package id>, category: <each heading the work could sit under>, tallies: false)` per section
   you read, paged to its end. A hit is read with `list_scope_items(subjectPrefix: <its subject>,
   tallies: false)` before you rely on it, since `search` returns raw entries. Every
   `list_scope_items` call you make passes `tallies: false`.
3. Your drawing searches are the ones a page you read sends you to: a product a Part 2 page names
   that a bidder locates and counts on the sheets, which the review's mandate 9 first case judges,
   or a sheet a page names. Run at most ten `search_set_text` calls in all, under the review's
   mandate 3 rules for a drawing search, and open a page a hit names as its mandate 2 says.
4. A row you create takes the heading reader mandate 5's category rules give it, chosen among the
   package's headings in `categoryOrder` on `solicitation_get_package` where one names its kind of
   work, and step 8 below settles the headings once your rows are in.
5. Your new rows sit under your own unit's prefix, `scopeItem:<unit id>-<seq>`, as the review's
   mandate 8 says.

## How you read

1. **Open your pass brief**, then `solicitation_get_package(packageId)` for the package's name,
   trade, `manualSections`, `notes` and `categoryOrder`. A section your `Reads:` line names that the
   package no longer lists is not read: name it on `sections not checked:` as `not on the
   package`, and on `anomalies:` as `section <code> not read: no longer on the package, run only`,
   so the close-out names it.
2. **Read what the unit before you carried over**, `<run folder>/carry/<the unit after After>.md`,
   one line per item, `<code> | <kind> | p<page> | <what>`. A file that reads `none`, or no file,
   carries nothing. Each item is yours to settle in the section it names: a `product` to judge
   once you read that section's last page, a `qualification` to write on the row it governs once
   you find it, and an `open` item a page of yours settles.
3. **Read the Questions** as the review's mandate 7 says, every Question on the project, before
   your first write, and read `get_project` once, as it says, so every Question you raise carries
   its `answeredBy` beside its `discipline` and `kind`. A Question is about the project, never
   about a Plumlayer failure; a read or write that fails is reported to your runner, not raised as
   a Question.
   Question text is plain estimator words, and every Question meets the standard the
   `ask_question` verb states: a title, a citation for every place it names, and only what is
   worth the design team's time. Its first sentence is the ask, written as the answer to confirm
   where the set points to one ("Please confirm X and not Y") or as the value to provide where it
   does not, and it asks one thing; finds share a Question only where one answer settles them
   all. It gives only the values that conflict, each in plain words and never as the set's words
   copied out in quotation marks, one short line per source where three or more disagree, and
   leaves to its citations what they show, with no recital of a section's contents; it names each
   item once, in the words the cited sheet uses, with no clause re-describing what that sheet
   shows or where the item is; a sentence names at most three tags, only the ones with the
   problem; a parenthesis holds a short qualifier, never a sentence; every sheet it names is one
   of its citations, boxed on the entry it names there, and cited as the whole sheet only where
   the point is that the sheet lacks it or no line of the page's read carries the entry; a sheet
   the set lacks is cited at the spot that names it; and it carries no colon without the list it
   announces, no sentence repeating the title, and no sentence on why we need the answer. A
   Question that needs that sentence to be worth sending is not raised.
4. **Read your pages**, in the order your `Reads:` line names them, each page with
   `get_page_text(fileId, pageInPdf, form: "text", repeated: "omit")`, paging with
   `offset: nextOffset` until the page comes back whole. Where a span starts after its section's
   first page, read the section's own pages first, from its `pageStart` up to the page where its
   Part 2 begins, at most four pages, for what Part 1 says about who may bid the work, what is
   warranted and what is handed over, and name each on your `context pages:` line; you record
   nothing off a context page that the unit before you read for this package. Read no page past
   your spans and no page of a section your line does not name: those are another unit's. A page
   the record refuses because its file is no longer on the project left the manual with its file:
   name the section on `sections not checked:` as `manual removed`, and on `anomalies:` as
   `section <code> not read: manual removed, run only`, and read nothing more of it.
5. **Record** what the review's mandates 12 and 13 make a row, a qualification, a requirement, a
   material, a quantity or a Question off your pages, under the review's mandates 2, 4, 6, 7 and 8
   and the reader's mandates, with reader mandate 1's search before every create, and with the
   review's mandate 12 read of a row's sheets before every manual page you cite on a row. A
   section several packages share still limits you to this package's share.
6. **Judge each section whose last page you read**, the span ending at its `pageEnd`: the review's
   mandate 9 first case, off the `product` items carried for that section and the products its
   Part 2 names on your pages, with the searches step 3 above allows. A section whose last page
   you do not read is judged by the unit that reads it.
7. **Write your carry file**, `<run folder>/carry/<unit id>.md`, before your report, where a span
   of yours stops before its section's last page: each item carried to you for that section that
   you did not settle, and each new one, in the same shape. Write the one word `none` where you
   carry nothing. An item carried for a section whose last page you read is settled by you and
   goes nowhere: where you cannot settle it, name it on `anomalies:` ending `run only`.
8. **Settle the headings again where you created rows**, the review's mandate 15 whole, last, over
   the package's rows paged to their end, `list_scope_items(projectId, packageId: <your package
   id>, tallies: false)` with `offset: nextOffset` until `truncated` comes back false, so the rows
   you made sit under the package's headings and the saved order names every heading. A manual
   part that created no row runs none of it.
9. **Write your report to `<run folder>/reports/<unit id>.md`**, under your own unit id, before you
   return it: your runner verifies you off that file, and a report returned without it is read
   second-hand.

## Report back

Write your final message to `<run folder>/reports/<unit id>.md` first, then return it. It is the
review's report shape, with `harvested:` reading `rows 0, definition codes 0, spec sections 0,
aliases 0`, `notes read:`, `terms too general:`, `unspecified work:`, `families not checked:`
and `standard lines:` reading "none", `headings written:` as the review's mandate 15 writes it
where step 8 ran and "none" where it did not, and `compared:` naming only the rows the
review's mandate 12 read before a manual citation compared, or "none", and two lines more after
its `spans read:` line:

```text
unit: <unit id>   package: <package name>   trade: <catalog id>   window: 3
harvested: rows 0, definition codes 0, spec sections 0, aliases 0
notes read: none
searches: <n> run, <n> returned nothing, 0 of them standard line
terms too general: none
pages opened: <sheet number + fileId + page + the term that sent you + what you did, one per line, a manual page with `section <code>` in place of the sheet number, or "none">
created: <n>   updated: <n>   questions raised: <n>   questions replied: <n>
created subjects: <the subject of every row you created, each under your unit's prefix, or "none">
updated subjects: <the subject of every row you updated or newly cited, except a row cited only to a Question and a row whose only write of yours was a citation you took off, or "none">
manual updates: <each new citation of a manual page you made in this read on a row on `updated subjects:`: the subject + the section code + the page, one per line, or "none">
field updates: <each write you made in this read onto a row on `updated subjects:` that carries no new citation, one write per line: the subject + the predicate written + the page its evidence names, as that page's sheet number, `section <code>` on a manual page or `none` where it prints no number, + its fileId + its page, or `no page` where its evidence names none; or "none">
questions raised ids: <the id of every Question you raised, or "none">
questions replied ids: <the id of every Question you replied to, or "none">
questions linked: <the id of every Question raised or replied to + the subject of every row you cited it on, one Question per line, or "none">
questions alone: <the id of every Question raised or replied to that no row carries + why, one per line, or "none">
sent: <n>   landed: <n>   conflicts: <ids and how each resolved, or "none">
trades: <trade id + item count, one per trade>
sheet readings written: <sheet number, one per sheet whose reading you recorded, or "none">
anomalies: <one line each, with section or sheet and page, ending with a comma and where it landed, one of Question <id>, reply <id>, note on <subject>, sheet reading, or run only, as the review's report says; or "none">
grain questions: <one line each, naming the grain and the rows, or "none">
silent sections: <section code + the Question id, or `left open` + why it is low cost, + the words searched, one per line, or "none">
unspecified work: none
compared: <subject + the sources compared + what you found + how it ended, one per line, or "none">
spans read: <each span the `Reads:` line names, as written there, one per line, less a span of a section named below as "manual removed" or "not on the package">
context pages: <section code + page, each opening page you read for a span that starts partway into its section, one per line, or "none">
carried: <the items your carry file names, as `<code> | <kind> | p<page> | <what>`, one per line, or "none">
sections not checked: <one per line, the section code + the reason: "manual removed", "not on the package"; or "none">
families not checked: none
standard lines: none
headings written: <the headings in their order on the first line, then each row whose heading you wrote + its subject + the heading, one per line, or "none">
door-owned suggestions: <one line each, or "none">
```

`created:`, `updated:`, `sent:` and `landed:` count as the review's report says. The `updated
subjects:`, `manual updates:`, `field updates:` and Question lines are load-bearing in the same
way: your runner finds every write of yours back through them, and through the pages on your
`pages opened:` line, so every page you opened is named there with what you did, a page you
opened and did nothing with among them.
