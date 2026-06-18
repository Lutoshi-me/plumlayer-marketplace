"""Merge per-issue Drawing Index CSVs into a single Franken Set CSV.

Inputs are two or more per-issue CSVs in chronological order (earliest first).
Output is written next to the inputs.

Usage:
    python build_franken_set.py issue1.csv issue2.csv [issue3.csv ...]
    python build_franken_set.py --unlisted <unlisted.csv> issue1.csv issue2.csv ...
    python build_franken_set.py --out <path> issue1.csv ...

See ../SKILL.md for the full design rationale.
"""

from __future__ import annotations

import argparse
import csv
import os
import re
import sys
from collections import defaultdict

DISCIPLINE_ORDER = {
    name: i for i, name in enumerate([
        "GENERAL", "LIFE SAFETY", "CIVIL", "ARCHITECTURAL DEMO", "ARCHITECTURAL",
        "STRUCTURAL", "FIRE PROTECTION", "PLUMBING", "HVAC", "ELECTRICAL",
        "FIRE ALARM", "SECURITY", "TELECOMMUNICATIONS", "ELEVATOR",
    ])
}

REQUIRED_COLS = ["Discipline", "Sheet Number", "Page Title", "PDF File", "Page in PDF"]


def issue_label_from(filename: str) -> str:
    """Drawing Index - 2026-02-09 Bulletin 01.csv  ->  '2026-02-09 Bulletin 01'."""
    base = os.path.splitext(os.path.basename(filename))[0]
    return re.sub(r"^Drawing Index\s*-\s*", "", base).strip()


def sheet_sort_key(sn: str) -> tuple:
    """Split a sheet # into a tuple that sorts numerically.

    Examples:
        'A-100'    -> ('A-', 100, 0, '')
        'A-100.2'  -> ('A-', 100, 2, '')
        'A-101A'   -> ('A-', 101, 0, 'A')
        'LS-100.1' -> ('LS-', 100, 1, '')
        'VT01'     -> ('VT', 1, 0, '')
        'SKS-1'    -> ('SKS-', 1, 0, '')
    """
    m = re.match(r"^([A-Z]+-?)([0-9]+)(?:\.([0-9]+))?([A-Z]?)$", sn)
    if not m:
        return (sn, 0, 0, "")
    prefix, intpart, decpart, suffix = m.groups()
    return (prefix, int(intpart), int(decpart) if decpart else 0, suffix or "")


