---
name: project-record
description: >
  Read or add to a Plumlayer project record: the drawing set, scope items, takeoff data, and
  Questions. Use when the user asks "what's in my project" or says "/project-record". Drives
  set_grid, search, list_scope_items, record, record_batch, and the Question verbs:
  list_questions, read_question_list, ask_question, reply_question, pin_question_reply,
  close_question, reopen_question, mark_question_sent, set_question_rfi_number,
  log_question_reply_received. Does not upload drawings (drawing-upload), build the scope list
  (scope-run), or place takeoff measurements (takeoff).
---

# Working a Plumlayer project record

**The project record** is the cloud, entry-based model of a
construction project as it currently stands. Each Plumlayer **project has one project record**.
You interact with it through the `plumlayer` MCP tools (every tool is scoped to the
signed-in user's own projects).

## The atom: an entry
`subject — predicate — value`, backed by evidence and a record of who said it. Examples:
- `sheet:A-101 — title — "First Floor Plan"`
- `door:103 — count — 6`

## Who wrote it, when, and from what
An entry you write becomes the field's current value the moment it lands, with your citation.
There is no promotion step to wait for. The record carries who wrote each entry, when, and the
evidence it came from, so cite every entry (an ungrounded entry is a guess; say so instead of
writing it).
- Every write you make is credited to the person who asked for it, by name, and that name is what
  a person reads. When you tell anyone who wrote, sent, pinned or closed something, name the
  person ("you", or a colleague by name), never "your agent" or "the agent". Nothing you write on
  the record, a Question, a reply or a note names an agent as its author.
- The server records who wrote an entry from your sign-in, never from what you declare, and
  nothing about who wrote it ranks it above or below any other entry.
- A field holds one current value: the latest write, by anyone, with who wrote it, when, and from
  what. A write onto a field that already holds a value names the record it replaces with
  `supersedesId`, whether that is your own prior read, the server's recognition pass, or something
  a person set; a write onto an occupied field that names nothing is refused, and the refusal names
  the current record. If you're not sure your read should replace what's there, ask the user
  instead of overwriting it.
- Raise a Question only for a draft RFI that meets the standard the `ask_question` verb
  states; what you are unsure of in your own reading goes on the record as your reading, with its
  sources, or to the user in the conversation. Human sign-off still gates what leaves the
  building: an ITB or package send, an RFI, anything published outside, a bid. Nothing leaves
  unsigned; nothing enters untraced.

## The verbs
**Identity / discovery**
- `whoami`: confirm which account you're acting as.
- `list_projects`: the user's projects (each has a project record). Confirm the right one before acting.
- `get_project`: one project's details.
- `create_project`: create a new project (= a new project record). Supply `name` (required) and optional
  `description`; returns the new `projectId`. Use before any write or upload on a new bid/pursuit.

**Read**
- `set_grid`: the sheet inventory (the drawing set as a grid: discipline, sheet number,
  governing issue, open-question count per sheet).
- `search`: the raw entry ledger, every entry that's ever been written, not just what's
  currently governing. Filter by subject / predicate / text; paginated. Use
  this to see what's actually been asserted, including entries you wrote yourself.
- `list_scope_items`: the live scope list (name, category, description, notes, quantity per item,
  the distinct sheets it was read off, and its citation count), 30 rows a page by default;
  `categoryCounts` tallies the whole list, so filter by `category` or `subjectPrefix`. `limit` up
  to 500 is accepted but a large one can outrun what a call carries, so page with `offset:
  nextOffset` while `truncated` is true rather than asking for it all at once. `full: true` adds
  each item's records, including the page and file behind each citation. Use this to see what's
  already been captured before creating or updating a scope item.
- `list_questions`: the questions on the project. A bare call returns the open ones only, one
  compact row each (its RFI number once it holds one, its title, the start of its wording, the
  sheets it cites, the trades it affects as codes, every trade, or not known yet, how many replies
  it has, and where it stands); pass `status: "all"` for the closed ones too, narrow with `trade`
  (a Question that names the trade comes back, and so does one that affects every trade), `sheet`
  or `section`, and pass `full: true` for the thread: the wording, every place it cites, its
  replies oldest first, the pinned reply (`pinnedReply`), every close and reopen with whoever made
  it, every answer about which trades it affects with whoever gave it, and its communications,
  every send, follow-up and reply that came back, in time order. On a long Question each of those
  lists carries its newest twenty, with `listsCut` true when one is short of its count. Read it
  with `status: "all"` before you ask, so you don't raise one that's already open or already
  answered, and before you close one, so you close the right one.
- `read_question_list`: one list on one Question read whole, oldest first (`list: "replies"`,
  `"communications"`, `"closes"` or `"trades"`). Call it when the estimator asks about entries
  older than the newest twenty and `listsCut` is true on the row.

**Drawing recognition** (cloud PDF: these work against files already uploaded to the project)
- `list_files`: list the drawing files registered to a project.
- `register_pages`: once per project, register renderable page rows for every uploaded PDF (not
  entries, just viewable pages) so uploaded files are readable even before recognition runs.
- `recognize_sheets`: start the async deterministic bulk sheet-number recognition pass over one
  uploaded PDF. Returns `{jobId, status}` immediately; poll `recognize_sheets_status` rather than
  waiting inline. Recognized sheet entries land in the record automatically on success; never
  `record_batch` them yourself.
- `recognize_sheets_status`: poll a `recognize_sheets` job. Returns run counts (`report`), the
  server-side write summary (`written`), and the tail of pages it could not name (`unnamedPages`) for
  you to read and judge; it never carries the recognized entries themselves.
- `render_page`: render a single page of a registered PDF to an image so you can read it.
- `get_page_text`: extract the text layer from a registered PDF page (deterministic; use
  alongside `render_page`: text for tokens, render for layout/meaning). Each span is an array
  `[text, x0, y0, x1, y1]`, the word then its box in PDF points. A bare call returns as many spans
  as fit one answer, bounded by size rather than a fixed count, so a dense sheet walks in a few
  calls; page with `offset: nextOffset` while `truncated` is true, or pass `region` in PDF points
  to read one area.
- `search_set_text`: find a mark or phrase in the project's files and get back which pages
  carry it and where; search first, then render only the pages it points at. It searches one
  kind of file at a time and every answer names which in `kind`. Left out, that is the drawings
  on a project that holds drawings beside a manual or proposals, the one kind a project holds
  pages of where it holds only one (a manual-only project searches its manual), and every kind
  at once where there are several and none are drawings; `countsByKind` says how many pages of
  each other kind carry the same text. Name it yourself with `kind: drawing`, `kind: document`
  for the project manual and any other filed document, `kind: proposal` for the sub proposals,
  `kind: batch` for a write file you uploaded, or `kind: all` for every page at once.
- `set_text_status`: how much of the project's text has been read so far; a page nobody has read
  yet cannot be found by `search_set_text`.

**Delivery** (group uploaded files into a source package)
- `list_drawing_deliveries`: list a project's registered drawing deliveries (baseline sets and
  revision packages like bulletins/addenda).
