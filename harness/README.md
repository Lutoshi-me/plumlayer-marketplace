# Plumlayer Plugin Test Harness — Phase 1

Two-layer test harness for the Plumlayer Claude Code plugin
(`plugins/plumlayer/`). No model calls in Layer 1; one bounded headless call
in Layer 2.

## How to run

From the repo root:

```sh
python harness/run.py all       # Layers 1+2 (default)
python harness/run.py static    # Layer 1 only (no model calls)
python harness/run.py load      # Layer 2 only (one headless claude call)
```

Exits 0 if all selected layers pass; exits 1 on any failure. Print output
gives a per-check PASS/FAIL with detail.

## Dependencies

Standard library only (`json`, `subprocess`, `pathlib`, `re`). No pip install
needed.

```
harness/requirements.txt   # empty / annotated — for completeness
```

---

## Layer 1 — Static Checks (`static_checks.py`)

Fully deterministic. No model calls. Runs in < 5 seconds.

| # | Check | What it proves |
|---|-------|----------------|
| 1 | `claude plugin validate --strict` | CLI validator passes with warnings-as-errors |
| 2 | Version-triple lockstep | `plugin.json`, `marketplace.json[metadata.version]`, and `marketplace.json[plugins[0].version]` are identical |
| 3 | Skills frontmatter | Every skill dir has `SKILL.md` with non-empty `name` + `description`; no duplicates; all 7 expected skills present |
| 4 | Agents frontmatter | Both expected agent `.md` files exist with non-empty `name` + `description` |
| 5 | MCP URL exact-match | `.mcp.json` `plumlayer` server url == `https://api-production-0a7b.up.railway.app/mcp` |
| 6 | No absolute paths | No `C:\`, `/Users/`, `/home/`, `/root/` literals baked into `.mcp.json`, `plugin.json`, or `marketplace.json` |

**SKILL_DESC_WARN_CHARS** constant (default 600): descriptions exceeding this
threshold emit a WARN but do not fail the check. The export skills have long
descriptions by design — adjust the constant if the threshold needs tuning.

---

## Layer 2 — Load Check (`load_check.py`)

One headless claude invocation, bounded at 120 seconds.

```
claude --bare --plugin-dir <plugin_path>
       -p "Initialize only. Do nothing else."
       --output-format stream-json --verbose
```

Raw JSONL output is written to `harness/.test-results/claude-init.jsonl`
(gitignored) for inspection.

### Empirical init-event shape (confirmed v2.1.183, 2026-06-20)

The `{"type":"system","subtype":"init"}` event fires **before** authentication
is attempted and contains:

- `plugins`: list of `{name, path, source}` — one entry per loaded plugin.
  A plugin that fails to load is **absent** from this list (no explicit error
  field). The check infers "no load error" from presence.
- `skills`: list of prefixed skill names (`plumlayer:drawing-ingest`, etc.).
- `agents`: globally-configured agent types only — **does NOT include
  plugin-bundled agents** (see limitation below).
- `mcp_servers`: MCP servers loaded into this session.
- `apiKeySource`: `"none"` when the shell has no API key — expected.

### Checks

| Check | What it proves |
|-------|----------------|
| headless-claude-invocation | `claude` CLI runs and emits an init event within 120s |
| plugin-plumlayer-loaded | Plugin `plumlayer` present in `plugins[]` by name |
| no-plugin-load-errors | Plumlayer plugin loaded (absence = load error); auth failure is a separate, expected event |
| skills-all-7-present | All 7 `plumlayer:*` skills present in `skills[]` |
| mcp-under-bare (observational) | Documents MCP server presence/absence — see limitation |
| plugin-agents (limitation noted) | Documents agent assertion gap — see limitation |

### Limitation: MCP under `--bare`

The bundled hosted MCP server (`https://api-production-0a7b.up.railway.app/mcp`)
does **not** appear in `mcp_servers[]` under `--bare --plugin-dir`. The runtime
defers the HTTP+OAuth connection attempt (no OAuth flow starts in headless mode).
The check is marked observational and does not fail on absence. To assert MCP
load end-to-end, use a non-bare interactive session with an authenticated user.

### Limitation: plugin-bundled agents not in init event

Plugin `agents/` definitions (`scope-decomposer`, `trade-specialist`) do **not** surface in the init
event's `agents[]` field.
That field lists only globally-configured agent types. Plugin agents load
correctly at runtime but cannot be asserted from the headless JSONL stream.
Layer 1's `check_agents()` validates file presence + frontmatter statically —
that is the appropriate gate for agent definitions.

### Authentication note

The Bash tool shell environment has `apiKeySource: "none"`, so the session ends
with `authentication_failed` after the init event. This is expected and does
not affect plugin load assertions (init fires first, unconditionally).

---

## File layout

```
harness/
  README.md            # this file
  run.py               # entry point (Layers 1+2)
  static_checks.py     # Layer 1 — deterministic checks
  load_check.py        # Layer 2 — headless load assertion
  _cli.py              # shared: subprocess invoke + JSONL parse
  requirements.txt     # stdlib only; annotated
  .gitignore           # excludes .test-results/ and __pycache__
  .test-results/       # gitignored — raw JSONL output lands here
```
