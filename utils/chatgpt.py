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
    """
    Асинхронно получает ответ от ChatGPT (GPT-4) на заданный промпт.

    Args:
        prompt (str): Текст запроса (промпт), который будет отправлен в ChatGPT.

    Returns:
        str: Ответ от ChatGPT или сообщение об ошибке, если что-то пошло не так.
    """
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
            model="gpt-4o-mini",  # Используемая модель (возможно, опечатка - должно быть "gpt-4" или "gpt-3.5-turbo"?)
        )

        # Возвращаем текст первого ответа
        return response.choices[0].message.content

    except Exception as e:
        # В случае ошибки возвращаем информативное сообщение
        return f"Ошибка: {str(e)}"



