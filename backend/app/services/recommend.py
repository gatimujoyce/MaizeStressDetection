"""
Recommendation service.
"""

RECOMMENDATION_TABLE = {
    # Healthy cases
    ("Healthy", "Low"): "Your crop appears healthy with no signs of environmental stress. Continue standard standard farming practices. [NEEDS KALRO/extension-service source citation]",
    ("Healthy", "Medium"): "Your crop appears healthy, but sensors indicate early signs of environmental stress (like drought, heat, or waterlogging). Monitor the field closely. [NEEDS KALRO/extension-service source citation]",
    ("Healthy", "High"): "Your crop has no visible disease, but extreme environmental stress is detected. Take immediate preventive action to manage the stress. [NEEDS KALRO/extension-service source citation] Consider contacting your local agricultural extension officer.",
    ("Healthy", "Inconclusive"): "Unable to determine a clear recommendation based on the current readings. Inspect the field manually. [NEEDS KALRO/extension-service source citation]",

    # Common Rust
    ("Common Rust", "Low"): "Mild symptoms of Common Rust detected. Ensure good air circulation and avoid overhead watering if possible. [NEEDS KALRO/extension-service source citation]",
    ("Common Rust", "Medium"): "Moderate Common Rust present. Consider applying recommended protective treatments before the disease spreads further. [NEEDS KALRO/extension-service source citation]",
    ("Common Rust", "High"): "Severe Common Rust detected. Cool and humid conditions are highly favorable for rapid spread. Immediate treatment is necessary. [NEEDS KALRO/extension-service source citation] Consider contacting your local agricultural extension officer.",
    ("Common Rust", "Inconclusive"): "Common Rust prediction is uncertain. Inspect the field carefully for rust pustules on leaves. [NEEDS KALRO/extension-service source citation]",

    # Northern Leaf Blight
    ("Northern Leaf Blight", "Low"): "Mild symptoms of Northern Leaf Blight detected. Keep monitoring the fields for elongation of the spots. [NEEDS KALRO/extension-service source citation]",
    ("Northern Leaf Blight", "Medium"): "Moderate Northern Leaf Blight present. Prepare for potential protective treatments to protect the upper canopy. [NEEDS KALRO/extension-service source citation]",
    ("Northern Leaf Blight", "High"): "Severe Northern Leaf Blight detected. Current conditions strongly favor rapid spread and yield loss. Immediate protective action required. [NEEDS KALRO/extension-service source citation] Consider contacting your local agricultural extension officer.",
    ("Northern Leaf Blight", "Inconclusive"): "Northern Leaf Blight prediction is uncertain. Manually check for cigar-shaped lesions on lower leaves. [NEEDS KALRO/extension-service source citation]",

    # Gray Leaf Spot
    ("Gray Leaf Spot", "Low"): "Mild signs of Gray Leaf Spot detected. Keep a close eye on humidity levels and crop density. [NEEDS KALRO/extension-service source citation]",
    ("Gray Leaf Spot", "Medium"): "Moderate Gray Leaf Spot present. Consider applying appropriate treatments soon to prevent progression up the plant. [NEEDS KALRO/extension-service source citation]",
    ("Gray Leaf Spot", "High"): "Severe Gray Leaf Spot detected. High humidity and heat favor extensive damage. Urgent treatment is critical to protect yield. [NEEDS KALRO/extension-service source citation] Consider contacting your local agricultural extension officer.",
    ("Gray Leaf Spot", "Inconclusive"): "Gray Leaf Spot prediction is uncertain. Verify visually for small tan spots on leaves. [NEEDS KALRO/extension-service source citation]",
}

def get_recommendation(disease_label: str, severity: str) -> str:
    """
    Looks up the recommendation corresponding to the disease label and severity.
    
    Args:
        disease_label (str): The predicted disease or "Healthy".
        severity (str): The computed severity ("Low", "Medium", "High", or "Inconclusive").
        
    Returns:
        str: Farmer-facing recommendation text.
    """
    key = (disease_label, severity)
    
    # Provide a safe fallback if an unmapped combination occurs
    if key in RECOMMENDATION_TABLE:
        return RECOMMENDATION_TABLE[key]
    
    default_msg = f"No specific recommendation available for {disease_label} with {severity} severity. [NEEDS KALRO/extension-service source citation]"
    if severity == "High":
        default_msg += " Consider contacting your local agricultural extension officer."
    return default_msg
