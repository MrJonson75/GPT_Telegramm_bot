from aiogram.types import Message, FSInputFile


async def send_image(message: Message, image_path: str) -> None:
    """
    Отправляет изображение пользователю в Telegram чат.

    Args:
        message (Message): Объект сообщения от aiogram, содержащий информацию о чате.
        image_path (str): Путь к файлу изображения на сервере.

    Returns:
        None: Функция ничего не возвращает, но отправляет изображение в чат или сообщение об ошибке.

    Raises:
        Exception: Ловит любые исключения при отправке изображения и отправляет сообщение об ошибке пользователю.
    """
    try:
        # Создаем объект FSInputFile из указанного пути
        photo = FSInputFile(image_path)

        # Отправляем изображение в чат
        await message.answer_photo(photo)
    except Exception as e:
        # В случае ошибки отправляем сообщение с описанием проблемы
        await message.answer(f"Не удалось отправить изображение: {e}")