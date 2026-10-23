"""Typed inference contracts and the explicitly selected demo pipeline.

Real model implementations must define their own verified preprocessing,
class mapping, output interpretation, and artifact-loading behavior. This
module intentionally does not guess those details or load ML frameworks.
"""

import logging
import os
import random
from dataclasses import dataclass
from typing import Literal, Protocol

from app.core.config import settings

logger = logging.getLogger(__name__)

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


@dataclass(frozen=True)
class StubScenario:
    disease_label: str
    disease_confidence: float
    sensor_label: str
    nutrient_label: str
    triage_result: str = "in_scope"
    leaf_wetness_proxy: float = 4.0


STUB_SCENARIOS = {
    "healthy": StubScenario(
        disease_label="Healthy",
        disease_confidence=0.99,
        sensor_label="Normal",
        nutrient_label="No Deficiency",
    ),
    "common_rust": StubScenario(
        disease_label="Common Rust",
        disease_confidence=0.94,
        sensor_label="Waterlogging Risk",
        nutrient_label="No Deficiency",
    ),
    "northern_leaf_blight": StubScenario(
        disease_label="Northern Leaf Blight",
        disease_confidence=0.94,
        sensor_label="Waterlogging Risk",
        nutrient_label="No Deficiency",
    ),
    "gray_leaf_spot": StubScenario(
        disease_label="Gray Leaf Spot",
        disease_confidence=0.94,
        sensor_label="Heat Stress",
        nutrient_label="No Deficiency",
    ),
    "drought_stress": StubScenario(
        disease_label="Healthy",
        disease_confidence=0.99,
        sensor_label="Drought Stress",
        nutrient_label="No Deficiency",
    ),
    "heat_stress": StubScenario(
        disease_label="Healthy",
        disease_confidence=0.99,
        sensor_label="Heat Stress",
        nutrient_label="No Deficiency",
    ),
    "waterlogging_risk": StubScenario(
        disease_label="Healthy",
        disease_confidence=0.99,
        sensor_label="Waterlogging Risk",
        nutrient_label="No Deficiency",
    ),
    "nutrient_deficiency": StubScenario(
        disease_label="Healthy",
        disease_confidence=0.99,
        sensor_label="Normal",
        nutrient_label="Nitrogen Deficiency",
    ),
    "out_of_scope": StubScenario(
        disease_label="Healthy",
        disease_confidence=0.99,
        sensor_label="Normal",
        nutrient_label="No Deficiency",
        triage_result="out_of_scope",
    ),
    "inconclusive": StubScenario(
        disease_label="Common Rust",
        disease_confidence=0.5,
        sensor_label="Normal",
        nutrient_label="No Deficiency",
        leaf_wetness_proxy=4.0,
    ),
}
_last_random_scenario: str | None = None


def _get_stub_scenario() -> StubScenario:
    global _last_random_scenario

    requested = os.getenv("STUB_SCENARIO", "random").strip().lower()
    if requested == "random":
        choices = [name for name in STUB_SCENARIOS if name != _last_random_scenario]
        selected = random.choice(choices)
        _last_random_scenario = selected
        return STUB_SCENARIOS[selected]
    try:
        return STUB_SCENARIOS[requested]
    except KeyError as exc:
        allowed = ", ".join(("random", *STUB_SCENARIOS.keys()))
        raise ValueError(
            f"Invalid STUB_SCENARIO {requested!r}; allowed values: {allowed}"
        ) from exc


class StubCheckinInferencePipeline:
    """Scenario-driven stand-in used until real model artifacts are available."""

    async def predict(
        self,
        image: ImageInput,
        reading: SensorInput | None,
    ) -> CheckinInference:
        del image
        scenario = _get_stub_scenario()
        use_readings = os.getenv("STUB_USE_READINGS", "true").strip().lower() in {
            "1", "true", "yes", "on"
        }
        if reading is None or not use_readings:
            sensor_label = scenario.sensor_label
            leaf_wetness_proxy = scenario.leaf_wetness_proxy
        else:
            leaf_wetness_proxy = reading.leaf_wetness
            sensor_label = (
                "Waterlogging Risk"
                if leaf_wetness_proxy > 3
                else "Normal"
                if leaf_wetness_proxy > 1
                else "Heat Stress"
            )

        return CheckinInference(
            triage=ModelOutput(scenario.triage_result, 1.0),
            disease=ModelOutput(
                scenario.disease_label,
                scenario.disease_confidence,
            ),
            sensor=ModelOutput(sensor_label, 0.88),
            nutrient=ModelOutput(scenario.nutrient_label, 0.9),
            leaf_wetness_proxy=leaf_wetness_proxy,
            model_versions={
                "inference_mode": "stub",
                "triage": "stub",
                "disease": "stub",
                "sensor": "stub",
                "nutrient": "stub",
            },
        )


def get_checkin_inference_pipeline(
    mode: InferenceMode | None = None,
) -> CheckinInferencePipeline:
    """Select real inference when available, otherwise use the scenario stub."""
    selected_mode = mode or settings.CHECKIN_INFERENCE_MODE
    if selected_mode == "demo":
        return StubCheckinInferencePipeline()
    unavailable = InferenceUnavailableError(
        "Real check-in inference is not available: trained model artifacts and "
        "verified inference implementations are not configured."
    )
    if mode is not None:
        raise unavailable

    logger.warning("Real inference is unavailable; using the configured stub scenario")
    return StubCheckinInferencePipeline()
