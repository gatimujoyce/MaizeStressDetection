"""Create an administrator account or promote an existing user."""

# From Development/backend/: .\.venv\Scripts\python.exe -m scripts.create_admin --phone "0712345678" --name "Admin User"

import argparse
import asyncio
from getpass import getpass
import uuid

from sqlalchemy import select

from app.core.security import get_password_hash
from app.core.utils import normalize_ke_phone
from app.db import SessionLocal
from app.models import RoleEnum, User


async def create_or_promote_admin(db, phone: str, name: str, password: str, promote: bool = False):
    """Create an admin, or promote an existing user without changing its password."""
    normalized_phone = normalize_ke_phone(phone)
    user = await db.scalar(select(User).where(User.phone == normalized_phone))
    if user is not None:
        if not promote:
            raise ValueError("A user with this phone already exists; pass --promote to promote them")
        user.role = RoleEnum.admin
    else:
        user = User(
            id=uuid.uuid4(), name=name, phone=normalized_phone,
            password_hash=get_password_hash(password), role=RoleEnum.admin,
        )
        db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


async def _run(args, password: str) -> None:
    async with SessionLocal() as session:
        user = await create_or_promote_admin(session, args.phone, args.name, password, args.promote)
    print(f"Admin ready: {user.name} ({user.phone})")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--phone", required=True, help="Kenyan phone number")
    parser.add_argument("--name", required=True, help="Admin user's name")
    parser.add_argument("--promote", action="store_true", help="Promote an existing user without changing their password")
    args = parser.parse_args()
    asyncio.run(_run(args, getpass("Admin password: ")))


if __name__ == "__main__":
    main()
