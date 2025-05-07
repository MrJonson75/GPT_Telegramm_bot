import asyncio
from aiogram import Bot, Dispatcher
import misc
import logging
from hendlers import all_handlers
from config import Config



async def main():
    """
    Основная асинхронная функция для запуска бота.

    Инициализирует бота, диспетчер, регистрирует обработчики и запускает polling.
    """
    # Инициализация бота с токеном из переменных окружения
    bot = Bot(token=Config.TELEGRAM_TOKEN)

    # Удаление вебхука (если был установлен) и пропуск накопившихся апдейтов
    await bot.delete_webhook(drop_pending_updates=True)

    # Инициализация диспетчера
    dp = Dispatcher()

    # Подключение всех обработчиков из модуля handlers
    dp.include_routers(all_handlers)

    # Регистрация функций, которые будут вызваны при старте и остановке бота
    dp.startup.register(misc.on_start)
    dp.shutdown.register(misc.on_shutdown)

    # Запуск бота в режиме polling (постоянный опрос серверов Telegram)
    await dp.start_polling(bot)


if __name__ == '__main__':
    # Настройка логирования в файл bot_log.log с уровнем INFO
    # logging.basicConfig(filename='bot_log.log', level=logging.INFO)

    try:
        # Запуск основной асинхронной функции
        asyncio.run(main())
    except KeyboardInterrupt:
        # Корректная обработка прерывания с клавиатуры (Ctrl+C)
        pass