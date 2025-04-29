import asyncio

import openai
import httpx
from config import Config



async def get_chatgpt_response(prompt: str) -> str:
    try:
        gpt_client = openai.AsyncOpenAI(
            api_key=Config.OPENAI_API_KEY,
            http_client=httpx.AsyncClient(
                proxy=Config.PROXY,
            ),
        )
        response = await gpt_client.chat.completions.create(
            messages=[
                {
                    'role': 'system',
                    'content': prompt,
                }
            ],
            model='gpt-3.5-turbo',

        )
        return response.choices[0].message.content
    except Exception as e:

        return f"Ошибка: {str(e)}"




