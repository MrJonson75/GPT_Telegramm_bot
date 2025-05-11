"""
Модуль обработки диалогов с ИИ-персонажами

Этот модуль предоставляет функционал для:
    - Старта диалога с выбором персонажа
    - Обработки выбора персонажа
    - Ведения диалога с выбранным персонажем через ChatGPT
    - Отправки соответствующих изображений персонажей
"""
import logging
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from keybords import Keyboards, CallbackData
from utils.chatgpt import get_chatgpt_response
from utils.images import send_image
from config import Config

# Настройка логирования
logger = logging.getLogger(__name__)

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
        message: Объект сообщения от пользователя
    """
    logger.debug(f"Пользователь {message.from_user.id} начал диалог")

    # Отправляем изображение, связанное с командой talk
    try:
        await send_image(message, Config.IMAGE_PATHS["talk"])
    except KeyError:
        logger.warning("Изображение для команды 'talk' не найдено")

    answer_text = Config.get_messages('talk') or "Выберите личность для диалога:"

    # Проверяем, доступна ли клавиатура личностей
    keyboard = Keyboards.get_personalities_keyboard()
    if keyboard is None:
        logger.warning("Config.PERSONS пуст, клавиатура личностей не создана")
        await message.answer("Личности не настроены. Обратитесь к администратору.")
        return

    # Отправляем сообщение с клавиатурой для выбора персонажа
    await message.answer(
        answer_text,
        reply_markup=keyboard
    )

@talk_router.callback_query(F.data.startswith(CallbackData.TALK_PREFIX.value))
async def handle_person(callback: CallbackQuery):
    """
    Обрабатывает выбор персонажа из клавиатуры.

    Действия:
    1. Извлекает выбранного персонажа из callback данных
    2. Сохраняет промт персонажа в сессию пользователя
    3. Отправляет изображение персонажа
    4. Сообщает о начале диалога с выбранным персонажем

    Args:
        callback: Объект callback от нажатия кнопки выбора персонажа
    """
    logger.debug(f"Получен callback: user={callback.from_user.id}, data={callback.data}")

    # Извлекаем person_id из callback_data (формат "talk_person_id")
    try:
        person_id = callback.data[len(CallbackData.TALK_PREFIX.value):]
    except IndexError:
        logger.error(f"Некорректный формат callback_data: {callback.data}")
        await callback.message.answer("Ошибка при выборе персонажа. Попробуйте снова.")
        await callback.answer()
        return

    # Проверяем, существует ли персонаж
    if person_id not in Config.PERSONS:
        logger.warning(f"Недопустимый персонаж: {person_id}")
        await callback.message.answer(
            "Этот персонаж недоступен. Выберите другого.",
            reply_markup=Keyboards.get_personalities_keyboard()
        )
        await callback.answer()
        return

    person_name = Config.PERSONS[person_id]

    # Сохраняем промт персонажа в сессию пользователя
    try:
        prompt = Config.get_prompts(f"talk_{person_id}")
        Config.USER_SESSIONS[callback.from_user.id] = {"person": prompt}
    except (FileNotFoundError, IOError) as e:
        logger.error(f"Ошибка получения промта для {person_id}: {str(e)}")
        await callback.message.answer("Ошибка при загрузке персонажа. Попробуйте другого.")
        await callback.answer()
        return

    # Отправляем изображение выбранного персонажа
    try:
        await send_image(callback.message, Config.IMAGE_PATHS[person_id])
    except KeyError:
        logger.warning(f"Изображение для персонажа {person_id} не найдено")

    # Отправляем сообщение о начале диалога с кнопкой возврата
    await callback.message.answer(
        f"Вы говорите с {person_name.upper()}. Отправьте сообщение:",
        reply_markup=Keyboards.get_talk_exit_keyboard()
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
        message: Входящее сообщение от пользователя в режиме диалога
    """
    user_id = message.from_user.id
    logger.debug(f"Пользователь {user_id} отправил сообщение в диалоге: {message.text}")

    # Проверяем, есть ли сессия
    if user_id not in Config.USER_SESSIONS:
        logger.warning(f"Сессия для пользователя {user_id} не найдена")
        await message.answer("Сессия диалога не найдена. Начните новый диалог с /talk.")
        return

    # Формируем промт: берем сохраненный промт персонажа и добавляем сообщение пользователя
    prompt = Config.USER_SESSIONS[user_id]["person"] + "\n\n" + message.text

    # Получаем ответ от ChatGPT
    try:
        response = await get_chatgpt_response(prompt)
    except Exception as e:
        logger.error(f"Ошибка получения ответа от ChatGPT: {str(e)}")
        await message.answer("Ошибка при получении ответа. Попробуйте снова.")
        return

    # Отправляем ответ пользователю с клавиатурой для возврата
    await message.answer(
        response,
        reply_markup=Keyboards.get_talk_exit_keyboard()
    )

@talk_router.callback_query(F.data == CallbackData.END_TALK.value)
async def handle_talk_exit(callback: CallbackQuery):
    """
    Обрабатывает завершение диалога.

    Действия:
    1. Удаляет сессию пользователя
    2. Отправляет сообщение о завершении диалога
    3. Показывает главное меню

    Args:
        callback: Объект callback от нажатия кнопки "Закончить"
    """
    user_id = callback.from_user.id
    logger.debug(f"Пользователь {user_id} завершил диалог")

    # Удаляем сессию пользователя
    Config.USER_SESSIONS.pop(user_id, None)

    # Отправляем сообщение о завершении диалога
    await callback.message.answer(
        "Диалог завершён. Выберите команду:\n/start - главное меню",
        reply_markup=Keyboards.main_menu()
    )

    # Подтверждаем обработку callback
    await callback.answer()

@talk_router.callback_query()
async def catch_all_callbacks(callback: CallbackQuery):
    """
    Универсальный хендлер для необработанных callback-запросов.

    Логирует необработанные callback и уведомляет пользователя.

    Args:
        callback: Объект callback от нажатия кнопки
    """
    logger.warning(
        f"Необработанный callback: user={callback.from_user.id}, "
        f"data={callback.data}"
    )
    await callback.answer("Этот запрос не поддерживается.", show_alert=True)