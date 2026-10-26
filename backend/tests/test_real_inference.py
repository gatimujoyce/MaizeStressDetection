import json
import uuid

from app.routers.checkins import build_prediction_data
from app.services.real_inference import severity_from, to_inference


def make_result(severity="high", retake=False, quality_ok=True, gate_ok=True,
                disease=("northern_leaf_blight", 0.97), nutrient=None):
    gate = None
    if quality_ok:
        gate = {"label": "in_scope" if gate_ok else "out_of_scope", "confidence": 0.99, "ok": gate_ok,
                "probabilities": {"in_scope": 0.99 if gate_ok else 0.01, "not_leaf": 0.005,
                                  "out_of_scope": 0.005 if gate_ok else 0.985}}
    passed = quality_ok and gate_ok
    primary = {"source": "disease", "label": disease[0], "level": "strong"} if disease and passed else None
    return {
        "quality": {"ok": quality_ok, "issues": [] if quality_ok else ["too_dark"], "metrics": {}},
        "gate": gate,
        "disease": {"label": disease[0], "confidence": disease[1]} if disease and passed else None,
        "nutrient": {"label": nutrient[0], "confidence": nutrient[1]} if nutrient and passed else None,
        "sensor": None,
        "fusion": {"severity": severity, "primary_issue": primary, "secondary_issues": [], "retake": retake,
                   "notes": [], "sources": {"sensor": {"status": "unavailable", "label": None}}},
        "model_versions": {"inference_mode": "real", "gate": "gate-v1+655a8af6"},
    }


def test_high_severity_maps_labels_to_the_backend_vocabulary():
    inf = to_inference(make_result())
    assert inf.triage.label == "in_scope"
    assert inf.disease.label == "Northern Leaf Blight" and inf.disease.confidence == 0.97
    assert severity_from(inf) == "High"


def test_none_severity_without_retake_is_low():
    inf = to_inference(make_result(severity="none", disease=("healthy", 0.99)))
    assert severity_from(inf) == "Low" and inf.disease.label == "Healthy"


def test_none_severity_with_retake_is_inconclusive():
    inf = to_inference(make_result(severity="none", retake=True, disease=("common_rust", 0.5)))
    assert severity_from(inf) == "Inconclusive"


def test_quality_failure_is_an_unclear_photo_not_out_of_scope():
    inf = to_inference(make_result(severity="none", retake=True, quality_ok=False))
    assert inf.triage.label == "in_scope" and inf.disease.label == "Unassessed"
    assert severity_from(inf) == "Inconclusive"
    assert inf.model_versions["quality_issues"] == ["too_dark"]


def test_gate_rejection_is_out_of_scope():
    inf = to_inference(make_result(severity="none", retake=True, gate_ok=False))
    assert inf.triage.label == "out_of_scope" and severity_from(inf) == "Inconclusive"


def test_real_prediction_uses_fusion_severity_and_is_json_serialisable():
    inf = to_inference(make_result(nutrient=("zinc", 0.9)))
    data = build_prediction_data(uuid.uuid4(), inf)
    assert data["severity"] == "High" and data["nutrient_label"] == "Zinc Deficiency"
    json.dumps(data["model_versions"])