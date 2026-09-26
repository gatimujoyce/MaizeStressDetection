def compute_severity(
    disease_label: str,
    disease_conf: float,
    sensor_label: str,
    sensor_conf: float,
    leaf_wetness_proxy: float,
    triage_result: str
) -> str:
    """
    DECISION-LEVEL fusion — rule-based lookup combining disease prediction and sensor prediction.
    
    Args:
        disease_label (str): Label predicted by the disease model (e.g., "Healthy", "Common Rust").
        disease_conf (float): Confidence score of the disease prediction (0.0 to 1.0).
        sensor_label (str): Label predicting environmental stress from sensor data.
        sensor_conf (float): Confidence score of the sensor prediction (0.0 to 1.0).
        leaf_wetness_proxy (float): Metric derived from sensor data representing condensation risk.
        triage_result (str): Result from the triage gate (e.g., "in_scope", "out_of_scope").

    Returns:
        str: "Low", "Medium", "High", or "Inconclusive".
    """
    # 1. If disease confidence is below 0.6 (uncertain) OR triage gate result is "out_of_scope"
    if disease_conf < 0.6 or triage_result == "out_of_scope":
        return "Inconclusive"

    # 2. If disease_label is NOT "Healthy"
    if disease_label != "Healthy":
        is_favored = False
        
        # Common Rust favoring cool+humid conditions
        if disease_label == "Common Rust":
            if sensor_label in ["Waterlogging Risk"] or leaf_wetness_proxy < 3:
                is_favored = True
                
        # Northern Leaf Blight favoring moderate temp+prolonged leaf wetness
        elif disease_label == "Northern Leaf Blight":
            if sensor_label in ["Waterlogging Risk"] or leaf_wetness_proxy < 3:
                is_favored = True
                
        # Gray Leaf Spot favoring warm+very high humidity, per the maize disease climate literature
        elif disease_label == "Gray Leaf Spot":
            if sensor_label in ["Waterlogging Risk", "Heat Stress"] or leaf_wetness_proxy < 2:
                is_favored = True

        # a. If sensor_label indicates conditions that favor that specific disease -> severity = "High"
        if is_favored:
            return "High"
        # b. Otherwise (disease present, sensor conditions don't specifically favor it) -> severity = "Medium"
        else:
            return "Medium"

    # 3. If disease_label IS "Healthy"
    else:
        # a. If sensor_label is "Normal" -> severity = "Low"
        if sensor_label == "Normal":
            return "Low"
        # b. If sensor_label is "Drought Stress", "Heat Stress", or "Waterlogging Risk" -> severity = "Medium" (early warning)
        elif sensor_label in ["Drought Stress", "Heat Stress", "Waterlogging Risk"]:
            return "Medium"
            
    # Fallback in case of unexpected conditions
    return "Inconclusive"
