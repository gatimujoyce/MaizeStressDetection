# ---------------------------------------------------------------------------
# SQLite compat: map Postgres-only column types to their SQLite equivalents
# Must happen before any SQLAlchemy metadata is touched.
# ---------------------------------------------------------------------------
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.dialects.postgresql import JSONB

@compiles(JSONB, "sqlite")
def _jsonb_as_json(type_, compiler, **kw):
    return "JSON"

import pytest
import pytest_asyncio
import uuid
import io
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.future import select

from app.db import Base
from app.core.deps import get_db
from app.main import app
from app.models import SensorReading

engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
TestingSessionLocal = async_sessionmaker(
    autocommit=False, autoflush=False, bind=engine, class_=AsyncSession
)

async def override_get_db():
    async with TestingSessionLocal() as session:
        yield session

app.dependency_overrides[get_db] = override_get_db

@pytest_asyncio.fixture(autouse=True)
async def setup_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

async def create_user(ac, name, phone, password="p"):
    await ac.post("/auth/register", json={"name": name, "phone": phone, "password": password})
    r = await ac.post("/auth/login", data={"username": phone, "password": password})
    return {"Authorization": f"Bearer {r.json()['access_token']}"}

@pytest.mark.asyncio
async def test_cross_user_404_nested_routes():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        headers_a = await create_user(ac, "A", "0711111111")
        headers_b = await create_user(ac, "B", "0722222222")
        
        # User A creates farm
        r = await ac.post("/farms", json={"name": "Farm A", "location": "L", "soil_type": "loam"}, headers=headers_a)
        farm_a_id = r.json()["id"]

        r = await ac.get(f"/farms/{farm_a_id}/readings", headers=headers_b)
        assert r.status_code == 404
        r = await ac.post(f"/farms/{farm_a_id}/readings", json={
            "soil_moisture": 10, "temperature": 20, "humidity": 30, "leaf_wetness": 0, "source": "simulated"
        }, headers=headers_b)
        assert r.status_code == 404
        
        r = await ac.get(f"/farms/{farm_a_id}/predictions", headers=headers_b)
        assert r.status_code == 404
        r = await ac.get(f"/farms/{farm_a_id}/alerts", headers=headers_b)
        assert r.status_code == 404

        # A creates a checkin to test feedback route 404
        files = {"image": ("test.jpg", io.BytesIO(b"abc"), "image/jpeg")}
        r = await ac.post(f"/farms/{farm_a_id}/checkins", files=files, headers=headers_a)
        pred_id = r.json()["id"]

        # B tries to feedback
        r = await ac.post(f"/predictions/{pred_id}/feedback", json={"accurate": True}, headers=headers_b)
        assert r.status_code == 404

@pytest.mark.asyncio
async def test_two_farm_isolation():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        headers = await create_user(ac, "A", "0733333333")
        r1 = await ac.post("/farms", json={"name": "F1", "location": "L", "soil_type": "loam"}, headers=headers)
        f1_id = r1.json()["id"]
        r2 = await ac.post("/farms", json={"name": "F2", "location": "L", "soil_type": "loam"}, headers=headers)
        f2_id = r2.json()["id"]

        await ac.post(f"/farms/{f1_id}/readings", json={
            "soil_moisture": 10, "temperature": 20, "humidity": 30, "leaf_wetness": 0, "source": "simulated"
        }, headers=headers)

        r = await ac.get(f"/farms/{f2_id}/readings", headers=headers)
        assert len(r.json()) == 0

@pytest.mark.asyncio
async def test_get_current_user_profile_with_valid_token():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        headers = await create_user(ac, "Profile User", "0712345678")

        response = await ac.get("/auth/me", headers=headers)

    assert response.status_code == 200
    assert response.json()["name"] == "Profile User"
    assert response.json()["phone"] == "+254712345678"
    assert response.json()["role"] == "farmer"
    assert set(response.json()) == {"id", "name", "phone", "role"}
    assert "password_hash" not in response.json()

@pytest.mark.asyncio
async def test_get_current_user_profile_without_token():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/auth/me")

    assert response.status_code == 401

