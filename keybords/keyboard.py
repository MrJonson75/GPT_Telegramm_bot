from aiogram.types import InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder
from config import Config


class CallbackData:
    """Константы для callback_data."""
    RANDOM = "random"
    START = "start"
    BREAK = "break"
    TALK_PREFIX = "talk_"
    QUIZ_PREFIX = "quiz_"
    QUIZ_MORE = "quiz_more"
    CHANGE_TOPIC = "change_topic"
    END_QUIZ = "end_quiz"
    LANG_PREFIX = "lang_"
    CHANGE_LANG = "change_lang"
    MAIN_MENU = "main_menu"


class Keyboards:
    """
    Класс для создания inline и reply-клавиатур бота.
    Все методы возвращают объекты клавиатур, готовые к использованию.
    """

    @staticmethod
    def main_menu() -> ReplyKeyboardBuilder:
        """
        Создает главное меню бота с основными командами.

        Returns:
            ReplyKeyboardBuilder: Клавиатура с кнопками основных функций бота
        """
        builder = ReplyKeyboardBuilder()
        builder.button(text="🎲 /random - Случайный факт")
        builder.button(text="🤖 /gpt - ChatGPT интерфейс")
        builder.button(text="👤 /talk - Диалог с личностью")
        builder.button(text="🧩 /quiz - Квиз")
        builder.button(text="🌐 /translate - Переводчик")
        builder.button(text="🎙️ /voice - Голосовой чат")
        builder.adjust(2)
        return builder.as_markup(resize_keyboard=True)

    @staticmethod
    def get_random_fact_keyboard() -> InlineKeyboardBuilder:
        """
        Создает inline-клавиатуру для режима случайных фактов.

        Returns:
            InlineKeyboardBuilder: Клавиатура с кнопками "Еще факт" и "Закончить"
        """
        builder = InlineKeyboardBuilder()
        builder.button(text="🔁 Хочу ещё факт", callback_data=CallbackData.RANDOM)
        builder.button(text="🏠 Закончить", callback_data=CallbackData.START)
        return builder.as_markup()

    @staticmethod
    def get_gpt_exit_keyboard() -> InlineKeyboardBuilder:
        """
        Создает inline-клавиатуру для выхода из режима GPT.

        Returns:
            InlineKeyboardBuilder: Клавиатура с кнопкой "Закончить"
        """
        builder = InlineKeyboardBuilder()
        builder.button(text="🏠 Закончить", callback_data=CallbackData.BREAK)
        return builder.as_markup()

    @staticmethod
    def get_personalities_keyboard() -> InlineKeyboardBuilder:
        """
        Создает inline-клавиатуру с выбором личностей для диалога.

        Returns:
            InlineKeyboardBuilder: Клавиатура с кнопками личностей

        Raises:
            ValueError: Если в Config.PERSONS нет данных
        """
        if not Config.PERSONS:
            raise ValueError("No personalities configured in Config.PERSONS")

        builder = InlineKeyboardBuilder()
        for person_id, person_name in Config.PERSONS.items():
            builder.button(
                text=person_name.upper(),
                callback_data=f"{CallbackData.TALK_PREFIX}{person_id}"
            )
        builder.adjust(1)
        return builder.as_markup()

    @staticmethod
    def get_talk_exit_keyboard():
        """
        Создает inline-клавиатуру для выхода из режима диалога.

        Returns:
            InlineKeyboardBuilder: Клавиатура с кнопкой "Закончить"
        """
        builder = InlineKeyboardBuilder()
        builder.button(text="🏠 Закончить", callback_data=CallbackData.START)
        return builder.as_markup()

    @staticmethod
    def get_quiz_topics_keyboard() -> InlineKeyboardBuilder:
        """
        Создает inline-клавиатуру с выбором тем для квиза.

        Returns:
            InlineKeyboardBuilder: Клавиатура с кнопками тем
        """
        builder = InlineKeyboardBuilder()
        builder.button(text="🐍 Программирование (Python)", callback_data=f"{CallbackData.QUIZ_PREFIX}prog")
        builder.button(text="∫ Математика", callback_data=f"{CallbackData.QUIZ_PREFIX}math")
        builder.button(text="🧬 Биология", callback_data=f"{CallbackData.QUIZ_PREFIX}biology")
        builder.adjust(1)
        return builder.as_markup()

    @staticmethod
    def get_quiz_control_keyboard() -> InlineKeyboardBuilder:
        """
        Создает inline-клавиатуру для управления квизом после ответа.

        Returns:
            InlineKeyboardBuilder: Клавиатура с кнопками управления квизом
        """
        builder = InlineKeyboardBuilder()
        builder.button(text="🔄 Ещё вопрос", callback_data=CallbackData.QUIZ_MORE)
        builder.button(text="🔀 Сменить тему", callback_data=CallbackData.CHANGE_TOPIC)
        builder.button(text="🏠 Закончить", callback_data=CallbackData.END_QUIZ)
        builder.adjust(1)
        return builder.as_markup()

    @staticmethod
    def get_languages_keyboard() -> InlineKeyboardBuilder:
        """
        Создает inline-клавиатуру с выбором языков для перевода.

        Returns:
            InlineKeyboardBuilder: Клавиатура с кнопками языков

        Raises:
            ValueError: Если в Config.LANGUAGES нет данных
        """
        if not Config.LANGUAGES:
            raise ValueError("No languages configured in Config.LANGUAGES")

        builder = InlineKeyboardBuilder()
        for lang_name, lang_code in Config.LANGUAGES.items():
            builder.button(
                text=lang_name,
                callback_data=f"{CallbackData.LANG_PREFIX}{lang_code}"
            )
        builder.adjust(2)
        return builder.as_markup()

    @staticmethod
    def get_translator_control_keyboard() -> InlineKeyboardBuilder:
        """
        Создает inline-клавиатуру для управления переводчиком.

        Returns:
            InlineKeyboardBuilder: Клавиатура с кнопками управления
        """
        builder = InlineKeyboardBuilder()
        builder.button(text="🔀 Сменить язык", callback_data=CallbackData.CHANGE_LANG)
        builder.button(text="🏠 Закончить", callback_data=CallbackData.MAIN_MENU)
        return builder.as_markup()