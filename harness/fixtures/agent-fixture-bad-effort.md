---
name: agent-fixture-bad-effort
description: A harness fixture standing in for a run agent whose frontmatter names an effort level Claude Code does not take. Not shipped, and not dispatched by anything.
model: sonnet
effort: medum
tools: Read, Write, Bash, mcp__plugin_plumlayer_plumlayer__search
---

You read one invented unit and you report. Nothing dispatches this file: the harness reads it to
prove the model check refuses a definition whose effort is not one of the levels Claude Code takes.

You call `search` to find the unit. The tools line and the model are in order, so the misspelled
`effort` value is the only thing wrong here.
