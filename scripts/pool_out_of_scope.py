import os
import shutil
import hashlib

RAW_BASE = "data/raw/pest_diseases/data"
OUTPUT_DIR = "data/negative_samples/out_of_scope"

# The four classes confirmed usable for the disease gate's out-of-scope bucket.
# (magnesium/sulphur deficiency, nitrogen/potassium/zinc deficiency, healthy, and
# "multiple" are deliberately excluded — see conversation notes / data_dictionary.md)
SOURCE_CLASSES = ["fall army worm", "stalk borer", "maize streak", "herbicide burn"]


def file_md5(path):
    hasher = hashlib.md5()
    with open(path, "rb") as f:
        hasher.update(f.read())
    return hasher.hexdigest()


def pool_classes():
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    seen_hashes = {}
    exact_dupes_skipped = 0
    total_copied = 0

    print(f"{'Class':<18} {'Found':>8} {'Copied':>8} {'Dupes skipped':>15}")
    for class_name in SOURCE_CLASSES:
        src_folder = os.path.join(RAW_BASE, class_name)
        if not os.path.isdir(src_folder):
            print(f"WARNING: {src_folder} does not exist — skipping")
            continue

        files = [f for f in os.listdir(src_folder) if f.lower().endswith((".jpg", ".jpeg", ".png"))]
        copied_this_class = 0
        dupes_this_class = 0

        # class name -> safe filename prefix (spaces -> underscores)
        prefix = class_name.replace(" ", "_")

        for fname in files:
            src_path = os.path.join(src_folder, fname)

            # Exact-duplicate check across the whole pooled set (cheap at this scale)
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
        exact_dupes_skipped += dupes_this_class
        print(f"{class_name:<18} {len(files):>8} {copied_this_class:>8} {dupes_this_class:>15}")

    print(f"\nTotal images pooled into {OUTPUT_DIR}: {total_copied}")
    if exact_dupes_skipped:
        print(f"Total exact duplicates skipped: {exact_dupes_skipped}")


if __name__ == "__main__":
    pool_classes()