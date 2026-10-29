---
name: project-setup
description: >
  Set up a new pursuit end to end: create the project record, seed the facts only you carry, read the
  drawing delivery and the project manual in, then orient and draft the baseline packages. Trigger on
  "set up this project", "new project", "create a project", "start a new bid or pursuit", "onboard
  this project", "/project-setup". Drives create_project, record_batch, and the drawing-upload and
  learn-project skills in full. Does not build the scope list (scope-run), prepare the invitations
  (prepare-invitations), read sub proposals (bid-intake), or place takeoff measurements (takeoff).
---

# Project setup: stand up a new pursuit, end to end

A Plumlayer project has one project record, the cloud, entry-based model of that project as it
currently stands. This skill stands the pursuit up: it creates the project, puts what the user
knows (or can hand you in a file) into Overview's own fields and into **cited entries**, reads
the drawing delivery and the project manual in, and orients on what came back.

> **Doctrine (binds every step):** you read and judge; deterministic tooling grounds; nothing leaves
> unsigned and nothing enters untraced. What you seed here takes effect right away as the project's
> starting frame, credited to the user with your citation, and its source is what someone *told
> you*, not a drawing you read. When the drawings and specs are read later, an empty field is
> filled from them, and a sheet that says something different from what the user gave is named to
> the user, never written over it. Cite every entry, never invent a fact, and
> name what's uncertain to the user rather than seeding it.
>
> **Confidentiality:** project specifics live in the runtime and in the user's own scoped cloud project record
> (project isolation + private bucket + RLS), that's fine. They must never land in tracked or
> committed plugin/repo files.

---

## Where this sits (read this before you start asking questions)

A skill is a step; what a user runs is a process. This skill is **New pursuit, session 1**, and it
runs that session end to end: the shell, the seed facts, the delivery read in, and the orientation
pass. The scope run is session 2, its own skill (`scope-run`), and it wants its own session; do
not start it from here. Getting the invitations ready is its own step too (`prepare-invitations`),
callable any time after this session; it does not wait for the scope run. When new paper arrives
later (a bulletin, an addendum, a re-issue), that is a different process and its first step is
`drawing-upload` on its own.

**The load-bearing consequence, don't interrogate for what the set is about to tell you.** Almost
everything about a project is read off the drawings later in this same session, cited to the
sheet it came from. A user answering from memory gives you a restatement of what someone recalls;
a cover-sheet / title-block read gives you the value printed on the drawing, and fills the field
minutes later when it is still empty. A guess written now holds the field, and the read can only
name the difference to the user. So asking the user to guess the project type, the engineers, the
trades, or the square footage isn't just slow, it puts a recalled value where the printed one
belongs.
<!-- user-facing -->
Ask
only for what no drawing will ever carry; for the rest, say "I'll read that off the set next" and move
on.
<!-- /user-facing -->

**One turn, start to finish.** With the drawing set and the project manual in hand, and the user able
to answer the few ask-now questions, this skill should run start to finish in one turn. Ending the
turn to ask something in prose is the failure mode to avoid. The stop points inside `drawing-upload`
and `learn-project` are unchanged, and they are the only reasons to stop this session early.

---

## 1. Preflight

1. **Confirm the account.** Call `whoami`. State which account the project will be created under.
2. **Load user defaults (optional).** Read `~/.plumlayer/operator.json` if it exists (written by
   the `setup` skill), use its `defaults` to pre-fill and avoid re-asking. If it's missing and the
   user wants personalization, suggest running `/setup` first (optional, not required).
3. **The project may already exist.** Call `list_projects`. When the project the user names is
   already there, create nothing. Read where they are and tell them, then stop:
   - `list_drawing_deliveries(projectId)`: which deliveries are registered, if any.
   - `search(projectId, predicate: "appearsOnPage", limit: 1)`: whether any sheet has been
     recognized yet.
   - `search(projectId, predicate: "inDivision", limit: 1)`: whether a project manual has been read.
   - `solicitation_list_packages(projectId, limit: 1)`, reading `total`: whether the baseline
     packages exist.
   - `search(projectId, subjectPrefix: "scopeItem:", limit: 1)`, reading `count`: whether the scope
     run has produced anything.
   Each read is a count, never the rows: this branch only says where the project stands.
