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
from aiogram.types import Message, Voice, CallbackQuery, FSInputFile
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.exceptions import TelegramAPIError
from keybords import Keyboards, CallbackData
from utils.voice import voice_to_text, text_to_voice
from utils.chatgpt import get_chatgpt_response
from config import Config
from functools import wraps
import asyncio
from utils.callback_finality import callback_finality

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

                # Подготовка текста
                answer_text = (
                    f"Слишком много запросов. Максимум {self.max_requests} за "
                    f"{int(self.period.total_seconds() // 60)} минут. Попробуйте позже."
                )
                if len(answer_text) > 1024:
                    answer_text = answer_text[:1020] + "..."
                    logger.warning(f"Подпись для лимита запросов обрезана до 1024 символов: {answer_text}")

                try:
                    image_path = Config.IMAGE_PATHS["main"]
                    photo = FSInputFile(path=image_path)
                    await message.answer_photo(
                        photo=photo,
                        caption=answer_text,
                        reply_markup=Keyboards.main_menu()
                    )
                    logger.debug(f"Отправлено изображение {image_path} с подписью для user_id={message.from_user.id}")
                except (KeyError, FileNotFoundError, Exception) as e:
                    logger.error(f"Ошибка отправки изображения: {str(e)}")
                    await message.answer(
                        answer_text,
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

    # Подготовка текста
    answer_text = "Отправьте голосовое сообщение, и я отвечу вам голосом!"
    if len(answer_text) > 1024:
        answer_text = answer_text[:1020] + "..."
        logger.warning(f"Подпись для команды 'voice' обрезана до 1024 символов: {answer_text}")

    # Отправляем изображение с текстом и клавиатурой
    try:
        image_path = Config.IMAGE_PATHS["voice_gpt"]
        photo = FSInputFile(path=image_path)
        await message.answer_photo(
            photo=photo,
            caption=answer_text,
            reply_markup=Keyboards.get_voice_control_keyboard()
        )
        logger.debug(f"Отправлено изображение {image_path} с подписью для user_id={message.from_user.id}")
    except KeyError:
        logger.warning("Изображение для команды 'voice_gpt' не найдено")
        await message.answer(
            answer_text,
            reply_markup=Keyboards.get_voice_control_keyboard()
        )
    except FileNotFoundError:
        logger.error(f"Файл изображения {image_path} не найден")
        await message.answer(
            answer_text,
            reply_markup=Keyboards.get_voice_control_keyboard()
        )
    except Exception as e:
        logger.error(f"Ошибка обработки команды /voice: {str(e)}")
        answer_text = "Ошибка обработки команды. Попробуйте позже."
        if len(answer_text) > 1024:
            answer_text = answer_text[:1020] + "..."
            logger.warning(f"Подпись для ошибки команды обрезана до 1024 символов: {answer_text}")
        try:
            image_path = Config.IMAGE_PATHS["main"]
            photo = FSInputFile(path=image_path)
            await message.answer_photo(
                photo=photo,
                caption=answer_text,
                reply_markup=Keyboards.main_menu()
            )
            logger.debug(f"Отправлено изображение {image_path} с подписью для user_id={message.from_user.id}")
        except (KeyError, FileNotFoundError, Exception) as e:
            logger.error(f"Ошибка отправки изображения: {str(e)}")
            await message.answer(
                answer_text,
                reply_markup=Keyboards.main_menu()
            )
        return

    await state.set_state(VoiceState.waiting_for_voice)
    logger.debug(f"Установлено состояние VoiceState.waiting_for_voice для user_id={message.from_user.id}")

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
            answer_text = f"Сообщение слишком длинное (максимум {MAX_VOICE_DURATION} сек)."
            if len(answer_text) > 1024:
                answer_text = answer_text[:1020] + "..."
                logger.warning(f"Подпись для длинного сообщения обрезана до 1024 символов: {answer_text}")
            try:
                image_path = Config.IMAGE_PATHS["voice_gpt"]
                photo = FSInputFile(path=image_path)
                await message.answer_photo(
                    photo=photo,
                    caption=answer_text,
                    reply_markup=Keyboards.get_voice_control_keyboard()
                )
                logger.debug(f"Отправлено изображение {image_path} с подписью для user_id={message.from_user.id}")
            except (KeyError, FileNotFoundError, Exception) as e:
                logger.error(f"Ошибка отправки изображения: {str(e)}")
                await message.answer(
                    answer_text,
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
            answer_text = "Не удалось обработать голосовое сообщение. Попробуйте снова."
            if len(answer_text) > 1024:
                answer_text = answer_text[:1020] + "..."
                logger.warning(f"Подпись для ошибки файла обрезана до 1024 символов: {answer_text}")
            try:
                image_path = Config.IMAGE_PATHS["voice_gpt"]
                photo = FSInputFile(path=image_path)
                await message.answer_photo(
                    photo=photo,
                    caption=answer_text,
                    reply_markup=Keyboards.get_voice_control_keyboard()
                )
                logger.debug(f"Отправлено изображение {image_path} с подписью для user_id={message.from_user.id}")
            except (KeyError, FileNotFoundError, Exception) as e:
                logger.error(f"Ошибка отправки изображения: {str(e)}")
                await message.answer(
                    answer_text,
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
            answer_text = "Не удалось распознать речь. Попробуйте говорить четче."
            if len(answer_text) > 1024:
                answer_text = answer_text[:1020] + "..."
                logger.warning(f"Подпись для ошибки распознавания обрезана до 1024 символов: {answer_text}")
            try:
                image_path = Config.IMAGE_PATHS["voice_gpt"]
                photo = FSInputFile(path=image_path)
                await message.answer_photo(
                    photo=photo,
                    caption=answer_text,
                    reply_markup=Keyboards.get_voice_control_keyboard()
                )
                logger.debug(f"Отправлено изображение {image_path} с подписью для user_id={message.from_user.id}")
            except (KeyError, FileNotFoundError, Exception) as e:
                logger.error(f"Ошибка отправки изображения: {str(e)}")
                await message.answer(
                    answer_text,
                    reply_markup=Keyboards.get_voice_control_keyboard()
                )
            return

        logger.debug(f"Распознанный текст: {text}")
        answer_text = f"Вы сказали: {text}"
        if len(answer_text) > 1024:
            answer_text = answer_text[:1020] + "..."
            logger.warning(f"Подпись для распознанного текста обрезана до 1024 символов: {answer_text}")
        try:
            image_path = Config.IMAGE_PATHS["voice_gpt"]
            photo = FSInputFile(path=image_path)
            await message.answer_photo(
                photo=photo,
                caption=answer_text,
                reply_markup=Keyboards.get_voice_control_keyboard()
            )
            logger.debug(f"Отправлено изображение {image_path} с подписью для user_id={message.from_user.id}")
        except (KeyError, FileNotFoundError, Exception) as e:
            logger.error(f"Ошибка отправки изображения: {str(e)}")
            await message.answer(
                answer_text,
                reply_markup=Keyboards.get_voice_control_keyboard()
            )

        # Получение ответа от ChatGPT
        response = await retry_on_failure(get_chatgpt_response, text)
        if not response:
            logger.error("Не удалось получить ответ от ChatGPT")
            answer_text = "Ошибка получения ответа. Попробуйте снова."
            if len(answer_text) > 1024:
                answer_text = answer_text[:1020] + "..."
                logger.warning(f"Подпись для ошибки ChatGPT обрезана до 1024 символов: {answer_text}")
            try:
                image_path = Config.IMAGE_PATHS["voice_gpt"]
                photo = FSInputFile(path=image_path)
                await message.answer_photo(
                    photo=photo,
                    caption=answer_text,
                    reply_markup=Keyboards.get_voice_control_keyboard()
                )
                logger.debug(f"Отправлено изображение {image_path} с подписью для user_id={message.from_user.id}")
            except (KeyError, FileNotFoundError, Exception) as e:
                logger.error(f"Ошибка отправки изображения: {str(e)}")
                await message.answer(
                    answer_text,
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
            answer_text = f"Ошибка генерации голосового ответа. Вот текстовый ответ:\n\n{response}"
            if len(answer_text) > 1024:
                answer_text = answer_text[:1020] + "..."
                logger.warning(f"Подпись для текстового ответа обрезана до 1024 символов: {answer_text}")
            try:
                image_path = Config.IMAGE_PATHS["voice_gpt"]
                photo = FSInputFile(path=image_path)
                await message.answer_photo(
                    photo=photo,
                    caption=answer_text,
                    reply_markup=Keyboards.get_voice_control_keyboard()
                )
                logger.debug(f"Отправлено изображение {image_path} с подписью для user_id={message.from_user.id}")
            except (KeyError, FileNotFoundError, Exception) as e:
                logger.error(f"Ошибка отправки изображения: {str(e)}")
                await message.answer(
                    answer_text,
                    reply_markup=Keyboards.get_voice_control_keyboard()
                )

    except ValueError as e:
        logger.warning(f"Ошибка значения: {str(e)}")
        answer_text = str(e)
        if len(answer_text) > 1024:
            answer_text = answer_text[:1020] + "..."
            logger.warning(f"Подпись для ошибки значения обрезана до 1024 символов: {answer_text}")
        try:
            image_path = Config.IMAGE_PATHS["voice_gpt"]
            photo = FSInputFile(path=image_path)
            await message.answer_photo(
                photo=photo,
                caption=answer_text,
                reply_markup=Keyboards.get_voice_control_keyboard()
            )
            logger.debug(f"Отправлено изображение {image_path} с подписью для user_id={message.from_user.id}")
        except (KeyError, FileNotFoundError, Exception) as e:
            logger.error(f"Ошибка отправки изображения: {str(e)}")
            await message.answer(
                answer_text,
                reply_markup=Keyboards.get_voice_control_keyboard()
            )
    except TelegramAPIError as e:
        logger.warning(f"Ошибка Telegram API: {str(e)}")
        answer_text = "Слишком много запросов. Подождите немного."
        if len(answer_text) > 1024:
            answer_text = answer_text[:1020] + "..."
            logger.warning(f"Подпись для ошибки API обрезана до 1024 символов: {answer_text}")
        try:
            image_path = Config.IMAGE_PATHS["main"]
            photo = FSInputFile(path=image_path)
            await message.answer_photo(
                photo=photo,
                caption=answer_text,
                reply_markup=Keyboards.main_menu()
            )
            logger.debug(f"Отправлено изображение {image_path} с подписью для user_id={message.from_user.id}")
        except (KeyError, FileNotFoundError, Exception) as e:
            logger.error(f"Ошибка отправки изображения: {str(e)}")
            await message.answer(
                answer_text,
                reply_markup=Keyboards.main_menu()
            )
    except Exception as e:
        logger.error(f"Необработанная ошибка в handle_voice_message: {str(e)}")
        answer_text = "Произошла ошибка. Попробуйте позже."
        if len(answer_text) > 1024:
            answer_text = answer_text[:1020] + "..."
            logger.warning(f"Подпись для необработанной ошибки обрезана до 1024 символов: {answer_text}")
        try:
            image_path = Config.IMAGE_PATHS["voice_gpt"]
            photo = FSInputFile(path=image_path)
            await message.answer_photo(
                photo=photo,
                caption=answer_text,
                reply_markup=Keyboards.get_voice_control_keyboard()
            )
            logger.debug(f"Отправлено изображение {image_path} с подписью для user_id={message.from_user.id}")
        except (KeyError, FileNotFoundError, Exception) as e:
            logger.error(f"Ошибка отправки изображения: {str(e)}")
            await message.answer(
                answer_text,
                reply_markup=Keyboards.get_voice_control_keyboard()
            )

@voice_router.callback_query(F.data == CallbackData.END_VOICE.value)
async def return_to_main_menu(callback: CallbackQuery, state: FSMContext):
    """
    Обработчик для возврата в главное меню.

    Args:
        callback: Объект callback-запроса от кнопки
        state: Контекст состояния FSM
    """
    logger.debug(f"Пользователь {callback.from_user.id} вернулся в главное меню")

    # Подготовка текста
    try:
        await callback_finality(callback)
        logger.debug(f"Выполнена callback_finality для user_id={callback.from_user.id}")
    except Exception as e:
        logger.error(f"Ошибка в callback_finality: {str(e)}")

    await state.clear()
    await callback.answer()

@voice_router.callback_query()
async def catch_all_callbacks(callback: CallbackQuery, state: FSMContext):
    """
    Универсальный хендлер для необработанных callback-запросов.
    """
    current_state = await state.get_state()
    logger.warning(
        f"Необработанный callback в voice_gpt: user={callback.from_user.id}, "
        f"data={callback.data}, state={current_state}"
    )

    # Отправляем изображение с текстом и главным меню
    try:
        await callback_finality(callback)
        logger.debug(f"Выполнена callback_finality для user_id={callback.from_user.id}")
    except Exception as e:
        logger.error(f"Ошибка в callback_finality: {str(e)}")

    await state.clear()
    logger.debug(f"Сброшено состояние для user_id={callback.from_user.id}")
    await callback.answer()