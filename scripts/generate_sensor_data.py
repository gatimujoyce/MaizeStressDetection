import os
import math
import random
import csv

OUTPUT_RAW = "data/raw/synthetic_sensor/sensor_data_full.csv"
OUTPUT_PROCESSED_DIR = "data/processed/synthetic_sensor"

RANDOM_SEED = 42
SAMPLES_PER_CLASS = 1000  # synthetic data, so classes are generated balanced by design

STRESS_CLASSES = ["normal", "drought_stress", "heat_stress", "waterlogging_risk"]
SOIL_TYPES = ["sandy_loam", "loam", "silt_loam", "clay"]
GROWTH_STAGES = ["V4", "V6", "V11", "flowering", "grain_filling", "maturity"]

# ---------------------------------------------------------------------------
# Soil water properties (% volumetric water content), sourced from Cornell
# NRCCA soil/water guidance and Oklahoma State University Extension:
#   - Field capacity: sandy 15-25%, loam 35-45%, clay 45-55% (midpoints used)
#   - Wilting point:  sandy 5-10%,  loam 10-15%, clay 15-20% (midpoints used)
#   - Saturation:     sandy ~30%,   clay ~60% (loam/silt loam interpolated)
# Silt loam values interpolated between loam and clay (not separately
# reported in the sources consulted).
#
# IMPORTANT: thresholds below are expressed as a PERCENTAGE OF EACH SOIL'S
# OWN FIELD CAPACITY, not as different absolute values per soil type. This
# is the approach used in multiple maize water-stress studies (e.g. a
# lysimeter study categorizing drought severity at 70/55/45/35% of field
# capacity; a waterlogging study finding soil water >120% of field capacity
# produces standing water). Expressing thresholds relative to field capacity
# keeps the underlying biological threshold consistent across soil types,
# while still producing different absolute sensor readings per soil type
# (since each soil's field capacity differs) — this reflects soil texture
# affecting the RATE at which a given soil reaches stress, rather than
# implying one soil type is inherently "more resistant" at a fixed
# absolute moisture percentage.
# ---------------------------------------------------------------------------
SOIL_PROPERTIES = {
    "sandy_loam": {"field_capacity": 20.0, "wilting_point": 7.5, "saturation": 30.0},
    "loam":       {"field_capacity": 40.0, "wilting_point": 12.5, "saturation": 45.0},
    "silt_loam":  {"field_capacity": 42.0, "wilting_point": 14.0, "saturation": 48.0},
    "clay":       {"field_capacity": 50.0, "wilting_point": 17.5, "saturation": 58.0},
}

DROUGHT_THRESHOLD_PCT_FC = 55    # below this % of field capacity -> drought stress
NORMAL_UPPER_PCT_FC = 100        # normal range ceiling, at field capacity itself
WATERLOG_THRESHOLD_PCT_FC = 110  # above this % of field capacity -> waterlogging risk

# Heat stress threshold — consistent with the grain-filling heat stress
# literature already cited in Chapter 2 (Qu et al. 2023's mild/moderate/severe
# gradient: ~32/24°C, ~36/28°C, ~40/32°C day/night; Li et al. 2025).
HEAT_THRESHOLD_C = 32
NORMAL_TEMP_RANGE = (18, 29)


def dew_point_celsius(temp_c, rh_percent):
    """Magnus formula approximation for dew point, given temperature (°C)
    and relative humidity (%)."""
    a, b = 17.27, 237.7
    rh = max(1, min(100, rh_percent))  # guard against log(0)
    alpha = ((a * temp_c) / (b + temp_c)) + math.log(rh / 100.0)
    return (b * alpha) / (a - alpha)


def leaf_wetness_proxy(temp_c, rh_percent):
    """Dew point depression (°C): temperature minus dew point.
    Smaller values indicate air near saturation — conditions favorable for
    condensation on leaf surfaces, and therefore higher fungal disease risk
    (relevant to Common Rust, Northern Leaf Blight, Gray Leaf Spot)."""
    td = dew_point_celsius(temp_c, rh_percent)
    return round(temp_c - td, 2)


def gauss_clamped(mean, sd, low, high, rng):
    """Gaussian sample clamped to a range — avoids hard cutoffs while keeping
    values physically plausible."""
    val = rng.gauss(mean, sd)
    return max(low, min(high, val))


