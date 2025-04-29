from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder
from typing import Optional, List
from config import Config


class Keyboards:
    """
    Класс inline-клавиатур для бота
    Все методы возвращают объект InlineKeyboardMarkup
    """

    @staticmethod
    def main_menu():
        """Главное меню бота"""
        builder = ReplyKeyboardBuilder()
        builder.button(text="🎲 /random - Случайный факт")
        builder.button(text="🤖 /gpt - ChatGPT интерфейс")
        builder.button(text="👤 /talk - Диалог с личностью")
        builder.button(text="🧩 /quiz - Квиз")
        builder.adjust(2, 2)  # 2 кнопки в первом ряду, 2 во втором
        return builder.as_markup(resize_keyboard=True)

    @staticmethod
    def get_random_fact_keyboard():
        builder = InlineKeyboardBuilder()
        builder.button(text="🔁 Хочу ещё факт", callback_data="random")
        builder.button(text="🏠 Закончить", callback_data="start")
        return builder.as_markup()







