from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from config.main_conf import settings

engine = create_async_engine(
    settings.db.database_url,
    echo=settings.db.sql_echo
)

AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False
)

