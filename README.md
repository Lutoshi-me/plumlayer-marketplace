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

The drawing-index pipeline is now included; more precon harness skills are coming.

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
  skills/
    mosot/SKILL.md                  # the starter MOSOT skill
    drawing-index/SKILL.md + references/
    drawing-index-bulletin/SKILL.md + references/
    drawing-index-merge/SKILL.md + references/
    drawing-index-publish/SKILL.md + references/
    drawing-set-assemble/SKILL.md + references/
```
