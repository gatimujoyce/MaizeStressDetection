import pytest
import os
import sys
import random

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from scripts.generate_sensor_data import generate_sample, generate_dataset, split_rows
from scripts.sensor_constants import SOIL_PROPERTIES
from scripts.rule_baseline import predict_sensor_stress

def test_generate_sample_bounds():
    rng = random.Random(99)
    # Test large overlap to stress the bounds
    for cls in ["normal", "drought_stress", "heat_stress", "waterlogging_risk"]:
        for _ in range(100):
            sample = generate_sample(cls, rng, overlap_scale=3.0)
            
            # Constraints
            assert 0.0 <= sample["soil_moisture"] <= 100.0, "Soil moisture out of domain 0-100"
            assert 0.0 <= sample["humidity_percent"] <= 100.0, "Humidity out of domain 0-100"
            assert -20.0 <= sample["temperature_c"] <= 60.0, "Temperature out of domain -20-60"
            assert sample["leaf_wetness_proxy"] >= 0.0, "Leaf wetness < 0"

            # Check that moisture still sits correctly within realistic soil saturation capacities
            soil_props = SOIL_PROPERTIES[sample["soil_type"]]
            # floating point round off could cause it to be slightly out of exact bounds, but we handle via round(moisture, 2)
            assert sample["soil_moisture"] >= soil_props["wilting_point"] - 1e-5
            assert sample["soil_moisture"] <= soil_props["saturation"] + 1e-5

def test_labels_not_derived_from_features():
    # 400 samples per class, seeded RNG
    # overlap=3.0 should be very inaccurate (<0.95)
    # overlap=0.25 should be very accurate (>0.95)
    
    def evaluate_scale(scale):
        dataset_rows = generate_dataset(seed=42, samples_per_class=400, overlap_scale=scale)
        correct = 0
        for r in dataset_rows:
            pred = predict_sensor_stress(r["soil_moisture"], r["temperature_c"], r["soil_type"])
            if pred == r["sensor_prediction"]:
                correct += 1
        return correct / len(dataset_rows)

    acc_3 = evaluate_scale(scale=3.0)
    acc_0_25 = evaluate_scale(scale=0.25)
    
    assert acc_3 < 0.95, f"Expected low accuracy at scale=3.0, got {acc_3}"
    assert acc_0_25 > 0.95, f"Expected high accuracy at scale=0.25, got {acc_0_25}"
