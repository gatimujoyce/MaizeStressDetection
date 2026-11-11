"""Device keys: an installed sensor box posts readings with its own key; the admin creates, replaces and revokes keys."""
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
from app.models import AdminAuditLog, DeviceKey, Farm, RoleEnum, SensorReading, SoilTypeEnum, SourceEnum, User


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


async def plot(owner_id, name="South Field", npk=False):
    farm_id = uuid.uuid4()
    async with SessionLocal() as db:
        db.add(Farm(id=farm_id, user_id=owner_id, name=name, location="Nakuru", soil_type=SoilTypeEnum.loam, has_npk_sensor=npk,
                    sensor_status="installed"))
        await db.commit()
    return farm_id


READING = {"soil_moisture": 40, "temperature": 24, "humidity": 70, "leaf_wetness": 5}


async def make_key_for(admin_id, farm_id):
    async with client() as c:
        res = await c.post(f"/admin/farms/{farm_id}/device-key", headers=headers_for(admin_id))
    assert res.status_code == 200, res.text
    return res.json()


@pytest.mark.asyncio
async def test_a_sensor_box_posts_a_reading_with_its_key():
    admin, farmer = await user(RoleEnum.admin, "+254722000009", "Admin"), await user()
    farm = await plot(farmer)
    created = await make_key_for(admin, farm)
    assert created["key"].startswith("mk_") and created["key"].startswith(created["prefix"])
    async with client() as c:
        res = await c.post("/device/readings", json=READING, headers={"X-Device-Key": created["key"]})
    assert res.status_code == 200, res.text
    assert res.json()["source"] == "real" and res.json()["farm_id"] == str(farm)
    async with SessionLocal() as db:
        rows = (await db.execute(select(SensorReading).where(SensorReading.farm_id == farm))).scalars().all()
        key = (await db.execute(select(DeviceKey))).scalar_one()
    assert len(rows) == 1 and rows[0].source == SourceEnum.real
    assert key.last_used_at is not None


@pytest.mark.asyncio
async def test_missing_wrong_and_revoked_keys_are_refused():
    admin, farmer = await user(RoleEnum.admin, "+254722000009", "Admin"), await user()
    farm = await plot(farmer)
    created = await make_key_for(admin, farm)
    async with client() as c:
        assert (await c.post("/device/readings", json=READING)).status_code == 401
        assert (await c.post("/device/readings", json=READING, headers={"X-Device-Key": "mk_wrong"})).status_code == 401
        gone = await c.delete(f"/admin/farms/{farm}/device-key", headers=headers_for(admin))
        assert gone.status_code == 200 and gone.json()["has_key"] is False
        assert (await c.post("/device/readings", json=READING, headers={"X-Device-Key": created["key"]})).status_code == 401


@pytest.mark.asyncio
async def test_a_new_key_replaces_the_old_one_and_the_key_is_stored_only_as_a_hash():
    admin, farmer = await user(RoleEnum.admin, "+254722000009", "Admin"), await user()
    farm = await plot(farmer)
    first, second = await make_key_for(admin, farm), await make_key_for(admin, farm)
    async with client() as c:
        old = await c.post("/device/readings", json=READING, headers={"X-Device-Key": first["key"]})
        new = await c.post("/device/readings", json=READING, headers={"X-Device-Key": second["key"]})
        info = await c.get(f"/admin/farms/{farm}/device-key", headers=headers_for(admin))
    assert old.status_code == 401 and new.status_code == 200
    assert info.json()["has_key"] is True and info.json()["prefix"] == second["prefix"] and "key" not in info.json()
    async with SessionLocal() as db:
        stored = (await db.execute(select(DeviceKey.key_hash))).scalars().all()
    assert len(stored) == 2 and first["key"] not in stored and second["key"] not in stored


@pytest.mark.asyncio
async def test_key_actions_are_admin_only_and_audited():
    admin, farmer = await user(RoleEnum.admin, "+254722000009", "Admin"), await user()
    farm = await plot(farmer)
    async with client() as c:
        assert (await c.post(f"/admin/farms/{farm}/device-key", headers=headers_for(farmer))).status_code == 403
    await make_key_for(admin, farm)
    async with client() as c:
        await c.delete(f"/admin/farms/{farm}/device-key", headers=headers_for(admin))
    async with SessionLocal() as db:
        actions = [a.action for a in (await db.execute(select(AdminAuditLog))).scalars().all()]
    assert "farm.device_key_created" in actions and "farm.device_key_revoked" in actions


@pytest.mark.asyncio
async def test_device_readings_follow_the_same_rules_as_dashboard_readings():
    admin, farmer = await user(RoleEnum.admin, "+254722000009", "Admin"), await user()
    farm = await plot(farmer, npk=False)
    key = (await make_key_for(admin, farm))["key"]
    async with client() as c:
        npk = await c.post("/device/readings", json={**READING, "nitrogen_mg_kg": 20}, headers={"X-Device-Key": key})
        bad = await c.post("/device/readings", json={**READING, "soil_moisture": 500}, headers={"X-Device-Key": key})
        who = await c.get("/device/whoami", headers={"X-Device-Key": key})
    assert npk.status_code == 422 and bad.status_code == 422
    assert who.status_code == 200 and who.json()["farm_name"] == "South Field"
