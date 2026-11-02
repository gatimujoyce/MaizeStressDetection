from datetime import datetime, timedelta, timezone

from app.services.trends import MIN_READINGS, bucket_points, build_trend, day_change, status_segments

NOW = datetime(2026, 11, 1, 12, 0, tzinfo=timezone.utc)


def reading(hours_ago, soil=40.0, temp=20.0):
    return {"recorded_at": NOW - timedelta(hours=hours_ago), "soil_moisture": soil, "temperature": temp,
            "humidity": 70.0, "leaf_wetness": 1.0}


def test_readings_are_averaged_into_buckets():
    rows = [{"recorded_at": NOW - timedelta(minutes=m), "soil_moisture": v, "temperature": 20, "humidity": 70,
             "leaf_wetness": 1} for m, v in [(5, 40), (10, 50), (50, 30)]]
    points = bucket_points(rows, NOW - timedelta(hours=2), NOW, timedelta(minutes=30))
    assert [p["n"] for p in points] == [1, 2]  # the 50-minute-old reading is alone; the other two share a bucket
    assert points[1]["soil_moisture"] == 45.0


def test_readings_outside_the_range_are_ignored():
    assert bucket_points([reading(30)], NOW - timedelta(hours=24), NOW, timedelta(minutes=30)) == []


def test_day_change_compares_the_last_day_with_the_day_before():
    rows = [reading(h, soil=50) for h in range(1, 13)] + [reading(h, soil=40) for h in range(25, 37)]
    assert day_change(rows, "soil_moisture", NOW) == 10.0


def test_day_change_is_none_without_enough_readings_in_both_days():
    rows = [reading(h) for h in range(1, 13)] + [reading(30)] * (MIN_READINGS - 1)
    assert day_change(rows, "soil_moisture", NOW) is None
    assert day_change([], "soil_moisture", NOW) is None


def test_trend_reports_latest_value_silence_and_data_hours():
    rows = [reading(h, soil=40 + h) for h in range(5, 30)]
    t = build_trend(rows, [], "24h", NOW)
    assert t["summary"]["soil_moisture"]["latest"] == 45.0 and t["hours_since_latest"] == 5.0
    assert t["bucket_minutes"] == 30 and t["hours_of_data"] == 19.0 and len(t["points"]) == 20


def test_trend_with_no_readings_is_empty_not_an_error():
    t = build_trend([], [], "7d", NOW)
    assert t["points"] == [] and t["latest_at"] is None and t["hours_since_latest"] is None
    assert t["summary"]["temperature"] == {"latest": None, "change": None}


def test_only_alerts_overlapping_the_range_are_returned():
    def alert(i, start_h, end_h):
        return {"id": i, "stress_class": "waterlogging_risk", "severity": "High",
                "created_at": NOW - timedelta(hours=start_h),
                "resolved_at": None if end_h is None else NOW - timedelta(hours=end_h)}
    alerts = [alert(1, 80, 70), alert(2, 30, 20), alert(3, 5, None)]  # the first one ended before the 24 h range
    t = build_trend([reading(1)], alerts, "24h", NOW)
    assert [a["id"] for a in t["alerts"]] == ["2", "3"] and t["alerts"][1]["end"] is None


def test_sensor_status_merges_neighbouring_buckets_and_splits_on_change():
    step = timedelta(hours=2)
    rows = [reading(h) for h in (10, 9, 8, 7, 6, 5)]  # three two-hour buckets, three readings of two
    labels = ["normal", "normal", "waterlogging_risk", "waterlogging_risk", "waterlogging_risk", "waterlogging_risk"]
    segments = status_segments(rows, labels, NOW - timedelta(hours=24), NOW, step)
    assert [s["status"] for s in segments] == ["normal", "waterlogging_risk"]


def test_sensor_status_tie_goes_to_the_stress_label_and_unknown_labels_are_normal():
    rows = [reading(1), reading(1.1)]
    seg = status_segments(rows, ["normal", "heat_stress"], NOW - timedelta(hours=24), NOW, timedelta(hours=2))
    assert [s["status"] for s in seg] == ["heat_stress"]
    seg = status_segments(rows, ["healthy", "something_else"], NOW - timedelta(hours=24), NOW, timedelta(hours=2))
    assert [s["status"] for s in seg] == ["normal"]


def test_sensor_status_leaves_a_gap_when_the_sensor_was_silent():
    rows = [reading(20), reading(2)]
    seg = status_segments(rows, ["normal", "normal"], NOW - timedelta(hours=24), NOW, timedelta(hours=2))
    assert len(seg) == 2  # same status, but 18 hours apart: two stretches, not one


def test_trend_reports_when_the_sensor_model_is_not_available():
    assert build_trend([reading(1)], [], "24h", NOW)["sensor_status"] == {"available": False, "segments": []}
    t = build_trend([reading(1)], [], "24h", NOW, ["normal"])
    assert t["sensor_status"]["available"] and len(t["sensor_status"]["segments"]) == 1