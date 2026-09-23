---
name: dispatch-fixture-unclosed
description: A harness fixture standing in for a file whose last fenced block is never closed. Not shipped, and not dispatched by anything.
model: sonnet
tools: Read, Write, Bash
---

Nothing dispatches this file: the harness reads it to prove the dispatch check refuses a file whose
last fence is never closed, rather than dropping the block it opened and reporting a clean read.
The block below names a subagent type and names the foreground, so the only thing wrong here is the
missing closing fence, and the refusal is one line.

```text
subagent_type: plumlayer:scope-reader
run_in_background: false
Project: <projectId>. Unit: <unit id>.
Read your unit as your definition says, then return your report.
