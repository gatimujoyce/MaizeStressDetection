import os
import sys

# Ensure this accesses the constants
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from sensor_constants import SOIL_PROPERTIES, WATERLOG_THRESHOLD_PCT_FC, DROUGHT_THRESHOLD_PCT_FC, HEAT_THRESHOLD_C

def predict_sensor_stress(moisture, temperature, soil_type):
    """
    Rule-based prediction baseline.
    Precedence convention (not severity claim):
    1. waterlogging (>110% FC)
    2. drought (<55% FC)
    3. heat (>=32 C)
    4. normal
    """
    fc = SOIL_PROPERTIES[soil_type]["field_capacity"]
    
    # Exact math boundaries avoiding precision issues from division
    
    if moisture * 100.0 > WATERLOG_THRESHOLD_PCT_FC * fc:
        return "waterlogging_risk"
    elif moisture * 100.0 < DROUGHT_THRESHOLD_PCT_FC * fc:
        return "drought_stress"
    elif temperature >= HEAT_THRESHOLD_C:
        return "heat_stress"
    else:
        return "normal"
