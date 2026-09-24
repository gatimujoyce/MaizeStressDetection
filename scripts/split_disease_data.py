import os
import random
import shutil
import imagehash
from PIL import Image

RAW_BASE = "data/raw/plantvillage_maize/data"
OUTPUT_DIR = "data/processed/plantvillage_maize"

# Map raw folder names -> final class labels (matches schema CHECK constraint values)
LABEL_MAP = {
    "Blight": "northern_leaf_blight",
    "Common_Rust": "common_rust",
    "Gray_Leaf_Spot": "gray_leaf_spot",
    "Healthy": "healthy",
}

SPLIT_RATIOS = {"train": 0.70, "val": 0.15, "test": 0.15}
RANDOM_SEED = 42
PHASH_THRESHOLD = 5


def find_and_drop_near_duplicates(folder, files):
    """Removes one image from each confirmed near-duplicate pair, keeping the first
    (alphabetically) of each pair. Returns the filtered file list."""
    phashes = {}
    for fname in files:
        path = os.path.join(folder, fname)
        try:
            phashes[fname] = imagehash.phash(Image.open(path))
        except Exception:
            continue

    fname_list = sorted(phashes.keys())
    to_drop = set()
    for i in range(len(fname_list)):
        if fname_list[i] in to_drop:
            continue
        for j in range(i + 1, len(fname_list)):
            if fname_list[j] in to_drop:
                continue
            if phashes[fname_list[i]] - phashes[fname_list[j]] <= PHASH_THRESHOLD:
                to_drop.add(fname_list[j])  # drop the later one, keep the first

    if to_drop:
        print(f"  Dropping {len(to_drop)} near-duplicate image(s): {sorted(to_drop)}")
    return [f for f in files if f not in to_drop]


def split_files(files, seed=RANDOM_SEED):
    files = sorted(files)
    random.Random(seed).shuffle(files)

    n = len(files)
    n_train = int(n * SPLIT_RATIOS["train"])
    n_val = int(n * SPLIT_RATIOS["val"])

    return {
        "train": files[:n_train],
        "val": files[n_train:n_train + n_val],
        "test": files[n_train + n_val:],
    }


def copy_split(folder, split_map, class_label):
    counts = {}
    for split_name, files in split_map.items():
        dest_dir = os.path.join(OUTPUT_DIR, split_name, class_label)
        os.makedirs(dest_dir, exist_ok=True)
        for fname in files:
            shutil.copy2(os.path.join(folder, fname), os.path.join(dest_dir, fname))
        counts[split_name] = len(files)
    return counts


def main():
    print(f"{'Class':<20} {'Total':>8} {'Dropped':>8} {'Train':>8} {'Val':>8} {'Test':>8}")
    for raw_folder_name, class_label in LABEL_MAP.items():
        folder = os.path.join(RAW_BASE, raw_folder_name)
        if not os.path.isdir(folder):
            print(f"WARNING: {folder} does not exist")
            continue

        files = [f for f in os.listdir(folder) if f.lower().endswith((".jpg", ".jpeg", ".png"))]
        original_count = len(files)

        print(f"\n{raw_folder_name}:")
        files = find_and_drop_near_duplicates(folder, files)

        split_map = split_files(files)
        counts = copy_split(folder, split_map, class_label)

        dropped = original_count - len(files)
        print(f"{class_label:<20} {original_count:>8} {dropped:>8} "
              f"{counts['train']:>8} {counts['val']:>8} {counts['test']:>8}")


if __name__ == "__main__":
    main()