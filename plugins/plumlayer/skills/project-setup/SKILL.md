---
name: project-setup
description: >
  Set up a new pursuit end to end: create the project record, seed the facts only you carry, read the
  drawing delivery and the project manual in, then orient and draft the baseline packages. Trigger on
  "set up this project", "new project", "create a project", "start a new bid or pursuit", "onboard
  this project", "/project-setup". Drives create_project, record_batch, and the drawing-upload and
  learn-project skills in full. Does not build the scope list (scope-run), read sub proposals
  (bid-intake), or place takeoff measurements (takeoff).
---

# Project setup: stand up a new pursuit, end to end

A Plumlayer **project has one project record**, the cloud, entry-based model of that project's current
governing truth. This skill **stands the pursuit up**: it creates the project, turns what the user
knows (or can hand you in a file) into **cited entries**, reads the drawing delivery and the project
manual in, and orients on what came back.

> **Doctrine (binds every step):** you read and judge; deterministic tooling grounds; nothing leaves
> unsigned and nothing enters untraced. What you seed here takes effect right away as the project's
> starting frame, recorded as agent-stated with your citation, and it is user-asserted at the
> source: someone *told you*, you didn't read it off a stamped drawing. That makes it the weakest
> thing in the ledger, so when real drawings and specs are read later, better-grounded entries
> supersede or corroborate it. **Cite every entry, never invent a fact, and raise a Question for
> what's uncertain.**
>
> **Confidentiality:** project specifics live in the runtime and in the user's own scoped cloud project record
> (project isolation + private bucket + RLS), that's fine. They must never land in tracked or
> committed plugin/repo files.

---

## Where this sits (read this before you start asking questions)

A skill is a step; what a user runs is a process. This skill is **New pursuit, session 1**, and it
runs that session end to end: the shell, the seed facts, the delivery read in, and the orientation
pass. The **scope run is session 2**, its own skill (`scope-run`), and it wants its own session; do
not start it from here. When new paper arrives later (a bulletin, an addendum, a re-issue), that is
a different process and its first step is `drawing-upload` on its own.

**The load-bearing consequence, don't interrogate for what the set is about to tell you.** Almost
everything about a project is **read off the drawings later in this same session, at a far higher
instrument tier** than anything the user can recite here. A user answering from memory produces
the **weakest entry there is**, your restatement of what someone told you; a cover-sheet /
title-block read produces a value confirmed off the drawing itself, which **supersedes it minutes
later, naming the restatement as what it replaces.** So asking the user to guess the project type, the engineers, the trades, or the square footage
isn't just slow, it seeds bottom-tier entries the set read overwrites, cluttering the ledger.
<!-- user-facing -->
**Ask
only for what no drawing will ever carry; for the rest, say "I'll read that off the set next" and move
on.**
<!-- /user-facing -->

---

## 1. Preflight

1. **Confirm the account.** Call `whoami`. State which account the project will be created under.
2. **Load user defaults (optional).** Read `~/.plumlayer/operator.json` if it exists (written by
   the `setup` skill), use its `defaults` to pre-fill and avoid re-asking. If it's missing and the
   user wants personalization, suggest running `/setup` first (optional, not required).
3. **The project may already exist.** Call `list_projects`. When the project the user names is
   already there, **create nothing**. Read where they are and tell them, then stop:
   - `list_drawing_deliveries(projectId)`: which deliveries are registered, if any.
   - `search(projectId, predicate: "appearsOnPage", limit: 1)`: whether any sheet has been
     recognized yet.
   - `search(projectId, predicate: "inDivision", limit: 1)`: whether a project manual has been read.
   - `solicitation_list_packages(projectId)`: whether the baseline packages exist.
   - `list_scope_items(projectId)`: whether the scope run has produced anything.
<!-- user-facing -->
   Say where the project stands and what the next step is, in plain terms: the set is in and sorted
   by type but nothing is scoped yet, or a delivery is registered but was never read, or nothing has
   been uploaded at all. This branch reads and reports; it writes nothing and creates nothing.
<!-- /user-facing -->
   If the user genuinely wants a second, separate project rather than to carry on with this one,
   confirm that with them before creating it.

---

## 2. Ask for what only the user carries

The goal is **a named shell plus only the facts the drawings won't supply**, not a complete project
record. **Never invent a fact.** Mark each one `confirmed`, `uncertain`, or `conflicting` as you go:
a confirmed fact seeds as a record entry; an uncertain or conflicting one gets raised as a Question
with `ask_question` instead of seeded. A Question is about the project, never about a Plumlayer
failure; a tool problem in this interview is reported in the conversation, not raised as a
Question. Question text is plain estimator words, per docs/plugin-text-style.md.

