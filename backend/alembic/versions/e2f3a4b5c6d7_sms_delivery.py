"""SMS log keeps why a message failed and, later, whether it was delivered

Revision ID: e2f3a4b5c6d7
Revises: d1e2f3a4b5c6
"""
from alembic import op
import sqlalchemy as sa

revision = "e2f3a4b5c6d7"
down_revision = "d1e2f3a4b5c6"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("sms_log", sa.Column("provider_message_id", sa.Text(), nullable=True))
    op.add_column("sms_log", sa.Column("failure_reason", sa.Text(), nullable=True))
    op.add_column("sms_log", sa.Column("delivery_status", sa.Text(), nullable=True))
    op.add_column("sms_log", sa.Column("delivery_reported_at", sa.DateTime(timezone=True), nullable=True))
    op.create_index("ix_sms_log_provider_message_id", "sms_log", ["provider_message_id"])


def downgrade():
    op.drop_index("ix_sms_log_provider_message_id", table_name="sms_log")
    op.drop_column("sms_log", "delivery_reported_at")
    op.drop_column("sms_log", "delivery_status")
    op.drop_column("sms_log", "failure_reason")
    op.drop_column("sms_log", "provider_message_id")
