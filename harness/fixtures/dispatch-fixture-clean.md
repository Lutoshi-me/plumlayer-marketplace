---
name: dispatch-fixture-clean
description: A harness fixture standing in for a file whose dispatch template names the foreground, beside a fenced block that dispatches nothing. Not shipped, and not dispatched by anything.
model: sonnet
tools: Read, Write, Bash
---

Nothing dispatches this file: the harness reads it to prove the dispatch check passes a template
that names the foreground, and leaves a fenced block naming no agent type alone.

```text
subagent_type: plumlayer:scope-reader
run_in_background: false
Project: <projectId>. Unit: <unit id>.
Read your unit as your definition says, then return your report.
```

The block below names no subagent type, so the check has nothing to say about it.

```text
verify_unit(subject_prefix: scopeItem:fixture-)
```
