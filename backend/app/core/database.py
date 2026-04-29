from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from app.core.config import settings

# Import Base from the models package (this triggers import of all model files)
from app.models import Base

# Detect database type
IS_SQLITE = "sqlite" in settings.DATABASE_URL.lower()
IS_ASYNC_SQLITE = "aiosqlite" in settings.DATABASE_URL.lower()

# ── Lazy engine creation ───────────────────────────────
# We delay engine creation until first access so that tests
# which set DATABASE_URL at runtime (e.g. to sqlite) don't
# fail at import time because a DB driver is missing.
# ─────────────────────────────────────────────────────

_async_engine = None
_sync_engine = None

def _make_async_engine():
    """Create async engine on demand."""
    kwargs = {
        "echo": settings.DEBUG,
        "future": True,
    }
    if not IS_ASYNC_SQLITE:
        kwargs.update({
            "pool_size": 10,
            "max_overflow": 20,
            "pool_pre_ping": True,
            "pool_recycle": 3600,
            "pool_timeout": 30,
        })
    return create_async_engine(settings.DATABASE_URL, **kwargs)

def _make_sync_engine():
    """Create sync engine on demand."""
    kwargs = {
        "echo": settings.DEBUG,
    }
    if not IS_SQLITE:
        kwargs.update({
            "pool_pre_ping": True,
            "pool_recycle": 3600,
        })
    return create_engine(settings.DATABASE_URL_SYNC, **kwargs)


class _EngineProxy:
    """Lazy proxy that creates the real engine on first attribute access."""
    __slots__ = ("_real", "_maker")

    def __init__(self, maker):
        self._real = None
        self._maker = maker

    def _ensure(self):
        if self._real is None:
            self._real = self._maker()
        return self._real

    # ── SQLAlchemy engine attributes ──
    def execute(self, *a, **kw):
        return self._ensure().execute(*a, **kw)

    def connect(self):
        return self._ensure().connect()

    def begin(self):
        return self._ensure().begin()

    def dispose(self):
        if self._real is not None:
            self._real.dispose()
            self._real = None

    @property
    def dialect(self):
        return self._ensure().dialect

    @property
    def url(self):
        return self._ensure().url

    # Pass through everything else
    def __getattr__(self, name):
        return getattr(self._ensure(), name)


# Module-level exports: access these just like normal engines.
# The real engine is created lazily when first used.
async_engine = _EngineProxy(_make_async_engine)
sync_engine = _EngineProxy(_make_sync_engine)

# ── Session factories (lazy too) ─────────────────────

_async_session_local = None
_sync_session_local = None

def _get_async_session_local():
    global _async_session_local
    if _async_session_local is None:
        _async_session_local = async_sessionmaker(
            async_engine,
            class_=AsyncSession,
            expire_on_commit=False,
            autoflush=False,
        )
    return _async_session_local

def _get_sync_session_local():
    global _sync_session_local
    if _sync_session_local is None:
        _sync_session_local = sessionmaker(bind=sync_engine)
    return _sync_session_local


async def get_db():
    """Dependency for getting async database sessions"""
    factory = _get_async_session_local()
    async with factory() as session:
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
    factory = _get_sync_session_local()
    with factory() as session:
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
    async_engine.dispose()
    sync_engine.dispose()
