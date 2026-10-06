import pytest
import os
import sys

# Ensure scripts can be imported from root
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from scripts.rule_baseline import predict_sensor_stress

def test_rule_baseline_exact_boundaries():
    # Precedence: waterlogging (>110), drought (<55), heat (>=32), normal
    # loam FC = 40.0
    # 55% FC = 22.0
    # 110% FC = 44.0
    
    # 1. Exact boundaries:
    # 55.0% FC -> exactly 55 is NOT drought, it is < 55. So normal, unless heat.
    assert predict_sensor_stress(22.0, 25.0, "loam") == "normal", "Exactly 55% FC shouldn't trigger strictly <55 drought"
    assert predict_sensor_stress(21.9, 25.0, "loam") == "drought_stress", "Below 55% should trigger drought stress"
    
    # 110.0% FC -> exactly 110 is NOT waterlog, it is > 110.
    assert predict_sensor_stress(44.0, 25.0, "loam") == "normal", "Exactly 110% shouldn't trigger >110 waterlogging"
    assert predict_sensor_stress(44.1, 25.0, "loam") == "waterlogging_risk", "Above 110% should trigger waterlogging risk"

    # Heat exactly 32 -> is heat
    assert predict_sensor_stress(30.0, 32.0, "loam") == "heat_stress", "Exactly 32C should trigger heat stress"
    assert predict_sensor_stress(30.0, 31.9, "loam") == "normal", "Below 32C shouldn't trigger heat stress"
    
    # Precedence testing
    # >110% FC and >= 32 C -> should be waterlogging
    assert predict_sensor_stress(45.0, 35.0, "loam") == "waterlogging_risk", "Waterlogging precedence failed"
    
    # <55% FC and >= 32 C -> should be drought
    assert predict_sensor_stress(20.0, 35.0, "loam") == "drought_stress", "Drought precedence failed"