- `create_drawing_delivery`: register one delivery (e.g. "2025-12-15 Conformed Set" as
  `deliveryKind: "baseline"`, or "2026-02-09 Bulletin 01" as `"revision"`). Project metadata, not a
  governing entry. Attach files with `register_file.deliveryId`, then recognize with
  `recognize_sheets.deliveryId`.
- `update_drawing_delivery`: correct a delivery's label, kind, or issue date after the fact; never
  renames or mutates the uploaded files themselves.

**Upload** (register a new delivery)
- `request_file_upload`: get a signed upload URL for a drawing PDF you want to register.
- `register_file`: after uploading, register the file to the project so it becomes available
  to `list_files` / `render_page` / `get_page_text` and the `drawing-upload` pipeline.

**Write**
- `record`: append one entry (`subject`, `predicate`, `value`, `sourceInstrument`, `evidence`,
  optional `supersedesId`). A scope item and a schedule definition must both be cited, on a create
  and on an update alike: their `evidence` has to name what you read, a sheet with the 1-based page
  you read it on, a file, or a spec section, and evidence that names none of the three is refused.
  The two derived trade tags (`belongsToTrade`, `packageRole:<trade>`) need no citation. It is
  credited to the person you work for and becomes the field's current value immediately.
  `supersedesId` is the correction edge: see "Correcting a machine misread" below. Recorded text
  (name, description, note, value prose) is plain estimator words, per
  docs/plugin-text-style.md: never another entry's subject id or a hand-written supersede or date
  tag.

  A new scope item also needs its trade, and the door refuses one without it: give it
  `belongsToTrade`, or a `packageRole:<trade>` entry for every trade that might own the work, in
  the same `record_batch` as the `name`, or before the `name` at this door, which carries one
  entry per call. The trade is the package's catalog id copied verbatim, exactly as
  `solicitation_list_packages` or `directory_list_trades` prints it, spaces and all (`09 21 16`),
  on `belongsToTrade` and inside `packageRole:<trade>` alike: a code the catalog does not carry is
  refused too, so `drywall` does not land, and neither does a respelling of a real code, so
  `09-21-16` and `092116` are refused with a hint naming the exact id.
