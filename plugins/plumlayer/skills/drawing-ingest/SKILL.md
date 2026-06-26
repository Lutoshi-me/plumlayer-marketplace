---
name: drawing-ingest
description: >
  Ingest a construction drawing delivery in ANY packaging and turn it into cited, proposed sheet
  claims in the project's Plumlayer MOSOT — no manual conforming, no local CSV intermediate. Use
  whenever the user hands over a new drawing set, bulletin, addendum, ASI, permit/CD/conformed set,
  or any pile of drawing PDFs and wants it read, registered, indexed, or inventoried. Trigger on
  "we got a new set for <project>", "ingest this set", "register the drawings", "drawing index",
  "drawing list", "sheet schedule", "sheet inventory", "list every sheet", "what's in this drawing
  set", "index this bulletin", "franken set / current set", "/drawing-ingest". Drives a fixed, gated
  pipeline: find the drawing pages -> bulk deterministic grounding pass -> agent reads + judges the
  residue -> derive discipline + issue scope -> deposit proposed claims. The agent reads and judges;
  deterministic tooling grounds; nothing governs unverified. Supersedes the retired drawing-index /
  drawing-index-bulletin / drawing-index-merge skills (the export skills drawing-set-assemble /
  drawing-index-publish survive as on-demand projections off the cloud claims).
---

# Drawing Ingest — the foundation pass, agent-driven

Take whatever the architect actually sent — in whatever shape — and turn it into the one canonical,
grounded set of **proposed sheet claims** in the project's MOSOT. This is **Stage 0**: the first thing
that touches a delivery, before anything is split by discipline, routed, or deep-read.

Doctrine binds every stage: **agents read and judge; deterministic tooling grounds; nothing governs
unverified.** Every claim deposited is `proposed` (or `derived`) — trust enters only when a human
promotes it on plumlayer.com. You read the way a person reads a sheet; the deterministic tools are the
anti-hallucination anchor and the cheap bulk pass, **not** the inference engine.

> **You (the agent) ARE the reader.** Ingestion is agent-driven, not server-autonomous: you have the
> files (or a path), you drive the grounding tools, you judge the residue, you propose. There is no
> server doing the read for you. Ground every reported number in a command you just ran; print honest
> coverage at each stage (never hide a residue count behind a total).

Design lineage (in the main plumlayer repo, not shipped in this plugin): `agent-driven-ingestion.md`
(who runs the read and where) and `drawing-set-intake-design.md` (what a good read produces). Read
those if you need the why; this file is the how.

---

## What this is, and the boundary (read before you start)

`drawing-ingest` does exactly **one** thing: take a drawing delivery and register every drawing sheet
in it as cited, proposed claims in the project's MOSOT. The canonical form is **virtual** — claims +
provenance over the **untouched original** delivery; discipline organization, by-discipline / combined
PDFs, page labels, bookmarks, and a drawing-index CSV are all **projections / exports** of that form,
rendered on demand, never the foundation. So this skill:

- does **not** physically split the set into discipline folders, and never reads discipline from a
  **filename or folder** — discipline is inferred from each sheet's own number prefix;
- does **not** produce a CSV as its deliverable (the deliverable is claims in the MOSOT). The
  surviving export skills render artifacts *from* the cloud claims when a sub or the field wants a
  physical package: `drawing-set-assemble` (discipline PDFs / franken set) and `drawing-index-publish`
  (the Master Index workbook);
- does **not** scope, take off, or comprehend the sheets (that is `scope-run`, downstream);
- does **not** create the project (`project-create`) or **promote** anything (a human does, on
  plumlayer.com).

