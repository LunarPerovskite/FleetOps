from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from app.core.config import settings
from app.models.models import Base

# Detect database type
IS_SQLITE = "sqlite" in settings.DATABASE_URL.lower()
IS_ASYNC_SQLITE = "aiosqlite" in settings.DATABASE_URL.lower()

# Async engine for FastAPI with connection pooling
async_engine_kwargs = {
    "echo": settings.DEBUG,
    "future": True,
}

# SQLite doesn't support connection pooling options
if not IS_ASYNC_SQLITE:
    async_engine_kwargs.update({
        "pool_size": 10,
        "max_overflow": 20,
        "pool_pre_ping": True,
        "pool_recycle": 3600,
        "pool_timeout": 30,
    })

async_engine = create_async_engine(
    settings.DATABASE_URL,
    **async_engine_kwargs
)

AsyncSessionLocal = async_sessionmaker(
    async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False
)

# Sync engine for migrations and seeding
sync_engine_kwargs = {
    "echo": settings.DEBUG,
}
if not IS_SQLITE:
    sync_engine_kwargs.update({
        "pool_pre_ping": True,
        "pool_recycle": 3600,
    })

sync_engine = create_engine(
    settings.DATABASE_URL_SYNC,
    **sync_engine_kwargs
)

async def get_db():
    """Dependency for getting async database sessions"""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()

def get_sync_db():
    """Get synchronous database session (for scripts/CLI)"""
    from sqlalchemy.orm import Session
    with Session(sync_engine) as session:
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

def init_db():
    """Initialize database tables"""
    Base.metadata.create_all(bind=sync_engine)

async def close_db():
    """Close database connections (for graceful shutdown)"""
    await async_engine.dispose()
    sync_engine.dispose()
