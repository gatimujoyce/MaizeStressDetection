"""Feedback questionnaire and one-week follow-up

Revision ID: f6a7b8c9d0e1
Revises: e5f6a7b8c9d0
"""
from alembic import op
import sqlalchemy as sa

revision = "f6a7b8c9d0e1"
down_revision = "e5f6a7b8c9d0"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("feedback", sa.Column("matched", sa.Text(), nullable=True))
    op.add_column("feedback", sa.Column("action_taken", sa.Text(), nullable=True))
    op.add_column("feedback", sa.Column("follow_up_outcome", sa.Text(), nullable=True))
    op.add_column("feedback", sa.Column("follow_up_at", sa.DateTime(timezone=True), nullable=True))


def downgrade():
    op.drop_column("feedback", "follow_up_at")
    op.drop_column("feedback", "follow_up_outcome")
    op.drop_column("feedback", "action_taken")
    op.drop_column("feedback", "matched")