<!-- user-facing -->
   Say where the project stands and what the next step is, in plain terms: the set is in and sorted
   by type but nothing is scoped yet, or a delivery is registered but was never read, or nothing has
   been uploaded at all. This branch reads and reports; it writes nothing and creates nothing.
<!-- /user-facing -->
   If the user genuinely wants a second, separate project rather than to carry on with this one,
   confirm that with them before creating it.

---

## 2. Ask for what only the user carries

The goal is a named shell plus only the facts the drawings won't supply, not a complete project
record. Never invent a fact. Mark each one `confirmed`, `uncertain`, or `conflicting` as you go.
A confirmed fact is written in step 4, into its Overview field or as a record entry. An
uncertain one, where the user is unsure or a document is unclear, is not seeded and is not a
Question: when it is one of the ask-now facts below, put it forward in that group; otherwise name
it in the closing report as left unseeded, and why. A conflicting one, where two handed-over
documents disagree, is not seeded either: it becomes one Question with `ask_question`, cited to
both documents, and only when it meets the standard. A Question is about the project, never about
a Plumlayer failure; a tool problem in this interview is reported in the conversation, not raised
as a Question. Question text is plain estimator words, and every Question meets the standard the
`ask_question` verb states: a title, a citation for every place it names, and only what is worth
the design team's time.

### Ask now vs. defer to the read (the triage that keeps this short)

**Ask now, user-only facts no drawing carries.** Even these: *offer, don't interrogate*, accept
"skip" freely.
- **Project name** *(required)*, the user's working name for the pursuit.
- **The drawing delivery and the project manual**, asked for together, in one breath: where the
  drawings are, and whether a project manual / spec book came with them. Give the one-line reason:
  the baseline package split anchors on the spec table of contents, so a manual handed over now
  saves re-running the split later. Local paths are all you need here; step 5 does the upload.
- **Procurement**, how the owner buys the job (a hard bid, a negotiated job), a contract fact often
  absent from the drawings. The choices are the labels on the company's own `owner_process` list
  from `list_project_options`, called once before this ask and reused in step 4, so the answer is one step 4 can fill as given; the saved delivery
  method default is put forward only when it plainly names one of those labels. Take it if known;
  skip if not (the contract confirms it later). Don't argue it against the user default, just
  take what they say. When a document the user handed over (an ITB, an RFP, a bid form) states how
  the owner buys the job, you do not ask it: you fill it from that document in step 4, the closing
  report names the document and page, and the user corrects it on Overview if it is wrong. The
  contract form
  (`contract_type`) is not asked; it is filled in step 4 when the user says it or a document
  states it.

Anything the user volunteers beyond this, an exclusion, a date, a strategy note, is still written
per step 4, but nothing of the kind is asked for.

**Defer to the read, do NOT interrogate.** Step 5's orientation pass reads these off the set:
it fills an empty address, project type and the firms on the contacts from the cover sheet and
title blocks, and the upload produces the set inventory. Note in one line that you'll read it,
then move on:
- Project **type** (cover sheet + index).
- **Parties** beyond any the user volunteers, owner, architect, structural EOR, MEP / civil engineers
  (title blocks + cover stamps). If an engineer is stamped nowhere, that's an upload-time finding / RFI,
  not an interview question.
- **Location** (cover sheet).
- The **drawing-set inventory**, which issues exist and their dates (the drawing index *is* this;
  the registration and recognition in step 5 produce it).

**Size** (gross area, floor and unit counts) is not read off the set by any step yet. Never ask for
it; when the user volunteers it, step 4 records it.

### How the ask-now questions are put

