---
name: agent-fixture-wildcard-tools
description: A harness fixture standing in for a run agent whose tools line takes the whole connector instead of naming its verbs. Not shipped, and not dispatched by anything.
model: sonnet
tools: Read, Write, Bash, mcp__plugin_plumlayer_plumlayer__*
---

You read one invented unit and you report. Nothing dispatches this file: the harness reads it to
prove the tool surface check refuses a wildcard tools line.

The body names no connector verb, so the wildcard is the only thing wrong here and the refusal is
one line.