**Retired by this skill:** `drawing-index`, `drawing-index-bulletin`, `drawing-index-merge`. Those ran
*organize-then-read* (hand-split into discipline PDFs, then parse the architect's master list) — three
ways backwards: they commit a discipline guess to the filesystem before any read confirms it, they make
derived copies that drift on every re-issue, and they depend on a master list that failed on 3 of 4
characterized projects. This skill reads first; the master list is **corroboration only**, never the
bootstrap.

---

## Bundled assets vs. your working directory

- **Bundled, read-only (shipped in the plugin):** the grounding tools under the plugin's
  `scope-harness/` directory. Resolve that root once:
  ```bash
  PLUGIN="$CLAUDE_PLUGIN_ROOT/scope-harness"   # Claude Code sets CLAUDE_PLUGIN_ROOT to the install path
  ls "$PLUGIN/ingestion/sheet_inventory.py" "$PLUGIN/ingestion/derive_set_claims.py" \
     "$PLUGIN/tools/prepare_deposit.py"        # sanity-check it resolved
  ```
- **Your working directory:** the **delivery** (supplied by path — confidential, never copied into the
  repo or plugin) and all **output** (`./output/ingest/<job>/`). The plugin is never written to.
- The grounding tools need **Python 3 + PyMuPDF (`fitz`)**. No other dependency. **Do not add one** —
  vision reads are agent-native (you), OCR for scanned pages is deferred (PLU-186, see § Deferred).

## Preflight (do this first)

1. **Resolve `$PLUGIN`** and confirm the three tools are present.
2. **The delivery is confidential, supplied by path.** On a Windows host pass a **Windows-style path**
   (`C:/Users/...`), NOT an MSYS path (`/c/Users/...`), or PyMuPDF can't open it. Quote it (paths have
   spaces).
3. **Set the job + output dir** — `JOB=<job>`; everything lands in `./output/ingest/<job>/`. Keep it
   out of any tracked tree.
4. **Know the issue label** — the version scope (e.g. `2025-12-22 CD / IFC`). Ask the user, or read it
   off the cover sheet during the read. It is load-bearing for supersession (Stage 4).

---

## The format playbook — find the drawing pages first

A delivery comes in one of four packaging classes. **Recognize the class, then find the drawing
pages** — a drawing sheet is not a spec page, a geotech report, a furniture book, or an email.

| Class | What it looks like | How you read it |
|---|---|---|
| **Combined PDF** | the whole set in one file, often mixed in a folder with specs / schedules / geotech / emails | run the reader over the one drawing PDF; probe out any non-drawing PDFs in the folder |
| **By-discipline folder** | one PDF per discipline (`...Architectural.pdf`, `...Structural.pdf`) | run the reader per PDF; **do not** trust the filename for discipline — derive it per sheet |
| **Sequence splits** | arbitrary `Sequence 1 / Sequence 2` PDFs that ignore discipline | run the reader per sequence PDF; sheets carry their own discipline prefix |
| **Mixed bag** | drawings + specs + reports as separate PDFs / Office files, no naming convention | probe each PDF to find which are drawings; ingest only those |

**A drawing sheet vs. a non-drawing page** — judge by **text density + title-block grammar**, never by
filename:
- A **drawing sheet** has sparse text and a **sheet-number token in the bottom-right title block**
  (large font, in the corner) — e.g. `A-101`, `S-201`, `P-400`. The bulk reader (next stage) scores
  these high-confidence (`corner+font-dominant` / `corner+unique`).
- A **spec / geotech / narrative page** has dense flowing body text and **no corner title block**; its
  "numbers" are section codes (`23 05 00-4`) or page numbers, not corner sheet numbers. The reader
  scores these `no-grammar-token` or a low-confidence body token you reject.

**To pick the drawing PDF out of a mixed bag**, run the reader on a **sample page range** of each
candidate (the reader accepts `... sheet_inventory.py <start> <end>`) and look at the hit rate: a PDF
whose sampled pages mostly yield corner title-block sheet numbers is a drawing set; one that yields
dense text + `no-grammar-token` is specs/geotech. Filename hints may *orient* you, they never *decide*.

**Emit a packaging report up front** (honest, before the full read): the class, which file(s) are the
drawings and why (the probe evidence), page counts, and which files you are excluding (specs, geotech,
emails) and why. If the delivery has a dual-source quirk (a combined PDF **and** a full set of per-sheet
PDFs — it happens), say so and pick the authoritative source, don't read both.

---

## Stages (fixed, gated — run in order)

