"""Read-only analysis for the nutrient dataset.
Counts how many independent photo groups each class really has under three rules.
Writes only data/processed/nutrient_phash_cache.csv (inside the gitignored data/ folder)."""
import csv
import os
import re
from collections import defaultdict

import imagehash
import numpy as np
from PIL import Image

ROOT = "data/processed/nutrient_deficiency"
CLASSES = ["no_deficiency", "nitrogen", "phosphorus", "potassium", "zinc"]
SPLITS = ["train", "val", "test"]
CACHE = "data/processed/nutrient_phash_cache.csv"
THRESHOLDS = [0, 3, 5]
EXTS = (".jpg", ".jpeg", ".png")
POP = np.array([bin(i).count("1") for i in range(256)], dtype=np.uint8)


def current_key(fname):
    """Same rule as resplit_nutrient_data.py."""
    m = re.match(r"(\d+_\d+)_\d+\.(jpg|jpeg|png)$", fname, re.I)
    if m:
        return m.group(1)
    m = re.match(r"(\d+)_\d+\.(jpg|jpeg|png)$", fname, re.I)
    if m:
        return m.group(1)
    m = re.match(r"(IMG\d+)(?:_\d+)?\.(jpg|jpeg|png)$", fname, re.I)
    if m:
        return m.group(1)
    return "__unmatched__" + fname


def lead_key(fname):
    """Leading photo number only."""
    m = re.match(r"(\d+)_", fname)
    if m:
        return m.group(1)
    m = re.match(r"(IMG\d+)(?:_\d+)?\.", fname, re.I)
    if m:
        return m.group(1)
    return "__unmatched__" + fname


def popcount(x):
    if hasattr(np, "bitwise_count"):
        return np.bitwise_count(x)
    b = np.ascontiguousarray(x).view(np.uint8).reshape(x.shape + (8,))
    return POP[b].sum(axis=-1)


class UF:
    def __init__(self, n):
        self.p = list(range(n))

    def find(self, x):
        while self.p[x] != x:
            self.p[x] = self.p[self.p[x]]
            x = self.p[x]
        return x

    def union(self, a, b):
        ra, rb = self.find(a), self.find(b)
        if ra != rb:
            self.p[rb] = ra


def get_hashes(paths):
    cache = {}
    if os.path.exists(CACHE):
        with open(CACHE, newline="", encoding="utf-8") as fh:
            for row in csv.reader(fh):
                if len(row) == 2:
                    cache[row[0]] = row[1]
    new = 0
    for p in paths:
        if p in cache and cache[p]:
            continue
        try:
            with Image.open(p) as im:
                cache[p] = str(imagehash.phash(im))
        except Exception:
            cache[p] = ""
        new += 1
        if new % 1000 == 0:
            print(f"  hashed {new} images so far...", flush=True)
    if new:
        with open(CACHE, "w", newline="", encoding="utf-8") as fh:
            csv.writer(fh).writerows(cache.items())
    return cache


def add_hash_edges(uf, h, t, chunk=512):
    n = len(h)
    for i0 in range(0, n, chunk):
        d = popcount(h[i0:i0 + chunk][:, None] ^ h[None, :])
        r, c = np.nonzero(d <= t)
        for a, b in zip(r.tolist(), c.tolist()):
            if b > i0 + a:
                uf.union(i0 + a, b)


def group_sizes(uf, n):
    cnt = defaultdict(int)
    for i in range(n):
        cnt[uf.find(i)] += 1
    return sorted(cnt.values(), reverse=True)


def main():
    rows = []
    for cls in CLASSES:
        for split in SPLITS:
            folder = os.path.join(ROOT, split, cls)
            if not os.path.isdir(folder):
                print("WARNING: missing folder", folder)
                continue
            for f in sorted(os.listdir(folder)):
                if f.lower().endswith(EXTS):
                    rows.append((cls, f, os.path.join(folder, f)))
    print("images found:", len(rows))
    hashes = get_hashes([r[2] for r in rows])
    print("images that could not be hashed:", sum(1 for r in rows if not hashes.get(r[2])))
    print()
    for cls in CLASSES:
        items = [r for r in rows if r[0] == cls and hashes.get(r[2])]
        n = len(items)
        if n == 0:
            continue
        names = [r[1] for r in items]
        h = np.array([int(hashes[r[2]], 16) for r in items], dtype=np.uint64)
        lead = defaultdict(list)
        for i, f in enumerate(names):
            lead[lead_key(f)].append(i)
        print(f"=== {cls}: {n} images ===")
        print(f"  A) groups by the current rule ........ {len({current_key(f) for f in names})}")
        print(f"  B) groups by leading photo number .... {len(lead)}")
        for t in THRESHOLDS:
            uf = UF(n)
            for idxs in lead.values():
                for j in idxs[1:]:
                    uf.union(idxs[0], j)
            add_hash_edges(uf, h, t)
            s = group_sizes(uf, n)
            print(f"  C) + near-duplicate links (distance <= {t}): {len(s)} groups, "
                  f"largest {s[0]} ({100 * s[0] / n:.1f}% of class), top5 {s[:5]}, "
                  f"single-image groups {sum(1 for x in s if x == 1)}, "
                  f"test groups at 15%: {round(0.15 * len(s))}")
        print()


if __name__ == "__main__":
    main()