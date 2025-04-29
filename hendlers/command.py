from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from keybords import Keyboards
from config import Config
from utils.images import send_image



comm_router = Router()


@comm_router.message(Command("start"))
async def handle_start(message: Message):
    await send_image(message, Config.IMAGE_PATHS['main'])
    answer_text = Config.get_messages('main')
    await message.answer(
        answer_text,
        reply_markup=Keyboards.main_menu()
    )


@comm_router.callback_query(F.data == "start")
async def handle_start_callback(callback: CallbackQuery):
    await callback.answer()
    await handle_start(callback.message)

    # Очищаем сессии при возврате в стартовое меню
    user_id = callback.from_user.id
    if user_id in Config.user_sessions:
        del Config.user_sessions[user_id]
    if user_id in Config.user_quizzes:
        del Config.user_quizzes[user_id]