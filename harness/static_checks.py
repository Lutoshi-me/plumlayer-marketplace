"""
static_checks.py — Layer 1: deterministic, no model calls.

Checks:
  1. `claude plugin validate <plugin_path> --strict` exits 0 (SKIP if the
     `claude` CLI is not on PATH).
  2. Version-quadruple lockstep across plugin.json (Claude), plugin.json
     (Codex), and marketplace.json (2 fields).
  3. Skills: no duplicate `name`; no missing/empty `description`; the shipped
     skill set matches EXPECTED_SKILLS exactly, in both directions.
  4. Description contract: every skill description is non-empty, folded YAML
     style (`description: >`), and at most DESC_MAX_CHARS characters.
  4b. Agents: every agents/*.md has frontmatter that actually parses as YAML
     and a non-empty `name` and `description`; the shipped agent set matches
     EXPECTED_AGENTS exactly, in both directions; and no agent declares a
     frontmatter field the runtime ignores for plugin-shipped agents
     (`hooks`, `mcpServers`, `permissionMode`). Checks 3 and 4b both validate
     the frontmatter block with PyYAML when it is importable, falling back to
     a stdlib check for the unquoted ": " failure when it is not.
  5. No banned string in shipped text: client-name denylist, `PLU-\\d+`,
     internal vault filenames, `MOSOT`, em dash, middle dot. Em dash and
     middle dot are exempt inside fenced code blocks and inline code spans
     (data, not prose); every other pattern applies to code too. Only the
     pinned trade-knowledge/ corpus files (read from MANIFEST.md's own
     Trade files list) get the client-name-only scan; MANIFEST.md itself and
     any other file in that directory get the full scan by default.
  6. Retired vocabulary regression guard: a curated list of names retired by
     the D6 vocabulary sweep (commit 8096333 and follow-ups) must not creep
     back in. Whole-file terms (e.g. `residue`, `roster`, `operator` as the
     name for the person) are banned everywhere in the full-scope files;
     scoped terms (e.g. `supersede`, `fan-out`, `census`) are legitimate
     agent-facing machinery and are banned only inside a
     `<!-- user-facing -->` span or an `Audience: user` artifact clause.
  7. Bold-for-emphasis on a short, high-precision denylist of ordinary words
     (`not`, `never`, `only`, ...) not immediately followed by a colon.
  8. Title-Case pseudo-heading lines (advisory only — reported as a WARN,
     never fails the release; see the check's own docstring for why).
  9. MCP-URL: .mcp.json `plumlayer` server url == EXPECTED_MCP_URL exactly.
  10. No absolute paths (Windows C:\\ or Unix /Users/ /home/) in .mcp.json,
      plugin.json (Claude), plugin.json (Codex), or marketplace.json.
  11. Question/failure boundary: no shipped skill or agent file tells the agent to raise a
      Question over a Plumlayer failure (a job that failed or timed out, an image-only or
      unresolved page, a retry), and every file that mentions `ask_question` / "raise a
      Question" at all carries the boundary sentence saying a Question is about the project,
      never about a Plumlayer failure.
  12. Ledger fixed shape: the runner definition's ledger grammar block still declares exactly
      three line kinds and the closed `note` kind set; every shipped file instructing an append
      to the ledger carries the prohibition sentence; and no prose-permitting cue sits near a
      ledger mention with no prohibition cue in range.
  13. Runner mode set: the `##` headings of agents/scope-round-runner.md match
      EXPECTED_RUNNER_MODE_HEADINGS exactly, in both directions, so the per-pass shape cannot be
      partly undone without failing the release.
  14. Plan inventory: the shipped scripts/plan_inventory.py, imported in-process and run end to
      end over invented fixtures, produces counts that agree with a tally this file computes
      itself, unit lines whose page references match the fixture's own sheet-to-page map, a
      window 1 selection matching an independent tally of the vocabulary sheet types plus the
      include and minus the exclude, window 2's overlap and unread counts matching its own unit
      lines, the balanced split of a pass over twelve units, every declared seam among the trades
      planned either adjacent or named on the bounds line as a group no order can satisfy (checked
      over the fixture and again over all of the shipped map's pairs), no pass claiming a seam its
      own order contradicts, a window 3 that is exactly the inventory minus window 2's own unit
      lines, every partial input named on the bounds line rather than folded into a clean number,
      and a one-line refusal naming what is missing for each of eleven broken invocations. The
      shipped scripts are compiled from source here rather than imported through the loader, so a
      script edited twice inside one second to the same byte length can never be checked as its
      earlier bytecode.
  15. No shipped skill or agent file names `fork` as a subagent type, in either the
      `subagent_type:` dispatch-line shape or a `tools: Agent(fork)` frontmatter declaration.
  16. Every shipped skill or agent file that names `ask_question` or tells the agent to raise a
      Question carries the fixed phrase "Question text is plain estimator words", either stating
      the rule in full or pointing at it (docs/plugin-text-style.md §1, `learn-project`'s
      judgment-entry table).
  17. Trade sheet map: trade-knowledge/trade-sheets.json covers every trade file the manifest
      lists and names no trade file it does not, in both directions, with a named exception list
      the only allowance; its pinned sheet type list equals the recognizer's twelve deterministic
      types; every family names a discipline or a pattern and only pinned sheet types; and every
      seam pair names two different trades the map itself holds. A trade file is general to its
      family, so the shared resolver is checked against the shipped map on five catalog codes: a
      child code, a code whose only mapped ancestor is its division, a code under two mapped
      ancestors where the nearer must win, a code the map keys outright, and a division the map
      covers at no level.

Grounding role: reads files and shells out to the claude CLI. No inference.
"""

from __future__ import annotations

import contextlib
import fnmatch
import importlib.util
import io
import json
import math
import re
import string
import subprocess
import sys
from pathlib import Path

# --------------------------------------------------------------------------- #
# Constants
# --------------------------------------------------------------------------- #

EXPECTED_PLUGIN_NAME = "plumlayer"
EXPECTED_MCP_URL = "https://api-production-0a7b.up.railway.app/mcp"

EXPECTED_SKILLS = {
    "bid-intake",
    "drawing-set-assemble",
    "drawing-upload",
    "learn-project",
    "project-record",
    "project-setup",
    "scope-run",
    "setup",
    "takeoff",
}

# The agent definitions the plugin ships under agents/. Both are dispatched by
# the scope run: the lead starts one round runner per round, and the runner
# starts one reader per read unit.
EXPECTED_AGENTS = {
    "scope-reader",
    "scope-round-runner",
}

# Frontmatter fields the runtime ignores for plugin-shipped agents. Declaring
# one is not a load error, which is exactly why it needs catching here: it
# reads as configured behavior and silently isn't.
AGENT_UNSUPPORTED_FIELDS = ("hooks", "mcpServers", "permissionMode")

# Hard ceiling on a skill's frontmatter description length (chars). Above
# this is a FAIL, not a warning — docs/plugin-text-style.md §2.
DESC_MAX_CHARS = 600

# Client / project names that must never appear in shipped text. Add new
# names here as they turn up — matching is case-insensitive and whole-string,
# not word-bounded, so partials inside longer strings still hit.
BANNED_CLIENT_NAMES = [
    "150 Main",
    "31 Milk",
    "248 Dorchester",
    "South Shore",
]

# Internal vault filenames that live in a repo the plugin's user does not have.
BANNED_VAULT_FILENAMES = [
    "scope-package-architecture.md",
    "agent-driven-ingestion.md",
    "drawing-set-intake-design.md",
    "package-identity-design.md",
]

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
    def __init__(self, name: str, passed: bool, detail: str = "", warning: str = "", skipped: bool = False):
        self.name = name
        self.passed = passed
        self.detail = detail
        self.warning = warning
        self.skipped = skipped

    def __repr__(self) -> str:
        if self.skipped:
            status = "SKIP"
        else:
            status = "PASS" if self.passed else "FAIL"
        s = f"  [{status}] {self.name}"
        if self.detail:
            s += f"\n         {self.detail}"
        if self.warning:
            s += f"\n         WARN: {self.warning}"
        return s


# --------------------------------------------------------------------------- #
# Frontmatter parser
# --------------------------------------------------------------------------- #
#
# PyYAML is used when it is importable, because only a real parser catches the
# whole class of malformed frontmatter (the live example: an unquoted ": "
# inside a plain scalar, which makes the block invalid YAML while looking
# perfectly fine to a regex). harness/requirements.txt is stdlib-only, so the
# import is optional and a hand-rolled fallback covers the same failure the
# strict way when PyYAML is absent.

try:  # optional; the fallback below covers the stdlib-only case
    import yaml as _yaml
except ImportError:  # pragma: no cover - depends on the environment
    _yaml = None


def _frontmatter_block(path: Path) -> str | None:
    """
    Return the raw text between the opening '---' on line 1 and the next '---'.

    Line 1 IS the opening delimiter: the next '---' closes the block and
    everything after it is body. Getting this wrong (treating the closing
    delimiter as the opener) silently scans the body for `key: value` lines,
    which is how body text can overwrite a real frontmatter field.
    """
    lines = path.read_text(encoding="utf-8").splitlines()
    if not lines or lines[0].strip() != "---":
        return None
    for i, line in enumerate(lines[1:], start=1):
        if line.strip() == "---":
            return "\n".join(lines[1:i])
    return None  # unterminated block is no block


def _frontmatter_errors(path: Path) -> list[str]:
    """
    Report what makes a frontmatter block unusable, in the terms the runtime
    would see. With PyYAML present this is the parser's own verdict. Without
    it, the fallback enforces the one failure mode that has actually bitten
    this repo: an unquoted ": " inside a plain scalar value.
    """
    block = _frontmatter_block(path)
    if block is None:
        return ["no frontmatter block (missing or unterminated '---' delimiters)"]

    if _yaml is not None:
        try:
            data = _yaml.safe_load(block)
        except Exception as e:  # yaml.YAMLError and anything it wraps
            first = str(e).splitlines()[0].strip()
            return [f"frontmatter is not valid YAML: {first}"]
        if data is not None and not isinstance(data, dict):
            return [f"frontmatter parses as {type(data).__name__}, not a mapping"]
        return []

    errors: list[str] = []
    for raw in block.splitlines():
        m = re.match(r'^(\w[\w-]*):\s*(.*)$', raw)
        if not m:
            continue
        val = m.group(2).strip()
        if not val or val[0] in "\"'>|[{&*#":
            continue  # quoted, block scalar, or a collection: not a plain scalar
        if ": " in val or val.endswith(":"):
            errors.append(
                f"`{m.group(1)}` value contains an unquoted ': ', which is not valid "
                f"YAML (quote the value or reword it)"
            )
    return errors


def _parse_frontmatter(path: Path) -> dict[str, str]:
    """
    Parse YAML frontmatter delimited by '---' lines into key -> value strings.

    With PyYAML present, block scalars (e.g. `description: >`) come back as
    their folded text; without it they come back as the bare indicator (">").
    Either way `_extract_description` remains the authority on description
    text. Returns {} when there is no parseable frontmatter block.
    """
    block = _frontmatter_block(path)
    if block is None:
        return {}

    if _yaml is not None:
        try:
            data = _yaml.safe_load(block)
        except Exception:
            data = None  # malformed: _frontmatter_errors reports it
        if isinstance(data, dict):
            return {str(k): ("" if v is None else str(v)) for k, v in data.items()}
        return {}

    fields: dict[str, str] = {}
    for line in block.splitlines():
        m = re.match(r'^(\w[\w-]*):\s*(.*)', line)
        if m:
            key = m.group(1)
            val = m.group(2).strip()
            if (val.startswith('"') and val.endswith('"')) or \
               (val.startswith("'") and val.endswith("'")):
                val = val[1:-1]
            fields[key] = val
    return fields


def _extract_description(path: Path) -> dict:
    """
    Parse the frontmatter `description` field specifically, handling the
    YAML folded block-scalar style (`description: >`). Returns:
      style: "folded" | "inline" | "missing"
      exact_indicator: True if the source line is exactly "description: >"
      text: the folded/joined description text (for char counting)
    """
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return {"style": "missing", "exact_indicator": False, "text": ""}

    end_idx = None
    for i in range(1, len(lines)):
        if lines[i].strip() == "---":
            end_idx = i
            break
    if end_idx is None:
        return {"style": "missing", "exact_indicator": False, "text": ""}
    fm_lines = lines[1:end_idx]

    desc_idx = None
    desc_val = ""
    for i, line in enumerate(fm_lines):
        m = re.match(r'^description:\s*(.*)$', line)
        if m:
            desc_idx = i
            desc_val = m.group(1).strip()
            break
    if desc_idx is None:
        return {"style": "missing", "exact_indicator": False, "text": ""}

    if desc_val.startswith(">"):
        block_lines: list[str] = []
        for line in fm_lines[desc_idx + 1:]:
            if line.strip() == "":
                block_lines.append("")
                continue
            if re.match(r'^\S', line):  # dedent = next top-level key, block ends
                break
            block_lines.append(line.strip())

        paragraphs: list[str] = []
        para: list[str] = []
        for l in block_lines:
            if l == "":
                if para:
                    paragraphs.append(" ".join(para))
                    para = []
            else:
                para.append(l)
        if para:
            paragraphs.append(" ".join(para))
        folded_text = "\n".join(paragraphs)
        return {"style": "folded", "exact_indicator": desc_val == ">", "text": folded_text}

    if desc_val:
        val = desc_val
        if (val.startswith('"') and val.endswith('"')) or \
           (val.startswith("'") and val.endswith("'")):
            val = val[1:-1]
        return {"style": "inline", "exact_indicator": False, "text": val}

    return {"style": "missing", "exact_indicator": False, "text": ""}


# --------------------------------------------------------------------------- #
# Check — CLI validate
# --------------------------------------------------------------------------- #

def check_cli_validate(plugin_path: Path) -> Result:
    name = "cli-validate (claude plugin validate --strict)"
    try:
        r = subprocess.run(
            ["claude", "plugin", "validate", str(plugin_path), "--strict"],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=30,
        )
    except FileNotFoundError:
        return Result(name, True, detail="`claude` not found on PATH — check skipped", skipped=True)
    except subprocess.TimeoutExpired:
        return Result(name, False, detail="timed out after 30s")

    stdout = r.stdout or ""
    stderr = r.stderr or ""
    output = (stdout + stderr).strip()
    if r.returncode == 0:
        return Result(name, True, detail=output)
    else:
        return Result(name, False, detail=f"exit {r.returncode}: {output}")


# --------------------------------------------------------------------------- #
# Check — Version-quadruple lockstep
# --------------------------------------------------------------------------- #

def check_version_quadruple(plugin_path: Path, marketplace_root: Path) -> Result:
    name = "version-quadruple-lockstep"
    plugin_json_path = plugin_path / ".claude-plugin" / "plugin.json"
    codex_plugin_json_path = plugin_path / ".codex-plugin" / "plugin.json"
    marketplace_json_path = marketplace_root / ".claude-plugin" / "marketplace.json"

    errors: list[str] = []
    versions: dict[str, str] = {}

    try:
        pj = json.loads(plugin_json_path.read_text(encoding="utf-8"))
        versions["plugin.json[version]"] = pj.get("version", "<missing>")
    except Exception as e:
        errors.append(f"plugin.json read error: {e}")

    try:
        cpj = json.loads(codex_plugin_json_path.read_text(encoding="utf-8"))
        versions[".codex-plugin/plugin.json[version]"] = cpj.get("version", "<missing>")
    except Exception as e:
        errors.append(f".codex-plugin/plugin.json read error: {e}")

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
# Check — Skills
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
    seen_names: dict[str, str] = {}  # skill_name -> dir name

    for skill_dir in sorted(skill_dirs):
        entry = skill_dir / "SKILL.md"
        if not entry.exists():
            errors.append(f"{skill_dir.name}: SKILL.md missing")
            continue

        for problem in _frontmatter_errors(entry):
            errors.append(f"{skill_dir.name}: {problem}")

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

        if not fm.get("description", "").strip():
            errors.append(f"{skill_dir.name}: frontmatter `description` is missing or empty")

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

    return Result(name, passed=len(errors) == 0, detail=detail)


# --------------------------------------------------------------------------- #
# Check — Agents
# --------------------------------------------------------------------------- #