- The Question verbs, from `ask_question` to the ones that log a send, are under "Questions"
  below.
- `record_batch`: append an array of entries in one atomic call (`projectId` + `entries`
  array). Atomic: a bad entry rejects the whole batch and names the index. Prefer this over
  repeated `record` calls for bulk writes (e.g. upload or scope writes). Each call
  accepts up to 500 entries; stay at ≤50 per batch so each read is faithful and
  count-verifiable.
- `record_batch_file`: like `record_batch`, but for a run whose entries are too large to send
  inline: upload a JSONL file of entries, then write from it in one atomic call. Use this instead
  of `record_batch` for large runs (e.g. a scope-run pass recording hundreds of items).
- `retire_scope_item`: remove ONE scope item from the scope list (`projectId`, `subject`,
  `basis`, optional `reason`). Appends a retirement record; nothing is deleted and a later
  record can bring the item back. Same door a person uses; the record carries the name of the
  person you work for and the time. Call it only
  for a row the user asked removed and put their ask in `basis` in their words. A row you
  merely suspect is wrong is reported, not retired. The generic write doors refuse the
  `scopeItemRetraction` predicate; this verb and `restore_scope_item` are its only doors.
- `restore_scope_item`: put a retired scope item back (`projectId`, `subject`, `basis`,
  optional `reason`). Same door for a person and an agent, and it takes effect whoever retired
  the item, so if a person retired it, ask them before you put it back.
- `renumber_sheet`: give ONE sheet a new number (`projectId`, `sheetNumber` as `set_grid` lists it
  now, `newSheetNumber`), the same renumber a person makes in Edit Sheet; the record credits it to
  the person you work for, and what was recorded on the sheet (title, discipline, marks, scale,
  packages) reads under the new number. Refused when the new number already belongs to another sheet, when someone
  renumbered the sheet after you read it (the refusal names its number now), and when a number is
  typed with `sheet:` in front. To undo, renumber the sheet from its new number back to the one it
  had. A page that bears the same printed number as another page is named by the `opensAs` value
  `set_grid` lists for it in `pageOccurrences`; renumbering it takes that page alone out of the
  shared number, and `formerNumbers` will not list the shared number for it, so keep it yourself
  for the undo. Call it only for a number the user asked changed; a number you merely suspect is
  misread is reported, not renumbered.

