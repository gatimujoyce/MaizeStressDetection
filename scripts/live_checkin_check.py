"""Live check of the real inference through the actual check-in endpoint. Run with the BACKEND's Python (it needs
TensorFlow, FastAPI and aiosqlite) from the repo root. Uses FastAPI's TestClient with a throwaway SQLite database,
so no server, login or Postgres is needed. Not part of the test suite: it loads the real models."""
import os
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
BACKEND = REPO / "backend"
sys.path.insert(0, str(BACKEND))
os.chdir(BACKEND)  # the app writes uploads to ./uploads relative to the working directory

tmp = tempfile.mkdtemp()
os.environ.setdefault("SECRET_KEY", "live-check-only")
os.environ["DATABASE_URL"] = f"sqlite+aiosqlite:///{tmp}/live.db"
os.environ["CHECKIN_INFERENCE_MODE"] = "real"
os.environ["ML_ROOT"] = str(REPO)

import asyncio
import uuid
from datetime import datetime, timedelta, timezone

from fastapi.testclient import TestClient

from app.core.deps import get_db, require_farmer
from app.db import Base, engine
from app.main import app
import app.routers.checkins as _checkins
_checkins.send_sms = lambda *a, **k: True  # live check only: never send a real SMS
from app.models import Farm, SensorReading, User
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

session_factory = async_sessionmaker(engine, expire_on_commit=False)
user_id, farm_id = uuid.uuid4(), uuid.uuid4()


async def setup():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    async with session_factory() as s:
        s.add(User(id=user_id, name="Live", phone="+254700000001", password_hash="x"))
        s.add(Farm(id=farm_id, user_id=user_id, name="Live farm", location="Here", soil_type="loam"))
        await s.commit()


async def add_readings(kind):
    """kind: 'none' | 'heat' (a day of hot, dry-ish readings, one every 15 minutes)."""
    if kind == "none":
        return
    now = datetime.now(timezone.utc)
    async with session_factory() as s:
        for k in range(96):
            s.add(SensorReading(id=uuid.uuid4(), farm_id=farm_id, soil_moisture=24.0, temperature=38.0,
                                humidity=35.0, leaf_wetness=14.0, recorded_at=now - timedelta(minutes=15 * (96 - k))))
        await s.commit()


async def override_db():
    async with session_factory() as s:
        yield s


app.dependency_overrides[get_db] = override_db
app.dependency_overrides[require_farmer] = lambda: User(id=user_id, name="Live", phone="+254700000001", password_hash="x")
asyncio.run(setup())
client = TestClient(app)


def post(path, label):
    r = client.post(f"/farms/{farm_id}/checkins", files={"image": (path.name, path.read_bytes(), "image/jpeg")})
    if r.status_code != 200:
        print(f"{label:<28} HTTP {r.status_code}: {r.text[:160]}")
        return
    j = r.json()
    f = j["model_versions"].get("fusion", {})
    print(f"{label:<28} severity {j['severity']:<12} disease {j['disease_label']} ({j['disease_conf']:.2f}) | "
          f"nutrient {j['nutrient_label']} | triage {j['triage_result']} | sensor {j['sensor_label']} | "
          f"retake {f.get('retake')} | mode {j['model_versions'].get('inference_mode')}")


test = REPO / "data/processed/plantvillage_maize/test"
pick = {c: sorted((test / c).glob("*"))[0] for c in ("healthy", "common_rust", "northern_leaf_blight", "gray_leaf_spot")}
print("--- no sensor readings ---")
for c, p in pick.items():
    post(p, c)
print("\n--- a day of hot, dry readings (38 C, 24% VWC on loam) ---")
asyncio.run(add_readings("heat"))
for c in ("healthy", "common_rust"):
    post(pick[c], c + " + heat")

import io

from PIL import Image
buf = io.BytesIO()
Image.new("RGB", (300, 300), (128, 128, 128)).save(buf, "JPEG")
tmpimg = Path(tmp) / "flat.jpg"
tmpimg.write_bytes(buf.getvalue())
print("\n--- edge cases ---")
post(tmpimg, "flat grey photo")
bad = Path(tmp) / "bad.jpg"
bad.write_bytes(b"this is not a jpeg")
post(bad, "unreadable file")