def check_agents(plugin_path: Path) -> Result:
    """
    The plugin ships agent definitions under agents/ at the plugin root (the
    location the runtime reads them from). This check proves the shipped set
    is exactly EXPECTED_AGENTS, that each file carries a usable `name` and
    `description`, and that none declares a field the runtime ignores for
    plugin-shipped agents.
    """
    name = "agents-frontmatter"
    agents_dir = plugin_path / "agents"
    if not agents_dir.is_dir():
        return Result(name, False, detail=f"agents/ directory not found at {agents_dir}")

    agent_files = sorted(agents_dir.rglob("*.md"))
    if not agent_files:
        return Result(name, False, detail="no agent definitions found in agents/")

    errors: list[str] = []
    seen_names: dict[str, str] = {}  # agent name -> file name

    for agent_file in agent_files:
        for problem in _frontmatter_errors(agent_file):
            errors.append(f"{agent_file.name}: {problem}")

        fm = _parse_frontmatter(agent_file)

        agent_name = fm.get("name", "").strip()
        if not agent_name:
            errors.append(f"{agent_file.name}: frontmatter `name` is missing or empty")
        elif agent_name in seen_names:
            errors.append(
                f"duplicate agent name '{agent_name}' in files "
                f"'{seen_names[agent_name]}' and '{agent_file.name}'"
            )
        else:
            seen_names[agent_name] = agent_file.name

        if not fm.get("description", "").strip():
            errors.append(f"{agent_file.name}: frontmatter `description` is missing or empty")

        for field in AGENT_UNSUPPORTED_FIELDS:
            if field in fm:
                errors.append(
                    f"{agent_file.name}: declares `{field}`, which the runtime ignores "
                    f"for plugin-shipped agents"
                )

    found_names = set(seen_names.keys())
    missing = EXPECTED_AGENTS - found_names
    unexpected = found_names - EXPECTED_AGENTS
    if missing:
        errors.append(f"expected agents missing: {sorted(missing)}")
    if unexpected:
        errors.append(f"unexpected agent names (not in expected set): {sorted(unexpected)}")

    detail_parts = [f"{len(agent_files)} agent files scanned, {len(found_names)} valid names found"]
    if errors:
        detail_parts.extend(errors)

    return Result(name, passed=len(errors) == 0, detail="; ".join(detail_parts))


# --------------------------------------------------------------------------- #
# Check — Description contract
# --------------------------------------------------------------------------- #

def check_description_contract(plugin_path: Path) -> Result:
    name = "description-contract"
    skills_dir = plugin_path / "skills"
    if not skills_dir.is_dir():
        return Result(name, False, detail=f"skills/ directory not found at {skills_dir}")

    skill_dirs = sorted(d for d in skills_dir.iterdir() if d.is_dir())
    counts: list[str] = []
    errors: list[str] = []

    for skill_dir in skill_dirs:
        entry = skill_dir / "SKILL.md"
        if not entry.exists():
            continue  # already reported by check_skills

        info = _extract_description(entry)
        style = info["style"]
        char_count = len(info["text"])
        counts.append(f"{skill_dir.name}={char_count} chars")

        if style == "missing" or not info["text"].strip():
            errors.append(f"{skill_dir.name}: description missing or empty")
            continue
        if not (style == "folded" and info["exact_indicator"]):
            errors.append(
                f"{skill_dir.name}: description is not folded YAML style "
                f"(expected the frontmatter line to be exactly 'description: >')"
            )
        if char_count > DESC_MAX_CHARS:
            errors.append(f"{skill_dir.name}: description length {char_count} > {DESC_MAX_CHARS} chars")

    detail = ", ".join(counts)
    if errors:
        detail += " | " + "; ".join(errors)

    return Result(name, passed=len(errors) == 0, detail=detail)


# --------------------------------------------------------------------------- #
# Check — Banned strings in shipped text
# --------------------------------------------------------------------------- #

# Inline code span: single backtick-delimited, no newline inside.
_INLINE_CODE_RE = re.compile(r"`[^`\n]*`")


def _build_banned_patterns(client_names_only: bool) -> list[tuple[str, re.Pattern, bool]]:
    """Return (label, pattern, code_exempt) triples. code_exempt marks the two
    patterns (em dash, middle dot) that are data, not prose, inside fenced
    code blocks and inline code spans — docs/plugin-text-style.md §4. Every
    other pattern (confidentiality, ticket IDs, vault filenames, MOSOT) stays
    whole-file, code included, and must never be marked code_exempt."""
    patterns: list[tuple[str, re.Pattern, bool]] = [
        (f"client name '{n}'", re.compile(re.escape(n), re.IGNORECASE), False)
        for n in BANNED_CLIENT_NAMES
    ]
    if client_names_only:
        return patterns

    patterns.append(("internal ticket ID", re.compile(r"PLU-\d+"), False))
    for fname in BANNED_VAULT_FILENAMES:
        patterns.append((f"internal vault filename '{fname}'", re.compile(re.escape(fname)), False))
    patterns.append(("'MOSOT' as user-facing vocabulary", re.compile(r"\bMOSOT\b", re.IGNORECASE), False))
    patterns.append(("em dash", re.compile(r"—"), True))
    patterns.append(("middle dot", re.compile(r"·"), True))
    return patterns


def _fenced_code_line_mask(lines: list[str]) -> list[bool]:
    """Return a list parallel to `lines`: True if that line is a fenced
    code-block delimiter or falls inside one (``` ... ```)."""
    in_fence = False
    mask: list[bool] = []
    for line in lines:
        is_fence_delim = line.strip().startswith("```")
        if is_fence_delim:
            mask.append(True)  # the delimiter line itself counts as code
            in_fence = not in_fence
        else:
            mask.append(in_fence)
    return mask


def _mask_inline_code(line: str) -> str:
    """Blank out inline code spans (single backtick-delimited), preserving
    line length, so code-exempt patterns never match their contents while
    everything else on the line is still scanned normally."""
    return _INLINE_CODE_RE.sub(lambda m: " " * len(m.group(0)), line)


def _scan_file_for_banned(path: Path, client_names_only: bool) -> list[str]:
    hits: list[str] = []
    try:
        text = path.read_text(encoding="utf-8")
    except Exception as e:
        return [f"{path}: read error: {e}"]

    lines = text.splitlines()
    fence_mask = _fenced_code_line_mask(lines)
    patterns = _build_banned_patterns(client_names_only)

    for i, line in enumerate(lines, 1):
        in_fence = fence_mask[i - 1]
        for label, pattern, code_exempt in patterns:
            if code_exempt:
                if in_fence:
                    continue  # whole line is fenced code — data, not prose
                scan_line = _mask_inline_code(line)
            else:
                # Confidentiality / ticket-ID / vault-filename / MOSOT bans
                # apply whole-file, code included — never masked.
                scan_line = line
            m = pattern.search(scan_line)
            if m:
                hits.append(f"{path.name}:{i}: {label} — {m.group(0)!r} in: {line.strip()[:160]}")
    return hits


def _pinned_trade_package_names(trade_knowledge_dir: Path) -> set[str] | None:
    """
    The pinned, corpus-derived trade files (currently 44) are deliberately
    out of scope for style and get the client-name-only scan. Everything else
    in trade-knowledge/ — MANIFEST.md, and any future hand-authored file
    dropped in beside the trade files — is ordinary shipped prose in the
    plugin's own voice and must get the full scan by default.

    Rather than hardcoding the file list (or hardcoding "MANIFEST.md" as a
    one-off exception, which would leave the same hole for the next
    hand-authored file), this reads the trade file names from MANIFEST.md's
    own "## Trade files" section — that list is already the authoritative
    record of what the pinned corpus contains, and a corpus update that adds
    or drops a trade updates this scope automatically as long as the
    manifest itself stays accurate. A file whose stem isn't in that list
    defaults to the full scan, covered by default rather than by someone
    remembering to list it.

    Returns None if MANIFEST.md or its Trade files list can't be parsed — the
    caller must then fail safe (treat every file as full scope) rather than
    guess which files are pinned.
    """
    manifest_path = trade_knowledge_dir / "MANIFEST.md"
    if not manifest_path.exists():
        return None
    try:
        lines = manifest_path.read_text(encoding="utf-8").splitlines()
    except Exception:
        return None

    heading_idx = None
    for i, line in enumerate(lines):
        if line.strip() == "## Trade files":
            heading_idx = i
            break
    if heading_idx is None:
        return None

    # The trade files are a comma-separated prose list starting right after
    # the heading (skipping the blank line that follows it) and ending at
    # the next blank line or heading.
    entry_lines: list[str] = []
    started = False
    for line in lines[heading_idx + 1:]:
        if line.strip() == "":
            if started:
                break
            continue
        if line.startswith("#"):
            break
        entry_lines.append(line.strip())
        started = True
    if not entry_lines:
        return None

    names = {n.strip() for n in " ".join(entry_lines).split(",") if n.strip()}
    return names if names else None


def _collect_scope_files(
    plugin_path: Path, marketplace_root: Path
) -> tuple[list[Path], list[Path], str | None]:
    """
    Shared file-scope collection for every text-content check (banned
    strings, retired vocabulary, bold/Title-Case). Returns
    (full_scope_files, client_only_files, warning):

    - full_scope_files: every shipped-skill .md, every agents/ .md, every
      scripts/ .py, README.md, the manifest JSON files, and any
      trade-knowledge/ file that is NOT one of the pinned corpus files
      (e.g. MANIFEST.md itself) — this is the plugin's own prose, in its
      own voice, and gets the strictest scan.
    - client_only_files: the pinned, corpus-derived trade files (currently
      44), which get a lighter client-name-only scan elsewhere — ordinary
      trade vocabulary there (e.g. "deposit", "proposed") is real and
      expected, not a style violation.
    - warning: set when trade-knowledge/MANIFEST.md's own Trade files list
      couldn't be parsed, in which case every trade-knowledge file was
      folded into full_scope_files as the fail-safe default (never silently
      guessed into the lenient scan).
    """
    full_scope_files: list[Path] = []
    skills_dir = plugin_path / "skills"
    if skills_dir.is_dir():
        full_scope_files.extend(sorted(skills_dir.rglob("*.md")))

    # Agent definitions are shipped text in the plugin's own voice, and a
    # dispatched agent reads them as its whole system prompt, so they get the
    # same scan a skill body does.
    agents_dir = plugin_path / "agents"
    if agents_dir.is_dir():
        full_scope_files.extend(sorted(agents_dir.rglob("*.md")))

    # A shipped script's own prose (its module docstring, its stdout line, its error messages) is
    # text in the plugin's voice too, and it reaches a user when a run reports what a script said,
    # so it joins the scan rather than sitting outside every text check.
    scripts_dir = plugin_path / "scripts"
    if scripts_dir.is_dir():
        full_scope_files.extend(sorted(scripts_dir.rglob("*.py")))

    readme = marketplace_root / "README.md"
    if readme.exists():
        full_scope_files.append(readme)

    manifest_files = [
        plugin_path / ".claude-plugin" / "plugin.json",
        marketplace_root / ".claude-plugin" / "marketplace.json",
        plugin_path / ".codex-plugin" / "plugin.json",
        marketplace_root / ".agents" / "plugins" / "marketplace.json",
    ]
    full_scope_files.extend(f for f in manifest_files if f.exists())

    # The trade to sheet family map is hand-authored prose in the plugin's own voice (its `note`
    # fields reach a run's output), and the .md glob below never reaches a .json, so it is named
    # here rather than left outside every text check.
    trade_sheets = plugin_path / "trade-knowledge" / "trade-sheets.json"
    if trade_sheets.exists():
        full_scope_files.append(trade_sheets)

    client_only_files: list[Path] = []
    trade_knowledge_dir = plugin_path / "trade-knowledge"
    pinned_names: set[str] | None = None
    warning: str | None = None
    if trade_knowledge_dir.is_dir():
        pinned_names = _pinned_trade_package_names(trade_knowledge_dir)
        for f in sorted(trade_knowledge_dir.rglob("*.md")):
            # Fail safe: if the pinned trade files list couldn't be parsed,
            # every trade-knowledge file goes to the full scan rather than
            # being guessed into the lenient one.
            if pinned_names is not None and f.stem in pinned_names:
                client_only_files.append(f)
            else:
                full_scope_files.append(f)
        if pinned_names is None:
            warning = (
                "could not parse trade-knowledge/MANIFEST.md's Trade files list, "
                "so every trade-knowledge file was scanned at full strictness as a safe default"
            )

    return full_scope_files, client_only_files, warning


def check_banned_strings(plugin_path: Path, marketplace_root: Path) -> Result:
    name = "banned-strings"

    full_scope_files, client_only_files, warning = _collect_scope_files(plugin_path, marketplace_root)

    hits: list[str] = []
    for f in full_scope_files:
        hits.extend(_scan_file_for_banned(f, client_names_only=False))
    for f in client_only_files:
        hits.extend(_scan_file_for_banned(f, client_names_only=True))

    detail = (
        f"{len(full_scope_files)} files under full banned-set scan, "
        f"{len(client_only_files)} pinned trade files under client-name-only scan"
    )
    if warning:
        detail += f" | WARNING: {warning}"
    if hits:
        detail += " | " + "; ".join(hits)

    return Result(name, passed=len(hits) == 0, detail=detail)


# --------------------------------------------------------------------------- #
# Check — Retired vocabulary regression guard (PLU-1346)
# --------------------------------------------------------------------------- #
#
# The estimator-block enumeration and its byte-identical harness check were
# deleted entirely (commit 8096333, "Rewrite scope-run vocabulary; delete the
# estimator block everywhere") in favor of doctrine D6 (Luke): don't ban a
# word and demand a live replacement — give every concept one settled name,
# used identically on both sides of the user/agent boundary. This check does
# NOT reintroduce that deleted mechanism. It is narrower and different in
# kind: a regression guard for the SPECIFIC old names that D6's sweep (and
# its follow-up commits) actually retired, so a stale name can't quietly
# creep back into new text. It is not a live style enforcement layer and it
# is not meant to grow into one.
#
# Two scopes, matching docs/plugin-text-style.md §1's two-audience split:
#
#   - RETIRED_WHOLE_FILE_TERMS never appear anywhere in a full-scope file
#     (the same `full_scope_files` set `check_banned_strings` already scans —
#     shipped skills, README, manifests; NOT the pinned trade-knowledge
#     corpus, where ordinary English collides with several of these names —
#     see the false-positive notes below).
#   - RETIRED_SCOPED_TERMS are legitimate agent-facing machinery vocabulary
#     everywhere else in a skill file; they are banned only where the file
#     itself declares the text user-facing: inside a
#     `<!-- user-facing --> ... <!-- /user-facing -->` span, or inside an
#     `Audience: user` artifact clause.
#
# Deliberately NOT included, even though each term appears in the source
# vocabulary work that motivated this issue, because each is ordinary
# English or real, current construction-industry vocabulary and would make
# this check noisy enough to get waived (this issue's own stated risk):
#
#   stage      - skills use "Stage 1/2/3" as their own structural headers
#   door       - sign-off doors (real doctrine term) + a literal takeoff/sheet item
#   edge       - "Edge of Slab" (E.O.S.) is a real, current sheet type
#   slot, receipt, ledger, reader, engine
#   packet     - "submittal packet" is real, current trade vocabulary
#   dispatch   - bare word; "dispatch a crew to the site" is real construction usage
#   governing  - "governing code" / "governing authority" is real construction vocabulary
#   promote, reconcile - "index reconciliation" is a real, CURRENTLY SHIPPED
#                        feature (reconcile_index / reconcile_set are live MCP
#                        verbs) — banning "reconcile" would false-positive on
#                        real product vocabulary
#   QA, grounding - electrical grounding is real trade vocabulary
#   projection, drift, backstop, wave, bundle
#
# Deviation from the issue brief: "trust class" is NOT whole-file banned.
# It is live, current, agent-facing machinery vocabulary —
# docs/plugin-text-style.md §1 itself names it as a load-bearing example of
# what should NOT be de-jargoned ("claim, predicate, trust class,
# supersede"), and plugins/plumlayer/skills/project-record/SKILL.md uses it
# correctly and currently. Only the trust-class VALUE "proposed" was
# retired (renamed to "recorded", commit 92e8243) — the field/concept name
# itself was never deleted. A whole-file ban on the phrase would fail the
# harness on real, correct, current text. It is instead added to
# RETIRED_SCOPED_TERMS below: the user should never read "trust class" (this
# repo's own estimator-words rule), but the agent legitimately reads and
# writes it.

