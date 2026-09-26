import os
import random
import shutil

# Existing, already-split disease data — reuse its train/val/test assignment as-is
DISEASE_PROCESSED = "data/processed/plantvillage_maize"
DISEASE_CLASSES = ["healthy", "common_rust", "northern_leaf_blight", "gray_leaf_spot"]

# Not-yet-split negative pools
OUT_OF_SCOPE_POOL = "data/negative_samples/out_of_scope"
NON_LEAF_POOL = "data/negative_samples/non_leaf/other_crops"

OUTPUT_DIR = "data/processed/triage_gate"

SPLIT_RATIOS = {"train": 0.70, "val": 0.15, "test": 0.15}
RANDOM_SEED = 42

# Per-class, per-split cap for in-scope sampling, so this class doesn't dwarf
# the negative classes (which sit at ~641 and ~2040 total). Uses min(cap, available)
# so smaller classes (e.g. gray_leaf_spot) just contribute what they have.
IN_SCOPE_CAP = {"train": 260, "val": 55, "test": 55}


def split_flat_pool(pool_dir, seed=RANDOM_SEED):
    """Fresh random split for a flat, not-yet-split folder of images."""
    files = [f for f in os.listdir(pool_dir) if f.lower().endswith((".jpg", ".jpeg", ".png"))]
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


def copy_negative_class(pool_dir, split_map, gate_class_name):
    counts = {}
    for split_name, files in split_map.items():
        dest_dir = os.path.join(OUTPUT_DIR, split_name, gate_class_name)
        os.makedirs(dest_dir, exist_ok=True)
        for fname in files:
            shutil.copy2(os.path.join(pool_dir, fname), os.path.join(dest_dir, fname))
        counts[split_name] = len(files)
    return counts


def copy_in_scope(seed=RANDOM_SEED):
    """Samples from the EXISTING disease split folders, preserving their
    train/val/test assignment rather than re-splitting."""
    rng = random.Random(seed)
    counts = {"train": 0, "val": 0, "test": 0}

    for split_name in ["train", "val", "test"]:
        dest_dir = os.path.join(OUTPUT_DIR, split_name, "in_scope")
        os.makedirs(dest_dir, exist_ok=True)
        cap = IN_SCOPE_CAP[split_name]

        for class_name in DISEASE_CLASSES:
            src_dir = os.path.join(DISEASE_PROCESSED, split_name, class_name)
            if not os.path.isdir(src_dir):
                print(f"WARNING: {src_dir} does not exist — skipping")
                continue

            files = [f for f in os.listdir(src_dir) if f.lower().endswith((".jpg", ".jpeg", ".png"))]
            sample_size = min(cap, len(files))
            sampled = rng.sample(files, sample_size)

            prefix = class_name  # keep source class visible in filename for traceability
            for fname in sampled:
                dest_name = f"{prefix}__{fname}"
                shutil.copy2(os.path.join(src_dir, fname), os.path.join(dest_dir, dest_name))
                counts[split_name] += 1

    return counts


def main():
    print("=== In-scope (sampled from existing disease split, assignment preserved) ===")
    in_scope_counts = copy_in_scope()
    for split_name, count in in_scope_counts.items():
        print(f"  {split_name}: {count}")

    print("\n=== Out-of-scope (fresh 70/15/15 split) ===")
    oos_split = split_flat_pool(OUT_OF_SCOPE_POOL)
    oos_counts = copy_negative_class(OUT_OF_SCOPE_POOL, oos_split, "out_of_scope")
    for split_name, count in oos_counts.items():
        print(f"  {split_name}: {count}")

    print("\n=== Not-leaf (fresh 70/15/15 split) ===")
    nl_split = split_flat_pool(NON_LEAF_POOL)
    nl_counts = copy_negative_class(NON_LEAF_POOL, nl_split, "not_leaf")
    for split_name, count in nl_counts.items():
        print(f"  {split_name}: {count}")

    print(f"\n{'Split':<8} {'in_scope':>10} {'out_of_scope':>14} {'not_leaf':>10} {'Total':>8}")
    for split_name in ["train", "val", "test"]:
        total = in_scope_counts[split_name] + oos_counts[split_name] + nl_counts[split_name]
        print(f"{split_name:<8} {in_scope_counts[split_name]:>10} {oos_counts[split_name]:>14} "
              f"{nl_counts[split_name]:>10} {total:>8}")


if __name__ == "__main__":
    main()