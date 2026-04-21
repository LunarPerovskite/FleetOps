from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from app.core.config import settings
from app.models.models import Base

# Async engine for FastAPI
async_engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,
    future=True
)

AsyncSessionLocal = async_sessionmaker(
    async_engine,
    class_=AsyncSession,
    expire_on_commit=False
)

# Sync engine for migrations
sync_engine = create_engine(
    settings.DATABASE_URL_SYNC,
    echo=settings.DEBUG
)

async def get_db():
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()

def init_db():
    Base.metadata.create_all(bind=sync_engine)
