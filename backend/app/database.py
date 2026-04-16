"""Database configuration and session management."""

import time
from typing import AsyncGenerator

from app.config import settings
from app.logging_config import logger
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.pool import NullPool


class Base(DeclarativeBase):
    """Base class for ORM models."""


engine_kwargs = {
    "echo": settings.DEBUG,
    "pool_pre_ping": True,
}
if settings.ENGINE_MODE == "mock":
    engine_kwargs["poolclass"] = NullPool
else:
    engine_kwargs["pool_size"] = settings.DATABASE_POOL_SIZE
    engine_kwargs["max_overflow"] = settings.DATABASE_MAX_OVERFLOW

engine = create_async_engine(settings.DATABASE_URL, **engine_kwargs)

async_session_factory = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency for database sessions."""
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            logger.exception("database_session_error")
            raise


async def init_db():
    """Initialize database tables for local-first development."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("database_initialized")


async def close_db():
    """Close open database connections."""
    await engine.dispose()
    logger.info("database_closed")


async def check_db_connection() -> dict:
    """Run a lightweight DB ping and expose timing plus pool state."""
    start = time.perf_counter()
    async with engine.connect() as conn:
        await conn.execute(text("SELECT 1"))
    duration_ms = round((time.perf_counter() - start) * 1000, 2)
    pool = engine.sync_engine.pool
    return {
        "ok": True,
        "latency_ms": duration_ms,
        "pool_class": pool.__class__.__name__,
        "pool_size": getattr(pool, "size", lambda: None)(),
        "checked_in": getattr(pool, "checkedin", lambda: None)(),
        "checked_out": getattr(pool, "checkedout", lambda: None)(),
        "overflow": getattr(pool, "overflow", lambda: None)(),
    }
