"""
static_checks.py — Layer 1: deterministic, no model calls.

Checks:
  1. `claude plugin validate <plugin_path> --strict` exits 0.
  2. Version-triple lockstep across plugin.json / marketplace.json (2 fields).
  3. Skills: no duplicate `name`; no missing/empty `description`.
     WARN (not fail) if description > SKILL_DESC_WARN_CHARS.
  4. Agents: 3 expected agent files exist with non-empty `name` + `description`.
  5. MCP-URL: .mcp.json `plumlayer` server url == EXPECTED_MCP_URL exactly.
  6. No absolute paths (Windows C:\\ or Unix /Users/ /home/) in .mcp.json /
     plugin.json / marketplace.json.

Grounding role: reads files and shells out to the claude CLI. No inference.
"""

import json
import re
import subprocess
from pathlib import Path
from typing import Iterator

# --------------------------------------------------------------------------- #
# Constants
# --------------------------------------------------------------------------- #

EXPECTED_PLUGIN_NAME = "plumlayer"
EXPECTED_MCP_URL = "https://api-production-0a7b.up.railway.app/mcp"

EXPECTED_SKILLS = {
    "drawing-index-publish",
    "drawing-ingest",
    "drawing-set-assemble",
    "project-record",
    "project-create",
    "scope-run",
    "setup",
}

EXPECTED_AGENTS = {
    "scope-decomposer",
    "trade-specialist",
}

# Descriptions longer than this are flagged as WARNINGs (not FAILures).
SKILL_DESC_WARN_CHARS = 600

# Patterns that indicate an absolute local path baked into a config file.
_ABS_PATH_PATTERNS = [
    re.compile(r"[A-Za-z]:\\"),   # Windows  C:\, D:\, …
    re.compile(r"/Users/"),        # macOS home dirs
    re.compile(r"/home/"),         # Linux home dirs
    re.compile(r"/root/"),         # Linux root home
]


# --------------------------------------------------------------------------- #
# Result helpers
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
# Frontmatter parser (no pyyaml dependency)
# --------------------------------------------------------------------------- #

def _parse_frontmatter(path: Path) -> dict[str, str]:
    """
    Parse simple YAML-style frontmatter delimited by '---' lines.
    Returns a dict of key -> value strings (values are stripped of quotes).
    Returns {} if no frontmatter block is found.
    """
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return {}
    fields: dict[str, str] = {}
    in_block = False
    for line in lines[1:]:
        if line.strip() == "---":
            if in_block:
                break
            in_block = True
            continue
        # Parse "key: value" or 'key: "value"'
        m = re.match(r'^(\w[\w-]*):\s*(.*)', line)
        if m:
            key = m.group(1)
            val = m.group(2).strip()
            # Strip surrounding quotes if present
            if (val.startswith('"') and val.endswith('"')) or \
               (val.startswith("'") and val.endswith("'")):
                val = val[1:-1]
            fields[key] = val
    return fields


# Frontmatter block is between the first and second '---' lines.
# Re-implement to handle multi-line values (description can span lines
# in theory, but in practice all current SKILL.mds use a single quoted
# line). The simple regex parser above handles the real corpus correctly.


# --------------------------------------------------------------------------- #
# Check 1 — CLI validate
# --------------------------------------------------------------------------- #

def check_cli_validate(plugin_path: Path) -> Result:
    name = "cli-validate (claude plugin validate --strict)"
    try:
        r = subprocess.run(
            ["claude", "plugin", "validate", str(plugin_path), "--strict"],
            capture_output=True,
            text=True,
            timeout=30,
        )
        output = (r.stdout + r.stderr).strip()
        if r.returncode == 0:
            return Result(name, True, detail=output)
        else:
            return Result(name, False, detail=f"exit {r.returncode}: {output}")
    except FileNotFoundError:
        return Result(name, False, detail="`claude` not found on PATH")
    except subprocess.TimeoutExpired:
        return Result(name, False, detail="timed out after 30s")


# --------------------------------------------------------------------------- #
# Check 2 — Version-triple lockstep
# --------------------------------------------------------------------------- #

