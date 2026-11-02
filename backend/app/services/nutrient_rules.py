"""Low-nutrient alerts for plots that have an NPK sensor. Pure logic: no database, no models.

Rule (our assumption, not reviewed by an agronomist):
  - look at the average of each nutrient over the last 24 hours, and only when there are at least MIN_READINGS of them
  - open a "low" alert when the average is below the warning level
  - close it once the average is back at least 10 % above the warning level, so a value hovering at the line
    does not open and close the alert again and again
  - one open alert per plot and nutrient, severity Medium, shown in the app only (never an SMS)
"""
from datetime import timedelta, timezone

WINDOW = timedelta(hours=24)
MIN_READINGS = 4
CLEAR_MARGIN = 1.10

# PLACEHOLDER warning levels, in mg/kg. No agronomist has reviewed these numbers, and sensor readings are not the same
# thing as a laboratory soil test, so the right levels also depend on the sensor and the soil. Change them here only:
# the alert text, the Trends page and the simulator all read them from this table.
NUTRIENTS = {
    "low_nitrogen": {"field": "nitrogen_mg_kg", "name": "nitrogen", "low": 20.0},
    "low_phosphorus": {"field": "phosphorus_mg_kg", "name": "phosphorus", "low": 10.0},
    "low_potassium": {"field": "potassium_mg_kg", "name": "potassium", "low": 80.0},
}
NPK_FIELDS = tuple(cfg["field"] for cfg in NUTRIENTS.values())
NUTRIENT_STRESSES = frozenset(NUTRIENTS)
LEVELS_BY_FIELD = {cfg["field"]: cfg["low"] for cfg in NUTRIENTS.values()}


def _utc(ts):
    return ts.replace(tzinfo=timezone.utc) if ts.tzinfo is None else ts.astimezone(timezone.utc)


def plan_nutrient_alerts(readings, open_stresses, now):
    """Returns (to_open, to_close).
    readings: dicts with recorded_at and the NPK fields (a field can be missing or None).
    open_stresses: nutrient stresses that already have an unresolved alert.
    to_open: list of dicts (stress_class, severity, message); to_close: list of stress classes."""
    now = _utc(now)
    to_open, to_close = [], []
    for stress, cfg in NUTRIENTS.items():
        values = [
            r[cfg["field"]] for r in readings
            if r.get(cfg["field"]) is not None and now - WINDOW < _utc(r["recorded_at"]) <= now
        ]
        if len(values) < MIN_READINGS:
            continue                                   # too little to judge from: leave things as they are
        average = sum(values) / len(values)
        low = cfg["low"]
        if stress in open_stresses:
            if average >= low * CLEAR_MARGIN:
                to_close.append(stress)
        elif average < low:
            name = cfg["name"]
            to_open.append({
                "stress_class": stress,
                "severity": "Medium",
                "message": (
                    f"Low {name}: The soil {name} has averaged {average:.0f} mg/kg over the last day, below the "
                    f"{low:.0f} mg/kg warning level. This is an early warning from the sensor, not a lab test, and "
                    f"the warning level is provisional. Ask your extension officer before applying fertiliser."
                ),
            })
    return to_open, to_close
