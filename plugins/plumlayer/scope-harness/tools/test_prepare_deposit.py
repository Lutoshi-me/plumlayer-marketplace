"""
test_prepare_deposit.py — pytest coverage for write_batches() in prepare_deposit.py.

Tests all invariants specified in PLU-134:
  - sum(b.count for b in manifest.batches) == manifest.totalClaims == len(deposit)
  - each batch file's array length == its manifest count, and <= batch_size
  - batchCount == len(manifest.batches) == number of deposit_batch_*.json files on disk
  - re-running with a smaller input leaves NO stale deposit_batch_*.json from prior run
  - all written files are valid JSON, indent=2

Exercises deposit sizes: 0, 1, 50 (exact boundary), 123 (multi-batch).
Stdlib + pytest only.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

# Allow running from any cwd by importing from this file's directory.
import sys
sys.path.insert(0, str(Path(__file__).parent))

from prepare_deposit import write_batches, BatchManifest  # noqa: E402


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_deposit(n: int) -> list[dict]:
    """Synthesize n minimal propose-ready arg dicts."""
    return [
        {
            "subject": f"item-{i:04d}",
            "predicate": "description",
            "value": f"Scope item {i}",
            "sourceInstrument": "scope-harness",
        }
        for i in range(n)
    ]


def _assert_invariants(
    deposit: list[dict],
    batch_dir: Path,
    batch_size: int,
    manifest: BatchManifest,
) -> None:
    """Assert every PLU-134 invariant against the manifest + files on disk."""

    # 1. Manifest totalClaims matches deposit length.
    assert manifest.total_claims == len(deposit), (
        f"manifest.totalClaims={manifest.total_claims} != len(deposit)={len(deposit)}"
    )

    # 2. sum of batch counts == totalClaims.
    batch_sum = sum(b.count for b in manifest.batches)
    assert batch_sum == manifest.total_claims, (
        f"sum(batch counts)={batch_sum} != totalClaims={manifest.total_claims}"
    )

    # 3. batchCount == len(manifest.batches).
    assert manifest.batch_count == len(manifest.batches), (
        f"manifest.batchCount={manifest.batch_count} != len(batches)={len(manifest.batches)}"
    )

    # 4. Number of deposit_batch_*.json files on disk == batchCount.
    disk_files = sorted(batch_dir.glob("deposit_batch_*.json"))
    assert len(disk_files) == manifest.batch_count, (
        f"files on disk={len(disk_files)} != batchCount={manifest.batch_count}"
    )

    # 5. Each batch file: valid JSON array, length matches manifest count, <= batch_size.
    for entry in manifest.batches:
        fpath = batch_dir / entry.file
        assert fpath.exists(), f"batch file missing: {fpath}"
        raw = fpath.read_text(encoding="utf-8")
        # indent=2 means the file starts with "[\n" (not a single line) for non-empty arrays.
        # For empty arrays json.dumps([], indent=2) == "[]" — single line, which is fine.
        arr = json.loads(raw)
        assert isinstance(arr, list), f"{entry.file} is not a JSON array"
        assert len(arr) == entry.count, (
            f"{entry.file}: array length {len(arr)} != manifest count {entry.count}"
        )
        assert entry.count <= batch_size, (
            f"{entry.file}: count {entry.count} > batch_size {batch_size}"
        )

    # 6. deposit_manifest.json on disk is valid JSON and matches the returned manifest.
    manifest_path = batch_dir / "deposit_manifest.json"
    assert manifest_path.exists(), "deposit_manifest.json missing"
    manifest_dict = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert manifest_dict["totalClaims"] == manifest.total_claims
    assert manifest_dict["batchCount"] == manifest.batch_count
    assert len(manifest_dict["batches"]) == manifest.batch_count

    # 7. Ordering: concatenating all batch arrays in order reproduces the original deposit.
    reconstructed: list[dict] = []
    for entry in manifest.batches:
        chunk = json.loads((batch_dir / entry.file).read_text(encoding="utf-8"))
        reconstructed.extend(chunk)
    assert reconstructed == deposit, "reconstructed deposit from batches != original deposit"


# ---------------------------------------------------------------------------
# Parameterised core tests
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("n,batch_size", [
    (0,   50),   # empty deposit — edge case
    (1,   50),   # single claim
    (50,  50),   # exact boundary — should be exactly 1 batch
    (123, 50),   # multi-batch: 3 batches of 50/50/23
])
def test_write_batches_invariants(tmp_path: Path, n: int, batch_size: int) -> None:
    deposit = _make_deposit(n)
    batch_dir = tmp_path / "batches"

    manifest = write_batches(deposit, batch_dir, batch_size)
    _assert_invariants(deposit, batch_dir, batch_size, manifest)


def test_exact_boundary_one_batch(tmp_path: Path) -> None:
    """50 claims with batch_size=50 must produce exactly 1 batch file."""
    deposit = _make_deposit(50)
    manifest = write_batches(deposit, tmp_path / "b", 50)
    assert manifest.batch_count == 1
    assert manifest.batches[0].count == 50


def test_123_claims_three_batches(tmp_path: Path) -> None:
    """123 claims / 50 per batch → 3 batches: [50, 50, 23]."""
    deposit = _make_deposit(123)
    manifest = write_batches(deposit, tmp_path / "b", 50)
    assert manifest.batch_count == 3
    counts = [b.count for b in manifest.batches]
    assert counts == [50, 50, 23], f"unexpected batch counts: {counts}"


# ---------------------------------------------------------------------------
# Stale-clear test (the "prior larger run" footgun)
# ---------------------------------------------------------------------------

def test_stale_batches_cleared(tmp_path: Path) -> None:
    """Re-running with a smaller deposit must leave NO files from the prior larger run."""
    batch_dir = tmp_path / "batches"

    # First run: 123 claims → 3 batches.
    large = _make_deposit(123)
    manifest_large = write_batches(large, batch_dir, 50)
    assert manifest_large.batch_count == 3

    disk_after_large = sorted(batch_dir.glob("deposit_batch_*.json"))
    assert len(disk_after_large) == 3

    # Second run: 10 claims → 1 batch.
    small = _make_deposit(10)
    manifest_small = write_batches(small, batch_dir, 50)
    assert manifest_small.batch_count == 1

    disk_after_small = sorted(batch_dir.glob("deposit_batch_*.json"))
    assert len(disk_after_small) == 1, (
        f"stale batches not cleared: {[f.name for f in disk_after_small]}"
    )

    # And the invariants still hold for the small run.
    _assert_invariants(small, batch_dir, 50, manifest_small)


# ---------------------------------------------------------------------------
# Pretty-print (indent=2) test — load-bearing for agent reads
# ---------------------------------------------------------------------------

def test_batch_files_are_indented(tmp_path: Path) -> None:
    """Batch files with >=1 item must be multi-line (indent=2), not single-line."""
    deposit = _make_deposit(3)
    batch_dir = tmp_path / "b"
    write_batches(deposit, batch_dir, 50)
    raw = (batch_dir / "deposit_batch_000.json").read_text(encoding="utf-8")
    # indent=2 on a non-empty array always starts "[\n"
    assert raw.startswith("[\n"), f"batch file is not pretty-printed; starts with: {raw[:40]!r}"


def test_manifest_is_indented(tmp_path: Path) -> None:
    """deposit_manifest.json must be pretty-printed (indent=2)."""
    deposit = _make_deposit(5)
    batch_dir = tmp_path / "b"
    write_batches(deposit, batch_dir, 50)
    raw = (batch_dir / "deposit_manifest.json").read_text(encoding="utf-8")
    assert "\n" in raw, "manifest is not pretty-printed"
