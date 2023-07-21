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

    async def get_channel_messages(self, channel_name: str, limit: int = 10) -> Tuple[int, str, List[Message]]:
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
        messages = self.client.iter_messages(channel_id, limit=limit)

        # channel = await self.client.get_entity(channel_name)
        # messages = await self.client.get_message_history(channel, limit=limit)
        logger.info(f"Got {len(messages)} messages from {channel_name}")

        return channel_id, channel_name, messages
