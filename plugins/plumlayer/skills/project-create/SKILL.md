---
name: project-create
description: >
  Create and customize a new Plumlayer project: interview the user or read in what they already have
  (an ITB, drawing index, spec TOC, project summary), then seed the new project record with cited
  project-level facts. Trigger on "create a project", "new project", "start a new bid or pursuit",
  "onboard this project", "/project-create", or when the user hands over project documents. Drives
  the create_project and record (or record_batch) MCP tools. Does not upload or read drawings
  (drawing-upload) or build the scope list (scope-run).
---

# Project create: stand up a new project record and customize it

A Plumlayer **project has one project record**, the cloud, entry-based model of that project's current
governing truth. This skill **creates the project and customizes it** by turning what the user knows
(or can hand you in a file) into **cited entries** seeded into the new project record.

> **Doctrine (binds every step):** you read and judge; deterministic tooling grounds; nothing leaves
> unsigned and nothing enters untraced. What you seed here takes effect right away as the project's
> starting frame, recorded as agent-stated with your citation, and it is user-asserted at the
> source: someone *told you*, you didn't read it off a stamped drawing. That makes it the weakest
> thing in the ledger, so when real drawings and specs are read later, better-grounded entries
> supersede or corroborate it. **Cite every entry, never invent a fact, and flag what's uncertain.**
>
> **Confidentiality:** project specifics live in the runtime and in the user's own scoped cloud project record
> (project isolation + private bucket + RLS), that's fine. They must never land in tracked or
> committed plugin/repo files.

---

## Where this sits in the workflow (read this before you start asking questions)

`project-create` stands up the **shell + a minimal starting frame**, it is not the project's
data-entry form. It runs **early, before the drawings are read**, and its whole job is to get a named
project record into existence carrying the few facts only *you* can supply.

**The arc:**
`setup` (user profile, once), then **`project-create`** (this skill, the shell plus minimal
frame), then **`drawing-upload`** (the agent reads and registers the drawing delivery as recognized
sheet entries), then **`scope-run`** (the scope list and the trade packages), then review what's uncertain
on plumlayer.com.

**The load-bearing consequence, don't interrogate for what the set is about to tell you.** Almost
everything about a project is **read off the drawings, in the very next step, at a far higher
instrument tier** than anything the user can recite here. A user answering from memory produces
the **weakest entry there is**, your restatement of what someone told you; a cover-sheet /
title-block read produces a value confirmed off the drawing itself, which **outranks it minutes
later.** So asking the user to guess the project type, the engineers, the trades, or the square footage
isn't just slow, it seeds bottom-tier entries the next step overwrites, cluttering the ledger.
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
3. **Avoid a duplicate.** Call `list_projects`. If something close already exists, confirm the user
   wants a *new* one rather than adding to the existing project record.

---

## 2. Gather project facts (ask narrow, read what you're handed)

The goal is **a named shell plus only the facts the drawings won't supply**, not a complete project
record. **Never invent a fact.** Mark each one `confirmed`, `uncertain`, or `conflicting` as you go,
that classification drives `ambiguityClass` at seed time.

### Ask now vs. defer to the read (the triage that keeps this short)

**Ask now, user-only facts no drawing carries.** Even these: *offer, don't interrogate*, accept
"skip" freely.
- **Project name** *(required)*, the user's working name for the pursuit.
- **Delivery method** (DBB / CM-at-risk / design-build / GMP), a contract fact often absent from the
  drawings. Take it if known; skip if not (the ITB / contract confirms it later). Don't argue it
  against the user default, just record what they say.
- **How they're bidding / buying it**, the trade *packages* they intend to carry, *if* they already
  have a commercial plan in mind. A business decision, not a drawing fact, but it firms up fast once
  they see the set, so don't force it.
- **Known exclusions / allowances / strategy notes** they already hold in mind.
- **Bid due date / key dates**, only if one actually matters to them now; otherwise skip.

**Defer to the read, do NOT interrogate.** The next step reads each of these off the set at a higher
tier. Note in one line that you'll read it, then move on:
- Project **type** (cover sheet + index).
- **Parties** beyond any the user volunteers, owner, architect, structural EOR, MEP / civil engineers
  (title blocks + cover stamps). If an engineer is stamped nowhere, that's an **upload-time finding / RFI**,
  not an interview question.
- **Size**, gross area, floor / unit counts (the drawings, often a code-summary sheet).
- **Location** (cover sheet).
- The **drawing-set inventory**, which issues exist and their dates (the drawing index *is* this;
  `drawing-upload` + sheet registration produce it).

### Mode A: interview (the ask-now set only)
Ask conversationally, in **one short group**, pre-filled from user defaults
(`~/.plumlayer/operator.json`). **Only `name` is required; everything else is "skip if you don't have
it handy."** Do **not** reconcile the user's saved defaults against this project here. Package and
trade-fit decisions belong to `scope-run`, not this step.

