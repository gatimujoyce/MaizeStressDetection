import os
import math
import random
import csv
import json
import sys

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from sensor_constants import (
    SOIL_PROPERTIES, DROUGHT_THRESHOLD_PCT_FC, NORMAL_UPPER_PCT_FC, 
    WATERLOG_THRESHOLD_PCT_FC, HEAT_THRESHOLD_C, NORMAL_TEMP_RANGE
)

OUTPUT_RAW_V2 = "data/raw/synthetic_sensor_v2/sensor_data_full.csv"
OUTPUT_PROCESSED_DIR_V2 = "data/processed/synthetic_sensor_v2"

RANDOM_SEED = 42
SAMPLES_PER_CLASS = 1000

STRESS_CLASSES = ["normal", "drought_stress", "heat_stress", "waterlogging_risk"]
SOIL_TYPES = ["sandy_loam", "loam", "silt_loam", "clay"]
GROWTH_STAGES = ["V4", "V6", "V11", "flowering", "grain_filling", "maturity"]

# ASSUMPTION - tunable, to be justified in thesis
GROWTH_STAGE_WEIGHTS = {
    "normal":            [1, 1, 1, 1, 1, 1],
    "waterlogging_risk": [2, 2, 1, 1, 1, 1],
    "drought_stress":    [1, 1, 1, 2, 2, 1],
    "heat_stress":       [1, 1, 1, 2, 2, 1],
}

def dew_point_celsius(temp_c, rh_percent):
    a, b = 17.27, 237.7
    rh = max(1.0, min(100.0, rh_percent))
    alpha = ((a * temp_c) / (b + temp_c)) + math.log(rh / 100.0)
    return (b * alpha) / (a - alpha)


def leaf_wetness_proxy(temp_c, rh_percent):
    td = dew_point_celsius(temp_c, rh_percent)
    return max(0.0, temp_c - td)


def gauss_clamped(mean, sd, low, high, rng):
    val = rng.gauss(mean, sd)
    return max(low, min(high, val))


def moisture_from_pct_fc(pct_fc, soil_props):
    absolute = (pct_fc / 100.0) * soil_props["field_capacity"]
    return max(soil_props["wilting_point"], min(soil_props["saturation"], absolute))


def generate_sample(stress_class, rng, overlap_scale=1.0):
    soil_type = rng.choice(SOIL_TYPES)
    growth_stage = rng.choices(GROWTH_STAGES, weights=GROWTH_STAGE_WEIGHTS[stress_class])[0]
    soil_props = SOIL_PROPERTIES[soil_type]

    if stress_class == "normal":
        pct_fc = gauss_clamped(80, 10 * overlap_scale, 0, 300, rng)
        temperature = gauss_clamped(23.5, 3 * overlap_scale, -20, 60, rng)
        humidity = gauss_clamped(55, 10 * overlap_scale, 0, 100, rng)

    elif stress_class == "drought_stress":
        pct_fc = gauss_clamped(35, 10 * overlap_scale, 0, 300, rng)
        temperature = gauss_clamped(27, 3 * overlap_scale, -20, 60, rng)
        humidity = gauss_clamped(30, 8 * overlap_scale, 0, 100, rng)

    elif stress_class == "heat_stress":
        # clamped to normal band [55, 110]
        pct_fc = gauss_clamped(75, 12 * overlap_scale, DROUGHT_THRESHOLD_PCT_FC, WATERLOG_THRESHOLD_PCT_FC, rng)
        temperature = gauss_clamped(HEAT_THRESHOLD_C + 4, 3 * overlap_scale, -20, 60, rng)
        humidity = gauss_clamped(45, 12 * overlap_scale, 0, 100, rng)

    elif stress_class == "waterlogging_risk":
        pct_fc = gauss_clamped(125, 10 * overlap_scale, 0, 300, rng)
        temperature = gauss_clamped(22, 3 * overlap_scale, -20, 60, rng)
        humidity = gauss_clamped(85, 8 * overlap_scale, 0, 100, rng)

    else:
        raise ValueError(f"Unknown stress class: {stress_class}")

    moisture = moisture_from_pct_fc(pct_fc, soil_props)
    
    # Enforce API limits
    moisture = max(0.0, min(100.0, moisture))
    humidity = max(0.0, min(100.0, humidity))
    temperature = max(-20.0, min(60.0, temperature))
    leaf_wetness = round(max(0.0, leaf_wetness_proxy(temperature, humidity)), 2)

    return {
        "soil_moisture": round(moisture, 2),
        "temperature_c": round(temperature, 2),
        "humidity_percent": round(humidity, 2),
        "leaf_wetness_proxy": leaf_wetness,
        "soil_type": soil_type,
        "growth_stage": growth_stage,
        "sensor_prediction": stress_class,
    }


