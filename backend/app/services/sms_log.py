"""One row per text message we tried to send, so the admin SMS log shows what was sent, to whom, and whether it went."""
from app.models import SmsLog


def record_sms(db, *, user_id, farm_id, alert_id, kind, phone, message, status, severity=None):
    """Add a log row to the session. The caller commits. kind: 'sensor_alert' or 'photo_alert'. status: 'sent' or 'failed'."""
    db.add(SmsLog(user_id=user_id, farm_id=farm_id, alert_id=alert_id, kind=kind, phone=phone or "",
                  message=message, status=status, severity=severity))
