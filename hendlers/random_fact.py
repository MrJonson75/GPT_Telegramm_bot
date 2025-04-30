"""
        Обработчики для работы со случайными фактами.

        Основные функции:
        - handle_random: Обработчик сообщений с запросом случайного факта
        - handle_more_fact: Обработчик callback-запросов на получение дополнительного случайного факта

        Зависимости:
        - aiogram: Для работы с Telegram API
        - Внутренние модули: keyboards, utils.images, utils.chatgpt, config
"""

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from keybords import Keyboards
from utils.images import send_image
from utils.chatgpt import get_chatgpt_response
from config import Config

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
    # Отправляем изображение из пути, указанного в конфиге
    await send_image(message, Config.IMAGE_PATHS["random"])

    # Получаем ответ от ChatGPT с использованием промпта для случайных фактов
    response = await get_chatgpt_response(Config.get_prompts("random"))

    # Отправляем ответ пользователю с клавиатурой для запроса доп. факта
    await message.answer(
        response,
        reply_markup=Keyboards.get_random_fact_keyboard()
    )


@rand_router.callback_query(F.data == "random")
async def handle_more_fact(callback: CallbackQuery):
    """
    Обработчик callback-запросов на получение дополнительного случайного факта.

    Параметры:
    - callback: CallbackQuery объект от нажатия кнопки

    Действия:
    1. Отправляет подтверждение о получении callback
    2. Вызывает handle_random для обработки запроса как обычного сообщения
    """
    # Подтверждаем получение callback
    await callback.answer()

    # Обрабатываем запрос как обычное сообщение
    await handle_random(callback.message)