def moisture_from_pct_fc(pct_fc, soil_props):
    """Converts a percentage of field capacity into an absolute volumetric
    water content reading for the given soil type, clamped between that
    soil's wilting point and saturation (the only physically possible range)."""
    absolute = (pct_fc / 100.0) * soil_props["field_capacity"]
    return max(soil_props["wilting_point"], min(soil_props["saturation"], absolute))


def generate_sample(stress_class, rng):
    soil_type = rng.choice(SOIL_TYPES)
    growth_stage = rng.choice(GROWTH_STAGES)
    soil_props = SOIL_PROPERTIES[soil_type]

    if stress_class == "normal":
        pct_fc = gauss_clamped(80, 10, DROUGHT_THRESHOLD_PCT_FC, NORMAL_UPPER_PCT_FC, rng)
        moisture = moisture_from_pct_fc(pct_fc, soil_props)
        temperature = gauss_clamped(23.5, 3, *NORMAL_TEMP_RANGE, rng)
        humidity = gauss_clamped(55, 10, 30, 80, rng)

    elif stress_class == "drought_stress":
        pct_fc = gauss_clamped(35, 10, 5, DROUGHT_THRESHOLD_PCT_FC, rng)
        moisture = moisture_from_pct_fc(pct_fc, soil_props)
        temperature = gauss_clamped(27, 3, 20, 34, rng)
        humidity = gauss_clamped(30, 8, 10, 50, rng)  # dry conditions correlate with drought

    elif stress_class == "heat_stress":
        # Heat stress is driven by temperature, not moisture — moisture stays
        # within the normal band while temperature is elevated.
        pct_fc = gauss_clamped(75, 12, DROUGHT_THRESHOLD_PCT_FC, NORMAL_UPPER_PCT_FC, rng)
        moisture = moisture_from_pct_fc(pct_fc, soil_props)
        temperature = gauss_clamped(HEAT_THRESHOLD_C + 4, 3, HEAT_THRESHOLD_C, 45, rng)
        humidity = gauss_clamped(45, 12, 20, 70, rng)

    elif stress_class == "waterlogging_risk":
        pct_fc = gauss_clamped(125, 10, WATERLOG_THRESHOLD_PCT_FC, 160, rng)
        moisture = moisture_from_pct_fc(pct_fc, soil_props)
        temperature = gauss_clamped(22, 3, 16, 28, rng)
        humidity = gauss_clamped(85, 8, 65, 100, rng)  # wet conditions correlate with waterlogging

    else:
        raise ValueError(f"Unknown stress class: {stress_class}")

    leaf_wetness = leaf_wetness_proxy(temperature, humidity)

    return {
        "soil_moisture": round(moisture, 2),
        "temperature_c": round(temperature, 2),
        "humidity_percent": round(humidity, 2),
        "leaf_wetness_proxy": leaf_wetness,
        "soil_type": soil_type,
        "growth_stage": growth_stage,
        "sensor_prediction": stress_class,
    }


def generate_dataset(seed=RANDOM_SEED, samples_per_class=SAMPLES_PER_CLASS):
    rng = random.Random(seed)
    rows = []
    for stress_class in STRESS_CLASSES:
        for _ in range(samples_per_class):
            rows.append(generate_sample(stress_class, rng))
    rng.shuffle(rows)
    return rows


def split_rows(rows, seed=RANDOM_SEED):
    rows = rows[:]  # already shuffled at generation time, but re-shuffle deterministically for the split step
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


def main():
    rows = generate_dataset()
    write_csv(OUTPUT_RAW, rows)
    print(f"Generated {len(rows)} synthetic sensor readings -> {OUTPUT_RAW}")

    splits = split_rows(rows)
    print(f"\n{'Split':<8} {'Count':>8}")
    for split_name, split_rows_ in splits.items():
        path = os.path.join(OUTPUT_PROCESSED_DIR, f"{split_name}.csv")
        write_csv(path, split_rows_)
        print(f"{split_name:<8} {len(split_rows_):>8}  -> {path}")

    # Quick class-balance sanity check per split
    print("\nClass balance check (should be roughly equal per split):")
    for split_name, split_rows_ in splits.items():
        counts = {c: 0 for c in STRESS_CLASSES}
        for r in split_rows_:
            counts[r["sensor_prediction"]] += 1
        print(f"  {split_name}: {counts}")


if __name__ == "__main__":
    main()