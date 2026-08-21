# Plumlayer plugin test harness

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
gives a per-check PASS/FAIL/SKIP with detail.

## Dependencies

Standard library only (`json`, `subprocess`, `pathlib`, `re`). No pip install
needed.

```
harness/requirements.txt   # empty / annotated, for completeness
```

## Layer 1, static checks (`static_checks.py`)

Fully deterministic. No model calls. Runs in a few seconds. This is the layer
that enforces `docs/plugin-text-style.md`; see that file for the authoring
contract each check is derived from.

| # | Check | What it proves |
|---|-------|----------------|
| 1 | `claude plugin validate --strict` | CLI validator passes with warnings-as-errors. Reports SKIP, not a crash or a silent pass, when `claude` isn't on PATH. |
| 2 | Version-quadruple lockstep | `plugin.json` (Claude), `plugin.json` (Codex), and both version fields in `marketplace.json` are identical |
| 3 | Skills frontmatter | Every skill dir has `SKILL.md` with non-empty `name` and `description`; no duplicates; the shipped skill set matches the expected ten exactly, in both directions |
| 4 | Description contract | Every description is non-empty, folded YAML style (`description: >`), and at most 600 characters. Reports each skill's actual character count. |
| 5 | Banned strings | No client-name denylist hit, `PLU-\d+`, internal vault filename, `MOSOT`, em dash, or middle dot in shipped text. The full set applies to skills, the root README, all four manifest JSON files, and anything in `trade-knowledge/` that isn't a pinned corpus trade file (currently `MANIFEST.md`, hand-authored release prose, and any future hand-authored file dropped in beside the trade files); the client-name denylist alone applies to the pinned trade files themselves, read from `MANIFEST.md`'s own "## Trade files" list rather than hardcoded, so a file not on that list defaults to the full scan. Em dash and middle dot are exempt inside fenced code blocks and inline code spans, since those are data (e.g. the citation format, the claim-atom notation), not prose; every other pattern still applies inside code. The detail line reports the two scan populations as separate counts. Each hit is reported with file, line, and the offending match. |
| 6 | MCP URL exact-match | `.mcp.json` `plumlayer` server url equals `https://api-production-0a7b.up.railway.app/mcp` |
| 7 | No absolute paths | No `C:\`, `/Users/`, `/home/`, `/root/` literals baked into `.mcp.json`, `plugin.json` (Claude), `plugin.json` (Codex), or `marketplace.json` |

The plugin ships nine skills and no `agents/` directory, so there is nothing
for this harness to check about plugin agents.

## Layer 2, load check (`load_check.py`)

One headless claude invocation, bounded at 120 seconds.

```
claude --bare --plugin-dir <plugin_path>
       -p "Initialize only. Do nothing else."
       --output-format stream-json --verbose
```

Raw JSONL output is written to `harness/.test-results/claude-init.jsonl`
(gitignored) for inspection.

### Empirical init-event shape (confirmed v2.1.183, 2026-06-20)

The `{"type":"system","subtype":"init"}` event fires before authentication is
attempted and contains:

- `plugins`: list of `{name, path, source}`, one entry per loaded plugin. A
  plugin that fails to load is absent from this list (no explicit error
  field). The check infers "no load error" from presence.
- `skills`: list of prefixed skill names (`plumlayer:setup`, etc.).
- `agents`: globally-configured agent types only.
- `mcp_servers`: MCP servers loaded into this session.
- `apiKeySource`: `"none"` when the shell has no API key, which is expected.

### Checks

| Check | What it proves |
|-------|----------------|
| headless-claude-invocation | `claude` CLI runs and emits an init event within 120s |
| plugin-plumlayer-loaded | Plugin `plumlayer` present in `plugins[]` by name |
| no-plugin-load-errors | Plumlayer plugin loaded (absence means a load error); auth failure is a separate, expected event |
| skills-all-10-present | All 10 `plumlayer:*` skills present in `skills[]` |
| mcp-under-bare (observational) | Documents MCP server presence or absence, see limitation below |

### Limitation: MCP under `--bare`

The bundled hosted MCP server (`https://api-production-0a7b.up.railway.app/mcp`)
does not appear in `mcp_servers[]` under `--bare --plugin-dir`. The runtime
defers the HTTP+OAuth connection attempt (no OAuth flow starts in headless
mode). The check is marked observational and does not fail on absence. To
assert MCP load end to end, use a non-bare interactive session with an
authenticated user.

### Authentication note

The Bash tool shell environment has `apiKeySource: "none"`, so the session
ends with `authentication_failed` after the init event. This is expected and
does not affect plugin load assertions (init fires first, unconditionally).

## File layout

```
harness/
  README.md          # this file
  run.py             # entry point (Layers 1+2)
  static_checks.py   # Layer 1, deterministic checks, enforces docs/plugin-text-style.md
  load_check.py      # Layer 2, headless load assertion
  _cli.py             # shared: subprocess invoke + JSONL parse
  requirements.txt   # stdlib only; annotated
  .gitignore          # excludes .test-results/ and __pycache__
  .test-results/       # gitignored, raw JSONL output lands here
```
