from contextlib import contextmanager

from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import Session, sessionmaker

from src.core.config import settings


dsn = f"postgresql+asyncpg://{settings.postgres_user}:{settings.postgres_password}@{settings.database_host}:{settings.database_port}/{settings.postgres_db}"

engine = create_async_engine(dsn, future=True)
async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


sync_dsn = f"postgresql://{settings.postgres_user}:{settings.postgres_password}@{settings.database_host}:{settings.database_port}/{settings.postgres_db}"
sync_engine = create_engine(sync_dsn, echo=False, pool_pre_ping=True)
sync_session = sessionmaker(bind=sync_engine, autocommit=False, autoflush=False)


async def get_session() -> AsyncSession:
    async with async_session() as session:
        yield session


@contextmanager
def get_session_for_cli() -> Session:
    """Контекстный менеджер для синхронной сессии CLI"""
    session = sync_session()  # Создаем сессию
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
