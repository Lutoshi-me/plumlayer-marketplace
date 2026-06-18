# Scope-checklist output format — the target shape

**Status:** v0.1 — **RECOMMENDED TARGET, format only** (2026-06-14: "an ideal *format* — we will
expand on details and other aspects"). Learned from a real GC procurement **bid-eval workbook** (one tab
per CSI trade). This captures the **structure**, not any one project's data. Pairs with
`$CLAUDE_PLUGIN_ROOT/scope-harness/reference/read-grain.md` (this is what that grain *renders into*).

> Confidentiality: the source workbook is a confidential client project. Only the generic estimating
> *format* is recorded here — no bidder names, prices, contacts, quantities, or job identifiers. Examples
> below are illustrative.

---

## The shape

**One workbook, one tab per CSI trade division** — `03-3000 Concrete`, `05-5000 Metal Fab`,
`06-2000 Finish Carpentry`, `08-1000 Doors/Frames/Hardware`, `09-2100 Drywall`, `21-0000 Fire
Protection`, `22-1000 Plumbing`, `26-0000 Electrical`, `31-0000 Site`, … Each tab is that trade's **scope
package** (and, post-bid, its **bid comparison**). This is the per-trade fan-out, made tangible.

## Per-tab anatomy

1. **Header block** — project info (job #, name, address) + a **bidder-comparison matrix**: each bidder a
   column with proposal date, contact, labor type (Union/Open-Shop), Base Bid, Adjustments, Total. *(This
   half is **post-bid procurement** — not what the read harness produces; see "Boundary" below.)*
2. **Scope table** — the part the harness produces. Columns:

   | Col | Meaning | Harness source |
   |---|---|---|
   | **#** | sequential line number | (assigned at render) |
   | **Ref** | **citation** — drawing sheet + detail (`A-810`, `4/A-811`) **and/or spec section** (`Spec 087100`) | `citations` / `isShownOn` |
   | **Scope** | the line item — **one _kind_ of work** | decompose item `title` |
   | **Notes / Qualifier** | governing detail + **quantities** ("≈210 frames, 117 doors"; "27,140 LF casing") | item `scopeText` + qty |
   | **Y/N/$** | **inclusion status** (see below) | routing + review |
   | *(per bidder)* Breakout Cost, Notes+Qtys | each sub's price + their qty read | *(post-bid)* |

3. **Two-level hierarchy** — **section headers** (work categories *within* the trade — e.g. for DFH:
   `COMMON AREA HOLLOW METAL`, `UNIT DOORS`, `DOOR HARDWARE`, `TRIM/MOULDING`) over their line items.

---

## The load-bearing conventions (these are the doctrine, not the spreadsheet)

- **Ref cites drawings AND specs.** Roughly half of real scope lines reference a spec section, not a
  sheet — the spec carries scope the drawings don't. **Specs are first-class evidence**, so they must be
  first-class intake (parked: in-loop spec ingestion).
- **Grain = kind of work; counts live in the qualifier.** "Exterior HM doors & frames" is **one line**
  carrying "≈210 frames / 117 doors," never 210 rows. At **bid/buyout grain a trade is a few dozen
  lines** — confirms `$CLAUDE_PLUGIN_ROOT/scope-harness/reference/read-grain.md`'s coarser-for-bid level
  against real practice.
- **`Y/N/$` makes every line a decision, and exclusions are explicit rows:**
  - **Y** — included.
  - **N** — **excluded** — written as its own row ("Common-area door casing — N — trim by others"), never
    a silent omission. This is the exclusions/qualifications library in action.
  - **?** — open question / unclear → **this is an RFI candidate** (ties to the in-loop issue/RFI log and
    to `unowned`/`contested` from reconcile).
  - **$ / Add** — priced add or alternate (spec deviation, VE option).
- **Cross-trade boundaries are carried inline** — "by others," "by Finish Carpentry," furnish-vs-install
  splits, and **"breakout if included in base bid"** (a double-count guard between adjacent trades). This
  is the cross-trade reconciliation layer, done by hand in the source — the harness should produce it.

---

## How the harness maps onto this today

| Bid-eval element | Harness artifact |
|---|---|
| one trade tab | one `scope_checklist_<trade>.md` (per-trade fan-out output) |
| Scope line | a decomposed/claimed scope item |
| Ref | the item's `citations` (sheet + bbox; spec section once spec-ingest exists) |
| Notes / Qty | `scopeText` (+ `appliesTo` once schema v0.3 lands) |
| `Y` line | a `clear`-routed item the trade owns |
| `N` / "by others" | `furnishedBy`/`installedBy` boundary + exclusions library |
| `?` line | `unowned` / `contested` → cross-trade gap log → RFI candidate |
| section headers | work-category grouping within a trade *(to add)* |

## Boundary — what is NOT the read harness's job

The **bidder-comparison matrix and cost breakouts are post-bid procurement** (comparing returned sub
proposals). The read harness produces the **scope-definition columns the bid-eval is built on**
(`# / Ref / Scope / Notes / Y-N`); the cost columns get filled when real bids come back. Keeping that
line clean is what lets the same scope package feed both the **bid solicitation** and the **bid eval**.
