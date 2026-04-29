from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from typing import AsyncGenerator
from app.config import settings

engine_kwargs = {"echo": False, "future": True}
if "sqlite" not in settings.database_url:
    engine_kwargs["pool_size"] = 10
    engine_kwargs["max_overflow"] = 20

engine = create_async_engine(
    settings.database_url,
    **engine_kwargs
)

async_session_maker = async_sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)

async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """Dependency для FastAPI роутеров"""
    async with async_session_maker() as session:
        yield session

# Синхронная/Асинхронная инициализация пула больше не нужна в том виде, в каком она была,
# так как SQLAlchemy engine управляет пулом сам.