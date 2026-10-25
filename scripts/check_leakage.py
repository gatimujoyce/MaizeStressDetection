import argparse
import csv
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


def main():
    parser = argparse.ArgumentParser(
        description="Check dataset train and test splits for near-duplicate images."
    )
    parser.add_argument(
        "--data-dir", default="data/processed/nutrient_deficiency",
        help="dataset directory containing the train and test splits",
    )
    parser.add_argument("--train-split", default="train", help="train split folder name")
    parser.add_argument("--test-split", default="test", help="test split folder name")
    parser.add_argument(
        "--threshold", type=int, default=5,
        help="maximum phash Hamming distance that counts as a leak (default: 5)",
    )
    parser.add_argument(
        "--max-print", type=int, default=20,
        help="maximum number of flagged pairs to print (default: 20)",
    )
    parser.add_argument(
        "--out", help="optional CSV path for every flagged pair",
    )
    args = parser.parse_args()

    train_folder = os.path.join(args.data_dir, args.train_split)
    test_folder = os.path.join(args.data_dir, args.test_split)
    train_hashes = hash_folder(train_folder)
    test_hashes = hash_folder(test_folder)

    print(f"Train images hashed: {len(train_hashes)}")
    print(f"Test images hashed: {len(test_hashes)}")

    if len(train_hashes) == 0 or len(test_hashes) == 0:
        print("WARNING: one or both folders are empty — check you're running this from the "
              "repo root (Development), not from inside scripts/.")

    # Flag any test image whose perceptual hash is very close to a train image.
    flagged_pairs = []
    affected_test_images = set()
    for test_path, test_h in test_hashes.items():
        for train_path, train_h in train_hashes.items():
            distance = test_h - train_h
            if distance <= args.threshold:  # small Hamming distance = likely near-duplicate/augmented pair
                flagged_pairs.append((test_path, train_path, distance))
                affected_test_images.add(test_path)

    for test_path, train_path, distance in flagged_pairs[:max(0, args.max_print)]:
        print(f"Possible leak: {test_path} ~ {train_path} (distance: {distance})")

    if args.out:
        with open(args.out, "w", newline="", encoding="utf-8") as csv_file:
            writer = csv.writer(csv_file)
            writer.writerow(("test_path", "train_path", "distance"))
            writer.writerows(flagged_pairs)

    leak_count = len(flagged_pairs)
    affected_count = len(affected_test_images)
    test_count = len(test_hashes)
    share = (affected_count / test_count * 100) if test_count else 0.0
    print(f"\nTotal possible leaks found: {leak_count}")
    print(f"Distinct test images with at least one flagged pair: {affected_count}")
    print(f"Test images hashed: {test_count}")
    print(f"Share of test images affected: {share:.2f}%")
    if leak_count == 0:
        print("Clean — no near-duplicate images found between train and test.")


if __name__ == "__main__":
    main()
