"""
derive_set_claims.py -- the deposit-layer post-process for drawing ingestion.

`sheet_inventory.py` (the frozen, self-calibrating grounding reader, validated across
11 firms' sets) is NOT edited here -- editing it trips the grounding-pipeline-change
re-validation gate. This script DRIVES its output: it reads the reader's
`sheet_inventory_claims.jsonl` and adds the two canonical-form claims the reader does
not emit but the intake doctrine requires per sheet
(`drawing-set-intake-design.md` -> "What intake produces"):

  * discipline   -- derived deterministically from the sheet-number PREFIX (never the
                    filename/folder), cited back to the SAME grounded sheet-number bbox
                    the `appearsOnPage` claim carries, method "derived-from-prefix".
                    The label + its certainty come from the reader's `discipline_of`
                    (single-sourced, below): a known prefix (NCS or confirmed non-NCS,
                    incl. building-prefix A1-101->A) is CONFIDENT -> trustClass "derived".
                    An uncertain prefix (first-char fallback "X(?)", or genuinely
                    "Unknown") is emitted low-trust "proposed" AND ambiguityClass-flagged
                    ("discipline-uncertain"), so the guess is visibly a guess: it surfaces
                    in the open-ambiguities ledger for the agent title-block backstop / a
                    human to settle, and never governs as fact (nothing-governs-unverified).
  * partOfIssue  -- the version scope (load-bearing for supersession), value = the issue
                    label the user gives or the agent reads off the cover sheet. Carried
                    per distinct sheet subject so a later re-issue supersedes per sheet.

Paradigm: deterministic tooling GROUNDS -- discipline-from-prefix is a mechanical
derivation off an already-grounded token (the sheet number), so it is a deterministic
post-process, NOT an agent judgment and NOT a model. Everything emitted is `proposed`/
`derived`; nothing governs until a human promotes it.

Output: a MERGED `set_claims.jsonl` = the reader's claims (verbatim) + the derived
claims. The agent then appends its residue reads (same Claim schema,
method "agent-vision-crop", cited bbox) to this file and hands it to the current
MOSOT deposit path unchanged -- the rows are well-formed claims like any other.

The DISCIPLINE map + discipline_of are SINGLE-SOURCED from sheet_inventory.py via import
(see the import block below), so the derived discipline matches the reader's printed
discipline exactly and can never drift from it. The earlier design kept a verbatim COPY
here guarded by a "keep in lockstep" comment -- and it drifted anyway (the copy went
stale, missing the reader's non-NCS prefixes and uncertainty flag, so a Solar-PV sheet
deposited as a confident "Plumbing"), which is the bug this fix removes. A comment is not
a guard; one source of truth is.

Confidential: reads/writes only caller-supplied paths (kept outside the repo). ASCII
output. Stdlib + the single-source import of sheet_inventory.py (which needs PyMuPDF) --
no other dependency; derive always runs in the ingestion stage where PyMuPDF is present.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import os
import sys
from collections import Counter
from pathlib import Path

# --- Single-source the discipline map + logic from the frozen reader -------------------
# `derive`'s discipline labeling MUST match the reader's `discipline_of` exactly, or the
# deposited `discipline` claim drifts from the printed inventory. The prior design kept a
# VERBATIM COPY of the reader's DISCIPLINE map + discipline_of here, guarded only by a
# "keep in lockstep" comment -- and it DID drift (the copy went stale: missing the reader's
# non-NCS prefixes AND its uncertainty flag, so PV-1xx confidently deposited as "Plumbing").
# A comment is not a guard, so we now IMPORT them -- one source of truth, no copy to drift.
#
# The reader sys.exit()s at import when INGEST_PDF is unset and imports PyMuPDF at module
# top. Both are satisfied here: a stub INGEST_PDF defuses the guard (the reader never OPENS
# the PDF at import -- main() is __name__-guarded -- so a fake path is harmless), and derive
# always runs in the ingestion stage right after the reader, where PyMuPDF is already
# present. The reader is loaded by its absolute path next to this file, so the import is
# independent of cwd / sys.path. Do NOT "simplify" this back to a vendored copy -- that is
# exactly the drift that caused the bug.
os.environ.setdefault("INGEST_PDF", "__derive_set_claims_import_stub__")
_reader_path = Path(__file__).with_name("sheet_inventory.py")
_spec = importlib.util.spec_from_file_location("sheet_inventory", _reader_path)
_reader = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_reader)

DISCIPLINE = _reader.DISCIPLINE        # re-exported so the map stays inspectable from here
discipline_of = _reader.discipline_of  # (sheetno) -> (label, uncertain_flag)


def derive(
    reader_claims: list[dict],
    issue_label: str,
    issue_source: str = "user-supplied",
    source_pdf: str = "",
) -> list[dict]:
    """Return the derived claims (discipline + partOfIssue) for each distinct
    `sheet:<NO>` subject seen in the reader's `appearsOnPage` claims.

    discipline cites the FIRST (lowest-page) appearsOnPage occurrence's grounded
    evidence -- the prefix lives in that sheet-number token, so that bbox IS the
    discipline's grounding."""
    # First appearsOnPage claim per subject (the grounding anchor for discipline).
    first_appears: dict[str, dict] = {}
    for c in reader_claims:
        if c.get("predicate") != "appearsOnPage":
            continue
        subj = c["subject"]
        page = c.get("value")
        prev = first_appears.get(subj)
        if prev is None or (isinstance(page, int) and page < prev.get("value", 1 << 30)):
            first_appears[subj] = c

    derived: list[dict] = []
    for subj in first_appears:  # dict preserves first-seen subject order
        anchor = first_appears[subj]
        sheetno = subj.split("sheet:", 1)[-1]
        disc, disc_uncertain = discipline_of(sheetno)  # reader's logic, single-sourced
        prefix = sheetno.split("-", 1)[0]

        # discipline: derived off the grounded sheet-number token. The reader's
        # discipline_of returns BOTH the label and whether it is a guess:
        #   * confident (NCS or known non-NCS prefix, incl. building-prefix A1-101 -> A)
        #       -> trustClass "derived" (can govern below authoritative), source confidence.
        #   * uncertain (first-char fallback "X(?)", or genuinely "Unknown")
        #       -> low-trust "proposed" AND ambiguityClass-flagged, so the guess is VISIBLY
        #          a guess: it surfaces in the open-ambiguities ledger for the agent
        #          title-block backstop / a human to settle, and never governs as fact.
        # Nothing-governs-unverified: a guessed discipline is never asserted confident.
        src_conf = anchor.get("confidence", 0.0)
        disc_evidence = []
        for ev in anchor.get("evidence", []) or []:
            disc_evidence.append({
                "source": ev.get("source"),
                "locator": ev.get("locator"),
                "method": "derived-from-prefix",
                "snippet": prefix,
            })
        disc_claim = {
            "subject": subj,
            "predicate": "discipline",
            "value": disc,
            "evidence": disc_evidence,
            "trustClass": "proposed" if disc_uncertain else "derived",
            "confidence": 0.4 if disc_uncertain else round(min(src_conf, 0.9), 2),
            "status": "current",
            "assertedBy": "derive_set_claims.py",
            "promotedBy": None,
        }
        if disc_uncertain:
            # ambiguityClass is the operative MOSOT marker (counts toward openAmbiguities
            # and is carried to the deposit by prepare_deposit); disciplineUncertain mirrors
            # the reader's additive flag for local inspection.
            disc_claim["ambiguityClass"] = "discipline-uncertain"
            disc_claim["disciplineUncertain"] = True
        derived.append(disc_claim)

        # partOfIssue: the version scope. A user-asserted label has no bbox (it is a
        # human assertion, not a read); a cover-sheet-read label would carry that
        # citation instead (pass --issue-source with the citation in that case).
        derived.append({
            "subject": subj,
            "predicate": "partOfIssue",
            "value": {"label": issue_label},
            "evidence": [{
                "source": issue_source,
                "method": "user-asserted" if issue_source == "user-supplied" else "vector",
                "snippet": issue_label,
            }],
            "trustClass": "proposed",
            "confidence": 0.6,
            "status": "current",
            "assertedBy": "derive_set_claims.py",
            "promotedBy": None,
            "versionScope": issue_label,
        })

        # locatedAt: canonical sheet pointer — {sourcePdf, page}. Cites the SAME
        # grounded evidence as the appearsOnPage anchor (same bbox/source); this is
        # not a new read, it is the location pointer in canonical vocabulary.
        # trustClass mirrors the anchor (authoritative for high-conf, proposed for low).
        if source_pdf:
            derived.append({
                "subject": subj,
                "predicate": "locatedAt",
                "value": {"sourcePdf": source_pdf, "page": anchor.get("value")},
                "evidence": [
                    {
                        "source": ev.get("source"),
                        "locator": ev.get("locator"),
                        "method": ev.get("method"),
                        "snippet": ev.get("snippet"),
                    }
                    for ev in anchor.get("evidence", []) or []
                ],
                "trustClass": anchor.get("trustClass", "proposed"),
                "confidence": anchor.get("confidence", 0.0),
                "status": "current",
                "assertedBy": "derive_set_claims.py",
                "promotedBy": None,
            })

    return derived


