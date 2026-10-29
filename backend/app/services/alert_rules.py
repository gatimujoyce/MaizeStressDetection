"""Decide which sensor alerts to open or close after a new reading. Pure logic: no database, no models.

Input is the 24-hour sensor result from fusion/sensor_window.py (run with min_coverage 0 so alerts can fire early),
the stresses that already have an open alert, and when each stress last alerted.
Design (our assumption, agreed with the supervisor only in outline):
  strong  -> open an alert (Medium; High for waterlogging, which can ruin a crop in hours)
  weak    -> nothing yet ("watch"); it only shows on the dashboard
  one alert per farm and stress while it is open, and a 6-hour cooldown after it closes
  an open alert closes when the stress is no longer strong"""
from datetime import timedelta

COOLDOWN = timedelta(hours=6)
HIGH_SEVERITY = {"waterlogging_risk"}
TITLES = {"heat_stress": "Heat stress", "drought_stress": "Drought stress", "waterlogging_risk": "Waterlogging risk"}
# Wording is a placeholder until the extension officer has reviewed it.
ADVICE = {
    "heat_stress": "Temperatures have stayed high for several hours. Check the crop for wilting and consider watering or shade.",
    "drought_stress": "The soil has stayed dry for many hours. Check soil moisture and consider irrigating.",
    "waterlogging_risk": "The soil has stayed saturated. Check that water can drain away from the plot.",
}


SMS_TEXT = {
    "heat_stress": "Heat stress on {farm}: temperatures have stayed high for hours. Check for wilting; water or shade if you can.",
    "drought_stress": "Drought stress on {farm}: the soil has stayed dry for hours. Check soil moisture and irrigate if needed.",
    "waterlogging_risk": "Waterlogging risk on {farm}: the soil is saturated. Make sure water can drain from the plot.",
}


def sms_text(stress, farm_name):
    """One short text for a High alert (about 120 characters)."""
    return "MaizeStress: " + SMS_TEXT[stress].format(farm=farm_name[:20].rstrip())


def stress_levels(result):
    """{stress_class: 'weak' | 'strong'} from an aggregate_sensor result."""
    if result.get("status") in (None, "unavailable") or not result.get("primary"):
        return {}
    levels = {result["primary"]: result["status"]}
    for s in result.get("secondary", []):
        levels[s["class"]] = s["level"]
    return levels


def plan_alerts(result, open_stresses, last_alert_at, now, cooldown=COOLDOWN):
    """Returns (to_open, to_close).
    open_stresses: stresses that already have an unresolved sensor alert.
    last_alert_at: {stress: datetime of its most recent sensor alert}.
    to_open: list of dicts (stress_class, severity, message); to_close: list of stress classes."""
    if result.get("status") == "unavailable":
        return [], []                       # nothing to judge from: keep things as they are
    levels = stress_levels(result)
    to_close = [s for s in open_stresses if levels.get(s) != "strong"]
    to_open = []
    for stress, level in levels.items():
        if level != "strong" or stress in open_stresses:
            continue
        last = last_alert_at.get(stress)
        if last is not None and now - last < cooldown:
            continue
        hours = result["hours"][stress]["confirmed"]
        to_open.append({
            "stress_class": stress,
            "severity": "High" if stress in HIGH_SEVERITY else "Medium",
            "message": f"{TITLES[stress]}: {ADVICE[stress]} (about {hours:.0f} hours so far)",
        })
    return to_open, to_close