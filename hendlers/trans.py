"""
Модуль для работы с переводчиком в Telegram-боте.

Основные функции:
- Активация переводчика по команде /translate или упоминанию "translate"
- Выбор языка перевода через клавиатуру
- Перевод текста на выбранный язык с использованием ChatGPT API
- Использование Finite State Machine (FSM) для управления состоянием
- Предоставление клавиатуры для смены языка или завершения

"""
import logging
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from keybords import Keyboards, CallbackData
from utils.images import send_image
from utils.chatgpt import get_chatgpt_response
from config import Config

# Настройка логирования
logger = logging.getLogger(__name__)

# Создаем роутер для обработки сообщений, связанных с переводчиком
trans_router = Router()

class TranslateState(StatesGroup):
    """
    Класс состояний Finite State Machine (FSM) для управления переводчиком.

    Состояния:
        selecting_language: Состояние выбора языка перевода
        translating: Состояние перевода текста
    """
    selecting_language = State()
    translating = State()


@trans_router.message(F.text.lower().contains("translate"))
async def handle_translate(message: Message, state: FSMContext):
    """
    Обработчик команды запуска переводчика.

    Активируется по команде /translate или при упоминании "translate" в тексте.

    Args:
        message: Объект сообщения от пользователя
        state: Контекст состояния FSM

    Действия:
        1. Отправляет тематическое изображение
        2. Приглашает пользователя выбрать язык
        3. Устанавливает состояние выбора языка
    """
    logger.debug(f"Пользователь {message.from_user.id} запустил переводчик")
    try:
        # Отправляем тематическое изображение
        await send_image(message, Config.IMAGE_PATHS["translate"])
    except KeyError:
        logger.warning("Изображение для команды 'translate' не найдено")

    # Получаем приветственное сообщение
    answer_text = Config.get_messages('translate') or "Выберите язык для перевода:"
    keyboard = Keyboards.get_languages_keyboard()
    if keyboard is None:
        logger.warning("Клавиатура языков не создана")
        await message.answer("Языки не настроены. Обратитесь к администратору.")
        return

    await message.answer(
        answer_text,
        reply_markup=keyboard
    )
    await state.set_state(TranslateState.selecting_language)
    logger.debug(f"Установлено состояние TranslateState.selecting_language для пользователя {message.from_user.id}")

@trans_router.callback_query(TranslateState.selecting_language, F.data.startswith(CallbackData.LANG_PREFIX))
async def handle_language(callback: CallbackQuery, state: FSMContext):
    """
    Обработчик выбора языка перевода.

    Args:
        callback: Объект callback-запроса от кнопки
        state: Контекст состояния FSM

    Действия:
        1. Извлекает и сохраняет выбранный язык
        2. Приглашает пользователя отправить текст для перевода
        3. Устанавливает состояние перевода
    """
    logger.debug(f"Callback data: {callback.data}")
    language = callback.data[len(CallbackData.LANG_PREFIX):]
    available_languages = [str(lang) for lang in Config.LANGUAGES.values()]
    logger.debug(f"Проверка языка: {language}, доступные языки: {available_languages}")
    if language not in available_languages:
        logger.warning(f"Недопустимый язык: {language}")
        await callback.message.answer(
            f"Язык {language} недоступен. Доступные языки: {', '.join(Config.LANGUAGES.keys())}.",
            reply_markup=Keyboards.get_languages_keyboard()
        )
        await callback.answer()
        return

    logger.debug(f"Пользователь {callback.from_user.id} выбрал язык: {language}")
    await state.update_data(selected_language=language)
    await callback.message.answer(
        f"Выбран язык: {language}. Отправьте текст для перевода:",
        reply_markup=Keyboards.get_translator_control_keyboard()
    )
    await state.set_state(TranslateState.translating)
    logger.debug(f"Установлено состояние TranslateState.translating для пользователя {callback.from_user.id}")
    await callback.answer()

@trans_router.callback_query(F.data == CallbackData.CHANGE_LANG)
async def handle_change_language(callback: CallbackQuery, state: FSMContext):
    """
    Обработчик запроса на смену языка перевода.

    Args:
        callback: Объект callback-запроса от кнопки
        state: Контекст состояния FSM

    Действия:
        1. Показывает клавиатуру выбора языков
        2. Устанавливает состояние выбора языка
    """
    logger.debug(f"Пользователь {callback.from_user.id} запросил смену языка")
    await callback.message.answer(
        "Выберите язык для перевода:",
        reply_markup=Keyboards.get_languages_keyboard()
    )
    await state.set_state(TranslateState.selecting_language)
    logger.debug(f"Установлено состояние TranslateState.selecting_language для пользователя {callback.from_user.id}")
    await callback.answer()

@trans_router.message(TranslateState.translating)
async def handle_translation(message: Message, state: FSMContext):
    """
    Обработчик текста для перевода.

    Args:
        message: Объект сообщения с текстом для перевода
        state: Контекст состояния FSM

    Действия:
        1. Получает выбранный язык из состояния
        2. Отправляет запрос на перевод к ChatGPT
        3. Отправляет переведенный текст пользователю
    """
    user_data = await state.get_data()
    language = user_data.get('selected_language')
    if not language:
        logger.error(f"Язык не выбран для пользователя {message.from_user.id}")
        await message.answer(
            "Язык не выбран. Пожалуйста, выберите язык с помощью /translate.",
            reply_markup=Keyboards.get_languages_keyboard()
        )
        await state.set_state(TranslateState.selecting_language)
        return

    logger.debug(f"Пользователь {message.from_user.id} отправил текст для перевода на {language}: {message.text}")
    prompt = f"Переведи следующий текст на {language}:\n\n{message.text}"
    try:
        translation = await get_chatgpt_response(prompt)
        logger.debug(f"Получен перевод: {translation}")
    except Exception as e:
        logger.error(f"Ошибка получения перевода: {str(e)}")
        await message.answer(
            "Не удалось выполнить перевод. Попробуйте снова.",
            reply_markup=Keyboards.get_translator_control_keyboard()
        )
        return

    await message.answer(
        f"Перевод ({language}):\n\n{translation}",
        reply_markup=Keyboards.get_translator_control_keyboard()
    )

@trans_router.callback_query(F.data == CallbackData.END_TRANS)
async def return_to_main_menu(callback: CallbackQuery, state: FSMContext):
    """
    Обработчик завершения работы с переводчиком.

    Args:
        callback: Объект callback-запроса от кнопки
        state: Контекст состояния FSM

    Действия:
        1. Очищает состояние FSM
        2. Отправляет сообщение о завершении
        3. Показывает главное меню
    """
    logger.debug(f"Пользователь {callback.from_user.id} завершил работу с переводчиком")
    await state.clear()
    await callback.message.answer(
        "Переводчик завершён. Начните заново с /translate или вернитесь в меню с /start.",
        reply_markup=Keyboards.main_menu()
    )
    await callback.answer()
