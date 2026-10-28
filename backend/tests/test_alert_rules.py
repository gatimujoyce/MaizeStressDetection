import copy
from datetime import datetime, timedelta, timezone
from pathlib import Path

import yaml

import sys
sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parent.parent.parent))

from app.services.alert_rules import plan_alerts, stress_levels
from fusion.sensor_window import aggregate_sensor

CFG = yaml.safe_load((Path(__file__).resolve().parent.parent.parent / "models/fusion/fusion_rules.yaml").read_text(encoding="utf-8"))
CFG = copy.deepcopy(CFG)
CFG["sensor"]["min_coverage"] = 0.0
T0 = datetime(2026, 10, 28, 0, 0, tzinfo=timezone.utc)


def reading(i, label, temp=23.0, pct=80.0):
    return {"timestamp": T0 + timedelta(hours=i), "label": label, "temperature_c": temp, "soil_pct_fc": pct}


def replay(labels):
    """Feed hourly readings one at a time, as the backend does, and collect what happens."""
    rs, open_, last, events = [], set(), {}, []
    for i, lab in enumerate(labels):
        rs.append(reading(i, lab, temp=36.0 if lab == "heat_stress" else 23.0, pct=125.0 if lab == "waterlogging_risk" else 80.0))
        now = rs[-1]["timestamp"]
        to_open, to_close = plan_alerts(aggregate_sensor(rs, now, CFG), open_, last, now)
        for a in to_open:
            open_.add(a["stress_class"]); last[a["stress_class"]] = now; events.append((i, "open", a["stress_class"], a["severity"]))
        for s in to_close:
            open_.discard(s); events.append((i, "close", s, None))
    return events


def test_heat_opens_once_after_five_hours():
    ev = replay(["heat_stress"] * 10)
    assert [e for e in ev if e[1] == "open"] == [(5, "open", "heat_stress", "Medium")]


def test_waterlogging_is_high():
    ev = replay(["waterlogging_risk"] * 14)
    assert ev and ev[0][2:] == ("waterlogging_risk", "High")


def test_normal_never_alerts():
    assert replay(["normal"] * 24) == []


def test_alert_closes_after_recovery():
    ev = replay(["heat_stress"] * 8 + ["normal"] * 3)
    assert [e[1] for e in ev] == ["open", "close"]


def test_cooldown_blocks_flapping():
    ev = replay(["heat_stress"] * 8 + ["normal"] * 2 + ["heat_stress"] * 1)
    assert [e[1] for e in ev].count("open") == 1


def test_unavailable_changes_nothing():
    res = {"status": "unavailable", "primary": None, "secondary": [], "hours": {}}
    assert plan_alerts(res, {"heat_stress"}, {}, T0) == ([], [])
    assert stress_levels(res) == {}