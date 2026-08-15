# Plumlayer marketplace

Private plugin marketplace for the Plumlayer plugin. Plumlayer connects your Claude Code or
Codex agent to your Plumlayer project record, the cloud record of a construction project, and gives
it the precon workflow skills to work that record directly: upload and index drawing sets, build a
grounded scope list for the job, level sub bids, and place takeoffs, all from inside your agent
session.

## Setup: Claude Code

```
/plugin marketplace add Lutoshi-me/plumlayer-marketplace
/plugin install plumlayer@plumlayer
```

On first use of a Plumlayer tool, Claude opens your browser to authorize against your own
Plumlayer account (OAuth). After that, Claude can read and record entries on your own
projects, scoped to you; you never see anyone else's.

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

A hosted MCP connector to your Plumlayer project record
(`api-production-0a7b.up.railway.app/mcp`), auto-wired on install with no manual `claude mcp add`,
and ten skills that use it.

### Getting started

- **`setup`**: a one-time interview that captures your company profile and defaults, stored only
  on your machine, so every other skill is personalized without any confidential config living in
  the shared plugin.
- **`project-create`**: stands up a new project record, either by interviewing you or by reading
  documents you already have (an invitation to bid, a drawing index, a spec table of contents).

### Drawings

- **`drawing-upload`**: takes a drawing delivery in any packaging (a new set, a bulletin, an
  addendum, a permit set) and turns it into a searchable, indexed set of sheet records, no manual
  conforming and no local spreadsheet step.
- **`learn-project`**: a quick orientation pass over an uploaded set that reads the cover sheet,
  the drawing index, and the key plans, then records what it found so every other skill starts from
  a shared picture of the project instead of from scratch.

### Scope and bids

- **`scope-run`**: reads the drawing set and builds one complete, cited scope list for the whole
  job, checks it for gaps, then splits it into trade packages. Draws on a bundled reference set of
  44 trade packages (see below) so each split follows how that trade actually bids and scopes work
  in the market.
- **`bid-intake`**: reads a trade's sub proposals and turns them into bid responses against the
  matching trade package, so you can level bids side by side with the amounts, inclusions, and
  exclusions each sub actually quoted.

### Takeoff

- **`takeoff`**: turns a plain request like "count the doors on the level 2 plans" or "measure the
  retaining wall" into placed marks or measurements on the actual sheets, the same as if you had
  drawn them yourself.

### Records and exports

- **`project-record`**: the general-purpose skill for reading, searching, and adding to a project
  record directly: the sheet and set grid, flagged items, and scope and takeoff data.
- **`drawing-index-publish`**: publishes a Master Drawing Index Excel workbook straight off the
  current set, with a tab per delivery and links that jump to each sheet.
- **`drawing-set-assemble`**: assembles the current drawing set into fresh PDFs, one per
  discipline plus an optional combined PDF.

### Trade reference set

The plugin also ships `trade-packages/`, a set of 44 trade reference files plus a manifest, read by
`scope-run` when it splits the job's scope list into packages. Each entry covers how that trade
bids and scopes work in the market, distilled and scrubbed of any identifying project or company
data.

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
docs/                               # authoring contracts for this repo's shipped text
plugins/plumlayer/
  .claude-plugin/plugin.json        # Claude plugin manifest
  .codex-plugin/plugin.json         # Codex plugin manifest
  .mcp.json                         # the hosted MCP connector shared by both surfaces
  skills/
    setup/SKILL.md
    project-create/SKILL.md
    drawing-upload/SKILL.md
    learn-project/SKILL.md
    scope-run/SKILL.md
    bid-intake/SKILL.md
    takeoff/SKILL.md
    project-record/SKILL.md
    drawing-index-publish/SKILL.md + references/
    drawing-set-assemble/SKILL.md + references/
  trade-packages/                   # 44 trade reference files + MANIFEST.md, read by scope-run
```