### Ask now vs. defer to the read (the triage that keeps this short)

**Ask now, user-only facts no drawing carries.** Even these: *offer, don't interrogate*, accept
"skip" freely.
- **Project name** *(required)*, the user's working name for the pursuit.
- **The drawing delivery and the project manual**, asked for together, in one breath: where the
  drawings are, and whether a project manual / spec book came with them. Give the one-line reason:
  the baseline package split anchors on the spec table of contents, so a manual handed over now
  saves re-running the split later. Local paths are all you need here; step 5 does the upload.
- **Delivery method** (DBB / CM-at-risk / design-build / GMP), a contract fact often absent from the
  drawings. Take it if known; skip if not (the ITB / contract confirms it later). Don't argue it
  against the user default, just record what they say.
- **How they're bidding / buying it**, the trade *packages* they intend to carry, *if* they already
  have a commercial plan in mind. A business decision, not a drawing fact, but it firms up fast once
  they see the set, so don't force it.
- **Known exclusions / allowances / strategy notes** they already hold in mind.
- **Bid due date / key dates**, only if one actually matters to them now; otherwise skip.

**Defer to the read, do NOT interrogate.** Step 5 reads each of these off the set at a higher
tier. Note in one line that you'll read it, then move on:
- Project **type** (cover sheet + index).
- **Parties** beyond any the user volunteers, owner, architect, structural EOR, MEP / civil engineers
  (title blocks + cover stamps). If an engineer is stamped nowhere, that's an **upload-time finding / RFI**,
  not an interview question.
- **Size**, gross area, floor / unit counts (the drawings, often a code-summary sheet).
- **Location** (cover sheet).
- The **drawing-set inventory**, which issues exist and their dates (the drawing index *is* this;
  the registration and recognition in step 5 produce it).

### How the ask-now questions are put

Run, or stop and report; never create a consent step. The user's decisions in this skill are the
ask-now set above and nothing else. Ask them once, conversationally, in **one short group**. Where
you already hold an answer, put it forward as the answer with its source named (the profile, a
document they handed you, a cover sheet you can see), so the user corrects it rather than composes
it; a pre-filled answer is how their own context earns its keep. **Only `name` is required;
everything else is "skip if you don't have it handy."** Everything else this skill does is its own
work, recorded with its trail and editable on plumlayer.com: never ask whether to proceed with it,
never ask the user to confirm a summary of what you are about to do, and never put your own next
step to them as a choice. Do not reconcile the user's saved defaults against this project here.
Package and trade-fit decisions belong to `scope-run`, not this step.

### Mode A: interview (the ask-now set only)
Nothing was handed over: ask the group above, pre-filled from user defaults
(`~/.plumlayer/operator.json`), and move on.

### Mode B: read what they already have (preferred when docs exist)
Being started in a folder, or being pointed at one, is a hand-over: the user put you there on
purpose, and what is in it is theirs to give. Before opening anything, list what you were handed,
one level deep, and say what you see.

Check whether the folder already holds `CLAUDE.md` or `AGENTS.md`, and check
`~/.plumlayer/operator.json` for `instructions.scaffold == "declined"`. If either is true, the
instructions offer below is off: offer nothing, write nothing, say nothing about it.

Otherwise, fold one more offer into this same ask, so it stays one question group, not a second
consent step: the folder has no standing instructions telling an agent how to work in it, a short
starter file means you behave the same way here from the first prompt of every future session and
never reorganize project files on your own, and the file carries no project specifics, so writing
it into a git repo is safe.
<!-- user-facing -->
"I see the drawing set, a spec folder, two bid tabs and a budget. I'll take the drawings and the
specs; do you want me to read the bid tabs and the budget too, or leave them? Also, this folder has
no instructions file telling an agent how to work here, so I stay consistent from the start and
never reorganize your project files on my own. Want me to write a short starter file for that?"
<!-- /user-facing -->
The drawings and the project manual you take without asking: they are the job, and step 5 uploads
them. Anything else in the folder you name and ask about once, then proceed with the answer. Never
walk above the folder you were handed, into siblings, or into a folder you merely happen to be
running in when the user named a different one. Never go looking: if nothing was handed over and
the user has not said where the drawings are, ask where they are.

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
`~/.plumlayer/operator.json`, preserving every other field already there. If the file doesn't
exist yet, don't create it for this alone; the offer is simply made again next time, and `setup`
explains the field.
<!-- user-facing -->
Say in one line that you won't offer it again, and that `/setup` can turn the offer back on.
<!-- /user-facing -->