Run, or stop and report; never create a consent step. The user's decisions in this skill are the
ask-now set above and nothing else. Ask them once, conversationally, in one short group. Where
you already hold an answer, put it forward as the answer with its source named (the profile, a
document they handed you, a cover sheet you can see), so the user corrects it rather than composes
it; a pre-filled answer is how their own context earns its keep. Only `name` is required;
everything else is "skip if you don't have it handy." Everything else this skill does is its own
work, recorded with who did it and when, and editable on plumlayer.com: never ask whether to proceed with it,
never ask the user to confirm a summary of what you are about to do, and never put your own next
step to them as a choice. Do not reconcile the user's saved defaults against this project here.
Package and trade-fit decisions belong to `scope-run`, not this step.

Put the ask-now group as a single choice question through the client's choice-question tool where
one exists (`AskUserQuestion` in Claude Code, the equivalent in Codex): one question per fact, each
with the held answer as the first, recommended option and its source named, plus a skip option. A
choice question keeps the turn alive; a prose ask ends it. Where the client has no such tool, ask in
prose with the default stated in the same shape. The starter-file offer (Mode B) is one more
question in that same group, "yes" recommended, never a separate prose ask.

### Mode A: interview (the ask-now set only)
When the Mode B look below finds nothing: ask the group above, pre-filled from user defaults
(`~/.plumlayer/operator.json`), and move on.

### Mode B: read what they already have (preferred when docs exist)
Being started in a folder, or being pointed at one, is a hand-over: the user put you there on
purpose, and what is in it is theirs to give. When the opening message names no path, look through
the folder the session was started in, a few levels down (three is enough), for the drawing set,
the project manual and any bid invitation (an ITB, an RFP, a bid form): PDFs, a drawings or specs folder, a project manual. Never look above that
folder, into siblings, or elsewhere on the machine, and never into a folder the user named as
somewhere else. Say nothing about the search itself.

Check whether the folder already holds `CLAUDE.md` or `AGENTS.md`, and check
`~/.plumlayer/operator.json` for `instructions.scaffold == "declined"`. If either is true, the
instructions offer below is off: offer nothing, write nothing, and never mention the offer, the
profile setting, or that you skipped it.

Otherwise, fold one more offer into this same ask, so it stays one question group, not a second
consent step: the folder has no standing instructions telling an agent how to work in it, a short
starter file means you behave the same way here from the first prompt of every future session and
never reorganize project files on your own, and the file carries no project specifics, so writing
it into a git repo is safe.
<!-- user-facing -->
Example choice-question content, once the drawings and manual are found: project name, pre-filled
from the folder name or a cover sheet / ITB found with the set when one names the job, otherwise a
short free-text entry; procurement (left out when a document found with the set states it), the
company's own choices with the held default as the first, recommended option and its source named,
plus a skip option; and, in the same group, "Write a short starter file so I work the same way here
every time?" with "yes" recommended. When the folder also holds files beyond the drawings, the
manual and any bid invitation (bid tabs, a budget), one more entry in the same group: "Also found
<files> here, use them too or leave them?" with "leave them" recommended.
<!-- /user-facing -->
The drawings and the project manual found are never put to the user as a question: they are named
in the question's framing as what will be uploaded. A bid invitation found with them (an ITB, an
RFP, a bid form) is not put to the take-or-leave question either: read it before the ask, as the
end of this step says, and leave procurement out of the group when it states it. The choice group
holds the project name (pre-filled when a held answer exists, otherwise a short free-text entry),
procurement when no document found with the set states it, the starter-file offer, and, when other
files exist, that one take-or-leave question. The one ask with no held answer, when nothing at all
is found, is the exception the one-turn rule allows: a plain request for the drawings' path.

When the user says to use the other files, each is a handed-over document, read as the end of this
step says: seed what it plainly states, cited to it, and pass any that belongs to the drawing
delivery or the project manual (an addendum, another volume) to step 5 with the rest. A file that
carries neither, a bid tab or a budget, is named in the closing report as read with nothing
seeded. Left, nothing reads them.

The drawings and the project manual are the job, and step 5 uploads them. Never walk above the
folder you were handed, into siblings, or into a folder you merely happen to be running in when the
user named a different one.

