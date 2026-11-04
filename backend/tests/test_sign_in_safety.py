"""Sign-in safety: phone check at sign-up, lockout, forgot password, change password, and admin temporary passwords."""
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
from app.models import RoleEnum, SmsLog, User


@compiles(JSONB, "sqlite")
def _jsonb_as_json(type_, compiler, **kw):
    return "JSON"


engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
SessionLocal = async_sessionmaker(autocommit=False, autoflush=False, bind=engine, class_=AsyncSession)


async def override_get_db():
    async with SessionLocal() as session:
        yield session


@pytest_asyncio.fixture(autouse=True)
async def setup(monkeypatch):
    previous = app.dependency_overrides.copy()
    app.dependency_overrides[get_db] = override_get_db
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    texts = []

    def fake_send(phone, message):
        texts.append((phone, message))
        return True

    monkeypatch.setattr("app.services.auth_codes.send_sms", fake_send)
    monkeypatch.setattr("app.routers.admin.send_sms", fake_send)
    monkeypatch.setattr("app.core.config.settings.PHONE_VERIFICATION_REQUIRED", True)
    try:
        yield texts
    finally:
        app.dependency_overrides.clear()
        app.dependency_overrides.update(previous)
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)


def client():
    return AsyncClient(transport=ASGITransport(app=app), base_url="http://test")


def code_from(texts):
    return texts[-1][1].split("code is ")[1][:6]


def wrong_code(code):
    return "000000" if code != "000000" else "111111"


async def register(ac, texts, phone="0722000001", password="longenough1"):
    sent = await ac.post("/auth/register/code", json={"phone": phone})
    assert sent.status_code == 202, sent.text
    return await ac.post("/auth/register", json={"name": "Farmer", "phone": phone, "password": password, "code": code_from(texts)})


async def login(ac, phone, password):
    return await ac.post("/auth/login", data={"username": phone, "password": password})


async def make_admin():
    admin_id = uuid.uuid4()
    async with SessionLocal() as db:
        db.add(User(id=admin_id, name="Admin", phone="+254799000999", password_hash=get_password_hash("adminpass1"), role=RoleEnum.admin))
        await db.commit()
    return {"Authorization": f"Bearer {create_access_token(subject=str(admin_id))}"}


@pytest.mark.asyncio
async def test_register_needs_the_texted_code(setup):
    texts = setup
    async with client() as ac:
        no_code = await ac.post("/auth/register", json={"name": "F", "phone": "0722000001", "password": "longenough1"})
        assert no_code.status_code == 400
        await ac.post("/auth/register/code", json={"phone": "0722000001"})
        good = code_from(texts)
        bad = await ac.post("/auth/register", json={"name": "F", "phone": "0722000001", "password": "longenough1", "code": wrong_code(good)})
        assert bad.status_code == 400
        ok = await ac.post("/auth/register", json={"name": "F", "phone": "0722000001", "password": "longenough1", "code": good})
        assert ok.status_code == 200, ok.text
        assert ok.json()["phone"] == "+254722000001"
        again = await ac.post("/auth/register", json={"name": "F", "phone": "0722000001", "password": "longenough1", "code": good})
        assert again.status_code == 400  # a code works once, and the phone is now taken


@pytest.mark.asyncio
async def test_register_code_rules(setup):
    texts = setup
    async with client() as ac:
        await ac.post("/auth/register/code", json={"phone": "0722000002"})
        assert (await ac.post("/auth/register/code", json={"phone": "0722000002"})).status_code == 429  # asked again too soon
        good = code_from(texts)
        for _ in range(5):
            await ac.post("/auth/register", json={"name": "F", "phone": "0722000002", "password": "longenough1", "code": wrong_code(good)})
        locked = await ac.post("/auth/register", json={"name": "F", "phone": "0722000002", "password": "longenough1", "code": good})
        assert locked.status_code == 400  # five wrong tries used the code up
        short = await ac.post("/auth/register", json={"name": "F", "phone": "0722000003", "password": "short", "code": "123456"})
        assert short.status_code == 400 and "8 characters" in short.json()["detail"]
        await register(ac, texts, "0722000004")
        taken = await ac.post("/auth/register/code", json={"phone": "0722000004"})
        assert taken.status_code == 400  # already registered
    async with SessionLocal() as db:
        logs = (await db.execute(select(SmsLog))).scalars().all()
    assert logs and all("hidden" in log.message for log in logs)  # the code is never kept in the SMS log


