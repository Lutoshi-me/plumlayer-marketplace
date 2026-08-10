"""
derive_type_claims.py -- sheet-type and level labeling post-process.

Sibling to derive_set_claims.py: reads the pipeline's set_claims.jsonl (the
reader claims + derived discipline/issue/location claims) and emits two new
claim types per sheet:

  * sheetType  -- 13-value vocabulary (see SHEET_TYPE_RULES):
                  cover-index, overall-plan, enlarged-plan, plan, RCP,
                  schedule, legend, elevation, section, detail, notes,
                  schematic, other.

                  Classified in two passes:
                    1. Deterministic: keyword/pattern map applied to the
                       already-grounded `hasTitle` value. Evidence inherits
                       the hasTitle claim's source + bbox (same grounded
                       token; method = "keyword-from-title"). Confident and
                       cheap -- no render needed.
                    2. Agent residue: sheets where the keyword map returns
                       "other" are queued for an agent visual read. When
                       --render-dir is given, those pages are rendered at
                       ~100 DPI (fitz.get_pixmap) for batched agent reads.
                       The agent emits claims with method "agent-vision-crop";
                       this script writes them verbatim (same Claim shape) to
                       the output when --agent-claims is provided.

  * coveredLevels -- array of level strings extracted deterministically from
                     the title ("LEVEL 1", "BASEMENT", "ROOF", etc.). Omitted
                     when the title carries no level markers.

Paradigm: deterministic tooling GROUNDS -- `sheetType` from the keyword map
is a deterministic derivation off an already-grounded token (the hasTitle
claim value), NOT an agent judgment. The agent-read residue is the backstop
for titles that the keyword map cannot classify (blank, garbage, or a drawing
type outside the keyword vocabulary). Nothing-governs-unverified: all emitted
claims are "proposed".

Output: type_claims.jsonl -- the sheetType + coveredLevels claims, in the
same Claim shape as the rest of the pipeline, suitable for append to
set_claims.jsonl or direct feed to the current project record deposit path.

Confidential: reads/writes only caller-supplied paths (outside the repo).
The rendered thumbnails for the agent queue also go to the caller-supplied
--render-dir (never inside this repo). ASCII output. PyMuPDF + stdlib;
no additional dependencies.

Run (deterministic pass only):
  python derive_type_claims.py --claims set_claims.jsonl --out type_claims.jsonl

Run (with agent-queue render):
  python derive_type_claims.py --claims set_claims.jsonl --out type_claims.jsonl \\
      --pdf /path/to/set.pdf --render-dir /path/to/renders

Run (incorporate agent-read claims and finalize):
  python derive_type_claims.py --claims set_claims.jsonl --out type_claims.jsonl \\
      --agent-claims agent_type_claims.jsonl
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from pathlib import Path

# ---------------------------------------------------------------------------
# sheetType vocabulary + keyword classification rules
# ---------------------------------------------------------------------------
# Rule format: (sheet_type, [(regex_pattern, ...)])
# First match wins; order is load-bearing (specific types before general).
# All patterns are applied to UPPER-CASED title (re.search).
#
# Design notes:
#   * cover-index and schedule come first -- explicit vocabulary, no overlap.
#   * RCP before plan -- "REFLECTED CEILING PLAN" must NOT land as `plan`.
#   * section, elevation before plan -- e.g. "STAIR ELEVATION PLAN" is edge;
#     section/elevation have distinct keywords so order matters less but
#     correctness is preserved.
#   * schematic before detail/plan -- RISER/SCHEMATIC/DIAGRAM is an explicit
#     MEP class; it must not fall into `detail` or `plan`.
#   * enlarged-plan before plan -- "ENLARGED" alone is a strong enough signal
#     for residential-unit plan sheets that omit the word "PLAN".
#   * overall-plan before enlarged-plan/plan -- "OVERALL.*PLAN" must not
#     absorb into the catch-all `plan`.
#   * `other` is emitted only by the fallback; it is not in the rules list.

SHEET_TYPE_RULES: list[tuple[str, list[str]]] = [
    # --- unambiguous sheet classes ---
    ("cover-index", [
        r"\bCOVER\b",
        r"\bDRAWING LIST\b",
        r"\bSHEET LIST\b",
        r"\bDRAWING INDEX\b",
        r"\bSHEET INDEX\b",
        r"\bINDEX OF DRAWINGS\b",
    ]),
    ("schedule", [
        r"\bSCHEDULE[S]?\b",
        r"\bMATRIX\b",
    ]),
    ("legend", [
        r"\bLEGEND\b",
        r"\bKEY PLAN\b",
        r"\bSYMBOL[S]?\b",
        r"\bABBREVIATION",
    ]),
    ("notes", [
        r"\bGENERAL NOTES?\b",
        # "NOTES" alone, but not "NOTES ON PLAN" / "NOTES FOR PLAN"
        r"\bNOTES?\b(?!\s+(?:ON|FOR)\s+PLAN)",
        r"\bSPECIFICATION\b",
        r"\bCONVENTION",
        r"\bCODE SHEET\b",
        r"\bMOUNTING HEIGHT",
        r"\bSPECIAL INSPECTION",
        r"\bCRITERIA\b",
        r"\bMAAB\b",
    ]),
    # --- RCP before plan ---
    ("RCP", [
        r"\bREFLECTED CEILING\b",
        r"\bRCPS?\b",
    ]),
    # --- structural drawing types ---
    ("section", [
        r"\bBUILDING SECTION",
        r"\bWALL SECTION",
        r"\bSTAIR SECTION",
        r"\bSECTION[S]?\b",
    ]),
    ("elevation", [
        r"\bELEVATION[S]?\b",
    ]),
    # --- MEP riser / schematic class (before detail/plan to avoid absorption) ---
    ("schematic", [
        r"\bRISER[S]?\b",
        r"\bSCHEMATIC[S]?\b",
        r"\bONE.LINE\b",           # ONE-LINE, ONE LINE, ONELINE
        r"\bONELINE\b",
        r"\bDIAGRAM[S]?\b",
    ]),
    ("detail", [
        r"\bDETAIL[S]?\b",
        r"\bPARTITION TYPE",
        r"\bDOOR.*TYPE",
        r"\bFRAME TYPE",
        r"\bMOCKUP\b",
        r"\bISOMETRIC\b",
    ]),
    # --- plan subtypes (most specific to least) ---
    ("overall-plan", [
        r"\bOVERALL\b.*\bPLAN[S]?\b",
    ]),
    ("enlarged-plan", [
        r"\bENLARGED\b",
        r"\bUNIT KITCHEN\b",
        r"\bUNIT BATHROOM\b",
        r"\bUNIT BATH\b",
    ]),
    ("plan", [
        r"\bPLAN[S]?\b",
        r"\bFLOOR\b",
        r"\bROOF\b",
        r"\bSITE\b",
        r"\bGRADING\b",
        r"\bLIGHTING\b.*\bPLAN\b",
        r"\bCEILING\b.*\bPLAN\b",
        r"\bPAVING\b",
        r"\bDEMOLITION\b",
        r"\bEDGE OF SLAB\b",
    ]),
]

# Compile all patterns once.
_COMPILED_RULES: list[tuple[str, list[re.Pattern[str]]]] = [
    (stype, [re.compile(pat) for pat in pats])
    for stype, pats in SHEET_TYPE_RULES
]


def classify_title(title: str | None) -> tuple[str, str | None]:
    """Return (sheet_type, matched_snippet_or_None).

    sheet_type is one of the 13 vocab values; matched_snippet is the portion
    of the title that triggered the match (for evidence.snippet). Returns
    ("other", None) when no rule matches or the title is blank/missing.
    """
    if not title or not title.strip():
        return "other", None
    t = title.upper()
    for stype, compiled_pats in _COMPILED_RULES:
        for pat in compiled_pats:
            m = pat.search(t)
            if m:
                return stype, m.group(0)
    return "other", None


# ---------------------------------------------------------------------------
# coveredLevels extraction (deterministic from title)
# ---------------------------------------------------------------------------

# Patterns to find explicit level references in a sheet title.
# All matched strings are normalised to "Level N" / "Basement" / "Roof" / etc.
_LEVEL_NUM_RE = re.compile(
    r"\bLEVEL[S]?\s+(\d+)\b"
    r"|"
    r"\bL(\d+)\b(?!\s*\()"      # "L2" short form, but not followed by "(" (unit labels)
    r"|"
    r"\bFLOOR\s+(\d+)\b",
    re.IGNORECASE,
)
_LEVEL_NAMED_RE = re.compile(
    r"\b(BASEMENT|SUB.?BASEMENT|BELOW GRADE|ROOF|PENTHOUSE|GROUND|MEZZANINE|LOBBY)\b",
    re.IGNORECASE,
)

_NAMED_CANONICAL = {
    "BASEMENT": "Basement",
    "SUB-BASEMENT": "Sub-Basement",
    "SUB BASEMENT": "Sub-Basement",
    "BELOW GRADE": "Below Grade",
    "ROOF": "Roof",
    "PENTHOUSE": "Penthouse",
    "GROUND": "Ground",
    "MEZZANINE": "Mezzanine",
    "LOBBY": "Lobby",
}


def extract_covered_levels(title: str | None) -> list[str] | None:
    """Return sorted list of level strings from the title, or None if none found.

    Examples:
      "BASEMENT & LEVEL 1 OVERALL PLANS" -> ["Basement", "Level 1"]
      "LEVEL 2 & 3 OVERALL FLOOR PLANS"  -> ["Level 2", "Level 3"]
      "ENLARGED BATHROOM LEVEL 4"         -> ["Level 4"]
      "ROOF PLAN"                         -> ["Roof"]
      "DOOR SCHEDULE"                     -> None (no level marker)
    """
    if not title:
        return None
    levels: set[str] = set()
    for m in _LEVEL_NUM_RE.finditer(title):
        num = m.group(1) or m.group(2) or m.group(3)
        if num:
            levels.add("Level %s" % num)
    for m in _LEVEL_NAMED_RE.finditer(title):
        raw = m.group(0).upper().strip()
        # Normalise hyphenated variants
        raw = re.sub(r"SUB[\s-]BASEMENT", "Sub-Basement", raw, flags=re.IGNORECASE) if "BASEMENT" in raw else raw
        canonical = _NAMED_CANONICAL.get(raw)
        if canonical:
            levels.add(canonical)
    return sorted(levels) if levels else None


# ---------------------------------------------------------------------------
# Claim builder
# ---------------------------------------------------------------------------

ASSERTER = "derive_type_claims.py"


def make_sheet_type_claim(
    subject: str,
    sheet_type: str,
    confidence: float,
    evidence: list[dict],
    method: str,
    snippet: str | None,
    supersedes_id: str | None = None,
) -> dict:
    """Build a sheetType proposed claim in the pipeline Claim shape."""
    ev = []
    for e in evidence:
        entry: dict = {
            "source": e.get("source"),
            "method": method,
        }
        if e.get("locator"):
            entry["locator"] = e["locator"]
        if snippet:
            entry["snippet"] = snippet
        ev.append(entry)
    c: dict = {
        "subject": subject,
        "predicate": "sheetType",
        "value": sheet_type,
        "evidence": ev if ev else [{"source": "unknown", "method": method}],
        "trustClass": "proposed",
        "confidence": confidence,
        "status": "current",
        "assertedBy": ASSERTER,
        "promotedBy": None,
    }
    if supersedes_id:
        c["supersedesId"] = supersedes_id
    return c


def make_covered_levels_claim(
    subject: str,
    levels: list[str],
    evidence: list[dict],
    title_snippet: str,
) -> dict:
    """Build a coveredLevels proposed claim."""
    ev = [
        {
            "source": e.get("source"),
            "method": "keyword-from-title",
            "snippet": title_snippet,
        }
        for e in evidence
    ]
    return {
        "subject": subject,
        "predicate": "coveredLevels",
        "value": levels,
        "evidence": ev if ev else [{"source": "unknown", "method": "keyword-from-title", "snippet": title_snippet}],
        "trustClass": "proposed",
        "confidence": 0.80,
        "status": "current",
        "assertedBy": ASSERTER,
        "promotedBy": None,
    }


# ---------------------------------------------------------------------------
# Core derive function (importable)
# ---------------------------------------------------------------------------

def derive_type(
    set_claims: list[dict],
) -> tuple[list[dict], list[dict]]:
    """Classify sheet types from the pipeline's set_claims list.

    Returns (det_claims, agent_queue) where:
      det_claims   -- sheetType + coveredLevels claims for deterministically
                      classified sheets (all proposed).
      agent_queue  -- list of {subject, page, hasTitle_value, hasTitle_id}
                      for sheets that need an agent visual read (type="other").
    """
    # Group claims by subject -- collect hasTitle and appearsOnPage per sheet.
    titles: dict[str, dict] = {}   # subject -> hasTitle claim (first/best)
    pages: dict[str, int] = {}     # subject -> lowest page number
    page_ev: dict[str, list] = {}  # subject -> evidence from appearsOnPage

    for c in set_claims:
        subj = c.get("subject", "")
        if not subj.startswith("sheet:"):
            continue
        pred = c.get("predicate")
        if pred == "hasTitle":
            # Prefer the first-seen (lowest page, from reader order)
            if subj not in titles:
                titles[subj] = c
        elif pred == "appearsOnPage":
            pg = c.get("value")
            if isinstance(pg, int):
                prev = pages.get(subj)
                if prev is None or pg < prev:
                    pages[subj] = pg
                    page_ev[subj] = c.get("evidence", []) or []

    det_claims: list[dict] = []
    agent_queue: list[dict] = []

    for subj in sorted(titles):
        tc = titles[subj]
        title_val = tc.get("value") or ""
        title_str = str(title_val) if title_val is not None else ""
        ev = tc.get("evidence") or []

        stype, snippet = classify_title(title_str)
        levels = extract_covered_levels(title_str)

        if stype != "other":
            # Deterministic: inherit hasTitle evidence (same bbox/source)
            conf = 0.85 if stype in ("schedule", "cover-index", "RCP", "legend",
                                      "elevation", "schematic") else 0.80
            det_claims.append(make_sheet_type_claim(
                subj, stype, conf, ev, "keyword-from-title", snippet
            ))
            if levels:
                det_claims.append(make_covered_levels_claim(
                    subj, levels, ev, snippet or title_str[:60]
                ))
        else:
            # Queue for agent read
            pg = pages.get(subj)
            agent_queue.append({
                "subject": subj,
                "page": pg,
                "titleValue": title_str,
                "hasTitleId": tc.get("id"),
                "evidence": ev,
            })

    return det_claims, agent_queue


# ---------------------------------------------------------------------------
# Page rendering (for agent-read queue)
# ---------------------------------------------------------------------------

def render_agent_queue(
    queue: list[dict],
    pdf_path: str,
    render_dir: Path,
    dpi: int = 100,
) -> list[dict]:
    """Render pages for the agent-read queue to render_dir at `dpi` DPI.

    Returns the queue with 'renderPath' added to each entry.
    Skips entries with no page number (no appearsOnPage claim found).
    Prints a warning for skipped entries.
    """
    try:
        import fitz
    except ImportError:
        print("[warn] PyMuPDF not available -- skipping renders (install fitz)",
              file=sys.stderr)
        return queue

    render_dir.mkdir(parents=True, exist_ok=True)
    doc = fitz.open(pdf_path)
    mat = fitz.Matrix(dpi / 72, dpi / 72)

    for entry in queue:
        pg = entry.get("page")
        if pg is None:
            print("[warn] no page for %s -- cannot render; queued for manual review"
                  % entry["subject"], file=sys.stderr)
            entry["renderPath"] = None
            continue
        page = doc[pg]
        pix = page.get_pixmap(matrix=mat)
        subj_slug = entry["subject"].replace("sheet:", "").replace("/", "_")
        out_path = render_dir / ("p%04d_%s.png" % (pg, subj_slug))
        pix.save(str(out_path))
        entry["renderPath"] = str(out_path)

    doc.close()
    return queue


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main() -> None:
    ap = argparse.ArgumentParser(
        description="Derive sheetType + coveredLevels claims from the "
                    "pipeline's set_claims.jsonl.")
    ap.add_argument("--claims", required=True,
                    help="set_claims.jsonl from derive_set_claims.py")
    ap.add_argument("--out", required=True,
                    help="Output type_claims.jsonl (sheetType + coveredLevels)")
    ap.add_argument("--pdf",
                    help="Source drawing PDF -- required to render the "
                         "agent-read queue (--render-dir).")
    ap.add_argument("--render-dir",
                    help="Directory for rendered agent-queue page thumbnails. "
                         "Requires --pdf.")
    ap.add_argument("--render-dpi", type=int, default=100,
                    help="DPI for rendered thumbnails (default 100).")
    ap.add_argument("--agent-claims",
                    help="JSONL of agent-read claims to incorporate into "
                         "the output (emitted by the agent after visual reads).")
    ap.add_argument("--queue-manifest",
                    help="Write the agent-read queue as JSON manifest to this "
                         "path (subjects + page numbers + render paths).")
    args = ap.parse_args()

    # Load set_claims
    set_claims: list[dict] = []
    with open(args.claims, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line:
                set_claims.append(json.loads(line))

    # Derive deterministic + build queue
    det_claims, agent_queue = derive_type(set_claims)

    # Render agent queue (optional)
    if args.render_dir:
        if not args.pdf:
            print("[error] --render-dir requires --pdf", file=sys.stderr)
            sys.exit(1)
        agent_queue = render_agent_queue(
            agent_queue, args.pdf, Path(args.render_dir), args.render_dpi
        )

    # Write queue manifest (optional)
    if args.queue_manifest:
        Path(args.queue_manifest).parent.mkdir(parents=True, exist_ok=True)
        manifest = [
            {
                "subject": e["subject"],
                "page": e.get("page"),
                "titleValue": e.get("titleValue"),
                "renderPath": e.get("renderPath"),
            }
            for e in agent_queue
        ]
        with open(args.queue_manifest, "w", encoding="utf-8") as fh:
            json.dump(manifest, fh, indent=2)
        print("[ok] agent-queue manifest: %d entries -> %s"
              % (len(manifest), args.queue_manifest))

    # Incorporate agent-read claims (optional)
    agent_claims: list[dict] = []
    if args.agent_claims:
        with open(args.agent_claims, encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if line:
                    agent_claims.append(json.loads(line))

    # Write output
    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    all_claims = det_claims + agent_claims
    with out_path.open("w", encoding="utf-8") as fh:
        for c in all_claims:
            fh.write(json.dumps(c) + "\n")

    # --- summary ---
    total_subjects = len(set({
        c["subject"] for c in set_claims if c.get("subject", "").startswith("sheet:")
    }))
    st_counts = Counter(c["value"] for c in all_claims if c.get("predicate") == "sheetType")
    agent_st = Counter(c["value"] for c in agent_claims if c.get("predicate") == "sheetType")
    level_count = sum(1 for c in all_claims if c.get("predicate") == "coveredLevels")
    corrected_titles = sum(
        1 for c in agent_claims if c.get("predicate") == "hasTitle"
    )

    print("[ok] %d set claims -> %d type claims (%d det + %d agent) -> %s"
          % (len(set_claims), len(all_claims), len(det_claims), len(agent_claims), args.out))
    print("[ok] %d distinct sheet subjects; agent queue: %d sheets"
          % (total_subjects, len(agent_queue)), file=sys.stderr)
    print("[ok] sheetType distribution: %s" % dict(st_counts), file=sys.stderr)
    if agent_st:
        print("[ok] agent-read types: %s" % dict(agent_st), file=sys.stderr)
    print("[ok] coveredLevels claims: %d" % level_count, file=sys.stderr)
    if corrected_titles:
        print("[ok] hasTitle corrected by agent: %d" % corrected_titles, file=sys.stderr)

    # Schedule recall check
    has_schedule_word = [
        c for c in set_claims
        if c.get("predicate") == "hasTitle"
        and c.get("value") and "SCHEDULE" in str(c["value"]).upper()
    ]
    schedule_subjects = {c["subject"] for c in has_schedule_word}
    classified_schedule = {
        c["subject"] for c in all_claims
        if c.get("predicate") == "sheetType" and c.get("value") == "schedule"
    }
    missed = schedule_subjects - classified_schedule
    print("[ok] schedule recall: %d/%d (title contains 'SCHEDULE')"
          % (len(schedule_subjects & classified_schedule), len(schedule_subjects)), file=sys.stderr)
    if missed:
        print("[warn] missed as schedule: %s" % sorted(missed), file=sys.stderr)

    # Coverage
    all_sheet_subjects = {
        c["subject"] for c in set_claims if c.get("subject", "").startswith("sheet:")
    }
    typed_subjects = {
        c["subject"] for c in all_claims if c.get("predicate") == "sheetType"
    }
    untyped = sorted(all_sheet_subjects - typed_subjects)
    print("[ok] sheetType coverage: %d/%d sheet subjects"
          % (len(typed_subjects), len(all_sheet_subjects)), file=sys.stderr)
    if untyped:
        print("[warn] untyped subjects (%d): %s" % (len(untyped), untyped[:10]),
              file=sys.stderr)
    if len(agent_queue):
        unrendered = [e["subject"] for e in agent_queue if not e.get("renderPath")]
        if unrendered:
            print("[warn] %d agent-queue entries could not be rendered: %s"
                  % (len(unrendered), unrendered[:5]), file=sys.stderr)


if __name__ == "__main__":
    main()
