"""normalize_phones

Revision ID: 8344159f9fec
Revises: f738311b1212
Create Date: 2026-10-07 14:16:37.431889

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import re


# revision identifiers, used by Alembic.
revision: str = '8344159f9fec'
down_revision: Union[str, Sequence[str], None] = 'f738311b1212'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _normalize_ke_phone(raw: str):
    """
    Inline copy of app.core.utils.normalize_ke_phone for use inside this
    migration (no app imports allowed here).

    Returns the E.164 string (+254XXXXXXXXX) on success, or None if the
    value is not a valid Kenyan number.  Never raises.

    Accepted input formats (spaces/dashes/brackets are stripped first):
        +2547XXXXXXXX  +2541XXXXXXXX
         2547XXXXXXXX   2541XXXXXXXX
          07XXXXXXXX     01XXXXXXXX
    """
    if not isinstance(raw, str):
        return None

    cleaned = re.sub(r'[\s\-\(\)]', '', raw)

    if cleaned.startswith('+254'):
        normalized = cleaned
    elif cleaned.startswith('254'):
        normalized = '+' + cleaned
    elif cleaned.startswith('0'):
        normalized = '+254' + cleaned[1:]
    else:
        return None

    if not re.match(r'^\+254[17]\d{8}$', normalized):
        return None

    return normalized


def upgrade() -> None:
    conn = op.get_bind()
    rows = conn.execute(sa.text("SELECT id, phone FROM users")).fetchall()

    # --- Step 1: compute normalised value for every user ---
    # records: list of (user_id, original_phone, normalized_or_None)
    records = []
    for user_id, phone in rows:
        records.append((user_id, phone, _normalize_ke_phone(phone)))

    # --- Step 2: group by normalized value to find collisions ---
    # Only consider users whose normalized value is not None.
    from collections import defaultdict
    norm_to_ids = defaultdict(list)
    for user_id, phone, norm in records:
        if norm is not None:
            norm_to_ids[norm].append(user_id)

    collision_norm_values = {n for n, ids in norm_to_ids.items() if len(ids) > 1}

    # --- Step 3: update, collect report data ---
    updated_count = 0
    collisions = []   # (user_id, original_phone)
    invalids = []     # (user_id, original_phone)

    for user_id, phone, norm in records:
        if norm is None:
            invalids.append((user_id, phone))
            continue

        if norm in collision_norm_values:
            collisions.append((user_id, phone))
            continue

        if norm == phone:
            # Already normalised – nothing to do (no DB round-trip needed)
            continue

        conn.execute(
            sa.text("UPDATE users SET phone = :norm WHERE id = :id"),
            {"norm": norm, "id": user_id},
        )
        updated_count += 1

    # --- Step 4: print report ---
    print(f"\n[normalize_phones] Updated : {updated_count} user(s)")

    if invalids:
        print(f"[normalize_phones] Invalid  : {len(invalids)} user(s) – phone unchanged")
        for uid, ph in invalids:
            print(f"  user {uid}: {ph!r}")
    else:
        print("[normalize_phones] Invalid  : 0")

    if collisions:
        print(f"[normalize_phones] Collision: {len(collisions)} user(s) – phone unchanged")
        for uid, ph in collisions:
            print(f"  user {uid}: {ph!r}")
    else:
        print("[normalize_phones] Collision: 0")


def downgrade() -> None:
    """Downgrade schema."""
    pass
