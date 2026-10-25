import copy
import sys
from datetime import datetime, timedelta
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "scripts"))

from fusion.fuse import fuse, image_source, load_rules
from fusion.sensor_window import _in_band, aggregate_sensor, pct_field_capacity

CFG = load_rules()
NOW = datetime(2026, 10, 24, 12, 0, 0)


def readings(label_at, hours=24.0, step=0.25, **extra):
    """One reading every `step` hours over the last `hours` hours; label_at(hours_ago) gives its label."""
    out = []
    for k in range(int(round(hours / step))):
        ago = hours - k * step
        r = {"timestamp": NOW - timedelta(hours=ago), "label": label_at(ago)}
        r.update({key: (v(ago) if callable(v) else v) for key, v in extra.items()})
        out.append(r)
    return out


def agg(rs, cfg=CFG):
    return aggregate_sensor(rs, NOW, cfg)


# ---- sensor window ----
def test_no_readings_is_unavailable():
    r = agg([])
    assert r["status"] == "unavailable" and r["reason"] == "no_readings"


def test_short_window_is_insufficient():
    r = agg(readings(lambda ago: "normal", hours=6))
    assert r["status"] == "unavailable" and r["reason"] == "insufficient_data"


def test_sparse_readings_do_not_count_as_coverage():
    r = agg(readings(lambda ago: "normal", step=4.0))
    assert r["status"] == "unavailable" and r["reason"] == "insufficient_data"


def test_heat_five_hours_is_strong():
    r = agg(readings(lambda ago: "heat_stress" if ago <= 5 else "normal"))
    assert r["status"] == "strong" and r["primary"] == "heat_stress"


def test_heat_three_hours_is_weak():
    r = agg(readings(lambda ago: "heat_stress" if ago <= 3 else "normal"))
    assert r["status"] == "weak" and r["primary"] == "heat_stress"


def test_heat_below_weak_threshold_is_not_flagging():
    r = agg(readings(lambda ago: "heat_stress" if ago <= 1.75 else "normal"))
    assert r["status"] == "not_flagging" and r["primary"] is None


def test_single_flicker_is_ignored():
    r = agg(readings(lambda ago: "heat_stress" if ago == 12.0 else "normal"))
    assert r["status"] == "not_flagging"


def test_recovery_drops_one_level():
    r = agg(readings(lambda ago: "heat_stress" if 3 < ago <= 10 else "normal"))
    assert r["status"] == "weak" and r["primary"] == "heat_stress"


def test_borderline_temperature_reaches_weak_never_strong():
    r = agg(readings(lambda ago: "normal", temperature_c=30.0, soil_pct_fc=80.0))
    assert r["status"] == "weak" and r["primary"] == "heat_stress"
    assert r["hours"]["heat_stress"]["confirmed"] == 0.0


def test_band_edges():
    heat = CFG["sensor"]["borderline"]["heat_stress"]
    wet = CFG["sensor"]["borderline"]["waterlogging_risk"]
    assert not _in_band(29.0, heat) and _in_band(29.5, heat) and _in_band(31.99, heat) and not _in_band(32.0, heat)
    assert not _in_band(100.0, wet) and _in_band(100.5, wet) and _in_band(110.0, wet) and not _in_band(110.01, wet)
    assert not _in_band(None, heat)


def test_waterlogging_twelve_hours_is_strong_and_severe():
    r = agg(readings(lambda ago: "waterlogging_risk" if ago <= 12 else "normal"))
    assert r["status"] == "strong" and r["primary"] == "waterlogging_risk" and r["severe"] is True


def test_primary_prefers_level_over_hours():
    cfg = copy.deepcopy(CFG)
    cfg["sensor"]["recovery_hours"] = 0           # no recovery check, so both classes stay active
    r = agg(readings(lambda ago: "heat_stress" if ago <= 5 else ("drought_stress" if 6 < ago <= 14 else "normal")), cfg)
    assert r["primary"] == "heat_stress" and r["status"] == "strong"
    assert r["secondary"] == [{"class": "drought_stress", "level": "weak"}]


# ---- fusion ----
def sensor(status, primary="heat_stress", severe=False):
    return {"status": status, "reason": None, "primary": primary if status in ("weak", "strong") else None,
            "secondary": [], "hours": {}, "coverage": 1.0, "severe": severe}