RETIRED_WHOLE_FILE_TERMS: list[tuple[str, re.Pattern, bool]] = [
    (
        "'residue' as the retired open-items concept (renamed to 'open items')",
        re.compile(r"\bresidue\b", re.IGNORECASE),
        False,
    ),
    ("'entry-silent' (deleted concept)", re.compile(r"\bentry-silent\b", re.IGNORECASE), False),
    ("'unspecced' (deleted concept)", re.compile(r"\bunspecced\b", re.IGNORECASE), False),
    ("'review-status' (deleted feature)", re.compile(r"\breview-status\b", re.IGNORECASE), False),
    ("'bid response(s)' (renamed to 'bid records')", re.compile(r"\bbid responses?\b", re.IGNORECASE), False),
    ("'model tier' (deleted from user narration)", re.compile(r"\bmodel tiers?\b", re.IGNORECASE), False),
    ("'off-checklist' (renamed to 'unlisted scope items')", re.compile(r"\boff-checklist\b", re.IGNORECASE), False),
    (
        "'read-back' (renamed to 'verification'; the unhyphenated verb phrase "
        "'read back' is ordinary English and is not matched)",
        re.compile(r"\bread-back\b", re.IGNORECASE),
        False,
    ),
    ("'silent-row' (renamed to 'not addressed')", re.compile(r"\bsilent-row\b", re.IGNORECASE), False),
    ("'roster' (renamed to 'list')", re.compile(r"\broster\b", re.IGNORECASE), False),
    ("'checkpoint' (renamed to 'check-in')", re.compile(r"\bcheckpoint\b", re.IGNORECASE), False),
    ("'mint'/'minting' (renamed to 'create')", re.compile(r"\bmint(?:ing|s|ed)?\b", re.IGNORECASE), False),
    ("'enrich'/'enriching' (renamed to 'update')", re.compile(r"\benrich(?:ing|es|ed)?\b", re.IGNORECASE), False),
    (
        "'operator' as the retired name for the person (renamed to 'user', PLU-1361; "
        "the literal `operator.json` filename and the JSON key \"operator\" are real, "
        "current identifiers and are exempt)",
        re.compile(r'(?<!")\boperator\b(?!\.json)(?!")', re.IGNORECASE),
        False,
    ),
    ("'schedule entries' (renamed to 'schedule rows')", re.compile(r"\bschedule entries\b", re.IGNORECASE), False),
    ("'proposed' as the retired trust-class posture (renamed to 'recorded')", re.compile(r"\bproposed\b", re.IGNORECASE), False),
    ("'deposit' (renamed to 'record' as a verb)", re.compile(r"\bdeposit(?:s|ing|ed)?\b", re.IGNORECASE), False),
    ("'trade-packages' (directory renamed to 'trade-knowledge')", re.compile(r"\btrade-packages\b", re.IGNORECASE), False),
    # Token cost vocabulary retired (cost is measured outside the plugin, from
    # harness transcripts, never narrated by a skill; PLU-1345).
    (
        "token cost vocabulary (cost is measured outside the plugin)",
        re.compile(r"\btoken (cost|totals?|usage|budget)s?\b", re.IGNORECASE),
        False,
    ),
]

RETIRED_SCOPED_TERMS: list[tuple[str, re.Pattern]] = [
    ("'anti-join'", re.compile(r"\banti-join\b", re.IGNORECASE)),
    ("'context-packet'", re.compile(r"\bcontext-packet\b", re.IGNORECASE)),
    ("'fan-out'", re.compile(r"\bfan-out\b", re.IGNORECASE)),
    ("'idempotency'", re.compile(r"\bidempotency\b", re.IGNORECASE)),
    ("'content-keyed'", re.compile(r"\bcontent-keyed\b", re.IGNORECASE)),
    ("'content-disjoint'", re.compile(r"\bcontent-disjoint\b", re.IGNORECASE)),
    ("'supersede'/'supersession'", re.compile(r"\bsupersede[sd]?\b|\bsupersession\b", re.IGNORECASE)),
    ("'convention lines'", re.compile(r"\bconvention lines?\b", re.IGNORECASE)),
    ("'closure loop'", re.compile(r"\bclosure loop\b", re.IGNORECASE)),
    ("'grain bracket'", re.compile(r"\bgrain bracket\b", re.IGNORECASE)),
    ("'census'", re.compile(r"\bcensus\b", re.IGNORECASE)),
    ("'grain'", re.compile(r"\bgrain\b", re.IGNORECASE)),
    ("'trust class'", re.compile(r"\btrust class\b", re.IGNORECASE)),
]


def _user_facing_span_mask(lines: list[str]) -> list[bool]:
    """
    Lines strictly between a `<!-- user-facing -->` / `<!-- /user-facing -->`
    marker pair. The marker lines themselves are not included (they carry no
    banned vocabulary of their own). Markers must be exact and each on its
    own line, per docs/plugin-text-style.md §1 — the same contract the
    markers themselves promise.
    """
    mask: list[bool] = []
    in_span = False
    for line in lines:
        stripped = line.strip()
        if stripped == "<!-- user-facing -->":
            in_span = True
            mask.append(False)
            continue
        if stripped == "<!-- /user-facing -->":
            in_span = False
            mask.append(False)
            continue
        mask.append(in_span)
    return mask


_AUDIENCE_USER_RE = re.compile(r"Audience:\s*user\b")
_LIST_ITEM_START_RE = re.compile(r"^\s*(?:[-*+]|\d+\.)\s")


def _audience_user_clause_mask(lines: list[str]) -> list[bool]:
    """
    Lines that are part of an `Audience: user` artifact clause: the line
    declaring it, plus any continuation lines of the same list item (e.g. a
    bullet's wrapped second line), stopping at the next blank line, the next
    top-level list item, or a heading. docs/plugin-text-style.md §1 writes
    these clauses inline in prose (e.g. "... Audience: user, it is shown to
    the user for approval."), not inside `<!-- user-facing -->` markers, so
    they need their own scan.
    """
    mask = [False] * len(lines)
    i = 0
    while i < len(lines):
        if _AUDIENCE_USER_RE.search(lines[i]):
            mask[i] = True
            j = i + 1
            while j < len(lines):
                stripped = lines[j].strip()
                if not stripped or _LIST_ITEM_START_RE.match(lines[j]) or stripped.startswith("#"):
                    break
                mask[j] = True
                j += 1
            i = j
        else:
            i += 1
    return mask


def _scan_file_for_retired_whole_file(path: Path) -> list[str]:
    hits: list[str] = []
    try:
        text = path.read_text(encoding="utf-8")
    except Exception as e:
        return [f"{path}: read error: {e}"]

    lines = text.splitlines()
    fence_mask = _fenced_code_line_mask(lines)

    for i, line in enumerate(lines, 1):
        in_fence = fence_mask[i - 1]
        for label, pattern, code_exempt in RETIRED_WHOLE_FILE_TERMS:
            if code_exempt:
                if in_fence:
                    continue
                scan_line = _mask_inline_code(line)
            else:
                scan_line = line
            m = pattern.search(scan_line)
            if m:
                hits.append(f"{path.name}:{i}: retired term {label} — {m.group(0)!r} in: {line.strip()[:160]}")
    return hits


def _scan_file_for_retired_scoped(path: Path) -> list[str]:
    hits: list[str] = []
    try:
        text = path.read_text(encoding="utf-8")
    except Exception as e:
        return [f"{path}: read error: {e}"]

    lines = text.splitlines()
    uf_mask = _user_facing_span_mask(lines)
    aud_mask = _audience_user_clause_mask(lines)

    for i, line in enumerate(lines, 1):
        if not (uf_mask[i - 1] or aud_mask[i - 1]):
            continue
        for label, pattern in RETIRED_SCOPED_TERMS:
            m = pattern.search(line)
            if m:
                hits.append(
                    f"{path.name}:{i}: agent-facing machinery term {label} used in user-facing text "
                    f"— {m.group(0)!r} in: {line.strip()[:160]}"
                )
    return hits


def check_retired_vocabulary(plugin_path: Path, marketplace_root: Path) -> Result:
    name = "retired-vocabulary"
    full_scope_files, _client_only_files, warning = _collect_scope_files(plugin_path, marketplace_root)

    hits: list[str] = []
    for f in full_scope_files:
        hits.extend(_scan_file_for_retired_whole_file(f))
        hits.extend(_scan_file_for_retired_scoped(f))

    detail = f"{len(full_scope_files)} files scanned for retired vocabulary"
    if warning:
        detail += f" | WARNING: {warning}"
    if hits:
        detail += " | " + "; ".join(hits)

    return Result(name, passed=len(hits) == 0, detail=detail)


# --------------------------------------------------------------------------- #
# Check — Bold-for-emphasis (docs/plugin-text-style.md §4)
# --------------------------------------------------------------------------- #
#
# A short, high-precision denylist of single ordinary words, rather than a
# generic "any bold span not immediately followed by a colon" rule. The
# broader rule was tested against the real shipped corpus (499 bold spans
# total) and flagged 408 of them (82%) — almost all of them this codebase's
# own established, legitimate conventions: a bolded imperative lead-in on a
# numbered step ("1. **Confirm the account and project.** Call ...") and a
# first-use term definition ("**edge**", "**identity**"), neither of which
# happens to end in a colon but neither of which is "emphasis on an ordinary
# word" either. This narrower denylist is the subset actually verified
# against the shipped text: every current hit (20, listed in the PLU-1346
# report) was a genuine emphasis violation, not a mislabeled genuine label.
# It will not catch every possible emphasis-bolding — favor false negatives,
# per the issue brief — but what it does flag is real.
BOLD_EMPHASIS_WORDS = {
    "not", "never", "always", "only", "must", "no", "none", "any", "every",
    "all", "exactly", "actually", "really", "truly", "genuinely", "definitely",
    "certainly", "absolutely", "literally", "especially", "particularly",
    "explicitly", "precisely", "strictly", "solely",
}

_BOLD_RE = re.compile(r"\*\*([^*\n]+)\*\*")


def _scan_file_for_bold_emphasis(path: Path) -> list[str]:
    hits: list[str] = []
    try:
        text = path.read_text(encoding="utf-8")
    except Exception as e:
        return [f"{path}: read error: {e}"]

    lines = text.splitlines()
    fence_mask = _fenced_code_line_mask(lines)

    for i, line in enumerate(lines, 1):
        if fence_mask[i - 1]:
            continue
        for m in _BOLD_RE.finditer(line):
            content = m.group(1).strip()
            if " " in content:
                continue  # multi-word spans are out of this check's scope
            after = line[m.end():m.end() + 1]
            if after == ":":
                continue  # genuine label, per the `**Label**:` convention
            word = content.strip(".,;!?").lower()
            if word in BOLD_EMPHASIS_WORDS:
                hits.append(
                    f"{path.name}:{i}: bold-for-emphasis on ordinary word {content!r} in: {line.strip()[:160]}"
                )
    return hits


def check_bold_emphasis(plugin_path: Path, marketplace_root: Path) -> Result:
    name = "bold-emphasis"
    full_scope_files, _client_only_files, _warning = _collect_scope_files(plugin_path, marketplace_root)

    hits: list[str] = []
    for f in full_scope_files:
        hits.extend(_scan_file_for_bold_emphasis(f))

    detail = f"{len(full_scope_files)} files scanned"
    if hits:
        detail += " | " + "; ".join(hits)

    return Result(name, passed=len(hits) == 0, detail=detail)


# --------------------------------------------------------------------------- #
# Check — Title-Case pseudo-headings (docs/plugin-text-style.md §4) — advisory
# --------------------------------------------------------------------------- #
#
# Conservative on purpose: only a STANDALONE line of 2+ consecutive
# Title-Case words is flagged — not a real `#`/`##` heading, not a table
# row, not a list item, not a blockquote, not fenced code. An inline
# version of this check (scanning running prose for any 2+-word Title-Case
# run) was tested against the real shipped corpus and found 13 hits, ALL of
# them false positives: the product name ("Claude Code"), real proper nouns
# ("New England", "Acme Construction"), sentence-initial capitalization
# colliding with a proper noun ("The Additional", "If Codex"), and literal
# quoted example values ("Metal Stud Partitions", "Unit Casework" — example
# scope-category names in scope-run's own instructions). The standalone-line
# version below had zero hits, true or false, against the same corpus.
#
# Because it is unproven against a single real positive case, and because a
# two-word proper noun standing alone on its own line (a rare but possible
# shape) would still false-positive it, this check is advisory only: it
# always reports PASS and surfaces any hit as a WARN, never a FAIL. Promote
# it to a real gate only after it has been observed catching a genuine
# violation without also catching an innocent one.
_TITLECASE_LINE_RE = re.compile(r"^([A-Z][A-Za-z0-9'/-]*(?:\s+[A-Z][A-Za-z0-9'/-]*){1,})[.:]?$")


def _scan_file_for_titlecase_labels(path: Path) -> list[str]:
    hits: list[str] = []
    try:
        text = path.read_text(encoding="utf-8")
    except Exception as e:
        return [f"{path}: read error: {e}"]

    lines = text.splitlines()
    fence_mask = _fenced_code_line_mask(lines)

    for i, line in enumerate(lines, 1):
        if fence_mask[i - 1]:
            continue
        stripped = line.strip()
        if not stripped or stripped.startswith(("#", "|", "-", "*", "+", ">")):
            continue
        if re.match(r"^\d+\.", stripped):
            continue
        m = _TITLECASE_LINE_RE.match(stripped)
        if m and len(m.group(1).split()) >= 2:
            hits.append(f"{path.name}:{i}: possible Title-Case pseudo-heading: {stripped[:160]}")
    return hits


def check_titlecase_labels(plugin_path: Path, marketplace_root: Path) -> Result:
    name = "titlecase-labels (advisory, never fails)"
    full_scope_files, _client_only_files, _warning = _collect_scope_files(plugin_path, marketplace_root)

    hits: list[str] = []
    for f in full_scope_files:
        hits.extend(_scan_file_for_titlecase_labels(f))

    detail = f"{len(full_scope_files)} files scanned"
    warning = "; ".join(hits) if hits else ""

    return Result(name, passed=True, detail=detail, warning=warning)


# --------------------------------------------------------------------------- #
# Check — MCP URL
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
# Check — No absolute paths in config files
# --------------------------------------------------------------------------- #

def check_no_absolute_paths(plugin_path: Path, marketplace_root: Path) -> Result:
    name = "no-absolute-paths-in-config"
    config_files = [
        plugin_path / ".mcp.json",
        plugin_path / ".claude-plugin" / "plugin.json",
        plugin_path / ".codex-plugin" / "plugin.json",
        marketplace_root / ".claude-plugin" / "marketplace.json",
    ]

    hits: list[str] = []
    for cfg_path in config_files:
        if not cfg_path.exists():
            continue
        text = cfg_path.read_text(encoding="utf-8")
        for pattern in _ABS_PATH_PATTERNS:
            if pattern.search(text):
                for i, line in enumerate(text.splitlines(), 1):
                    if pattern.search(line):
                        hits.append(f"{cfg_path.name} line {i}: {line.strip()[:120]}")

    if hits:
        return Result(name, False, detail="; ".join(hits))
    else:
        return Result(name, True, detail=f"{len(config_files)} config files checked, no absolute paths")