Reading a document they handed you is not interrogation, it's the high-value path. Good sources:
- An **ITB / invitation-to-bid** or project summary → name, type, parties, key dates.
- A **drawing index** the architect or the transmittal supplied (a drawing list in the ITB, a
  transmittal sheet) → the set inventory + disciplines.
- A **spec TOC** → divisions/trades in scope.

```bash
# list what the user handed over, one level deep, and say what is there before opening
# anything; the drawings and the project manual are uploaded and read in step 5, not here
ls -la <path/to/their/files>
```

Seed what a handed-over document plainly states, cited to that document (it is the entry's
source, never a bare fact), and say what you seeded from where. Do not ask the user to confirm a
fact the document states. Anything the source leaves unclear or that two sources disagree on is
`uncertain` / `conflicting` and becomes a Question, never a seed. **Defer the gaps to the read
rather than interrogating** for them.

---

## 3. Create the project record shell

Call the **`create_project`** MCP tool with the confirmed `name` (required) and optional
`description`. **Capture the returned `projectId`**: every entry in the seed step below is
scoped to it.

> **Fallback if `create_project` isn't available** (older plugin/server without the verb): ask the
> user to create the project on **plumlayer.com** (one click), then call `list_projects` and resolve
> the new `projectId` from the list. The rest of the skill is unchanged.

<!-- user-facing -->
Confirm back to the user: "Created project **<name>** (`<projectId>`)."
<!-- /user-facing -->
One project = one project record.

---

## 4. Seed the facts only the user carries

Map the confirmed facts to entries and record them; raise every uncertain or conflicting fact as a
Question instead of seeding it. **Prefer the `record_batch` MCP tool**, one call with
`projectId=<the new project>` and an `entries` array of all the confirmed-fact seed entries (it's
atomic: one bad entry rejects the batch and names the index). **Fallback:** if `record_batch` isn't
available (older server), call the **`record`** tool once per entry, batched in parallel (many per
message).

**Entry shape** (matches the entry atom: `subject — predicate — value` + evidence):
- `sourceInstrument` = `project-setup-interview` (interview) or the **uploaded file name** (read-in).
  This correctly marks the entry as low-instrument / user-asserted.
- `evidence` = `{ source: "<user-interview | filename>", method: "human", snippet: "<what was
  said / the source line>" }`.
- **Uncertain or conflicting fact:** don't seed it as an entry. Raise it with `ask_question` instead,
  citing the source(s) it came from, so a person resolves it.