def d(label, conf):
    return {"label": label, "confidence": conf}


HEALTHY, NODEF = d("healthy", 0.95), d("no_deficiency", 0.95)


@pytest.mark.parametrize("conf,status", [(0.80, "strong"), (0.7999, "weak"), (0.60, "weak"), (0.5999, "uncertain")])
def test_confidence_bands(conf, status):
    assert image_source("disease", d("common_rust", conf), CFG)["status"] == status


def test_low_confidence_healthy_is_uncertain():
    assert image_source("disease", d("healthy", 0.55), CFG)["status"] == "uncertain"


def test_nothing_flagging_is_none():
    r = fuse(True, HEALTHY, NODEF, sensor("not_flagging"), CFG)
    assert r["severity"] == "none" and r["retake"] is False and r["primary_issue"] is None and r["notes"] == []


def test_one_weak_is_low():
    r = fuse(True, d("common_rust", 0.7), NODEF, sensor("not_flagging"), CFG)
    assert r["severity"] == "low" and r["primary_issue"]["source"] == "disease"


def test_one_strong_is_medium_and_notes_normal_conditions():
    r = fuse(True, d("common_rust", 0.9), NODEF, sensor("not_flagging"), CFG)
    assert r["severity"] == "medium" and r["notes"] == ["disease_with_normal_field_conditions"]


def test_two_weak_is_medium_disease_first():
    r = fuse(True, d("common_rust", 0.7), d("phosphorus", 0.7), sensor("not_flagging"), CFG)
    assert r["severity"] == "medium" and r["primary_issue"]["source"] == "disease"
    assert [i["source"] for i in r["secondary_issues"]] == ["nutrient"]


def test_strong_plus_weak_is_high():
    r = fuse(True, d("common_rust", 0.9), d("phosphorus", 0.7), sensor("not_flagging"), CFG)
    assert r["severity"] == "high"


def test_severe_sensor_alone_is_high():
    r = fuse(True, HEALTHY, NODEF, sensor("strong", "waterlogging_risk", severe=True), CFG)
    assert r["severity"] == "high"


def test_strong_heat_alone_is_medium():
    r = fuse(True, HEALTHY, NODEF, sensor("strong", "heat_stress"), CFG)
    assert r["severity"] == "medium"


def test_uncertain_never_raises_severity():
    r = fuse(True, d("common_rust", 0.9), d("zinc", 0.5), sensor("not_flagging"), CFG)
    assert r["severity"] == "medium" and r["sources"]["nutrient"]["status"] == "uncertain"


def test_everything_uncertain_is_none_with_retake():
    r = fuse(True, d("common_rust", 0.5), d("zinc", 0.4), None, CFG)
    assert r["severity"] == "none" and r["retake"] is True
    assert "unclear_retake_photo_and_check_again" in r["notes"]


def test_gate_failed_uses_sensors_only_and_asks_for_retake():
    r = fuse(False, d("common_rust", 0.95), d("zinc", 0.95), sensor("weak", "drought_stress"), CFG)
    assert r["sources"]["disease"]["status"] == "unavailable" and r["sources"]["nutrient"]["status"] == "unavailable"
    assert r["severity"] == "low" and r["retake"] is True and r["primary_issue"]["source"] == "sensor"
    assert "gate_failed_sensors_only" in r["notes"]


def test_healthy_leaf_stressed_sensor_reports_sensor_without_disease_claim():
    r = fuse(True, HEALTHY, NODEF, sensor("weak", "heat_stress"), CFG)
    assert r["primary_issue"]["source"] == "sensor" and r["primary_issue"]["label"] == "heat_stress"
    assert r["notes"] == ["leaf_looks_healthy_sensor_stress"]


def test_nitrogen_is_capped_at_weak():
    assert image_source("nutrient", d("nitrogen", 0.95), CFG)["status"] == "weak"
    assert image_source("nutrient", d("phosphorus", 0.95), CFG)["status"] == "strong"
    assert image_source("nutrient", d("nitrogen", 0.55), CFG)["status"] == "uncertain"


