"""The SMS log keeps why a message failed and learns from the delivery report whether it arrived."""
import io
import json
import urllib.error
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
from app.models import RoleEnum, SmsLog, User
from app.services import sms
from app.services.sms_log import record_sms


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


class FakeResponse(io.BytesIO):
    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False


def reply(recipient):
    return FakeResponse(json.dumps({"SMSMessageData": {"Recipients": [recipient]}}).encode())


def test_an_accepted_message_is_true_and_keeps_the_provider_id(monkeypatch):
    monkeypatch.setattr(sms.urllib.request, "urlopen",
                        lambda *a, **k: reply({"status": "Success", "statusCode": 101, "messageId": "ATXid_1"}))
    result = sms.send_sms("+254700000001", "hi")
    assert result and result.message_id == "ATXid_1" and result.reason is None


def test_a_refused_message_is_false_with_a_plain_reason(monkeypatch):
    monkeypatch.setattr(sms.urllib.request, "urlopen", lambda *a, **k: reply({"status": "InvalidPhoneNumber", "statusCode": 403}))
    result = sms.send_sms("+254700000001", "hi")
    assert not result and "InvalidPhoneNumber" in result.reason

    def refuse(*a, **k):
        raise urllib.error.HTTPError("http://x", 401, "Unauthorized", {}, None)
    monkeypatch.setattr(sms.urllib.request, "urlopen", refuse)
    result = sms.send_sms("+254700000001", "hi")
    assert not result and "API key" in result.reason and "401" in result.reason

    def offline(*a, **k):
        raise urllib.error.URLError("no route")
    monkeypatch.setattr(sms.urllib.request, "urlopen", offline)
    assert sms.send_sms("+254700000001", "hi").reason == "Could not reach the SMS service"


async def logged(message_id="ATXid_9", status="sent"):
    async with SessionLocal() as db:
        record_sms(db, user_id=None, farm_id=None, alert_id=None, kind="sensor_alert", phone="+254700000001", message="m",
                   status=status, result=sms.SmsResult(status == "sent", None if status == "sent" else "Could not reach the SMS service", message_id))
        await db.commit()


async def the_row():
    async with SessionLocal() as db:
        return (await db.execute(select(SmsLog))).scalar_one()


@pytest.mark.asyncio
async def test_the_log_keeps_the_id_and_the_failure_reason():
    await logged("ATXid_9", "sent")
    row = await the_row()
    assert row.provider_message_id == "ATXid_9" and row.failure_reason is None
    async with SessionLocal() as db:
        await db.delete(row)
        await db.commit()
    await logged(None, "failed")
    row = await the_row()
    assert row.failure_reason == "Could not reach the SMS service" and row.delivery_status is None


@pytest.mark.asyncio
async def test_a_delivery_report_updates_the_matching_message(monkeypatch):
    monkeypatch.setenv("SMS_DLR_TOKEN", "secret-token")
    await logged("ATXid_9")
    async with client() as c:
        wrong = await c.post("/sms/delivery-report?token=nope", data={"id": "ATXid_9", "status": "Success"})
        ok = await c.post("/sms/delivery-report?token=secret-token", data={"id": "ATXid_9", "status": "Success"})
        unknown = await c.post("/sms/delivery-report?token=secret-token", data={"id": "other", "status": "Failed"})
    assert wrong.status_code == 403 and ok.status_code == 200 and unknown.status_code == 200
    row = await the_row()
    assert row.delivery_status == "delivered" and row.delivery_reported_at is not None

    async with client() as c:
        await c.post("/sms/delivery-report?token=secret-token",
                     data={"id": "ATXid_9", "status": "Failed", "failureReason": "UserInBlacklist"})
    row = await the_row()
    assert row.delivery_status == "failed" and row.failure_reason == "UserInBlacklist"


@pytest.mark.asyncio
async def test_delivery_reports_are_off_without_a_token(monkeypatch):
    monkeypatch.delenv("SMS_DLR_TOKEN", raising=False)
    async with client() as c:
        res = await c.post("/sms/delivery-report?token=", data={"id": "x", "status": "Success"})
    assert res.status_code == 503


@pytest.mark.asyncio
async def test_the_admin_log_shows_the_new_fields():
    admin_id = uuid.uuid4()
    async with SessionLocal() as db:
        db.add(User(id=admin_id, name="Admin", phone="+254722000009", password_hash=get_password_hash("longenough1"), role=RoleEnum.admin))
        await db.commit()
    await logged(None, "failed")
    headers = {"Authorization": f"Bearer {create_access_token(subject=str(admin_id))}"}
    async with client() as c:
        res = await c.get("/admin/sms-log", headers=headers)
    entry = res.json()[0]
    assert entry["failure_reason"] == "Could not reach the SMS service" and entry["delivery_status"] is None
