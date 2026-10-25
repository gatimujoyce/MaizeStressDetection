"""Grouped, stratified re-split of the nutrient dataset into train/val/test = 65/15/20.
Group = leading photo number, merged with near-duplicate links (phash distance <= threshold) inside a class.
Reads the current split (data/processed/nutrient_deficiency), writes a NEW folder (default
data/processed/nutrient_deficiency_v2) plus manifest.csv. Never modifies or deletes the source images.
Reuses scripts/analyze_nutrient_groups.py and its hash cache."""
import argparse
import csv
import os
import random
import shutil
from collections import defaultdict

import numpy as np

from analyze_nutrient_groups import (CLASSES, EXTS, ROOT, SPLITS, UF, add_hash_edges,
                                     get_hashes, lead_key)

OUT_DEFAULT = "data/processed/nutrient_deficiency_v2"
RATIOS = {"train": 0.65, "val": 0.15, "test": 0.20}


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--out-dir", default=OUT_DEFAULT)
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--threshold", type=int, default=5, help="max phash distance that links two images")
    ap.add_argument("--min-test-photos", type=int, default=30)
    ap.add_argument("--dry-run", action="store_true", help="print the plan, copy nothing")
    args = ap.parse_args()

    if not args.dry_run and os.path.isdir(args.out_dir) and os.listdir(args.out_dir):
        raise SystemExit(f"ERROR: {args.out_dir} already has files. Delete it yourself or pass another --out-dir.")

    rows = []  # (class, filename, source_path)
    for cls in CLASSES:
        for split in SPLITS:
            folder = os.path.join(ROOT, split, cls)
            if not os.path.isdir(folder):
                raise SystemExit(f"ERROR: missing folder {folder}")
            for f in sorted(os.listdir(folder)):
                if f.lower().endswith(EXTS):
                    rows.append((cls, f, os.path.join(folder, f)))
    print("images found:", len(rows))
    hashes = get_hashes([r[2] for r in rows])
    unhashed = [r[2] for r in rows if not hashes.get(r[2])]
    if unhashed:
        raise SystemExit(f"ERROR: {len(unhashed)} images could not be hashed, e.g. {unhashed[0]}")

    manifest, summary, failures = [], [], []
    for cls in CLASSES:
        items = [r for r in rows if r[0] == cls]
        names = [r[1] for r in items]
        if len(set(names)) != len(names):
            raise SystemExit(f"ERROR: duplicate file names inside class {cls}")
        n = len(items)
        h = np.array([int(hashes[r[2]], 16) for r in items], dtype=np.uint64)
        uf = UF(n)
        first = {}
        for i, r in enumerate(items):
            k = lead_key(r[1])
            if k in first:
                uf.union(first[k], i)
            else:
                first[k] = i
        add_hash_edges(uf, h, args.threshold)
        comps = defaultdict(list)
        for i in range(n):
            comps[uf.find(i)].append(i)
        groups = sorted(comps.values(), key=lambda g: min(names[i] for i in g))  # stable numbering

        order = list(range(len(groups)))
        random.Random(f"{args.seed}-{cls}").shuffle(order)
        order.sort(key=lambda gi: len(groups[gi]), reverse=True)  # largest first; ties keep the shuffled order
        targets = {s: RATIOS[s] * n for s in SPLITS}
        filled = {s: 0 for s in SPLITS}
        assign = {}
        for gi in order:
            s = max(SPLITS, key=lambda sp: (targets[sp] - filled[sp]) / targets[sp])
            assign[gi] = s
            filled[s] += len(groups[gi])

        p = {s: 0 for s in SPLITS}
        im = {s: 0 for s in SPLITS}
        ln = {s: set() for s in SPLITS}
        for gi, g in enumerate(groups):
            s = assign[gi]
            p[s] += 1
            im[s] += len(g)
            for i in g:
                ln[s].add(lead_key(names[i]))
                manifest.append({
                    "path": f"{s}/{cls}/{names[i]}", "class": cls, "split": s,
                    "group_id": f"{cls}_{gi:04d}", "phash": hashes[items[i][2]],
                    "source_path": items[i][2].replace("\\", "/"),
                })
        summary.append({"cls": cls, "photos": len(groups), "p": p, "i": im,
                        "sh": {s: 100.0 * im[s] / n for s in SPLITS}, "ln": {s: len(ln[s]) for s in SPLITS}})
        for s in SPLITS:
            if p[s] == 0:
                failures.append(f"{cls}: the {s} split is empty")
        if p["test"] < args.min_test_photos:
            failures.append(f"{cls}: only {p['test']} independent test photos (minimum {args.min_test_photos})")

    print(f"\ngrouping: leading photo number + phash links <= {args.threshold}, seed {args.seed}, "
          f"ratios {RATIOS['train']:.2f}/{RATIOS['val']:.2f}/{RATIOS['test']:.2f}")
    print(f"{'class':<14}{'photos':>7}   {'photos tr/va/te':<17}{'images tr/va/te':<22}{'image share % tr/va/te':<26}photo numbers tr/va/te")
    for s in summary:
        print(f"{s['cls']:<14}{s['photos']:>7}   "
              f"{s['p']['train']:>4}/{s['p']['val']:>4}/{s['p']['test']:>4}    "
              f"{s['i']['train']:>5}/{s['i']['val']:>5}/{s['i']['test']:>5}    "
              f"{s['sh']['train']:>5.1f}/{s['sh']['val']:>5.1f}/{s['sh']['test']:>5.1f}      "
              f"{s['ln']['train']:>4}/{s['ln']['val']:>4}/{s['ln']['test']:>4}")
    print(f"total images: {len(manifest)}")
    if failures:
        print("\nFAILED CHECKS:")
        for f in failures:
            print("  -", f)
        raise SystemExit(1)
    if args.dry_run:
        print("\n(dry run: nothing was copied)")
        return

    for k, m in enumerate(manifest, 1):
        dest = os.path.join(args.out_dir, m["split"], m["class"])
        os.makedirs(dest, exist_ok=True)
        shutil.copy2(m["source_path"], os.path.join(dest, os.path.basename(m["path"])))
        if k % 3000 == 0:
            print(f"  copied {k} images...", flush=True)
    with open(os.path.join(args.out_dir, "manifest.csv"), "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=["path", "class", "split", "group_id", "phash", "source_path"])
        w.writeheader()
        w.writerows(manifest)
    print(f"\ndone: {len(manifest)} images copied to {args.out_dir}, manifest.csv written")


if __name__ == "__main__":
    main()