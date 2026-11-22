# Disease model v2: rules fixed before training (22 Nov 2026)

Written before any v2 training or evaluation. Do not change after seeing results.

## Why
disease-v1 was trained on PlantVillage only (lab photos). It reached 92.2% on the PlantVillage test set, but on the
Bangladesh field photos (eval/bangladesh_results.csv) it called most photos northern leaf blight: common rust 0/135
correct, gray leaf spot 10/100, healthy 22/114.

## Data
- PlantVillage: the existing split in data/processed/plantvillage_maize (train, val, test), unchanged.
- Bangladesh (DOI 10.17632/sb4wwjs8bz.1, CC BY 4.0): RAW_Image only. Augmented_Images and Converted raw Images are not used.
- Classes used: Common_Rust → common_rust, Gray_Leaf_Spot → gray_leaf_spot, Healthy_Leaf → healthy,
  Corn_Leaf_Blight → northern_leaf_blight. Bacterial_Leaf_Streak, Eyespot and Maize_Streak_Disease are left out
  (not in the model's four classes).
- The Bangladesh RAW_Image folder holds each original photo as a run of about 10 re-saved copies (same size, same
  image hash, different file bytes). Distinct photos: common rust 20, gray leaf spot 12, healthy about 96,
  corn leaf blight 37 (scripts/check_bd_duplicates.py, 22 Nov).
- Bangladesh split 60/15/25 (train/val/test) by group, per class, seed 42. Group = photos within 256-bit dHash
  distance 8 of each other inside a class (one run of copies = one group). A group never crosses splits.
  Train keeps every copy; val and test keep one copy per group, so their scores count distinct photos.
  The leak check reports any test photo within distance 30 of a train/val photo, in any class.
- Changes before any training: grouping first used a 64-bit hash plus blocks of 5 photo numbers; runs of copies
  straddle the blocks and chained each class into one group (gray leaf spot: no val or test photos). Number blocks
  were dropped and the hash made 256-bit. Final settings are in split_report.json.
- Photos that look identical across two classes are left out. EXIF rotation applied; longest side 1024 px.
- Script: scripts/build_disease_v2_data.py. Output: manifest.csv and split_report.json (counts, groups, leak check).

## Training
- Same script (scripts/train_image_classifier.py) and the same hyperparameters as v1, from ImageNet weights, seed 42.
- train = PlantVillage train + Bangladesh train; val = PlantVillage val + Bangladesh val. The checkpoint is
  picked on val, as for v1. One run. A rerun is allowed only if the run crashes.
- Saved as disease_v2.keras. disease_best.keras (v1) is kept unchanged as the fallback.

## Evaluation
- Both v1 and v2 are evaluated with evaluation/evaluate_images.py on (a) the PlantVillage test set (631 images) and
  (b) the Bangladesh held-out test set. The Bangladesh test set is used once, for this comparison only.
- Confidence threshold t_disease stays 0.60 (no re-selection).

## v2 replaces v1 only if all of these hold
1. PlantVillage test accuracy ≥ 87.2% (v1 minus 5 points) and PlantVillage healthy recall ≥ 95%.
2. Bangladesh test: macro recall ≥ 70%, and no class below 50%.
3. On the Bangladesh test set, v2 recall is not lower than v1's in any class, and v2 macro recall is higher.
4. Sick Bangladesh test photos called healthy at confidence ≥ 0.80: at most 5%.

If any rule fails, v1 stays in the app and v2 is reported as an attempted improvement. There is no second round of
tuning.

## Caveats to report whatever the outcome
- Corn_Leaf_Blight may include blights other than northern leaf blight; it is treated as northern leaf blight.
- The Bangladesh test set is small (about 40 distinct photos; gray leaf spot about 3, common rust about 5), so
  report counts as well as percentages; one photo moves a small class's recall by 20-33 points.
- Training and test photos come from the same Bangladesh source, so this is not a test on Kenyan fields or the
  farmer's own phone.

## Results (22 Nov 2026, evaluated once)
| | v1 PlantVillage | v2 PlantVillage | v1 Bangladesh | v2 Bangladesh |
|---|---|---|---|---|
| n | 631 | 631 | 46 | 46 |
| Accuracy | 92.2% | 93.5% | 34.8% | 69.6% |
| Macro recall | 90.7% | 92.2% | 31.0% | 53.2% |
| Macro F1 | 0.902 | 0.917 | 0.210 | 0.512 |
| Common rust | 191/197 | 195/197 | 0/5 | 3/5 |
| Gray leaf spot | 71/87 | 74/87 | 0/3 | 1/3 |
| Healthy | 174/175 | 174/175 | 7/29 | 25/29 |
| Northern leaf blight | 146/172 | 147/172 | 9/9 | 3/9 |
| Sick called healthy at ≥ 0.80 | 0/456 | 0/456 | 0/17 | 0/17 |

Rules: 1 PASS, 2 FAIL (macro recall 53.2% < 70%; gray leaf spot and blight 33.3% < 50%), 3 FAIL (blight 3/9 vs v1 9/9),
4 PASS. Source: results/disease_v2_decision.json.

v2 on the Bangladesh test: of the 6 missed blight photos, 4 were called gray leaf spot, 1 common rust and 1 healthy
(below 0.80). Two sick photos in total were called healthy, both below 0.80. Confidence bands for the 17 sick photos:
9 strong, 4 weak, 4 uncertain.

## Decision: deviation from the pre-set rule
By the pre-set rules v1 would stay. v2 was adopted instead (Joy, 22 Nov 2026), and the deviation is reported as such.
Reason: rule 3 compared recall class by class, which rewarded v1 for calling nearly every field photo northern leaf
blight (v1 blight precision on the Bangladesh test 0.30; its 9/9 blight recall is a by-product of that bias). v2 is
better than v1 on every overall measure on both test sets and makes no strong sick-as-healthy errors. Rule 2 still
fails: v2 does not meet the field performance set beforehand and is not field-ready; this is reported as a
limitation, with more field data as future work. Rollback: models/core_classifier/manifest_v1.json.
