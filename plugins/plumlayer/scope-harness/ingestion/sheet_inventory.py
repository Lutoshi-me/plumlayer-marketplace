"""
Stage 0-2 sheet-inventory ingestion -- the foundational drawing-set process.

Turns a real architect-issued PDF set into a grounded, source-linked SHEET
INVENTORY (the "drawing log"): one record per page = sheet-number + title
candidates, each with bbox evidence + method + confidence + trustClass. This is
the mosot-atomic-unit-of-truth truth engine run at SHEET granularity --
the subject is `sheet:A-101`, the page number is an attribute claim.

Paradigm (agents read and judge; deterministic tooling grounds; nothing governs unverified):
  * deterministic GROUNDS -- pull all title-block text + coordinates + font size
    (PyMuPDF). The sheet number is LOCALIZED by perception signals (largest
    sheet-grammar token, bottom-right corner), NOT inferred by a title-block
    regex. Grammar match (SHEETNO_RE) is used only to MATCH/canonicalize.
  * agent READS + judges -- low-confidence rows (ambiguous / missing) are flagged
    for a vision-agent read of the rendered crop; this script does not guess them.
  * humans review + promote -- nothing here is "approved"; rows are proposed /
    authoritative-candidate claims awaiting reconciliation + review.

Stage 3-4 (index parse + reconcile) is a light first cut here: page-0/index
declared sheet list vs extracted sheets -> match / declared-not-found / found-not-
declared. Real precision/recall needs the hand-verified inventory (next step).

Confidential: writes only to ./output/ (gitignored). ASCII output. PyMuPDF + stdlib.
Run:  python sheet_inventory.py            (full set)
      python sheet_inventory.py 0 20       (page range, inclusive start/exclusive end)

Environment variables (required):
  INGEST_PDF      path to the drawing PDF (e.g. C:/path/to/drawings.pdf)
  INGEST_SET_TAG  short identifier for the set (e.g. PROJECT-DD); defaults to SET
  INGEST_REVISION optional revision label; defaults to unspecified
"""
import json
import os
import re
import sys
from collections import Counter

import fitz  # PyMuPDF

# No project default — the PDF is always supplied per run. A silent default is a
# footgun: it would run against the wrong set if the env var is unset.
PDF = os.environ.get("INGEST_PDF")
if not PDF:
    sys.exit("[error] set INGEST_PDF to the drawing PDF path (e.g. C:/.../set.pdf) — no default")
SET_TAG = os.environ.get("INGEST_SET_TAG", "SET")
REVISION = os.environ.get("INGEST_REVISION", "unspecified")
# Output goes to the caller's working tree, never into this (read-only, possibly
# plugin-bundled) script's directory — set INGEST_OUT_DIR to steer it; default ./output.
OUT_DIR = os.environ.get("INGEST_OUT_DIR") or os.path.join(os.getcwd(), "output")

# Sheet-number grammar (AIA/NCS): A-101, AD-101, A-110A, G-001, S-201, the
# decimal sub-sheet form A-100.1, and the SINGLE-DIGIT-MAJOR decimal form that
# appears on some sets: E1.01, G0.00, FA1.06, S1.03A. Widening MATCHING to
# \d{1,3} is safe -- localization (font + corner) still picks the right token;
# the regex only gates which tokens compete.
SHEETNO_RE = re.compile(r"^[A-Z]{1,3}-?\d{1,3}(?:\.\d+)?[A-Z]?$")
# Discipline designators (NCS): the leading alpha prefix of the sheet number.
DISCIPLINE = {
    "G": "General", "C": "Civil", "L": "Landscape", "S": "Structural",
    "A": "Architectural", "AD": "Arch-Demo", "I": "Interiors", "F": "Fire",
    "P": "Plumbing", "M": "Mechanical", "H": "HVAC", "E": "Electrical",
    "T": "Telecom", "FP": "Fire-Protection", "FA": "Fire-Alarm",
}


def canon_sheetno(s):
    """Normalize for MATCHING only (A1.1 / A-1.1 / A101 families collapse to A-#)."""
    s = s.strip().upper()
    m = re.match(r"^([A-Z]{1,3})-?(\d{1,3}(?:\.\d+)?[A-Z]?)$", s)
    return "%s-%s" % (m.group(1), m.group(2)) if m else s


def discipline_of(sheetno):
    m = re.match(r"^([A-Z]{1,3})-", sheetno)
    if not m:
        return "Unknown"
    pre = m.group(1)
    return DISCIPLINE.get(pre, DISCIPLINE.get(pre[0], "Unknown"))