Output lands in `./output/ingest/<job>/`. Run the bulk + derive + deposit stages **per drawing PDF**;
for a by-discipline folder or sequence splits, give each PDF its own `SET_TAG` and merge the claim files
before deposit (or deposit each — same project).

### 1 · Bulk first pass *(deterministic — grounds ~98% in seconds)*

The reader pulls exact title-block text + coordinates + font size (PyMuPDF), **localizes** the sheet
number by perception (largest sheet-grammar token, in the learned title-block region), and emits one
grounded claim per page with a bbox citation + confidence + trust class. It is self-calibrating (learns
*this set's* title-block region) and validated across 11 firms' sets — **drive it, do not modify it.**
Editing it trips the grounding-pipeline-change re-validation gate.

```bash
# Drives via its env contract (verified var names): INGEST_PDF / INGEST_SET_TAG / INGEST_REVISION /
# INGEST_OUT_DIR. No default PDF exists — it errors without INGEST_PDF (a silent default is a footgun).
INGEST_PDF="$PDF" INGEST_SET_TAG=<SETID> INGEST_REVISION="<issue label>" \
  INGEST_OUT_DIR=./output/ingest/<job> \
  python "$PLUGIN/ingestion/sheet_inventory.py"
```

*Produces* `./output/ingest/<job>/sheet_inventory_claims.jsonl` — one `appearsOnPage` + one `hasTitle`
claim per grounded sheet, each in the MOSOT Claim shape (`subject: "sheet:<NO>"`, `evidence` with a
page-points bbox, `trustClass` + `confidence`). It also prints a per-page table and a summary: pages
scanned, sheet# extracted, **high-conf (>=0.88)**, **flagged for review**, by-discipline, duplicate
sheet numbers, and an index-page reconciliation (declared vs found).

*Gate:* read the summary and **report the real counts** — never assume "542 pages = 542 sheets read."
The flagged set and the `no-grammar-token` pages are the residue the next stage owns.

### 2 · Residue read *(you read + judge — the bounded LLM cost)*

The reader hands up the clean ~98%; the judgment calls are yours. Two residue classes:

- **Low-confidence pages** (`font-dominant-off-corner`, `ambiguous-largest-font`, `unique-but-off-corner`)
  — the reader found a candidate but isn't sure. Is `DTT-2Z` a sheet number or a Simpson hold-down tag?
  Which of two duplicate picks is the real title-block number? What discipline is this orphan?
- **`no-grammar-token` pages** — the reader found no sheet-grammar token at all (an unusual title block,
  a divider, or a genuinely non-drawing page that slipped into the set).

For each residue page, **render the page (and its bottom-right title block) and read it**, then cite a
grounded bbox so you cannot invent:

```bash
python - <<'PY'
import fitz
doc = fitz.open(r"<PDF>")                       # Windows-style path
pg = doc[<PAGE>]
out = r"./output/ingest/<job>"
pg.get_pixmap(dpi=200).save(out + r"/residue_p<PAGE>.png")          # full sheet
r = pg.rect                                                          # rotation-aware rect
clip = fitz.Rect(r.x0 + 0.62*r.width, r.y0 + 0.55*r.height, r.x1, r.y1)
pg.get_pixmap(dpi=300, clip=clip).save(out + r"/residue_p<PAGE>_tb.png")  # title-block crop
PY
```

Read the PNG (use the Read tool), judge the sheet number + title + discipline, and **append a
Claim-shaped row** to `./output/ingest/<job>/residue_claims.jsonl` in the **same schema the reader
emits** — `method: "agent-vision-crop"`, `trustClass: "proposed"`, and `evidence` citing the
title-block bbox in page points you read it from. Subject keying: `sheet:<canon sheetno>` (uppercase,
prefix-dash-number; e.g. `sheet:A-101`). A residue claim row:

```json
{"subject": "sheet:S-501", "predicate": "appearsOnPage", "value": 412,
 "evidence": [{"source": "<SETID>/412", "locator": {"frame": "page-points-rendered",
   "bboxPts": [2890.1, 2080.4, 2986.2, 2132.1]}, "method": "agent-vision-crop",
   "snippet": "S-501"}], "trustClass": "proposed", "confidence": 0.85, "status": "current",
 "assertedBy": "agent-vision-crop", "promotedBy": null}
```

- When you **override a bad reader pick** (it chose a tag, not the sheet number), append your corrected
  claim and **note the superseded page** so review sees both — both deposit `proposed`; the human picks.
  Nothing governs unverified.
- **Image-only / scanned pages** (no text layer, the render is a flat raster): **flag honestly** as
  unread (`{"subject": null, "predicate": "imageOnlyPage", "value": <page>, ...}` or just report the
  page list) — do **not** add an OCR dependency. The OCR tier is deferred (PLU-186). An honest "I could
  not ground these N scanned pages" beats a silent drop or a guess.

*Gate:* every residue page is **judged-or-flagged**, never silently dropped. State how many you read,
how many you corrected, and how many you flagged image-only.

### 3 · Merge reader + residue

Concatenate the bulk claims and your residue reads into one inventory:

```bash
cat ./output/ingest/<job>/sheet_inventory_claims.jsonl \
    ./output/ingest/<job>/residue_claims.jsonl \
    > ./output/ingest/<job>/inventory.jsonl   # omit residue_claims.jsonl if there was none
```

### 4 · Derive the canonical form *(deterministic — discipline + issue scope)*

The reader emits `appearsOnPage` + `hasTitle`. The canonical intake form needs two more per sheet:
**`discipline`** (derived deterministically from the number prefix, cited as `derived`) and
**`partOfIssue {label}`** (the version scope, load-bearing for supersession). This is added **at the
deposit layer**, never by editing the frozen reader:

```bash
python "$PLUGIN/ingestion/derive_set_claims.py" \
  --claims ./output/ingest/<job>/inventory.jsonl \
  --issue-label "<issue label>" \
  --out ./output/ingest/<job>/set_claims.jsonl
# --issue-source defaults to "user-supplied"; pass a cover-sheet citation source if you READ the label.
```

It passes the inventory claims through **verbatim** and appends, per distinct `sheet:<NO>` subject:
- a `discipline` claim — value from the prefix (`A` -> Architectural, `S` -> Structural, …), cited back
  to the **same grounded sheet-number bbox**, `method: "derived-from-prefix"`, `trustClass: "derived"`.
  An **unknown / non-NCS prefix** (a `D-`, `B-`, `U-` orphan series) is emitted `proposed` +
  `disciplineUncertain` — read the title block and judge it in Stage 2 rather than letting the fallback
  govern.
- a `partOfIssue` claim — value `{"label": "<issue label>"}`, so a later re-issue supersedes per sheet.

*Gate:* the printed discipline distribution is **per distinct subject** (not per page); the `[warn]`
line names how many unknown-prefix sheets need an agent discipline read.

### 5 · Deposit into the MOSOT *(the claims land in the cloud, via `propose_batch`)*

This is what makes ingestion a **projection over the project's MOSOT** rather than a terminal file.

1. **Pick the project.** Call `list_projects` and confirm with the user which MOSOT to deposit into (a
   project = one MOSOT). Get its `projectId`. If there is no project yet, that's `project-create` first.
2. **Transform the claims.** `prepare_deposit.py` is a **generic claim -> propose-arg transport** — it
   carries every well-formed claim row unchanged (no change needed for discipline / partOfIssue rows;
   they are claims like any other). It writes the full `deposit.json` plus a `deposit_batches/`
   directory of pretty-printed batch files (≤50 claims each) and a `deposit_manifest.json` with exact
   per-batch counts.
   ```bash
   python "$PLUGIN/tools/prepare_deposit.py" \
     --claims ./output/ingest/<job>/set_claims.jsonl \
     --out ./output/ingest/<job>/deposit.json
   # → also writes ./output/ingest/<job>/deposit_batches/{deposit_batch_NNN.json, deposit_manifest.json}
   ```
   It prints the total claim count + predicate composition. **Confirm the magnitude with the user**
   before firing (a full set runs ~4 claims per sheet: appearsOnPage + hasTitle + discipline +
   partOfIssue).
3. **Deposit — faithful transport, never authorship.** Read `deposit_manifest.json` (small) for the
   batch list + expected counts, then for **each batch file** in order:
   - **Read the ENTIRE batch file.** It is small and pretty-printed precisely so it reads in full.
   - Call **`propose_batch`** with `projectId=<the project>` and `claims=` the file's array **emitted
     verbatim** — every entry exactly as written. Each file is ≤50 entries, within the 500 limit.
     `propose_batch` is **atomic** — a bad entry rejects the whole batch and names the index.
   - **Verify** the returned inserted `count` equals this batch's `count` in the manifest.
   - **HARD GATE — stop, never invent.** If you cannot read the whole file, or the returned count ≠ the
     manifest count, **STOP IMMEDIATELY** and report which batch and the discrepancy. **Never**
     reconstruct, summarize, infer, complete, or regenerate an entry from memory or from the drawings —
     a claim you did not read verbatim from the batch file is a **fabrication** and a doctrine
     violation. A truncated read is a hard error, not a cue to fill in the rest.
   - Track count-verified batches so a stop is **resumable from the next unsent batch**.
   - **Fallback** (older server without `propose_batch`): deposit the same batch files with per-entry
     `propose` calls — still read verbatim, still count-verified against the manifest, same hard gate.
   Every claim lands `proposed` (or `derived`) — it never governs until a human promotes it on
   plumlayer.com.
4. **Report the deposit.** State the project; **total claims deposited (sum of count-verified batches)
   vs. the manifest `totalClaims`** — they must match; if not, name the batch that stopped and why.
   Then the residue you read vs. flagged image-only, and that the claims are visible on plumlayer.com
   for review/promotion + in this session via `search` / `set_grid` / `ambiguities`.

---

## Gates (non-negotiable)

- Every sheet claim carries an **evidence link** (page + title-block bbox, or — for a residue read —
  the crop you cited). **No citation → not in the inventory, and not deposited.**
- Discipline is **derived from the sheet's own number prefix**, cited as `derived` — never from a
  filename or folder, never silently governed when the prefix is unknown.
- The residue is **judged-or-flagged**, never silently dropped; image-only pages are **named honestly**,
  not guessed (OCR is deferred, not improvised).
- Everything deposited is `proposed` / `derived`. This skill never promotes — a human does.
- **Deposit is verbatim transport, count-verified.** A read truncation or count mismatch **stops** the
  deposit — never reconstruct or invent a claim to "finish" a batch.
- **Honest coverage.** If a stage bounded its coverage (pages skipped, a PDF sampled not fully read,
  scanned pages unread), **say so** — silent truncation reads as "covered everything."
- Data hygiene: the delivery + `output/` stay in the user's cwd and out of git; **no client specifics
  in any tracked / committed file**.

## Cost knob (cheapest tier first)

The bulk deterministic pass (Stage 1) and the derive + transport (Stages 4–5) are **free** — they
ground ~98% of sheets in seconds. Your token cost is **fenced to the residue** (Stage 2): the ~2% of
pages the reader couldn't ground, read once each. That is the cost posture by design — zero server-side
reading cost; a bounded agent read on the small tail. **No GPU / model hosting.**

## Deferred (named honestly — not skipped silently)

- **OCR tier for image-only / scanned pages (PLU-186).** When a page has no text layer, the bulk reader
  and your render both come up empty; today you **flag** those pages. The cheap-OCR tier (RapidOCR
  feeding the same region+grammar scoring) that closes them is its own issue — do not add the
  dependency here.
- **Scale auto-detect at intake.** Detecting + presetting `hasScale` (proposed, human-confirmed per P5)
  is part of the canonical form but not built into this skill yet.
- **Master-list reconciliation as corroboration.** The reader prints a light declared-vs-found cut; a
  full diff against a parseable architect drawing list (to surface RFI-worthy discrepancies) is a
  corroboration layer, not the bootstrap.
- **Design + qa gates: N/A.** This skill has no UI surface — its verification is real-runs-with-real-
  counts, not a design or browser pass. Named, not silently skipped.
