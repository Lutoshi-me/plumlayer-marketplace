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

1. `whoami`, then `list_projects`: confirm which project this is and take its `projectId`. With no
   project yet, hand off to `project-setup` and stop.
2. `read_invitation_flow(projectId)`. Keep the whole answer: it is the before picture, and its
   counts are the before numbers the report prints. When `trades.source` is `none`, the project has
   no packages and no trades selected: stop and hand off to `learn-project`, or to `project-setup`
   when nothing has been read in yet.
3. Is there anything to read? `set_text_status(projectId)` lists every file the project's text read
   covers, each with its `kind`. A `document` file is a project manual or another filed document,
   whether or not its table of contents was ever read into sections, so a project with no sections
   on the record can still have everything to read. What the estimator hands over counts too: the
   owner's invitation to bid, an email, a bid form. With no document file and nothing handed over,
   report what the invitations already hold, say there was nothing to read, and stop.
4. Is the text read? A document file still `queued` or `running`, or with `pagesNotRead` above
   zero, has pages a search cannot find yet; `pagesBounded` and `pagesFailed` are pages read in part
   or not at all. Look once more after step 2's orientation reads. If it is still reading, carry on
   over what is read and name in the report how many of those pages were not searched. A page
   nobody has read is never reported as stating nothing.

## 2. Read the bidding requirements (about a minute)

The budget, in calls: about 10 orientation reads (step 1 and item 1 below), at most 5 record reads
(item 2), at most 8 text searches, at most 10 page reads, at most 3 pages of Questions in step 4,
then the writes. Past it, stop reading and name in the report what was not read. Never read
on silently.

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
     `pageEnd`, the page numbers `get_page_text` takes. Read it in full: the compact preview is cut
     at 200 characters and a long filename pushes the page numbers off the end. A section read only
     from the table of contents carries `declaredOnPage` and no range. Read the Division 01
     summary's `locatedAt` by its own subject when you need its pages.
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

`search` returns every entry, the ones later entries replaced included. Wherever this skill compares
a record value it read through `search`, a seeded location or bid date, a section's title or pages,
it compares only that slot's current value:

- group the rows by subject and predicate;
- drop every row another row in the group names in its `supersedesId`;
- take the newest `assertedAt` among the rest, and the lowest `id` on a tie.

Read every row of a slot before deciding: `count` beside the page says whether it held them all. A
replaced value is never compared and never makes a disagreement. A slot whose rows are all replaced
holds nothing.

### What counts as stated

Anything not stated is not set.

| Value | Stated when the documents | Not stated, set nothing |
|---|---|---|
| prevailing wage | say the work or the contract is subject to prevailing wage, Davis-Bacon, or a named state wage law, or attach a wage schedule or determination for this project | "comply with applicable laws", "if applicable", a public owner, a building type, the market |
| union | require union labor, or union-signatory subcontractors, for the work or for named trades | a project labor agreement alone, the region, the market, a trade's usual |
| job location | give the project's address: the invitation, the title page, Division 01's summary | where bids are delivered, the architect's or the owner's office |
| owner bid due | give the day, and the time, bids must be received by: the deadline for submitting them | the time bids are opened, when given apart from that deadline; "to be announced" |
| site visit, pre-bid meeting, questions due | give the day, and the time | "by appointment", "to be scheduled" |
| subcontractor bid due | never from the documents: only the estimator's own word | the owner bid date less some days, a usual offset |
| time of day | give the time and either name the zone or the job's state lies in one zone | a state spanning two zones with no zone named: set the day only and quote the time in the report |

Never inferred: a wage requirement from who the owner is; union from a labor agreement or the
region; one date from another; the job's state from a city with no state named; a trade the
document does not name.

The owner bid date is always the deadline for receiving bids. A bid opening the documents give
apart from it is named in the report and set on nothing.

A statement naming trades, "electrical work by signatory contractors" for example, goes on the
selected codes under the division or section it names. A trade name whose codes cannot be read off
is reported, not set.

Participation goals, insurance, bonds, bid security and a project labor agreement are not filters
on who is invited. The report names them with their sections; nothing sets them.

## 3. Decide each value

Nothing is written in this step. Compare each stated value with the current values step 2 read. A
value already set to what the documents state is left alone. A decision that waits on an answer
from step 4 is made in step 5, once the answer is in.

