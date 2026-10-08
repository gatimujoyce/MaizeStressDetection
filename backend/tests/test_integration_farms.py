# ---------------------------------------------------------------------------
# SQLite compat: map Postgres-only column types to their SQLite equivalents
# Must happen before any SQLAlchemy metadata is touched.
# ---------------------------------------------------------------------------
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.dialects.postgresql import JSONB

@compiles(JSONB, "sqlite")
def _jsonb_as_json(type_, compiler, **kw):
    return "JSON"

# ---------------------------------------------------------------------------
# Now safe to import app code that references JSONB-typed models
# ---------------------------------------------------------------------------
import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

from app.db import Base
from app.core.deps import get_db
from app.main import app
from app.core.security import get_password_hash

# ---------------------------------------------------------------------------
# Test database (SQLite in-memory, async via aiosqlite)
# ---------------------------------------------------------------------------
engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
TestingSessionLocal = async_sessionmaker(
    autocommit=False, autoflush=False, bind=engine, class_=AsyncSession
)

async def override_get_db():
    async with TestingSessionLocal() as session:
        yield session

app.dependency_overrides[get_db] = override_get_db

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------
@pytest_asyncio.fixture(autouse=True)
async def setup_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

# ---------------------------------------------------------------------------
# Integration test
# ---------------------------------------------------------------------------
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
