import pytest
import numpy as np
import json
import os
import tempfile
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sensor.preprocessing import fit_preprocessing, transform
from scripts.sensor_constants import SOIL_TYPES, GROWTH_STAGES

def test_fit_computes_exact_mean_and_std():
    rows = [
        {"soil_moisture": "10.0", "temperature_c": "10.0", "humidity_percent": "10.0", "leaf_wetness_proxy": "10.0", "soil_type": "sandy_loam", "growth_stage": "V4"},
        {"soil_moisture": "30.0", "temperature_c": "30.0", "humidity_percent": "30.0", "leaf_wetness_proxy": "30.0", "soil_type": "clay", "growth_stage": "flowering"}
    ]
    prep = fit_preprocessing(rows)
    assert prep["means"]["soil_moisture"] == 20.0
    # Uses population std (N=2 rather than N-1)
    assert prep["stds"]["soil_moisture"] == 10.0
    
    row_low = [rows[0]]
    mat = transform(row_low, prep, True)
    assert mat[0][0] == -1.0
    
def test_scaler_uses_train_rows_only():
    rows = [
        {"soil_moisture": "10.0", "temperature_c": "10.0", "humidity_percent": "10.0", "leaf_wetness_proxy": "10.0", "soil_type": "sandy_loam", "growth_stage": "V4"},
        {"soil_moisture": "30.0", "temperature_c": "30.0", "humidity_percent": "30.0", "leaf_wetness_proxy": "30.0", "soil_type": "clay", "growth_stage": "flowering"}
    ]
    prep = fit_preprocessing(rows)
    row3 = [{"soil_moisture": "50.0", "temperature_c": "50.0", "humidity_percent": "50.0", "leaf_wetness_proxy": "50.0", "soil_type": "clay", "growth_stage": "flowering"}]
    mat3 = transform(row3, prep, True)
    assert mat3[0][0] == 3.0

def test_one_hot_order_exact_match():
    prep = {
         "numeric_features": ["soil_moisture", "temperature_c", "humidity_percent", "leaf_wetness_proxy"],
         "means": {"soil_moisture": 20.0, "temperature_c": 20.0, "humidity_percent": 20.0, "leaf_wetness_proxy": 20.0},
         "stds": {"soil_moisture": 10.0, "temperature_c": 10.0, "humidity_percent": 10.0, "leaf_wetness_proxy": 10.0},
         "soil_types": SOIL_TYPES,
         "growth_stages": GROWTH_STAGES
    }
    
    row3 = [{"soil_moisture": "50.0", "temperature_c": "50.0", "humidity_percent": "50.0", "leaf_wetness_proxy": "50.0", "soil_type": "clay", "growth_stage": "flowering"}]
    mat3 = transform(row3, prep, True)
    
    # 50 - 20 / 10 = 3.0
    expected = [3.0, 3.0, 3.0, 3.0,  0.0, 0.0, 0.0, 1.0,  0.0, 0.0, 0.0, 1.0, 0.0, 0.0]
    np.testing.assert_array_equal(mat3[0], np.array(expected, dtype=np.float32))

def test_include_growth_stage_false_drops_exactly_stage_columns():
    prep = {
         "numeric_features": ["soil_moisture", "temperature_c", "humidity_percent", "leaf_wetness_proxy"],
         "means": {"soil_moisture": 20.0, "temperature_c": 20.0, "humidity_percent": 20.0, "leaf_wetness_proxy": 20.0},
         "stds": {"soil_moisture": 10.0, "temperature_c": 10.0, "humidity_percent": 10.0, "leaf_wetness_proxy": 10.0},
         "soil_types": SOIL_TYPES,
         "growth_stages": GROWTH_STAGES
    }
    row3 = [{"soil_moisture": "50.0", "temperature_c": "50.0", "humidity_percent": "50.0", "leaf_wetness_proxy": "50.0", "soil_type": "clay", "growth_stage": "flowering"}]
    mat_full = transform(row3, prep, True)[0]
    mat_no_gs = transform(row3, prep, False)[0]
    
    expected = [3.0, 3.0, 3.0, 3.0,  0.0, 0.0, 0.0, 1.0]
    np.testing.assert_array_equal(mat_no_gs, np.array(expected, dtype=np.float32))
    np.testing.assert_array_equal(mat_no_gs, mat_full[:-6])

def test_json_round_trip():
    rows = [{"soil_moisture": "10.0", "temperature_c": "10.0", "humidity_percent": "10.0", "leaf_wetness_proxy": "10.0", "soil_type": "sandy_loam", "growth_stage": "V4"}]
    prep = fit_preprocessing(rows)
    with tempfile.TemporaryDirectory() as d:
        path = os.path.join(d, "sensor_preprocessing.json")
        with open(path, "w") as f:
            json.dump(prep, f)
        
        with open(path, "r") as f:
            loaded = json.load(f)
            
        assert prep == loaded
