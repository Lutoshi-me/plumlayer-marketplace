---
name: scope-run
description: >
  Run the Plumlayer scope harness over a construction drawing set: point it at a drawing PDF and get
  cited per-trade scope checklists + a cross-trade gap log + a completeness ledger, then deposit the
  scope as proposed claims into your Plumlayer MOSOT. Trigger on "run the scope harness on <set>",
  "scope this set / drawing PDF", "generate scope for <project>", or "/scope-run". Drives
  ground -> decompose -> fan-out -> reconcile -> coverage-audit -> project -> deposit as a fixed,
  gated, inspectable pipeline. The per-job delta is a cluster config — never code.
---

# Scope Run — the codified, controlled scope workflow

Turn a drawing set into **cited, per-trade scope** and land it in the project's MOSOT. Doctrine binds
every stage: **agents read and judge; deterministic tooling grounds; nothing governs unverified.**
Every artifact is a cited **draft of proposed claims** — *the drawings govern; the checklist assists.*
Trust enters only when a human promotes a claim on plumlayer.com.

**The one rule that keeps this scalable + legible:** the per-job delta is **data** — a cluster config
(`clusters/cluster_<job>.json`) naming the set, sheets, lenses, and `grainLevel`. Tools, prompts,
subagents, and lens knowledge are bundled in the plugin and generalized once. **A new job never edits
code.**

> **You (the orchestrating agent) ARE the conductor.** You dispatch the agent reads and run the
> deterministic glue between them; each agent writes a file and returns one line (that discipline is
> what lets one context drive ~15 agents). Ground every reported number in a command you just ran;
> print honest coverage at each stage (never hide a zero behind a total).

---

## Where this sits, what it is, and what you need ready (read this before you start)

**Where it sits in the workflow.** `scope-run` is the **takeoff step**, and it runs **after the set is
assembled and the project exists** — it does not stand up either:

`setup` (operator profile, once) → `project-create` (the MOSOT shell) → **assemble & index the set**
(`drawing-ingest` — register the set, deposit sheet claims, produce the cloud index) → **`scope-run`
(this skill — turn the set into cited per-trade scope claims)** → **review & promote on plumlayer.com**.

