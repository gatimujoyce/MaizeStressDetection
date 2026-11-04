"""Sign-in safety: forced password change, failed-login lockout, one-time SMS codes

Revision ID: e5f6a7b8c9d0
Revises: d4e5f6a7b8c9
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "e5f6a7b8c9d0"
down_revision = "d4e5f6a7b8c9"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("users", sa.Column("must_change_password", sa.Boolean(), nullable=False, server_default=sa.text("false")))
    op.add_column("users", sa.Column("failed_login_count", sa.Integer(), nullable=False, server_default=sa.text("0")))
    op.add_column("users", sa.Column("locked_until", sa.DateTime(timezone=True), nullable=True))
    op.create_table(
        "one_time_codes",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("phone", sa.Text(), nullable=False),
        sa.Column("purpose", sa.Text(), nullable=False),
        sa.Column("code_hash", sa.Text(), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("attempts", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("used", sa.Boolean(), nullable=False, server_default=sa.text("false")),
    )
    op.create_index("ix_one_time_codes_phone", "one_time_codes", ["phone"])
    op.create_index("ix_one_time_codes_created_at", "one_time_codes", ["created_at"])


def downgrade():
    op.drop_index("ix_one_time_codes_created_at", table_name="one_time_codes")
    op.drop_index("ix_one_time_codes_phone", table_name="one_time_codes")
    op.drop_table("one_time_codes")
    op.drop_column("users", "locked_until")
    op.drop_column("users", "failed_login_count")
    op.drop_column("users", "must_change_password")
