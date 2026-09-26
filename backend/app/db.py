from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from app.core.config import settings

# Create async engine for PostgreSQL
engine = create_async_engine(settings.DATABASE_URL, echo=False)

# Async session factory
SessionLocal = async_sessionmaker(autocommit=False, autoflush=False, bind=engine)

class Base(DeclarativeBase):
    """Base class for SQLAlchemy declarative models."""
    pass
