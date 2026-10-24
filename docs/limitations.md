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

**Confidence threshold (`t_disease` = 0.55).** Chosen on the validation split only (n = 625), by a rule fixed before looking at the numbers: the lowest threshold on a 0.50 to 0.95 grid (steps of 0.05) with accuracy on accepted images of at least 0.97 and no diseased leaf accepted as healthy. At 0.55 the validation coverage is 0.9664 and accuracy on accepted images is 0.9735; gray leaf spot coverage is 0.860, so about one gray leaf spot photo in seven asks for a retake. Source: `results/disease_best/disease_v1_val/predictions.csv`; the threshold table was printed in the notebook and not saved as a file. The test split has no 0.55 row. At 0.50 its accuracy on accepted images is 0.9274 and at 0.60 it is 0.9526, so the expected test accuracy at 0.55 lies between those two values and is below the 0.97 target. Source: `confidence_analysis` in the test metrics file.

**Training data and the real-world gap.** The images come from the PlantVillage maize set, which is photographed under controlled conditions. No real-world test of the disease model has been run, so performance on phone photos taken in the field is unknown and is likely to be lower.

**Leakage check.** A perceptual-hash check (distance of 5 or less) between the train and test splits found 0 near-duplicate pairs (2,922 train and 631 test images hashed). This was run on 23 October 2026 and its console output was not saved as a file. It catches near-identical images only, so different photos of the same leaf could still appear in both splits.

**Scope.** The model covers three foliar diseases (common rust, northern leaf blight, gray leaf spot) and healthy leaves. Other diseases, pests and deficiencies are not recognised.