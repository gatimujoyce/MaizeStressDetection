import uuid

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import settings
from app.core.deps import get_db
from app.core.security import get_password_hash, verify_password
from app.db import Base
from app.main import app
from app.models import ModelNameEnum, ModelVersion, RoleEnum, User
from scripts.create_admin import create_or_promote_admin


@compiles(JSONB, "sqlite")
def _jsonb_as_json(type_, compiler, **kw):
    return "JSON"


engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
TestSessionLocal = async_sessionmaker(
    autocommit=False, autoflush=False, bind=engine, class_=AsyncSession
)


async def override_get_db():
    async with TestSessionLocal() as session:
        yield session


@pytest_asyncio.fixture(autouse=True)
async def setup_db():
    previous_overrides = app.dependency_overrides.copy()
    app.dependency_overrides[get_db] = override_get_db
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    try:
        yield
    finally:
        app.dependency_overrides.clear()
        app.dependency_overrides.update(previous_overrides)
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)


@pytest.mark.asyncio
async def test_create_admin_normalizes_phone_and_hashes_password():
    async with TestSessionLocal() as db:
        user = await create_or_promote_admin(
            db, "0712345678", "Admin", "secret-password"
        )
    assert user.phone == "+254712345678"
    assert user.role == RoleEnum.admin
    assert verify_password("secret-password", user.password_hash)


@pytest.mark.asyncio
async def test_duplicate_refused_without_promote_and_changes_nothing():
    original_hash = get_password_hash("original-password")
    user_id = uuid.uuid4()
    async with TestSessionLocal() as db:
        db.add(User(
            id=user_id, name="Existing Farmer", phone="+254712345678",
            password_hash=original_hash, role=RoleEnum.farmer,
        ))
        await db.commit()
        with pytest.raises(ValueError, match="--promote"):
            await create_or_promote_admin(
                db, "0712345678", "Replacement Name", "replacement-password"
            )
        user = await db.scalar(select(User).where(User.id == user_id))
    assert user.name == "Existing Farmer"
    assert user.role == RoleEnum.farmer
    assert user.password_hash == original_hash


@pytest.mark.asyncio
async def test_promote_changes_role_but_preserves_password_and_other_fields():
    original_hash = get_password_hash("original-password")
    user_id = uuid.uuid4()
    async with TestSessionLocal() as db:
        db.add(User(
            id=user_id, name="Existing Farmer", phone="+254712345678",
            password_hash=original_hash, role=RoleEnum.farmer,
        ))
        await db.commit()
        user = await create_or_promote_admin(
            db, "0712345678", "Ignored New Name", "ignored-password", promote=True
        )
    assert user.id == user_id
    assert user.name == "Existing Farmer"
    assert user.role == RoleEnum.admin
    assert user.password_hash == original_hash


@pytest.mark.asyncio
async def test_admin_login_and_route_access_while_farmer_is_forbidden(monkeypatch):
    monkeypatch.setattr(settings, "PHONE_VERIFICATION_REQUIRED", False)  # sign-up codes are tested in test_sign_in_safety.py
    async with TestSessionLocal() as db:
        await create_or_promote_admin(db, "0712345678", "Admin", "admin-password")

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        admin_login = await client.post(
            "/auth/login", data={"username": "0712345678", "password": "admin-password"}
        )
        assert admin_login.status_code == 200, admin_login.text
        admin_headers = {"Authorization": f"Bearer {admin_login.json()['access_token']}"}
        assert (await client.get("/admin/users", headers=admin_headers)).status_code == 200

        created = await client.post("/admin/users", headers=admin_headers, json={
            "name": "Second Admin", "phone": "0103486063", "password": "second-secret",
        })
        assert created.status_code == 201, created.text
        assert created.json()["role"] == "admin"
        assert created.json()["phone"] == "+254103486063"
        second_login = await client.post(
            "/auth/login", data={"username": "0103486063", "password": "second-secret"}
        )
        assert second_login.status_code == 200, second_login.text
        duplicate = await client.post("/admin/users", headers=admin_headers, json={
            "name": "Duplicate", "phone": "0103486063", "password": "another-secret",
        })
        assert duplicate.status_code == 409

        registration = await client.post(
            "/auth/register",
            json={"name": "Farmer", "phone": "0722222222", "password": "farmer-password"},
        )
        assert registration.status_code == 200, registration.text
        farmer_login = await client.post(
            "/auth/login", data={"username": "0722222222", "password": "farmer-password"}
        )
        farmer_headers = {"Authorization": f"Bearer {farmer_login.json()['access_token']}"}
        response = await client.get("/admin/users", headers=farmer_headers)
        forbidden_create = await client.post("/admin/users", headers=farmer_headers, json={
            "name": "Nope", "phone": "0103486064", "password": "farmer-secret",
        })
    assert response.status_code == 403
    assert forbidden_create.status_code == 403


@pytest.mark.asyncio
async def test_activating_model_version_replaces_active_version_for_same_model():
    old_id, new_id = uuid.uuid4(), uuid.uuid4()
    async with TestSessionLocal() as db:
        await create_or_promote_admin(db, "0712345678", "Admin", "admin-password")
        db.add_all([
            ModelVersion(id=old_id, model_name=ModelNameEnum.triage, version="v1", metrics={}, is_active=True),
            ModelVersion(id=new_id, model_name=ModelNameEnum.triage, version="v2", metrics={}, is_active=False),
        ])
        await db.commit()

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        login = await client.post(
            "/auth/login", data={"username": "0712345678", "password": "admin-password"}
        )
        headers = {"Authorization": f"Bearer {login.json()['access_token']}"}
        response = await client.patch(f"/admin/model-versions/{new_id}", headers=headers, json={"is_active": True})
        assert response.status_code == 200, response.text
        versions = (await client.get("/admin/model-versions", headers=headers)).json()

    by_id = {version["id"]: version for version in versions}
    assert by_id[str(old_id)]["is_active"] is False
    assert by_id[str(new_id)]["is_active"] is True