def check_version_triple(plugin_path: Path, marketplace_root: Path) -> Result:
    name = "version-triple-lockstep"
    plugin_json_path = plugin_path / ".claude-plugin" / "plugin.json"
    marketplace_json_path = marketplace_root / ".claude-plugin" / "marketplace.json"

    errors: list[str] = []
    versions: dict[str, str] = {}

    # plugin.json
    try:
        pj = json.loads(plugin_json_path.read_text(encoding="utf-8"))
        versions["plugin.json[version]"] = pj.get("version", "<missing>")
    except Exception as e:
        errors.append(f"plugin.json read error: {e}")

    # marketplace.json — metadata.version and plugins[0].version
    try:
        mj = json.loads(marketplace_json_path.read_text(encoding="utf-8"))
        versions["marketplace.json[metadata.version]"] = mj.get("metadata", {}).get("version", "<missing>")
        plugins_list = mj.get("plugins", [])
        if plugins_list:
            versions["marketplace.json[plugins[0].version]"] = plugins_list[0].get("version", "<missing>")
        else:
            errors.append("marketplace.json[plugins] is empty")
    except Exception as e:
        errors.append(f"marketplace.json read error: {e}")

    if errors:
        return Result(name, False, detail="; ".join(errors))

    unique_versions = set(versions.values())
    detail = "  " + ", ".join(f"{k}={v}" for k, v in versions.items())
    if len(unique_versions) == 1:
        return Result(name, True, detail=detail)
    else:
        return Result(name, False, detail=f"mismatch — {detail}")


# --------------------------------------------------------------------------- #
# Check 3 — Skills
# --------------------------------------------------------------------------- #

def check_skills(plugin_path: Path) -> Result:
    name = "skills-frontmatter"
    skills_dir = plugin_path / "skills"
    if not skills_dir.is_dir():
        return Result(name, False, detail=f"skills/ directory not found at {skills_dir}")

    skill_dirs = [d for d in skills_dir.iterdir() if d.is_dir()]
    if not skill_dirs:
        return Result(name, False, detail="no skill directories found")

    errors: list[str] = []
    warnings: list[str] = []
    seen_names: dict[str, str] = {}  # skill_name -> dir name

    for skill_dir in sorted(skill_dirs):
        entry = skill_dir / "SKILL.md"
        if not entry.exists():
            errors.append(f"{skill_dir.name}: SKILL.md missing")
            continue

        fm = _parse_frontmatter(entry)

        skill_name = fm.get("name", "").strip()
        if not skill_name:
            errors.append(f"{skill_dir.name}: frontmatter `name` is missing or empty")
        else:
            if skill_name in seen_names:
                errors.append(
                    f"duplicate skill name '{skill_name}' in dirs "
                    f"'{seen_names[skill_name]}' and '{skill_dir.name}'"
                )
            else:
                seen_names[skill_name] = skill_dir.name

        description = fm.get("description", "").strip()
        if not description:
            errors.append(f"{skill_dir.name}: frontmatter `description` is missing or empty")
        elif len(description) > SKILL_DESC_WARN_CHARS:
            warnings.append(
                f"{skill_dir.name}: description length {len(description)} > {SKILL_DESC_WARN_CHARS} chars"
            )

    found_names = set(seen_names.keys())
    missing = EXPECTED_SKILLS - found_names
    unexpected = found_names - EXPECTED_SKILLS
    if missing:
        errors.append(f"expected skills missing: {sorted(missing)}")
    if unexpected:
        errors.append(f"unexpected skill names (not in expected set): {sorted(unexpected)}")

    detail_parts = [f"{len(skill_dirs)} skill dirs scanned, {len(found_names)} valid names found"]
    if errors:
        detail_parts.extend(errors)
    detail = "; ".join(detail_parts)
    warn_str = "; ".join(warnings) if warnings else ""

    return Result(name, passed=len(errors) == 0, detail=detail, warning=warn_str)


# --------------------------------------------------------------------------- #
# Check 4 — Agents
# --------------------------------------------------------------------------- #

