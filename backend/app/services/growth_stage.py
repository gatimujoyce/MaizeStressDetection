"""Maize growth stage from the planting date, and how the stage changes sensor alerts. Pure logic: no database.

PROVISIONAL. The day ranges below are typical for tropical lowland / mid-altitude maize of medium maturity, taken from
general published guidance (Farmers Weekly "Managing critical plant growth stages"; Pannar "Know the maize plant";
IITA, Kling, "Morphology and development"). Cooler sites and later-maturing varieties take longer; early varieties
are quicker. [NEEDS KALRO/extension-service source citation for Kenya-specific day ranges]
What the rules rely on (same sources): dry soil and heat do the most damage around flowering; waterlogging does the
most damage to seedlings; nutrients matter little at sowing and once the crop is ripening."""
from datetime import date

# key, label, first day after planting, what the farmer should know
STAGES = [
    ("germination", "Germination and emergence", 0, "Seeds are sprouting. Wet, cold or waterlogged soil can rot them."),
    ("seedling", "Young seedling", 7, "Young plants are small and easily hurt by waterlogging."),
    ("vegetative", "Leaf growth", 21, "The plant is growing leaves and stem. It needs nitrogen and steady moisture."),
    ("flowering", "Flowering (tassel and silk)", 56, "The most sensitive time. Dry soil or heat now can cut the harvest sharply."),
    ("grain_filling", "Grain filling", 81, "Cobs are filling. Water still matters, but the crop is past its most sensitive time."),
    ("ripening", "Ripening", 116, "Grain is drying down. Extra water is no longer needed."),
    ("harvest", "Ready to harvest", 151, "The crop should be ready or nearly ready to harvest."),
]
KEYS = [s[0] for s in STAGES]

NO_ALERTS = {"not_planted", "harvest"}                              # nothing to protect
NO_STRESS = {"ripening": {"drought_stress", "heat_stress"}}         # dry or hot weather no longer matters much
NO_NUTRIENT_ALERTS = {"not_planted", "germination", "ripening", "harvest"}
RAISE_TO_HIGH = {("drought_stress", "flowering"), ("heat_stress", "flowering")}
LOWER_TO_MEDIUM = {("waterlogging_risk", "ripening")}
CONTEXT = {
    "flowering": " Your maize is flowering, the stage most sensitive to this.",
    "germination": " Your maize has only just been planted.",
    "seedling": " Your maize is still a young seedling.",
}


def stage_for(planting_date, today):
    """None when there is no planting date. Otherwise a dict: key, label, tip, days (after planting; negative before)."""
    if planting_date is None:
        return None
    days = (today - planting_date).days
    if days < 0:
        return {"key": "not_planted", "label": "Not planted yet", "days": days,
                "tip": f"Planting is set for {planting_date.isoformat()}. Stress alerts start once the maize is in the ground."}
    chosen = STAGES[0]
    for stage in STAGES:
        if days >= stage[2]:
            chosen = stage
    return {"key": chosen[0], "label": chosen[1], "days": days, "tip": chosen[3]}


def stage_key(planting_date, today):
    stage = stage_for(planting_date, today)
    return stage["key"] if stage else None


def apply_stage(to_open, key):
    """Adjust alerts planned by plan_alerts for the growth stage. key None (no planting date) changes nothing."""
    if key is None:
        return list(to_open)
    if key in NO_ALERTS:
        return []
    out = []
    for alert in to_open:
        stress = alert["stress_class"]
        if stress in NO_STRESS.get(key, ()):
            continue
        alert = dict(alert)
        if (stress, key) in RAISE_TO_HIGH:
            alert["severity"] = "High"
        elif (stress, key) in LOWER_TO_MEDIUM:
            alert["severity"] = "Medium"
        alert["message"] += CONTEXT.get(key, "") if (stress, key) not in LOWER_TO_MEDIUM else ""
        out.append(alert)
    return out


def allow_nutrient_alerts(key):
    return key is None or key not in NO_NUTRIENT_ALERTS
