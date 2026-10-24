"""Sensor window aggregation: turns a time window of per-reading sensor labels into one status for fusion.
Pure Python (standard library only). Thresholds come from models/fusion/fusion_rules.yaml (section `sensor`).

readings: list of dicts
  {"timestamp": datetime, "label": str (the sensor model's class), "temperature_c": float or None,
   "soil_pct_fc": float or None}    # soil_pct_fc = pct_field_capacity(soil_moisture, soil_type, cfg["soil"])
Timestamps and `now` must both be naive or both timezone-aware.
The hour thresholds are design parameters, not tuned on data: the sensor data in this project is simulated."""
from datetime import timedelta

LEVEL_NAMES = ["not_flagging", "weak", "strong"]
EPS = 1e-9


def pct_field_capacity(soil_moisture, soil_type, soil_table):
    """Percent of field capacity. Matches scripts/rule_baseline.py, which compares moisture * 100 with
    threshold * field_capacity. soil_moisture must be in the same units as field_capacity in
    scripts/sensor_constants.py."""
    return 100.0 * float(soil_moisture) / soil_table[soil_type]["field_capacity"]


def _in_band(value, band):
    """Borderline bands from the RAP gaps: temperature 29 < t < 32, field capacity 100 < pct <= 110."""
    if value is None or not value > band["above"]:
        return False
    if "below" in band:
        return value < band["below"]
    return value <= band["up_to"]


def _credits(times, now, max_gap_hours):
    """Hours credited to each reading: until the next reading (or `now`), capped at max_gap_hours."""
    out = []
    for i, t in enumerate(times):
        nxt = times[i + 1] if i + 1 < len(times) else now
        gap = (nxt - t).total_seconds() / 3600.0
        out.append(min(max(gap, 0.0), max_gap_hours))
    return out


def _runs_hours(flags, times, credits, max_gap_hours, min_run_hours):
    """Total hours of consecutive True runs that last at least min_run_hours. A gap longer than max_gap_hours ends a run."""
    total, run, active = 0.0, 0.0, False
    for i, flag in enumerate(flags):
        contiguous = (active and i > 0 and
                      (times[i] - times[i - 1]).total_seconds() / 3600.0 <= max_gap_hours + EPS)
        if flag:
            if contiguous:
                run += credits[i]
            else:
                if active and run + EPS >= min_run_hours:
                    total += run
                run, active = credits[i], True
        else:
            if active and run + EPS >= min_run_hours:
                total += run
            run, active = 0.0, False
    if active and run + EPS >= min_run_hours:
        total += run
    return total


def _unavailable(reason, coverage=0.0):
    return {"status": "unavailable", "reason": reason, "primary": None, "secondary": [],
            "hours": {}, "coverage": coverage, "severe": False}


def aggregate_sensor(readings, now, cfg):
    s = cfg["sensor"]
    start = now - timedelta(hours=s["window_hours"])
    rs = sorted((r for r in readings if start <= r["timestamp"] <= now), key=lambda r: r["timestamp"])
    if not rs:
        return _unavailable("no_readings")
    times = [r["timestamp"] for r in rs]
    credits = _credits(times, now, s["max_gap_hours"])
    coverage = sum(credits) / s["window_hours"]
    if coverage + EPS < s["min_coverage"]:
        return _unavailable("insufficient_data", coverage)

    stress = s["stress_classes"]
    recent = [i for i, t in enumerate(times) if t >= now - timedelta(hours=s["recovery_hours"])]
    hours, levels = {}, {}
    for c in stress:
        confirmed = [r["label"] == c for r in rs]
        band = s["borderline"].get(c)
        borderline = [(r["label"] not in stress) and band is not None and _in_band(r.get(band["variable"]), band)
                      for r in rs]
        conf_h = _runs_hours(confirmed, times, credits, s["max_gap_hours"], s["min_run_hours"])
        bord_h = _runs_hours(borderline, times, credits, s["max_gap_hours"], s["min_run_hours"])
        th = s["hours"][c]
        if conf_h + EPS >= th["strong"]:
            level = 2
        elif conf_h + bord_h + EPS >= th["weak"]:
            level = 1
        else:
            level = 0
        if level > 0 and recent and not any(confirmed[i] or borderline[i] for i in recent):
            level -= 1                          # the condition has cleared in the most recent period
        hours[c] = {"confirmed": conf_h, "borderline": bord_h}
        levels[c] = level

    active = [c for c in stress if levels[c] > 0]
    active.sort(key=lambda c: (levels[c], (hours[c]["confirmed"] + hours[c]["borderline"]) / s["hours"][c]["strong"]),
                reverse=True)
    return {"status": LEVEL_NAMES[max(levels.values())], "reason": None,
            "primary": active[0] if active else None,
            "secondary": [{"class": c, "level": LEVEL_NAMES[levels[c]]} for c in active[1:]],
            "hours": hours, "coverage": coverage,
            "severe": any(levels[c] == 2 and c in s["severe_alone"] for c in stress)}