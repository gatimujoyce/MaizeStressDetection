"""normalize_phones

Revision ID: 8344159f9fec
Revises: f738311b1212
Create Date: 2026-10-07 14:16:37.431889

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '8344159f9fec'
down_revision: Union[str, Sequence[str], None] = 'f738311b1212'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    from app.core.utils import normalize_ke_phone
    from fastapi import HTTPException
    
    conn = op.get_bind()
    res = conn.execute(sa.text("SELECT id, phone FROM users"))
    users = res.fetchall()
    
    for user_id, phone in users:
        try:
            new_phone = normalize_ke_phone(phone)
            if new_phone != phone:
                conn.execute(
                    sa.text("UPDATE users SET phone = :new_phone WHERE id = :id"),
                    {"new_phone": new_phone, "id": user_id}
                )
        except HTTPException as e:
            print(f"Skipping normalization for user {user_id}, invalid phone {phone}: {e.detail}")
        except Exception as e:
            print(f"Skipping normalization for user {user_id}, invalid phone {phone}: {str(e)}")


def downgrade() -> None:
    """Downgrade schema."""
    pass
