# Read-grain doctrine — "what is one scope item?"

**Status:** v0.1 — **VALIDATED + LIVE** (2026-06-14). Confirmed against a real GC bid-eval
and green-lit; now executable in `scope-decomposer.md` Rule 1 +
`appliesTo` (schema v0.3) and **acceptance-tested** (see end). The first artifact of the `reference/`
corpus; cross-trade (governs every read, not one trade's knowledge).

**Why this exists.** The decompose read is non-deterministic in *grain*. On a real test run the same
prompt produced **302 items one run and 124 another**, driven almost entirely by a finish schedule
exploding to **226 items** one run vs ~29 another. The cause: the read had a surface-split
rule (`scope-decomposer.md` Rule 1) but **no rule for whether to group instances that share a kind of
work**. Where the rule runs out, the agent free-styles, and free-styling is where consistency dies. This
doctrine closes that gap. It pairs with the completeness axis (`coverage_audit.py`): grain and
completeness are different axes, but bad grain *pollutes* completeness (those 226 items put 53 of 60
unowned items on one sheet).

---

## Grain level is set at intake, not fixed (project stage × size)

The rule below is applied **at a grain level chosen for the project** — it is *not* one fixed default.
The same set read for a hard bid and for construction administration deserves different granularity, and
a 25-sheet project and a 400-sheet set deserve different granularity. **Both over- and under-granularity
are failures at every stage:** under-granular hides scope and routes coarsely; over-granular buries the
estimator, inflates the unowned pile, and pollutes the completeness signal. The level is **one knob**,
resolved at intake from (stage, size) and carried in the cluster config (`grainLevel`); the decompose
read is told its level and applies the litmus *relative to it*.

**Stage — what the scope is _for_:**

| Stage | Grain | Why |
|---|---|---|
| **Hard bid / pre-bid** | Coarser — **trade-package level.** One line per (type × area) an estimator would price and write an inclusion/exclusion against. | The deliverable is a priced, qualified bid + the RFI/gap list — not a room log. |
| **Awarded / CA / coordination** | Finer — **toward per-location.** Room/opening-level matters: submittals, installs, RFIs, coordination are tracked per location. | The deliverable manages the actual build. |

**Size — how big the set is:**

| Set size | Effect on grain |
|---|---|
| Small (≈ < 50 sheets) | Can afford finer grain; absolute counts stay manageable. |
| Large (≈ 400 sheets) | Hold the line coarser per item; lean harder on type-level grouping, or the list becomes unmanageable. |

A hard-bid 400-sheet set sits at the **coarsest**; an awarded 25-sheet fit-out at the **finest**. The
litmus — *"would an estimator carry this as one line?"* — is therefore **stage-relative**: a bidding
estimator carries "VCT-1 flooring, Level 2" as one line; a CA manager tracking installation may carry it
closer to per-area. Same rule, different level.

**Validated against real practice.** A real GC bid-eval workbook runs each trade at exactly this
bid-grain — a few **dozen** scope lines per trade, instance counts carried in the qualifier column
("≈210 frames / 117 doors"), organized under work-category section headers. The 226-row explosion is not
how estimators carry scope. See `$CLAUDE_PLUGIN_ROOT/scope-harness/reference/scope-checklist-format.md`.

---

## The rule (one sentence)

> **One scope item = one _kind of work_ (work type × its distinguishing attributes × a contiguous area)
> — carrying the list of locations/instances it applies to. Enumerate the distinct _kinds_ of work, not
> the _instances_.**

The litmus test, applied to every candidate item:

> **"Would an estimator carry this as one line and route it to one trade?"**
> If yes → one item. If it splits across trades → split it (by the attribute that splits the trade,
> usually *surface*). If it's the *same* line repeated at many locations → **one item with a location
> list**, never one item per location.

Instances (rooms, openings, locations, floors) are **data on the item** (`appliesTo`), not separate
items. Grouping this way **loses no information** — every room is still named, just under one line — so
completeness is preserved while grain becomes deterministic: the item count is bounded by the number of
**distinct work kinds**, which is stable run-to-run, not by how exhaustively the agent enumerated rows.

---

## Why this rule (the two forces it balances)

1. **Route-cleanliness (why we split at all).** In the fan-out→reconcile model, trades claim items by
   `itemId`; an item spanning several trades lands `contested` by construction. So we split an item along
   the attribute that changes *who owns it* — for finishes that is **surface** (floor→flooring,
   wall→paint/drywall, ceiling→paint/ACT/drywall, base→its trade). Splitting by surface pre-resolves
   routing instead of dumping a 4-way-contested blob on the gap log.
2. **Determinism + estimator-fit (why we group instances).** We do **not** split along attributes that
   *don't* change the work or the trade — the room number doesn't. An estimator prices "VCT-1 flooring,
   Level 2" as one line carrying a room list and a quantity, not 41 separate lines. Grouping by
   (material × surface × area) makes the count a function of the drawings' actual variety, not the
   agent's enumeration stamina.

The two forces meet at: **split by trade-changing attributes, group by non-trade-changing instances.**

---

## How it applies by item kind

| Item kind | One item = | Instances carried as | Count driver (stable) |
|---|---|---|---|
| **Finishes** (from a finish schedule or finish plan) | one **material × surface × area/level** | the rooms/spaces that share it | # distinct finish codes × surfaces × areas |
| **Assemblies** (wall/floor/ceiling/roof types: F2A, etc.) | one **assembly type** | the locations it occurs | # distinct typed assemblies |
| **Partition types** (P1, P2…) | one **partition type** | the walls/locations using it | # distinct partition types |
| **Doors / frames / hardware** | one **door type / hardware set** (by size·rating·material·hardware group) | the openings (door numbers) | # distinct door/hardware types |
| **Windows / storefront / glazing** | one **type mark** | the openings | # distinct type marks |
| **Specialties, fixtures, equipment** | one **type / model** | the locations/counts | # distinct types |
| **Details that govern construction** | one **constructible condition** the detail defines | where it's referenced | # distinct governing conditions |

General principle behind the table: **type-level, not instance-level.** A schedule or plan that lists
many instances of a few types yields *a few items with instance lists*, never one item per row.

---

## Schedules are tables, not callout piles (the specific fix)

A **finish schedule** lists every room × its surfaces — it is a structured table, and the explosion came
from reading it row-by-row. Read it **column-wise by finish code**, not row-by-row by room:

1. Identify the distinct finish codes per surface (e.g. floors: `VCT-1, PT-1, CPT-2`; walls: `PNT-W1,
   WC-1`; ceilings: `ACT-1, GYP-1`; base: `RB-1, WDB-2`).
2. Emit **one item per (code × surface × contiguous area)** — e.g. *"Wall finish PNT-W1 — Level 2"* — and
   list the rooms it covers in `appliesTo`.
3. If one code spans the whole project uniformly, that's **one item**; if it changes by level/zone, one
   per level/zone (area is a trade- and quantity-relevant attribute, so it earns a split).

**Expected effect on a large finish schedule:** many rooms × many surfaces → per-row explosion collapses
to roughly **(distinct floor codes + wall codes + ceiling codes + base codes) × areas ≈ a few dozen items**,
each carrying its room list. Same scope, stable count, unowned pile no longer inflated by per-room artifacts.

> **Boundary:** group only instances that are genuinely the *same line*. Different material code,
> different rating, different substrate, or different area = different item. When unsure whether two
> instances are the same line, **keep them separate and say why in the item** — over-grouping hides
> scope (worse than over-splitting). Grain serves the estimate; never merge to hit a target count.

---

## What this changed downstream

- **`scope-decomposer.md` + `$CLAUDE_PLUGIN_ROOT/scope-harness/prompts/decompose.md` Rule 1** rewritten
  from "one surface = one item" to this doctrine (split-by-surface **and** group-by-instance, schedule
  read column-wise, grain-level-aware).
- **Schema** gained optional `appliesTo` (list of room/opening/location labels) on a decompose item, so
  grouped instances are captured as data, not lost (`scope-decompose-v0.2` → `v0.3`); `merge_decompose.py`
  carries it through.
- **Cluster config** carries `grainLevel` (`bid` for hard-bid/precon).

### Acceptance test (PASS)

Re-decomposed the exploder sheet (a large finish/lighting/shade schedule) **twice**, same
bid-grain instructions, independent reads:

| | Items | Run-to-run spread |
|---|---|---|
| Before (per-surface-per-room) | **226** (one run) vs ~29 (another) | ~197 |
| After (this doctrine, bid grain) | **25** and **26** | **1** |

~9× collapse to the bid-eval's "few dozen" target, and the variance that opened this whole thread went
from ~197 to **1**. 20 of 25 items carried `appliesTo` (grouped rooms/codes); single-type items correctly
carried none; both runs converged on the same scope structure and survived the v0.3 merge. The grain
rule makes the read **consistent** — the thesis, proven on the exact sheet that broke it.
