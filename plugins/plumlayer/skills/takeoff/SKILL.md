---
name: takeoff
description: >
  Turn a plain-language takeoff request into a named condition with marks or measurements placed
  in the project record, like a person drawing them in the editor. Trigger on "take off the
  windows", "count the doors", "measure the wall", "/takeoff". Drives sheet discovery and the
  takeoff verbs (takeoff_read, takeoff_condition, takeoff_record, render_page, get_page_text).
  Does not upload drawings (drawing-upload), create the project (project-create), run scope
  stages (scope-run), or read sub proposals (bid-intake).
---

# Takeoff: count and measure from the sheets, land it as ordinary takeoff

Take the user's sentence (what to count or measure, and where) and come back with the same
artifact an intern at the next desk would produce: a named condition in the Measurements panel with
individual marks placed at true locations on the sheets, totaled, editable, and carrying the full
trail of who counted what from where. The user opens the takeoff editor and sees a takeoff,
not a data import.

Doctrine binds every stage: **you read and judge; deterministic tooling grounds; nothing enters
untraced.** The tag census, the coordinates, the rendered legend are the anti-hallucination anchors:
they ground what you place, but they never decide what counts. Deciding what counts (is this token a
window tag or a cladding callout?) is your reading of the sheet, recorded as your word with a
citation. There is no counting algorithm in this skill and none behind the verbs; a fixed rule
table would replace your reading with a guess that happens to be repeatable.

Your work lands as working truth immediately, carrying its trail. There is no waiting pile and no
review step to narrate: the user corrects anything they disagree with directly in the editor,
and anything a person touches or has said outranks your word on that spot from then on: the verbs
enforce this; you never need to police it, only to expect refusals near human-touched work and to
treat them as information, not errors.

## Confidentiality (non-negotiable)

Drawing sheets, tag conventions, counts, and project names are a client's confidential project
data. They live in the cloud project record (project isolation) and in the run's own evidence and report:
**never in this file, never in a committed plugin or repo file, never quoted into a durable note.**
The examples in this skill are generic; a real project's specifics never replace them. Reading the
sheets you were pointed at is the job; writing what they contain into tracked source is the leak.
(Oversized tool results can spill to harness-managed local files outside your control; that is
outside the repo and acceptable: the rule you own is what you write into tracked files.)

## What this is, and the boundary

One run of this skill produces **one condition** (or a small named set of them, when the request
genuinely spans kinds, a count plus a linear measure) with its marks, on the sheets the request
names. It does **not**:

- upload or register drawings (`drawing-upload`) or create the project (`project-create`);
- run scope identification or trade derivation (`scope-run`; a takeoff is quantities, not
  scope);
- delete, approve, or reorganize existing takeoff work: corrections to standing work belong to the
  user in the editor; you may add to it and may revise your own prior work, never remove
  another author's;
- derive quantities the sheets do not show (no "typical floor times 12" extrapolation unless the
  user asks for exactly that, and then it is named as arithmetic in the report, never placed as
  marks on sheets you did not read).

The pipeline: **preflight → what already stands → find the sheets → ground the scale → read and
judge → define the condition → place the marks → verify by reading back → report.** Each stage has
gates, collected at the end.

## 1. Preflight: resolve the sentence

1. **Account and project.** `whoami`, then `list_projects`; match the project the request names and
   confirm with the user only if the match is not obvious. Capture `projectId`.
