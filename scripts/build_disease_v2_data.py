"""Builds the disease-v2 dataset: PlantVillage train/val + Bangladesh field photos (RAW_Image only), split by group.

Output (a NEW folder; the source images are never modified):
  <out>/train/<class>/            PlantVillage train + Bangladesh train
  <out>/val/<class>/              PlantVillage val   + Bangladesh val
  <out>/test_bangladesh/<class>/  Bangladesh held-out test (never used for training or picking the checkpoint)
  <out>/manifest.csv              one row per image: source, class, split, group, original path, output path
  <out>/split_report.json         counts, group sizes and the leak check
The PlantVillage test set is not copied; evaluate on data/processed/plantvillage_maize/test as for v1.

Bangladesh photos: EXIF rotation applied (the app does the same), converted to RGB, longest side shrunk to
--max-side, saved as JPEG. Group = photos within 256-bit dHash distance --hash-threshold of each other inside a class (the dataset
holds each original photo as a run of ~10 re-saved copies; a run is one group). Train keeps every copy;
val and test keep one copy per group, so their scores count real photos.
The leak check reports test photos within --leak-threshold of any train/val photo, in any class. A whole group goes to one split.

Run from the repo root (Development), in .venv-1:
  python scripts/build_disease_v2_data.py --bd "C:\\...\\eval_data\\bangladesh_maize\\maize (corn) leaf images\\RAW_Image" --dry-run
  python scripts/build_disease_v2_data.py --bd "<same>"
"""
import argparse
import csv
import json
import os
import random
import re
import shutil
from collections import Counter, defaultdict

import numpy as np
from PIL import Image, ImageOps

CLASSES = ["common_rust", "gray_leaf_spot", "healthy", "northern_leaf_blight"]
BD_MAP = {"Common_Rust": "common_rust", "Gray_Leaf_Spot": "gray_leaf_spot",
          "Healthy_Leaf": "healthy", "Corn_Leaf_Blight": "northern_leaf_blight"}
BD_SKIPPED = ["Bacterial_Leaf_Streak", "Eyespot", "Maize_Streak_Disease"]  # unknown to the model
EXTS = (".jpg", ".jpeg", ".png", ".bmp", ".webp")
SPLITS = ["train", "val", "test"]
RATIOS = {"train": 0.60, "val": 0.15, "test": 0.25}
OUT_SPLIT = {"train": "train", "val": "val", "test": "test_bangladesh"}


class UF:
    def __init__(self, n):
        self.p = list(range(n))

    def find(self, i):
        while self.p[i] != i:
            self.p[i] = self.p[self.p[i]]
            i = self.p[i]
        return i

    def union(self, a, b):
        ra, rb = self.find(a), self.find(b)
        if ra != rb:
            self.p[max(ra, rb)] = min(ra, rb)


HASH_SIDE = 16  # 16x16 = 256-bit difference hash; the 8x8 version gave identical hashes for different field photos


def dhash(img):
    g = np.asarray(img.convert("L").resize((HASH_SIDE + 1, HASH_SIDE), Image.LANCZOS), dtype=np.int16)
    bits = (g[:, 1:] > g[:, :-1]).flatten()
    return int("".join("1" if b else "0" for b in bits), 2)


def hamming(a, b):
    return bin(a ^ b).count("1")


def photo_number(name):
    m = re.findall(r"\d+", os.path.splitext(name)[0])
    return int(m[-1]) if m else None