def generate_dataset(seed=RANDOM_SEED, samples_per_class=SAMPLES_PER_CLASS, overlap_scale=1.0):
    rng = random.Random(seed)
    rows = []
    # Note: Drawing label FIRST natively
    for stress_class in STRESS_CLASSES:
        for _ in range(samples_per_class):
            rows.append(generate_sample(stress_class, rng, overlap_scale=overlap_scale))
    rng.shuffle(rows)
    return rows


def split_rows(rows, seed=RANDOM_SEED):
    rows = rows[:]
    random.Random(seed + 1).shuffle(rows)
    n = len(rows)
    n_train = int(n * 0.70)
    n_val = int(n * 0.15)
    return {
        "train": rows[:n_train],
        "val": rows[n_train:n_train + n_val],
        "test": rows[n_train + n_val:],
    }


def write_csv(path, rows):
    if not rows:
        return
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)


def tune_overlap_scale():
    grid = [0.5 + i*0.25 for i in range(11)]  # 0.5 to 3.0
    best_scale = None
    best_diff = 100.0
    best_acc = 0.0
    results_table = []
    target_accuracy = 0.90
    
    from rule_baseline import predict_sensor_stress
    
    for scale in grid:
        rows = generate_dataset(seed=42, overlap_scale=scale) # Fixed seed
        splits = split_rows(rows, seed=42)
        val_rows = splits["val"]
        
        correct = 0
        for row in val_rows:
            pred = predict_sensor_stress(row["soil_moisture"], row["temperature_c"], row["soil_type"])
            if pred == row["sensor_prediction"]:
                correct += 1
        acc = correct / len(val_rows)
        results_table.append({"OVERLAP_SCALE": scale, "Validation_Baseline_Accuracy": acc})
        
        diff = abs(acc - target_accuracy)
        if diff < best_diff and 0.85 <= acc <= 0.95:
            best_diff = diff
            best_scale = scale
            best_acc = acc

    return best_scale, best_acc, results_table

def main():
    print("Tuning OVERLAP_SCALE...")
    best_scale, best_val_acc, results_table = tune_overlap_scale()
    
    os.makedirs("results/sensor", exist_ok=True)
    with open("results/sensor/overlap_tuning.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["OVERLAP_SCALE", "Validation_Baseline_Accuracy"])
        w.writeheader()
        w.writerows(results_table)

    if best_scale is None:
        print("Error: could not find scale in 85-95% bounds.")
        import pprint
        pprint.pprint(results_table)
        sys.exit(1)
        
    print(f"Selected OVERLAP_SCALE: {best_scale} with Validation Accuracy: {best_val_acc:.4f}")
    
    print("Generating full dataset v2...")
    rows = generate_dataset(seed=RANDOM_SEED, overlap_scale=best_scale)
    write_csv(OUTPUT_RAW_V2, rows)
    
    splits = split_rows(rows)
    for split_name, split_rows_ in splits.items():
        path = os.path.join(OUTPUT_PROCESSED_DIR_V2, f"{split_name}.csv")
        write_csv(path, split_rows_)

    from rule_baseline import predict_sensor_stress
    test_correct = sum(
        1 for r in splits["test"] 
        if predict_sensor_stress(r["soil_moisture"], r["temperature_c"], r["soil_type"]) == r["sensor_prediction"]
    )
    test_acc = test_correct / len(splits["test"])
    
    config = {
        "RANDOM_SEED": RANDOM_SEED,
        "SAMPLES_PER_CLASS": SAMPLES_PER_CLASS,
        "OVERLAP_SCALE": best_scale,
        "Validation_Baseline_Accuracy": best_val_acc,
        "Test_Baseline_Accuracy": test_acc
    }
    with open(os.path.join(OUTPUT_PROCESSED_DIR_V2, "generation_config.json"), "w") as f:
        json.dump(config, f, indent=2)

if __name__ == "__main__":
    main()