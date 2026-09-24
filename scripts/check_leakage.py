import os
import imagehash
from PIL import Image


def hash_folder(folder):
    hashes = {}
    for root, _, files in os.walk(folder):
        for f in files:
            if not f.lower().endswith((".jpg", ".jpeg", ".png")):
                continue
            path = os.path.join(root, f)
            try:
                h = imagehash.phash(Image.open(path))
                hashes[path] = h
            except Exception:
                continue
    return hashes


# Pointed at the re-split, processed data — NOT the original raw train/test folders.
train_hashes = hash_folder("data/processed/nutrient_deficiency/train")
test_hashes = hash_folder("data/processed/nutrient_deficiency/test")

print(f"Train images hashed: {len(train_hashes)}")
print(f"Test images hashed: {len(test_hashes)}")

if len(train_hashes) == 0 or len(test_hashes) == 0:
    print("WARNING: one or both folders are empty — check you're running this from the "
          "repo root (Development), not from inside scripts/.")

# Flag any test image whose perceptual hash is very close to a train image.
leak_count = 0
for test_path, test_h in test_hashes.items():
    for train_path, train_h in train_hashes.items():
        if test_h - train_h <= 5:  # small Hamming distance = likely near-duplicate/augmented pair
            print(f"Possible leak: {test_path} ~ {train_path}")
            leak_count += 1

print(f"\nTotal possible leaks found: {leak_count}")
if leak_count == 0:
    print("Clean — no near-duplicate images found between train and test.")