"""
Модуль commands.py

Обработчик команд и callback-запросов для Telegram-бота.

Основные функции:
- Обработка команды /start и callback-запроса "start"
- Отправка главного меню с изображением и приветственным сообщением
- Очистка сессий пользователя при возврате в стартовое меню
- Поддержка команд /state и /reset для диагностики
- Обработка всех необработанных callback-запросов
"""
import logging
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from keybords import Keyboards
from config import Config
from utils.images import send_image

# Настройка логирования
logger = logging.getLogger(__name__)
logger.info(f"Config.IMAGE_PATHS: {Config.IMAGE_PATHS}, Config.get_messages('main'): {Config.get_messages('main')}")

# Инициализация роутера для обработки команд
comm_router = Router()



@comm_router.message(Command("start"))
async def handle_start(message: Message, state: FSMContext = None) -> None:
    """
    Обработчик команды /start.

    Действия:
    1. Отправляет главное изображение из конфига
    2. Отправляет приветственное сообщение из конфига
    3. Отображает главное меню с клавиатурой
    4. Очищает сессии пользователя
    5. Сбрасывает состояние FSM (если передан state)

    Args:
        message: Объект сообщения от пользователя
        state: Контекст состояния FSM (опционально, для callback)
    """
    user_id = message.from_user.id
    logger.debug(f"Пользователь {user_id} вызвал команду /start")

    try:
        await send_image(message, Config.IMAGE_PATHS['main'])
    except KeyError:
        logger.warning(f"Изображение 'main' не найдено в Config.IMAGE_PATHS")
    except Exception as e:
        logger.error(f"Ошибка отправки изображения: {str(e)}")

    answer_text = Config.get_messages('main') or "Добро пожаловать! Выберите действие в меню."
    try:
        await message.answer(
            answer_text,
            reply_markup=Keyboards.main_menu()
        )
    except Exception as e:
        logger.error(f"Ошибка отправки сообщения: {str(e)}")
        await message.answer(
            "Произошла ошибка. Попробуйте позже.",
            reply_markup=Keyboards.main_menu()
        )
        return

    # Очищаем сессии
    try:
        if user_id in Config.USER_SESSIONS:
            del Config.USER_SESSIONS[user_id]
            logger.debug(f"Очищена сессия USER_SESSIONS для user_id={user_id}")
        if user_id in Config.USER_QUIZZES:
            del Config.USER_QUIZZES[user_id]
            logger.debug(f"Очищена сессия USER_QUIZZES для user_id={user_id}")
    except Exception as e:
        logger.error(f"Ошибка очистки сессий для user_id={user_id}: {str(e)}")

    # Сбрасываем состояние FSM, если state передан
    if state:
        await state.clear()
        logger.debug(f"Сброшено состояние FSM для user_id={user_id}")


@comm_router.callback_query(F.data == "start")
async def handle_start_callback(callback: CallbackQuery, state: FSMContext) -> None:
    """
    Обработчик callback-запроса с данными "start".

    Действия:
    1. Вызывает обработчик команды /start
    2. Подтверждает callback

    Args:
        callback: Объект callback-запроса от кнопки
        state: Контекст состояния FSM
    """
    user_id = callback.from_user.id
    logger.debug(f"Пользователь {user_id} вызвал callback 'start'")
    try:
        await handle_start(callback.message, state)
        await callback.answer()
    except Exception as e:
        logger.error(f"Ошибка обработки callback 'start' для user_id={user_id}: {str(e)}")
        await callback.message.answer(
            "Произошла ошибка. Попробуйте позже.",
            reply_markup=Keyboards.main_menu()
        )
        await callback.answer()