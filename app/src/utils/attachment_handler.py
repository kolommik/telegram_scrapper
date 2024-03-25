"""
Модуль для обработки и сохранения вложений из сообщений Telegram.

Этот модуль содержит класс `AttachmentHandler`, который предоставляет методы для сохранения различных
типов вложений, полученных из сообщений Telegram, в локальной файловой системе.
"""

import os
from telethon.sync import TelegramClient


class AttachmentHandler:
    """
    Класс для обработки и сохранения вложений из сообщений Telegram.

    Attributes:
    -----------
    images_path : str
        Путь к директории для сохранения изображений.
    attachments_path : str
        Путь к директории для сохранения остальных типов вложений.

    Methods:
    --------
    async save_attachment(client: TelegramClient, attachment: dict) -> str:
        Сохраняет вложение и возвращает путь к файлу.
    """

    def __init__(self, images_path: str, attachments_path: str):
        """
        Инициализирует объект класса AttachmentHandler.

        Parameters:
        -----------
        images_path : str
            Путь к директории для сохранения изображений.
        attachments_path : str
            Путь к директории для сохранения остальных типов вложений.
        """
        self.images_path = images_path
        self.attachments_path = attachments_path
        os.makedirs(images_path, exist_ok=True)
        os.makedirs(attachments_path, exist_ok=True)

    async def save_attachment(self, client: TelegramClient, attachment: dict) -> str:
        """
        Сохраняет вложение и возвращает путь к файлу.

        Parameters:
        -----------
        client : TelegramClient
            Клиент Telegram для скачивания медиафайлов.
        attachment : dict
            Словарь с информацией о вложении.

        Returns:
        --------
        str
            Путь к сохраненному файлу или None, если сохранение не удалось.
        """
        file_path = None

        try:
            # photo - фотки берем
            # document - документы берем

            # web_preview - не берем, превью не нужно
            # audio - не берем, не ясно как юзать
            # voice - не берем, не ясно как юзать
            # video - не берем, не ясно как юзать
            # video_note - не берем, не ясно как юзать
            # gif - не берем, это как правило фигня
            # sticker - не берем, не нужно

            if attachment["type"] == "photo":
                file_path = os.path.join(self.images_path, f"{attachment['id']}.jpg")
                await client.download_media(attachment["file"], file=file_path)
            elif attachment["type"] == "document":
                file_path = os.path.join(
                    self.attachments_path, f"{attachment['id']}{attachment['ext']}"
                )
                await client.download_media(attachment["file"], file=file_path)

        except OSError as e:
            print(f"При сохранении вложения произошла ошибка: {e}")
            file_path = None
        except Exception as e:
            print(f"Произошла неожиданная ошибка: {e}")
            file_path = None

        return file_path