### Mode B: read what they already have (preferred when docs exist)
If the user points you at files, **read them locally** and pre-fill, reading a document they handed
you is not interrogation, it's the high-value path. Good sources:
- An **ITB / invitation-to-bid** or project summary → name, type, parties, key dates.
- A **drawing index** (`.csv`/`.xlsx` from the `drawing-upload` skill) → the set inventory + disciplines.
- A **spec TOC** → divisions/trades in scope.

```bash
# read the files the user names (local only, do NOT upload them to the cloud here;
# cloud upload + recognition is a separate path on plumlayer.com)
ls -la <path/to/their/files>
```

Extract candidate facts, **present them for confirmation** (don't trust an extraction silently), seed
what's confirmed, and **defer the gaps to the read rather than interrogating** for them. Anything
ambiguous in the source → mark `uncertain` / `conflicting`.

---

## 3. Create the project record shell

Call the **`create_project`** MCP tool with the confirmed `name` (required) and optional
`description`. **Capture the returned `projectId`**: every entry in the Customize step below is
scoped to it.

> **Fallback if `create_project` isn't available** (older plugin/server without the verb): ask the
> user to create the project on **plumlayer.com** (one click), then call `list_projects` and resolve
> the new `projectId` from the list. The rest of the skill is unchanged.

<!-- user-facing -->
Confirm back to the user: "Created project **<name>** (`<projectId>`)."
<!-- /user-facing -->
One project = one project record.

---

## 4. Customize: seed the starting entries

Map the confirmed facts to entries and record them. **Prefer the `record_batch` MCP
tool**, one call with `projectId=<the new project>` and an `entries` array of all the seed entries (it's
atomic: one bad entry rejects the batch and names the index). **Fallback:** if `record_batch` isn't
available (older server), call the **`record`** tool once per entry, batched in parallel (many per
message).

**Entry shape** (matches the entry atom: `subject — predicate — value` + evidence):
- `sourceInstrument` = `project-setup-interview` (interview) or the **uploaded file name** (read-in).
  This correctly marks the entry as low-instrument / user-asserted.
- `evidence` = `{ source: "<user-interview | filename>", method: "human", snippet: "<what was
  said / the source line>" }`.
- `ambiguityClass` = set it when the fact was `uncertain` or `conflicting` (this is what later
  surfaces it in the `ambiguities` queue / RFI pile for human resolution). Omit for `confirmed`.

**What to seed** (skip any the user didn't give, never fabricate):

> At create time this table is **often mostly empty, a sparse shell is the correct early state**, not a
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

## 5. Name the scope handoff

<!-- user-facing -->
Tell the user the next step is `drawing-upload` to register and recognize the drawing delivery, and
the spec book too, when there is one, since the baseline package split anchors on it. Once the set
is recognized, `/learn-project` orients on it and drafts the baseline package split, then
`/scope-run` builds one grounded, cited scope list and amends and tags the packages.
<!-- /user-facing -->
Never suggest the retired route-first path or a `scope-run`
cluster config: `scope-run` is a skill, not a config.

---

## 6. Report and handoff

<!-- user-facing -->
Tell the user, in plain terms:
- **Created:** project name + `projectId`.
- **Seeded:** how many entries, broken down (facts / parties / trades / sets), and **how many were
  flagged ambiguous** (the pile a person should resolve).
- **Where it landed**, visible now via `search` / `set_grid` / `ambiguities` in this session, and on
  **plumlayer.com**, where every seeded value carries your name, the time, and what you read it from.
  Anything you flagged is what a person should look at.
- **Next steps:** upload the drawing set on plumlayer.com (or run `drawing-upload` locally), then run
  `/learn-project` to orient and draft the baseline trade packages, then `/scope-run` to build the
  scope list and amend and tag the packages.
  Say "seeded 12 project facts, 2 flagged for your judgment": what you
  seeded is the project's starting frame now, carrying your name and what you were told, and anything
  a person changes, or a drawing read later replaces, wins.
<!-- /user-facing -->

---

## Gates (non-negotiable)

- **Cite everything.** Every seeded entry carries `sourceInstrument` + evidence. No citation → don't
  seed it.
- **Never invent a fact.** If the user didn't say it and no file shows it, don't seed it. Uncertain or
  conflicting facts are seeded **with `ambiguityClass`**, not silently resolved or dropped.
- **Seeds are the weakest entries in the ledger.** They take effect as the starting frame, recorded as
  agent-stated from what the user told you, and a drawing read supersedes them. Never present one
  as a fact read off the documents.
- **One project = one project record.** Always seed within the correct `projectId` returned by `create_project`.
- **Data hygiene.** Project specifics may live in the cloud project record and in the user's cwd config; they
  must never be written to a tracked/committed plugin or repo file.