@pytest.mark.asyncio
async def test_patch_user_id_ignored():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        headers = await create_user(ac, "A", "0744444444")
        r = await ac.post("/farms", json={"name": "F1", "location": "L", "soil_type": "loam"}, headers=headers)
        f1_id = r.json()["id"]
        user_id = r.json()["user_id"]
        
        r = await ac.patch(f"/farms/{f1_id}", json={"name": "F1a", "user_id": str(uuid.uuid4())}, headers=headers)
        assert r.status_code == 200
        assert r.json()["user_id"] == user_id

@pytest.mark.asyncio
async def test_soft_delete_retains_children():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        headers = await create_user(ac, "A", "0755555555")
        r = await ac.post("/farms", json={"name": "F1", "location": "L", "soil_type": "loam"}, headers=headers)
        f1_id = r.json()["id"]

        await ac.post(f"/farms/{f1_id}/readings", json={
            "soil_moisture": 10, "temperature": 20, "humidity": 30, "leaf_wetness": 0, "source": "simulated"
        }, headers=headers)

        r = await ac.delete(f"/farms/{f1_id}", headers=headers)
        assert r.status_code == 200

        r = await ac.get("/farms", headers=headers)
        assert len(r.json()) == 0

        r = await ac.get(f"/farms/{f1_id}", headers=headers)
        assert r.status_code == 404

        r = await ac.get(f"/farms/{f1_id}/readings", headers=headers)
        assert r.status_code == 404

        async with TestingSessionLocal() as session:
            res = await session.execute(select(SensorReading))
            assert len(res.scalars().all()) == 1

@pytest.mark.asyncio
async def test_duplicate_farm_names():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        h1 = await create_user(ac, "A", "0766666666")
        h2 = await create_user(ac, "B", "0777777777")
        
        r = await ac.post("/farms", json={"name": "Plot 1", "location": "L", "soil_type": "loam"}, headers=h1)
        assert r.status_code == 200
        
        r = await ac.post("/farms", json={"name": "Plot 1", "location": "L", "soil_type": "loam"}, headers=h1)
        assert r.status_code == 409

        r = await ac.post("/farms", json={"name": "Plot 1", "location": "L", "soil_type": "loam"}, headers=h2)
        assert r.status_code == 200

@pytest.mark.asyncio
async def test_farm_isolation_integration():
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:

        # --- 1. Register user A with local format 0712345678 ---
        resp = await ac.post("/auth/register", json={
            "name": "User A",
            "phone": "0712345678",
            "password": "secretA",
        })
        assert resp.status_code == 200, resp.json()
        assert resp.json()["phone"] == "+254712345678"  # stored normalised

        # --- 2. Register user B with 0112345678 ---
        resp = await ac.post("/auth/register", json={
            "name": "User B",
            "phone": "0112345678",
            "password": "secretB",
        })
        assert resp.status_code == 200, resp.json()
        assert resp.json()["phone"] == "+254112345678"

        # --- 3. Login as A using +254712345678 (E.164) must succeed ---
        resp = await ac.post("/auth/login", data={
            "username": "+254712345678",
            "password": "secretA",
        })
        assert resp.status_code == 200, resp.json()
        token_a = resp.json()["access_token"]

        # --- 4. Register a THIRD user with +254712345678 must be rejected ---
        resp = await ac.post("/auth/register", json={
            "name": "Duplicate A",
            "phone": "+254712345678",
            "password": "x",
        })
        assert resp.status_code == 400, resp.json()

        # --- 5. Login as B ---
        resp = await ac.post("/auth/login", data={
            "username": "0112345678",
            "password": "secretB",
        })
        assert resp.status_code == 200, resp.json()
        token_b = resp.json()["access_token"]

        headers_a = {"Authorization": f"Bearer {token_a}"}
        headers_b = {"Authorization": f"Bearer {token_b}"}

        # --- 6. A creates a farm ---
        resp = await ac.post("/farms", json={
            "name": "A Farm",
            "location": "Nairobi",
            "soil_type": "loam",
        }, headers=headers_a)
        assert resp.status_code == 200, resp.json()
        farm_id = resp.json()["id"]

        # --- 7. B gets 404 on GET of A's farm ---
        resp = await ac.get(f"/farms/{farm_id}", headers=headers_b)
        assert resp.status_code == 404, resp.json()

        # --- 8. GET /farms returns [] for B ---
        resp = await ac.get("/farms", headers=headers_b)
        assert resp.status_code == 200, resp.json()
        assert resp.json() == []

        # --- 9. GET /farms returns exactly A's farm for A ---
        resp = await ac.get("/farms", headers=headers_a)
        assert resp.status_code == 200, resp.json()
        farms_a = resp.json()
        assert len(farms_a) == 1
        assert farms_a[0]["id"] == farm_id

        # --- 10. A can GET their own farm ---
        resp = await ac.get(f"/farms/{farm_id}", headers=headers_a)
        assert resp.status_code == 200, resp.json()
        assert resp.json()["id"] == farm_id

        # --- 11. B gets 404 on DELETE of A's farm ---
        resp = await ac.delete(f"/farms/{farm_id}", headers=headers_b)
        assert resp.status_code == 404, resp.json()

        # --- 12. A can DELETE their own farm ---
        resp = await ac.delete(f"/farms/{farm_id}", headers=headers_a)
        assert resp.status_code == 200, resp.json()

        # --- 13. Farm is gone; 404 for A too now ---
        resp = await ac.get(f"/farms/{farm_id}", headers=headers_a)
        assert resp.status_code == 404, resp.json()

