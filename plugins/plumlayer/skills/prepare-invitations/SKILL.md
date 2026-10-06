---
name: prepare-invitations
description: >
  Get a job's invitations ready without waiting for the scope run: read the bidding requirements
  and set only what the documents state (labor condition, the job's state, dates, address), each
  reported with its section. Trigger on "prepare the invitations", "get the invites ready",
  "/prepare-invitations". Drives read_invitation_flow, search_set_text, get_page_text,
  set_invitation_labor, set_invitation_places, set_project_date, update_project. Does not send, save
  the invite list, or put the plan room up (the site does), build the scope list (scope-run), or set
  up the project (project-setup).
---

# Prepare invitations: read the bidding requirements into the invitations

Hard bids go out to subcontractors long before a scope list exists, so the invitations cannot wait
for a scope run. What an invitation needs is the trades and the bidding requirements, and a person
gets those in about a minute from the project manual's table of contents and the invitation to bid.
This skill does that minute of reading, puts what the documents state onto the project's
invitations, and reports where each value came from. The estimator reviews and sends on
plumlayer.com.

## Where this sits

Its own step, callable any time after `project-setup`, which offers it at its close when the job is
going out to bid. It works off the packages orientation drafted (`learn-project`) and never waits
for `scope-run`. Run it again when new paper arrives, an addendum that moves the bid date or a wage
schedule issued late: a re-run writes only what changed and rewrites nothing already set to the
stated value.

## What already happens, and stays as it is

`read_invitation_flow` fills most of an invitation without this skill:

- The trades follow the project's open packages, minus the trades the company performs itself, on
  every read until someone changes the list. `trades.source` reads `packages`, with its receipt.
- The company's usual places and usual labor per trade show through, with `source: "your usual"`.
- The plan room's name, location, size and description come from the project.

This skill does not write these back, and does not call `set_invitation_trades`: storing the trades
stops the list following the packages, so a package added later would never go out. Writing the
usual places or labor onto the project stops a later change to the usual settings reaching it. The
one exception is places in step 3, and only to add the job's state.

## The boundary

This skill works the project the way the estimator would, through the same doors, and every write
it makes is marked as the agent's. It does not save the invite list, and no verb it drives does.
Sending the invitations, putting the plan room up, and changing which files the plan room shows are
signature acts: they create an obligation outside the company or publish to it, so they are the
person's to sign on the site, and this skill never does them. Every write goes through the verbs
step 5 names, never through plumlayer.com or its api directly. Two reads also write: the first
`read_invitation_flow` on an account creates that account's usual settings row, and
`get_page_text`, when it has to read a page itself, keeps what it read as that page's text.

## 1. Preconditions

1. `whoami`, then `list_projects`: confirm which project this is and take its `id` from
   `projects[]` as the `projectId`. With no project yet, hand off to `project-setup` and stop.
2. `read_invitation_flow(projectId)`. Keep the whole answer: it is the before picture, and its
   counts are the report's before numbers. Then `solicitation_list_packages(projectId, status:
   "open")`. An empty `trades.selected` means no invite trades are selected yet: no open package,
   every package trade one the company performs itself (`trades.source: "none"`), or someone
   emptied the list (`"project"`). Carry on: the dates, the address and a job-wide labor condition
   do not wait on trades. A requirement naming trades is then reported, not set, and the report
   says no invite trades are selected yet, naming `learn-project` when there is no open package.
3. Is there anything to read? `set_text_status(projectId)` lists the files the text read covers,
   each with its `kind`, oldest first and at most 500: `truncated` says when there are more, and
   `fileCount` is the true number. A `document` file is a project manual or another filed
   document, whether or not its sections were ever read onto the record. What the estimator hands
   over counts too: the owner's invitation to bid, an email, a bid form. With no document file
   listed, `truncated` false, and nothing handed over, report what the invitations already hold,
   say there was nothing to read, and stop.
4. Is the text read? A document file whose `state` is not `succeeded`, or whose `pagesNotRead` is
   above zero or null (nobody has opened it), has pages a search cannot find yet; `pagesBounded`
   and `pagesFailed` are pages read in part or not at all. Look once more after step 2's
   orientation reads, then carry on over what is read. Right after setup nothing may be read, and
   `search_set_text` or `get_page_text` refuses for that reason: that is this state, not a refusal
   to work around. Read what the estimator handed over and set only what it states. The report
   names the pages not searched yet (or that a file's page count is not known), that this check saw
   the first 500 of `fileCount` files when `truncated` is true, and that a later run picks up the
   rest. A page nobody has read is never reported as stating nothing.

## 2. Read the bidding requirements (about a minute)

The budget, in calls: about 10 orientation reads (step 1 and item 1 below), at most 5 record reads
(item 2), at most 8 text searches, at most 10 page reads, then the writes and their reads back.
Past it, stop reading and name in the report what was not read. Never read on silently. Send
reads that do not wait on each other together, several calls in one turn, to keep to the minute.

1. Orientation.
   - `get_project(projectId)` for `location`.
   - `search(projectId, subject: "project", predicate: "location")` and
     `search(projectId, subject: "project", predicate: "bidDueDate")` for what project setup seeded.
     A seeded entry is a second home for the same fact: read its current value beside the column,
     never instead of it.
   - `list_project_dates(projectId)`.
2. The table of contents, when the manual's sections are on the record
   (`search(projectId, predicate: "inDivision", limit: 1)` finds one).
   - `search(projectId, subjectPrefix: "specSection:00", predicate: "hasTitle", limit: 500)` and
     `search(projectId, subjectPrefix: "specSection:01", predicate: "hasTitle", limit: 100)`.
     Section subjects keep the design team's own numbering, packed or not, and every Division 00
     spelling starts `specSection:00`.
   - Pick the bidding sections by title: the invitation or advertisement for bids, the instructions
     to bidders and any supplement to them, the bid form, wage rate requirements or a wage
     determination, labor agreements, the supplementary conditions, and Division 01's summary of
     work for the address.
   - `search(projectId, subjectPrefix: "specSection:00", predicate: "locatedAt", full: true,
     limit: 100)` for where each section's pages are. Each value carries `fileId`, `pageStart` and
     `pageEnd`, the page numbers `get_page_text` takes; the compact preview, cut at 200 characters,
     can lose them. A section read only from the table of contents carries `declaredOnPage` and no
     range. Read the Division 01 summary's `locatedAt` by its own subject when you need its pages.
   - With no sections on the record, skip this item: the text searches still run over the document
     files, and a hit is named by its file and page instead of its section.
3. Text searches, `search_set_text(projectId, query, kind: "document")`, in this order until the
   budget is spent: "prevailing wage", "Davis-Bacon", "wage rate", "project labor agreement",
   "union" with `wholeWord: true` (the bare text also hits "reunion"; "credit union" still matches,
   so read the hit), "pre-bid", "site visit", "bids will be received".
   - Each hit is a page, `fileId` and `page`. Its section is the one whose `locatedAt` range on that
     file holds the page, and that is how the report names the section.
   - `coverage` on each answer says how much of the text there was to search. An empty answer over
     unread pages is not "not stated".
   - `truncated` says more pages hit than came back: read on with `offset` (`limit` up to 100)
     while the search budget lasts, and name the hit pages left unread in the report.
4. Page reads, `get_page_text(projectId, fileId, pageNum)`: the invitation to bid's pages, the hit
   pages that could state a requirement or a date, and the first page of the wage section. This is
   text, so there is no `render_page`. Read each answer's own limits:
   - `truncated` with `nextOffset`: more of the page is there. Read on with `offset: nextOffset`
     while the page budget lasts; what is left over is not read.
   - `workerCapped`: the page holds more text than any read reaches, so the rest is not read.
   - `ocr.bounded`: the machine read covered only part of the page, so the rest is not read.
   - `notReadReason`: nothing has read the page yet, so none of it is read.

   The part not read is reported as not read, never as stating nothing.
5. What the estimator handed over is read with your own file reading and named by its file name in
   the report.

A manual whose Division 00 carries no bidding requirements, a permit set for example, still gets
the searches. If nothing is stated, nothing is set, and the report says so.

### The current value on the record

`search` returns every entry, replaced ones included. A record value read through `search`, a
seeded location or bid date, a section's title or pages, is compared only by its slot's current
value: group the rows by subject and predicate, drop every row another row in the group names in
its `supersedesId`, and take the newest `assertedAt` among the rest, the lowest `id` on a tie. Read
every row of a slot first (`count` says whether the page held them all). A replaced value never
makes a disagreement, and a slot whose rows are all replaced holds nothing.

### What counts as stated

Only what the documents or the estimator state is set.

| Value | Stated when the documents | Not stated, set nothing |
|---|---|---|
| prevailing wage | say the work or the contract is subject to prevailing wage or Davis-Bacon, attach a wage schedule or determination for this project, or cite a law the documents themselves say sets the wage rates for this work ("minimum wage rates as required by" the law) | "comply with applicable laws", "if applicable", a general minimum wage or wage payment law, a public owner, a building type, the market |
| union | require union labor, or union-signatory subcontractors, for the work or for named trades | a project labor agreement alone, the region, the market, a trade's usual |
| job location | give the project's address: the invitation, the title page, Division 01's summary | where bids are delivered, the architect's or the owner's office |
| owner bid due | give the day, and the time, bids must be received by: the deadline for submitting them, the general bids' where subcontractors' bids have their own | the time bids are opened, when given apart from that deadline; "to be announced"; a deadline for bids from subcontractors |
| site visit, pre-bid meeting, questions due | give the day, and the time | "by appointment", "to be scheduled" |
| subcontractor bid due | never from the documents: only the estimator's own word | the owner bid date less some days, a usual offset, a date the documents set for bids from subcontractors |
| time of day | give the time and either name the zone or the job's state lies in one zone | a state spanning two zones with no zone named: set the day only and quote the time in the report |

Never inferred: a wage requirement from who the owner is; union from a labor agreement or the
region; one date from another, a year included; the job's state from a city with no state named;
a trade the document does not name. A date printed without a year is not stated: it is never set,
and the report quotes it as printed under what is still missing.

Participation goals, insurance, bonds, bid security, a project labor agreement and a bid opening
time are not filters on who is invited. The report names them with their sections; nothing sets
them.

## 3. Decide each value

Nothing is written in this step. Compare each stated value with the current values step 2 read. A
value already set to what the documents state is left alone. A decision that waits on an answer
from step 4 is made in step 5, once the answer is in.

### Labor

Labor the documents do not state is the company's call, not this skill's: set nothing and ask
nothing. The report gives each trade's current condition and where it came from.

What the first `read_invitation_flow` can and cannot tell:

- `wholeProjectLabor` is `"union"` or `"prevailing wage"` when exactly one whole-job condition
  stands and spells one of them. Null means none stands, more than one stands, or the one standing
  spells none of the three; the read does not say which, so null never means the job asks nothing.
  While more than one stands, every whole-job write is refused.
- A trade whose `labor.source` is `project` reads a condition set on this project, its own or the
  whole job's, and the read does not say which. Only its own stays when the job-wide one changes.
- A trade whose `labor.condition` is null reads a rule or a usual none of the three conditions
  spell: leave it out of every write and name it. A trade with `labor.source: "none"` reads
  `"open shop"`, which is nothing asked of it, never a condition someone set.

The decisions:

- A requirement for the whole contract ("the work is subject to", "this contract requires") is one
  job-wide condition: `set_invitation_labor(projectId, wholeProject: true, condition)`. It reaches
  every trade the invitations list, and every trade a later package adds, except a trade carrying a
  condition of its own. When `wholeProjectLabor` already holds a different condition, that is a
  disagreement with the record for step 4's labor item, unless an addendum governs.
- A requirement naming trades goes on the selected codes (`trades.selected[].code`) under the
  division or section it names: `set_invitation_labor(projectId, codes, condition)`, at most 50
  codes a call. A manual section the catalog numbers differently reaches no code by its number: the
  open package whose `manualSections` lists it (packed, `113013`) buys it, and when that package
  carries one trade (its `tradeCode` and no `codes`), that is the trade. Otherwise, and for a trade
  named only in words, it is reported, not set.
- Every trade a requirement reaches that reads a different condition set on this project, its own
  or the job's alike, is a disagreement with the record for step 4's labor item.
- Step 5's read after the whole-job write settles which trades carry their own: there, a trade with
  `labor.source: "project"` reading anything but the job-wide condition carries its own.
- The verb answers `written`, one row per named code with `code`, `ruleId` and `changed`, or for
  the whole job one `ruleId` and `changed`. `changed: false` means nothing was written: the trade's
  own rule or the job-wide condition already held it, or open shop found no job-wide condition to
  take off (`ruleId` null). The `changed` flags are what the report says was set, and why a re-run
  rewrites nothing. A trade that read the condition from the job gets a rule of its own.
- Prevailing wage and union both required: set prevailing wage, and report the union requirement
  as not set. A trade carries one condition, and union on it would take prevailing wage off.
- A project labor agreement alone is reported with its section and set on no trade.
- A job-wide condition an addendum expressly withdraws follows the addendum rule below. When it
  governs, `set_invitation_labor(projectId, wholeProject: true, condition: "open shop")` takes the
  job-wide condition off, and each trade reads its own condition or the usual again.

### Places

- The job's state comes from a project address nobody disputes: the one the documents state, or the
  project's `location` when it names a state. Never from a city with no state. When the address is
  a question in step 4, the job's state, and this decision, wait for the answer.
- Set it only when a places filter is in effect (`places.states` is not empty) and lacks the job's
  state by name or two-letter code: `set_invitation_places(projectId, states: [every state in
  places.states, the job's state])`, since the verb replaces the list. The report names the list it
  replaced, and that the project now keeps its own places, so a later change to the usual places
  no longer reaches it.
- No filter in effect (`places.states` empty): set nothing. One state would narrow every trade.
- `places.ungrounded` not empty: set nothing and name those places. The verb refuses a list holding
  a spelling the catalog does not carry, and correcting it is not this skill's.

### Dates

- `owner_bid` for the deadline for receiving bids; `site_visit` for a site visit, with `endDay` for
  a range, one date when the documents combine it with a pre-bid meeting; `other` for a pre-bid
  meeting, a questions deadline, and any date the documents set for bids from subcontractors (a
  filed sub-bid deadline), one date per deadline, each named in the documents' words.
- `list_project_dates` answers `{ count, dates }`, each date with an `id`. To change one, send
  `set_project_date(projectId, dateId: <that id>, ...)` with only the fields that change and never
  `kind`: a change naming a kind is refused, because a different kind is a different date. To add
  one, leave `dateId` out and send `kind` and `onDay`, with `internal` left at its default.
- A document's date matches a record date of the same kind when `onDay`, `endDay`, `atTime` and
  `timeZone` all agree, whatever an `other` date's name. A match is left alone; only a document
  date with no match is added.
- A record date that agrees on the day and the range but has no time, where the documents give one,
  gets the time added by its `dateId`. Nothing it holds is replaced, and the report says so.
- One owner bid date is this skill's own rule; the server would take a second. A record `owner_bid`
  that differs in its day, its range, its time or its zone is a disagreement with the record,
  unless an addendum governs. Never add a second one beside it.
- Site visits and named dates can be several, so a document's site visit on a different day from
  the record's may be the same visit moved or another visit. The record holds none of that kind:
  add it. The documents list the record's date as well as this one: it is another visit, add it.
  Otherwise it is a step 4 item.
- A time only per the table above. `atTime` always goes with `timeZone`, an IANA zone such as
  "America/New_York". A time zone read off the job's state waits for step 4 when the address is a
  question there.
- The subcontractor bid due date, the estimator's own, is never read off the documents and never
  worked out from another date. When `list_project_dates` already holds a `subcontractor_bids`
  date, leave it. When the estimator has already said it in this conversation, set it with
  `set_project_date(kind: "subcontractor_bids")`. Otherwise it is asked in step 4, beside the
  owner's date and any date the documents set for bids from subcontractors.
- A seeded `bidDueDate` entry names a bid date without saying whose. Never set it as either date;
  show its current value in step 4's question too.

### The address

- The project's `location` is empty, the documents state the project address, and no current
  seeded `location` entry names a different place: `update_project(projectId, location: "<the
  address as the document gives it>")`. Filling an empty address is the same edit a person makes on
  the project, whether or not the plan room is up.
- The column or a current seeded entry names a different place from the documents: a disagreement
  with the record, since writing over it would replace what stands.
- A record value that is a shorter form of the same place ("Riverton, MA" against a full street
  address in Riverton, MA) is not a disagreement: leave it and quote the full address in the report.
- Two documents giving different project addresses: a disagreement between documents.

### When sources disagree

- An addendum that expressly replaces a requirement or a date, one that says it changes, revises,
  deletes or replaces that item, governs over the document it amends. It is not asked and not
  raised as a Question. When the record holds the value it replaces, or nothing, the addendum's
  value is set and the report names both. When the record holds a value neither document gives,
  that is a disagreement with the record.
- Every other conflict, one document against another or a document against the record, is asked in
  step 4.
- A current seeded entry whose `sourceInstrument` or evidence names a file or a sheet, rather than
  `project-setup-interview`, the estimator's own word in project setup, stands for the document it
  cites. A setting, a date, the project's location and an interview seed are not documents.

## 4. Ask once

One question group, through the client's choice-question tool (`AskUserQuestion` in Claude Code,
the equivalent in Codex), holding:

- every disagreement, each value with where it came from, plus "leave it as it is";
- one labor item: a different job-wide condition, and every trade a requirement reaches that reads
  a different condition set on this project, with "leave it as it is" when the job-wide condition
  differs;
- a site visit or named date the skill cannot place as moved or another;
- the subcontractor bid due date, when the project has none and the estimator has not said it.

<!-- user-facing -->
A disagreement reads like: "The invitation to bid (page 3) says bids must be received by March 3 at
2:00 PM. The project's owner bid date is March 5. Which one stands?", with "March 3, from the
invitation" and "leave it at March 5" as the choices.

The labor item reads like: "Section 00 73 46 says the whole contract is subject to prevailing
wage. Electrical and Plumbing are on union, set on this project. Put them on prevailing wage too?",
with "every trade on prevailing wage" and "a trade with its own condition keeps it" as the choices.

A site visit reads like: "The instructions to bidders (page 12) give a site visit on May 6. The
project has one on May 4.", with "add it as another site visit", "move the one on the project to
May 6" and "leave it" as the choices.

The bid date reads like: "When are subcontractor bids due to you? Bids to the owner are due March 3
at 2:00 PM, and filed sub-bids February 18, from the invitation to bid, page 3.", answered in their
own words, with "not decided yet" offered beside it.
<!-- /user-facing -->

Nothing else is asked: not labor the documents leave unstated, never a trade at a time, never a
confirmation of what was read, never whether to go ahead. With nothing to ask, there is no question
at all. Where the client has no choice-question tool, or the group holds more than it takes in
one call, ask the rest in prose in the same turn, so it is still one ask.

The estimator's bid date is set with `set_project_date(kind: "subcontractor_bids", onDay)`, with
`atTime` and `timeZone` only per the time rule above. An answer that does not pin one calendar day
is not set; the report quotes it under what is still missing.

A disagreement between two documents is also raised as a Question, whatever the answer, except
about labor: the verb's standard keeps what the GC decides off Questions, so a labor conflict is
asked and reported only. Before each, read `list_questions(projectId, status: "all", section: "<a
section it cites>")`: an open one on the same topic is named in the report rather than raised
again, and a closed one is not asked again; with `scanTruncated` true, the report says this check
was incomplete. Then one `ask_question` per disagreement, with a `title` of a few words naming the
ask, the ask itself as `text`, written for a reader coming to it cold, and:

- `sources`: each spec section as `{ "type": "spec", "section": "specSection:<the six digits,
  packed>" }`; a sheet it cites as `{ "type": "sheet", "sheet": "<the sheet subject>" }`; a seeded
  entry as `{ "type": "record", "entryId": "<its current entry's id>" }`, only beside a section or
  a sheet. A section numbered the older five-digit way, or a document handed over that is not on the
  record, cannot be cited, so name it and its page in the text. With no section or sheet to cite,
  the verb takes no Question: the disagreement is asked only, and the report says so.
- `everyTrade: true` when it is about the whole job, and `sourceInstrument: "prepare-invitations"`.

Question text is plain estimator words, and every Question meets the standard the `ask_question`
verb states. A Question is about the project, never about a Plumlayer failure: a refused write or a
page that would not read goes in the report.

## 5. Write

Nothing is written before step 4's answers are in. First settle what waited on them: the job's
state from the address the estimator chose, then the places decision, then any time whose zone
follows from the job's state. Then write in this order:

1. Labor on the whole job, then `read_invitation_flow(projectId)` again, which settles the trades
   carrying a condition of their own (step 3).
2. Labor on named codes: the trades a named requirement reaches, and, where the estimator chose
   "every trade", the trades still carrying a different condition of their own. A trade the
   estimator chose to keep is left out.
3. Places, dates, the address, the Questions.

The writes this skill makes, and no others:

- `set_invitation_labor`, on the whole job or on named codes;
- `set_invitation_places`;
- `set_project_date`: `owner_bid`, `site_visit`, `other`, and `subcontractor_bids` from the
  estimator's word;
- `update_project` with `location` only;
- `ask_question` for a disagreement between documents.

Read each answer back, labor by its `changed` flags.

Then one more `read_invitation_flow(projectId)`. Its counts are the after numbers.

## 6. Report

The counts are `counts.perCode`: `base` passes the places, `companies` is those that also pass the
labor condition, and with `includeUnknown` true both count companies with no answer on file.

<!-- user-facing -->
One closing report in plain words. Every count comes from a read of the invitations: the first read
gives the before numbers and the last read the after numbers, and the report prints both.

- **Trades going out**: how many, and where the list comes from (the packages, or a list someone
  set on this project), or that none are selected yet, and why. For each trade, how many companies
  pass its filters; the companies are on the site's invite list. Trades no company passes come
  first. Say when these numbers count companies with no answer on file, because your account keeps
  them in, and when the directory holds no companies yet.
- **What changed each trade's count**: before and after for every trade whose count moved. Each
  trade has two numbers, the companies that pass the places and, of those, the companies that pass
  its labor condition. A change in the first is the places change, and a change between the two is
  labor, so a change is never put down to labor alone when places moved too: "Electrical went from
  14 companies to 6: adding the job's state took it to 16, and 6 of those pass the prevailing wage
  filter, counting the companies with no labor answer on file."
- **What I set, and where it came from**: one line per value, with its section and page. "Prevailing
  wage on the whole job, from section 00 73 46, page 212 of the project manual." "Owner bid due
  March 3 at 2:00 PM, from the invitation to bid, page 3." A value the estimator gave says so. A
  value an addendum changed names both. A places change names the list it replaced. A labor
  condition that already stood, on a trade or on the whole job, is listed as already set, not as
  set now. A trade that kept a condition of its own under the job-wide one is named with it.
- **What I read and did not set**: participation goals, bonds, insurance, a project labor
  agreement, a union requirement beside prevailing wage, a bid opening time, a trade named in words
  the trade list cannot be matched to, each with its section.
- **Labor, when the documents state none**: say so, then each trade's current condition from the
  last read and where it came from: set on this project (it stays), your usual, or nothing
  required. Trades that read the same are grouped.
- **What is still missing**: for example no subcontractor bid due date, no project address stated,
  no labor requirement stated. No places filter is not missing: say once, under the trades, that
  every state goes out.
- **What I asked, and any Questions I raised**: each Question by its number, any one already open
  named instead of raised again, and whether the check for one already open was incomplete.
- **What I did not read**: pages past the reading budget, pages of the manual not read yet, and
  pages read only in part or not at all, and that running this again later picks them up.
- **Next**: review and send from the invitations on plumlayer.com, through the project's Coverage
  page and its invite list. I did not save the list or send anything; signing the send is yours.
<!-- /user-facing -->

## Gates

- Writing over a value that already stands names what it replaces, or is asked first.
- A refused write is reported in its own words, and never sent again in another shape, routed
  through another verb, or handed to the site. A read refused because nothing is read yet is step
  1.4's case.
