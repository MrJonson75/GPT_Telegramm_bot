from typing import Optional, Dict
from datetime import datetime, timedelta
from aiogram import Router, F
from aiogram.types import Message, Voice
from aiogram.exceptions import TelegramAPIError
from utils.images import send_image
from config import Config
from utils.voice import voice_to_text, text_to_voice
from utils.chatgpt import get_chatgpt_response
from functools import wraps


class RateLimiter:
    """
    Класс для ограничения количества запросов от пользователей.

    Атрибуты:
        user_limits (Dict[int, dict]): Словарь с данными о лимитах пользователей
        max_requests (int): Максимальное количество запросов в период
        period (timedelta): Период времени для ограничения

    Методы:
        check_limit: Проверяет не превышен ли лимит запросов
        decorator: Декоратор для ограничения запросов
    """

    def __init__(self, max_requests: int = 5, period: timedelta = timedelta(minutes=1)):
        """
        Инициализирует RateLimiter.

        Параметры:
            max_requests: Максимальное количество запросов
            period: Период времени для ограничения
        """
        self.user_limits: Dict[int, dict] = {}
        self.max_requests = max_requests
        self.period = period

    def check_limit(self, user_id: int) -> bool:
        """
        Проверяет лимит запросов для пользователя.

        Параметры:
            user_id: ID пользователя

        Возвращает:
            True если лимит не превышен, False если превышен
        """
        now = datetime.now()

        if user_id not in self.user_limits:
            self.user_limits[user_id] = {
                'count': 0,
                'last_request': now
            }
            return True

        user_data = self.user_limits[user_id]

        if now - user_data['last_request'] > self.period:
            user_data['count'] = 0
            user_data['last_request'] = now
            return True

        if user_data['count'] >= self.max_requests:
            return False

        user_data['count'] += 1
        return True

    def decorator(self, func):
        """
        Декоратор для ограничения запросов к функции.
        """

        @wraps(func)
        async def wrapper(message: Message, *args, **kwargs):
            if not self.check_limit(message.from_user.id):
                raise TelegramAPIError(
                    f"Превышен лимит запросов. Максимум {self.max_requests} в {self.period.total_seconds() // 60} минут."
                )
            return await func(message, *args, **kwargs)

        return wrapper


# Создаем роутер для обработки голосовых сообщений
voice_router = Router()

# Инициализируем систему лимитов
rate_limiter = RateLimiter(max_requests=5, period=timedelta(minutes=1))

# Константы
MAX_VOICE_DURATION = 30  # Максимальная длительность голосового сообщения (секунды)
RETRY_ATTEMPTS = 3  # Количество повторных попыток
RETRY_DELAY = 1  # Задержка между попытками (секунды)


async def retry_on_failure(
        func,
        *args,
        attempts: int = RETRY_ATTEMPTS,
        delay: float = RETRY_DELAY,
        **kwargs
) -> Optional[any]:
    """
    Выполняет функцию с повторными попытками при ошибках.

    Параметры:
        func: Выполняемая функция
        attempts: Количество попыток
        delay: Задержка между попытками
        *args: Аргументы функции
        **kwargs: Именованные аргументы

    Возвращает:
        Результат функции или None при ошибке

    Вызывает:
        Последнее исключение после исчерпания попыток
    """
    import asyncio
    last_exception = None

    for attempt in range(attempts):
        try:
            return await func(*args, **kwargs)
        except Exception as e:
            last_exception = e
            if attempt < attempts - 1:
                await asyncio.sleep(delay)

    if last_exception:
        raise last_exception
    return None


@voice_router.message(F.text.lower().contains("voice"))
@rate_limiter.decorator
async def handle_voice_command(message: Message) -> None:
    """
    Обрабатывает команду 'voice' и предлагает отправить голосовое сообщение.
    """
    try:
        await send_image(message, Config.IMAGE_PATHS["voice_gpt"])
        await message.answer("Отправьте голосовое сообщение, и я отвечу вам голосом!")
    except Exception:
        await message.answer("Ошибка обработки команды. Попробуйте позже.")


@voice_router.message(F.voice)
@rate_limiter.decorator
async def handle_voice_message(message: Message) -> None:
    """
    Обрабатывает голосовое сообщение: преобразует в текст, получает ответ от ChatGPT
    и возвращает голосовой ответ.
    """
    try:
        voice = message.voice

        # Проверка длительности сообщения
        if voice.duration > MAX_VOICE_DURATION:
            raise ValueError(
                f"Сообщение слишком длинное (максимум {MAX_VOICE_DURATION} сек)."
            )

        # Получение и обработка голосового сообщения
        voice_file = await retry_on_failure(
            message.bot.get_file,
            voice.file_id
        )

        text = await retry_on_failure(
            voice_to_text,
            voice_file,
            message
        )
        if not text:
            return await message.answer("Не удалось распознать речь.")

        await message.answer(f"Вы сказали: {text}")

        # Получение ответа от ChatGPT
        response = await retry_on_failure(get_chatgpt_response, text)
        if not response:
            return await message.answer("Ошибка получения ответа.")

        # Преобразование и отправка ответа
        voice_response = await retry_on_failure(text_to_voice, response)
        if voice_response:
            await message.answer_voice(voice_response)
        else:
            await message.answer("Ошибка генерации голосового ответа.")

    except ValueError as e:
        await message.answer(str(e))
    except TelegramAPIError:
        await message.answer("Слишком много запросов. Подождите немного.")
    except Exception:
        await message.answer("Произошла ошибка. Попробуйте позже.")