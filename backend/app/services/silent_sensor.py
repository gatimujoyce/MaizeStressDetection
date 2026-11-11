"""Tell the farmer when a plot's sensor has stopped reporting. App alert only, never an SMS.

Without this a dead sensor looks the same as a calm field: no readings means no stress alerts. A background check runs
every few minutes; the alert closes by itself when a reading arrives. PROVISIONAL: the silence limit (6 hours) is our
own choice, longer than the usual gap between readings and short enough to act on the same day."""
import asyncio
import logging
import os
import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy import func, select, update

from app.core.config import settings
from app.models import Alert, ChannelEnum, Farm, SensorReading
from app.services.growth_stage import NO_ALERTS, stage_key

log = logging.getLogger(__name__)
STRESS = "sensor_silent"


def _utc(ts):
    return ts.replace(tzinfo=timezone.utc) if ts.tzinfo is None else ts.astimezone(timezone.utc)


def plan_silence(hours_since_reading, has_open_alert, limit_hours):
    """'open', 'close' or None."""
    silent = hours_since_reading >= limit_hours
    if silent and not has_open_alert:
        return "open"
    if not silent and has_open_alert:
        return "close"
    return None


def silence_message(hours):
    return f"Sensor not reporting: no readings for {int(hours)} hours. Please tell your administrator so the sensor can be checked."


async def close_silence_alert(db, farm_id, now):
    """A reading just arrived for this plot: close its open 'sensor not reporting' alert, if any."""
    result = await db.execute(update(Alert).where(
        Alert.farm_id == farm_id, Alert.source == "sensor", Alert.stress_class == STRESS,
        Alert.resolved_at.is_(None)).values(resolved_at=now))
    if result.rowcount:
        await db.commit()


async def check_silent_sensors(db, now, limit_hours=None):
    """Open or close 'sensor not reporting' alerts for every plot with an installed sensor that has reported before. Returns (opened, closed) farm ids."""
    limit = settings.SILENT_SENSOR_HOURS if limit_hours is None else limit_hours
    now = _utc(now)
    latest = dict((await db.execute(
        select(SensorReading.farm_id, func.max(SensorReading.recorded_at)).group_by(SensorReading.farm_id))).all())
    if not latest:
        return [], []
    farms = (await db.execute(select(Farm).where(
        Farm.id.in_(list(latest)), Farm.sensor_status == "installed", Farm.deleted_at.is_(None)))).scalars().all()
    open_rows = (await db.execute(select(Alert).where(
        Alert.source == "sensor", Alert.stress_class == STRESS, Alert.resolved_at.is_(None)))).scalars().all()
    open_by_farm = {a.farm_id: a for a in open_rows}

    opened, closed = [], []
    for farm in farms:
        farm_id = farm.id
        hours = (now - _utc(latest[farm_id])).total_seconds() / 3600
        if stage_key(farm.planting_date, now.date()) in NO_ALERTS:
            hours = 0                                   # not planted yet or past harvest: a quiet sensor is expected
        action = plan_silence(hours, farm_id in open_by_farm, limit)
        if action == "open":
            db.add(Alert(id=uuid.uuid4(), prediction_id=None, farm_id=farm_id, severity="Medium", channel=ChannelEnum.app,
                         status="active", source="sensor", stress_class=STRESS, message=silence_message(hours), created_at=now))
            opened.append(farm_id)
        elif action == "close":
            open_by_farm[farm_id].resolved_at = now
            closed.append(farm_id)
    if opened or closed:
        await db.commit()
        log.info("Silent sensors: opened %s, closed %s", opened, closed)
    return opened, closed


async def _run_forever(minutes):
    from app.db import SessionLocal
    while True:
        try:
            async with SessionLocal() as db:
                await check_silent_sensors(db, datetime.now(timezone.utc))
        except asyncio.CancelledError:
            raise
        except Exception:
            log.exception("Silent-sensor check failed")
        await asyncio.sleep(minutes * 60)


def start_background_check():
    """Start the repeating check. Returns the task, or None when it is switched off (SILENT_SENSOR_CHECK_MINUTES=0) or under pytest."""
    minutes = settings.SILENT_SENSOR_CHECK_MINUTES
    if minutes <= 0 or "PYTEST_CURRENT_TEST" in os.environ:
        return None
    return asyncio.create_task(_run_forever(minutes))
