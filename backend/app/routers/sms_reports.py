"""Delivery reports from the SMS service. Africa's Talking posts one here when a message reaches (or fails to reach) the
phone, so the admin SMS log can say Delivered or Not delivered, not just 'accepted'.

Setup (production): in the Africa's Talking dashboard set the delivery report URL to
    https://<your server>/sms/delivery-report?token=<SMS_DLR_TOKEN>
and set SMS_DLR_TOKEN in the server's environment. Without that token the endpoint stays switched off (503), because it is
open to the internet and the token is the only thing that proves a report is genuine. It cannot work from a laptop that has
no public address, so the log then shows 'No report yet'."""
import os
import secrets
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, Form, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.core.deps import get_db
from app.models import SmsLog

router = APIRouter(prefix="/sms", tags=["sms"])


def delivery_state(status: str) -> str:
    """Africa's Talking statuses: Success = on the phone; Failed or Rejected = will not arrive; the rest = still on its way."""
    s = (status or "").strip().lower()
    if s == "success":
        return "delivered"
    if s in ("failed", "rejected"):
        return "failed"
    return "in_transit"


@router.post("/delivery-report")
async def delivery_report(
    token: str = Query(default=""),
    id: str = Form(...),
    status: str = Form(...),
    failureReason: Optional[str] = Form(default=None),
    db: AsyncSession = Depends(get_db),
):
    expected = os.getenv("SMS_DLR_TOKEN", "")
    if not expected:
        raise HTTPException(status_code=503, detail="Delivery reports are switched off")
    if not secrets.compare_digest(token.encode(), expected.encode()):
        raise HTTPException(status_code=403, detail="Wrong token")
    row = (await db.execute(select(SmsLog).where(SmsLog.provider_message_id == id))).scalars().first()
    if row is not None:
        state = delivery_state(status)
        row.delivery_status = state
        row.delivery_reported_at = datetime.now(timezone.utc)
        if state == "failed":
            row.failure_reason = (failureReason or status or "Not delivered")[:200]
        await db.commit()
    return {"ok": True}
