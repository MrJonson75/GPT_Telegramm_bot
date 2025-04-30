"""
        Модуль commands.py

        Обработчик команд и callback-запросов для Telegram бота.

        Основные функции:
        - Обработка команды /start и кнопки "start"
        - Отправка главного меню
        - Очистка сессий пользователя при возврате в стартовое меню

        Зависимости:
        - aiogram (Router, F, Message, CallbackQuery, Command)
        - Локальные модули: keybords, config, utils.images
"""

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from keybords import Keyboards
from config import Config
from utils.images import send_image

# Инициализация роутера для обработки команд
comm_router = Router()


@comm_router.message(Command("start"))
async def handle_start(message: Message) -> None:
    """
    Обработчик команды /start.

    Действия:
    1. Отправляет главное изображение из конфига
    2. Отправляет приветственное сообщение из конфига
    3. Отображает главное меню с клавиатурой

    Args:
        message (Message): Входящее сообщение от пользователя
    """
    await send_image(message, Config.IMAGE_PATHS['main'])
    answer_text = Config.get_messages('main')
    await message.answer(
        answer_text,
        reply_markup=Keyboards.main_menu()
    )


@comm_router.callback_query(F.data == "start")
async def handle_start_callback(callback: CallbackQuery) -> None:
    """
    Обработчик callback-запроса с данными "start".

    Действия:
    1. Отправляет ответ на callback (убирает часики)
    2. Вызывает обработчик команды /start
    3. Очищает сессии пользователя (если они есть)

    Args:
        callback (CallbackQuery): Входящий callback от кнопки
    """
    await callback.answer()
    await handle_start(callback.message)

    # Очищаем сессии при возврате в стартовое меню
    user_id = callback.from_user.id
    if user_id in Config.USER_SESSIONS:
        del Config.USER_SESSIONS[user_id]
    if user_id in Config.USER_QUIZZES:
        del Config.USER_QUIZZES[user_id]