"""Sensor trends for the farmer Trends page: readings grouped into time buckets, a day-on-day change per reading, and the
sensor alerts that were open in the period. Pure functions (no database), so they are easy to test."""
from datetime import datetime, timedelta, timezone

from app.services.nutrient_rules import NUTRIENT_STRESSES

FIELDS = ("temperature", "humidity", "soil_moisture", "leaf_wetness")
STRESS_LABELS = {"heat_stress", "drought_stress", "waterlogging_risk"}  # any other sensor-model label counts as normal
# range -> (how far back, bucket size). Keeps every chart to about 50 to 120 points.
RANGES = {
    "24h": (timedelta(hours=24), timedelta(minutes=30)),
    "7d": (timedelta(days=7), timedelta(hours=2)),
    "30d": (timedelta(days=30), timedelta(hours=6)),
}
DAY = timedelta(hours=24)
MIN_READINGS = 6  # a day-on-day change needs at least this many readings in each of the two days


def _utc(ts):
    return ts.replace(tzinfo=timezone.utc) if ts.tzinfo is None else ts.astimezone(timezone.utc)


def _mean(values):
    return sum(values) / len(values) if values else None


def _round(value):
    return None if value is None else round(value, 2)


def bucket_points(readings, start, end, step, fields=FIELDS):
    """Average each reading over fixed time buckets between start and end. readings: dicts with recorded_at and FIELDS."""
    size = int(step.total_seconds())
    buckets = {}
    for r in readings:
        t = _utc(r["recorded_at"])
        if t < start or t > end:
            continue
        buckets.setdefault(int(t.timestamp()) // size * size, []).append(r)
    points = []
    for key in sorted(buckets):
        rows = buckets[key]
        point = {"t": datetime.fromtimestamp(key, tz=timezone.utc).isoformat(), "n": len(rows)}
        for f in fields:
            point[f] = _round(_mean([r[f] for r in rows if r.get(f) is not None]))
        points.append(point)
    return points


def day_change(readings, field, now):
    """Average of the last 24 hours minus the average of the 24 hours before. None when either day has too few readings."""
    last = [r[field] for r in readings if r.get(field) is not None and now - DAY <= _utc(r["recorded_at"]) <= now]
    before = [r[field] for r in readings
              if r.get(field) is not None and now - 2 * DAY <= _utc(r["recorded_at"]) < now - DAY]
    if len(last) < MIN_READINGS or len(before) < MIN_READINGS:
        return None
    return _round(_mean(last) - _mean(before))


def status_segments(readings, labels, start, end, step):
    """What the sensor model said over time. Each bucket takes its most common label (a tie goes to the stress label), and
    neighbouring buckets with the same status are merged into one stretch. A silent sensor leaves a gap, not a stretch."""
    size = int(step.total_seconds())
    per_bucket = {}
    for reading, label in zip(readings, labels):
        t = _utc(reading["recorded_at"])
        if start <= t <= end:
            per_bucket.setdefault(int(t.timestamp()) // size * size, []).append(label if label in STRESS_LABELS else "normal")
    stretches = []
    for key in sorted(per_bucket):
        votes = per_bucket[key]
        status = max(set(votes), key=lambda v: (votes.count(v), v != "normal"))
        b_start = datetime.fromtimestamp(key, tz=timezone.utc)
        last = stretches[-1] if stretches else None
        if last and last["status"] == status and b_start - last["end"] <= step * 1.5:
            last["end"] = b_start + step
        else:
            stretches.append({"status": status, "start": b_start, "end": b_start + step})
    return [{"status": x["status"], "start": x["start"].isoformat(), "end": x["end"].isoformat()} for x in stretches]


def _latest_value(readings, field):
    """The newest value a field has, skipping readings that left it out (an NPK sensor can miss a reading on its own)."""
    newest = None
    for r in readings:
        if r.get(field) is not None and (newest is None or _utc(r["recorded_at"]) > _utc(newest["recorded_at"])):
            newest = r
    return newest[field] if newest else None


def _alert_json(a):
    return {
        "id": str(a["id"]),
        "stress_class": a["stress_class"],
        "severity": a["severity"],
        "start": _utc(a["created_at"]).isoformat(),
        "end": _utc(a["resolved_at"]).isoformat() if a["resolved_at"] else None,
    }


def build_trend(readings, alerts, range_key, now, labels=None, fields=FIELDS, nutrient_levels=None):
    """readings: dicts with recorded_at and FIELDS covering at least the range (and 48 hours, for the day change).
    alerts: dicts with id, stress_class, severity, created_at, resolved_at.
    labels: the sensor model's label for each reading (same order), or None when the model is not available."""
    window, step = RANGES[range_key]
    now = _utc(now)
    start = now - window
    in_range = [r for r in readings if start <= _utc(r["recorded_at"]) <= now]
    latest = max(readings, key=lambda r: _utc(r["recorded_at"]), default=None)
    times = [_utc(r["recorded_at"]) for r in in_range]
    summary = {
        f: {
            "latest": _latest_value(readings, f),
            "change": day_change(readings, f, now),
        }
        for f in fields
    }
    overlapping = [
        a for a in alerts
        if _utc(a["created_at"]) <= now and (a["resolved_at"] is None or _utc(a["resolved_at"]) >= start)
    ]
    ordered = sorted(overlapping, key=lambda a: _utc(a["created_at"]))
    return {
        "range": range_key,
        "from": start.isoformat(),
        "to": now.isoformat(),
        "bucket_minutes": int(step.total_seconds() // 60),
        "latest_at": _utc(latest["recorded_at"]).isoformat() if latest else None,
        "hours_since_latest": round((now - _utc(latest["recorded_at"])).total_seconds() / 3600, 1) if latest else None,
        "hours_of_data": round((max(times) - min(times)).total_seconds() / 3600, 1) if len(times) > 1 else 0,
        "points": bucket_points(in_range, start, now, step, fields),
        "sensor_status": {
            "available": labels is not None,
            "segments": status_segments(readings, labels, start, now, step) if labels is not None else [],
        },
        "summary": summary,
        "alerts": [_alert_json(a) for a in ordered if a["stress_class"] not in NUTRIENT_STRESSES],
        # Low-nutrient alerts are kept apart so they shade only the nutrient charts, not temperature or humidity.
        "has_npk_sensor": nutrient_levels is not None,
        "nutrient_levels": nutrient_levels or {},
        "nutrient_alerts": [_alert_json(a) for a in ordered if a["stress_class"] in NUTRIENT_STRESSES],
    }
