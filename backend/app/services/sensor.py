"""
app.services.sensor
~~~~~~~~~~~~~~~~~~~
Core sensor-reading generation logic, shared between:
  - The live simulator  (simulator/run.py)
  - Offline dataset generation (scripts/)

All thresholds are expressed as a PERCENTAGE OF EACH SOIL'S FIELD CAPACITY so
that the biological stress boundaries stay consistent across soil types while
still producing different absolute Volumetric Water Content(VWC) readings per soil texture.

Sources: Cornell NRCCA soil/water guidance; Oklahoma State University
Extension; Qu et al. 2023 heat-stress gradient; Li et al. 2025.
"""

import math
import random


# Soil types & water properties (% volumetric water content)
# ---------------------------------------------------------------------------
SOIL_TYPES = ["sandy_loam", "loam", "silt_loam", "clay"]

SOIL_PROPERTIES: dict[str, dict[str, float]] = {
    #              field_capacity  wilting_point  saturation
    "sandy_loam": {"field_capacity": 20.0, "wilting_point":  7.5, "saturation": 30.0},
    "loam":       {"field_capacity": 40.0, "wilting_point": 12.5, "saturation": 45.0},
    "silt_loam":  {"field_capacity": 42.0, "wilting_point": 14.0, "saturation": 48.0},
    "clay":       {"field_capacity": 50.0, "wilting_point": 17.5, "saturation": 58.0},
}


# Stress scenario definitions
# ---------------------------------------------------------------------------
STRESS_CLASSES = ["normal", "drought_stress", "heat_stress", "waterlogging_risk"]

# Thresholds relative to field capacity (%)
DROUGHT_THRESHOLD_PCT_FC  = 55   # below this → drought stress
NORMAL_UPPER_PCT_FC       = 100  # normal ceiling — at field capacity itself
WATERLOG_THRESHOLD_PCT_FC = 110  # above this → waterlogging risk

# Temperature thresholds (°C)
HEAT_THRESHOLD_C   = 32
NORMAL_TEMP_RANGE  = (18, 29)


# Helper functions
# ---------------------------------------------------------------------------

def _dew_point_celsius(temp_c: float, rh_percent: float) -> float:
    """Magnus-formula dew point (°C)."""
    a, b = 17.27, 237.7
    rh = max(1.0, min(100.0, rh_percent))
    alpha = ((a * temp_c) / (b + temp_c)) + math.log(rh / 100.0)
    return (b * alpha) / (a - alpha)


def leaf_wetness_proxy(temp_c: float, rh_percent: float) -> float:
    """Dew-point depression (°C): smaller → air near saturation → higher
    fungal disease risk (Common Rust, NLB, Gray Leaf Spot)."""
    return round(temp_c - _dew_point_celsius(temp_c, rh_percent), 2)


def _gauss_clamped(mean: float, sd: float, low: float, high: float,
                   rng: random.Random) -> float:
    """Gaussian sample clamped to [low, high]- physically plausible values."""
    return max(low, min(high, rng.gauss(mean, sd)))


def _moisture_from_pct_fc(pct_fc: float, soil_props: dict) -> float:
    """Convert % of field capacity to absolute VWC, clamped to
    [wilting_point, saturation]."""
    absolute = (pct_fc / 100.0) * soil_props["field_capacity"]
    return max(soil_props["wilting_point"], min(soil_props["saturation"], absolute))


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def generate_reading(
    stress_class: str,
    soil_type: str,
    rng: random.Random | None = None,
) -> dict:
    """Generate one realistic sensor reading for *stress_class* and *soil_type*.

    Returns a dict whose keys match the ``SensorReadingCreate`` schema:
        soil_moisture  (float, VWC %)
        temperature    (float, °C)
        humidity       (float, %)
        leaf_wetness   (float, dew-point depression °C)

    Args:
        stress_class: One of STRESS_CLASSES.
        soil_type:    One of SOIL_TYPES.
        rng:          Optional seeded ``random.Random`` instance; a fresh
                      instance is used when *None*.

    Raises:
        ValueError: Unknown stress_class or soil_type.
    """
    if stress_class not in STRESS_CLASSES:
        raise ValueError(f"Unknown stress_class {stress_class!r}. "
                         f"Choose from {STRESS_CLASSES}.")
    if soil_type not in SOIL_PROPERTIES:
        raise ValueError(f"Unknown soil_type {soil_type!r}. "
                         f"Choose from {SOIL_TYPES}.")

    if rng is None:
        rng = random.Random()

    props = SOIL_PROPERTIES[soil_type]

    if stress_class == "normal":
        pct_fc      = _gauss_clamped(80, 10, DROUGHT_THRESHOLD_PCT_FC, NORMAL_UPPER_PCT_FC, rng)
        temperature = _gauss_clamped(23.5, 3, *NORMAL_TEMP_RANGE, rng)
        humidity    = _gauss_clamped(55, 10, 30, 80, rng)

    elif stress_class == "drought_stress":
        pct_fc      = _gauss_clamped(35, 10, 5, DROUGHT_THRESHOLD_PCT_FC, rng)
        temperature = _gauss_clamped(27, 3, 20, 34, rng)
        humidity    = _gauss_clamped(30, 8, 10, 50, rng)

    elif stress_class == "heat_stress":
        # Temperature elevated; moisture stays within the normal band.
        pct_fc      = _gauss_clamped(75, 12, DROUGHT_THRESHOLD_PCT_FC, NORMAL_UPPER_PCT_FC, rng)
        temperature = _gauss_clamped(HEAT_THRESHOLD_C + 4, 3, HEAT_THRESHOLD_C, 45, rng)
        humidity    = _gauss_clamped(45, 12, 20, 70, rng)

    elif stress_class == "waterlogging_risk":
        pct_fc      = _gauss_clamped(125, 10, WATERLOG_THRESHOLD_PCT_FC, 160, rng)
        temperature = _gauss_clamped(22, 3, 16, 28, rng)
        humidity    = _gauss_clamped(85, 8, 65, 100, rng)

    moisture = _moisture_from_pct_fc(pct_fc, props)

    return {
        "soil_moisture": round(moisture, 2),
        "temperature":   round(temperature, 2),
        "humidity":      round(humidity, 2),
        "leaf_wetness":  leaf_wetness_proxy(temperature, humidity),
    }
