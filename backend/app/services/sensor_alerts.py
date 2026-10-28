"""Real-time sensor alerts: runs after each stored sensor reading. Never raises, so a failure here cannot lose a reading."""
import logging
from datetime import timedelta

from sqlalchemy import select

from app.core.config import settings
from app.models import Alert, ChannelEnum, Farm, SensorReading
from app.services.alert_rules import plan_alerts
from app.services.inference import InferenceUnavailableError

log = logging.getLogger(__name__)
WINDOW = timedelta(hours=24)


async def evaluate_reading(db, reading):
    try:
        await _evaluate(db, reading)
    except InferenceUnavailableError as exc:
        log.info("Sensor alerts skipped: %s", exc)
    except Exception:
        log.exception("Sensor alert check failed for farm %s", reading.farm_id)
        await db.rollback()


async def _evaluate(db, reading):
    if getattr(settings, "CHECKIN_INFERENCE_MODE", "stub") != "real":
        return
    from app.services.real_inference import sensor_window_status

    farm = await db.get(Farm, reading.farm_id)
    if farm is None:
        return
    farm_id = farm.id
    now = reading.recorded_at
    rows = (await db.execute(
        select(SensorReading)
        .where(SensorReading.farm_id == farm.id, SensorReading.recorded_at > now - WINDOW,
               SensorReading.recorded_at <= now)
        .order_by(SensorReading.recorded_at))).scalars().all()
    window = [{"timestamp": r.recorded_at, "soil_moisture": r.soil_moisture, "temperature": r.temperature,
               "humidity": r.humidity, "leaf_wetness": r.leaf_wetness} for r in rows]
    soil_type = getattr(farm.soil_type, "value", farm.soil_type)
    result = await sensor_window_status(window, soil_type, now)
    if result is None:
        return

    alerts = (await db.execute(
        select(Alert).where(Alert.farm_id == farm.id, Alert.source == "sensor"))).scalars().all()
    open_alerts = {a.stress_class: a for a in alerts if a.resolved_at is None}
    last_alert_at = {}
    for a in alerts:
        if a.stress_class and (a.stress_class not in last_alert_at or a.created_at > last_alert_at[a.stress_class]):
            last_alert_at[a.stress_class] = a.created_at

    to_open, to_close = plan_alerts(result, set(open_alerts), last_alert_at, now)
    for stress in to_close:
        open_alerts[stress].resolved_at = now
    for a in to_open:
        db.add(Alert(prediction_id=None, farm_id=farm.id, severity=a["severity"], channel=ChannelEnum.app,
                     status="active", source="sensor", stress_class=a["stress_class"], message=a["message"],
                     created_at=now))
    if to_open or to_close:
        await db.commit()
        log.info("Farm %s: opened %s, closed %s", farm_id, [a["stress_class"] for a in to_open], to_close)