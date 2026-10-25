# Real-world photo test: pass criteria (fixed before any photo is scored)

Written on 25 October 2026, before any phone photo has been taken or scored. This file's first commit and push are the record that the criteria came first. After the first photo is scored, this file is not edited.

## Photos
Taken by the project owner on a phone, no downloaded images, at least 10 minutes apart where possible, mixed light.
- in_scope: 20 maize leaves in a field, healthy where possible (no known disease). Used for the gate and for the nutrient smoke test.
- out_of_scope: 10 photos of plants other than maize, taken locally: grasses, hedges, weeds, banana or other broad leaves, beans, kale and other vegetables, and look-alikes (sorghum, napier grass, sugarcane) wherever they can be found. The plant type of each photo is recorded in `notes.csv` before scoring, with look-alikes marked as such. At least 3 of the 10 should be look-alikes; if fewer can be found, the number found is stated in the results, and the test then says nothing about look-alikes.
- not_leaf: 10 photos of soil, hands, sky, stems and random objects.
Photos are named `<class>_NN.jpg`, kept in `realworld_gate/in_scope`, `realworld_gate/out_of_scope` and `realworld_gate/not_leaf`, and not edited or filtered by whether the model got them right. If a photo is excluded for a non-model reason (blurred beyond use, wrong subject), the reason is written in the results.

## Gate test (`gate_best.keras`, argmax rule, evaluated once)
All three numbers are reported with exact binomial 95% intervals. Photos are independent only if taken of different leaves, so intervals are indicative.
- G1: at least 16 of 20 in_scope photos accepted (80%).
- G2: at most 1 of 20 non-in_scope photos (out_of_scope plus not_leaf) accepted as in_scope.
- G3: the number of accepted non-in_scope photos is reported by class.
This test sets the gate threshold only through `scripts/threshold_sweep.py`, with the rule: the lowest threshold where at most 1 of the 20 non-in_scope photos is accepted. If no threshold satisfies the rule, the manifest stays `null` and provisional. The threshold is a proposal, not a validated value, because 20 photos per group is small.

## Nutrient smoke test (healthy in_scope photos only; not an evaluation)
- N1: of the 20 in_scope photos, the number predicted as any deficiency class with confidence at least 0.60, reported by class.
- N2: flagged as a deployment risk if more than 4 of 20 (20%) get a deficiency call at 0.60 or more.
- The nitrogen cap stays whatever this shows. A pass proves nothing about detection.

## Disease smoke test (same healthy photos)
- D1: the number predicted as a disease class (not healthy) with confidence at least 0.60, reported by class.
- D2: flagged as a deployment risk if more than 4 of 20 get a disease call at 0.60 or more.

## Supplementary look-alike set (optional, never counted in G1 to G3 or the threshold rule)
About 10 downloaded images of sorghum, napier grass and sugarcane, from varied sources, listed with their sources in `notes.csv` before scoring and labelled as downloaded. Reported separately, with accepted counts by crop type. Because common crop images are often copies of public datasets, including those the gate was trained on, a good result on this set is not read as evidence of robustness.

## Reading the result
- Passing means "no failure seen on 20 photos", not "works in the field". Photos are few and from one person, place and phone.
- A failure is reported as a failure and documented in `docs/limitations.md`. It does not lead to retraining against these photos.
- The photos are not used for training, selection or threshold choice except for the gate threshold rule above.