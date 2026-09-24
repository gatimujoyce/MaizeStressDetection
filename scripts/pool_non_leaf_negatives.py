import os
import random
import shutil
import hashlib

COLOR_DIR = "data/raw/other_crops/plantvillage dataset/color"
OUTPUT_DIR = "data/negative_samples/non_leaf/other_crops"

SAMPLES_PER_CLASS = 60  # capped so no single crop/disease subclass dominates
RANDOM_SEED = 42


def file_md5(path):
    hasher = hashlib.md5()
    with open(path, "rb") as f:
        hasher.update(f.read())
    return hasher.hexdigest()


def main():
    if not os.path.isdir(COLOR_DIR):
        print(f"ERROR: {COLOR_DIR} does not exist — check the folder name/path")
        return

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    rng = random.Random(RANDOM_SEED)

    seen_hashes = {}
    total_copied = 0
    total_dupes_skipped = 0

    all_classes = sorted(os.listdir(COLOR_DIR))
    # Exclude maize/corn — must never leak into the non-maize negative pool
    excluded = [c for c in all_classes if c.lower().startswith("corn_")]
    usable_classes = [c for c in all_classes if c not in excluded]

    print(f"Excluding {len(excluded)} maize class folder(s): {excluded}")
    print(f"\n{'Class':<55} {'Found':>8} {'Sampled':>8} {'Dupes':>6}")

    for class_name in usable_classes:
        class_path = os.path.join(COLOR_DIR, class_name)
        if not os.path.isdir(class_path):
            continue

        files = [f for f in os.listdir(class_path) if f.lower().endswith((".jpg", ".jpeg", ".png"))]
        if not files:
            continue

        sample_size = min(SAMPLES_PER_CLASS, len(files))
        sampled_files = rng.sample(files, sample_size)

        # Safe filename prefix from the class name
        prefix = class_name.replace(" ", "_").replace(",", "").replace("(", "").replace(")", "")

        copied_this_class = 0
        dupes_this_class = 0

        for fname in sampled_files:
            src_path = os.path.join(class_path, fname)
            try:
                h = file_md5(src_path)
            except Exception:
                continue
            if h in seen_hashes:
                dupes_this_class += 1
                continue
            seen_hashes[h] = f"{prefix}__{fname}"

            dest_name = f"{prefix}__{fname}"
            dest_path = os.path.join(OUTPUT_DIR, dest_name)
            shutil.copy2(src_path, dest_path)  # copy, never move — raw/ stays untouched
            copied_this_class += 1

        total_copied += copied_this_class
        total_dupes_skipped += dupes_this_class
        print(f"{class_name:<55} {len(files):>8} {copied_this_class:>8} {dupes_this_class:>6}")

    print(f"\nTotal non-leaf negative images pooled into {OUTPUT_DIR}: {total_copied}")
    if total_dupes_skipped:
        print(f"Total exact duplicates skipped: {total_dupes_skipped}")


if __name__ == "__main__":
    main()