### Labor

Labor the documents do not state is the company's call, not this skill's: set nothing and ask
nothing. The report gives each trade's current condition and where it came from.

Which trades carry a condition of their own comes from the first `read_invitation_flow` alone. Its
`wholeProjectLabor` is `"union"` or `"prevailing wage"` when that condition is set on the whole
job, and null when none is. A trade whose `labor.source` is `project` carries its own rule when its
`labor.condition` differs from `wholeProjectLabor`, or when `wholeProjectLabor` is null. A trade
that reads the job-wide condition has no rule of its own that conflicts with anything, so there is
nothing to ask about it.

- A requirement for the whole contract ("the work is subject to", "this contract requires") is one
  job-wide condition: `set_invitation_labor(projectId, wholeProject: true, condition)`. It reaches
  every trade the invitations list, and every trade a later package adds. When `wholeProjectLabor`
  already holds a different condition, that is a disagreement with the record, unless an addendum
  governs.
- A trade carrying its own rule keeps it under a job-wide condition, because a trade's own rule
  wins. When its own condition differs from what the documents require of it, that is a
  disagreement with the record for step 4. When the estimator picks the documents' condition,
  `set_invitation_labor(projectId, code, condition)` puts it on that trade.
- A requirement naming trades goes on the selected codes (`trades.selected[].code`) under the
  division or section it names: `set_invitation_labor(projectId, codes, condition)`, at most 50
  codes a call. Leave out a code carrying its own rule with a different condition; that one is a
  disagreement for step 4.
- For named codes the verb answers `{ projectId, condition, written }`, one `written` row per code
  with `code`, `ruleId` and `changed`. `changed: false` means the trade's own rule already held the
  condition and nothing was written. Only the trade's own rule counts: a trade that reads the
  condition from the job-wide rule gets a rule of its own, so the named requirement stays if the
  job-wide condition is taken off later.
- For the whole job it answers `{ projectId, condition, wholeProject: true, ruleId, changed }`.
  `changed: false` means the job-wide condition already held it, or, for open shop, that there was
  none to take off, when `ruleId` is null.
- The `changed` flags are what the report says was set, and why a re-run rewrites nothing.
- Prevailing wage and union both required: set prevailing wage, and report the union requirement
  as not set. A trade carries one condition, and union on it would take prevailing wage off.
- A trade whose `labor.condition` is null carries a rule none of the three conditions spell: leave
  it out of every write and name it.
- A project labor agreement alone is reported with its section and set on no trade.
- A job-wide condition an addendum expressly withdraws follows the addendum rule below. When it
  governs, `set_invitation_labor(projectId, wholeProject: true, condition: "open shop")` takes the
  job-wide condition off, and each trade reads its own condition or the usual again.

### Places

- The job's state comes from a project address nobody disputes: the one the documents state, or the
  project's `location` when it names a state. Never from a city with no state. When the address is
  a question in step 4, the job's state, and this decision, wait for the answer.
- Set it only when a places filter is in effect (`places.states` is not empty) and lacks the job's
  state: `set_invitation_places(projectId, states: [every state in places.states, the job's
  state])`. The verb replaces the list, so send everything in effect plus the one state. The report
  names the list it replaced, and that the project now keeps its own places, so a later change to
  the usual places no longer reaches it.
- No filter in effect (`places.states` empty): set nothing. One state would narrow every trade to
  it.
- `places.ungrounded` not empty: set nothing and name those places. The verb refuses a list holding
  a spelling the catalog does not carry, and correcting it is not this skill's.

### Dates

- `owner_bid` for the deadline for receiving bids; `site_visit` for a site visit, with `endDay` for
  a range; `other` for a pre-bid meeting and a questions deadline, named "Pre-bid meeting" and
  "Questions due".
- `list_project_dates` answers `{ count, dates }`, each date with an `id`. To change one, send
  `set_project_date(projectId, dateId: <that id>, ...)` with only the fields that change and never
  `kind`: a change naming a kind is refused, because a different kind is a different date. To add
  one, leave `dateId` out and send `kind` and `onDay`.
- A document's date matches a record date of the same kind (and, for `other`, the same name) when
  `onDay`, `endDay`, `atTime` and `timeZone` all agree. A matched date is left alone.
