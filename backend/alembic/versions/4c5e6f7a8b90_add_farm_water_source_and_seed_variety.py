"""add optional farm water source and seed variety

Revision ID: 4c5e6f7a8b90
Revises: d1234567890a
Create Date: 2026-10-12 15:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "4c5e6f7a8b90"
down_revision: Union[str, Sequence[str], None] = "d1234567890a"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table("farms", schema=None) as batch_op:
        batch_op.add_column(sa.Column("water_source", sa.String(), nullable=True))
        batch_op.add_column(sa.Column("seed_variety", sa.String(), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table("farms", schema=None) as batch_op:
        batch_op.drop_column("seed_variety")
        batch_op.drop_column("water_source")
