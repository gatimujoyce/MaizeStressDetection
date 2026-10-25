# Real-world photo test: pass criteria (fixed before any photo is taken)

Written on 25 October 2026, before any phone photo has been taken or scored. This file's first commit and push are the record that the criteria came first. After the first photo is scored this file is not edited; any amendment goes into a dated addendum file next to it.

## Photos
Taken by the project owner on a phone, no downloaded images, in mixed light. Every photo is of a different plant, ideally from more than one plot, and never two leaves of the same plant.
- in_scope: 20 maize leaves in a field.
- out_of_scope: 10 photos of plants other than maize, taken locally: grasses, hedges, weeds, banana or other broad leaves, beans, kale and other vegetables, and look-alikes (sorghum, napier grass, sugarcane) wherever they can be found. The plant type of each photo is recorded in `notes.csv` before scoring, with look-alikes marked as such. At least 3 of the 10 should be look-alikes; if fewer can be found, the number found is stated in the results, and the test then says nothing about look-alikes.
- not_leaf: 10 photos of soil, hands, sky, stems and random objects.
Photos are kept in `realworld_gate/in_scope`, `realworld_gate/out_of_scope` and `realworld_gate/not_leaf` and named `<class>_NN.jpg`. The crop of each out_of_scope photo is recorded in a file `notes.csv` written before scoring.
- Health note, written before any photo is scored: each in_scope photo is marked "looks healthy" or "visible symptoms" in `notes.csv`. Photos with visible symptoms stay in the gate test but are excluded from the nutrient and disease smoke test denominators.
- Photos are not selected by what the models say. A photo may be dropped only for a non-model reason (blurred beyond use, wrong subject), with the reason written in the results.

## Preprocessing (the backend path, fixed in advance)
Photos are decoded with PIL, rotated by their EXIF orientation (`ImageOps.exif_transpose`), converted to RGB, resized to 224x224 by bilinear interpolation without cropping, and passed through the EfficientNet preprocessing (guide section 7.1). HEIC photos are converted to JPEG on the phone before being copied. This is the path the deployed backend is meant to use. The parity test between this path and the evaluation path used for the committed results has not been run, so the two may differ slightly. This is stated in the results, and the path is not changed after seeing them.

## Gate test (`gate_best.keras`, argmax rule, evaluated once)
All numbers are reported with exact binomial 95% intervals. With 20 photos per group the intervals are wide, so a pass is weak evidence.
- G1: at least 16 of the 20 in_scope photos accepted.
- G2: at most 1 of the 20 non-in_scope photos (out_of_scope plus not_leaf) accepted as in_scope.
- G3: accepted non-in_scope photos reported by class and by crop type for out_of_scope (a single accepted look-alike is a failure to be named, even if G2 holds).
- Threshold rule (`scripts/threshold_sweep.py`): the lowest threshold in 0.50 to 0.99 with at most 1 of the 20 non-in_scope photos accepted. In_scope acceptance at that threshold is reported next to it and labelled in-sample, because the threshold was tuned on the same photos. If it falls below 16 of 20, or no threshold satisfies the rule, the manifest threshold stays null and provisional. A chosen threshold is a proposal and not a validated value.

## Smoke tests (in_scope photos marked "looks healthy"; not evaluations)
Each is reported on two sets: all such photos, and only those the gate accepts (what a farmer's result reflects).
- N1: how many are predicted as a deficiency class with confidence at least 0.60, by class.
- N2: flagged as possible false alarms if more than 20% get a deficiency call at 0.60 or more.
- N3: flagged if 3 or more are called nitrogen at 0.60 or more (tests the worry that phone photos are pulled towards nitrogen).
- D1: how many are predicted as a disease class (not healthy) with confidence at least 0.60, by class.
- D2: flagged as possible false alarms if more than 20% get a disease call at 0.60 or more.
- F1: how many get a fused severity of Medium or High (`fusion/fuse.py` with the sensor source not assessed, because photos carry no sensor data), reported without a cutoff.
- A "healthy" field leaf can carry mild disease or a real deficiency, so a flagged photo is a possible false alarm, not a proven error.
- The nitrogen cap stays whatever these show. A pass proves nothing about detection.

## Supplementary look-alike set (optional, never counted in G1 to G3 or the threshold rule)
About 10 downloaded images of sorghum, napier grass and sugarcane, from varied sources, listed with their sources in `notes.csv` before scoring and labelled as downloaded. Reported separately, with accepted counts by crop type. Because common crop images are often copies of public datasets, including those the gate was trained on, a good result on this set is not read as evidence of robustness.

## Reading the result
- Passing means "no failure seen on these photos", not "works in the field". The photos are few and come from one person, place and phone.
- A failure is reported and documented in `docs/limitations.md`. It does not lead to retraining against these photos.
- These photos are not used for training or selection, except for the gate threshold rule above.