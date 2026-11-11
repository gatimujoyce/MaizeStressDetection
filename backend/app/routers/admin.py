from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import desc
from sqlalchemy.exc import IntegrityError
from sqlalchemy.future import select
import asyncio
from typing import List, Optional
from datetime import datetime, timezone
import uuid

from app.core.deps import get_db, require_admin
from app.models import User, Farm, Feedback, ModelVersion, RetrainingJob, Alert, Prediction, Checkin, SmsLog, AdminAuditLog
from app.schemas.auth import UserResponse
from app.schemas.farms import FarmCreate, FarmResponse
from app.schemas.predictions import FeedbackResponse
from app.schemas.admin import ModelVersionResponse, ModelVersionUpdate, RetrainingJobResponse, RetrainRequest
from app.schemas.admin import AdminUserCreate, AdminFarmResponse, AdminFeedbackResponse, SmsLogEntry
from app.schemas.admin import AdminUserUpdate, AdminFarmUpdate, AuditLogEntry, SensorInstalled, SensorRequestEntry
from app.core.security import get_password_hash
from app.core.utils import normalize_ke_phone
from app.services.audit import record_admin_action
from app.services.auth_codes import make_temp_password
from app.services.sms import send_sms
from app.services.sms_log import record_sms

router = APIRouter(prefix="/admin", tags=["admin"])

@router.get("/users", response_model=List[UserResponse])
async def admin_users(current_admin: User = Depends(require_admin), db: AsyncSession = Depends(get_db)):
    res = await db.execute(select(User))
    return res.scalars().all()

