'''
        Модуль для взаимодействия с OpenAI ChatGPT через асинхронный API.

        Основные функции:
        - Асинхронное получение ответов от ChatGPT (GPT-4)
                1.	В модели указано "gpt-4o-mini" – возможно использование модели OpenAI:
                        o	gpt-4
                        o	gpt-4-turbo
                        o	gpt-3.5-turbo

        - Поддержка прокси-соединений
        - Обработка ошибок API

'''
import openai
import httpx
from config import Config



async def get_chatgpt_response(prompt: str) -> str:
    try:
        # Инициализация асинхронного клиента OpenAI с прокси
        gpt_client = openai.AsyncOpenAI(
            api_key=Config.OPENAI_API_KEY,  # API ключ из конфигурации
            http_client=httpx.AsyncClient(
                proxy=Config.PROXY,  # Прокси-сервер из конфигурации
            ),
        )

        # Отправка запроса к API ChatGPT
        response = await gpt_client.chat.completions.create(
            messages=[
                {
                    'role': 'user',  # Роль системы задает контекст
                    'content': prompt,  # Наш запрос
                }
            ],
            model="gpt-4o-mini",  # Используемая модель
        )

        # Возвращаем текст первого ответа
        return response.choices[0].message.content

    except Exception as e:
        # В случае ошибки возвращаем информативное сообщение
        return f"Ошибка: {str(e)}"



async def get_quiz_question(topic: str, previous_question: str = None) -> str:
    if topic == "quiz_more":
        prompt = (f"Сгенерируй новый вопрос на ту же тему, что и предыдущий вопрос: '{previous_question}'. Ответ "
                  f"должен быть коротким - несколько слов.")
    else:
        topics_map = {
            "quiz_prog": "программирования на языке Python",
            "quiz_math": "математических теорий (алгоритмы, теория множеств, матанализ)",
            "quiz_biology": "биологии"
        }
        prompt = (f"Сгенерируй вопрос для квиза на тему {topics_map[topic]}. Ответ должен быть "
                  f"коротким - несколько слов. Не используй вопросы с численными ответами.")
    text = await get_chatgpt_response(prompt)
    return text


async def check_answer(question: str, user_answer: str) -> str:
    prompt = f"""Вопрос: {question}
    Ответ пользователя: {user_answer}

    Если ответ правильный или очень похож на правильный, ответь "Правильно!".
    Если ответ неправильный - ответь в формате: "Неправильно! 
    Правильный ответ - {{answer}}", где {{answer}} - правильный ответ.
    """
    text = await get_chatgpt_response(prompt)
    return text