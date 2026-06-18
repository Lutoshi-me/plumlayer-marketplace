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

## Step 0 — Preflight

1. **Confirm the account.** Call `whoami`. State which account the project will be created under.
2. **Load operator defaults (optional).** Read `~/.plumlayer/operator.json` if it exists (written by
   the `setup` skill) — use its `defaults` to pre-fill and avoid re-asking. If it's missing and the
   user wants personalization, suggest running `/setup` first (optional, not required).
3. **Avoid a duplicate.** Call `list_projects`. If something close already exists, confirm the user
   wants a *new* one rather than adding to the existing MOSOT.

---

## Step 1 — Gather project facts (two intake modes — use either or both)

The goal is a confirmed set of project facts. **Never invent one.** Mark every fact `confirmed`,
`uncertain`, or `conflicting` as you go — that classification drives `ambiguityClass` at seed time.

### Mode A — Interview
Ask conversationally, in small groups, pre-filled from operator defaults. Only `name` is strictly
required; everything else is "skip if unknown."

- **Identity:** project name *(required)*; one-line description; project type; delivery method;
  location; gross area / floors.
- **Parties** (these seed the party-trust frame — who is authoritative about what): owner, architect
  of record, structural engineer (EOR), MEP engineer, GC/CM, and any already-known key subs. Get a
  name for each you can.
- **Drawing sets known:** which issues exist and their status (e.g. `conformed`, `permit`,
  `bulletin 02`, `DD`, `addendum 1`) and dates, if known. (Files aren't uploaded here — this just
  records what exists.)
- **Trades in scope:** the trade packages this project will be bid/bought as (drives the scope-run
  lens set).
- **Key dates:** bid due date, award target, etc.
- **Known scope notes / exclusions / allowances** the user already has in mind.

### Mode B — Ingest uploaded info
If the user points you at files they already have, **read them locally** to pre-fill the interview,
then confirm. Good sources:
- An **ITB / invitation-to-bid** or project summary → name, type, parties, key dates.
- A **drawing index** (`.csv`/`.xlsx` from the `drawing-index` skill) → the set inventory + disciplines.
- A **spec TOC** → divisions/trades in scope.

```bash
# read the files the user names (local only — do NOT upload them to the cloud here;
# cloud upload + ingest is a separate path on plumlayer.com)
ls -la <path/to/their/files>
```

Extract candidate facts, **present them for confirmation** (don't trust an extraction silently), and
fill gaps by asking. Anything ambiguous in the source → mark `uncertain`/`conflicting`.

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

Map the confirmed facts to **`proposed` claims** and append each with the **`propose`** MCP tool,
passing `projectId=<the new project>`. **Batch the calls in parallel** (many per message).

**Claim shape** (matches the Claim atom — `subject — predicate — value` + evidence):
- `sourceInstrument` = `project-setup-interview` (interview) or the **uploaded file name** (ingest).
  This correctly marks the claim as low-instrument / operator-asserted.
- `evidence` = `{ source: "<operator-interview | filename>", method: "human", snippet: "<what was
  said / the source line>" }`.
- `ambiguityClass` = set it when the fact was `uncertain` or `conflicting` (this is what later
  surfaces it in the `ambiguities` queue / RFI pile for human resolution). Omit for `confirmed`.

**What to seed** (skip any the user didn't give — never fabricate):

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
