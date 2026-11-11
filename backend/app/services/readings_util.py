"""Helpers for readings where a sensor may be missing. A reading is 'complete' when the four core values are all there; the
sensor model needs all four, so anything that feeds it skips incomplete readings."""
import math

from sqlalchemy import and_

CORE = ("soil_moisture", "temperature", "humidity", "leaf_wetness")


def _get(reading, field):
    return reading.get(field) if isinstance(reading, dict) else getattr(reading, field, None)


def is_complete(reading):
    return all(_get(reading, f) is not None for f in CORE)


def complete_reading():
    """SQL condition: the four core values are all present."""
    from app.models import SensorReading
    return and_(*[getattr(SensorReading, f).is_not(None) for f in CORE])


def leaf_wetness_from(temperature, humidity):
    """Dew point gap in degrees C (air temperature minus dew point, Magnus formula); small = wet leaves. The same quantity
    the field sensor reports, so a box that sends only temperature and humidity still gives the leaf value.
    None when either value is missing or the humidity is 0."""
    if temperature is None or humidity is None or humidity <= 0:
        return None
    a, b = 17.62, 243.12
    gamma = math.log(humidity / 100.0) + a * temperature / (b + temperature)
    dew_point = b * gamma / (a - gamma)
    return round(max(0.0, temperature - dew_point), 2)
