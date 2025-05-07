import os
from pathlib import Path
from typing import Dict, Optional
from enum import Enum
from dotenv import load_dotenv

load_dotenv()

# Константы для имен директорий
RESOURCES_DIR = "resources"
IMAGES_DIR = "images"
PROMPTS_DIR = "prompts"
MESSAGES_DIR = "messages"

class PersonEnum(str, Enum):
    """Перечисление для имен виртуальных персонажей."""
    COBAIN = "cobain"
    HAWKING = "hawking"
    NIETZSCHE = "nietzsche"
    QUEEN = "queen"
    TOLKIEN = "tolkien"

class LanguageEnum(str, Enum):
    """Перечисление для поддерживаемых языков перевода."""
    ENGLISH = "english"
    FRENCH = "french"
    GERMAN = "german"
    SPANISH = "spanish"
    CHINESE = "chinese"
    JAPANESE = "japanese"
    RUSSIAN = "russian"
    KOREAN = "korean"

class Config:
    """
    Класс конфигурации для Telegram-бота.

    Атрибуты:
        TELEGRAM_TOKEN: Токен Telegram-бота из переменных окружения.
        OPENAI_API_KEY: Ключ API OpenAI из переменных окружения.
        PROXY: Необязательный URL прокси для API-запросов.
        USER_QUIZZES: Хранилище в памяти для состояния викторин пользователей.
        USER_SESSIONS: Хранилище в памяти для данных сессий пользователей.
        PERSONS: Соответствие ключей персонажей и их отображаемых имен.
        IMAGE_PATHS: Соответствие ключей изображений и путей к файлам.
        LANGUAGES: Соответствие отображаемых имен языков и их кодов.
    """
    # Переменные окружения
    TELEGRAM_TOKEN: Optional[str] = os.getenv("TOKEN")
    OPENAI_API_KEY: Optional[str] = os.getenv("GPT_TOKEN")
    PROXY: Optional[str] = os.getenv("PROXY")

    # Хранилища в памяти (рассмотрите потокобезопасные альтернативы для продакшена)
    USER_QUIZZES: Dict[int, Dict[str, str]] = {}  # {user_id: {"topic": topic, "score": 0, "current_question": ""}}
    USER_SESSIONS: Dict[int, Dict[str, str]] = {}  # {user_id: {"personality": prompt}}

    # Соответствия персонажей
    PERSONS: Dict[str, str] = {
        PersonEnum.COBAIN: "Курт Кобейн",
        PersonEnum.HAWKING: "профессор Стивен Хокинг",
        PersonEnum.NIETZSCHE: "Фридрих Ницше",
        PersonEnum.QUEEN: "Королева Елизавета II",
        PersonEnum.TOLKIEN: "Дж.Р.Р. Толкин",
    }

    # Базовый путь к ресурсам
    _BASE_PATH: Path = Path(__file__).parent.resolve()

    # Пути к изображениям
    IMAGE_PATHS: Dict[str, str] = {
        "random": str(_BASE_PATH / RESOURCES_DIR / IMAGES_DIR / "random.jpg"),
        "gpt": str(_BASE_PATH / RESOURCES_DIR / IMAGES_DIR / "gpt.jpg"),
        "talk": str(_BASE_PATH / RESOURCES_DIR / IMAGES_DIR / "talk.jpg"),
        "quiz": str(_BASE_PATH / RESOURCES_DIR / IMAGES_DIR / "quiz.jpg"),
        "main": str(_BASE_PATH / RESOURCES_DIR / IMAGES_DIR / "main.jpg"),
        PersonEnum.COBAIN: str(_BASE_PATH / RESOURCES_DIR / IMAGES_DIR / "talk_cobain.jpg"),
        PersonEnum.HAWKING: str(_BASE_PATH / RESOURCES_DIR / IMAGES_DIR / "talk_hawking.jpg"),
        PersonEnum.NIETZSCHE: str(_BASE_PATH / RESOURCES_DIR / IMAGES_DIR / "talk_nietzsche.jpg"),
        PersonEnum.QUEEN: str(_BASE_PATH / RESOURCES_DIR / IMAGES_DIR / "talk_queen.jpg"),
        PersonEnum.TOLKIEN: str(_BASE_PATH / RESOURCES_DIR / IMAGES_DIR / "talk_tolkien.jpg"),
        "translate": str(_BASE_PATH / RESOURCES_DIR / IMAGES_DIR / "translate.jpg"),
        "voice_gpt": str(_BASE_PATH / RESOURCES_DIR / IMAGES_DIR / "voice_gpt.jpg"),
    }

    # Соответствия языков
    LANGUAGES: Dict[str, str] = {
        "Английский": LanguageEnum.ENGLISH,
        "Французский": LanguageEnum.FRENCH,
        "Немецкий": LanguageEnum.GERMAN,
        "Испанский": LanguageEnum.SPANISH,
        "Китайский": LanguageEnum.CHINESE,
        "Японский": LanguageEnum.JAPANESE,
        "Русский": LanguageEnum.RUSSIAN,
        "Корейский": LanguageEnum.KOREAN,
    }

    def __init__(self):
        """Инициализация и валидация конфигурации."""
        self._validate_env_vars()
        self._validate_image_paths()

    def _validate_env_vars(self) -> None:
        """Проверка наличия обязательных переменных окружения."""
        if not self.TELEGRAM_TOKEN:
            raise ValueError("Переменная окружения TELEGRAM_TOKEN не установлена")
        if not self.OPENAI_API_KEY:
            raise ValueError("Переменная окружения OPENAI_API_KEY не установлена")

    def _validate_image_paths(self) -> None:
        """Проверка существования всех файлов изображений."""
        for key, path in self.IMAGE_PATHS.items():
            if not Path(path).is_file():
                raise FileNotFoundError(f"Файл изображения для '{key}' не найден по пути: {path}")

    @staticmethod
    def _get_resource_path(resource_type: str, filename: str) -> Path:
        """Построение пути к файлу ресурса."""
        return Config._BASE_PATH / RESOURCES_DIR / resource_type / filename

    @staticmethod
    def get_prompts(prompt: str) -> str:
        """
        Чтение файла промпта из директории prompts.

        Аргументы:
            prompt: Имя файла промпта (без расширения .txt).

        Возвращает:
            Содержимое файла промпта.

        Исключения:
            FileNotFoundError: Если файл промпта не существует.
            IOError: Если файл не может быть прочитан.
        """
        file_path = Config._get_resource_path(PROMPTS_DIR, f"{prompt}.txt")
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                return f.read()
        except FileNotFoundError:
            raise FileNotFoundError(f"Файл промпта не найден: {file_path}")
        except IOError as e:
            raise IOError(f"Ошибка чтения файла промпта {file_path}: {str(e)}")

    @staticmethod
    def get_messages(message: str) -> str:
        """
        Чтение файла сообщения из директории messages.

        Аргументы:
            message: Имя файла сообщения (без расширения .txt).

        Возвращает:
            Содержимое файла сообщения.

        Исключения:
            FileNotFoundError: Если файл сообщения не существует.
            IOError: Если файл не может быть прочитан.
        """
        file_path = Config._get_resource_path(MESSAGES_DIR, f"{message}.txt")
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                return f.read()
        except FileNotFoundError:
            raise FileNotFoundError(f"Файл сообщения не найден: {file_path}")
        except IOError as e:
            raise IOError(f"Ошибка чтения файла сообщения {file_path}: {str(e)}")

