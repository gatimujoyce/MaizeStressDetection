"""
test_migration.py

Two tests:
  1. test_migration_upgrade_and_downgrade – smoke-test the full Alembic chain
     (uses the real DATABASE_URL from env, same as before).
  2. test_normalize_phones_migration – exercises the normalize_phones data
     migration in isolation against an in-process SQLite database, without
     going through alembic command.upgrade (which would hit env.py and
     override the URL with the real Postgres DATABASE_URL).
"""
import os
import uuid
import pytest
import sqlalchemy as sa
from sqlalchemy import text
from alembic import command
from alembic.config import Config
from alembic.runtime.migration import MigrationContext
from alembic.operations import Operations


def test_migration_upgrade_and_downgrade(tmp_path):
    backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    os.chdir(backend_dir)

    alembic_cfg = Config("alembic.ini")
    db_path = str(tmp_path / "test.db").replace("\\", "/")
    alembic_cfg.set_main_option("sqlalchemy.url", f"sqlite:///{db_path}")

    # upgrade to head
    command.upgrade(alembic_cfg, "head")

    # downgrade to previous
    command.downgrade(alembic_cfg, "8344159f9fec")

    # upgrade again to ensure reversibility
    command.upgrade(alembic_cfg, "head")


def test_normalize_phones_migration():
    """
    Exercise the normalize_phones upgrade() logic directly against an
    in-process SQLite engine, bypassing env.py (which would redirect to
    Postgres).

    Seed:
      UserA  0712345678       ← collision with UserB
      UserB  +254712345678    ← collision with UserA (already normalised)
      UserC  0112345678       ← valid, unique → must be normalised
      UserD  abc123           ← invalid  → must stay unchanged

    Expected after upgrade():
      UserC → +254112345678
      UserA, UserB, UserD → unchanged
    """
    # Import the migration module's functions directly.
    import importlib.util, pathlib
    migration_path = pathlib.Path(__file__).parent.parent / "alembic" / "versions" / "8344159f9fec_normalize_phones.py"
    spec = importlib.util.spec_from_file_location("migration_normalize_phones", migration_path)
    migration = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(migration)

    # Build a minimal users table in SQLite.
    engine = sa.create_engine("sqlite:///:memory:", echo=False)
    with engine.begin() as conn:
        conn.execute(text(
            "CREATE TABLE users ("
            "  id TEXT PRIMARY KEY,"
            "  name TEXT NOT NULL,"
            "  phone TEXT NOT NULL,"
            "  password_hash TEXT NOT NULL,"
            "  role TEXT NOT NULL"
            ")"
        ))
        for name, phone in [
            ("UserA", "0712345678"),
            ("UserB", "+254712345678"),
            ("UserC", "0112345678"),
            ("UserD", "abc123"),
        ]:
            conn.execute(
                text("INSERT INTO users (id, name, phone, password_hash, role) "
                     "VALUES (:id, :name, :phone, 'x', 'farmer')"),
                {"id": str(uuid.uuid4()), "name": name, "phone": phone},
            )

    # Run upgrade() via MigrationContext so op.get_bind() works correctly.
    with engine.begin() as conn:
        mc = MigrationContext.configure(conn)
        with Operations.context(mc):
            migration.upgrade()

    # Verify.
    with engine.connect() as conn:
        rows = {
            r[0]: r[1]
            for r in conn.execute(text("SELECT name, phone FROM users"))
        }

    assert rows["UserC"] == "+254112345678", (
        f"UserC (valid unique) must be normalised; got {rows['UserC']!r}"
    )
    assert rows["UserA"] == "0712345678", (
        f"UserA (collision) must be unchanged; got {rows['UserA']!r}"
    )
    assert rows["UserB"] == "+254712345678", (
        f"UserB (collision, already E.164) must be unchanged; got {rows['UserB']!r}"
    )
    assert rows["UserD"] == "abc123", (
        f"UserD (invalid) must be unchanged; got {rows['UserD']!r}"
    )
