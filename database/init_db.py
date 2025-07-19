from database.session import engine, AsyncSessionLocal
from loguru import logger
from models.base import Base
from database.default_exercises import init_default_exercises

# Инициализация базы данных и создание таблиц
async def create_tables_and_exercises():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        logger.info("✅ Таблицы успешно созданы.")

# Добавляем упражнения по умолчанию
    async with AsyncSessionLocal() as session:
        await init_default_exercises()
        logger.info("✅ Упражнения по умолчанию добавлены.")