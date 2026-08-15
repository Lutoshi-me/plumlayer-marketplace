"""
run.py — Plumlayer plugin test harness entry point.

Usage:
    python harness/run.py [static|load|all]

Layer layout:
  Layer 1 (static)  — deterministic file + CLI checks (no model calls).
  Layer 2 (load)    — headless claude init-event assertions (one model call).

  `all` runs Layers 1+2 (the default).

Exits nonzero if any layer fails.
"""

import sys
from pathlib import Path

# Windows consoles default stdout to the system codepage (cp1252), which
# can't encode characters some checks legitimately surface (e.g. a banned
# em dash quoted in a violation detail, or a checkmark in `claude`'s own
# CLI output). Reconfigure to UTF-8 with a safe fallback so a check result
# never crashes the harness on the way out.
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

# Resolve the marketplace repo root and plugin path relative to this file.
_HARNESS_DIR = Path(__file__).parent.resolve()
_MARKETPLACE_ROOT = _HARNESS_DIR.parent.resolve()
_PLUGIN_PATH = _MARKETPLACE_ROOT / "plugins" / "plumlayer"

# Add harness dir to sys.path so _cli / static_checks / load_check can import.
sys.path.insert(0, str(_HARNESS_DIR))


def _print_header(title: str) -> None:
    print()
    print("=" * 60)
    print(f"  {title}")
    print("=" * 60)


def _print_results(results: list, layer_passed: bool) -> None:
    for r in results:
        print(repr(r))
    print()
    verdict = "PASSED" if layer_passed else "FAILED"
    print(f"  Layer verdict: {verdict}")


def run_static(verbose: bool = True) -> bool:
    from static_checks import run_static_checks

    _print_header("Layer 1 — Static Checks")
    results, passed = run_static_checks(_PLUGIN_PATH, _MARKETPLACE_ROOT)
    _print_results(results, passed)
    return passed


def run_load(verbose: bool = True) -> bool:
    from load_check import run_load_check

    _print_header("Layer 2 — Load Check (headless claude)")
    results, passed = run_load_check(_PLUGIN_PATH)
    _print_results(results, passed)
    return passed


def _usage() -> None:
    print("Usage: python harness/run.py [static|load|all]")
    print("  static  — Layer 1: deterministic file + CLI checks (no model calls)")
    print("  load    — Layer 2: headless claude init-event assertions")
    print("  all     — Layers 1+2 (default)")
    sys.exit(1)


def main() -> None:
    args = [a.lower() for a in sys.argv[1:]]
    arg = args[0] if args else "all"

    if arg not in ("static", "load", "all"):
        _usage()

    print(f"\nPlumlayer plugin harness — Phase 1")
    print(f"  Plugin:    {_PLUGIN_PATH}")
    print(f"  Marketplace root: {_MARKETPLACE_ROOT}")

    results_by_layer: dict[str, bool] = {}

    if arg in ("static", "all"):
        results_by_layer["Layer 1 (static)"] = run_static()

    if arg in ("load", "all"):
        results_by_layer["Layer 2 (load)"] = run_load()

    # Summary
    _print_header("Summary")
    overall_passed = True
    for layer_name, passed in results_by_layer.items():
        verdict = "PASSED" if passed else "FAILED"
        print(f"  {layer_name}: {verdict}")
        if not passed:
            overall_passed = False

    print()
    if overall_passed:
        print("  OVERALL: PASSED")
    else:
        print("  OVERALL: FAILED")
    print()

    sys.exit(0 if overall_passed else 1)


if __name__ == "__main__":
    main()