**If they accept the starter file,** write the scaffold below, verbatim, to whichever file the
client actually running this session reads: `CLAUDE.md` for Claude Code, `AGENTS.md` for Codex.
Write exactly one of the two, never both.
<!-- user-facing -->
Say in one line what was written and where, and that it is theirs to edit.
<!-- /user-facing -->

```
# Project instructions

This folder is the working directory for a construction project.

## Project files

Project drawings, specifications, addenda, estimates, bids, correspondence,
and other records may be stored in this directory and its subdirectories.
Use the actual project documents as the source for project-specific facts.
Do not infer contractual requirements, scope, pricing, or document precedence
from these instructions.

## Plumlayer

This project may be connected to Plumlayer.
Use the Plumlayer tools when they provide structured project information or
construction-specific capabilities that are more appropriate than manually
processing files.
When citing drawings, specifications, or other project records, preserve the
source reference whenever possible.

## Working behavior

Inspect available project context before asking the user to provide information
that may already exist in this workspace or in Plumlayer.
Do not modify, delete, rename, or reorganize project files unless the user
explicitly requests it.
```

**If they decline,** merge `{"instructions": {"scaffold": "declined"}}` into
`~/.plumlayer/operator.json`, preserving every other field already there. If the file doesn't exist
yet, write it fresh, carrying only `instructions.scaffold` and `_meta` (version 2), so the next
setup does not offer it again either.
<!-- user-facing -->
Say in one short line that you won't offer it again.
<!-- /user-facing -->

Reading a document they handed you is not interrogation, it's the high-value path. Good sources:
- An **ITB / invitation-to-bid** or project summary → name, type, parties, key dates.
- A **drawing index** the architect or the transmittal supplied (a drawing list in the ITB, a
  transmittal sheet) → the set inventory + disciplines.
- A **spec TOC** → divisions/trades in scope.

Seed what a handed-over document plainly states, cited to that document (it is the entry's
source, never a bare fact), and say what you seeded from where. Do not ask the user to confirm a
fact the document states. Anything the source leaves unclear is `uncertain`, and anything two
sources disagree on is `conflicting`; neither is ever a seed, and each is handled as the top of
this step says. Defer the gaps to the read rather than interrogating for them. A bid invitation
found with the set (an ITB, an RFP, a bid form) is read before the ask, so what it states fills its
fact in step 4 and takes that fact out of the group.

---

## 3. Create the project record shell

Call the `create_project` MCP tool with the confirmed `name` (required) and optional
`description`. Capture the returned `projectId`: every write in step 4 below is scoped to
it.

> **Fallback if `create_project` isn't available** (older plugin/server without the verb): ask the
> user to create the project on plumlayer.com (one click), then call `list_projects` and resolve
> the new `projectId` from the list. The rest of the skill is unchanged.
>
> **If the client refuses the call** (its permission check, or the user declining it), nothing was
> created: say so, quote the refusal, and stop. Never send the write again in another shape or
> through another verb; once the user allows it, `/project-setup` starts over from step 1.

<!-- user-facing -->
Confirm back to the user: "Created project **<name>** (`<projectId>`)."
<!-- /user-facing -->
One project = one project record.

---

## 4. Fill Overview and seed the rest

A confirmed fact Overview has a field for goes into that field, through the same verb a person's
edit on Overview goes through, and reads as the user's own write. The rest are record entries.
An uncertain or conflicting fact is written to neither (step 2), and every fact written has a
source: what the user said, or a document they handed over. The fields keep who set them and when,
not what from, so the closing report names where each field's value came from.

### Overview's fields

Fill only what the user said or a handed-over document states; a sparse project is the correct
early state.

- **Project type, procurement, contract.** Use the `list_project_options` answer from step 2
  (call it once now if step 2 did not). For each fact given,
  pick the option on its list (`project_type`, `owner_process`, `contract_type`) whose label
  plainly names what was given, and send the picked ids together:
  `update_project(projectId, projectTypeId, ownerProcessId, contractTypeId)`, only the ones
  picked. When no label plainly names what was given, leave that field empty and name the fact and
  what was given in the closing report. Never create an option, and never pick a near match: a
  contract given as "design-build" against a list of Lump sum, GMP and Cost plus fills nothing.
