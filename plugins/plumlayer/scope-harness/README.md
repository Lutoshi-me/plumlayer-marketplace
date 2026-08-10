# Scope Harness - Remaining Assets

Status: route-first execution removed by PLU-349. Guard added by PLU-323. Replacement tracked by PLU-274.

This directory no longer contains the retired route-first execution machinery. PLU-349 removed the old
tools, scope subagents, lens data, and cluster configs. If someone needs to inspect that code, use git
history from before the PLU-349 removal commit as the archive.

What remains here is intentionally narrower:

- `ingestion/` - active stage-2 schedule/spec extractors and drawing-set grounding helpers.
- `reference/` - historical and active doctrine used by the scope rebuild work.
- `prompts/` - design lineage retained for the stage-3 reader.
- `requirements.txt` - Python dependencies for the remaining local harness utilities.

Current doctrine: PLU-274 owns the replacement scope-item-first engine. The replacement produces one
grounded, cited, trade-agnostic scope list for the job first, then derives trade packages. The
scope-item-first contract doc lives in the main Plumlayer repo as `scope-package-architecture.md`, not in
this marketplace plugin.

Hard guard:

- normal `/scope-run` requests stop in `skills/scope-run/SKILL.md`;
- do not revive the removed route-first fan-out/reconcile path as production scope;
- do not deposit historical route-first output into the project record as current scope.