Both write doors refuse the takeoff-domain predicates (`hasTakeoffCount`, `hasTakeoffRollup`,
`hasScale`, `hasTakeoffLength`, `hasTakeoffArea`, `hasTakeoffCountMark`, `hasTakeoffCondition`,
`instanceVerdict`, `hasHumanInstance`). Those belong to the takeoff door on plumlayer.com, the
only one that enforces their value shapes, subject identity, and unit immutability. Do not try
to write a measurement, a count, or a sheet scale through `record`.

### How to shape a citation

Your citation becomes a clickable chip on the scope surface, parsed deterministically from
`evidence`. An entry the parser cannot read renders **nothing**, silently and with no error:
an unreadable reference is treated as no citation rather than as a fake one. So an entry can
land perfectly well and still show no source, purely from a malformed `evidence` entry. Shape
it like this:

```json
"evidence": [
  {
    "source": "A-746 — millwork elevation at leasing desk",
    "locator": {
      "pageInPdf": 165,
      "frame": "page-points-rendered",
      "bboxPts": [1180, 640, 1890, 1120]
    }
  }
]
```

- `evidence` may be one entry or an array of them; both are read. What fails is an **empty**
  `{}`: it carries no source, so on a scope item or a definition the record refuses it outright,
  and on any other entry it cites nothing.
- `source` **must lead with the document reference**: a sheet number (`A-746`, `S-201.1`) or
  a spec section (`09 21 16`). That leading reference is what becomes the chip. An internal id
  like `bidPackage:proj-…`, or a prose sentence, is not a document reference and renders
  nothing by design.
- After the reference, add ` — ` and what you read there. A bare reference on its own is
  accepted and renders, so never pad it with a filler phrase just to satisfy the format; write
  the suffix when you have something real to say about what you saw, since it becomes the
  chip's tooltip.
- `locator.pageInPdf` is required wherever the reference is a sheet: the 1-based page you
  actually read it on. A sheet named with no page is refused on a scope item and on a definition,
  so there is no pageless chip to fall back to.
- `locator.bboxPts` with `frame: "page-points-rendered"` is what makes the chip land on the
  **region** you actually read instead of the top of the sheet. Supply them whenever you know
  where on the page you looked. Omit them and the chip still works, at page level.
- A `citedRegion` entry needs its **own** item in `evidence`. Putting the sheet and box only in
  the entry's `value` records the region but cites nothing, so no chip appears for it.

Cite the sheet you genuinely read. A citation is a document reference, never a warrant that
the tokens there mean what you concluded. That judgment is yours, recorded under the name of the
person you work for.

### Correcting a machine misread (a mis-bound title or discipline)

The deterministic recognizer grounds the tokens it reads, but *which* cell fills a semantic slot
(`hasTitle`, `discipline`) is its fallible positional guess. When you read a sheet and can see it
grabbed the wrong cell (a boxed drawing note recorded as the title, say), correct it with a
supersession **edge** that names the recognized entry:

1. `search(projectId, subject: "sheet:<n>", predicate: "hasTitle")` (or `"discipline"`) → the live
   entry's `id`.
2. `record` (or a `record_batch` entry) with `supersedesId` set to that id, `value` = what you read,
   cited to the sheet you read it from.

Your entry becomes the sheet's title or discipline the moment it lands, the same as any write
that names what it replaces, whoever wrote the value before it. The recognizer's entry stays in
the record beneath yours, with who wrote it and when. An entry with no `supersedesId` onto a field
that already holds a value is refused, so the edge is the one path. A reading
of a sheet's title or discipline you cannot resolve is named to the user in the conversation, not
raised as a Question, and a title you already read correctly is never put to anyone (that is the
"go set it on the site" dead end).
<!-- user-facing -->
To the user this is plain: "the automatic scan grabbed the wrong
text on those sheets, so I read them and set them right."
<!-- /user-facing -->

## Questions

