---
name: agent-fixture-no-effort
description: A harness fixture standing in for a run agent whose frontmatter pins its model and no effort. Not shipped, and not dispatched by anything.
model: sonnet
tools: Read, Write, Bash, mcp__plugin_plumlayer_plumlayer__search
---

You read one invented unit and you report. Nothing dispatches this file: the harness reads it to
prove the model check refuses a definition that pins no effort.

You call `search` to find the unit. The tools line and the model are in order, so the missing
`effort` field is the only thing wrong here.
