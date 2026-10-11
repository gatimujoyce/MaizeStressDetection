"""multi_farm_hardening

Revision ID: d1234567890a
Revises: 8344159f9fec
Create Date: 2026-10-09 14:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd1234567890a'
down_revision: Union[str, Sequence[str], None] = '8344159f9fec'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Add columns to farms table
    with op.batch_alter_table('farms', schema=None) as batch_op:
        batch_op.add_column(sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True))
        batch_op.add_column(sa.Column('size_acres', sa.Float(), nullable=True))
        batch_op.add_column(sa.Column('planting_date', sa.Date(), nullable=True))
        batch_op.add_column(sa.Column('latitude', sa.Float(), nullable=True))
        batch_op.add_column(sa.Column('longitude', sa.Float(), nullable=True))

    # 2. Rename duplicates
    conn = op.get_bind()
    # Find all farms where deleted_at IS NULL
    res = conn.execute(sa.text("SELECT id, user_id, name FROM farms WHERE deleted_at IS NULL ORDER BY name"))
    rows = res.fetchall()

    seen = {} # (user_id, name) -> count
    for farm_id, user_id, name in rows:
        key = (user_id, name)
        if key not in seen:
            seen[key] = 1
        else:
            seen[key] += 1
            new_name = f"{name} ({seen[key]})"
            # Ensure the new name itself doesn't collide
            while (user_id, new_name) in seen:
                seen[key] += 1
                new_name = f"{name} ({seen[key]})"
            
            seen[(user_id, new_name)] = 1
            conn.execute(
                sa.text("UPDATE farms SET name = :new_name WHERE id = :id"),
                {"new_name": new_name, "id": farm_id}
            )

    # 3. Add Index
    with op.batch_alter_table('farms', schema=None) as batch_op:
        batch_op.create_index(
            'ix_farm_user_name_unique',
            ['user_id', 'name'],
            unique=True,
            postgresql_where=sa.text('deleted_at IS NULL'),
            sqlite_where=sa.text('deleted_at IS NULL')
        )

def downgrade() -> None:
    # Remove Index and columns
    with op.batch_alter_table('farms', schema=None) as batch_op:
        batch_op.drop_index('ix_farm_user_name_unique')
        batch_op.drop_column('longitude')
        batch_op.drop_column('latitude')
        batch_op.drop_column('planting_date')
        batch_op.drop_column('size_acres')
        batch_op.drop_column('deleted_at')
