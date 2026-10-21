"""
static_checks.py — Layer 1: deterministic, no model calls.

Checks:
  1. `claude plugin validate <plugin_path> --strict` exits 0 (SKIP if the
     `claude` CLI is not on PATH).
  2. Version-quadruple lockstep across plugin.json (Claude), plugin.json
     (Codex), and marketplace.json (2 fields).
  3. Skills: no duplicate `name`; no missing/empty `description`; the shipped
     skill set matches EXPECTED_SKILLS exactly, in both directions.
  4. Agents: every agents/*.md has frontmatter that actually parses as YAML
     and a non-empty `name` and `description`; the shipped agent set matches
     EXPECTED_AGENTS exactly, in both directions (`scope-reader`,
     `scope-reviewer`, `scope-round-runner`, `sheet-checker`); and no agent declares a
     frontmatter field the runtime ignores for plugin-shipped agents
     (`hooks`, `mcpServers`, `permissionMode`). Checks 3 and 4 both validate
     the frontmatter block with PyYAML when it is importable, falling back to
     a stdlib check for the unquoted ": " failure when it is not.
  5. Description contract: every skill description is non-empty, folded YAML
     style (`description: >`), and at most DESC_MAX_CHARS characters.
  6. No banned string in shipped text: client-name denylist, `PLU-\\d+`,
     internal vault filenames, `MOSOT`, em dash, middle dot. Em dash and
     middle dot are exempt inside fenced code blocks and inline code spans
     (data, not prose); every other pattern applies to code too. Every
     shipped file takes the same scan: there is no lenient population and no
     exemption list.
  7. Retired vocabulary regression guard: a curated list of names retired by
     the D6 vocabulary sweep (commit 8096333 and follow-ups) must not creep
     back in. Whole-file terms (e.g. `residue`, `roster`, `operator` as the
     name for the person) are banned everywhere in the full-scope files;
     scoped terms (e.g. `supersede`, `fan-out`, `census`) are legitimate
     agent-facing machinery and are banned only inside a
     `<!-- user-facing -->` span or an `Audience: user` artifact clause.
  8. Bold-for-emphasis: a mid-sentence bold span made only of words on a
     short denylist of ordinary words (`not`, `never`, `only`, `each`, ...),
     one word or several, with or without a colon after it. A span that opens
     its line (after indentation, `>`, or a list marker) or sits in a table
     row that starts with a pipe is a label and passes. One line at a time,
     outside fenced code.
  9. Title-Case pseudo-heading lines (advisory only — reported as a WARN,
     never fails the release; see the check's own docstring for why).
  10. MCP-URL: .mcp.json `plumlayer` server url == EXPECTED_MCP_URL exactly.
  11. No absolute paths (Windows C:\\ or Unix /Users/ /home/) in .mcp.json,
      plugin.json (Claude), plugin.json (Codex), or marketplace.json.
  12. Question/failure boundary: no shipped skill or agent file tells the agent to raise a
      Question over a Plumlayer failure (a job that failed or timed out, an image-only or
      unresolved page, a retry), and every file that mentions `ask_question` / "raise a
      Question" at all carries the boundary sentence saying a Question is about the project,
      never about a Plumlayer failure.
  13. Question RFI bar: agents/scope-reader.md carries the bar in its fixed wording, "a draft
      RFI"; no shipped skill or agent file carries a retired raise-for-everything phrase ("rather
      than smoothing it", "rather than guessing") on the same line as the word Question; and none
      carries the wording of a Question rule the draft-RFI standard retired ("always raises a
      Question", "raise a Question if inferred" or "when inferred", "Question naming the grain",
      "a correction of an earlier write, that is a Question", `mepDeliveryShape`, a
      `"scope-item"` source type), matched over the whole file with whitespace collapsed.
  14. Every shipped skill or agent file that names `ask_question` or tells the agent to raise a
      Question carries the fixed phrase "Question text is plain estimator words", either stating
      the rule in full or pointing at it (docs/plugin-text-style.md §1) beside the standard the
      `ask_question` verb states.
  15. Ledger fixed shape: the runner definition's ledger grammar block still declares exactly
      three line kinds and the closed `note` kind set; every shipped file instructing an append
      to the ledger carries the prohibition sentence; and no prose-permitting cue sits near a
      ledger mention with no prohibition cue in range.
  16. Runner mode set: the `##` headings of agents/scope-round-runner.md match
      EXPECTED_RUNNER_MODE_HEADINGS exactly, in both directions, so the per-pass shape cannot be
      partly undone without failing the release. The set is pass, review and
      boundary; a `Leftover mode` coming back fails here.
  17. Plan inventory: the shipped scripts/plan_inventory.py, imported in-process and run end to
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
      2 numbering each discipline part's units from 1 and a replan keeping every unit id the run
      ledger and the previous plan file already handed out, numbering new sheets after the highest
      number the part has ever carried and never handing a cut sheet's id out again, a window 2
      slice planned with `--only` holding exactly the sheets its patterns name and deferring the
      rest, with its
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
      hold, among them. Every window 1 and 2 plan it writes is also held to the fold: a pass of at
      most twelve units holding at most one part of three or more, which names it, a part under
      three joining the pass before it whenever that pass has room and the pass after it
      otherwise, no pass under three beside one it fits into, every folded unit keeping the id its
      own discipline gave it, and the heading, the `folded in` line, the bounds line and the totals
      naming each fold, with the fixtures' groupings pinned by hand, one sheet between two passes
      of twelve read alone and named as kept, a unit verified under its part's own pass before a
      replan folds that part kept, marked verified and counted once in the folded pass's summary,
      every pass block reading `summed: yes` only while its summary on file names exactly its unit
      ids and its last `pass:` line carries that summary, a fold at the same count included,
      and harness/fixtures/set-grid-fixture-209.json, a
      209-sheet grid with a real set's discipline and sheet type counts in grid order and invented
      sheet numbers, planning its window 1 of seventeen vocabulary sheets over eight disciplines in
      three passes and its window 2 of twenty-two parts in nineteen. The shipped script is
      compiled from source here
      rather than imported through the loader, so a script edited twice inside one second to the
      same byte length can never be checked as its earlier bytecode.
  18. Pass summary: the shipped scripts/pass_summary.py, imported in-process and run over three
      invented ledger fixtures with their read plans, sums the lines of every unit the pass's plan
      block carries, whatever pass they name, into the published summary shape, and every number,
      every note line and every label is compared against a tally this file computes itself off
      the same fixture text. The labels it prints are compared in order against the skill's own
      summary block, and the runner's own summary command is fed to the script's arguments.
      Another pass's and another window's lines and the lead's own `pass:` line are shown to reach
      no total; a folded pass counts a unit verified under its part's own pass id once, with its
      trades off that pass's file, and names a unit the plan cut; and sixteen broken invocations
      each refuse in one line with nothing on stdout.
  19. No shipped skill or agent file names `fork` as a subagent type, in either the
      `subagent_type:` dispatch-line shape or a `tools: Agent(fork)` frontmatter declaration.
  20. Agent tool surface: no agents/*.md tools line takes the whole connector as a wildcard;
      every connector verb an agent's body names is on its tools line; every declared connector
      verb is one of the 122 the connector registers; and the prohibition-only exception table
      stays honest, each entry still named in that agent's text and still off its tools line.
  21. Agent model pinned: every agents/*.md frontmatter carries a non-empty `model`, so a
      dispatched agent does not run on whatever model the session happens to be on. Checks 20 and
      21 each run their own helper over the agent fixtures under harness/fixtures/, so the clean
      one is shown to pass and each broken one to refuse in one line naming what is wrong.
  22. Dispatch foreground: every fenced block in a shipped skill or agent file that carries a
      `subagent_type:` line also carries `run_in_background: false`, so the Agent call that
      dispatches an agent is the wait; a fence left open at the end of a file is refused rather
      than skipped. Runs its own helper over the dispatch fixtures under harness/fixtures/, so the
      clean one is shown to pass and each broken one to refuse in one line naming what is wrong.
  24. Drawing issue passes: the shipped scripts/plan_inventory.py plans two sets of one project,
      each from a run folder whose run.json names its delivery and unit tag, every unit id of a
      pass carrying its tag and no pass's subject prefix reaching another's, the old layout still
      planning untagged; it refuses a taken tag, a grid or inventory of another issue or of
      deliveries run.json does not name, and two passes in flight; its `issue` mode resumes the
      pass in flight first and starts only the latest set with no pass; and the skill's own
      `issue` command and run.json, and the reader's citation shapes, are checked against it.
  26. Pages one number prints twice: the shipped scripts/plan_inventory.py makes each further page
      of a number printed on more than one page, listed under a grid row's `pageOccurrences`, a
      sheet of its own right after its number's row, counted and named, bound across a replan by
      the key it opens as, and left out with the number by `--exclude`; it names and never plans
      a page of an earlier issue, refuses a missing or malformed page list, and binds the runner's
      own worked dispatch line for a further page. A window 1 file an earlier plugin wrote keeps
      its left-out number out on both pages, and a dispatched pass a further page takes past
      twelve keeps its part.
  27. Setup reads stay out of the lead: no page read verb (`render_page`, `get_page_text`,
      `search_set_text`, `reconcile_index`) and no `set_grid` other than a `limit: 0` summary call
      on a line a lead session runs, which is project-setup whole, drawing-upload outside its
      steps 9b and 10, and learn-project's `## Running one level down`, and no Read tool on a
      PDF's pages there either; drawing-upload carries its `plumlayer:sheet-checker` dispatch,
      with each recognition job paired with its `fileId` on its `Jobs:` line, learn-project its orientation dispatch and the first
      line of its summary, scope-run neither of its own, project-setup and scope-run point at
      learn-project's section, and the retired sentences forbidding any agent in the upload are
      gone. Runs its scan over the lead-reads fixtures under harness/fixtures/ and its shape arms
      over the shipped text with each guarded part broken, so every refusal is shown.

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
import shlex
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

# The agent definitions the plugin ships under agents/. Three are dispatched by
# the scope run: the lead starts one runner per pass, and that runner starts one
# reader per sheet in windows 1 and 2, or one reviewer per package in window 3.
# The fourth, the sheet checker, is dispatched by drawing-upload for every page
# read an upload makes.
EXPECTED_AGENTS = {
    "scope-reader",
    "scope-reviewer",
    "scope-round-runner",
    "sheet-checker",
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
# Check — Retired vocabulary regression guard
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
# The record no longer ranks one entry above another by who wrote it. A field
# holds one current value, the latest write by anyone, and a write onto an
# occupied field names what it replaces or is refused. So the authorship
# stamps (`agent-stated`, `machine-read`, `tool-verified`, `human-stated`),
# the trust classes, levels and tiers, an entry called human-authored,
# agent-authored or machine-authored, and the phrases that taught precedence between them
# ("working truth", "governing truth", "governs provisionally",
# "provisional working", "a candidate beneath the machine value") are
# whole-file retired: an agent that reads one reasons from a ranking the
# server does not apply.

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
        "'operator' as the retired name for the person (renamed to 'user'; "
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
    # harness transcripts, never narrated by a skill).
    (
        "token cost vocabulary (cost is measured outside the plugin)",
        re.compile(r"\btoken (cost|totals?|usage|budget)s?\b", re.IGNORECASE),
        False,
    ),
    (
        "an authorship stamp (`agent-stated`, `machine-read`, `tool-verified`, `human-stated`); "
        "who wrote an entry ranks nothing",
        re.compile(r"\b(?:agent-stated|machine-read|tool-verified|human-stated)\b", re.IGNORECASE),
        False,
    ),
    (
        "a trust class, level or tier, or an entry ranked by tier ('higher tier', "
        "'instrument tier', 'bottom-tier'); no entry outranks another",
        re.compile(
            r"\btrust[- ](?:class|level|tier)(?:es|s)?\b|\b(?:higher|instrument|bottom)[- ]tiers?\b",
            re.IGNORECASE,
        ),
        False,
    ),
    (
        "'human-authored', 'agent-authored' or 'machine-authored' as a kind of entry; "
        "who wrote an entry ranks nothing",
        re.compile(r"\b(?:human|agent|machine)-authored\b", re.IGNORECASE),
        False,
    ),
    (
        "precedence wording ('working truth', 'governing truth', 'governs provisionally', "
        "'provisional working', 'candidate beneath'); a field holds the latest write by anyone",
        re.compile(
            r"\b(?:working|governing) truth\b|\bgoverns? provisionally\b|\bprovisional working\b"
            r"|\bcandidate beneath\b",
            re.IGNORECASE,
        ),
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
# A bold span is flagged when two things hold. Every word in it is on a short
# denylist of ordinary words (`**not**`, `**only**:`, `**must never**`), where
# words split on whitespace, compare case-insensitively, and have .,;:!?
# stripped from both ends. And it sits mid-sentence: a span that is the first
# thing on its line, after optional indentation, an optional blockquote `>`
# and an optional list marker (`-`, `*`, `N.`), or that sits in a table row
# written with a leading pipe (quoted or not), is a label and passes, whatever its words (`| **Before** |`,
# `1. **One** ...`, `> **Also:**`, `- **No**: the bidder excluded it.`).
#
# Position decides, the colon does not: `It does **not**:` stresses a word in
# front of a list and fails, while `- **No**:` labels a case and passes. A
# span with any word off the list passes anywhere, because that is what the
# rest of this codebase's genuine bold looks like: a bolded lead-in on a
# numbered step, a first-use term definition ("**edge**", "**receipt**").
# A generic "any bold not followed by a colon" rule flags those conventions
# wholesale, so the check stays this narrow and favors a missed emphasis over
# a flagged label.
#
# Bounds: one line at a time, so a span that wraps a line is not seen; lines
# inside fenced code are skipped; emphasis on a word off the list, or a span
# that opens a line in the middle of a wrapped sentence, passes; a table row
# written without a leading pipe reads as prose, so its later cell labels can
# be flagged (every table this plugin ships uses leading pipes).
BOLD_EMPHASIS_WORDS = {
    "not", "never", "always", "only", "must", "no", "none", "any", "every",
    "all", "exactly", "actually", "really", "truly", "genuinely", "definitely",
    "certainly", "absolutely", "literally", "especially", "particularly",
    "explicitly", "precisely", "strictly", "solely",
    "before", "after", "each", "both", "either", "neither", "is", "are",
    "once", "twice", "nothing", "one", "and", "or", "own", "alongside",
    "also", "still", "ever", "whole",
}

_BOLD_RE = re.compile(r"\*\*([^*\n]+)\*\*")
# What may stand before a span that opens its line: indentation, blockquote
# markers, and one list marker.
_BOLD_LINE_LEAD_RE = re.compile(r"\s*(?:>\s*)*(?:(?:[-*]|\d+\.)\s+)?")


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
        if line.lstrip().lstrip("> ").startswith("|"):
            continue  # a table row's bold is a cell label
        for m in _BOLD_RE.finditer(line):
            if _BOLD_LINE_LEAD_RE.fullmatch(line[:m.start()]):
                continue  # the span opens its line: a lead-in label, not emphasis
            content = m.group(1).strip()
            words = [w.strip(".,;:!?").lower() for w in content.split()]
            if words and all(w in BOLD_EMPHASIS_WORDS for w in words):
                hits.append(
                    f"{path.name}:{i}: bold-for-emphasis on ordinary words {content!r} in: {line.strip()[:160]}"
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
# Check — Question/failure boundary
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
# The bar was then raised to a draft RFI, the standard the `ask_question` verb states, after a
# review of one project's Questions found orientation asking the design team to confirm the
# agent's own reading, a grain call nobody on the design team answers raised as a Question, and a
# scope row cited as the evidence against the drawings.
#
# Three mechanical arms, the same shape as the two checks above:
#
#   1. scope-reader.md carries the bar in its fixed wording, so the rule is provably present rather
#      than plausible-sounding nearby text.
#   2. No shipped skill or agent file carries a retired raise-for-everything phrase next to the
#      word Question. Matched on one line: the phrases are short and the collocation is what makes
#      them a directive, and "rather than guessing at one" about a category string (which the same
#      file legitimately carries) is not about Questions at all.
#   3. No shipped skill or agent file carries the wording of a Question rule the standard retired:
#      a Question raised for the agent's own inferred reading or by an entry's nature, a grain
#      call raised as a Question, the MEP delivery-shape judgment, or a scope row as a Question's
#      source. Matched over the whole file with whitespace collapsed, since these phrases wrap
#      across lines.
#
# What this cannot judge, and does not try to: whether a Question an agent actually raises clears
# the bar. That stays in review.

QUESTION_RFI_BAR_PHRASES = (
    "a draft RFI",
)

# Wording retired with the bar: it told the reader to raise a Question wherever it was unsure,
# which is the failure mode the bar exists to stop.
_QUESTION_RAISE_FOR_EVERYTHING_RE = re.compile(
    r"rather than smoothing it|rather than guessing", re.IGNORECASE
)

# Wording of the Question rules the draft-RFI standard retired.
_QUESTION_RETIRED_RULE_RE = re.compile(
    r"always raises? a Question|raises? a Question (?:if|when)\b[^.,;]{0,30}\binferred|"
    r"Question naming the grain|correction of (?:an|your own) earlier write[,;]? "
    r"(?:that|which) is a Question|mepDeliveryShape|type\"?:\s*\"scope-item\"",
    re.IGNORECASE,
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

        normalized = re.sub(r"\s+", " ", "\n".join(lines))
        for m in _QUESTION_RETIRED_RULE_RE.finditer(normalized):
            errors.append(f"{label}: retired Question rule wording '{m.group(0)}'")

    detail = f"{len(files)} skill/agent files scanned, {len(QUESTION_RFI_BAR_PHRASES)} bar phrases required"
    if errors:
        detail += " | " + "; ".join(errors)

    return Result(name, passed=len(errors) == 0, detail=detail)


# --------------------------------------------------------------------------- #
# Check — Question plain-words pointer
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
    "anomaly", "unread", "kinds", "deviation", "overlap", "grain", "door", "packet", "set",
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
# A set over more than one file names the file before the page.
_PLAN_UNIT_RE = re.compile(r"^(\S+)\. (\S+), (?:file \S+, )?page (\d+): (.*)$")
_PLAN_REVIEW_RE = re.compile(r"^(\d+)\. (rev-\S+): (.*)$")
_PLAN_FIELD_RE = re.compile(r"^([a-z][a-z ]*): (.*)$")
# A repeated lines unit reads a file from one of its pages, in its own pass, `RS1` or a part of it.
_REPEATED_PASS_RE = re.compile(r"^RS1[a-z]?$")
_PLAN_REPEATED_UNIT_RE = re.compile(
    r"^(RS1[a-z]?-[1-9][0-9]*)\. file (\S+), from page (\d+): repeated lines"
    r"(?:, sheets left out (.+?))?( verified)?$"
)
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


def _plan_passes(read_plan: str, repeated: bool = False) -> list[dict]:
    """
    The read plan's passes, read straight off the file: the pass id, the `key: value` lines of its
    block, its sheet unit lines as (unit id, sheet number, page), and its review unit lines as
    (unit id, name). Stops at the left-out section, whose entries share the sheet unit line's shape
    and carry a plain ordinal where a planned unit carries its id.

    The repeated lines passes read files rather than sheets and never fold, so they are left out of
    what this returns unless `repeated` asks for them alone, each unit then as (unit id, file id,
    page, whether it is marked verified), and each pass's `leftOut` naming per unit the sheets of
    its file the run left out.
    """
    passes: list[dict] = []
    skipping = False
    for line in read_plan.splitlines():
        if line.strip() == _LEFT_OUT_HEADING:
            break
        heading = _PLAN_PASS_RE.match(line)
        if heading:
            skipping = bool(_REPEATED_PASS_RE.match(heading.group(1))) != repeated
            if not skipping:
                passes.append(
                    {"id": heading.group(1), "heading": line[4:], "fields": {}, "units": [], "reviews": []}
                )
            continue
        if not passes or skipping:
            continue
        if repeated:
            repeated_unit = _PLAN_REPEATED_UNIT_RE.match(line)
            if repeated_unit:
                passes[-1]["units"].append(
                    (repeated_unit.group(1), repeated_unit.group(2), int(repeated_unit.group(3)),
                     repeated_unit.group(5) is not None)
                )
                # The file's sheets the run left out, which the unit's reader records nothing from.
                passes[-1].setdefault("leftOut", {})[repeated_unit.group(1)] = (
                    repeated_unit.group(4).split(", ") if repeated_unit.group(4) else []
                )
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


# A pass under this many units folds into a neighbouring pass: a runner pays a fixed cost before its
# first unit, so a runner started for one or two sheets is mostly that cost.
_SMALL_PASS_UNITS = 3


def _plan_parts(passes: list[dict]) -> list[dict]:
    """
    The discipline parts a read plan's passes carry, rebuilt off the unit ids in file order. A unit
    id's pass component names the part it was numbered in, and a fold groups whole parts into one
    runner pass without renumbering a unit, so each run of one pass component inside one pass is a
    part. Each part records the index of the pass it sits in.
    """
    parts: list[dict] = []
    for index, plan_pass in enumerate(passes):
        for unit in plan_pass["units"]:
            part_id = unit[0].rsplit("-", 1)[0]
            if not parts or parts[-1]["id"] != part_id or parts[-1]["passIndex"] != index:
                parts.append({"id": part_id, "passIndex": index, "units": []})
            parts[-1]["units"].append(unit)
    return parts


def _grouping(passes: list[dict]) -> list[list[str]]:
    """Each pass's part ids, in file order, for comparing against a grouping pinned by hand."""
    parts = _plan_parts(passes)
    return [[part["id"] for part in parts if part["passIndex"] == index] for index in range(len(passes))]


