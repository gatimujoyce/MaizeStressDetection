"""sensor alerts: alerts no longer need a prediction

Revision ID: a1b2c3d4e5f6
Revises: 4c5e6f7a8b90
"""
from alembic import op
import sqlalchemy as sa

revision = "a1b2c3d4e5f6"
down_revision = "4c5e6f7a8b90"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.alter_column("alerts", "prediction_id", existing_type=sa.UUID(), nullable=True)
    op.add_column("alerts", sa.Column("source", sa.Text(), nullable=False, server_default="prediction"))
    op.add_column("alerts", sa.Column("stress_class", sa.Text(), nullable=True))
    op.add_column("alerts", sa.Column("message", sa.Text(), nullable=True))
    op.add_column("alerts", sa.Column("created_at", sa.DateTime(timezone=True), nullable=False,
                                      server_default=sa.text("now()")))
    op.add_column("alerts", sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True))


def downgrade() -> None:
    op.drop_column("alerts", "resolved_at")
    op.drop_column("alerts", "created_at")
    op.drop_column("alerts", "message")
    op.drop_column("alerts", "stress_class")
    op.drop_column("alerts", "source")
    op.execute("DELETE FROM alerts WHERE prediction_id IS NULL")
    op.alter_column("alerts", "prediction_id", existing_type=sa.UUID(), nullable=False)