@pytest.mark.asyncio
async def test_five_wrong_passwords_lock_the_account(setup):
    async with client() as ac:
        assert (await register(ac, setup)).status_code == 200
        for _ in range(4):
            assert (await login(ac, "0722000001", "wrongwrong")).status_code == 400
        fifth = await login(ac, "0722000001", "wrongwrong")
        assert fifth.status_code == 429 and "15 minutes" in fifth.json()["detail"]
        still = await login(ac, "0722000001", "longenough1")  # the right password is refused while locked
        assert still.status_code == 429


@pytest.mark.asyncio
async def test_a_good_sign_in_clears_the_count(setup):
    async with client() as ac:
        await register(ac, setup)
        for _ in range(4):
            await login(ac, "0722000001", "wrongwrong")
        assert (await login(ac, "0722000001", "longenough1")).status_code == 200
        for _ in range(4):
            assert (await login(ac, "0722000001", "wrongwrong")).status_code == 400
        assert (await login(ac, "0722000001", "longenough1")).status_code == 200


@pytest.mark.asyncio
async def test_forgot_password_by_sms_code(setup):
    texts = setup
    async with client() as ac:
        await register(ac, texts)
        before = len(texts)
        unknown = await ac.post("/auth/forgot-password", json={"phone": "0799999999"})
        assert unknown.status_code == 200 and len(texts) == before  # same answer, nothing sent
        known = await ac.post("/auth/forgot-password", json={"phone": "0722000001"})
        assert known.json() == unknown.json() and len(texts) == before + 1
        code = code_from(texts)
        wrong = await ac.post("/auth/reset-password", json={"phone": "0722000001", "code": wrong_code(code), "new_password": "brandnewpass"})
        assert wrong.status_code == 400
        ok = await ac.post("/auth/reset-password", json={"phone": "0722000001", "code": code, "new_password": "brandnewpass"})
        assert ok.status_code == 200
        assert (await login(ac, "0722000001", "longenough1")).status_code == 400
        assert (await login(ac, "0722000001", "brandnewpass")).status_code == 200
        reuse = await ac.post("/auth/reset-password", json={"phone": "0722000001", "code": code, "new_password": "anotherpass1"})
        assert reuse.status_code == 400  # the code worked once


@pytest.mark.asyncio
async def test_reset_code_lifts_a_lockout(setup):
    texts = setup
    async with client() as ac:
        await register(ac, texts)
        for _ in range(5):
            await login(ac, "0722000001", "wrongwrong")
        await ac.post("/auth/forgot-password", json={"phone": "0722000001"})
        await ac.post("/auth/reset-password", json={"phone": "0722000001", "code": code_from(texts), "new_password": "brandnewpass"})
        assert (await login(ac, "0722000001", "brandnewpass")).status_code == 200


@pytest.mark.asyncio
async def test_change_password_needs_the_current_one(setup):
    async with client() as ac:
        await register(ac, setup)
        headers = {"Authorization": f"Bearer {(await login(ac, '0722000001', 'longenough1')).json()['access_token']}"}
        wrong = await ac.post("/auth/change-password", headers=headers, json={"current_password": "nope", "new_password": "brandnewpass"})
        same = await ac.post("/auth/change-password", headers=headers, json={"current_password": "longenough1", "new_password": "longenough1"})
        short = await ac.post("/auth/change-password", headers=headers, json={"current_password": "longenough1", "new_password": "short"})
        assert (wrong.status_code, same.status_code, short.status_code) == (400, 400, 400)
        ok = await ac.post("/auth/change-password", headers=headers, json={"current_password": "longenough1", "new_password": "brandnewpass"})
        assert ok.status_code == 200
        assert (await login(ac, "0722000001", "brandnewpass")).status_code == 200
        # the profile update can no longer set a password
        await ac.patch("/auth/me", headers=headers, json={"name": "Renamed", "password": "sneaky-new-pass"})
        assert (await login(ac, "0722000001", "sneaky-new-pass")).status_code == 400
        assert (await login(ac, "0722000001", "brandnewpass")).status_code == 200


