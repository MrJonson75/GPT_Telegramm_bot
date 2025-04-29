from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from keybords import Keyboards
from utils.images import send_image
from utils.chatgpt import get_chatgpt_response
from config import Config


rand_router = Router()



@rand_router.message(F.text.lower().contains("random"))
async def handle_random(message: Message):
    await send_image(message, Config.IMAGE_PATHS["random"])
    response = await get_chatgpt_response(Config.get_prompts("random"))
    await message.answer(
        response,
        reply_markup=Keyboards.get_random_fact_keyboard()
    )

@rand_router.callback_query(F.data == "random")
async def handle_more_fact(callback: CallbackQuery):
    await callback.answer()
    await handle_random(callback.message)