- A record date that agrees on the day and the range but has no time, where the documents give one,
  gets the time added by its `dateId`. Nothing it holds is replaced, and the report says so.
- The project has one owner bid date. A record `owner_bid` that differs in its day, its range, its
  time or its zone is a disagreement with the record, unless an addendum governs. Never add a second
  one beside it.
- Site visits and named dates can be several, so a document's site visit on a different day from
  the record's may be the same visit moved or another visit. The record holds none of that kind:
  add it. The documents list the record's date as well as this one: it is another visit, add it.
  Otherwise ask in step 4, with "add it as another site visit", "move the one on the record to this
  day" and "leave it" as the choices.
- `internal` stays at its default.
- A time only per the table above. `atTime` always goes with `timeZone`, an IANA zone such as
  "America/New_York". A time zone read off the job's state waits for step 4 when the address is a
  question there.
- The subcontractor bid due date is never read off the documents and never worked out from the
  owner's date. When `list_project_dates` already holds a `subcontractor_bids` date, leave it. When
  the estimator has already said it in this conversation, set it with `set_project_date(kind:
  "subcontractor_bids")`. Otherwise it is asked in step 4.
- A seeded `bidDueDate` entry names a bid date without saying whose. Never set it as either date;
  show its current value in step 4's question beside the owner's date.

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
- A record value that carries its own citation is a second source: a current seeded entry whose
  `sourceInstrument` or evidence names a file or a sheet, rather than `project-setup-interview`,
  the estimator's own word in project setup. A disagreement with it is between two sources, so it
  is asked and also raised as a Question. A record value with no citation, the project's location,
  a date, a labor or places setting, or a seed from the interview, is asked only.
- Two documents disagreeing is asked and also raised as a Question.

## 4. Ask once

One question group, through the client's choice-question tool (`AskUserQuestion` in Claude Code,
the equivalent in Codex), holding:

- every disagreement, each value with where it came from, plus "leave it as it is";
- a site visit or named date the skill cannot place as moved or another;
- the subcontractor bid due date, when the project has none and the estimator has not said it.

<!-- user-facing -->
A disagreement reads like: "The invitation to bid (page 3) says bids must be received by March 3 at
2:00 PM. The project's owner bid date is March 5. Which one stands?", with "March 3, from the
invitation" and "leave it at March 5" as the choices.

The bid date reads like: "When are subcontractor bids due to you? Bids to the owner are due March 3
at 2:00 PM, from the invitation to bid, page 3.", answered in their own words, with "not decided
yet" offered beside it.
<!-- /user-facing -->

Nothing else is asked: not labor the documents leave unstated, never a trade at a time, never a
confirmation of what was read, never whether to go ahead. With nothing to ask, there is no question
at all. Where the client has no choice-question tool, ask the same group once in prose.

The estimator's bid date is set with `set_project_date(kind: "subcontractor_bids", onDay)`, with
`atTime` and `timeZone` only per the time rule above. An answer that does not pin one calendar day
is not set; the report quotes it under what is still missing.

A disagreement the rules above also send to the record is raised as a Question. Read
`list_questions(projectId, limit: 200)` first, following `truncated` and `nextOffset` until every
open Question is read, at most 3 pages, so an open one is not raised twice. When the pages run out
first, or `scanTruncated` is true, raise it anyway and say in the report that the check for one
already open was incomplete. Then one `ask_question` per disagreement:

- `sources`: each spec section as `{ "type": "spec", "section": "specSection:<the six digits,
  packed>" }`; a seeded entry as `{ "type": "record", "entryId": "<its current entry's id>" }`; a
  sheet it cites as `{ "type": "sheet", "sheet": "<the sheet subject>" }`. A section numbered the
  older five-digit way, or a document handed over that is not on the record, cannot be cited that
  way, so name it and its page in the text.
- `everyTrade: true` when it is about the whole job, and `sourceInstrument: "prepare-invitations"`.

Question text is plain estimator words, per docs/plugin-text-style.md. A Question is about the
project, never about a Plumlayer failure: a refused write or a page that would not read goes in the
report.

## 5. Write

Nothing is written before step 4's answers are in. First settle what waited on them: the job's
state from the address the estimator chose, then the places decision, then any time whose zone
follows from the job's state. Then write in this order: labor, places, dates, the address, the
Questions. The writes this skill makes, and no others:

