"""
build_reading_packet.py — render sheets and assemble the reading packet for an agent.

Doctrine role (agents read and judge; deterministic tooling grounds; nothing governs unverified):
  * Deterministic GROUNDING tool — renders pixmaps (fitz, same dpi pattern as
    render_sheet.py), gathers text anchors per sheet, and writes a manifest. It
    captures pixels and locates anchors; it does NOT infer meaning.
  * Missing text anchors → WARN honestly and proceed; the agent reads pixels,
    cites estimated regions. Silent truncation is not permitted.
  * If --only (or v0Subset in the cluster config) is given, only that subset is
    rendered; the manifest documents exactly which sheets were included.

Tiling (tiling is first-class):
  A full 42" ARCH-E sheet rendered as one image downsamples to illegible mush
  through an agent's image read — schedule rows become gray smear. The fix,
  proven on a real test run, is to render each sheet as an OVERLAPPING GRID OF TILES at
  a higher dpi, so every schedule row and material code stays crisply legible.
  Tiling is now a first-class packet output (--tiles), not a one-off script.

  Geometry: each tile is its grid cell padded by `overlap` on every interior
  side, clamped at the sheet edge. Tile bboxNorm is reported in 0..1
  sheet-fraction coordinates so a citation on a tile maps straight back onto the
  full sheet (and the interactive view can crop the source image to the cited region).

  Grid selection: rather than a fixed 3x3 (which under-tiles a huge schedule and
  over-tiles a small detail sheet), the grid is chosen PER SHEET so each tile's
  rendered pixel dimensions land near --target-tile-px — every tile ends up at
  roughly the same legible density regardless of sheet size. Pass --grid RxC to
  force a fixed grid instead.

Usage:
  python build_reading_packet.py \\
    --pdf <arch.pdf> \\
    --selected selected_sheets.json \\
    --out-dir output/scope/packet/ \\
    [--dpi 150] \\
    [--only A-400,A-401,...] \\
    [--anchor-dir <dir containing per-sheet .jsonl files>] \\
    [--tiles] [--tile-dpi 200] [--overlap 0.06] \\
    [--grid 3x3 | --target-tile-px 2800]
"""

import argparse
import json
import math
import shutil
import sys
from pathlib import Path

import fitz  # PyMuPDF


SCHEMA_VERSION = "reading-packet-v0"
TILES_SCHEMA_VERSION = "reading-packet-tiles-v1"

# Defaults proven on a real test run: a ~42x30" sheet at 200 dpi with 0.06
# overlap and target 2800px/tile resolves to a 3x3 grid whose tiles (~3300x2360 px)
# are crisply legible row-by-row.
DEFAULT_TILE_DPI = 200
DEFAULT_OVERLAP = 0.06
DEFAULT_TARGET_TILE_PX = 2800


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _load_selected(selected_path: Path) -> dict:
    with selected_path.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def _resolve_subset(selected_sheets: list[dict], only_sheet_nos: list[str] | None) -> list[dict]:
    """
    Filter the selected list to only the sheets in only_sheet_nos (matched by
    sheetNo, case-insensitive).  Sheets in only_sheet_nos that are NOT in the
    selected list are warned about but not fatal.
    """
    if only_sheet_nos is None:
        return selected_sheets
    lookup = {s["sheetNo"].upper(): s for s in selected_sheets}
    result = []
    for sno in only_sheet_nos:
        entry = lookup.get(sno.upper())
        if entry is None:
            print(
                f"[warn] v0Subset sheet {sno!r} not found in selected_sheets - skipped",
                file=sys.stderr,
            )
        else:
            result.append(entry)
    return result


def _find_anchor_file(anchor_dir: Path, sheet_id: str) -> Path | None:
    """
    Look for a text-anchor JSONL for the given sheetId.
    Pattern: <sheet_id>.jsonl in the anchor directory.
    """
    candidate = anchor_dir / f"{sheet_id}.jsonl"
    return candidate if candidate.exists() else None


def _parse_grid(grid_arg: str | None) -> tuple[int, int] | None:
    """Parse a forced --grid 'RxC' (e.g. '3x3') into (nrows, ncols)."""
    if not grid_arg:
        return None
    try:
        rows_s, cols_s = grid_arg.lower().split("x")
        nrows, ncols = int(rows_s), int(cols_s)
        if nrows < 1 or ncols < 1:
            raise ValueError
        return nrows, ncols
    except ValueError:
        print(f"[error] --grid {grid_arg!r} is not 'RxC' (e.g. 3x3)", file=sys.stderr)
        sys.exit(1)