@router.post("/users", response_model=UserResponse, status_code=201)
async def create_admin_user(
    user_in: AdminUserCreate,
    current_admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    phone = normalize_ke_phone(user_in.phone)
    existing = await db.execute(select(User).where(User.phone == phone))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Phone already registered")
    user = User(
        id=uuid.uuid4(),
        name=user_in.name,
        phone=phone,
        password_hash=get_password_hash(user_in.password),
        role="admin",
        must_change_password=True,  # the new administrator replaces this temporary password at first sign-in
    )
    db.add(user)
    record_admin_action(db, current_admin, "user.create_admin", "user", user.id, f"{user.name} ({user.phone})")
    await db.commit()
    await db.refresh(user)
    return user

@router.get("/farms", response_model=List[AdminFarmResponse])
async def admin_farms(
    include_deleted: bool = False,
    current_admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    query = select(Farm, User).join(User, User.id == Farm.user_id)
    if not include_deleted:
        query = query.where(Farm.deleted_at.is_(None))
    res = await db.execute(query.order_by(Farm.name))
    return [
        AdminFarmResponse(**FarmResponse.model_validate(farm).model_dump(), owner_name=owner.name, owner_phone=owner.phone)
        for farm, owner in res.all()
    ]

@router.get("/feedback", response_model=List[AdminFeedbackResponse])
async def admin_feedback(current_admin: User = Depends(require_admin), db: AsyncSession = Depends(get_db)):
    res = await db.execute(
        select(Feedback, Prediction, Farm, User)
        .join(Prediction, Prediction.id == Feedback.prediction_id)
        .join(Checkin, Checkin.id == Prediction.checkin_id)
        .join(Farm, Farm.id == Checkin.farm_id)
        .join(User, User.id == Farm.user_id)
        .order_by(desc(Feedback.created_at))
    )
    # One row per result: the farmer's latest answers.
    seen = set()
    rows = [row for row in res.all() if not (row[0].prediction_id in seen or seen.add(row[0].prediction_id))]
    return [
        AdminFeedbackResponse(
            **FeedbackResponse.model_validate(feedback).model_dump(),
            farm_id=farm.id, farm_name=farm.name, farmer_name=owner.name, farmer_phone=owner.phone,
            disease_label=prediction.disease_label, severity=prediction.severity,
        )
        for feedback, prediction, farm, owner in rows
    ]

@router.get("/model-versions", response_model=List[ModelVersionResponse])
async def get_model_versions(current_admin: User = Depends(require_admin), db: AsyncSession = Depends(get_db)):
    res = await db.execute(select(ModelVersion))
    return res.scalars().all()

@router.patch("/model-versions/{id}", response_model=ModelVersionResponse)
async def update_model_version(id: uuid.UUID, update_data: ModelVersionUpdate, current_admin: User = Depends(require_admin), db: AsyncSession = Depends(get_db)):
    res = await db.execute(select(ModelVersion).where(ModelVersion.id == id))
    mv = res.scalar_one_or_none()
    if not mv: raise HTTPException(404, "Not found")
    if update_data.is_active:
        active_versions = await db.execute(
            select(ModelVersion).where(
                ModelVersion.model_name == mv.model_name,
                ModelVersion.is_active.is_(True),
                ModelVersion.id != mv.id,
            )
        )
        for active_version in active_versions.scalars():
            active_version.is_active = False
    mv.is_active = update_data.is_active
    await db.commit()
    await db.refresh(mv)
    return mv

@router.get("/retraining-jobs", response_model=List[RetrainingJobResponse])
async def get_retraining_jobs(current_admin: User = Depends(require_admin), db: AsyncSession = Depends(get_db)):
    res = await db.execute(select(RetrainingJob))
    return res.scalars().all()

@router.post("/retrain")
async def trigger_retrain(req: RetrainRequest, current_admin: User = Depends(require_admin)):
    return {"status": "started", "job_id": str(uuid.uuid4()), "model_name": req.model_name}

@router.get("/sms-log", response_model=List[SmsLogEntry])
async def get_sms_log(
    limit: int = Query(500, ge=1, le=2000),
    current_admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Every text message we tried to send, newest first, with the farmer and farm names."""
    res = await db.execute(
        select(SmsLog, Farm.name, User.name)
        .outerjoin(Farm, Farm.id == SmsLog.farm_id)
        .outerjoin(User, User.id == SmsLog.user_id)
        .order_by(desc(SmsLog.created_at))
        .limit(limit)
    )
    return [
        SmsLogEntry(
            id=sms.id, created_at=sms.created_at, status=sms.status, kind=sms.kind, severity=sms.severity,
            message=sms.message, phone=sms.phone, farm_id=sms.farm_id, farm_name=farm_name,
            farmer_id=sms.user_id, farmer_name=farmer_name,
        )
        for sms, farm_name, farmer_name in res.all()
    ]


# ── Managing farmers and farms (every change is written to the admin action log) ──────────────────────────────────────

def _text(value):
    value = getattr(value, "value", value)
    return None if value is None else str(value)


def _diff(obj, data):
    """{field: [old, new]} (as text) for the fields in data that really change."""
    changes = {}
    for key, new in data.items():
        old = _text(getattr(obj, key))
        if old != _text(new):
            changes[key] = [old, _text(new)]
    return changes


def _admin_farm(farm, owner_name, owner_phone):
    return AdminFarmResponse(**FarmResponse.model_validate(farm).model_dump(), owner_name=owner_name, owner_phone=owner_phone)


async def _close_nutrient_alerts(db, farm_id):
    """Close a farm's open low-nutrient alerts. Used when its NPK sensor is turned off: nothing would close them later."""
    from app.services.nutrient_rules import NUTRIENT_STRESSES
    res = await db.execute(select(Alert).where(
        Alert.farm_id == farm_id, Alert.source == "sensor",
        Alert.stress_class.in_(sorted(NUTRIENT_STRESSES)), Alert.resolved_at.is_(None)))
    for alert in res.scalars().all():
        alert.resolved_at = datetime.now(timezone.utc)


async def _load_farmer(db, user_id):
    user = await db.get(User, user_id)
    if user is None or getattr(user.role, "value", user.role) != "farmer":
        raise HTTPException(status_code=404, detail="Farmer not found")
    return user


async def _load_farm(db, farm_id):
    res = await db.execute(select(Farm, User).join(User, User.id == Farm.user_id).where(Farm.id == farm_id))
    row = res.first()
    if row is None:
        raise HTTPException(status_code=404, detail="Farm not found")
    return row


@router.patch("/users/{user_id}", response_model=UserResponse)
async def admin_update_user(
    user_id: uuid.UUID,
    data_in: AdminUserUpdate,
    current_admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    user = await _load_farmer(db, user_id)
    data = data_in.model_dump(exclude_unset=True)
    if "name" in data:
        data["name"] = (data["name"] or "").strip()
        if not data["name"]:
            raise HTTPException(status_code=422, detail="Name cannot be empty")
    if "phone" in data:
        data["phone"] = normalize_ke_phone(data["phone"] or "")
        clash = await db.execute(select(User).where(User.phone == data["phone"], User.id != user.id))
        if clash.scalar_one_or_none():
            raise HTTPException(status_code=409, detail="That phone number belongs to another account")
    changes = _diff(user, data)
    if changes:
        label = f"{user.name} ({user.phone})"
        for key, value in data.items():
            setattr(user, key, value)
        record_admin_action(db, current_admin, "user.update", "user", user.id, label, changes)
        await db.commit()
        await db.refresh(user)
    return user


@router.post("/users/{user_id}/reset-password")
async def admin_reset_password(
    user_id: uuid.UUID,
    current_admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Text the farmer a random temporary password. The administrator never sees it, and the farmer must replace it
    the first time they sign in. The SMS log and the activity log do not keep the password."""
    user = await _load_farmer(db, user_id)
    farmer_id, name, phone = user.id, user.name, user.phone
    temporary = make_temp_password()
    sent = await asyncio.to_thread(
        send_sms, phone, f"MaizeStressMonitor: your temporary password is\n{temporary}\nSign in with it, then choose your own password.")
    record_sms(db, user_id=farmer_id, farm_id=None, alert_id=None, kind="password_reset", phone=phone,
               message="Temporary password sent (hidden)", status="sent" if sent else "failed")
    if not sent:
        await db.commit()  # keep the failed attempt in the SMS log; the old password still works
        raise HTTPException(status_code=502, detail="The text message could not be sent, so the password was not changed.")
    user.password_hash = get_password_hash(temporary)
    user.must_change_password = True
    user.failed_login_count = 0
    user.locked_until = None
    record_admin_action(db, current_admin, "user.password_reset", "user", farmer_id, f"{name} ({phone})")
    await db.commit()
    return {"status": "sent"}


@router.post("/users/{user_id}/farms", response_model=AdminFarmResponse, status_code=201)
async def admin_create_farm(
    user_id: uuid.UUID,
    farm_in: FarmCreate,
    current_admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    owner = await _load_farmer(db, user_id)
    owner_name, owner_phone = owner.name, owner.phone
    farm = Farm(id=uuid.uuid4(), user_id=owner.id, **farm_in.model_dump())
    db.add(farm)
    shown = {key: _text(getattr(farm, key)) for key in ("name", "location", "soil_type", "has_npk_sensor")}
    record_admin_action(db, current_admin, "farm.create", "farm", farm.id, f"{farm.name} ({owner_name})",
                        {key: [None, value] for key, value in shown.items()})
    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise HTTPException(status_code=409, detail="This farmer already has a farm with that name")
    await db.refresh(farm)
    return _admin_farm(farm, owner_name, owner_phone)


@router.patch("/farms/{farm_id}", response_model=AdminFarmResponse)
async def admin_update_farm(
    farm_id: uuid.UUID,
    farm_in: AdminFarmUpdate,
    current_admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    farm, owner = await _load_farm(db, farm_id)
    owner_name, owner_phone = owner.name, owner.phone
    data = farm_in.model_dump(exclude_unset=True)
    for required in ("name", "location", "soil_type", "has_npk_sensor"):
        if required in data and data[required] is None:
            data.pop(required)                       # these cannot be empty: ignore an explicit null
    changes = _diff(farm, data)
    if changes:
        label = f"{farm.name} ({owner_name})"
        if data.get("has_npk_sensor") is False and farm.has_npk_sensor:
            await _close_nutrient_alerts(db, farm.id)
        for key, value in data.items():
            setattr(farm, key, value)
        record_admin_action(db, current_admin, "farm.update", "farm", farm.id, label, changes)
        try:
            await db.commit()
        except IntegrityError:
            await db.rollback()
            raise HTTPException(status_code=409, detail="This farmer already has a farm with that name")
        await db.refresh(farm)
    return _admin_farm(farm, owner_name, owner_phone)


async def _set_archived(db, current_admin, farm_id, archived):
    farm, owner = await _load_farm(db, farm_id)
    owner_name, owner_phone = owner.name, owner.phone
    if archived == (farm.deleted_at is not None):
        return _admin_farm(farm, owner_name, owner_phone)        # already in that state
    label = f"{farm.name} ({owner_name})"
    farm.deleted_at = datetime.now(timezone.utc) if archived else None
    record_admin_action(db, current_admin, "farm.archive" if archived else "farm.restore", "farm", farm.id, label)
    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise HTTPException(status_code=409, detail="This farmer already has an active farm with that name")
    await db.refresh(farm)
    return _admin_farm(farm, owner_name, owner_phone)


@router.post("/farms/{farm_id}/archive", response_model=AdminFarmResponse)
async def admin_archive_farm(farm_id: uuid.UUID, current_admin: User = Depends(require_admin), db: AsyncSession = Depends(get_db)):
    return await _set_archived(db, current_admin, farm_id, True)


@router.post("/farms/{farm_id}/restore", response_model=AdminFarmResponse)
async def admin_restore_farm(farm_id: uuid.UUID, current_admin: User = Depends(require_admin), db: AsyncSession = Depends(get_db)):
    return await _set_archived(db, current_admin, farm_id, False)


@router.get("/audit-log", response_model=List[AuditLogEntry])
async def get_audit_log(
    limit: int = Query(500, ge=1, le=2000),
    current_admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    res = await db.execute(select(AdminAuditLog).order_by(desc(AdminAuditLog.created_at)).limit(limit))
    return res.scalars().all()


# ── Sensor setup requests: farmers ask, an administrator visits, then marks the plot installed ─────────────────────────

@router.get("/sensor-requests", response_model=List[SensorRequestEntry])
async def admin_sensor_requests(current_admin: User = Depends(require_admin), db: AsyncSession = Depends(get_db)):
    """Plots waiting for a sensor visit, oldest request first, with what the installer needs to know."""
    res = await db.execute(
        select(Farm, User).join(User, User.id == Farm.user_id)
        .where(Farm.sensor_requested_at.is_not(None), Farm.sensor_status.in_(("requested", "in_progress", "installed")),
               Farm.deleted_at.is_(None))
        .order_by(Farm.sensor_requested_at))
    return [
        SensorRequestEntry(
            farm_id=farm.id, farm_name=farm.name, location=farm.location, soil_type=_text(farm.soil_type),
            size_acres=farm.size_acres, planting_date=farm.planting_date, water_source=farm.water_source,
            seed_variety=farm.seed_variety, latitude=farm.latitude, longitude=farm.longitude,
            has_npk_sensor=farm.has_npk_sensor, status=farm.sensor_status, requested_at=farm.sensor_requested_at,
            contacted_at=farm.sensor_contacted_at, installed_at=farm.sensor_installed_at, note=farm.sensor_request_note,
            farmer_id=owner.id, farmer_name=owner.name, farmer_phone=owner.phone)
        for farm, owner in res.all()
    ]


@router.post("/farms/{farm_id}/sensor-installed", response_model=AdminFarmResponse)
async def admin_sensor_installed(
    farm_id: uuid.UUID,
    body: Optional[SensorInstalled] = None,
    current_admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Installation is done: the plot leaves the request list. The admin can say here whether it also has an NPK sensor."""
    farm, owner = await _load_farm(db, farm_id)
    owner_name, owner_phone = owner.name, owner.phone
    label = f"{farm.name} ({owner_name})"
    changes = {}
    if farm.sensor_status != "installed":
        changes["sensor_status"] = [farm.sensor_status, "installed"]
        farm.sensor_status = "installed"
        farm.sensor_installed_at = datetime.now(timezone.utc)
    npk = body.has_npk_sensor if body else None
    if npk is not None and npk != farm.has_npk_sensor:
        changes["has_npk_sensor"] = [_text(farm.has_npk_sensor), _text(npk)]
        if not npk:
            await _close_nutrient_alerts(db, farm.id)
        farm.has_npk_sensor = npk
    if changes:
        record_admin_action(db, current_admin, "farm.sensor_installed", "farm", farm.id, label, changes)
        await db.commit()
        await db.refresh(farm)
    return _admin_farm(farm, owner_name, owner_phone)


@router.post("/farms/{farm_id}/sensor-request/cancel", response_model=AdminFarmResponse)
async def admin_cancel_sensor_request(
    farm_id: uuid.UUID,
    current_admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Remove a request that will not go ahead (the farmer changed their mind, wrong plot, and so on)."""
    farm, owner = await _load_farm(db, farm_id)
    owner_name, owner_phone = owner.name, owner.phone
    if farm.sensor_status in ("requested", "in_progress"):
        label = f"{farm.name} ({owner_name})"
        previous = farm.sensor_status
        farm.sensor_status = "none"
        farm.sensor_requested_at = None
        farm.sensor_contacted_at = None
        farm.sensor_request_note = None
        record_admin_action(db, current_admin, "farm.sensor_request_cancelled", "farm", farm.id, label,
                            {"sensor_status": [previous, "none"]})
        await db.commit()
        await db.refresh(farm)
    return _admin_farm(farm, owner_name, owner_phone)


@router.post("/farms/{farm_id}/sensor-request/contact", response_model=AdminFarmResponse)
async def admin_sensor_contacted(
    farm_id: uuid.UUID,
    current_admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Contact with the farmer has begun: the request moves from New to In progress."""
    farm, owner = await _load_farm(db, farm_id)
    owner_name, owner_phone = owner.name, owner.phone
    if farm.sensor_status == "requested":
        label = f"{farm.name} ({owner_name})"
        farm.sensor_status = "in_progress"
        farm.sensor_contacted_at = datetime.now(timezone.utc)
        record_admin_action(db, current_admin, "farm.sensor_contact_started", "farm", farm.id, label,
                            {"sensor_status": ["requested", "in_progress"]})
        await db.commit()
        await db.refresh(farm)
    return _admin_farm(farm, owner_name, owner_phone)
