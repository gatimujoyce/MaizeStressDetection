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
