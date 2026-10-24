"""Runs the full grid of source states through fusion.fuse.fuse and writes results/fusion/fusion_scenarios.csv.
Representative confidences: strong = 0.90, weak = 0.70, uncertain = 0.50 (from the bands in models/fusion/fusion_rules.yaml).
Image labels: disease = common_rust (a problem) or healthy; nutrient = phosphorus (a problem, an uncapped class),
nitrogen (capped at weak) or no_deficiency. Sensor states are the aggregated outputs, not raw readings."""
import csv
import itertools
import sys
from collections import Counter
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))

from fusion.fuse import fuse, load_rules

CFG = load_rules()
CONF = {"strong": 0.90, "weak": 0.70, "uncertain": 0.50, "not_flagging": 0.95}


def image(state, problem_label, ok_label):
    if state == "unavailable":
        return None
    if state == "not_flagging":
        return {"label": ok_label, "confidence": CONF["not_flagging"]}
    return {"label": problem_label, "confidence": CONF[state]}


def sensor(state):
    if state == "missing":
        return None
    if state == "unavailable":
        return {"status": "unavailable", "reason": "insufficient_data", "primary": None, "secondary": [],
                "hours": {}, "coverage": 0.3, "severe": False}
    if state == "not_flagging":
        return {"status": "not_flagging", "reason": None, "primary": None, "secondary": [],
                "hours": {}, "coverage": 1.0, "severe": False}
    cls = "waterlogging_risk" if state == "strong_severe" else "heat_stress"
    return {"status": "strong" if state.startswith("strong") else "weak", "reason": None, "primary": cls,
            "secondary": [], "hours": {}, "coverage": 1.0, "severe": state == "strong_severe"}


IMAGE_STATES = ["strong", "weak", "uncertain", "not_flagging", "unavailable"]
SENSOR_STATES = ["strong_severe", "strong", "weak", "not_flagging", "unavailable", "missing"]
NUTRIENT_PROBLEMS = ["phosphorus", "nitrogen"]

rows = []
for gate_ok in (True, False):
    for d, n, s in itertools.product(IMAGE_STATES, IMAGE_STATES, SENSOR_STATES):
        if not gate_ok and (d != "strong" or n != "strong"):
            continue                       # when the gate fails the image sources are dropped, so one image combination is enough
        for npl in (NUTRIENT_PROBLEMS if n in ("strong", "weak") and gate_ok else ["phosphorus"]):
            r = fuse(gate_ok, image(d, "common_rust", "healthy"), image(n, npl, "no_deficiency"), sensor(s), CFG)
            rows.append({
                "gate_ok": gate_ok, "disease": d, "nutrient": n, "nutrient_label": npl if n in ("strong", "weak") else "",
                "sensor": s, "severity": r["severity"], "retake": r["retake"],
                "primary_source": r["primary_issue"]["source"] if r["primary_issue"] else "",
                "primary_level": r["primary_issue"]["level"] if r["primary_issue"] else "",
                "n_secondary": len(r["secondary_issues"]), "notes": ";".join(r["notes"]),
            })

out = REPO / "results" / "fusion" / "fusion_scenarios.csv"
out.parent.mkdir(parents=True, exist_ok=True)
with open(out, "w", newline="", encoding="utf-8") as fh:
    w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
    w.writeheader()
    w.writerows(rows)
print("wrote", out.relative_to(REPO), "-", len(rows), "scenarios")
print("severity counts:", dict(Counter(r["severity"] for r in rows)))
print("retake counts:", dict(Counter(str(r["retake"]) for r in rows)))
bad = [r for r in rows if r["gate_ok"] and r["disease"] == "uncertain" and r["nutrient"] == "uncertain"
       and r["sensor"] in ("not_flagging", "unavailable", "missing") and r["severity"] != "none"]
print("all-uncertain-with-no-sensor-stress cases that did not give 'none':", len(bad))
cap = [r for r in rows if r["gate_ok"] and r["nutrient_label"] == "nitrogen" and r["nutrient"] == "strong"
       and r["disease"] in ("not_flagging", "uncertain", "unavailable") and r["sensor"] in ("not_flagging", "unavailable", "missing")]
print("nitrogen strong alone, severity values:", sorted({r["severity"] for r in cap}), "(expected: ['low'], because the cap makes it weak)")