def main() -> None:
    ap = argparse.ArgumentParser(
        description="Add discipline + partOfIssue claims to the reader's sheet inventory.")
    ap.add_argument("--claims", required=True,
                    help="sheet_inventory_claims.jsonl from sheet_inventory.py")
    ap.add_argument("--issue-label", required=True,
                    help="the issue/version label (e.g. '2025-12-22 CD / IFC') -- "
                         "user-given or read off the cover sheet")
    ap.add_argument("--issue-source", default="user-supplied",
                    help="sourceInstrument for partOfIssue: 'user-supplied' (default) "
                         "or a cover-sheet citation source when the agent read it")
    ap.add_argument("--source-pdf", default="",
                    help="basename of the source drawing PDF (used in locatedAt claims, "
                         "e.g. '2025_12_19_1270 Comm Ave_Issue For Construction_Drawings.pdf'). "
                         "Required to emit locatedAt claims; omitting suppresses them.")
    ap.add_argument("--out", required=True,
                    help="merged set_claims.jsonl (reader claims verbatim + derived claims)")
    args = ap.parse_args()

    reader_claims: list[dict] = []
    with open(args.claims, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line:
                reader_claims.append(json.loads(line))

    derived = derive(reader_claims, args.issue_label, args.issue_source, args.source_pdf)

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8") as fh:
        for c in reader_claims:        # reader's claims, verbatim
            fh.write(json.dumps(c) + "\n")
        for c in derived:              # discipline + partOfIssue, appended
            fh.write(json.dumps(c) + "\n")

    subjects = {c["subject"] for c in derived}
    disc_claims = [c for c in derived if c["predicate"] == "discipline"]
    disc_vals = Counter(c["value"] for c in disc_claims)
    uncertain = sum(1 for c in disc_claims if c.get("ambiguityClass"))
    unknown = sum(1 for c in disc_claims if c["value"] == "Unknown")
    has_located_at = bool(args.source_pdf)
    per_subject = "+discipline +partOfIssue +locatedAt" if has_located_at else "+discipline +partOfIssue"
    print("[ok] %d reader claims + %d derived claims -> %s"
          % (len(reader_claims), len(derived), args.out))
    print("[ok] %d distinct sheet subjects: %s each"
          % (len(subjects), per_subject), file=sys.stderr)
    print("[ok] discipline distribution: %s" % dict(disc_vals), file=sys.stderr)
    if has_located_at:
        print("[ok] locatedAt emitted for each subject (sourcePdf=%r)" % args.source_pdf,
              file=sys.stderr)
    if uncertain:
        print("[warn] %d discipline claims are UNCERTAIN -> emitted 'proposed' + "
              "ambiguityClass='discipline-uncertain' (of which %d are fully 'Unknown'); "
              "the agent/human title-block backstop settles these -- a guessed prefix never "
              "governs as fact" % (uncertain, unknown), file=sys.stderr)


if __name__ == "__main__":
    main()
