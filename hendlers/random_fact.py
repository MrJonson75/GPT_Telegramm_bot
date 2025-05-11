"""
Обработчики для работы со случайными фактами.

Основные функции:
- handle_random: Обработчик сообщений с запросом случайного факта
- handle_more_fact: Обработчик callback-запросов на получение дополнительного случайного факта
- handle_end_random: Обработчик callback-запросов на завершение взаимодействия
"""
import logging
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, FSInputFile
from keybords import Keyboards, CallbackData
from utils.chatgpt import get_chatgpt_response
from config import Config
from utils.callback_finality import callback_finality

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
    1. Получает ответ от ChatGPT с использованием промпта для случайных фактов
    2. Отправляет изображение с фактом в качестве подписи и клавиатурой
    """
    logger.debug(f"Пользователь {message.from_user.id} запросил случайный факт")

    # Получаем ответ от ChatGPT
    try:
        response = await get_chatgpt_response(Config.get_prompts("random"))
        logger.debug(f"Получен факт: {response}")
    except Exception as e:
        logger.error(f"Ошибка получения факта: {str(e)}")
        await message.answer(
            "Не удалось получить факт. Попробуйте снова.",
            reply_markup=Keyboards.get_random_fact_keyboard()
        )
        return

    # Отправляем изображение с подписью и клавиатурой
    try:
        image_path = Config.IMAGE_PATHS["random"]
        photo = FSInputFile(path=image_path)
        await message.answer_photo(
            photo=photo,
            caption=response,
            reply_markup=Keyboards.get_random_fact_keyboard()
        )
        logger.debug(f"Отправлено изображение {image_path} с фактом для user_id={message.from_user.id}")
    except KeyError:
        logger.warning("Изображение для команды 'random' не найдено")
        await message.answer(
            response,
            reply_markup=Keyboards.get_random_fact_keyboard()
        )
    except FileNotFoundError:
        logger.error(f"Файл изображения {image_path} не найден")
        await message.answer(
            response,
            reply_markup=Keyboards.get_random_fact_keyboard()
        )
    except Exception as e:
        logger.error(f"Ошибка отправки изображения: {str(e)}")
        await message.answer(
            "Произошла ошибка. Попробуйте снова.",
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
    2. Отправляет изображение с сообщением о завершении и главное меню
    """
    logger.debug(f"Пользователь {callback.from_user.id} завершил взаимодействие с фактами")
    await callback.answer()

    # Отправка изображения с подписью и главным меню
    try:
        await callback_finality(callback)
        logger.debug(f"Выполнена callback_finality для user_id={callback.from_user.id}")
    except Exception as e:
        logger.error(f"Ошибка в callback_finality: {str(e)}")