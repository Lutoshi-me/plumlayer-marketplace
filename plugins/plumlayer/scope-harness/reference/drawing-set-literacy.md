# Drawing-set literacy — what a set is, how to read it, in what order

> **PLU-323 guard:** this reference was written for the superseded route-first harness. It remains useful
> as historical set-reading doctrine, but normal `/scope-run` execution is blocked while PLU-274 rebuilds
> scope-item-first.

**Status:** v0.1 — the second cross-trade doctrine in `reference/` (sibling to `read-grain.md`). Where
`read-grain.md` answers *"what is one scope item?"*, this answers the question **before** it: *"what am I
looking at, and where do I find the scope?"* It governs every read — the conductor at Ground/cluster
selection, and the per-sheet reader as it orients on a sheet.

**Why this exists.** A construction set is not a pile of pages to brute-force; it is a **structured
document with a table of contents, a definition layer, and a conventional order**. An agent that reads it
blind — no map, no sense of which sheets carry the scope, no read sequence — either drowns (reads details
before plans) or misses scope (never opens the schedules). This doctrine gives the read a frame so it
behaves like a senior estimator on a first pass: *orient from the index, read the definitions, then work
the scope-bearing sheets in priority order.*

> **The cardinal rule — read, don't assume (it overrides every table below).** Sheet-numbering, legend
> conventions, and tag grammars **vary by firm and even by sheet**. The conventions here are a *prior*,
> not a rulebook — the regex that counted 55 units where an agent reading the tiles found ~109 is the
> standing cautionary tale (`drawing-comprehension-layer-design.md`). **This set's own cover sheet,
> drawing index, legends, and schedules are the ground truth for this set** — always prefer what the set
> says about itself over any general convention below.

---

## 1 · A set has three layers — find them before you read scope

| Layer | What it is | Why it matters first |
|---|---|---|
| **The map** | Cover/title sheet + **drawing index** (the set's table of contents) | Tells you what disciplines exist, how many sheets, the issue/revision state, and where to find each thing. **Read this first — it is cheap and orients everything.** |
| **The definitions** | General/legend/code sheets + **schedules** (door, window, finish, partition, equipment, fixture) | These *define* what placed tags mean (`C-1` → a door-schedule row; `P2` → a partition legend). Resolve the definition **before/alongside** the plan that places the tag — the scavenger hunt done once. |
| **The placements** | Plans, RCPs, elevations, sections, details | Where the scope actually lives — the symbols, runs, and assemblies that get priced and built. Read these *through* the definitions, not cold. |

The single biggest first-pass error is reading **placements before the map and definitions**. Don't.

---

## 2 · Disciplines — the prefix convention (a prior, confirm against the index)

Sheet numbers usually lead with a discipline designator (National CAD Standard lineage). Common ones:

| Prefix | Discipline | Typical scope payload |
|---|---|---|
| **G** | General | Cover, **drawing index**, code/life-safety, symbols & abbreviations legends, mounting heights — *the map + definition layer* |
| **C** (V/B) | Civil (Survey/Geotech) | Site, grading, drainage, site utilities |
| **L** | Landscape | Planting, hardscape, irrigation |
| **S** | Structural | Foundations, framing plans, structural schedules + details |
| **A** | Architectural | Floor plans, RCPs, elevations, sections, **schedules**, partition types, details — *usually the densest scope* |
| **I** / **ID** | Interiors | Finishes, furniture, casework, signage |
| **F** / **FP** | Fire protection | Sprinkler / standpipe |
| **P** | Plumbing | DWV, domestic water, fixtures, gas |
| **M** | Mechanical | HVAC, ductwork, equipment schedules |
| **E** | Electrical | Power, lighting, panel schedules, one-lines |
| **T** | Telecom / low-voltage | Data, comms |
| **FA / FS** | Fire alarm / suppression | Detection, suppression (sometimes folded under E/F) |
| **Z** | Contractor / shop | Shop drawings (not design intent) |

**Do not hardcode this.** A set may merge or split disciplines, use a firm-specific scheme, or carry
prefixes not listed. The **drawing index is authoritative for this set** — let it correct the table.

---

## 3 · Sheet types within a discipline — and their scope weight

| Sheet type | Scope weight | Read note |
|---|---|---|
| **Drawing index / cover** | Map (not scope) | Read first; it inventories everything else. |
| **Legends / general notes / code plans** | Definitions (not scope) | Read early; they resolve tags and carry ratings/occupancy. |
| **Plans** (floor, RCP, roof, enlarged) | **High** — primary scope | The workhorses. Enlarged plans carry the fine grain. |
| **Schedules** (door/window/finish/partition/equip/fixture) | **High + dense** | The most scope per sheet *and* the legibility wall — **tile finely** and read **column-wise by type, not row-by-row** (`read-grain.md`). |
| **Elevations / sections / wall sections** | Medium | Facade scope + assemblies; pair with the assembly schedules. |
| **Details** | Low-per-sheet, governing | Read only the **constructible conditions referenced by callouts** — don't narrate every detail. |

---

## 4 · The read sequence (priority order for a scope pass)

1. **Map** — cover + drawing index. Establish disciplines, sheet count, issue/revision state. *(Orient.)*
2. **Definitions** — general/legend/code sheets, then the **schedules**. Resolve tag grammars and types so
   placements read cleanly and links resolve once.
3. **Scope-bearing plans** — per discipline, at the chosen `grainLevel`. Breadth first: one read across all
   plans at grain **before** deep-diving any one sheet.
4. **Elevations + sections** — facade and assembly scope.
5. **Details** — only the governing conditions the callouts point to.
6. **Specs** — carry ≈half the scope lines, but are **not yet ingested by the harness** (named in
   `scope-run` §"What is NOT codified yet"). Until they are, flag spec-dependent scope as a known gap, not
   a silent omission.

Two principles under the sequence:
- **Breadth before depth** — a complete first pass at the chosen grain beats an exhaustive read of sheet 1.
- **Definition before placement** — read the schedule/legend that defines a tag before the plan that
  places it, so the link resolves once instead of on every later question.

---

## 5 · This is selection + sequencing, not a content engine

This doctrine tells the read **what a set is and how to move through it**. It does **not** tell it *what
the drawings specifically say* — that is the per-sheet agent read (grounded, judged) governed by
`read-grain.md`, and, when symbol-level explanation is pulled, the **comprehension layer**
(`drawing-comprehension-layer-design.md` in the project vault — demand-pulled, reasoning-not-rules, its
own arc). Inside `scope-run`, this doc feeds **cluster selection** (which sheets, in what priority) and
gives each per-sheet reader the frame "what kind of sheet is this and where's its payload." The harness
still reads a **cluster** — a bounded subset by discipline/area/grain — not a whole 400-sheet set blind;
the cluster config is that scoping knob.
