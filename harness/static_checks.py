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
     EXPECTED_AGENTS exactly, in both directions (`scope-reader`,
     `scope-reviewer`, `scope-round-runner`); and no agent declares a
     frontmatter field the runtime ignores for plugin-shipped agents
     (`hooks`, `mcpServers`, `permissionMode`). Checks 3 and 4b both validate
     the frontmatter block with PyYAML when it is importable, falling back to
     a stdlib check for the unquoted ": " failure when it is not.
  5. No banned string in shipped text: client-name denylist, `PLU-\\d+`,
     internal vault filenames, `MOSOT`, em dash, middle dot. Em dash and
     middle dot are exempt inside fenced code blocks and inline code spans
     (data, not prose); every other pattern applies to code too. Every
     shipped file takes the same scan: there is no lenient population and no
     exemption list.
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
      partly undone without failing the release. The set is pass, review and
      boundary; a `Leftover mode` coming back fails here.
  14. Plan inventory: the shipped scripts/plan_inventory.py, imported in-process and run end to
      end over invented fixtures, produces counts that agree with a tally this file computes
      itself, unit lines whose page references match the fixture's own sheet-to-page map, a
      window 1 selection matching an independent tally of the vocabulary sheet types plus the
      include and minus the exclude with a window-1.json matching it key for key, a window 2 that
      is an exact partition of the inventory minus both of window 1's lists, in the pinned sheet
      type order and with the balanced split of a pass over twelve units, both shipped sheet type
      constants pinned here and neither naming a type the recognizer does not produce, one
      window 3 review per package over two packages fixtures in package order with two packages
      on one trade both planning and planned one after the other, every window 3 unit id a legal
      verify_unit subject prefix stem with none a prefix of another, and a one-line refusal naming
      what is wrong for each of eleven broken invocations, two grid rows folding to one unit key
      and a window 1 file naming a key as both selected and excluded among them. The shipped script is compiled from source here rather than
      imported through the loader, so a script edited twice inside one second to the same byte
      length can never be checked as its earlier bytecode.
  15. No shipped skill or agent file names `fork` as a subagent type, in either the
      `subagent_type:` dispatch-line shape or a `tools: Agent(fork)` frontmatter declaration.
  16. Every shipped skill or agent file that names `ask_question` or tells the agent to raise a
      Question carries the fixed phrase "Question text is plain estimator words", either stating
      the rule in full or pointing at it (docs/plugin-text-style.md §1, `learn-project`'s
      judgment-entry table).

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

