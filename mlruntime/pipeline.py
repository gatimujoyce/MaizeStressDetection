"""Real inference pipeline: photo quality, gate, disease, nutrient, sensor window, fusion.
Pure Python plus numpy and Pillow. TensorFlow is only needed by mlruntime.loader, and predictors are injected, so this
module is testable with fakes. A predictor is any object with `.classes` (class names in model output order) and
`.predict(x)` returning probabilities, one row per input row.

readings: list of dicts {"timestamp": datetime, "soil_moisture": VWC %, "temperature": C, "humidity": %, "leaf_wetness": float}.
Naive timestamps are treated as UTC. The no-stage sensor model is used because growth stage is not recorded."""
import io
from datetime import datetime, timedelta, timezone

import numpy as np
from PIL import Image, ImageOps

from fusion.fuse import fuse
from fusion.sensor_window import aggregate_sensor, pct_field_capacity
from quality.photo_quality import check_photo

GATE_ACCEPT_LABEL = "in_scope"


class InvalidImageError(ValueError):
    """The uploaded bytes could not be read as an image."""


def decode_image(content):
    try:
        with Image.open(io.BytesIO(content)) as im:
            im.load()
            return ImageOps.exif_transpose(im).convert("RGB")
    except Exception as exc:
        raise InvalidImageError("The file could not be read as an image.") from exc


def sensor_features(rows, prep):
    """No-stage feature vector; identical to sensor.preprocessing.transform(rows, prep, include_growth_stage=False)."""
    out = []
    for row in rows:
        vec = [(float(row[k]) - prep["means"][k]) / prep["stds"][k] for k in prep["numeric_features"]]
        vec += [1.0 if row["soil_type"] == s else 0.0 for s in prep["soil_types"]]
        out.append(vec)
    return np.array(out, dtype=np.float32)


def _utc(ts):
    return ts.replace(tzinfo=timezone.utc) if ts.tzinfo is None else ts.astimezone(timezone.utc)


def _top(probs, classes):
    i = int(np.argmax(probs))
    return {"label": classes[i], "confidence": float(probs[i])}


class RealPipeline:
    def __init__(self, *, gate, disease, nutrient, sensor, preprocess, fusion_cfg, quality_cfg,
                 sensor_prep, versions, gate_threshold=None):
        if GATE_ACCEPT_LABEL not in gate.classes:
            raise ValueError(f"the gate classes {gate.classes} do not contain '{GATE_ACCEPT_LABEL}'")
        self.gate, self.disease, self.nutrient, self.sensor = gate, disease, nutrient, sensor
        self.preprocess = preprocess
        self.fusion_cfg, self.quality_cfg = fusion_cfg, quality_cfg
        self.sensor_prep, self.versions, self.gate_threshold = sensor_prep, versions, gate_threshold

    def _sensor(self, readings, soil_type, now):
        s, soil = self.fusion_cfg["sensor"], self.fusion_cfg["soil"]
        if not readings or soil_type not in soil:
            return None
        start = now - timedelta(hours=s["window_hours"])
        recent = [r for r in readings if start <= _utc(r["timestamp"]) <= now]
        if not recent:
            return None
        rows = [{"soil_moisture": r["soil_moisture"], "temperature_c": r["temperature"],
                 "humidity_percent": r["humidity"], "leaf_wetness_proxy": r["leaf_wetness"],
                 "soil_type": soil_type} for r in recent]
        probs = self.sensor.predict(sensor_features(rows, self.sensor_prep))
        labels = [self.sensor.classes[int(i)] for i in np.argmax(probs, axis=1)]
        converted = [{"timestamp": _utc(r["timestamp"]), "label": lab, "temperature_c": float(r["temperature"]),
                      "soil_pct_fc": pct_field_capacity(r["soil_moisture"], soil_type, soil)}
                     for r, lab in zip(recent, labels)]
        return aggregate_sensor(converted, now, self.fusion_cfg)

    def run(self, image_bytes, readings=(), soil_type=None, now=None):
        now = _utc(now or datetime.now(timezone.utc))
        image = decode_image(image_bytes)
        quality = check_photo(image, self.quality_cfg)
        sensor = self._sensor(list(readings), soil_type, now)
        gate_info = disease = nutrient = None
        gate_ok = False
        if quality["ok"]:
            x = np.stack([self.preprocess(image)])
            gprobs = self.gate.predict(x)[0]
            gate_info = {**_top(gprobs, self.gate.classes),
                         "probabilities": {c: float(p) for c, p in zip(self.gate.classes, gprobs)}}
            p_in = float(gprobs[self.gate.classes.index(GATE_ACCEPT_LABEL)])
            gate_ok = (gate_info["label"] == GATE_ACCEPT_LABEL if self.gate_threshold is None
                       else p_in >= self.gate_threshold)
            gate_info["ok"] = gate_ok
            if gate_ok:
                disease = _top(self.disease.predict(x)[0], self.disease.classes)
                if self.nutrient is not None:
                    nutrient = _top(self.nutrient.predict(x)[0], self.nutrient.classes)
        fused = fuse(gate_ok, disease, nutrient, sensor, self.fusion_cfg)
        return {"quality": {"ok": quality["ok"], "issues": quality["issues"], "metrics": quality["metrics"]},
                "gate": gate_info, "disease": disease, "nutrient": nutrient, "sensor": sensor,
                "fusion": fused, "model_versions": self.versions}

def classify_sensor_reading(pipeline, reading, soil_type):
    """One sensor reading -> the no-stage sensor model's label (no 24-hour window).
    reading: dict with soil_moisture, temperature, humidity and leaf_wetness, as stored by the backend."""
    row = {"soil_moisture": reading["soil_moisture"], "temperature_c": reading["temperature"],
           "humidity_percent": reading["humidity"], "leaf_wetness_proxy": reading["leaf_wetness"],
           "soil_type": soil_type}
    probs = pipeline.sensor.predict(sensor_features([row], pipeline.sensor_prep))[0]
    return {**_top(probs, pipeline.sensor.classes),
            "probabilities": {c: float(p) for c, p in zip(pipeline.sensor.classes, probs)},
            "model_version": pipeline.versions.get("sensor")}


def sensor_alert_status(pipeline, readings, soil_type, now):
    """Same as RealPipeline._sensor, but with min_coverage 0 so a real-time alert can fire before 24 hours of data exist.
    The photo check-in path is unchanged and keeps the 0.60 rule."""
    import copy

    cfg = copy.deepcopy(pipeline.fusion_cfg)
    cfg["sensor"]["min_coverage"] = 0.0
    s, soil = cfg["sensor"], cfg["soil"]
    now = _utc(now)
    if not readings or soil_type not in soil:
        return None
    start = now - timedelta(hours=s["window_hours"])
    recent = [r for r in readings if start <= _utc(r["timestamp"]) <= now]
    if not recent:
        return None
    rows = [{"soil_moisture": r["soil_moisture"], "temperature_c": r["temperature"],
             "humidity_percent": r["humidity"], "leaf_wetness_proxy": r["leaf_wetness"],
             "soil_type": soil_type} for r in recent]
    probs = pipeline.sensor.predict(sensor_features(rows, pipeline.sensor_prep))
    labels = [pipeline.sensor.classes[int(i)] for i in np.argmax(probs, axis=1)]
    converted = [{"timestamp": _utc(r["timestamp"]), "label": lab, "temperature_c": float(r["temperature"]),
                  "soil_pct_fc": pct_field_capacity(r["soil_moisture"], soil_type, soil)}
                 for r, lab in zip(recent, labels)]
    return aggregate_sensor(converted, now, cfg)