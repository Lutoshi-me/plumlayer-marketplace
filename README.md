# Plumlayer marketplace

Private Claude Code marketplace for the **Plumlayer** plugin — connects Claude to your
Plumlayer MOSOT (cloud) and the precon harness.

## Install

```
/plugin marketplace add Lutoshi-me/plumlayer-marketplace
/plugin install plumlayer@plumlayer
```

On first use of a Plumlayer tool, Claude opens your browser to authorize against **your
Plumlayer account** (OAuth). After that, Claude can read and propose claims on your own
projects — scoped to you; you never see anyone else's.

> If you previously added the MCP manually (`claude mcp add plumlayer …`), remove it first
> with `claude mcp remove plumlayer` so the plugin's connector is the one in use.

## What's in the plugin

- **MCP connector** to the hosted Plumlayer MOSOT (`api-production-0a7b.up.railway.app/mcp`)
  — auto-wired on install; no manual `claude mcp add`.
- **`mosot` skill** — teaches Claude the MOSOT verb surface (`set_grid`, `ambiguities`,
  `rfi_candidates`, `search`, `propose`, …) and the propose-only / human-promotes doctrine.
- **`drawing-index` skill** — build the master Drawing Index CSV for a discipline-split issue (Conformed Set, Permit Set, etc.) from a folder of one PDF per discipline.
- **`drawing-index-bulletin` skill** — build a per-issue Drawing Index CSV for a Bulletin, ASI, or Addendum that ships as a single combined PDF; cross-checks against the Narrative of Changes.
- **`drawing-index-merge` skill** — merge per-issue Drawing Index CSVs into a Franken Set CSV showing where the latest version of every sheet lives.
- **`drawing-index-publish` skill** — publish a Master Drawing Index Excel workbook (.xlsx) with one tab per issue plus a Franken Set tab and page-level hyperlinks.
- **`drawing-set-assemble` skill** — assemble fresh discipline-split PDFs (and an optional combined PDF) from a Franken Set CSV, preserving annotations and synthesizing bookmarks.
- **`drawing-indexer` subagent** — pipeline operator that runs the full drawing-index chain (index → bulletin → merge → publish → assemble) as a delegated background task.
- **`scope-run` skill** — the codified scope harness: point it at a drawing PDF and it runs ground → decompose → fan-out → reconcile → coverage-audit → project, then **deposits the cited per-trade scope into your MOSOT as proposed claims** via the `propose` verb (a human promotes them on plumlayer.com). Drives the two scope subagents + bundled deterministic tools (`scope-harness/`).
- **`scope-decomposer` subagent** — reads ONE sheet (as legible tiles) and emits trade-agnostic, cited scope items; assigns no trades.
- **`trade-specialist` subagent** — reads the decompose through ONE trade lens and claims its items; a generic executor whose trade knowledge is all DATA (`scope-harness/trade-lenses.json`), routing measured later from claim overlap.

The drawing-index pipeline and the scope harness are now included; more precon harness skills are coming.

## Updating

Push changes here, then in Claude Code: `/plugin update plumlayer@plumlayer`.

## Structure

```
.claude-plugin/marketplace.json     # marketplace manifest (lists the plugin)
plugins/plumlayer/
  .claude-plugin/plugin.json        # plugin manifest
  .mcp.json                         # the hosted MCP connector (remote, OAuth)
  agents/
    drawing-indexer.md              # drawing-index pipeline subagent
    scope-decomposer.md             # per-sheet trade-agnostic scope read
    trade-specialist.md             # per-lens scope claim
  skills/
    mosot/SKILL.md                  # the starter MOSOT skill
    drawing-index/SKILL.md + references/
    drawing-index-bulletin/SKILL.md + references/
    drawing-index-merge/SKILL.md + references/
    drawing-index-publish/SKILL.md + references/
    drawing-set-assemble/SKILL.md + references/
    scope-run/SKILL.md              # the scope harness orchestrator (deposits to MOSOT)
  scope-harness/                    # bundled read-only assets for scope-run ($CLAUDE_PLUGIN_ROOT)
    tools/*.py                      # deterministic grounding + glue + prepare_deposit.py
    ingestion/sheet_inventory.py    # vendored set-inventory tool
    trade-lenses.json               # the trade-knowledge data (7 interior lenses, v0.1)
    reference/  prompts/  clusters/cluster_TEMPLATE.json  requirements.txt
```
