"""Sensor setup requests: how each plot is monitored (photo only, sensor requested, sensor installed)

Revision ID: a8b9c0d1e2f3
Revises: f6a7b8c9d0e1
"""
from alembic import op
import sqlalchemy as sa

revision = "a8b9c0d1e2f3"
down_revision = "f6a7b8c9d0e1"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("farms", sa.Column("sensor_status", sa.String(), nullable=False, server_default="none"))
    op.add_column("farms", sa.Column("sensor_requested_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("farms", sa.Column("sensor_installed_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("farms", sa.Column("sensor_request_note", sa.Text(), nullable=True))
    # Plots that already send readings (the simulator ones) count as installed.
    op.execute("UPDATE farms SET sensor_status = 'installed' WHERE id IN (SELECT DISTINCT farm_id FROM sensor_readings)")


def downgrade():
    op.drop_column("farms", "sensor_request_note")
    op.drop_column("farms", "sensor_installed_at")
    op.drop_column("farms", "sensor_requested_at")
    op.drop_column("farms", "sensor_status")