def spans_of(page):
    """All text spans with text, font size, and normalized-page center + bbox,
    reported in the RENDERED (rotation-applied) frame.

    get_text returns coordinates in UNROTATED page space; on a /Rotate page the
    visual bottom-right title block therefore lands at a different corner.
    Mapping every bbox through page.rotation_matrix (identity when rotation == 0)
    puts cx/cy + bboxPts in the same frame the page renders in, so corner
    localization, title banding, and citation crops all agree."""
    r = page.rect
    W, H = r.width, r.height
    mat = page.rotation_matrix
    out = []
    d = page.get_text("dict")
    for blk in d.get("blocks", []):
        for line in blk.get("lines", []):
            for sp in line.get("spans", []):
                t = sp["text"].strip()
                if not t:
                    continue
                rect = fitz.Rect(sp["bbox"]) * mat  # unrotated -> rendered frame
                x0, x1 = min(rect.x0, rect.x1), max(rect.x0, rect.x1)
                y0, y1 = min(rect.y0, rect.y1), max(rect.y0, rect.y1)
                out.append({
                    "text": t, "size": round(sp["size"], 2),
                    "bboxPts": [round(x0, 2), round(y0, 2), round(x1, 2), round(y1, 2)],
                    "cx": (((x0 + x1) / 2) - r.x0) / W,
                    "cy": (((y0 + y1) / 2) - r.y0) / H,
                })
    return out


def pick_sheet_number(spans):
    r"""LOCALIZE the title-block sheet number: among sheet-grammar spans, the
    largest font wins (tie-break: nearest the bottom-right corner). Returns
    (span, confidence, reason, n_distinct_competing).

    Confidence leans on perception corroboration: corner position + FONT
    DOMINANCE. On a real set the title-block sheet number is rendered far larger
    than any body/detail grammar token, so a dominant corner token is trusted
    even when many small grammar tokens compete -- raw competitor COUNT must not
    sink an obvious giant."""
    cands = [s for s in spans if SHEETNO_RE.match(s["text"].replace(" ", ""))]
    if not cands:
        return None, 0.0, "no-grammar-token", 0
    # largest font, then closest to bottom-right (max cx+cy)
    cands.sort(key=lambda s: (s["size"], s["cx"] + s["cy"]), reverse=True)
    best = cands[0]
    distinct = {canon_sheetno(s["text"]) for s in cands}
    in_corner = best["cx"] > 0.80 and best["cy"] > 0.70
    # font dominance: is best dramatically larger than the next-smaller grammar
    # token? (a giant title-block number vs small detail/grid refs). No smaller
    # competitor at all -> trivially dominant.
    smaller = [s["size"] for s in cands if s["size"] < best["size"] - 0.6]
    dominant = (not smaller) or best["size"] >= 1.6 * max(smaller)
    # confidence from corroborating perception signals
    if in_corner and (len(distinct) == 1 or dominant):
        conf = 0.95
        reason = "corner+unique" if len(distinct) == 1 else "corner+font-dominant"
    elif in_corner:
        conf, reason = 0.88, "corner+largest-font"
    elif dominant:
        conf, reason = 0.80, "font-dominant-off-corner"
    elif len(distinct) == 1:
        conf, reason = 0.75, "unique-but-off-corner"
    else:
        conf, reason = 0.55, "ambiguous-largest-font"
    return best, conf, reason, len(distinct)


def pick_title(spans, sheet_span):
    """Title candidate = largest-font text span in the same bottom-right title
    block as the sheet number, excluding the sheet number itself. This is the
    judgment-heavy field -- emitted as a low-trust candidate for agent read."""
    if sheet_span is None:
        return None
    sx, sy = sheet_span["cx"], sheet_span["cy"]
    block = [s for s in spans
             if abs(s["cx"] - sx) < 0.18 and s["cy"] < sy and s["cy"] > sy - 0.30
             and not SHEETNO_RE.match(s["text"].replace(" ", ""))
             and any(ch.isalpha() for ch in s["text"]) and len(s["text"]) >= 3]
    if not block:
        return None
    block.sort(key=lambda s: s["size"], reverse=True)
    top = block[0]["size"]
    # join same-size spans on roughly the same band (multi-word titles)
    line = [s for s in block if top - s["size"] <= 0.6]
    line.sort(key=lambda s: s["cx"])
    return {"text": " ".join(s["text"] for s in line),
            "size": top, "bboxPts": block[0]["bboxPts"]}


def claim(subject, predicate, value, method, conf, trust, src_bbox, snippet):
    return {
        "subject": subject, "predicate": predicate, "value": value,
        "evidence": [{"source": "%s/%s" % (SET_TAG, src_bbox["page"]),
                      # rendered (rotation-applied) frame -- spans_of maps bboxes
                      # through page.rotation_matrix, so on /Rotate pages these are
                      # NOT raw unrotated PDF user space (identical when rot==0).
                      "locator": {"frame": "page-points-rendered", "bboxPts": src_bbox["bbox"]},
                      "method": method, "snippet": snippet}],
        "trustClass": trust, "confidence": conf,
        "status": "current", "assertedBy": "sheet_inventory.py", "promotedBy": None,
    }


