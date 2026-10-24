# Limitations

Document known data, model, deployment, and operational limitations here.

## Model limitations

### Gate (gate_best.keras)

**In-scope images wrongly rejected.** The gate wrongly rejected 4 of 220 in-scope images, an in-scope wrongly rejected rate of `0.01818181818181818`. Source: `results/gate_best/gate_v1_recheck/metrics.json` (`task_extras.in_scope_wrongly_rejected_rate`; `per_class` entry `in_scope`, `support`), and `results/gate_best/gate_v1_recheck/predictions.csv` (rejected rows below).

| Image path | Disease class (image_path prefix before `__`) | Predicted label | Confidence |
|---|---|---|---|
| `in_scope/gray_leaf_spot__Corn_Gray_Spot (37).jpg` | `gray_leaf_spot` | `out_of_scope` | `0.587970` |
| `in_scope/northern_leaf_blight__Corn_Blight (1114).jpg` | `northern_leaf_blight` | `out_of_scope` | `0.795794` |
| `in_scope/northern_leaf_blight__Corn_Blight (37).jpg` | `northern_leaf_blight` | `out_of_scope` | `0.907046` |
| `in_scope/northern_leaf_blight__Corn_Blight (78).jpg` | `northern_leaf_blight` | `out_of_scope` | `0.869634` |

The severity of the disease in these images has not been checked by viewing them. The practical effect is that a farmer can be asked to retake a photo of a genuinely diseased leaf.

**Evaluation basis.** These gate figures come from the test split of the same dataset pools used for training. The real-world gate test (phase P5) has not been run yet, so the threshold is provisional. Source: `results/gate_best/gate_v1_recheck/metrics.json` (test-split evaluation metrics); real-world test status: guide section 12 (risks).



### Disease classifier (disease_best.keras)

**Test performance.** On the held-out test split (n = 631) the model reaches accuracy 0.9223 and macro F1 0.9020. Source: `results/disease_best/disease_v1_test/metrics.json`. The checkpoint was chosen by validation accuracy (0.9616, `models/core_classifier/training_run.json`), so the validation figures are optimistic and the test figures are the ones to report. The test split was evaluated once and not used for any tuning.

**Per-class recall on test** (same file): common_rust 0.9695, healthy 0.9943, northern_leaf_blight 0.8488, gray_leaf_spot 0.8161 (only 87 test images, so this figure is uncertain).

**Weakest point: gray leaf spot versus northern leaf blight.** Of the 49 test errors, 40 are confusions between these two diseases (15 gray leaf spot called northern leaf blight, 25 the other way round). Source: `confusion_matrix` in the same metrics file. Both are foliar diseases, so a sick leaf is still flagged as sick, but the disease label, and therefore the advice, can be wrong.

**Safety property.** No diseased leaf was called healthy on test (`diseased_called_healthy_rate` = 0.0). One healthy leaf was called diseased (`healthy_called_diseased_rate` = 0.0057). On the validation split no diseased leaf was accepted as healthy at any confidence threshold. Sources: `task_extras` in the test and validation metrics files.

**Confidence threshold (`t_disease` = 0.55).** Chosen on the validation split only (n = 625), by a rule fixed before looking at the numbers: the lowest threshold on a 0.50 to 0.95 grid (steps of 0.05) with accuracy on accepted images of at least 0.97 and no diseased leaf accepted as healthy. At 0.55 the validation coverage is 0.9664 and accuracy on accepted images is 0.9735; gray leaf spot coverage is 0.860, so about one gray leaf spot photo in seven asks for a retake. Source: `results/disease_best/disease_v1_val/predictions.csv`; the threshold table was recomputed from this file and saved as results/disease_best/disease_v1_val/threshold_table.csv. The test split has no 0.55 row. At 0.50 its accuracy on accepted images is 0.9274 and at 0.60 it is 0.9526, so the expected test accuracy at 0.55 lies between those two values and is below the 0.97 target. Source: `confidence_analysis` in the test metrics file.

**Training data and the real-world gap.** The images come from the PlantVillage maize set, which is photographed under controlled conditions. No real-world test of the disease model has been run, so performance on phone photos taken in the field is unknown and is likely to be lower.

**Leakage check.** A perceptual-hash check (distance of 5 or less) between the train and test splits found 0 near-duplicate pairs (2,922 train and 631 test images hashed). This was run on 23 October 2026 and its console output was not saved as a file. It catches near-identical images only, so different photos of the same leaf could still appear in both splits.

**Scope.** The model covers three foliar diseases (common rust, northern leaf blight, gray leaf spot) and healthy leaves. Other diseases, pests and deficiencies are not recognised.



### Gate: near-duplicate check (added 24 October 2026)

A perceptual-hash check (phash distance of 5 or less) between the train and test splits of the gate dataset flagged 11 of the 623 test images (1.77%). Source: `results/gate_best/gate_leakage_check.txt`; every pair is in `results/gate_best/gate_leakage_pairs.csv`. All 11 are out_of_scope images, 10 from fall_army_worm and 1 from maize_streak, so 11 of the 97 out_of_scope test images (11.3%) have a near-twin in train. The one pair that was inspected is two photos taken one second apart (`maize_streak__IMG_20190523_134751_5.jpg` and `maize_streak__IMG_20190523_134752_4.jpg`, distance 4); the other ten were not inspected. No in_scope or not_leaf test image was flagged. Effect: the out_of_scope rejection figures from the test split may be slightly optimistic. The real-world gate test (phase P5) has not been run and remains the evidence that counts.

### Sensor classifier (sensor_v2.keras and sensor_v2_no_stage.keras)

