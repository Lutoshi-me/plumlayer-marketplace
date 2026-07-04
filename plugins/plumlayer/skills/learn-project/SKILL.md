---
name: learn-project
description: >
  Stage 1 of the scope engine — a cheap orientation pass over an already-ingested drawing set. Reads
  the project's seed claims, sheet inventory, and spec-section index (if present), takes a handful of
  bounded renders (cover sheet, drawing index, up to four key plans), then deposits proposed, cited
  project-level claims (structural/envelope systems, MEP delivery shape, scope areas, phasing, set-shape
  observations, missing scope families, hazards) and compiles a run-context packet from them so every
  downstream reader orients once instead of from scratch. Trigger on "learn the project", "orient on
  this set", "orientation pass", "run the orientation pass", "what's this project about", "give me the
  project context", "/learn-project". Everything emitted is proposed — a human reviews and promotes on
  plumlayer.com. Does not ingest drawings (that's `drawing-ingest`) or run the scope/derive stages
  (guarded by PLU-323 until PLU-274 ships).
---

# Learn Project — the cheap orientation pass (stage 1)

The first stage of the scope engine (`scope-package-architecture.md` §4). Before anything is read
deep, one cheap pass over what's already grounded builds the project's **context**: what it is, its
structural and envelope systems, its scope areas, the shape of the set, and what's missing. Every
downstream reader (stage 3's content-keyed specialists) gets this context instead of orienting from
scratch, which is where tokens leak and reads get unreliable.

Doctrine binds every step: **agents read and judge; deterministic tooling grounds; nothing governs
unverified.** This is an *orientation* pass, not comprehension — it reads what ingestion already
grounded, takes a handful of bounded renders, and stops. Everything it emits lands **`proposed`**; a
human reviews and promotes it on plumlayer.com. Examples in this file are generic — never put a real
project name, client data, or a real extracted value here.

Governing spec: `scope-package-architecture.md` §4.3 (the emit-shape decision this skill implements) and
§4 (the six-stage pipeline this is stage 1 of).

## What this is, and the boundary

`learn-project` does exactly one thing: read an already-ingested set, deposit **net-new** project-level
orientation claims, and compile a packet from them. So it does **not**: ingest a drawing delivery
(precondition, owned by `drawing-ingest`); extract spec sections itself (it reads the spec-section index
if `drawing-ingest`'s later spec-ingestion work has already deposited one — it never extracts specs);
run definitions-first extract, content-keyed decompose, the one scope list, package derivation, or
tag+project (stages 2–6, guarded by PLU-323 until PLU-274 ships); or promote anything (a human does, on
plumlayer.com).

The run-context packet this skill compiles is a **projection**, never stored as truth — the same
pattern as a trade package. It lives in the run's working context only (the private tree), never the
repo, never the MOSOT.

## 0 · Preconditions

1. **Project exists.** Call `list_projects` and confirm with the user which MOSOT this orientation pass
   is for — get its `projectId`. If there is no project yet, hand off to `project-create` first, the
   same way `drawing-ingest` step 1 does.
2. **The baseline set is grounded.** Orientation reads the base set shape — it does not need revisions
   or bulletins to have landed, and spec-TOC presence is optional/best-effort, **not** a precondition.
   What it does need is a delivery that has actually been through `ground_sheets`. There is normally no
   retained `jobId` to poll at orientation time (that job ran, and finished, in an earlier session), so
   confirm groundedness by its observable effect rather than by re-polling a job you don't hold: call
   `list_drawing_deliveries(projectId)` — if none exist, stop plainly and hand off to `drawing-ingest`.
   If a delivery exists, spot-check with a small `search(projectId, predicate: "appearsOnPage", limit:
   1)` — zero rows means grounding hasn't actually deposited anything yet; stop and hand off to
   `drawing-ingest` rather than orienting on an empty set.

## 1 · Read the claims (identity, seeds, sheet inventory)

1. `get_project(projectId)` — the project's identity (name, description, created date).
2. **Read the project-create seed claims verbatim — never re-mint them.** For each of `projectType`,
   `deliveryMethod`, `location`, `grossArea`, `floorCount`, `bidDueDate`, `tradeInScope`,
   `knownExclusion`, call `search(projectId, predicate: "<predicate>")` and read what's there. These
   feed the packet's Identity section directly; where a seed is thin or missing, orientation may add a
   document-grounded claim on the same predicate later (competing claims on one slot resolve at review —
   no bespoke merge here).
3. **Sheet inventory.** Call `list_drawing_deliveries(projectId)` for the registered deliveries, then
   attempt `set_grid(projectId)` once. A set_grid payload on a set of real size can be large enough to
   file-redirect instead of returning inline — if that happens, fall back to sampled
   `search(projectId, predicate: "discipline")` calls for the disciplines you need (A, S, M, P, E, C, G)
   rather than pulling the full grid. Either path gives you discipline, sheet number, and governing
   issue per sheet, plus the file/page reference each row carries — the render targets for step 3 come
   from here, not from a separate `list_files` call.

## 2 · Read the spec-section index, if present

Call `search(projectId, predicate: "inDivision")` for `specSection:<csi>` subjects. When spec ingestion
has run for a project, these claims are real and cited — `hasTitle`, `locatedAt`, `inDivision`, and
`partOfIssue` on each section (verified on at least one live project). What's missing today is only the
packaged extraction skill for it, so **many projects won't have these claims yet** — that is a gap in
what's been run, not the expected steady state.

- **If present:** read the division spread and section count into the packet's set-shape section.
- **If absent:** write "spec ingestion hasn't run for this project" in the packet's set-shape section
  and continue. Never write "expected empty today," never treat absence as the norm, and never let this
  block the rest of the pass.

## 3 · Bounded renders (budget: ≤6 total)

Use the file/page references already surfaced by step 1's sheet inventory to pick `fileId` /
`pageInPdf` targets — don't call `list_files` separately for this. For every render, pair `render_page`
with `get_page_text` on the same page (render for layout and meaning, text for exact tokens).

1. **Cover sheet (1 render).** Find it via `search(projectId, predicate: "hasTitle", text: "cover")` or
   `text: "title sheet"`. If neither turns up a match, fall back to the lowest G-series sheet number in
   the inventory; if there's no G series either, fall back to the lowest sheet number in the set overall.
   Whenever you use a fallback, record a `setShapeObservation` claim naming the substitution (e.g. "no
   hasTitle match for a cover/title sheet; used the lowest G-series sheet instead").
2. **Drawing-index page (1 render).** Find it via `search(projectId, predicate: "hasTitle", text:
   "index")`, `"drawing list"`, or `"sheet list"`. If none of these match, **skip the render** and note
   the absence in the report — never synthesize an index page that isn't there.
3. **Key plans (up to 4 renders).** For each series in this order — **A**, then **S**, then **M/P/E**
   (one representative render for whichever of M, P, E exists first, in that order — it counts as one
   slot, not three), then **C** — render the lowest-numbered sheet you judge, from its title and
   position in the inventory, to actually be a plan (not a detail, schedule, or elevation) in that
   series, and only if the series exists in the inventory at all. A series that is genuinely absent from
   the inventory renders nothing for that slot and instead becomes a `missingScopeFamily` candidate in
   step 4 — don't force a render to fill the slot.

If the set is large enough that six renders plainly can't cover it (many buildings, many phases, an
unusually deep set), say so explicitly in the report rather than quietly rendering more.

## 4 · Emit orientation claims

All net-new, subject `project` unless noted, deposited via **one** `propose_batch(projectId, claims)`
call:

| Predicate | Value shape | Ambiguity rule |
|---|---|---|
| `structuralSystem` | free text, one claim per system (e.g. "post-tensioned concrete flat plate") | flag if inferred rather than labeled on the drawings |
| `envelopeSystem` | free text, one claim per system (e.g. "unitized curtain wall") | flag if inferred |
| `mepDeliveryShape` | `{division, shape}`, `shape` ∈ `full-design` \| `design-build-thin`, one claim per MEP division present | **always flagged** — this is a judgment claim by §4.3 |
| `scopeArea` | free text, one claim per area (e.g. "below-grade parking", "amenity terrace") | flag if the boundary was inferred rather than labeled |
| `phasingNote` | free text (e.g. "occupied renovation, phased by wing") | flag if inferred |
| `setShapeObservation` | free text (e.g. "schedules live on the A-10 series") | usually unflagged — a direct observation |
| `missingScopeFamily` | free text (e.g. "no Division 31 Earthwork/SOE sections in the TOC") | **always flagged** — an absence claim is defeasible |
| `hazardFlag` | free text (e.g. "occupied renovation — coordinate around active tenants") | flag when inferred from context rather than stated outright |

**`sourceInstrument` is per-claim, not one batch label** (the PLU-350 correction). For a claim grounded
in a specific page or render, cite the specific source file/instrument name — the same convention
`drawing-ingest` and `project-create`'s ingest mode use. Reserve the label `learn-project-orientation`
only for derived or absence observations with no single source page: `missingScopeFamily` and any
set-level `setShapeObservation`. Every claim's `evidence` cites the exact page/render or claims-query
that produced it — never a fabricated locator.

Call `propose_batch` once with the full array. **Verify:** the returned `count` must equal the number of
entries sent; a mismatch stops the run and gets reported, never a guessed correction.

## 5 · Compile the run-context packet

A projection compiled fresh from the claims read in step 1 and deposited in step 4 — **never itself
proposed, never stored as truth.** Sections, in order:

1. **Identity** — name, type, delivery method, location, size, key dates (from the seed claims).
2. **Systems** — structural and envelope systems, MEP delivery shape per division.
3. **Scope areas** — the `scopeArea` and `phasingNote` claims.
4. **Set shape** — disciplines present, issue labels seen, `setShapeObservation` claims,
   `missingScopeFamily` claims, and the spec-TOC status (division spread + count, or the "hasn't run
   yet" note from step 2).
5. **Hazards** — the `hazardFlag` claims.
6. `[PLACEHOLDER — definitions-as-context envelope, PLU-351]` — a clearly marked final section; this
   skill does not design that envelope, it only reserves the slot.

Write it to `$MOSOT_DATA_PATH/<project-slug>/run-context/learn-project-packet.md` in the private tree —
derive `<project-slug>` from the project name (lowercase, spaces to hyphens) or fall back to the
`projectId` if the name doesn't produce a clean slug. Never write it into the repo, and never deposit it
as a claim. Regenerate it in full the next time this skill runs for the project — it is a projection,
not a document to patch.

## 6 · Report

Tell the user, in plain terms (mirrors `project-create` step 5):
- **What was read** — identity, which seed predicates had claims, the sheet-inventory scope (disciplines
  covered, set_grid vs. sampled search), and the spec-TOC status.
- **What was learned**, per checklist category — systems, MEP delivery shape, scope areas, set shape,
  hazards.
- **Claim counts** — how many deposited, and how many were ambiguity-flagged.
- **Where the packet landed** — the full path.
- **The placeholder note** — the definitions-as-context section is a stub pending PLU-351.
- **Everything is `proposed`** — pending review and promotion on plumlayer.com.

## Gates (non-negotiable)

- **Cite everything.** No citation → don't emit the claim.
- **Net-new facts only.** Never re-mint a seed claim `project-create` already deposited, or a sheet /
  spec-section claim `drawing-ingest` already deposited.
- **Judgment claims are cited and flagged.** `mepDeliveryShape` is always flagged; the rest are flagged
  whenever the value was inferred rather than read off a label.
- **This skill never promotes.** Everything lands `proposed`.
- **Orientation, not comprehension.** Respect the ≤6 render budget — if the set is too large for it to
  cover meaningfully, say so in the report rather than silently exceeding it.
- **The packet is a projection only.** Never deposited as a claim, never written to the repo, always
  regenerated in full on the next run rather than patched.

## Cost (cheapest tier first)

The bulk of this pass is `search` over claims `project-create` and `drawing-ingest` already deposited —
already-paid-for reads, effectively free. Token cost is fenced to the ≤6 renders and their paired
`get_page_text` calls, plus the small, fixed cost of compiling the packet from a small claim set. No GPU
or model hosting on this path.

## Deferred (named, not skipped silently)

- **The definitions-as-context envelope (PLU-351).** The packet's final section is a placeholder only;
  how orientation and definitions-first context share one envelope's token budget is PLU-351's design
  question, not this skill's.
- **Spec-section extraction as a packaged skill (PLU-223's tail).** Step 2 reads spec-section claims if
  they already exist; it does not extract them. Until that extraction skill ships, most projects will hit
  the "hasn't run yet" branch.
