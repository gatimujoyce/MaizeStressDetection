"""Checks the grouped nutrient split in data/processed/nutrient_deficiency_v2.
Fails if a group ID appears in two splits, if manifest and folders disagree, if two images of the same class
in different splits have phash distance <= 5, or if a class has fewer than 30 independent test photos.
Skipped when the v2 data is not on this machine. First run hashes ~13,800 images (several minutes);
later runs reuse data/processed/nutrient_v2_phash_cache.csv."""
import csv
from collections import defaultdict
from pathlib import Path

import numpy as np
import pytest

imagehash = pytest.importorskip("imagehash")
Image = pytest.importorskip("PIL.Image")

REPO = Path(__file__).resolve().parent.parent
V2 = REPO / "data" / "processed" / "nutrient_deficiency_v2"
MANIFEST = V2 / "manifest.csv"
CACHE = REPO / "data" / "processed" / "nutrient_v2_phash_cache.csv"
THRESHOLD = 5
MIN_TEST_PHOTOS = 30
SPLITS = ("train", "val", "test")
EXTS = (".jpg", ".jpeg", ".png")
POP = np.array([bin(i).count("1") for i in range(256)], dtype=np.uint8)

pytestmark = pytest.mark.skipif(not MANIFEST.exists(),
                                reason="data/processed/nutrient_deficiency_v2/manifest.csv not found")


def popcount(x):
    if hasattr(np, "bitwise_count"):
        return np.bitwise_count(x)
    b = np.ascontiguousarray(x).view(np.uint8).reshape(x.shape + (8,))
    return POP[b].sum(axis=-1)


@pytest.fixture(scope="module")
def rows():
    with open(MANIFEST, newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


@pytest.fixture(scope="module")
def hashes(rows):
    cache = {}
    if CACHE.exists():
        with open(CACHE, newline="", encoding="utf-8") as fh:
            for row in csv.reader(fh):
                if len(row) == 2:
                    cache[row[0]] = row[1]
    out, new = {}, False
    for r in rows:
        p = V2 / r["path"]
        st = p.stat()
        key = f"{r['path']}|{st.st_size}|{st.st_mtime_ns}"
        if key not in cache:
            with Image.open(p) as im:
                cache[key] = str(imagehash.phash(im))
            new = True
        out[r["path"]] = int(cache[key], 16)
    if new:
        with open(CACHE, "w", newline="", encoding="utf-8") as fh:
            csv.writer(fh).writerows(cache.items())
    return out


def test_manifest_matches_folders(rows):
    listed = {r["path"] for r in rows}
    assert len(listed) == len(rows), "duplicate paths in the manifest"
    on_disk = {p.relative_to(V2).as_posix() for p in V2.rglob("*")
               if p.is_file() and p.suffix.lower() in EXTS}
    assert on_disk == listed, (f"in folders but not in manifest: {sorted(on_disk - listed)[:5]}; "
                               f"in manifest but not in folders: {sorted(listed - on_disk)[:5]}")
    for r in rows:
        parts = r["path"].split("/")
        assert parts[0] == r["split"] and parts[1] == r["class"], f"manifest row disagrees with its path: {r['path']}"


def test_no_group_in_two_splits(rows):
    splits_of = defaultdict(set)
    for r in rows:
        assert r["group_id"].startswith(r["class"] + "_"), f"group id {r['group_id']} does not belong to {r['class']}"
        splits_of[r["group_id"]].add(r["split"])
    bad = {g: sorted(s) for g, s in splits_of.items() if len(s) > 1}
    assert not bad, f"{len(bad)} groups appear in more than one split, e.g. {dict(list(bad.items())[:5])}"


def test_no_cross_split_near_duplicates(rows, hashes):
    found = []
    for cls in sorted({r["class"] for r in rows}):
        by = {s: [r["path"] for r in rows if r["class"] == cls and r["split"] == s] for s in SPLITS}
        arr = {s: np.array([hashes[p] for p in by[s]], dtype=np.uint64) for s in SPLITS}
        for a, b in (("train", "val"), ("train", "test"), ("val", "test")):
            A, B = arr[a], arr[b]
            for i0 in range(0, len(A), 512):
                d = popcount(A[i0:i0 + 512][:, None] ^ B[None, :])
                rr, cc = np.nonzero(d <= THRESHOLD)
                for x, y in zip(rr.tolist(), cc.tolist()):
                    found.append((cls, by[a][i0 + x], by[b][y], int(d[x, y])))
    assert not found, f"{len(found)} cross-split pairs with phash distance <= {THRESHOLD}, e.g. {found[:5]}"


def test_enough_independent_test_photos(rows):
    for cls in sorted({r["class"] for r in rows}):
        groups = {r["group_id"] for r in rows if r["class"] == cls and r["split"] == "test"}
        assert len(groups) >= MIN_TEST_PHOTOS, f"{cls}: only {len(groups)} independent test photos"