def check_agents(plugin_path: Path) -> Result:
    name = "agents-frontmatter"
    agents_dir = plugin_path / "agents"
    if not agents_dir.is_dir():
        return Result(name, False, detail=f"agents/ directory not found at {agents_dir}")

    errors: list[str] = []
    found_names: set[str] = set()

    for agent_name in sorted(EXPECTED_AGENTS):
        agent_file = agents_dir / f"{agent_name}.md"
        if not agent_file.exists():
            errors.append(f"{agent_name}.md: file missing")
            continue

        fm = _parse_frontmatter(agent_file)
        fm_name = fm.get("name", "").strip()
        fm_desc = fm.get("description", "").strip()

        if not fm_name:
            errors.append(f"{agent_name}.md: frontmatter `name` missing or empty")
        else:
            found_names.add(fm_name)

        if not fm_desc:
            errors.append(f"{agent_name}.md: frontmatter `description` missing or empty")

    # Check for unexpected agent files
    all_md = list(agents_dir.glob("*.md"))
    unexpected = [f.stem for f in all_md if f.stem not in EXPECTED_AGENTS]
    if unexpected:
        errors.append(f"unexpected agent files: {unexpected}")

    detail = (
        f"{len(EXPECTED_AGENTS)} expected agents; "
        f"{len(EXPECTED_AGENTS) - len(errors)} error-free"
    )
    if errors:
        detail = "; ".join([detail] + errors)

    return Result(name, passed=len(errors) == 0, detail=detail)


# --------------------------------------------------------------------------- #
# Check 5 — MCP URL
# --------------------------------------------------------------------------- #

def check_mcp_url(plugin_path: Path) -> Result:
    name = "mcp-url-exact-match"
    mcp_path = plugin_path / ".mcp.json"

    if not mcp_path.exists():
        return Result(name, False, detail=".mcp.json not found")

    try:
        mcp = json.loads(mcp_path.read_text(encoding="utf-8"))
    except Exception as e:
        return Result(name, False, detail=f".mcp.json parse error: {e}")

    server = mcp.get(EXPECTED_PLUGIN_NAME)
    if server is None:
        return Result(name, False, detail=f"key '{EXPECTED_PLUGIN_NAME}' not found in .mcp.json")

    actual_url = server.get("url", "")
    if actual_url == EXPECTED_MCP_URL:
        return Result(name, True, detail=f"url={actual_url}")
    else:
        return Result(name, False, detail=f"expected '{EXPECTED_MCP_URL}', got '{actual_url}'")


# --------------------------------------------------------------------------- #
# Check 6 — No absolute paths in config files
# --------------------------------------------------------------------------- #

def check_no_absolute_paths(plugin_path: Path, marketplace_root: Path) -> Result:
    name = "no-absolute-paths-in-config"
    config_files = [
        plugin_path / ".mcp.json",
        plugin_path / ".claude-plugin" / "plugin.json",
        marketplace_root / ".claude-plugin" / "marketplace.json",
    ]

    hits: list[str] = []
    for cfg_path in config_files:
        if not cfg_path.exists():
            continue
        text = cfg_path.read_text(encoding="utf-8")
        for pattern in _ABS_PATH_PATTERNS:
            if pattern.search(text):
                # Find the offending lines for context
                for i, line in enumerate(text.splitlines(), 1):
                    if pattern.search(line):
                        hits.append(f"{cfg_path.name} line {i}: {line.strip()[:120]}")

    if hits:
        return Result(name, False, detail="; ".join(hits))
    else:
        return Result(name, True, detail=f"{len(config_files)} config files checked, no absolute paths")


# --------------------------------------------------------------------------- #
# Public entry point
# --------------------------------------------------------------------------- #

def run_static_checks(plugin_path: Path, marketplace_root: Path) -> tuple[list[Result], bool]:
    """Run all Layer 1 checks. Returns (results, all_passed)."""
    results = [
        check_cli_validate(plugin_path),
        check_version_triple(plugin_path, marketplace_root),
        check_skills(plugin_path),
        check_agents(plugin_path),
        check_mcp_url(plugin_path),
        check_no_absolute_paths(plugin_path, marketplace_root),
    ]
    all_passed = all(r.passed for r in results)
    return results, all_passed
