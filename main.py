import asyncio
from bot import bot, dp
from database.init_db import create_tables_and_exercises
from handlers import start, workouts, exercises
from loguru import logger


async def on_startup():
    logger.info("Успешно стартовали ✅")
    await create_tables_and_exercises()


async def main():
    logger.info("Старт бота...")

    # Регистрируем роутеры
    dp.include_router(start.router)
    dp.include_router(workouts.router)
    dp.include_router(exercises.router)

    dp.startup.register(on_startup)

    # Запускаем бота
    await dp.start_polling(
        bot,
        allowed_updates=dp.resolve_used_update_types(),
    )


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Bot stopped ❌")