2. **Parse the request into three facts** and hold them explicitly:
   - **The item**: what is being counted or measured ("windows", "hollow metal doors", "brick
     veneer"). This is the user's name for it; it becomes the condition name.
   - **The surface**: which sheets ("the elevations", "level 2 plans", "A-3.01"). A sheet family,
     a named list, or a discipline; resolved in stage 3.
   - **The kind**: count (each), linear (lf), or area (sf). Usually implied by the item; when the
     request is genuinely ambiguous ("take off the curtain wall": count of panels? sf of system?),
     ask before reading. One clarifying question up front is cheap; a wrong-kind takeoff is a redo.
3. **Do not ask what you can read.** Which tags mark the item, what the legend says, where the
   sheets are: that is your job in stages 3–5, not a questionnaire for the user.

## 2. What already stands (before anything else writes)

Call `takeoff_read(projectId)` and read the **whole summary, not only the conditions list**:
`summary.conditions` (every live condition, its type, unit, member count, total, sheets) **and**
`summary.byPredicate` (live counts per family). Overlapping standing work comes in two shapes, and
only one of them is a condition:

- **A condition matching this request**: same item, same kind, overlapping sheets; judge by name
  and members, not exact string match.
- **A legacy per-sheet count on a target sheet.** Older agent runs recorded whole-sheet count
  records (`hasTakeoffCount`, visible in `byPredicate`, returned flagged `legacy: true`). These
  render nowhere in the editor and can no longer be written (the write door refuses the family),
  but they are standing counted work all the same: a count of the same item on the same sheet
  **is** overlap even though no condition exists.

**Either shape → stop and put the choice to the user** before reading a single sheet.
<!-- user-facing -->
Name
what stands, say plainly whether it is visible in the editor or on record only, and offer the
honest options with their real costs:

- **extend**: count only sheets not yet covered and file the new marks under the existing
  condition (its id is in the stage 2 read);
- **place marks from what was already read**: when the standing record carries complete
  per-instance geometry (a legacy count's recorded instance boxes), marks can be placed under a
  new condition from that evidence without re-reading the sheets. Cheap and honest only if
  the earlier read's judgment calls and caveats travel with it, into the condition's notes, the
  records' evidence, and the report, never quietly dropped: the marks inherit that read, and
  the trail must say so;
- **count fresh**: a genuinely independent second read; slower, and the standing record remains
  on record beside it;
- **leave it**: report what stands and stop.
<!-- /user-facing -->

Be honest about removal: you cannot remove standing work, and a legacy per-sheet count is not in
the editor for the user to delete either. Whatever is added lands **alongside** it. Never
silently count the same thing onto the same sheets twice; never present a new condition as if it
replaced anything.

- **Nothing relevant stands** → proceed. Note any standing scale per target sheet (stage 4 uses
  this).
- That read is also your source for **conditionIds**: a prior run's condition you are
  extending is addressed by the id this read returns, never by a remembered one.

## 3. Find the sheets

Resolve "the elevations" to concrete sheets with file and page locations, from the project's own
records: never from filename guesses.

1. **Titles and types together, cheapest read first.** `search` matches a `text` substring across
   subject, predicate, and value: `search(projectId, predicate: "hasTitle", text: "ELEVATION")`
   style queries are the cheap opening move. Pair them with the type records
   (`search(projectId, predicate: "sheetType")`, but beware: on a large set that unfiltered pull
   can exceed the tool's output limit; filter or paginate deliberately). Use both, because each
   misses alone: a sheet titled "EXTERIOR ELEVATIONS" can be missing its type record, and a
   combo sheet ("PLANS, RCPS & ELEVATIONS") can be typed as something else. **Always pair
   subject with predicate in a `search`**: a bare subject query returns every record on the
   sheet, including enormous ones. And know the failure shape: a mistyped predicate returns
   `count: 0` silently, exactly like real absence: an empty result for a predicate you expected
   to exist means check your spelling before concluding the data is missing.
2. Resolve each candidate's **fileId and page** from its location records: predicates
   `locatedAt` (fileId, page, source PDF, delivery) and `appearsOnPage`, with a paired
   subject+predicate query per candidate. If the project's sheets carry no type records at all
   (an old or partial upload), fall back honestly: read the drawing index sheet or titles, and
   say in the report that you resolved sheets by title because the set is untyped.
3. **Settle the sheet list from titles first; render only the ones still open.** Titles usually separate an
   exterior elevation from an interior or structural one at zero render cost; render a candidate
   only when its title and type leave the call genuinely unclear, and to spot-check the list
   (one render on a sheet you will read anyway is free confirmation).
<!-- user-facing -->
State the final sheet list to
   the user before the heavy read, naming the sheets you will count on.
<!-- /user-facing -->
Interior elevations,
   enlarged partial elevations, and similar near-misses are a judgment call: include or exclude
   deliberately and say which in the report.
4. **Scope discipline.** The request's surface bounds the run. "The elevations" does not quietly
   become "and also the window schedule for cross-check" unless you name it as context reading:
   context reads are free; marks land only on the requested sheets.

## 4. Ground the scale (per sheet that needs one)

Counts do not need a scale; lengths and areas do, and a correct standing scale helps either way.
Per target sheet:

- **A scale already stands** (from the stage 2 read): use it. If it was set by a person, it is
  theirs: never replace it, even if you read the title block differently; note the disagreement
  in the report instead. If your own earlier run set it and it is wrong, revise it (the record
  names what it replaces).
- **No scale stands:** read the stated scale off the sheet (title block or the view labels), then
  **verify it against something the sheet itself dimensions**: level datums on an elevation
  (two labeled levels and their pixel distance), a dimension string on a plan, a graphic scale
  bar. The stated label is a starting point; the verification is what earns the record. Record
  `hasScale` with `method: "auto-detected"`, the display label as read, the derived
  units-per-point, and the two-point `calibration` geometry of the very feature you verified
  against. If the sheet states no scale and dimensions nothing you can calibrate on, record
  no-scale only if the request needs no scale; otherwise stop and tell the user that sheet
  cannot be measured yet.
- A scale disagreement you cannot resolve (label says one thing, the datums say another) is a
  judgment call: go with what the geometry proves, and put the discrepancy in the report.

## 5. Read and judge (the method, not the answers)

This is your reading. The discipline below is method (what a careful estimator does) and none of
it pre-decides what a tag means on this project's sheets. Every project's legend is its own law.

1. **Read the legend first.** Render the sheet (and the legend/notes region at detail zoom) and
   learn how *this* set marks the item: tag shapes, series letters, where tags sit relative to the
   thing they mark. If a legend sheet exists in the set, read it. Never import tag conventions
   from another project or from memory.
2. **Census with coordinates.** `get_page_text` gives every text span with its box in PDF points:
   the same coordinate frame the records use. Collect the candidate tokens and their positions.
   Expect a full-size sheet's census not to fit in your context (a thousand-plus spans is
   normal): the result spills to a local file, and the working pattern is to filter and tally it
   with a small script, not to read it. The census is your completeness backstop: it is how you
   know there are 47 candidate tokens, so a count of 41 means six were judged out, not missed.
   `hasTextLayer: false` means an image-only sheet: the census is unavailable, your count comes
   from the render alone at whatever zoom it takes, and the report says so.
3. **Judge every candidate against the sheet, not the token.** The same token can mark two
   different things (a window tag series and a cladding series sharing letters is a real,
   observed case, on the same sheet, in two different legends). Two rules make the census
   honest:
   - **A census hit is not identified until you have seen its marker.** The census gives the
     token and the coordinate; only a render shows what the token is wearing: the tag shape and
     placement that the legend keys meaning to. Look at least once per token family per sheet,
     and at every instance where families collide.
   - **The set's schedules are identity evidence, not just a total to compare against.** A
     window/door/finish schedule that carries a tag settles what that tag *is* far more firmly
     than the elevation alone: reading one to resolve a border case is a context read, always
     allowed. When two sheets of the same set mark the same physical thing differently, follow
     each sheet's own legend and report the inconsistency; it is the architect's, not yours to
     smooth over.
   Secondary signals you discover (glyph metrics, tag geometry) are evidence for *this* sheet's
   read: cite them, and never promote them into a rule for the next project.
4. **Every decision is one of three things:**
   - **counted**: it is the item; it gets a mark;
   - **excluded, named**: it is not the item (or is a border case judged out: the full-height
     glazed unit that is probably a door, the partial view that re-shows counted instances); it
     gets no mark, and the exclusion is recorded with its reason and location: in the record
     evidence where it shaped a count, and always in the report;
   - **blocked**: you genuinely cannot tell and the answer materially changes the takeoff: stop
     and ask the user, with the render in front of them. Rare by design; most border cases
     are calls you make and name.
   Nothing is silently dropped. The census count, the placed count, and the named exclusions must
   reconcile exactly; if they do not, find the gap before recording.
5. **Double-count discipline.** Partial views, match-line repeats, and keyed enlargements can
   re-show instances another view already shows. Decide per sheet-family how you are treating
   them, apply it consistently, and name the rule in the report. When the sheet itself cannot
   settle whether views repeat (no cross-reference markers), size the uncertainty: if the
   unclear instances could move the total by more than a few percent, stop and ask with the
   render in front of the user; below that, make the call, apply it consistently, and lead
   the report with it.

## 6. Define the condition

One `takeoff_condition` call per condition. The server creates the identity and returns it as the
landed record's `subject`: **that string is the conditionId every mark in stage 7 carries.** You
never invent one.

- `value`: `name` is the user's own words for the item, qualified by surface when it helps
  ("Windows: exterior elevations"); `type` is the kind from stage 1 (`count` / `linear` /
  `area`); `unit` to match (`ea`, `lf`, `sf`); `folder` / `color` / `notes` only when they carry
  real information (a note is a fine home for the run's counting rule).
- `evidence`: `method`: how you decided this condition belongs (the request plus what you read);
  `source`: the sheets and legend you read to define it.
- `sourceInstrument`: name what actually produced it (e.g. `takeoff-skill`). Never
  `takeoff-editor`: that name belongs to the human editor and the door refuses it.
- Extending a person's existing condition (they defined "Windows", you are filling it) is allowed
  and is the intended shape: reuse their conditionId from stage 2; do not create a duplicate. Only
  revise a condition definition (`supersedesId`) when it is your own and the revision is real
  (rename, note); type and unit are immutable: a different kind is a new condition.

## 7. Place the marks

One `takeoff_record` per instance: a count mark per counted tag, a length per run, an area per
region. Never a list of points in one call, never a rollup: the total the user sees is the
marks summed, so the marks are the takeoff.

- **Geometry is the census's own coordinates** (PDF points, the `get_page_text` frame): a count
  mark's `point` is the instance's location (center of its tag/box); vertices for lengths and
  areas trace what you measured. Scaled quantities cite the scale they were computed under
  (`scaledUnder`).
- **Every record carries `conditionId`** (from stage 6) and evidence: `method`: how this
  instance was read (census + visual confirmation, render-only on image sheets, and the judgment
  that included it when it was a border case); `source`: sheet and page. A mark you cannot cite
  to a location you actually read is not recorded.
- **Expect volume, and bookkeep for it.** One record per instance is the doctrine, and a normal
  elevation takeoff is hundreds of sequential calls with verbose responses. Before the first
  write, fix **one canonical ordered list** of every mark to place and track sent/remaining
  against it by index, programmatically, not by eye. Two differently-ordered copies of the same
  list is how a duplicate or a gap happens at this volume. Record sheet by sheet, keeping a
  per-sheet sent count against the canonical list.
- **Triage a failed call into one of three shapes:**
  - **refused near human-touched work**, the machinery protecting a person's word: skip it,
    count it, name it in the report;
  - **transport or auth error** (a timeout, an expired-token error; the call returned an error,
    not a landed record): retry that one write once; the stage-8 verification is what proves no
    duplicate resulted either way;
  - **a refusal you cannot explain**: stop the run rather than retrying blind.
- **Judgment calls ride the trail.** A border-case instance you counted carries the call in its
  own evidence; exclusions shaped by judgment are recorded with the census reconciliation. (A
  dedicated way to raise a Question on a record is coming to the verbs; until it exists, the trail and the
  report are where your unsureness lives, and it must live somewhere. Silent confidence you do
  not have is the one dishonesty this skill cannot absorb.)

## 8. Verify by reading back

Two reads, because they answer different questions:

1. **The condition:** `takeoff_read(projectId, conditionId: <the condition>)`: the same read the
   editor's panel is fed from. Its summary carries the condition's live member count and base
   total for the whole set. Two traps: the row list includes the condition's own definition row
   (so raw row totals run one higher than the member count), and paging with `nextCursor` can
   repeat a boundary row: if you walk rows across pages, dedupe by entry id before counting.
2. **Per-sheet counts, the cheap way:** the summary always describes the **whole filtered set**,
   so `takeoff_read(projectId, sheet: "sheet:<number>", predicate: "hasTakeoffCountMark",
   limit: 1)` returns a definitive count for that sheet in one tiny call: one per sheet
   beats walking hundreds of rows.
3. **The scales:** scale rows belong to sheets, not conditions, so the condition read does not
   return them. Per sheet you recorded a scale on:
   `takeoff_read(projectId, sheet: "sheet:<number>", predicate: "hasScale")`.

Check, with a fresh recount against your stage-7 canonical list (never an echoed number):

- member count per sheet equals what you sent per sheet;
- the condition's base total matches the arithmetic of its members;
- each scale you recorded is live on its sheet.

A mismatch stops the run and is reported as a discrepancy with both numbers: never patched by
re-sending, never rounded into "close enough". The verification result is the only ground for telling
the user the takeoff landed; a successful write call alone is not.

## 9. Report

<!-- user-facing -->
The report is the manifest:

- **What landed:** per sheet: marks placed, by tag/type breakdown where tags exist; the condition
  name and its total; which scale each measured sheet used and where it came from (already set /
  read off the sheet and checked against a dimensioned feature).
- **Judgment calls, led with, numbered:** every border case counted or excluded, each with its
  location and reason, so the user can check exactly those in the editor. This is the first
  thing after the totals, not a footnote.
- **The count check:** candidates found → counted → excluded (named) per sheet, and the
  verification result.
- **Anything left alone:** human-set scales you disagreed with, refusals near human work, sheets
  skipped and why.
- **Where to look:** the sheet in the takeoff editor on plumlayer.com: the condition is in the
  Measurements panel; every mark is clickable, movable, deletable; anything they change wins.

**If the run stopped at stage 2**, the report is a different, shorter shape, and it is a
successful run, not an apology: what stands (named, with whether it is visible in the editor or
on record only), why that blocks proceeding without a choice, the options from stage 2 with their
real costs, and the standing work's own judgment calls and caveats. The user inherits those
the moment they lean on the standing number, so they are part of the answer, not trivia.
<!-- /user-facing -->

## Gates (non-negotiable)

- `takeoff_read` runs before any write, and the overlap check covers **both** shapes of standing
  work: conditions and legacy per-sheet counts (`summary.byPredicate`, not only
  `summary.conditions`); either stops the run for the user's choice. Re-running never
  silently duplicates and never claims to have replaced work it cannot remove.
- The sheet list is stated to the user before any mark lands.
- The legend and the sheet decide what a token means: never a rule imported from another project,
  a prior run, or this file. Method travels; answers do not.
- Census, placed marks, and named exclusions reconcile exactly; nothing is silently dropped. On
  image-only sheets the render-based count says it is render-based.
- A scale is verified against the sheet's own dimensioned features before it is recorded;
  a person's scale is never replaced, only noted.
- Marks land only on sheets the request names; context sheets inform, they do not receive marks.
- Every write cites what was read (sheet, page, method) and carries its conditionId; no
  citation, no write.
- One record per instance; no rollups, no multi-point payloads.
- A refusal near human-touched work is skipped and named, never fought; a transport/auth error
  is retried once with the verification read as the duplicate-proof; an unexplained refusal stops the
  run.
- The landed result is verified by a fresh recount read before the user is told it
  landed: the condition read (paginated to completion) for marks, a separate sheet-scoped read
  for each scale; a mismatch is reported, never patched silently.
- Judgment calls are named in the trail and led with in the report: never silently resolved,
  never buried.
- Nothing this skill writes is a person's word, and nothing it does deletes, approves, or signs;
  corrections and removals belong to the user in the editor.

## Bundled vs. config

This skill generalizes once. The per-run delta (which project, which item, which sheets, which
kind) is data the user supplies in their sentence, never an edit to this file. A new takeoff
never edits `SKILL.md`; observed specifics of one project (its tag conventions, its legends) live
in that run's evidence and report, never here.

## Deferred / for proving runs to confirm (named, not skipped silently)

- **Redo semantics.** There is no agent-side removal, and legacy per-sheet counts are not in the
  editor for the user to remove either, so every redo shape lands alongside what stands. If
  real use makes redo common, a deliberate revision path for a whole condition's marks (and a
  retirement path for legacy records) is a verb-surface question, not something this skill
  improvises.
- **A way to raise a Question on writes.** A first-class way for a write to carry "check this one" (visible
  at the true location on the sheet) is designed but not yet in the verbs; the trail + report
  carry it meanwhile. Adopt it here when it ships.
- **Untyped sets.** Sheet discovery leans on `sheetType` records from drawing-upload; the
  title-based fallback for untyped sets should be confirmed against a real old project.
- **Cross-check reads.** Reading a schedule to sanity-check an elevation count (not to mark it) is
  allowed as context today; whether a count-vs-schedule discrepancy deserves its own structured
  finding in the report is open: for now it is prose in the report.