# --------------------------------------------------------------------------- #
# Check — Question/failure boundary (PLU-1524)
# --------------------------------------------------------------------------- #
#
# A project Question is a construction-project artifact: the user reads it as an open item
# about the drawings, the specs, the scope, or a value the agent genuinely cannot resolve from
# what it read. Agents were instead writing their own tooling problems into it through
# `ask_question` -- a recognize_sheets timeout, a page the pass never resolved, a job that
# failed -- because nothing on the page said a Question was the wrong door for that. This check
# is the regression guard for the fix (docs/plugin-text-style.md's authoring contract does not
# cover this; it is a doctrine boundary, not a text-style rule): no skill or agent file may tell
# the agent to raise a Question near failure language, and every file that names `ask_question`
# or "raise a Question" at all must carry the boundary sentence that states the rule.
#
# Two failure modes, checked separately:
#
#   1. A Question-raising phrase sitting within a small line window of failure language, with no
#      negation/prohibition cue in that same window. This is the shape of the actual violation
#      found in drawing-upload's own text before this issue: "Raise any pages still unresolved or
#      flagged image-only pages as questions with `ask_question`." The window is small (3 lines
#      either side) and the negation guard (`never`, `not raise`, `rather than`, `instead of`,
#      "no Question") exists because the fix for that violation still has to say "unresolved" and
#      "image-only" right next to "never raise this as a Question" -- the corrected sentence
#      necessarily uses the same vocabulary the violation did, just inverted. A word-proximity
#      check with no negation guard would flag the fix as hard as the bug.
#   2. A file that mentions `ask_question` / "raise a Question" anywhere but never states the
#      boundary rule at all. Checked against one fixed phrase so every addition made for this
#      issue is provably present, not just plausible-sounding nearby text.
#
# This is intentionally narrower than "is every Question in this file actually about the
# project" -- that judgment call belongs in review, not a regex. What is mechanical here is
# proven mechanical: a known-bad phrase pattern, and a known-required phrase.

_QUESTION_VERB_RE = re.compile(
    r"ask_question|raise (?:it |them )?as (?:a |)questions?|raise a question|"
    r"raised as (?:a |)questions?",
    re.IGNORECASE,
)

# Failure/job-trouble vocabulary a Question should never sit next to. Matches the brief's own
# list; deliberately not "failure" itself, since that is the word the boundary sentence uses to
# NAME the rule ("never about a Plumlayer failure") and would make the negation guard load-bearing
# for the boundary sentence's own trigger word instead of for genuine nearby failure language.
_FAILURE_WORD_RE = re.compile(
    r"\bfailed\b|\btimed out\b|\bimage-only\b|\bunresolved\b|\bretry\b|\bretried\b|"
    r"\bcould not\b|\bcouldn't\b",
    re.IGNORECASE,
)

# A prohibition cue nearby means the sentence is stating the boundary rule (the fix), not
# inviting the violation: "never raise this as a Question", "not raised as a Question", "rather
# than raising them as Questions", "never about a Plumlayer failure".
_NEGATION_CUE_RE = re.compile(
    r"\bnever\b|\bnot raise\b|\brather than\b|\binstead of\b|\bno question\b",
    re.IGNORECASE,
)

QUESTION_BOUNDARY_PHRASE = "never about a Plumlayer failure"

_QUESTION_FAILURE_WINDOW = 3  # lines scanned on each side of a Question-verb hit


def _paragraph_clamped_window(lines: list[str], i: int, radius: int) -> tuple[int, int]:
    """
    Line range [lo, hi) around index i, expanded up to `radius` lines each way but stopped at
    the nearest blank line. A blank line is where this codebase actually separates one thought
    from the next (a new paragraph, or the boundary of a `<!-- user-facing -->` block), so an
    unrelated "rather than" two paragraphs up should not silently clear a real violation, the
    same way an unrelated failure word two paragraphs down should not manufacture one.
    """
    lo = i
    for k in range(1, radius + 1):
        j = i - k
        if j < 0 or lines[j].strip() == "":
            break
        lo = j
    hi = i
    for k in range(1, radius + 1):
        j = i + k
        if j >= len(lines) or lines[j].strip() == "":
            break
        hi = j
    return lo, hi + 1


def _scan_file_for_question_near_failure(path: Path, label: str) -> list[str]:
    hits: list[str] = []
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except Exception as e:
        return [f"{label}: read error: {e}"]

    for i, line in enumerate(lines):
        if not _QUESTION_VERB_RE.search(line):
            continue
        lo, hi = _paragraph_clamped_window(lines, i, _QUESTION_FAILURE_WINDOW)
        window_text = " ".join(lines[lo:hi])
        if not _FAILURE_WORD_RE.search(window_text):
            continue
        if _NEGATION_CUE_RE.search(window_text):
            continue  # states the boundary rule; does not invite the violation
        hits.append(
            f"{label}:{i + 1}: raises a Question next to failure language, with no "
            f"boundary sentence in range — {line.strip()[:160]}"
        )
    return hits


def check_question_failure_boundary(plugin_path: Path) -> Result:
    name = "question-never-a-failure-report"
    skills_dir = plugin_path / "skills"
    agents_dir = plugin_path / "agents"

    files: list[Path] = []
    if skills_dir.is_dir():
        files.extend(sorted(skills_dir.rglob("SKILL.md")))
    if agents_dir.is_dir():
        files.extend(sorted(agents_dir.rglob("*.md")))

    errors: list[str] = []
    for f in files:
        try:
            text = f.read_text(encoding="utf-8")
        except Exception as e:
            errors.append(f"{f}: read error: {e}")
            continue

        # Every SKILL.md file shares the same filename, so identify it by its skill/agent
        # directory (`project-record/SKILL.md`) rather than the bare, ambiguous basename.
        label = f"{f.parent.name}/{f.name}" if f.name == "SKILL.md" else f.name

        errors.extend(_scan_file_for_question_near_failure(f, label))

        # Markdown wraps prose at the line, so the boundary phrase can legitimately span a
        # line break (e.g. "...Plumlayer\n  failure"); collapse whitespace before matching
        # rather than demanding it land unbroken on one source line.
        normalized = re.sub(r"\s+", " ", text)
        if _QUESTION_VERB_RE.search(text) and QUESTION_BOUNDARY_PHRASE not in normalized:
            errors.append(
                f"{label}: names ask_question / raises a Question but carries no "
                f"'{QUESTION_BOUNDARY_PHRASE}' boundary sentence"
            )

    detail = f"{len(files)} skill/agent files scanned"
    if errors:
        detail += " | " + "; ".join(errors)

    return Result(name, passed=len(errors) == 0, detail=detail)


# --------------------------------------------------------------------------- #
# Check — the Question RFI bar
# --------------------------------------------------------------------------- #
#
# A reader was raising a Question for every uncertainty it met, because the text told it to: the
# closing line of its own report shape said to raise one "rather than smoothing it". The result was
# a Question for anything a sub could have priced as drawn, which buries the handful a person
# actually has to answer. The bar is now stated once, in scope-reader's mandate 1, in fixed words.
#
# Two mechanical arms, the same shape as the two checks above:
#
#   1. scope-reader.md carries the bar in its fixed wording. Two phrases, both required, so the
#      rule is provably present rather than plausible-sounding nearby text.
#   2. No shipped skill or agent file carries a retired raise-for-everything phrase next to the
#      word Question. Matched on one line: the phrases are short and the collocation is what makes
#      them a directive, and "rather than guessing at one" about a category string (which the same
#      file legitimately carries) is not about Questions at all.
#
# What this cannot judge, and does not try to: whether a Question an agent actually raises clears
# the bar. That stays in review.

QUESTION_RFI_BAR_PHRASES = (
    "first inkling of an RFI",
)

# Wording retired with the bar: it told the reader to raise a Question wherever it was unsure,
# which is the failure mode the bar exists to stop.
_QUESTION_RAISE_FOR_EVERYTHING_RE = re.compile(
    r"rather than smoothing it|rather than guessing", re.IGNORECASE
)

_QUESTION_WORD_RE = re.compile(r"\bquestions?\b", re.IGNORECASE)


def check_question_rfi_bar(plugin_path: Path) -> Result:
    name = "question-rfi-bar"
    skills_dir = plugin_path / "skills"
    agents_dir = plugin_path / "agents"

    files: list[Path] = []
    if skills_dir.is_dir():
        files.extend(sorted(skills_dir.rglob("SKILL.md")))
    if agents_dir.is_dir():
        files.extend(sorted(agents_dir.rglob("*.md")))

    errors: list[str] = []

    reader = agents_dir / "scope-reader.md"
    if not reader.is_file():
        errors.append(f"reader definition not found at {reader}")
    else:
        try:
            # Markdown wraps prose at the line, so a required phrase can legitimately span a
            # line break; collapse whitespace before matching rather than demanding one line.
            normalized = re.sub(r"\s+", " ", reader.read_text(encoding="utf-8"))
        except Exception as e:
            normalized = ""
            errors.append(f"{reader.name}: read error: {e}")
        for phrase in QUESTION_RFI_BAR_PHRASES:
            if phrase and phrase not in normalized:
                errors.append(f"{reader.name}: carries no '{phrase}' bar sentence")

    for f in files:
        try:
            lines = f.read_text(encoding="utf-8").splitlines()
        except Exception as e:
            errors.append(f"{f}: read error: {e}")
            continue

        label = f"{f.parent.name}/{f.name}" if f.name == "SKILL.md" else f.name

        for i, line in enumerate(lines):
            m = _QUESTION_RAISE_FOR_EVERYTHING_RE.search(line)
            if m and _QUESTION_WORD_RE.search(line):
                errors.append(
                    f"{label}:{i + 1}: retired raise-for-everything wording '{m.group(0)}' "
                    f"next to Question — {line.strip()[:160]}"
                )

    detail = f"{len(files)} skill/agent files scanned, {len(QUESTION_RFI_BAR_PHRASES)} bar phrases required"
    if errors:
        detail += " | " + "; ".join(errors)

    return Result(name, passed=len(errors) == 0, detail=detail)


# --------------------------------------------------------------------------- #
# Check — Question plain-words pointer (PLU-1526)
# --------------------------------------------------------------------------- #
#
# A Question an agent raises reaches the user as project text, read on the site exactly like any
# other user-facing string, but nothing checked that its wording actually read that way: an agent
# was writing its own judgment-entry predicate names (`mepDeliveryShape`, `missingScopeFamily`) and
# an em dash straight into a Question's text. docs/plugin-text-style.md now states the rule once,
# in full, and every other file that tells an agent to raise a Question points at that rule rather
# than repeating it. This check is the mechanical half of that, the same shape as the
# Question/failure boundary check above: it cannot judge whether a given Question actually reads in
# plain estimator words (that stays in review), only that every instruction telling an agent to
# raise one carries the fixed pointer phrase.

QUESTION_PLAIN_WORDS_PHRASE = "Question text is plain estimator words"


def check_question_plain_words_pointer(plugin_path: Path) -> Result:
    name = "question-plain-words-pointer"
    skills_dir = plugin_path / "skills"
    agents_dir = plugin_path / "agents"

    files: list[Path] = []
    if skills_dir.is_dir():
        files.extend(sorted(skills_dir.rglob("SKILL.md")))
    if agents_dir.is_dir():
        files.extend(sorted(agents_dir.rglob("*.md")))

    errors: list[str] = []
    for f in files:
        try:
            text = f.read_text(encoding="utf-8")
        except Exception as e:
            errors.append(f"{f}: read error: {e}")
            continue

        label = f"{f.parent.name}/{f.name}" if f.name == "SKILL.md" else f.name

        if not _QUESTION_VERB_RE.search(text):
            continue

        # Markdown wraps prose at the line, so the phrase can legitimately span a line break;
        # collapse whitespace before matching rather than demanding it land unbroken on one line.
        normalized = re.sub(r"\s+", " ", text)
        if QUESTION_PLAIN_WORDS_PHRASE not in normalized:
            errors.append(
                f"{label}: names ask_question / raises a Question but carries no "
                f"'{QUESTION_PLAIN_WORDS_PHRASE}' rule or pointer"
            )

    detail = f"{len(files)} skill/agent files scanned"
    if errors:
        detail += " | " + "; ".join(errors)

    return Result(name, passed=len(errors) == 0, detail=detail)


# --------------------------------------------------------------------------- #
# Check: the ledger's fixed line shapes
# --------------------------------------------------------------------------- #
#
# The run ledger is a line-shaped log, not prose. A measured run wrote 75 KB of headings and
# paragraphs into it and then re-read the whole file on every call, which is the accumulation this
# shape exists to stop. The harness never sees a run's ledger, so the checkable target is the
# shipped text that tells the agent what to write.
#
# Three mechanical properties, checked separately:
#
#   1. The grammar block in the runner definition still declares exactly three line kinds, and the
#      `note` kind list is still the closed set. A fourth shape added or one dropped fails.
#   2. Every shipped file that instructs appending to the ledger carries the prohibition sentence
#      verbatim. Same mechanism as the Question/failure boundary check: one fixed phrase, matched
#      after collapsing whitespace so a markdown line wrap does not break it.
#   3. No prose-permitting cue ("narrate", "summarize", "in your own words") sits near a ledger
#      mention with no prohibition cue in range. This is a regression guard against the drift shape
#      that actually shipped, not a general proof: a definition that permits prose in wording this
#      list does not name still passes.

LEDGER_LINE_KINDS = {"dispatch", "verified", "note"}

LEDGER_NOTE_KINDS = {
    "anomaly", "unread", "kinds", "deviation", "overlap", "grain", "door", "packet", "convention",
}

LEDGER_PROHIBITION_PHRASE = "Nothing else goes in the ledger"

_LEDGER_HEADING_RE = re.compile(r"^#{2,3}\s+.*ledger line", re.IGNORECASE)

_LEDGER_MENTION_RE = re.compile(r"\bledger\b", re.IGNORECASE)

_LEDGER_APPEND_RE = re.compile(r"\bappend(?:s|ed|ing)?\b", re.IGNORECASE)

# Wording that invites prose where a fixed line shape belongs.
_LEDGER_PROSE_CUE_RE = re.compile(
    r"narrat|summariz|summaris|paragraph|in prose|in your own words|write up|"
    r"describe what|re-tell|retell|recount",
    re.IGNORECASE,
)

# A prohibition cue in range means the sentence is stating the rule (no paragraphs, never narrate),
# not inviting the violation. The corrected sentence necessarily uses the same vocabulary the
# violation did, just inverted.
_LEDGER_PROHIBITION_CUE_RE = re.compile(
    r"\bnever\b|\bno\b|\bnot\b|\bnothing\b|\brather than\b|\binstead of\b|\bforbid",
    re.IGNORECASE,
)

_LEDGER_PROSE_WINDOW = 3  # lines scanned on each side of a ledger mention

# The sentence that pins the `note` kinds. Read from the file rather than assumed so a kind added
# in the text without a decision here fails, and a kind removed here without the text fails too.
_LEDGER_NOTE_KIND_SENTENCE_RE = re.compile(
    r"on a `note` line is one of exactly these:([^.]*)\.", re.IGNORECASE
)

_INLINE_CODE_TOKEN_RE = re.compile(r"`([A-Za-z][A-Za-z0-9_-]*)`")


def _first_fenced_block_after(lines: list[str], start: int) -> list[str] | None:
    """Body lines of the first fenced block at or after `start`, or None if there is none."""
    i = start
    while i < len(lines):
        if lines[i].lstrip().startswith("```"):
            body: list[str] = []
            for j in range(i + 1, len(lines)):
                if lines[j].lstrip().startswith("```"):
                    return body
                body.append(lines[j])
            return None
        i += 1
    return None


def _check_ledger_grammar_block(path: Path, label: str) -> list[str]:
    errors: list[str] = []
    try:
        text = path.read_text(encoding="utf-8")
    except Exception as e:
        return [f"{label}: read error: {e}"]
    lines = text.splitlines()

    heading_idx = next(
        (i for i, line in enumerate(lines) if _LEDGER_HEADING_RE.match(line)), None
    )
    if heading_idx is None:
        return [f"{label}: no heading naming the ledger line shapes"]

    body = _first_fenced_block_after(lines, heading_idx + 1)
    if body is None:
        errors.append(f"{label}: the ledger line heading is followed by no fenced block")
    else:
        found = {line.split()[0] for line in body if line.strip()}
        if found != LEDGER_LINE_KINDS:
            errors.append(
                f"{label}: ledger line kinds are {sorted(found)}, expected "
                f"{sorted(LEDGER_LINE_KINDS)}"
            )

    normalized = re.sub(r"\s+", " ", text)
    m = _LEDGER_NOTE_KIND_SENTENCE_RE.search(normalized)
    if m is None:
        errors.append(f"{label}: no sentence naming the closed set of `note` kinds")
    else:
        found_kinds = set(_INLINE_CODE_TOKEN_RE.findall(m.group(1)))
        if found_kinds != LEDGER_NOTE_KINDS:
            errors.append(
                f"{label}: `note` kinds are {sorted(found_kinds)}, expected "
                f"{sorted(LEDGER_NOTE_KINDS)}"
            )
    return errors


