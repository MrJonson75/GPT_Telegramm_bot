"""
Модуль обработки квиза
"""
import logging
from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import Message, CallbackQuery
from config import Config
from utils.images import send_image
from utils.chatgpt import get_quiz_question, check_answer
from keybords import Keyboards, CallbackData

# Настройка логирования
logger = logging.getLogger(__name__)

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
    logger.debug(f"Пользователь {message.from_user.id} начал квиз")
    await state.clear()  # Очищаем состояние для нового квиза
    await state.set_state(QuizStates.selecting_topic)
    logger.debug(f"Установлено состояние QuizStates.selecting_topic для пользователя {message.from_user.id}")
    await state.update_data(score=0)  # Инициализируем счёт

    # Отправляем изображение из пути, указанного в конфиге
    try:
        await send_image(message, Config.IMAGE_PATHS["quiz"])
    except KeyError:
        logger.warning("Изображение для команды 'quiz' не найдено")

    answer_text = Config.get_messages('quiz') or "Выберите тему квиза:"
    keyboard = Keyboards.get_quiz_topics_keyboard()
    if keyboard is None:
        logger.warning("Клавиатура тем квиза не создана")
        await message.answer("Темы квиза не настроены. Обратитесь к администратору.")
        return

    await message.answer(
        answer_text,
        reply_markup=keyboard
    )

@quiz_router.callback_query(F.data.in_([f"{CallbackData.QUIZ_PREFIX.value}{topic}" for topic in ["prog", "math", "biology"]]))
async def process_topic_selection(callback: CallbackQuery, state: FSMContext):
    """
    Обработчик выбора темы квиза с клавиатуры get_quiz_topics_keyboard.

    Получает вопрос по выбранной теме, сохраняет тему и вопрос в состоянии FSM,
    и переводит пользователя в состояние ответа на вопрос.

    Args:
        callback: Объект callback от нажатия кнопки
        state: Текущее состояние FSM
    """
    current_state = await state.get_state()
    logger.debug(f"Получен callback: user={callback.from_user.id}, data={callback.data}, state={current_state}")

    # Извлекаем тему из callback_data (например, "prog" из "quiz_prog")
    topic = callback.data[len(CallbackData.QUIZ_PREFIX.value):]
    logger.debug(f"Извлечена тема: {topic}")

    # Проверяем допустимость темы
    valid_topics = ["prog", "math", "biology"]
    if topic not in valid_topics:
        logger.warning(f"Недопустимая тема: {topic}")
        await callback.message.answer(
            "Эта тема недоступна. Выберите другую.",
            reply_markup=Keyboards.get_quiz_topics_keyboard()
        )
        await callback.answer()
        return

    # Получаем вопрос по выбранной теме
    try:
        question = await get_quiz_question(topic)
        logger.debug(f"Получен вопрос для темы '{topic}': {question}")
    except Exception as e:
        logger.error(f"Ошибка получения вопроса для темы '{topic}': {str(e)}")
        await callback.message.answer(
            "Не удалось загрузить вопрос. Попробуйте выбрать другую тему.",
            reply_markup=Keyboards.get_quiz_topics_keyboard()
        )
        await callback.answer()
        return

    # Сохраняем тему и вопрос в состоянии
    await state.set_state(QuizStates.answering_question)
    logger.debug(f"Установлено состояние QuizStates.answering_question для пользователя {callback.from_user.id}")
    await state.update_data(
        current_topic=topic,
        current_question=question,
        previous_question=question
    )
    logger.debug(f"Сохранены данные: current_topic={topic}, current_question={question}")

    # Отправляем вопрос пользователю
    await callback.message.answer(f"Вопрос: {question}\n\nНапиши свой ответ:")
    await callback.answer()

