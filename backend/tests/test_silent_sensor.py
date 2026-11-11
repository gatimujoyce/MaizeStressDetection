import uuid
from datetime import date, datetime, timedelta, timezone

import pytest
import pytest_asyncio
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.ext.compiler import compiles

from app.core.security import get_password_hash
from app.db import Base
from app.models import Alert, Farm, RoleEnum, SensorReading, SoilTypeEnum, User
from app.services.silent_sensor import check_silent_sensors, close_silence_alert, plan_silence

NOW = datetime(2026, 11, 11, 12, 0, tzinfo=timezone.utc)


@compiles(JSONB, "sqlite")
def _jsonb_as_json(type_, compiler, **kw):
    return "JSON"


engine = create_async_engine("sqlite+aiosqlite:///:memory:")
SessionLocal = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)


@pytest_asyncio.fixture(autouse=True)
async def tables():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


async def plot(hours_ago, planting_date=None, status="installed"):
    """A farm whose last reading was hours_ago hours before NOW (None: it has never reported)."""
    user_id, farm_id = uuid.uuid4(), uuid.uuid4()
    async with SessionLocal() as db:
        db.add(User(id=user_id, name="Joy", phone=f"+2547{uuid.uuid4().int % 10**8:08d}",
                    password_hash=get_password_hash("longenough1"), role=RoleEnum.farmer))
        db.add(Farm(id=farm_id, user_id=user_id, name="North", location="Nakuru", soil_type=SoilTypeEnum.loam,
                    planting_date=planting_date, sensor_status=status))
        if hours_ago is not None:
            db.add(SensorReading(farm_id=farm_id, soil_moisture=30, temperature=22, humidity=60, leaf_wetness=8,
                                 recorded_at=NOW - timedelta(hours=hours_ago)))
        await db.commit()
    return farm_id


async def silent_alerts(farm_id):
    async with SessionLocal() as db:
        rows = (await db.execute(select(Alert).where(Alert.farm_id == farm_id, Alert.stress_class == "sensor_silent"))).scalars().all()
        return rows


def test_plan_silence():
    assert plan_silence(7, False, 6) == "open"
    assert plan_silence(7, True, 6) is None
    assert plan_silence(1, True, 6) == "close"
    assert plan_silence(1, False, 6) is None
    assert plan_silence(6, False, 6) == "open"


@pytest.mark.asyncio
async def test_a_silent_sensor_opens_one_app_alert():
    farm = await plot(hours_ago=8)
    async with SessionLocal() as db:
        assert await check_silent_sensors(db, NOW) == ([farm], [])
        assert await check_silent_sensors(db, NOW + timedelta(minutes=10)) == ([], [])   # no second alert
    (alert,) = await silent_alerts(farm)
    assert alert.severity == "Medium" and alert.channel.value == "app" and alert.source == "sensor"
    assert alert.resolved_at is None and "8 hours" in alert.message


@pytest.mark.asyncio
async def test_a_recent_reading_or_no_reading_ever_opens_nothing():
    fresh = await plot(hours_ago=2)
    never = await plot(hours_ago=None)
    async with SessionLocal() as db:
        assert await check_silent_sensors(db, NOW) == ([], [])
    assert await silent_alerts(fresh) == [] and await silent_alerts(never) == []


@pytest.mark.asyncio
async def test_the_alert_closes_when_readings_resume():
    farm = await plot(hours_ago=8)
    async with SessionLocal() as db:
        await check_silent_sensors(db, NOW)
        db.add(SensorReading(farm_id=farm, soil_moisture=30, temperature=22, humidity=60, leaf_wetness=8, recorded_at=NOW))
        await db.commit()
        assert await check_silent_sensors(db, NOW + timedelta(minutes=5)) == ([], [farm])
    (alert,) = await silent_alerts(farm)
    assert alert.resolved_at is not None


@pytest.mark.asyncio
async def test_a_new_reading_closes_it_straight_away():
    farm = await plot(hours_ago=8)
    async with SessionLocal() as db:
        await check_silent_sensors(db, NOW)
        await close_silence_alert(db, farm, NOW)
    assert (await silent_alerts(farm))[0].resolved_at is not None


@pytest.mark.asyncio
async def test_only_plots_with_an_installed_sensor_are_watched():
    photo_only = await plot(hours_ago=30, status="none")
    requested = await plot(hours_ago=30, status="requested")
    async with SessionLocal() as db:
        assert await check_silent_sensors(db, NOW) == ([], [])
    assert await silent_alerts(photo_only) == [] and await silent_alerts(requested) == []


@pytest.mark.asyncio
async def test_a_plot_not_planted_yet_stays_quiet():
    farm = await plot(hours_ago=30, planting_date=NOW.date() + timedelta(days=5))
    async with SessionLocal() as db:
        assert await check_silent_sensors(db, NOW) == ([], [])
    assert await silent_alerts(farm) == []


@pytest.mark.asyncio
async def test_a_silent_planted_plot_still_alerts():
    farm = await plot(hours_ago=30, planting_date=NOW.date() - timedelta(days=40))
    async with SessionLocal() as db:
        assert (await check_silent_sensors(db, NOW))[0] == [farm]
