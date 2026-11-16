"""PATCH /auth/me: people can change their own name (2 to 60 characters, trimmed), and nothing else."""
import uuid

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select
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


async def make_user(role=RoleEnum.farmer, phone="+254722000001", must_change_password=False):
    user_id = uuid.uuid4()
    async with SessionLocal() as db:
        db.add(User(id=user_id, name="Original Name", phone=phone, password_hash=get_password_hash("longenough1"),
                    role=role, must_change_password=must_change_password))
        await db.commit()
    return user_id, {"Authorization": f"Bearer {create_access_token(subject=str(user_id))}"}


async def stored(user_id):
    async with SessionLocal() as db:
        return (await db.execute(select(User).where(User.id == user_id))).scalar_one()


@pytest.mark.asyncio
@pytest.mark.parametrize("role", [RoleEnum.farmer, RoleEnum.admin])
async def test_name_is_updated_and_trimmed(role):
    user_id, headers = await make_user(role=role)
    async with client() as ac:
        response = await ac.patch("/auth/me", headers=headers, json={"name": "  Wanjiru Kamau  "})
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["name"] == "Wanjiru Kamau"
    assert set(body) == {"id", "name", "phone", "role", "must_change_password"}  # response shape unchanged
    assert body["role"] == role.value and body["phone"] == "+254722000001"
    assert (await stored(user_id)).name == "Wanjiru Kamau"


@pytest.mark.asyncio
@pytest.mark.parametrize("name", ["", " ", "A", "  B  ", "x" * 61, None, 42])
async def test_invalid_names_are_refused(name):
    user_id, headers = await make_user()
    async with client() as ac:
        response = await ac.patch("/auth/me", headers=headers, json={"name": name})
    assert response.status_code == 422
    assert (await stored(user_id)).name == "Original Name"


@pytest.mark.asyncio
async def test_name_length_limits_are_inclusive():
    _, headers = await make_user()
    async with client() as ac:
        assert (await ac.patch("/auth/me", headers=headers, json={"name": "Jo"})).status_code == 200
        assert (await ac.patch("/auth/me", headers=headers, json={"name": "y" * 60})).status_code == 200


@pytest.mark.asyncio
async def test_missing_name_is_refused():
    _, headers = await make_user()
    async with client() as ac:
        assert (await ac.patch("/auth/me", headers=headers, json={})).status_code == 422


@pytest.mark.asyncio
@pytest.mark.parametrize("extra", [
    {"phone": "0733000002"},
    {"role": "admin"},
    {"password": "sneaky-new-pass"},
    {"must_change_password": True},
    {"id": str(uuid.uuid4())},
])
async def test_other_fields_are_refused_and_nothing_changes(extra):
    user_id, headers = await make_user()
    async with client() as ac:
        response = await ac.patch("/auth/me", headers=headers, json={"name": "New Name", **extra})
    assert response.status_code == 422
    user = await stored(user_id)
    assert (user.name, user.phone, user.role, user.must_change_password) == ("Original Name", "+254722000001", RoleEnum.farmer, False)


@pytest.mark.asyncio
async def test_needs_sign_in():
    async with client() as ac:
        assert (await ac.patch("/auth/me", json={"name": "Someone"})).status_code == 401


@pytest.mark.asyncio
async def test_blocked_while_temporary_password_is_in_use():
    user_id, headers = await make_user(must_change_password=True)
    async with client() as ac:
        assert (await ac.patch("/auth/me", headers=headers, json={"name": "New Name"})).status_code == 403
    assert (await stored(user_id)).name == "Original Name"


@pytest.mark.asyncio
async def test_only_changes_the_signed_in_user():
    first_id, headers = await make_user()
    other_id, _ = await make_user(phone="+254722000009")
    async with client() as ac:
        assert (await ac.patch("/auth/me", headers=headers, json={"name": "Changed"})).status_code == 200
    assert (await stored(first_id)).name == "Changed"
    assert (await stored(other_id)).name == "Original Name"
