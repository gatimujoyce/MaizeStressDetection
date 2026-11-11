"""Sensor requests move New -> In progress -> Completed, and completed ones stay on the list."""
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


async def farm(owner, name="North", status="none"):
    farm_id = uuid.uuid4()
    async with SessionLocal() as db:
        db.add(Farm(id=farm_id, user_id=owner, name=name, location="Nakuru", soil_type=SoilTypeEnum.loam, sensor_status=status))
        await db.commit()
    return farm_id


@pytest.mark.asyncio
async def test_a_request_moves_through_the_three_stages_and_stays_on_the_list():
    farmer = await user()
    plot = await farm(farmer)
    admin = headers_for(await user(RoleEnum.admin, "+254799000999", "Admin"))
    async with client() as ac:
        fh = headers_for(farmer)
        await ac.post(f"/farms/{plot}/sensor-request", headers=fh, json={"note": "Gate is blue"})
        (entry,) = (await ac.get("/admin/sensor-requests", headers=admin)).json()
        assert entry["status"] == "requested" and entry["contacted_at"] is None and entry["installed_at"] is None

        r = await ac.post(f"/admin/farms/{plot}/sensor-request/contact", headers=admin)
        assert r.json()["sensor_status"] == "in_progress" and r.json()["sensor_contacted_at"]
        (entry,) = (await ac.get("/admin/sensor-requests", headers=admin)).json()
        assert entry["status"] == "in_progress" and entry["contacted_at"]
        # asking again while an administrator is already in touch changes nothing
        again = await ac.post(f"/farms/{plot}/sensor-request", headers=fh, json={"note": "Mornings"})
        assert again.json()["sensor_status"] == "in_progress"

        await ac.post(f"/admin/farms/{plot}/sensor-installed", headers=admin)
        (entry,) = (await ac.get("/admin/sensor-requests", headers=admin)).json()
        assert entry["status"] == "installed" and entry["installed_at"] and entry["contacted_at"] and entry["note"] == "Mornings"
    async with SessionLocal() as db:
        actions = [row.action for row in (await db.execute(select(AdminAuditLog).order_by(AdminAuditLog.created_at))).scalars().all()]
        assert actions == ["farm.sensor_contact_started", "farm.sensor_installed"]


@pytest.mark.asyncio
async def test_plots_that_never_asked_are_not_in_the_list_even_if_installed():
    farmer = await user()
    await farm(farmer, "Simulator plot", status="installed")
    admin = headers_for(await user(RoleEnum.admin, "+254799000999", "Admin"))
    async with client() as ac:
        assert (await ac.get("/admin/sensor-requests", headers=admin)).json() == []


@pytest.mark.asyncio
async def test_a_request_in_progress_can_be_removed_by_the_admin_or_the_farmer():
    farmer = await user()
    first, second = await farm(farmer, "A"), await farm(farmer, "B")
    admin = headers_for(await user(RoleEnum.admin, "+254799000999", "Admin"))
    async with client() as ac:
        fh = headers_for(farmer)
        for plot in (first, second):
            await ac.post(f"/farms/{plot}/sensor-request", headers=fh, json={})
            await ac.post(f"/admin/farms/{plot}/sensor-request/contact", headers=admin)
        removed = await ac.post(f"/admin/farms/{first}/sensor-request/cancel", headers=admin)
        assert removed.json()["sensor_status"] == "none" and removed.json()["sensor_contacted_at"] is None
        cancelled = await ac.delete(f"/farms/{second}/sensor-request", headers=fh)
        assert cancelled.json()["sensor_status"] == "none" and cancelled.json()["sensor_contacted_at"] is None
        assert (await ac.get("/admin/sensor-requests", headers=admin)).json() == []


@pytest.mark.asyncio
async def test_a_farmer_cannot_pick_the_npk_sensor_when_adding_a_plot():
    farmer = await user()
    async with client() as ac:
        r = await ac.post("/farms", headers=headers_for(farmer), json={
            "name": "New plot", "location": "Nakuru", "soil_type": "loam", "has_npk_sensor": True})
        assert r.status_code == 200, r.text
        assert r.json()["has_npk_sensor"] is False and r.json()["sensor_status"] == "none"
