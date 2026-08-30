import os

print("Current working directory:", os.getcwd())
print("Contents of cwd:", os.listdir("."))
print("Does the train path exist?", os.path.exists("data/raw/nutrient_deficiency/Nutrition_dataset/train"))

import imagehash
from PIL import Image
import os

def hash_folder(folder):
    hashes = {}
    for root, _, files in os.walk(folder):
        for f in files:
            path = os.path.join(root, f)
            try:
                h = imagehash.phash(Image.open(path))
                hashes[path] = h
            except Exception:
                continue
    return hashes

train_hashes = hash_folder("data/raw/nutrient_deficiency/Nutrition_dataset/train")
test_hashes = hash_folder("data/raw/nutrient_deficiency/Nutrition_dataset/test")

# Flag any test image whose perceptual hash is very close to a train image
for test_path, test_h in test_hashes.items():
    for train_path, train_h in train_hashes.items():
        if test_h - train_h <= 5:  # small Hamming distance = likely near-duplicate/augmented pair
            print(f"Possible leak: {test_path} ~ {train_path}")


train_hashes = hash_folder("data/raw/nutrient_deficiency/Nutrition_dataset/train")
test_hashes = hash_folder("data/raw/nutrient_deficiency/Nutrition_dataset/test")

print(f"Train images hashed: {len(train_hashes)}")
print(f"Test images hashed: {len(test_hashes)}")

import os
import re
from collections import defaultdict

def get_base_ids(folder):
    base_ids = defaultdict(set)  # class_name -> set of base ids
    for class_name in os.listdir(folder):
        class_path = os.path.join(folder, class_name)
        if not os.path.isdir(class_path):
            continue
        for f in os.listdir(class_path):
            match = re.match(r"(\d+)_\d+\.jpg", f)
            if match:
                base_ids[class_name].add(match.group(1))
    return base_ids

train_base_ids = get_base_ids("data/raw/nutrient_deficiency/Nutrition_dataset/train")
test_base_ids = get_base_ids("data/raw/nutrient_deficiency/Nutrition_dataset/test")

print("Checking for shared base photo IDs between train and test:\n")
total_overlap = 0
for class_name in test_base_ids:
    overlap = train_base_ids.get(class_name, set()) & test_base_ids[class_name]
    if overlap:
        print(f"{class_name}: {len(overlap)} shared base IDs out of {len(test_base_ids[class_name])} test base IDs")
        total_overlap += len(overlap)

print(f"\nTotal classes with overlap: {sum(1 for c in test_base_ids if train_base_ids.get(c, set()) & test_base_ids[c])}")

for class_name in sorted(set(train_base_ids) | set(test_base_ids)):
    print(f"{class_name}: train={len(train_base_ids.get(class_name, set()))} base IDs, "
          f"test={len(test_base_ids.get(class_name, set()))} base IDs")