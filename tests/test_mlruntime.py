import io
import json
import shutil
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import numpy as np
import pytest
from PIL import Image

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))

from fusion.fuse import load_rules as load_fusion_rules
from mlruntime.loader import MANIFESTS, RuntimeUnavailable, load_runtime
from mlruntime.pipeline import InvalidImageError, RealPipeline, sensor_features
from quality.photo_quality import load_rules as load_quality_rules

FUSION = load_fusion_rules()
QUALITY = load_quality_rules()
PREP = json.loads((REPO / "models/mlp_sensor/sensor_preprocessing.json").read_text(encoding="utf-8"))
NOW = datetime(2026, 10, 26, 12, 0, 0, tzinfo=timezone.utc)
GATE_C = ["in_scope", "not_leaf", "out_of_scope"]
DISEASE_C = ["common_rust", "gray_leaf_spot", "healthy", "northern_leaf_blight"]
NUTRIENT_C = ["nitrogen", "no_deficiency", "phosphorus", "potassium", "zinc"]
SENSOR_C = ["drought_stress", "heat_stress", "normal", "waterlogging_risk"]


class Fake:
    def __init__(self, classes, probs):
        self.classes, self.probs = classes, np.array(probs, dtype=float)

    def predict(self, x):
        return np.tile(self.probs, (len(x), 1))


class Boom:
    classes = ["in_scope"]

    def predict(self, x):
        raise AssertionError("this model must not be called")


def jpeg(size=(320, 320)):
    arr = np.random.default_rng(0).integers(60, 200, (size[1], size[0], 3)).astype(np.uint8)
    buf = io.BytesIO()
    Image.fromarray(arr).save(buf, "JPEG", quality=95)
    return buf.getvalue()


def make(gate=None, disease=None, nutrient="default", sensor=None, gate_threshold=None):
    return RealPipeline(
        gate=gate or Fake(GATE_C, [0.95, 0.03, 0.02]),
        disease=disease or Fake(DISEASE_C, [0.01, 0.01, 0.97, 0.01]),
        nutrient=Fake(NUTRIENT_C, [0.01, 0.95, 0.01, 0.01, 0.02]) if nutrient == "default" else nutrient,
        sensor=sensor or Fake(SENSOR_C, [0.0, 0.0, 1.0, 0.0]),
        preprocess=lambda im: np.zeros((224, 224, 3), dtype=np.float32),
        fusion_cfg=FUSION, quality_cfg=QUALITY, sensor_prep=PREP,
        versions={"inference_mode": "real"}, gate_threshold=gate_threshold)


def readings(hours=24, step_min=15, naive=False):
    n = int(hours * 60 / step_min)
    out = []
    for k in range(n):
        ts = NOW - timedelta(minutes=(n - k) * step_min)
        out.append({"timestamp": ts.replace(tzinfo=None) if naive else ts, "soil_moisture": 30.0,
                    "temperature": 24.0, "humidity": 55.0, "leaf_wetness": 8.0})
    return out


def test_gate_rejection_skips_disease_and_nutrient_and_asks_for_retake():
    p = make(gate=Fake(GATE_C, [0.1, 0.8, 0.1]), disease=Boom(), nutrient=Boom())
    r = p.run(jpeg(), [], "loam", NOW)
    assert r["gate"]["ok"] is False and r["disease"] is None and r["nutrient"] is None
    assert r["fusion"]["retake"] is True and "gate_failed_sensors_only" in r["fusion"]["notes"]


def test_healthy_leaf_without_sensor_data_is_none():
    r = make().run(jpeg(), [], "loam", NOW)
    assert r["fusion"]["severity"] == "none" and r["fusion"]["retake"] is False
    assert r["fusion"]["sources"]["sensor"]["status"] == "unavailable"