# ---------------------------------------------------------------------------
# Admin: GET /admin/farms include_deleted behaviour
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_admin_farms_include_deleted():
    from datetime import datetime, timezone
    from app.models import User, Farm, RoleEnum, SoilTypeEnum
    from app.core.security import get_password_hash, create_access_token

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # Register a regular farmer and create a farm
        farmer_headers = await create_user(ac, "Farmer", "0799000001")
        r = await ac.post(
            "/farms",
            json={"name": "ToDelete", "location": "Loc", "soil_type": "loam"},
            headers=farmer_headers,
        )
        assert r.status_code == 200, r.json()
        farm_id = r.json()["id"]

        # Soft-delete the farm via the normal DELETE endpoint
        r = await ac.delete(f"/farms/{farm_id}", headers=farmer_headers)
        assert r.status_code == 200, r.json()

        # Also create one active farm so we can distinguish the two
        r = await ac.post(
            "/farms",
            json={"name": "Active", "location": "Loc", "soil_type": "loam"},
            headers=farmer_headers,
        )
        assert r.status_code == 200, r.json()
        active_farm_id = r.json()["id"]

        # Insert an admin user directly into the DB (registration endpoint blocks admin creation)
        admin_id = uuid.uuid4()
        async with TestingSessionLocal() as session:
            admin_user = User(
                id=admin_id,
                name="Admin",
                phone="+254799000999",
                password_hash=get_password_hash("adminpass"),
                role=RoleEnum.admin,
            )
            session.add(admin_user)
            await session.commit()

        admin_token = create_access_token(subject=str(admin_id))
        admin_headers = {"Authorization": f"Bearer {admin_token}"}

        # Default call (include_deleted=False) must exclude the soft-deleted farm
        r = await ac.get("/admin/farms", headers=admin_headers)
        assert r.status_code == 200, r.json()
        ids = [f["id"] for f in r.json()]
        assert farm_id not in ids, "Soft-deleted farm must be excluded by default"
        assert active_farm_id in ids, "Active farm must appear"

        # include_deleted=true must return the soft-deleted farm too
        r = await ac.get("/admin/farms?include_deleted=true", headers=admin_headers)
        assert r.status_code == 200, r.json()
        ids_all = [f["id"] for f in r.json()]
        assert farm_id in ids_all, "Soft-deleted farm must be included when include_deleted=true"
        assert active_farm_id in ids_all, "Active farm must still appear"

        # The soft-deleted farm entry must expose a non-null deleted_at
        deleted_entry = next(f for f in r.json() if f["id"] == farm_id)
        assert deleted_entry["deleted_at"] is not None, "deleted_at must be non-null for the deleted farm"
