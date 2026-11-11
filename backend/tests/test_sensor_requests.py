"""Sensor setup requests: the farmer asks, the admin sees the farmer and plot details, installing removes it from the queue."""
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
from app.models import AdminAuditLog, Farm, RoleEnum, SoilTypeEnum, User


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


async def farm(owner, name="North"):
    farm_id = uuid.uuid4()
    async with SessionLocal() as db:
        db.add(Farm(id=farm_id, user_id=owner, name=name, location="Nakuru", soil_type=SoilTypeEnum.loam, size_acres=2.5,
                    water_source="Rain", seed_variety="H614"))
        await db.commit()
    return farm_id


@pytest.mark.asyncio
async def test_a_new_plot_is_photo_only_and_the_farmer_can_request_a_sensor():
    farmer = await user()
    plot = await farm(farmer)
    async with client() as ac:
        h = headers_for(farmer)
        assert (await ac.get(f"/farms/{plot}", headers=h)).json()["sensor_status"] == "none"
        r = await ac.post(f"/farms/{plot}/sensor-request", headers=h, json={"note": " Come on Tuesdays "})
        assert r.status_code == 200, r.text
        body = r.json()
        assert body["sensor_status"] == "requested" and body["sensor_requested_at"] and body["sensor_request_note"] == "Come on Tuesdays"
        first = body["sensor_requested_at"]
        again = await ac.post(f"/farms/{plot}/sensor-request", headers=h, json={"note": "Mornings please"})
        assert again.json()["sensor_requested_at"] == first and again.json()["sensor_request_note"] == "Mornings please"


@pytest.mark.asyncio
async def test_the_admin_sees_farmer_and_plot_details_and_installing_removes_the_request():
    farmer = await user(name="Wanjiru", phone="+254722111222")
    plot = await farm(farmer, "Upper field")
    admin = headers_for(await user(RoleEnum.admin, "+254799000999", "Admin"))
    async with client() as ac:
        await ac.post(f"/farms/{plot}/sensor-request", headers=headers_for(farmer), json={"note": "Gate is blue"})
        queue = (await ac.get("/admin/sensor-requests", headers=admin)).json()
        assert len(queue) == 1
        entry = queue[0]
        assert entry["farmer_name"] == "Wanjiru" and entry["farmer_phone"] == "+254722111222"
        assert entry["farm_name"] == "Upper field" and entry["location"] == "Nakuru" and entry["soil_type"] == "loam"
        assert entry["size_acres"] == 2.5 and entry["water_source"] == "Rain" and entry["seed_variety"] == "H614"
        assert entry["note"] == "Gate is blue"

        done = await ac.post(f"/admin/farms/{plot}/sensor-installed", headers=admin, json={"has_npk_sensor": True})
        assert done.status_code == 200, done.text
        assert done.json()["sensor_status"] == "installed" and done.json()["has_npk_sensor"] is True
        (still_listed,) = (await ac.get("/admin/sensor-requests", headers=admin)).json()
        assert still_listed["status"] == "installed"   # completed requests stay on the list

        again = await ac.post(f"/admin/farms/{plot}/sensor-installed", headers=admin)
        assert again.status_code == 200 and again.json()["sensor_status"] == "installed"
    async with SessionLocal() as db:
        log = (await db.execute(select(AdminAuditLog))).scalars().all()
        assert [row.action for row in log] == ["farm.sensor_installed"]


@pytest.mark.asyncio
async def test_a_farmer_cannot_use_the_admin_list_or_request_for_someone_elses_plot():
    farmer = await user()
    other = await user(phone="+254722000002", name="Other")
    plot = await farm(other)
    async with client() as ac:
        assert (await ac.get("/admin/sensor-requests", headers=headers_for(farmer))).status_code == 403
        assert (await ac.post(f"/farms/{plot}/sensor-request", headers=headers_for(farmer), json={})).status_code == 404


@pytest.mark.asyncio
async def test_the_farmer_can_cancel_and_cannot_cancel_or_request_once_installed():
    farmer = await user()
    plot = await farm(farmer)
    admin = headers_for(await user(RoleEnum.admin, "+254799000999", "Admin"))
    async with client() as ac:
        h = headers_for(farmer)
        await ac.post(f"/farms/{plot}/sensor-request", headers=h, json={})
        gone = await ac.delete(f"/farms/{plot}/sensor-request", headers=h)
        assert gone.json()["sensor_status"] == "none" and gone.json()["sensor_requested_at"] is None
        assert (await ac.get("/admin/sensor-requests", headers=admin)).json() == []
        await ac.post(f"/admin/farms/{plot}/sensor-installed", headers=admin)
        assert (await ac.post(f"/farms/{plot}/sensor-request", headers=h, json={})).status_code == 409
        assert (await ac.delete(f"/farms/{plot}/sensor-request", headers=h)).status_code == 409


@pytest.mark.asyncio
async def test_the_admin_can_remove_a_request_and_it_is_logged():
    farmer = await user()
    plot = await farm(farmer)
    admin = headers_for(await user(RoleEnum.admin, "+254799000999", "Admin"))
    async with client() as ac:
        await ac.post(f"/farms/{plot}/sensor-request", headers=headers_for(farmer), json={})
        r = await ac.post(f"/admin/farms/{plot}/sensor-request/cancel", headers=admin)
        assert r.json()["sensor_status"] == "none"
        assert (await ac.get("/admin/sensor-requests", headers=admin)).json() == []
    async with SessionLocal() as db:
        assert [row.action for row in (await db.execute(select(AdminAuditLog))).scalars().all()] == ["farm.sensor_request_cancelled"]