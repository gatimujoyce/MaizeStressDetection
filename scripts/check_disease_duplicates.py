import os
import hashlib
import imagehash
from PIL import Image

CLASS_FOLDERS = {
    "Blight": "data/raw/plantvillage_maize/data/Blight",
    "Common_Rust": "data/raw/plantvillage_maize/data/Common_Rust",
    "Gray_Leaf_Spot": "data/raw/plantvillage_maize/data/Gray_Leaf_Spot",
    "Healthy": "data/raw/plantvillage_maize/data/Healthy",
}

PHASH_THRESHOLD = 5  # same threshold used before; small Hamming distance = likely near-duplicate


def file_md5(path):
    """Exact-duplicate check: identical file content, byte for byte."""
    hasher = hashlib.md5()
    with open(path, "rb") as f:
        hasher.update(f.read())
    return hasher.hexdigest()


def analyze_folder(class_name, folder):
    if not os.path.isdir(folder):
        print(f"WARNING: {folder} does not exist")
        return

    files = [f for f in os.listdir(folder) if f.lower().endswith((".jpg", ".jpeg", ".png"))]
    print(f"\n=== {class_name} ({len(files)} images) ===")

    # --- Exact duplicate check (fast, byte-for-byte) ---
    md5_map = {}
    exact_dupes = 0
    for fname in files:
        path = os.path.join(folder, fname)
        try:
            h = file_md5(path)
        except Exception:
            continue
        if h in md5_map:
            print(f"  EXACT duplicate: {fname}  ==  {md5_map[h]}")
            exact_dupes += 1
        else:
            md5_map[h] = fname
    print(f"  Exact duplicates found: {exact_dupes}")

    # --- Near-duplicate check (perceptual hash, catches resized/re-encoded/augmented copies) ---
    phashes = {}
    near_dupe_pairs = 0
    for fname in files:
        path = os.path.join(folder, fname)
        try:
            phashes[fname] = imagehash.phash(Image.open(path))
        except Exception:
            continue

    fname_list = list(phashes.keys())
    for i in range(len(fname_list)):
        for j in range(i + 1, len(fname_list)):
            f1, f2 = fname_list[i], fname_list[j]
            if phashes[f1] - phashes[f2] <= PHASH_THRESHOLD:
                near_dupe_pairs += 1
    print(f"  Near-duplicate pairs found (phash <= {PHASH_THRESHOLD}): {near_dupe_pairs}")


def main():
    for class_name, folder in CLASS_FOLDERS.items():
        analyze_folder(class_name, folder)


if __name__ == "__main__":
    main()