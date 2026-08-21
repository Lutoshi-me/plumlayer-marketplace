"""
load_check.py — Layer 2: headless model-load validation.

Goal: prove a fresh Claude session loads the plugin with the expected skills
      and no plugin load errors. One model call; bounded timeout.

Empirical findings from real init-event inspection (2026-06-20, v2.1.183):

  Init event shape (type="system", subtype="init"):
    - plugins: list of {name, path, source} — one entry per loaded plugin.
      Plugin load errors are indicated by ABSENCE from this list (the runtime
      silently drops a failed plugin rather than emitting an error field).
      No separate "plugin_errors" field exists in the observed event stream.
    - skills: list of prefixed skill names (e.g. "plumlayer:drawing-ingest").
    - agents: list of globally-configured agent TYPE names — does NOT include
      per-plugin agent definitions from agents/*.md. Plugin agents are loaded
      by the runtime but are NOT surfaced in the init event's agents field.
    - mcp_servers: list of MCP server configs loaded into this session.
      Under --bare --plugin-dir, bundled hosted MCP (HTTP+OAuth) does NOT
      appear in mcp_servers (--bare suppresses it, or OAuth flow is deferred).
      See README "MCP under --bare" section for the noted limitation.
    - apiKeySource: "none" in unauthenticated shells — expected; auth failure
      fires as a separate assistant event after init, which is normal.

  Authentication: the Bash tool environment lacks an API key, so the session
  fails with authentication_failed after the init event. This is EXPECTED and
  does not affect plugin load assertions (init fires before auth is attempted).

Assertions built against the actual observed event shape:
  - Plugin "plumlayer" present in plugins[] by name.
  - All nine expected skills present in skills[] with "plumlayer:" prefix.
  - The plugin ships two agents under agents/, but the init event's agents[]
    field carries globally-configured agent types only, so Layer 2 cannot
    assert them. Their static check is Layer 1's agents-frontmatter.
  - MCP under --bare: bundled hosted MCP not observed in mcp_servers[].
    Documented limitation — needs non-bare invocation with auth to test.

Grounding role: shells out to claude CLI and parses JSONL. No inference.
"""

import subprocess
from pathlib import Path

from _cli import invoke_headless, find_init_event

# --------------------------------------------------------------------------- #
# Constants
# --------------------------------------------------------------------------- #

EXPECTED_PLUGIN_NAME = "plumlayer"

EXPECTED_SKILL_NAMES = {
    "plumlayer:bid-intake",
    "plumlayer:drawing-set-assemble",
    "plumlayer:drawing-upload",
    "plumlayer:learn-project",
    "plumlayer:project-create",
    "plumlayer:project-record",
    "plumlayer:scope-run",
    "plumlayer:setup",
    "plumlayer:takeoff",
}

HEADLESS_TIMEOUT_SEC = 120
JSONL_OUTPUT_PATH = Path(__file__).parent / ".test-results" / "claude-init.jsonl"


# --------------------------------------------------------------------------- #
# Result helper (shared shape with Layer 1)
# --------------------------------------------------------------------------- #

class Result:
    def __init__(self, name: str, passed: bool, detail: str = "", warning: str = ""):
        self.name = name
        self.passed = passed
        self.detail = detail
        self.warning = warning

    def __repr__(self) -> str:
        status = "PASS" if self.passed else "FAIL"
        s = f"  [{status}] {self.name}"
        if self.detail:
            s += f"\n         {self.detail}"
        if self.warning:
            s += f"\n         WARN: {self.warning}"
        return s


# --------------------------------------------------------------------------- #
# Checks
# --------------------------------------------------------------------------- #

def check_plugin_present(init_event: dict) -> Result:
    name = "plugin-plumlayer-loaded"
    plugins = init_event.get("plugins", [])
    loaded_names = [p.get("name") for p in plugins]
    if EXPECTED_PLUGIN_NAME in loaded_names:
        entry = next(p for p in plugins if p.get("name") == EXPECTED_PLUGIN_NAME)
        return Result(name, True, detail=f"source={entry.get('source')}, path={entry.get('path')}")
    else:
        return Result(name, False, detail=f"'plumlayer' not in plugins[]; found: {loaded_names}")


