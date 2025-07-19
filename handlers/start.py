from aiogram import Router, F
from aiogram.types import Message
from crud.user import add_user
from database.connection import connection
from keyboards.main_menu import MAIN_MENU_TEXT
from loguru import logger

router = Router()

@router.message(F.text == "/start")
@connection
async def start_command(message: Message, session):
    logger.info(f"Пользователь {message.from_user.id} вызвал команду /start.")

    is_new_user = await add_user(
        session=session,
        id=message.from_user.id,
        username=message.from_user.username,
        full_name=message.from_user.full_name
    )

    if is_new_user:
        logger.info(f"✅ Новый пользователь {message.from_user.id} добавлен в БД.")
    else:
        logger.info(f"ℹ️ Пользователь {message.from_user.id} уже есть в БД.")

    await message.answer(MAIN_MENU_TEXT)


