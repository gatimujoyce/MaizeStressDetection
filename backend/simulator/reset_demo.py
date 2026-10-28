"""Clear simulated demo data before a clean replay:  python -m simulator.reset_demo
Deletes sensor alerts and simulated readings that no check-in result uses (those are kept, they belong to saved results)."""
import asyncio

from sqlalchemy import text

from app.db import SessionLocal, engine


async def main():
    async with SessionLocal() as db:
        a = await db.execute(text("DELETE FROM alerts WHERE source = 'sensor'"))
        r = await db.execute(text(
            "DELETE FROM sensor_readings r WHERE r.source = 'simulated' "
            "AND NOT EXISTS (SELECT 1 FROM predictions p WHERE p.reading_id = r.id)"))
        await db.commit()
        print(f"Deleted {a.rowcount} sensor alerts and {r.rowcount} simulated readings.")
    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())