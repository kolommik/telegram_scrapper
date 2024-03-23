"""A module for interacting with Telegram via the Telethon library.
This module provides the TelegramScrapper class to retrieve messages from specified Telegram channels.
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
    """A class used to interact with Telegram via Telethon."""

    def __init__(self, api_id: str, api_hash: str, session: str) -> None:
        """Initialize TelegramScrapper instance.

        Args:
        -----
            api_id (str): API ID provided by Telegram.
            api_hash (str): API Hash provided by Telegram.
            session (str): Session file location.
        """
        self.client = TelegramClient(session, api_id, api_hash)
        logger.info("TelegramClient initialized")

    async def connect(self) -> None:
        """Connect to Telegram."""
        await self.client.connect()
        logger.info("TelegramClient connected")

    async def get_dialogs_list(self) -> List[dict]:
        """Get a list of dalogs.

        Returns
        -------
        List[dict]
            A list of dalogs with properties:
            {
                "_": "Channel",
                "id": 1380524958,
                "title": "Хулиномика",
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
        """Get new messages for a dialog starting from a specific offset_id.

        Args:
            dialog_id (int): The ID of the dialog.
            offset_id (int): The message ID from which to start fetching messages.
            limit (int): The number of messages to retrieve.

        Returns:
            List[Message]: A list of new messages.
        """
        messages = await self.client.get_messages(
            dialog_id, offset_id=offset_id, limit=limit, reverse=True
        )
        return messages

    async def get_message_attachments(self, message: Message) -> List[dict]:
        """Get attachments from a message.

        Args:
            message (Message): The message object from Telethon.

        Returns:
            List[dict]: A list of attachments with their properties.
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
        """Get replies for a message.

        Args:
            channel_id (int): The ID of the channel.
            message_id (int): The ID of the message to get replies for.
            limit (int): The number of replies to retrieve.

        Returns:
            List[dict]: A list of replies with their properties.
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
