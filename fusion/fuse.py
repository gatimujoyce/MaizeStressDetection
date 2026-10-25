"""Decision-level fusion following the RAP rules. Pure Python plus PyYAML, no TensorFlow.
All thresholds come from models/fusion/fusion_rules.yaml.

Inputs:
  gate_ok   bool, whether the gate accepted the photo
  disease   {"label": str, "confidence": float} or None
  nutrient  same, or None when the nutrient head is disabled
  sensor    the dict returned by fusion.sensor_window.aggregate_sensor, or None when there is no sensor data
Output keys: severity (none/low/medium/high), primary_issue, secondary_issues, sources, retake, notes (codes).
Source statuses: strong, weak, not_flagging, uncertain, unavailable. The display layer shows uncertain and
unavailable as "not assessed"."""
from pathlib import Path

import yaml

DEFAULT_RULES = Path(__file__).resolve().parent.parent / "models" / "fusion" / "fusion_rules.yaml"
LEVEL = {"strong": 2, "weak": 1}
ASSESSED = ("strong", "weak", "not_flagging")


def load_rules(path=None):
    with open(path or DEFAULT_RULES, encoding="utf-8") as fh:
        return yaml.safe_load(fh)


def image_source(name, result, cfg):
    if result is None:
        return {"status": "unavailable", "label": None, "confidence": None, "reason": "not_provided"}
    conf, label = float(result["confidence"]), result["label"]
    if conf < cfg["bands"]["weak_min"]:
        return {"status": "uncertain", "label": None, "confidence": conf, "reason": "low_confidence"}
    if label in cfg["not_flagging_labels"][name]:
        return {"status": "not_flagging", "label": label, "confidence": conf, "reason": None}
    status = "strong" if conf >= cfg["bands"]["strong_min"] else "weak"
    if cfg.get("class_caps", {}).get(name, {}).get(label) == "weak":
        status = "weak"
    return {"status": status, "label": label, "confidence": conf, "reason": None}


def sensor_source(sensor):
    if sensor is None:
        return {"status": "unavailable", "label": None, "confidence": None, "reason": "no_sensor_data"}
    if sensor["status"] == "unavailable":
        return {"status": "unavailable", "label": None, "confidence": None, "reason": sensor.get("reason")}
    return {"status": sensor["status"], "label": sensor["primary"], "confidence": None, "reason": None,
            "secondary_classes": sensor["secondary"], "hours": sensor["hours"]}


def severity_of(sources, sensor_severe):
    flagging = [s for s in sources.values() if s["status"] in LEVEL]
    n_strong = sum(1 for s in flagging if s["status"] == "strong")
    n_weak = len(flagging) - n_strong
    if sensor_severe:
        return "high"
    if len(flagging) >= 2 and n_strong >= 1:
        return "high"
    if n_strong >= 1:
        return "medium"
    if n_weak >= 2:
        return "medium"
    if n_weak == 1:
        return "low"
    return "none"


def fuse(gate_ok, disease, nutrient, sensor, cfg):
    if gate_ok:
        sources = {"disease": image_source("disease", disease, cfg),
                   "nutrient": image_source("nutrient", nutrient, cfg)}
    else:
        gone = {"status": "unavailable", "label": None, "confidence": None, "reason": "gate_failed"}
        sources = {"disease": dict(gone), "nutrient": dict(gone)}
    sources["sensor"] = sensor_source(sensor)

    order = cfg["primary_order"]
    flagging = sorted((n for n, s in sources.items() if s["status"] in LEVEL),
                      key=lambda n: (-LEVEL[sources[n]["status"]], order.index(n)))

    def issue(n):
        return {"source": n, "label": sources[n]["label"], "level": sources[n]["status"]}

    primary = issue(flagging[0]) if flagging else None
    secondary = [issue(n) for n in flagging[1:]]
    severity = severity_of(sources, bool(sensor and sensor.get("severe")))
    retake = (not gate_ok) or sources["disease"]["status"] not in ASSESSED

    d, se = sources["disease"]["status"], sources["sensor"]["status"]
    notes = []
    if not gate_ok:
        notes.append("gate_failed_sensors_only")
    if d in LEVEL and se == "not_flagging":
        notes.append("disease_with_normal_field_conditions")
    if d == "not_flagging" and se in LEVEL:
        notes.append("leaf_looks_healthy_sensor_stress")
    if gate_ok and nutrient is None:
        notes.append("nutrient_not_assessed")
    if retake and gate_ok:
        notes.append("unclear_retake_photo_and_check_again")
    return {"severity": severity, "primary_issue": primary, "secondary_issues": secondary,
            "sources": sources, "retake": retake, "notes": notes}