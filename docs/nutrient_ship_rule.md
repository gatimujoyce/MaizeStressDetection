# Nutrient head: ship rule (fixed before any training)

Written on 24 October 2026, before any nutrient image model has been trained on the grouped split. This file's first commit and its push to GitHub are the record that the bar was set before the result.

## Data this rule is tied to
- Split: `data/processed/nutrient_deficiency_v2`, made by `scripts/split_nutrient_grouped.py` (seed 42, 65/15/20 by independent photo group, near-duplicate links at phash distance 5 or less, grouping confirmed by eye on 24 October 2026).
- Manifest: `results/nutrient/split_v2_manifest.csv`, git blob id f3e7724a3edbbb989984729aa2c594044a6ff8ac. Verify with `git rev-parse HEAD:results/nutrient/split_v2_manifest.csv`.
- Test split: 2,773 images. Independent test photos per class: no_deficiency 95, nitrogen 171, phosphorus 115, potassium 33, zinc 46 (source: `results/nutrient/split_v2_plan.txt`).

## Evaluation level
- Pass or fail uses image-level numbers pooled over the whole test split (n = 2,773), computed by `evaluation/evaluate_images.py` from the test split's `predictions.csv`.
- Photo-level numbers are reported alongside. Photo-level recall of a class is the mean, over that class's test photo groups, of the share of the group's images predicted correctly.
- Tiles of one photo are strongly correlated, so the real uncertainty depends on the number of independent photos. Intervals are 95% intervals from resampling photo groups (group_id from the manifest, 2,000 resamples, seed 42). They are reported but do not decide.

## The four rules (each measured once, on the test split)
| # | Condition |
|---|---|
| 1 | Macro recall at least 0.70 |
| 2 | Every class recall at least 0.50 |
| 3 | no_deficiency recall at least 0.80 |
| 4 | Among test images with confidence at least 0.80: at least 100 images, from at least 20 independent photos, with at least 85% of them correct |

Rule 4 uses confidences after calibration, if calibration was applied. Its pass or fail uses the pooled point estimate of that 85%.

## Outcomes, decided now
- Rules 1 to 4 all pass: the head ships, and the fusion rules treat confidence of 0.80 or more as strong.
- Rules 1 to 3 pass and rule 4 fails: the head ships but is capped at weak. A nutrient flag counts as weak whatever its confidence (it still needs 0.60 or more to flag at all) and cannot raise severity as a strong source.
- Any of rules 1 to 3 fails: the head is disabled (`enabled: false` in its manifest), shown as "not assessed", and the numbers and the reason go into `docs/limitations.md`.

## Budget
- At most two training runs. Anything changed between them is decided from validation results only.
- Calibration is allowed: temperature scaling (one scalar) may be fitted once, on the validation split only, between the runs or on the final model. The fitted temperature is recorded in the model manifest and must be applied wherever the model's confidences are used. Calibration is not a training run.
- The test split is evaluated exactly once, after the final model and temperature are chosen. A failure is not followed by retraining against the test result.

## Reporting
- Each measured value is reported next to its cutoff, with photo-group intervals. A value below its cutoff is a fail by however little. A near-miss is reported as a near-miss and never rounded into a pass.
- Also reported: the fused false-alarm rate, meaning the share of no_deficiency test images predicted as a deficiency class with confidence 0.60 or more (the level at which the fusion rules flag), next to rule 3's 1 minus recall.
- Potassium has only 33 independent test photos, so one or two photos can move its recall by several points and rule 2 is close to a coin flip for that class. Pass or fail still uses the point estimate.

## Status of these numbers
The cutoffs (0.70, 0.50, 0.80, 0.85, 100 images, 20 photos) are judgment calls, not derived from a requirement. Before the first training run they are to be shared with Dr Anyango. Any change must be committed to this file before the first training run starts, and after that this file is not edited.