import numpy as np
import math
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from scripts.sensor_constants import SOIL_TYPES, GROWTH_STAGES

def fit_preprocessing(rows):
    """
    Fits scaler means and stds on training data only.
    rows: list of dicts from csv.DictReader
    returns dict with preprocessing instructions
    """
    numeric_keys = ["soil_moisture", "temperature_c", "humidity_percent", "leaf_wetness_proxy"]
    sums = {k: 0.0 for k in numeric_keys}
    sq_sums = {k: 0.0 for k in numeric_keys}
    n = len(rows)
    
    if n == 0:
        raise ValueError("Cannot fit on empty dataset")
        
    for row in rows:
        for k in numeric_keys:
            val = float(row[k])
            sums[k] += val
            sq_sums[k] += val * val
            
    means = {k: sums[k] / n for k in numeric_keys}
    stds = {}
    for k in numeric_keys:
        variance = (sq_sums[k] / n) - (means[k] ** 2)
        std_val = math.sqrt(max(0.0, variance))
        stds[k] = std_val if std_val > 1e-6 else 1.0
        
    return {
        "numeric_features": numeric_keys,
        "means": means,
        "stds": stds,
        "soil_types": SOIL_TYPES,
        "growth_stages": GROWTH_STAGES
    }

def transform(rows, prep, include_growth_stage=True):
    """
    Transforms rows into float32 matrix.
    Rows missing properties will throw KeyError.
    """
    numeric_keys = prep["numeric_features"]
    means = prep["means"]
    stds = prep["stds"]
    soil_types = prep["soil_types"]
    growth_stages = prep["growth_stages"]
    
    matrix = []
    
    for row in rows:
        vec = []
        for k in numeric_keys:
            vec.append((float(row[k]) - means[k]) / stds[k])
            
        st = row["soil_type"]
        for st_cat in soil_types:
            vec.append(1.0 if st == st_cat else 0.0)
            
        if include_growth_stage:
            gs = row["growth_stage"]
            for gs_cat in growth_stages:
                vec.append(1.0 if gs == gs_cat else 0.0)
                
        matrix.append(vec)
        
    return np.array(matrix, dtype=np.float32)
