"""Real-time sensor alerts: runs after each stored sensor reading. Never raises, so a failure here cannot lose a reading."""
import asyncio
import logging
import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy import select, update

from app.core.config import settings
from app.models import Alert, ChannelEnum, Farm, SensorReading, User
from app.services.alert_rules import plan_alerts, sms_text
from app.services.inference import InferenceUnavailableError
from app.services.sms import send_sms

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
    farm_id, farm_name = farm.id, farm.name
    owner = await db.get(User, farm.user_id)
    phone = owner.phone if owner is not None else None
    now = reading.recorded_at
    rows = (await db.execute(
        select(SensorReading)
        .where(SensorReading.farm_id == farm_id, SensorReading.recorded_at > now - WINDOW,
               SensorReading.recorded_at <= now)
        .order_by(SensorReading.recorded_at))).scalars().all()
    window = [{"timestamp": r.recorded_at, "soil_moisture": r.soil_moisture, "temperature": r.temperature,
               "humidity": r.humidity, "leaf_wetness": r.leaf_wetness} for r in rows]
    soil_type = getattr(farm.soil_type, "value", farm.soil_type)
    result = await sensor_window_status(window, soil_type, now)
    if result is None:
        return

    alerts = (await db.execute(
        select(Alert).where(Alert.farm_id == farm_id, Alert.source == "sensor"))).scalars().all()
    open_alerts = {a.stress_class: a for a in alerts if a.resolved_at is None}
    last_alert_at = {}
    for a in alerts:
        if a.stress_class and (a.stress_class not in last_alert_at or a.created_at > last_alert_at[a.stress_class]):
            last_alert_at[a.stress_class] = a.created_at

    to_open, to_close = plan_alerts(result, set(open_alerts), last_alert_at, now)
    for stress in to_close:
        open_alerts[stress].resolved_at = now

    sms_jobs = []                                    # (alert id, text) for High alerts, sent after the commit
    for a in to_open:
        high = a["severity"] == "High"
        alert_id = uuid.uuid4()
        db.add(Alert(id=alert_id, prediction_id=None, farm_id=farm_id, severity=a["severity"],
                     channel=ChannelEnum.sms if high else ChannelEnum.app,
                     status="pending" if high else "active", source="sensor",
                     stress_class=a["stress_class"], message=a["message"], created_at=now))
        if high:
            sms_jobs.append((alert_id, sms_text(a["stress_class"], farm_name)))
    if not (to_open or to_close):
        return
    await db.commit()
    log.info("Farm %s: opened %s, closed %s", farm_id, [a["stress_class"] for a in to_open], to_close)

    for alert_id, text in sms_jobs:
        sent = False
        if phone:
            try:
                sent = await asyncio.wait_for(asyncio.to_thread(send_sms, phone, text), timeout=10.0)
            except Exception:
                log.exception("Failed to send sensor alert SMS for farm %s", farm_id)
        await db.execute(update(Alert).where(Alert.id == alert_id).values(
            status="sent" if sent else "failed",
            sent_at=datetime.now(timezone.utc) if sent else None))
    if sms_jobs:
        await db.commit()