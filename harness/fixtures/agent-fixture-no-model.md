---
name: agent-fixture-no-model
description: A harness fixture standing in for a run agent whose frontmatter pins no model. Not shipped, and not dispatched by anything.
tools: Read, Write, Bash, mcp__plugin_plumlayer_plumlayer__search
---

You read one invented unit and you report. Nothing dispatches this file: the harness reads it to
prove the model check refuses a definition that pins no model.

You call `search` to find the unit. The tools line is in order, so the missing `model` field is the
only thing wrong here.