- `set_invitation_labor`, on the whole job or on named codes;
- `set_invitation_places`;
- `set_project_date`: `owner_bid`, `site_visit`, `other`, and `subcontractor_bids` from the
  estimator's word;
- `update_project` with `location` only;
- `ask_question` for a disagreement between sources.

Read each answer back. For labor, read `changed` on each `written` row and on the whole-job answer:
`false` means the condition already held and nothing was written. A refusal is
reported in its own words and never sent again in another shape, routed through another verb, or
handed to the site.

Then one more `read_invitation_flow(projectId)`. Its counts are the after numbers.

## 6. Report

<!-- user-facing -->
One closing report in plain words. Every count comes from a read of the invitations: the first read
gives the before numbers and the last read the after numbers, and the report prints both.

- **Trades going out**: how many, and where the list comes from: the packages, or a list someone
  set on this project. For each trade, how many companies it reaches, a number; the companies behind
  it are on the site's invite list. Trades that reach no company come first. When the directory
  holds no companies yet, say so, since every trade then reaches none.
- **What changed each trade's count**: before and after for every trade whose count moved. Each
  trade has two numbers, the companies that pass the places and, of those, the companies that pass
  its labor condition. A change in the first is the places change, and a change between the two is
  labor, so a change is never put down to labor alone when places moved too: "Electrical went from
  14 companies to 6: adding the job's state took it to 16, and 6 of those pay prevailing wage."
- **What I set, and where it came from**: one line per value, with its section and page. "Prevailing
  wage on the whole job, from section 00 73 46, page 212 of the project manual." "Owner bid due
  March 3 at 2:00 PM, from the invitation to bid, page 3." A value the estimator gave says so. A
  value an addendum changed names both. A places change names the list it replaced. A labor
  condition that already stood, on a trade or on the whole job, is listed as already set, not as
  set now.
- **What I read and did not set**: participation goals, bonds, insurance, a project labor
  agreement, a union requirement beside prevailing wage, a bid opening time, a trade named in words
  the trade list cannot be matched to, each with its section.
- **Labor, when the documents state none**: say so, then each trade's current condition and where
  it came from, from the last read: set on this project, your usual, or nothing. A condition set on
  this project stays and is named as set on this project. Trades that read the same are grouped.
- **What is still missing**: for example no subcontractor bid due date, no project address stated,
  no labor requirement stated.
- **What I asked, and any Questions I raised**: each Question by its number, and whether the check
  for one already open was incomplete.
- **What I did not read**: pages past the reading budget, pages of the manual not read yet, and
  pages read only in part or not at all, and that running this again later picks them up.
- **Next**: review and send from the invitations on plumlayer.com, through the project's Coverage
  page and its invite list. I did not save the invite list or send anything; signing the send is
  yours.
<!-- /user-facing -->

## Gates

- Set only what the documents or the estimator state. Nothing is inferred from the owner, the
  region, the building type, or another date.
- The owner bid date is the deadline for receiving bids, never the opening.
- Only the current entry of a value read through `search` is compared; a replaced one never makes
  a disagreement.
- Which trades carry a labor condition of their own is read from `read_invitation_flow` alone,
  never from the stored rules.
- This skill does not write the trade list, the usual settings, or the invitation message. The
  places list is written only to add the job's state.
- This skill does not save the invite list, and no verb it drives does.
- Sending the invitations, putting the plan room up, and changing which files it shows are signature
  acts, the person's to sign; this skill never does them.
- Every write goes through the verbs step 5 names, so each is marked as the agent's, never through
  the site or its api directly.
- Writing over a value that already stands names what it replaces, or is asked first.
- One question group: every disagreement, a date the skill cannot place, and the subcontractor bid
  due date when the project has none. Labor the documents leave unstated is never asked about.
- Nothing is written before that group is answered.
- Never work one date out from another.
- A re-run rewrites nothing already set to the stated value. For labor that is the verb's doing:
  `changed: false` means it wrote nothing, and the report follows those answers.
- The reading budget holds, and anything past it, or read only in part, is named in the report.
- Every count in the report is read from the invitations, before and after.
- A refusal is reported in its own words, never worked around.
