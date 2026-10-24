# Nutrient head: post-hoc findings (written after the test evaluation)

Written on 24 October 2026, after the single test evaluation of `nutrient_run1`. Nothing here changes `docs/nutrient_ship_rule.md` or its verdict (SHIPS, source: `results/nutrient_run1/nutrient_run1_test/test_decision.json`). These are findings and decisions made afterwards, and they are labelled as such.

## Finding 1: nitrogen is captured differently from every other class
Source: `results/nutrient/capture_style.txt` (script `scripts/inspect_nutrient_capture_style.py`, v2 split).
- nitrogen: 1,535 images, all camera-style file names, 1,320 distinct image sizes (around 1200 pixels), median file size 150.3 KB.
- no_deficiency, phosphorus, potassium, zinc: tiny crops in exactly two sizes (100x200 and 200x100), median file size between 5.2 and 8.3 KB. Potassium has the smallest files (5.2 KB) and is the only class cut into numbered tiles.
- Consequence: the model could separate nitrogen from the other classes by capture style alone. Its nitrogen test recall (0.9967, `results/nutrient_run1/nutrient_run1_test/metrics.json`) is therefore not evidence that nitrogen deficiency can be detected. Potassium is also separable by file size and tiling, so part of its score may come from capture style as well. The confusion among potassium, zinc and phosphorus is not evidence either way.

## Decision (post-hoc, separate from the ship rule): nitrogen is capped at weak in fusion
A nitrogen call from the nutrient head counts as a weak source whatever its confidence (it still needs a confidence of 0.60 or more to flag at all). The other deficiency classes keep the normal bands. This is a response to Finding 1 and not part of the pre-registered rule. It is lifted only if a check on real phone photos supports it.

## Diagnostic B (validation split only; interpretation fixed before it is run)
Take the nitrogen images of the validation split (231). Centre-crop each to 2:1, downscale to 100x200, re-encode as JPEG at the highest quality (floor 30) that keeps the file at or under 8.3 KB. Score the original and degraded versions with `nutrient_run1.keras` through the same image loader. Report nitrogen recall for both, the predicted labels of the degraded images, and the median degraded file size. The test split is not used.
- degraded recall at least 0.90: little evidence that the nitrogen result depends on capture style. This is still not proof that deficiency is being detected.
- degraded recall from 0.50 up to (not including) 0.90: partial dependence on capture style.
- degraded recall below 0.50: strong dependence on capture style, or detail lost in the downscaling. This data cannot tell the two apart.
The result is reported whatever it is and does not change the ship verdict.

## Smoke test C: phone photos of healthy maize leaves
20 to 30 photos taken by the project owner of healthy maize leaves are run through the nutrient head directly (without the gate). Reported: how many are predicted as a deficiency class with confidence 0.60 or more, by class. It is a smoke test and not an evaluation, with no labels beyond "healthy", and the photos are not used for training or selection. If more than 20% of the photos get a deficiency call at confidence 0.60 or more, it is flagged as a deployment risk. The 20% line is a judgment call fixed before any photo is scored.

## Limitation covering both image models
Every class of the disease and nutrient datasets is studio-style (PlantVillage-type crops and tiles). No field test of either model has been run, so performance on phone photos is unknown and likely lower.



## Result of Diagnostic B (validation split only; the test split was not used)
Source: `results/nutrient_run1/nutrient_run1_val_diagB/diagB_result.json` and the `metrics.json` beside it.
- The 231 nitrogen validation images were degraded as specified above: median degraded file size 6.94 KB, none above 8.3 KB, median JPEG quality 90.
- Nitrogen recall was 1.0000 before and 0.9827 after (227 of 231). The 4 errors: 3 called zinc, 1 called phosphorus. Median confidence was 1.0 before and after.
- The other four classes were copied unchanged, and their recall is identical before and after, as expected for a control.
- Pre-stated reading (recall at least 0.90): little evidence that the nitrogen result depends on capture style as measured by resolution, file size and aspect ratio. This is not proof that deficiency is detected. Every image is resized to 224x224 before the model sees it, so the test mainly adds blur and compression. Colour, background and lighting differences were not removed. Potassium, which is also separable by file size and tiling, was not tested.
- Consequence: the weak cap on nitrogen stays until the phone-photo smoke test (C) has been run. The ship verdict is unchanged.