def test_nutrient_head_disabled_changes_nothing_else():
    r = fuse(True, d("common_rust", 0.9), None, sensor("not_flagging"), CFG)
    assert r["sources"]["nutrient"]["status"] == "unavailable" and r["severity"] == "medium"
    assert "nutrient_not_assessed" in r["notes"]


def test_tie_goes_to_nutrient_before_sensor():
    r = fuse(True, HEALTHY, d("zinc", 0.7), sensor("weak", "heat_stress"), CFG)
    assert r["primary_issue"]["source"] == "nutrient" and r["severity"] == "medium"
    assert [i["source"] for i in r["secondary_issues"]] == ["sensor"]


def test_strong_sensor_beats_weak_disease():
    r = fuse(True, d("common_rust", 0.7), NODEF, sensor("strong", "heat_stress"), CFG)
    assert r["primary_issue"]["source"] == "sensor" and r["severity"] == "high"


# ---- config consistency ----
def test_config_matches_sensor_constants():
    import sensor_constants as sc
    assert CFG["soil"] == sc.SOIL_PROPERTIES
    heat = CFG["sensor"]["borderline"]["heat_stress"]
    wet = CFG["sensor"]["borderline"]["waterlogging_risk"]
    assert heat["above"] == sc.NORMAL_TEMP_RANGE[1] and heat["below"] == sc.HEAT_THRESHOLD_C
    assert wet["above"] == sc.NORMAL_UPPER_PCT_FC and wet["up_to"] == sc.WATERLOG_THRESHOLD_PCT_FC


def test_pct_field_capacity_formula():
    assert pct_field_capacity(10.0, "sandy_loam", CFG["soil"]) == 50.0




def test_pct_field_capacity_agrees_with_rule_baseline():
    import sensor_constants as sc
    from rule_baseline import predict_sensor_stress
    cases = [(40.0, "drought_stress"), (54.0, "drought_stress"), (56.0, "normal"), (100.0, "normal"),
             (105.0, "normal"), (109.0, "normal"), (111.0, "waterlogging_risk"), (130.0, "waterlogging_risk")]
    for soil, props in sc.SOIL_PROPERTIES.items():
        for pct, expected in cases:
            moisture = pct / 100.0 * props["field_capacity"]
            assert pct_field_capacity(moisture, soil, CFG["soil"]) == pytest.approx(pct)
            assert predict_sensor_stress(moisture, 22.0, soil) == expected




def test_retake_when_disease_not_assessed_even_if_sensor_contributes():
    r = fuse(True, d("common_rust", 0.5), NODEF, sensor("weak", "heat_stress"), CFG)
    assert r["retake"] is True and r["severity"] == "low"
    assert "unclear_retake_photo_and_check_again" in r["notes"]


def test_no_retake_when_only_nutrient_not_assessed():
    r = fuse(True, HEALTHY, d("zinc", 0.5), sensor("not_flagging"), CFG)
    assert r["retake"] is False and r["severity"] == "none"


def test_more_evidence_never_lowers_severity():
    import itertools
    sev = {"none": 0, "low": 1, "medium": 2, "high": 3}
    levels = ["not_flagging", "weak", "strong"]
    rank = {lv: i for i, lv in enumerate(levels)}

    def src(name, level):
        if level == "not_flagging":
            return HEALTHY if name == "disease" else NODEF
        return d("common_rust" if name == "disease" else "phosphorus", 0.9 if level == "strong" else 0.7)

    def severity(dl, nl, sl):
        return sev[fuse(True, src("disease", dl), src("nutrient", nl), sensor(sl), CFG)["severity"]]

    combos = list(itertools.product(levels, repeat=3))
    for a in combos:
        for b in combos:
            if all(rank[x] <= rank[y] for x, y in zip(a, b)):
                assert severity(*a) <= severity(*b), (a, b)





def test_scattered_hourly_readings_do_not_add_up_to_an_episode():
    spaced = {int(h) for h in (3, 6, 9, 12, 15, 18, 21, 23)}
    rs = readings(lambda ago: "heat_stress" if int(ago) in spaced and ago == int(ago) else "normal", step=1.0)
    assert agg(rs)["status"] == "not_flagging"
    cfg = copy.deepcopy(CFG)
    cfg["sensor"]["min_run_readings"] = 1
    assert agg(rs, cfg)["status"] != "not_flagging"