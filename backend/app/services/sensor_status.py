"""Run the real sensor model over stored readings, for the Trends page. Never raises: when the models are not available the
Trends page simply shows the readings without the model's status row."""
import asyncio
import logging

from app.services.inference import InferenceUnavailableError

logger = logging.getLogger(__name__)


def _classify(readings, soil_type):
    from app.services.real_inference import _get_runtime

    runtime = _get_runtime()
    from mlruntime.pipeline import sensor_features  # importable once _get_runtime has put ML_ROOT on the path

    rows = [
        {"soil_moisture": r["soil_moisture"], "temperature_c": r["temperature"], "humidity_percent": r["humidity"],
         "leaf_wetness_proxy": r["leaf_wetness"], "soil_type": soil_type}
        for r in readings
    ]
    probs = runtime.sensor.predict(sensor_features(rows, runtime.sensor_prep))
    return [runtime.sensor.classes[int(i)] for i in probs.argmax(axis=1)]


async def label_readings(readings, soil_type):
    """The sensor model's label for each reading, in order, or None if the real models are not available."""
    if not readings:
        return []
    try:
        return await asyncio.to_thread(_classify, readings, soil_type)
    except InferenceUnavailableError:
        return None
    except Exception:
        logger.exception("Could not label readings for the trend page")
        return None