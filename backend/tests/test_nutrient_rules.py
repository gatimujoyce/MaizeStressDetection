from datetime import datetime, timedelta, timezone

from app.services.nutrient_rules import CLEAR_MARGIN, MIN_READINGS, NUTRIENTS, plan_nutrient_alerts
from app.services.trends import build_trend

NOW = datetime(2026, 11, 2, 12, 0, tzinfo=timezone.utc)
N_LOW = NUTRIENTS["low_nitrogen"]["low"]


def npk(hours_ago, n=45.0, p=22.0, k=170.0):
    return {"recorded_at": NOW - timedelta(hours=hours_ago), "nitrogen_mg_kg": n, "phosphorus_mg_kg": p,
            "potassium_mg_kg": k}


def test_healthy_values_open_nothing():
    assert plan_nutrient_alerts([npk(h) for h in range(1, 9)], set(), NOW) == ([], [])


def test_a_low_average_opens_one_alert_for_that_nutrient_only():
    rows = [npk(h, n=N_LOW * 0.5) for h in range(1, 9)]
    to_open, to_close = plan_nutrient_alerts(rows, set(), NOW)
    assert to_close == [] and [a["stress_class"] for a in to_open] == ["low_nitrogen"]
    assert to_open[0]["severity"] == "Medium"
    assert "provisional" in to_open[0]["message"] and "10 mg/kg" in to_open[0]["message"]
    assert to_open[0]["message"].count(": ") == 1  # the app shows what follows the first ": " as the advice


def test_too_few_readings_are_not_enough_to_judge():
    rows = [npk(h, n=1.0) for h in range(1, MIN_READINGS)]
    assert plan_nutrient_alerts(rows, set(), NOW) == ([], [])


def test_readings_older_than_a_day_are_ignored():
    rows = [npk(h, n=1.0) for h in range(25, 40)] + [npk(h) for h in range(1, 6)]
    assert plan_nutrient_alerts(rows, set(), NOW) == ([], [])


def test_readings_without_npk_values_are_skipped():
    rows = [{"recorded_at": NOW - timedelta(hours=h), "nitrogen_mg_kg": None} for h in range(1, 9)]
    assert plan_nutrient_alerts(rows, set(), NOW) == ([], [])


def test_an_open_alert_stays_open_until_the_average_clears_the_margin():
    just_above = N_LOW * 1.05                      # above the level but not by the margin: stays open
    rows = [npk(h, n=just_above) for h in range(1, 9)]
    assert plan_nutrient_alerts(rows, {"low_nitrogen"}, NOW) == ([], [])
    recovered = [npk(h, n=N_LOW * CLEAR_MARGIN) for h in range(1, 9)]
    assert plan_nutrient_alerts(recovered, {"low_nitrogen"}, NOW) == ([], ["low_nitrogen"])


def test_an_alert_that_is_already_open_is_not_opened_again():
    rows = [npk(h, n=1.0) for h in range(1, 9)]
    assert plan_nutrient_alerts(rows, {"low_nitrogen"}, NOW) == ([], [])


def test_trend_without_an_npk_sensor_has_no_npk_data():
    t = build_trend([npk(1)], [], "24h", NOW)
    assert t["has_npk_sensor"] is False and t["nutrient_alerts"] == [] and "nitrogen_mg_kg" not in t["summary"]


def test_trend_with_an_npk_sensor_reports_values_levels_and_nutrient_alerts():
    base = {"temperature": 20.0, "humidity": 70.0, "soil_moisture": 40.0, "leaf_wetness": 1.0}
    rows = [{**base, **npk(h, n=12.0)} for h in range(1, 13)]
    rows[0]["potassium_mg_kg"] = None             # the newest reading missed potassium: the latest value is the one before
    rows[1]["potassium_mg_kg"] = 150.0
    alerts = [
        {"id": 1, "stress_class": "low_nitrogen", "severity": "Medium", "created_at": NOW - timedelta(hours=3), "resolved_at": None},
        {"id": 2, "stress_class": "heat_stress", "severity": "Medium", "created_at": NOW - timedelta(hours=3), "resolved_at": None},
    ]
    fields = ("temperature", "humidity", "soil_moisture", "leaf_wetness", "nitrogen_mg_kg", "phosphorus_mg_kg", "potassium_mg_kg")
    t = build_trend(rows, alerts, "24h", NOW, fields=fields, nutrient_levels={"nitrogen_mg_kg": 20.0})
    assert t["has_npk_sensor"] is True and t["nutrient_levels"] == {"nitrogen_mg_kg": 20.0}
    assert t["summary"]["nitrogen_mg_kg"]["latest"] == 12.0 and t["summary"]["potassium_mg_kg"]["latest"] == 150.0
    assert [a["id"] for a in t["alerts"]] == ["2"] and [a["id"] for a in t["nutrient_alerts"]] == ["1"]
    assert all("nitrogen_mg_kg" in p for p in t["points"])
