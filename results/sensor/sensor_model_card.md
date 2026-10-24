# Sensor Classifier Model Card

## Data Description
Simulated synthetic data. Classes: drought_stress, heat_stress, normal, waterlogging_risk.
Includes soil types (sandy_loam, loam, silt_loam, clay) and growth stages (V4, V6, V11, flowering, grain_filling, maturity).

Growth Stage Biases:
{
  "normal": [
    1,
    1,
    1,
    1,
    1,
    1
  ],
  "waterlogging_risk": [
    2,
    2,
    1,
    1,
    1,
    1
  ],
  "drought_stress": [
    1,
    1,
    1,
    2,
    2,
    1
  ],
  "heat_stress": [
    1,
    1,
    1,
    2,
    2,
    1
  ]
}

## Rule-Based Precedence Constraints
1. Waterlogging: > 110.0% Field Capacity
2. Drought: < 55.0% Field Capacity
3. Heat: >= 32.0 C
4. Normal otherwise.

## Performance Validation
OVERLAP_SCALE: 1.25
Validation Baseline Accuracy: 0.9016666666666666
Test Baseline Accuracy: 0.9216666666666666

### Results
Full Network Accuracy: 0.9483
Baseline Accuracy: 0.9217
Network difference to baseline is larger than seed-to-seed standard deviation.
No-stage network difference to full network is within seed-to-seed variation.

## Limitations
- All data is strictly simulated. The network is not validated on real sensor fields mappings.
- For loam, silt loam and clay, the waterlogging band (110% of field capacity up to saturation, about 112-116%) is narrow, so many waterlogging samples sit clamped at saturation value.
- Many drought samples sit at the wilting-point value.