@pytest.mark.asyncio
async def test_admin_temporary_password_flow(setup):
    texts = setup
    async with client() as ac:
        farmer = await register(ac, texts)
        farmer_id = farmer.json()["id"]
        admin_headers = await make_admin()
        reset = await ac.post(f"/admin/users/{farmer_id}/reset-password", headers=admin_headers, json={})
        assert reset.status_code == 200, reset.text
        phone, message = texts[-1]
        temporary = message.split("\n")[1]
        assert phone == "+254722000001" and len(temporary) == 10
        assert temporary not in reset.text  # the administrator is never shown it

        assert (await login(ac, "0722000001", "longenough1")).status_code == 400  # old password stopped working
        signed_in = await login(ac, "0722000001", temporary)
        assert signed_in.status_code == 200 and signed_in.json()["must_change_password"] is True
        headers = {"Authorization": f"Bearer {signed_in.json()['access_token']}"}
        assert (await ac.get("/auth/me", headers=headers)).json()["must_change_password"] is True
        assert (await ac.patch("/auth/me", headers=headers, json={"name": "X"})).status_code == 403  # blocked until a new password is chosen
        changed = await ac.post("/auth/change-password", headers=headers, json={"current_password": temporary, "new_password": "myownchoice1"})
        assert changed.status_code == 200
        assert (await ac.patch("/auth/me", headers=headers, json={"name": "X"})).status_code == 200

        log = await ac.get("/admin/sms-log", headers=admin_headers)
        assert temporary not in log.text and "Temporary password sent (hidden)" in log.text
        audit = await ac.get("/admin/audit-log", headers=admin_headers)
        assert temporary not in audit.text and "user.password_reset" in audit.text


@pytest.mark.asyncio
async def test_failed_text_leaves_the_password_alone(setup, monkeypatch):
    async with client() as ac:
        farmer = await register(ac, setup)
        admin_headers = await make_admin()
        monkeypatch.setattr("app.routers.admin.send_sms", lambda phone, message: False)
        reset = await ac.post(f"/admin/users/{farmer.json()['id']}/reset-password", headers=admin_headers, json={})
        assert reset.status_code == 502
        assert (await login(ac, "0722000001", "longenough1")).status_code == 200


@pytest.mark.asyncio
async def test_new_admin_must_replace_the_temporary_password(setup):
    async with client() as ac:
        admin_headers = await make_admin()
        created = await ac.post("/admin/users", headers=admin_headers, json={"name": "New Admin", "phone": "0733000009", "password": "starterpass1"})
        assert created.status_code == 201 and created.json()["must_change_password"] is True
        short = await ac.post("/admin/users", headers=admin_headers, json={"name": "Weak", "phone": "0733000010", "password": "short"})
        assert short.status_code == 422
        signed_in = await login(ac, "0733000009", "starterpass1")
        assert signed_in.json()["must_change_password"] is True
        headers = {"Authorization": f"Bearer {signed_in.json()['access_token']}"}
        assert (await ac.get("/admin/users", headers=headers)).status_code == 403
        await ac.post("/auth/change-password", headers=headers, json={"current_password": "starterpass1", "new_password": "adminsownpass1"})
        assert (await ac.get("/admin/users", headers=headers)).status_code == 200
        audit = await ac.get("/admin/audit-log", headers=admin_headers)
        assert "user.create_admin" in audit.text and "starterpass1" not in audit.text
