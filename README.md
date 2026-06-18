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

The precon harness (scope-run + trade agents) ports onto this MCP next.

## Updating

Push changes here, then in Claude Code: `/plugin update plumlayer@plumlayer`.

## Structure

```
.claude-plugin/marketplace.json     # marketplace manifest (lists the plugin)
plugins/plumlayer/
  .claude-plugin/plugin.json        # plugin manifest
  .mcp.json                         # the hosted MCP connector (remote, OAuth)
  skills/mosot/SKILL.md             # the starter MOSOT skill
```
