from aiogram.types import Message, FSInputFile
from config import Config

async def send_image(message: Message, image_path: str):
    try:
        photo = FSInputFile(image_path)
        await message.answer_photo(photo)
    except Exception as e:
        await message.answer(f"Не удалось отправить изображение: {e}")