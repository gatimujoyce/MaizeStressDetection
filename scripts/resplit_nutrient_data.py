import os
import re
import random
import shutil
from collections import defaultdict

# --- Config ---
RAW_TRAIN = "data/raw/nutrient_deficiency/Nutrition_dataset/train"
RAW_TEST = "data/raw/nutrient_deficiency/Nutrition_dataset/test"
OUTPUT_DIR = "data/processed/nutrient_deficiency"

# Map raw folder names -> final class labels. Deliberately excludes "ALL Present".
LABEL_MAP = {
    "ALLAB": "no_deficiency",
    "NAB": "nitrogen",
    "PAB": "phosphorus",
    "KAB": "potassium",
    "ZNAB": "zinc",
}

SPLIT_RATIOS = {"train": 0.70, "val": 0.15, "test": 0.15}
RANDOM_SEED = 42


def get_grouping_key(fname, raw_class_name):
    """
    Returns a base-ID string used to group augmented variants of the same
    source photo together, so they never get split across train/val/test.
    Falls back to treating the file as its own independent group if no
    known pattern matches (safe default: cannot cause leakage, may just
    be slightly more conservative than necessary).
    """
    # KAB pattern: 0347_0_1.jpg -> base id = "0347_0"
    m = re.match(r"(\d+_\d+)_\d+\.(jpg|jpeg|png)$", fname, re.IGNORECASE)
    if m:
        return m.group(1)

    # Standard pattern used elsewhere (ZNAB, ALLAB, PAB, ALL Present): 2074_3.jpg -> base id = "2074"
    m = re.match(r"(\d+)_\d+\.(jpg|jpeg|png)$", fname, re.IGNORECASE)
    if m:
        return m.group(1)

    # NAB raw camera filenames: IMG20230319153455.jpg / IMG20230319153455_01.jpg
    # Collapse the _01-style duplicate-shot suffix onto the same base timestamp.
    m = re.match(r"(IMG\d+)(?:_\d+)?\.(jpg|jpeg|png)$", fname, re.IGNORECASE)
    if m:
        return m.group(1)

    # Fallback: no recognized pattern — treat as its own independent group
    return f"__unmatched__{raw_class_name}__{fname}"


def collect_images_by_base_id(class_folder_paths, raw_class_name):
    """Returns {base_id: [list of full file paths]} pooling across all given folders."""
    grouped = defaultdict(list)
    unmatched_count = 0
    for folder in class_folder_paths:
        if not os.path.isdir(folder):
            continue
        for fname in os.listdir(folder):
            if not fname.lower().endswith((".jpg", ".jpeg", ".png")):
                continue
            key = get_grouping_key(fname, raw_class_name)
            if key.startswith("__unmatched__"):
                unmatched_count += 1
            grouped[key].append(os.path.join(folder, fname))
    if unmatched_count:
        print(f"  Note: {unmatched_count} files in {raw_class_name} didn't match a known "
              f"pattern and were treated as independent images (safe default).")
    return grouped


def split_base_ids(base_ids, seed=RANDOM_SEED):
    base_ids = sorted(base_ids)  # sort first for reproducibility across runs/machines
    random.Random(seed).shuffle(base_ids)

    n = len(base_ids)
    n_train = int(n * SPLIT_RATIOS["train"])
    n_val = int(n * SPLIT_RATIOS["val"])

    train_ids = set(base_ids[:n_train])
    val_ids = set(base_ids[n_train:n_train + n_val])
    test_ids = set(base_ids[n_train + n_val:])
    return train_ids, val_ids, test_ids


def copy_split(grouped, id_split_map, class_label):
    counts = {"train": 0, "val": 0, "test": 0}
    for base_id, file_paths in grouped.items():
        split_name = id_split_map[base_id]
        dest_dir = os.path.join(OUTPUT_DIR, split_name, class_label)
        os.makedirs(dest_dir, exist_ok=True)
        for src_path in file_paths:
            dest_path = os.path.join(dest_dir, os.path.basename(src_path))
            shutil.copy2(src_path, dest_path)  # copy, never move — raw/ stays untouched
            counts[split_name] += 1
    return counts


def main():
    print(f"{'Class':<14} {'BaseIDs':>8} {'Train':>8} {'Val':>8} {'Test':>8}")
    for raw_folder_name, class_label in LABEL_MAP.items():
        class_paths = [
            os.path.join(RAW_TRAIN, raw_folder_name),
            os.path.join(RAW_TEST, raw_folder_name),
        ]
        grouped = collect_images_by_base_id(class_paths, raw_folder_name)

        if not grouped:
            print(f"WARNING: no images found for {raw_folder_name} — check folder name/path")
            continue

        train_ids, val_ids, test_ids = split_base_ids(grouped.keys())
        id_split_map = {}
        for bid in train_ids: id_split_map[bid] = "train"
        for bid in val_ids: id_split_map[bid] = "val"
        for bid in test_ids: id_split_map[bid] = "test"

        counts = copy_split(grouped, id_split_map, class_label)
        print(f"{class_label:<14} {len(grouped):>8} {counts['train']:>8} {counts['val']:>8} {counts['test']:>8}")


if __name__ == "__main__":
    main()