# The agent definitions the plugin ships under agents/. All three are dispatched
# by the scope run: the lead starts one runner per pass, and that runner starts
# one reader per sheet in windows 1 and 2, or one reviewer per package in
# window 3.
EXPECTED_AGENTS = {
    "scope-reader",
    "scope-reviewer",
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


def _build_banned_patterns() -> list[tuple[str, re.Pattern, bool]]:
    """Return (label, pattern, code_exempt) triples. code_exempt marks the two
    patterns (em dash, middle dot) that are data, not prose, inside fenced
    code blocks and inline code spans — docs/plugin-text-style.md §4. Every
    other pattern (confidentiality, ticket IDs, vault filenames, MOSOT) stays
    whole-file, code included, and must never be marked code_exempt."""
    patterns: list[tuple[str, re.Pattern, bool]] = [
        (f"client name '{n}'", re.compile(re.escape(n), re.IGNORECASE), False)
        for n in BANNED_CLIENT_NAMES
    ]
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


def _scan_file_for_banned(path: Path) -> list[str]:
    hits: list[str] = []
    try:
        text = path.read_text(encoding="utf-8")
    except Exception as e:
        return [f"{path}: read error: {e}"]

    lines = text.splitlines()
    fence_mask = _fenced_code_line_mask(lines)
    patterns = _build_banned_patterns()

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


def _collect_scope_files(plugin_path: Path, marketplace_root: Path) -> list[Path]:
    """
    Shared file-scope collection for every text-content check (banned
    strings, retired vocabulary, bold/Title-Case): every shipped-skill .md,
    every agents/ .md, every scripts/ .py, README.md and the manifest JSON
    files. Every one of them is the plugin's own prose, in its own voice, and
    every one takes the same scan. There is no lenient population: a file the
    plugin ships is a file the plugin is answerable for.
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

    return full_scope_files


def check_banned_strings(plugin_path: Path, marketplace_root: Path) -> Result:
    name = "banned-strings"

    full_scope_files = _collect_scope_files(plugin_path, marketplace_root)

    hits: list[str] = []
    for f in full_scope_files:
        hits.extend(_scan_file_for_banned(f))

    detail = f"{len(full_scope_files)} files under the banned-set scan"
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
#     shipped skills, agent definitions, shipped scripts, README, manifests).
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
    ("'trade-packages' (a retired directory name)", re.compile(r"\btrade-packages\b", re.IGNORECASE), False),
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
    full_scope_files = _collect_scope_files(plugin_path, marketplace_root)

    hits: list[str] = []
    for f in full_scope_files:
        hits.extend(_scan_file_for_retired_whole_file(f))
        hits.extend(_scan_file_for_retired_scoped(f))

    detail = f"{len(full_scope_files)} files scanned for retired vocabulary"
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
    full_scope_files = _collect_scope_files(plugin_path, marketplace_root)

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
    full_scope_files = _collect_scope_files(plugin_path, marketplace_root)

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
    "anomaly", "unread", "kinds", "deviation", "overlap", "grain", "door", "packet",
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
# The runner supervises one pass, one review, or one window boundary,
# and nothing larger. Its `##` headings are what say so, so pinning the set in both directions is
# the cheap mechanical way to catch the shape being partly undone: a `## Round mode` or a
# `## Leftover mode` coming back, or `## Pass mode` renamed away, fails the release.

EXPECTED_RUNNER_MODE_HEADINGS = {
    "What your dispatch gives you",
    "Pass mode",
    "The ledger lines",
    "Boundary mode",
    "Review mode",
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
# Check: the plan inventory script
# --------------------------------------------------------------------------- #
#
# The scope run's lead no longer holds a sheet row: a fetch agent puts the grid on disk and the
# shipped plan script turns it into counts and then into each window's read plan. The script is the
# only thing standing between a grid file and a plan, so this runs it end to end over invented
# fixtures and asserts its numbers against a tally this check computes itself.
#
# The extraction below is written independently of the script's own, so the two agreeing is
# evidence rather than a tautology. Window 2 is checked hardest that way: it has to be an exact
# partition of the inventory minus the window 1 file the script itself wrote, in the discipline and
# sheet type order this check recomputes off the fixture grid, split at twelve.
#
# The join this check exists for: the plan writes a window 3 unit id, a reviewer records its rows
# under `scopeItem:<unit id>-<seq>`, and the runner verifies that review by prefix. The three would
# otherwise meet for the first time mid-run, so every id the script writes is asserted here to be a
# legal subject prefix stem and never a prefix of another one.
#
# Honest bound, stated in the detail line: the fixtures are invented and small, so this proves the
# script's arithmetic, its ordering and its refusals, and nothing about how a real record read
# arrives.

PLAN_INVENTORY_SCRIPT = ("scripts", "plan_inventory.py")

_PLAN_PASS_RE = re.compile(r"^### (\S+?)\.\s")
_PLAN_UNIT_RE = re.compile(r"^(\d+)\. (\S+), page (\d+): (.*)$")
_PLAN_REVIEW_RE = re.compile(r"^(\d+)\. (rev-\S+): (.*)$")
_PLAN_FIELD_RE = re.compile(r"^([a-z][a-z ]*): (.*)$")
_LEFT_OUT_HEADING = "## Deliberately left out"

# The recognizer's deterministic sheet types: SHEET_TYPES in the api's sheet-type-classifier.ts,
# less `other`, which that classifier never returns (an unplaceable sheet types null instead).
# Copied here by hand because the api is a different repo; a constant naming anything else would
# select nothing on a real set instead of failing here.
RECOGNIZER_SHEET_TYPES = {
    "schedule", "plan", "overall-plan", "enlarged-plan", "section", "elevation",
    "detail", "RCP", "schematic", "legend", "notes", "cover-index",
}

# The two names the plan script declares for its own placement of a row the recognizer did not
# type. They are the script's own vocabulary rather than a claim about what the recognizer returns,
# so the assertion below allows them beside the recognizer's list rather than against it.
_PLACEMENT_SHEET_TYPES = {"other", "untyped"}

# The script's two sheet type constants, pinned here so a change to either fails the release. The
# window 1 four are a set. The window 2 ten are an order, and that order decides which sheet gets
# to create a row and which gets to update it, so it is pinned in full and in sequence.
_VOCABULARY_SHEET_TYPES = ["schedule", "legend", "notes", "cover-index"]
_WINDOW_2_SHEET_TYPE_ORDER = [
    "section", "detail", "elevation", "RCP", "enlarged-plan",
    "plan", "overall-plan", "schematic", "other", "untyped",
]

# A window 3 unit id becomes a `verify_unit` subject prefix with `scopeItem:` in front and `-`
# behind, so it may carry nothing a subject cannot.
_UNIT_ID_RE = re.compile(r"^rev-[0-9A-Za-z]+-[0-9]+$")
_SUBJECT_PREFIX_RE = re.compile(r"^scopeItem:[0-9A-Za-z._-]+-$")


def _load_script_module(script_path: Path, module_name: str):
    """
    Import a shipped script in-process, so the check runs no subprocess and no model. The source is
    compiled here rather than imported through the loader: a .pyc records the source mtime in whole
    seconds, so a script edited twice inside one second to the same byte length loads the earlier
    bytecode, and the harness would report on a version of the script that is no longer on disk.
    """
    # Dropping the scripts directory's own modules first means every load reads what is on disk now,
    # rather than a copy an earlier load in this process cached.
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


def _fold_code(code: str) -> str:
    """The catalog fold, written here rather than imported, so the two agreeing is evidence."""
    return "".join(code.split()).lower()


def _plan_passes(read_plan: str) -> list[dict]:
    """
    The read plan's passes, read straight off the file: the pass id, the `key: value` lines of its
    block, its sheet unit lines as (sheet number, page), and its review unit lines as (unit id,
    name). Stops at the left-out section, whose entries share the sheet unit line's shape.
    """
    passes: list[dict] = []
    for line in read_plan.splitlines():
        if line.strip() == _LEFT_OUT_HEADING:
            break
        heading = _PLAN_PASS_RE.match(line)
        if heading:
            passes.append({"id": heading.group(1), "fields": {}, "units": [], "reviews": []})
            continue
        if not passes:
            continue
        unit = _PLAN_UNIT_RE.match(line)
        if unit:
            passes[-1]["units"].append((unit.group(2), int(unit.group(3))))
            continue
        review = _PLAN_REVIEW_RE.match(line)
        if review:
            passes[-1]["reviews"].append((review.group(2), review.group(3)))
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


def check_plan_inventory(plugin_path: Path, marketplace_root: Path) -> Result:
    name = "plan-inventory"
    script = plugin_path.joinpath(*PLAN_INVENTORY_SCRIPT)
    if not script.is_file():
        return Result(name, False, detail=f"plan script not found at {script}")

    fixtures = marketplace_root / "harness" / "fixtures"
    grid_fixture = fixtures / "set-grid-fixture.json"
    if not grid_fixture.is_file():
        return Result(name, False, detail=f"fixture not found at {grid_fixture}")

    try:
        module = _load_script_module(script, "plan_inventory")
    except Exception as e:
        return Result(name, False, detail=f"cannot import {script.name}: {e}")

    # The independent tally, computed here off the fixtures and never off the script's output.
    try:
        fixture_rows = json.loads(grid_fixture.read_text(encoding="utf-8"))["sheets"]
    except Exception as e:
        return Result(name, False, detail=f"fixture: {e}")

    expected_rows = len(fixture_rows)
    expected_by_discipline: dict[str, int] = {}
    expected_cross: dict[str, dict[str, int]] = {}
    page_of: dict[str, int] = {}
    key_of: dict[str, str] = {}
    for row in fixture_rows:
        discipline = row.get("discipline") or "(none)"
        sheet_type = row.get("sheetType") or "(untyped)"
        expected_by_discipline[discipline] = expected_by_discipline.get(discipline, 0) + 1
        expected_cross.setdefault(discipline, {})
        expected_cross[discipline][sheet_type] = expected_cross[discipline].get(sheet_type, 0) + 1
        page_of[row["sheetNumber"]] = row["pageInPdf"]
        key_of[row["sheetNumber"]] = (
            f"{row['sheetNumber']}@{row.get('fileId') or ''}#{row['pageInPdf']}"
        )

    out_dir = Path(__file__).parent / ".test-results" / "plan-inventory"
    errors: list[str] = []

    # ------------------------------------------------------------------ #
    # The two shipped sheet type constants
    # ------------------------------------------------------------------ #
    #
    # The one assertion the retired trade sheet map check carried that still has a subject: no
    # shipped constant may name a sheet type the recognizer does not produce, or the window it
    # drives would select nothing on a real set instead of failing here.
    shipped_types = list(getattr(module, "VOCABULARY_SHEET_TYPES", ())) + list(
        getattr(module, "WINDOW_2_SHEET_TYPE_ORDER", ())
    )
    if list(getattr(module, "VOCABULARY_SHEET_TYPES", ())) != _VOCABULARY_SHEET_TYPES:
        errors.append(
            f"the script's window 1 sheet types are "
            f"{list(getattr(module, 'VOCABULARY_SHEET_TYPES', ()))}, pinned here as "
            f"{_VOCABULARY_SHEET_TYPES}"
        )
    if list(getattr(module, "WINDOW_2_SHEET_TYPE_ORDER", ())) != _WINDOW_2_SHEET_TYPE_ORDER:
        errors.append(
            f"the script's window 2 reading order is "
            f"{list(getattr(module, 'WINDOW_2_SHEET_TYPE_ORDER', ()))}, pinned here as "
            f"{_WINDOW_2_SHEET_TYPE_ORDER}"
        )
    strangers = sorted(
        {t for t in shipped_types if t not in RECOGNIZER_SHEET_TYPES and t not in _PLACEMENT_SHEET_TYPES}
    )
    if strangers:
        errors.append(
            f"the script's sheet type constants name {strangers}, which is neither a type the "
            f"recognizer produces nor one of the script's own placement names"
        )
    if len(set(shipped_types)) != len(shipped_types):
        errors.append("a sheet type is named in both of the script's two type constants")

    # ------------------------------------------------------------------ #
    # inventory
    # ------------------------------------------------------------------ #
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
    # The unit key window 1 writes and window 2 subtracts is built here from the grid's own fields,
    # so a change to how the script spells one fails the window 2 partition below rather than
    # quietly agreeing with itself.
    if {r["unitKey"] for r in written.get("sheets", [])} != set(key_of.values()):
        errors.append("inventory.json's unit keys are not sheet number, file id and page")

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
    window_1_json = out_dir / "plan" / "window-1.json"

    # ------------------------------------------------------------------ #
    # Window 1: the vocabulary, plus one include and one exclude
    # ------------------------------------------------------------------ #
    include_pattern = "A-4.*"
    exclude_pattern = "S-1.01"
    w1_path = out_dir / "read-plan-w1.md"
    window_1_json.unlink(missing_ok=True)
    code, w1_bounds, err = _run_plan_script(
        module,
        ["plan", "--window", "1", "--inventory", inventory_json,
         "--include", f"{include_pattern}:the elevations carry the window and finish marks",
         "--exclude", f"{exclude_pattern}:structural notes carry no scope this run reads",
         "--out", str(w1_path)],
    )
    w1_passes: list[dict] = []
    expected_w1: set[str] = set()
    excluded: set[str] = set()
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

        # The file window 2 subtracts, and the reason it exists: window 2 provably reads what
        # window 1 left rather than recomputing window 1's own selection from its arguments.
        if str(window_1_json) not in w1_bounds:
            errors.append(f"the window 1 bounds line does not name the file it wrote: {w1_bounds!r}")
        try:
            window_1_file = json.loads(window_1_json.read_text(encoding="utf-8"))
        except Exception as e:
            errors.append(f"window-1.json: {e}")
            window_1_file = {"selected": [], "excluded": []}
        if window_1_file.get("window") != 1:
            errors.append("window-1.json does not say which window wrote it")
        if set(window_1_file.get("selected", [])) != {key_of[s] for s in expected_w1}:
            errors.append("window-1.json's selected keys are not the sheets window 1 planned")
        if set(window_1_file.get("excluded", [])) != {key_of[s] for s in excluded}:
            errors.append("window-1.json's excluded keys are not the sheets the pattern left out")

    # ------------------------------------------------------------------ #
    # Window 2: every remaining sheet, once, in the fixed sheet type order
    # ------------------------------------------------------------------ #
    #
    # The expectation is built here from the grid and from window 1's own file: the inventory minus
    # both of window 1's lists, grouped by discipline in inventory order, sorted inside a discipline
    # by the pinned type order with inventory order kept inside a type, split at twelve. An excluded
    # sheet stays out: the lead left it out with a reason, and reading it here would overrule that.
    w2_path = out_dir / "read-plan-w2.md"
    code, w2_bounds, err = _run_plan_script(
        module,
        ["plan", "--window", "2", "--inventory", inventory_json,
         "--window-1", str(window_1_json), "--out", str(w2_path)],
    )
    w2_passes: list[dict] = []
    expected_w2_order: list[tuple[str, list[str]]] = []
    w2_split = 0
    if code != 0:
        errors.append(f"window 2 refused the fixtures: {err}")
    else:
        left = [
            r for r in fixture_rows
            if r["sheetNumber"] not in expected_w1 and r["sheetNumber"] not in excluded
        ]
        rank = {t: i for i, t in enumerate(_WINDOW_2_SHEET_TYPE_ORDER)}
        groups: dict[str, list[dict]] = {}
        group_order: list[str] = []
        for row in left:
            discipline = row.get("discipline") or "(none)"
            if discipline not in groups:
                groups[discipline] = []
                group_order.append(discipline)
            groups[discipline].append(row)
        for discipline in group_order:
            ordered = sorted(
                groups[discipline],
                key=lambda r: rank.get(r.get("sheetType") or "untyped", len(rank)),
            )
            stem = ("NONE" if discipline == "(none)" else discipline) + "2"
            expected_w2_order.append((stem, [r["sheetNumber"] for r in ordered]))

        by_type: dict[str, int] = {}
        for row in left:
            by_type[row.get("sheetType") or "untyped"] = (
                by_type.get(row.get("sheetType") or "untyped", 0) + 1
            )
        for fragment in (
            f"sheets {len(left)}",
            f"disciplines {len(group_order)}",
            f"every sheet once (units {len(left)} equals distinct sheets {len(left)})",
            f"sheets window 1 selected {len(expected_w1)}",
            f"sheets window 1 left out {len(excluded)}",
            f"sheets in the inventory {expected_rows}",
            f"sheets typed other or untyped "
            f"{by_type.get('other', 0) + by_type.get('untyped', 0)}",
        ):
            if fragment not in w2_bounds:
                errors.append(f"the window 2 bounds line does not name `{fragment}`: {w2_bounds!r}")
        for sheet_type, count in by_type.items():
            if f"{sheet_type} {count}" not in w2_bounds:
                errors.append(
                    f"the window 2 bounds line does not count `{sheet_type} {count}`: {w2_bounds!r}"
                )
        # Window 1 said how many sheets it does not read, and window 2 has to be exactly those.
        if f"unassigned {len(left)}" not in w1_bounds:
            errors.append(
                f"window 1's unassigned count is not window 2's sheet count ({len(left)}): "
                f"{w1_bounds!r}"
            )

        w2_passes = _plan_passes(w2_path.read_text(encoding="utf-8"))
        planned: list[tuple[str, list[str]]] = []
        for plan_pass in w2_passes:
            stem = plan_pass["id"]
            if len(stem) > 1 and stem[-1] in string.ascii_lowercase:
                stem = stem[:-1]
            if not planned or planned[-1][0] != stem:
                planned.append((stem, []))
            planned[-1][1].extend(sheet for sheet, _page in plan_pass["units"])
        if planned != expected_w2_order:
            errors.append(
                f"window 2 is not the inventory minus window 1, by discipline and in the sheet "
                f"type order: planned {planned}, expected {expected_w2_order}"
            )
        reads = [sheet for _stem, sheets in planned for sheet in sheets]
        if len(reads) != len(set(reads)):
            errors.append("a sheet appears in more than one window 2 unit line")
        for plan_pass in w2_passes:
            if plan_pass["fields"].get("reads for") != "the sheet":
                errors.append(f"window 2 pass {plan_pass['id']} does not read for the sheet")
        # The fixture has to be able to fail these two, or neither says anything.
        reordered = any(
            sheets != [r["sheetNumber"] for r in fixture_rows if r["sheetNumber"] in set(sheets)]
            for _stem, sheets in expected_w2_order
        )
        if not reordered:
            errors.append("the window 2 fixture proves nothing about the sheet type order")
        w2_split = _check_split_arithmetic(w2_passes, 12, errors, "window 2")
        if w2_split == 0:
            errors.append("the window 2 fixture proves nothing about the twelve-unit split")

    # ------------------------------------------------------------------ #
    # Window 3: one review per package
    # ------------------------------------------------------------------ #
    def window_3_over(label: str, packages_path: Path, out_name: str) -> tuple[list[dict], str]:
        """Run window 3 over one packages fixture and assert everything the plan file says."""
        path = out_dir / out_name
        run_code, run_bounds, run_err = _run_plan_script(
            module,
            ["plan", "--window", "3", "--packages", str(packages_path), "--out", str(path)],
        )
        if run_code != 0:
            errors.append(f"window 3 refused {label}: {run_err}")
            return [], ""
        rows = json.loads(packages_path.read_text(encoding="utf-8"))["packages"]

        ordinals: dict[str, int] = {}
        expected: list[dict] = []
        for row in rows:
            code_text = row["tradeCode"].strip()
            key = _fold_code(code_text)
            ordinals[key] = ordinals.get(key, 0) + 1
            expected.append(
                {
                    "id": f"rev-{''.join(code_text.split())}-{ordinals[key]}",
                    "key": key,
                    "code": code_text,
                    "name": row.get("name") or code_text,
                    "package": row.get("id") or "(no id)",
                    "codes": ", ".join(row.get("codes") or []) or "none",
                }
            )
        per_trade = {key: count for key, count in ordinals.items()}
        shared = [r for r in expected if per_trade[r["key"]] > 1]

        passes = _plan_passes(path.read_text(encoding="utf-8"))
        if len(passes) != len(rows):
            errors.append(f"{label}: window 3 planned {len(passes)} passes over {len(rows)} packages")
        if any(len(p["reviews"]) != 1 or p["units"] for p in passes):
            errors.append(f"{label}: a window 3 pass does not carry exactly one review and no sheet")
        by_id = {r["id"]: r for r in expected}
        planned_ids = [p["reviews"][0][0] for p in passes if p["reviews"]]
        if sorted(planned_ids) != sorted(by_id):
            errors.append(
                f"{label}: window 3 planned unit ids {sorted(planned_ids)}, expected {sorted(by_id)}"
            )
        for plan_pass in passes:
            if not plan_pass["reviews"]:
                continue
            unit_id, unit_name = plan_pass["reviews"][0]
            want = by_id.get(unit_id)
            if want is None:
                continue
            if plan_pass["id"] != unit_id:
                errors.append(f"{label}: pass {plan_pass['id']} carries the unit id {unit_id}")
            for field, value in (
                ("reads for", want["code"]),
                ("package", want["package"]),
                ("codes", want["codes"]),
            ):
                if plan_pass["fields"].get(field) != value:
                    errors.append(
                        f"{label}: review {unit_id} carries `{field}: "
                        f"{plan_pass['fields'].get(field)}`, expected {value!r}"
                    )
            if unit_name != want["name"]:
                errors.append(f"{label}: review {unit_id} is named {unit_name!r}, expected {want['name']!r}")

        for fragment in (
            f"packages {len(rows)}",
            f"reviews {len(expected)}",
            f"trades {len(per_trade)}",
            f"packages sharing a trade: {len(shared)}",
        ):
            if fragment not in run_bounds:
                errors.append(f"{label}: the bounds line does not name `{fragment}`: {run_bounds!r}")
        # The fixtures name few enough that the script's five-name cap cannot bite.
        for review in shared:
            if review["code"] not in run_bounds:
                errors.append(
                    f"{label}: the bounds line does not name {review['code']} as sharing a trade"
                )

        # Two packages on one trade run one after the other, so the runner's overlap scan sees them.
        positions: dict[str, list[int]] = {}
        for index, unit_id in enumerate(planned_ids):
            positions.setdefault(by_id[unit_id]["key"] if unit_id in by_id else unit_id, []).append(index)
        for key, at in positions.items():
            if at != list(range(at[0], at[0] + len(at))):
                errors.append(f"{label}: the packages on trade {key} are not planned one after the other")

        # Reviews run in package order, grouped by folded trade code in first-seen order. That is
        # the whole of the ordering rule, so it is computed here off the fixture rather than read
        # back off the plan the script wrote.
        first_seen: list[str] = []
        for review in expected:
            if review["key"] not in first_seen:
                first_seen.append(review["key"])
        expected_order = [r["id"] for key in first_seen for r in expected if r["key"] == key]
        if planned_ids != expected_order:
            errors.append(
                f"{label}: window 3 planned {planned_ids}, expected package order grouped by "
                f"trade: {expected_order}"
            )
        return passes, run_bounds

    ordinary_packages = fixtures / "packages-fixture.json"
    shared_packages = fixtures / "packages-fixture-duplicate-trade.json"
    w3_passes, w3_bounds = window_3_over("window 3", ordinary_packages, "read-plan-w3.md")
    shared_passes, shared_bounds = window_3_over(
        "window 3 over two packages on one trade", shared_packages, "read-plan-w3-shared.md"
    )

    # The fixtures have to reach the cases they exist for, or the assertions above say nothing.
    if w3_passes and "packages sharing a trade: 0" not in w3_bounds:
        errors.append(
            "the ordinary window 3 fixture puts two packages on one trade, so it no longer "
            "proves the plain one-package-per-trade case"
        )
    if shared_bounds and "packages sharing a trade: 2" not in shared_bounds:
        errors.append(
            f"the shared-trade fixture does not put two packages on one trade: {shared_bounds!r}"
        )

    # ------------------------------------------------------------------ #
    # The join: a unit id is a verify_unit subject prefix stem
    # ------------------------------------------------------------------ #
    #
    # The plan writes the id and the reviewer records `scopeItem:<unit id>-<seq>` under it, which the
    # runner then verifies with one `verify_unit(subjectPrefix: ...)` call. A prefix that is also the
    # prefix of another review's would count that review's rows as this one's.
    unit_ids = [p["reviews"][0][0] for p in shared_passes if p["reviews"]]
    prefixes = [f"scopeItem:{unit_id}-" for unit_id in unit_ids]
    for unit_id, prefix in zip(unit_ids, prefixes):
        if not _UNIT_ID_RE.match(unit_id):
            errors.append(f"the unit id {unit_id!r} is not `rev-<packed catalog code>-<ordinal>`")
        if not _SUBJECT_PREFIX_RE.match(prefix):
            errors.append(f"the subject prefix {prefix!r} is not a legal verify_unit prefix stem")
    for one in prefixes:
        for other in prefixes:
            if one is not other and other.startswith(one):
                errors.append(f"the subject prefix {one!r} is a prefix of {other!r}")
    if len(set(unit_ids)) != len(unit_ids):
        errors.append("two window 3 reviews carry one unit id")
    if not any(unit_id.endswith("-2") for unit_id in unit_ids):
        errors.append("the join test never sees a second review on one trade, which is the case it exists for")

    # ------------------------------------------------------------------ #
    # Every sheet unit line's page reference, checked against the fixture grid
    # ------------------------------------------------------------------ #
    sheet_units = [unit for p in w1_passes + w2_passes for unit in p["units"]]
    misplaced = [
        f"{sheet} on page {page} where the grid says {page_of.get(sheet)}"
        for sheet, page in sheet_units
        if page_of.get(sheet) != page
    ]
    if misplaced:
        errors.append("unit lines cite a page the grid does not: " + "; ".join(misplaced[:5]))

    # ------------------------------------------------------------------ #
    # Refusals, each exiting 1 with one line on stderr
    # ------------------------------------------------------------------ #
    broken = out_dir / "broken"
    broken.mkdir(parents=True, exist_ok=True)
    (broken / "window-1-stranger.json").write_text(
        json.dumps({"window": 1, "selected": ["Z-9.99@file-0001#99"], "excluded": []}) + "\n",
        encoding="utf-8",
    )
    # A key in both lists still leaves window 2 a correct partition, so nothing downstream would
    # catch it; what it corrupts is the count the bounds line says out loud.
    a_real_key = sorted(key_of.values())[0]
    (broken / "window-1-both-lists.json").write_text(
        json.dumps({"window": 1, "selected": [a_real_key], "excluded": [a_real_key]}) + "\n",
        encoding="utf-8",
    )
    # Two grid rows folding to one unit key. The delimiters are `@` and `#`, so a sheet number
    # carrying an `@` and an empty file id reach the same string as the reverse. Window 2 would drop
    # both rows, and its partition check could not see it, because neither reaches the remainder for
    # the count to disagree on.
    (broken / "colliding-grid.json").write_text(
        json.dumps(
            {
                "count": 2,
                "offset": 0,
                "sheets": [
                    {"discipline": "A", "sheetNumber": "A@1", "sheetType": "plan",
                     "pageTitle": "One of the two", "fileId": "", "pageInPdf": 2},
                    {"discipline": "A", "sheetNumber": "A", "sheetType": "plan",
                     "pageTitle": "The other", "fileId": "1@", "pageInPdf": 2},
                ],
            }
        )
        + "\n",
        encoding="utf-8",
    )

    refused = str(out_dir / "refused.md")
    packages = str(ordinary_packages)
    refusals: list[tuple[str, list[str], str]] = [
        (
            "a package row with no tradeCode",
            ["plan", "--window", "3", "--packages", str(fixtures / "packages-fixture-no-trade-code.json"),
             "--out", refused],
            "tradeCode",
        ),
        (
            "window 2 with no --window-1",
            ["plan", "--window", "2", "--inventory", inventory_json, "--out", refused],
            "--window-1",
        ),
        (
            "window 2 given --packages",
            ["plan", "--window", "2", "--inventory", inventory_json, "--window-1", str(window_1_json),
             "--packages", packages, "--out", refused],
            "--packages",
        ),
        (
            "window 3 given --inventory",
            ["plan", "--window", "3", "--inventory", inventory_json, "--packages", packages,
             "--out", refused],
            "--inventory",
        ),
        (
            "window 1 given --kinds",
            ["plan", "--window", "1", "--inventory", inventory_json,
             "--kinds", inventory_json, "--out", refused],
            "--kinds",
        ),
        (
            "window 1 given --index",
            ["plan", "--window", "1", "--inventory", inventory_json,
             "--index", str(out_dir), "--out", refused],
            "--index",
        ),
        (
            "a window 1 file naming a unit key the inventory does not hold",
            ["plan", "--window", "2", "--inventory", inventory_json,
             "--window-1", str(broken / "window-1-stranger.json"), "--out", refused],
            "does not hold",
        ),
        (
            "an include pattern matching no sheet",
            ["plan", "--window", "1", "--inventory", inventory_json,
             "--include", "Z-9.*:a family that is not in this set", "--out", refused],
            "Z-9.*",
        ),
        (
            "an include with no colon",
            ["plan", "--window", "1", "--inventory", inventory_json, "--include", "A-4.01",
             "--out", refused],
            "reason",
        ),
        (
            "a window 1 file naming a key as both selected and excluded",
            ["plan", "--window", "2", "--inventory", inventory_json,
             "--window-1", str(broken / "window-1-both-lists.json"), "--out", refused],
            "both selected and excluded",
        ),
        (
            "a grid whose rows fold to one unit key",
            ["inventory", "--grid", str(broken / "colliding-grid.json"), "--expect-count", "2",
             "--out-dir", str(out_dir / "colliding")],
            "colliding unit key",
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
        f"the inventory tallies and unit keys checked against an independent count, "
        f"{len(sheet_units)} sheet unit lines over two windows with every page checked against the "
        f"grid, window 1's selection and its bounds counts checked against an independent tally and "
        f"its window-1.json checked key for key, window 2 checked to be an exact partition of the "
        f"inventory minus both of window 1's lists in the pinned sheet type order with {w2_split} "
        f"pass split at the twelve-unit cap, both sheet type constants pinned here and neither "
        f"naming a type the recognizer does not produce, one review per package over two packages "
        f"fixtures, in package order, with two packages on "
        f"one trade both planning and planned one after the other, {len(unit_ids)} unit ids checked "
        f"to be legal verify_unit prefix stems with none a prefix of another, "
        f"{len(refusals)} broken invocations each refused in one line naming what is wrong"
    )
    # An honest bound, not a pass: the fixtures are invented and small. They carry the field names
    # the shipped verbs return, so a rename on the record's side would fail here, but nothing about
    # a real grid or a real packages read is proved by them.
    detail += "; bound: invented fixtures, not a real grid or a real packages read"
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
# (a forklift, a decision fork) are untouched: the pattern only matches "fork" sitting immediately
# after one of those two anchors.

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
        check_plan_inventory(plugin_path, marketplace_root),
        check_no_fork_subagent(plugin_path),
    ]
    all_passed = all(r.passed for r in results)
    return results, all_passed
