import os
import re

PROCESSED_DIR = "data/processed/nutrient_deficiency"
CLASSES = ["no_deficiency", "nitrogen", "phosphorus", "potassium", "zinc"]


def get_grouping_key(fname):
    """Same logic as resplit_nutrient_data.py's get_grouping_key,
    applied post-hoc to verify no base ID crosses splits."""
    m = re.match(r"(\d+_\d+)_\d+\.(jpg|jpeg|png)$", fname, re.IGNORECASE)
    if m:
        return m.group(1)
    m = re.match(r"(\d+)_\d+\.(jpg|jpeg|png)$", fname, re.IGNORECASE)
    if m:
        return m.group(1)
    m = re.match(r"(IMG\d+)(?:_\d+)?\.(jpg|jpeg|png)$", fname, re.IGNORECASE)
    if m:
        return m.group(1)
    return f"__unmatched__{fname}"


def get_base_ids(split, class_name):
    folder = os.path.join(PROCESSED_DIR, split, class_name)
    ids = set()
    if not os.path.isdir(folder):
        print(f"WARNING: {folder} does not exist")
        return ids
    for fname in os.listdir(folder):
        if fname.lower().endswith((".jpg", ".jpeg", ".png")):
            ids.add(get_grouping_key(fname))
    return ids


print(f"{'Class':<14} {'Train IDs':>10} {'Val IDs':>10} {'Test IDs':>10} {'Overlap':>10}")
total_overlap = 0
for class_name in CLASSES:
    train_ids = get_base_ids("train", class_name)
    val_ids = get_base_ids("val", class_name)
    test_ids = get_base_ids("test", class_name)

    overlap = (train_ids & val_ids) | (train_ids & test_ids) | (val_ids & test_ids)
    total_overlap += len(overlap)

    print(f"{class_name:<14} {len(train_ids):>10} {len(val_ids):>10} {len(test_ids):>10} {len(overlap):>10}")
    if overlap:
        print(f"  -> Overlapping IDs: {sorted(overlap)[:10]}{' ...' if len(overlap) > 10 else ''}")

print(f"\nTotal base-ID overlap across all classes and splits: {total_overlap}")
if total_overlap == 0:
    print("Confirmed clean: no base photo ID appears in more than one split.")