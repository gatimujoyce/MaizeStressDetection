"""Real-time sensor alerts: runs after each stored sensor reading. Never raises, so a failure here cannot lose a reading."""
import asyncio
import logging
import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy import select, update

from app.core.config import settings
from app.models import Alert, ChannelEnum, Farm, SensorReading, User
from app.services.alert_rules import TITLES, plan_alerts, sms_text
from app.services.nutrient_rules import NUTRIENT_STRESSES, NUTRIENTS, plan_nutrient_alerts
from app.services.growth_stage import allow_nutrient_alerts, apply_stage, stage_key
from app.services.inference import InferenceUnavailableError
from app.services.sms import send_sms
from app.services.readings_util import is_complete
from app.services.silent_sensor import close_silence_alert, close_npk_silence_alert
from app.services.sms_log import record_sms

log = logging.getLogger(__name__)
WINDOW = timedelta(hours=24)


async def evaluate_reading(db, reading):
    farm_id, recorded_at = reading.farm_id, reading.recorded_at   # read now: a commit below expires the reading
    has_npk = any(getattr(reading, f, None) is not None for f in ("nitrogen_mg_kg", "phosphorus_mg_kg", "potassium_mg_kg"))
    try:
        await close_silence_alert(db, farm_id, recorded_at)   # the sensor is talking again
        if has_npk:
            await close_npk_silence_alert(db, farm_id, recorded_at)
    except Exception:
        log.exception("Could not close the silent-sensor alert for farm %s", farm_id)
        await db.rollback()
    try:
        await _evaluate(db, reading)
    except InferenceUnavailableError as exc:
        log.info("Sensor alerts skipped: %s", exc)
    except Exception:
        log.exception("Sensor alert check failed for farm %s", farm_id)
        await db.rollback()
    try:
        await _evaluate_nutrients(db, farm_id, recorded_at)
    except Exception:
        log.exception("Nutrient alert check failed for farm %s", farm_id)
        await db.rollback()


async def _evaluate(db, reading):
    if getattr(settings, "CHECKIN_INFERENCE_MODE", "stub") != "real":
        return
    from app.services.real_inference import sensor_window_status

    farm = await db.get(Farm, reading.farm_id)
    if farm is None:
        return
    farm_id, farm_name = farm.id, farm.name
    stage = stage_key(farm.planting_date, reading.recorded_at.date())   # None when no planting date: alerts work as before
    owner = await db.get(User, farm.user_id)
    phone = owner.phone if owner is not None else None
    owner_id = owner.id if owner is not None else None
    now = reading.recorded_at
    rows = (await db.execute(
        select(SensorReading)
        .where(SensorReading.farm_id == farm_id, SensorReading.recorded_at > now - WINDOW,
               SensorReading.recorded_at <= now)
        .order_by(SensorReading.recorded_at))).scalars().all()
    window = [{"timestamp": r.recorded_at, "soil_moisture": r.soil_moisture, "temperature": r.temperature,
               "humidity": r.humidity, "leaf_wetness": r.leaf_wetness} for r in rows if is_complete(r)]
    if not window:
        return                                       # the sensor model needs all four values; none of these readings has them
    soil_type = getattr(farm.soil_type, "value", farm.soil_type)
    result = await sensor_window_status(window, soil_type, now)
    if result is None:
        return

    alerts = (await db.execute(
        select(Alert).where(Alert.farm_id == farm_id, Alert.source == "sensor"))).scalars().all()
    alerts = [a for a in alerts if a.stress_class in TITLES]   # low-nutrient alerts are handled by _evaluate_nutrients
    open_alerts = {a.stress_class: a for a in alerts if a.resolved_at is None}
    last_alert_at = {}
    for a in alerts:
        if a.stress_class and (a.stress_class not in last_alert_at or a.created_at > last_alert_at[a.stress_class]):
            last_alert_at[a.stress_class] = a.created_at

    to_open, to_close = plan_alerts(result, set(open_alerts), last_alert_at, now)
    to_open = apply_stage(to_open, stage)
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
        record_sms(db, user_id=owner_id, farm_id=farm_id, alert_id=alert_id, kind="sensor_alert", phone=phone,
                   message=text, status="sent" if sent else "failed", severity="High", result=sent)
    if sms_jobs:
        await db.commit()


async def _evaluate_nutrients(db, farm_id, now):
    """Low-nutrient alerts for a plot with an NPK sensor. In the app only, never an SMS: the warning levels are provisional."""
    farm = await db.get(Farm, farm_id)
    if farm is None or not farm.has_npk_sensor:
        return
    if not allow_nutrient_alerts(stage_key(farm.planting_date, now.date())):
        return
    fields = [cfg["field"] for cfg in NUTRIENTS.values()]
    rows = (await db.execute(
        select(SensorReading)
        .where(SensorReading.farm_id == farm_id, SensorReading.recorded_at > now - WINDOW,
               SensorReading.recorded_at <= now))).scalars().all()
    readings = [{"recorded_at": r.recorded_at, **{f: getattr(r, f) for f in fields}} for r in rows]
    open_rows = (await db.execute(
        select(Alert).where(Alert.farm_id == farm_id, Alert.source == "sensor",
                            Alert.stress_class.in_(sorted(NUTRIENT_STRESSES)),
                            Alert.resolved_at.is_(None)))).scalars().all()
    open_alerts = {a.stress_class: a for a in open_rows}

    to_open, to_close = plan_nutrient_alerts(readings, set(open_alerts), now)
    if not (to_open or to_close):
        return
    for stress in to_close:
        open_alerts[stress].resolved_at = now
    for a in to_open:
        db.add(Alert(id=uuid.uuid4(), prediction_id=None, farm_id=farm_id, severity=a["severity"],
                     channel=ChannelEnum.app, status="active", source="sensor",
                     stress_class=a["stress_class"], message=a["message"], created_at=now))
    await db.commit()
    log.info("Farm %s: nutrient alerts opened %s, closed %s", farm_id, [a["stress_class"] for a in to_open], to_close)
