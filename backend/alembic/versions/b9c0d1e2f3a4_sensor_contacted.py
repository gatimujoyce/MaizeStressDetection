"""Sensor requests: when contact with the farmer began

Revision ID: b9c0d1e2f3a4
Revises: a8b9c0d1e2f3
"""
from alembic import op
import sqlalchemy as sa

revision = "b9c0d1e2f3a4"
down_revision = "a8b9c0d1e2f3"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("farms", sa.Column("sensor_contacted_at", sa.DateTime(timezone=True), nullable=True))


def downgrade():
    op.drop_column("farms", "sensor_contacted_at")
