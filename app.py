"""
Модуль app.py

Точка входа для Telegram-бота.

Основные функции:
- Инициализация бота и диспетчера
- Регистрация обработчиков из модулей handlers
- Настройка логирования в консоль и файл
- Запуск бота в режиме polling
- Обработка событий запуска и остановки
"""
import asyncio
import logging
from aiogram import Bot, Dispatcher
import misc
from hendlers import all_handlers
from config import Config

# Настройка логирования
logger = logging.getLogger(__name__)

def setup_logging():
    """
    Настраивает логирование в консоль и файл bot_log.log.

    Формат: %(asctime)s - %(name)s - %(levelname)s - %(message)s
    Уровень: INFO
    """
    logging.basicConfig(
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        level=logging.INFO,
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler('bot_log.log', encoding='utf-8')
        ]
    )
    logger.info("Логирование настроено: консоль и файл bot_log.log")

async def main():
    """
    Основная асинхронная функция для запуска бота.

    Действия:
    1. Проверяет конфигурацию
    2. Инициализирует бота и диспетчер
    3. Регистрирует роутеры и обработчики startup/shutdown
    4. Удаляет вебхук и запускает polling

    Raises:
        ValueError: Если TELEGRAM_TOKEN не задан
        Exception: При ошибках инициализации или polling
    """
    logger.info("Запуск бота")

    # Проверка конфигурации
    if not Config.TELEGRAM_TOKEN:
        logger.error("TELEGRAM_TOKEN не задан в конфигурации")
        raise ValueError("TELEGRAM_TOKEN не задан")

    try:
        # Инициализация бота
        bot = Bot(token=Config.TELEGRAM_TOKEN)
        logger.info("Бот инициализирован")

        # Инициализация диспетчера
        dp = Dispatcher()
        logger.info("Диспетчер инициализирован")

        # Регистрация роутеров
        dp.include_router(all_handlers)

        logger.info("Роутеры зарегистрированы")

        # Регистрация функций startup и shutdown
        dp.startup.register(misc.on_start)
        dp.shutdown.register(misc.on_shutdown)
        logger.info("Обработчики startup/shutdown зарегистрированы")

        # Удаление вебхука и пропуск апдейтов
        await bot.delete_webhook(drop_pending_updates=True)
        logger.info("Вебхук удален, апдейты пропущены")

        # Запуск polling
        logger.info("Запуск polling")
        await dp.start_polling(bot)

    except Exception as e:
        logger.error(f"Ошибка при запуске бота: {str(e)}")
        raise

if __name__ == '__main__':
    # Настройка логирования
    setup_logging()

    try:
        # Запуск основной функции
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Бот остановлен пользователем (KeyboardInterrupt)")
    except Exception as e:
        logger.error(f"Критическая ошибка: {str(e)}")
    finally:
        logger.info("Завершение работы бота")