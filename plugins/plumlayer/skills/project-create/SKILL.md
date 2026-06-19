---
name: project-create
description: >
  Create and customize a new Plumlayer project (= a MOSOT) by interviewing the user or ingesting
  project info they already have (an ITB, a drawing index, a spec TOC, a project summary), then
  seeding the new MOSOT with cited, proposed project-level claims. Trigger on "create a project",
  "new project", "set up / start a new MOSOT", "onboard this project", "start a new bid / pursuit",
  "/project-create", or when the user hands over project documents to spin up a project. Creates the
  project via the create_project MCP verb, seeds parties / delivery / type / trades / sets via the
  propose verb (everything proposed — a human promotes on plumlayer.com), and can emit a scope-run
  cluster config so the user can scope the set next.
---

# Project Create — stand up a new MOSOT and customize it

A Plumlayer **project is one MOSOT** — the cloud, claim-based model of that project's current
governing truth. This skill **creates the project and customizes it** by turning what the user knows
(or can hand you in a file) into **cited, `proposed` claims** seeded into the new MOSOT.

> **Doctrine (binds every step):** you read and judge; deterministic tooling grounds; **nothing
> governs unverified.** Everything you seed here is **`proposed`** and is **operator-asserted** — the
> lowest instrument tier (someone *told you*, you didn't read it off a stamped drawing). It is a
> starting frame for the project, **not** governing truth. A human reviews and promotes on
> plumlayer.com; when real drawings/specs are ingested later, higher-instrument claims supersede or
> corroborate these. **Cite every claim, never invent a fact, and flag what's uncertain.**
>
> **Confidentiality:** project specifics live in the runtime and in the user's own scoped cloud MOSOT
> (project isolation + private bucket + RLS) — that's fine. They must **never** land in tracked or
> committed plugin/repo files. Any local config you write (a cluster config) stays in the user's cwd
> and out of git.

---

## Where this sits in the workflow (read this before you start asking questions)

`project-create` stands up the **shell + a minimal starting frame** — it is **not** the project's
data-entry form. It runs **early, before the drawings are read**, and its whole job is to get a named
MOSOT into existence carrying the few facts only *you* can supply.

**The arc:**
`setup` (operator profile, once) → **`project-create` (this skill — shell + minimal frame)** →
**ingest & read the set** (the agent reads the cover sheet, drawing index, title blocks, and specs —
via the sheet-registration / `scope-run` path — and asserts grounded sheet / party / type / size
claims) → `scope-run` (per-trade takeoff) → **review & promote on plumlayer.com**.

**The load-bearing consequence — don't interrogate for what the set is about to tell you.** Almost
everything about a project is **read off the drawings, in the very next step, at a far higher
instrument tier** than anything the user can recite here. An operator answering from memory produces
the **lowest tier there is** — `proposed` + operator-asserted ("someone told me"); a cover-sheet /
title-block read produces a grounded, `authoritative`-eligible claim that **supersedes it minutes
later.** So asking the user to guess the project type, the engineers, the trades, or the square footage
isn't just slow — it seeds bottom-tier claims the next step overwrites, cluttering the ledger. **Ask
only for what no drawing will ever carry; for the rest, say "I'll read that off the set next" and move
on.**

---

## Step 0 — Preflight

1. **Confirm the account.** Call `whoami`. State which account the project will be created under.
2. **Load operator defaults (optional).** Read `~/.plumlayer/operator.json` if it exists (written by
   the `setup` skill) — use its `defaults` to pre-fill and avoid re-asking. If it's missing and the
   user wants personalization, suggest running `/setup` first (optional, not required).
3. **Avoid a duplicate.** Call `list_projects`. If something close already exists, confirm the user
   wants a *new* one rather than adding to the existing MOSOT.

---

## Step 1 — Gather project facts (ask narrow; read what you're handed)

The goal is **a named shell plus only the facts the drawings won't supply** — not a complete project
record. **Never invent a fact.** Mark each one `confirmed`, `uncertain`, or `conflicting` as you go —
that classification drives `ambiguityClass` at seed time.

### Ask now vs. defer to the read (the triage that keeps this short)

**Ask now — operator-only facts no drawing carries.** Even these: *offer, don't interrogate* — accept
"skip" freely.
- **Project name** *(required)* — the user's working name for the pursuit.
- **Delivery method** (DBB / CM-at-risk / design-build / GMP) — a contract fact often absent from the
  drawings. Take it if known; skip if not (the ITB / contract confirms it later). Don't argue it
  against the operator default — just record what they say.
- **How they're bidding / buying it** — the trade *packages* they intend to carry, *if* they already
  have a commercial plan in mind. A business decision, not a drawing fact — but it firms up fast once
  they see the set, so don't force it.
- **Known exclusions / allowances / strategy notes** they already hold in mind.
- **Bid due date / key dates** — only if one actually matters to them now; otherwise skip.

**Defer to the read — do NOT interrogate.** The next step reads each of these off the set at a higher
tier. Note in one line that you'll read it, then move on:
- Project **type** (cover sheet + index).
- **Parties** beyond any the user volunteers — owner, architect, structural EOR, MEP / civil engineers
  (title blocks + cover stamps). If an engineer is stamped nowhere, that's an **ingestion finding / RFI**,
  not an interview question.
- **Size** — gross area, floor / unit counts (the drawings, often a code-summary sheet).
- **Location** (cover sheet).
- The **drawing-set inventory** — which issues exist and their dates (the drawing index *is* this;
  `drawing-index` + sheet registration produce it).

### Mode A — Interview (the ask-now set only)
Ask conversationally, in **one short group**, pre-filled from operator defaults
(`~/.plumlayer/operator.json`). **Only `name` is required; everything else is "skip if you don't have
it handy."** Do **not** reconcile the operator's saved defaults (e.g. interior-only scope lenses)
against this project here — trade / lens fit is a `scope-run` input, decided when the set is read.

### Mode B — Ingest what they already have (preferred when docs exist)
If the user points you at files, **read them locally** and pre-fill — reading a document they handed
you is not interrogation, it's the high-value path. Good sources:
- An **ITB / invitation-to-bid** or project summary → name, type, parties, key dates.
- A **drawing index** (`.csv`/`.xlsx` from the `drawing-index` skill) → the set inventory + disciplines.
- A **spec TOC** → divisions/trades in scope.

```bash
# read the files the user names (local only — do NOT upload them to the cloud here;
# cloud upload + ingest is a separate path on plumlayer.com)
ls -la <path/to/their/files>
```

Extract candidate facts, **present them for confirmation** (don't trust an extraction silently), seed
what's confirmed, and **defer the gaps to the read rather than interrogating** for them. Anything
ambiguous in the source → mark `uncertain` / `conflicting`.

---

## Step 2 — Create the MOSOT shell

Call the **`create_project`** MCP tool with the confirmed `name` (required) and optional
`description`. **Capture the returned `projectId`** — every claim in Step 3 is scoped to it.

> **Fallback if `create_project` isn't available** (older plugin/server without the verb): ask the
> user to create the project on **plumlayer.com** (one click), then call `list_projects` and resolve
> the new `projectId` from the list. The rest of the skill is unchanged.

Confirm back to the user: "Created project **<name>** (`<projectId>`)." One project = one MOSOT.

---

## Step 3 — Customize: seed proposed claims

Map the confirmed facts to **`proposed` claims** and deposit them. **Prefer the `propose_batch` MCP
tool** — one call with `projectId=<the new project>` and a `claims` array of all the seed entries (it's
atomic: one bad entry rejects the batch and names the index). **Fallback:** if `propose_batch` isn't
available (older server), call the **`propose`** tool once per claim, batched in parallel (many per
message).

**Claim shape** (matches the Claim atom — `subject — predicate — value` + evidence):
- `sourceInstrument` = `project-setup-interview` (interview) or the **uploaded file name** (ingest).
  This correctly marks the claim as low-instrument / operator-asserted.
- `evidence` = `{ source: "<operator-interview | filename>", method: "human", snippet: "<what was
  said / the source line>" }`.
- `ambiguityClass` = set it when the fact was `uncertain` or `conflicting` (this is what later
  surfaces it in the `ambiguities` queue / RFI pile for human resolution). Omit for `confirmed`.

**What to seed** (skip any the user didn't give — never fabricate):

> At create time this table is **often mostly empty — a sparse shell is the correct early state**, not a
> failure. Seed only what the user volunteered or a handed-over document supports; the set read fills the
> rest, at a higher tier. Never ask a question just to populate a row.

| Fact | subject | predicate | value |
|---|---|---|---|
| Project type | `project` | `projectType` | e.g. `interior fit-out` |
| Delivery method | `project` | `deliveryMethod` | e.g. `CM-at-risk` |
| Location | `project` | `location` | the location string |
| Size | `project` | `grossArea` / `floorCount` | e.g. `42,000 SF` / `6` |
| Bid due date | `project` | `bidDueDate` | ISO date |
| Owner | `party:<slug>` | `hasRole` | `owner` (+ a `name` claim) |
| Architect of record | `party:<slug>` | `hasRole` | `architect-of-record` |
| Structural engineer | `party:<slug>` | `hasRole` | `structural-engineer` |
| MEP engineer | `party:<slug>` | `hasRole` | `mep-engineer` |
| GC / CM | `party:<slug>` | `hasRole` | `gc` / `cm` |
| Party name | `party:<slug>` | `name` | the firm name |
| Trade in scope | `project` | `tradeInScope` | one claim per trade |
| Known set | `set:<id>` | `issueStatus` | `conformed` / `permit` / `bulletin-02` / … |
| Set date | `set:<id>` | `issueDate` | ISO date |
| Known exclusion | `project` | `knownExclusion` | the exclusion text |

Use short, stable slugs for party subjects (`party:smma`, `party:owner`). Keep values literal and
sourced. **Every claim carries a `sourceInstrument` and evidence — no exceptions.**

---

## Step 4 — (Optional) wire up a scope-run config

Offer to pre-fill a **`scope-run` cluster config** so the user can scope this set next without
re-entering anything. If they want it, copy the bundled template and fill it from the interview:

```bash
PLUGIN="$CLAUDE_PLUGIN_ROOT/scope-harness"
mkdir -p ./clusters
cp "$PLUGIN/clusters/cluster_TEMPLATE.json" ./clusters/cluster_<job>.json
# fill: job, setId (NEVER a real project name — a generic tag), trades/lenses (from scope), grainLevel
```

This config lives in the user's **cwd**, is **gitignored**, and **carries no confidential PDF path**.
Tell the user they can now run `/scope-run` pointed at their drawing PDF.

---

## Step 5 — Report + handoff

Tell the user, in plain terms:
- **Created:** project name + `projectId`.
- **Seeded:** how many claims, broken down (facts / parties / trades / sets), and **how many were
  flagged ambiguous** (the pile a human should resolve).
- **Everything is `proposed`** — visible now via `search` / `set_grid` / `ambiguities` in this session,
  and on **plumlayer.com** for review and promotion. Nothing governs until a human promotes it.
- **Next steps:** upload the drawing set on plumlayer.com (or run `drawing-index` locally), then
  `scope-run` to take off scope, then review/promote on plumlayer.com.

---

## Gates (non-negotiable)

- **Cite everything.** Every seeded claim carries `sourceInstrument` + evidence. No citation → don't
  seed it.
- **Never invent a fact.** If the user didn't say it and no file shows it, don't seed it. Uncertain or
  conflicting facts are seeded **with `ambiguityClass`**, not silently resolved or dropped.
- **Everything is `proposed`.** This skill never promotes — a human does, on the review surface. Seed
  claims are operator-asserted (lowest instrument); they don't govern.
- **One project = one MOSOT.** Always seed within the correct `projectId` returned by `create_project`.
- **Data hygiene.** Project specifics may live in the cloud MOSOT and in the user's cwd config; they
  must **never** be written to a tracked/committed plugin or repo file. No confidential PDF path in a
  committed cluster config.
