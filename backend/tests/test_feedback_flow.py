"""Feedback questionnaire, the alert moving to read, the one-week follow-up, and the admin summary."""
import uuid
from datetime import datetime, timedelta, timezone

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import settings
from app.core.deps import get_db
from app.core.security import create_access_token, get_password_hash
from app.db import Base
from app.main import app
from app.models import Alert, ChannelEnum, Checkin, Farm, Feedback, Prediction, RoleEnum, SoilTypeEnum, User


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


async def seed(phone="+254722000001", severity="High", role=RoleEnum.farmer):
    """A farmer with one farm, one photo check-in, one result and its alert."""
    ids = {k: uuid.uuid4() for k in ("user", "farm", "checkin", "prediction", "alert")}
    now = datetime.now(timezone.utc)
    async with SessionLocal() as db:
        db.add(User(id=ids["user"], name="Joy", phone=phone, password_hash=get_password_hash("longenough1"), role=role))
        db.add(Farm(id=ids["farm"], user_id=ids["user"], name="North", location="Nakuru", soil_type=SoilTypeEnum.loam))
        db.add(Checkin(id=ids["checkin"], farm_id=ids["farm"], image_path="x.jpg", created_at=now))
        db.add(Prediction(id=ids["prediction"], checkin_id=ids["checkin"], triage_result="leaf", disease_label="northern_leaf_blight",
                          severity=severity, recommendation="Spray.", model_versions={}, created_at=now))
        db.add(Alert(id=ids["alert"], prediction_id=ids["prediction"], farm_id=ids["farm"], severity=severity,
                     channel=ChannelEnum.app, status="pending", created_at=now))
        await db.commit()
    return ids


async def make_admin():
    admin_id = uuid.uuid4()
    async with SessionLocal() as db:
        db.add(User(id=admin_id, name="Admin", phone="+254799000999", password_hash=get_password_hash("x" * 8), role=RoleEnum.admin))
        await db.commit()
    return headers_for(admin_id)


@pytest.mark.asyncio
async def test_questionnaire_saves_answers_and_marks_the_alert_read():
    ids = await seed()
    async with client() as ac:
        headers = headers_for(ids["user"])
        r = await ac.post(f"/predictions/{ids['prediction']}/feedback", headers=headers, json={
            "matched": "no", "action_taken": "other", "correct_label": "common_rust", "comment": "Looked like rust"})
        assert r.status_code == 200, r.text
        body = r.json()
        assert body["accurate"] is False and body["matched"] == "no" and body["action_taken"] == "other"
        assert body["correct_label"] == "common_rust"
        alerts = await ac.get(f"/farms/{ids['farm']}/alerts", headers=headers)
        assert alerts.json()[0]["status"] == "acknowledged"
    # answering again replaces the answers instead of adding a second row
        again = await ac.post(f"/predictions/{ids['prediction']}/feedback", headers=headers, json={"matched": "yes", "action_taken": "followed"})
        assert again.json()["accurate"] is True and again.json()["id"] == body["id"]
    async with SessionLocal() as db:
        assert len((await db.execute(select(Feedback))).scalars().all()) == 1


@pytest.mark.asyncio
async def test_answers_are_checked():
    ids = await seed()
    async with client() as ac:
        headers = headers_for(ids["user"])
        url = f"/predictions/{ids['prediction']}/feedback"
        assert (await ac.post(url, headers=headers, json={"matched": "maybe"})).status_code == 422
        assert (await ac.post(url, headers=headers, json={})).status_code == 422
        assert (await ac.post(url, headers=headers, json={"matched": "yes", "comment": "x" * 501})).status_code == 422
        assert (await ac.post(url, headers=headers, json={"accurate": True})).status_code == 200   # older callers still work


@pytest.mark.asyncio
async def test_other_farmers_cannot_answer_for_you():
    ids = await seed()
    other = await seed(phone="+254733000002")
    async with client() as ac:
        r = await ac.post(f"/predictions/{ids['prediction']}/feedback", headers=headers_for(other["user"]), json={"matched": "yes"})
        assert r.status_code == 404
        r = await ac.post(f"/predictions/{ids['prediction']}/follow-up", headers=headers_for(other["user"]), json={"outcome": "better"})
        assert r.status_code == 404
        r = await ac.get(f"/farms/{ids['farm']}/follow-ups", headers=headers_for(other["user"]))
        assert r.status_code == 404


