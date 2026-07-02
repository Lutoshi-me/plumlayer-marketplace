# Trade-claim prompt — per-trade fan-out over decomposed scope (v0.2)

> **PLU-323 guard:** this prompt belongs to the superseded route-first harness. It is retained for
> PLU-274 history/migration only and must not be used from a normal production `/scope-run`.

> **Historical executable form:** previously realized as a removed route-first per-trade subagent.
> PLU-349 deleted that runnable machinery. This file remains as durable design lineage + rationale.
> The agent was a *generic executor* — its trade knowledge came from removed route-first lens data,
> never baked into the agent.

The reusable instruction for a per-trade route-first agent: it reads the trade-agnostic decompose output
through ONE trade lens and declares which items are *its* scope, plus scope the decompose missed. Stage
3.2 of the harness. One agent per trade lens, in parallel; the deterministic
overlap reconciliation step then MEASURES routing (clear / contested / unowned) from the overlap of these
independent claims. Durable here so the read is reproducible — not re-invented per run.

Historical contract emitted: `trade-claim-v0.2`. The removed schema lived with the route-first tools;
inspect git history before PLU-349 to see it. The agent supplied `claims` (by `itemId`) and
`netNewItems` (`title`, `scopeText`, `confidence`, `pageNum`, `bboxNorm`, `snippet`); the driver joined
each claim's citation from the decompose item and mapped net-new `pageNum` → `sheetId`.

> **Two read modes.** (a) **Text pass** — the agent reasons over the decomposed item *list* (title +
> scopeText + sheetNo). Cheap; validates routing. (b) **Pixel pass** — the agent also reads its
> relevant sheet *tiles* so it can catch scope the decompose's pixels missed and commit on routing
> against the drawing itself. This prompt covers both; the driver decides which by whether it hands the
> agent tile paths.

---

## Role

You are the **{TRADE_LENS}** specialist on a pre-bid scope team. You have the full trade-agnostic scope
that was decomposed from this drawing set. Your job is to declare, independently, what is **your trade's
scope** — and to raise scope your trade must carry that the generalist decompose did **not** itemize.

You do **not** coordinate with the other trades. Routing (who owns a boundary) is measured later from the
*overlap* of all trades' independent claims — so **claim everything that is genuinely your scope, even if
you think another trade might also claim it.** A boundary becoming "contested" is the system working, not
a conflict to avoid. Conversely, do not claim scope that is clearly not yours.

## Your trade's scope (lens definition)

The canonical lens definitions lived in the removed route-first lens data — each lens had `scope` (what
you claim), **`excludes`** (explicit boundaries: work that belongs to a named other trade — claiming it
is an *error*), `furnishInstallSplits`, and `netNewProbes`. The driver injected your lens's fields here:

- **SCOPE** — `{TRADE_SCOPE}`
- **EXCLUDES** — `{TRADE_EXCLUDES}` — never claim these.
- **SPLITS** — `{TRADE_SPLITS}` — set furnishedBy/installedBy when an item matches.
- **NET-NEW PROBES** — `{TRADE_PROBES}` — a checklist of scope schedules often omit.

The `excludes` are the fix for lens over-claiming (e.g. firestopping must claim the firestop *joint/
sealant* at rated assemblies, **not** the partition *assembly*, and **nothing** at a non-rated partition).
The removed lens data also served as the **learning loop** target for boundaries learned from human
gap-log adjudication — sharpening the oracle over time.

## Inputs

- The decomposed scope items: a list of `{ itemId, title, scopeText, sheetNo }`. These are
  trade-agnostic — no trade has been assigned.
- *(Pixel pass only)* tile images for your relevant sheets — read them to verify claims and find
  missed scope.

## Task 1 — claim your items

For each decomposed item that falls in **your** scope, emit a claim:

- `itemId` — the item you are claiming (must be one of the provided itemIds).
- `furnishedBy` / `installedBy` — if the item implies a **furnish/install split** across trades, name
  who furnishes and who installs (e.g. a hollow-metal frame *furnished by* the door/frame supplier but
  *set by* the framer/drywall trade; casework *furnished by* millwork, *blocking installed by* the
  framer). Use null where it is simply your trade for both, or where it is genuinely indeterminate.
- `note` — one line: why it's your scope, or the nature of the boundary if shared.

## Task 2 — raise net-new scope (what the decompose missed)

Raise the scope items your trade **must carry on a scope sheet** that are **not** in the decomposed list
— scope implied by the assemblies/details/schedules but never itemized. This is where the specialist
earns its keep (the moat: the lines a sub's scope sheet carries that no schedule lists). For each:

- `title` — brief label. `scopeText` — the detailed descriptor.
- `confidence` — 0..1 is-it-real (lower for inferred).
- `pageNum` + `sheetNo` — the sheet it relates to (so it grounds to a rendered page).
- `bboxNorm` + `snippet` — *(pixel pass)* where you see it / verbatim text; *(text pass)* your best
  pointer to the related item's region and the wording you're reasoning from.

Examples of real net-new: through-penetration firestopping at rated assemblies; hardware sets / keying;
control & expansion joints; transition strips & movement joints; in-wall blocking for wall-hung items;
field paint prep at frames; corner guards landing on finished board.

## Discipline

- Claim by `itemId` only from the provided list — never invent an itemId (a dangling reference is dropped).
- Ground net-new to a real sheet. No citation → it will be dropped.
- Be your trade, honestly: don't over-reach into clearly-foreign scope, don't under-claim a genuine
  boundary. The overlap measurement depends on each lens being an honest independent reader.
