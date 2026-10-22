"""Typed inference contracts and the explicitly selected demo pipeline.

Real model implementations must define their own verified preprocessing,
class mapping, output interpretation, and artifact-loading behavior. This
module intentionally does not guess those details or load ML frameworks.
"""

from dataclasses import dataclass
from typing import Literal, Protocol

from app.core.config import settings

InferenceMode = Literal["demo", "real"]


@dataclass(frozen=True)
class ImageInput:
    """Uploaded image bytes as received; no decoding or preprocessing implied."""

    content: bytes
    content_type: str


@dataclass(frozen=True)
class SensorInput:
    """Existing stored sensor fields, without inferred units or transformations."""

    soil_moisture: float
    temperature: float
    humidity: float
    leaf_wetness: float


@dataclass(frozen=True)
class ModelOutput:
    """Generic model output contract; label vocabulary is model-specific."""

    label: str
    confidence: float


class TriageModel(Protocol):
    """Classifies an uploaded image into a model-defined triage result."""

    async def predict(self, image: ImageInput) -> ModelOutput: ...


class DiseaseModel(Protocol):
    """Classifies an uploaded image into a model-defined disease result."""

    async def predict(self, image: ImageInput) -> ModelOutput: ...


class NutrientModel(Protocol):
    """Classifies an uploaded image into a model-defined nutrient result."""

    async def predict(self, image: ImageInput) -> ModelOutput: ...


class SensorModel(Protocol):
    """Classifies available sensor values; missing-reading policy is TBD."""

    async def predict(self, reading: SensorInput | None) -> ModelOutput: ...


@dataclass(frozen=True)
class CheckinInference:
    """Model-stage outputs passed to deterministic severity fusion."""

    triage: ModelOutput
    disease: ModelOutput
    sensor: ModelOutput
    nutrient: ModelOutput
    leaf_wetness_proxy: float
    model_versions: dict[str, str]


class CheckinInferencePipeline(Protocol):
    async def predict(
        self,
        image: ImageInput,
        reading: SensorInput | None,
    ) -> CheckinInference: ...


class InferenceUnavailableError(RuntimeError):
    """Raised when the configured real inference implementation is unavailable."""


class DemoCheckinInferencePipeline:
    """Explicit demo-only stand-in preserving the endpoint's previous outputs."""

    async def predict(
        self,
        image: ImageInput,
        reading: SensorInput | None,
    ) -> CheckinInference:
        del image  # Demo mode does not inspect image content.
        leaf_wetness_proxy = reading.leaf_wetness if reading is not None else 2.0
        sensor_label = (
            "Waterlogging Risk"
            if leaf_wetness_proxy > 3
            else "Normal"
            if leaf_wetness_proxy > 1
            else "Heat Stress"
        )
        return CheckinInference(
            triage=ModelOutput("Needs attention", 1.0),
            disease=ModelOutput("Northern Leaf Blight", 0.94),
            sensor=ModelOutput(sensor_label, 0.88),
            nutrient=ModelOutput("Nitrogen Deficiency", 0.72),
            leaf_wetness_proxy=leaf_wetness_proxy,
            model_versions={
                "inference_mode": "demo",
                "triage": "demo",
                "disease": "demo",
                "sensor": "demo",
                "nutrient": "demo",
            },
        )


def get_checkin_inference_pipeline(
    mode: InferenceMode | None = None,
) -> CheckinInferencePipeline:
    """Return the configured pipeline, failing closed when real inference is absent."""
    selected_mode = mode or settings.CHECKIN_INFERENCE_MODE
    if selected_mode == "demo":
        return DemoCheckinInferencePipeline()
    raise InferenceUnavailableError(
        "Real check-in inference is not available: trained model artifacts and "
        "verified inference implementations are not configured."
    )
