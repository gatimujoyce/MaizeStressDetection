"""The admin action log: who changed what, and when. Rows are only ever added; nothing in the app edits or deletes them."""
from app.models import AdminAuditLog


def record_admin_action(db, admin, action, target_type, target_id, target_label, changes=None):
    """Add a log row to the session; the caller commits it together with the change itself.
    changes: {field: [old, new]} as text. Passwords are never put in here."""
    db.add(AdminAuditLog(admin_id=admin.id, admin_name=admin.name, action=action, target_type=target_type,
                         target_id=target_id, target_label=target_label, changes=changes or {}))
