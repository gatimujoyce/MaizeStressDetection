"""A sensor box with a dead sensor still reports the rest; leaf wetness is worked out; the NPK sensor going quiet is noticed."""
import uuid

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.ext.compiler import compiles

from app.core.deps import get_db
from app.core.security import create_access_token, get_password_hash
from app.db import Base
from app.main import app
from datetime import datetime, timedelta, timezone

from app.models import Alert, DeviceKey, Farm, RoleEnum, SensorReading, SoilTypeEnum, SourceEnum, User
from app.services.readings_util import is_complete, leaf_wetness_from
from app.services.silent_sensor import check_silent_npk


@compiles(JSONB, "sqlite")
def _jsonb_as_json(type_, compiler, **kw):
    return "JSON"


engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
SessionLocal = async_sessionmaker(autocommit=False, autoflush=False, bind=engine, class_=AsyncSession)


async def override_get_db():
    async with SessionLocal() as session:
        yield session


@pytest_asyncio.fixture(autouse=True)
async def setup():
    previous = app.dependency_overrides.copy()
    app.dependency_overrides[get_db] = override_get_db
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    try:
        yield
    finally:
        app.dependency_overrides.clear()
        app.dependency_overrides.update(previous)
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)


def client():
    return AsyncClient(transport=ASGITransport(app=app), base_url="http://test")


def headers_for(user_id):
    return {"Authorization": f"Bearer {create_access_token(subject=str(user_id))}"}


async def user(role=RoleEnum.farmer, phone="+254722000001", name="Joy"):
    user_id = uuid.uuid4()
    async with SessionLocal() as db:
        db.add(User(id=user_id, name=name, phone=phone, password_hash=get_password_hash("longenough1"), role=role))
        await db.commit()
    return user_id


async def plot(owner_id, npk=True):
    farm_id = uuid.uuid4()
    async with SessionLocal() as db:
        db.add(Farm(id=farm_id, user_id=owner_id, name="South Field", location="Nakuru", soil_type=SoilTypeEnum.loam,
                    has_npk_sensor=npk, sensor_status="installed"))
        await db.commit()
    return farm_id


async def box_key(farm_id):
    admin = await user(RoleEnum.admin, "+254722000009", "Admin")
    async with client() as c:
        res = await c.post(f"/admin/farms/{farm_id}/device-key", headers=headers_for(admin))
    return {"X-Device-Key": res.json()["key"]}


def test_leaf_wetness_is_the_dew_point_gap():
    assert leaf_wetness_from(25, 100) == 0.0
    assert 11 < leaf_wetness_from(25, 50) < 11.3        # 25 C at 50 % humidity: dew point about 13.9 C
    assert leaf_wetness_from(None, 50) is None and leaf_wetness_from(25, None) is None and leaf_wetness_from(25, 0) is None


def test_complete_means_all_four_core_values():
    assert is_complete({"soil_moisture": 1, "temperature": 2, "humidity": 3, "leaf_wetness": 4})
    assert not is_complete({"soil_moisture": 1, "temperature": 2, "humidity": 3, "leaf_wetness": None})


@pytest.mark.asyncio
async def test_a_box_with_a_dead_sensor_still_reports_the_rest():
    farmer = await user()
    farm = await plot(farmer)
    headers = await box_key(farm)
    async with client() as c:
        res = await c.post("/device/readings", headers=headers, json={"temperature": 25, "humidity": 50, "battery_percent": 82, "firmware": "0.3"})
        empty = await c.post("/device/readings", headers=headers, json={"battery_percent": 80})
        latest = await c.get(f"/farms/{farm}/readings/latest", headers=headers_for(farmer))
    assert res.status_code == 200, res.text
    body = res.json()
    assert body["soil_moisture"] is None and body["temperature"] == 25
    assert 11 < body["leaf_wetness"] < 11.3                 # worked out from temperature and humidity
    assert body["battery_percent"] == 82 and body["firmware"] == "0.3"
    assert empty.status_code == 422                       # a reading needs at least one sensor value
    assert latest.status_code == 200 and latest.json()["soil_moisture"] is None


@pytest.mark.asyncio
async def test_a_reading_without_temperature_has_no_leaf_value_and_is_stored():
    farmer = await user()
    farm = await plot(farmer)
    headers = await box_key(farm)
    async with client() as c:
        res = await c.post("/device/readings", headers=headers, json={"soil_moisture": 33})
    assert res.status_code == 200 and res.json()["leaf_wetness"] is None
    async with SessionLocal() as db:
        row = (await db.execute(select(SensorReading))).scalar_one()
    assert row.soil_moisture == 33 and row.temperature is None


NOW = datetime(2026, 11, 11, 12, 0, tzinfo=timezone.utc)


async def add_reading(farm, hours_ago, npk):
    async with SessionLocal() as db:
        db.add(SensorReading(id=uuid.uuid4(), farm_id=farm, recorded_at=NOW - timedelta(hours=hours_ago), temperature=24,
                             humidity=60, soil_moisture=40, leaf_wetness=5, source=SourceEnum.real,
                             nitrogen_mg_kg=30 if npk else None, phosphorus_mg_kg=20 if npk else None,
                             potassium_mg_kg=150 if npk else None))
        await db.commit()


async def npk_alerts(farm):
    async with SessionLocal() as db:
        rows = (await db.execute(select(Alert).where(Alert.farm_id == farm, Alert.stress_class == "npk_silent"))).scalars().all()
    return [a for a in rows if a.resolved_at is None]


@pytest.mark.asyncio
async def test_npk_going_quiet_while_the_rest_reports_opens_an_alert_and_it_closes_on_return():
    farm = await plot(await user())
    await add_reading(farm, 20, npk=True)
    await add_reading(farm, 1, npk=False)             # the box is alive, the NPK values stopped
    async with SessionLocal() as db:
        opened, _ = await check_silent_npk(db, NOW)
    assert opened == [farm] and len(await npk_alerts(farm)) == 1
    async with SessionLocal() as db:
        assert await check_silent_npk(db, NOW) == ([], [])      # not opened twice
    await add_reading(farm, 0.1, npk=True)
    async with SessionLocal() as db:
        _, closed = await check_silent_npk(db, NOW)
    assert closed == [farm] and await npk_alerts(farm) == []


@pytest.mark.asyncio
async def test_a_silent_box_is_left_to_the_main_alert_and_plots_that_never_sent_npk_are_ignored():
    silent_box = await plot(await user())
    await add_reading(silent_box, 30, npk=True)       # everything is old: the whole box is silent
    never = await plot(await user(phone="+254722000002", name="Ann"))
    await add_reading(never, 1, npk=False)
    async with SessionLocal() as db:
        assert await check_silent_npk(db, NOW) == ([], [])
