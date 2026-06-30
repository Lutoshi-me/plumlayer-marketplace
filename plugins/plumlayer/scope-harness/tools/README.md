# Tools - Superseded Route-First Harness

Status: superseded by PLU-274. Guard added by PLU-323.

These Python tools belong to the retired route-first scope harness. They are retained as historical and
migration assets only. Do not run them as a normal production scope pipeline from `/scope-run`.

In particular, the old fan-out/reconcile/default deposit path is blocked:

- `build_fanout.py`
- `ingest_fanout.py`
- `reconcile_overlap.py`
- `coverage_audit.py`
- `project_scope.py`
- `prepare_deposit.py`

If a migration or replay needs one of these tools, label the run as a superseded route-first experiment
and keep any output out of MOSOT unless Luke explicitly approves that historical deposit.
