# Photo quality check: second calibration pass (criteria fixed before it was run)

Written on 25 October 2026. This is a post-hoc check: the first pass (percentile rule, `results/quality/calibration.txt`) had already been seen, and it showed that rule to be the wrong tool (it rejected 3.33% of test originals and caught 6.7% of blur-radius-2 copies). The test split was therefore used for a quality report twice. No model is tuned on it. Both passes are kept as evidence.

## What is tested
The placeholder thresholds in `models/quality/quality_rules.yaml`, untouched: min_side_px 224, dark_mean 40, bright_mean 225, blur_laplacian_var 30. Images: the disease validation and test images (`data/processed/plantvillage_maize`). Degradations are synthetic (blur radius 2 and 4, darkened to 20%, glare +150) and are not real phone failures.

## Criteria
- Size, darkness and brightness: reported as they are (false rejections on originals, degradations caught). No tuning, no pass or fail.
- Blur: pass or fail is decided on the validation split only. The 30 limit stays only if, on validation, it rejects at most 2% of originals for blur and catches at least 80% of the blur-radius-4 copies. Otherwise the blur check is switched off in the config (`blur_laplacian_var: 0`) and sharpness is reported as not reliably measurable on this data.
- The test split is reported next to validation and is not used to decide.

## Reading the result
- Laplacian variance depends on resolution and on image content, and these images are small studio crops. Whatever happens here does not transfer to phone photos, and the blur limit stays provisional until it can be checked on phone photos.
- A loose quality check is acceptable in the system because a blurry or dark photo tends to produce low-confidence predictions, which fusion treats as not assessed. This has not been measured here.