def _scan_file_for_ledger_prose(path: Path, label: str) -> list[str]:
    hits: list[str] = []
    try:
        text = path.read_text(encoding="utf-8")
    except Exception as e:
        return [f"{label}: read error: {e}"]
    lines = text.splitlines()

    instructs_append = False
    for i, line in enumerate(lines):
        if not _LEDGER_MENTION_RE.search(line):
            continue
        lo, hi = _paragraph_clamped_window(lines, i, _LEDGER_PROSE_WINDOW)
        window_text = " ".join(lines[lo:hi])
        if _LEDGER_APPEND_RE.search(window_text):
            instructs_append = True
        if not _LEDGER_PROSE_CUE_RE.search(window_text):
            continue
        if _LEDGER_PROHIBITION_CUE_RE.search(window_text):
            continue  # states the rule; does not invite prose
        hits.append(
            f"{label}:{i + 1}: prose cue next to a ledger mention, with no prohibition cue in "
            f"range: {line.strip()[:160]}"
        )

    if instructs_append:
        normalized = re.sub(r"\s+", " ", text)
        if LEDGER_PROHIBITION_PHRASE not in normalized:
            hits.append(
                f"{label}: instructs appending to the ledger but carries no "
                f"'{LEDGER_PROHIBITION_PHRASE}' sentence"
            )
    return hits


def check_ledger_fixed_shape(plugin_path: Path) -> Result:
    name = "ledger-fixed-shape"
    skills_dir = plugin_path / "skills"
    agents_dir = plugin_path / "agents"

    files: list[Path] = []
    if skills_dir.is_dir():
        files.extend(sorted(skills_dir.rglob("SKILL.md")))
    if agents_dir.is_dir():
        files.extend(sorted(agents_dir.rglob("*.md")))

    errors: list[str] = []
    for f in files:
        label = f"{f.parent.name}/{f.name}" if f.name == "SKILL.md" else f.name
        errors.extend(_scan_file_for_ledger_prose(f, label))

    runner = agents_dir / "scope-round-runner.md"
    if not runner.is_file():
        errors.append("agents/scope-round-runner.md not found")
    else:
        errors.extend(_check_ledger_grammar_block(runner, runner.name))

    detail = f"{len(files)} skill/agent files scanned"
    if errors:
        detail += " | " + "; ".join(errors)

    return Result(name, passed=len(errors) == 0, detail=detail)


# --------------------------------------------------------------------------- #
# Check: the runner's mode set
# --------------------------------------------------------------------------- #
#
# The runner supervises one pass, one round boundary, or one completeness accounting, and nothing
# larger. Its `##` headings are what say so, so pinning the set in both directions is the cheap
# mechanical way to catch the shape being partly undone: a `## Round mode` coming back, or
# `## Pass mode` renamed away, fails the release.

EXPECTED_RUNNER_MODE_HEADINGS = {
    "What your dispatch gives you",
    "Pass mode",
    "The ledger lines",
    "Boundary mode",
    "Leftover mode",
    "What you never do",
    "Your summary",
}


def check_runner_mode_set(plugin_path: Path) -> Result:
    name = "runner-mode-set"
    runner = plugin_path / "agents" / "scope-round-runner.md"
    if not runner.is_file():
        return Result(name, False, detail=f"agent definition not found at {runner}")

    try:
        lines = runner.read_text(encoding="utf-8").splitlines()
    except Exception as e:
        return Result(name, False, detail=f"{runner.name}: read error: {e}")

    fence_mask = _fenced_code_line_mask(lines)
    found = {
        line[3:].strip()
        for i, line in enumerate(lines)
        if not fence_mask[i] and line.startswith("## ")
    }

    errors: list[str] = []
    missing = EXPECTED_RUNNER_MODE_HEADINGS - found
    unexpected = found - EXPECTED_RUNNER_MODE_HEADINGS
    if missing:
        errors.append(f"expected headings missing: {sorted(missing)}")
    if unexpected:
        errors.append(f"unexpected headings: {sorted(unexpected)}")

    detail = f"{len(found)} top-level headings in {runner.name}"
    if errors:
        detail += " | " + "; ".join(errors)

    return Result(name, passed=len(errors) == 0, detail=detail)


# --------------------------------------------------------------------------- #
# Check: the pass knowledge excerpt
# --------------------------------------------------------------------------- #
#
# A reader opens no shipped file itself: its pass runner cuts the hints of every trade the pass
# carries into one pass knowledge file, and the reader reads that. The cut is only safe if nothing
# the reader acts on goes missing in it, so this runs the shipped script over every trade the
# manifest lists and asserts each hints file comes back as a contiguous, byte-identical run.
# Contiguity is the point: an every-line-is-present assertion would pass on text that had been
# reordered or reflowed, which is the failure a verbatim cut exists to rule out.
#
# The two budgets are recomputed here rather than trusted from the script, so a drift between the
# source repo's Node gate and this Python one is a release failure and not a silent disagreement.
#
# The join the runner depends on is asserted too: the runner opens conventions/<slug>.md for a slug
# the cut printed, and the cut is the only place a catalog code becomes a slug, so a pass named by
# code and a conventions file that is not there would otherwise meet for the first time mid-pass.

PASS_KNOWLEDGE_SCRIPT = ("scripts", "cut_pass_knowledge.py")

_KNOWLEDGE_VERSION_RE = re.compile(r"\*\*Knowledge version:\s*`([^`]+)`\*\*")

# The same two numbers the source repo's exit check applies, restated here rather than imported
# from the script under test.
_HINT_LINE_BUDGET = 20
_HINT_CHARACTER_BUDGET = 2400
_CONVENTION_COLUMNS = ["name", "category", "note to bidder", "applies when"]
_CONVENTION_NAME_LIMIT = 80


def _load_cut_module(script_path: Path):
    """Import the shipped cut script in-process, so the check runs no subprocess and no model."""
    return _load_script_module(script_path, "cut_pass_knowledge")


def _content_lines(text: str) -> list[str]:
    """The file's lines less the one empty element a trailing newline leaves behind."""
    lines = text.split("\n")
    if len(lines) > 1 and lines[-1] == "":
        lines.pop()
    return lines


def _hints_errors(slug: str, text: str) -> list[str]:
    """
    The shipped hints file's shape and its two budgets, computed here. The shape is a title, a
    blank, one hint per line, a blank, then the coverage line last.
    """
    errors: list[str] = []
    lines = _content_lines(text)
    if not lines or not lines[0].startswith("# "):
        errors.append(f"hints/{slug}.md: line 1 is not a title")
    if len(lines) < 5:
        errors.append(f"hints/{slug}.md: {len(lines)} lines, too few for the shape")
        return errors
    blanks = [i + 1 for i, line in enumerate(lines) if line.strip() == ""]
    if blanks != [2, len(lines) - 1]:
        errors.append(f"hints/{slug}.md: blank lines at {blanks or 'none'}, expected [2, {len(lines) - 1}]")
    if not lines[-1].startswith("coverage:"):
        errors.append(f"hints/{slug}.md: the last line is not the coverage line")
    hint_lines = len(lines) - 4
    if hint_lines > _HINT_LINE_BUDGET:
        errors.append(f"hints/{slug}.md: {hint_lines} hint lines, over the budget of {_HINT_LINE_BUDGET}")
    if len(text) > _HINT_CHARACTER_BUDGET:
        errors.append(f"hints/{slug}.md: {len(text)} characters, over the budget of {_HINT_CHARACTER_BUDGET}")
    return errors


def _table_cells(line: str) -> list[str]:
    body = line.strip()
    if body.startswith("|"):
        body = body[1:]
    if body.endswith("|"):
        body = body[:-1]
    return [cell.strip() for cell in body.split("|")]


def _conventions_errors(slug: str, text: str) -> list[str]:
    """A title line, one table with the four columns in order, and no name cell over the bound."""
    errors: list[str] = []
    lines = _content_lines(text)
    if not lines or not lines[0].startswith("# "):
        errors.append(f"conventions/{slug}.md: line 1 is not a title")
    numbered = [(i + 2, line) for i, line in enumerate(lines[1:])]
    non_blank = [(n, line) for n, line in numbered if line.strip()]
    rows = [(n, line) for n, line in non_blank if line.strip().startswith("|")]
    strays = [n for n, line in non_blank if not line.strip().startswith("|")]
    if strays:
        errors.append(f"conventions/{slug}.md: line(s) {strays} are neither the title, a row nor blank")
    if not rows:
        errors.append(f"conventions/{slug}.md: no table")
        return errors
    if any(rows[i][0] != rows[i - 1][0] + 1 for i in range(1, len(rows))):
        errors.append(f"conventions/{slug}.md: the table rows are not contiguous, so there is more than one table")
    header = [cell.lower() for cell in _table_cells(rows[0][1])]
    if header != _CONVENTION_COLUMNS:
        errors.append(f"conventions/{slug}.md: header is {header}, expected {_CONVENTION_COLUMNS}")
    for number, line in rows[2:]:
        cells = _table_cells(line)
        if len(cells) != len(_CONVENTION_COLUMNS):
            errors.append(f"conventions/{slug}.md: line {number} has {len(cells)} cells, expected 4")
        elif len(cells[0]) > _CONVENTION_NAME_LIMIT:
            errors.append(
                f"conventions/{slug}.md: line {number} names {len(cells[0])} characters, "
                f"over the bound of {_CONVENTION_NAME_LIMIT}"
            )
    return errors


def _write_cut_fixture(
    root: Path,
    slug: str,
    hints: str | None,
    conventions: str | None,
    sheets: dict | None = None,
) -> Path:
    """
    A throwaway trade-knowledge tree holding one trade, for driving the cut's named refusals and
    the resolution cases the shipped map cannot show, since it keys one code per trade. The files
    are rewritten every run and the absent ones removed, so a previous run's tree cannot make a
    refusal case pass by leaving a file behind.
    """
    trade_dir = root / slug
    (trade_dir / "hints").mkdir(parents=True, exist_ok=True)
    (trade_dir / "conventions").mkdir(parents=True, exist_ok=True)
    (trade_dir / "MANIFEST.md").write_text(
        f"# Manifest\n\n**Knowledge version: `fixture01`**.\n\n## Trade files\n\n{slug}\n",
        encoding="utf-8",
    )
    (trade_dir / "trade-sheets.json").write_text(
        json.dumps(sheets if sheets is not None else {"trades": {}}) + "\n", encoding="utf-8"
    )
    hints_path = trade_dir / "hints" / f"{slug}.md"
    conventions_path = trade_dir / "conventions" / f"{slug}.md"
    for path, content in ((hints_path, hints), (conventions_path, conventions)):
        if content is None:
            path.unlink(missing_ok=True)
        else:
            path.write_text(content, encoding="utf-8")
    return trade_dir


def check_pass_knowledge_excerpt(plugin_path: Path) -> Result:
    name = "pass-knowledge-excerpt"
    script = plugin_path.joinpath(*PASS_KNOWLEDGE_SCRIPT)
    if not script.is_file():
        return Result(name, False, detail=f"cut script not found at {script}")

    trade_dir = plugin_path / "trade-knowledge"
    manifest = trade_dir / "MANIFEST.md"
    if not manifest.is_file():
        return Result(name, False, detail=f"trade knowledge manifest not found at {manifest}")

    pinned = _pinned_trade_package_names(trade_dir)
    if not pinned:
        return Result(name, False, detail=f"could not parse {manifest.name}'s Trade files list")
    trades = sorted(pinned)

    try:
        manifest_text = manifest.read_text(encoding="utf-8")
    except Exception as e:
        return Result(name, False, detail=f"{manifest.name}: read error: {e}")
    version_match = _KNOWLEDGE_VERSION_RE.search(manifest_text)
    if not version_match:
        return Result(name, False, detail=f"no Knowledge version line in {manifest.name}")
    version = version_match.group(1).strip()

    try:
        module = _load_cut_module(script)
    except Exception as e:
        return Result(name, False, detail=f"cannot import {script.name}: {e}")

    errors: list[str] = []
    results_dir = Path(__file__).parent / ".test-results"

    # ------------------------------------------------------------------ #
    # Every manifest trade ships both files, and both hold their shape
    # ------------------------------------------------------------------ #
    hints_text: dict[str, str] = {}
    missing: list[str] = []
    largest = ("", 0)
    for slug in trades:
        hints_path = trade_dir / "hints" / f"{slug}.md"
        conventions_path = trade_dir / "conventions" / f"{slug}.md"
        if not hints_path.is_file():
            missing.append(f"hints/{slug}.md")
        else:
            try:
                text = hints_path.read_text(encoding="utf-8")
            except Exception as e:
                errors.append(f"hints/{slug}.md: read error: {e}")
            else:
                hints_text[slug] = text
                errors.extend(_hints_errors(slug, text))
                if len(text) > largest[1]:
                    largest = (slug, len(text))
        if not conventions_path.is_file():
            missing.append(f"conventions/{slug}.md")
        else:
            try:
                errors.extend(_conventions_errors(slug, conventions_path.read_text(encoding="utf-8")))
            except Exception as e:
                errors.append(f"conventions/{slug}.md: read error: {e}")
    if missing:
        shown = ", ".join(missing[:8]) + (", ..." if len(missing) > 8 else "")
        errors.append(f"{len(missing)} file(s) the manifest lists are not on disk: {shown}")

    # ------------------------------------------------------------------ #
    # The cut carries each hints file whole, contiguous and byte-identical
    # ------------------------------------------------------------------ #
    excerpt = ""
    if not missing:
        out = results_dir / "pass-knowledge-all.md"
        try:
            module.cut(trade_dir, trades, "harness-all-trades", out)
            excerpt = out.read_text(encoding="utf-8")
        except Exception as e:
            errors.append(f"the cut failed over the shipped hints files: {e}")
        else:
            if f"knowledge version: {version}" not in excerpt:
                errors.append(f"the excerpt does not carry the manifest's knowledge version {version}")
            for slug, text in hints_text.items():
                if text.rstrip("\n") not in excerpt:
                    errors.append(f"{slug}: the hints file is not in the excerpt contiguous and byte-identical")

    # ------------------------------------------------------------------ #
    # The join: every slug the cut prints for a catalog code has a table
    # ------------------------------------------------------------------ #
    #
    # The runner builds the conventions path out of the slug this report names, and a window 2 pass
    # names its trade by catalog code, so the codes are what the join has to be proved over.
    joined = 0
    try:
        sheet_trades = json.loads((trade_dir / "trade-sheets.json").read_text(encoding="utf-8"))["trades"]
    except Exception as e:
        errors.append(f"trade-sheets.json: {e}")
        sheet_trades = {}
    codes = sorted(code for code, entry in sheet_trades.items() if isinstance(entry, dict) and entry.get("knowledge"))
    if codes and not missing:
        try:
            report = module.cut(
                trade_dir, codes, "harness-all-codes", results_dir / "pass-knowledge-codes.md"
            )
        except Exception as e:
            errors.append(f"the cut failed over every mapped catalog code: {e}")
        else:
            carried = [line for line in report.splitlines() if line and not line.startswith("wrote ")]
            if not carried:
                errors.append("the cut reported no carried trade for any catalog code")
            for line in carried:
                slug = line.split()[0]
                if not (trade_dir / "conventions" / f"{slug}.md").is_file():
                    errors.append(f"the cut named `{slug}` for a code and conventions/{slug}.md is not on disk")
                else:
                    joined += 1

    fixture_root = results_dir / "cut-refusals"
    good_hints = "# Fixture\n\nA hint about what the sheet shows.\n\ncoverage: invented.\n"
    good_table = "# Fixture\n\n| name | category | note to bidder | applies when |\n| --- | --- | --- | --- |\n"

    # ------------------------------------------------------------------ #
    # Two codes of one family, one trade: the line names both
    # ------------------------------------------------------------------ #
    #
    # A person reads the per-trade line to check what the pass was asked for, so a code that
    # resolved and went unreported is a code they would believe was never asked for. The shipped
    # map keys one code per trade and cannot show this, so it takes a fixture map.
    two_code_dir = _write_cut_fixture(
        fixture_root,
        "twocodes",
        good_hints,
        good_table,
        sheets={"trades": {"04 20 00": {"knowledge": "twocodes"}}},
    )
    try:
        two_code_report = module.cut(
            two_code_dir, ["04 22 13", "04 20 00"], "harness-two-codes",
            results_dir / "cut-refusals" / "two-codes.md",
        )
    except Exception as e:
        errors.append(f"the cut refused two codes of one family: {e}")
    else:
        carried_lines = [ln for ln in two_code_report.splitlines() if ln and not ln.startswith("wrote ")]
        if len(carried_lines) != 1:
            errors.append(
                f"two codes of one trade produced {len(carried_lines)} carried lines, not 1: {carried_lines!r}"
            )
        elif "04 22 13" not in carried_lines[0] or "04 20 00" not in carried_lines[0]:
            errors.append(
                f"the carried line does not name both codes that resolved to the trade: {carried_lines[0]!r}"
            )
        elif "by family" not in carried_lines[0]:
            errors.append(f"the carried line does not say the narrower code resolved by family: {carried_lines[0]!r}")

    # ------------------------------------------------------------------ #
    # Refusals, each exiting 1 with one line on stderr
    # ------------------------------------------------------------------ #
    refusals: list[tuple[str, Path, str, str]] = [
        (
            "a hints file over the line budget",
            _write_cut_fixture(
                fixture_root,
                "overlines",
                "# Fixture\n\n"
                + "\n".join(f"Hint {i}." for i in range(_HINT_LINE_BUDGET + 1))
                + "\n\ncoverage: invented.\n",
                good_table,
            ),
            "overlines",
            "hint lines",
        ),
        (
            "a hints file over the character budget",
            _write_cut_fixture(
                fixture_root,
                "overchars",
                "# Fixture\n\n" + "x" * (_HINT_CHARACTER_BUDGET + 1) + "\n\ncoverage: invented.\n",
                good_table,
            ),
            "overchars",
            "characters",
        ),
        (
            "a manifest trade with no hints file",
            _write_cut_fixture(fixture_root, "nohints", None, good_table),
            "nohints",
            "hints",
        ),
        (
            "a manifest trade with no conventions file",
            _write_cut_fixture(fixture_root, "noconventions", good_hints, None),
            "noconventions",
            "conventions",
        ),
    ]
    for what, fixture_dir, slug, must_name in refusals:
        code, _bounds, err = _run_plan_script(
            module,
            ["--trade-knowledge", str(fixture_dir), "--trades", slug, "--pass-id", "refused",
             "--out", str(results_dir / "cut-refusals" / "refused.md")],
        )
        if code != 1:
            errors.append(f"{what}: exited {code}, not 1")
        elif len(err.splitlines()) != 1:
            errors.append(f"{what}: the refusal is not one line on stderr")
        elif must_name not in err:
            errors.append(f"{what}: the refusal does not name {must_name}: {err!r}")

    detail = (
        f"{len(trades)} manifest trades, each with a hints file and a convention table; "
        f"{len(hints_text)} hints files cut into {len(excerpt.encode('utf-8')):,} bytes, "
        f"knowledge version {version}; largest hints file {largest[1]:,} characters ({largest[0]}); "
        f"both budgets and both file shapes recomputed here rather than read off the script; "
        f"{joined} catalog code(s) resolved to a slug whose convention table is on disk; "
        f"two codes of one family reported on one line naming both; "
        f"{len(refusals)} broken invocations each refused in one line naming what is wrong"
    )
    # An honest bound, not a pass: the shape checks prove the files are the shape the reader and
    # the runner parse, and nothing here can judge whether a hint earns its line.
    detail += "; bound: shape and budget only, never whether a hint or a row is the right one"
    if errors:
        detail += " | " + "; ".join(errors)

    return Result(name, passed=len(errors) == 0, detail=detail)


