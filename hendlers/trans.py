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
from aiogram.types import Message, CallbackQuery, FSInputFile
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from keybords import Keyboards, CallbackData
from utils.chatgpt import get_chatgpt_response
from config import Config
from utils.callback_finality import callback_finality

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
        1. Отправляет изображение с текстом и клавиатурой выбора языка
        2. Устанавливает состояние выбора языка
    """
    logger.debug(f"Пользователь {message.from_user.id} запустил переводчик")

    # Подготовка текста
    answer_text = Config.get_messages('translate') or "Выберите язык для перевода:"
    # Обрезаем подпись, если она слишком длинная
    if len(answer_text) > 1024:
        answer_text = answer_text[:1020] + "..."
        logger.warning(f"Подпись для команды 'translate' обрезана до 1024 символов: {answer_text}")

    keyboard = Keyboards.get_languages_keyboard()
    if keyboard is None:
        logger.warning("Клавиатура языков не создана")
        await message.answer("Языки не настроены. Обратитесь к администратору.")
        return

    # Отправляем изображение с текстом и клавиатурой
    try:
        image_path = Config.IMAGE_PATHS["translate"]
        photo = FSInputFile(path=image_path)
        await message.answer_photo(
            photo=photo,
            caption=answer_text,
            reply_markup=keyboard
        )
        logger.debug(f"Отправлено изображение {image_path} с подписью для user_id={message.from_user.id}")
    except KeyError:
        logger.warning("Изображение для команды 'translate' не найдено")
        await message.answer(
            answer_text,
            reply_markup=keyboard
        )
    except FileNotFoundError:
        logger.error(f"Файл изображения {image_path} не найден")
        await message.answer(
            answer_text,
            reply_markup=keyboard
        )
    except Exception as e:
        logger.error(f"Ошибка отправки изображения: {str(e)}")
        await message.answer(
            "Произошла ошибка. Попробуйте снова.",
            reply_markup=keyboard
        )

    await state.set_state(TranslateState.selecting_language)
    logger.debug(f"Установлено состояние TranslateState.selecting_language для пользователя {message.from_user.id}")

@trans_router.callback_query(TranslateState.selecting_language, F.data.startswith(CallbackData.LANG_PREFIX.value))
async def handle_language(callback: CallbackQuery, state: FSMContext):
    """
    Обработчик выбора языка перевода.

    Args:
        callback: Объект callback-запроса от кнопки
        state: Контекст состояния FSM

    Действия:
        1. Извлекает и сохраняет выбранный язык
        2. Отправляет изображение с приглашением ввести текст
        3. Устанавливает состояние перевода
    """
    logger.debug(f"Callback data: {callback.data}")
    language = callback.data[len(CallbackData.LANG_PREFIX.value):]
    out_language = ''.join([key for key, value in Config.LANGUAGES.items() if str(value) == language])
    available_languages = [str(lang) for lang in Config.LANGUAGES.values()]
    logger.debug(f"Проверка языка: {language}, доступные языки: {available_languages}")
    if language not in available_languages:
        logger.warning(f"Недопустимый язык: {language}")

        # Подготовка текста для ошибки
        answer_text = f"Язык {language} недоступен. Доступные языки: {', '.join(Config.LANGUAGES.keys())}."
        if len(answer_text) > 1024:
            answer_text = answer_text[:1020] + "..."
            logger.warning(f"Подпись для ошибки языка обрезана до 1024 символов: {answer_text}")

        try:
            image_path = Config.IMAGE_PATHS["translate"]
            photo = FSInputFile(path=image_path)
            await callback.message.answer_photo(
                photo=photo,
                caption=answer_text,
                reply_markup=Keyboards.get_languages_keyboard()
            )
        except (KeyError, FileNotFoundError, Exception) as e:
            logger.error(f"Ошибка отправки изображения: {str(e)}")
            await callback.message.answer(
                answer_text,
                reply_markup=Keyboards.get_languages_keyboard()
            )
        await callback.answer()
        return

    logger.debug(f"Пользователь {callback.from_user.id} выбрал язык: {language}")
    await state.update_data(selected_language=language)

    # Подготовка текста
    answer_text = f"Выбран язык: {out_language}. Отправьте текст для перевода:"
    if len(answer_text) > 1024:
        answer_text = answer_text[:1020] + "..."
        logger.warning(f"Подпись для выбора языка обрезана до 1024 символов: {answer_text}")

    # Отправляем изображение с текстом и клавиатурой
    try:
        image_path = Config.IMAGE_PATHS["translate"]
        photo = FSInputFile(path=image_path)
        await callback.message.answer_photo(
            photo=photo,
            caption=answer_text,
            reply_markup=Keyboards.get_translator_control_keyboard()
        )
        logger.debug(f"Отправлено изображение {image_path} с подписью для user_id={callback.from_user.id}")
    except KeyError:
        logger.warning("Изображение для команды 'translate' не найдено")
        await callback.message.answer(
            answer_text,
            reply_markup=Keyboards.get_translator_control_keyboard()
        )
    except FileNotFoundError:
        logger.error(f"Файл изображения {image_path} не найден")
        await callback.message.answer(
            answer_text,
            reply_markup=Keyboards.get_translator_control_keyboard()
        )
    except Exception as e:
        logger.error(f"Ошибка отправки изображения: {str(e)}")
        await callback.message.answer(
            "Произошла ошибка. Попробуйте снова.",
            reply_markup=Keyboards.get_translator_control_keyboard()
        )

    await state.set_state(TranslateState.translating)
    logger.debug(f"Установлено состояние TranslateState.translating для пользователя {callback.from_user.id}")
    await callback.answer()

@trans_router.callback_query(F.data == CallbackData.CHANGE_LANG.value)
async def handle_change_language(callback: CallbackQuery, state: FSMContext):
    """
    Обработчик запроса на смену языка перевода.

    Args:
        callback: Объект callback-запроса от кнопки
        state: Контекст состояния FSM

    Действия:
        1. Отправляет изображение с клавиатурой выбора языков
        2. Устанавливает состояние выбора языка
    """
    logger.debug(f"Пользователь {callback.from_user.id} запросил смену языка")

    # Подготовка текста
    answer_text = "Выберите язык для перевода:"
    if len(answer_text) > 1024:
        answer_text = answer_text[:1020] + "..."
        logger.warning(f"Подпись для смены языка обрезана до 1024 символов: {answer_text}")

    # Отправляем изображение с текстом и клавиатурой
    try:
        image_path = Config.IMAGE_PATHS["translate"]
        photo = FSInputFile(path=image_path)
        await callback.message.answer_photo(
            photo=photo,
            caption=answer_text,
            reply_markup=Keyboards.get_languages_keyboard()
        )
        logger.debug(f"Отправлено изображение {image_path} с подписью для user_id={callback.from_user.id}")
    except KeyError:
        logger.warning("Изображение для команды 'translate' не найдено")
        await callback.message.answer(
            answer_text,
            reply_markup=Keyboards.get_languages_keyboard()
        )
    except FileNotFoundError:
        logger.error(f"Файл изображения {image_path} не найден")
        await callback.message.answer(
            answer_text,
            reply_markup=Keyboards.get_languages_keyboard()
        )
    except Exception as e:
        logger.error(f"Ошибка отправки изображения: {str(e)}")
        await callback.message.answer(
            "Произошла ошибка. Попробуйте снова.",
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
        3. Отправляет изображение с переведенным текстом
    """
    user_data = await state.get_data()
    language = user_data.get('selected_language')
    if not language:
        logger.error(f"Язык не выбран для пользователя {message.from_user.id}")

        # Подготовка текста
        answer_text = "Язык не выбран. Пожалуйста, выберите язык с помощью /translate."
        if len(answer_text) > 1024:
            answer_text = answer_text[:1020] + "..."
            logger.warning(f"Подпись для ошибки языка обрезана до 1024 символов: {answer_text}")

        try:
            image_path = Config.IMAGE_PATHS["translate"]
            photo = FSInputFile(path=image_path)
            await message.answer_photo(
                photo=photo,
                caption=answer_text,
                reply_markup=Keyboards.get_languages_keyboard()
            )
        except (KeyError, FileNotFoundError, Exception) as e:
            logger.error(f"Ошибка отправки изображения: {str(e)}")
            await message.answer(
                answer_text,
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

        # Подготовка текста
        answer_text = "Не удалось выполнить перевод. Попробуйте снова."
        if len(answer_text) > 1024:
            answer_text = answer_text[:1020] + "..."
            logger.warning(f"Подпись для ошибки перевода обрезана до 1024 символов: {answer_text}")

        try:
            image_path = Config.IMAGE_PATHS["translate"]
            photo = FSInputFile(path=image_path)
            await message.answer_photo(
                photo=photo,
                caption=answer_text,
                reply_markup=Keyboards.get_translator_control_keyboard()
            )
        except (KeyError, FileNotFoundError, Exception) as e:
            logger.error(f"Ошибка отправки изображения: {str(e)}")
            await message.answer(
                answer_text,
                reply_markup=Keyboards.get_translator_control_keyboard()
            )
        return

    # Подготовка текста
    out_language = ''.join([key for key, value in Config.LANGUAGES.items() if str(value) == language])
    answer_text = f"Перевод ({out_language}):\n\n{translation}"
    if len(answer_text) > 1024:
        answer_text = answer_text[:1020] + "..."
        logger.warning(f"Подпись для перевода обрезана до 1024 символов: {answer_text}")

    # Отправляем изображение с переводом и клавиатурой
    try:
        image_path = Config.IMAGE_PATHS["translate"]
        photo = FSInputFile(path=image_path)
        await message.answer_photo(
            photo=photo,
            caption=answer_text,
            reply_markup=Keyboards.get_translator_control_keyboard()
        )
        logger.debug(f"Отправлено изображение {image_path} с переводом для user_id={message.from_user.id}")
    except KeyError:
        logger.warning("Изображение для команды 'translate' не найдено")
        await message.answer(
            answer_text,
            reply_markup=Keyboards.get_translator_control_keyboard()
        )
    except FileNotFoundError:
        logger.error(f"Файл изображения {image_path} не найден")
        await message.answer(
            answer_text,
            reply_markup=Keyboards.get_translator_control_keyboard()
        )
    except Exception as e:
        logger.error(f"Ошибка отправки изображения: {str(e)}")
        await message.answer(
            "Произошла ошибка. Попробуйте снова.",
            reply_markup=Keyboards.get_translator_control_keyboard()
        )

@trans_router.callback_query(F.data == CallbackData.END_TRANS.value)
async def return_to_main_menu(callback: CallbackQuery, state: FSMContext):
    """
    Обработчик завершения работы с переводчиком.

    Действия:
        1. Очищает состояние FSM
        2. Отправляет изображение с сообщением о завершении
        3. Показывает главное меню
    """
    logger.debug(f"Пользователь {callback.from_user.id} завершил работу с переводчиком")

    try:
        await callback_finality(callback)
        logger.debug(f"Выполнена callback_finality для user_id={callback.from_user.id}")
    except Exception as e:
        logger.error(f"Ошибка в callback_finality: {str(e)}")

    # Отправляем изображение с текстом и главным меню

    await state.clear()
    await callback.answer()