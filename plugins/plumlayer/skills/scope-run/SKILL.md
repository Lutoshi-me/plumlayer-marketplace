---
name: scope-run
description: >
  Guarded Plumlayer scope entrypoint. Trigger when asked to run the scope harness, scope a drawing set,
  generate per-trade scope, or use /scope-run. PLU-323 blocks the retired route-first pipeline while
  PLU-274 rebuilds scope as scope-item-first: one grounded scope list first, then trade-package
  derivation. This skill refuses old fan-out/reconcile execution by default.
---

# Scope Run - Guarded During PLU-274

## Talk to your user like an estimator

Verbs, claims, and trust classes are machinery for you, never words the user reads. Speak estimator
words to them: project record, entry, sheet, set, scale, scope item, bid response, flagged item,
trail. Never say to the user: claim, deposit, predicate, subject, proposed, governing, trust class,
supersede, promote, reconcile, QA, sheet type as "sheetType", grounding, residue, or any raw verb or
field name. Translate instead: a value you replaced is "I updated my earlier read"; a machine
mis-read you caught is "the automatic scan grabbed the wrong text, so I read the sheet and flagged
it for you to set on the site"; cross-checking the index is "checking the drawing list against the
actual sheets". Plain prose, no em dashes, no bolded emphasis words. Full guidance is in the
project-record skill's Words section.

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

1. Stop before running any route-first command, bundled scope subagent, or project record deposit.
2. Tell the user plainly:

   ```text
   I cannot run the installed scope-run harness as the current production scope path. The installed
   route-first pipeline was retired by PLU-274. Current doctrine is scope-item-first: produce one
   grounded whole-job scope list, then derive trade packages. The removed route-first machinery was
   deleted in PLU-349; git history before that removal commit is the archive for inspection. I can
   run drawing-upload/recognition, read what is already in the project record, or work on PLU-274, but I will not
   dispatch the old fan-out/reconcile process by default.
   ```

3. Offer only safe next actions:
   - run or help with `drawing-upload` so the set is identified and recognized;
   - inspect existing project data with the `project-record` skill;
   - work on PLU-274's scope-item-first design or implementation;
   - inspect the removed route-first machinery through git history before PLU-349, clearly labeled
     superseded.

## Hard Stops

- Do not restore or run the removed route-first toolchain as a normal scope-run path.
- Do not dispatch removed route-first scope subagents from a normal scope request.
- Do not deposit route-first scope output into the project record unless Luke explicitly asks for a historical
  replay or migration experiment and the output is labeled `superseded route-first experiment`.
- Do not present the legacy route-first harness as production, current, recommended, or doctrine-aligned.

## Historical Assets

The route-first tools, lenses, cluster configs, and scope subagents were removed in PLU-349. The
remaining `scope-harness/` content is limited to active ingestion helpers, reference material, and
design-lineage prompts. Use git history before the PLU-349 removal commit to inspect the removed
machinery for comparison, tests, migration, or PLU-274 design archaeology.

If asked to inspect them, use these labels:

- Evidence: the asset was removed in PLU-349 and belonged to the superseded route-first harness.
- Decision: PLU-274 owns the production replacement.
- Open Question: any behavior that should survive into scope-item-first must be re-justified in PLU-274
  rather than copied forward by inertia.

## Completion Bar For This Guard

A fresh plugin install/session triggered by "scope this set" must reach this guard and stop before the
retired fan-out/reconcile pipeline can start.
