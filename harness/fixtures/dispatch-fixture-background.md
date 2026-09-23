---
name: dispatch-fixture-background
description: A harness fixture standing in for a file whose dispatch template leaves the call's foreground unsaid. Not shipped, and not dispatched by anything.
model: sonnet
tools: Read, Write, Bash
---

Nothing dispatches this file: the harness reads it to prove the dispatch check refuses a template
that names a subagent type and does not name the foreground. That is the one thing wrong here, so
the refusal is one line.

```text
subagent_type: plumlayer:scope-reader
Project: <projectId>. Unit: <unit id>.
Read your unit as your definition says, then return your report.
```