def load_bd(path, max_side):
    with Image.open(path) as im:
        im = ImageOps.exif_transpose(im).convert("RGB")
        w, h = im.size
        if max(w, h) > max_side:
            s = max_side / max(w, h)
            im = im.resize((round(w * s), round(h * s)), Image.LANCZOS)
        return im.copy()


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--bd", required=True, help="Bangladesh RAW_Image folder")
    ap.add_argument("--pv", default="data/processed/plantvillage_maize", help="PlantVillage split (train/val/test)")
    ap.add_argument("--out", default="data/processed/disease_v2")
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--block", type=int, default=0,
                    help="consecutive photo numbers kept together (0 = off; runs of copies straddle blocks and chain)")
    ap.add_argument("--hash-threshold", type=int, default=8, help="256-bit dHash distance that joins two photos into one group (-1 = off)")
    ap.add_argument("--leak-threshold", type=int, default=30, help="256-bit dHash distance reported by the leak check")
    ap.add_argument("--max-side", type=int, default=1024)
    ap.add_argument("--dry-run", action="store_true", help="print the plan, write nothing")
    args = ap.parse_args()

    if not args.dry_run and os.path.isdir(args.out) and os.listdir(args.out):
        raise SystemExit(f"ERROR: {args.out} already has files. Delete it yourself or pass another --out.")
    for split in ("train", "val"):
        for c in CLASSES:
            if not os.path.isdir(os.path.join(args.pv, split, c)):
                raise SystemExit(f"ERROR: missing PlantVillage folder {os.path.join(args.pv, split, c)}")
    for folder in BD_MAP:
        if not os.path.isdir(os.path.join(args.bd, folder)):
            raise SystemExit(f"ERROR: missing Bangladesh folder {os.path.join(args.bd, folder)}")

    # ---- Bangladesh: load, hash, group, split ----
    items = []  # dict per image
    for folder, cls in BD_MAP.items():
        for f in sorted(os.listdir(os.path.join(args.bd, folder))):
            if f.lower().endswith(EXTS):
                src = os.path.join(args.bd, folder, f)
                try:
                    im = load_bd(src, args.max_side)
                except Exception as exc:  # unreadable file: report, do not use
                    print(f"WARNING: skipped unreadable {src}: {exc}")
                    continue
                items.append({"cls": cls, "name": f, "src": src, "hash": dhash(im), "num": photo_number(f),
                              "img": None if args.dry_run else im})
    print("Bangladesh images used:", len(items), dict(Counter(i["cls"] for i in items)))

    # distance distribution, to judge the thresholds
    hs = [it["hash"] for it in items]
    nearest = [min(hamming(hs[i], hs[j]) for j in range(len(hs)) if j != i) for i in range(len(hs))]
    print("Nearest-neighbour hash distance (256 bits): min", min(nearest), "| 5th pct",
          int(np.percentile(nearest, 5)), "| median", int(np.median(nearest)))

    # same picture filed under two classes = label noise; report it, keep it out of training
    by_hash = defaultdict(set)
    for it in items:
        by_hash[it["hash"]].add(it["cls"])
    conflicts = [it for it in items if len(by_hash[it["hash"]]) > 1]
    if conflicts:
        print(f"WARNING: {len(conflicts)} Bangladesh images appear identical across classes; they are left out:")
        for it in conflicts[:10]:
            print("   ", it["src"])
    conflict_srcs = {it["src"] for it in conflicts}
    items = [it for it in items if it["src"] not in conflict_srcs]

    assign, group_of, report_groups = {}, {}, {}
    for cls in CLASSES:
        cl = [it for it in items if it["cls"] == cls]
        n = len(cl)
        uf = UF(n)
        first = {}
        for i, it in enumerate(cl):
            if args.block > 0 and it["num"] is not None:
                k = it["num"] // args.block
                if k in first:
                    uf.union(first[k], i)
                else:
                    first[k] = i
        block_groups = len({uf.find(i) for i in range(n)})
        for i in range(n):
            for j in range(i + 1, n):
                if args.hash_threshold >= 0 and hamming(cl[i]["hash"], cl[j]["hash"]) <= args.hash_threshold:
                    uf.union(i, j)
        comps = defaultdict(list)
        for i in range(n):
            comps[uf.find(i)].append(i)
        groups = sorted(comps.values(), key=lambda g: min(cl[i]["name"] for i in g))
        order = list(range(len(groups)))
        random.Random(f"{args.seed}-{cls}").shuffle(order)
        order.sort(key=lambda gi: len(groups[gi]), reverse=True)
        targets = {s: RATIOS[s] * n for s in SPLITS}
        filled = {s: 0 for s in SPLITS}
        for gi in order:
            s = max(SPLITS, key=lambda sp: (targets[sp] - filled[sp]) / targets[sp])
            filled[s] += len(groups[gi])
            for i in groups[gi]:
                assign[cl[i]["src"]] = s
                group_of[cl[i]["src"]] = f"{cls}-g{gi:03d}"
        report_groups[cls] = {"images": n, "groups": len(groups), "groups_from_numbers_only": block_groups,
                              "largest_group": max(len(g) for g in groups) if groups else 0,
                              "split": filled}

    # ---- val/test keep one copy per group (one original photo); train keeps every copy ----
    seen, dropped = set(), []
    for it in items:
        s_ = assign[it["src"]]
        if s_ == "train":
            continue
        key = group_of[it["src"]]
        if key in seen:
            dropped.append(it["src"])
        else:
            seen.add(key)
    dropped_set = set(dropped)
    items = [it for it in items if it["src"] not in dropped_set]
    print(f"Copies removed from val/test (same photo, kept once): {len(dropped)}")
    uniq = defaultdict(set)
    for it in items:
        uniq[(assign[it["src"]], it["cls"])].add(group_of[it["src"]])

    # ---- leak check: any test photo close to a train/val photo, in ANY class ----
    test = [it for it in items if assign[it["src"]] == "test"]
    fit = [it for it in items if assign[it["src"]] != "test"]
    leaks = []
    for t in test:
        for o in fit:
            d = hamming(t["hash"], o["hash"])
            if d <= args.leak_threshold:
                leaks.append({"test": t["src"], "train_or_val": o["src"], "distance": d,
                              "same_class": t["cls"] == o["cls"]})
    print(f"Leak check: {len(set(l['test'] for l in leaks))} test photos within dHash distance {args.leak_threshold} of a train/val photo "
          f"({len(leaks)} close pairs, {sum(not l['same_class'] for l in leaks)} across classes)")

    # ---- PlantVillage train/val (copied as they are) ----
    pv = []
    for split in ("train", "val"):
        for c in CLASSES:
            folder = os.path.join(args.pv, split, c)
            for f in sorted(os.listdir(folder)):
                if f.lower().endswith(EXTS):
                    pv.append((split, c, f, os.path.join(folder, f)))

    table = defaultdict(Counter)
    for split, c, _, _ in pv:
        table[f"pv_{split}"][c] += 1
    for it in items:
        table[f"bd_{assign[it['src']]}"][it["cls"]] += 1
    print("\nImages per split and class:")
    cols = ["pv_train", "bd_train", "pv_val", "bd_val", "bd_test"]
    print(f"{'class':<22}" + "".join(f"{c:>10}" for c in cols))
    for c in CLASSES:
        print(f"{c:<22}" + "".join(f"{table[k][c]:>10}" for k in cols))
    print(f"{'total':<22}" + "".join(f"{sum(table[k].values()):>10}" for k in cols))
    print("Different photos (groups) in bd_train / bd_val / bd_test:")
    for c in CLASSES:
        print(f"  {c:<22}" + " / ".join(str(len(uniq[(sp, c)])) for sp in SPLITS))
    for c, g in report_groups.items():
        print(f"  {c}: {g['groups']} groups ({g['groups_from_numbers_only']} from photo numbers alone), "
              f"largest {g['largest_group']} photos")

    if args.dry_run:
        print("\nDry run: nothing written.")
        return

    # ---- write ----
    rows = []
    for split, c, f, src in pv:
        dst = os.path.join(args.out, split, c, f"pv_{f}")
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        shutil.copy2(src, dst)
        rows.append(["plantvillage", c, split, "", src, dst])
    for it in items:
        split = assign[it["src"]]
        stem = os.path.splitext(it["name"])[0]
        dst = os.path.join(args.out, OUT_SPLIT[split], it["cls"], f"bd_{stem}.jpg")
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        if os.path.exists(dst):
            raise SystemExit(f"ERROR: two Bangladesh files map to {dst}")
        it["img"].save(dst, "JPEG", quality=95)
        rows.append(["bangladesh", it["cls"], OUT_SPLIT[split], group_of[it["src"]], it["src"], dst])
    with open(os.path.join(args.out, "manifest.csv"), "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["source", "class", "split", "group", "original_path", "output_path"])
        w.writerows(rows)
    with open(os.path.join(args.out, "split_report.json"), "w", encoding="utf-8") as fh:
        json.dump({"args": vars(args), "ratios": RATIOS, "bangladesh_map": BD_MAP, "bangladesh_skipped": BD_SKIPPED,
                   "cross_class_duplicates_removed": [it["src"] for it in conflicts],
                   "val_test_copies_removed": dropped,
                   "unique_photos": {f"{sp}/{c}": len(uniq[(sp, c)]) for sp in SPLITS for c in CLASSES},
                   "counts": {k: dict(v) for k, v in table.items()}, "groups": report_groups, "leaks": leaks},
                  fh, indent=2)
    print(f"\nWritten to {args.out} (manifest.csv, split_report.json)")


if __name__ == "__main__":
    main()
