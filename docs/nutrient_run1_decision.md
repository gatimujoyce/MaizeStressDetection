# Nutrient head: decisions after training run 1 (before the test split was evaluated)

Written on 24 October 2026. The test split of `nutrient_deficiency_v2` had not been evaluated when this file was committed. `docs/nutrient_ship_rule.md` is unchanged.

## Decisions
- Run 1 (`models/nutrient_head/run1`, checkpoint `nutrient_run1.keras`, best validation accuracy in `training_run.json`) is the final model. There is no second training run.
- No calibration is applied (temperature = 1.0). The temperature fitted on validation (0.90) improved validation NLL and ECE only slightly, and rule 4 passes with and without it. Source: `results/nutrient_run1/nutrient_run1_val/calibration_preview.json`.
- The test split is evaluated once, next, with `evaluation/evaluate_images.py` on `nutrient_deficiency_v2/test`, and judged against the four rules in `docs/nutrient_ship_rule.md`.

## Validation results (for the record, not the decision)
Computed from `results/nutrient_run1/nutrient_run1_val/`. Validation was also used to pick the checkpoint, so these numbers are optimistic.

## Caution recorded before the test result
Nitrogen is perfectly separated on validation. The splitter treats nitrogen files as raw camera filenames (IMG...), unlike the other classes, so the model may be using the capture style. This has not been checked. A nitrogen result on this dataset does not show that nitrogen deficiency can be detected in field photos.