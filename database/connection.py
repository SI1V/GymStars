from loguru import logger
from database.session import AsyncSessionLocal
from functools import wraps


# Декоратор для управления сессией базы данных
def connection(method):
    @wraps(method)
    async def wrapper(*args, **kwargs):
        async with AsyncSessionLocal() as session:
            try:
                kwargs["session"] = session
                return await method(*args, **kwargs)
            except Exception as e:
                await session.rollback()
                logger.error(f"DB error: {e}")
                raise
            finally:
                await session.close()
    return wrapper
