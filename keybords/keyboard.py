import logging
from enum import Enum

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder
from config import Config

# Настройка логирования
logger = logging.getLogger(__name__)

class CallbackData(str, Enum):
    """Перечисление для callback_data, используемых в клавиатурах."""
    RANDOM = "random"
    START = "start"
    BREAK = "break"
    TALK_PREFIX = "talk_"
    QUIZ_PREFIX = "quiz_"
    QUIZ_MORE = "quiz_more"
    CHANGE_TOPIC = "change_topic"
    END_QUIZ = "end_quiz"
    END_TALK = "end_talk"
    END_TRANS = "end_trans"
    END_VOICE = "end_voice"
    LANG_PREFIX = "lang_"
    CHANGE_LANG = "change_lang"
    MAIN_MENU = "main_menu"

class Keyboards:
    """
    Класс для создания inline и reply-клавиатур Telegram-бота.

    Все методы возвращают готовые объекты клавиатур для использования в обработчиках.
    """

    # Тексты кнопок для повторного использования
    BUTTON_TEXTS = {
        "random_more": "🔁 Хочу ещё факт",
        "exit": "🏠 Закончить",
        "quiz_more": "🔄 Ещё вопрос",
        "change_topic": "🔀 Сменить тему",
        "change_lang": "🔀 Сменить язык",
    }

    @staticmethod
    def _get_exit_button(callback_data: str = CallbackData.MAIN_MENU) -> InlineKeyboardButton:
        """Создает кнопку 'Закончить' с заданным callback_data."""
        return InlineKeyboardButton(
            text=Keyboards.BUTTON_TEXTS["exit"],
            callback_data=callback_data
        )

    @staticmethod
    def main_menu(columns: int = 2) -> ReplyKeyboardMarkup:
        """
        Создает главное меню бота с основными командами.

        Args:
            columns: Количество столбцов для кнопок (по умолчанию 2).

        Returns:
            ReplyKeyboardBuilder: Клавиатура с кнопками основных функций бота.
        """
        logger.debug("Создание главного меню")
        builder = ReplyKeyboardBuilder()
        buttons = [
            "🎲 /random - Случайный факт",
            "🤖 /gpt - ChatGPT интерфейс",
            "👤 /talk - Диалог с личностью",
            "🧩 /quiz - Квиз",
            "🌐 /translate - Переводчик",
            "🎙️ /voice - Голосовой чат",
        ]
        for text in buttons:
            builder.button(text=text)
        builder.adjust(columns)
        return builder.as_markup(resize_keyboard=True)

    @staticmethod
    def get_random_fact_keyboard() -> InlineKeyboardMarkup:
        """
        Создает inline-клавиатуру для режима случайных фактов.

        Returns:
            InlineKeyboardBuilder: Клавиатура с кнопками "Ещё факт" и "Закончить".
        """
        logger.debug("Создание клавиатуры для случайных фактов")
        builder = InlineKeyboardBuilder()
        builder.button(
            text=Keyboards.BUTTON_TEXTS["random_more"],
            callback_data=CallbackData.RANDOM
        )
        builder.add(Keyboards._get_exit_button())
        return builder.as_markup()

    @staticmethod
    def get_gpt_exit_keyboard() -> InlineKeyboardMarkup:
        """
        Создает inline-клавиатуру для выхода из режима GPT.

        Returns:
            InlineKeyboardBuilder: Клавиатура с кнопкой "Закончить".
        """
        logger.debug("Создание клавиатуры выхода из режима GPT")
        builder = InlineKeyboardBuilder()
        builder.add(Keyboards._get_exit_button(CallbackData.BREAK))
        return builder.as_markup()

    @staticmethod
    def get_personalities_keyboard(columns: int = 1) -> InlineKeyboardMarkup | None:
        """
        Создает inline-клавиатуру с выбором личностей для диалога.

        Args:
            columns: Количество столбцов для кнопок (по умолчанию 1).

        Returns:
            InlineKeyboardBuilder: Клавиатура с кнопками личностей, или None, если личности не настроены.

        Notes:
            Если Config.PERSONS пуст, логируется предупреждение, и возвращается None.
        """
        if not Config.PERSONS:
            logger.warning("Config.PERSONS пуст, клавиатура личностей не создана")
            return None

        logger.debug("Создание клавиатуры выбора личностей")
        builder = InlineKeyboardBuilder()
        for person_id, person_name in Config.PERSONS.items():
            callback_data = f"{CallbackData.TALK_PREFIX.value}{person_id.value}"
            logger.debug(f"Добавлена кнопка личности: текст={person_name.upper()}, callback_data={callback_data}")
            builder.button(
                text=person_name.upper(),
                callback_data=callback_data
            )
        builder.adjust(columns)
        return builder.as_markup()

    @staticmethod
    def get_talk_exit_keyboard() -> InlineKeyboardMarkup:
        """
        Создает inline-клавиатуру для выхода из режима диалога.

        Returns:
            InlineKeyboardBuilder: Клавиатура с кнопкой "Закончить".
        """
        logger.debug("Создание клавиатуры выхода из режима диалога")
        builder = InlineKeyboardBuilder()
        builder.add(Keyboards._get_exit_button(CallbackData.END_TALK))
        return builder.as_markup()

    @staticmethod
    def get_quiz_topics_keyboard(columns: int = 1) -> InlineKeyboardMarkup:
        """
        Создает inline-клавиатуру с выбором тем для квиза.

        Args:
            columns: Количество столбцов для кнопок (по умолчанию 1).

        Returns:
            InlineKeyboardBuilder: Клавиатура с кнопками тем.
        """
        logger.debug("Создание клавиатуры выбора тем квиза")
        builder = InlineKeyboardBuilder()
        topics = [
            ("🐍 Программирование (Python)", f"{CallbackData.QUIZ_PREFIX.value}prog"),
            ("∫ Математика", f"{CallbackData.QUIZ_PREFIX.value}math"),
            ("🧬 Биология", f"{CallbackData.QUIZ_PREFIX.value}biology"),
        ]
        for text, callback_data in topics:
            logger.debug(f"Добавлена кнопка: текст={text}, callback_data={callback_data}")
            builder.button(text=text, callback_data=callback_data)
        builder.adjust(columns)
        return builder.as_markup()

    @staticmethod
    def get_quiz_control_keyboard(columns: int = 1) -> InlineKeyboardMarkup:
        """
        Создает inline-клавиатуру для управления квизом после ответа.

        Args:
            columns: Количество столбцов для кнопок (по умолчанию 1).

        Returns:
            InlineKeyboardBuilder: Клавиатура с кнопками управления квизом.
        """
        logger.debug("Создание клавиатуры управления квизом")
        builder = InlineKeyboardBuilder()
        builder.button(
            text=Keyboards.BUTTON_TEXTS["quiz_more"],
            callback_data=CallbackData.QUIZ_MORE
        )
        builder.button(
            text=Keyboards.BUTTON_TEXTS["change_topic"],
            callback_data=CallbackData.CHANGE_TOPIC
        )
        builder.add(Keyboards._get_exit_button(CallbackData.END_QUIZ))
        builder.adjust(columns)
        return builder.as_markup()

    @staticmethod
    def get_languages_keyboard(columns: int = 2) -> InlineKeyboardMarkup | None:
        """
        Создает inline-клавиатуру с выбором языков для перевода.

        Args:
            columns: Количество столбцов для кнопок (по умолчанию 2).

        Returns:
            InlineKeyboardBuilder: Клавиатура с кнопками языков, или None, если языки не настроены.

        Notes:
            Если Config.LANGUAGES пуст, логируется предупреждение, и возвращается None.
        """
        if not Config.LANGUAGES:
            logger.warning("Config.LANGUAGES пуст, клавиатура языков не создана")
            return None

        logger.debug("Создание клавиатуры выбора языков")
        builder = InlineKeyboardBuilder()
        for lang_name, lang_code in Config.LANGUAGES.items():
            builder.button(
                text=lang_name,
                callback_data=f"{CallbackData.LANG_PREFIX.value}{lang_code}"
            )
        builder.adjust(columns)
        return builder.as_markup()

    @staticmethod
    def get_translator_control_keyboard(columns: int = 1) -> InlineKeyboardMarkup:
        """
        Создает inline-клавиатуру для управления переводчиком.

        Args:
            columns: Количество столбцов для кнопок (по умолчанию 1).

        Returns:
            InlineKeyboardBuilder: Клавиатура с кнопками управления.
        """
        logger.debug("Создание клавиатуры управления переводчиком")
        builder = InlineKeyboardBuilder()
        builder.button(
            text=Keyboards.BUTTON_TEXTS["change_lang"],
            callback_data=CallbackData.CHANGE_LANG.value
        )
        builder.add(Keyboards._get_exit_button(CallbackData.END_TRANS))
        builder.adjust(columns)
        return builder.as_markup()

    @staticmethod
    def get_voice_control_keyboard() -> InlineKeyboardMarkup:
        builder = InlineKeyboardBuilder()
        builder.button(
            text="Попробовать снова",
            callback_data="retry_voice"
        )
        builder.add(Keyboards._get_exit_button(CallbackData.END_VOICE.value))
        builder.adjust(2)
        return builder.as_markup()