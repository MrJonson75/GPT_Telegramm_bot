import logging

from aiogram.types import FSInputFile

from config import Config
from keybords import Keyboards

# Настройка логирования
logger = logging.getLogger(__name__)



async def callback_finality(callback):
    answer_text = Config.get_messages('main')
    image_path = Config.IMAGE_PATHS['main']
    try:
        photo = FSInputFile(path=image_path)
        await callback.message.answer_photo(
            photo=photo,
            caption=answer_text,
            reply_markup=Keyboards.main_menu()
        )
        logger.debug(f"Отправлено изображение {image_path} с подписью для user_id={callback.from_user.id}")
    except KeyError:
        logger.warning(f"Изображение 'main' не найдено в Config.IMAGE_PATHS")
        await callback.message.answer(
            answer_text,
            reply_markup=Keyboards.main_menu()
        )
    except FileNotFoundError:
        logger.error(f"Файл изображения {image_path} не найден")
        await callback.message.answer(
            answer_text,
            reply_markup=Keyboards.main_menu()
        )
    except Exception as e:
        logger.error(f"Ошибка отправки изображения: {str(e)}")
        await callback.message.answer(
            "Произошла ошибка. Попробуйте позже.",
            reply_markup=Keyboards.main_menu()
        )