- **The address.** `update_project(projectId, location: "<the address as given>")`, in the same
  call when the options went out together.
- **The owner's bid date.** The day the bid is due to the owner:
  `set_project_date(projectId, kind: "owner_bid", onDay: "YYYY-MM-DD")`, with `atTime` (`HH:MM`, 24-hour) only
  when a time was given, and always with its `timeZone`; a time whose zone nobody stated and the
  address does not settle is left off and named in the closing report. A date given only for
  subcontractors' bids is not this one: leave it for `prepare-invitations`, which asks for it.
- **The owner, the architect, the engineers.** Each goes on the project's contacts as a firm from
  the company directory. What a firm is on the job is its type in the directory, so the owner is
  the firm typed Owner. For each firm named:
  1. Find it: `directory_list_companies(text: "<the firm's name>")`. Exactly one company whose
     name is the firm's name is that firm. Several that could be it, or only a near match: leave
     the firm off and name it in the closing report; never pick one.
  2. Its type: `directory_list_company_types` lists the account's types. Take the one whose label
     plainly names the role (Owner for the owner, Architect for the architect, Engineer for a
     structural, MEP or civil engineer), as the list spells it. A firm not in the directory is
     added with `directory_add_company(name, vendorKind: [<that type>])`. A firm already there
     without that type gets it beside the types it has,
     `directory_update_company(companyId, vendorKind: [<its types>, <that type>])`, since
     `vendorKind` replaces the whole list. When no type on the list names the role, the firm goes
     on with the types it has, and the closing report says so; never add a type to the list.
  3. Put it on: `project_set_design_team_company(projectId, companyId)`, the firm alone, with no
     `add`.

### The facts recorded as entries

Map the remaining confirmed facts to entries and record them. Prefer the `record_batch` MCP tool,
one call with
`projectId=<the new project>` and an `entries` array of all the confirmed-fact seed entries (it's
atomic: one bad entry rejects the batch and names the index). **Fallback:** if `record_batch` isn't
available (older server), call the `record` tool once per entry, batched in parallel (many per
message).

**Entry shape** (matches the entry atom: `subject — predicate — value` + evidence):
- `sourceInstrument` = `project-setup-interview` (interview) or the uploaded file name (read-in).
  This correctly marks the entry as low-instrument / user-asserted.
- `evidence` = `{ source: "<user-interview | filename>", method: "human", snippet: "<what was
  said / the source line>" }`.
- **Uncertain or conflicting fact:** don't seed it as an entry. An uncertain one is named to the
  user; a conflicting one is one Question cited to both documents, per step 2.

