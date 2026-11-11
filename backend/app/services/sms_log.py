"""One row per text message we tried to send, so the admin SMS log shows what was sent, to whom, and whether it went."""
from app.models import SmsLog


def record_sms(db, *, user_id, farm_id, alert_id, kind, phone, message, status, severity=None, result=None):
    """Add a log row to the session. The caller commits. kind: 'sensor_alert', 'photo_alert', 'password_reset' or
    'verification_code'. status: 'sent' (the SMS service accepted it) or 'failed'. result: the SmsResult from send_sms,
    when there is one, so the log keeps the provider's message id (for the delivery report) and the reason for a failure."""
    db.add(SmsLog(user_id=user_id, farm_id=farm_id, alert_id=alert_id, kind=kind, phone=phone or "",
                  message=message, status=status, severity=severity,
                  provider_message_id=getattr(result, "message_id", None),
                  failure_reason=getattr(result, "reason", None) if status == "failed" else None))
