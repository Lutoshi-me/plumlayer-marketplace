---
name: dispatch-fixture-retired-wait
description: A harness fixture standing in for a file that still carries the retired wait sentence beside the current one. Not shipped, and not dispatched by anything.
model: sonnet
tools: Read, Write, Bash
---

Nothing dispatches this file: the harness reads it to prove the dispatch check refuses a file that
carries the retired wait sentence. Its template names the foreground and it carries the current
wait sentence, so the retired one is the one thing wrong here, and the refusal is one line.

Where the call comes back with an agent id instead, the agent's report arrives later as its own
message: end the turn with one line naming what is running, and take the report when it arrives.
On the rare seat where the call still comes back at once with an agent id, wait for the report,
making no other call in between.

```text
subagent_type: plumlayer:scope-reader
run_in_background: false
Project: <projectId>. Unit: <unit id>.
Read your unit as your definition says, then return your report.
```