def _choose_grid(
    page_rect: fitz.Rect,
    tile_dpi: int,
    target_tile_px: int,
    forced_grid: tuple[int, int] | None,
) -> tuple[int, int]:
    """
    Pick (nrows, ncols) for a sheet. If forced_grid is given, use it. Otherwise
    choose per-sheet so each tile's rendered max dimension lands near
    target_tile_px — keeping every tile at roughly the same legible density
    independent of sheet size.
    """
    if forced_grid is not None:
        return forced_grid
    # rendered full-sheet pixel size at the tile dpi
    w_px = page_rect.width * tile_dpi / 72.0
    h_px = page_rect.height * tile_dpi / 72.0
    ncols = max(1, math.ceil(w_px / target_tile_px))
    nrows = max(1, math.ceil(h_px / target_tile_px))
    return nrows, ncols


def _tile_bbox_norm(r: int, c: int, nrows: int, ncols: int, overlap: float) -> list[float]:
    """Normalized [x0,y0,x1,y1] for tile (r,c): the grid cell padded by `overlap`
    on each interior side, clamped at the sheet edge."""
    x0 = max(0.0, c / ncols - overlap)
    x1 = min(1.0, (c + 1) / ncols + overlap)
    y0 = max(0.0, r / nrows - overlap)
    y1 = min(1.0, (r + 1) / nrows + overlap)
    return [round(x0, 4), round(y0, 4), round(x1, 4), round(y1, 4)]


