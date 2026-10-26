"""Loads the committed manifests and Keras weights into a RealPipeline. Every manifest and weight hash is checked
before TensorFlow is imported, so a missing or wrong file fails fast with RuntimeUnavailable."""
import hashlib
import json
import threading
from pathlib import Path

import numpy as np

from fusion.fuse import load_rules as load_fusion_rules
from mlruntime.pipeline import RealPipeline
from quality.photo_quality import load_rules as load_quality_rules

MANIFESTS = {"gate": "models/gate/manifest.json", "disease": "models/core_classifier/manifest.json",
             "nutrient": "models/nutrient_head/manifest.json", "sensor": "models/mlp_sensor/manifest.json"}


class RuntimeUnavailable(RuntimeError):
    """The trained model artifacts or the ML runtime could not be loaded."""


def _read_json(path):
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def _sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _weights(root, manifest_rel, manifest, file_key="file", sha_key="sha256"):
    path = (root / manifest_rel).parent / manifest[file_key]
    if not path.is_file():
        raise RuntimeUnavailable(f"trained model artifacts are missing: {path.name} (expected at {path})")
    if _sha256(path) != manifest[sha_key]:
        raise RuntimeUnavailable(f"trained model artifact {path.name} does not match its manifest hash")
    return path


class KerasPredictor:
    def __init__(self, tf, path, classes):
        self.classes = list(classes)
        self._model = tf.keras.models.load_model(path, compile=False)
        self._lock = threading.Lock()

    def predict(self, x):
        with self._lock:
            return self._model.predict(np.asarray(x, dtype="float32"), verbose=0)


def make_preprocess(tf, size):
    """Same path as the evaluation: bilinear resize without antialiasing (as image_dataset_from_directory), then
    the EfficientNet preprocessing. The input is an RGB PIL image already rotated by its EXIF orientation."""
    def preprocess(pil_image):
        x = tf.image.resize(np.asarray(pil_image, dtype=np.uint8), (size, size), method="bilinear")
        return tf.keras.applications.efficientnet.preprocess_input(x).numpy()
    return preprocess


def load_runtime(ml_root):
    root = Path(ml_root)
    manifests = {}
    for name, rel in MANIFESTS.items():
        if not (root / rel).is_file():
            raise RuntimeUnavailable(f"trained model artifacts are not configured: {rel} not found under {root}")
        manifests[name] = _read_json(root / rel)
    paths = {"gate": _weights(root, MANIFESTS["gate"], manifests["gate"]),
             "disease": _weights(root, MANIFESTS["disease"], manifests["disease"]),
             "sensor": _weights(root, MANIFESTS["sensor"], manifests["sensor"], "no_stage_file", "no_stage_sha256")}
    nutrient_on = manifests["nutrient"].get("enabled", True)
    if nutrient_on:
        paths["nutrient"] = _weights(root, MANIFESTS["nutrient"], manifests["nutrient"])
    sizes = {manifests[n]["input"]["size"] for n in ("gate", "disease", "nutrient")}
    if len(sizes) != 1:
        raise RuntimeUnavailable(f"the image models disagree on the input size: {sizes}")
    try:
        import tensorflow as tf
    except ImportError as exc:
        raise RuntimeUnavailable("TensorFlow is not installed, so the trained model artifacts cannot be loaded") from exc
    versions = {"inference_mode": "real"}
    for n in ("gate", "disease", "nutrient"):
        if n != "nutrient" or nutrient_on:
            versions[n] = f"{manifests[n]['version']}+{manifests[n]['sha256'][:8]}"
    versions["sensor"] = f"{manifests['sensor']['version']}+{manifests['sensor']['no_stage_sha256'][:8]}"
    sensor_dir = (root / MANIFESTS["sensor"]).parent
    return RealPipeline(
        gate=KerasPredictor(tf, paths["gate"], manifests["gate"]["classes"]),
        disease=KerasPredictor(tf, paths["disease"], manifests["disease"]["classes"]),
        nutrient=KerasPredictor(tf, paths["nutrient"], manifests["nutrient"]["classes"]) if nutrient_on else None,
        sensor=KerasPredictor(tf, paths["sensor"], manifests["sensor"]["classes"]),
        preprocess=make_preprocess(tf, sizes.pop()),
        fusion_cfg=load_fusion_rules(root / "models/fusion/fusion_rules.yaml"),
        quality_cfg=load_quality_rules(root / "models/quality/quality_rules.yaml"),
        sensor_prep=_read_json(sensor_dir / manifests["sensor"]["input"]["preprocessing_file"]),
        versions=versions, gate_threshold=manifests["gate"]["thresholds"].get("accept_p_in_scope"))