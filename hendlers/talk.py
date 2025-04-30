'''
Модуль обработки диалогов с ИИ-персонажами

Этот модуль предоставляет функционал для:
    - Старта диалога с выбором персонажа
    - Обработки выбора персонажа
    - Ведения диалога с выбранным персонажом через ChatGPT
    - Отправки соответствующих изображений персонажей
'''
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from keybords import Keyboards
from utils.chatgpt import get_chatgpt_response
from utils.images import send_image
from config import Config

# Создаем роутер для обработки диалогов
talk_router = Router()


@talk_router.message(F.text.lower().contains("talk"))
async def handle_talk(message: Message):
    """
    Обрабатывает команду начала диалога (сообщение, содержащее 'talk').

    Действия:
    1. Отправляет изображение для команды talk
    2. Предлагает выбрать персонажа через клавиатуру

    Args:
        message (Message): Входящее сообщение от пользователя
    """
    # Отправляем изображение, связанное с командой talk
    await send_image(message, Config.IMAGE_PATHS["talk"])

    # Отправляем сообщение с клавиатурой для выбора персонажа
    await message.answer(
        "Выберите личность:",
        reply_markup=Keyboards.get_personalities_keyboard()
    )


@talk_router.callback_query(F.data.startswith("talk_"))
async def handle_person(callback: CallbackQuery):
    """
    Обрабатывает выбор персонажа из клавиатуры.

    Действия:
    1. Извлекает выбранного персонажа из callback данных
    2. Сохраняет промт персонажа в сессию пользователя
    3. Отправляет изображение персонажа
    4. Сообщает о начале диалога с выбранным персонажем

    Args:
        callback (CallbackQuery): Колбэк от нажатия кнопки выбора персонажа
    """
    # Извлекаем имя персонажа из callback данных (формат "talk_[person]")
    person = callback.data.split("_")[1]

    # Сохраняем промт персонажа в сессию пользователя
    Config.USER_SESSIONS[callback.from_user.id] = {
        "person": Config.get_prompts(callback.data)
    }

    # Отправляем изображение выбранного персонажа
    await send_image(callback.message, Config.IMAGE_PATHS[person])

    # Отправляем сообщение о начале диалога с кнопкой возврата
    await callback.message.answer(
        f"Вы говорите с {Config.PERSONS[person].upper()}. Отправьте сообщение:",
        reply_markup=Keyboards.return_talk_keyboard()
    )

    # Подтверждаем обработку callback
    await callback.answer()


@talk_router.message(lambda message: message.from_user.id in Config.USER_SESSIONS)
async def handle_talk_message(message: Message):
    """
    Обрабатывает сообщения пользователя в режиме диалога с персонажем.

    Действия:
    1. Формирует промт для ChatGPT (промт персонажа + сообщение пользователя)
    2. Получает ответ от ChatGPT
    3. Отправляет ответ пользователю

    Args:
        message (Message): Входящее сообщение от пользователя в режиме диалога
    """
    # Формируем промт: берем сохраненный промт персонажа и добавляем сообщение пользователя
    prompt = Config.USER_SESSIONS[message.from_user.id]["person"] + "\n\n" + message.text

    # Получаем ответ от ChatGPT
    response = await get_chatgpt_response(prompt)

    # Отправляем ответ пользователю с клавиатурой для возврата
    await message.answer(
        response,
        reply_markup=Keyboards.return_talk_keyboard(),
    )