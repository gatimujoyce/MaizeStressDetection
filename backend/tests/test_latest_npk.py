"""The Home screen shows the newest value of each nutrient, each from its own latest reading."""
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

from app.models import Farm, RoleEnum, SensorReading, SoilTypeEnum, SourceEnum, User


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


async def plot(owner_id, npk=True, name="South Field"):
    farm_id = uuid.uuid4()
    async with SessionLocal() as db:
        db.add(Farm(id=farm_id, user_id=owner_id, name=name, location="Nakuru", soil_type=SoilTypeEnum.loam,
                    has_npk_sensor=npk, sensor_status="installed"))
        await db.commit()
    return farm_id


async def add_reading(farm, hours_ago, n=None, p=None, k=None):
    async with SessionLocal() as db:
        db.add(SensorReading(id=uuid.uuid4(), farm_id=farm, recorded_at=datetime.now(timezone.utc) - timedelta(hours=hours_ago),
                             temperature=24, humidity=60, soil_moisture=40, leaf_wetness=5, source=SourceEnum.real,
                             nitrogen_mg_kg=n, phosphorus_mg_kg=p, potassium_mg_kg=k))
        await db.commit()


@pytest.mark.asyncio
async def test_each_nutrient_uses_its_own_newest_value_and_is_marked_low_or_ok():
    farmer = await user()
    farm = await plot(farmer, npk=True)
    await add_reading(farm, 5, n=15, p=30, k=200)          # older reading with all three
    await add_reading(farm, 1, n=18)                       # newer reading: only nitrogen came in
    async with client() as c:
        res = await c.get(f"/farms/{farm}/readings/latest-npk", headers=headers_for(farmer))
    assert res.status_code == 200, res.text
    items = {i["name"]: i for i in res.json()["items"]}
    assert res.json()["has_npk_sensor"] is True
    assert items["nitrogen"]["value"] == 18 and items["nitrogen"]["status"] == "low"      # warning level 20
    assert items["phosphorus"]["value"] == 30 and items["phosphorus"]["status"] == "ok"   # from the older reading
    assert items["potassium"]["value"] == 200 and items["potassium"]["status"] == "ok"


@pytest.mark.asyncio
async def test_a_nutrient_that_never_reported_is_left_out_and_plots_without_npk_return_nothing():
    farmer = await user()
    farm = await plot(farmer, npk=True)
    await add_reading(farm, 1, n=25)
    plain = await plot(farmer, npk=False, name="North Field")
    async with client() as c:
        res = await c.get(f"/farms/{farm}/readings/latest-npk", headers=headers_for(farmer))
        none = await c.get(f"/farms/{plain}/readings/latest-npk", headers=headers_for(farmer))
    assert [i["name"] for i in res.json()["items"]] == ["nitrogen"]
    assert none.json() == {"has_npk_sensor": False, "items": []}