**What to seed** (skip any the user didn't give, never fabricate):

> At this point the table is **often mostly empty, a sparse shell is the correct early state**, not a
> failure. Seed only what the user volunteered or a handed-over document supports; the set read fills the
> rest, at a higher tier. Never ask a question just to populate a row.

| Fact | subject | predicate | value |
|---|---|---|---|
| Project type | `project` | `projectType` | e.g. `interior fit-out` |
| Delivery method | `project` | `deliveryMethod` | e.g. `CM-at-risk` |
| Location | `project` | `location` | the location string |
| Size | `project` | `grossArea` / `floorCount` | e.g. `42,000 SF` / `6` |
| Bid due date | `project` | `bidDueDate` | ISO date |
| Owner | `party:<slug>` | `hasRole` | `owner` (+ a `name` entry) |
| Architect of record | `party:<slug>` | `hasRole` | `architect-of-record` |
| Structural engineer | `party:<slug>` | `hasRole` | `structural-engineer` |
| MEP engineer | `party:<slug>` | `hasRole` | `mep-engineer` |
| GC / CM | `party:<slug>` | `hasRole` | `gc` / `cm` |
| Party name | `party:<slug>` | `name` | the firm name |
| Trade in scope | `project` | `tradeInScope` | one entry per trade |
| Known set | `set:<id>` | `issueStatus` | `conformed` / `permit` / `bulletin-02` / … |
| Set date | `set:<id>` | `issueDate` | ISO date |
| Known exclusion | `project` | `knownExclusion` | the exclusion text |

Use short, stable slugs for party subjects (`party:smma`, `party:owner`). Keep values literal and
sourced. **Every entry carries a `sourceInstrument` and evidence, no exceptions.**

---

## 5. Read the delivery in

Run the **`drawing-upload`** skill now, in full, with this `projectId` and the local paths the user
gave you in step 2. It owns the whole read: what kind of delivery this is, registration, the cloud
upload, sheet-number recognition, the pages the pass could not name, sheet typing, the project
manual's table of contents, and the reconciliation gate. Every gate in it applies unchanged.

- **Run it, don't restate it.** None of its steps are copied here, condensed here, or run partially
  from here. When a step in it calls for a decision, make that decision there, on its own terms.
- **Run it here, in this conversation.** Never hand it, or any part of it, to a background agent or
  a subagent, and never answer its questions on the user's behalf in a brief so that an agent will
  not need them. The user stays in the loop for the whole read, and every report of a job's state
  is first-hand.
- **The one piece of context this skill supplies:** this is the project's first delivery. What
  follows from that is stated once, in `drawing-upload` step 1b, the file that owns the rule.
- **Come back here** once it has emitted its closing report, and carry on at step 6.

---

## 6. Orient and draft the baseline packages

Run the **`learn-project`** skill now, in full, then return here for the closing report. It reads
the seeded facts and the sheet inventory, takes a small number of bounded renders, records cited
project-level facts, and drafts and creates the baseline trade-package split off the spec table of
contents.

Its preconditions 1 and 2 (a project exists, the set is recognized) hold by construction on this
path: step 3 created the project and step 5 read the set in. If either check fails anyway, that is a
real finding out of step 5, not a precondition to wave through.

---

## 7. Report

<!-- user-facing -->
One closing report for the whole session, in plain terms. Read every count back from the record
rather than restating it from what an earlier step said:
- **Created:** project name + `projectId`.
- **Seeded:** how many entries, broken down (facts / parties / trades / sets), and how many were
  raised as Questions, the pile a person should resolve.
- **The set:** the delivery that was read in, how many sheets were recognized, how many pages you
  read yourself, how many sheets carry a type and how many you left for a closer look, how many
  spec sections were found (or that no project manual came with it), and what the index check found.
- **Orientation:** what it learned, and the baseline packages that now exist.
- **What a person should look at:** everything raised as a Question, on plumlayer.com, where every
  seeded value carries your name, the time, and what you read it from. What you seeded is the
  project's starting frame now, carrying your name and what you were told, and anything a person
  changes, or a drawing read later replaces, wins.
- **Next:** the scope run is the next step and it wants its own session. Say plainly that this
  session is done, and that `/scope-run` starts the next one.
<!-- /user-facing -->

---

## Gates (non-negotiable)

- **Cite everything.** Every seeded entry carries `sourceInstrument` + evidence. No citation → don't
  seed it.
- **Never invent a fact.** If the user didn't say it and no file shows it, don't seed it. Uncertain or
  conflicting facts are raised as Questions with `ask_question`, not silently resolved, seeded as
  fact, or dropped.
- **Seeds are the weakest entries in the ledger.** They take effect as the starting frame, recorded as
  agent-stated from what the user told you, and a drawing read supersedes them. Never present one
  as a fact read off the documents.
- **One project = one project record.** Always seed within the correct `projectId` returned by `create_project`.
- **An existing project is read, never re-created.** Step 1's branch reports where the project
  stands and ends there; it writes nothing.
- **The two sub-skills run in full, in this conversation.** `drawing-upload` and `learn-project`
  are run as written, never restated here, never run partially, never swapped for a shortcut
  through their tools, and never handed to a background agent.
- **Run, or stop and report; never create a consent step.** The user's decisions are the ask-now
  set in step 2, put once with a pre-filled answer and its source where you hold one. Nothing else
  is put to the user as a question or a confirmation.
- **Read what was handed over, and say so.** A folder you were started in or pointed at is listed
  one level deep and described before anything opens; drawings and the manual are taken, anything
  else is asked about once; never above that folder, never a search of the machine. Whatever is
  read is the citation of what it seeds.
- **Every count in the closing report is read back from the record**, never carried across from a
  sub-skill's own report or from memory.
- **The instructions offer never overwrites.** Never write `CLAUDE.md` or `AGENTS.md` over one that
  already exists, never write either file without the user's yes, and write only the one file that
  matches the client running the session.
- **Data hygiene.** Project specifics may live in the cloud project record and in the user's cwd config; they
  must never be written to a tracked/committed plugin or repo file.
