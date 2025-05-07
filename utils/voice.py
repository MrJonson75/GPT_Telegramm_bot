import asyncio
import os
import httpx
import openai
from config import Config


async def voice_to_text(voice_file, message):
    """
    Асинхронная функция для преобразования голосового сообщения в текст.

    Параметры:
        voice_file: Объект голосового файла из Telegram бота
        message: Объект сообщения из Telegram бота

    Возвращает:
        str: Распознанный текст или сообщение об ошибке

    Процесс работы:
        1. Скачивание голосового сообщения
        2. Конвертация из OGG в MP3 с помощью ffmpeg
        3. Отправка аудио в OpenAI Whisper для распознавания
        4. Очистка временных файлов
    """
    voice_path = None
    mp3_path = None

    try:
        # Скачиваем голосовое сообщение
        voice_path = f"voice_{voice_file.file_id}.ogg"
        await message.bot.download_file(voice_file.file_path, voice_path)

        if not os.path.exists(voice_path):
            return "Ошибка: не удалось сохранить голосовое сообщение"

        # Конвертируем в MP3 через ffmpeg
        mp3_path = os.path.splitext(voice_path)[0] + ".mp3"

        # Указываем полный путь к ffmpeg или убедимся, что он в PATH
        ffmpeg_path = "ffmpeg"  # Замените на полный путь при необходимости

        process = await asyncio.create_subprocess_exec(
            ffmpeg_path,
            "-i", voice_path,
            "-codec:a", "libmp3lame",
            "-q:a", "2",
            "-y",
            mp3_path,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )

        _, stderr = await process.communicate()

        if process.returncode != 0:
            error_msg = stderr.decode('utf-8')
            print(f"FFmpeg error: {error_msg}")  # Логируем ошибку
            raise RuntimeError(f"Ошибка конвертации: {error_msg}")

        if not os.path.exists(mp3_path):
            raise RuntimeError("Конвертированный файл не создан")

        # Читаем конвертированный файл
        with open(mp3_path, "rb") as f:
            audio_data = f.read()

        # Отправляем в OpenAI
        gpt_client = openai.AsyncOpenAI(
            api_key=Config.OPENAI_API_KEY,
            http_client=httpx.AsyncClient(proxy=Config.PROXY),
        )

        translation = await gpt_client.audio.translations.create(
            model="whisper-1",
            file=audio_data,
            response_format="text"
        )

        return translation

    except httpx.HTTPError:
        return "Ошибка подключения к сервису распознавания речи"
    except openai.APIError:
        return "Ошибка API распознавания речи"
    except openai.AuthenticationError:
        return "Ошибка аутентификации в сервисе распознавания речи"
    except Exception as e:
        return f"Произошла ошибка: {str(e)}"
    finally:
        # Удаляем временные файлы
        for file_path in [voice_path, mp3_path]:
            if file_path and os.path.exists(file_path):
                try:
                    os.remove(file_path)
                except:
                    pass


async def text_to_voice(text: str) -> bytes:
    """
    Асинхронная функция для преобразования текста в аудио (речь).

    Параметры:
        text: str - Текст для преобразования в речь

    Возвращает:
        bytes: Бинарные данные аудиофайла в формате MP3

    Исключения:
        RuntimeError: Если происходит ошибка при преобразовании

    Примечание:
        Использует модель GPT-4o-mini-tts с веселым и позитивным тоном голоса
    """
    try:
        gpt_client = openai.AsyncOpenAI(
            api_key=Config.OPENAI_API_KEY,
            http_client=httpx.AsyncClient(proxy=Config.PROXY),
        )

        async with gpt_client.audio.speech.with_streaming_response.create(
                model="gpt-4o-mini-tts",  # Возможно, следует использовать "tts-1" или "tts-1-hd"
                voice="nova",
                input=text,
                instructions="Говорите веселым и позитивным тоном.",
        ) as response:
            return await response.read()

    except Exception as e:
        raise RuntimeError(f"Ошибка при преобразовании текста в речь: {str(e)}")