def test_diseased_leaf_is_medium_with_disease_as_primary():
    p = make(disease=Fake(DISEASE_C, [0.9, 0.04, 0.03, 0.03]))
    r = p.run(jpeg(), [], "loam", NOW)
    assert r["fusion"]["severity"] == "medium" and r["fusion"]["primary_issue"]["source"] == "disease"


def test_quality_failure_stops_before_any_model():
    r = make(gate=Boom(), disease=Boom(), nutrient=Boom()).run(jpeg((100, 100)), [], "loam", NOW)
    assert r["quality"]["ok"] is False and "too_small" in r["quality"]["issues"]
    assert r["gate"] is None and r["fusion"]["retake"] is True


def test_unreadable_bytes_raise():
    with pytest.raises(InvalidImageError):
        make().run(b"not an image", [], "loam", NOW)


def test_disabled_nutrient_head_is_not_assessed():
    r = make(nutrient=None).run(jpeg(), [], "loam", NOW)
    assert r["nutrient"] is None and "nutrient_not_assessed" in r["fusion"]["notes"]


def test_sustained_heat_in_the_window_raises_severity():
    p = make(sensor=Fake(SENSOR_C, [0.0, 1.0, 0.0, 0.0]))
    r = p.run(jpeg(), readings(), "loam", NOW)
    assert r["sensor"]["status"] == "strong"
    assert r["fusion"]["severity"] == "medium" and r["fusion"]["primary_issue"]["source"] == "sensor"


def test_naive_timestamps_are_treated_as_utc():
    p = make(sensor=Fake(SENSOR_C, [0.0, 1.0, 0.0, 0.0]))
    a = p.run(jpeg(), readings(), "loam", NOW)["sensor"]["status"]
    b = p.run(jpeg(), readings(naive=True), "loam", NOW)["sensor"]["status"]
    assert a == b == "strong"


def test_gate_threshold_overrides_argmax():
    p = make(gate=Fake(GATE_C, [0.8, 0.1, 0.1]), gate_threshold=0.9)
    assert p.run(jpeg(), [], "loam", NOW)["gate"]["ok"] is False


def test_nitrogen_cap_reaches_fusion():
    p = make(nutrient=Fake(NUTRIENT_C, [0.95, 0.01, 0.01, 0.01, 0.02]))
    r = p.run(jpeg(), [], "loam", NOW)
    assert r["fusion"]["sources"]["nutrient"]["status"] == "weak" and r["fusion"]["severity"] == "low"


def test_result_is_json_serialisable():
    p = make(sensor=Fake(SENSOR_C, [0.0, 1.0, 0.0, 0.0]))
    json.dumps(p.run(jpeg(), readings(), "loam", NOW))


def test_sensor_features_match_the_training_transform():
    from sensor.preprocessing import transform
    rows = [{"soil_moisture": 31.2, "temperature_c": 24.5, "humidity_percent": 60.0, "leaf_wetness_proxy": 7.5, "soil_type": "loam"},
            {"soil_moisture": 12.0, "temperature_c": 35.0, "humidity_percent": 30.0, "leaf_wetness_proxy": 20.0, "soil_type": "clay"},
            {"soil_moisture": 55.0, "temperature_c": 18.0, "humidity_percent": 90.0, "leaf_wetness_proxy": 1.0, "soil_type": "sandy_loam"}]
    assert np.allclose(sensor_features(rows, PREP), transform(rows, PREP, include_growth_stage=False))


def test_load_runtime_without_manifests_raises_unavailable(tmp_path):
    with pytest.raises(RuntimeUnavailable, match="trained model artifacts"):
        load_runtime(tmp_path)


def test_load_runtime_detects_a_wrong_hash(tmp_path):
    for rel in MANIFESTS.values():
        dest = tmp_path / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(REPO / rel, dest)
        m = json.loads(dest.read_text(encoding="utf-8"))
        for key in ("file", "no_stage_file"):
            if key in m:
                (dest.parent / m[key]).write_bytes(b"x")
    with pytest.raises(RuntimeUnavailable, match="manifest hash"):
        load_runtime(tmp_path)