def check_skills_present(init_event: dict) -> Result:
    name = "skills-all-present"
    skills_in_event = set(init_event.get("skills", []))
    plumlayer_skills = {s for s in skills_in_event if s.startswith("plumlayer:")}
    missing = EXPECTED_SKILL_NAMES - plumlayer_skills
    unexpected = plumlayer_skills - EXPECTED_SKILL_NAMES

    present_count = len(EXPECTED_SKILL_NAMES) - len(missing)
    detail = f"{present_count}/{len(EXPECTED_SKILL_NAMES)} skills present"
    if missing:
        detail += f"; missing: {sorted(missing)}"
    if unexpected:
        detail += f"; unexpected plumlayer skills: {sorted(unexpected)}"

    return Result(name, passed=len(missing) == 0, detail=detail)


def check_no_plugin_load_errors(init_event: dict) -> Result:
    """
    The init event has no explicit plugin_errors field (empirically confirmed).
    A plugin that fails to load is simply absent from plugins[].
    We infer 'no load errors' from the plugin being present (check_plugin_present).
    This check surfaces the auth state as a distinct observation.
    """
    name = "no-plugin-load-errors"
    api_key_source = init_event.get("apiKeySource", "unknown")
    plugins = init_event.get("plugins", [])
    plumlayer_loaded = any(p.get("name") == EXPECTED_PLUGIN_NAME for p in plugins)

    if plumlayer_loaded:
        note = (
            f"apiKeySource={api_key_source} — auth failure is expected in this "
            f"shell context and is separate from plugin loading"
            if api_key_source == "none" else f"apiKeySource={api_key_source}"
        )
        return Result(name, True, detail=note)
    else:
        return Result(name, False, detail="plumlayer absent from plugins[] — likely a load error")


def check_mcp_under_bare(init_event: dict) -> Result:
    """
    Observe whether the bundled hosted MCP server appears in mcp_servers[].
    Documents the finding; does not fail on absence (expected limitation under --bare).
    """
    name = "mcp-under-bare (observational)"
    mcp_servers = init_event.get("mcp_servers", [])
    plumlayer_mcp = [s for s in mcp_servers if "plumlayer" in str(s).lower()]

    if plumlayer_mcp:
        return Result(
            name, True,
            detail=f"plumlayer MCP server present in mcp_servers: {plumlayer_mcp}"
        )
    else:
        return Result(
            name, True,  # not a failure — expected behavior under --bare
            warning=(
                "plumlayer MCP server NOT in mcp_servers[] under --bare. "
                "Expected: --bare suppresses bundled HTTP+OAuth MCP servers (OAuth flow deferred). "
                "To assert MCP load, use a non-bare invocation with auth."
            ),
            detail=f"mcp_servers=[{mcp_servers}]",
        )


# --------------------------------------------------------------------------- #
# Public entry point
# --------------------------------------------------------------------------- #

def run_load_check(plugin_path: Path) -> tuple[list[Result], bool]:
    """
    Run Layer 2. Returns (results, all_passed).
    Stops early and returns a single FAIL result if claude is unavailable or
    the init event is missing from the stream.
    """
    # Attempt the headless invocation
    try:
        events = invoke_headless(
            plugin_dir=plugin_path,
            prompt="Initialize only. Do nothing else.",
            output_path=JSONL_OUTPUT_PATH,
            timeout_sec=HEADLESS_TIMEOUT_SEC,
        )
    except FileNotFoundError:
        r = Result("headless-claude-invocation", False,
                   detail="`claude` not found on PATH — Layer 2 cannot run")
        return [r], False
    except subprocess.TimeoutExpired:
        r = Result("headless-claude-invocation", False,
                   detail=f"claude timed out after {HEADLESS_TIMEOUT_SEC}s")
        return [r], False
    except Exception as e:
        r = Result("headless-claude-invocation", False, detail=f"unexpected error: {e}")
        return [r], False

    init_event = find_init_event(events)
    if init_event is None:
        r = Result("headless-claude-invocation", False,
                   detail=f"no system/init event found in {len(events)} JSONL events — "
                          f"check {JSONL_OUTPUT_PATH} for raw output")
        return [r], False

    invocation_ok = Result(
        "headless-claude-invocation", True,
        detail=f"init event received; {len(events)} total events; "
               f"apiKeySource={init_event.get('apiKeySource')}; "
               f"model={init_event.get('model')}; "
               f"output saved to {JSONL_OUTPUT_PATH}"
    )

    results = [
        invocation_ok,
        check_plugin_present(init_event),
        check_no_plugin_load_errors(init_event),
        check_skills_present(init_event),
        check_mcp_under_bare(init_event),
    ]
    all_passed = all(r.passed for r in results)
    return results, all_passed