# --------------------------------------------------------------------------- #
# Check: the trade to sheet family map
# --------------------------------------------------------------------------- #
#
# The trade files say how a trade bids and splits itself; they carry no sheet families, so the
# window 2 plan reads them out of trade-knowledge/trade-sheets.json instead. That file is the only
# thing deciding which sheets a trade's pass opens, so this checks it against the two records it has
# to agree with: the manifest's own trade file list, in both directions, and the recognizer's sheet
# type vocabulary.

TRADE_SHEETS_FILE = ("trade-knowledge", "trade-sheets.json")

# The recognizer's deterministic sheet types: SHEET_TYPES in the api's sheet-type-classifier.ts,
# less `other`, which that classifier never returns (an unplaceable sheet types null instead).
# Copied here by hand because the api is a different repo; a family naming anything else would
# select nothing on a real set instead of failing here.
RECOGNIZER_SHEET_TYPES = {
    "schedule", "plan", "overall-plan", "enlarged-plan", "section", "elevation",
    "detail", "RCP", "schematic", "legend", "notes", "cover-index",
}


def check_trade_sheet_map(plugin_path: Path) -> Result:
    name = "trade-sheet-map"
    path = plugin_path.joinpath(*TRADE_SHEETS_FILE)
    if not path.is_file():
        return Result(name, False, detail=f"trade sheet map not found at {path}")

    trade_dir = plugin_path / "trade-knowledge"
    pinned = _pinned_trade_package_names(trade_dir)
    if not pinned:
        return Result(name, False, detail="could not parse MANIFEST.md's Trade files list")

    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception as e:
        return Result(name, False, detail=f"{path.name}: {e}")

    errors: list[str] = []

    declared_types = data.get("sheetTypes")
    if not isinstance(declared_types, list):
        return Result(name, False, detail=f"{path.name} carries no `sheetTypes` list")
    if set(declared_types) != RECOGNIZER_SHEET_TYPES:
        errors.append(
            f"the pinned `sheetTypes` list is not the recognizer's twelve: extra "
            f"{sorted(set(declared_types) - RECOGNIZER_SHEET_TYPES)}, missing "
            f"{sorted(RECOGNIZER_SHEET_TYPES - set(declared_types))}"
        )

    trades = data.get("trades")
    if not isinstance(trades, dict) or not trades:
        return Result(name, False, detail=f"{path.name} carries no `trades` object")

    unmapped = data.get("unmapped", {})
    if not isinstance(unmapped, dict):
        return Result(name, False, detail=f"{path.name}: `unmapped` is not an object")

    mapped: dict[str, str] = {}
    empty_families: list[str] = []
    for trade_id, entry in trades.items():
        if not isinstance(entry, dict):
            errors.append(f"trade {trade_id} is not an object")
            continue
        knowledge = entry.get("knowledge")
        if not isinstance(knowledge, str) or knowledge not in pinned:
            errors.append(f"trade {trade_id}: `knowledge` {knowledge!r} is not a manifest trade file")
        elif knowledge in mapped:
            errors.append(f"trade files {mapped[knowledge]} and {trade_id} both claim {knowledge}")
        else:
            mapped[knowledge] = trade_id
        families = entry.get("families")
        if not isinstance(families, list):
            errors.append(f"trade {trade_id}: `families` is not a list")
            continue
        if not families:
            if not entry.get("note"):
                errors.append(f"trade {trade_id}: `families` is empty and no `note` says why")
            empty_families.append(trade_id)
        for index, family in enumerate(families, 1):
            if not isinstance(family, dict):
                errors.append(f"trade {trade_id} family {index} is not an object")
                continue
            if "discipline" not in family and "patterns" not in family:
                errors.append(f"trade {trade_id} family {index} names neither a discipline nor patterns")
            for sheet_type in family.get("sheetTypes", []) or []:
                if sheet_type not in RECOGNIZER_SHEET_TYPES:
                    errors.append(
                        f"trade {trade_id} family {index}: sheet type {sheet_type!r} is not one the "
                        f"recognizer produces"
                    )

    for slug, reason in unmapped.items():
        if slug not in pinned:
            errors.append(f"`unmapped` names {slug}, which is not a manifest trade file")
        if slug in mapped:
            errors.append(f"{slug} is both mapped to {mapped[slug]} and named in `unmapped`")
        if not isinstance(reason, str) or not reason.strip():
            errors.append(f"`unmapped` entry {slug} carries no reason")

    uncovered = sorted(pinned - set(mapped) - set(unmapped))
    if uncovered:
        errors.append(
            f"{len(uncovered)} manifest trade file(s) have no map entry and no named exception: "
            f"{', '.join(uncovered)}"
        )

    seams = data.get("seams", [])
    if not isinstance(seams, list):
        errors.append("`seams` is not a list")
        seams = []
    seen_pairs: set[frozenset] = set()
    for index, pair in enumerate(seams, 1):
        if not isinstance(pair, list) or len(pair) != 2:
            errors.append(f"seam {index} is not a pair")
            continue
        first, second = pair
        if first == second:
            errors.append(f"seam {index} names {first} twice")
            continue
        for member in pair:
            if member not in trades:
                errors.append(f"seam {index} names {member}, which is not a `trades` key")
        key = frozenset(pair)
        if key in seen_pairs:
            errors.append(f"seam {index} repeats a pair already listed")
        seen_pairs.add(key)

    # A trade file is general to its family, so the plan resolves a package's code to the nearest
    # broader CSI section the map keys. These are the four shapes that rule has to get right, each
    # asserted against what the shipped map actually holds rather than against a fixture.
    resolver_path = plugin_path.joinpath(*TRADE_CODE_SCRIPT)
    resolved_cases = 0
    sole_file_divisions = 0
    if not resolver_path.is_file():
        errors.append(f"the shared trade code resolver is not at {resolver_path}")
    else:
        try:
            resolver = _load_script_module(resolver_path, "trade_code")
        except Exception as e:
            errors.append(f"cannot import {resolver_path.name}: {e}")
        else:
            folded = {resolver.fold(key): key for key in trades}
            expected = [
                # a child code, resolving up to the division its one trade file is keyed at
                ("04 22 13", "04 00 00", "family"),
                # that division header itself, which is a key rather than a code nothing covers
                ("04 00 00", "04 00 00", "exact"),
                # a code whose only mapped ancestor is a division header keyed that way already
                ("26 05 19", "26 00 00", "family"),
                # a code under two mapped ancestors: the nearer one wins, never the division
                ("31 50 13", "31 50 00", "family"),
                # a code the map keys outright is still exact, never resolved by family
                ("09 21 16", "09 21 16", "exact"),
            ]
            for code, want_key, want_how in expected:
                got = resolver.resolve(code, folded)
                if got != (want_key, want_how):
                    errors.append(
                        f"{code} resolved to {got}, expected ({want_key!r}, {want_how!r})"
                    )
                else:
                    resolved_cases += 1
            # A trade file is keyed at the broadest code it actually covers: where a division maps
            # exactly one file, that file sits at the division header, so a package drafted anywhere
            # in the division reaches it. A division mapping several files keeps each at its own
            # section, since a bare division header there would have to pick one of several.
            by_division: dict[str, list[str]] = {}
            for key in trades:
                by_division.setdefault(resolver.fold(key)[:2], []).append(key)
            for division, keys_here in sorted(by_division.items()):
                if len(keys_here) != 1:
                    continue
                header = f"{division} 00 00"
                if keys_here[0] != header:
                    errors.append(
                        f"division {division} maps only {keys_here[0]}, which should be keyed at "
                        f"{header} so a package drafted anywhere in the division reaches it"
                    )
            sole_file_divisions = sum(1 for keys_here in by_division.values() if len(keys_here) == 1)

            # A division the map holds nothing under at any level stays unresolved, so the plan
            # names the package rather than reading it for a trade nobody chose.
            unmapped_division = resolver.resolve("13 34 19", folded)
            if unmapped_division is not None:
                errors.append(
                    f"13 34 19 resolved to {unmapped_division}, expected nothing: no trade in the "
                    f"map covers that division"
                )
            else:
                resolved_cases += 1

    exceptions = ", ".join(sorted(unmapped)) if unmapped else "none"
    detail = (
        f"{len(trades)} trades mapped over {len(pinned)} manifest trade files, both directions; "
        f"{len(declared_types)} sheet types pinned and equal to the recognizer's set; "
        f"{len(seams)} seam pairs, every member a mapped trade; "
        f"{len(empty_families)} trade(s) mapped with no sheet family and a reason "
        f"({', '.join(empty_families) if empty_families else 'none'}); "
        f"{resolved_cases} of 6 catalog codes resolved to the trade file covering them, by nearest "
        f"CSI ancestor, checked against the shipped map; every one of the {sole_file_divisions} "
        f"divisions mapping a single trade file keyed at its division header; "
        f"named exception(s) allowed with a reason: {exceptions}"
    )
    if errors:
        detail += " | " + "; ".join(errors)

    return Result(name, passed=len(errors) == 0, detail=detail)


# --------------------------------------------------------------------------- #
# Check: the plan inventory script
# --------------------------------------------------------------------------- #
#
# The scope run's lead no longer holds a sheet row: a fetch agent puts the grid on disk and the
# shipped plan script turns it into counts and then into each window's read plan. The script is the
# only thing standing between a grid file and a plan, so this runs it end to end over invented
# fixtures and asserts its numbers against a tally this check computes itself.
#
# The extraction below is written independently of the script's own, so the two agreeing is
# evidence rather than a tautology. Window 3 is checked hardest that way: the script recomputes
# window 2's selection from the same inputs and never parses window 2's plan file, and this check
# does the opposite, reading window 2's own unit lines and asserting window 3 holds exactly the
# inventory minus them.
#
# Honest bound, stated in the detail line: the fixtures are invented, and the kinds and index
# fixtures are shaped against verbs that do not exist yet, so this proves the script's arithmetic,
# its ordering and its refusals, and nothing about how a real record read arrives.

PLAN_INVENTORY_SCRIPT = ("scripts", "plan_inventory.py")
TRADE_CODE_SCRIPT = ("scripts", "trade_code.py")

_PLAN_PASS_RE = re.compile(r"^### (\S+?)\.\s")
_PLAN_UNIT_RE = re.compile(r"^(\d+)\. (\S+), page (\d+): (.*)$")
_PLAN_FIELD_RE = re.compile(r"^([a-z][a-z ]*): (.*)$")
_LEFT_OUT_HEADING = "## Deliberately left out"

# The four recognizer types window 1 selects. Named here independently of the script's own list.
_VOCABULARY_SHEET_TYPES = {"schedule", "legend", "notes", "cover-index"}


def _load_script_module(script_path: Path, module_name: str):
    """
    Import a shipped script in-process, so the check runs no subprocess and no model. The source is
    compiled here rather than imported through the loader: a .pyc records the source mtime in whole
    seconds, so a script edited twice inside one second to the same byte length loads the earlier
    bytecode, and the harness would report on a version of the script that is no longer on disk.
    """
    # A shipped script imports its siblings (the shared trade code resolver), and an import caches
    # the module, so a second load in one process would reuse the copy the first load read. Dropping
    # the scripts directory's own modules first means every load reads what is on disk now.
    scripts_dir = script_path.resolve().parent
    for loaded_name, loaded in list(sys.modules.items()):
        loaded_file = getattr(loaded, "__file__", None)
        if loaded_file and Path(loaded_file).resolve().parent == scripts_dir:
            del sys.modules[loaded_name]

    module = importlib.util.module_from_spec(
        importlib.util.spec_from_loader(module_name, loader=None)
    )
    module.__file__ = str(script_path)
    exec(compile(script_path.read_text(encoding="utf-8"), str(script_path), "exec"), module.__dict__)
    return module


def _run_plan_script(module, argv: list[str]) -> tuple[int, str, str]:
    """Call the script's own main() and capture its exit code and both streams."""
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        code = module.main(argv)
    return code, out.getvalue().strip(), err.getvalue().strip()


def _plan_passes(read_plan: str) -> list[dict]:
    """
    The read plan's passes, read straight off the file: the pass id, the `key: value` lines of its
    block, and its unit lines as (sheet number, page). Stops at the left-out section, whose entries
    share the unit line's shape.
    """
    passes: list[dict] = []
    for line in read_plan.splitlines():
        if line.strip() == _LEFT_OUT_HEADING:
            break
        heading = _PLAN_PASS_RE.match(line)
        if heading:
            passes.append({"id": heading.group(1), "fields": {}, "units": []})
            continue
        if not passes:
            continue
        unit = _PLAN_UNIT_RE.match(line)
        if unit:
            passes[-1]["units"].append((unit.group(2), int(unit.group(3))))
            continue
        field = _PLAN_FIELD_RE.match(line)
        if field:
            passes[-1]["fields"][field.group(1)] = field.group(2)
    return passes


