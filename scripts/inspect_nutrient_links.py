"""Read-only inspection of near-duplicate links in the nutrient dataset (run before writing the splitter).
Reuses the hash cache and helpers from analyze_nutrient_groups.py.
Writes only inside data/processed/ (gitignored): montage PNGs, and the cache if it is incomplete."""
import os
import random
import re
from collections import Counter, defaultdict

import numpy as np
from PIL import Image, ImageDraw, ImageFont

from analyze_nutrient_groups import (CLASSES, EXTS, ROOT, SPLITS, current_key,
                                     get_hashes, lead_key, popcount)

OUT = "data/processed/inspection"
T = 5  # maximum phash distance that counts as a link


def bucket(d):
    return "0" if d == 0 else ("1-3" if d <= 3 else "4-5")


def thumb(path, size):
    with Image.open(path) as im:
        im = im.convert("RGB")
        im.thumbnail((size, size))
        return im.copy()


def montage_pairs(picks, out_path, size=200):
    font = ImageFont.load_default()
    cols, pad, cap_h = 2, 10, 30
    pair_w = 2 * size + pad
    rows_n = (len(picks) + cols - 1) // cols
    W = cols * pair_w + (cols + 1) * pad
    H = rows_n * (size + cap_h + pad) + pad
    canvas = Image.new("RGB", (W, H), "white")
    draw = ImageDraw.Draw(canvas)
    for k, (dist, ra, rb) in enumerate(picks):
        r_, c_ = divmod(k, cols)
        x = pad + c_ * (pair_w + pad)
        y = pad + r_ * (size + cap_h + pad)
        canvas.paste(thumb(ra[3], size), (x, y))
        canvas.paste(thumb(rb[3], size), (x + size + pad, y))
        draw.text((x, y + size + 2), f"d={dist}  {ra[2]} ({ra[1]})", fill="black", font=font)
        draw.text((x, y + size + 15), f"     vs {rb[2]} ({rb[1]})", fill="black", font=font)
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    canvas.save(out_path)


def montage_grid(tiles, out_path, size=120):
    cells = {}
    for r in tiles:
        m = re.match(r"\d+_(\d+)_(\d+)\.", r[2])
        if m:
            cells[(int(m.group(1)), int(m.group(2)))] = r
    if not cells:
        print("  (no tiles matched the NNNN_a_b.jpg pattern)")
        return
    nr = max(a for a, _ in cells) + 1
    nc = max(b for _, b in cells) + 1
    font = ImageFont.load_default()
    pad, cap_h = 6, 26
    W = nc * (size + pad) + pad
    H = nr * (size + cap_h + pad) + pad
    canvas = Image.new("RGB", (W, H), "white")
    draw = ImageDraw.Draw(canvas)
    for (a, b), r in cells.items():
        x = pad + b * (size + pad)
        y = pad + a * (size + cap_h + pad)
        canvas.paste(thumb(r[3], size), (x, y))
        draw.text((x, y + size + 2), r[2], fill="black", font=font)
        draw.text((x, y + size + 13), f"({r[1]})", fill="black", font=font)
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    canvas.save(out_path)
    print(f"  grid saved: {nr} rows (first suffix) x {nc} columns (second suffix)")


