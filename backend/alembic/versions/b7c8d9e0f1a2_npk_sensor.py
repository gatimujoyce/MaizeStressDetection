"""NPK sensor: a per-plot setting and optional nitrogen, phosphorus and potassium readings

Revision ID: b7c8d9e0f1a2
Revises: a1b2c3d4e5f6
"""
from alembic import op
import sqlalchemy as sa

revision = "b7c8d9e0f1a2"
down_revision = "a1b2c3d4e5f6"
branch_labels = None
depends_on = None

NPK_COLUMNS = ("nitrogen_mg_kg", "phosphorus_mg_kg", "potassium_mg_kg")


def upgrade():
    op.add_column("farms", sa.Column("has_npk_sensor", sa.Boolean(), nullable=False, server_default=sa.text("false")))
    for name in NPK_COLUMNS:
        op.add_column("sensor_readings", sa.Column(name, sa.Float(), nullable=True))


def downgrade():
    for name in reversed(NPK_COLUMNS):
        op.drop_column("sensor_readings", name)
    op.drop_column("farms", "has_npk_sensor")