def _expected_split(n: int, cap: int) -> list[int]:
    """
    The split this check computes for itself: a pass over the cap becomes as few parts as will hold
    it, of as even a size as possible, earlier parts taking the remainder.
    """
    if n <= cap:
        return [n]
    count = math.ceil(n / cap)
    base, extra = divmod(n, count)
    return [base + (1 if i < extra else 0) for i in range(count)]


def _check_split_arithmetic(passes: list[dict], cap: int, errors: list[str], where: str) -> int:
    """
    Every pass whose id ends in a single letter after a shared stem is a part of one split pass.
    Checks the part ids run a, b, c with no gap, the sizes are the balanced split of the total, and
    no part is over the cap. Returns how many passes were split.
    """
    stems: dict[str, list[dict]] = {}
    for plan_pass in passes:
        stem = plan_pass["id"]
        if len(stem) > 1 and stem[-1] in string.ascii_lowercase and stem[:-1] in {
            p["id"][:-1] for p in passes if len(p["id"]) > 1 and p["id"][-1] in string.ascii_lowercase
        }:
            stem = stem[:-1]
        stems.setdefault(stem, []).append(plan_pass)

    split = 0
    for stem, parts in stems.items():
        sizes = [len(p["units"]) for p in parts]
        if any(size > cap for size in sizes):
            errors.append(f"{where}: pass {stem} has a part of {max(sizes)} units, over the cap of {cap}")
        if len(parts) == 1:
            continue
        split += 1
        expected_ids = [f"{stem}{letter}" for letter in string.ascii_lowercase[: len(parts)]]
        if [p["id"] for p in parts] != expected_ids:
            errors.append(f"{where}: pass {stem} split into {[p['id'] for p in parts]}, expected {expected_ids}")
        expected_sizes = _expected_split(sum(sizes), cap)
        if sizes != expected_sizes:
            errors.append(f"{where}: pass {stem} split {sizes}, expected {expected_sizes}")
    return split


def _pass_trade(plan_pass: dict) -> str:
    """
    The map key a pass reads for. Where the package's own code is not itself a key, the block names
    the broader key covering it, and that key is the one the map declares seams on, so it is the one
    every seam assertion has to work from.
    """
    return plan_pass["fields"].get("trade file covers", "") or plan_pass["fields"].get("reads for", "")


def _trades_in_order(passes: list[dict]) -> list[str]:
    """
    The trades window 2 plans, in the order their passes run, each named once. A pass block carries
    the catalog id verbatim on its `reads for` line, and a pass split into parts repeats it on every
    part, so the runs are collapsed here: seam adjacency is a property of the trade, not of a part.
    """
    order: list[str] = []
    for plan_pass in passes:
        trade_id = _pass_trade(plan_pass)
        if trade_id and (not order or order[-1] != trade_id):
            order.append(trade_id)
    return order


def _contiguous_runs(trade_order: list[str]) -> dict[str, int]:
    """How many separate places each trade occupies. More than one means its passes are not together."""
    runs: dict[str, int] = {}
    for trade_id in trade_order:
        runs[trade_id] = runs.get(trade_id, 0) + 1
    return runs


def _seam_order_errors(
    trade_order: list[str], seam_pairs: list[tuple[str, str]], bounds: str, where: str
) -> list[str]:
    """
    Every seam pair whose two trades are both planned must either sit side by side, or have its group
    named on the bounds line as one no order can fully satisfy. Silently dropping a declared seam is
    the failure this exists to catch: the runner's overlap scan only fires when the two run together.
    """
    errors: list[str] = []
    position = {trade_id: i for i, trade_id in enumerate(trade_order)}
    for first, second in seam_pairs:
        if first not in position or second not in position:
            continue
        if abs(position[first] - position[second]) == 1:
            continue
        if first in bounds and second in bounds:
            continue
        errors.append(
            f"{where}: the seam {first} with {second} is neither adjacent nor named on the bounds line"
        )
    return errors


