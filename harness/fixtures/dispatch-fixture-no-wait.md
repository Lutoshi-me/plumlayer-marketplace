---
name: dispatch-fixture-no-wait
description: A harness fixture standing in for a file that dispatches an agent in the foreground and never says how to wait on a call that comes back with an agent id. Not shipped, and not dispatched by anything.
model: sonnet
tools: Read, Write, Bash
---

Nothing dispatches this file: the harness reads it to prove the dispatch check refuses a file that
dispatches an agent and carries no wait sentence for a call that comes back with an agent id. Its
template names the foreground, so the missing sentence is the one thing wrong here, and the
refusal is one line.

```text
subagent_type: plumlayer:scope-reader
run_in_background: false
Project: <projectId>. Unit: <unit id>.
Read your unit as your definition says, then return your report.
```