**Simulated data.** The sensor data is simulated, not recorded by real sensors (`results/sensor/sensor_model_card.md`); according to the implementation guide (section 12) it is generated from rules plus overlap noise (`OVERLAP_SCALE` 1.25). The results below show that the training and evaluation pipeline works. They do not show that the model works on real sensors, and it has not been validated on any.

**Results on the simulated test set** (source: `results/sensor/comparison.md`). Accuracy: rule baseline 0.9217, full network (with growth stage) 0.9490 ± 0.0017, no-stage network 0.9500 ± 0.0026 (mean and spread over seeds). The full network beats the baseline by 0.0267, more than the seed-to-seed spread, and the no-stage network is within seed variation of the full network (difference 0.0017). The baseline uses the threshold rules (waterlogging above 110% of field capacity, drought below 55%, heat at 32 degrees C or above; `results/sensor/sensor_model_card.md`) that the simulation is built on, so a gain over it on this data says little about the gain on real sensors.

**Model card discrepancy.** The generated model card quotes 0.9483 for the full network, while `comparison.md` gives 0.9490. The reason was not checked and this document uses `comparison.md`. The card's own Limitations heading is empty.

**Scope.** The evaluation is per row of the test file. No aggregation over a time window has been built or evaluated in the ML track so far.

### Nutrient classifier (nutrient_run1.keras)

**The original split leaked and was replaced.** On the first split, 4,953 train and test pairs (718 of 2,080 test images, 34.52%) and 5,577 train and validation pairs (720 of 2,045 validation images, 35.21%) were near-duplicates (phash distance 5 or less). Sources: `results/nutrient/leakage_check.txt` and `results/nutrient/leakage_check_train_vs_val.txt`. The existing ID check (`scripts/verify_no_id_overlap.py`) reported 0 overlap because it applies the same grouping rule that built the split, so it cannot detect a wrong rule. Potassium photo 0431 has 25 tiles, of which 10 were in train and 15 in test (`results/nutrient/potassium_one_photo.png`); in zinc, images with different photo numbers are near-identical (`results/nutrient/zinc_linked_pairs.png`). Photo groups: potassium 861 under the old rule against 162 after merging photo numbers and near-duplicate links; zinc 509 against 243 (`results/nutrient/group_analysis.txt`). There are 0 cross-class links at distance 5 or less (`results/nutrient/cross_class_links.txt`). No model was trained or evaluated on the leaked split.

**The new split.** `scripts/split_nutrient_grouped.py` splits by independent photo group, 65/15/20, seed 42, written to `data/processed/nutrient_deficiency_v2`: 8,932 train, 2,076 validation and 2,773 test images, with independent test photos per class: no_deficiency 95, nitrogen 171, phosphorus 115, potassium 33, zinc 46 (`results/nutrient/split_v2_plan.txt`, `results/nutrient/split_v2_manifest.csv`). `tests/test_nutrient_split.py` checks that no group is in two splits and that no cross-split pair has a distance of 5 or less. That test uses the same distance as the grouping, so it is a consistency check. A perceptual hash would not link a rotated copy of a photo; this was not checked.

**Ship rule and result.** The ship rule (`docs/nutrient_ship_rule.md`) was committed before any training; the two cutoffs and the pooled evaluation level were judgment calls, not derived values. The test split was evaluated once (`results/nutrient_run1/nutrient_run1_test/test_decision.json`, `results/nutrient_run1/nutrient_run1_test/metrics.json`): accuracy 0.9383; macro recall 0.9527; recall nitrogen 0.9967, no_deficiency 0.9918, phosphorus 0.9782, zinc 0.9314, potassium 0.8653. Images with confidence 0.80 or more: 2,555 from 451 photos, precision 0.9656. Rate of no_deficiency images predicted as a deficiency at confidence 0.60 or more: 0.0021. All four rules passed and the verdict is SHIPS. The checkpoint was chosen on the validation split, so the validation figures are optimistic (best validation accuracy 0.9672, `models/nutrient_head/run1/training_run.json`). No calibration was applied (`docs/nutrient_run1_decision.md`).

**Weakest classes.** Potassium recall is 0.8653 with a 95% interval of 0.753 to 0.958, based on only 33 independent test photos; zinc is 0.9314 (interval 0.828 to 0.975, 46 photos). Of the 171 test errors, 118 are potassium (63 called phosphorus, 55 called zinc) and 35 are zinc (14 called phosphorus, 21 called potassium). Intervals come from resampling photo groups (2,000 resamples, seed 42).

**Nitrogen is captured differently from the other classes.** All 1,535 nitrogen images are camera-style files in 1,320 different sizes with a median file size of 150.3 KB; the other four classes are tiny crops in exactly two sizes with median file sizes between 5.2 and 8.3 KB, and potassium is cut into numbered tiles (`results/nutrient/capture_style.txt`). Nitrogen's near-perfect score is therefore not evidence that nitrogen deficiency can be detected. In a check on the validation split only (`results/nutrient_run1/nutrient_run1_val_diagB/diagB_result.json`), nitrogen images were cropped, shrunk to 100x200 and recompressed to a median of 6.94 KB: nitrogen recall went from 1.0000 to 0.9827 (4 errors in 231). That is little evidence of reliance on resolution or file size, but every image is resized to 224x224 before the model sees it, colour, background and lighting differences were not removed, and potassium (also separable by file size and tiling) was not tested.

**Post-hoc decision.** After the test evaluation, a nitrogen call is capped at weak in fusion, whatever its confidence. This is separate from the pre-registered rule (`docs/nutrient_posthoc_findings.md`). It is lifted only if a check on real phone photos supports it; that smoke test has not been run.

**Real-world gap (both image models).** Every class of the disease and nutrient datasets is studio-style. No field test of either model has been run, so performance on phone photos is unknown and likely lower.