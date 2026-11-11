"""Device keys: a secret per plot that lets an installed sensor box post readings

Revision ID: c0d1e2f3a4b5
Revises: b9c0d1e2f3a4
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "c0d1e2f3a4b5"
down_revision = "b9c0d1e2f3a4"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "device_keys",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("farm_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("farms.id"), nullable=False),
        sa.Column("key_hash", sa.String(), nullable=False, unique=True),
        sa.Column("key_prefix", sa.String(), nullable=False),
        sa.Column("created_by_name", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_used_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_device_keys_farm_id", "device_keys", ["farm_id"])


def downgrade():
    op.drop_index("ix_device_keys_farm_id", table_name="device_keys")
    op.drop_table("device_keys")
