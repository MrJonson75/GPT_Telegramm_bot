from aiogram.types import InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder
from config import Config


class Keyboards:
    """
    Класс inline и Reply-клавиатур для бота
    """

    @staticmethod
    def main_menu():
        """Главное меню бота"""
        builder = ReplyKeyboardBuilder()
        builder.button(text="🎲 /random - Случайный факт")
        builder.button(text="🤖 /gpt - ChatGPT интерфейс")
        builder.button(text="👤 /talk - Диалог с личностью")
        builder.button(text="🧩 /quiz - Квиз")
        builder.button(text="🌐 /translate - Переводчик")
        builder.button(text="🎙️ /voice - Голосовой ChatGPT")
        builder.adjust(2)
        return builder.as_markup(resize_keyboard=True)

    @staticmethod
    def get_random_fact_keyboard():
        builder = InlineKeyboardBuilder()
        builder.button(text="🔁 Хочу ещё факт", callback_data="random")
        builder.button(text="🏠 Закончить", callback_data="start")
        return builder.as_markup()


    @staticmethod
    def return_gpt_keyboard():
        builder = InlineKeyboardBuilder()
        builder.button(text="🏠 Закончить", callback_data="break")
        return builder.as_markup()

    @staticmethod
    def get_personalities_keyboard():
        builder = InlineKeyboardBuilder()
        for person in Config.PERSONS.keys():
            builder.button(text=Config.PERSONS[person].upper(), callback_data=f"talk_{person}")
        builder.adjust(1)
        return builder.as_markup()

    @staticmethod
    def return_talk_keyboard():
        builder = InlineKeyboardBuilder()
        builder.button(text="🏠 Закончить", callback_data="start")
        return builder.as_markup()

    @staticmethod
    def get_topics_keyboard():
        builder = InlineKeyboardBuilder()
        builder.add(
            InlineKeyboardButton(text="🐍 Программирование (Python)", callback_data="quiz_prog"),
            InlineKeyboardButton(text="∫ Математика", callback_data="quiz_math"),
            InlineKeyboardButton(text="🧬 Биология", callback_data="quiz_biology"),
        )
        builder.adjust(1)
        return builder.as_markup()

    @staticmethod
    def get_after_answer_keyboard():
        builder = InlineKeyboardBuilder()
        builder.add(
            InlineKeyboardButton(text="🔄 Ещё вопрос", callback_data="quiz_more"),
            InlineKeyboardButton(text="🔀 Сменить тему", callback_data="change_topic"),
            InlineKeyboardButton(text="🏠Закончить", callback_data="end_quiz"),
        )
        builder.adjust(1)
        return builder.as_markup()

    @staticmethod
    def get_languages_keyboard():
        builder = InlineKeyboardBuilder()
        for name, code in Config.LANGUAGES.items():
            builder.button(text=name, callback_data=f"lang_{code}")
        builder.adjust(2)
        return builder.as_markup()

    @staticmethod
    def get_translator_keyboard():
        builder = InlineKeyboardBuilder()
        builder.button(text="🔀 Сменить язык", callback_data="change_lang")
        builder.button(text="🏠 Закончить", callback_data="start")
        return builder.as_markup()