def main():
    rows = []  # (class, split, filename, path)
    for cls in CLASSES:
        for split in SPLITS:
            folder = os.path.join(ROOT, split, cls)
            if not os.path.isdir(folder):
                print("WARNING: missing folder", folder)
                continue
            for f in sorted(os.listdir(folder)):
                if f.lower().endswith(EXTS):
                    rows.append((cls, split, f, os.path.join(folder, f)))
    hashes = get_hashes([r[3] for r in rows])
    rows = [r for r in rows if hashes.get(r[3])]
    n = len(rows)
    print("images:", n)

    ids, lead_ids = {}, []
    for r in rows:
        lead_ids.append(ids.setdefault((r[0], lead_key(r[2])), len(ids)))
    h = np.array([int(hashes[r[3]], 16) for r in rows], dtype=np.uint64)

    cross = Counter()
    cross_by_d = Counter()
    cross_examples = []
    within_same = Counter()
    within_diff = Counter()
    zinc_pairs = {}
    chunk = 512
    for i0 in range(0, n, chunk):
        d = popcount(h[i0:i0 + chunk][:, None] ^ h[None, :])
        rr, cc = np.nonzero(d <= T)
        for a, b in zip(rr.tolist(), cc.tolist()):
            i = i0 + a
            if b <= i:
                continue
            dist = int(d[a, b])
            ca, cb = rows[i][0], rows[b][0]
            if ca != cb:
                cross[(ca, cb)] += 1
                cross_by_d[dist] += 1
                cross_examples.append((dist, rows[i], rows[b]))
            elif lead_ids[i] == lead_ids[b]:
                within_same[(ca, bucket(dist))] += 1
            else:
                within_diff[(ca, bucket(dist))] += 1
                if ca == "zinc":
                    key = tuple(sorted((lead_ids[i], lead_ids[b])))
                    if key not in zinc_pairs or dist < zinc_pairs[key][0]:
                        zinc_pairs[key] = (dist, rows[i], rows[b])

    print(f"\n=== CHECK 1: CROSS-CLASS LINKS (phash distance <= {T}, all {len(CLASSES)} classes together) ===")
    print("total cross-class pairs:", sum(cross.values()))
    for (a, b), v in sorted(cross.items()):
        print(f"  {a} ~ {b}: {v}")
    print("  by distance:", dict(sorted(cross_by_d.items())))
    for dist, ra, rb in sorted(cross_examples, key=lambda x: (x[0], x[1][2]))[:15]:
        print(f"  d={dist}  {ra[0]}/{ra[1]}/{ra[2]}  ~  {rb[0]}/{rb[1]}/{rb[2]}")

    print("\n=== WITHIN-CLASS LINKS BETWEEN DIFFERENT PHOTO NUMBERS (these are the links that merge groups) ===")
    for c in CLASSES:
        print(f"  {c}: " + ", ".join(f"d {b}: {within_diff[(c, b)]}" for b in ("0", "1-3", "4-5")))
    print("(links inside the same photo number, for reference)")
    for c in CLASSES:
        print(f"  {c}: " + ", ".join(f"d {b}: {within_same[(c, b)]}" for b in ("0", "1-3", "4-5")))

    print("\n=== CHECK 2a: ZINC PAIRS OF DIFFERENT PHOTO NUMBERS THAT THE HASHES LINK ===")
    buckets = defaultdict(list)
    for dist, ra, rb in zinc_pairs.values():
        buckets[bucket(dist)].append((dist, ra, rb))
    print("distinct zinc photo-number pairs per distance bucket:",
          {b: len(buckets[b]) for b in ("0", "1-3", "4-5")})
    rng = random.Random(0)
    picks = []
    for name, k in (("0", 4), ("1-3", 3), ("4-5", 3)):
        pool = sorted(buckets[name], key=lambda x: (x[1][2], x[2][2]))
        picks += rng.sample(pool, min(k, len(pool)))
    for dist, ra, rb in picks:
        print(f"  d={dist}  {ra[2]} ({ra[1]})  ~  {rb[2]} ({rb[1]})")
    montage_pairs(picks, os.path.join(OUT, "zinc_linked_pairs.png"))
    print("  saved:", os.path.join(OUT, "zinc_linked_pairs.png"))

    print("\n=== CHECK 2b: ONE POTASSIUM PHOTO, ALL ITS TILES ===")
    by_lead = defaultdict(list)
    for r in rows:
        if r[0] == "potassium":
            by_lead[lead_key(r[2])].append(r)
    pick = "0431" if "0431" in by_lead else sorted(by_lead)[0]
    tiles = by_lead[pick]
    print(f"photo number {pick}: {len(tiles)} tiles, per split under the CURRENT split: "
          f"{dict(Counter(r[1] for r in tiles))}")
    for key in sorted({current_key(r[2]) for r in tiles}):
        print(f"  old-rule group {key}: {dict(Counter(r[1] for r in tiles if current_key(r[2]) == key))}")
    montage_grid(tiles, os.path.join(OUT, "potassium_one_photo.png"))
    print("  saved:", os.path.join(OUT, "potassium_one_photo.png"))


if __name__ == "__main__":
    main()