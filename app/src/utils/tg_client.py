"""Модуль для взаимодействия с Telegram через библиотеку Telethon.

Этот модуль предоставляет класс TelegramScrapper для получения сообщений из указанных каналов Telegram.
"""

import os
from typing import List
import logging
from telethon import utils
from telethon.sync import TelegramClient
from telethon.tl.custom.message import Message
from telethon.tl.functions.messages import GetRepliesRequest

logger = logging.getLogger(__name__)


class TelegramScrapper:
    """
    Класс для взаимодействия с Telegram через Telethon.

    Attributes:
    -----------
    api_id : str
        API ID, предоставленный Telegram.
    api_hash : str
        API Hash, предоставленный Telegram.
    session : str
        Расположение файла сессии.
    """

    def __init__(self, api_id: str, api_hash: str, session: str) -> None:
        """
        Инициализация экземпляра TelegramScrapper.

        Parameters:
        -----------
        api_id : str
            API ID, предоставленный Telegram.
        api_hash : str
            API Hash, предоставленный Telegram.
        session : str
            Расположение файла сессии.
        """
        self.client = TelegramClient(session, api_id, api_hash)
        logger.info("TelegramClient initialized")

    async def connect(self) -> None:
        """Подключение к Telegram"""
        await self.client.connect()
        logger.info("TelegramClient connected")

    async def get_dialogs_list(self) -> List[dict]:
        """Получить список диалогов.

        Returns:
        --------
        List[dict]
            Список диалогов с свойствами:
            {
                "_": "Channel",
                "id": 112233445566,
                "title": "Channel Title",
            }

        """
        dialogs = await self.client.get_dialogs()
        logger.info(f"Got {len(dialogs)} channels")

        results = []
        selected_keys = ["_", "id", "title"]

        for dialog in dialogs:
            raw_dialog_dict = dialog.entity.to_dict()
            final_dialog_dict = {
                key: raw_dialog_dict[key]
                for key in selected_keys
                if key in raw_dialog_dict
            }

            # for User dialogs, the title from entity is None
            if final_dialog_dict.get("title", None) is None:
                final_dialog_dict["title"] = dialog.title

            results.append(final_dialog_dict)

        return results

    async def get_new_dialog_messages(
        self, dialog_id: int, offset_id: int = 0, limit: int = 10
    ) -> List[Message]:
        """Получить новые сообщения для диалога, начиная с определенного offset_id.

        Parameters:
        -----------
            dialog_id : int
                ID диалога.
            offset_id : int
                ID сообщения, с которого начать извлечение сообщений.
            limit : int
                Количество извлекаемых сообщений.

        Returns:
        --------
            List[Message]: Список новых сообщений.
        """
        messages = await self.client.get_messages(
            dialog_id, offset_id=offset_id, limit=limit, reverse=True
        )
        return messages

    async def get_message_attachments(self, message: Message) -> List[dict]:
        """Получить вложения из сообщения.

        Parameters:
        -----------
            message : Message
                Объект сообщения из Telethon.

        Returns:
        --------
            List[dict]: Список вложений с их свойствами.
        """
        attachments = []
        if message.photo:
            attachments.append(
                {"type": "photo", "id": message.photo.id, "file": message.photo}
            )
        if message.document:
            file_name = message.file.name
            file_ext = os.path.splitext(file_name)[1]
            attachments.append(
                {
                    "type": "document",
                    "id": message.document.id,
                    "file": message.document,
                    "ext": file_ext,
                }
            )

        return attachments

    async def get_message_replies(self, channel_id, message_id, limit=10) -> List[dict]:
        """Получить ответы на сообщение.

        Parameters:
        -----------
            channel_id : int
                ID канала.
            message_id : int
                ID сообщения, для которого нужно получить ответы.
            limit : int
                Количество извлекаемых ответов.

        Returns:
        --------
            List[dict]: Список ответов с их свойствами.
        """
        replies = []
        thread = await self.client(
            GetRepliesRequest(
                peer=channel_id,
                msg_id=message_id,
                offset_id=0,
                limit=limit,
                offset_date=None,
                add_offset=0,
                max_id=0,
                min_id=0,
                hash=0,
            )
        )

        for reply in thread.messages:
            sender_id = utils.get_peer_id(reply.from_id) if reply.from_id else None
            replies.append(
                {
                    "id": reply.id,
                    "reply_to_message_id": reply.reply_to_msg_id,
                    "reply_to_dialog_id": reply.peer_id.channel_id,
                    "content": reply.message,
                    "sender_id": sender_id,
                    "date": reply.date.strftime("%Y-%m-%d %H:%M:%S"),
                }
            )

        return replies