**What this skill is — and the boundary (so it isn't "here's whatever, go figure it out").** `scope-run`
does exactly **one** thing: take an **assembled, identified drawing set** (or a bounded **cluster** of it)
and turn it into **cited, per-trade scope claims** in the project's MOSOT, via the fixed gated pipeline
below. The open-ended judgment is **bounded** — it is per-sheet reads at a chosen grain, governed by
`reference/read-grain.md` (*what is one scope item*) and `reference/drawing-set-literacy.md` (*what am I
looking at and where's the scope*). It is **not** a do-everything skill. It does **not**:
- **assemble or merge** the set across issues/disciplines — that's `drawing-ingest`, done first;
- **comprehend every symbol** on every sheet — that's the demand-pulled comprehension layer, its own arc;
- **create the project** (`project-create`) or **promote** anything (a human does, on plumlayer.com).

And it reads a **cluster — a bounded subset by discipline / area / grain — not a whole 400-sheet set
blind.** The cluster config (`grainLevel` + `lenses` + `titleKeywords`) is that scoping knob; if you find
yourself about to scope an entire large set in one run, scope a cluster instead.

**What must be ready before you start (the readiness gate — check these first):**
1. **One assembled drawing set as a PDF, supplied by path** — the current/governing issue (or a defined
   cluster of it). If you only have loose per-discipline PDFs or several un-merged issues, that's a
   `drawing-ingest` / set-assembly job **first**, not a scope-run.
2. **A sense of the set's shape** — ideally a **drawing index** (run `drawing-ingest` if you don't have
   one). The Ground stage builds a sheet inventory regardless, but knowing the disciplines + issue state
   up front is what lets you select a sane cluster. See `reference/drawing-set-literacy.md` for *how* to
   read and sequence a set (the map → definitions → placements order).
3. **A grain + lens decision in the cluster config** — `grainLevel` (`bid` vs `ca`) and the trade
   `lenses`/`titleKeywords` for this cluster (`./clusters/cluster_<job>.json`, from the template).
4. **A target MOSOT to deposit into** — `project-create` already run (you'll pick/confirm the `projectId`
   at deposit, Stage 7).

If any of these isn't ready, **say which and resolve it first** rather than running the pipeline on an
unready input — that is the failure this gate exists to catch.

---

## Bundled assets vs. your working directory (read first)

- **Bundled, read-only (shipped in the plugin):** the tools, the vendored ingestion script, the trade
  lenses, the reference doctrine, and the cluster template — all under the plugin's
  `scope-harness/` directory. Resolve that root once:
  ```bash
  PLUGIN="$CLAUDE_PLUGIN_ROOT/scope-harness"   # Claude Code sets CLAUDE_PLUGIN_ROOT to the install path
  # Fallback if the env var is not set in your shell: find the install dir via /plugin
  #   (…/plugins/cache/plumlayer/plumlayer/<version>) and set PLUGIN=<that>/scope-harness
  ls "$PLUGIN/tools" "$PLUGIN/ingestion" "$PLUGIN/trade-lenses.json"   # sanity-check it resolved
  ```
- **Your working directory (the user's cwd):** the **drawing PDF** (supplied by path), the per-job
  **cluster config** (`./clusters/cluster_<job>.json`, copied from `$PLUGIN/clusters/cluster_TEMPLATE.json`),
  and all **output** (`./output/scope/<job>/`). The plugin is never written to.
- The **subagents** `scope-decomposer` and `trade-specialist` ship with the plugin and are dispatched
  by `subagent_type`. If a dispatch errors "agent type not found", fall back to `general-purpose`
  agents told to *read and follow* the bundled `agents/<name>.md`.

---

## Preflight (do this first — it catches the known offenders)

1. **Resolve `$PLUGIN`** (above) and confirm the tools are present.
2. **The drawing PDF is the one runtime input.** It is confidential and supplied by path — never copied
   into the repo or plugin. On a Windows host pass a **Windows-style path** (`C:/Users/...`), NOT an
   MSYS path (`/c/Users/...`), or PyMuPDF can't open it. Quote it (paths have spaces):
   ```bash
   PDF="C:/Users/.../<set>/<drawings>.pdf"
   ```
3. **Resolve the job config.** `JOB=<job>`; read `./clusters/cluster_<job>.json` for `setId`, `outDir`,
   `grainLevel`, `trades`/`lenses`, `titleKeywords`, `packet` opts, `v0Subset`. Create it from
   `$PLUGIN/clusters/cluster_TEMPLATE.json` for a new job.
4. **Stale-inventory guard.** The Ground stage writes a sheet inventory; if a stale one from a
   different set is reused, the whole run is wrong. Build the inventory fresh for THIS set (step 1a),
   or pass an `--inventory-jsonl` you built for this set and sanity-check it (expected sheet numbers
   present).

---

## Stages (fixed, gated — run in order)

Substitute your job's config values for `<job>` / `<SETID>`. Output lands in `./output/scope/<job>/`.

**1 · Ground** *(deterministic)* — inventory the set, select the cluster's sheets, render the tiled packet.
Selection is where set-literacy applies: use the inventory as your **map**, and `titleKeywords` to pull
the cluster's scope-bearing sheets + their definition sheets (legends/schedules), per
`$PLUGIN/reference/drawing-set-literacy.md` (§1 map→definitions→placements, §3 scope weight).
```bash
# 1a. Sheet inventory → the JOB folder in your cwd (INGEST_OUT_DIR keeps it out of the
#     read-only plugin). No default PDF exists — it errors without INGEST_PDF.
INGEST_PDF="$PDF" INGEST_SET_TAG=<SETID> INGEST_OUT_DIR=./output/scope/<job> \
  python "$PLUGIN/ingestion/sheet_inventory.py"
# 1b. Select the cluster's sheets (keyword match; empty titleKeywords = whole set).
#     Pass the inventory you just built explicitly — never let it fall back to a cached one.
python "$PLUGIN/tools/select_cluster.py" --pdf "$PDF" --set-id <SETID> \
  --cluster-config ./clusters/cluster_<job>.json \
  --inventory-jsonl ./output/scope/<job>/sheet_inventory_claims.jsonl \
  --out ./output/scope/<job>/selected_sheets.json
# 1c. Render + tile ONLY the cluster's sheets. Tiling is REQUIRED for schedule sheets
#     (a full 42" sheet through one image read downsamples to illegible mush).
#     --motifs adds deterministic congruent-symbol counts alongside tiles and anchors.
python "$PLUGIN/tools/build_reading_packet.py" --pdf "$PDF" \
  --selected ./output/scope/<job>/selected_sheets.json \
  --out-dir ./output/scope/<job>/packet/ --tiles --tile-dpi 200 --target-tile-px 2800 \
  --motifs
```
*Gate:* citations key on **pageNum + sheetId-from-page**; extracted sheetNo/title are best-effort
labels. Produces `packet/packet_manifest.json` + `tiles_manifest.json` + `packet/tiles/<sheetId>/` +
**`packet/anchors/<sheetId>.jsonl`** — deterministic per-sheet text tokens (`{i,text,bboxNorm}`, in the
tile coordinate frame): the decomposer's ground truth for the *words* on the sheet. A genuinely no-text
(scanned) sheet warns honestly (`hasTextAnchors:false`) rather than emitting empty anchors.
Also produces **`packet/motifs/<sheetId>.json`** — deterministic congruent-geometry motifs with grounded
counts (`{motifId, count, symbolLikely, innerTextSamples, instances[bboxNorm], exemplar.bboxNorm}`, in the
same 0–1 tile frame): the decomposer's grounded count reference for repeated symbols. A scanned or
zero-motif sheet sets `hasMotifs:false` and WARNs honestly — no motif file is written. The manifest
records `hasMotifs`/`motifPath`/`motifCount`/`symbolLikelyCount` per sheet.

**2 · Decompose** *(agent read → deterministic merge)* — trade-agnostic scope, one reader per sheet.
- For **each scope-bearing sheet** in `packet_manifest.json`, dispatch a **`scope-decomposer`**
  (`subagent_type: scope-decomposer`). Tell it: the sheet's `sheetId/sheetNo/title/pageNum`, the
  **`grainLevel`** from the config (e.g. `bid`), the tiles dir `packet/tiles/<sheetId>/`, the
  **text-anchor file `packet/anchors/<sheetId>.jsonl`** (deterministic text — it reads the *words* from
  the anchors and the *layout/meaning* from the tiles, instead of re-deriving text from pixels), the
  **motif file `packet/motifs/<sheetId>.json`** when `hasMotifs` is true (deterministic grounded counts
  for repeated symbols — the decomposer cites the motif `count`+`motifId` for repeated-symbol quantities
  instead of eyeballing from pixels; words from anchors, layout+meaning from tiles, COUNTS from motifs),
  the write path `decompose/raw_<sheetId>.json`, and to consult `$PLUGIN/reference/drawing-set-literacy.md`
  §3 for the sheet-type → scope-payload frame (a schedule reads column-wise and dense; a details sheet
  yields only governing conditions). **Issue all per-sheet dispatches in ONE message → parallel.**
```bash
python "$PLUGIN/tools/merge_decompose.py" --raw-dir ./output/scope/<job>/decompose/ \
  --packet-manifest ./output/scope/<job>/packet/packet_manifest.json \
  --set-id <SETID> --out ./output/scope/<job>/decompose_read.json
```
*Gate:* every item carries a citation; a scope-bearing sheet must return items; a genuine
empty/placeholder sheet is **flagged honestly** (`sheetIsScopeBearing:false`), not silently dropped.
Grain is governed by `$PLUGIN/reference/read-grain.md`.

**3 · Fan out → reconcile** *(agent reads → deterministic overlap)* — the routing moat.
```bash
python "$PLUGIN/tools/build_fanout.py" --decompose ./output/scope/<job>/decompose_read.json \
  --packet-manifest ./output/scope/<job>/packet/packet_manifest.json \
  --lenses "$PLUGIN/trade-lenses.json" --out-dir ./output/scope/<job>/fanout/
```
- For **each lens**, dispatch a **`trade-specialist`** (`subagent_type: trade-specialist`) pointed at
  its `fanout/input_<lens>.json`, writing `trade_claims/raw_<lens>.json`. **One message, all lenses
  parallel.** Each lens reads independently — do **not** let them coordinate.
```bash
python "$PLUGIN/tools/ingest_fanout.py" --raw-dir ./output/scope/<job>/trade_claims/ \
  --decompose ./output/scope/<job>/decompose_read.json \
  --packet-manifest ./output/scope/<job>/packet/packet_manifest.json --set-id <SETID>
python "$PLUGIN/tools/reconcile_overlap.py" --decompose ./output/scope/<job>/decompose_read.json \
  --trade-claims ./output/scope/<job>/trade_claims/ \
  --packet-manifest ./output/scope/<job>/packet/packet_manifest.json --set-id <SETID> \
  --out ./output/scope/<job>/scope_claims.jsonl \
  --summary ./output/scope/<job>/reconcile_summary.json
```
*Gate:* routing is **measured from overlap, never a generalist's guess**; `excludes` respected; every
net-new grounded; routing vs is-it-real kept separate.

**4 · Coverage audit** *(deterministic — the completeness gate)*.
```bash
python "$PLUGIN/tools/coverage_audit.py" --decompose ./output/scope/<job>/decompose_read.json \
  --trade-claims ./output/scope/<job>/trade_claims/ \
  --packet-manifest ./output/scope/<job>/packet/packet_manifest.json --set-id <SETID> \
  --raw-decompose ./output/scope/<job>/decompose/ \
  --out ./output/scope/<job>/coverage_ledger.json \
  --md ./output/scope/<job>/coverage_ledger.md
```
*Gate:* every sheet/item is accounted-for-or-flagged. **Red** = a sheet referenced by 0 trades, or
unread (not an agent-confirmed placeholder). **Amber** = unowned concentration. Completeness ≠ grain:
unowned items are expected output, not a failure.

**5 · Project** *(deterministic)* —
```bash
python "$PLUGIN/tools/project_scope.py" --claims ./output/scope/<job>/scope_claims.jsonl \
  --out-dir ./output/scope/<job>/
```
→ per-trade `scope_checklist_<trade>.md` (clear items) + `cross_trade_gap_log.md` (contested + unowned,
each carrying all claimants' citations). Every doc leads with the proposed-not-governing header. Target
shape: `$PLUGIN/reference/scope-checklist-format.md`.

**6 · Report (artifacts)** — honest counts from `reconcile_summary.json` + `coverage_ledger.json`:
decomposed items; clear/contested/unowned; net-new; grounding drops; coverage red/amber flags. Name
where the artifacts are, and that they are a **cited draft**, not governing truth. If any stage bounded
coverage (sheets skipped, a lens failed, retries), say so.

**7 · Deposit into MOSOT** *(the claims land in the cloud, via the `propose` verb)* — this is what makes
scope a **projection over the project's MOSOT** rather than a terminal file.
1. **Pick the project.** Call `list_projects` and confirm with the user which MOSOT to deposit into (a
   project = one MOSOT). Get its `projectId`. If the cluster config carries a `projectId`, confirm it.
2. **Transform the claims.** This writes the full `deposit.json` (for inspection) **and** a
   `deposit_batches/` directory of small, pretty-printed batch files (≤50 claims each) plus a
   `deposit_manifest.json` listing every batch file and its exact claim count. **The batch files are what
   you deposit; the manifest is your fidelity check.** (Drops null-value rows; flags contested/unowned
   with `ambiguityClass`; sets `sourceInstrument` from each citation.)
   ```bash
   python "$PLUGIN/tools/prepare_deposit.py" \
     --claims ./output/scope/<job>/scope_claims.jsonl \
     --out ./output/scope/<job>/deposit.json
   # → also writes ./output/scope/<job>/deposit_batches/{deposit_batch_NNN.json, deposit_manifest.json}
   ```
   It prints the total claim count + composition. **Confirm the magnitude with the user before firing**
   (a cluster runs ~6–8 claims per scope item; run on a **cluster subset**, not a whole 400-sheet set).
3. **Deposit — faithful transport, never authorship.** You are moving deterministic, already-grounded
   claims from disk into the MOSOT. **You are a transport, not an author.** Read `deposit_manifest.json`
   (small) for the batch list + expected counts, then for **each batch file** in order:
   - **Read the ENTIRE batch file.** It is small and pretty-printed precisely so it reads in full.
   - Call **`propose_batch`** with `projectId=<the project>` and `claims=` the file's array **emitted
     verbatim** — every entry exactly as written (`subject`/`predicate`/`value`/`sourceInstrument`, plus
     `evidence`/`ambiguityClass`/`versionScope` when present). Each file is ≤50 entries, well within the
     500-per-call limit. `propose_batch` is **atomic** — a bad entry rejects the whole batch and names
     the index.
   - **Verify** the returned inserted `count` equals this batch's `count` in the manifest.
   - **HARD GATE — stop, never invent.** If you cannot read the whole file, or the returned count ≠ the
     manifest count, **STOP IMMEDIATELY** and report which batch and the discrepancy. **Never**
     reconstruct, summarize, infer, complete, or regenerate an entry from memory or from the drawings — a
     claim you did not read verbatim from the batch file is a **fabrication** and a doctrine violation
     (*never invent a fact*). A truncated read is a hard error, not a cue to fill in the rest.
   - Track which batches are count-verified so a stop is **resumable from the next unsent batch**.
     Process batches one at a time or in small parallel waves. **Optional:** delegate one batch per
     subagent to keep context lean — each subagent honors this same gate on its one small file.
   - **Fallback** (older server without `propose_batch`): deposit the same batch files with per-entry
     `propose` calls — still read verbatim, still count-verified against the manifest, same hard gate.
   - If `deposit_manifest.json` reports `totalClaims: 0`, there is nothing to deposit — say so and stop.
   Every claim lands `proposed` — it never governs until a human promotes it on plumlayer.com.
4. **Report the deposit.** State the project; **total claims deposited (sum of count-verified batches)
   vs. the manifest `totalClaims`** — they must match; if not, name the batch that stopped and why. Then
   how many items were flagged ambiguous (the RFI pile), and that they're visible on plumlayer.com for
   review/promotion + in this session via `search` / `set_grid` / `ambiguities`.

## Gates (non-negotiable)

- Every scope line carries an evidence link (sheet + coords, or spec section). **No citation → not in
  the draft, and not deposited.**
- Routing is measured (overlap of independent reads), never asserted; ambiguous items surface in the
  gap log + as `ambiguityClass` on deposit — never silently assigned.
- Completeness is **audited, not assumed** (stage 4); nothing read or routed falls through silently.
- Everything deposited is `proposed`. The harness never promotes — a human does, on the review surface.
- **Deposit is verbatim transport, count-verified.** Claims are deposited exactly as
  `prepare_deposit.py` wrote them, each batch checked against `deposit_manifest.json`. A read truncation
  or count mismatch **stops** the deposit — never reconstruct or invent a claim to "finish" a batch.
- Data hygiene: the drawing PDF + `output/` stay in the user's cwd and out of git; **no client
  specifics in any tracked/committed file**; no confidential PDF path in a committed cluster config.

## Model / cost knob

The read stages (`scope-decomposer`, `trade-specialist`) are where quality is made and tokens spent —
N dispatches = (#scope-bearing sheets) + (#lenses). They inherit the session model by default (best
quality); drop to a cheaper tier per-dispatch when validating mechanics rather than accuracy. The
deterministic stages (ground/merge/fanout/ingest/reconcile/coverage/project/prepare-deposit) are free;
the deposit cost is the `propose_batch` calls — one per ≤50-claim batch file (the verb accepts up to
500, but small batches keep each read faithful and count-verifiable); one `propose` per claim only on
the older-server fallback.

## What is NOT codified yet (named honestly — the iteration surfaces)

- **Trade-knowledge depth** — `trade-lenses.json` is v0.1 and thin (7 interior lenses). The learning
  loop sharpens it from how humans resolve the gap log.
- **Specs as intake** — specs carry ≈half the scope lines; not yet ingested or routed per trade.
- **Comprehend** — auto-deriving the project overview + trade list (today the lens set + `grainLevel`
  are fixed in the config).
- **Reviewer layer + completeness critic** — adversarial per-trade review + cross-trade reconciliation
  after drafting.
