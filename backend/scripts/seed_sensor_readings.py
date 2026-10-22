"""Seed four generated sensor readings over the previous 24 hours for one farm."""

import argparse
import asyncio
from datetime import datetime, timedelta, timezone
import random
import uuid

from sqlalchemy import select

from app.db import SessionLocal
from app.models import Farm, SensorReading, SourceEnum
from app.services.sensor import generate_reading


READING_OFFSETS = (
    ("normal", 23),
    ("drought_stress", 17),
    ("heat_stress", 11),
    ("waterlogging_risk", 5),
)


async def seed_farm_readings(farm_id: uuid.UUID) -> None:
    async with SessionLocal() as session:
        farm = await session.scalar(
            select(Farm).where(Farm.id == farm_id, Farm.deleted_at.is_(None))
        )
        if farm is None:
            raise ValueError(f"Active farm {farm_id} was not found")

        now = datetime.now(timezone.utc)
        rng = random.Random()
        for stress_class, hours_ago in READING_OFFSETS:
            reading_values = generate_reading(stress_class, farm.soil_type.value, rng)
            session.add(
                SensorReading(
                    id=uuid.uuid4(),
                    farm_id=farm.id,
                    recorded_at=now - timedelta(hours=hours_ago),
                    source=SourceEnum.simulated,
                    **reading_values,
                )
            )
        await session.commit()

    print(f"Added {len(READING_OFFSETS)} simulated readings for farm {farm_id}:")
    for stress_class, hours_ago in READING_OFFSETS:
        print(f"  {stress_class}: {hours_ago} hours ago")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--farm-id", required=True, type=uuid.UUID)
    args = parser.parse_args()
    asyncio.run(seed_farm_readings(args.farm_id))


if __name__ == "__main__":
    main()