A Question is a draft RFI: something the estimator would answer himself or send to the design
team, worth his time, with a title and at least one citation, written for a reader coming to it
cold. The standard it meets is the one the `ask_question` verb states; read it there rather than
from a summary. A Question is a thread: the ask, the replies under it, at most one reply pinned as
the answer, and every send, follow-up and reply received logged against it. Every verb that works
a Question already raised takes it as the `questionId` a `list_questions` row gives, or as its RFI
number ("RFI 22") once it holds one, and names one Question per call.

### Raising a Question

- When you find a disagreement between sources, or a gap that stops a bidder pricing the work,
  while you read, write it as a Question with `ask_question`. Do not leave it as a remark in the
  conversation.
- Check before asking: search the rest of the set and the manual with `search_set_text`, and read
  every Question with `list_questions(status: "all")`, closed ones included, with no trade filter
  and paged with `offset: nextOffset` until it comes back whole. An open one on the same ask gets a
  `reply_question`, or `add_question_source` when all you have is another place it shows; a closed
  one is never asked again.
- Give it a short title naming the ask. Write the text in the shape "this is what you meant,
  right?": state the assumption you would price on and ask the design team to confirm it, or to
  say what replaces it. Cite the exact spots: a box around the callout, schedule row or note, and
  the spec section where one bears on it. Put a Question's citations in `sources`, shaped the way
  `ask_question` describes them; the `evidence` shape under "How to shape a citation" is for scope
  rows and facts only.
- Say which trades it affects with `trades` (the codes, one or several), `trade` (one code) or
  `everyTrade: true` for the whole job; with none of the three it sits at not known yet rather than
  being guessed into a package. `set_question_trades` answers that later, when somebody knows, and
  names no trade the ask does not state; `trades: []` puts it back to not known yet.
- Your own reading of the set (its delivery method, its structure, how you reached a count or a
  grouping) is a fact you record with its sources, never a Question.
- Not a Question: a sub's revised number, a re-read of a sheet already read, or anything the
  drawings or the manual already answer.
- A Question is about the project, never about a Plumlayer failure: a job that failed or timed
  out, a verb that refused a write, a server limit, a retry decision, confusion about how to run a
  workflow, or a report that something now works belongs in the conversation and in the skill's
  own failure path, never here.

### Keep the work moving