def check_plan_inventory(plugin_path: Path, marketplace_root: Path) -> Result:
    name = "plan-inventory"
    script = plugin_path.joinpath(*PLAN_INVENTORY_SCRIPT)
    if not script.is_file():
        return Result(name, False, detail=f"plan script not found at {script}")

    fixtures = marketplace_root / "harness" / "fixtures"
    grid_fixture = fixtures / "set-grid-fixture.json"
    if not grid_fixture.is_file():
        return Result(name, False, detail=f"grid fixture not found at {grid_fixture}")

    trade_knowledge = plugin_path / "trade-knowledge"

    try:
        module = _load_script_module(script, "plan_inventory")
    except Exception as e:
        return Result(name, False, detail=f"cannot import {script.name}: {e}")

    # The independent tally, computed here off the fixtures and never off the script's output.
    try:
        fixture_rows = json.loads(grid_fixture.read_text(encoding="utf-8"))["sheets"]
        # The index pages are one leftover kind each, the shape index_citations_leftover returns,
        # plus the located-code page the script also accepts. Both are read here the way the script
        # reads them, so the tally below is this file's own and never the script's output.
        index_pages = [
            json.loads(path.read_text(encoding="utf-8"))
            for path in sorted((fixtures / "index-fixture").iterdir())
            if path.is_file()
        ]
        leftover_rows = [row for page in index_pages for row in page.get("rows", [])]
        location_rows = [row for page in index_pages for row in page.get("locations", [])]
        trade_sheets = json.loads(
            (trade_knowledge / "trade-sheets.json").read_text(encoding="utf-8")
        )
        seam_pairs = [(pair[0], pair[1]) for pair in trade_sheets["seams"]]
    except Exception as e:
        return Result(name, False, detail=f"fixture: {e}")

    expected_rows = len(fixture_rows)
    expected_by_discipline: dict[str, int] = {}
    expected_cross: dict[str, dict[str, int]] = {}
    page_of: dict[str, int] = {}
    for row in fixture_rows:
        discipline = row.get("discipline") or "(none)"
        sheet_type = row.get("sheetType") or "(untyped)"
        expected_by_discipline[discipline] = expected_by_discipline.get(discipline, 0) + 1
        expected_cross.setdefault(discipline, {})
        expected_cross[discipline][sheet_type] = expected_cross[discipline].get(sheet_type, 0) + 1
        page_of[row["sheetNumber"]] = row["pageInPdf"]

    out_dir = Path(__file__).parent / ".test-results" / "plan-inventory"
    errors: list[str] = []
    # The partial-input notes window 2 asserts, filled in below and named in the detail line.
    fragments: list[str] = []

    code, bounds, err = _run_plan_script(
        module,
        ["inventory", "--grid", str(grid_fixture), "--expect-count", str(expected_rows),
         "--out-dir", str(out_dir)],
    )
    if code != 0:
        return Result(name, False, detail=f"the inventory mode refused the fixture: {err or bounds}")
    if f"{expected_rows} rows" not in bounds:
        errors.append(f"the inventory bounds line does not name its row count: {bounds!r}")

    try:
        written = json.loads((out_dir / "inventory.json").read_text(encoding="utf-8"))
    except Exception as e:
        return Result(name, False, detail=f"inventory.json: {e}")

    written_counts = written.get("counts", {})
    if len(written.get("sheets", [])) != expected_rows:
        errors.append(
            f"inventory.json holds {len(written.get('sheets', []))} rows and the fixture has "
            f"{expected_rows}"
        )
    if written_counts.get("byDiscipline") != expected_by_discipline:
        errors.append(
            f"per-discipline counts disagree with the independent tally: "
            f"{written_counts.get('byDiscipline')} against {expected_by_discipline}"
        )
    if written_counts.get("byDisciplineAndSheetType") != expected_cross:
        errors.append("the discipline-by-sheet-type cross tab disagrees with the independent tally")

    off_code, _off_bounds, off_err = _run_plan_script(
        module,
        ["inventory", "--grid", str(grid_fixture), "--expect-count", str(expected_rows + 1),
         "--out-dir", str(out_dir / "off-by-one")],
    )
    if off_code != 1:
        errors.append(f"--expect-count off by one exited {off_code}, not 1")
    elif len(off_err.splitlines()) != 1:
        errors.append("the --expect-count refusal is not one line on stderr")

    inventory_json = str(out_dir / "inventory.json")
    packages = str(fixtures / "packages-fixture.json")
    kinds = str(fixtures / "kinds-fixture.json")
    index_dir = str(fixtures / "index-fixture")

    # ------------------------------------------------------------------ #
    # Window 1: the vocabulary, plus one include and one exclude
    # ------------------------------------------------------------------ #
    include_pattern = "A-4.*"
    exclude_pattern = "S-1.01"
    w1_path = out_dir / "read-plan-w1.md"
    code, w1_bounds, err = _run_plan_script(
        module,
        ["plan", "--window", "1", "--inventory", inventory_json, "--packages", packages,
         "--trade-knowledge", str(trade_knowledge),
         "--include", f"{include_pattern}:the elevations carry the window and finish marks",
         "--exclude", f"{exclude_pattern}:structural notes carry no scope this run reads",
         "--out", str(w1_path)],
    )
    w1_passes: list[dict] = []
    if code != 0:
        errors.append(f"window 1 refused the fixtures: {err}")
    else:
        expected_w1 = {
            r["sheetNumber"] for r in fixture_rows
            if (r.get("sheetType") or "") in _VOCABULARY_SHEET_TYPES
        }
        expected_w1 |= {
            r["sheetNumber"] for r in fixture_rows
            if fnmatch.fnmatchcase(r["sheetNumber"], include_pattern)
        }
        excluded = {
            r["sheetNumber"] for r in fixture_rows
            if fnmatch.fnmatchcase(r["sheetNumber"], exclude_pattern)
        }
        expected_w1 -= excluded
        expected_w1_disciplines = {
            (r.get("discipline") or "(none)") for r in fixture_rows
            if r["sheetNumber"] in expected_w1
        }
        for fragment in (
            f"units {len(expected_w1)}",
            f"passes {len(expected_w1_disciplines)}",
            f"excluded {len(excluded)}",
            f"unassigned {expected_rows - len(expected_w1) - len(excluded)}",
        ):
            if fragment not in w1_bounds:
                errors.append(f"the window 1 bounds line does not name `{fragment}`: {w1_bounds!r}")
        w1_passes = _plan_passes(w1_path.read_text(encoding="utf-8"))
        w1_sheets = [sheet for p in w1_passes for sheet, _page in p["units"]]
        if set(w1_sheets) != expected_w1:
            errors.append(
                f"window 1 planned {sorted(set(w1_sheets))}, expected {sorted(expected_w1)}"
            )
        if len(w1_sheets) != len(set(w1_sheets)):
            errors.append("a sheet appears in more than one window 1 unit line")
        _check_split_arithmetic(w1_passes, 12, errors, "window 1")

    # ------------------------------------------------------------------ #
    # Window 2: one pass per package
    # ------------------------------------------------------------------ #
    w2_path = out_dir / "read-plan-w2.md"
    code, w2_bounds, err = _run_plan_script(
        module,
        ["plan", "--window", "2", "--inventory", inventory_json, "--packages", packages,
         "--kinds", kinds, "--index", index_dir, "--trade-knowledge", str(trade_knowledge),
         "--out", str(w2_path)],
    )
    w2_passes: list[dict] = []
    w2_sheets: set[str] = set()
    w2_split = 0
    if code != 0:
        errors.append(f"window 2 refused the fixtures: {err}")
    else:
        w2_passes = _plan_passes(w2_path.read_text(encoding="utf-8"))
        w2_sheets = {sheet for p in w2_passes for sheet, _page in p["units"]}
        # One package carries a trade the map does not hold and another a trade whose families name
        # nothing in this set. Both must be named on the bounds line by code, in their own field:
        # the code alone would also match where some other field happens to mention it.
        for fragment, what in (
            ("packages with no sheet family mapped 1 (13 34 19)", "the unmapped package"),
            (
                "packages whose families named no sheet 1 (32 90 00)",
                "the package whose families named no sheet",
            ),
        ):
            if fragment not in w2_bounds:
                errors.append(
                    f"the window 2 bounds line does not name {what} in its own field "
                    f"(`{fragment}`): {w2_bounds!r}"
                )
        counted: dict[str, int] = {}
        for plan_pass in w2_passes:
            for sheet, _page in plan_pass["units"]:
                counted[sheet] = counted.get(sheet, 0) + 1
        read_twice = sum(1 for n in counted.values() if n > 1)
        if f"sheets read for more than one trade {read_twice}" not in w2_bounds:
            errors.append(
                f"the window 2 bounds line's overlap count disagrees with the plan's own unit lines "
                f"({read_twice}): {w2_bounds!r}"
            )
        if read_twice == 0:
            errors.append("the window 2 fixture proves nothing about overlap: no sheet is read twice")
        if f"sheets no trade reads {expected_rows - len(w2_sheets)}" not in w2_bounds:
            errors.append(f"the window 2 bounds line's unread count is not the inventory minus what it planned")
        # Four partial-input notes the fixtures are built to trip: a code row carrying a kind and no
        # defining sheet, a kind whose code rows fall short of the count the record gave for it, an
        # index location row naming no kind, and a leftover kind whose rows fall short of its own
        # total. Each must reach the bounds line, or a run would report a clean number over an input
        # it could only partly use.
        kinds_documents = json.loads(Path(kinds).read_text(encoding="utf-8"))
        code_rows = [row for doc in kinds_documents for row in doc.get("codes", [])]
        codes_without_sheet = sum(1 for row in code_rows if not row.get("sheetNumber"))
        kinds_short = sorted(
            f"{doc['codes'][0]['kind']} {len(doc['codes'])} of {doc['count']}"
            for doc in kinds_documents
            if doc.get("codes") and len(doc["codes"]) < doc.get("count", 0)
        )
        locations_without_field = sum(
            1 for row in location_rows
            if not row.get("kind") or not row.get("sheetNumber")
        )
        leftover_short = sorted(
            f"{page['kind']} {len(page['rows'])} of {page['total']}"
            for page in index_pages
            if page.get("rows") is not None and len(page["rows"]) < page.get("total", 0)
        )
        if codes_without_sheet == 0 or locations_without_field == 0 or not leftover_short:
            errors.append("the fixtures no longer trip every partial-input note")
        fragments += [
            f"definition codes with no defining sheet {codes_without_sheet}",
            f"index locations naming no kind or no sheet {locations_without_field}",
            "leftover kinds short of their own total: " + ", ".join(leftover_short),
        ]
        if kinds_short:
            fragments.append("definition kinds short of their own count: " + ", ".join(kinds_short))
        for fragment in fragments:
            if fragment not in w2_bounds:
                errors.append(f"the window 2 bounds line does not carry `{fragment}`: {w2_bounds!r}")
        # A package whose code the map does not key reads for the family's trade file, and a run has
        # to show that it did. Which packages those are is resolved here off the map, never a list
        # written down beside the fixture that could go stale as the map is re-keyed.
        by_family: list[str] = []
        try:
            resolver = _load_script_module(plugin_path.joinpath(*TRADE_CODE_SCRIPT), "trade_code")
        except Exception as e:
            errors.append(f"cannot import the shared resolver: {e}")
        else:
            folded_keys = {resolver.fold(key): key for key in trade_sheets["trades"]}
            for row in json.loads(Path(packages).read_text(encoding="utf-8"))["packages"]:
                code = row.get("tradeCode", "")
                found = resolver.resolve(code, folded_keys)
                if found is not None and found[1] == "family":
                    by_family.append(code)
        if len(by_family) < 2:
            errors.append(
                f"the packages fixture carries {len(by_family)} codes resolved by family, too few "
                f"to prove the window 2 plan reports them"
            )
        if f"resolved by family {len(by_family)}" not in w2_bounds:
            errors.append(
                f"the window 2 bounds line does not count what it resolved by family: {w2_bounds!r}"
            )
        for code in by_family:
            if code not in w2_bounds:
                errors.append(f"the window 2 bounds line does not name {code} as resolved by family")
        w2_split = _check_split_arithmetic(w2_passes, 12, errors, "window 2")
        if w2_split == 0:
            errors.append("the window 2 fixture proves nothing about the twelve-unit split")
        # The packages file names two seam groups and splits both: a pair (09 21 16 with 09 91 00)
        # with another package between them, and a three-trade chain (08 40 00, 08 50 00, 12 20 00,
        # where 08 50 00 seams with both of the others) with a package inside it. Every declared seam
        # among the trades planned here must come back adjacent, or its group must be named on the
        # bounds line; the three-trade chain is the shape a pairwise move cannot get right.
        trade_order = _trades_in_order(w2_passes)
        for trade_id, runs in _contiguous_runs(trade_order).items():
            if runs > 1:
                errors.append(f"window 2 splits trade {trade_id} across {runs} places in its order")
        if trade_order.count("08 40 00") and trade_order.count("12 20 00"):
            chain = sorted(trade_order.index(t) for t in ("08 40 00", "08 50 00", "12 20 00"))
            if chain != list(range(chain[0], chain[0] + 3)):
                errors.append(
                    f"the three-trade seam chain is not contiguous in window 2's order: {trade_order}"
                )
        else:
            errors.append("the window 2 fixture proves nothing about a trade in two seams")
        # The seam assertions say nothing at all if the map and the packages between them declare no
        # seam over the trades planned here, so the fixture's own reach is asserted before them.
        live_seams = [(a, b) for a, b in seam_pairs if a in trade_order and b in trade_order]
        if len(live_seams) < 3:
            errors.append(
                f"the window 2 fixture exercises {len(live_seams)} declared seams, too few to prove "
                f"a pair and a three-trade chain"
            )
        errors.extend(_seam_order_errors(trade_order, seam_pairs, w2_bounds, "window 2"))
        for plan_pass in w2_passes:
            declared = {
                s.strip() for s in plan_pass["fields"].get("seam with", "").split(",") if s.strip()
            }
            trade_id = _pass_trade(plan_pass)
            index_of = trade_order.index(trade_id) if trade_id in trade_order else None
            beside = set()
            if index_of is not None:
                for i in (index_of - 1, index_of + 1):
                    if 0 <= i < len(trade_order):
                        beside.add(trade_order[i])
            stranded = declared - beside
            if stranded:
                errors.append(
                    f"pass {plan_pass['id']} claims a seam with {sorted(stranded)}, which its own "
                    f"order does not put next to it"
                )

    # ------------------------------------------------------------------ #
    # Window 3: the leftover, checked against window 2's own unit lines
    # ------------------------------------------------------------------ #
    w3_path = out_dir / "read-plan-w3.md"
    code, w3_bounds, err = _run_plan_script(
        module,
        ["plan", "--window", "3", "--inventory", inventory_json, "--packages", packages,
         "--kinds", kinds, "--index", index_dir, "--trade-knowledge", str(trade_knowledge),
         "--out", str(w3_path)],
    )
    w3_passes: list[dict] = []
    if code != 0:
        errors.append(f"window 3 refused the fixtures: {err}")
    else:
        w3_passes = _plan_passes(w3_path.read_text(encoding="utf-8"))
        w3_sheets = [sheet for p in w3_passes for sheet, _page in p["units"]]
        expected_w3 = {r["sheetNumber"] for r in fixture_rows} - w2_sheets
        if set(w3_sheets) != expected_w3:
            errors.append(
                f"window 3 is not the inventory minus what window 2 read: planned "
                f"{sorted(set(w3_sheets))}, expected {sorted(expected_w3)}"
            )
        if len(w3_sheets) != len(set(w3_sheets)):
            errors.append("a sheet appears in more than one window 3 unit line")
        expected_w3_disciplines = {
            (r.get("discipline") or "(none)") for r in fixture_rows if r["sheetNumber"] in expected_w3
        }
        for fragment in (f"sheets {len(expected_w3)}", f"passes {len(expected_w3_disciplines)}"):
            if fragment not in w3_bounds:
                errors.append(f"the window 3 bounds line does not name `{fragment}`: {w3_bounds!r}")
        open_on_leftover = sum(
            1 for row in leftover_rows if row.get("sheet") in expected_w3
        )
        total_open = len(leftover_rows)
        if f"open entries {open_on_leftover} of {total_open}" not in w3_bounds:
            errors.append(
                f"the window 3 bounds line does not carry {open_on_leftover} of {total_open} open "
                f"entries: {w3_bounds!r}"
            )
        _check_split_arithmetic(w3_passes, 12, errors, "window 3")

    # ------------------------------------------------------------------ #
    # Every unit line's page reference, checked against the fixture grid
    # ------------------------------------------------------------------ #
    planned = [unit for p in w1_passes + w2_passes + w3_passes for unit in p["units"]]
    misplaced = [
        f"{sheet} on page {page} where the grid says {page_of.get(sheet)}"
        for sheet, page in planned
        if page_of.get(sheet) != page
    ]
    if misplaced:
        errors.append("unit lines cite a page the grid does not: " + "; ".join(misplaced[:5]))

    # ------------------------------------------------------------------ #
    # The ordering over the shipped map itself, not just over the fixture
    # ------------------------------------------------------------------ #
    #
    # The fixture holds two seam groups. The shipped map holds twenty one seam pairs over the whole
    # catalog, and a project that buys a package for every mapped trade meets all of them at once.
    # This runs the ordering over exactly that case, one pass per mapped trade, and asserts the same
    # property the fixture asserts: every declared pair is adjacent, or its group came back named.
    map_passes = [
        {"tradeId": trade_id, "id": entry["knowledge"], "units": []}
        for trade_id, entry in trade_sheets["trades"].items()
    ]
    try:
        apart_groups = module._order_by_seams(map_passes, {
            "trades": trade_sheets["trades"],
            "seams": seam_pairs,
        })
    except Exception as e:
        errors.append(f"the ordering raised over the shipped map: {e}")
    else:
        map_order = [plan_pass["tradeId"] for plan_pass in map_passes]
        if sorted(map_order) != sorted(trade_sheets["trades"]):
            errors.append("the ordering over the shipped map lost or repeated a trade")
        named = " ".join(" ".join(group) for group in apart_groups)
        errors.extend(_seam_order_errors(map_order, seam_pairs, named, "the shipped map"))
        for plan_pass in map_passes:
            declared = {
                s.strip() for s in str(plan_pass.get("seamWith", "")).split(",") if s.strip()
            }
            at = map_order.index(plan_pass["tradeId"])
            beside = {map_order[i] for i in (at - 1, at + 1) if 0 <= i < len(map_order)}
            if declared - beside:
                errors.append(
                    f"over the shipped map, {plan_pass['tradeId']} claims a seam with "
                    f"{sorted(declared - beside)} that its own order does not put next to it"
                )

    # ------------------------------------------------------------------ #
    # An index that ran without its located-code half says so, never a clean number
    # ------------------------------------------------------------------ #
    code, partial_bounds, err = _run_plan_script(
        module,
        ["plan", "--window", "2", "--inventory", inventory_json, "--packages", packages,
         "--kinds", kinds, "--index", str(fixtures / "index-fixture-no-locations"),
         "--trade-knowledge", str(trade_knowledge), "--out", str(out_dir / "read-plan-w2-partial.md")],
    )
    if code != 0:
        errors.append(f"window 2 refused an index with no located codes: {err}")
    elif "index locations not present" not in partial_bounds:
        errors.append(
            f"window 2 over an index with no located codes reported a clean number: {partial_bounds!r}"
        )

    # ------------------------------------------------------------------ #
    # Refusals, each exiting 1 with one line on stderr
    # ------------------------------------------------------------------ #
    refusals: list[tuple[str, list[str], str]] = [
        (
            "a package row with no tradeCode",
            ["plan", "--window", "2", "--inventory", inventory_json,
             "--packages", str(fixtures / "packages-fixture-no-trade-code.json"),
             "--kinds", kinds, "--index", index_dir, "--trade-knowledge", str(trade_knowledge),
             "--out", str(out_dir / "refused.md")],
            "tradeCode",
        ),
        (
            "two codes of one family on one trade file",
            ["plan", "--window", "2", "--inventory", inventory_json,
             "--packages", str(fixtures / "packages-fixture-family-collision.json"),
             "--kinds", kinds, "--index", index_dir, "--trade-knowledge", str(trade_knowledge),
             "--out", str(out_dir / "refused.md")],
            "04 00 00",
        ),
        (
            "two packages on one trade",
            ["plan", "--window", "2", "--inventory", inventory_json,
             "--packages", str(fixtures / "packages-fixture-duplicate-trade.json"),
             "--kinds", kinds, "--index", index_dir, "--trade-knowledge", str(trade_knowledge),
             "--out", str(out_dir / "refused.md")],
            "pkg-0009",
        ),
        (
            "a kinds row with no kind",
            ["plan", "--window", "2", "--inventory", inventory_json, "--packages", packages,
             "--kinds", str(fixtures / "kinds-fixture-no-kind.json"), "--index", index_dir,
             "--trade-knowledge", str(trade_knowledge), "--out", str(out_dir / "refused.md")],
            "kind",
        ),
        (
            "an index page carrying neither array",
            ["plan", "--window", "2", "--inventory", inventory_json, "--packages", packages,
             "--kinds", kinds, "--index", str(fixtures / "index-fixture-broken"),
             "--trade-knowledge", str(trade_knowledge), "--out", str(out_dir / "refused.md")],
            "locations",
        ),
        (
            "a leftover page read off a pass that has not finished",
            ["plan", "--window", "3", "--inventory", inventory_json, "--packages", packages,
             "--kinds", kinds, "--index", str(fixtures / "index-fixture-not-succeeded"),
             "--trade-knowledge", str(trade_knowledge), "--out", str(out_dir / "refused.md")],
            "not succeeded",
        ),
        (
            "window 2 with no --kinds",
            ["plan", "--window", "2", "--inventory", inventory_json, "--packages", packages,
             "--index", index_dir, "--trade-knowledge", str(trade_knowledge),
             "--out", str(out_dir / "refused.md")],
            "--kinds",
        ),
        (
            "window 3 with no --index",
            ["plan", "--window", "3", "--inventory", inventory_json, "--packages", packages,
             "--kinds", kinds, "--trade-knowledge", str(trade_knowledge),
             "--out", str(out_dir / "refused.md")],
            "--index",
        ),
        (
            "window 1 with no --packages",
            ["plan", "--window", "1", "--inventory", inventory_json,
             "--trade-knowledge", str(trade_knowledge), "--out", str(out_dir / "refused.md")],
            "--packages",
        ),
        (
            "an include pattern matching no sheet",
            ["plan", "--window", "1", "--inventory", inventory_json, "--packages", packages,
             "--trade-knowledge", str(trade_knowledge),
             "--include", "Z-9.*:a family that is not in this set",
             "--out", str(out_dir / "refused.md")],
            "Z-9.*",
        ),
        (
            "an include with no colon",
            ["plan", "--window", "1", "--inventory", inventory_json, "--packages", packages,
             "--trade-knowledge", str(trade_knowledge), "--include", "A-4.01",
             "--out", str(out_dir / "refused.md")],
            "reason",
        ),
    ]
    for what, argv, must_name in refusals:
        code, _refused_bounds, err = _run_plan_script(module, argv)
        if code != 1:
            errors.append(f"{what}: exited {code}, not 1")
        elif len(err.splitlines()) != 1:
            errors.append(f"{what}: the refusal is not one line on stderr")
        elif must_name not in err:
            errors.append(f"{what}: the refusal does not name {must_name}: {err!r}")

    detail = (
        f"{expected_rows} fixture sheets over {len(expected_by_discipline)} disciplines: "
        f"the inventory tallies checked against an independent count, "
        f"{len(planned)} unit lines over three windows with every page checked against the grid, "
        f"window 1's selection and its bounds counts checked against an independent tally, "
        f"window 2's overlap and unread counts checked against its own unit lines, "
        f"{w2_split} pass split at the twelve-unit cap with ids and sizes checked against a "
        f"balanced split computed here, two seam groups (a pair and a three-trade chain) each "
        f"contiguous with no pass claiming a seam its own order contradicts, the same seam property "
        f"checked over all {len(seam_pairs)} pairs of the shipped map with one pass per mapped "
        f"trade, {len(fragments)} partial-input notes asserted by their text, window 3 checked to be "
        f"exactly the inventory minus window 2's own unit lines, an index with no located codes "
        f"reported as a partial input, "
        f"{len(refusals)} broken invocations each refused in one line naming what is missing"
    )
    # An honest bound, not a pass: the fixtures are invented and small. They carry the field names
    # the shipped verbs return, so a rename on the record's side would fail here, but nothing about
    # a real grid, a real definitions read or a real leftover read is proved by them.
    detail += "; bound: invented fixtures, not a real grid, definitions read or leftover read"
    if errors:
        detail += " | " + "; ".join(errors)

    return Result(name, passed=len(errors) == 0, detail=detail)


# --------------------------------------------------------------------------- #
# Check: no shipped text names `fork` as a subagent type (PLU-1557)
# --------------------------------------------------------------------------- #
#
# A pass runner invented a wait primitive by dispatching fork agents -- one told to wait for a
# reader's completion notification, two told to do nothing and return done. The Agent tool has no
# such type; the runner's dispatch shape is a single foreground call that already blocks until the
# reader reports. This is the regression guard: no shipped skill or agent file may tell an agent to
# dispatch a `fork` subagent, in either the `subagent_type:` dispatch-line shape this codebase's own
# templates use, or a `tools: Agent(fork)` frontmatter declaration. Ordinary English uses of "fork"
# (a forklift, a decision fork -- both real, current trade-knowledge vocabulary) are untouched: the
# pattern only matches "fork" sitting immediately after one of those two anchors, and trade-knowledge
# files are outside this check's file scope regardless.

_FORK_SUBAGENT_RE = re.compile(
    r'subagent_type["\':=]*\s*["\']?fork\b|Agent\(\s*fork\s*\)',
    re.IGNORECASE,
)


def _scan_file_for_fork_subagent(path: Path, label: str) -> list[str]:
    hits: list[str] = []
    try:
        text = path.read_text(encoding="utf-8")
    except Exception as e:
        return [f"{label}: read error: {e}"]
    for i, line in enumerate(text.splitlines(), 1):
        m = _FORK_SUBAGENT_RE.search(line)
        if m:
            hits.append(
                f"{label}:{i}: names `fork` as a subagent type — {m.group(0)!r} in: "
                f"{line.strip()[:160]}"
            )
    return hits


def check_no_fork_subagent(plugin_path: Path) -> Result:
    name = "no-fork-subagent-type"
    skills_dir = plugin_path / "skills"
    agents_dir = plugin_path / "agents"

    files: list[Path] = []
    if skills_dir.is_dir():
        files.extend(sorted(skills_dir.rglob("SKILL.md")))
    if agents_dir.is_dir():
        files.extend(sorted(agents_dir.rglob("*.md")))

    errors: list[str] = []
    for f in files:
        label = f"{f.parent.name}/{f.name}" if f.name == "SKILL.md" else f.name
        errors.extend(_scan_file_for_fork_subagent(f, label))

    detail = f"{len(files)} skill/agent files scanned"
    if errors:
        detail += " | " + "; ".join(errors)

    return Result(name, passed=len(errors) == 0, detail=detail)


# --------------------------------------------------------------------------- #
# Public entry point
# --------------------------------------------------------------------------- #

def run_static_checks(plugin_path: Path, marketplace_root: Path) -> tuple[list[Result], bool]:
    """Run all Layer 1 checks. Returns (results, all_passed)."""
    results = [
        check_cli_validate(plugin_path),
        check_version_quadruple(plugin_path, marketplace_root),
        check_skills(plugin_path),
        check_agents(plugin_path),
        check_description_contract(plugin_path),
        check_banned_strings(plugin_path, marketplace_root),
        check_retired_vocabulary(plugin_path, marketplace_root),
        check_bold_emphasis(plugin_path, marketplace_root),
        check_titlecase_labels(plugin_path, marketplace_root),
        check_mcp_url(plugin_path),
        check_no_absolute_paths(plugin_path, marketplace_root),
        check_question_failure_boundary(plugin_path),
        check_question_rfi_bar(plugin_path),
        check_question_plain_words_pointer(plugin_path),
        check_ledger_fixed_shape(plugin_path),
        check_runner_mode_set(plugin_path),
        check_pass_knowledge_excerpt(plugin_path),
        check_trade_sheet_map(plugin_path),
        check_plan_inventory(plugin_path, marketplace_root),
        check_no_fork_subagent(plugin_path),
    ]
    all_passed = all(r.passed for r in results)
    return results, all_passed