def _render_tiles(
    page: fitz.Page,
    sheet_id: str,
    tiles_root: Path,
    nrows: int,
    ncols: int,
    overlap: float,
    tile_dpi: int,
) -> list[dict]:
    """
    Render the page as an nrows x ncols overlapping grid of tiles into
    tiles_root/<sheet_id>/r{r}c{c}.png. Returns the tile records for the
    manifest. Uses page.rect (rotation-aware) so tiles render in the visually
    correct orientation — sheets with /Rotate 270 are handled correctly.
    """
    rect = page.rect  # rotation-aware visible page rectangle
    sheet_dir = tiles_root / sheet_id
    # wipe any stale tiles from a prior run so grids never mix
    if sheet_dir.exists():
        shutil.rmtree(sheet_dir)
    sheet_dir.mkdir(parents=True, exist_ok=True)

    tiles: list[dict] = []
    for r in range(nrows):
        for c in range(ncols):
            bbox = _tile_bbox_norm(r, c, nrows, ncols, overlap)
            clip = fitz.Rect(
                rect.x0 + bbox[0] * rect.width,
                rect.y0 + bbox[1] * rect.height,
                rect.x0 + bbox[2] * rect.width,
                rect.y0 + bbox[3] * rect.height,
            )
            pix = page.get_pixmap(dpi=tile_dpi, clip=clip)
            tile_path = sheet_dir / f"r{r}c{c}.png"
            pix.save(str(tile_path))
            tiles.append(
                {
                    "path": tile_path.as_posix(),
                    "row": r,
                    "col": c,
                    "bboxNorm": bbox,
                    "px": [pix.width, pix.height],
                }
            )
    return tiles


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Render sheets and assemble a reading packet for an agent."
    )
    parser.add_argument("--pdf", required=True, help="Path to the Arch PDF")
    parser.add_argument(
        "--selected", required=True, help="Path to selected_sheets.json"
    )
    parser.add_argument(
        "--out-dir", required=True, help="Output directory for the packet"
    )
    parser.add_argument(
        "--dpi", type=int, default=150, help="Full-page render DPI (default 150)"
    )
    parser.add_argument(
        "--only",
        default=None,
        help="Comma-separated sheet numbers to render (overrides full selected list)",
    )
    parser.add_argument(
        "--anchor-dir",
        default=None,
        help="Directory containing per-sheet text-anchor .jsonl files",
    )
    # --- tiling ---
    parser.add_argument(
        "--tiles",
        action="store_true",
        help="Also render each sheet as an overlapping grid of legible tiles",
    )
    parser.add_argument(
        "--tile-dpi", type=int, default=DEFAULT_TILE_DPI,
        help=f"Tile render DPI (default {DEFAULT_TILE_DPI})",
    )
    parser.add_argument(
        "--overlap", type=float, default=DEFAULT_OVERLAP,
        help=f"Tile overlap as a sheet fraction (default {DEFAULT_OVERLAP})",
    )
    parser.add_argument(
        "--grid", default=None,
        help="Force a fixed tile grid 'RxC' (e.g. 3x3). Default: per-sheet adaptive.",
    )
    parser.add_argument(
        "--target-tile-px", type=int, default=DEFAULT_TARGET_TILE_PX,
        help=f"Adaptive-grid target tile pixel size (default {DEFAULT_TARGET_TILE_PX})",
    )
    args = parser.parse_args()

    pdf_path = Path(args.pdf)
    if not pdf_path.exists():
        print(f"[error] PDF not found: {pdf_path}", file=sys.stderr)
        sys.exit(1)

    selected_path = Path(args.selected)
    if not selected_path.exists():
        print(f"[error] selected_sheets.json not found: {selected_path}", file=sys.stderr)
        sys.exit(1)

    out_dir = Path(args.out_dir)
    img_dir = out_dir / "images"
    img_dir.mkdir(parents=True, exist_ok=True)

    forced_grid = _parse_grid(args.grid)
    tiles_root = out_dir / "tiles"
    if args.tiles:
        tiles_root.mkdir(parents=True, exist_ok=True)

    selected_data = _load_selected(selected_path)
    cluster_name = selected_data.get("clusterName", "unknown")
    set_id = selected_data.get("setId", "unknown")
    selected_sheets = selected_data.get("selectedSheets", [])

    # Determine the subset to render
    only_sheet_nos: list[str] | None = None
    if args.only:
        only_sheet_nos = [s.strip() for s in args.only.split(",") if s.strip()]

    subset = _resolve_subset(selected_sheets, only_sheet_nos)

    # anchor dir — default to the ingestion output directory within the plugin
    if args.anchor_dir:
        anchor_dir = Path(args.anchor_dir)
    else:
        anchor_dir = (
            Path(__file__).parent.parent / "ingestion" / "output"
        )

    # open PDF
    doc = fitz.open(str(pdf_path))
    total_pages = doc.page_count
    pdf_source = str(pdf_path)

    manifest_sheets = []
    tiles_manifest_sheets = []
    rendered_count = 0
    tiled_count = 0

    for entry in subset:
        sheet_no = entry["sheetNo"]
        page_num = entry.get("pageNum")
        sheet_id = entry.get("sheetId")
        title = entry.get("title", "")

        if page_num is None or page_num < 0 or page_num >= total_pages:
            print(
                f"[warn] {sheet_no}: invalid pageNum {page_num!r} - skipped",
                file=sys.stderr,
            )
            continue

        page = doc[page_num]
        pix = page.get_pixmap(dpi=args.dpi)
        img_filename = f"{sheet_id}.png"
        img_path = img_dir / img_filename
        pix.save(str(img_path))
        rendered_count += 1

        # text anchors
        anchor_file = _find_anchor_file(anchor_dir, sheet_id) if sheet_id else None
        has_anchors = anchor_file is not None
        if not has_anchors:
            print(
                f"[warn] no text anchors for {sheet_no} ({sheet_id}) - "
                f"agent reads pixels, cites estimated region",
                file=sys.stderr,
            )

        manifest_entry: dict = {
            "sheetId": sheet_id,
            "sheetNo": sheet_no,
            "pageNum": page_num,
            "title": title,
            "imagePath": str(img_path),
            "hasTextAnchors": has_anchors,
            "tiled": False,
        }
        if has_anchors:
            manifest_entry["textAnchorPath"] = str(anchor_file)

        # --- tiles ---
        if args.tiles:
            nrows, ncols = _choose_grid(
                page.rect, args.tile_dpi, args.target_tile_px, forced_grid
            )
            tiles = _render_tiles(
                page, sheet_id, tiles_root, nrows, ncols, args.overlap, args.tile_dpi
            )
            tiled_count += 1
            manifest_entry["tiled"] = True
            manifest_entry["grid"] = [nrows, ncols]
            manifest_entry["tilesDir"] = (tiles_root / sheet_id).as_posix()
            tiles_manifest_sheets.append(
                {
                    "sheetId": sheet_id,
                    "sheetNo": sheet_no,
                    "pageNum": page_num,
                    "title": title,
                    "grid": [nrows, ncols],
                    "tiles": tiles,
                }
            )
            print(f"     {sheet_no} ({sheet_id}): {nrows}x{ncols} = {len(tiles)} tiles")

        manifest_sheets.append(manifest_entry)

    doc.close()

    manifest = {
        "schemaVersion": SCHEMA_VERSION,
        "setId": set_id,
        "clusterName": cluster_name,
        "pdfSource": pdf_source,
        "tiled": bool(args.tiles),
        "sheets": manifest_sheets,
    }
    manifest_path = out_dir / "packet_manifest.json"
    with manifest_path.open("w", encoding="utf-8") as fh:
        json.dump(manifest, fh, indent=2)

    print(f"[ok] rendered {rendered_count} sheets")
    print(f"     manifest -> {manifest_path}")

    if args.tiles:
        tiles_manifest = {
            "schemaVersion": TILES_SCHEMA_VERSION,
            "setId": set_id,
            "tileDpi": args.tile_dpi,
            "overlap": args.overlap,
            "gridMode": "fixed" if forced_grid else "adaptive",
            "targetTilePx": None if forced_grid else args.target_tile_px,
            "sheets": tiles_manifest_sheets,
        }
        tiles_manifest_path = out_dir / "tiles_manifest.json"
        with tiles_manifest_path.open("w", encoding="utf-8") as fh:
            json.dump(tiles_manifest, fh, indent=2)
        print(f"[ok] tiled {tiled_count} sheets ({args.tile_dpi} dpi, overlap {args.overlap})")
        print(f"     tiles manifest -> {tiles_manifest_path}")


if __name__ == "__main__":
    main()
