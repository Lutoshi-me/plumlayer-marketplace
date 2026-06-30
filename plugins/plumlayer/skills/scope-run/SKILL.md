---
name: scope-run
description: >
  Guarded Plumlayer scope entrypoint. Trigger when asked to run the scope harness, scope a drawing set,
  generate per-trade scope, or use /scope-run. PLU-323 blocks the retired route-first pipeline while
  PLU-274 rebuilds scope as scope-item-first: one grounded scope list first, then trade-package
  derivation. This skill refuses old fan-out/reconcile execution by default.
---

# Scope Run - Guarded During PLU-274

This installed skill is a guard, not an active production scope engine.

## Current Status

- Decision: the old route-first harness is superseded. Its sequence was
  `ground -> decompose -> per-trade fan-out -> reconcile-by-overlap -> coverage -> project -> deposit`.
- Decision: PLU-274 is the canonical build issue for the replacement scope-item-first engine.
- Decision: the replacement shape is one grounded, cited, trade-agnostic scope list for the job first,
  then derived trade packages. No routing stage, no per-trade fan-out, no reconcile-by-overlap as the
  production architecture.
- Evidence: PLU-323 exists because the installed 0.10.1 skill still advertised the retired route-first
  path, creating a live correctness hazard for fresh plugin sessions.

Until PLU-274 ships the replacement, a normal "scope this set" request must fail loud instead of
dispatching the old harness.

## Required Behavior When Triggered

1. Stop before running any route-first command, bundled scope subagent, or MOSOT deposit.
2. Tell the user plainly:

   ```text
   I cannot run the installed scope-run harness as the current production scope path. The installed
   route-first pipeline was retired by PLU-274. Current doctrine is scope-item-first: produce one
   grounded whole-job scope list, then derive trade packages. I can help inspect the historical
   route-first assets, run drawing-ingest/grounding, read existing MOSOT claims, or work on PLU-274,
   but I will not dispatch the old fan-out/reconcile process by default.
   ```

3. Offer only safe next actions:
   - run or help with `drawing-ingest` so the set is identified and grounded;
   - inspect existing MOSOT data with the `mosot` skill;
   - work on PLU-274's scope-item-first design or implementation;
   - inspect the legacy route-first assets as historical evidence, clearly labeled superseded.

## Hard Stops

- Do not run `build_fanout.py`, `ingest_fanout.py`, `reconcile_overlap.py`, `coverage_audit.py`,
  `project_scope.py`, or `prepare_deposit.py` as a normal scope-run path.
- Do not dispatch `scope-decomposer` or `trade-specialist` from a normal scope request.
- Do not deposit route-first scope output into MOSOT unless Luke explicitly asks for a historical
  replay or migration experiment and the output is labeled `superseded route-first experiment`.
- Do not present the legacy route-first harness as production, current, recommended, or doctrine-aligned.

## Historical Assets

The bundled `scope-harness/` tools, prompts, lenses, and the `scope-decomposer` / `trade-specialist`
agents remain in the plugin as historical route-first artifacts. They may be useful for comparison,
tests, migration, or PLU-274 design archaeology. They are not the current execution path.

If asked to inspect them, use these labels:

- Evidence: the asset exists and belongs to the superseded route-first harness.
- Decision: PLU-274 owns the production replacement.
- Open Question: any behavior that should survive into scope-item-first must be re-justified in PLU-274
  rather than copied forward by inertia.

## Completion Bar For This Guard

A fresh plugin install/session triggered by "scope this set" must reach this guard and stop before the
retired fan-out/reconcile pipeline can start.