def _check_fold(
    passes: list[dict],
    bounds: str,
    read_plan: str,
    window: int,
    discipline_of: dict[str, str],
    errors: list[str],
    where: str,
) -> list[list[str]]:
    """
    What a fold may do, checked on one read plan the script wrote; the expected grouping is the
    caller's, pinned by hand, and this returns the grouping the file holds.

    A fold moves the boundary between adjacent passes and nothing else. Every part reads whole in
    one pass, under ids numbered in its own discipline; a pass holds at most twelve units and at
    most one part of three or more, which gives the pass its id; a part under three joins the pass
    before it whenever that pass has room; no pass under three stands beside a pass it would fit
    into; and the heading, the `folded in` line, the bounds line and the totals block each say what
    the file holds.
    """
    parts = _plan_parts(passes)
    seen: set[str] = set()
    for part in parts:
        if part["id"] in seen:
            errors.append(f"{where}: part {part['id']} is read in two places, so a fold split or moved it")
        seen.add(part["id"])
        # A folded unit keeps the id its own discipline numbered it under, so every part is one
        # discipline's sheets under that discipline's pass id, lettered or not.
        disciplines = {discipline_of.get(sheet, "(unknown)") for _id, sheet, _page in part["units"]}
        stems = {("NONE" if d == "(none)" else d) + str(window) for d in disciplines}
        lettered = part["id"][:-1] in stems and part["id"][-1] in string.ascii_lowercase
        if len(stems) != 1 or not (part["id"] in stems or lettered):
            errors.append(
                f"{where}: unit ids {[unit[0] for unit in part['units']]} are numbered under "
                f"{part['id']} over sheets of discipline {sorted(disciplines)}"
            )

    grouping = _grouping(passes)
    sizes: list[int] = []
    folds: list[str] = []
    kept: list[str] = []
    for index, plan_pass in enumerate(passes):
        members = [part for part in parts if part["passIndex"] == index]
        size = sum(len(part["units"]) for part in members)
        sizes.append(size)
        if size > 12:
            errors.append(f"{where}: pass {plan_pass['id']} holds {size} units, over the cap of 12")
        if plan_pass["fields"].get("units") != str(size):
            errors.append(
                f"{where}: pass {plan_pass['id']} reads `units: {plan_pass['fields'].get('units')}` "
                f"over {size} unit lines"
            )
        if not members:
            continue
        large = [part for part in members if len(part["units"]) >= _SMALL_PASS_UNITS]
        if len(large) > 1:
            errors.append(
                f"{where}: pass {plan_pass['id']} joins {[part['id'] for part in large]}, each of "
                f"{_SMALL_PASS_UNITS} units or more"
            )
        host = large[0] if large else members[0]
        if plan_pass["id"] != host["id"]:
            errors.append(
                f"{where}: the pass holding {grouping[index]} is named {plan_pass['id']}, not "
                f"{host['id']}"
            )
        folded = [part for part in members if part is not host]
        folds.extend(f"{part['id']} into {host['id']}" for part in folded)
        if size < _SMALL_PASS_UNITS:
            kept.append(plan_pass["id"])
        want_field = ", ".join(part["id"] for part in folded) or None
        if plan_pass["fields"].get("folded in") != want_field:
            errors.append(
                f"{where}: pass {plan_pass['id']} reads `folded in: "
                f"{plan_pass['fields'].get('folded in')}`, expected {want_field!r}"
            )
        folded_disciplines = [discipline_of.get(part["units"][0][1], "(unknown)") for part in folded]
        suffix = (
            f", with discipline{'s' if len(folded_disciplines) > 1 else ''} "
            f"{', '.join(folded_disciplines)}"
            if folded
            else ""
        )
        if not plan_pass["heading"].endswith(suffix) or (not folded and ", with discipline" in plan_pass["heading"]):
            errors.append(
                f"{where}: pass {plan_pass['id']} is headed {plan_pass['heading']!r}, which does not "
                f"name the disciplines folded into it ({suffix!r})"
            )

    for index in range(1, len(sizes)):
        before, after = sizes[index - 1], sizes[index]
        if (before < _SMALL_PASS_UNITS or after < _SMALL_PASS_UNITS) and before + after <= 12:
            errors.append(
                f"{where}: passes {passes[index - 1]['id']} of {before} and {passes[index]['id']} of "
                f"{after} stand apart though one is under {_SMALL_PASS_UNITS} units and both fit in 12"
            )
        first = next((part for part in parts if part["passIndex"] == index), None)
        if first is not None and len(first["units"]) < _SMALL_PASS_UNITS and before + len(first["units"]) <= 12:
            errors.append(
                f"{where}: part {first['id']} starts pass {passes[index]['id']} though the pass before "
                f"it holds {before} units and has room for it"
            )

    fold_clause = f"folds {len(folds)} ({', '.join(folds)})" if folds else "folds 0"
    kept_clause = (
        f", passes under three units kept {len(kept)} ({', '.join(kept)})" if kept else ""
    )
    fragment = f"passes {len(passes)}, {fold_clause}{kept_clause},"
    if fragment not in bounds:
        errors.append(f"{where}: the bounds line does not name `{fragment}`: {bounds!r}")
    totals = f"units planned {sum(sizes)}, passes {len(passes)}, folds {len(folds)}"
    if totals not in read_plan.splitlines():
        errors.append(f"{where}: the read plan's totals do not carry `{totals}`")
    return grouping


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
    discipline_of: dict[str, str] = {}
    for row in fixture_rows:
        discipline = row.get("discipline") or "(none)"
        sheet_type = row.get("sheetType") or "(untyped)"
        expected_by_discipline[discipline] = expected_by_discipline.get(discipline, 0) + 1
        expected_cross.setdefault(discipline, {})
        expected_cross[discipline][sheet_type] = expected_cross[discipline].get(sheet_type, 0) + 1
        page_of[row["sheetNumber"]] = row["pageInPdf"]
        discipline_of[row["sheetNumber"]] = discipline
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
    # Every fixture row lists no further page, as `set_grid` gives a number printed on one page, so
    # the inventory reads exactly the grid's rows and says so.
    inert = (
        f"0 further pages of a number printed on more than one page, 0 pages of an earlier issue "
        f"left out, {expected_rows} sheets to read"
    )
    if inert not in bounds:
        errors.append(f"the inventory bounds line does not name `{inert}`: {bounds!r}")

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
        _check_split_arithmetic(_plan_parts(w1_passes), 12, errors, "window 1")
        if len(_plan_parts(w1_passes)) != len(expected_w1_disciplines):
            errors.append(
                f"window 1 reads {len(_plan_parts(w1_passes))} discipline parts over "
                f"{len(expected_w1_disciplines)} disciplines"
            )
        # The fold, pinned by hand off the fixture. G1 is one sheet with no pass before it, so it
        # starts a pass, and a pass under three takes in the part behind it: A1's five, which give
        # the pass its id. NONE1's one sheet then joins A1 at seven.
        w1_grouping = _check_fold(
            w1_passes, w1_bounds, w1_path.read_text(encoding="utf-8"), 1, discipline_of, errors,
            "window 1",
        )
        if w1_grouping != [["G1", "A1", "NONE1"]]:
            errors.append(f"window 1 reads its parts as {w1_grouping}, expected [['G1', 'A1', 'NONE1']]")

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
        for part in _plan_parts(w2_passes):
            stem = part["id"]
            if len(stem) > 1 and stem[-1] in string.ascii_lowercase:
                stem = stem[:-1]
            if not planned or planned[-1][0] != stem:
                planned.append((stem, []))
            planned[-1][1].extend(sheet for _id, sheet, _page in part["units"])
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
        w2_split = _check_split_arithmetic(_plan_parts(w2_passes), 12, errors, "window 2")
        if w2_split == 0:
            errors.append("the window 2 fixture proves nothing about the twelve-unit split")
        # The fold, pinned by hand off the fixture. S2's two sheets fit beside A2b's nine at
        # eleven. P2's two would make that thirteen, so P2 starts a pass, and a pass under three
        # takes in E2's one sheet at three. C2's eight stand alone.
        w2_grouping = _check_fold(
            w2_passes, w2_bounds, w2_path.read_text(encoding="utf-8"), 2, discipline_of, errors,
            "window 2",
        )
        if w2_grouping != [["A2a"], ["A2b", "S2"], ["P2", "E2"], ["C2"]]:
            errors.append(
                f"window 2 reads its parts as {w2_grouping}, expected "
                f"[['A2a'], ['A2b', 'S2'], ['P2', 'E2'], ['C2']]"
            )

    # ------------------------------------------------------------------ #
    # A 209-sheet set: window 1 in three passes
    # ------------------------------------------------------------------ #
    #
    # The grid of a 209-page set as its record holds it: the discipline and sheet type of every row,
    # in grid order, with every sheet number invented. Its vocabulary is seventeen sheets over eight
    # disciplines, five of them one or two sheets, and that planned as eight runners before the
    # fold. The tally below is computed off the fixture, never off what the script wrote.
    set_209 = fixtures / "set-grid-fixture-209.json"
    set_209_dir = out_dir / "set-209"
    shutil.rmtree(set_209_dir, ignore_errors=True)
    w1_209_grouping: list[list[str]] = []
    w2_209_grouping: list[list[str]] = []
    try:
        rows_209 = json.loads(set_209.read_text(encoding="utf-8"))["sheets"]
    except Exception as e:
        errors.append(f"the 209-sheet fixture: {e}")
        rows_209 = []
    if len(rows_209) != 209:
        errors.append(f"the 209-sheet fixture holds {len(rows_209)} rows, not 209")
    discipline_209 = {row["sheetNumber"]: row.get("discipline") or "(none)" for row in rows_209}
    vocabulary_209: dict[str, int] = {}
    rest_209: dict[str, int] = {}
    for row in rows_209:
        tally = vocabulary_209 if (row.get("sheetType") or "") in _VOCABULARY_SHEET_TYPES else rest_209
        tally[row.get("discipline") or "(none)"] = tally.get(row.get("discipline") or "(none)", 0) + 1

    def expected_parts(counts: dict[str, int], window: int) -> list[tuple[str, int]]:
        parts: list[tuple[str, int]] = []
        for discipline, count in counts.items():
            stem = ("NONE" if discipline == "(none)" else discipline) + str(window)
            sizes = _expected_split(count, 12)
            parts += [
                (stem if len(sizes) == 1 else f"{stem}{string.ascii_lowercase[i]}", size)
                for i, size in enumerate(sizes)
            ]
        return parts

    w1_209_parts = expected_parts(vocabulary_209, 1)
    w2_209_parts = expected_parts(rest_209, 2)
    code, bounds_209, err = _run_script_main(
        module,
        ["inventory", "--grid", str(set_209), "--expect-count", "209", "--out-dir", str(set_209_dir)],
    )
    if code != 0:
        errors.append(f"the inventory mode refused the 209-sheet fixture: {err}")
    else:
        if "209 rows" not in bounds_209:
            errors.append(f"the 209-sheet inventory bounds line does not name 209 rows: {bounds_209!r}")
        inventory_209 = str(set_209_dir / "inventory.json")
        w1_209_path = set_209_dir / "read-plan-w1.md"
        code, w1_209_bounds, err = _run_script_main(
            module, ["plan", "--window", "1", "--inventory", inventory_209, "--out", str(w1_209_path)]
        )
        if code != 0:
            errors.append(f"the 209-sheet window 1 refused: {err}")
        else:
            w1_209_text = w1_209_path.read_text(encoding="utf-8")
            w1_209_passes = _plan_passes(w1_209_text)
            got = [(part["id"], len(part["units"])) for part in _plan_parts(w1_209_passes)]
            if got != w1_209_parts:
                errors.append(f"the 209-sheet window 1 reads the parts {got}, expected {w1_209_parts}")
            if f"units {sum(vocabulary_209.values())}," not in w1_209_bounds:
                errors.append(
                    f"the 209-sheet window 1 bounds line does not name `units "
                    f"{sum(vocabulary_209.values())}`: {w1_209_bounds!r}"
                )
            # E1's three hold the pass five parts of one or two sheets join, in grid order, ten in
            # all. A1's four and S1's three each stand alone, since two parts of three or more
            # never join.
            w1_209_grouping = _check_fold(
                w1_209_passes, w1_209_bounds, w1_209_text, 1, discipline_209, errors,
                "the 209-sheet window 1",
            )
            pinned = [["A1"], ["E1", "FA1", "FP1", "G1", "H1", "P1"], ["S1"]]
            if w1_209_grouping != pinned or len(w1_209_grouping) > 3:
                errors.append(
                    f"the 209-sheet window 1 reads in {len(w1_209_grouping)} passes, "
                    f"{w1_209_grouping}, expected three: {pinned}"
                )
        w2_209_path = set_209_dir / "read-plan-w2.md"
        code, w2_209_bounds, err = _run_script_main(
            module,
            ["plan", "--window", "2", "--inventory", inventory_209,
             "--window-1", str(set_209_dir / "plan" / "window-1.json"), "--out", str(w2_209_path)],
        )
        if code != 0:
            errors.append(f"the 209-sheet window 2 refused: {err}")
        else:
            w2_209_text = w2_209_path.read_text(encoding="utf-8")
            w2_209_passes = _plan_passes(w2_209_text)
            got = [(part["id"], len(part["units"])) for part in _plan_parts(w2_209_passes)]
            if got != w2_209_parts:
                errors.append(f"the 209-sheet window 2 reads the parts {got}, expected {w2_209_parts}")
            # I2's one sheet cannot join H2b's twelve, so it starts a pass L2a's eight join. LS2's
            # one sheet joins L2b at eight, and the one page no sheet covers joins S2c at twelve.
            w2_209_grouping = _check_fold(
                w2_209_passes, w2_209_bounds, w2_209_text, 2, discipline_209, errors,
                "the 209-sheet window 2",
            )
            folded_209 = [group for group in w2_209_grouping if len(group) > 1]
            if folded_209 != [["I2", "L2a"], ["L2b", "LS2"], ["S2c", "Pages2"]] or len(
                w2_209_grouping
            ) != len(w2_209_parts) - 3:
                errors.append(
                    f"the 209-sheet window 2 reads {len(w2_209_grouping)} passes folding "
                    f"{folded_209}, expected {len(w2_209_parts) - 3} folding I2 into L2a, LS2 into "
                    f"L2b and Pages2 into S2c"
                )

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
        if any("folded in" in p["fields"] for p in passes) or ", folds " in run_bounds:
            errors.append(f"{label}: window 3 folds a review into another pass")
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
            if plan_pass["fields"].get("summed") != "no, no summary on file":
                errors.append(
                    f"{where}: pass {plan_pass['id']} reads `summed: "
                    f"{plan_pass['fields'].get('summed')}` on a plan with no summary on file"
                )
    for where, first_plan_passes in (("window 1", w1_passes), ("window 2", w2_passes)):
        for part in _plan_parts(first_plan_passes):
            first_ids = [unit_id for unit_id, _sheet, _page in part["units"]]
            wanted_ids = [f"{part['id']}-{i}" for i in range(1, len(first_ids) + 1)]
            if first_ids != wanted_ids:
                errors.append(
                    f"{where}: part {part['id']} carries unit ids {first_ids}, expected "
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
        run_text = out.read_text(encoding="utf-8")
        run_passes = _plan_passes(run_text)
        # Whatever case a fixture exists for, the plan it writes keeps the fold's rules.
        inventory_rows = json.loads(Path(inventory_path).read_text(encoding="utf-8"))["sheets"]
        _check_fold(
            run_passes, run_bounds, run_text, window,
            {row["sheetNumber"]: row.get("discipline") or "(none)" for row in inventory_rows},
            errors, f"{folder.name} window {window}",
        )
        return run_code, run_bounds, run_err, run_passes

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
        # S2's one sheet joins A2a's six, the part the whole window letters, so the slice is one
        # pass of seven.
        if _grouping(slice_passes) != [["A2a", "S2"]]:
            errors.append(f"the window 2 slice reads its parts as {_grouping(slice_passes)}, expected [['A2a', 'S2']]")
        remaining_count = len(sliced_keys) + len(deferred_rows)
        for fragment in (
            f"window 2, sheets {len(sliced_keys)}, passes 1, folds 1 (S2 into A2a), disciplines 2",
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
        if set(slice_file) != {"window", "units", "only", "deferredKeys", "deferredCount", "readEarlierKeys"}:
            errors.append(f"the slice's window-2.json carries the keys {sorted(slice_file)}")
        if slice_file.get("readEarlierKeys") != [] or "read earlier" in slice_bounds or "ids held" in slice_bounds:
            errors.append("the first slice reports sheets read earlier or ids held")
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
        if "read earlier" in whole_bounds or "ids held" in whole_bounds:
            errors.append("the whole window's bounds line names sheets read earlier or ids held")
        _check_split_arithmetic(_plan_parts(whole_passes), 12, errors, "the whole window after the slice")
        whole_file = json.loads((slice_dir / "plan" / "window-2.json").read_text(encoding="utf-8"))
        if (whole_file.get("only"), whole_file.get("deferredKeys"), whole_file.get("deferredCount")) != ([], [], 0):
            errors.append("the whole window's window-2.json still carries a slice or a deferral")
        if whole_file.get("readEarlierKeys") != []:
            errors.append("the whole window's window-2.json still carries sheets read earlier")
        if _SLICE_HEADING in whole_text:
            errors.append("the whole window's read plan still carries the slice's section")

    def check_read_earlier(
        label: str, folder: Path, bounds: str, planned_rows: list[dict], earlier_rows: list[dict],
        remaining_rows: list[dict], held_count: int,
    ) -> None:
        earlier_keys = {r["unitKey"] for r in earlier_rows}
        planned_keys = {r["unitKey"] for r in planned_rows}
        waiting = [r for r in remaining_rows if r["unitKey"] not in earlier_keys | planned_keys]
        partition = (
            f"every sheet once (units {len(planned_rows)} plus read earlier {len(earlier_rows)} "
            f"plus deferred {len(waiting)} equals distinct sheets {len(remaining_rows)})"
        )
        expect_bounds(label, bounds, partition)
        expect_bounds(label, bounds, f"sheets deferred {len(waiting)} by --only")
        expect_bounds(label, bounds, f"ids held {held_count}")
        saved = json.loads((folder / "plan" / "window-2.json").read_text(encoding="utf-8"))
        if saved.get("readEarlierKeys") != [r["unitKey"] for r in earlier_rows]:
            errors.append(f"{label}: readEarlierKeys does not list the verified held sheets in inventory order")
        if (saved.get("deferredKeys"), saved.get("deferredCount")) != (
            [r["unitKey"] for r in waiting], len(waiting)
        ):
            errors.append(f"{label}: deferredKeys or deferredCount does not match the sheets still waiting")
        text = (folder / "read-plan.md").read_text(encoding="utf-8")
        earlier_block = ["### Read earlier", "", f"sheets: {len(earlier_rows)}", ""] + [
            f"{i}. {r['sheetNumber']}, page {r['pageInPdf']}: {r['pageTitle']}"
            for i, r in enumerate(earlier_rows, 1)
        ] + ["", "### Deferred"]
        if "\n".join(earlier_block) not in text:
            errors.append(f"{label}: the read plan does not list exactly the sheets read earlier beside Deferred")
        deferred_block = text.split("### Deferred\n", 1)[-1].split("\n## ", 1)[0]
        expected_table = [
            f"{discipline} | {sum(r['discipline'] == discipline for r in waiting)}"
            for discipline in dict.fromkeys(r["discipline"] for r in waiting)
        ]
        actual_table = [line for line in deferred_block.splitlines() if " | " in line]
        if f"sheets: {len(waiting)}" not in deferred_block.splitlines() or actual_table != [
            "discipline | sheets", *expected_table
        ]:
            errors.append(f"{label}: the Deferred block does not count the sheets still waiting")
        for line in (partition, f"sheets deferred {len(waiting)} by --only"):
            if line not in text.splitlines():
                errors.append(f"{label}: the read plan totals do not carry `{line}`")

    # A second slice holds the first one's dispatched ids and counts three verified sheets as
    # read earlier. The mismatch stays deferred, and the selected sheet keeps its full-plan id.
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
        finished_sheets = {sheet for unit_id, sheet in ledger_units if unit_id in finished}
        check_read_earlier(
            "a second slice after dispatched units", slice_dir, again_bounds,
            [r for r in slice_s if r["sheetNumber"] == "S-2.02"],
            [r for r in slice_a if r["sheetNumber"] in finished_sheets],
            slice_a + slice_s + slice_m, len(ledger_units),
        )

    # Slice after slice, with no whole-window plan between: six verified units hold numbers 1..6,
    # the next three take 7..9, and the whole window then binds and marks all nine verified.
    consecutive_dir = replan_root / "slice-after-slice"
    remaining_rows = slice_a + slice_s + slice_m
    consecutive_inventory = write_replan_inventory(consecutive_dir, vocabulary_rows + remaining_rows)
    consecutive_window_1 = ["--window-1", str(consecutive_dir / "plan" / "window-1.json")]
    code, _bounds, err, _passes = run_replan(consecutive_dir, 1, consecutive_inventory, [])
    if code != 0:
        errors.append(f"the slice-after-slice fixture's window 1 refused: {err}")
    first_six = expected_slice[:6]
    next_rows = [r for r in slice_a if fnmatch.fnmatchcase(r["sheetNumber"], "A-3.0[7-9]")]
    next_three = [(f"A2a-{i}", r["sheetNumber"]) for i, r in enumerate(in_type_order(next_rows), 7)]
    code, _bounds, err, first_passes = run_replan(
        consecutive_dir, 2, consecutive_inventory,
        consecutive_window_1 + ["--only", f"A-3.0[1-6]:{first_reason}"],
    )
    if code != 0 or planned_ids(first_passes) != first_six:
        errors.append(f"the slice-after-slice first cut refused or numbered incorrectly: {err}")

    def verified_dispatches(units: list[tuple[str, str]]) -> list[str]:
        return [
            f"dispatch 2 A2a {unit_id} sheets {sheet} purpose the sheet"
            for unit_id, sheet in units
        ] + [
            f"verified 2 A2a {unit_id} created 4 items 4 updated 0 questions 0 replied 0 sent 4 "
            f"landed 4 conflicts 0 result ok"
            for unit_id, _sheet in units
        ]

    first_ledger = verified_dispatches(first_six)
    write_ledger(consecutive_dir, first_ledger)
    code, consecutive_bounds, err, next_passes = run_replan(
        consecutive_dir, 2, consecutive_inventory,
        consecutive_window_1 + ["--only", "A-3.0[7-9]:the user asked for three more sheets"],
    )
    if code != 0:
        errors.append(f"slice after slice with no whole-window plan between refused: {err}")
    else:
        if planned_ids(next_passes) != next_three:
            errors.append(f"slice after slice planned {planned_ids(next_passes)}, expected {next_three}")
        expect_bounds("slice after slice with no whole-window plan between", consecutive_bounds,
                      "ids kept 0 (ledger 0, plan file 0), ids new 3, ids retired 0, ids held 6")
        check_read_earlier(
            "slice after slice with no whole-window plan between", consecutive_dir, consecutive_bounds,
            next_rows, sliced_a, remaining_rows, 6,
        )

    write_ledger(consecutive_dir, first_ledger + verified_dispatches(next_three))
    code, consecutive_whole_bounds, err, consecutive_whole = run_replan(
        consecutive_dir, 2, consecutive_inventory, consecutive_window_1,
    )
    if code != 0:
        errors.append(f"the whole window after consecutive slices refused: {err}")
    else:
        all_nine = first_six + next_three
        if planned_ids(consecutive_whole)[:9] != all_nine:
            errors.append("the whole window after consecutive slices did not bind all nine to their sheets")
        whole_text = (consecutive_dir / "read-plan.md").read_text(encoding="utf-8")
        if marked_units(whole_text) != {unit_id for unit_id, _sheet in all_nine}:
            errors.append("the whole window after consecutive slices did not mark exactly all nine verified")
        for plan_pass in consecutive_whole:
            want = "9" if plan_pass["id"] == "A2a" else "0"
            if plan_pass["fields"].get("units verified") != want:
                errors.append(f"the whole window after consecutive slices miscounts verified units in {plan_pass['id']}")
        expect_bounds("the whole window after consecutive slices", consecutive_whole_bounds,
                      f"ids kept 9 (ledger 9, plan file 0), ids new {len(remaining_rows) - 9}, ids retired 0")
        expect_bounds("the whole window after consecutive slices", consecutive_whole_bounds,
                      f"every sheet once (units {len(remaining_rows)} equals distinct sheets {len(remaining_rows)})")
        saved = json.loads((consecutive_dir / "plan" / "window-2.json").read_text(encoding="utf-8"))
        if (saved.get("readEarlierKeys"), saved.get("deferredKeys"), saved.get("deferredCount")) != ([], [], 0):
            errors.append("the whole window after consecutive slices still counts sheets outside its units")

    # --- the twelve-unit cap outranks the fold ------------------------ #
    #
    # One sheet between two passes of twelve has no pass it fits into, so it reads alone, and the
    # bounds line names it as kept rather than leaving a small pass unexplained.
    full_dir = replan_root / "both-full"
    full_inventory = write_replan_inventory(
        full_dir,
        [slice_row("A", f"A-1.{i:02d}", "schedule", i) for i in range(1, 13)]
        + [slice_row("B", "B-1.01", "legend", 13)]
        + [slice_row("C", f"C-1.{i:02d}", "schedule", 13 + i) for i in range(1, 13)],
    )
    code, full_bounds, err, full_passes = run_replan(full_dir, 1, full_inventory, [])
    if code != 0:
        errors.append(f"the both-full fixture's window 1 run refused: {err}")
    elif _grouping(full_passes) != [["A1"], ["B1"], ["C1"]] or (
        "passes 3, folds 0, passes under three units kept 1 (B1)," not in full_bounds
    ):
        errors.append(
            f"one sheet between two passes of twelve reads as {_grouping(full_passes)}, expected "
            f"[['A1'], ['B1'], ['C1']] with B1 named as kept: {full_bounds!r}"
        )

    # --- a unit verified before a replan folds its pass ---------------- #
    #
    # Two sheets of G beside eleven of A make thirteen, so the first plan keeps G1 alone. G1-1 and
    # A1-1 are dispatched and verified in that shape, then the user cuts one schedule and the replan
    # folds G1 into A1. The folded pass keeps both ids and marks both verified, its runner skips
    # them and reads the rest under A1, and its summary counts every unit it carries once, G1-1 off
    # the line that names G1.
    refold_dir = replan_root / "verified-then-folded"
    refold_inventory = write_replan_inventory(
        refold_dir,
        [slice_row("G", f"G-0.0{i}", "notes", i) for i in (1, 2)]
        + [slice_row("A", f"A-0.{i:02d}", "schedule", 2 + i) for i in range(1, 12)],
    )
    refold_label = "a unit verified before a replan folds its pass"
    code, _bounds, err, refold_first = run_replan(refold_dir, 1, refold_inventory, [])
    if code != 0 or _grouping(refold_first) != [["G1"], ["A1"]]:
        errors.append(
            f"{refold_label}: the first plan reads as {_grouping(refold_first)}, expected "
            f"[['G1'], ['A1']]: {err}"
        )
    else:
        first_ids = {sheet: unit_id for unit_id, sheet in planned_ids(refold_first)}
        early = {
            first_ids["G-0.01"]: ("G1", "G-0.01", 12),
            first_ids["A-0.01"]: ("A1", "A-0.01", 20),
        }
        refold_ledger: list[str] = []
        for unit_id, (pass_id, sheet, created) in early.items():
            refold_ledger += [
                f"dispatch 1 {pass_id} {unit_id} sheets {sheet} purpose the sheet",
                f"verified 1 {pass_id} {unit_id} created {created} items 4 updated 1 questions 0 "
                f"replied 0 sent {created} landed {created} conflicts 0 result ok",
            ]
        write_ledger(refold_dir, refold_ledger)
        code, refold_bounds, err, refold_passes = run_replan(
            refold_dir, 1, refold_inventory, ["--exclude", "A-0.11:the user cut one schedule"],
        )
        kept = len(first_ids) - 1
        if code != 0 or _grouping(refold_passes) != [["G1", "A1"]]:
            errors.append(
                f"{refold_label}: the replan after one cut reads as {_grouping(refold_passes)}, "
                f"expected [['G1', 'A1']]: {err}"
            )
        else:
            expect_bounds(
                refold_label, refold_bounds,
                f"ids kept {kept} (ledger {len(early)}, plan file {kept - len(early)}), ids new 0, "
                f"ids retired 1",
            )
            folded_pass = refold_passes[0]
            if [(u, s) for u, s in planned_ids(refold_passes) if u in early] != [
                (u, s) for u, (_p, s, _c) in early.items()
            ]:
                errors.append(f"{refold_label}: the folded pass does not keep the ids verified before the fold")
            if (
                folded_pass["id"], folded_pass["fields"].get("units"),
                folded_pass["fields"].get("units verified"),
            ) != ("A1", str(kept), str(len(early))):
                errors.append(
                    f"{refold_label}: the folded pass reads {folded_pass['id']} with units "
                    f"{folded_pass['fields'].get('units')} and units verified "
                    f"{folded_pass['fields'].get('units verified')}, expected A1, {kept} and "
                    f"{len(early)}"
                )
            refold_marked = marked_units((refold_dir / "read-plan.md").read_text(encoding="utf-8"))
            if refold_marked != set(early):
                errors.append(
                    f"{refold_label}: the folded plan marks {sorted(refold_marked)} verified, "
                    f"expected {sorted(early)}"
                )

            # The folded pass's runner skips the two verified units and reads the rest under A1,
            # each unit's trades going to the file of the pass that verified it.
            trades_dir = refold_dir / "trades"
            trades_dir.mkdir(parents=True, exist_ok=True)
            trade_lines: dict[str, list[str]] = {"G1": [], "A1": []}
            for unit_id, (pass_id, _sheet, _created) in early.items():
                trade_lines[pass_id] += [f"{unit_id} trade 01 10 00 2", f"{unit_id} candidates 1"]
            for unit_id, sheet, _page in folded_pass["units"]:
                if unit_id in early:
                    continue
                refold_ledger += [
                    f"dispatch 1 A1 {unit_id} sheets {sheet} purpose the sheet",
                    f"verified 1 A1 {unit_id} created 4 items 4 updated 0 questions 0 replied 0 "
                    f"sent 4 landed 4 conflicts 0 result ok",
                ]
                trade_lines["A1"] += [f"{unit_id} trade 09 21 16 1", f"{unit_id} candidates 0"]
            write_ledger(refold_dir, refold_ledger)
            for pass_id, lines_for_pass in trade_lines.items():
                (trades_dir / f"{pass_id}.txt").write_text(
                    "\n".join(lines_for_pass) + "\n", encoding="utf-8"
                )

            summary_module = _load_script_module(
                plugin_path.joinpath(*PASS_SUMMARY_SCRIPT), "pass_summary"
            )

            def summarize_pass(pass_id: str) -> tuple[int, str, str]:
                try:
                    return _run_script_main(summary_module, [
                        str(refold_dir / "ledger.md"), "1", pass_id,
                        "--plan", str(refold_dir / "read-plan.md"),
                        "--trades", str(trades_dir / f"{pass_id}.txt"),
                    ])
                except SystemExit as e:
                    return (e.code if isinstance(e.code, int) else 2), "", ""

            code, summary_out, summary_err = summarize_pass("A1")
            summary_lines = summary_out.splitlines()
            verified_lines = [line.split() for line in refold_ledger if line.startswith("verified ")]
            read_order: list[str] = []
            for line in refold_ledger:
                if line.startswith("dispatch ") and line.split()[3] not in read_order:
                    read_order.append(line.split()[3])
            created = sum(int(parts[parts.index("created") + 1]) for parts in verified_lines)
            by_trade: dict[str, int] = {}
            candidates = 0
            for lines_for_pass in trade_lines.values():
                for line in lines_for_pass:
                    fields = line.split()
                    if fields[1] == "candidates":
                        candidates += int(fields[2])
                    else:
                        trade = " ".join(fields[2:-1])
                        by_trade[trade] = by_trade.get(trade, 0) + int(fields[-1])
            wanted_trades = "trades: " + ", ".join(
                f"{c} x{n}" for c, n in sorted(by_trade.items(), key=lambda pair: (-pair[1], pair[0]))
            ) + f"; candidates {candidates}"
            g_unit = next(u for u, (p, _s, _c) in early.items() if p == "G1")
            wanted_g = (
                f"per unit: {g_unit} created 12 items 4 updated 1 questions 0 replied 0 verified yes"
            )
            if code != 0:
                errors.append(f"{refold_label}: the folded pass's summary refused: exit {code}, {summary_err}")
            elif (
                f"units read: {', '.join(read_order)}" not in summary_lines
                or summary_lines.count(wanted_g) != 1
                or f"totals verified: created {created} (entry count" not in summary_out
                or wanted_trades not in summary_lines
            ):
                errors.append(
                    f"{refold_label}: the folded pass's summary does not count every unit it "
                    f"carries once, {g_unit} under G1 included: expected units read "
                    f"{read_order}, {wanted_g!r}, created {created} and {wanted_trades!r}, got "
                    f"{summary_lines[1:4]} and "
                    f"{[line for line in summary_lines if line.startswith('trades:')]}"
                )
            code, _out, gone_err = summarize_pass("G1")
            if code != 1 or "carries no pass G1" not in gone_err:
                errors.append(
                    f"{refold_label}: a summary of G1, which the replan folded away, did not refuse "
                    f"naming it: exit {code}, {gone_err!r}"
                )

    # --- a summed pass whose units a fold changed, at the same count ---- #
    #
    # G1 of two and A1 of twelve are each read, summed and given the lead's `pass:` line. Cutting
    # two A sheets folds G1 into A1: twelve units again, every one verified, and A1's last `pass:`
    # line counts twelve, so only the units its summary names show that A1 needs a new summary. Its
    # runner then rewrites the summary, and until the lead's line for it lands the plan still reads
    # A1 as not summed; the new line closes it. Each summary here is the shipped pass summary
    # script's own output, written where the runner writes it.
    summed_dir = replan_root / "summed-then-folded"
    summed_inventory = write_replan_inventory(
        summed_dir,
        [slice_row("G", f"G-0.0{i}", "notes", i) for i in (1, 2)]
        + [slice_row("A", f"A-0.{i:02d}", "schedule", 2 + i) for i in range(1, 13)],
    )
    summed_label = "a summed pass whose units a fold changed"
    summed_summary = _load_script_module(plugin_path.joinpath(*PASS_SUMMARY_SCRIPT), "pass_summary")

    def summed_of(plan_passes: list[dict]) -> dict[str, str]:
        return {plan_pass["id"]: plan_pass["fields"].get("summed", "") for plan_pass in plan_passes}

    def sum_passes(folder: Path, window: int, pass_ids: list[str], suffix: str) -> list[str]:
        """Each pass's summary written as its runner writes it, and the lead's line copied off it."""
        reports = folder / "reports"
        reports.mkdir(parents=True, exist_ok=True)
        lead_lines: list[str] = []
        for pass_id in pass_ids:
            try:
                run_code, summary, run_err = _run_script_main(summed_summary, [
                    str(folder / "ledger.md"), str(window), pass_id,
                    "--plan", str(folder / "read-plan.md"),
                ])
            except SystemExit as e:
                run_code, summary, run_err = e.code, "", ""
            totals = re.search(
                r"created (\d+) .*updated (\d+), questions (\d+) replied (\d+)", summary
            )
            if run_code != 0 or totals is None:
                errors.append(f"{summed_label}: the summary of {pass_id} refused: {run_err}")
                continue
            (reports / f"{pass_id}{suffix}.md").write_text(summary + "\n", encoding="utf-8")
            units = sum(1 for line in summary.splitlines() if line.startswith("per unit: "))
            lead_lines.append(
                f"pass: {window} {pass_id} units {units} created {totals.group(1)} updated "
                f"{totals.group(2)} questions {totals.group(3)} replied {totals.group(4)} "
                f"candidates 0 lead-verified yes"
            )
        return lead_lines

    code, _bounds, err, summed_first = run_replan(summed_dir, 1, summed_inventory, [])
    if code != 0 or _grouping(summed_first) != [["G1"], ["A1"]]:
        errors.append(
            f"{summed_label}: the first plan reads as {_grouping(summed_first)}, expected "
            f"[['G1'], ['A1']]: {err}"
        )
    else:
        summed_ledger: list[str] = []
        for plan_pass in summed_first:
            # G's units raise a Question each, so a summary over other units carries other figures.
            questions = 1 if plan_pass["id"] == "G1" else 0
            for unit_id, sheet, _page in plan_pass["units"]:
                summed_ledger += [
                    f"dispatch 1 {plan_pass['id']} {unit_id} sheets {sheet} purpose the sheet",
                    f"verified 1 {plan_pass['id']} {unit_id} created 5 items 5 updated 0 "
                    f"questions {questions} replied 0 sent 5 landed 5 conflicts 0 result ok",
                ]
        write_ledger(summed_dir, summed_ledger)
        summed_ledger += sum_passes(summed_dir, 1, ["G1", "A1"], "")
        write_ledger(summed_dir, summed_ledger)
        code, _bounds, err, summed_again = run_replan(summed_dir, 1, summed_inventory, [])
        if code != 0 or summed_of(summed_again) != {"G1": "yes", "A1": "yes"}:
            errors.append(
                f"{summed_label}: two passes read, summed and given their lines read "
                f"{summed_of(summed_again)}, expected yes for both: {err}"
            )

        first_ids = {sheet: unit_id for unit_id, sheet in planned_ids(summed_first)}
        cut_ids = [first_ids["A-0.11"], first_ids["A-0.12"]]
        g_ids = [first_ids["G-0.01"], first_ids["G-0.02"]]
        cut_args = ["--exclude", "A-0.1[12]:the user cut two schedules"]
        code, _bounds, err, summed_folded = run_replan(summed_dir, 1, summed_inventory, cut_args)
        if code != 0 or _grouping(summed_folded) != [["G1", "A1"]]:
            errors.append(
                f"{summed_label}: the replan after two cuts reads as {_grouping(summed_folded)}, "
                f"expected [['G1', 'A1']]: {err}"
            )
        else:
            folded_fields = summed_folded[0]["fields"]
            a1_line = [line for line in summed_ledger if line.startswith("pass: 1 A1 ")][-1].split()
            # Every count agreeing with the summary before the fold is what the case exists for.
            if not (
                folded_fields.get("units") == folded_fields.get("units verified") == a1_line[4]
            ):
                errors.append(
                    f"{summed_label}: the fold leaves A1 at units {folded_fields.get('units')}, "
                    f"verified {folded_fields.get('units verified')} and a last pass line of "
                    f"{a1_line[4]}, so the counts alone already tell it apart"
                )
            wanted = (
                f"no, the summary on file reads other units: without {', '.join(g_ids)}; "
                f"beyond {', '.join(cut_ids)}"
            )
            if summed_of(summed_folded).get("A1") != wanted:
                errors.append(
                    f"{summed_label}: A1 after the fold reads `summed: "
                    f"{summed_of(summed_folded).get('A1')}`, expected `summed: {wanted}`"
                )

            resum_lines = sum_passes(summed_dir, 1, ["A1"], "")
            code, _bounds, err, summed_resummed = run_replan(
                summed_dir, 1, summed_inventory, cut_args
            )
            stale = "no, the last pass line does not carry the summary on file"
            if summed_of(summed_resummed).get("A1") != stale:
                errors.append(
                    f"{summed_label}: a summary rewritten before the lead's line for it reads "
                    f"`summed: {summed_of(summed_resummed).get('A1')}`, expected `summed: {stale}`"
                )
            summed_ledger += resum_lines
            write_ledger(summed_dir, summed_ledger)
            code, _bounds, err, summed_closed = run_replan(
                summed_dir, 1, summed_inventory, cut_args
            )
            if summed_of(summed_closed).get("A1") != "yes":
                errors.append(
                    f"{summed_label}: the lead's line after the new summary leaves A1 reading "
                    f"`summed: {summed_of(summed_closed).get('A1')}`, expected yes"
                )

    # A window 3 summary sits under the `-pass` name, since the review's own report holds the bare
    # pass id.
    review_dir = replan_root / "summed-window-3"
    review_dir.mkdir(parents=True, exist_ok=True)
    review_args = [
        "plan", "--window", "3", "--packages", str(ordinary_packages),
        "--out", str(review_dir / "read-plan.md"),
    ]
    code, _bounds, err = _run_script_main(module, review_args)
    review_ids = (
        [p["id"] for p in _plan_passes((review_dir / "read-plan.md").read_text(encoding="utf-8"))]
        if code == 0 else []
    )
    if not review_ids:
        errors.append(f"{summed_label}: the window 3 plan refused: {err}")
    else:
        review = review_ids[0]
        review_ledger = [
            f"dispatch 3 {review} {review} sheets none purpose review the package",
            f"verified 3 {review} {review} created 4 items 4 updated 0 questions 0 replied 0 "
            f"sent 4 landed 4 conflicts 0 result ok",
        ]
        write_ledger(review_dir, review_ledger)
        (review_dir / "reports").mkdir(parents=True, exist_ok=True)
        (review_dir / "reports" / f"{review}.md").write_text("the review's own report\n", encoding="utf-8")
        write_ledger(review_dir, review_ledger + sum_passes(review_dir, 3, [review], "-pass"))
        code, _bounds, err = _run_script_main(module, review_args)
        review_summed = summed_of(
            _plan_passes((review_dir / "read-plan.md").read_text(encoding="utf-8"))
        )
        wanted_review = {
            review_id: "yes" if review_id == review else "no, no summary on file"
            for review_id in review_ids
        }
        if code != 0 or review_summed != wanted_review:
            errors.append(
                f"{summed_label}: window 3 reads {review_summed}, expected {wanted_review}: {err}"
            )

    # The lead decides a pass is finished off this line, so the skill has to name it.
    skill_path = plugin_path / "skills" / "scope-run" / "SKILL.md"
    if "`summed: yes`" not in (skill_path.read_text(encoding="utf-8") if skill_path.is_file() else ""):
        errors.append(f"{skill_path.name} does not name the `summed: yes` line the plan writes")

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
    # Dispatched under the second lettered part, the unit sorts to the front of the pass and lands in
    # A1a. A unit dispatched under the pass's own unlettered id keeps that part when the pass grows
    # past twelve, which check 26 holds, so this case dispatches under a lettered one.
    moved_out, moved_inventory = broken_replan(
        "moved-pass", [f"dispatch 1 A1b A1b-1 sheets A-1.01 {read_line}"], wide_rows)

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
                     "pageTitle": "One of the two", "fileId": "", "pageInPdf": 2,
                     "pageOccurrences": []},
                    {"discipline": "A", "sheetNumber": "A", "sheetType": "plan",
                     "pageTitle": "The other", "fileId": "1@", "pageInPdf": 2,
                     "pageOccurrences": []},
                ],
            }
        )
        + "\n",
        encoding="utf-8",
    )

    # ------------------------------------------------------------------ #
    # The repeated lines: one unit per file in window 1, the mark in window 2
    # ------------------------------------------------------------------ #
    #
    # `get_page_text` leaves a file's repeated lines out of a page only where five or more of its
    # pages print them, and a reader may ask it to only where those lines were read once already.
    # The ways the plan can get that wrong, each a case below:
    #
    #   1  no unit for a file holding exactly five of the rows the run reads, or one for four;
    #   2  rows `--exclude` left out counted toward the five, so a run scopes notes off a file the
    #      lead left out, or a unit not naming its file's left-out sheets, which its reader needs
    #      because `repeated: "only"` reads the whole file;
    #   3  the unit line, `repeatedSets`, or the page (the file's first row in inventory order)
    #      disagreeing with each other;
    #   4  a repeated lines unit folded into a discipline's pass, or counted among the sheets, in
    #      `selected`, in `units`, or on the sheet ids clause;
    #   5  a replan renumbering a dispatched or planned repeated lines unit, or reusing a retired
    #      id, or the `sheets none` dispatch lines tripping the sheet binding's refusals;
    #   6  a dispatch line naming no file, one id on two files, or one file under two ids, taken
    #      in; a discipline whose window 1 pass id is RS1 taken in;
    #   7  window 2 marking a unit with no ok `verified` line for its file's unit, after a
    #      mismatch, after an ok followed by a mismatch, beside an `unread` note, with no `set`
    #      note naming the version read, or on another file's sheets; or a mark carrying another
    #      version than the unit's last `set` note, which is what the reader compares its page to;
    #   8  window 2 taking a `repeatedSets` naming a file the inventory does not hold, or one
    #      malformed;
    #   9  the mark moving a unit id or changing the partition;
    #  10  the pass summary script unable to read a repeated lines pass's block, or the plan never
    #      reading that pass as summed.
    #
    # The expectations are built here off the fixture rows. The fixture spans four files, so its
    # unit lines name their file, which is the shape a real multi-file set plans in.
    repeated_root = replan_root / "repeated-lines"
    repeated_label = "the repeated lines"
    repeated_refusals: list[tuple[str, list[str], str]] = []

    def file_row(file_id: str, discipline: str, number: str, sheet_type: str, page: int) -> dict:
        return {
            "unitKey": f"{number}@{file_id}#{page}",
            "discipline": discipline,
            "sheetNumber": number,
            "pageTitle": f"{sheet_type} on {number}",
            "sheetType": sheet_type,
            "fileId": file_id,
            "pageInPdf": page,
        }

    # file-a holds six rows; file-b five, its first row in inventory order on page 4 though page 1
    # is lower; file-c four; file-d six, two of which the exclusion below leaves out.
    repeated_rows = (
        [file_row("file-a", "A", "A-0.01", "schedule", 1), file_row("file-a", "A", "A-0.02", "schedule", 2)]
        + [file_row("file-a", "A", f"A-2.0{i}", "plan", 2 + i) for i in range(1, 5)]
        + [file_row("file-b", "S", "S-0.01", "notes", 4)]
        + [file_row("file-b", "S", f"S-2.0{i}", "plan", page) for i, page in ((1, 1), (2, 2), (3, 3), (4, 5))]
        + [file_row("file-c", "M", "M-0.01", "legend", 1)]
        + [file_row("file-c", "M", f"M-2.0{i}", "plan", 1 + i) for i in range(1, 4)]
        + [file_row("file-d", "E", "E-0.01", "schedule", 1)]
        + [file_row("file-d", "E", f"E-2.0{i}", "plan", 1 + i) for i in range(1, 6)]
    )
    file_of_sheet = {row["sheetNumber"]: row["fileId"] for row in repeated_rows}
    leave_out_two = [
        arg for sheet in ("E-2.01", "E-2.02")
        for arg in ("--exclude", f"{sheet}:the user left these two sheets out")
    ]

    def repeated_units(folder: Path) -> list[tuple[str, str, int, bool]]:
        text = (folder / "read-plan.md").read_text(encoding="utf-8")
        return [unit for p in _plan_passes(text, repeated=True) for unit in p["units"]]

    def repeated_sets_on_file(folder: Path) -> list:
        try:
            return json.loads((folder / "plan" / "window-1.json").read_text(encoding="utf-8")).get("repeatedSets")
        except Exception as e:
            return [f"unreadable: {e}"]

    # --- 1 to 4: the first plan --------------------------------------- #
    rs_first = repeated_root / "first"
    rs_inventory = write_replan_inventory(rs_first, repeated_rows)
    code, rs_bounds, err, rs_sheet_passes = run_replan(rs_first, 1, rs_inventory, leave_out_two)
    if code != 0:
        errors.append(f"{repeated_label}: the first window 1 plan refused: {err}")
    else:
        expected_units = [("RS1-1", "file-a", 1, False), ("RS1-2", "file-b", 4, False)]
        if repeated_units(rs_first) != expected_units:
            errors.append(
                f"{repeated_label}: window 1 plans {repeated_units(rs_first)}, expected "
                f"{expected_units}: a unit for each file holding five or more rows the run reads, "
                f"at its first row's page"
            )
        if repeated_sets_on_file(rs_first) != [
            {"fileId": "file-a", "unitId": "RS1-1", "page": 1, "sheetsLeftOut": []},
            {"fileId": "file-b", "unitId": "RS1-2", "page": 4, "sheetsLeftOut": []},
        ]:
            errors.append(
                f"{repeated_label}: window-1.json's repeatedSets are {repeated_sets_on_file(rs_first)}, "
                f"not the units the plan lists"
            )
        rs_text = (rs_first / "read-plan.md").read_text(encoding="utf-8")
        rs_passes = _plan_passes(rs_text, repeated=True)
        if [(p["id"], p["fields"].get("reads for"), p["fields"].get("folded in"), p["fields"].get("units"))
                for p in rs_passes] != [("RS1", "the repeated lines", None, "2")]:
            errors.append(
                f"{repeated_label}: the repeated lines pass reads {[(p['id'], p['fields']) for p in rs_passes]}, "
                f"expected one pass RS1 of two units reading for the repeated lines, folding nothing in"
            )
        # The sheet passes fold among themselves: four parts of one or two sheets join into one
        # pass of five, and the repeated lines pass of two stands apart though it would fit.
        if _grouping(rs_sheet_passes) != [["A1", "S1", "M1", "E1"]]:
            errors.append(
                f"{repeated_label}: the sheet passes read as {_grouping(rs_sheet_passes)}, expected "
                f"[['A1', 'S1', 'M1', 'E1']] with the repeated lines pass apart"
            )
        if any(_REPEATED_PASS_RE.match(unit_id.rsplit("-", 1)[0]) for unit_id, _s in planned_ids(rs_sheet_passes)):
            errors.append(f"{repeated_label}: a repeated lines unit is read among the sheets")
        try:
            rs_window_1 = json.loads((rs_first / "plan" / "window-1.json").read_text(encoding="utf-8"))
        except Exception as e:
            rs_window_1 = {}
            errors.append(f"{repeated_label}: window-1.json: {e}")
        if any("RS1" in str(entry) for entry in rs_window_1.get("units", []) + rs_window_1.get("selected", [])):
            errors.append(f"{repeated_label}: window-1.json carries a repeated lines unit among the sheets")
        expect_bounds(repeated_label, rs_bounds, "ids kept 0 (ledger 0, plan file 0), ids new 5, ids retired 0")
        expect_bounds(
            repeated_label, rs_bounds,
            "repeated lines read once: files 2, passes 1, their ids kept 0 (ledger 0, plan file 0), "
            "new 2, retired 0",
        )
        if "repeated lines read once: files 2, passes 1," not in rs_text:
            errors.append(f"{repeated_label}: the read plan's totals do not count the repeated lines units")

    # Without the exclusion, file-d's six rows are all read, so it plans a unit too: the exclusion
    # is what kept it out above, not something else about the file.
    rs_whole = repeated_root / "whole"
    code, _bounds, err, _passes = run_replan(
        rs_whole, 1, write_replan_inventory(rs_whole, repeated_rows), []
    )
    if code != 0:
        errors.append(f"{repeated_label}: the window 1 plan with nothing left out refused: {err}")
    elif [unit[1] for unit in repeated_units(rs_whole)] != ["file-a", "file-b", "file-d"]:
        errors.append(
            f"{repeated_label}: with nothing left out, window 1 plans the repeated lines of "
            f"{[unit[1] for unit in repeated_units(rs_whole)]}, expected file-a, file-b and file-d"
        )

    # A file the run reads five of with one of its sheets left out still plans a unit, and that
    # unit names the sheet: `repeated: "only"` reads the whole file, the left-out sheet included,
    # so its reader needs the number to record nothing from a block printed only there.
    rs_one_out = repeated_root / "one-left-out"
    code, _bounds, err, _passes = run_replan(
        rs_one_out, 1, write_replan_inventory(rs_one_out, repeated_rows),
        leave_out_two + ["--exclude", "A-2.04:the user left this sheet out"],
    )
    one_out_text = (rs_one_out / "read-plan.md").read_text(encoding="utf-8") if code == 0 else ""
    one_out_left = {
        unit_id: sheets
        for p in _plan_passes(one_out_text, repeated=True) for unit_id, sheets in p.get("leftOut", {}).items()
    }
    if code != 0:
        errors.append(f"{repeated_label}: the window 1 plan leaving one of file-a's sheets out refused: {err}")
    elif one_out_left != {"RS1-1": ["A-2.04"], "RS1-2": []} or [
        entry.get("sheetsLeftOut") for entry in repeated_sets_on_file(rs_one_out)
    ] != [["A-2.04"], []]:
        errors.append(
            f"{repeated_label}: with A-2.04 left out, the unit lines name {one_out_left} and "
            f"window-1.json {repeated_sets_on_file(rs_one_out)}; file-a's unit should name A-2.04 "
            f"and file-b's none"
        )

    # --- 5: the ids across a replan ------------------------------------ #
    # A new file listed first in the inventory, so its natural place is ahead of both kept units.
    new_file_rows = [file_row("file-e", "G", "G-0.01", "cover-index", 1)] + [
        file_row("file-e", "G", f"G-2.0{i}", "plan", 1 + i) for i in range(1, 5)
    ]
    grown_inventory = write_replan_inventory(rs_first, new_file_rows + repeated_rows)
    code, grown_bounds, err, _passes = run_replan(rs_first, 1, grown_inventory, leave_out_two)
    if code != 0:
        errors.append(f"{repeated_label}: the replan with a new file refused: {err}")
    else:
        got = [(unit[0], unit[1]) for unit in repeated_units(rs_first)]
        if got != [("RS1-1", "file-a"), ("RS1-2", "file-b"), ("RS1-3", "file-e")]:
            errors.append(
                f"{repeated_label}: the replan with a new file reads {got}; the plan file's two ids "
                f"keep their files and the new file numbers after them"
            )
        expect_bounds(
            repeated_label, grown_bounds,
            "their ids kept 2 (ledger 0, plan file 2), new 1, retired 0",
        )

    # Both units dispatched, each on a `sheets none` line, beside one sheet's dispatch. Two units
    # naming no sheet must not read as one sheet under two ids, nor count as retired sheet ids.
    write_ledger(rs_first, [
        "dispatch 1 RS1 RS1-1 sheets none purpose repeated lines of file file-a",
        "dispatch 1 RS1 RS1-2 sheets none purpose repeated lines of file file-b",
        "dispatch 1 A1 A1-1 sheets A-0.01 purpose a schedule this pass reads",
    ])
    code, dispatched_bounds, err, _passes = run_replan(rs_first, 1, grown_inventory, leave_out_two)
    if code != 0:
        errors.append(f"{repeated_label}: a replan over two dispatched repeated lines units refused: {err}")
    else:
        expect_bounds(
            repeated_label, dispatched_bounds,
            "their ids kept 3 (ledger 2, plan file 1), new 0, retired 0",
        )
        expect_bounds(
            repeated_label, dispatched_bounds,
            "ids kept 6 (ledger 1, plan file 5), ids new 0, ids retired 0",
        )

    # Leaving out one more of file-b's rows takes it under five: its dispatched id is retired, and
    # no other file takes that number.
    code, cut_bounds, err, _passes = run_replan(
        rs_first, 1, grown_inventory, leave_out_two + ["--exclude", "S-2.01:the user left it out"]
    )
    if code != 0:
        errors.append(f"{repeated_label}: the replan cutting file-b under five rows refused: {err}")
    else:
        got = [(unit[0], unit[1]) for unit in repeated_units(rs_first)]
        if got != [("RS1-1", "file-a"), ("RS1-3", "file-e")]:
            errors.append(
                f"{repeated_label}: with file-b under five rows the plan reads {got}, expected "
                f"RS1-1 on file-a and RS1-3 on file-e, with RS1-2 retired"
            )
        expect_bounds(
            repeated_label, cut_bounds,
            "their ids kept 2 (ledger 1, plan file 1), new 0, retired 1",
        )

    # --- 10: the pass summary reads the pass, and the plan reads it summed - #
    rs_summary = repeated_root / "summary"
    rs_summary_inventory = write_replan_inventory(rs_summary, repeated_rows)
    run_replan(rs_summary, 1, rs_summary_inventory, leave_out_two)
    write_ledger(rs_summary, [
        "dispatch 1 RS1 RS1-1 sheets none purpose repeated lines of file file-a",
        "verified 1 RS1 RS1-1 created 40 items 12 updated 2 questions 1 replied 0 sent 44 landed 44 conflicts 0 result ok",
        "dispatch 1 RS1 RS1-2 sheets none purpose repeated lines of file file-b",
        "verified 1 RS1 RS1-2 created 9 items 3 updated 0 questions 0 replied 0 sent 9 landed 9 conflicts 0 result ok",
    ])
    rs_summary_module = _load_script_module(plugin_path.joinpath(*PASS_SUMMARY_SCRIPT), "pass_summary")
    try:
        code, summary, err = _run_script_main(rs_summary_module, [
            str(rs_summary / "ledger.md"), "1", "RS1", "--plan", str(rs_summary / "read-plan.md"),
        ])
    except SystemExit as e:
        code, summary, err = e.code, "", ""
    summary_lines = summary.splitlines()
    for wanted in (
        "units read: RS1-1, RS1-2",
        "per unit: RS1-1 created 40 items 12 updated 2 questions 1 replied 0 verified yes",
        "per unit: RS1-2 created 9 items 3 updated 0 questions 0 replied 0 verified yes",
    ):
        if code != 0 or wanted not in summary_lines:
            errors.append(
                f"{repeated_label}: the pass summary of RS1 does not read `{wanted}`: exit {code}, {err!r}"
            )
    if code == 0:
        (rs_summary / "reports").mkdir(parents=True, exist_ok=True)
        (rs_summary / "reports" / "RS1.md").write_text(summary + "\n", encoding="utf-8")
        with (rs_summary / "ledger.md").open("a", encoding="utf-8") as ledger:
            ledger.write(
                "pass: 1 RS1 units 2 created 49 updated 2 questions 1 replied 0 candidates 0 "
                "lead-verified yes\n"
            )
        run_replan(rs_summary, 1, rs_summary_inventory, leave_out_two)
        summed_pass = _plan_passes((rs_summary / "read-plan.md").read_text(encoding="utf-8"), repeated=True)
        got = [(p["fields"].get("units verified"), p["fields"].get("summed")) for p in summed_pass]
        if got != [("2", "yes")] or not all(unit[3] for unit in repeated_units(rs_summary)):
            errors.append(
                f"{repeated_label}: a repeated lines pass verified and summed reads {got} with units "
                f"{repeated_units(rs_summary)}, expected both units marked verified and the pass summed"
            )

    # --- 7 and 9: the window 2 mark ------------------------------------- #
    rs_w2 = repeated_root / "window-2"
    rs_w2_inventory = write_replan_inventory(rs_w2, repeated_rows)
    run_replan(rs_w2, 1, rs_w2_inventory, leave_out_two)
    rs_w2_window_1 = str(rs_w2 / "plan" / "window-1.json")
    ok_line = "verified 1 RS1 {} created 5 items 2 updated 0 questions 0 replied 0 sent 5 landed 5 conflicts 0 result {}"
    window_2_sheets = {
        "file-a": 4, "file-b": 4,
    }
    # Each unit's `set` note names the set version it read; the mark carries it to the reader.
    set_a = "note 1 RS1 RS1-1 set 1111aaaa2222bbbb file file-a"
    set_b = "note 1 RS1 RS1-2 set 3333cccc4444dddd file file-b"
    marked_cases: list[tuple[str, list[str], dict[str, str]]] = [
        ("no verified line for either unit", [set_a, set_b], {}),
        ("file-a verified ok", [ok_line.format("RS1-1", "ok"), set_a], {"file-a": "1111aaaa2222bbbb"}),
        ("file-a verified ok with no set note", [ok_line.format("RS1-1", "ok")], {}),
        ("file-a read twice, the second set note naming another version", [
            ok_line.format("RS1-1", "ok"), set_a, "note 1 RS1 RS1-1 set 5555eeee6666ffff file file-a",
        ], {"file-a": "5555eeee6666ffff"}),
        ("file-b verified as a mismatch", [
            ok_line.format("RS1-1", "ok"), set_a, ok_line.format("RS1-2", "mismatch"), set_b,
        ], {"file-a": "1111aaaa2222bbbb"}),
        ("file-a verified ok, then as a mismatch", [
            ok_line.format("RS1-1", "ok"), set_a, ok_line.format("RS1-1", "mismatch"),
        ], {}),
        ("file-a verified ok beside an unread note", [
            ok_line.format("RS1-1", "ok"), set_a,
            "note 1 RS1 RS1-1 unread file file-a repeated lines not read, the check stopped",
        ], {}),
        ("both verified ok", [
            ok_line.format("RS1-1", "ok"), set_a, ok_line.format("RS1-2", "ok"), set_b,
        ], {"file-a": "1111aaaa2222bbbb", "file-b": "3333cccc4444dddd"}),
    ]
    unmarked_ids: list[tuple[str, str]] | None = None
    for case, ledger_lines, wanted_files in marked_cases:
        write_ledger(rs_w2, ledger_lines or ["phase: plan approved"])
        code, w2_case_bounds, err, w2_case_passes = run_replan(
            rs_w2, 2, rs_w2_inventory, ["--window-1", rs_w2_window_1]
        )
        if code != 0:
            errors.append(f"{repeated_label}, {case}: window 2 refused: {err}")
            continue
        marked_files: dict[str, set[str]] = {}
        marked_count = 0
        for line in (rs_w2 / "read-plan.md").read_text(encoding="utf-8").splitlines():
            if line.strip() == _LEFT_OUT_HEADING:
                break
            unit = _PLAN_UNIT_RE.match(line)
            mark = re.search(r", repeated lines read(?: in set (\S+))?$", unit.group(4).removesuffix(" verified")) if unit else None
            if mark:
                marked_files.setdefault(file_of_sheet[unit.group(2)], set()).add(mark.group(1) or "")
                marked_count += 1
        if marked_files != {f: {v} for f, v in wanted_files.items()} or marked_count != sum(
            window_2_sheets[f] for f in wanted_files
        ):
            errors.append(
                f"{repeated_label}, {case}: window 2 marks {marked_count} sheets as {marked_files}, "
                f"expected every window 2 sheet of {wanted_files}, each in its file's set version, and "
                f"no other"
            )
        expect_bounds(
            f"{repeated_label}, {case}", w2_case_bounds,
            f"sheets read without their file's repeated lines {marked_count}, files whose repeated "
            f"lines were read {len(wanted_files)} of 2 planned",
        )
        expect_bounds(
            f"{repeated_label}, {case}", w2_case_bounds,
            "every sheet once (units 14 equals distinct sheets 14)",
        )
        if unmarked_ids is None:
            unmarked_ids = planned_ids(w2_case_passes)
        elif planned_ids(w2_case_passes) != unmarked_ids:
            errors.append(
                f"{repeated_label}, {case}: the mark moved a unit id: {planned_ids(w2_case_passes)} "
                f"against {unmarked_ids}"
            )

    # --- 6 and 8: refusals ---------------------------------------------- #
    def broken_repeated(case: str, ledger_lines: list[str], inventory_rows: list[dict]) -> tuple[str, str]:
        folder = repeated_root / "broken" / case
        shutil.rmtree(folder, ignore_errors=True)
        path = write_replan_inventory(folder, inventory_rows)
        write_ledger(folder, ledger_lines)
        return str(folder / "read-plan.md"), path

    def broken_window_1_file(case: str, repeated_sets: list) -> tuple[str, str, str]:
        out, path = broken_repeated(case, ["phase: plan approved"], repeated_rows)
        window_1_file = Path(out).parent / "plan" / "window-1.json"
        window_1_file.parent.mkdir(parents=True, exist_ok=True)
        window_1_file.write_text(
            json.dumps({"window": 1, "selected": [], "excluded": [], "repeatedSets": repeated_sets}) + "\n",
            encoding="utf-8",
        )
        return out, path, str(window_1_file)

    no_file_out, no_file_inventory = broken_repeated(
        "no-file", ["dispatch 1 RS1 RS1-1 sheets none purpose repeated lines"], repeated_rows)
    two_files_out, two_files_inventory = broken_repeated(
        "id-on-two-files",
        ["dispatch 1 RS1 RS1-1 sheets none purpose repeated lines of file file-a",
         "dispatch 1 RS1 RS1-1 sheets none purpose repeated lines of file file-b"],
        repeated_rows)
    two_ids_rs_out, two_ids_rs_inventory = broken_repeated(
        "file-under-two-ids",
        ["dispatch 1 RS1 RS1-1 sheets none purpose repeated lines of file file-a",
         "dispatch 1 RS1 RS1-2 sheets none purpose repeated lines of file file-a"],
        repeated_rows)
    rs_discipline_out, rs_discipline_inventory = broken_repeated(
        "discipline-rs", [], repeated_rows + [file_row("file-a", "RS", "RS-0.01", "schedule", 7)])
    stranger_out, stranger_inventory, stranger_window_1 = broken_window_1_file(
        "stranger-file", [{"fileId": "file-zz", "unitId": "RS1-1", "page": 1}])
    malformed_out, malformed_inventory, malformed_window_1 = broken_window_1_file(
        "malformed", [{"fileId": "file-a", "unitId": "A1-1", "page": 1}])
    repeated_refusals = [
        (
            "a repeated lines dispatch line naming no file",
            ["plan", "--window", "1", "--inventory", no_file_inventory, "--out", no_file_out],
            "names no file after `of file`",
        ),
        (
            "one repeated lines unit dispatched on two files",
            ["plan", "--window", "1", "--inventory", two_files_inventory, "--out", two_files_out],
            "one repeated lines unit reads one file",
        ),
        (
            "one file's repeated lines dispatched under two unit ids",
            ["plan", "--window", "1", "--inventory", two_ids_rs_inventory, "--out", two_ids_rs_out],
            "are dispatched under RS1-1 and RS1-2",
        ),
        (
            "a discipline whose window 1 pass id is RS1",
            ["plan", "--window", "1", "--inventory", rs_discipline_inventory, "--out", rs_discipline_out],
            "which is the repeated lines pass",
        ),
        (
            "a window 1 file planning the repeated lines of a file the inventory does not hold",
            ["plan", "--window", "2", "--inventory", stranger_inventory, "--window-1", stranger_window_1,
             "--out", stranger_out],
            "file-zz",
        ),
        (
            "a window 1 file whose repeatedSets entry is no repeated lines unit",
            ["plan", "--window", "2", "--inventory", malformed_inventory, "--window-1", malformed_window_1,
             "--out", malformed_out],
            "`repeatedSets` entry 1",
        ),
    ]

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
    refusals.extend(repeated_refusals)
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
        f"holding the first one's dispatched ids with verified sheets read earlier and a mismatch "
        f"still deferred, consecutive slices keeping ids 1..9 with six read earlier and all nine "
        f"bound and verified on the next whole-window plan, window-1.json carrying its patterns, "
        f"the fold checked on every window 1 and 2 plan (a pass at most twelve units holding at "
        f"most one part of three or more, which names it, a part under three joining the pass "
        f"before it whenever that has room, no pass under three beside one it fits into, every "
        f"folded unit keeping its own discipline's id, and the heading, the folded in line, the "
        f"bounds line and the totals naming each fold) with the fixture's groupings pinned by hand, "
        f"one sheet between two passes of twelve kept alone and named, a unit verified under its "
        f"part's own pass before a replan folds that part kept, marked verified and counted once "
        f"in the folded pass's summary, every pass marked summed only while its summary on file "
        f"names exactly its units and its last pass line carries that summary (a fold at the same "
        f"count, a summary rewritten before its pass line, and window 3's summary name among the "
        f"cases), a 209-sheet set's window 1 "
        f"of {sum(vocabulary_209.values())} vocabulary sheets in {len(w1_209_parts)} discipline "
        f"parts read in {len(w1_209_grouping)} passes with "
        f"{sum(len(group) - 1 for group in w1_209_grouping)} folds and its window 2 of "
        f"{len(w2_209_parts)} parts in {len(w2_209_grouping)} passes with "
        f"{sum(len(group) - 1 for group in w2_209_grouping)} folds, the repeated lines over a "
        f"four-file fixture (a unit per file of five or more rows the run reads, excluded rows not "
        f"counted and named on the unit, in a pass that never folds; their ids kept by file across "
        f"a replan and retired under five; the window 2 mark over {len(marked_cases)} ledgers, only "
        f"on a file whose unit verified ok last with a set note and no unread note, carrying the "
        f"last set version, moving no id; an RS1 pass summed), "
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
# and the runner writes what it returns. This runs the script in-process over three ledger fixtures
# and their read plans, and asserts every number against a tally computed here off the same text.
#
# A pass's units come off its read plan block. A replan can fold a part into another pass after a
# unit of that part was verified under the part's own pass id, and the runner then skips the unit,
# so the folded pass's summary has to count it off that line, once. The folded fixture carries that
# unit, and a unit the plan cut whose lines still name the pass.
#
# The joins this check exists for: the summary shape is published in the skill and in the runner
# definition, and the script fills it. The three would otherwise meet for the first time mid-run,
# so the labels the script prints are compared against the labels of the skill's own fenced block,
# in order, with nothing extra and nothing missing. The runner definition also spells the command
# that runs the script, and that command is fed to the script's own arguments.
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
    w1_plan = fixtures / "read-plan-fixture-w1.md"
    w3_plan = fixtures / "read-plan-fixture-w3.md"
    folded_fixture = fixtures / "ledger-fixture-folded.md"
    folded_plan = fixtures / "read-plan-fixture-folded.md"
    folded_trades = fixtures / "trades-folded"
    for fixture in (
        a1_fixture, mixed_fixture, trades_fixture, w1_plan, w3_plan, folded_fixture, folded_plan,
        folded_trades / "A1.txt", folded_trades / "G1.txt",
    ):
        if not fixture.is_file():
            return Result(name, False, detail=f"fixture not found at {fixture}")

    try:
        module = _load_script_module(script, "pass_summary")
    except Exception as e:
        return Result(name, False, detail=f"cannot import {script.name}: {e}")

    def summarize(argv: list[str]) -> tuple[int, str, str]:
        """The script's own main, with an invocation argparse refuses read as its exit code."""
        try:
            return _run_script_main(module, argv)
        except SystemExit as e:
            return (e.code if isinstance(e.code, int) else 2), "", ""

    errors: list[str] = []
    out_dir = Path(__file__).parent / ".test-results" / "pass-summary"
    out_dir.mkdir(parents=True, exist_ok=True)
    w1_args = ["--plan", str(w1_plan)]

    # ------------------------------------------------------------------ #
    # The whole of one pass, against a tally computed here
    # ------------------------------------------------------------------ #
    code, a1_out, a1_err = summarize([str(a1_fixture), "1", "A1", *w1_args])
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
    # The join: the runner's own command line is one the script accepts
    # ------------------------------------------------------------------ #
    runner = plugin_path / "agents" / "scope-round-runner.md"
    calls = (
        re.findall(
            r"`python3 '<scripts path>/pass_summary\.py' ([^`]*)`",
            runner.read_text(encoding="utf-8"),
        )
        if runner.is_file() else []
    )
    if len(calls) != 1:
        errors.append(f"{len(calls)} pass summary command lines in {runner.name}, expected 1")
    else:
        command = " ".join(calls[0].split()).replace("<window>", "1").replace("<pass id>", "A1")
        call_argv = [token.strip("'") for token in re.findall(r"'[^']*'|\S+", command)]
        code, _out, _err = summarize(call_argv)
        if code == 2:
            errors.append(
                f"the runner's summary command is one the script's arguments refuse: {call_argv}"
            )

    # ------------------------------------------------------------------ #
    # One pass only, and none of the lead's own numbers
    # ------------------------------------------------------------------ #
    code, mixed_out, mixed_err = summarize([str(mixed_fixture), "1", "B1", *w1_args])
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
    code, trades_out, _trades_err = summarize(
        [str(a1_fixture), "1", "A1", *w1_args, "--trades", str(trades_fixture)]
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
    # A pass a replan folded: every unit it carries, whatever pass verified it
    # ------------------------------------------------------------------ #
    #
    # G1-1 was verified while G1 still read alone, and a replan then put G1 inside A1. The runner
    # skips a unit verified under any pass, so the folded pass's summary has to count G1-1 off the
    # line that names G1, and once. A1-4 was verified under A1 and the replan left it out, so its
    # lines name A1 and still reach no total. Everything expected is tallied here off the files.
    folded_block = [
        plan_pass for plan_pass in _plan_passes(folded_plan.read_text(encoding="utf-8"))
        if plan_pass["id"] == "A1"
    ]
    folded_units = [unit_id for block in folded_block for unit_id, _sheet, _page in block["units"]]
    folded_in = [
        part.strip() for block in folded_block
        for part in block["fields"].get("folded in", "").split(",") if part.strip()
    ]
    folded_rows: list[list[str]] = []
    for raw in folded_fixture.read_text(encoding="utf-8").splitlines():
        parts = raw.split()
        if len(parts) >= 4 and parts[0] in ("dispatch", "verified", "note") and parts[1] == "1":
            folded_rows.append(parts)
    member_rows = [
        parts for parts in folded_rows
        if parts[3] in folded_units or (parts[3] == "-" and parts[2] in ["A1", *folded_in])
    ]
    member_verified = [parts for parts in member_rows if parts[0] == "verified"]
    read_order: list[str] = []
    for parts in member_rows:
        if parts[0] == "dispatch" and parts[3] not in read_order:
            read_order.append(parts[3])
    moved = [(parts[3], parts[2]) for parts in member_verified if parts[2] != "A1"]
    left_behind: dict[str, int] = {}
    for parts in folded_rows:
        if parts[2] == "A1" and parts[3] != "-" and parts[3] not in folded_units:
            left_behind[parts[3]] = left_behind.get(parts[3], 0) + 1
    if not moved or not left_behind or not folded_in:
        errors.append(
            "the folded fixture no longer carries a unit verified under another pass, a unit the "
            "plan left out and a folded-in part, which are the cases it exists for"
        )

    code, folded_out, folded_err = summarize([
        str(folded_fixture), "1", "A1", "--plan", str(folded_plan),
        "--trades", str(folded_trades / "A1.txt"),
    ])
    folded_lines = folded_out.splitlines()
    if code != 0:
        errors.append(f"the folded fixture refused: exit {code}, {folded_err or folded_out}")
    else:
        if f"units read: {', '.join(read_order)}" not in folded_lines:
            errors.append(
                f"the folded pass's units read are not every unit it carries, once each: "
                f"{[l for l in folded_lines if l.startswith('units read:')]}, expected {read_order}"
            )
        for parts in member_verified:
            counts = " ".join(
                f"{field} {field_of(parts, field)}"
                for field in ("created", "items", "updated", "questions", "replied")
            )
            wanted = f"per unit: {parts[3]} {counts} verified yes"
            if folded_lines.count(wanted) != 1:
                errors.append(f"the folded pass does not print {wanted!r} exactly once")
        folded_totals = {
            field: sum(field_of(parts, field) for parts in member_verified)
            for field in ("created", "items", "updated", "questions", "replied", "conflicts")
        }
        wanted_folded = (
            f"totals verified: created {folded_totals['created']} (entry count under the unit "
            f"prefixes), items {folded_totals['items']} (reader's own item count), updated "
            f"{folded_totals['updated']}, questions {folded_totals['questions']} replied "
            f"{folded_totals['replied']}"
        )
        if wanted_folded not in folded_lines:
            errors.append(
                f"the folded pass's totals are not its units' verified lines, each once: "
                f"{[l for l in folded_lines if l.startswith('totals verified:')]}, expected "
                f"{wanted_folded!r}"
            )
        folded_conflicted = [parts[3] for parts in member_verified if field_of(parts, "conflicts")]
        wanted_conflicts = (
            f"conflicting rows: {folded_totals['conflicts']}, on units {', '.join(folded_conflicted)}"
        )
        if wanted_conflicts not in folded_lines:
            errors.append(f"the folded pass's conflicting rows line is not {wanted_conflicts!r}")
        for kind, label in (("anomaly", "anomalies"), ("deviation", "deviations and repairs")):
            of_kind = [parts for parts in member_rows if parts[0] == "note" and parts[4] == kind]
            printed = [line for line in folded_lines if line.startswith(f"{label}: ")]
            wanted_lines = [
                f"{label}: {'' if parts[3] == '-' else parts[3] + ' '}{' '.join(parts[5:])}"
                for parts in of_kind
            ]
            if printed != wanted_lines:
                errors.append(
                    f"the folded pass's {label} lines are {printed}, expected {wanted_lines}: a "
                    f"note follows its unit, and a note on no unit follows the part it names"
                )
        for unit in left_behind:
            if unit in folded_out:
                errors.append(f"{unit}, which the plan left out, reached the folded pass's summary")
        if "9999" in folded_out:
            errors.append("the lead's own `pass:` line reached the folded pass's totals")
        named_moved = "verified under another pass: " + ", ".join(f"{u} ({p})" for u, p in moved)
        if named_moved not in folded_err:
            errors.append(f"the bounds line does not name `{named_moved}`: {folded_err!r}")
        named_left = "for a unit its plan block does not carry: " + ", ".join(
            f"{u} ({n} lines)" for u, n in left_behind.items()
        )
        if named_left not in folded_err:
            errors.append(f"the bounds line does not name `{named_left}`: {folded_err!r}")

        # Each unit's trades sit in the file of the pass whose runner verified it.
        folded_by_trade: dict[str, int] = {}
        folded_candidates = 0
        files_of: dict[str, set[str]] = {}
        for trades_file in sorted(folded_trades.glob("*.txt")):
            for raw in trades_file.read_text(encoding="utf-8").splitlines():
                if raw.split():
                    files_of.setdefault(raw.split()[0], set()).add(trades_file.stem)
        for parts in member_verified:
            for raw in (folded_trades / f"{parts[2]}.txt").read_text(encoding="utf-8").splitlines():
                fields = raw.split()
                if not fields or fields[0] != parts[3]:
                    continue
                if fields[1] == "candidates":
                    folded_candidates += int(fields[2])
                else:
                    trade = " ".join(fields[2:-1])
                    folded_by_trade[trade] = folded_by_trade.get(trade, 0) + int(fields[-1])
        for unit, verifying_pass in moved:
            if files_of.get(unit) != {verifying_pass}:
                errors.append(
                    f"{unit}'s trades are not on the file of {verifying_pass}, the pass that "
                    f"verified it, alone, so the fixture proves nothing about where they are read"
                )
        if not any(unit in files_of for unit in left_behind):
            errors.append("the folded trades files carry no line for the unit the plan left out")
        ordered = sorted(folded_by_trade.items(), key=lambda pair: (-pair[1], pair[0]))
        wanted_trades = (
            "trades: " + ", ".join(f"{c} x{n}" for c, n in ordered)
            + f"; candidates {folded_candidates}"
        )
        if wanted_trades not in folded_lines:
            errors.append(
                f"the folded pass's trades line is not its units' trades, each off the file of "
                f"the pass that verified it: {[l for l in folded_lines if l.startswith('trades:')]}, "
                f"expected {wanted_trades!r}"
            )

    # ------------------------------------------------------------------ #
    # Window 3: the pass and its one unit share an id
    # ------------------------------------------------------------------ #
    code, w3_out, _w3_err = summarize(
        [str(mixed_fixture), "3", "rev-099999-1", "--plan", str(w3_plan)]
    )
    if code != 0:
        errors.append(f"the window 3 summary refused: exit {code}")
    else:
        w3_verified = [
            parts for parts in _ledger_rows(mixed_fixture, 3, "rev-099999-1")
            if parts[0] == "verified"
        ]
        w3_created = sum(field_of(parts, "created") for parts in w3_verified)
        if "units read: rev-099999-1" not in w3_out.splitlines() or (
            f"created {w3_created} (entry count" not in w3_out
        ):
            errors.append("the window 3 summary does not read its one review unit off the plan")
        # The pass id itself carries 9999, so the strangers are looked for on the totals line.
        w3_totals = next(
            (line for line in w3_out.splitlines() if line.startswith("totals verified:")), ""
        )
        for stranger in ("9999", "777"):
            if stranger in w3_totals:
                errors.append(f"a figure of another window reached the window 3 totals: {stranger}")

    # The plan is what says which units a pass carries, so a summary without one is no summary.
    code, _out, _err = summarize([str(a1_fixture), "1", "A1"])
    if code != 2:
        errors.append(f"a summary given no read plan exited {code}, not 2")

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
        refusals.append((what, [str(path), "1", "A1", *w1_args], must_name))
    lonely_trades = out_dir / "lonely-trades"
    lonely_trades.mkdir(parents=True, exist_ok=True)
    refusals.extend([
        (
            "a window and pass with no lines",
            [str(a1_fixture), "1", "B1", *w1_args],
            "carries no dispatch, verified or note line",
        ),
        (
            "a ledger that is not there",
            [str(out_dir / "no-such-ledger.md"), "1", "A1", *w1_args],
            "no ledger at",
        ),
        (
            "a trades file that is not there",
            [str(a1_fixture), "1", "A1", *w1_args, "--trades", str(out_dir / "no-such-trades.txt")],
            "no trades file at",
        ),
        (
            "a trades file line in neither of its two shapes",
            [str(a1_fixture), "1", "A1", *w1_args, "--trades", str(out_dir / "broken-trades.txt")],
            "neither",
        ),
        (
            "a read plan that is not there",
            [str(a1_fixture), "1", "A1", "--plan", str(out_dir / "no-such-plan.md")],
            "no read plan at",
        ),
        (
            "a read plan of another window",
            [str(a1_fixture), "1", "A1", "--plan", str(w3_plan)],
            "is the read plan for window 3",
        ),
        (
            "a pass the read plan does not carry",
            [str(folded_fixture), "1", "G1", "--plan", str(folded_plan)],
            "carries no pass G1",
        ),
        (
            "a pass block listing fewer unit lines than its units count",
            [str(a1_fixture), "1", "A1", "--plan", str(out_dir / "short-plan.md")],
            "lists 10 unit lines",
        ),
        (
            "one unit verified under two passes",
            [str(out_dir / "twice-verified.md"), "1", "A1", "--plan", str(folded_plan)],
            "under pass G1",
        ),
        (
            "a moved unit whose verifying pass left no trades file",
            [str(folded_fixture), "1", "A1", "--plan", str(folded_plan),
             "--trades", str(lonely_trades / "A1.txt")],
            "no trades file at",
        ),
    ])
    (out_dir / "broken-trades.txt").write_text("A1-1 trades 09 21 16\n", encoding="utf-8")
    (out_dir / "short-plan.md").write_text(
        w1_plan.read_text(encoding="utf-8").replace("A1-11. A-9.11, page 199: (no title)\n", ""),
        encoding="utf-8",
    )
    (out_dir / "twice-verified.md").write_text(
        folded_fixture.read_text(encoding="utf-8")
        + "verified 1 A1 G1-1 created 1 items 1 updated 0 questions 0 replied 0 sent 1 landed 1 "
          "conflicts 0 result ok\n",
        encoding="utf-8",
    )
    (lonely_trades / "A1.txt").write_text(
        (folded_trades / "A1.txt").read_text(encoding="utf-8"), encoding="utf-8"
    )

    for what, argv, must_name in refusals:
        run_code, run_out, run_err = summarize(argv)
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
        f"trades line summed from a trades file and said plainly to be absent without one; a "
        f"folded pass counting every unit its plan block carries once, a unit verified under the "
        f"part's own pass id included with its trades off that pass's file, and a unit the plan "
        f"left out reaching no total and named on the bounds line; a window 3 pass whose one unit "
        f"is its own id; a summary with no read plan refused by argparse; "
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
# Check: no shipped text names `fork` as a subagent type
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
    "directory_update_comparable_project", "directory_update_contact", "edit_question_follow_up",
    "edit_question_reply_received", "edit_question_send", "extract_spec_toc",
    "extract_spec_toc_status", "follow_invitation_labor_default", "follow_up_question",
    "generate_deliverable",
    "get_bid_package", "get_page_text", "get_project", "index_citations",
    "index_citations_leftover", "index_citations_status", "list_definition_kinds",
    "list_definitions", "list_drawing_deliveries", "list_email_templates", "list_files",
    "list_invitation_flow_companies", "list_project_dates", "list_project_options",
    "list_projects", "list_questions", "list_scope_items", "log_question_reply_received",
    "mark_question_sent", "pin_question_reply", "project_set_design_team_company",
    "question_board", "read_deliverables", "read_invitation_flow", "read_question_list",
    "read_set_text", "read_sheet_context",
    "recognize_sheets", "recognize_sheets_status", "reconcile_index", "reconcile_set", "record",
    "record_additional_item", "record_batch", "record_batch_file", "register_file",
    "register_files", "register_pages", "remove_project_date", "remove_question_communication",
    "remove_sheet_from_page",
    "render_page", "renumber_sheet",
    "reopen_question", "reply_question", "request_file_upload", "request_file_uploads",
    "restore_question_communication", "restore_scope_item", "restore_source", "retire_scope_item",
    "retract_source",
    "rewrite_question", "search", "search_set_symbols", "search_set_symbols_status",
    "search_set_text", "set_grid", "set_invitation_include_missing", "set_invitation_labor",
    "set_invitation_places",
    "set_invitation_trades", "set_project_date", "set_question_reminder",
    "set_question_rfi_number", "set_question_trades", "set_text_status",
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
        # The runner dispatches readers; it reads no scope list itself.
        "list_scope_items",
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

# --------------------------------------------------------------------------- #
# Check: the repeated lines, as the reader and the runner are told to read and cite them
# --------------------------------------------------------------------------- #
#
# A repeated lines unit reads a drawing file's repeated lines once with `get_page_text` and
# `repeated: "only"`, and a window 2 reader leaves them out of its sheet with `repeated: "omit"`
# only where they were read. The citation is the part no run can repair afterwards: a row cites
# the block's first sheet with a box built from that note's line boxes, and the box lands only in
# the frame the boxes were measured in.
#
# The frame, settled off the api and worker code rather than assumed: the worker maps every word
# box from PyMuPDF's unrotated page space through `page.rotation_matrix` into the rendered frame,
# which is the frame of `page.rect` and of the SVG the sheet viewer draws with no scaling. A line
# box is the min and max of its words' boxes with nothing converted, and the repeated set's lines
# are copied verbatim from the first sheet's own lines. The contract's sheet locator reads both
# frame labels as that one space, and names `page-points` for a box read off the page text and
# `page-points-rendered` for one drawn on the canvas. So the reader sends the boxes as they are,
# labelled `page-points`, which is also the label the citation index writes for the same boxes.
#
# The checks: the reader's repeated lines section states the walk, the box rule and that label,
# and never `page-points-rendered`; its window 2 bullet asks for `omit` only on the dispatch's
# `Repeated lines: read` and reads whole on `repeatedNotChecked`; the reader report published in
# the agent and in the skill carries `cited sheets:`, which the runner names as what it verifies a
# repeated lines unit against. And the join: the runner's own dispatch and unread note lines for a
# repeated lines unit, filled in, are read by the shipped plan script exactly as it binds and
# marks, so the text and the script cannot drift apart.
#
# Honest bound, stated in the detail line: this is text and the script's ledger reader. It does
# not prove the record door takes the evidence shape or that the scope surface draws the box; the
# api's batch citation smoke proves a `sheet-region` citation sent with `frame: "page-points"`
# lands, and a new row's evidence locator is proved by no test here.

_REPEATED_SECTION_HEADING = "## Reading a file's repeated lines"
_REPEATED_SECTION_PHRASES = (
    'repeated: "only"',
    "`setVersion`",
    "`nextOffset`",
    "`firstSheet`",
    "lowest `x0` and `y0` to the highest `x1` and `y1`",
    'frame: "page-points"',
    "never convert a number",
    "`cited sheets:`",
    # The set it read, which a window 2 reader compares its answer against.
    "`set version:`",
    # A file that prints nothing repeated, and a context read never taken off a null first sheet.
    "`blockCount` is 0",
    "whose `firstSheet` carries a sheet number",
    # The sheets the run left out, which the whole-file read covers anyway, judged off each block's
    # own page list, with the search kept for a list the answer cut.
    "`Left out:`",
    "printed only on sheets left out",
    "its `printedOn`, every page that prints it as `[page, sheet number]`",
    "where `printedOnMore` is absent, the list is every page",
    "Only where `printedOnMore` is present",
    # A box on another page that prints the block is read off that page, around the same spot. Each
    # page sits within 2 points of the earliest page's spot, and the first sheet comes from the
    # set's order, so two occurrences can sit 4 points apart.
    "grown by 4 points on every side",
    # A first sheet with no number: a box needs one, and a page cited with none carries no box.
    'kind: "document-page"',
    "name the box you could not send",
    # An update cited to a page with no sheet number, which no sheet verifies.
    "`page citations:`",
    # `notListed` is one count for the whole set, read at that grain.
    "`{ blocks, lines, why }`",
)
# Phrases the section must not carry: a 2 point region misses an occurrence 4 points off.
_REPEATED_SECTION_FORBIDDEN = ("grown by 2 points",)
_OMIT_PHRASES = (
    'repeated: "omit"',
    "`Repeated lines: read in set <version>`",
    "`setVersion` equal to the version on your dispatch",
    # Each `omit` call reads the set as it stands, so every answer of the walk is compared.
    "compare on every answer of the walk",
    "on the first answer or any later one, restart the page from offset 0",
    "`repeatedOmitted`",
    "`repeatedNotChecked`",
    "never ask for `omit`",
)
# The omit answer names its set's version on every call, so the walk opens with no probe.
_OMIT_FORBIDDEN_PHRASES = ("`limit: 1`",)
# Every `verify_unit` call answers the whole prefix, so the prefix counts come off one call.
_RUNNER_SPLIT_VERIFY_PHRASE = "never added across calls"
_RUNNER_DISPATCH_RE = re.compile(
    r"`(dispatch <window> <pass> <unit> sheets none purpose repeated lines of file <fileId>)`"
)
_RUNNER_SET_RE = re.compile(r"`(note <window> <pass> <unit> set <setVersion> file <fileId>)`")
_RUNNER_UNREAD_RE = re.compile(
    r"`(note <window> <pass> <unit> unread file <fileId> repeated lines not read, <the reason>)`"
)
_RUNNER_NOT_LISTED_RE = re.compile(
    r"`(note <window> <pass> <unit> unread file <fileId> <blocks> blocks <lines> lines not listed, <why>)`"
)
# An update cited to a page with no sheet number is found back by its subject and that page.
_RUNNER_PAGE_CITATION_PHRASE = 'search(subject: "<subject>", full: true)'


def check_repeated_lines_text(plugin_path: Path, marketplace_root: Path) -> Result:
    name = "repeated-lines-text"
    reader = plugin_path / "agents" / "scope-reader.md"
    runner = plugin_path / "agents" / "scope-round-runner.md"
    skill = plugin_path / "skills" / "scope-run" / "SKILL.md"
    script = plugin_path.joinpath(*PLAN_INVENTORY_SCRIPT)
    for path in (reader, runner, skill, script):
        if not path.is_file():
            return Result(name, False, detail=f"not found: {path}")
    reader_text = reader.read_text(encoding="utf-8")
    runner_text = runner.read_text(encoding="utf-8")
    skill_text = skill.read_text(encoding="utf-8")
    errors: list[str] = []

    if _REPEATED_SECTION_HEADING not in reader_text:
        errors.append(f"scope-reader.md carries no `{_REPEATED_SECTION_HEADING}` section")
        section = ""
    else:
        section = reader_text.split(_REPEATED_SECTION_HEADING, 1)[1].split("\n## ", 1)[0]
    # Phrases wrap across lines in the file, so both sides are read with whitespace collapsed.
    section = " ".join(section.split())
    for phrase in _REPEATED_SECTION_PHRASES:
        if phrase not in section:
            errors.append(f"the reader's repeated lines section does not carry {phrase!r}")
    for phrase in _REPEATED_SECTION_FORBIDDEN:
        if phrase in section:
            errors.append(
                f"the reader's repeated lines section still carries {phrase!r}, a region that misses "
                f"an occurrence up to 4 points from the first sheet's"
            )
    # `notListed` can ride an answer that lists no block, so it is handled before the empty-set
    # step returns.
    not_listed_at = section.find("`notListed`")
    empty_at = section.find("`blockCount` is 0")
    if not_listed_at < 0 or empty_at < 0 or not_listed_at > empty_at:
        errors.append(
            "the reader's repeated lines section does not handle `notListed` before an answer whose "
            "`blockCount` is 0 sends it to report"
        )
    if "page-points-rendered" in reader_text:
        errors.append(
            "scope-reader.md names `page-points-rendered`, the label for a box drawn on the canvas, "
            "where every box it sends was read off the page text"
        )
    omit_bullet = " ".join(next(
        (block for block in reader_text.split("\n- ") if block.startswith("**Leave out what was read once.**")),
        "",
    ).split())
    for phrase in _OMIT_PHRASES:
        if phrase not in omit_bullet:
            errors.append(f"the reader's leave-out bullet does not carry {phrase!r}")
    for phrase in _OMIT_FORBIDDEN_PHRASES:
        if phrase in omit_bullet:
            errors.append(
                f"the reader's leave-out bullet still carries {phrase!r}, a probe the answer's own "
                f"set version made needless"
            )

    for label, text in (("scope-reader.md", reader_text), ("the scope-run skill", skill_text)):
        report = next(
            (body for body in _fenced_block_bodies(text.splitlines()) if any(l.startswith("unit: <unit id>") for l in body)),
            [],
        )
        for wanted in ("cited sheets: ", "page citations: ", "set version: "):
            if not any(line.startswith(wanted) for line in report):
                errors.append(f"the reader report published in {label} carries no `{wanted.strip()}` line")
    if "`cited sheets:`" not in runner_text:
        errors.append("the runner does not say it verifies a repeated lines unit off `cited sheets:`")
    if "`page citations:`" not in runner_text or _RUNNER_PAGE_CITATION_PHRASE not in " ".join(runner_text.split()):
        errors.append(
            "the runner does not verify an update cited to a page with no sheet number off "
            "`page citations:`, by its subject and that page"
        )
    # Both places that split a verify over calls of 20 sheets, a repeated lines unit in pass mode
    # and a review in review mode, take the prefix counts once; neither may sum them.
    runner_sections = {
        chunk.split("\n", 1)[0].strip(): " ".join(chunk.split("\n", 1)[-1].split())
        for chunk in runner_text.split("\n## ")[1:]
    }
    for heading, unit in (("Pass mode", "a repeated lines unit"), ("Review mode", "a review")):
        if _RUNNER_SPLIT_VERIFY_PHRASE not in runner_sections.get(heading, ""):
            errors.append(
                f"the runner's {heading.lower()} does not say {unit}'s prefix counts are taken once "
                f"and never added across its verify calls, each of which answers the whole prefix"
            )
    if re.search(r"\bsum(?:med)? the counts\b", " ".join(runner_text.split())):
        errors.append("the runner tells itself to sum counts across verify calls that each answer the whole prefix")

    # The join: the runner's own lines, filled in, through the script's own ledger readers.
    dispatch = _RUNNER_DISPATCH_RE.search(" ".join(runner_text.split()))
    set_note = _RUNNER_SET_RE.search(" ".join(runner_text.split()))
    unread = _RUNNER_UNREAD_RE.search(" ".join(runner_text.split()))
    not_listed = _RUNNER_NOT_LISTED_RE.search(" ".join(runner_text.split()))
    joined = 0
    if dispatch is None or set_note is None or unread is None or not_listed is None:
        errors.append(
            "the runner does not spell the repeated lines dispatch line, set note, unread note and "
            "not listed note in their fixed shapes"
        )
    else:
        try:
            module = _load_script_module(script, "plan_inventory")
        except Exception as e:
            return Result(name, False, detail=f"cannot import {script.name}: {e}")

        def fill(template: str, unit: str, file_id: str) -> str:
            return (
                template.replace("<window>", "1").replace("<pass>", "RS1").replace("<unit>", unit)
                .replace("<fileId>", file_id).replace("<the reason>", "the check stopped")
                .replace("<setVersion>", "9f2c41d07ab3e815").replace("<blocks>", "2")
                .replace("<lines>", "14").replace("<why>", "their pages were read again")
            )

        folder = Path(__file__).parent / ".test-results" / "repeated-lines-text"
        shutil.rmtree(folder, ignore_errors=True)
        folder.mkdir(parents=True, exist_ok=True)
        ledger = folder / "ledger.md"
        verified = "verified 1 RS1 {} created 3 items 1 updated 0 questions 0 replied 0 sent 3 landed 3 conflicts 0 result ok"
        ledger.write_text(
            "\n".join([
                fill(dispatch.group(1), "RS1-1", "file-a"),
                verified.format("RS1-1"),
                fill(set_note.group(1), "RS1-1", "file-a"),
                fill(dispatch.group(1), "RS1-2", "file-b"),
                verified.format("RS1-2"),
                fill(unread.group(1), "RS1-2", "file-b"),
                fill(dispatch.group(1), "RS1-3", "file-c"),
                verified.format("RS1-3"),
                # Read and versioned, but some blocks not listed: read by nobody, so kept whole.
                fill(dispatch.group(1), "RS1-4", "file-d"),
                verified.format("RS1-4"),
                fill(set_note.group(1), "RS1-4", "file-d"),
                fill(not_listed.group(1), "RS1-4", "file-d"),
            ]) + "\n",
            encoding="utf-8",
        )
        try:
            bound = module._read_ledger_repeated(ledger)
            read = module._read_repeated_read(
                ledger,
                [
                    {"fileId": "file-a", "unitId": "RS1-1"},
                    {"fileId": "file-b", "unitId": "RS1-2"},
                    {"fileId": "file-c", "unitId": "RS1-3"},
                    {"fileId": "file-d", "unitId": "RS1-4"},
                ],
            )
        except Exception as e:
            bound, read = {}, {}
            errors.append(f"the plan script refused the runner's own repeated lines lines: {e}")
        if bound != {"RS1-1": "file-a", "RS1-2": "file-b", "RS1-3": "file-c", "RS1-4": "file-d"}:
            errors.append(f"the plan script binds the runner's dispatch lines as {bound}, not each unit to its file")
        if read != {"file-a": "9f2c41d07ab3e815"}:
            errors.append(
                f"the plan script reads the files whose repeated lines were read as {read}; the "
                f"runner's set note should mark file-a in that version, its unread note keep file-b "
                f"whole, file-c, with no set note, stay whole, and its not listed note keep file-d "
                f"whole"
            )
        joined = 4

    detail = (
        f"the reader's repeated lines section checked for {len(_REPEATED_SECTION_PHRASES)} phrases "
        f"(the `only` walk with its set version, each block's first sheet, the box from the note's "
        f"line boxes, the `page-points` label sent unconverted, the set version kept, an empty set, "
        f"the sheets left out judged off each block's `printedOn` with the search kept for a cut "
        f"list, a first sheet with no number and its page citations, a box on another page read "
        f"around the same spot grown by 4 points, `notListed` handled before an empty set returns, and "
        f"`notListed` at its own grain), its leave-out bullet for {len(_OMIT_PHRASES)} (omit only on "
        f"a matching set version, whole otherwise, with no probe call), no `page-points-rendered` "
        f"anywhere in the reader, `cited sheets:` and `set version:` on the reader report in the "
        f"agent and the skill, the runner verifying off `cited sheets:` with the prefix counts taken "
        f"once in pass mode and review mode, and the runner's own dispatch, set and "
        f"unread note lines read by the plan script over {joined} units; bound: text and the "
        f"script's ledger reader, not the record door or the scope surface"
    )
    if errors:
        detail += " | " + "; ".join(errors)
    return Result(name, passed=not errors, detail=detail)


# --------------------------------------------------------------------------- #
# 24. A scope pass belongs to one drawing issue
# --------------------------------------------------------------------------- #
#
# A project goes through several drawing issues, and the estimator runs a pass on each. Every pass
# records its rows under `scopeItem:<unit id>-<seq>` and counts them by that prefix, so a second
# pass numbering its units the way the first one did would write onto the first pass's subjects,
# and its counts would take in the first pass's rows. A pass therefore lives in a run folder of
# its own whose `run.json` names the drawing issue and a unit tag, `i<n>`, that every unit id of
# the pass carries; the plan script reads that file, and a fourth subcommand picks which pass the
# lead resumes or starts.
#
# The failures this check exists for, each run against the shipped script: a second pass's ids
# colliding with the first's; a second pass resuming the first's closed ledger; an inventory
# carrying a sheet from another issue; a resume after a later delivery rebuilding the sheet list
# from the newer state; a prefix count taking in an earlier pass's rows; a run in the old layout no
# longer resuming; and a second pass started while one is in flight. Every expected value here is
# written by hand off the fixtures this check builds, never off the script's output.
#
# Honest bound, stated in the detail line: the grids and deliveries are invented and built here,
# so this proves the script's tagging, its refusals and its choice of pass, and nothing about how
# a real `set_grid` or `list_drawing_deliveries` answer arrives.

_ISSUE_PASS_RE = re.compile(r"^### (\S+?)\.\s")
_ISSUE_UNIT_RE = re.compile(r"^(\S+-[1-9][0-9]*)\. ")
_ISSUE_REVIEW_RE = re.compile(r"^[1-9][0-9]*\. (\S+): ")
_ISSUE_TAGGED_ID_RE = re.compile(r"^(i[1-9][0-9]*)-(\S+)-([1-9][0-9]*)$")


def _issue_ref(delivery_id: str, issue: str, set_id: str, sheets: int) -> dict:
    """One delivery as `set_grid` names it on `delivery` and in `readFrom`."""
    return {"id": delivery_id, "label": f"Label of {delivery_id}", "issue": issue, "setId": set_id, "sheetCount": sheets}


def _issue_grid(rows: list[dict], delivery: dict | None, read_from: list[dict] | None, row_delivery: str | None) -> dict:
    """A `set_grid` answer over the given rows, by delivery when `delivery` is given."""
    body: dict = {}
    if delivery is not None:
        body["delivery"] = delivery
        body["readFrom"] = read_from or []
    body.update({
        "count": len(rows), "returned": len(rows), "offset": 0, "limit": 500, "truncated": False,
        "sheets": [dict(row, **({"deliveryId": row_delivery} if row_delivery else {})) for row in rows],
    })
    return body


def _issue_run(delivery_id: str, read_from: list[str], tag: str, count: int | None = 0) -> dict:
    """A run.json as the lead writes it before the plan, with the tag check it took."""
    run: dict = {
        "deliveryId": delivery_id,
        "label": f"Label of {delivery_id}",
        "issue": "set",
        "setId": delivery_id,
        "readFrom": read_from,
        "unitTag": tag,
    }
    if count is not None:
        run["unitTagCheck"] = {"subjectPrefix": f"scopeItem:{tag}-", "count": count}
    return run


def _issue_ids(read_plan: str) -> tuple[list[str], list[str]]:
    """The pass ids and the unit ids a read plan carries, stopping at its left-out section."""
    passes: list[str] = []
    units: list[str] = []
    for line in read_plan.splitlines():
        if line.strip() == _LEFT_OUT_HEADING:
            break
        heading = _ISSUE_PASS_RE.match(line)
        if heading:
            passes.append(heading.group(1))
            continue
        unit = _ISSUE_UNIT_RE.match(line)
        if unit:
            units.append(unit.group(1))
            continue
        review = _ISSUE_REVIEW_RE.match(line)
        if review:
            units.append(review.group(1))
    return passes, units


def check_drawing_issue_passes(plugin_path: Path, marketplace_root: Path) -> Result:
    name = "drawing-issue-passes"
    script = plugin_path.joinpath(*PLAN_INVENTORY_SCRIPT)
    fixtures = marketplace_root / "harness" / "fixtures"
    try:
        module = _load_script_module(script, "plan_inventory")
        rows = json.loads((fixtures / "set-grid-fixture.json").read_text(encoding="utf-8"))["sheets"]
    except Exception as e:
        return Result(name, False, detail=f"cannot load the plan script or its grid fixture: {e}")
    packages = fixtures / "packages-fixture.json"
    root = Path(__file__).parent / ".test-results" / "drawing-issues"
    shutil.rmtree(root, ignore_errors=True)
    errors: list[str] = []
    refusals = 0

    def write(path: Path, payload) -> Path:
        path.parent.mkdir(parents=True, exist_ok=True)
        text = payload if isinstance(payload, str) else json.dumps(payload, indent=2)
        path.write_text(text, encoding="utf-8")
        return path

    def run(argv: list[str]) -> tuple[int, str, str]:
        try:
            return _run_script_main(module, argv)
        except SystemExit as e:
            return int(e.code or 0), "", "argparse exit"
        except Exception as e:
            return 99, "", f"raised {type(e).__name__}: {e}"

    def refused(argv: list[str], case: str, needle: str) -> None:
        """One refusal: exit 1, one line on stderr naming what is wrong, nothing on stdout."""
        nonlocal refusals
        refusals += 1
        code, out, err = run(argv)
        if code != 1 or out or len(err.splitlines()) != 1:
            errors.append(f"{case}: exited {code} with stdout {out[:120]!r} and stderr {err[:160]!r}, not one refusal line")
        elif needle not in err:
            errors.append(f"{case}: refused without naming {needle!r}: {err[:200]}")

    def inventory(folder: Path, grid: dict) -> tuple[int, str, str]:
        grid_path = write(folder / "grid" / "page-000.json", grid)
        return run(["inventory", "--grid", str(grid_path), "--expect-count", str(len(grid["sheets"])), "--out-dir", str(folder)])

    def plans(folder: Path) -> dict[int, str]:
        """Windows 1, 2 and 3 planned in one folder; the read plan text of each."""
        texts: dict[int, str] = {}
        for window, extra in (
            (1, ["--inventory", str(folder / "inventory.json")]),
            (2, ["--inventory", str(folder / "inventory.json"), "--window-1", str(folder / "plan" / "window-1.json")]),
            (3, ["--packages", str(packages)]),
        ):
            out = folder / f"read-plan-w{window}.md"
            code, bounds, err = run(["plan", "--window", str(window), *extra, "--out", str(out)])
            if code != 0:
                errors.append(f"{folder.name} window {window} refused: {err or bounds}")
                texts[window] = ""
                continue
            texts[window] = out.read_text(encoding="utf-8")
        return texts

    # ------------------------------------------------------------------ #
    # Two passes on two sets of one project, and the old layout beside them
    # ------------------------------------------------------------------ #
    project = root / "two-sets"
    first = project / "deliv-s1"
    second = project / "deliv-s2"
    s1 = _issue_ref("deliv-s1", "set", "deliv-s1", len(rows))
    s2 = _issue_ref("deliv-s2", "set", "deliv-s2", len(rows))
    a1 = _issue_ref("deliv-a1", "addendum", "deliv-s1", 3)
    write(first / "run.json", _issue_run("deliv-s1", ["deliv-s1", "deliv-a1"], "i1"))
    write(second / "run.json", _issue_run("deliv-s2", ["deliv-s2"], "i2"))
    code, bounds, err = inventory(first, _issue_grid(rows, s1, [s1, a1], "deliv-s1"))
    if code != 0:
        errors.append(f"the first set's inventory refused its own grid: {err or bounds}")
    elif "deliv-s1" not in bounds:
        errors.append(f"the first set's inventory bounds line does not name its drawing issue: {bounds!r}")
    elif f"first sheet {rows[0]['sheetNumber']}," not in bounds:
        # The lead probes the corpus with this sheet number, since it reads no sheet line.
        errors.append(f"the inventory bounds line does not name the first sheet, {rows[0]['sheetNumber']}: {bounds!r}")
    code, bounds, err = inventory(second, _issue_grid(rows, s2, [s2], "deliv-s2"))
    if code != 0:
        errors.append(f"the second set's inventory refused its own grid: {err or bounds}")
    legacy = root / "old-layout"
    code, bounds, err = inventory(legacy, _issue_grid(rows, None, None, None))
    if code != 0:
        errors.append(f"an inventory in the old layout, with no run.json and no drawing issue, refused: {err or bounds}")

    first_plans = plans(first)
    second_plans = plans(second)
    legacy_plans = plans(legacy)

    # The runner dispatches a sheet's file and checks the unit by it, and reads both off the unit
    # line, so a tagged plan names the file on every sheet line even where the set is one file, as
    # the fixture is. The old layout names it only across several files, as it always has.
    for window in (1, 2):
        for line in first_plans[window].split(_LEFT_OUT_HEADING)[0].splitlines():
            unit = _ISSUE_UNIT_RE.match(line)
            if unit and "repeated lines" not in line and ", file file-0001, page " not in line:
                errors.append(f"the first set's window {window} unit line names no file: {line!r}")
                break

    prefixes: dict[str, str] = {}
    for label, texts, tag in (("the first set", first_plans, "i1"), ("the second set", second_plans, "i2"), ("the old layout", legacy_plans, None)):
        for window, text in texts.items():
            pass_ids, unit_ids = _issue_ids(text)
            if not unit_ids:
                errors.append(f"{label} window {window} planned no units")
            for pass_id in pass_ids:
                if tag is not None and not pass_id.startswith(f"{tag}-"):
                    errors.append(f"{label} window {window} names pass {pass_id}, not tagged {tag}")
                if tag is None and pass_id.startswith("i") and pass_id[1:2].isdigit():
                    errors.append(f"the old layout names pass {pass_id}, which carries a unit tag")
            numbers: dict[str, list[int]] = {}
            for unit_id in unit_ids:
                tagged = _ISSUE_TAGGED_ID_RE.match(unit_id)
                if tag is not None and (tagged is None or tagged.group(1) != tag):
                    errors.append(f"{label} window {window} carries unit {unit_id}, not tagged {tag}")
                if tag is None and tagged is not None:
                    errors.append(f"the old layout carries unit {unit_id}, which carries a unit tag")
                part, _sep, number = unit_id.rpartition("-")
                numbers.setdefault(part, []).append(int(number))
                prefix = f"scopeItem:{unit_id}-"
                if prefix in prefixes:
                    errors.append(f"{label} window {window} and {prefixes[prefix]} both record under {prefix}")
                prefixes[prefix] = f"{label} window {window}"
            if window in (1, 2):
                for part, found in numbers.items():
                    if sorted(found) != list(range(1, len(found) + 1)):
                        errors.append(f"{label} window {window} numbers part {part} {sorted(found)}, not from 1")
    ordered = sorted(prefixes)
    for index, prefix in enumerate(ordered):
        for other in ordered[index + 1:]:
            if other.startswith(prefix):
                errors.append(f"{prefix} ({prefixes[prefix]}) is a prefix of {other} ({prefixes[other]}), so one count takes in the other's rows")
            else:
                break
    if len(prefixes) < 3:
        errors.append("fewer than three passes' unit ids were planned, so nothing was compared")
    try:
        repeated = json.loads((first / "plan" / "window-1.json").read_text(encoding="utf-8"))["repeatedSets"]
        if not repeated or any(not entry["unitId"].startswith("i1-RS1") for entry in repeated):
            errors.append(f"the first set's window 1 file names its repeated lines units as {[e['unitId'] for e in repeated]}")
    except Exception as e:
        errors.append(f"the first set's window 1 file: {e}")

    # A replan keeps every tagged id the ledger handed out, and retires a cut sheet's.
    try:
        w1_units = _issue_ids(first_plans[1])[1]
        bound_id = next(u for u in w1_units if u.startswith("i1-A1-") and u.endswith("-2"))
        cut_id = bound_id[:-1] + "1"
        sheet_of: dict[str, str] = {}
        for line in first_plans[1].splitlines():
            unit = _ISSUE_UNIT_RE.match(line)
            if unit:
                sheet_of[unit.group(1)] = line.split(". ", 1)[1].split(",", 1)[0]
        write(first / "ledger.md", f"phase: plan approved\ndispatch 1 i1-A1 {bound_id} sheets {sheet_of[bound_id]} purpose vocabulary\n")
        out = first / "read-plan-w1-again.md"
        code, bounds, err = run([
            "plan", "--window", "1", "--inventory", str(first / "inventory.json"),
            "--exclude", f"{sheet_of[cut_id]}:the estimator left it out", "--out", str(out),
        ])
        if code != 0:
            errors.append(f"the first set's window 1 replan refused: {err or bounds}")
        else:
            again: dict[str, str] = {}
            for line in out.read_text(encoding="utf-8").split(_LEFT_OUT_HEADING)[0].splitlines():
                unit = _ISSUE_UNIT_RE.match(line)
                if unit:
                    again[unit.group(1)] = line.split(". ", 1)[1].split(",", 1)[0]
            if again.get(bound_id) != sheet_of[bound_id]:
                errors.append(f"the replan moved {bound_id} off {sheet_of[bound_id]}: it now reads {again.get(bound_id)}")
            if cut_id in again:
                errors.append(f"the replan handed the cut sheet's id {cut_id} out again, to {again[cut_id]}")
        (first / "ledger.md").unlink(missing_ok=True)
    except StopIteration:
        errors.append("the first set's window 1 plan carries no i1-A1-2 unit to replan around")

    # The runner sums a tagged pass with the summary script, which reads the pass off the plan.
    try:
        summary_module = _load_script_module(plugin_path.joinpath(*PASS_SUMMARY_SCRIPT), "pass_summary")
        write(first / "ledger.md", (
            "phase: plan approved\n"
            "dispatch 1 i1-A1 i1-A1-1 sheets A-0.01 purpose vocabulary\n"
            "verified 1 i1-A1 i1-A1-1 created 4 items 2 updated 1 questions 0 replied 0 sent 6 "
            "landed 6 conflicts 0 result ok\n"
        ))
        code, out, err = _run_script_main(
            summary_module,
            [str(first / "ledger.md"), "1", "i1-A1", "--plan", str(first / "read-plan-w1.md")],
        )
        if code != 0 or "per unit: i1-A1-1 created 4 items 2 updated 1" not in out:
            errors.append(f"the summary script does not sum a tagged pass: exited {code}, {err or out[:200]}")
        (first / "ledger.md").unlink(missing_ok=True)
    except Exception as e:
        errors.append(f"the summary script over a tagged pass: {e}")

    # ------------------------------------------------------------------ #
    # Refusals: the drawing issue and the unit tag
    # ------------------------------------------------------------------ #
    def tagged_folder(case: str, run_json, grid: dict | None = None, beside: Path | None = None) -> Path:
        """
        A run folder for one refusal, apart from the two sets unless `beside` puts it in their
        project folder, since a run folder naming a delivery another one names is refused too.
        """
        folder = (beside or root / "refusals") / case
        write(folder / "run.json", run_json)
        if grid is not None:
            write(folder / "grid" / "page-000.json", grid)
        return folder

    def plan_argv(folder: Path, inventory_path: Path) -> list[str]:
        return ["plan", "--window", "1", "--inventory", str(inventory_path), "--out", str(folder / "read-plan.md")]

    def inventory_argv(folder: Path) -> list[str]:
        return ["inventory", "--grid", str(folder / "grid"), "--expect-count", str(len(rows)), "--out-dir", str(folder)]

    first_inventory = first / "inventory.json"

    folder = tagged_folder("tag-taken", _issue_run("deliv-s3", ["deliv-s3"], "i1"), beside=project)
    refused(plan_argv(folder, first_inventory), "a tag another pass of the project already carries", "i1")
    shutil.rmtree(folder, ignore_errors=True)
    folder = tagged_folder("delivery-taken", _issue_run("deliv-s2", ["deliv-s2"], "i9"), beside=project)
    # The second set's own inventory, so nothing but the other folder naming deliv-s2 refuses it.
    refused(plan_argv(folder, second / "inventory.json"), "a second run folder for a delivery another one names", "deliv-s2")
    shutil.rmtree(folder, ignore_errors=True)
    wrong_prefix = _issue_run("deliv-s1", ["deliv-s1", "deliv-a1"], "i9")
    wrong_prefix["unitTagCheck"]["subjectPrefix"] = "scopeItem:i3-"
    folder = tagged_folder("tag-checked-elsewhere", wrong_prefix)
    refused(plan_argv(folder, first_inventory), "a tag whose record count was taken under another prefix", "i9")
    shutil.rmtree(folder, ignore_errors=True)
    false_count = _issue_run("deliv-s1", ["deliv-s1", "deliv-a1"], "i9")
    false_count["unitTagCheck"]["count"] = False
    folder = tagged_folder("tag-count-false", false_count)
    refused(plan_argv(folder, first_inventory), "a tag whose record count is false rather than a number", "i9")
    shutil.rmtree(folder, ignore_errors=True)
    # A broken run.json in another pass's folder names that folder when the issue mode reads it,
    # and never stops this pass from planning.
    beside_broken = root / "broken-sibling"
    write(beside_broken / "deliv-s1" / "run.json", _issue_run("deliv-s1", ["deliv-s1", "deliv-a1"], "i1"))
    write(beside_broken / "lost-pass" / "run.json", "{ not json")
    code, bounds, err = run(plan_argv(beside_broken / "deliv-s1", first_inventory))
    if code != 0:
        errors.append(f"a broken run.json in another pass's folder stopped this pass planning: {err or bounds}")
    write(beside_broken / "deliveries.json", {"count": 0, "deliveries": []})
    refused(["issue", "--runs", str(beside_broken), "--deliveries", str(beside_broken / "deliveries.json")],
            "a broken run.json the issue mode cannot place", "lost-pass")
    shutil.rmtree(beside_broken, ignore_errors=True)
    folder = tagged_folder("tag-on-record", _issue_run("deliv-s1", ["deliv-s1", "deliv-a1"], "i7", count=4))
    refused(plan_argv(folder, first_inventory), "a tag the record already carries rows under", "i7")
    shutil.rmtree(folder, ignore_errors=True)
    folder = tagged_folder("tag-unchecked", _issue_run("deliv-s1", ["deliv-s1", "deliv-a1"], "i8", count=None))
    refused(plan_argv(folder, first_inventory), "a tag never checked on the record", "i8")
    shutil.rmtree(folder, ignore_errors=True)
    for bad in ("I9", "i0", "x9", "i9a"):
        folder = tagged_folder(f"tag-shape-{bad}", _issue_run("deliv-s1", ["deliv-s1", "deliv-a1"], bad))
        refused(plan_argv(folder, first_inventory), f"a unit tag shaped {bad}", bad)
        shutil.rmtree(folder, ignore_errors=True)
    folder = tagged_folder("read-from-without-itself", _issue_run("deliv-s1", ["deliv-a1"], "i9"))
    refused(plan_argv(folder, first_inventory), "a run.json whose readFrom leaves out its own delivery", "readFrom")
    shutil.rmtree(folder, ignore_errors=True)

    # The inventory carries a sheet from another issue: one row came from a delivery the pass does
    # not read from.
    stray = _issue_grid(rows, s1, [s1, a1], "deliv-s1")
    stray["sheets"][5]["deliveryId"] = "deliv-s2"
    folder = tagged_folder("stray-row", _issue_run("deliv-s1", ["deliv-s1", "deliv-a1"], "i9"), stray)
    refused(inventory_argv(folder), "a grid row from a delivery the pass does not read from", stray["sheets"][5]["sheetNumber"])
    shutil.rmtree(folder, ignore_errors=True)
    # A resume after a later delivery: the fetch run again now reads from an addendum that landed
    # since run.json was written, so the sheet list would be the newer state.
    a2 = _issue_ref("deliv-a2", "addendum", "deliv-s1", 2)
    folder = tagged_folder("later-delivery", _issue_run("deliv-s1", ["deliv-s1", "deliv-a1"], "i9"), _issue_grid(rows, s1, [s1, a1, a2], "deliv-s1"))
    refused(inventory_argv(folder), "a grid fetched again after a later delivery landed", "deliv-a2")
    shutil.rmtree(folder, ignore_errors=True)
    folder = tagged_folder("delivery-gone", _issue_run("deliv-s1", ["deliv-s1", "deliv-a1"], "i9"), _issue_grid(rows, s1, [s1], "deliv-s1"))
    refused(inventory_argv(folder), "a grid reading from fewer deliveries than run.json names", "deliv-a1")
    shutil.rmtree(folder, ignore_errors=True)
    folder = tagged_folder("other-delivery", _issue_run("deliv-s1", ["deliv-s1", "deliv-a1"], "i9"), _issue_grid(rows, s2, [s2], "deliv-s2"))
    refused(inventory_argv(folder), "a grid fetched for another drawing issue", "deliv-s2")
    shutil.rmtree(folder, ignore_errors=True)
    folder = tagged_folder("grid-without-delivery", _issue_run("deliv-s1", ["deliv-s1", "deliv-a1"], "i9"), _issue_grid(rows, None, None, None))
    refused(inventory_argv(folder), "a grid fetched for the current set in a pass on one issue", "deliveryId")
    shutil.rmtree(folder, ignore_errors=True)
    folder = project / "grid-without-run"
    write(folder / "grid" / "page-000.json", _issue_grid(rows, s1, [s1, a1], "deliv-s1"))
    refused(inventory_argv(folder), "a grid fetched for one issue into a folder with no run.json", "run.json")
    shutil.rmtree(folder, ignore_errors=True)
    # The plan refuses an inventory whose delivery differs from run.json, and an inventory taken for
    # one issue in a folder that names none.
    folder = tagged_folder("inventory-of-another-issue", _issue_run("deliv-s2", ["deliv-s2"], "i9"))
    refused(plan_argv(folder, first_inventory), "an inventory taken for another drawing issue", "deliv-s1")
    shutil.rmtree(folder, ignore_errors=True)
    folder = project / "inventory-without-run"
    folder.mkdir(parents=True, exist_ok=True)
    refused(plan_argv(folder, first_inventory), "an inventory taken for one issue in a folder with no run.json", "run.json")
    shutil.rmtree(folder, ignore_errors=True)
    folder = tagged_folder("inventory-of-no-issue", _issue_run("deliv-s1", ["deliv-s1", "deliv-a1"], "i9"))
    refused(plan_argv(folder, legacy / "inventory.json"), "an inventory of the current set in a pass on one issue", "deliv-s1")
    shutil.rmtree(folder, ignore_errors=True)
    folder = tagged_folder("inventory-read-from-more", _issue_run("deliv-s1", ["deliv-s1"], "i9"))
    refused(plan_argv(folder, first_inventory), "an inventory read from deliveries run.json does not name", "deliv-a1")
    shutil.rmtree(folder, ignore_errors=True)
    # Window 2 plans off window 1's file, so a tag changed between the two would put the window's
    # ids under another tag than the vocabulary's.
    folder = tagged_folder("tag-changed-after-window-1", _issue_run("deliv-s1", ["deliv-s1", "deliv-a1"], "i5"))
    write(folder / "plan" / "window-1.json", (first / "plan" / "window-1.json").read_text(encoding="utf-8"))
    refused(
        ["plan", "--window", "2", "--inventory", str(first_inventory), "--window-1",
         str(folder / "plan" / "window-1.json"), "--out", str(folder / "read-plan.md")],
        "window 2 under another tag than window 1's", "i1",
    )
    shutil.rmtree(folder, ignore_errors=True)
    # Window 3 reads no inventory, so a pass folder that lost its run.json is found by what else it
    # holds: an inventory taken for one issue, or a ledger whose unit ids carry a tag.
    folder = root / "refusals" / "review-without-run"
    write(folder / "inventory.json", first_inventory.read_text(encoding="utf-8"))
    refused(["plan", "--window", "3", "--packages", str(packages), "--out", str(folder / "read-plan.md")],
            "window 3 in a pass folder whose inventory names an issue and which holds no run.json", "run.json")
    shutil.rmtree(folder, ignore_errors=True)
    folder = root / "refusals" / "review-tagged-ledger"
    write(folder / "ledger.md", "phase: plan approved\ndispatch 1 i1-A1 i1-A1-1 sheets A-0.01 purpose vocabulary\n")
    refused(["plan", "--window", "3", "--packages", str(packages), "--out", str(folder / "read-plan.md")],
            "window 3 in a pass folder whose ledger carries tagged ids and which holds no run.json", "run.json")
    shutil.rmtree(folder, ignore_errors=True)
    folder = tagged_folder("run-not-json", "{ not json")
    refused(plan_argv(folder, first_inventory), "a run.json that does not parse", "run.json")
    shutil.rmtree(folder, ignore_errors=True)

    # ------------------------------------------------------------------ #
    # Which pass the lead resumes or starts
    # ------------------------------------------------------------------ #
    def delivery(delivery_id: str, issue, set_id, sheets, reading: bool = False) -> dict:
        return {
            "id": delivery_id, "label": f"Label of {delivery_id}", "deliveryKind": "revision",
            "issuedOn": None, "sequence": None, "issue": issue, "setId": set_id,
            "sheetCount": sheets, "stillReading": reading,
        }

    deliveries = [
        delivery("deliv-d1", "set", "deliv-d1", 400),
        delivery("deliv-d2", "addendum", "deliv-d1", 40),
        delivery("deliv-d3", "set", "deliv-d3", 420),
        delivery("deliv-d4", "addendum", "deliv-d3", 12),
    ]
    closed = "phase: plan approved\nphase: window 1 complete\nphase: closed out\n"
    open_ledger = "phase: plan approved\nphase: window 1 complete\n"

    def choose(case: str, folders: dict[str, tuple[dict, str | None]] | None = None, root_ledger: str | None = None,
               listed: list[dict] | None = None) -> tuple[int, str, str, Path]:
        runs = root / "choose" / case
        shutil.rmtree(runs, ignore_errors=True)
        runs.mkdir(parents=True)
        if root_ledger is not None:
            write(runs / "ledger.md", root_ledger)
        for folder_name, (run_json, ledger) in (folders or {}).items():
            write(runs / folder_name / "run.json", run_json)
            if ledger is not None:
                write(runs / folder_name / "ledger.md", ledger)
        listing = write(runs / "deliveries.json", {"count": len(listed or deliveries), "deliveries": listed if listed is not None else deliveries})
        code, out, err = run(["issue", "--runs", str(runs), "--deliveries", str(listing)])
        return code, out, err, runs

    def verdict(case: str, want: str, *needles: str, **kwargs) -> None:
        code, out, err, runs = choose(case, **kwargs)
        if code != 0 or len(out.splitlines()) != 1:
            errors.append(f"choosing a pass, {case}: exited {code} with {out!r} {err!r}, not one line")
            return
        if out.split()[0].rstrip(":") != want:
            errors.append(f"choosing a pass, {case}: answered {out!r}, not {want}")
        for needle in needles:
            if needle.replace("<runs>", str(runs)) not in out:
                errors.append(f"choosing a pass, {case}: answered {out!r}, which does not name {needle.replace('<runs>', str(runs))!r}")

    run_d1 = _issue_run("deliv-d1", ["deliv-d1", "deliv-d2"], "i1")
    run_d3 = _issue_run("deliv-d3", ["deliv-d3"], "i2")
    verdict("a project with no pass", "start", "deliv-d3", "i1", "<runs>")
    verdict("the first set's pass closed", "start", "deliv-d3", "i2", folders={"deliv-d1": (run_d1, closed)})
    verdict("the first set's pass in flight", "resume", "deliv-d1", folders={"deliv-d1": (run_d1, open_ledger)})
    verdict("the first set's pass planned and not yet approved", "resume", "deliv-d1", folders={"deliv-d1": (run_d1, None)})
    verdict("a pass in the old layout in flight", "resume", "<runs>", root_ledger=open_ledger)
    verdict("a pass in the old layout closed", "start", "deliv-d3", "i1", "names no drawing issue", root_ledger=closed)
    verdict("a ledger whose phase line only starts like a close-out", "resume", "deliv-d1",
            folders={"deliv-d1": (run_d1, open_ledger + "phase: closed outstanding\n")})
    verdict("a pass in flight beside a delivery list the issue mode could not read", "resume", "deliv-d1",
            folders={"deliv-d1": (run_d1, open_ledger)},
            listed=deliveries + [delivery("deliv-d6", "baseline", None, 5)])
    # An addendum that landed after its set's pass gets a partial pass of its own, the earliest
    # first, and once it has one there is nothing left to start.
    verdict("the latest set's pass closed with its addendum unread", "start", "deliv-d4", "addendum", "i3",
            folders={"deliv-d1": (run_d1, closed), "deliv-d3": (run_d3, closed)})
    verdict("two addenda after the latest set's pass", "start", "deliv-d4",
            folders={"deliv-d3": (run_d3, closed)},
            listed=deliveries + [delivery("deliv-d7", "addendum", "deliv-d3", 6)])
    verdict("the addendum's own pass closed", "none", "deliv-d3",
            folders={"deliv-d3": (run_d3, closed),
                     "deliv-d4": (dict(_issue_run("deliv-d4", ["deliv-d4"], "i3"), issue="addendum", setId="deliv-d3"), closed)})
    verdict("an addendum's pass in flight", "resume", "deliv-d4",
            folders={"deliv-d3": (run_d3, closed),
                     "deliv-d4": (dict(_issue_run("deliv-d4", ["deliv-d4"], "i3"), issue="addendum", setId="deliv-d3"), open_ledger)},
            listed=deliveries + [delivery("deliv-d7", "addendum", "deliv-d3", 6)])
    # A closed pass in the old layout read some set, and the lead says so at a set's start. An
    # addendum's pass reads only the addendum's sheets, so its start carries no such note.
    code, out, err, _runs = choose("an addendum after a pass in the old layout", root_ledger=closed,
                                   folders={"deliv-d3": (run_d3, closed)})
    if code != 0 or not out.startswith("start deliv-d4") or "names no drawing issue" in out:
        errors.append(f"an addendum's start beside a closed pass in the old layout reads {out or err!r}")
    verdict("the latest set's pass closed with its addendum read in it", "none", "deliv-d3",
            folders={"deliv-d3": (_issue_run("deliv-d3", ["deliv-d3", "deliv-d4"], "i2"), closed)})
    verdict("a delivery still being read", "wait", "deliv-d5",
            listed=deliveries + [delivery("deliv-d5", None, None, None, reading=True)])
    verdict("a delivery still being read while a pass is in flight", "resume", "deliv-d1",
            folders={"deliv-d1": (run_d1, open_ledger)},
            listed=deliveries + [delivery("deliv-d5", None, None, None, reading=True)])
    verdict("the tags already handed out", "start", "i4",
            folders={"deliv-d1": (run_d1, closed), "deliv-d2": (_issue_run("deliv-d2", ["deliv-d2"], "i3"), closed)})
    verdict("no delivery reads as a set", "none",
            listed=[delivery("deliv-e1", None, None, 0)])

    for case, kwargs, needle in (
        ("two passes in flight", {"folders": {"deliv-d1": (run_d1, open_ledger), "deliv-d3": (run_d3, open_ledger)}}, "deliv-d3"),
        ("a pass in the old layout and one on an issue both in flight", {"folders": {"deliv-d3": (run_d3, open_ledger)}, "root_ledger": open_ledger}, "deliv-d3"),
    ):
        refusals += 1
        code, out, err, _runs = choose(case, **kwargs)
        if code != 1 or out or len(err.splitlines()) != 1 or needle not in err:
            errors.append(f"choosing a pass, {case}: exited {code} with {out!r} {err!r}, not one refusal naming {needle}")
    stray_runs = root / "choose" / "ledger-without-run"
    shutil.rmtree(stray_runs, ignore_errors=True)
    write(stray_runs / "lost" / "ledger.md", open_ledger)
    listing = write(stray_runs / "deliveries.json", {"count": len(deliveries), "deliveries": deliveries})
    refused(["issue", "--runs", str(stray_runs), "--deliveries", str(listing)], "a run folder with a ledger and no run.json", "lost")
    # The listing is read only once no pass is in flight, so its refusals run over a project with
    # no pass yet.
    no_runs = root / "choose" / "no-runs"
    no_runs.mkdir(parents=True, exist_ok=True)
    bad_listing = write(root / "choose" / "bad-listing.json", {"count": 1, "deliveries": [delivery("deliv-f1", "baseline", "deliv-f1", 10)]})
    refused(["issue", "--runs", str(no_runs), "--deliveries", str(bad_listing)], "a delivery whose issue is neither set nor addendum", "baseline")
    reading_word = write(root / "choose" / "reading-word.json", {"count": 1, "deliveries": [dict(delivery("deliv-g1", None, None, None), stillReading="false")]})
    refused(["issue", "--runs", str(no_runs), "--deliveries", str(reading_word)],
            "a delivery whose stillReading is not true or false", "deliv-g1")
    no_array = write(root / "choose" / "no-array.json", {"count": 0})
    refused(["issue", "--runs", str(no_runs), "--deliveries", str(no_array)], "a deliveries file with no deliveries array", "deliveries")

    # ------------------------------------------------------------------ #
    # An addendum's partial pass
    # ------------------------------------------------------------------ #
    #
    # An addendum's pass reads the sheets it prints and nothing else, its revised schedule in window
    # 1 ahead of the plans that call it in window 2, and reviews only the packages it wrote on.
    by_number = {row["sheetNumber"]: row for row in rows}
    addendum_numbers = ["A-0.04", "A-2.01", "A-2.02", "A-2.03"]
    ad = _issue_ref("deliv-ad", "addendum", "deliv-s1", len(addendum_numbers))
    addendum_run = dict(_issue_run("deliv-ad", ["deliv-ad"], "i3"), issue="addendum", setId="deliv-s1")
    addendum = root / "addendum" / "deliv-ad"
    write(addendum / "run.json", addendum_run)
    code, bounds, err = inventory(addendum, _issue_grid([by_number[n] for n in addendum_numbers], ad, [ad], "deliv-ad"))
    if code != 0:
        errors.append(f"an addendum's inventory refused its own grid: {err or bounds}")
    else:
        # Each runner creates its pass's trades file as it starts, so window 3 always finds the folder.
        (addendum / "trades").mkdir(parents=True, exist_ok=True)
        addendum_plans = plans(addendum)
        planned = {
            window: [line.split(". ", 1)[1].split(",", 1)[0]
                     for line in text.split(_LEFT_OUT_HEADING)[0].splitlines()
                     if _ISSUE_UNIT_RE.match(line) and "repeated lines" not in line]
            for window, text in addendum_plans.items() if window in (1, 2)
        }
        if planned.get(1) != ["A-0.04"]:
            errors.append(f"an addendum's window 1 reads {planned.get(1)}, not its revised schedule A-0.04 alone")
        if sorted(planned.get(2, [])) != ["A-2.01", "A-2.02", "A-2.03"]:
            errors.append(f"an addendum's window 2 reads {planned.get(2)}, not its three plans")
        strangers = sorted({n for sheets in planned.values() for n in sheets} - set(addendum_numbers))
        if strangers:
            errors.append(f"an addendum's pass reads sheets it does not print: {strangers}")
    stray = _issue_grid([by_number[n] for n in addendum_numbers], ad, [ad], "deliv-ad")
    stray["sheets"][1]["deliveryId"] = "deliv-s1"
    folder = tagged_folder("addendum-with-a-set-sheet", addendum_run, stray)
    refused(inventory_argv(folder), "an addendum's grid carrying a sheet of its set", "A-2.01")
    shutil.rmtree(folder, ignore_errors=True)

    # An addendum that prints no schedule, legend, notes or index sheet, and no file of five sheets,
    # plans no window 1 unit and reads everything in window 2.
    bare = root / "addendum-bare" / "deliv-ae"
    ae = _issue_ref("deliv-ae", "addendum", "deliv-s1", 3)
    write(bare / "run.json", dict(_issue_run("deliv-ae", ["deliv-ae"], "i4"), issue="addendum", setId="deliv-s1"))
    code, bounds, err = inventory(bare, _issue_grid([by_number[n] for n in ("A-2.04", "A-2.05", "P-1.01")], ae, [ae], "deliv-ae"))
    if code != 0:
        errors.append(f"an addendum with no vocabulary sheet refused its inventory: {err or bounds}")
    else:
        code, bounds, err = run(["plan", "--window", "1", "--inventory", str(bare / "inventory.json"), "--out", str(bare / "read-plan-w1.md")])
        if code != 0 or "units 0," not in bounds:
            errors.append(f"an addendum with no vocabulary sheet does not plan an empty window 1: {err or bounds}")
        code, bounds, err = run(["plan", "--window", "2", "--inventory", str(bare / "inventory.json"),
                                 "--window-1", str(bare / "plan" / "window-1.json"), "--out", str(bare / "read-plan-w2.md")])
        if code != 0 or "sheets 3," not in bounds:
            errors.append(f"an addendum with no vocabulary sheet does not read its three sheets in window 2: {err or bounds}")

    # Window 3 of an addendum's pass reviews the packages its trades files name and names the rest.
    def review_plan(folder: Path) -> tuple[int, str, str, str]:
        out = folder / "read-plan-w3.md"
        code, bounds, err = run(["plan", "--window", "3", "--packages", str(packages), "--out", str(out)])
        return code, bounds, err, out.read_text(encoding="utf-8") if code == 0 else ""

    write(addendum / "trades" / "i3-A1.txt", "i3-A1-1 trade 09 21 16 4\ni3-A1-1 candidates 1\n")
    write(addendum / "trades" / "i3-A2.txt", "i3-A2-1 trade 22 11 16 2\ni3-A2-1 candidates 0\ni3-A2-2 trade 09 21 16 1\n")
    code, bounds, err, text = review_plan(addendum)
    reviewed = sorted(_issue_ids(text)[1])
    if code != 0:
        errors.append(f"window 3 of an addendum's pass refused: {err or bounds}")
    elif reviewed != ["i3-rev-092116-1", "i3-rev-221116-1"]:
        errors.append(f"window 3 of an addendum's pass reviews {reviewed}, not the two packages its rows were written on")
    elif "packages left out 6" not in bounds or not all(
        name in text.split(_LEFT_OUT_HEADING)[-1] for name in ("Painting", "Windows", "Glazing", "Landscaping", "Window treatments", "Pre-engineered structures")
    ):
        errors.append(f"window 3 of an addendum's pass does not name the six packages it leaves out: {bounds!r}")
    for trades_file in (addendum / "trades").glob("*.txt"):
        write(trades_file, "i3-A1-1 candidates 0\n")
    code, bounds, err, text = review_plan(addendum)
    if code != 0 or _issue_ids(text)[1] or "packages left out 8" not in bounds:
        errors.append(f"window 3 of an addendum's pass that wrote no row does not plan no review: {err or bounds}")
    # An addendum that only changes existing scope, a revised hardware row cited on its page or a
    # Question it raised, is the case where the estimator most needs that package reviewed. The
    # runner carries the trades the reader touched as `touched` lines beside the created ones.
    # A trade folded into a package's `codes` is covered by that package: a pass that wrote only on
    # it still reviews the package that bids it.
    write(addendum / "trades" / "i3-A1.txt", "i3-A1-1 trade 09 22 16 2\ni3-A1-1 candidates 0\n")
    write(addendum / "trades" / "i3-A2.txt", "i3-A2-1 candidates 0\n")
    code, bounds, err, text = review_plan(addendum)
    if code != 0 or sorted(_issue_ids(text)[1]) != ["i3-rev-092116-1"]:
        errors.append(
            f"window 3 of an addendum's pass that wrote only on a trade in a package's codes does not "
            f"review that package: {err or sorted(_issue_ids(text)[1])}"
        )
    # A broad package code covers the trades under it, as the server reads coverage: 32 90 00
    # covers 32 93 00, and the section 09 91 00 covers 09 91 23.
    write(addendum / "trades" / "i3-A1.txt", "i3-A1-1 trade 32 93 00 1\ni3-A1-1 trade 09 91 23 1\ni3-A1-1 candidates 0\n")
    code, bounds, err, text = review_plan(addendum)
    if code != 0 or sorted(_issue_ids(text)[1]) != ["i3-rev-099100-1", "i3-rev-329000-1"]:
        errors.append(
            f"window 3 of an addendum's pass that wrote only on trades under a package's broad code "
            f"does not review those packages: {err or sorted(_issue_ids(text)[1])}"
        )
    write(addendum / "trades" / "i3-A1.txt", "i3-A1-1 candidates 0\ni3-A1-1 touched 08 50 00\n")
    write(addendum / "trades" / "i3-A2.txt", "i3-A2-1 candidates 0\ni3-A2-2 candidates 0\ni3-A2-2 touched 32 90 00\n")
    code, bounds, err, text = review_plan(addendum)
    if code != 0 or sorted(_issue_ids(text)[1]) != ["i3-rev-085000-1", "i3-rev-329000-1"]:
        errors.append(
            f"window 3 of an addendum's pass that only updated rows and raised a Question does not review "
            f"those two packages: {err or sorted(_issue_ids(text)[1])}"
        )
    # A catalog id the reader spaced otherwise than the package folds to the same trade.
    write(addendum / "trades" / "i3-A1.txt", "i3-A1-1 candidates 0\ni3-A1-1 touched 085000\n")
    write(addendum / "trades" / "i3-A2.txt", "i3-A2-1 candidates 0\n")
    code, bounds, err, text = review_plan(addendum)
    if code != 0 or _issue_ids(text)[1] != ["i3-rev-085000-1"]:
        errors.append(f"a touched id spaced `085000` does not review the `08 50 00` package: {err or _issue_ids(text)[1]}")
    # Both scripts read one grammar, equally strict: a count that is not a whole number is refused.
    write(addendum / "trades" / "i3-A2.txt", "i3-A2-1 candidates many\n")
    refused(["plan", "--window", "3", "--packages", str(packages), "--out", str(addendum / "read-plan-w3.md")],
            "a trades line whose candidates count is not a number", "i3-A2.txt line 1")
    write(addendum / "trades" / "i3-A2.txt", "i3-A2-1 trade 09 21 16 four\n")
    refused(["plan", "--window", "3", "--packages", str(packages), "--out", str(addendum / "read-plan-w3.md")],
            "a trades line whose trade count is not a number", "i3-A2.txt line 1")
    write(addendum / "trades" / "i3-A2.txt", "i3-A2-1 candidates 0\n")
    # The union rests on the reader's own `trades touched:` line, so a unit whose verified line shows
    # an update or a Question raised and that carries no touched line leaves the union unknown: every
    # package is reviewed and the plan says why, rather than naming packages left out as untouched.
    write(addendum / "ledger.md", (
        "phase: plan approved\n"
        "verified 1 i3-A1 i3-A1-1 created 0 items 0 updated 1 questions 0 replied 0 sent 1 landed 1 conflicts 0 result ok\n"
        "verified 2 i3-A2 i3-A2-1 created 0 items 0 updated 0 questions 1 replied 0 sent 1 landed 1 conflicts 0 result ok\n"
    ))
    code, bounds, err, text = review_plan(addendum)
    if code != 0 or len(_issue_ids(text)[1]) != 8 or "i3-A2-1" not in bounds or "i3-A2-1" not in text:
        errors.append(
            f"window 3 of an addendum's pass whose unit raised a Question and named no trade does not review "
            f"every package and say which unit: {err or bounds}"
        )
    write(addendum / "trades" / "i3-A2.txt", "i3-A2-1 candidates 0\ni3-A2-1 touched 32 90 00\n")
    code, bounds, err, text = review_plan(addendum)
    if code != 0 or sorted(_issue_ids(text)[1]) != ["i3-rev-085000-1", "i3-rev-329000-1"]:
        errors.append(
            f"window 3 of an addendum's pass whose every updating unit named its trades does not review "
            f"only those: {err or sorted(_issue_ids(text)[1])}"
        )
    (addendum / "ledger.md").unlink(missing_ok=True)
    # The summary script sums the created trades off the same file and reads past a touched line.
    try:
        summary_module = _load_script_module(plugin_path.joinpath(*PASS_SUMMARY_SCRIPT), "pass_summary")
        write(addendum / "ledger.md", (
            "phase: plan approved\n"
            "dispatch 1 i3-A1 i3-A1-1 sheets A-0.04 purpose vocabulary\n"
            "verified 1 i3-A1 i3-A1-1 created 0 items 0 updated 1 questions 0 replied 0 sent 1 "
            "landed 1 conflicts 0 result ok\n"
        ))
        code, out, err = _run_script_main(
            summary_module,
            [str(addendum / "ledger.md"), "1", "i3-A1", "--plan", str(addendum / "read-plan-w1.md"),
             "--trades", str(addendum / "trades" / "i3-A1.txt")],
        )
        if code != 0 or "08 50 00" in out:
            errors.append(f"the summary script does not read past a touched line, or sums it as created: exited {code}, {err or out[:200]}")
        (addendum / "ledger.md").unlink(missing_ok=True)
    except Exception as e:
        errors.append(f"the summary script over a touched line: {e}")
    shutil.rmtree(addendum / "trades", ignore_errors=True)
    refused(["plan", "--window", "3", "--packages", str(packages), "--out", str(addendum / "read-plan-w3.md")],
            "window 3 of an addendum's pass with no trades files", "trades")
    # A set's pass reviews every package, whatever its trades files say.
    write(first / "trades" / "i1-A1.txt", "i1-A1-1 trade 09 21 16 4\n")
    code, bounds, err, text = review_plan(first)
    if code != 0 or len(_issue_ids(text)[1]) != 8:
        errors.append(f"window 3 of a set's pass does not review all eight packages: {err or bounds}")
    shutil.rmtree(first / "trades", ignore_errors=True)

    # ------------------------------------------------------------------ #
    # The text the lead and the reader follow
    # ------------------------------------------------------------------ #
    skill_path = plugin_path / "skills" / "scope-run" / "SKILL.md"
    reader_path = plugin_path / "agents" / "scope-reader.md"
    try:
        skill = skill_path.read_text(encoding="utf-8")
        reader = reader_path.read_text(encoding="utf-8")
    except Exception as e:
        return Result(name, False, detail=f"cannot read the skill or the reader: {e}")
    reader_flat = " ".join(reader.split())
    skill_flat = " ".join(skill.split())

    # The lead's own command, fed to the script's arguments.
    # Both fences sit inside a list item, so they may be indented.
    command = re.search(r"python3 '<plugin root>/scripts/plan_inventory\.py' issue\b([^`]*?)\n *```", skill)
    if command is None:
        errors.append("the skill carries no fenced `plan_inventory.py' issue` command")
    else:
        lead_runs = root / "choose" / "lead-command"
        shutil.rmtree(lead_runs, ignore_errors=True)
        write(lead_runs / "deliveries.json", {"count": len(deliveries), "deliveries": deliveries})
        tail = command.group(1).replace("\\\n", " ").replace("<project folder>", str(lead_runs).replace("\\", "/"))
        try:
            argv = ["issue", *shlex.split(tail)]
        except ValueError as e:
            argv = []
            errors.append(f"the skill's issue command does not split as a shell line: {e}")
        if argv:
            code, out, err = run(argv)
            if code != 0 or not out.startswith("start deliv-d3"):
                errors.append(f"the skill's own issue command, run as written, exited {code}: {out or err}")

    # The run.json the skill shows is one the script accepts.
    shown = re.search(r"```json\n( *\{[^`]*?\"unitTag\"[^`]*?\})\n *```", skill)
    if shown is None:
        errors.append("the skill shows no run.json in a fenced json block")
    else:
        try:
            example = json.loads(shown.group(1))
            folder = root / "shown-run"
            write(folder / "run.json", example)
            module._read_run(folder)
        except Exception as e:
            errors.append(f"the run.json the skill shows is refused by the script: {e}")

    for phrase, where in (
        ('set_grid(projectId: "<projectId>", deliveryId: "<deliveryId>", limit: 500, offset: 0)', "the grid fetch"),
        ("set_grid(projectId, deliveryId, limit: 0)", "the shape call"),
        ("`scopeItem:<unit tag>-`", "the tag check"),
        ("These are the only `set_grid` calls the run makes", "list of the set_grid calls it permits"),
        ("the first sheet the inventory's bounds line names", "corpus probe"),
        ("the earlier run did not record which set it read", "read plan check-in after a pass in the old layout"),
    ):
        if phrase not in skill_flat:
            errors.append(f"the skill's {where} does not read {phrase!r}")
    # A summary-only call carries no rows, so no sheet number can be read off it, and a second
    # sentence calling one call the only one would contradict the list of the calls permitted.
    for phrase in ("set_grid's limit: 0 summary", "This is the only `set_grid` call you make"):
        if phrase in skill_flat:
            errors.append(f"the skill still reads {phrase!r}")
    paragraphs = [" ".join(p.split()) for p in re.split(r"\n\s*\n", skill)]
    if not any("`deliveries.json`, the delivery list" in p and "Audience: machine" in p for p in paragraphs):
        errors.append("the skill names deliveries.json with no `Audience: machine` clause beside it")
    for phrase in (
        '{ subject, kind: "sheet", sheet, pageInPdf, fileId }',
        "`{ sheet, pageInPdf, fileId }`",
        "`citesThisPage`",
        # The answer leaves the sheet number null on a replaced page, and every row then reads
        # false, so false alone does not say the row lacks this page.
        "every row reads `citesThisPage: false` whatever it cites",
        "a row is updated only where a write of yours landed on it",
        "and the `fileId` your dispatch names for that page, so the pin lands",
    ):
        if phrase not in reader_flat:
            errors.append(f"the reader does not document {phrase!r}")
    if '{ subject, kind: "sheet", sheet, pageInPdf }' in reader_flat:
        errors.append("the reader still documents a sheet citation with no fileId")

    # A search of the current set finds a later issue's page in place of the pass's own once that
    # issue lands, so the reader searches each delivery its pass reads from and keeps a hit only on
    # a page its inventory carries; the line it matches is the shape inventory.md really writes.
    # And a row's citations of a page are its live ones, the projected `drawingRefs`, since the raw
    # record also carries superseded fields and removed citations.
    for phrase in (
        "search with `deliveryId` set to each of them in turn",
        "ending `| <the hit's fileId> | <the hit's page>`",
        'list_scope_items(subjectPrefix: "<subject>", full: true)',
        "its `drawingRefs`, the live citations",
    ):
        if phrase not in reader_flat:
            errors.append(f"the reader does not document {phrase!r}")
    if 'read its citations with `search(subject: "<subject>", full: true)`' in reader_flat:
        errors.append("the reader still reads a row's citations off the raw record")
    try:
        inventory_lines = (first / "inventory.md").read_text(encoding="utf-8").splitlines()
    except Exception as e:
        inventory_lines = []
        errors.append(f"the first set's inventory.md: {e}")
    first_row = rows[0]
    if not any(
        line.startswith(f"{first_row['discipline']} | {first_row['sheetNumber']} | ")
        and line.endswith(f"| {first_row['fileId']} | {first_row['pageInPdf']}")
        for line in inventory_lines
    ):
        errors.append(
            f"inventory.md carries no sheet line for {first_row['sheetNumber']} ending "
            f"`| {first_row['fileId']} | {first_row['pageInPdf']}`, the shape the reader matches a hit by"
        )

    # The runner checks a unit's sheets on the drawing file the unit read them on, so an earlier
    # issue's citation of the same sheet never stands in for one on this page. The sheet shape it
    # sends is the one verify_unit takes: an object of exactly `sheet` and `fileId`, or a number.
    try:
        runner_flat = " ".join((plugin_path / "agents" / "scope-round-runner.md").read_text(encoding="utf-8").split())
    except Exception as e:
        return Result(name, False, detail=f"cannot read the runner: {e}")
    sheet_shape = '{ "sheet": "<sheet number>", "fileId": "<fileId>" }'
    if sheet_shape not in runner_flat:
        errors.append(f"the runner does not send verify_unit a sheet as {sheet_shape}")
    elif set(json.loads(sheet_shape)) != {"sheet", "fileId"}:
        errors.append("the runner's sheet shape is not the sheet and fileId verify_unit takes")
    for phrase, where in (
        ("each with the `fileId` its unit line names", "repeated lines unit"),
        ("as the sheet number alone", "sheet with no file"),
    ):
        if phrase not in runner_flat:
            errors.append(f"the runner's {where} does not read {phrase!r}")
    if "sheets: [<the unit's sheet numbers>]" in runner_flat:
        errors.append("the runner still verifies a unit by its sheet numbers alone")

    # An addendum's pass, in the text that drives it: the lead's partial pass, the reviewer searching
    # the pass's own deliveries and naming the file it opened, the runner checking a review on that
    # file, and drawing-upload taking set or addendum from the server rather than asking.
    try:
        reviewer_flat = " ".join((plugin_path / "agents" / "scope-reviewer.md").read_text(encoding="utf-8").split())
        upload_flat = " ".join((plugin_path / "skills" / "drawing-upload" / "SKILL.md").read_text(encoding="utf-8").split())
    except Exception as e:
        return Result(name, False, detail=f"cannot read the reviewer or drawing-upload: {e}")
    opened_shape = "pages opened: <sheet number + fileId + page + the term that sent you + what you did"
    for flat, who, phrase in (
        (skill_flat, "the skill", "a partial pass over the sheets it prints"),
        (skill_flat, "the skill", "the index after each window that ran"),
        (skill_flat, "the skill", "`phase: window 1 skipped`"),
        (skill_flat, "the skill", "`plan/packages-start.json`"),
        (skill_flat, "the skill's copy of the reviewer report", opened_shape.replace("you did", "it did").replace("sent you", "sent it")),
        (reviewer_flat, "the reviewer", "with `deliveryId` set to each delivery its `readFrom` names"),
        (reviewer_flat, "the reviewer", "carries the hit's `fileId`"),
        (reviewer_flat, "the reviewer", opened_shape),
        (runner_flat, "the runner", "with the `fileId` the reviewer's line names for it"),
        (runner_flat, "the runner", "`<unit id> touched <catalog id>`"),
        (reader_flat, "the reader", "trades touched: <the catalog id of every pre-existing row you updated or newly cited, and of every trade a Question you raised names"),
        (skill_flat, "the skill's copy of the reader report", "trades touched: <the catalog id of every pre-existing row the reader updated or newly cited, and of every trade a Question it raised names"),
        (upload_flat, "drawing-upload", "You never ask the user whether a delivery is a new set or an addendum"),
        (upload_flat, "drawing-upload", "a partial scope pass over the sheets it prints"),
        # A drawing search by delivery counts only that delivery's files, and a manual uploaded on
        # its own sits in none of them, so the manual is asked on its own before it is called silent.
        (reviewer_flat, "the reviewer", "run one `kind: document` search for the same words with no `deliveryId`"),
        # Step 9b reads the uploaded delivery's own sheets and cites them on its own file.
        (upload_flat, "drawing-upload", "`set_grid(projectId, deliveryId: <this delivery's id>, limit: 0)`"),
        (upload_flat, "drawing-upload", "`search_set_text` its tag with `deliveryId` set to this delivery"),
        (upload_flat, "drawing-upload", "with this delivery's `fileId`"),
        (upload_flat, "drawing-upload", "Keep every existing source"),
        # The handoff on the two paths with no scope pass to name.
        (upload_flat, "drawing-upload", "No scope pass reads a project manual on its own"),
        (upload_flat, "drawing-upload", "holds no sheet number"),
        # A set's grid by delivery carries a sheet one of its addenda reprinted as the addendum's
        # row, so the set's own page of it is found inside the set by a delivery-scoped search.
        (upload_flat, "drawing-upload", "A row from one of its addenda is a sheet the addendum reprinted or added"),
        (upload_flat, "drawing-upload", "`search_set_text(projectId, query: \"<sheet number>\", deliveryId: <this delivery's id>, wholeWord: true)`"),
        # set_grid refuses a delivery holding no sheet number, so step 9b skips the grid read.
        (upload_flat, "drawing-upload", "`set_grid` refuses it and no sheet is known to have changed, so skip the rest of this step"),
    ):
        if phrase not in flat:
            errors.append(f"{who} does not read {phrase!r}")
    for phrase in (
        "is this a set of changed sheets, or a full re-issue of the whole set?",
        "is not available yet",
        "A sheet citation names the sheet, not the file",
        # The filter that dropped a set's sheet an addendum of it reprinted.
        "for a new set its own sheets, not those an addendum of it already reprints",
    ):
        if phrase in upload_flat:
            errors.append(f"drawing-upload still reads {phrase!r}")

    shutil.rmtree(root / "choose", ignore_errors=True)
    detail = (
        f"two sets of one project and the old layout planned over the 39-sheet fixture, every unit "
        f"id of a pass tagged with its own unit tag, numbered from 1 in each part, none a prefix of "
        f"another pass's ({len(prefixes)} subject prefixes compared), a tagged replan keeping a "
        f"dispatched id and retiring a cut one, and the summary script summing a tagged pass; "
        f"{refusals} refusals each one line naming what is "
        f"wrong (a tag taken, on the record, unchecked, misshapen or counted under another prefix, "
        f"a second folder for one issue, a row from another issue, a grid fetched after a later "
        f"delivery, short of one, for another issue or for the current set, an inventory of "
        f"another issue, other deliveries or none, window 2 under another tag than window 1's, "
        f"window 3 in a pass folder that lost its run.json, two passes in flight, a stray ledger, "
        f"a bad listing, a stillReading that is not true or false), another pass's broken run.json "
        f"never stopping a plan; the pass chosen over 14 project folders (a pass in flight resumed "
        f"before any other and before the listing is read, the old layout resumed, a closed pass "
        f"never resumed and only an exact close-out line closing one, the latest set started with "
        f"the next tag and a closed old layout pass named on the line, a delivery still being read "
        f"waited on, an addendum after its set's pass started, earliest first); an addendum's "
        f"pass reading its own sheets only, its revised schedule in window 1, an empty window 1 "
        f"where it prints no vocabulary, and a window 3 reviewing only the packages its trades "
        f"files name, naming the rest, none where it wrote no row, refused with no trades folder; "
        f"the "
        f"skill's issue command and run.json fed to the script, its grid fetch by delivery, and the "
        f"reader's citations naming the drawing file; bound: invented grids and listings, not a "
        f"real set_grid or list_drawing_deliveries answer"
    )
    if errors:
        detail += " | " + "; ".join(errors)
    return Result(name, passed=not errors, detail=detail)


# --------------------------------------------------------------------------- #
# Check: the runner copies each worker's anomalies onto the ledger
# --------------------------------------------------------------------------- #
#
# pass_summary.py builds the summary's `anomalies:` line from the ledger's `anomaly` notes alone,
# and the close-out names the same work pairs off those notes. The runner once carried the note
# kind and a worked example and no step telling it to write one, so every summary's anomalies line
# could come back empty with every other check passing. The check holds the step itself, not only
# its words: the append sentence in pass mode, which review mode inherits, placed before the
# `verified` line so that line still means the unit is complete, and no sentence there that
# negates an append of the notes; and in the ledger rule, the one exception to its ban on
# re-telling a report, without which the ban forbids the notes, and the exemption from the
# 200-character clause, without which a long line is cut.

_ANOMALY_ACTION_PHRASE = (
    "Append the unit's `anomaly` notes first: one `note <window> <pass> <unit> anomaly <the line>` "
    "per line on the report's `anomalies:` line"
)
_ANOMALY_COPY_PHRASES = (
    _ANOMALY_ACTION_PHRASE,
    "each copied whole",
    "review mode copies the reviewer's line the same way",
)
_ANOMALY_VERIFIED_PHRASE = "Then append the unit's `verified` line"
_ANOMALY_NEGATION_RE = re.compile(
    r"\b(?:never|not|don't|no longer)\s+(?:\w+\s+){0,2}append\b[^.]{0,120}\banomaly\b", re.IGNORECASE
)
_ANOMALY_LEDGER_PHRASES = (
    "An `anomaly` note is the one exception, a line of the report copied whole",
    "An `anomaly` note is exempt from that limit",
)


def _runner_section(text: str, heading: str) -> str | None:
    """One `##` section of the runner, whitespace collapsed, or None where it is absent."""
    parts = text.split(f"\n## {heading}\n", 1)
    if len(parts) < 2:
        return None
    return " ".join(parts[1].split("\n## ", 1)[0].split())


def _anomaly_copy_errors(pass_mode: str | None, ledger_rule: str | None) -> list[str]:
    errors: list[str] = []
    if pass_mode is None:
        errors.append("scope-round-runner.md has no `## Pass mode` section")
    else:
        for phrase in _ANOMALY_COPY_PHRASES:
            if phrase not in pass_mode:
                errors.append(
                    f"the runner's pass mode does not carry {phrase!r}, so no step copies a "
                    f"report's `anomalies:` lines onto the ledger as `anomaly` notes"
                )
        action_at = pass_mode.find(_ANOMALY_ACTION_PHRASE)
        verified_at = pass_mode.find(_ANOMALY_VERIFIED_PHRASE)
        if action_at >= 0 and (verified_at < 0 or verified_at < action_at):
            errors.append(
                f"the runner's pass mode does not append the `anomaly` notes before "
                f"{_ANOMALY_VERIFIED_PHRASE!r}, so a `verified` line can stand for a unit whose "
                f"notes never landed"
            )
        negation = _ANOMALY_NEGATION_RE.search(pass_mode)
        if negation:
            errors.append(
                f"the runner's pass mode carries {negation.group(0)!r}, which negates the append "
                f"of the `anomaly` notes"
            )
    if ledger_rule is None:
        errors.append("scope-round-runner.md has no `## The ledger lines` section")
    else:
        for phrase in _ANOMALY_LEDGER_PHRASES:
            if phrase not in ledger_rule:
                errors.append(
                    f"the runner's ledger rule does not carry {phrase!r}, so its ban on re-telling "
                    f"a report or its 200-character clause keeps an anomaly line off the ledger "
                    f"whole"
                )
    return errors


def check_anomaly_notes(plugin_path: Path) -> Result:
    name = "anomaly-notes-copied"
    runner = plugin_path / "agents" / "scope-round-runner.md"
    if not runner.is_file():
        return Result(name, False, detail=f"not found: {runner}")
    text = runner.read_text(encoding="utf-8")
    pass_mode = _runner_section(text, "Pass mode")
    ledger_rule = _runner_section(text, "The ledger lines")
    errors = _anomaly_copy_errors(pass_mode, ledger_rule)

    # The helper is run over the shipped text with each guarded part taken out, the action negated
    # and the order reversed, so every refusal is shown rather than assumed.
    mutations: list[tuple[str, str, str]] = []
    if pass_mode is not None and ledger_rule is not None and not errors:
        for phrase in _ANOMALY_COPY_PHRASES:
            mutations.append((f"pass mode with {phrase!r} taken out", pass_mode.replace(phrase, ""), ledger_rule))
        mutations.append((
            "pass mode with the append negated",
            pass_mode.replace(_ANOMALY_ACTION_PHRASE, "Never a" + _ANOMALY_ACTION_PHRASE[1:]),
            ledger_rule,
        ))
        mutations.append((
            "pass mode with the `verified` line appended before the notes",
            pass_mode.replace(_ANOMALY_VERIFIED_PHRASE, "").replace(
                _ANOMALY_ACTION_PHRASE, _ANOMALY_VERIFIED_PHRASE + ". " + _ANOMALY_ACTION_PHRASE
            ),
            ledger_rule,
        ))
        for phrase in _ANOMALY_LEDGER_PHRASES:
            mutations.append((f"the ledger rule with {phrase!r} taken out", pass_mode, ledger_rule.replace(phrase, "")))
        for label, mutated_pass, mutated_ledger in mutations:
            if not _anomaly_copy_errors(mutated_pass, mutated_ledger):
                errors.append(f"the check passed {label}")

    detail = (
        f"the runner's pass mode appends each `anomalies:` line as an `anomaly` note before the "
        f"`verified` line, review mode's included, with no sentence negating it, and its ledger "
        f"rule carries the one exception and the exemption from the 200-character clause; "
        f"{len(mutations)} mutations refused; bound: text only, not whether a runner writes the notes"
    )
    if errors:
        detail += " | " + "; ".join(errors)
    return Result(name, passed=not errors, detail=detail)


# --------------------------------------------------------------------------- #
# Check: pages one number prints twice
# --------------------------------------------------------------------------- #
#
# A drawing issue can print one sheet number on two of its pages. `set_grid` gives the number one
# row, on its first page, and lists every page it prints on under the row's `pageOccurrences`: the
# row's own page with `selected: true`, each further page of the row's own delivery with
# `selected: false`, `deliveryId: null` and the key it opens as, and a page an earlier issue printed
# that the current set keeps beside them, with that issue's `deliveryId`. The plan script once made
# one unit per grid row, so a further page was never read and nothing said so. This runs the
# shipped script over an invented grid holding both kinds of page.
#
# What can fail, one case each below:
#   1. a further page gets no inventory row, or its counts, its place right after its number's row,
#      its fields, or `--expect-count` held against the grid's rows come out wrong;
#   2. a further page takes its number's sheet type rather than its own, so a schedule printed on
#      the second page of a plan's number reads in the wrong window;
#   3. its plan line drops the file or the key it opens as;
#   4. a replan moves the id a dispatch line bound to it under the key it opens as, or an old
#      ledger naming the number stops binding the number's own page;
#   5. `--exclude` on the number leaves one page in, or the repeated lines unit names the further
#      page by the number;
#   6. a page of an earlier issue gets a unit, or is dropped with nothing said;
#   7. a page list that is missing or malformed is planned rather than refused;
#   8. the runner's own dispatch line for a further page does not bind through the ledger reader.
#
# Honest bound: the grids are invented and built here, so this proves the script's expansion, its
# counts, its binding and its refusals, not how a real `set_grid` answer arrives.

_SHARED_FILE = "file-0001"
_SHARED_EARLIER_FILE = "file-0000"
# A plan unit line: id, number, the file where shown, the page, the key a further page opens as.
_SHARED_UNIT_RE = re.compile(
    r"^(\S+)\. (\S+), (?:file (\S+), )?page (\d+)(?:, opens as (\S+))?: (.*?)( verified)?$"
)
_SHARED_DISPATCH_RE = re.compile(
    r"^dispatch ([12]) (\S+) (\S+-[1-9][0-9]*) sheets (\S+-p[0-9]+) purpose \S.*$"
)


def _shared_occurrence(
    file_id: str, page: int, opens_as: str | None, title: str | None, sheet_type: str | None,
    selected: bool = False, delivery_id: str | None = None,
) -> dict:
    """One `pageOccurrences` entry in the shape `set_grid` gives it."""
    return {
        "fileId": file_id, "pdfFile": f"{file_id}.pdf", "pageInPdf": page, "title": title,
        "selected": selected, "opensAs": opens_as, "sheetType": sheet_type,
        "deliveryId": delivery_id,
        "deliveryLabel": None if delivery_id is None else f"Label of {delivery_id}",
    }


def _shared_key(file_id: str, page: int) -> str:
    """The key a page opens as, `<fileId>-p<page>`, padded to three digits as the api pads it."""
    return f"{file_id}-p{page:03d}" if page <= 999 else f"{file_id}-p{page}"


def _shared_row(
    discipline: str, number: str, sheet_type: str, page: int, title: str,
    further: tuple = (), carried: tuple = (), file_id: str = _SHARED_FILE,
) -> dict:
    """
    One grid row. `further` holds (page, title, sheet type) for each further page of the row's own
    delivery, and `carried` holds (file, page) for each page an earlier issue printed.
    """
    occurrences: list[dict] = []
    if further or carried:
        occurrences.append(_shared_occurrence(file_id, page, number, title, sheet_type, selected=True))
        for further_page, further_title, further_type in further:
            occurrences.append(
                _shared_occurrence(
                    file_id, further_page, _shared_key(file_id, further_page), further_title, further_type
                )
            )
        for carried_file, carried_page in carried:
            occurrences.append(
                _shared_occurrence(
                    carried_file, carried_page, _shared_key(carried_file, carried_page), title,
                    sheet_type, delivery_id="deliv-s0",
                )
            )
    return {
        "discipline": discipline, "sheetNumber": number, "pageTitle": title,
        "sheetType": sheet_type, "fileId": file_id, "pageInPdf": page,
        "pageOccurrences": occurrences,
    }


def _shared_units(text: str) -> list[tuple]:
    """Every unit line of a read plan's passes, ahead of the left-out section."""
    units: list[tuple] = []
    for line in text.split(_LEFT_OUT_HEADING, 1)[0].splitlines():
        m = _SHARED_UNIT_RE.match(line)
        if m:
            units.append(m.groups())
    return units


def check_shared_number_pages(plugin_path: Path, marketplace_root: Path) -> Result:
    name = "pages-one-number-prints-twice"
    script = plugin_path.joinpath(*PLAN_INVENTORY_SCRIPT)
    runner_path = plugin_path / "agents" / "scope-round-runner.md"
    reader_path = plugin_path / "agents" / "scope-reader.md"
    for path in (script, runner_path, reader_path):
        if not path.is_file():
            return Result(name, False, detail=f"not found: {path}")
    try:
        module = _load_script_module(script, "plan_inventory")
    except Exception as e:
        return Result(name, False, detail=f"cannot import {script.name}: {e}")

    root = Path(__file__).parent / ".test-results" / "shared-number-pages"
    shutil.rmtree(root, ignore_errors=True)
    errors: list[str] = []
    refusals = 0

    def run(argv: list[str]) -> tuple[int, str, str]:
        try:
            return _run_script_main(module, argv)
        except SystemExit as e:
            return int(e.code or 0), "", "argparse exit"
        except Exception as e:
            return 99, "", f"raised {type(e).__name__}: {e}"

    def write_grid(folder: Path, rows: list[dict]) -> Path:
        folder.mkdir(parents=True, exist_ok=True)
        path = folder / "grid.json"
        path.write_text(
            json.dumps({"count": len(rows), "offset": 0, "sheets": rows}, indent=2) + "\n",
            encoding="utf-8",
        )
        return path

    def inventory(folder: Path, rows: list[dict], expect: int | None = None) -> tuple[int, str, str]:
        grid = write_grid(folder, rows)
        count = len(rows) if expect is None else expect
        return run(["inventory", "--grid", str(grid), "--expect-count", str(count), "--out-dir", str(folder)])

    def plan(folder: Path, window: int, inventory_path: Path, *extra: str) -> tuple[int, str, str, str]:
        out = folder / "read-plan.md"
        argv = ["plan", "--window", str(window), "--inventory", str(inventory_path), *extra, "--out", str(out)]
        code, bounds, err = run(argv)
        text = out.read_text(encoding="utf-8") if code == 0 and out.is_file() else ""
        if code != 0:
            errors.append(f"{folder.name}: window {window} refused: {err or bounds}")
        return code, bounds, err, text

    # The set: one file, so a sheet line names its file only where it is a further page. C-5.02
    # prints a detail on a further page, C-7.01 a schedule on the further page of a plan, and C-2.01
    # carries a page an earlier issue printed.
    rows = [
        _shared_row("A", "A-1.01", "plan", 1, "FIRST FLOOR PLAN"),
        _shared_row("A", "A-6.01", "schedule", 2, "DOOR SCHEDULE"),
        _shared_row("C", "C-5.02", "detail", 3, "SITE DETAILS", further=((4, "SITE DETAILS CONTINUED", "detail"),)),
        _shared_row("C", "C-1.01", "plan", 5, "SITE PLAN"),
        _shared_row("C", "C-7.01", "plan", 6, "PAVING PLAN", further=((7, "PAVING SCHEDULE", "schedule"),)),
        _shared_row("C", "C-2.01", "plan", 8, "GRADING PLAN", carried=((_SHARED_EARLIER_FILE, 8),)),
        _shared_row("A", "A-2.01", "plan", 9, "SECOND FLOOR PLAN"),
    ]
    p4_key, p7_key = _shared_key(_SHARED_FILE, 4), _shared_key(_SHARED_FILE, 7)
    key = {
        "A-1.01": f"A-1.01@{_SHARED_FILE}#1", "A-6.01": f"A-6.01@{_SHARED_FILE}#2",
        "C-5.02": f"C-5.02@{_SHARED_FILE}#3", "C-5.02 p4": f"C-5.02@{_SHARED_FILE}#4",
        "C-1.01": f"C-1.01@{_SHARED_FILE}#5", "C-7.01": f"C-7.01@{_SHARED_FILE}#6",
        "C-7.01 p7": f"C-7.01@{_SHARED_FILE}#7", "C-2.01": f"C-2.01@{_SHARED_FILE}#8",
        "A-2.01": f"A-2.01@{_SHARED_FILE}#9",
    }
    inventory_order = list(key.values())
    set_dir = root / "set"
    inventory_path = set_dir / "inventory.json"

    # --- 1: the further pages are sheets of their own, counted and placed --- #
    code, bounds, err = inventory(set_dir, rows)
    sheets: list[dict] = []
    if code != 0:
        return Result(name, False, detail=f"the inventory refused the shared number grid: {err or bounds}")
    try:
        written = json.loads(inventory_path.read_text(encoding="utf-8"))
        sheets = written["sheets"]
    except Exception as e:
        return Result(name, False, detail=f"inventory.json: {e}")
    counts = written.get("counts", {})
    if (counts.get("rows"), counts.get("furtherPages"), counts.get("sheets")) != (7, 2, 9):
        errors.append(
            f"counts read rows {counts.get('rows')}, further pages {counts.get('furtherPages')}, "
            f"sheets {counts.get('sheets')}, expected 7 grid rows, 2 further pages and 9 sheets"
        )
    if [s.get("unitKey") for s in sheets] != inventory_order:
        errors.append(
            f"the inventory reads {[s.get('unitKey') for s in sheets]}, expected each further page "
            f"right after its number's row: {inventory_order}"
        )
    by_key = {s.get("unitKey"): s for s in sheets}
    for label, want in (
        ("C-5.02 p4", {"discipline": "C", "sheetNumber": "C-5.02", "pageTitle": "SITE DETAILS CONTINUED",
                       "sheetType": "detail", "fileId": _SHARED_FILE, "pageInPdf": 4, "opensAs": p4_key}),
        ("C-7.01 p7", {"discipline": "C", "sheetNumber": "C-7.01", "pageTitle": "PAVING SCHEDULE",
                       "sheetType": "schedule", "fileId": _SHARED_FILE, "pageInPdf": 7, "opensAs": p7_key}),
    ):
        got = {field: by_key.get(key[label], {}).get(field) for field in want}
        if got != want:
            errors.append(f"the further page {label} reads {got}, expected {want}")
    not_null = [
        s.get("unitKey") for s in sheets
        if s.get("unitKey") not in (key["C-5.02 p4"], key["C-7.01 p7"])
        and ("opensAs" not in s or s["opensAs"] is not None)
    ]
    if not_null:
        errors.append(f"these inventory rows are no further page and carry no `opensAs` of null: {not_null}")
    for fragment in (
        "7 rows from 1 grid file",
        "2 further pages of a number printed on more than one page (C-5.02 page 4; C-7.01 page 7)",
        "1 page of an earlier issue left out (C-2.01 page 8 of delivery deliv-s0)",
        "9 sheets to read",
    ):
        if fragment not in bounds:
            errors.append(f"the inventory bounds line does not name `{fragment}`: {bounds!r}")
    md = (set_dir / "inventory.md").read_text(encoding="utf-8")
    if f"C | C-5.02 | SITE DETAILS CONTINUED | detail | {_SHARED_FILE} | 4" not in md.splitlines():
        errors.append("inventory.md carries no sheet line for C-5.02's further page ending in its file and page")
    table = md.split("## Sheets by discipline\n", 1)[-1].split("\n## ", 1)[0].splitlines()
    for want_line in (
        "C | 6 | not reported",
        "total | 9 |",
        "The counts take each further page of a number printed on more than one page as a sheet of its own: 2 further pages.",
    ):
        if want_line not in table:
            errors.append(f"inventory.md's sheets by discipline table does not carry `{want_line}`")
    code, _bounds, err = inventory(root / "expect-sheets", rows, expect=9)
    if code != 1 or len(err.splitlines()) != 1 or "--expect-count says 9" not in err:
        errors.append(
            f"--expect-count 9, the sheets with the further pages, exited {code} with {err!r}; it "
            f"holds against the grid's 7 rows"
        )

    # --- 2: the schedule printed on a plan's further page reads in window 1 --- #
    w1_dir = set_dir
    code, w1_bounds, _err, w1_text = plan(w1_dir, 1, inventory_path)
    w1_units = _shared_units(w1_text)
    try:
        window_1 = json.loads((w1_dir / "plan" / "window-1.json").read_text(encoding="utf-8"))
    except Exception as e:
        window_1 = {}
        errors.append(f"window-1.json: {e}")
    if set(window_1.get("selected", [])) != {key["A-6.01"], key["C-7.01 p7"]}:
        errors.append(
            f"window 1 selected {window_1.get('selected')}, expected the door schedule and the "
            f"schedule on C-7.01's further page, and never C-7.01's own page"
        )
    w2_dir = root / "window-2"
    w2_dir.mkdir(parents=True, exist_ok=True)
    window_1_path = w1_dir / "plan" / "window-1.json"
    code, w2_bounds, _err, w2_text = plan(w2_dir, 2, inventory_path, "--window-1", str(window_1_path))
    w2_units = _shared_units(w2_text)
    w2_keys = {f"{u[1]}@{u[2] or _SHARED_FILE}#{u[3]}" for u in w2_units}
    want_w2 = set(inventory_order) - {key["A-6.01"], key["C-7.01 p7"]}
    if w2_keys != want_w2 or len(w2_units) != len(want_w2):
        errors.append(f"window 2 reads {sorted(w2_keys)} over {len(w2_units)} lines, expected {sorted(want_w2)}")
    if "every sheet once (units 7 equals distinct sheets 7)" not in w2_bounds:
        errors.append(f"the window 2 bounds line does not state its partition over 7 sheets: {w2_bounds!r}")

    # --- 3: a further page's line names its file and the key it opens as --- #
    w2_lines = w2_text.splitlines()
    for want_line in (
        "C2-1. C-5.02, page 3: SITE DETAILS",
        f"C2-2. C-5.02, file {_SHARED_FILE}, page 4, opens as {p4_key}: SITE DETAILS CONTINUED",
    ):
        if want_line not in w2_lines:
            errors.append(f"window 2 carries no line `{want_line}`")
    if f"C1-1. C-7.01, file {_SHARED_FILE}, page 7, opens as {p7_key}: PAVING SCHEDULE" not in w1_text.splitlines():
        errors.append("window 1 carries no line naming C-7.01's further page with its file and the key it opens as")

    # --- 4: a replan binds a further page by the key it opens as --- #
    for case, ledger_lines, want_lines, fragment in (
        (
            "replan-by-key",
            [f"dispatch 2 C2 C2-4 sheets {p4_key} purpose further page of a shared number",
             "dispatch 2 C2 C2-2 sheets C-5.02 purpose site details"],
            ["C2-2. C-5.02, page 3: SITE DETAILS",
             f"C2-4. C-5.02, file {_SHARED_FILE}, page 4, opens as {p4_key}: SITE DETAILS CONTINUED"],
            "ids kept 2 (ledger 2, plan file 0)",
        ),
        (
            "replan-old-ledger",
            ["dispatch 2 C2 C2-3 sheets C-5.02 purpose site details"],
            ["C2-3. C-5.02, page 3: SITE DETAILS",
             f"C2-4. C-5.02, file {_SHARED_FILE}, page 4, opens as {p4_key}: SITE DETAILS CONTINUED"],
            "ids kept 1 (ledger 1, plan file 0)",
        ),
    ):
        folder = root / case
        folder.mkdir(parents=True, exist_ok=True)
        (folder / "ledger.md").write_text("\n".join(["phase: plan approved", *ledger_lines]) + "\n", encoding="utf-8")
        code, replan_bounds, _err, replan_text = plan(folder, 2, inventory_path, "--window-1", str(window_1_path))
        for want_line in want_lines:
            if code == 0 and want_line not in replan_text.splitlines():
                errors.append(f"{case}: the replan carries no line `{want_line}`")
        if code == 0 and fragment not in replan_bounds:
            errors.append(f"{case}: the bounds line does not name `{fragment}`: {replan_bounds!r}")

    # --- 5: leaving out the number leaves out both its pages --- #
    excl_dir = root / "exclude"
    excl_dir.mkdir(parents=True, exist_ok=True)
    code, _bounds, _err, excl_text = plan(
        excl_dir, 1, inventory_path, "--exclude", "C-5.02:the user left the site details out"
    )
    try:
        excl_window_1 = json.loads((excl_dir / "plan" / "window-1.json").read_text(encoding="utf-8"))
    except Exception as e:
        excl_window_1 = {}
        errors.append(f"the exclude case's window-1.json: {e}")
    if excl_window_1.get("excluded") != [key["C-5.02"], key["C-5.02 p4"]]:
        errors.append(f"--exclude C-5.02 left out {excl_window_1.get('excluded')}, expected both of its pages")
    left_out = excl_text.split(_LEFT_OUT_HEADING, 1)[-1].splitlines()
    for want_line in (
        "1. C-5.02, page 3: SITE DETAILS",
        f"2. C-5.02, file {_SHARED_FILE}, page 4, opens as {p4_key}: SITE DETAILS CONTINUED",
    ):
        if want_line not in left_out:
            errors.append(f"the exclude case's left out section carries no line `{want_line}`")
    repeated_sets = excl_window_1.get("repeatedSets") or [{}]
    if repeated_sets[0].get("sheetsLeftOut") != ["C-5.02", p4_key]:
        errors.append(
            f"the repeated lines unit names {repeated_sets[0].get('sheetsLeftOut')} left out, expected "
            f"C-5.02 and its further page by the key it opens as"
        )
    if f"RS1-1. file {_SHARED_FILE}, from page 1: repeated lines, sheets left out C-5.02, {p4_key}" not in excl_text.splitlines():
        errors.append("the exclude case's repeated lines unit line does not name both pages left out")
    excl_w2_dir = root / "exclude-window-2"
    excl_w2_dir.mkdir(parents=True, exist_ok=True)
    code, _bounds, _err, excl_w2_text = plan(
        excl_w2_dir, 2, inventory_path, "--window-1", str(excl_dir / "plan" / "window-1.json")
    )
    if any(u[1] == "C-5.02" for u in _shared_units(excl_w2_text)):
        errors.append("window 2 after --exclude C-5.02 still plans a page of C-5.02")

    # --- 9: a window 1 file an earlier plugin wrote keeps its number left out whole --- #
    # A run resumed on a newer plugin can hold a window 1 file written when the number had one unit
    # key; the further page the inventory now adds stays out with the number it printed.
    upgrade_dir = root / "upgrade-exclude"
    (upgrade_dir / "plan").mkdir(parents=True, exist_ok=True)
    old_window_1_path = upgrade_dir / "plan" / "window-1.json"
    old_window_1_path.write_text(
        json.dumps(dict(excl_window_1, excluded=[key["C-5.02"]]), indent=2) + "\n", encoding="utf-8"
    )
    code, upgrade_bounds, _err, upgrade_text = plan(
        upgrade_dir, 2, inventory_path, "--window-1", str(old_window_1_path)
    )
    if code == 0:
        if any(u[1] == "C-5.02" for u in _shared_units(upgrade_text)):
            errors.append("window 2 over an earlier window 1 file that left C-5.02 out plans its further page")
        for fragment in (
            "sheets window 1 left out 2",
            "further pages left out with their number 1 (C-5.02 page 4)",
        ):
            if fragment not in upgrade_bounds:
                errors.append(f"the upgraded window 2 bounds line does not name `{fragment}`: {upgrade_bounds!r}")

    # --- 10: a further page past twelve keeps the ids a dispatched pass already carries --- #
    # D had twelve sheets and D2-1 and D2-2 were dispatched; the further page makes thirteen, and the
    # dispatched part keeps its id, the page numbered in a part after it.
    grow_dir = root / "twelve-to-thirteen"
    grow_rows = [_shared_row("D", f"D-1.{n:02d}", "plan", n, f"PLAN {n}") for n in range(1, 12)]
    grow_rows.append(
        _shared_row("D", "D-1.12", "plan", 12, "PLAN 12", further=((13, "PLAN 12 CONTINUED", "plan"),))
    )
    code, _bounds, err = inventory(grow_dir, grow_rows)
    if code != 0:
        errors.append(f"the twelve to thirteen grid refused: {err}")
    else:
        grow_inventory = grow_dir / "inventory.json"
        grow_w1 = root / "twelve-to-thirteen-w1"
        grow_w1.mkdir(parents=True, exist_ok=True)
        plan(grow_w1, 1, grow_inventory)
        (grow_dir / "ledger.md").write_text(
            "phase: plan approved\n"
            + "".join(f"dispatch 2 D2 D2-{n} sheets D-1.{n:02d} purpose plan read whole\n" for n in (1, 2)),
            encoding="utf-8",
        )
        code, grow_bounds, _err, grow_text = plan(
            grow_dir, 2, grow_inventory, "--window-1", str(grow_w1 / "plan" / "window-1.json")
        )
        if code == 0:
            for want_line in (
                "D2-1. D-1.01, page 1: PLAN 1",
                "D2-2. D-1.02, page 2: PLAN 2",
                "D2-12. D-1.12, page 12: PLAN 12",
                f"D2b-1. D-1.12, file {_SHARED_FILE}, page 13, opens as {_shared_key(_SHARED_FILE, 13)}: PLAN 12 CONTINUED",
            ):
                if want_line not in grow_text.splitlines():
                    errors.append(f"the twelve to thirteen replan carries no line `{want_line}`")
            if "ids kept 2 (ledger 2, plan file 0)" not in grow_bounds:
                errors.append(f"the twelve to thirteen bounds line does not keep both dispatched ids: {grow_bounds!r}")

    # --- 6: a page of an earlier issue is named and left out --- #
    if any(s.get("fileId") == _SHARED_EARLIER_FILE for s in sheets):
        errors.append("the inventory holds the page an earlier issue printed as a sheet to read")
    if any(u[2] == _SHARED_EARLIER_FILE for u in w1_units + w2_units):
        errors.append("a plan reads the page an earlier issue printed")
    if any(line.endswith(f"| {_SHARED_EARLIER_FILE} | 8") for line in md.splitlines()):
        errors.append("inventory.md carries a sheet line for the page an earlier issue printed")

    # --- 7: a page list that is missing or malformed is refused --- #
    def refused(case: str, broken_rows: list[dict], needles: list[str]) -> None:
        nonlocal refusals
        refusals += 1
        code, out, err = inventory(root / "refusals" / case, broken_rows)
        if code != 1 or out or len(err.splitlines()) != 1:
            errors.append(f"{case}: exited {code} with stdout {out[:120]!r} and stderr {err[:160]!r}, not one refusal line")
            return
        missing = [needle for needle in needles if needle not in err]
        if missing:
            errors.append(f"{case}: refused without naming {missing}: {err[:240]}")

    def broken(occurrences: list[dict] | None, page: int = 3, number: str = "C-5.02") -> list[dict]:
        row = _shared_row("C", number, "detail", page, "SITE DETAILS")
        if occurrences is None:
            del row["pageOccurrences"]
        else:
            row["pageOccurrences"] = occurrences
        return [_shared_row("A", "A-1.01", "plan", 1, "FIRST FLOOR PLAN"), row]

    own = _shared_occurrence(_SHARED_FILE, 3, "C-5.02", "SITE DETAILS", "detail", selected=True)
    further = _shared_occurrence(_SHARED_FILE, 4, p4_key, "SITE DETAILS CONTINUED", "detail")
    refused("no-page-list", broken(None), ["C-5.02", "carries no `pageOccurrences`"])
    refused("no-own-page", broken([dict(own, selected=False), further]), ["C-5.02", "none of them as its own page"])
    refused("two-own-pages", broken([own, dict(further, selected=True)]), ["C-5.02", "2 of them as its own page"])
    refused(
        "own-page-elsewhere", broken([dict(own, pageInPdf=5), further]),
        ["C-5.02", "page 3", "names file file-0001, page 5 as its own page"],
    )
    refused("further-no-file", broken([own, dict(further, fileId=None)]), ["C-5.02", "with no file"])
    refused("further-no-key", broken([own, dict(further, opensAs=None)]), ["C-5.02", "with no key it opens as"])
    refused("further-no-page", broken([own, dict(further, pageInPdf=None)]), ["C-5.02", "with no page number"])
    refused("page-twice", broken([own, further, dict(further)]), ["C-5.02", "file file-0001, page 4 twice"])
    refused(
        "page-of-another-row", broken([own, dict(further, pageInPdf=1, opensAs=_shared_key(_SHARED_FILE, 1))]),
        ["C-5.02", "file file-0001, page 1", "already the page of sheet A-1.01"],
    )
    refused(
        "further-no-delivery-field",
        broken([own, {field: value for field, value in further.items() if field != "deliveryId"}]),
        ["C-5.02", "file file-0001, page 4", "with no `deliveryId`"],
    )
    refused(
        "further-empty-delivery", broken([own, dict(further, deliveryId="")]),
        ["C-5.02", "file file-0001, page 4", "neither null nor a delivery id"],
    )

    # --- 8: the runner's own dispatch line binds a further page --- #
    runner = runner_path.read_text(encoding="utf-8")
    worked = [m for m in (_SHARED_DISPATCH_RE.match(line.strip()) for line in runner.splitlines()) if m]
    if not worked:
        errors.append(
            "the runner carries no worked dispatch line whose `sheets` names a further page by the "
            "key it opens as (`dispatch <window> <pass> <unit> sheets <fileId>-p<page> purpose ...`)"
        )
    else:
        window, pass_id, unit_id, opens_as = worked[0].groups()
        file_id, page_text = re.match(r"^(.+)-p([0-9]+)$", opens_as).groups()
        page = int(page_text)
        discipline = pass_id[:-1]
        if not pass_id.endswith(window) or not discipline.isalpha():
            errors.append(f"the runner's worked line names pass {pass_id}, not a discipline pass of window {window}")
        else:
            join_dir = root / "runner-line"
            sheet_type = "schedule" if window == "1" else "detail"
            base_page = page - 1 if page > 1 else page + 1
            join_rows = [
                _shared_row(discipline, f"{discipline}-4.30", sheet_type, base_page, "DETAILS",
                            further=((page, "DETAILS CONTINUED", sheet_type),), file_id=file_id),
            ]
            code, _bounds, err = inventory(join_dir, join_rows)
            if code != 0:
                errors.append(f"the runner line's grid refused: {err}")
            else:
                (join_dir / "ledger.md").write_text(
                    f"phase: plan approved\n{worked[0].group(0)}\n", encoding="utf-8"
                )
                bound = module._read_ledger_units(join_dir / "ledger.md", int(window))
                if bound != {unit_id: (opens_as,)}:
                    errors.append(f"the ledger reader binds the runner's worked line as {bound}, expected {unit_id} on {opens_as}")
                join_inventory = join_dir / "inventory.json"
                if window == "1":
                    code, _b, _e, join_text = plan(join_dir, 1, join_inventory)
                else:
                    first = root / "runner-line-w1"
                    first.mkdir(parents=True, exist_ok=True)
                    plan(first, 1, join_inventory)
                    code, _b, _e, join_text = plan(
                        join_dir, 2, join_inventory, "--window-1", str(first / "plan" / "window-1.json")
                    )
                want_line = (
                    f"{unit_id}. {discipline}-4.30, file {file_id}, page {page}, opens as {opens_as}: "
                    f"DETAILS CONTINUED"
                )
                if code == 0 and want_line not in join_text.splitlines():
                    errors.append(f"the plan after the runner's worked line carries no line `{want_line}`")
    reader = reader_path.read_text(encoding="utf-8")
    reviewer = (plugin_path / "agents" / "scope-reviewer.md").read_text(encoding="utf-8")
    # A corpus hit on another number's further page names no sheet number, and both searchers keep
    # hits off the inventory, so both cite it with the number on its inventory line.
    hit_rule = "is cited with the sheet number on that inventory line"
    for where, text, phrases in (
        ("the runner", runner, ["`Opens as:", "`Opens as: none`"]),
        ("the reader", reader, ["`Opens as: <key>`", "`Opens as: none`", "`sheet:<opens as>`", hit_rule]),
        ("the reviewer", reviewer, [hit_rule]),
    ):
        for phrase in phrases:
            if phrase not in " ".join(text.split()):
                errors.append(f"{where} does not carry {phrase}")

    detail = (
        "a grid of 7 rows printing two numbers on a further page each and carrying one page of an "
        "earlier issue: each further page a sheet of its own right after its number's row, with its "
        "own title and type and the key it opens as, counted apart and named on the bounds line, "
        "--expect-count held against the grid's rows, a schedule on a plan's further page read in "
        "window 1 and the plan in window 2, the further page's line naming its file and key, a "
        "replan binding it by its key and an old ledger's number still binding the number's own "
        "page, --exclude on the number leaving out both pages and the repeated lines unit naming the "
        "further page by its key, a window 1 file an earlier plugin wrote keeping its left-out "
        "number out on both pages, a further page past twelve keeping a dispatched part's ids, the "
        "earlier issue's page named and never planned, the runner's worked dispatch line bound "
        "through the ledger reader, the corpus hit rule in the reader and the reviewer; "
        f"{refusals} refusals each one line "
        "naming what is wrong; bound: invented grids, not a real set_grid answer"
    )
    if errors:
        detail += " | " + "; ".join(errors)
    return Result(name, passed=not errors, detail=detail)


# --------------------------------------------------------------------------- #
# Check: setup reads stay out of the lead
# --------------------------------------------------------------------------- #
#
# A project setup on a set of about 240 sheets once took the lead session from 58k to 774k tokens:
# the title block renders, the spec first pages, the package creates and the sheet grid all landed
# in the session the user talks to. The page reads now go to the plugin's `sheet-checker` agent and
# orientation runs one level down, as learn-project's own section says. This holds the text that
# drives the lead to that shape.
#
# What can fail, one case each below:
#   1. a page read verb (`render_page`, `get_page_text`, `search_set_text`, `reconcile_index`)
#      comes back into a section the lead runs: project-setup whole, drawing-upload outside its
#      steps 9b and 10, or learn-project's "Running one level down";
#   2. `set_grid` comes back there as anything but a summary call carrying `limit: 0`;
#   3. drawing-upload loses its sheet-checker dispatch, learn-project its orientation dispatch or
#      the first line of its summary, scope-run takes its own copy of either back, or project-setup
#      or scope-run stops pointing at learn-project's section;
#   4. one of the two retired sentences forbidding any agent in the upload comes back, so the text
#      contradicts itself;
#   5. a lead line reads a local PDF's pages with the Read tool, which puts the page images in the
#      session as surely as a render does;
#   6. the sheet-checker dispatch's `Jobs:` line stops pairing each recognition job with its
#      `fileId`, so with several drawing files a set unit cannot tell which file an unnamed page
#      is in.
#
# Honest bound: this reads the shipped text, not a session. Whether a lead session in fact stays
# small is measured from its transcript.

_LEAD_READ_VERBS = ("render_page", "get_page_text", "search_set_text", "reconcile_index")
_LEAD_READ_VERB_RE = re.compile(r"\b(" + "|".join(_LEAD_READ_VERBS) + r")\b")
_LEAD_GRID_RE = re.compile(r"\bset_grid\b(\([^)]*\))?")
# The Read tool named on a line that also names a PDF or its pages. Case-sensitive on purpose:
# "Read the report" is a verb in a sentence, "the Read tool" and "`Read`" are the tool.
_LEAD_LOCAL_READ_RE = re.compile(r"\bRead tool\b|`Read`")
_LEAD_PDF_WORD_RE = re.compile(r"\b(?:PDFs?|pages?)\b")
_LEAD_SECTION = "Running one level down"
_ORIENTATION_SUMMARY_LINE = (
    "sheets seen <n>   index findings <n>   spec sections <n>   packages drafted <n>   questions <n>"
)
_ORIENTATION_AGENT_PHRASE = "You are the orientation agent."
_SCOPE_RUN_OWN_DISPATCH = "Run the `learn-project` skill for this project, in full, exactly as it is written. Then return your summary and end."
_SHEET_CHECKER_LINE_RE = re.compile(r"^\s*subagent_type\s*:\s*plumlayer:sheet-checker\s*$")
_RETIRED_GATES = (
    ("drawing-upload", "No step of it is handed to a background agent or a subagent"),
    ("drawing-upload", "No step is handed to a background agent or a subagent"),
    ("project-setup", "Never hand it, or any part of it, to a background agent or a subagent"),
    ("project-setup", "never handed to a background agent"),
)


def _sections(text: str) -> list[tuple[str, int, list[str]]]:
    """Every `## ` section as (its heading, the 1-based line it opens on, its lines), the text
    above the first heading carried as a section with no heading."""
    sections: list[tuple[str, int, list[str]]] = [("", 1, [])]
    for i, line in enumerate(text.splitlines(), 1):
        if line.startswith("## "):
            sections.append((line[3:].strip(), i, []))
        sections[-1][2].append(line)
    return sections


def _lead_lines(text: str, only: str | None, exempt: tuple[str, ...]) -> list[tuple[int, str]]:
    """The lines a lead session runs, with their line numbers: the one section `only` names, or
    every section whose heading starts with none of `exempt`."""
    lines: list[tuple[int, str]] = []
    for heading, at, body in _sections(text):
        if only is not None and heading != only:
            continue
        if only is None and any(heading.startswith(prefix) for prefix in exempt):
            continue
        lines.extend((at + offset, line) for offset, line in enumerate(body))
    return lines


def _lead_read_errors(text: str, label: str, only: str | None = None, exempt: tuple[str, ...] = ()) -> list[str]:
    """One refusal per page read verb, and per `set_grid` that is not a summary call, on a line a
    lead runs; one more where `only` names a section the text does not carry."""
    if only is not None and not any(heading == only for heading, _, _ in _sections(text)):
        return [f"{label}: no `## {only}` section"]
    errors: list[str] = []
    for at, line in _lead_lines(text, only, exempt):
        for m in _LEAD_READ_VERB_RE.finditer(line):
            errors.append(f"{label}:{at}: the lead names `{m.group(1)}`, a page read that goes to an agent")
        for m in _LEAD_GRID_RE.finditer(line):
            if not m.group(1) or "limit: 0" not in m.group(1):
                errors.append(f"{label}:{at}: the lead names `set_grid` other than as a summary call with `limit: 0`")
        if _LEAD_LOCAL_READ_RE.search(line) and _LEAD_PDF_WORD_RE.search(line):
            errors.append(f"{label}:{at}: the lead reads a PDF's pages with the Read tool, a page read that goes to an agent")
    return errors


def _lead_shape_errors(texts: dict[str, str]) -> list[str]:
    """The dispatches and pointers that carry the reads away, and the retired gates."""
    errors: list[str] = []
    flat = {k: " ".join(v.split()) for k, v in texts.items()}
    upload_lines = texts["drawing-upload"].splitlines()
    blocks, _ = _fenced_blocks(upload_lines)
    checker_blocks = [body for _, body in blocks if any(_SHEET_CHECKER_LINE_RE.match(l) for l in body)]
    if not checker_blocks:
        errors.append("drawing-upload carries no dispatch block naming `subagent_type: plumlayer:sheet-checker`")
    for body in checker_blocks:
        jobs = [l for l in body if l.strip().startswith("Jobs:")]
        if len(jobs) != 1 or "fileId" not in jobs[0]:
            errors.append(
                "drawing-upload's sheet-checker dispatch does not pair each recognition job with its "
                "`fileId` on one `Jobs:` line"
            )
    lead = _lead_lines(texts["learn-project"], _LEAD_SECTION, ())
    lead_flat = " ".join(" ".join(line for _, line in lead).split())
    summary = " ".join(_ORIENTATION_SUMMARY_LINE.split())
    for phrase, what in ((summary, "the first line of the orientation summary"), (_ORIENTATION_AGENT_PHRASE, "the orientation dispatch")):
        if phrase not in lead_flat:
            errors.append(f"learn-project's `## {_LEAD_SECTION}` does not carry {what}")
    for phrase, what in ((summary, "its own copy of the orientation summary"), (" ".join(_SCOPE_RUN_OWN_DISPATCH.split()), "its own copy of the orientation dispatch")):
        if phrase in flat["scope-run"]:
            errors.append(f"scope-run carries {what}, which learn-project states")
    for skill in ("project-setup", "scope-run"):
        if f"Running one level down" not in flat[skill]:
            errors.append(f"{skill} does not point at learn-project's `Running one level down`")
    for skill, sentence in _RETIRED_GATES:
        if sentence in flat[skill]:
            errors.append(f"{skill} still reads {sentence!r}")
    return errors


def check_setup_lead_reads(plugin_path: Path, marketplace_root: Path) -> Result:
    name = "setup-reads-out-of-the-lead"
    skills = plugin_path / "skills"
    texts: dict[str, str] = {}
    for skill in ("project-setup", "learn-project", "drawing-upload", "scope-run"):
        path = skills / skill / "SKILL.md"
        if not path.is_file():
            return Result(name, False, detail=f"not found: {path}")
        texts[skill] = path.read_text(encoding="utf-8")

    scans = (
        ("project-setup", None, ()),
        ("learn-project", _LEAD_SECTION, ()),
        ("drawing-upload", None, ("9b.", "10.")),
    )
    errors: list[str] = []
    lead_lines = 0
    for skill, only, exempt in scans:
        lead_lines += len(_lead_lines(texts[skill], only, exempt))
        errors.extend(_lead_read_errors(texts[skill], f"{skill}/SKILL.md", only, exempt))
    errors.extend(_lead_shape_errors(texts))

    # The scan over fixtures, so a refusal is shown rather than assumed: a clean lead with a page
    # read under an exempt heading passes, and each broken one is refused in one line.
    fixtures = marketplace_root / "harness" / "fixtures"
    expected = [
        ("lead-reads-fixture-clean.md", None),
        ("lead-reads-fixture-render.md", "the lead names `render_page`"),
        ("lead-reads-fixture-grid-rows.md", "the lead names `set_grid` other than as a summary call"),
        ("lead-reads-fixture-local-read.md", "the lead reads a PDF's pages with the Read tool"),
    ]
    for fixture_name, wanted in expected:
        fixture = fixtures / fixture_name
        if not fixture.is_file():
            errors.append(f"fixture not found at {fixture}")
            continue
        got = _lead_read_errors(fixture.read_text(encoding="utf-8"), fixture_name, None, ("9b.", "10."))
        if wanted is None:
            if got:
                errors.append(f"{fixture_name}: clean fixture refused: {'; '.join(got)}")
        elif len(got) != 1 or wanted not in got[0]:
            errors.append(f"{fixture_name}: expected one refusal naming '{wanted}', got {got}")

    # The shape arms over the shipped text with each guarded part broken, so every refusal is shown.
    mutations: list[tuple[str, dict[str, str]]] = []
    if not errors:
        def mutated(skill: str, new_text: str) -> dict[str, str]:
            return {**texts, skill: new_text}

        mutations.append(("drawing-upload with its sheet-checker dispatch line taken out", mutated(
            "drawing-upload", re.sub(r"(?m)^\s*subagent_type\s*:\s*plumlayer:sheet-checker\s*$", "", texts["drawing-upload"]))))
        mutations.append(("drawing-upload with its `Jobs:` line naming no fileId", mutated(
            "drawing-upload", re.sub(r"(?m)^Jobs:.*$", "Jobs: <every recognition jobId>.", texts["drawing-upload"]))))
        mutations.append(("learn-project with its orientation dispatch taken out", mutated(
            "learn-project", texts["learn-project"].replace(_ORIENTATION_AGENT_PHRASE, ""))))
        mutations.append(("learn-project with its summary's first line taken out", mutated(
            "learn-project", re.sub(r"sheets seen <n>\s+index findings", "sheets <n> index findings", texts["learn-project"]))))
        mutations.append(("scope-run with the summary's first line put back", mutated(
            "scope-run", texts["scope-run"] + "\n" + _ORIENTATION_SUMMARY_LINE + "\n")))
        mutations.append(("project-setup with its pointer taken out", mutated(
            "project-setup", texts["project-setup"].replace("Running one level down", "running below"))))
        for skill, sentence in _RETIRED_GATES:
            mutations.append((f"{skill} with {sentence!r} put back", mutated(skill, texts[skill] + "\n" + sentence + ".\n")))
        for label, broken in mutations:
            if not _lead_shape_errors(broken):
                errors.append(f"the check passed {label}")

    detail = (
        f"{lead_lines} lines a lead runs scanned for {len(_LEAD_READ_VERBS)} page read verbs and "
        f"`set_grid` with rows and for the Read tool on a PDF's pages (project-setup whole, "
        f"drawing-upload outside steps 9b and 10, learn-project's `## {_LEAD_SECTION}`), the "
        f"sheet-checker dispatch with each job paired with its fileId, the orientation dispatch and "
        f"their pointers checked, {len(_RETIRED_GATES)} retired gate sentences absent, "
        f"{len(expected)} fixtures, {len(mutations)} mutations refused; bound: text only, not a "
        f"session's context"
    )
    if errors:
        detail += " | " + "; ".join(errors)
    return Result(name, passed=not errors, detail=detail)


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
        check_repeated_lines_text(plugin_path, marketplace_root),
        check_drawing_issue_passes(plugin_path, marketplace_root),
        check_anomaly_notes(plugin_path),
        check_shared_number_pages(plugin_path, marketplace_root),
        check_setup_lead_reads(plugin_path, marketplace_root),
    ]
    all_passed = all(r.passed for r in results)
    return results, all_passed