@quiz_router.message(QuizStates.answering_question)
async def process_user_answer(message: Message, state: FSMContext):
    """
    Обработчик ответа пользователя на вопрос квиза.

    Проверяет ответ, обновляет счёт и показывает результат.

    Args:
        message: Объект сообщения с ответом пользователя
        state: Текущее состояние FSM
    """
    user_data = await state.get_data()
    question = user_data.get('current_question')
    user_answer = message.text
    logger.debug(f"Пользователь {message.from_user.id} ответил: {user_answer} на вопрос: {question}")

    # Проверяем ответ
    try:
        result = await check_answer(question, user_answer)
    except Exception as e:
        logger.error(f"Ошибка проверки ответа: {str(e)}")
        await message.answer("Ошибка при проверке ответа. Попробуйте снова.")
        return

    score = user_data.get('score', 0)
    if "Правильно!" in result:
        score += 1  # Увеличиваем счёт за правильный ответ

    await state.update_data(score=score)
    logger.debug(f"Обновлен счёт: {score}, данные состояния: {await state.get_data()}")

    await message.answer(
        f"{result}\n\nТвой счёт: {score}",
        reply_markup=Keyboards.get_quiz_control_keyboard()
    )

@quiz_router.callback_query(QuizStates.answering_question, F.data == CallbackData.QUIZ_MORE.value)
async def next_question(callback: CallbackQuery, state: FSMContext):
    """
    Обработчик запроса следующего вопроса в текущей теме.

    Получает новый вопрос (исключая повтор предыдущего) и продолжает квиз.

    Args:
        callback: Объект callback от нажатия кнопки
        state: Текущее состояние FSM
    """
    current_state = await state.get_state()
    user_data = await state.get_data()
    topic = user_data.get('current_topic')
    previous_question = user_data.get('previous_question')
    logger.debug(f"Пользователь {callback.from_user.id} запросил новый вопрос. Тема: {topic}, предыдущий вопрос: {previous_question}, состояние: {current_state}")

    # Проверяем наличие темы
    valid_topics = ["prog", "math", "biology"]
    if not topic or topic not in valid_topics:
        logger.error(f"Недопустимая или отсутствующая тема: '{topic}'. Данные состояния: {user_data}")
        await callback.message.answer(
            "Тема квиза не определена. Выберите тему заново.",
            reply_markup=Keyboards.get_quiz_topics_keyboard()
        )
        await state.set_state(QuizStates.selecting_topic)
        await callback.answer()
        return

    # Получаем новый вопрос, исключая предыдущий
    try:
        question = await get_quiz_question(topic, previous_question)
        logger.debug(f"Получен вопрос для темы '{topic}': {question}")
    except Exception as e:
        logger.error(f"Ошибка получения вопроса для темы '{topic}': {str(e)}")
        await callback.message.answer(
            "Не удалось загрузить вопрос. Попробуйте выбрать другую тему.",
            reply_markup=Keyboards.get_quiz_topics_keyboard()
        )
        await state.set_state(QuizStates.selecting_topic)
        await callback.answer()
        return

    await state.update_data(
        current_question=question,
        previous_question=question
    )
    logger.debug(f"Сохранены данные: current_question={question}")

    await callback.message.answer(f"Вопрос: {question}\n\nНапиши свой ответ:")
    await callback.answer()

@quiz_router.callback_query(QuizStates.answering_question, F.data == CallbackData.CHANGE_TOPIC.value)
async def change_topic(callback: CallbackQuery, state: FSMContext):
    """
    Обработчик смены темы квиза.

    Возвращает пользователя в состояние выбора темы.

    Args:
        callback: Объект callback от нажатия кнопки
        state: Текущее состояние FSM
    """
    logger.debug(f"Пользователь {callback.from_user.id} запросил смену темы")
    await state.set_state(QuizStates.selecting_topic)
    await callback.message.answer(
        "Выбери новую тему:",
        reply_markup=Keyboards.get_quiz_topics_keyboard()
    )
    await callback.answer()

@quiz_router.callback_query(QuizStates.answering_question, F.data == CallbackData.END_QUIZ.value)
async def end_quiz(callback: CallbackQuery, state: FSMContext):
    """
    Обработчик завершения квиза.

    Показывает итоговый счёт и очищает состояние.

    Args:
        callback: Объект callback от нажатия кнопки
        state: Текущее состояние FSM
    """
    user_data = await state.get_data()
    score = user_data.get('score', 0)
    logger.debug(f"Пользователь {callback.from_user.id} завершил квиз с результатом {score}")

    await state.clear()  # Очищаем состояние
    await callback.message.answer(
        f"Квиз завершён! Твой итоговый счёт: {score}\n"
        "Напиши /quiz, если захочешь сыграть ещё раз.\n"
        "/start для возврата в основное меню",
        reply_markup=Keyboards.main_menu()
    )
    await callback.answer()

