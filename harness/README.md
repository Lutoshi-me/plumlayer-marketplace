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

One optional import: `yaml` (PyYAML). Where it is importable, the frontmatter
checks validate each block with a real parser, which is the only way to catch
the general case of malformed frontmatter. Where it is not, they fall back to a
stdlib check for the one failure this repo has actually shipped: an unquoted
`": "` inside a plain scalar value, which makes the block invalid YAML while
reading fine to a regex. Nothing is skipped either way.

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
| 3 | Skills frontmatter | Every skill dir has `SKILL.md` whose frontmatter parses as YAML and carries a non-empty `name` and `description`; no duplicates; the shipped skill set matches the expected nine exactly, in both directions |
| 4 | Description contract | Every description is non-empty, folded YAML style (`description: >`), and at most 600 characters. Reports each skill's actual character count. |
| 5 | Banned strings | No client-name denylist hit, `PLU-\d+`, internal vault filename, `MOSOT`, em dash, or middle dot in shipped text. One scan, one population: skills, the plugin's `agents/` definitions, the plugin's `scripts/*.py` (a shipped script's module docstring, stdout line, and error messages are text in the plugin's voice, and a run reports what the script said), the root README, and all four manifest JSON files. There is no lenient population and no exemption list; a shipped file is the plugin's own prose and takes the full set. Em dash and middle dot are exempt inside fenced code blocks and inline code spans, since those are data (e.g. the citation format, the claim-atom notation), not prose; every other pattern still applies inside code. Each hit is reported with file, line, and the offending match. |
| 6 | MCP URL exact-match | `.mcp.json` `plumlayer` server url equals `https://api-production-0a7b.up.railway.app/mcp` |
| 7 | No absolute paths | No `C:\`, `/Users/`, `/home/`, `/root/` literals baked into `.mcp.json`, `plugin.json` (Claude), `plugin.json` (Codex), or `marketplace.json` |
| 8 | Question/failure boundary | No skill or agent file tells the agent to raise a Question near failure language (a failed or timed-out job, an image-only or unresolved page, a retry) with no prohibition cue in range; every file naming `ask_question` / "raise a Question" carries the sentence stating a Question is about the project, never about a Plumlayer failure |
| 8b | Question plain-words pointer | Every file naming `ask_question` / "raise a Question" carries the fixed phrase "Question text is plain estimator words", either stating the rule in full (`learn-project`'s judgment-entry table) or pointing at it. Cannot judge whether a given Question actually reads in plain words; that stays in review. |
| 8c | Question RFI bar | `agents/scope-reader.md` carries the bar in its fixed wording, "first inkling of an RFI". And no shipped skill or agent file carries a retired raise-for-everything phrase ("rather than smoothing it", "rather than guessing") on the same line as the word Question, the wording that had the reader raise one for every uncertainty it met. Matched on one line because the collocation is what makes the phrase a directive: `scope-reader.md`'s own legitimate "rather than guessing at one" about a category string is not about Questions and stays clean. Cannot judge whether a Question an agent actually raises clears the bar; that stays in review. |
| 9 | Ledger fixed shape | The runner definition's ledger grammar block declares exactly the three line kinds (`dispatch`, `verified`, `note`) and the `note` kind list is the closed pinned set, both asserted in both directions; every skill or agent file that instructs appending to the ledger carries the sentence "Nothing else goes in the ledger"; and no prose-permitting cue (`narrate`, `summarize`, `paragraph`, `in your own words`, and similar) sits within a paragraph-clamped window of a ledger mention with no prohibition cue in range. Honest bound on that last arm, the same shape as check 6's: it is a regression guard against the drift that actually shipped (a runner that wrote 75 KB of prose into the ledger and re-read it on every call), not a general proof. It catches a definition that tells the runner to narrate or summarize near the ledger. A definition that permits prose in wording the cue list does not name still passes. The first two arms are exact set comparisons and are proofs. |
| 10 | Runner mode set | The `##` headings of `agents/scope-round-runner.md` match the pinned set exactly, in both directions (`What your dispatch gives you`, `Pass mode`, `The ledger lines`, `Boundary mode`, `Review mode`, `What you never do`, `Your summary`). This is the cheap mechanical way to catch the per-pass shape being partly undone: a `## Round mode` or a `## Leftover mode` coming back, or `## Pass mode` renamed away, fails the release. Follows the `EXPECTED_SKILLS` / `EXPECTED_AGENTS` precedent, which are already asserted both ways. |
| 11 | Plan inventory | The shipped `scripts/plan_inventory.py`, imported in-process and run end to end over an invented fixture set: a 39-sheet grid across seven disciplines (one with no discipline, one with no sheet type, every vocabulary type present, every window 2 type present in an order that is not the reading order, one discipline whose sheets exceed a pass) and two packages fixtures. Asserts the inventory mode's counts and its unit keys against a tally the check computes itself; that `--expect-count` off by one refuses in one line; that window 1 selects exactly the vocabulary sheets plus includes minus excludes, once each, every unit line citing the page the grid gives it, and writes a `plan/window-1.json` matching that selection key for key; that window 2 is an exact partition of the inventory minus both of window 1's lists, grouped by discipline in inventory order, sorted inside a discipline by the pinned sheet type order with inventory order kept inside a type, and split into balanced lettered passes at twelve; that both of the script's sheet type constants equal the lists pinned in the check and name no type the recognizer does not produce; that window 3 plans one review per package over both packages fixtures, in package order, with two packages on one trade both planning and planned one after the other; that every window 3 unit id is a legal `verify_unit` subject prefix stem with `scopeItem:` in front and `-` behind and none a prefix of another, which is the join the plan and the reviewer would otherwise first meet on mid-run; and that eleven broken invocations each refuse with exit 1 and one stderr line naming what is wrong, among them a window 1 file naming a key as both selected and excluded, which corrupts the count the bounds line says out loud while still leaving window 2 a correct partition, and a grid whose two rows fold to one unit key, the case where a sheet would otherwise vanish from every window with nothing said about it, since window 2 subtracts by that string and neither colliding row ever reaches the remainder its partition check counts. Every window's bounds line must name its counts. Honest bound: the fixtures are invented and small. They carry the field names the shipped verbs return, so a rename on the record's side fails here, but nothing about how a real grid or a real packages read arrives is proved by them. |
| 12 | No fork subagent | No shipped skill or agent file names `fork` as a subagent type, in either the `subagent_type:` dispatch-line shape this codebase's own templates use, or a `tools: Agent(fork)` frontmatter declaration. Regression guard for a runner that invented a wait primitive by dispatching fork agents (one told to wait for a reader's completion, two told to do nothing and return done) instead of making the reader dispatch itself the wait. Ordinary English uses of "fork" (a forklift, a decision fork) are untouched: the pattern only matches "fork" sitting immediately after one of the two anchors. |

Check 3b, agents frontmatter, sits between checks 3 and 4: every `agents/*.md`
has frontmatter that parses as YAML and carries a non-empty `name` and
`description`, the shipped agent set matches the expected three (`scope-reader`,
`scope-reviewer`, `scope-round-runner`) in both directions, and no agent declares `hooks`,
`mcpServers`, or `permissionMode`, the three frontmatter fields the runtime
ignores for plugin-shipped agents. That last one is worth a check rather than
review: declaring one is not a load error, so it reads as configured behavior
and silently isn't. The agent definitions are also shipped text in the plugin's
own voice, so they join the skills in the scan population for checks 5 through 8.

The frontmatter reader itself takes line 1 as the opening `---` and stops at the
next one. An earlier version treated the closing delimiter as the opener and
scanned the body, so a `key: value` line anywhere in a skill body could
overwrite a real frontmatter field. `claude plugin validate --strict` does not
cover this: it validates the plugin manifest, and it passed while a shipped
agent's frontmatter was invalid YAML.

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
| skills-all-present | All nine expected `plumlayer:*` skills present in `skills[]` |
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
