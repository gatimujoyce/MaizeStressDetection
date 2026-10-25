SOIL_PROPERTIES = {
    "sandy_loam": {"field_capacity": 20.0, "wilting_point": 7.5, "saturation": 30.0},
    "loam":       {"field_capacity": 40.0, "wilting_point": 12.5, "saturation": 45.0},
    "silt_loam":  {"field_capacity": 42.0, "wilting_point": 14.0, "saturation": 48.0},
    "clay":       {"field_capacity": 50.0, "wilting_point": 17.5, "saturation": 58.0},
}

DROUGHT_THRESHOLD_PCT_FC = 55.0
NORMAL_UPPER_PCT_FC = 100.0
WATERLOG_THRESHOLD_PCT_FC = 110.0
HEAT_THRESHOLD_C = 32.0
NORMAL_TEMP_RANGE = (18, 29)

SOIL_TYPES = ["sandy_loam", "loam", "silt_loam", "clay"]
GROWTH_STAGES = ["V4", "V6", "V11", "flowering", "grain_filling", "maturity"]

# ASSUMPTION - tunable, to be justified in thesis
GROWTH_STAGE_WEIGHTS = {
    "normal":            [1, 1, 1, 1, 1, 1],
    "waterlogging_risk": [2, 2, 1, 1, 1, 1],
    "drought_stress":    [1, 1, 1, 2, 2, 1],
    "heat_stress":       [1, 1, 1, 2, 2, 1],
}
