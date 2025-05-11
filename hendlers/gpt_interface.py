"""
Модуль для взаимодействия с ChatGPT в Telegram-боте.

Основные функции:
- Активация диалога по команде /gpt или упоминанию "gpt"
- Обработка вопросов пользователей через ChatGPT API
- Использование Finite State Machine (FSM) для управления диалогом
- Предоставление клавиатуры для завершения диалога
- Отправка тематических изображений для улучшения UX
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

# Создаем роутер для обработки сообщений, связанных с ChatGPT
gpt_router = Router()

class ChatState(StatesGroup):
    """
    Класс состояний Finite State Machine (FSM) для управления диалогом с ChatGPT.

    Состояния:
        waiting_for_question: Состояние ожидания вопроса пользователя
    """
    waiting_for_question = State()

@gpt_router.message(F.text.lower().contains("gpt"))
async def handle_gpt(message: Message, state: FSMContext):
    """
    Обработчик команды запуска диалога с ChatGPT.

    Активируется по команде /gpt или при упоминании "gpt" в тексте.

    Args:
        message: Объект сообщения от пользователя
        state: Контекст состояния FSM

    Действия:
        1. Отправляет тематическое изображение с приветственным текстом и клавиатурой
        2. Устанавливает состояние ожидания вопроса
    """
    logger.debug(f"Пользователь {message.from_user.id} запустил диалог с ChatGPT")

    # Получаем приветственное сообщение
    answer_text = Config.get_messages('gpt') or "Задайте свой вопрос ChatGPT:"

    # Отправляем изображение с подписью и клавиатурой
    try:
        image_path = Config.IMAGE_PATHS["gpt"]
        photo = FSInputFile(path=image_path)
        await message.answer_photo(
            photo=photo,
            caption=answer_text,
            reply_markup=Keyboards.get_gpt_exit_keyboard()
        )
        logger.debug(f"Отправлено изображение {image_path} с подписью для user_id={message.from_user.id}")
    except KeyError:
        logger.warning("Изображение для команды 'gpt' не найдено")
        await message.answer(
            answer_text,
            reply_markup=Keyboards.get_gpt_exit_keyboard()
        )
    except FileNotFoundError:
        logger.error(f"Файл изображения {image_path} не найден")
        await message.answer(
            answer_text,
            reply_markup=Keyboards.get_gpt_exit_keyboard()
        )
    except Exception as e:
        logger.error(f"Ошибка отправки изображения: {str(e)}")
        await message.answer(
            "Произошла ошибка. Попробуйте снова.",
            reply_markup=Keyboards.get_gpt_exit_keyboard()
        )
        return

    # Устанавливаем состояние ожидания вопроса
    await state.set_state(ChatState.waiting_for_question)
    logger.debug(f"Установлено состояние ChatState.waiting_for_question для пользователя {message.from_user.id}")

@gpt_router.message(ChatState.waiting_for_question)
async def handle_chatgpt_question(message: Message, state: FSMContext):
    """
    Обработчик вопросов пользователя в состоянии диалога с ChatGPT.

    Args:
        message: Объект сообщения с вопросом пользователя
        state: Контекст состояния FSM

    Действия:
        1. Отправляет запрос к ChatGPT API
        2. Отправляет изображение с ответом ChatGPT и клавиатурой
    """
    logger.debug(f"Пользователь {message.from_user.id} задал вопрос: {message.text}")

    # Отправляем запрос к ChatGPT
    try:
        response = await get_chatgpt_response(message.text)
        logger.debug(f"Получен ответ от ChatGPT: {response}")
    except Exception as e:
        logger.error(f"Ошибка получения ответа от ChatGPT: {str(e)}")
        await message.answer(
            "Не удалось получить ответ. Попробуйте снова.",
            reply_markup=Keyboards.get_gpt_exit_keyboard()
        )
        return

    # Отправляем изображение с ответом и клавиатурой
    try:
        image_path = Config.IMAGE_PATHS["gpt"]
        photo = FSInputFile(path=image_path)
        await message.answer_photo(
            photo=photo,
            caption=response,
            reply_markup=Keyboards.get_gpt_exit_keyboard()
        )
        logger.debug(f"Отправлено изображение {image_path} с ответом для user_id={message.from_user.id}")
    except KeyError:
        logger.warning("Изображение для команды 'gpt' не найдено")
        await message.answer(
            response,
            reply_markup=Keyboards.get_gpt_exit_keyboard()
        )
    except FileNotFoundError:
        logger.error(f"Файл изображения {image_path} не найден")
        await message.answer(
            response,
            reply_markup=Keyboards.get_gpt_exit_keyboard()
        )
    except Exception as e:
        logger.error(f"Ошибка отправки изображения: {str(e)}")
        await message.answer(
            "Произошла ошибка. Попробуйте снова.",
            reply_markup=Keyboards.get_gpt_exit_keyboard()
        )

@gpt_router.callback_query(F.data == CallbackData.BREAK)
async def end_chat(callback: CallbackQuery, state: FSMContext):
    """
    Обработчик завершения диалога с ChatGPT.

    Args:
        callback: Объект callback-запроса от кнопки
        state: Контекст состояния FSM

    Действия:
        1. Очищает состояние FSM
        2. Отправляет изображение с сообщением о завершении и главным меню
        3. Подтверждает обработку callback
    """

    logger.debug(f"Пользователь {callback.from_user.id} завершил диалог с ChatGPT")
    await state.clear()


    # Отправляем изображение с подписью и главным меню
    try:
        await callback_finality(callback)
        logger.debug(f"Выполнена callback_finality для user_id={callback.from_user.id}")
    except Exception as e:
        logger.error(f"Ошибка в callback_finality: {str(e)}")
    await callback.answer()
