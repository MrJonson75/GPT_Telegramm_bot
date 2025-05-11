"""
Модуль для обработки голосовых сообщений в Telegram-боте.

Основные функции:
- Обработка команды /voice или текста с "voice" для приглашения к отправке голосового сообщения
- Преобразование голосового сообщения в текст, получение ответа от ChatGPT и отправка голосового ответа
- Ограничение частоты запросов с помощью RateLimiter
- Использование Finite State Machine (FSM) для управления состоянием
- Повторные попытки при ошибках API

"""
import logging
from typing import Optional, Dict
from datetime import datetime, timedelta
from aiogram import Router, F
from aiogram.types import Message, Voice
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.exceptions import TelegramAPIError
from keybords import Keyboards, CallbackData
from utils.images import send_image
from utils.voice import voice_to_text, text_to_voice
from utils.chatgpt import get_chatgpt_response
from config import Config
from functools import wraps
import asyncio

# Настройка логирования
logger = logging.getLogger(__name__)

# Создаем роутер для обработки голосовых сообщений
voice_router = Router()

# Константы
MAX_VOICE_DURATION = 30  # Максимальная длительность голосового сообщения (секунды)
RETRY_ATTEMPTS = 3  # Количество повторных попыток
RETRY_DELAY = 1  # Задержка между попытками (секунды)

class VoiceState(StatesGroup):
    """
    Класс состояний FSM для управления голосовым интерфейсом.

    Состояния:
        waiting_for_voice: Ожидание голосового сообщения
    """
    waiting_for_voice = State()

class RateLimiter:
    """
    Класс для ограничения количества запросов от пользователей.

    Атрибуты:
        user_limits: Словарь с данными о лимитах пользователей
        max_requests: Максимальное количество запросов в период
        period: Период времени для ограничения
    """
    def __init__(self, max_requests: int = 5, period: timedelta = timedelta(minutes=1)):
        """
        Инициализирует RateLimiter.

        Args:
            max_requests: Максимальное количество запросов
            period: Период времени для ограничения
        """
        self.user_limits: Dict[int, dict] = {}
        self.max_requests = max_requests
        self.period = period
        logger.debug(f"RateLimiter инициализирован: max_requests={max_requests}, period={period}")

    def check_limit(self, user_id: int) -> bool:
        """
        Проверяет лимит запросов для пользователя.

        Args:
            user_id: ID пользователя

        Returns:
            bool: True если лимит не превышен, False если превышен
        """
        now = datetime.now()
        logger.debug(f"Проверка лимита для user_id={user_id}")

        if user_id not in self.user_limits:
            self.user_limits[user_id] = {
                'count': 1,
                'last_request': now
            }
            logger.debug(f"Новая запись для user_id={user_id}: count=1, last_request={now}")
            return True

        user_data = self.user_limits[user_id]

        if now - user_data['last_request'] > self.period:
            user_data['count'] = 1
            user_data['last_request'] = now
            logger.debug(f"Сброс лимита для user_id={user_id}: count=1, last_request={now}")
            return True

        if user_data['count'] >= self.max_requests:
            logger.warning(f"Превышен лимит для user_id={user_id}: count={user_data['count']}")
            return False

        user_data['count'] += 1
        logger.debug(f"Обновление для user_id={user_id}: count={user_data['count']}")
        return True

    def cleanup(self):
        """
        Удаляет устаревшие записи из user_limits.
        """
        now = datetime.now()
        expired_users = [
            user_id for user_id, data in self.user_limits.items()
            if now - data['last_request'] > self.period
        ]
        for user_id in expired_users:
            logger.debug(f"Удаление устаревшей записи для user_id={user_id}")
            del self.user_limits[user_id]

    def decorator(self, func):
        """
        Декоратор для ограничения запросов к функции.
        """
        @wraps(func)
        async def wrapper(message: Message, *args, **kwargs):
            self.cleanup()  # Очистка перед проверкой
            if not self.check_limit(message.from_user.id):
                logger.warning(f"Превышен лимит запросов для user_id={message.from_user.id}")
                await message.answer(
                    f"Слишком много запросов. Максимум {self.max_requests} за "
                    f"{int(self.period.total_seconds() // 60)} минут. Попробуйте позже.",
                    reply_markup=Keyboards.main_menu()
                )
                return
            return await func(message, *args, **kwargs)
        return wrapper

# Инициализируем систему лимитов
rate_limiter = RateLimiter(max_requests=5, period=timedelta(minutes=1))

async def retry_on_failure(
        func,
        *args,
        attempts: int = RETRY_ATTEMPTS,
        delay: float = RETRY_DELAY,
        **kwargs
) -> Optional[any]:
    """
    Выполняет функцию с повторными попытками при ошибках.

    Args:
        func: Выполняемая функция
        attempts: Количество попыток
        delay: Задержка между попытками
        *args: Аргументы функции
        **kwargs: Именованные аргументы

    Returns:
        Результат функции или None при ошибке

    Raises:
        Последнее исключение после исчерпания попыток
    """
    last_exception = None
    for attempt in range(attempts):
        try:
            logger.debug(f"Попытка {attempt + 1}/{attempts} для функции {func.__name__}")
            result = await func(*args, **kwargs)
            logger.debug(f"Успешное выполнение {func.__name__}")
            return result
        except Exception as e:
            logger.error(f"Ошибка в {func.__name__} (попытка {attempt + 1}): {str(e)}")
            last_exception = e
            if attempt < attempts - 1:
                await asyncio.sleep(delay)

    if last_exception:
        logger.error(f"Исчерпаны попытки для {func.__name__}: {str(last_exception)}")
        raise last_exception
    return None