**What to seed** (skip any the user didn't give, never fabricate):

> At this point the table is often mostly empty, a sparse shell is the correct early state, not a
> failure. Seed only what the user volunteered or a handed-over document supports; the set read fills the
> rest. Never ask a question just to populate a row.

| Fact | subject | predicate | value |
|---|---|---|---|
| Size | `project` | `grossArea` / `floorCount` | e.g. `42,000 SF` / `6` |
| Trade in scope | `project` | `tradeInScope` | one entry listing every trade |
| Known set | `set:<id>` | `issueStatus` | `conformed` / `permit` / `bulletin-02` / … |
| Set date | `set:<id>` | `issueDate` | ISO date |
| Known exclusion | `project` | `knownExclusion` | one entry listing every exclusion the user named |

The project type, procurement, contract, address, owner's bid date and the firms on the contacts
are never recorded as entries; they go into Overview's fields above. Keep values literal and
sourced. Every entry carries a `sourceInstrument` and evidence, no exceptions.

---

## 5. Read the delivery in

Run the `drawing-upload` skill now, in full, with this `projectId` and the local paths the user
gave you in step 2. It owns the whole read: what kind of delivery this is, registration, the cloud
upload, sheet-number recognition, the pages the pass could not name, sheet typing, the project
manual's table of contents, and the reconciliation gate. Every gate in it applies unchanged.

- **Run it, don't restate it.** None of its steps are copied here, condensed here, or run partially
  from here. When a step in it calls for a decision, make that decision there, on its own terms.
- **Run it here, in this conversation.** Its questions are put to the user here and its jobs are
  polled here, so the user stays in the loop for the whole read and every report of a job's state
  is first-hand. The one part that runs one level down is the page reading it sends to its sheet
  checker, as its "Who reads the pages" says. Never hand a question or a job to an agent, and never
  answer its questions on the user's behalf in a brief so that an agent will not need them.
- **The context this skill supplies:** the `projectId` from step 3, so its step 1 lists no
  projects, and that this is the project's first delivery. What follows from that is stated once,
  in `drawing-upload` step 1b, the file that owns the rule.
- **Come back here** once it has emitted its closing report, and carry on at step 6.

---

## 6. Orient and draft the baseline packages

Run the `learn-project` skill now, in full, then return here for the closing report. It runs one
level down: start it as its own "Running one level down" section says, handing its orientation
dispatch the `projectId` from step 3, and read back only its summary. The orientation agent reads
the fields and facts step 4 wrote and the sheet inventory, takes a small number of bounded
renders, records cited project-level facts, and drafts and creates the baseline trade-package
split off the spec table of contents; its renders, its spec page reads and its package calls stay
in that agent.

Its preconditions 1 and 2 (a project exists, the set is recognized) hold by construction on this
path: step 3 created the project and step 5 read the set in. If either check fails anyway, its
summary's `stopped:` line names it, and that is a real finding out of step 5, not a precondition
to wave through.

---

## 7. Report

Before the report, decide whether the job is going out to bid, from what this session already
holds and never from a new question. Any one of these is enough: the user called it a bid (a hard
bid, out to bid, a new bid); a document they handed over is an invitation to bid, a bid form, or
instructions to bidders; an owner's bid date was given or filled; or the project manual's
Division 00 carries bidding requirements, which one `search(projectId, subjectPrefix:
"specSection:00", predicate: "hasTitle")` shows (an invitation or advertisement for bids,
instructions to bidders, a bid form). With none of these, the close names the scope run alone.

<!-- user-facing -->
One closing report for the whole session, in plain terms. Read every count back from the record
rather than restating it from what an earlier step said:
- **Created:** project name + `projectId`.
- **Filled on Overview:** each field filled and where its value came from, what the user said
  or the document and page: the project type, procurement, contract, the address, the owner's bid
  date, and each firm put on the contacts with the type it carries.
- **Changed in the directory:** each firm added to the company directory, and each firm already
  there that was given a type (Owner, Architect, Engineer), with the type added.
- **Recorded:** how many other facts were recorded, broken down (size / trades / sets /
  exclusions).
- **Not filled or recorded:** each fact left off and why (the user was unsure, a document was
  unclear, no choice on the company's list names what was given, a firm the directory holds more
  than once, a time with no time zone), listed here in the conversation with what was given. These
  are not on the site, since nothing was written for them; this list is the one place they are
  named.
- **The set:** the delivery that was read in, how many sheets were recognized, how many pages were
  read for a closer look, how many sheets carry a type and how many were left for a closer look, how
  many spec sections were found (or that no project manual came with it), and what the index check
  found.
- **Orientation:** off its summary, in your own words: what it learned, any Question it raised,
  the baseline packages that now exist by name, the ones it created and the ones already on the
  project (their count is `solicitation_list_packages(projectId, limit: 1)`'s `total`, which the
  two lists of names add up to), each package a supplier furnishes with the package that installs its
  items, each default used, how many of the manual's sections are placed on a package, each
  section placed from its title alone by its number, each section whose item the catalog has no
  trade for with the package it went on, and each left on no package with what stopped its
  placing, whether the structure and the description were written, what
  it filled on Overview from the cover sheet and with which sheet, each firm it added to the
  directory or gave a type, anything a sheet states that it left off and why (a sheet that names
  something different from what the user gave is said here plainly), and where the packet landed.
- **What a person should look at on plumlayer.com:** any Question raised for two documents that
  disagree, among the project's Questions; the fields filled on Overview, each carrying your
  name and the time; and the facts recorded, each carrying your name, the time, and what you read
  it from. What you filled and recorded is the project's starting frame now; anyone who changes a
  value later by hand replaces it, and a drawing read fills only what is still empty.
- **Next:** when the job is going out to bid, offer `/prepare-invitations` as the next step in this
  same session: it reads the bidding requirements into the invitations in about a minute and does
  not wait for the scope run, and the user starts it by typing it now or any time later. Then name
  `/scope-run`, which builds the scope list and wants its own session. When nothing you hold says
  the job is going out to bid, say plainly that this session is done and name `/scope-run` alone.
<!-- /user-facing -->

---

## Gates (non-negotiable)

- **One turn, start to finish.** With the set and the manual in hand and the ask-now questions
  answerable, run this session to completion in one turn; only the stop points inside
  `drawing-upload` and `learn-project` end it early.
- **Cite everything.** Every seeded entry carries `sourceInstrument` + evidence. No citation → don't
  seed it. An Overview field is filled only from what the user said or a document states, and
  the closing report names which.
- **Fill the fields, never a look-alike.** A project type, procurement or contract is an option on
  the company's own list whose label plainly names what was given, or the field stays empty. Never
  create an option or a company type, and never pick a near match or one of several directory
  firms.
- **Never invent a fact.** If the user didn't say it and no file shows it, don't seed it. An
  uncertain fact is named to the user and a conflicting one between two documents is one Question
  with `ask_question`; neither is silently resolved, seeded as fact, or dropped.
- **Seeds come from what the user told you.** They take effect as the starting frame, cited to what
  the user said. A drawing read later never writes over an Overview field the user gave; it names
  a sheet that disagrees. A recorded entry a later read replaces is named by it in `supersedesId`.
  Never present one as a fact read off the documents.
- **One project = one project record.** Always seed within the correct `projectId` returned by `create_project`.
- **An existing project is read, never re-created.** Step 1's branch reports where the project
  stands and ends there; it writes nothing.
- **The two sub-skills run in full, where each says.** `drawing-upload` runs in this conversation
  and sends its page reads to its sheet checker; `learn-project` runs one level down, as its
  "Running one level down" says, and its summary is all this session reads of it. Neither is
  restated here, run partially, or swapped for a shortcut through its tools.
- **Run, or stop and report; never create a consent step.** The user's decisions are the ask-now
  set in step 2, put once with a pre-filled answer and its source where you hold one; procurement
  that a handed-over document plainly states is not put at all, and step 4 fills it. Nothing else
  is put to the user as a question or a confirmation.
- **Look inside the folder you were handed, quietly.** When no path was named, look through the
  folder the session started in, up to three levels down, for the drawing set, the project
  manual and any bid invitation; never above that folder, never siblings, never elsewhere on the machine, and never into a
  folder the user named as somewhere else. Say nothing about the search itself; what is found
  becomes the pre-filled answer in the ask-now question. Whatever is read is the citation of what it
  seeds.
- **Every count in the closing report is read back from the record**, never carried across from a
  sub-skill's own report or from memory.
- **Invitations are offered, never run from here.** `prepare-invitations` is named at the close
  when the job is going out to bid, and this skill never starts it. Reading an invitation to bid in
  step 2 for the identity facts it fills (name, type, procurement, the owner, architect and
  engineers, the address, the owner's bid date) is this skill's; setting what the invitations go out under (labor,
  places, site visits and the project's other dates) is `prepare-invitations`'.
- **The instructions offer never overwrites.** Never write `CLAUDE.md` or `AGENTS.md` over one that
  already exists, never write either file without the user's yes, and write only the one file that
  matches the client running the session.
- **Data hygiene.** Project specifics may live in the cloud project record and in the user's cwd config; they
  must never be written to a tracked/committed plugin or repo file.
