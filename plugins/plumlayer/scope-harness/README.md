# Scope Harness - Superseded Route-First Assets

Status: superseded by PLU-274. Guard added by PLU-323.

This directory contains the retired route-first scope harness:

`ground -> decompose -> per-trade fan-out -> reconcile-by-overlap -> coverage -> project -> deposit`

The assets remain bundled for historical inspection, migration analysis, and tests. They are not the
current production scope path and must not be launched from a normal "scope this set" request.

Current doctrine: PLU-274 owns the replacement scope-item-first engine. The replacement produces one
grounded, cited, trade-agnostic scope list for the job first, then derives trade packages. Route-first
tools, prompts, agents, lenses, and reference docs in this folder should be read as historical evidence
unless Luke explicitly asks for a labeled legacy replay or migration experiment.

Hard guard:

- normal `/scope-run` requests stop in `skills/scope-run/SKILL.md`;
- `scope-decomposer` and `trade-specialist` stop when directly invoked for production scope;
- do not deposit output from this folder into MOSOT as current scope.
