from aiogram import Router, F
from aiogram.types import Message, Voice

from utils.images import send_image
from config import Config
from utils.voice import voice_to_text, text_to_voice
from utils.chatgpt import get_chatgpt_response


voice_router = Router()

@voice_router.message(F.text.lower().contains("voice"))
async def handle_voice_command(message: Message):
    await send_image(message, Config.IMAGE_PATHS["voice_gpt"])
    await message.answer("Отправьте голосовое сообщение, и я отвечу вам голосом!")


@voice_router.message(F.voice)
async def handle_voice_message(message: Message):
    # Скачиваем голосовое сообщение
    voice = message.voice
    voice_file = await message.bot.get_file(voice.file_id)

    # Конвертируем голос в текст
    text = await voice_to_text(voice_file, message)
    await message.answer(f"Вы сказали: {text}")

    # Получаем ответ от ChatGPT
    response = await get_chatgpt_response(text)

    # Конвертируем текст в голос
    voice_response = await text_to_voice(response)

    # Отправляем голосовое сообщение
    await message.answer_voice(voice_response)

