"""GET /admin/audit-log names who made each change by id as well as by name, so an administrator's own actions
can be picked out reliably even when two administrators share a name."""
import uuid

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.deps import get_db
from app.core.security import create_access_token, get_password_hash
from app.db import Base
from app.main import app
from app.models import RoleEnum, User


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


async def make_user(name, phone, role):
    user_id = uuid.uuid4()
    async with SessionLocal() as db:
        db.add(User(id=user_id, name=name, phone=phone, password_hash=get_password_hash("longenough1"), role=role))
        await db.commit()
    return user_id, {"Authorization": f"Bearer {create_access_token(subject=str(user_id))}"}


@pytest.mark.asyncio
async def test_each_entry_carries_the_acting_admins_id():
    # Two administrators with the same name: only the id tells their actions apart.
    first_id, first = await make_user("Same Name", "+254799000001", RoleEnum.admin)
    second_id, second = await make_user("Same Name", "+254799000002", RoleEnum.admin)
    farmer_id, _ = await make_user("A Farmer", "+254722000001", RoleEnum.farmer)
    async with client() as ac:
        assert (await ac.patch(f"/admin/users/{farmer_id}", headers=first, json={"name": "Renamed Once"})).status_code == 200
        assert (await ac.patch(f"/admin/users/{farmer_id}", headers=second, json={"name": "Renamed Twice"})).status_code == 200
        response = await ac.get("/admin/audit-log", headers=first)

    assert response.status_code == 200
    entries = response.json()
    assert len(entries) == 2
    by_admin = {entry["admin_id"]: entry for entry in entries}
    assert set(by_admin) == {str(first_id), str(second_id)}
    assert by_admin[str(first_id)]["changes"]["name"][1] == "Renamed Once"
    assert by_admin[str(second_id)]["changes"]["name"][1] == "Renamed Twice"
    # The existing fields are all still there.
    assert {"id", "created_at", "admin_name", "action", "target_type", "target_id", "target_label", "changes"} <= set(entries[0])


@pytest.mark.asyncio
async def test_farmers_cannot_read_the_log():
    _, farmer = await make_user("A Farmer", "+254722000001", RoleEnum.farmer)
    async with client() as ac:
        assert (await ac.get("/admin/audit-log", headers=farmer)).status_code == 403
