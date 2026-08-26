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

Grounding role: reads files and shells out to the claude CLI. No inference.
"""

from __future__ import annotations

import json
import re
import subprocess
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

    - full_scope_files: every shipped-skill .md, README.md, the manifest
      JSON files, and any trade-knowledge/ file that is NOT one of the
      pinned corpus files (e.g. MANIFEST.md itself) — this is the plugin's
      own prose, in its own voice, and gets the strictest scan.
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
    ]
    all_passed = all(r.passed for r in results)
    return results, all_passed
