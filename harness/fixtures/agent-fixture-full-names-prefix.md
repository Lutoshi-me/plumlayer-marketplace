---
name: agent-fixture-full-names-prefix
description: A harness fixture standing in for an agent that writes the client prefix into its text. Not shipped, and not dispatched by anything.
model: sonnet
effort: medium
tools: Read, Write, mcp__plugin_plumlayer_plumlayer__search
---

You read one invented unit and you report. Nothing dispatches this file: the harness reads it to
prove the full tool name check refuses a name only one client gives.

Each Plumlayer verb this file writes as a call, such as `search(...)`, is the tool on your tools list whose name ends in that verb: call it by that full name, never by the verb alone.

## What your dispatch gives you

Find the unit with `mcp__plugin_plumlayer_plumlayer__search(projectId, subject: "unit:1")`.
