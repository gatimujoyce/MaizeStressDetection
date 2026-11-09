from datetime import date, timedelta

from app.services.alert_rules import plan_alerts
from app.services.growth_stage import STAGES, allow_nutrient_alerts, apply_stage, stage_for, stage_key

TODAY = date(2026, 11, 9)


def planted(days):
    return TODAY - timedelta(days=days)


def alert(stress, severity="Medium"):
    return {"stress_class": stress, "severity": severity, "message": "Text (about 8 hours so far)"}


def test_no_planting_date_means_no_stage_and_nothing_changes():
    assert stage_for(None, TODAY) is None
    rows = [alert("drought_stress")]
    assert apply_stage(rows, None) == rows
    assert allow_nutrient_alerts(None)


def test_stage_follows_days_after_planting():
    expected = {0: "germination", 6: "germination", 7: "seedling", 20: "seedling", 21: "vegetative", 55: "vegetative",
                56: "flowering", 80: "flowering", 81: "grain_filling", 115: "grain_filling", 116: "ripening",
                150: "ripening", 151: "harvest", 400: "harvest"}
    for days, key in expected.items():
        assert stage_key(planted(days), TODAY) == key, days


def test_future_planting_date_is_not_planted_yet():
    stage = stage_for(TODAY + timedelta(days=3), TODAY)
    assert stage["key"] == "not_planted" and stage["days"] == -3
    assert apply_stage([alert("heat_stress")], "not_planted") == []
    assert not allow_nutrient_alerts("not_planted")


def test_drought_and_heat_become_high_at_flowering_only():
    for stress in ("drought_stress", "heat_stress"):
        assert apply_stage([alert(stress)], "flowering")[0]["severity"] == "High"
        assert apply_stage([alert(stress)], "vegetative")[0]["severity"] == "Medium"
    assert "flowering" in apply_stage([alert("drought_stress")], "flowering")[0]["message"]


def test_waterlogging_stays_high_but_eases_when_ripening():
    assert apply_stage([alert("waterlogging_risk", "High")], "seedling")[0]["severity"] == "High"
    assert apply_stage([alert("waterlogging_risk", "High")], "ripening")[0]["severity"] == "Medium"


def test_dry_and_hot_spells_are_ignored_when_ripening():
    assert apply_stage([alert("drought_stress"), alert("heat_stress"), alert("waterlogging_risk", "High")],
                       "ripening")[0]["stress_class"] == "waterlogging_risk"


def test_nutrient_alerts_only_between_seedling_and_grain_filling():
    allowed = [s[0] for s in STAGES if allow_nutrient_alerts(s[0])]
    assert allowed == ["seedling", "vegetative", "flowering", "grain_filling"]


def test_input_list_is_not_modified():
    rows = [alert("drought_stress")]
    apply_stage(rows, "flowering")
    assert rows[0]["severity"] == "Medium" and "flowering" not in rows[0]["message"]


def test_works_with_the_real_planner():
    result = {"status": "strong", "primary": "drought_stress", "secondary": [], "hours": {"drought_stress": {"confirmed": 9}}}
    to_open, _ = plan_alerts(result, set(), {}, TODAY)
    assert to_open[0]["severity"] == "Medium"
    assert apply_stage(to_open, "flowering")[0]["severity"] == "High"