def read_csv(path: str, required: list[str] = None) -> tuple[list[dict], str]:
    if not os.path.isfile(path):
        sys.exit(f"Not found: {path}")
    with open(path, encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    if not rows:
        return [], issue_label_from(path)
    must_have = required if required is not None else REQUIRED_COLS
    missing = [c for c in must_have if c not in rows[0]]
    if missing:
        sys.exit(f"{path}: missing required columns {missing}")
    return rows, issue_label_from(path)


def safe_write_csv(path: str, header: list[str], rows) -> str:
    target = path
    base, ext = os.path.splitext(path)
    n = 2
    while True:
        try:
            with open(target, "w", newline="", encoding="utf-8") as f:
                w = csv.writer(f)
                w.writerow(header)
                w.writerows(rows)
            return target
        except PermissionError:
            target = f"{base} v{n}{ext}"
            n += 1


def detect_chronology(filenames: list[str]) -> None:
    """Warn if filename-embedded dates aren't monotonically non-decreasing."""
    date_re = re.compile(r"(\d{4}-\d{2}-\d{2})")
    dates = []
    for f in filenames:
        m = date_re.search(os.path.basename(f))
        dates.append(m.group(1) if m else None)
    if all(d is not None for d in dates):
        ordered = all(dates[i] <= dates[i + 1] for i in range(len(dates) - 1))
        if not ordered:
            print(f"[warn] filename dates aren't monotonically increasing: {dates}",
                  file=sys.stderr)
            print("[warn] inputs should be in chronological order (earliest first).",
                  file=sys.stderr)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("csvs", nargs="+",
                    help="Per-issue Drawing Index CSVs in chronological order.")
    ap.add_argument("--unlisted", default=None,
                    help="Optional Drawing Index - Unlisted Sheets.csv to fold in as Conformed-source rows.")
    ap.add_argument("--out", default=None,
                    help="Output path (default: 'Drawing Index - Franken Set.csv' next to inputs).")
    args = ap.parse_args()

    detect_chronology(args.csvs)

    # franken: sheet_no -> winning row dict
    franken: dict[str, dict] = {}
    title_by_sheet: dict[str, str] = {}
    touched: dict[str, list[str]] = defaultdict(list)

    # If unlisted CSV provided, treat its rows as if they were in the FIRST input (Conformed).
    # The unlisted CSV has a smaller schema (no Page Title); accept that.
    if args.unlisted:
        rows, _ = read_csv(args.unlisted, required=["Discipline", "Sheet Number", "PDF File", "Page in PDF"])
        first_label = issue_label_from(args.csvs[0])
        for r in rows:
            sheet = r["Sheet Number"].strip()
            if not sheet:
                continue
            touched[sheet].append(first_label + " (unlisted)")
            franken[sheet] = {
                "Discipline": r["Discipline"],
                "Source Issue": first_label,
                "Source PDF File": r["PDF File"],
                "Source Page in PDF": r["Page in PDF"],
            }

    for csv_path in args.csvs:
        rows, label = read_csv(csv_path)
        seen_in_this_issue: set[str] = set()
        for r in rows:
            sheet = r["Sheet Number"].strip()
            if not sheet:
                continue
            if sheet in seen_in_this_issue:
                print(f"[warn] {label}: duplicate sheet # {sheet} — keeping first occurrence",
                      file=sys.stderr)
                continue
            seen_in_this_issue.add(sheet)
            touched[sheet].append(label)
            franken[sheet] = {
                "Discipline": r["Discipline"],
                "Source Issue": label,
                "Source PDF File": r["PDF File"],
                "Source Page in PDF": r["Page in PDF"],
            }
            t = (r.get("Page Title") or "").strip()
            if t and sheet not in title_by_sheet:
                title_by_sheet[sheet] = t

    # Assemble output rows in discipline + sheet # order
    def sort_key(sheet):
        disc = franken[sheet]["Discipline"]
        return (DISCIPLINE_ORDER.get(disc, 999), disc, sheet_sort_key(sheet))

    sheets_sorted = sorted(franken.keys(), key=sort_key)
    out_rows = []
    blank_titles = []
    for sheet in sheets_sorted:
        f = franken[sheet]
        title = title_by_sheet.get(sheet, "")
        if not title:
            blank_titles.append(sheet)
        out_rows.append([
            f["Discipline"],
            sheet,
            title,
            f["Source Issue"],
            f["Source PDF File"],
            f["Source Page in PDF"],
            ", ".join(touched[sheet]),
        ])

    # Resolve output path
    if args.out:
        out_path = args.out
    else:
        out_dir = os.path.dirname(os.path.abspath(args.csvs[0]))
        out_path = os.path.join(out_dir, "Drawing Index - Franken Set.csv")

    written = safe_write_csv(
        out_path,
        ["Discipline", "Sheet Number", "Page Title", "Source Issue",
         "Source PDF File", "Source Page in PDF", "Touched By"],
        out_rows,
    )
    print(f"[ok] wrote {written}  ({len(out_rows)} sheets)")

    # Per-issue counts
    from collections import Counter
    by_source = Counter(franken[s]["Source Issue"] for s in franken)
    print("\n[summary] sheets per source issue:", file=sys.stderr)
    for issue, n in by_source.most_common():
        print(f"  {issue:40s} {n}", file=sys.stderr)

    # New-in-Bulletin callout (touched by no Conformed-like issue, only Bulletins)
    conformed_label = next((lbl for lbl in (issue_label_from(args.csvs[0]),) if "Conformed" in lbl), None)
    if conformed_label:
        new_in_bulletin = [s for s in sheets_sorted
                           if conformed_label not in touched[s]
                           and not any(t.startswith(conformed_label) for t in touched[s])]
        if new_in_bulletin:
            print(f"\n[info] {len(new_in_bulletin)} sheets that newly appear in Bulletins (not in Conformed):",
                  file=sys.stderr)
            for s in new_in_bulletin[:20]:
                print(f"  {s}  ({', '.join(touched[s])})", file=sys.stderr)
            if len(new_in_bulletin) > 20:
                print(f"  ... and {len(new_in_bulletin) - 20} more", file=sys.stderr)

    if blank_titles:
        print(f"\n[info] {len(blank_titles)} sheets have blank Page Title (no source CSV had one):",
              file=sys.stderr)
        for s in blank_titles[:10]:
            print(f"  {s}", file=sys.stderr)
        if len(blank_titles) > 10:
            print(f"  ... and {len(blank_titles) - 10} more", file=sys.stderr)


if __name__ == "__main__":
    main()