Write the assumption into the scope item it governs and cite the Question on that row, so the
scope list carries a line a bidder can price while the Question is open. The assumption is the
value the row carries, or one plain sentence in `notesExternal` when bidders price to it and in
`notesInternal` when it is the estimator's to watch. Cite the Question with `cite_source(kind:
"question", questionId)`, or in `record_batch`'s citations for several rows at once; the row keeps
its sheet or section citation beside it.

### The thread

- `reply_question` adds a note of yours to an open Question, cited the way a Question is cited. A
  reply settles nothing and leaves the Question open.
- `pin_question_reply` pins one reply as the answer, by the reply's `entryId` from
  `list_questions(full: true)`: one of its `replies`, or a `reply_received` item in its
  `communications`. A Question holds one pinned reply; pinning another replaces it, and `replyId:
  null` takes the pin off. Pin only the reply the estimator names, and move or take off a pin only
  when he says to.
- `close_question` closes a Question when the estimator says it is settled. Put his reason in
  `note` in his own words, or leave `note` off rather than writing a reason nobody gave. A Question
  you merely think looks answered is replied to or named to him, never closed.
- `reopen_question` puts a closed Question back when he says it was closed too early or has come
  up again. The generic write doors refuse the `questionClosed` predicate; these two verbs and the
  site are the only way to close or reopen a Question.
- `rewrite_question` rewords the ask, only when he tells you what it should say instead.
- `read_question_list` reads one list of the thread whole when he asks about entries older than
  the newest twenty (see the Read verbs above).

### When an answer arrives

The estimator pastes the design team's email or RFI response, or an addendum comes in that answers
a Question. Then:

1. Put the answer on the Question. The design team's own words go on with
   `log_question_reply_received`, as close to verbatim as you have them, with who sent them in
   `from` and when in `at`; his handing you their answer is the ask to log it. An answer the new
   documents give goes on with `reply_question`, saying what the revised sheet or section shows and
   citing it.
2. Pin that reply with `pin_question_reply` when the estimator says it is the answer.
3. Update the scope values the answer moves: write each new value naming what it replaces
   (`supersedesId`), cited to where the answer came from, and cite the Question on the row with
   `cite_source(kind: "question")`.
4. Tell the estimator what changed, row by row.
5. Leave the Question open. Closing it is his call; call `close_question` only when he asks.

<!-- user-facing -->
For example: "I logged the architect's answer on RFI 14: the corridor ceilings are acoustic tile at
9 feet. I changed the corridor ceiling row from gypsum board to acoustic tile, citing RFI 14. The
Question is still open; tell me if you want that reply pinned as the answer or the Question
closed."
<!-- /user-facing -->

### The RFI number

A Question has no number of its own. It takes an RFI number when it is sent to the design team,
and that number is the one on the job's RFI log, the number Procore or anyone else on the job uses
for it. Never invent a numbering scheme. Set or correct the number with `set_question_rfi_number`
only when the estimator gives it to you or tells you to take the next one on the log
(`nextRfiNumber` on `list_questions`), or pass it as `rfiNumber` when you log the send. Refer to a
Question that holds an RFI number by it ("RFI 22"), and to one that does not by its title.

### Sending and what comes back

Sending an RFI needs the estimator's signature, and you never send one. What you record is what he
did himself, each only when he asks:

- `mark_question_sent`: he sent it, by email, through Procore, or in a meeting. Name the recipient
  in `to` as he addressed them, pass `at` when it went out earlier than now, and pass `rfiNumber`
  when it went out under one. A send to a second party is a second call.
- `set_question_rfi_number`: set or correct its RFI number.
- `follow_up_question`: he chased it after it went out.
- `log_question_reply_received`: the design team answered.

A send, follow-up or reply received logged wrong is corrected with `edit_question_send`,
`edit_question_follow_up` or `edit_question_reply_received`, naming only the fields that change,
on the entry by its `entryId` under `communications` on `list_questions(full: true)`. One logged by
mistake is taken off with `remove_question_communication`, with his words in `reason` when he gave
one, and put back with `restore_question_communication` by its `removalId` under
`removedCommunications`. One entry takes 50 corrections; past that, remove it and log it again.
Correct or remove only the entry he names, never one that merely looks wrong to you.

## Typical flows
- **"What's in my project / project record?"** → `list_projects` → pick one → `set_grid` for the
  drawing set, `list_questions` for the open items, including the ones the drawing-index check
  raised; `search` to inspect specific subjects/entries.
- **"Scope something"** → read the relevant sheets/entries, judge, then `record`
  grounded entries (`sourceInstrument` = where it came from, plus `evidence`).
<!-- user-facing -->
Tell the user
  what you wrote and the citations behind it.
<!-- /user-facing -->
Drawn
  measurements and sheet scale are not this door's to write (see Write, above).
- **"Find conflicts / RFIs"** → `list_questions` for the open items, the drawing-index check's
  among them; then raise what you find as "Raising a Question" says. Where instead you can see
  the recognizer grabbed the wrong cell for a title or discipline, correct it with a supersession
  edge (see "Correcting a machine misread"), not a Question.
- **"Here's the architect's answer" / an addendum came in** → "When an answer arrives".
- **"I sent it" / "they wrote back" / "that send was logged wrong"** → "Sending and what comes
  back".

## Discipline
- Question text is plain estimator words, and every Question meets the standard the
  `ask_question` verb states: a title, a citation for every place it names, and only what is worth
  the design team's time.
- Be honest about your own entries: each is your reading of what you cited, and you say so when
  you tell the user about it. Anyone can replace it later the same way any write does, by naming
  it.
- Always cite, and shape the citation so it actually renders (see "How to shape a citation").
  Separate what's grounded from what's inferred.
- One project = one project record; always act within the correct `projectId`.
