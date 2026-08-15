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
  5. The estimator-voice block ("## Talk to your user like an estimator") is
     byte-identical, in every skill that carries it, against the canonical
     copy in docs/plugin-text-style.md §3 (not compared pairwise across
     skills — each skill's own unheaded intro paragraph follows the block).
  6. No banned string in shipped text: client-name denylist, `PLU-\\d+`,
     internal vault filenames, `MOSOT`, em dash, middle dot. Em dash and
     middle dot are exempt inside fenced code blocks and inline code spans
     (data, not prose); every other pattern applies to code too.
  7. MCP-URL: .mcp.json `plumlayer` server url == EXPECTED_MCP_URL exactly.
  8. No absolute paths (Windows C:\\ or Unix /Users/ /home/) in .mcp.json,
     plugin.json (Claude), plugin.json (Codex), or marketplace.json.

Grounding role: reads files and shells out to the claude CLI. No inference.
"""

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
    "drawing-index-publish",
    "drawing-set-assemble",
    "drawing-upload",
    "learn-project",
    "project-create",
    "project-record",
    "scope-run",
    "setup",
    "takeoff",
}

# Hard ceiling on a skill's frontmatter description length (chars). Above
# this is a FAIL, not a warning — docs/plugin-text-style.md §2.
DESC_MAX_CHARS = 600

# The estimator-voice block every skill (except project-record, which carries
# the extended "## Words (operator-facing language)" section instead) must
# reproduce byte-identically. docs/plugin-text-style.md §3.
ESTIMATOR_HEADING = "## Talk to your user like an estimator"

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
# Frontmatter parser (no pyyaml dependency)
# --------------------------------------------------------------------------- #

def _parse_frontmatter(path: Path) -> dict[str, str]:
    """
    Parse simple YAML-style frontmatter delimited by '---' lines.
    Returns a dict of key -> value strings (values are stripped of quotes).
    Block-scalar values (e.g. `description: >`) come back as the bare
    indicator (">") here — use `_extract_description` for the real text.
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


_ESTIMATOR_SECTION_HEADING_RE = re.compile(r'^##\s+3\.\s+The estimator-voice block\s*$')


def _extract_canonical_estimator_block(style_doc_path: Path) -> list[str] | None:
    """
    Parse the canonical estimator-voice block out of docs/plugin-text-style.md
    section 3 ("## 3. The estimator-voice block"): the content of the first
    fenced code block following that heading. Returns the block as a list of
    lines (no trailing/leading blank lines), or None if the doc, the section,
    or the fenced block cannot be found — the caller must treat None as a
    hard failure, not a quiet pass, since there is then nothing to compare
    skills against.
    """
    if not style_doc_path.exists():
        return None
    try:
        lines = style_doc_path.read_text(encoding="utf-8").splitlines()
    except Exception:
        return None

    section_start = None
    for i, line in enumerate(lines):
        if _ESTIMATOR_SECTION_HEADING_RE.match(line.strip()):
            section_start = i
            break
    if section_start is None:
        return None

    fence_start = None
    for i in range(section_start + 1, len(lines)):
        if lines[i].strip().startswith("```"):
            fence_start = i
            break
    if fence_start is None:
        return None

    fence_end = None
    for i in range(fence_start + 1, len(lines)):
        if lines[i].strip() == "```":
            fence_end = i
            break
    if fence_end is None:
        return None

    block_lines = lines[fence_start + 1:fence_end]
    # Trim only leading/trailing blank lines the fence itself may carry;
    # internal blank lines are part of the contract and must survive.
    while block_lines and block_lines[0].strip() == "":
        block_lines.pop(0)
    while block_lines and block_lines[-1].strip() == "":
        block_lines.pop()
    return block_lines if block_lines else None


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
# Check — Estimator-voice block identical across skills
# --------------------------------------------------------------------------- #

def check_estimator_block(plugin_path: Path, marketplace_root: Path) -> Result:
    """
    Every skill that carries the estimator-voice block must reproduce it byte
    for byte against the single canonical source: the fenced block in
    docs/plugin-text-style.md §3 (that file is the contract, so a skill that
    disagrees with it is wrong by definition, not the doc). This deliberately
    does NOT compare skills pairwise — an unheaded intro paragraph follows the
    block in every skill before the next '## ' heading, so a naive
    heading-to-next-heading extraction swallows that per-skill prose and
    reports false drift. Taking exactly as many lines as the canonical block
    has, starting at the heading, avoids that.
    """
    name = "estimator-block-identical"
    style_doc_path = marketplace_root / "docs" / "plugin-text-style.md"

    canonical_lines = _extract_canonical_estimator_block(style_doc_path)
    if canonical_lines is None:
        return Result(
            name, False,
            detail=(
                f"could not parse the canonical estimator-voice block from "
                f"{style_doc_path} (expected '## 3. The estimator-voice block' "
                f"followed by a fenced code block) — this check has no reference "
                f"to compare skills against and cannot run"
            ),
        )
    n = len(canonical_lines)

    skills_dir = plugin_path / "skills"
    if not skills_dir.is_dir():
        return Result(name, False, detail=f"skills/ directory not found at {skills_dir}")

    carriers: list[str] = []
    mismatches: list[str] = []

    for skill_dir in sorted(d for d in skills_dir.iterdir() if d.is_dir()):
        entry = skill_dir / "SKILL.md"
        if not entry.exists():
            continue
        lines = entry.read_text(encoding="utf-8").splitlines()

        heading_idx = None
        for i, line in enumerate(lines):
            if line.strip() == ESTIMATOR_HEADING:
                heading_idx = i
                break
        if heading_idx is None:
            continue  # doesn't carry the block (e.g. project-record) — not scored

        carriers.append(skill_dir.name)
        skill_block = lines[heading_idx:heading_idx + n]

        if len(skill_block) < n:
            mismatches.append(
                f"{skill_dir.name}: block runs off the end of the file at line "
                f"{heading_idx + len(skill_block)} ({len(skill_block)} lines found, "
                f"{n} expected starting at line {heading_idx + 1})"
            )
            continue

        if skill_block != canonical_lines:
            first_diff_line = None
            first_diff_detail = "content differs beyond a line-by-line walk"
            for offset, (ref, cur) in enumerate(zip(canonical_lines, skill_block)):
                if ref != cur:
                    first_diff_line = heading_idx + 1 + offset
                    first_diff_detail = f"expected {ref!r}, got {cur!r}"
                    break
            mismatches.append(
                f"{skill_dir.name}: differs from docs/plugin-text-style.md §3 "
                f"at line {first_diff_line} — {first_diff_detail}"
            )

    detail = f"{len(carriers)} skills carry the block: {carriers}"
    if mismatches:
        detail += " | " + "; ".join(mismatches)

    return Result(name, passed=len(mismatches) == 0, detail=detail)


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
    patterns.append(("'MOSOT' as operator-facing vocabulary", re.compile(r"\bMOSOT\b", re.IGNORECASE), False))
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


def check_banned_strings(plugin_path: Path, marketplace_root: Path) -> Result:
    name = "banned-strings"

    full_scope_files: list[Path] = []
    skills_dir = plugin_path / "skills"
    if skills_dir.is_dir():
        full_scope_files.extend(sorted(skills_dir.rglob("*.md")))

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

    hits: list[str] = []
    for f in full_scope_files:
        hits.extend(_scan_file_for_banned(f, client_names_only=False))

    client_only_files: list[Path] = []
    trade_packages_dir = plugin_path / "trade-packages"
    if trade_packages_dir.is_dir():
        client_only_files.extend(sorted(trade_packages_dir.rglob("*.md")))

    for f in client_only_files:
        hits.extend(_scan_file_for_banned(f, client_names_only=True))

    detail = (
        f"{len(full_scope_files)} files under full banned-set scan, "
        f"{len(client_only_files)} trade-package files under client-name-only scan"
    )
    if hits:
        detail += " | " + "; ".join(hits)

    return Result(name, passed=len(hits) == 0, detail=detail)


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
# Public entry point
# --------------------------------------------------------------------------- #

def run_static_checks(plugin_path: Path, marketplace_root: Path) -> tuple[list[Result], bool]:
    """Run all Layer 1 checks. Returns (results, all_passed)."""
    results = [
        check_cli_validate(plugin_path),
        check_version_quadruple(plugin_path, marketplace_root),
        check_skills(plugin_path),
        check_description_contract(plugin_path),
        check_estimator_block(plugin_path, marketplace_root),
        check_banned_strings(plugin_path, marketplace_root),
        check_mcp_url(plugin_path),
        check_no_absolute_paths(plugin_path, marketplace_root),
    ]
    all_passed = all(r.passed for r in results)
    return results, all_passed
