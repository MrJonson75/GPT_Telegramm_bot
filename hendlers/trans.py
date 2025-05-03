from aiogram import Router, F
from aiogram.types import Message, CallbackQuery

from config import Config
from utils.images import send_image
from utils.chatgpt import get_chatgpt_response
from keybords import Keyboards

trans_router = Router()
user_languages = {}

@trans_router.message(F.text.lower().contains("translate"))
async def handle_translate(message: Message):
    await send_image(message, Config.IMAGE_PATHS["translate"])
    answer_text = Config.get_messages('translate')
    await message.answer(
        answer_text,
        reply_markup=Keyboards.get_languages_keyboard()
    )

@trans_router.callback_query(F.data.startswith("lang_"))
async def handle_language(callback: CallbackQuery):
    language = callback.data.split("_")[1]
    user_languages[callback.from_user.id] = language
    await callback.message.answer(
        f"Выбран язык: {language}. Отправьте текст для перевода:",
        reply_markup=Keyboards.get_translator_keyboard()
    )
    await callback.answer()

@trans_router.callback_query(F.data == "change_lang")
async def handle_change_language(callback: CallbackQuery):
    await callback.message.answer(
        "Выберите язык для перевода:",
        reply_markup=Keyboards.get_languages_keyboard()
    )
    await callback.answer()

@trans_router.message(lambda message: message.from_user.id in user_languages)
async def handle_translation(message: Message):
    language = user_languages[message.from_user.id]
    prompt = f"Переведи следующий текст на {language}:\n\n{message.text}"

    translation = await get_chatgpt_response(prompt)
    await message.answer(
        f"Перевод ({language}):\n\n{translation}",
        reply_markup=Keyboards.get_translator_keyboard()
    )