@pytest.mark.asyncio
async def test_follow_up_appears_after_a_week_and_goes_once_answered(monkeypatch):
    ids = await seed()
    async with client() as ac:
        headers = headers_for(ids["user"])
        assert (await ac.post(f"/predictions/{ids['prediction']}/follow-up", headers=headers, json={"outcome": "better"})).status_code == 404  # no first answers yet
        await ac.post(f"/predictions/{ids['prediction']}/feedback", headers=headers, json={"matched": "yes", "action_taken": "followed"})
        assert (await ac.get(f"/farms/{ids['farm']}/follow-ups", headers=headers)).json() == []      # too soon
        async with SessionLocal() as db:
            row = (await db.execute(select(Feedback))).scalar_one()
            row.created_at = datetime.now(timezone.utc) - timedelta(days=8)
            await db.commit()
        due = (await ac.get(f"/farms/{ids['farm']}/follow-ups", headers=headers)).json()
        assert len(due) == 1 and due[0]["prediction_id"] == str(ids["prediction"]) and due[0]["label"] == "northern_leaf_blight"
        assert (await ac.post(f"/predictions/{ids['prediction']}/follow-up", headers=headers, json={"outcome": "sideways"})).status_code == 422
        done = await ac.post(f"/predictions/{ids['prediction']}/follow-up", headers=headers, json={"outcome": "better"})
        assert done.status_code == 200 and done.json()["follow_up_outcome"] == "better"
        assert (await ac.get(f"/farms/{ids['farm']}/follow-ups", headers=headers)).json() == []
        # changing the questionnaire answers keeps the follow-up answer
        again = await ac.post(f"/predictions/{ids['prediction']}/feedback", headers=headers, json={"matched": "partly", "action_taken": "followed"})
        assert again.json()["follow_up_outcome"] == "better"


@pytest.mark.asyncio
async def test_follow_up_days_setting_and_old_results(monkeypatch):
    ids = await seed()
    async with client() as ac:
        headers = headers_for(ids["user"])
        await ac.post(f"/predictions/{ids['prediction']}/feedback", headers=headers, json={"matched": "yes", "action_taken": "none"})
        monkeypatch.setattr(settings, "FOLLOW_UP_DAYS", 0)
        assert len((await ac.get(f"/farms/{ids['farm']}/follow-ups", headers=headers)).json()) == 1   # for trying it out
        monkeypatch.setattr(settings, "FOLLOW_UP_DAYS", 7)
        async with SessionLocal() as db:
            row = (await db.execute(select(Feedback))).scalar_one()
            row.created_at = datetime.now(timezone.utc) - timedelta(days=60)
            await db.commit()
        assert (await ac.get(f"/farms/{ids['farm']}/follow-ups", headers=headers)).json() == []        # too old to ask about


@pytest.mark.asyncio
async def test_no_follow_up_for_results_without_advice(monkeypatch):
    ids = await seed(severity="Low")
    monkeypatch.setattr(settings, "FOLLOW_UP_DAYS", 0)
    async with client() as ac:
        headers = headers_for(ids["user"])
        await ac.post(f"/predictions/{ids['prediction']}/feedback", headers=headers, json={"matched": "yes", "action_taken": "none"})
        assert (await ac.get(f"/farms/{ids['farm']}/follow-ups", headers=headers)).json() == []


@pytest.mark.asyncio
async def test_admin_sees_the_new_answers_once_per_result():
    ids = await seed()
    admin_headers = await make_admin()
    async with client() as ac:
        headers = headers_for(ids["user"])
        await ac.post(f"/predictions/{ids['prediction']}/feedback", headers=headers, json={"matched": "no", "action_taken": "none"})
        await ac.post(f"/predictions/{ids['prediction']}/feedback", headers=headers, json={"matched": "partly", "action_taken": "followed", "correct_label": "gray_leaf_spot"})
        await ac.post(f"/predictions/{ids['prediction']}/follow-up", headers=headers, json={"outcome": "worse"})
        rows = (await ac.get("/admin/feedback", headers=admin_headers)).json()
        assert len(rows) == 1
        row = rows[0]
        assert (row["matched"], row["action_taken"], row["follow_up_outcome"], row["correct_label"]) == ("partly", "followed", "worse", "gray_leaf_spot")
        assert row["farmer_name"] == "Joy" and row["farm_name"] == "North"