def main():
    doc = fitz.open(PDF)
    start = int(sys.argv[1]) if len(sys.argv) > 1 else 0
    end = int(sys.argv[2]) if len(sys.argv) > 2 else doc.page_count

    rows, claims = [], []
    for i in range(start, end):
        page = doc[i]
        spans = spans_of(page)
        sheet_span, conf, reason, ncomp = pick_sheet_number(spans)
        sheetno = canon_sheetno(sheet_span["text"]) if sheet_span else None
        title = pick_title(spans, sheet_span)
        trust = "authoritative" if conf >= 0.88 else "proposed"
        rows.append({"page": i, "sheetno": sheetno, "conf": conf, "reason": reason,
                     "ncomp": ncomp, "discipline": discipline_of(sheetno) if sheetno else "-",
                     "title": title["text"] if title else None,
                     "cx": round(sheet_span["cx"], 3) if sheet_span else None,
                     "cy": round(sheet_span["cy"], 3) if sheet_span else None})
        if sheetno:
            claims.append(claim("sheet:%s" % sheetno, "appearsOnPage", i, "vector",
                                conf, trust, {"page": i, "bbox": sheet_span["bboxPts"]},
                                sheet_span["text"]))
            if title:
                claims.append(claim("sheet:%s" % sheetno, "hasTitle", title["text"],
                                    "vector-localized", min(conf, 0.7), "proposed",
                                    {"page": i, "bbox": title["bboxPts"]}, title["text"]))

    # ---- printed drawing log ----
    print("=" * 92)
    print("SHEET INVENTORY  |  %s  |  pages %d-%d of %d" % (SET_TAG, start, end, doc.page_count))
    print("-" * 92)
    print("%4s %-8s %5s %-20s %4s  %-11s %s" %
          ("pg", "sheet#", "conf", "reason", "comp", "(cx,cy)", "title-candidate"))
    for r in rows:
        print("%4d %-8s %5.2f %-20s %4s  %-11s %s" % (
            r["page"], r["sheetno"] or "--", r["conf"], r["reason"], r["ncomp"],
            "(%s,%s)" % (r["cx"], r["cy"]) if r["cx"] is not None else "--",
            (r["title"] or "")[:42]))

    # ---- stage-0/2 summary ----
    found = [r for r in rows if r["sheetno"]]
    hi = [r for r in found if r["conf"] >= 0.88]
    flagged = [r for r in rows if r["conf"] < 0.88]
    disc = Counter(r["discipline"] for r in found)
    print("-" * 92)
    print("pages scanned ........ %d" % len(rows))
    print("sheet# extracted ..... %d  (high-conf >=0.88: %d)" % (len(found), len(hi)))
    print("flagged for review ... %d  (low-conf / missing -> agent-read queue)" % len(flagged))
    print("by discipline ........ %s" % dict(disc))
    dups = [s for s, c in Counter(r["sheetno"] for r in found).items() if c > 1]
    if dups:
        print("duplicate sheet# ..... %s  (supersession / revision collision -> reconcile)" % dups)

    # ---- stage 3-4: locate the index/sheet-list page(s) by title, then reconcile ----
    # (Don't assume page 0 is the index. Detect by keyword. A combined
    #  multi-discipline set carries MANY drawing-list pages — one per discipline —
    #  so union ALL of them, not just the first. If none, say so honestly.)
    INDEX_KEYS = ("DRAWING INDEX", "SHEET INDEX", "SHEET LIST", "DRAWING LIST",
                  "INDEX OF DRAWINGS")
    idx_pgs = [i for i in range(start, end)
               if any(k in doc[i].get_text("text").upper() for k in INDEX_KEYS)]
    extracted = {r["sheetno"] for r in found}
    print("-" * 92)
    if idx_pgs:
        # A declared token must look like a real sheet number, not a grid bubble
        # ("A1") or a stray body token: require >=2 digits.
        declared = set()
        for ip in idx_pgs:
            for t in doc[ip].get_text("text").replace("\n", " ").split():
                t = t.strip().strip(".,")
                if SHEETNO_RE.match(t) and sum(c.isdigit() for c in t) >= 2:
                    declared.add(canon_sheetno(t))
        missing = sorted(declared - extracted)
        extra = sorted(extracted - declared)
        print("index/drawing-list page(s): %s  (declare %d distinct sheets)"
              % (idx_pgs[:8], len(declared)))
        print("declared & found (match) ........... %d" % len(declared & extracted))
        print("declared, NOT found (RFI cand) ..... %d  %s" % (len(missing), missing[:12]))
        print("found, NOT declared (stale/addn) ... %d  %s" % (len(extra), extra[:12]))
    else:
        print("no index / sheet-list page in this discipline split")
        print("  -> cross-discipline reconciliation deferred (cover index likely in the G-series PDF)")

    os.makedirs(OUT_DIR, exist_ok=True)
    out = os.path.join(OUT_DIR, "sheet_inventory_claims.jsonl")
    with open(out, "w", encoding="utf-8") as f:
        for c in claims:
            f.write(json.dumps(c) + "\n")
    print("-" * 92)
    print("wrote %d sheet-inventory claims -> %s" % (len(claims), os.path.relpath(out)))
    doc.close()


if __name__ == "__main__":
    main()
