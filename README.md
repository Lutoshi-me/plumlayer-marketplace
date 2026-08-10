# Plumlayer marketplace

Private plugin marketplace for the **Plumlayer** plugin. The plugin started as a Claude Code
marketplace plugin and now has side-by-side Codex packaging infrastructure.

It connects an agent to your Plumlayer project record (cloud) and the precon workflow skills.

## Setup: Claude Code

```
/plugin marketplace add Lutoshi-me/plumlayer-marketplace
/plugin install plumlayer@plumlayer
```

On first use of a Plumlayer tool, Claude opens your browser to authorize against **your
Plumlayer account** (OAuth). After that, Claude can read and propose claims on your own
projects — scoped to you; you never see anyone else's.

> If you previously added the MCP manually (`claude mcp add plumlayer …`), remove it first
> with `claude mcp remove plumlayer` so the plugin's connector is the one in use.

## Setup: Codex

Codex uses the repo-local marketplace file at `.agents/plugins/marketplace.json` and the
Codex plugin manifest at `plugins/plumlayer/.codex-plugin/plugin.json`.

From a local checkout of this repo:

```powershell
codex plugin marketplace add .
codex plugin add plumlayer@plumlayer
```

If you are registering the marketplace from another working directory, pass the absolute path to
this repo instead:

```powershell
codex plugin marketplace add C:\path\to\plumlayer-marketplace
codex plugin add plumlayer@plumlayer
```

Verify the install:

```powershell
codex plugin list
codex mcp get plumlayer
```

Start a fresh Codex thread after install or update so Codex picks up newly installed skills and
MCP tool wiring. Running threads may keep the tool/skill set they started with.

Current Codex packaging note: `.codex-plugin/plugin.json` intentionally does not declare
`mcpServers`. The shared plugin-root `.mcp.json` remains in the Claude-compatible shape, and current
Codex installs/discovers it from the plugin root. Do not rewrite `.mcp.json` into a Codex-only shape
unless Claude compatibility is handled separately.

## What's in the plugin

- **MCP connector** to the hosted Plumlayer project record (`api-production-0a7b.up.railway.app/mcp`)
  — auto-wired on install; no manual `claude mcp add`.
- **`project-record` skill** — teaches Claude the project record verb surface (`set_grid`, `ambiguities`,
  `rfi_candidates`, `search`, `propose`, …) and the trust model: what an agent writes takes effect
  as its own cited reading, and a person's word outranks it.
- **`drawing-upload` skill** — register any drawing delivery into the cloud project record as recognized,
  cited sheet claims (including sheet-type classification).
- **`drawing-index-publish` skill** — legacy export projection that publishes a Master Drawing Index
  workbook from cloud claims.
- **`drawing-set-assemble` skill** — legacy export projection that assembles discipline PDFs from cloud
  claims.
- **`scope-run` skill** — guarded by PLU-323. It now refuses the retired route-first path and points
  agents to the PLU-274 scope-item-first rebuild: one grounded whole-job scope list first, then
  derived trade packages. It does not dispatch the old fan-out/reconcile harness by default.
- **`scope-decomposer` subagent** — legacy route-first asset retained for PLU-274 history/migration
  only; guarded against normal production scope dispatch.
- **`trade-specialist` subagent** — legacy route-first asset retained for PLU-274 history/migration
  only; guarded against normal production scope dispatch.

Drawing upload, project record, and export skills are active. The old route-first scope harness remains bundled
as historical material while PLU-274 rebuilds the current production scope engine.

## Updating

### Claude Code

Push changes here, then in Claude Code:

```
/plugin update plumlayer@plumlayer
```

### Codex

During local Codex iteration, validate the Codex manifest and reinstall from the local marketplace:

```powershell
python "$env:USERPROFILE\.codex\skills\.system\plugin-creator\scripts\validate_plugin.py" plugins\plumlayer
codex plugin add plumlayer@plumlayer
```

If Codex does not pick up a same-version local edit, add a Codex cachebuster to
`plugins/plumlayer/.codex-plugin/plugin.json`, reinstall, and start a fresh thread:

```powershell
python "$env:USERPROFILE\.codex\skills\.system\plugin-creator\scripts\update_plugin_cachebuster.py" plugins\plumlayer
codex plugin add plumlayer@plumlayer
```

## Structure

```
.claude-plugin/marketplace.json     # Claude marketplace manifest (lists the plugin)
.agents/plugins/marketplace.json    # Codex marketplace manifest (lists the plugin)
plugins/plumlayer/
  .claude-plugin/plugin.json        # Claude plugin manifest
  .codex-plugin/plugin.json         # Codex plugin manifest
  .mcp.json                         # the hosted MCP connector shared by both surfaces
  agents/
    scope-decomposer.md             # legacy route-first scope read guard
    trade-specialist.md             # legacy route-first fan-out guard
  skills/
    project-record/SKILL.md         # the starter project record skill
    drawing-upload/SKILL.md
    drawing-index-publish/SKILL.md + references/
    drawing-set-assemble/SKILL.md + references/
    scope-run/SKILL.md              # PLU-323 guard; refuses retired route-first scope-run
  scope-harness/                    # superseded route-first assets retained for history/migration
    tools/*.py                      # legacy deterministic grounding + glue + prepare_deposit.py
    ingestion/sheet_inventory.py    # vendored set-inventory tool
    trade-lenses.json               # legacy trade-lens data (7 interior lenses, v0.1)
    reference/  prompts/  clusters/cluster_TEMPLATE.json  requirements.txt
```
