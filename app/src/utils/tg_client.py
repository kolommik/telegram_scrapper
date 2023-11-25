"""A module for interacting with Telegram via the Telethon library.
This module provides the TelegramScrapper class to retrieve messages from specified Telegram channels.
"""
from typing import List, Tuple
import logging
from telethon.sync import TelegramClient, utils
from telethon.tl.custom.message import Message

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
            if raw_dialog_dict.get("title", None) is None:
                raw_dialog_dict["title"] = dialog.title

            results.append(final_dialog_dict)

        return results

    async def get_channel_messages(
        self, channel_name: str, limit: int = 10
    ) -> Tuple[int, str, List[Message]]:
        """Get a specified amount of messages from a channel.

        Args:
        -----
            channel_name (str): The name of the channel.
            limit (int): The number of messages to retrieve.
        Returns:
            A list of messages.
        """
        entity = await self.client.get_entity(channel_name)
        channel_id = utils.get_peer_id(entity)
        # messages = self.client.iter_messages(channel_id, limit=limit)
        messages_list = []
        async for message in self.client.iter_messages(channel_id, limit=limit):
            messages_list.append(message)

        # channel = await self.client.get_entity(channel_name)
        # messages = await self.client.get_message_history(channel, limit=limit)
        logger.info(f"Got {len(messages_list)} messages from {channel_name}")

        return channel_id, channel_name, messages_list