@voice_router.message(F.text.lower().contains("voice"))
@rate_limiter.decorator
async def handle_voice_command(message: Message, state: FSMContext) -> None:
    """
    Обрабатывает команду /voice или текст с "voice" и предлагает отправить голосовое сообщение.

    Args:
        message: Объект сообщения от пользователя
        state: Контекст состояния FSM
    """
    logger.debug(f"Пользователь {message.from_user.id} запустил голосовой интерфейс")
    try:
        await send_image(message, Config.IMAGE_PATHS["voice_gpt"])
        await message.answer(
            "Отправьте голосовое сообщение, и я отвечу вам голосом!",
            reply_markup=Keyboards.get_voice_control_keyboard()
        )
        await state.set_state(VoiceState.waiting_for_voice)
        logger.debug(f"Установлено состояние VoiceState.waiting_for_voice для user_id={message.from_user.id}")
    except KeyError:
        logger.warning("Изображение для команды 'voice_gpt' не найдено")
        await message.answer(
            "Отправьте голосовое сообщение, и я отвечу вам голосом!",
            reply_markup=Keyboards.get_voice_control_keyboard()
        )
        await state.set_state(VoiceState.waiting_for_voice)
    except Exception as e:
        logger.error(f"Ошибка обработки команды /voice: {str(e)}")
        await message.answer(
            "Ошибка обработки команды. Попробуйте позже.",
            reply_markup=Keyboards.main_menu()
        )

@voice_router.message(VoiceState.waiting_for_voice, F.voice)
@rate_limiter.decorator
async def handle_voice_message(message: Message, state: FSMContext) -> None:
    """
    Обрабатывает голосовое сообщение: преобразует в текст, получает ответ от ChatGPT
    и возвращает голосовой ответ.

    Args:
        message: Объект сообщения с голосом
        state: Контекст состояния FSM
    """
    logger.debug(f"Пользователь {message.from_user.id} отправил голосовое сообщение")
    try:
        voice = message.voice

        # Проверка длительности сообщения
        if voice.duration > MAX_VOICE_DURATION:
            logger.warning(f"Голосовое сообщение слишком длинное: {voice.duration} сек")
            await message.answer(
                f"Сообщение слишком длинное (максимум {MAX_VOICE_DURATION} сек).",
                reply_markup=Keyboards.get_voice_control_keyboard()
            )
            return

        # Получение и обработка голосового сообщения
        voice_file = await retry_on_failure(
            message.bot.get_file,
            voice.file_id
        )
        if not voice_file:
            logger.error("Не удалось получить файл голосового сообщения")
            await message.answer(
                "Не удалось обработать голосовое сообщение. Попробуйте снова.",
                reply_markup=Keyboards.get_voice_control_keyboard()
            )
            return

        text = await retry_on_failure(
            voice_to_text,
            voice_file,
            message
        )
        if not text:
            logger.warning("Не удалось распознать речь в голосовом сообщении")
            await message.answer(
                "Не удалось распознать речь. Попробуйте говорить четче.",
                reply_markup=Keyboards.get_voice_control_keyboard()
            )
            return

        logger.debug(f"Распознанный текст: {text}")
        await message.answer(
            f"Вы сказали: {text}",
            reply_markup=Keyboards.get_voice_control_keyboard()
        )

        # Получение ответа от ChatGPT
        response = await retry_on_failure(get_chatgpt_response, text)
        if not response:
            logger.error("Не удалось получить ответ от ChatGPT")
            await message.answer(
                "Ошибка получения ответа. Попробуйте снова.",
                reply_markup=Keyboards.get_voice_control_keyboard()
            )
            return

        logger.debug(f"Ответ от ChatGPT: {response}")

        # Преобразование и отправка ответа
        voice_response = await retry_on_failure(text_to_voice, response)
        if voice_response:
            logger.debug("Голосовой ответ успешно сгенерирован")
            await message.answer_voice(
                voice_response,
                reply_markup=Keyboards.get_voice_control_keyboard()
            )
        else:
            logger.error("Не удалось сгенерировать голосовой ответ")
            await message.answer(
                "Ошибка генерации голосового ответа. Вот текстовый ответ:\n\n{response}",
                reply_markup=Keyboards.get_voice_control_keyboard()
            )

    except ValueError as e:
        logger.warning(f"Ошибка значения: {str(e)}")
        await message.answer(
            str(e),
            reply_markup=Keyboards.get_voice_control_keyboard()
        )
    except TelegramAPIError as e:
        logger.warning(f"Ошибка Telegram API: {str(e)}")
        await message.answer(
            "Слишком много запросов. Подождите немного.",
            reply_markup=Keyboards.main_menu()
        )
    except Exception as e:
        logger.error(f"Необработанная ошибка в handle_voice_message: {str(e)}")
        await message.answer(
            "Произошла ошибка. Попробуйте позже.",
            reply_markup=Keyboards.get_voice_control_keyboard()
        )

@voice_router.message(F.data == CallbackData.END_VOICE)
async def return_to_main_menu(message: Message, state: FSMContext):
    """
    Обработчик для возврата в главное меню.

    Args:
        message: Объект сообщения от пользователя
        state: Контекст состояния FSM
    """
    logger.debug(f"Пользователь {message.from_user.id} вернулся в главное меню")
    await state.clear()
    await message.answer(
        "Голосовой интерфейс завершён. Начните заново с /voice или /start.",
        reply_markup=Keyboards.main_menu()
    )