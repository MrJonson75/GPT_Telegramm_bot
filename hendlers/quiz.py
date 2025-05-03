"""
        Этот модуль реализует логику интерактивного квиза с использованием FSM (Finite State Machine)
        из библиотеки aiogram. Квиз поддерживает несколько тем, подсчёт очков и возможность
        продолжить или сменить тему после каждого вопроса.


        Функции:

            cmd_quiz: инициализация квиза

            process_topic_selection: обработка выбора темы

            process_user_answer: проверка ответа пользователя

            next_question: получение следующего вопроса

            change_topic: смена темы квиза

            end_quiz: завершение квиза
"""
from aiogram.fsm.state import StatesGroup, State
from aiogram import Router, types, F
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from config import Config
from utils.images import send_image
from utils.chatgpt import get_quiz_question, check_answer
from keybords import Keyboards


class QuizStates(StatesGroup):
    """
    Класс для определения состояний FSM (Finite State Machine) для квиза.

    Состояния:
    - selecting_topic: состояние выбора темы квиза
    - answering_question: состояние ответа на вопрос квиза
    """
    selecting_topic = State()
    answering_question = State()


# Создаем роутер для обработки команд и сообщений, связанных с квизом
quiz_router = Router()


@quiz_router.message(F.text.lower().contains("quiz"))
async def cmd_quiz(message: Message, state: FSMContext):
    """
    Обработчик команды начала квиза.

    Активируется, когда пользователь отправляет сообщение, содержащее "quiz".
    Устанавливает начальное состояние и счёт, отправляет изображение и приветственное сообщение.

    Args:
        message: Объект сообщения от пользователя
        state: Текущее состояние FSM
    """
    await state.set_state(QuizStates.selecting_topic)
    await state.update_data(score=0)  # Инициализируем счёт

    # Отправляем изображение из пути, указанного в конфиге
    await send_image(message, Config.IMAGE_PATHS["quiz"])
    answer_text = Config.get_messages('quiz')
    await message.answer(
        answer_text,
        reply_markup=Keyboards.get_topics_keyboard()  # Предлагаем выбрать тему
    )


@quiz_router.callback_query(QuizStates.selecting_topic, F.data.in_(["quiz_prog", "quiz_math", "quiz_biology"]))
async def process_topic_selection(callback: types.CallbackQuery, state: FSMContext):
    """
    Обработчик выбора темы квиза.

    Получает вопрос по выбранной теме и переводит пользователя в состояние ответа.

    Args:
        callback: Объект callback от нажатия кнопки
        state: Текущее состояние FSM
    """
    topic = callback.data
    question = await get_quiz_question(topic)  # Получаем вопрос по теме

    await state.set_state(QuizStates.answering_question)
    await state.update_data(
        current_topic=topic,  # Сохраняем текущую тему
        current_question=question,  # Текущий вопрос
        previous_question=question  # Предыдущий вопрос (для избежания повторов)
    )

    await callback.message.answer(f"Вопрос: {question}\n\nНапиши свой ответ:")


@quiz_router.message(QuizStates.answering_question)
async def process_user_answer(message: types.Message, state: FSMContext):
    """
    Обработчик ответа пользователя на вопрос квиза.

    Проверяет ответ, обновляет счёт и показывает результат.

    Args:
        message: Объект сообщения с ответом пользователя
        state: Текущее состояние FSM
    """
    user_data = await state.get_data()
    question = user_data['current_question']
    user_answer = message.text

    result = await check_answer(question, user_answer)  # Проверяем ответ

    score = user_data['score']
    if "Правильно!" in result:
        score += 1  # Увеличиваем счёт за правильный ответ

    await state.update_data(score=score)

    await message.answer(
        f"{result}\n\n"
        f"Твой счёт: {score}",
        reply_markup=Keyboards.get_after_answer_keyboard()  # Предлагаем варианты действий
    )


@quiz_router.callback_query(QuizStates.answering_question, F.data == "quiz_more")
async def next_question(callback: types.CallbackQuery, state: FSMContext):
    """
    Обработчик запроса следующего вопроса в текущей теме.

    Получает новый вопрос (исключая повтор предыдущего) и продолжает квиз.

    Args:
        callback: Объект callback от нажатия кнопки
        state: Текущее состояние FSM
    """
    user_data = await state.get_data()
    topic = user_data['current_topic']
    previous_question = user_data['previous_question']

    # Получаем новый вопрос, исключая предыдущий
    question = await get_quiz_question(topic, previous_question)

    await state.update_data(
        current_question=question,
        previous_question=question
    )

    await callback.message.answer(f"Вопрос: {question}\n\nНапиши свой ответ:")


@quiz_router.callback_query(QuizStates.answering_question, F.data == "change_topic")
async def change_topic(callback: types.CallbackQuery, state: FSMContext):
    """
    Обработчик смены темы квиза.

    Возвращает пользователя в состояние выбора темы.

    Args:
        callback: Объект callback от нажатия кнопки
        state: Текущее состояние FSM
    """
    await state.set_state(QuizStates.selecting_topic)
    await callback.message.answer(
        "Выбери новую тему:",
        reply_markup=Keyboards.get_topics_keyboard()
    )


@quiz_router.callback_query(QuizStates.answering_question, F.data == "end_quiz")
async def end_quiz(callback: types.CallbackQuery, state: FSMContext):
    """
    Обработчик завершения квиза.

    Показывает итоговый счёт и очищает состояние.

    Args:
        callback: Объект callback от нажатия кнопки
        state: Текущее состояние FSM
    """
    user_data = await state.get_data()
    score = user_data['score']

    await state.clear()  # Очищаем состояние
    await callback.message.answer(
        f"Квиз завершён! Твой итоговый счёт: {score}\n"
        "Напиши /quiz если захочешь сыграть ещё раз."
        "/start для возврата в основное меню"
    )