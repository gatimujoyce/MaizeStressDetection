"""Sensors can be missing from a reading: core values become optional; battery level and firmware version added

Revision ID: d1e2f3a4b5c6
Revises: c0d1e2f3a4b5
"""
from alembic import op
import sqlalchemy as sa

revision = "d1e2f3a4b5c6"
down_revision = "c0d1e2f3a4b5"
branch_labels = None
depends_on = None

CORE = ("soil_moisture", "temperature", "humidity", "leaf_wetness")


def upgrade():
    for column in CORE:
        op.alter_column("sensor_readings", column, existing_type=sa.Float(), nullable=True)
    op.add_column("sensor_readings", sa.Column("battery_percent", sa.Float(), nullable=True))
    op.add_column("sensor_readings", sa.Column("firmware", sa.String(), nullable=True))


def downgrade():
    op.drop_column("sensor_readings", "firmware")
    op.drop_column("sensor_readings", "battery_percent")
    for column in CORE:
        op.alter_column("sensor_readings", column, existing_type=sa.Float(), nullable=False)
