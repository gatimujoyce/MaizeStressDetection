"""SMS log: one row per text message attempted

Revision ID: c3d4e5f6a7b8
Revises: b7c8d9e0f1a2
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "c3d4e5f6a7b8"
down_revision = "b7c8d9e0f1a2"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "sms_log",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("farm_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("farms.id", ondelete="SET NULL"), nullable=True),
        sa.Column("alert_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("alerts.id", ondelete="SET NULL"), nullable=True),
        sa.Column("kind", sa.Text(), nullable=False),
        sa.Column("phone", sa.Text(), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("status", sa.Text(), nullable=False),
        sa.Column("severity", sa.Text(), nullable=True),
    )
    op.create_index("ix_sms_log_created_at", "sms_log", ["created_at"])


def downgrade():
    op.drop_index("ix_sms_log_created_at", table_name="sms_log")
    op.drop_table("sms_log")
