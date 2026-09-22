---
name: agent-fixture-clean
description: A harness fixture standing in for a run agent whose tools line names every connector verb its text names and pins its model. Not shipped, and not dispatched by anything.
model: sonnet
tools: Read, Write, Bash, mcp__plugin_plumlayer_plumlayer__record, mcp__plugin_plumlayer_plumlayer__search, mcp__plugin_plumlayer_plumlayer__verify_unit
---

You read one invented unit and you report. Nothing dispatches this file: the harness reads it to
prove the tool surface and model checks pass a definition that is in order.

You call `search` to find the unit, and you call `record` to write what you
read. Both are on the tools line, and so is the verb the fenced call below names.

```
verify_unit(subject_prefix: scopeItem:fixture-)
```
