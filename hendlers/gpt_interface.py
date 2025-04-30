'''
                Общее описание модуля:
        Этот модуль реализует функционал взаимодействия с ChatGPT в Telegram-боте с использованием:

        1.	Finite State Machine (FSM) для управления состоянием диалога
        2.	Отдельных утилит для работы с изображениями и ChatGPT API
        3.	Кастомных клавиатур для улучшения UX

        Особенности:

        1.	Активация диалога происходит по команде /gpt или при упоминании "gpt" в тексте
        2.	Перед началом диалога отправляется тематическое изображение
        3.	После каждого ответа предлагается кнопка для завершения диалога
        4.	Используется FSM для контроля состояния диалога

'''
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from keybords import Keyboards  # Модуль с клавиатурами
from utils.images import send_image  # Утилита для отправки изображений
from config import Config  # Конфигурация приложения
from utils.chatgpt import get_chatgpt_response  # Утилита для работы с ChatGPT

# Создаем роутер для обработки сообщений, связанных с ChatGPT
gpt_router = Router()


# Класс состояний Finite State Machine (FSM) для управления диалогом
class ChatState(StatesGroup):
    """
    Состояния для управления диалогом с ChatGPT.

    Атрибуты:
        waiting_for_question: Состояние ожидания вопроса пользователя
    """
    waiting_for_question = State()


# Обработчик команды /gpt или сообщений, содержащих "gpt"
@gpt_router.message(F.text.lower().contains("gpt"))
async def handle_gpt(message: Message, state: FSMContext):
    """
    Обрабатывает команду запуска диалога с ChatGPT.

    Параметры:
        message: Объект сообщения от пользователя
        state: Контекст состояния FSM

    Действия:
        1. Отправляет тематическое изображение
        2. Приглашает пользователя задать вопрос
        3. Устанавливает состояние ожидания вопроса
    """
    # Отправляем заранее заготовленное изображение
    await send_image(message, Config.IMAGE_PATHS["gpt"])
    await message.answer("Давайте начнём диалог с ChatGPT! Задайте ваш вопрос.")
    # Переходим в состояние ожидания вопроса
    await state.set_state(ChatState.waiting_for_question)


# Обработчик текстовых сообщений в состоянии ожидания вопроса
@gpt_router.message(ChatState.waiting_for_question)
async def handle_chatgpt_question(message: Message, state: FSMContext):
    """
    Обрабатывает вопрос пользователя и возвращает ответ от ChatGPT.

    Параметры:
        message: Объект сообщения с вопросом пользователя
        state: Контекст состояния FSM

    Действия:
        1. Отправляет запрос к API ChatGPT
        2. Отправляет ответ пользователю
        3. Предлагает клавиатуру с опцией завершения диалога
    """
    # Отправляем запрос к ChatGPT
    response = await get_chatgpt_response(message.text)
    await message.answer(
        response,
        reply_markup=Keyboards.return_gpt_keyboard(),  # Клавиатура с кнопкой "Закончить"
    )


# Обработчик нажатия кнопки "Закончить" (на самом деле кнопки "start" по текущему коду)
@gpt_router.callback_query(F.data == "start")
async def end_chat(callback: CallbackQuery, state: FSMContext):
    """
    Завершает диалог с ChatGPT по запросу пользователя.

    Параметры:
        callback: Объект callback-запроса от кнопки
        state: Контекст состояния FSM

    Действия:
        1. Очищает состояние FSM
        2. Отправляет сообщение о завершении диалога
        3. Подтверждает обработку callback-запроса
    """
    await state.clear()  # Сбрасываем состояние
    await callback.message.answer("Диалог завершён. До новых встреч!")
    await callback.answer()  # Подтверждаем обработку callback