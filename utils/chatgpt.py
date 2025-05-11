"""
Модуль для взаимодействия с OpenAI ChatGPT через асинхронный API.

Основные функции:
- Асинхронное получение ответов от ChatGPT (GPT-4o-mini)
- Поддержка прокси-соединений
- Обработка ошибок API
"""
import logging
import openai
import httpx
from config import Config

logger = logging.getLogger(__name__)

async def get_chatgpt_response(prompt: str) -> str:
    """
    Получает ответ от ChatGPT по заданному промту.

    Args:
        prompt: Текст запроса для ChatGPT

    Returns:
        Ответ от модели

    Raises:
        Exception: Если произошла ошибка API
    """
    logger.debug(f"Отправка промта в ChatGPT: '{prompt}'")
    try:
        # Инициализация асинхронного клиента OpenAI с прокси
        gpt_client = openai.AsyncOpenAI(
            api_key=Config.OPENAI_API_KEY,
            http_client=httpx.AsyncClient(
                proxy=Config.PROXY,
            ),
        )

        # Отправка запроса к API ChatGPT
        response = await gpt_client.chat.completions.create(
            messages=[
                {
                    'role': 'user',
                    'content': prompt,
                }
            ],
            model="gpt-4o-mini",
        )

        # Возвращаем текст первого ответа
        result = response.choices[0].message.content
        logger.debug(f"Получен ответ от ChatGPT: '{result}'")
        return result

    except Exception as e:
        logger.error(f"Ошибка API ChatGPT: {str(e)}")
        raise

async def get_quiz_question(topic: str, previous_question: str = None) -> str:
    """
    Получает вопрос для квиза по заданной теме, исключая предыдущий вопрос.

    Args:
        topic: Тема квиза (например, 'prog', 'math', 'biology')
        previous_question: Предыдущий вопрос, чтобы избежать повтора (опционально)

    Returns:
        Текст вопроса

    Raises:
        ValueError: Если тема недопустима
    """
    logger.debug(f"Получение вопроса для темы '{topic}', исключая: '{previous_question}'")
    topics_map = {
        "prog": "программирования на языке Python",
        "math": "математических теорий (алгоритмы, теория множеств, матанализ)",
        "biology": "биологии"
    }

    if topic not in topics_map:
        logger.error(f"Недопустимая тема: '{topic}'. Допустимые темы: {list(topics_map.keys())}")
        raise ValueError(f"Недопустимая тема: '{topic}'")

    if topic == "quiz_more":
        prompt = (f"Сгенерируй новый вопрос на ту же тему, что и предыдущий вопрос: '{previous_question}'. "
                  f"Ответ должен быть коротким - несколько слов.")
    else:
        prompt = (f"Сгенерируй вопрос для квиза на тему {topics_map[topic]}. "
                  f"Ответ должен быть коротким - несколько слов. Не используй вопросы с численными ответами.")

    try:
        text = await get_chatgpt_response(prompt)
        logger.debug(f"Получен вопрос: '{text}'")
        return text
    except Exception as e:
        logger.error(f"Ошибка получения вопроса для темы '{topic}': {str(e)}")
        raise

async def check_answer(question: str, user_answer: str) -> str:
    """
    Проверяет правильность ответа на вопрос.

    Args:
        question: Текст вопроса
        user_answer: Ответ пользователя

    Returns:
        Результат проверки (например, "Правильно!" или "Неправильно. Правильный ответ - ...")
    """
    logger.debug(f"Проверка ответа '{user_answer}' на вопрос '{question}'")
    prompt = f"""Вопрос: {question}
    Ответ пользователя: {user_answer}

    Если ответ правильный или очень похож на правильный, ответь "Правильно!".
    Если ответ неправильный - ответь в формате: "Неправильно! 
    Правильный ответ - {{answer}}", где {{answer}} - правильный ответ.
    """
    try:
        text = await get_chatgpt_response(prompt)
        logger.debug(f"Результат проверки: '{text}'")
        return text
    except Exception as e:
        logger.error(f"Ошибка проверки ответа для вопроса '{question}': {str(e)}")
        raise