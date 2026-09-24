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
      verify_unit subject prefix stem with none a prefix of another, a first plan of windows 1 and
      2 numbering each pass's units from 1 and a replan keeping every unit id the run ledger and
      the previous plan file already handed out, numbering new sheets after the highest number the
      pass has ever carried and never handing a cut sheet's id out again, a window 2 slice planned
      with `--only` holding exactly the sheets its patterns name and deferring the rest, with its
      bounds line, its `plan/window-2.json` and its read plan's per-pattern and deferred sections
      each matching an independent tally, the slice lettered by the whole window so the full plan
      after it keeps its ids at the front of part a (three dispatched, then twelve) and reads its
      partition exactly as before once nothing is deferred, every pass block counting the units
      the ledger's `verified ... result ok` lines finished and marking exactly those lines (a
      `mismatch`, an id no plan carries and another window's line marking nothing), a planned and
      never dispatched id that changes pass renumbered in its new part with the old id retired, a
      second slice holding the first one's dispatched ids rather than retiring them, window-1.json
      carrying the patterns it was planned with, and a one-line refusal naming what is
      wrong for each of twenty-one broken invocations, two grid rows folding to one unit key, a
      window 1 file naming a key as both selected and excluded, the seven ways a kept unit id would
      be wrong, an `--only` on window 1, an `--only` matching no sheet window 2 reads, and a slice
      of thirteen dispatched in one discipline, which the full plan's first part of twelve cannot
      hold, among them. The shipped script is compiled from source here
      rather than imported through the loader, so a script edited twice inside one second to the
      same byte length can never be checked as its earlier bytecode.
  14b. Pass summary: the shipped scripts/pass_summary.py, imported in-process and run over two
      invented ledger fixtures, sums one pass's own dispatch and verified lines into the published
      summary shape, and every number, every note line and every label is compared against a tally
      this file computes itself off the same fixture text. The labels it prints are compared in
      order against the skill's own summary block, another pass's and another window's lines and
      the lead's own `pass:` line are shown to reach no total, and ten broken invocations each
      refuse in one line with nothing on stdout.
  15. No shipped skill or agent file names `fork` as a subagent type, in either the
      `subagent_type:` dispatch-line shape or a `tools: Agent(fork)` frontmatter declaration.
  16. Every shipped skill or agent file that names `ask_question` or tells the agent to raise a
      Question carries the fixed phrase "Question text is plain estimator words", either stating
      the rule in full or pointing at it (docs/plugin-text-style.md §1, `learn-project`'s
      judgment-entry table).
  17. Agent tool surface: no agents/*.md tools line takes the whole connector as a wildcard;
      every connector verb an agent's body names is on its tools line; every declared connector
      verb is one of the 112 the connector registers; and the prohibition-only exception table
      stays honest, each entry still named in that agent's text and still off its tools line.
  18. Agent model pinned: every agents/*.md frontmatter carries a non-empty `model`, so a
      dispatched agent does not run on whatever model the session happens to be on. Checks 17 and
      18 each run their own helper over the agent fixtures under harness/fixtures/, so the clean
      one is shown to pass and each broken one to refuse in one line naming what is wrong.

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
import shutil
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
    "drawing-upload",
    "learn-project",
    "prepare-invitations",
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
# A planned unit line leads with its own unit id (`A1-7.`) and the deliberately-left-out section
# leads with a plain ordinal, so the label is read as whatever non-space token sits before the dot.
_PLAN_UNIT_RE = re.compile(r"^(\S+)\. (\S+), page (\d+): (.*)$")
_PLAN_REVIEW_RE = re.compile(r"^(\d+)\. (rev-\S+): (.*)$")
_PLAN_FIELD_RE = re.compile(r"^([a-z][a-z ]*): (.*)$")
_LEFT_OUT_HEADING = "## Deliberately left out"
# A window 2 slice lists what each `--only` pattern read and counts what it deferred under this
# heading, after the left-out section, so no unit line in it is ever read as a planned unit.
_SLICE_HEADING = "## Read now, the rest deferred"

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


def _run_script_main(module, argv: list[str]) -> tuple[int, str, str]:
    """Call a shipped script's own main() and capture its exit code and both streams."""
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
    block, its sheet unit lines as (unit id, sheet number, page), and its review unit lines as
    (unit id, name). Stops at the left-out section, whose entries share the sheet unit line's shape
    and carry a plain ordinal where a planned unit carries its id.
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
            passes[-1]["units"].append((unit.group(1), unit.group(2), int(unit.group(3))))
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
    code, bounds, err = _run_script_main(
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

    off_code, _off_bounds, off_err = _run_script_main(
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
    # Both unit id tiers sit in the folder the plan is written into, so this run starts with
    # neither: the first plan of a window has no ledger and no previous plan file, and the two
    # bounds lines below are what prove the change is inert there.
    (out_dir / "ledger.md").unlink(missing_ok=True)
    code, w1_bounds, err = _run_script_main(
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
            f"ids kept 0 (ledger 0, plan file 0), ids new {len(expected_w1)}, ids retired 0",
        ):
            if fragment not in w1_bounds:
                errors.append(f"the window 1 bounds line does not name `{fragment}`: {w1_bounds!r}")
        w1_passes = _plan_passes(w1_path.read_text(encoding="utf-8"))
        w1_sheets = [sheet for p in w1_passes for _id, sheet, _page in p["units"]]
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
        # A resume runs this plan again exactly, so the patterns it was written with are on disk.
        if (window_1_file.get("include"), window_1_file.get("exclude")) != (
            [{"pattern": include_pattern, "reason": "the elevations carry the window and finish marks"}],
            [{"pattern": exclude_pattern, "reason": "structural notes carry no scope this run reads"}],
        ):
            errors.append(
                f"window-1.json's patterns are {window_1_file.get('include')} and "
                f"{window_1_file.get('exclude')}, not the include and exclude it was planned with"
            )

    # ------------------------------------------------------------------ #
    # Window 2: every remaining sheet, once, in the fixed sheet type order
    # ------------------------------------------------------------------ #
    #
    # The expectation is built here from the grid and from window 1's own file: the inventory minus
    # both of window 1's lists, grouped by discipline in inventory order, sorted inside a discipline
    # by the pinned type order with inventory order kept inside a type, split at twelve. An excluded
    # sheet stays out: the lead left it out with a reason, and reading it here would overrule that.
    w2_path = out_dir / "read-plan-w2.md"
    # Window 2 writes its own plan file too, and its ids are a tier the next run keeps, so the file
    # an earlier harness run left behind goes first, as window 1's does above.
    (out_dir / "plan" / "window-2.json").unlink(missing_ok=True)
    code, w2_bounds, err = _run_script_main(
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
            f"ids kept 0 (ledger 0, plan file 0), ids new {len(left)}, ids retired 0",
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
            planned[-1][1].extend(sheet for _id, sheet, _page in plan_pass["units"])
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
        run_code, run_bounds, run_err = _run_script_main(
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
    # Unit ids kept across a replan
    # ------------------------------------------------------------------ #
    #
    # A unit id is a live subject prefix on the project record: a reader records
    # `scopeItem:<unit id>-<seq>`, the runner verifies that prefix and the lead counts it. A replan
    # that renumbered would point an id already in use at another sheet's work, so the script reads
    # the run ledger's dispatch lines and its own previous plan file, keeps every id already handed
    # out, numbers what is new after the highest number its pass has ever carried, and hands no
    # number out twice. Everything below is computed here off the fixtures the check writes.
    # With no ledger and no previous plan file, a pass numbers its units from 1, so the id on each
    # line is exactly the ordinal the line used to carry. That is the guard that this is inert on a
    # first plan.
    for where, first_plan_passes in (
        ("window 1", w1_passes), ("window 2", w2_passes), ("window 3", w3_passes),
        ("window 3 over two packages on one trade", shared_passes),
    ):
        for plan_pass in first_plan_passes:
            if plan_pass["fields"].get("units verified") != "0":
                errors.append(
                    f"{where}: pass {plan_pass['id']} reads `units verified: "
                    f"{plan_pass['fields'].get('units verified')}` on a plan with no ledger"
                )
    for where, first_plan_passes in (("window 1", w1_passes), ("window 2", w2_passes)):
        for plan_pass in first_plan_passes:
            first_ids = [unit_id for unit_id, _sheet, _page in plan_pass["units"]]
            wanted_ids = [f"{plan_pass['id']}-{i}" for i in range(1, len(first_ids) + 1)]
            if first_ids != wanted_ids:
                errors.append(
                    f"{where}: pass {plan_pass['id']} carries unit ids {first_ids}, expected "
                    f"{wanted_ids} on a first plan"
                )

    replan_root = out_dir / "replan"
    shutil.rmtree(replan_root, ignore_errors=True)

    def replan_row(number: str, sheet_type: str, page: int) -> dict:
        return {
            "unitKey": f"{number}@file-0001#{page}",
            "discipline": "A",
            "sheetNumber": number,
            "pageTitle": f"{sheet_type} on {number}",
            "sheetType": sheet_type,
            "fileId": "file-0001",
            "pageInPdf": page,
        }

    def write_replan_inventory(folder: Path, inventory_rows: list[dict]) -> str:
        path = folder / "inventory.json"
        folder.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps({"sheets": inventory_rows}, indent=2) + "\n", encoding="utf-8")
        return str(path)

    def write_ledger(folder: Path, ledger_lines: list[str]) -> None:
        folder.mkdir(parents=True, exist_ok=True)
        (folder / "ledger.md").write_text("\n".join(ledger_lines) + "\n", encoding="utf-8")

    def run_replan(folder: Path, window: int, inventory_path: str, extra: list[str]):
        """One plan run in its own folder, so the ledger and the plan file it reads are its own."""
        out = folder / "read-plan.md"
        run_code, run_bounds, run_err = _run_script_main(
            module,
            ["plan", "--window", str(window), "--inventory", inventory_path, *extra,
             "--out", str(out)],
        )
        if run_code != 0:
            return run_code, run_bounds, run_err, []
        return run_code, run_bounds, run_err, _plan_passes(out.read_text(encoding="utf-8"))

    def planned_ids(plan_passes: list[dict]) -> list[tuple[str, str]]:
        """(unit id, sheet number) in the order the file lists them."""
        return [(unit_id, sheet) for p in plan_passes for unit_id, sheet, _page in p["units"]]

    def expect_bounds(label: str, bounds: str, fragment: str) -> None:
        if fragment not in bounds:
            errors.append(f"{label}: the bounds line does not name `{fragment}`: {bounds!r}")

    # Eleven sheets window 1 selects on sheet type alone, and four window 2 reads after it, in an
    # inventory order that is not the window 2 reading order.
    vocabulary_rows = [
        replan_row(f"A-1.{index:02d}", "schedule" if index % 2 else "legend", index)
        for index in range(1, 12)
    ]
    other_rows = [
        replan_row("A-2.01", "plan", 12),
        replan_row("A-2.02", "section", 13),
        replan_row("A-2.03", "detail", 14),
        replan_row("A-2.04", "elevation", 15),
    ]

    # --- plan six, dispatch four, replan with five more ---------------- #
    grow = replan_root / "grow"
    grow_inventory = write_replan_inventory(grow, vocabulary_rows + other_rows)
    first_six = [f"A-1.{index:02d}" for index in range(1, 12, 2)]
    held_back = [f"A-1.{index:02d}" for index in range(2, 12, 2)]
    cut_to_six = [
        arg
        for sheet in held_back
        for arg in ("--exclude", f"{sheet}:the user cut this window to six sheets")
    ]
    code, bounds, err, six_passes = run_replan(grow, 1, grow_inventory, cut_to_six)
    if code != 0:
        errors.append(f"the replan fixture's first window 1 run refused: {err}")
    elif planned_ids(six_passes) != [(f"A1-{i}", sheet) for i, sheet in enumerate(first_six, 1)]:
        errors.append(f"the first plan of six did not number them 1 to 6: {planned_ids(six_passes)}")

    write_ledger(grow, [
        "phase: plan approved",
        "dispatch: window 1 pass A1 units 6",
        *[
            f"dispatch 1 A1 A1-{index} sheets {sheet} purpose a schedule this pass reads"
            for index, sheet in enumerate(first_six[:4], 1)
        ],
    ])

    code, grow_bounds, err, grown_passes = run_replan(grow, 1, grow_inventory, [])
    if code != 0:
        errors.append(f"the replan over eleven sheets refused: {err}")
    else:
        # Kept ids hold the front of the pass in the order they were read; new sheets follow, in
        # inventory order. That is not the inventory's own order, which is what proves the file is
        # ordered by id rather than by the grid.
        expected_grown = (
            [(f"A1-{i}", sheet) for i, sheet in enumerate(first_six, 1)]
            + [(f"A1-{i}", sheet) for i, sheet in enumerate(held_back, 7)]
        )
        if planned_ids(grown_passes) != expected_grown:
            errors.append(
                f"the replan did not keep the six ids and append the five new ones: "
                f"{planned_ids(grown_passes)}, expected {expected_grown}"
            )
        inventory_order = [row["sheetNumber"] for row in vocabulary_rows]
        if [sheet for _id, sheet in planned_ids(grown_passes)] == inventory_order:
            errors.append("the replan fixture proves nothing about ordering by id: it is inventory order")
        expect_bounds(
            "the replan over eleven sheets", grow_bounds,
            "ids kept 6 (ledger 4, plan file 2), ids new 5, ids retired 0",
        )
        totals = (grow / "read-plan.md").read_text(encoding="utf-8")
        if "unit ids kept 6, new 5, retired 0" not in totals:
            errors.append("the plan file's totals block does not carry the same id counts as its bounds line")

    # --- the round trip: an id the plan wrote, dispatched, and read back - #
    seventh_id, seventh_sheet = planned_ids(grown_passes)[6] if len(planned_ids(grown_passes)) > 6 else ("", "")
    write_ledger(grow, [
        "phase: plan approved",
        "dispatch: window 1 pass A1 units 6",
        *[
            f"dispatch 1 A1 A1-{index} sheets {sheet} purpose a schedule this pass reads"
            for index, sheet in enumerate(first_six[:4], 1)
        ],
        f"dispatch 1 A1 {seventh_id} sheets {seventh_sheet} purpose a schedule this pass reads",
    ])
    code, round_trip_bounds, err, round_trip_passes = run_replan(grow, 1, grow_inventory, [])
    if code != 0:
        errors.append(f"the round trip replan refused: {err}")
    else:
        if (seventh_id, seventh_sheet) not in planned_ids(round_trip_passes):
            errors.append(
                f"the plan wrote {seventh_id} on {seventh_sheet}, the ledger dispatched it, and the "
                f"replan did not put it back: {planned_ids(round_trip_passes)}"
            )
        expect_bounds("the round trip replan", round_trip_bounds,
                      "ids kept 11 (ledger 5, plan file 6), ids new 0, ids retired 0")
        # Every id the plan writes is a legal verify_unit prefix stem, and none is a prefix of
        # another, which is what keeps one unit's rows from counting as another's.
        replan_prefixes = [f"scopeItem:{unit_id}-" for unit_id, _sheet in planned_ids(round_trip_passes)]
        for prefix in replan_prefixes:
            if not _SUBJECT_PREFIX_RE.match(prefix):
                errors.append(f"the subject prefix {prefix!r} is not a legal verify_unit prefix stem")
        for one in replan_prefixes:
            for other in replan_prefixes:
                if one is not other and other.startswith(one):
                    errors.append(f"the subject prefix {one!r} is a prefix of {other!r}")

    # --- a removed sheet's id is not reused ---------------------------- #
    retired_sheet = first_six[2]
    code, retire_bounds, err, retire_passes = run_replan(
        grow, 1, grow_inventory,
        ["--exclude", f"{retired_sheet}:the user took this sheet out of the window",
         "--include", "A-2.01:the key plan carries the unit mix"],
    )
    if code != 0:
        errors.append(f"the replan that cuts a read sheet refused: {err}")
    else:
        carried = dict(planned_ids(retire_passes))
        if "A1-3" in carried:
            errors.append(f"the id of the sheet cut from the plan was handed out again, to {carried['A1-3']}")
        if carried.get("A1-12") != "A-2.01":
            errors.append(f"the new sheet did not take the next number after the highest: {carried}")
        expect_bounds("the replan that cuts a read sheet", retire_bounds,
                      "ids kept 10 (ledger 4, plan file 6), ids new 1, ids retired 1")

    # --- the ledger beats the plan file -------------------------------- #
    conflict = replan_root / "conflict"
    conflict_inventory = write_replan_inventory(conflict, vocabulary_rows)
    kept_two = ["A-1.01", "A-1.02"]
    cut_to_two = [
        arg
        for row in vocabulary_rows
        if row["sheetNumber"] not in kept_two
        for arg in ("--exclude", f"{row['sheetNumber']}:the user cut this window to two sheets")
    ]
    (conflict / "plan").mkdir(parents=True, exist_ok=True)
    (conflict / "plan" / "window-1.json").write_text(
        json.dumps(
            {
                "window": 1,
                "selected": [row["unitKey"] for row in vocabulary_rows if row["sheetNumber"] in kept_two],
                "excluded": [],
                "units": [{"id": "A1-9", "unitKey": vocabulary_rows[0]["unitKey"]}],
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    write_ledger(conflict, [f"dispatch 1 A1 A1-2 sheets {kept_two[0]} purpose a schedule this pass reads"])
    code, conflict_bounds, err, conflict_passes = run_replan(conflict, 1, conflict_inventory, cut_to_two)
    if code != 0:
        errors.append(f"the ledger-against-plan-file replan refused: {err}")
    else:
        carried = dict(planned_ids(conflict_passes))
        if carried.get("A1-2") != kept_two[0]:
            errors.append(f"the ledger did not win the disagreement with the plan file: {carried}")
        if carried.get("A1-10") != kept_two[1]:
            errors.append(f"the new sheet did not number after the highest either tier names: {carried}")
        expect_bounds("the ledger-against-plan-file replan", conflict_bounds,
                      "ids kept 1 (ledger 1, plan file 0), ids new 1, ids retired 1")

    # --- window 2 numbers its new units in the pinned type order ------- #
    w2_replan = replan_root / "window-2"
    w2_rows = vocabulary_rows + other_rows
    w2_inventory = write_replan_inventory(w2_replan, w2_rows)
    code, _bounds, err, _passes = run_replan(w2_replan, 1, w2_inventory, [])
    if code != 0:
        errors.append(f"the window 2 replan fixture's window 1 run refused: {err}")
    w2_window_1 = str(w2_replan / "plan" / "window-1.json")
    write_ledger(w2_replan, [
        "dispatch 2 A2 A2-1 sheets A-2.02 purpose the wall section",
        "dispatch 2 A2 A2-2 sheets A-2.03 purpose the head and sill details",
    ])
    grown_w2_rows = w2_rows + [replan_row("A-2.05", "section", 16), replan_row("A-2.06", "plan", 17)]
    w2_inventory = write_replan_inventory(w2_replan, grown_w2_rows)
    code, _bounds, err, _passes = run_replan(w2_replan, 1, w2_inventory, [])
    if code != 0:
        errors.append(f"the window 2 replan fixture's second window 1 run refused: {err}")
    code, w2_replan_bounds, err, w2_replan_passes = run_replan(
        w2_replan, 2, w2_inventory, ["--window-1", w2_window_1]
    )
    if code != 0:
        errors.append(f"the window 2 replan refused: {err}")
    else:
        rank = {t: i for i, t in enumerate(_WINDOW_2_SHEET_TYPE_ORDER)}
        still_new = [r for r in grown_w2_rows if r["sheetNumber"] not in ("A-2.02", "A-2.03")
                     and r["sheetType"] not in _VOCABULARY_SHEET_TYPES]
        still_new.sort(key=lambda r: rank[r["sheetType"]])
        expected_w2_replan = (
            [("A2-1", "A-2.02"), ("A2-2", "A-2.03")]
            + [(f"A2-{i}", r["sheetNumber"]) for i, r in enumerate(still_new, 3)]
        )
        if planned_ids(w2_replan_passes) != expected_w2_replan:
            errors.append(
                f"window 2 did not keep its dispatched ids and number the new sheets in the pinned "
                f"type order: {planned_ids(w2_replan_passes)}, expected {expected_w2_replan}"
            )
        expect_bounds("the window 2 replan", w2_replan_bounds,
                      "ids kept 2 (ledger 2, plan file 0), ids new 4, ids retired 0")

    # --- a window 2 slice, and the whole window after it --------------- #
    #
    # `--only` plans the sheets a user asked for first and defers the rest of window 2, and the next
    # plan run without it plans the rest. The slice's ids have to survive that run, so a discipline
    # the whole window splits is lettered in the slice too, and the slice's units then sort to the
    # front of that discipline's part a. Every expectation below is built here off the fixture rows.
    def slice_row(discipline: str, number: str, sheet_type: str, page: int) -> dict:
        return {
            "unitKey": f"{number}@file-0001#{page}",
            "discipline": discipline,
            "sheetNumber": number,
            "pageTitle": f"{sheet_type} on {number}",
            "sheetType": sheet_type,
            "fileId": "file-0001",
            "pageInPdf": page,
        }

    slice_rank = {t: i for i, t in enumerate(_WINDOW_2_SHEET_TYPE_ORDER)}

    def in_type_order(type_rows: list[dict]) -> list[dict]:
        return sorted(type_rows, key=lambda r: slice_rank.get(r["sheetType"], len(slice_rank)))

    # Twenty architectural sheets in three types, so the whole discipline splits into two parts of
    # ten and a slice of six fits the first; five structural, which never split; three mechanical,
    # which the slice defers whole.
    slice_types = ("plan", "section", "elevation")
    slice_a = [slice_row("A", f"A-3.{i:02d}", slice_types[i % 3], 19 + i) for i in range(1, 21)]
    slice_s = [slice_row("S", f"S-2.{i:02d}", "plan", 39 + i) for i in range(1, 6)]
    slice_m = [slice_row("M", f"M-2.{i:02d}", "schematic", 44 + i) for i in range(1, 4)]
    slice_dir = replan_root / "slice"
    slice_inventory = write_replan_inventory(slice_dir, vocabulary_rows + slice_a + slice_s + slice_m)
    slice_window_1 = ["--window-1", str(slice_dir / "plan" / "window-1.json")]
    code, _bounds, err, _passes = run_replan(slice_dir, 1, slice_inventory, [])
    if code != 0:
        errors.append(f"the slice fixture's window 1 run refused: {err}")

    first_reason = "the user asked for the first six plans first"
    second_reason = "the key plan the user asked for"
    sliced_a = [r for r in slice_a if fnmatch.fnmatchcase(r["sheetNumber"], "A-3.0[1-6]")]
    sliced_s = [r for r in slice_s if r["sheetNumber"] == "S-2.01"]
    sliced_keys = {r["unitKey"] for r in sliced_a + sliced_s}
    deferred_rows = [r for r in slice_a + slice_s + slice_m if r["unitKey"] not in sliced_keys]
    # A slice of six in a discipline of twenty is part a, a slice in a discipline that never splits
    # keeps its bare pass id, and the six are not in inventory order once the type order sorts them.
    expected_slice = (
        [(f"A2a-{i}", r["sheetNumber"]) for i, r in enumerate(in_type_order(sliced_a), 1)]
        + [(f"S2-{i}", r["sheetNumber"]) for i, r in enumerate(in_type_order(sliced_s), 1)]
    )
    if not len(sliced_a) <= 12 < len(slice_a) or len(slice_s) > 12:
        errors.append("the slice fixture proves nothing about lettering a slice by the whole window")
    if [r["sheetNumber"] for r in in_type_order(sliced_a)] == [r["sheetNumber"] for r in sliced_a]:
        errors.append("the slice fixture proves nothing about the type order inside a slice")

    code, slice_bounds, err, slice_passes = run_replan(
        slice_dir, 2, slice_inventory,
        slice_window_1 + ["--only", f"A-3.0[1-6]:{first_reason}", "--only", f"S-2.01:{second_reason}"],
    )
    if code != 0:
        errors.append(f"the window 2 slice refused: {err}")
    else:
        if planned_ids(slice_passes) != expected_slice:
            errors.append(
                f"the window 2 slice planned {planned_ids(slice_passes)}, expected {expected_slice}"
            )
        remaining_count = len(sliced_keys) + len(deferred_rows)
        for fragment in (
            f"window 2, sheets {len(sliced_keys)}, passes 2, disciplines 2",
            f"every sheet once (units {len(sliced_keys)} plus deferred {len(deferred_rows)} equals "
            f"distinct sheets {remaining_count})",
            f"sheets deferred {len(deferred_rows)} by --only",
            f"ids kept 0 (ledger 0, plan file 0), ids new {len(sliced_keys)}, ids retired 0",
        ):
            expect_bounds("the window 2 slice", slice_bounds, fragment)

        slice_file_path = slice_dir / "plan" / "window-2.json"
        if str(slice_file_path) not in slice_bounds:
            errors.append(f"the window 2 slice bounds line does not name the file it wrote: {slice_bounds!r}")
        try:
            slice_file = json.loads(slice_file_path.read_text(encoding="utf-8"))
        except Exception as e:
            errors.append(f"the slice's window-2.json: {e}")
            slice_file = {}
        sheet_of = {r["unitKey"]: r["sheetNumber"] for r in slice_a + slice_s + slice_m}
        if set(slice_file) != {"window", "units", "only", "deferredKeys", "deferredCount"}:
            errors.append(f"the slice's window-2.json carries the keys {sorted(slice_file)}")
        if slice_file.get("window") != 2:
            errors.append("the slice's window-2.json does not say which window wrote it")
        written_units = [
            (u.get("id"), sheet_of.get(u.get("unitKey"))) for u in slice_file.get("units", [])
        ]
        if written_units != expected_slice:
            errors.append(f"the slice's window-2.json binds {written_units}, expected {expected_slice}")
        expected_only = [
            {"pattern": "A-3.0[1-6]", "reason": first_reason, "sheets": [r["unitKey"] for r in sliced_a]},
            {"pattern": "S-2.01", "reason": second_reason, "sheets": [r["unitKey"] for r in sliced_s]},
        ]
        if slice_file.get("only") != expected_only:
            errors.append(f"the slice's window-2.json `only` is {slice_file.get('only')}, expected {expected_only}")
        if slice_file.get("deferredKeys") != [r["unitKey"] for r in deferred_rows]:
            errors.append("the slice's window-2.json `deferredKeys` are not the deferred sheets in inventory order")
        if slice_file.get("deferredCount") != len(deferred_rows):
            errors.append(
                f"the slice's window-2.json `deferredCount` is {slice_file.get('deferredCount')}, "
                f"expected {len(deferred_rows)}"
            )

        # The read plan: one block per pattern listing what it selected, with a plain ordinal on each
        # line as a left-out block carries, and one deferred block that counts by discipline rather
        # than listing the rest of the window.
        slice_text = (slice_dir / "read-plan.md").read_text(encoding="utf-8")
        blocks: dict[str, list[str]] = {}
        inside, current = False, None
        for line in slice_text.splitlines():
            if line.startswith("## "):
                inside, current = line.strip() == _SLICE_HEADING, None
            elif inside and line.startswith("### "):
                current = line[4:].strip()
                blocks[current] = []
            elif inside and current is not None and line.strip():
                blocks[current].append(line.strip())

        def listed(block_rows: list[dict]) -> list[str]:
            return [
                f"{i}. {r['sheetNumber']}, page {r['pageInPdf']}: {r['pageTitle']}"
                for i, r in enumerate(block_rows, 1)
            ]

        deferred_table: list[str] = []
        for discipline in ("A", "S", "M"):
            count = sum(1 for r in deferred_rows if r["discipline"] == discipline)
            if count:
                deferred_table.append(f"{discipline} | {count}")
        expected_blocks = {
            "Only: A-3.0[1-6]": [f"reason: {first_reason}", f"sheets: {len(sliced_a)}", *listed(sliced_a)],
            "Only: S-2.01": [f"reason: {second_reason}", f"sheets: {len(sliced_s)}", *listed(sliced_s)],
            "Deferred": [
                f"reason: {first_reason}", f"reason: {second_reason}",
                f"sheets: {len(deferred_rows)}", "discipline | sheets", *deferred_table,
            ],
        }
        if blocks != expected_blocks:
            errors.append(f"the slice's read plan sections are {blocks}, expected {expected_blocks}")
        for line in (
            f"every sheet once (units {len(sliced_keys)} plus deferred {len(deferred_rows)} equals "
            f"distinct sheets {remaining_count})",
            f"sheets deferred {len(deferred_rows)} by --only",
        ):
            if line not in slice_text.splitlines():
                errors.append(f"the slice's read plan totals do not carry `{line}`")
        if w2_path.is_file() and _SLICE_HEADING in w2_path.read_text(encoding="utf-8"):
            errors.append("a whole window 2 plan carries the slice's section")

    # The whole window after the slice, three of the slice's units dispatched: the three keep their
    # ids off the ledger and the other slice units off the plan file, all of them at the front of
    # the part their ids name, and every sheet the slice deferred numbered after the highest.
    #
    # Four of the slice's units were dispatched, three verified `ok` and one `mismatch`, beside an
    # `ok` line for an id no plan carries and one of another window. The plan marks exactly the
    # three and counts them on their pass block, so the lead dispatches that part again and its
    # runner skips them.
    ledger_units = expected_slice[:4]
    write_ledger(slice_dir, [
        "phase: window 2 paused",
        "dispatch: window 2 pass A2a units 6",
        *[
            f"dispatch 2 A2a {unit_id} sheets {sheet} purpose the sheet"
            for unit_id, sheet in ledger_units
        ],
        *[
            f"verified 2 A2a {unit_id} created 4 items 4 updated 0 questions 0 replied 0 sent 4 "
            f"landed 4 conflicts 0 result {'ok' if index < 3 else 'mismatch'}"
            for index, (unit_id, _sheet) in enumerate(ledger_units)
        ],
        "verified 2 A2a A2a-99 created 1 items 1 updated 0 questions 0 replied 0 sent 1 landed 1 "
        "conflicts 0 result ok",
        f"verified 1 A2a {expected_slice[4][0]} created 1 items 1 updated 0 questions 0 replied 0 "
        f"sent 1 landed 1 conflicts 0 result ok",
    ])
    finished = {unit_id for unit_id, _sheet in ledger_units[:3]}

    def marked_units(text: str) -> set[str]:
        """The planned unit ids whose line ends with the verified marker, off the file itself."""
        marked: set[str] = set()
        for line in text.splitlines():
            if line.strip() == _LEFT_OUT_HEADING:
                break
            unit = _PLAN_UNIT_RE.match(line)
            if unit and unit.group(4).endswith(" verified"):
                marked.add(unit.group(1))
        return marked

    a_sizes = _expected_split(len(slice_a), 12)
    if len(a_sizes) != 2:
        errors.append(f"the slice fixture's architectural discipline splits {a_sizes}, not in two")
    a_kept = [(unit_id, sheet) for unit_id, sheet in expected_slice if unit_id.startswith("A2a-")]
    a_new = [r["sheetNumber"] for r in in_type_order(slice_a) if r["unitKey"] not in sliced_keys]
    room = a_sizes[0] - len(a_kept)
    expected_whole = (
        a_kept
        + [(f"A2a-{i}", sheet) for i, sheet in enumerate(a_new[:room], len(a_kept) + 1)]
        + [(f"A2b-{i}", sheet) for i, sheet in enumerate(a_new[room:], 1)]
        + [(unit_id, sheet) for unit_id, sheet in expected_slice if unit_id.startswith("S2-")]
        + [
            (f"S2-{i}", r["sheetNumber"])
            for i, r in enumerate(
                [r for r in in_type_order(slice_s) if r["unitKey"] not in sliced_keys], len(sliced_s) + 1
            )
        ]
        + [(f"M2-{i}", r["sheetNumber"]) for i, r in enumerate(in_type_order(slice_m), 1)]
    )
    code, whole_bounds, err, whole_passes = run_replan(slice_dir, 2, slice_inventory, slice_window_1)
    if code != 0:
        errors.append(f"the whole window after the slice refused: {err}")
    else:
        if planned_ids(whole_passes) != expected_whole:
            errors.append(
                f"the whole window after the slice did not keep the slice's ids in part a and number "
                f"the rest after them: {planned_ids(whole_passes)}, expected {expected_whole}"
            )
        whole_count = len(sliced_keys) + len(deferred_rows)
        # With nothing deferred the partition reads exactly as it always has.
        expect_bounds("the whole window after the slice", whole_bounds,
                      f"every sheet once (units {whole_count} equals distinct sheets {whole_count})")
        expect_bounds("the whole window after the slice", whole_bounds,
                      f"ids kept {len(expected_slice)} (ledger {len(ledger_units)}, plan file "
                      f"{len(expected_slice) - len(ledger_units)}), ids new {len(deferred_rows)}, "
                      f"ids retired 0")
        whole_text = (slice_dir / "read-plan.md").read_text(encoding="utf-8")
        if marked_units(whole_text) != finished:
            errors.append(
                f"the whole window after the slice marks {sorted(marked_units(whole_text))} as "
                f"verified, expected {sorted(finished)}"
            )
        for plan_pass in whole_passes:
            want = str(len(finished)) if plan_pass["id"] == "A2a" else "0"
            if plan_pass["fields"].get("units verified") != want:
                errors.append(
                    f"the whole window's pass {plan_pass['id']} reads `units verified: "
                    f"{plan_pass['fields'].get('units verified')}`, expected {want}"
                )
        if "deferred" in whole_bounds:
            errors.append(f"the whole window's bounds line names a deferral: {whole_bounds!r}")
        _check_split_arithmetic(whole_passes, 12, errors, "the whole window after the slice")
        whole_file = json.loads((slice_dir / "plan" / "window-2.json").read_text(encoding="utf-8"))
        if (whole_file.get("only"), whole_file.get("deferredKeys"), whole_file.get("deferredCount")) != ([], [], 0):
            errors.append("the whole window's window-2.json still carries a slice or a deferral")
        if _SLICE_HEADING in whole_text:
            errors.append("the whole window's read plan still carries the slice's section")

    # A second slice defers the first one's dispatched units: they keep their numbers and are not
    # counted retired, since they come back on the next full plan, and the sheet it names keeps the
    # id the full plan gave it.
    s202 = {sheet: unit_id for unit_id, sheet in expected_whole}.get("S-2.02", "")
    code, again_bounds, err, again_passes = run_replan(
        slice_dir, 2, slice_inventory,
        slice_window_1 + ["--only", "S-2.02:the user asked for one more plan first"],
    )
    if code != 0:
        errors.append(f"a second slice after dispatched units refused: {err}")
    else:
        if planned_ids(again_passes) != [(s202, "S-2.02")]:
            errors.append(f"the second slice planned {planned_ids(again_passes)}, expected {[(s202, 'S-2.02')]}")
        expect_bounds("a second slice after dispatched units", again_bounds,
                      "ids kept 1 (ledger 0, plan file 1), ids new 0, ids retired 0")

    # --- a planned id that changes pass is renumbered, not refused ----- #
    #
    # The whole window planned first, nothing dispatched, then the same slice: a slice unit whose
    # planned id already sits in part a keeps it, one whose id is in part b is numbered after the
    # highest part a number the slice keeps, and its old id is retired. Only a dispatched id is
    # refused for changing pass, since only a dispatched id has rows on the record.
    flip_dir = replan_root / "whole-then-slice"
    flip_inventory = write_replan_inventory(flip_dir, vocabulary_rows + slice_a + slice_s + slice_m)
    flip_window_1 = ["--window-1", str(flip_dir / "plan" / "window-1.json")]
    code, _bounds, err, _passes = run_replan(flip_dir, 1, flip_inventory, [])
    if code != 0:
        errors.append(f"the renumbering fixture's window 1 run refused: {err}")
    old_id: dict[str, str] = {}
    whole_order_a = in_type_order(slice_a)
    start = 0
    for index, size in enumerate(_expected_split(len(whole_order_a), 12)):
        for number in range(1, size + 1):
            old_id[whole_order_a[start + number - 1]["sheetNumber"]] = (
                f"A2{string.ascii_lowercase[index]}-{number}"
            )
        start += size
    for number, row in enumerate(in_type_order(slice_s), 1):
        old_id[row["sheetNumber"]] = f"S2-{number}"
    code, _bounds, err, flip_whole = run_replan(flip_dir, 2, flip_inventory, flip_window_1)
    if code != 0:
        errors.append(f"the renumbering fixture's whole window refused: {err}")
    elif {sheet: unit_id for unit_id, sheet in planned_ids(flip_whole) if sheet in old_id} != old_id:
        errors.append("the renumbering fixture's whole window did not number as this check expects")

    def id_order(unit_id: str) -> tuple[str, int]:
        pass_component, number = unit_id.rsplit("-", 1)
        return pass_component, int(number)

    sliced_old = sorted(
        ((old_id[r["sheetNumber"]], r["sheetNumber"]) for r in sliced_a), key=lambda pair: id_order(pair[0])
    )
    stay = [(unit_id, sheet) for unit_id, sheet in sliced_old if unit_id.startswith("A2a-")]
    moved = [(unit_id, sheet) for unit_id, sheet in sliced_old if not unit_id.startswith("A2a-")]
    if not stay or not moved:
        errors.append("the renumbering fixture proves nothing about keeping and renumbering in one slice")
    top = max((id_order(unit_id)[1] for unit_id, _sheet in stay), default=0)
    expected_flip = (
        stay
        + [(f"A2a-{top + i}", sheet) for i, (_old, sheet) in enumerate(moved, 1)]
        + [(old_id["S-2.01"], "S-2.01")]
    )
    code, flip_bounds, err, flip_passes = run_replan(
        flip_dir, 2, flip_inventory,
        flip_window_1 + ["--only", f"A-3.0[1-6]:{first_reason}", "--only", f"S-2.01:{second_reason}"],
    )
    if code != 0:
        errors.append(f"a slice after the whole window refused a planned id that changes pass: {err}")
    else:
        if planned_ids(flip_passes) != expected_flip:
            errors.append(
                f"a slice after the whole window planned {planned_ids(flip_passes)}, expected "
                f"{expected_flip}"
            )
        expect_bounds("a slice after the whole window", flip_bounds,
                      f"ids kept {len(stay) + 1} (ledger 0, plan file {len(stay) + 1}), ids new "
                      f"{len(moved)}, ids retired {len(moved)}")

    # The limit a slice lives within: the units the slices planned in one discipline keep their part
    # only while they fit the whole window's first part of it. Twenty-four sheets of one type split
    # twelve and twelve; a slice of twelve dispatched keeps every id, and a slice of thirteen, split
    # seven and six over itself, puts A2b-1 at position eight of part a, which the plan refuses.
    def dispatched_slice(case: str, count: int) -> tuple[Path, str, list[tuple[str, str]], str]:
        folder = replan_root / case
        rows_a = [slice_row("A", f"A-3.{i:02d}", "plan", 19 + i) for i in range(1, 25)]
        inventory_path = write_replan_inventory(folder, vocabulary_rows + rows_a)
        run_code, _b, run_err, _p = run_replan(folder, 1, inventory_path, [])
        if run_code != 0:
            errors.append(f"the {case} fixture's window 1 run refused: {run_err}")
        window_1_args = ["--window-1", str(folder / "plan" / "window-1.json")]
        reason = f"the user asked for {count} plans first"
        only_args = ["--only", f"A-3.0*:{reason}", "--only", f"A-3.1[0-{count - 10}]:{reason}"]
        sizes = _expected_split(count, 12)
        expected: list[tuple[str, str]] = []
        start = 0
        for index, size in enumerate(sizes):
            part = f"A2{string.ascii_lowercase[index]}"
            expected += [(f"{part}-{i}", rows_a[start + i - 1]["sheetNumber"]) for i in range(1, size + 1)]
            start += size
        run_code, _b, run_err, cut_passes = run_replan(folder, 2, inventory_path, window_1_args + only_args)
        if run_code != 0:
            errors.append(f"the {case} slice refused: {run_err}")
        elif planned_ids(cut_passes) != expected:
            errors.append(f"the {case} slice planned {planned_ids(cut_passes)}, expected {expected}")
        write_ledger(folder, [
            f"dispatch 2 {unit_id.rsplit('-', 1)[0]} {unit_id} sheets {sheet} purpose the sheet"
            for unit_id, sheet in expected
        ])
        return folder, inventory_path, expected, window_1_args[1]

    twelve_dir, twelve_inventory, twelve_ids, twelve_window_1 = dispatched_slice("slice-twelve", 12)
    code, twelve_bounds, err, twelve_passes = run_replan(
        twelve_dir, 2, twelve_inventory, ["--window-1", twelve_window_1])
    if code != 0:
        errors.append(f"the whole window after a slice of twelve dispatched refused: {err}")
    else:
        if planned_ids(twelve_passes)[:12] != twelve_ids:
            errors.append(
                f"the whole window after a slice of twelve dispatched did not keep them as part a: "
                f"{planned_ids(twelve_passes)[:12]}, expected {twelve_ids}"
            )
        expect_bounds("the whole window after a slice of twelve dispatched", twelve_bounds,
                      "ids kept 12 (ledger 12, plan file 0), ids new 12, ids retired 0")
    thirteen_dir, thirteen_inventory, thirteen_ids, thirteen_window_1 = dispatched_slice("slice-thirteen", 13)
    if [unit_id for unit_id, _sheet in thirteen_ids][7:8] != ["A2b-1"]:
        errors.append(f"the thirteen fixture does not put A2b-1 eighth: {thirteen_ids}")
    refused_plan = str(out_dir / "refused.md")
    slice_refusals: list[tuple[str, list[str], str]] = [
        (
            "an --only on window 1",
            ["plan", "--window", "1", "--inventory", inventory_json,
             "--only", f"{include_pattern}:the elevations first", "--out", refused_plan],
            "--only is a window 2 argument",
        ),
        (
            "an --only pattern matching no sheet window 2 reads",
            # Every sheet the include pattern names is one window 1 already reads.
            ["plan", "--window", "2", "--inventory", inventory_json, "--window-1", str(window_1_json),
             "--only", f"{include_pattern}:the elevations first", "--out", refused_plan],
            f"no sheet number window 2 reads matches the pattern {include_pattern}",
        ),
        (
            "thirteen units dispatched in one discipline across a slice",
            ["plan", "--window", "2", "--inventory", thirteen_inventory, "--window-1", thirteen_window_1,
             "--out", str(thirteen_dir / "read-plan.md")],
            f"unit A2b-1 read sheet {thirteen_ids[7][1] if len(thirteen_ids) > 7 else ''} and this "
            f"plan puts that sheet in pass A2a",
        ),
    ]

    # --- the seven ways a kept id would be wrong ----------------------- #
    #
    # Each one stops the plan rather than renumbering, because every one of them would move an id
    # the record already carries rows under.
    def broken_replan(case: str, ledger_lines: list[str], inventory_rows: list[dict]) -> tuple[Path, str]:
        folder = replan_root / "broken" / case
        path = write_replan_inventory(folder, inventory_rows)
        write_ledger(folder, ledger_lines)
        return folder / "read-plan.md", path

    read_line = "purpose a schedule this pass reads"
    doubled_rows = vocabulary_rows + [replan_row("A-1.01", "schedule", 99)]
    wide_rows = vocabulary_rows + [
        replan_row(f"A-1.{index}", "schedule", index) for index in range(12, 15)
    ]

    bad_id_out, bad_id_inventory = broken_replan(
        "unit-id", [f"dispatch 1 A1 A1x sheets A-1.01 {read_line}"], vocabulary_rows)
    two_ids_out, two_ids_inventory = broken_replan(
        "sheet-under-two-ids",
        [f"dispatch 1 A1 A1-1 sheets A-1.01 {read_line}",
         f"dispatch 1 A1 A1-2 sheets A-1.01 {read_line}"],
        vocabulary_rows)
    two_sets_out, two_sets_inventory = broken_replan(
        "id-over-two-sheet-sets",
        [f"dispatch 1 A1 A1-1 sheets A-1.01 {read_line}",
         f"dispatch 1 A1 A1-1 sheets A-1.02 {read_line}"],
        vocabulary_rows)
    doubled_out, doubled_inventory = broken_replan(
        "sheet-on-two-rows", [f"dispatch 1 A1 A1-1 sheets A-1.01 {read_line}"], doubled_rows)
    partly_out, partly_inventory = broken_replan(
        "partly-cut", [f"dispatch 1 A1 A1-1 sheets A-1.01,A-1.02 {read_line}"], vocabulary_rows)
    split_out, split_inventory = broken_replan(
        "split-units", [f"dispatch 1 A1 A1-1 sheets A-1.01,A-1.02 {read_line}"], vocabulary_rows)
    moved_out, moved_inventory = broken_replan(
        "moved-pass", [f"dispatch 1 A1 A1-1 sheets A-1.01 {read_line}"], wide_rows)

    replan_refusals: list[tuple[str, list[str], str]] = [
        (
            "a ledger dispatch line whose unit id is not <pass>-<number>",
            ["plan", "--window", "1", "--inventory", bad_id_inventory, "--out", str(bad_id_out)],
            "A1x",
        ),
        (
            "one sheet number dispatched under two unit ids",
            ["plan", "--window", "1", "--inventory", two_ids_inventory, "--out", str(two_ids_out)],
            "A-1.01 under A1-1 and A1-2",
        ),
        (
            "one unit id dispatched over two sheet sets",
            ["plan", "--window", "1", "--inventory", two_sets_inventory, "--out", str(two_sets_out)],
            "unit A1-1 is dispatched on",
        ),
        (
            "a bound sheet number the inventory holds twice",
            ["plan", "--window", "1", "--inventory", doubled_inventory, "--out", str(doubled_out)],
            "holds 2 times",
        ),
        (
            "a bound unit whose sheets are only partly still in the cut",
            ["plan", "--window", "1", "--inventory", partly_inventory,
             "--exclude", "A-1.02:the user took this sheet out of the window", "--out", str(partly_out)],
            "1 of them as its own unit",
        ),
        (
            "a bound unit whose sheets all stay in the cut and plan as two units",
            ["plan", "--window", "1", "--inventory", split_inventory, "--out", str(split_out)],
            "unit A1-1 was dispatched on A-1.01, A-1.02 and this plan reads them as 2 separate units",
        ),
        (
            "a bound unit whose sheet now plans under a different pass part",
            ["plan", "--window", "1", "--inventory", moved_inventory, "--out", str(moved_out)],
            "pass A1a",
        ),
    ]

    # ------------------------------------------------------------------ #
    # Every sheet unit line's page reference, checked against the fixture grid
    # ------------------------------------------------------------------ #
    sheet_units = [unit for p in w1_passes + w2_passes for unit in p["units"]]
    misplaced = [
        f"{sheet} on page {page} where the grid says {page_of.get(sheet)}"
        for _unit_id, sheet, page in sheet_units
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
    refusals.extend(replan_refusals)
    refusals.extend(slice_refusals)
    for what, argv, must_name in refusals:
        code, _refused_bounds, err = _run_script_main(module, argv)
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
        f"a first plan of each window numbering its units from 1, a replan keeping the ids the "
        f"ledger and the plan file already handed out and numbering five new sheets after the "
        f"highest, an id the ledger dispatched read back onto the same sheet, a cut sheet's id "
        f"retired and not handed out again, the ledger beating the plan file, window 2 numbering "
        f"its new sheets in the pinned type order, a window 2 slice planned with --only deferring "
        f"the rest with its bounds line, window-2.json and read plan sections checked against an "
        f"independent tally, the full plan after it keeping the slice's ids in part a with three "
        f"and then twelve dispatched, every pass counting and marking exactly its units verified ok, "
        f"a planned id that changes pass renumbered with the old one retired, a second slice "
        f"holding the first one's dispatched ids, window-1.json carrying its patterns, "
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
# Check: the pass summary script
# --------------------------------------------------------------------------- #
#
# A pass runner verifies each unit against the record and appends that unit's counts to the run
# ledger as it goes, and then the pass summary says those counts again. A runner that added them up
# itself gave a second answer that did not match the first, so the shipped script sums the ledger
# and the runner writes what it returns. This runs the script in-process over two ledger fixtures
# and asserts every number against a tally computed here off the same fixture text.
#
# The join this check exists for: the summary shape is published in the skill and in the runner
# definition, and the script fills it. The three would otherwise meet for the first time mid-run,
# so the labels the script prints are compared against the labels of the skill's own fenced block,
# in order, with nothing extra and nothing missing.
#
# Honest bound, stated in the detail line: the fixtures are ledger text, so this proves the
# script's arithmetic, its line placement and its refusals, and nothing about a real verification.

PASS_SUMMARY_SCRIPT = ("scripts", "pass_summary.py")

_SUMMARY_LABEL_RE = re.compile(r"^([a-z][a-z ]*): ")


def _fenced_block_bodies(lines: list[str]) -> list[list[str]]:
    """Every closed fenced block's body, in file order. A fence left open drops its body."""
    blocks: list[list[str]] = []
    body: list[str] = []
    inside = False
    for line in lines:
        if line.lstrip().startswith("```"):
            if inside:
                blocks.append(body)
                body = []
            inside = not inside
            continue
        if inside:
            body.append(line)
    return blocks


def _summary_labels(lines: list[str]) -> list[str]:
    """
    The label of each summary line, with consecutive repeats collapsed. `per unit:` prints one line
    per unit and `anomalies:` one line per note, while the published shape names each label once,
    so the two are comparable only after the repeats are folded.
    """
    labels: list[str] = []
    for line in lines:
        m = _SUMMARY_LABEL_RE.match(line)
        if m is None:
            continue
        label = m.group(1)
        if not labels or labels[-1] != label:
            labels.append(label)
    return labels


def _ledger_rows(path: Path, window: int, pass_id: str) -> list[list[str]]:
    """This window and pass's runner lines, split into fields, read here rather than off the script."""
    rows: list[list[str]] = []
    for raw in path.read_text(encoding="utf-8").splitlines():
        parts = raw.split()
        if len(parts) < 4 or parts[0] not in ("dispatch", "verified", "note"):
            continue
        if parts[1] != str(window) or parts[2] != pass_id:
            continue
        rows.append(parts)
    return rows


def check_pass_summary(plugin_path: Path, marketplace_root: Path) -> Result:
    name = "pass-summary"
    script = plugin_path.joinpath(*PASS_SUMMARY_SCRIPT)
    if not script.is_file():
        return Result(name, False, detail=f"pass summary script not found at {script}")

    fixtures = marketplace_root / "harness" / "fixtures"
    a1_fixture = fixtures / "ledger-fixture-a1.md"
    mixed_fixture = fixtures / "ledger-fixture-mixed.md"
    trades_fixture = fixtures / "trades-fixture.txt"
    for fixture in (a1_fixture, mixed_fixture, trades_fixture):
        if not fixture.is_file():
            return Result(name, False, detail=f"fixture not found at {fixture}")

    try:
        module = _load_script_module(script, "pass_summary")
    except Exception as e:
        return Result(name, False, detail=f"cannot import {script.name}: {e}")

    errors: list[str] = []
    out_dir = Path(__file__).parent / ".test-results" / "pass-summary"
    out_dir.mkdir(parents=True, exist_ok=True)

    # ------------------------------------------------------------------ #
    # The whole of one pass, against a tally computed here
    # ------------------------------------------------------------------ #
    code, a1_out, a1_err = _run_script_main(module, [str(a1_fixture), "1", "A1"])
    a1_lines = a1_out.splitlines()
    if code != 0:
        return Result(name, False, detail=f"the A1 fixture refused: {a1_err or a1_out}")

    rows = _ledger_rows(a1_fixture, 1, "A1")
    expected_units: list[str] = []
    for parts in rows:
        if parts[0] == "dispatch" and parts[3] not in expected_units:
            expected_units.append(parts[3])
    verified_rows = [parts for parts in rows if parts[0] == "verified"]

    def field_of(parts: list[str], field: str) -> int:
        return int(parts[parts.index(field) + 1])

    expected_totals = {
        field: sum(field_of(parts, field) for parts in verified_rows)
        for field in ("created", "items", "updated", "questions", "replied", "conflicts")
    }

    if f"units read: {', '.join(expected_units)}" not in a1_lines:
        errors.append(
            f"`units read:` is not the dispatched units in reading order, once each: "
            f"{[l for l in a1_lines if l.startswith('units read:')]}"
        )
    if len(expected_units) != len(set(expected_units)):
        errors.append("the A1 fixture no longer dispatches a unit twice, which is the case that line exists for")

    for parts in verified_rows:
        counts = " ".join(
            f"{field} {field_of(parts, field)}"
            for field in ("created", "items", "updated", "questions", "replied")
        )
        verdict = "yes" if parts[parts.index("result") + 1] == "ok" else "no"
        wanted = f"per unit: {parts[3]} {counts} verified {verdict}"
        if wanted not in a1_lines:
            errors.append(f"the per unit line for {parts[3]} is not {wanted!r}")
    per_unit_lines = [line for line in a1_lines if line.startswith("per unit: ")]
    if len(per_unit_lines) != len(expected_units):
        errors.append(
            f"{len(per_unit_lines)} per unit lines over {len(expected_units)} units read"
        )

    wanted_totals = (
        f"totals verified: created {expected_totals['created']} (entry count under the unit "
        f"prefixes), items {expected_totals['items']} (reader's own item count), updated "
        f"{expected_totals['updated']}, questions {expected_totals['questions']} replied "
        f"{expected_totals['replied']}"
    )
    if wanted_totals not in a1_lines:
        errors.append(
            f"the totals line is not the sum of the verified lines: "
            f"{[l for l in a1_lines if l.startswith('totals verified:')]}, expected {wanted_totals!r}"
        )

    conflicted = [parts[3] for parts in verified_rows if field_of(parts, "conflicts")]
    wanted_conflicts = f"conflicting rows: {expected_totals['conflicts']}, on units {', '.join(conflicted)}"
    if wanted_conflicts not in a1_lines:
        errors.append(f"the conflicting rows line is not {wanted_conflicts!r}")

    expected_kinds: list[str] = []
    for parts in rows:
        if parts[0] == "note" and parts[4] == "kinds":
            for word in parts[5:]:
                if word not in expected_kinds:
                    expected_kinds.append(word)
    if f"definitions kinds added: {', '.join(expected_kinds)}" not in a1_lines:
        errors.append("the definitions kinds line is not the union of the fixture's kinds notes, in first-seen order")

    for kind, label in (("anomaly", "anomalies"), ("deviation", "deviations and repairs"),
                        ("overlap", "overlap notes")):
        of_kind = [parts for parts in rows if parts[0] == "note" and parts[4] == kind]
        printed = [line for line in a1_lines if line.startswith(f"{label}: ")]
        if len(printed) != len(of_kind):
            errors.append(f"{label} carries {len(printed)} lines over {len(of_kind)} `{kind}` notes")
        for parts in of_kind:
            where = "" if parts[3] == "-" else f"{parts[3]} "
            wanted = f"{label}: {where}{' '.join(parts[5:])}"
            if wanted not in a1_lines:
                errors.append(f"a `{kind}` note is not carried verbatim: expected {wanted!r}")
    if "unread pages: none" not in a1_lines:
        errors.append("the A1 fixture raises no unread note, so that line has to read none")

    if f"ledger: {a1_fixture}, appended through " not in a1_out:
        errors.append("the ledger line does not name the file it read")

    # stdout is the deliverable, so the bounds line has to be somewhere else.
    if len(a1_err.splitlines()) != 1 or not a1_err.startswith("pass_summary: read "):
        errors.append(f"the bounds line is not one line on stderr: {a1_err!r}")
    stray = [line for line in a1_lines if _SUMMARY_LABEL_RE.match(line) is None]
    if stray:
        errors.append(f"stdout carries {len(stray)} line(s) that are not summary lines: {stray[:3]}")

    # ------------------------------------------------------------------ #
    # The join: the labels the script prints are the published shape's
    # ------------------------------------------------------------------ #
    skill = plugin_path / "skills" / "scope-run" / "SKILL.md"
    published: list[str] = []
    if not skill.is_file():
        errors.append(f"skill not found at {skill}")
    else:
        blocks = [
            block for block in _fenced_block_bodies(skill.read_text(encoding="utf-8").splitlines())
            if any(line.startswith("per unit:") for line in block)
        ]
        if len(blocks) != 1:
            errors.append(f"{len(blocks)} runner summary blocks in {skill.name}, expected 1")
        else:
            published = _summary_labels(blocks[0])
            if _summary_labels(a1_lines) != published:
                errors.append(
                    f"the script prints the labels {_summary_labels(a1_lines)} and the skill "
                    f"publishes {published}"
                )

    # ------------------------------------------------------------------ #
    # One pass only, and none of the lead's own numbers
    # ------------------------------------------------------------------ #
    code, mixed_out, mixed_err = _run_script_main(module, [str(mixed_fixture), "1", "B1"])
    mixed_lines = mixed_out.splitlines()
    if code != 0:
        errors.append(f"the mixed fixture refused: {mixed_err or mixed_out}")
    else:
        mixed_rows = _ledger_rows(mixed_fixture, 1, "B1")
        mixed_verified = [parts for parts in mixed_rows if parts[0] == "verified"]
        mixed_created = sum(field_of(parts, "created") for parts in mixed_verified)
        if f"created {mixed_created} (entry count" not in mixed_out:
            errors.append(f"the mixed fixture's totals are not the sum of its own verified lines")
        for stranger in ("9999", "777", "333"):
            if stranger in mixed_out:
                errors.append(
                    f"a figure from the lead's own line, another pass or another window reached "
                    f"the totals: {stranger}"
                )
        # A dispatched unit with no verified line prints dashes and is named on the bounds line.
        if "per unit: B1-3 created - items - updated - questions - replied - verified no" not in mixed_lines:
            errors.append("a dispatched unit with no verified line does not print as unverified")
        if "dispatched with no verified line: B1-3" not in mixed_err:
            errors.append(f"the bounds line does not name the unverified unit: {mixed_err!r}")
        if "verified no" not in " ".join(
            line for line in mixed_lines if line.startswith("per unit: B1-2 ")
        ):
            errors.append("a unit whose result is a mismatch does not print as unverified")
        # The last line of this pass, not the last line of the file.
        last_of_pass = [" ".join(parts) for parts in mixed_rows][-1]
        if not mixed_out.rstrip().endswith(last_of_pass):
            errors.append(
                f"the ledger line names {mixed_lines[-1]!r} rather than this pass's last line, "
                f"{last_of_pass!r}"
            )
        # Three note kinds have no line in this shape, and the bounds line counts them rather than
        # letting a note land nowhere in silence.
        for kind in ("grain", "door", "packet"):
            if f"{kind} 1 with no summary line" not in mixed_err:
                errors.append(f"the bounds line does not count the `{kind}` note it read: {mixed_err!r}")

    # ------------------------------------------------------------------ #
    # The trades file
    # ------------------------------------------------------------------ #
    code, trades_out, _trades_err = _run_script_main(
        module, [str(a1_fixture), "1", "A1", "--trades", str(trades_fixture)]
    )
    if code != 0:
        errors.append("the trades fixture refused")
    else:
        by_trade: dict[str, int] = {}
        candidates = 0
        for raw in trades_fixture.read_text(encoding="utf-8").splitlines():
            parts = raw.split()
            if not parts:
                continue
            if parts[1] == "candidates":
                candidates += int(parts[2])
            else:
                code_text = " ".join(parts[2:-1])
                by_trade[code_text] = by_trade.get(code_text, 0) + int(parts[-1])
        ordered = sorted(by_trade.items(), key=lambda pair: (-pair[1], pair[0]))
        wanted = (
            "trades: " + ", ".join(f"{c} x{n}" for c, n in ordered) + f"; candidates {candidates}"
        )
        if wanted not in trades_out.splitlines():
            errors.append(f"the trades line is not the sum of the trades file: expected {wanted!r}")
        if len({n for _c, n in ordered}) == len(ordered):
            errors.append("the trades fixture never ties on count, so it proves nothing about the tie break")
    if "trades: no trades file for this pass" not in a1_lines:
        errors.append("without a trades file the trades line does not say so")

    # ------------------------------------------------------------------ #
    # Refusals, each exiting 1 with one line on stderr
    # ------------------------------------------------------------------ #
    a1_text = a1_fixture.read_text(encoding="utf-8")
    broken: list[tuple[str, str, str]] = [
        (
            "two verified lines for one unit",
            a1_text + "verified 1 A1 A1-1 created 1 items 1 updated 0 questions 0 replied 0 "
                      "sent 1 landed 1 conflicts 0 result ok\n",
            "already carries a verified line",
        ),
        (
            "a count that is not a whole number",
            a1_text.replace("created 29 items 7", "created many items 7"),
            "not a whole number",
        ),
        (
            "a verified line missing a field the shape names",
            a1_text.replace(" landed 96 conflicts 0", " landed 96"),
            "no `conflicts` field",
        ),
        (
            "a dispatch line with no sheets field",
            a1_text.replace("dispatch 1 A1 A1-1 sheets A-0.11", "dispatch 1 A1 A1-1 pages A-0.11"),
            "no `sheets` field",
        ),
        (
            "a note kind outside the closed set",
            a1_text.replace("note 1 A1 A1-6 anomaly", "note 1 A1 A1-6 observation"),
            "observation",
        ),
        (
            "a line whose first word is none of the three shapes",
            a1_text + "narrative 1 A1 A1-1 a sentence nobody is counting\n",
            "none of the three shapes",
        ),
    ]
    refusals: list[tuple[str, list[str], str]] = []
    for index, (what, text, must_name) in enumerate(broken, 1):
        path = out_dir / f"broken-{index}.md"
        path.write_text(text, encoding="utf-8")
        refusals.append((what, [str(path), "1", "A1"], must_name))
    refusals.extend([
        (
            "a window and pass with no lines",
            [str(a1_fixture), "2", "A1"],
            "carries no dispatch, verified or note line",
        ),
        (
            "a ledger that is not there",
            [str(out_dir / "no-such-ledger.md"), "1", "A1"],
            "no ledger at",
        ),
        (
            "a trades file that is not there",
            [str(a1_fixture), "1", "A1", "--trades", str(out_dir / "no-such-trades.txt")],
            "no trades file at",
        ),
        (
            "a trades file line in neither of its two shapes",
            [str(a1_fixture), "1", "A1", "--trades", str(out_dir / "broken-trades.txt")],
            "neither",
        ),
    ])
    (out_dir / "broken-trades.txt").write_text("A1-1 trades 09 21 16\n", encoding="utf-8")

    for what, argv, must_name in refusals:
        run_code, run_out, run_err = _run_script_main(module, argv)
        if run_code != 1:
            errors.append(f"{what}: exited {run_code}, not 1")
        elif len(run_err.splitlines()) != 1:
            errors.append(f"{what}: the refusal is not one line on stderr")
        elif must_name not in run_err:
            errors.append(f"{what}: the refusal does not name {must_name}: {run_err!r}")
        elif run_out:
            errors.append(f"{what}: a refusal still printed a summary on stdout")

    detail = (
        f"{len(expected_units)} units over one pass of a ledger fixture: units read, every per "
        f"unit line, the totals, the conflicting rows, the definitions kinds union and every note "
        f"line checked against a tally computed here off the same text; {len(published)} summary "
        f"labels matched against the skill's own published block in order; a second fixture "
        f"proving another pass, another window and the lead's own `pass:` line reach no total, a "
        f"dispatched unit with no verified line printing as unverified and named on the bounds "
        f"line, a mismatch result printing as unverified, the ledger line naming this pass's last "
        f"line, and the three note kinds with no summary line counted rather than dropped; the "
        f"trades line summed from a trades file and said plainly to be absent without one; "
        f"{len(refusals)} broken invocations each refused in one line naming what is wrong, with "
        f"nothing on stdout"
    )
    # An honest bound, not a pass: the fixtures are ledger text. This proves the script's
    # arithmetic, where each note lands and what it refuses, and nothing about a real verification.
    detail += "; bound: ledger fixtures, not a real pass"
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
# Check: each run agent names the connector verbs it uses
# --------------------------------------------------------------------------- #
#
# All three run agents declared the whole connector as one wildcard, so a sheet reader held every
# verb the connector registers: the ones that create a project, delete a bid package, invite a sub,
# send a question out. Naming the verbs is the containment: an agent can call what its text tells it
# to call, and nothing else. That only holds while the two sides agree, which is what this checks.
#
# Four arms:
#   1. No tools line carries the connector wildcard.
#   2. Every connector verb an agent's body names is on that agent's tools line, so a definition
#      cannot instruct a call the runtime would refuse.
#   3. Every declared connector verb is one the connector registers, so a typo fails the release
#      rather than shipping a tool that silently is not there.
#   4. The exception table stays honest: each entry is still named in that agent's text and still
#      absent from its tools line.
#
# What this cannot judge: whether a declared verb is one the agent should hold. That stays in
# review. It proves the tools line and the text agree, and that both name real verbs.

# The verbs the connector registers, a pinned copy of the api's own registrations (one
# `server.registerTool` call each), on the LEDGER_NOTE_KINDS precedent: the harness never reaches
# the api, so the list is stated here and a new api verb an agent names means adding it here too.
CONNECTOR_VERBS = {
    "add_question_source", "ask_question", "assign_sheet_packages", "cite_source",
    "clear_quantity", "close_question", "create_drawing_delivery", "create_project",
    "deliverable_status", "directory_add_certification", "directory_add_company",
    "directory_add_comparable_project", "directory_add_contact", "directory_delete_company",
    "directory_delete_contact", "directory_find_subs_for_trade", "directory_get_company",
    "directory_list_companies", "directory_list_company_types", "directory_list_trades",
    "directory_remove_certification", "directory_remove_comparable_project",
    "directory_tag_trade", "directory_untag_trade", "directory_update_company",
    "directory_update_comparable_project", "directory_update_contact", "extract_spec_toc",
    "extract_spec_toc_status", "follow_up_question", "generate_deliverable",
    "get_bid_package", "get_page_text", "get_project", "index_citations",
    "index_citations_leftover", "index_citations_status", "list_definition_kinds",
    "list_definitions", "list_drawing_deliveries", "list_email_templates", "list_files",
    "list_invitation_flow_companies", "list_project_dates", "list_project_options",
    "list_projects", "list_questions", "list_scope_items", "log_question_reply_received",
    "mark_question_sent", "project_add_design_team_contact",
    "project_remove_design_team_contact", "project_set_design_team_contact", "question_board",
    "read_deliverables", "read_invitation_flow", "read_set_text", "read_sheet_context",
    "recognize_sheets", "recognize_sheets_status", "reconcile_index", "reconcile_set", "record",
    "record_additional_item", "record_batch", "record_batch_file", "register_file",
    "register_files", "register_pages", "remove_project_date", "render_page",
    "reopen_question", "reply_question", "request_file_upload", "request_file_uploads",
    "restore_scope_item", "restore_source", "retire_scope_item", "retract_source",
    "rewrite_question", "search", "search_set_symbols", "search_set_symbols_status",
    "search_set_text", "set_grid", "set_invitation_labor", "set_invitation_places",
    "set_invitation_trades", "set_project_date", "set_question_reference",
    "set_question_reminder", "set_question_trades", "set_text_status",
    "solicitation_coverage", "solicitation_create_package", "solicitation_delete_package",
    "solicitation_get_package", "solicitation_invite", "solicitation_list_invitations",
    "solicitation_list_packages", "solicitation_log_touchpoint",
    "solicitation_remove_invitation", "solicitation_update_invitation",
    "solicitation_update_package", "takeoff_condition", "takeoff_read", "takeoff_record",
    "takeoff_retract", "update_drawing_delivery", "update_file", "update_project",
    "verify_unit", "whoami",
}

CONNECTOR_TOOL_PREFIX = "mcp__plugin_plumlayer_plumlayer__"

# Verbs an agent's text names without ever calling them: in a prohibition, or in an account of
# another agent's writes. The agent must not hold them, so the tools line leaves them off and the
# arm that would flag the mismatch reads the reason here instead.
TOOLS_PROHIBITION_ONLY = {
    "scope-round-runner": {
        # The runner dispatches readers; it cites nothing and reads no scope list itself.
        "cite_source", "list_scope_items",
    },
    "scope-reviewer": {
        # The reviewer adds what no row carries; retiring a row is the estimator's call.
        "retire_scope_item",
    },
}

_CONNECTOR_DECLARATION_RE = re.compile(re.escape(CONNECTOR_TOOL_PREFIX) + r"([a-z][a-z0-9_]*)")

_VERB_TOKEN_RE = re.compile(r"[a-z][a-z0-9_]*")

# Group-capturing, and newline-tolerant where _INLINE_CODE_RE is not, because the body is joined
# into one string before the spans are found.
_INLINE_SPAN_RE = re.compile(r"`([^`]*)`")

# Inside a fenced block only a call shape counts, so an example or a report template cannot invent
# a verb while ordinary fenced text (a ledger line, a report field) stays untouched.
_FENCED_CALL_RE = re.compile(r"\b([a-z][a-z0-9_]*)\s*\(")


def _agent_body_lines(path: Path) -> list[str]:
    """The lines after the frontmatter block, so a tools line never counts as the body naming a
    verb. A file with no frontmatter is all body."""
    lines = path.read_text(encoding="utf-8").splitlines()
    if not lines or lines[0].strip() != "---":
        return lines
    for i, line in enumerate(lines[1:], start=1):
        if line.strip() == "---":
            return lines[i + 1:]
    return []  # unterminated block is no body


def _agent_tool_surface(path: Path) -> tuple[set[str], set[str], bool]:
    """
    Return (declared, named, wildcard) for one agent definition.

    `declared` are the connector verbs on its `tools:` line, `named` the connector verbs its body
    names, `wildcard` whether the tools line takes the whole connector.

    The body is joined before the spans are found, because an inline code span wraps across lines
    in these files (`get_page_text(...)` breaks mid-span in the reviewer) and a per-line scan
    desynchronizes on the unclosed backtick, silently reading prose as code from there on. Fenced
    blocks are scanned separately and only for a call shape.
    """
    tools_line = _parse_frontmatter(path).get("tools", "")
    declared = set(_CONNECTOR_DECLARATION_RE.findall(tools_line))
    wildcard = f"{CONNECTOR_TOOL_PREFIX}*" in tools_line

    body = _agent_body_lines(path)
    fence_mask = _fenced_code_line_mask(body)
    prose = " ".join(l for l, fenced in zip(body, fence_mask) if not fenced)

    named: set[str] = set()
    for span in _INLINE_SPAN_RE.findall(prose):
        named.update(t for t in _VERB_TOKEN_RE.findall(span) if t in CONNECTOR_VERBS)
    for line, fenced in zip(body, fence_mask):
        if fenced:
            named.update(v for v in _FENCED_CALL_RE.findall(line) if v in CONNECTOR_VERBS)

    return declared, named, wildcard


def _agent_tool_surface_errors(path: Path, agent: str, label: str) -> list[str]:
    """The four arms over one definition, in the terms the release reads them."""
    errors: list[str] = []
    declared, named, wildcard = _agent_tool_surface(path)

    if wildcard:
        errors.append(
            f"{label}: tools line takes the whole connector "
            f"(`{CONNECTOR_TOOL_PREFIX}*`) instead of naming its verbs"
        )

    for verb in sorted(declared - CONNECTOR_VERBS):
        errors.append(f"{label}: declares `{verb}`, which the connector does not register")

    prohibition_only = TOOLS_PROHIBITION_ONLY.get(agent, set())
    for verb in sorted(named - declared - prohibition_only):
        errors.append(f"{label}: names `{verb}` in its text but does not declare it on the tools line")

    for verb in sorted(prohibition_only):
        if verb not in named:
            errors.append(
                f"{label}: `{verb}` is held as prohibition-only but the file no longer names it"
            )
        if verb in declared:
            errors.append(
                f"{label}: `{verb}` is held as prohibition-only but the tools line now declares it"
            )

    return errors


def check_agent_tool_surface(plugin_path: Path, marketplace_root: Path) -> Result:
    name = "agent-tool-surface"
    agents_dir = plugin_path / "agents"
    if not agents_dir.is_dir():
        return Result(name, False, detail=f"agents/ directory not found at {agents_dir}")

    agent_files = sorted(agents_dir.rglob("*.md"))
    if not agent_files:
        return Result(name, False, detail="no agent definitions found in agents/")

    errors: list[str] = []
    declared_count = 0
    named_count = 0
    for agent_file in agent_files:
        declared, named, _ = _agent_tool_surface(agent_file)
        declared_count += len(declared)
        named_count += len(named)
        errors.extend(_agent_tool_surface_errors(agent_file, agent_file.stem, agent_file.name))

    # The same arms over fixtures, so the check is shown to refuse rather than assumed to: a clean
    # definition passes and each broken one comes back with the one line naming what is wrong.
    fixtures = marketplace_root / "harness" / "fixtures"
    expected = [
        ("agent-fixture-clean.md", None),
        ("agent-fixture-wildcard-tools.md", "takes the whole connector"),
        ("agent-fixture-unnamed-verb.md", "does not declare it on the tools line"),
    ]
    for fixture_name, wanted in expected:
        fixture = fixtures / fixture_name
        if not fixture.is_file():
            errors.append(f"fixture not found at {fixture}")
            continue
        got = _agent_tool_surface_errors(fixture, fixture.stem, fixture_name)
        if wanted is None:
            if got:
                errors.append(f"{fixture_name}: clean fixture refused: {'; '.join(got)}")
        elif len(got) != 1 or wanted not in got[0]:
            errors.append(
                f"{fixture_name}: expected one refusal naming '{wanted}', got {got}"
            )

    detail = (
        f"{len(agent_files)} agent definitions scanned, {declared_count} connector verbs declared "
        f"against {len(CONNECTOR_VERBS)} the connector registers, {named_count} named in their "
        f"text, {len(expected)} fixtures"
    )
    if errors:
        detail += " | " + "; ".join(errors)

    return Result(name, passed=len(errors) == 0, detail=detail)


# --------------------------------------------------------------------------- #
# Check: every agent definition pins its model
# --------------------------------------------------------------------------- #
#
# An agent with no `model` runs on whatever the session happens to be on, so the same pass costs
# and reasons differently depending on who dispatched it. Two of the three already pinned one and
# the runner did not, which is the drift this closes: the field is present and non-empty, and which
# model it names stays a decision, not a check.

def _agent_model_errors(path: Path, label: str) -> list[str]:
    if not _parse_frontmatter(path).get("model", "").strip():
        return [f"{label}: frontmatter `model` is missing or empty"]
    return []


def check_agent_model_pinned(plugin_path: Path, marketplace_root: Path) -> Result:
    name = "agents-model-pinned"
    agents_dir = plugin_path / "agents"
    if not agents_dir.is_dir():
        return Result(name, False, detail=f"agents/ directory not found at {agents_dir}")

    agent_files = sorted(agents_dir.rglob("*.md"))
    if not agent_files:
        return Result(name, False, detail="no agent definitions found in agents/")

    errors: list[str] = []
    models: list[str] = []
    for agent_file in agent_files:
        errors.extend(_agent_model_errors(agent_file, agent_file.name))
        models.append(f"{agent_file.stem}={_parse_frontmatter(agent_file).get('model', '').strip() or 'none'}")

    fixtures = marketplace_root / "harness" / "fixtures"
    expected = [
        ("agent-fixture-clean.md", None),
        ("agent-fixture-no-model.md", "frontmatter `model` is missing or empty"),
    ]
    for fixture_name, wanted in expected:
        fixture = fixtures / fixture_name
        if not fixture.is_file():
            errors.append(f"fixture not found at {fixture}")
            continue
        got = _agent_model_errors(fixture, fixture_name)
        if wanted is None:
            if got:
                errors.append(f"{fixture_name}: clean fixture refused: {'; '.join(got)}")
        elif len(got) != 1 or wanted not in got[0]:
            errors.append(f"{fixture_name}: expected one refusal naming '{wanted}', got {got}")

    detail = f"{', '.join(models)}, {len(expected)} fixtures"
    if errors:
        detail += " | " + "; ".join(errors)

    return Result(name, passed=len(errors) == 0, detail=detail)


# --------------------------------------------------------------------------- #
# Check: every dispatch template names the foreground
# --------------------------------------------------------------------------- #
#
# A dispatch is one Agent tool call and the call is the wait. A background dispatch breaks that
# shape: the dispatcher's turn can end with a reader still running, and a turn that ends in a
# headless session is a process that exits and takes the reader with it. The templates are where
# this run says how the call is made, so they are where the parameter is checked.
#
# What this cannot judge: whether a running agent actually passes the parameter. It proves the
# shipped text tells it to.

_SUBAGENT_TYPE_LINE_RE = re.compile(r"^\s*subagent_type\s*:", re.IGNORECASE)
_FOREGROUND_LINE_RE = re.compile(r"^\s*run_in_background\s*:\s*false\s*$", re.IGNORECASE)


def _fenced_blocks(lines: list[str]) -> tuple[list[tuple[int, list[str]]], int]:
    """
    Every fenced block, as (the 1-based line its opening fence sits on, its body lines), and the
    1-based line of a fence left open at end of file, or 0 when every fence closed. A block only
    lands when its closing fence arrives, so an unclosed fence would otherwise drop whatever it
    opened and leave the caller reading a short list as a clean file.
    """
    blocks: list[tuple[int, list[str]]] = []
    opened_at = 0
    body: list[str] = []
    in_fence = False
    for i, line in enumerate(lines, 1):
        if line.strip().startswith("```"):
            if in_fence:
                blocks.append((opened_at, body))
                body = []
            else:
                opened_at = i
            in_fence = not in_fence
            continue
        if in_fence:
            body.append(line)
    return blocks, (opened_at if in_fence else 0)


def _dispatch_templates(path: Path) -> tuple[list[tuple[int, list[str]]], int]:
    """The fenced blocks that dispatch an agent: the ones naming a subagent type, with the
    unclosed-fence line `_fenced_blocks` reports carried through."""
    lines = path.read_text(encoding="utf-8").splitlines()
    blocks, unclosed_at = _fenced_blocks(lines)
    return [
        (at, body)
        for at, body in blocks
        if any(_SUBAGENT_TYPE_LINE_RE.match(l) for l in body)
    ], unclosed_at


def _dispatch_foreground_errors(path: Path, label: str) -> list[str]:
    try:
        templates, unclosed_at = _dispatch_templates(path)
    except Exception as e:
        return [f"{label}: read error: {e}"]
    errors = [
        f"{label}:{at}: dispatch template names a subagent type and does not name "
        f"`run_in_background: false`"
        for at, body in templates
        if not any(_FOREGROUND_LINE_RE.match(l) for l in body)
    ]
    # The scan cannot speak for what an unclosed fence swallowed, so the file is refused rather
    # than read as though the dropped block were not there.
    if unclosed_at:
        errors.append(f"{label}:{unclosed_at}: fenced block opened here is never closed")
    return errors


def check_dispatch_foreground(plugin_path: Path, marketplace_root: Path) -> Result:
    name = "dispatch-foreground"
    skills_dir = plugin_path / "skills"
    agents_dir = plugin_path / "agents"

    files: list[Path] = []
    if skills_dir.is_dir():
        files.extend(sorted(skills_dir.rglob("SKILL.md")))
    if agents_dir.is_dir():
        files.extend(sorted(agents_dir.rglob("*.md")))

    errors: list[str] = []
    templates = 0
    for f in files:
        label = f"{f.parent.name}/{f.name}" if f.name == "SKILL.md" else f.name
        try:
            found, _ = _dispatch_templates(f)
            templates += len(found)
        except Exception:
            pass
        errors.extend(_dispatch_foreground_errors(f, label))

    # The same helper over fixtures, so the check is shown to refuse rather than assumed to.
    fixtures = marketplace_root / "harness" / "fixtures"
    expected = [
        ("dispatch-fixture-clean.md", None),
        ("dispatch-fixture-background.md", "does not name `run_in_background: false`"),
        ("dispatch-fixture-unclosed.md", "is never closed"),
    ]
    for fixture_name, wanted in expected:
        fixture = fixtures / fixture_name
        if not fixture.is_file():
            errors.append(f"fixture not found at {fixture}")
            continue
        got = _dispatch_foreground_errors(fixture, fixture_name)
        if wanted is None:
            if got:
                errors.append(f"{fixture_name}: clean fixture refused: {'; '.join(got)}")
        elif len(got) != 1 or wanted not in got[0]:
            errors.append(f"{fixture_name}: expected one refusal naming '{wanted}', got {got}")

    detail = (
        f"{len(files)} skill/agent files scanned, {templates} dispatch templates, "
        f"{len(expected)} fixtures"
    )
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
        check_pass_summary(plugin_path, marketplace_root),
        check_no_fork_subagent(plugin_path),
        check_agent_tool_surface(plugin_path, marketplace_root),
        check_agent_model_pinned(plugin_path, marketplace_root),
        check_dispatch_foreground(plugin_path, marketplace_root),
    ]
    all_passed = all(r.passed for r in results)
    return results, all_passed
