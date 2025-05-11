"""
Обработчики для работы со случайными фактами.

Основные функции:
- handle_random: Обработчик сообщений с запросом случайного факта
- handle_more_fact: Обработчик callback-запросов на получение дополнительного случайного факта
- handle_end_random: Обработчик callback-запросов на завершение взаимодействия

"""
import logging
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from keybords import Keyboards, CallbackData
from utils.images import send_image
from utils.chatgpt import get_chatgpt_response
from config import Config

# Настройка логирования
logger = logging.getLogger(__name__)

# Инициализация роутера для обработки случайных фактов
rand_router = Router()

@rand_router.message(F.text.lower().contains("random"))
async def handle_random(message: Message):
    """
    Обработчик сообщений с запросом случайного факта.

    Параметры:
    - message: Объект сообщения от пользователя

    Действия:
    1. Отправляет изображение из указанного в конфиге пути
    2. Получает ответ от ChatGPT с использованием промпта для случайных фактов
    3. Отправляет ответ пользователю с клавиатурой для запроса дополнительного факта
    """
    logger.debug(f"Пользователь {message.from_user.id} запросил случайный факт")
    try:
        # Отправляем изображение из пути, указанного в конфиге
        await send_image(message, Config.IMAGE_PATHS["random"])
    except KeyError:
        logger.warning("Изображение для команды 'random' не найдено")

    # Получаем ответ от ChatGPT
    try:
        response = await get_chatgpt_response(Config.get_prompts("random"))
        logger.debug(f"Получен факт: {response}")
    except Exception as e:
        logger.error(f"Ошибка получения факта: {str(e)}")
        await message.answer("Не удалось получить факт. Попробуйте снова.")
        return

    # Отправляем ответ пользователю с клавиатурой
    await message.answer(
        response,
        reply_markup=Keyboards.get_random_fact_keyboard()
    )

@rand_router.callback_query(F.data == CallbackData.RANDOM)
async def handle_more_fact(callback: CallbackQuery):
    """
    Обработчик callback-запросов на получение дополнительного случайного факта.

    Параметры:
    - callback: CallbackQuery объект от нажатия кнопки

    Действия:
    1. Отправляет подтверждение о получении callback
    2. Вызывает handle_random для обработки запроса как обычного сообщения
    """
    logger.debug(f"Пользователь {callback.from_user.id} запросил ещё один факт")
    await callback.answer()
    await handle_random(callback.message)

@rand_router.callback_query(F.data == CallbackData.MAIN_MENU)
async def handle_end_random(callback: CallbackQuery):
    """
    Обработчик callback-запросов на завершение взаимодействия с фактами.

    Параметры:
    - callback: CallbackQuery объект от нажатия кнопки

    Действия:
    1. Отправляет подтверждение о получении callback
    2. Отправляет сообщение о завершении и главное меню
    """
    logger.debug(f"Пользователь {callback.from_user.id} завершил взаимодействие с фактами")
    await callback.answer()
    await callback.message.answer(
        "Спасибо за интерес к фактам! Начните заново с /random или вернитесь в меню с /start.",
        reply_markup=Keyboards.main_menu()
    )