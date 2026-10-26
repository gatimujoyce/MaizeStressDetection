"""Real check-in inference: adapts the backend's inputs and outputs to the ML runtime (the mlruntime package).
The runtime is loaded once, lazily, from settings.ML_ROOT. All labels are mapped to the backend's existing vocabulary."""
import asyncio
import sys
import threading

from app.core.config import settings
from app.services.inference import (
    CheckinInference,
    ImageInput,
    InferenceUnavailableError,
    ModelOutput,
    SensorInput,
)

_runtime = None
_lock = threading.Lock()

TITLE = {"common_rust": "Common Rust", "gray_leaf_spot": "Gray Leaf Spot", "healthy": "Healthy",
         "northern_leaf_blight": "Northern Leaf Blight", "nitrogen": "Nitrogen Deficiency",
         "no_deficiency": "No Deficiency", "phosphorus": "Phosphorus Deficiency",
         "potassium": "Potassium Deficiency", "zinc": "Zinc Deficiency", "drought_stress": "Drought Stress",
         "heat_stress": "Heat Stress", "waterlogging_risk": "Waterlogging Risk", "normal": "Normal"}


class InvalidImageUpload(ValueError):
    """The uploaded file is not a readable image (the router turns this into a 400)."""


def _get_runtime():
    global _runtime
    with _lock:
        if _runtime is None:
            if not settings.ML_ROOT:
                raise InferenceUnavailableError(
                    "Real check-in inference is not available: trained model artifacts are not configured (ML_ROOT is empty)."
                )
            if settings.ML_ROOT not in sys.path:
                sys.path.insert(0, settings.ML_ROOT)
            from mlruntime.loader import RuntimeUnavailable, load_runtime
            try:
                _runtime = load_runtime(settings.ML_ROOT)
            except RuntimeUnavailable as exc:
                raise InferenceUnavailableError(f"Real check-in inference is not available: {exc}") from exc
        return _runtime


def to_inference(result: dict) -> CheckinInference:
    """Map a mlruntime result to the backend contract. The API keeps Low/Medium/High/Inconclusive (see severity_from);
    the full fusion output is kept in model_versions. A photo that failed the quality check is an unclear photo
    (in_scope, Inconclusive), not an out-of-scope one; only a gate rejection is out_of_scope."""
    fusion = result["fusion"]
    gate, disease, nutrient = result["gate"], result["disease"], result["nutrient"]
    sensor_src = fusion["sources"]["sensor"]
    triage_label = "out_of_scope" if (gate and not gate["ok"]) else "in_scope"
    sensor_label = (TITLE.get(sensor_src.get("label"), "Normal")
                    if sensor_src["status"] in ("strong", "weak", "not_flagging") else None)
    versions = dict(result["model_versions"])
    versions["fusion"] = {k: fusion[k] for k in ("severity", "primary_issue", "secondary_issues", "retake", "notes")}
    versions["quality_issues"] = result["quality"]["issues"]
    return CheckinInference(
        triage=ModelOutput(triage_label, float(gate["probabilities"].get("in_scope", 0.0)) if gate else 0.0),
        disease=(ModelOutput(TITLE.get(disease["label"], disease["label"]), disease["confidence"])
                 if disease else ModelOutput("Unassessed", 0.0)),
        sensor=ModelOutput(sensor_label or "Unassessed", 1.0 if sensor_label else 0.0),
        nutrient=(ModelOutput(TITLE.get(nutrient["label"], nutrient["label"]), nutrient["confidence"])
                  if nutrient else ModelOutput("Unassessed", 0.0)),
        leaf_wetness_proxy=0.0,
        model_versions=versions,
    )


def severity_from(inference: CheckinInference) -> str:
    fusion = inference.model_versions["fusion"]
    if fusion["retake"] and fusion["severity"] == "none":
        return "Inconclusive"
    return {"none": "Low", "low": "Low", "medium": "Medium", "high": "High"}[fusion["severity"]]


class RealCheckinInferencePipeline:
    wants_readings_window = True

    def __init__(self, readings=(), soil_type=None):
        self._readings, self._soil_type = list(readings), soil_type

    def with_context(self, readings, soil_type):
        return RealCheckinInferencePipeline(readings, soil_type)

    async def predict(self, image: ImageInput, reading: SensorInput | None) -> CheckinInference:
        runtime = await asyncio.to_thread(_get_runtime)
        from mlruntime.pipeline import InvalidImageError
        try:
            result = await asyncio.to_thread(runtime.run, image.content, self._readings, self._soil_type)
        except InvalidImageError as exc:
            raise InvalidImageUpload(str(exc)) from exc
        return to_inference(result)