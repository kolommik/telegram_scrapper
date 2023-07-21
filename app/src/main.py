"""The main module for organizing the process of receiving messages from Telegram channels and storing them
in a PostgreSQL database. This module combines the functionality of TelegramScrapper and Database classes
classes from the tg_scrapper and db modules.
"""
import logging
import os
import time
from typing import List
import asyncio
from utils.tg_client import TelegramScrapper
from utils.db import Database

# Set up logging
logging.basicConfig(
    filename=os.path.join("logs", "main.log"),  # log file location
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",  # log file format
)

# Create logger
logger = logging.getLogger(__name__)


class Main:
    """The main class that combines functionality of TelegramScrapper and Database."""

    def __init__(
        self,
        channels_list: List[str],
        const_api_id: str,
        const_api_hash: str,
        const_session: str,
        const_db_name: str,
        const_user: str,
        const_password: str,
        const_db_host: str,
        const_db_port: int,
    ) -> None:
        """Initialize Main instance.

        Args:
        -----
            channels_list (list): The list of channels.
            const_api_id (str): API ID provided by Telegram.
            const_api_hash (str): API Hash provided by Telegram.
            const_session (str): Session file location.
            const_db_name (str): The name of the database.
            const_user (str): The name of the user.
            const_password (str): The user's password.
            const_db_host(str): The host of the database.
            const_db_port(int): The port of the database.
        """
        self.channels = channels_list
        logger.info("Initializing Main class...")

        self.scrapper = TelegramScrapper(const_api_id, const_api_hash, const_session)
        logger.debug(f"TelegramScrapper initialized with session: {const_session}")

        self.database = Database(const_db_name, const_user, const_password, const_db_host, const_db_port)
        logger.debug(f"Database initialized with dbname: {const_db_name}, user: {const_user}")

    async def run(self) -> None:
        """Run the scrapper and store messages into the database."""
        logger.info("Attempting to connect to Telegram...")
        await self.scrapper.connect()
        logger.info("Connected to Telegram.")

        for channel in self.channels:
            logger.info(f"Fetching messages from {channel}...")

            try:
                (
                    channel_id,
                    channel_name,
                    messages,
                ) = await self.scrapper.get_channel_messages(channel)
                logger.debug(f"Fetched {len(messages)} messages from {channel_name} (ID: {channel_id})")

                self.database.check_and_add_channel(channel_id, channel_name)
                logger.debug(f"Checked and added channel: {channel_name}")

                self.database.add_messages(channel_id, messages)
                logger.debug(f"Added messages to database for channel: {channel_name}")

            except Exception as e:
                logger.error(f"Failed to fetch messages from {channel} due to {e}")
            else:
                logger.info(f"Successfully fetched and saved messages from {channel}")


def get_env_var(var_name: str) -> str:
    """Get environment variable and log an error if it's not set."""
    value = os.environ.get(var_name)
    if not value:
        logger.error(f"Environment variable {var_name} is not set!")
        raise RuntimeError(f"{var_name} is not set")
    return value


if __name__ == "__main__":
    logger.info("Start running")

    # telegram session file location (hardcode)
    TELEGRAM_SESSON = "session/telegram_session"

    # environment variables
    api_id = get_env_var("TELEGRAM_API_ID")
    api_hash = get_env_var("TELEGRAM_API_HASH")
    channels_str = get_env_var("TELEGRAM_CHANNELS")

    db_name = get_env_var("POSTGRES_DB")
    user = get_env_var("POSTGRES_USER")
    password = get_env_var("POSTGRES_PASSWORD")

    db_host = get_env_var("DB_HOST")
    db_port = int(get_env_var("DB_PORT"))

    # list of channels
    channels = [channel.strip() for channel in channels_str.split(",")]

    # need some time to up posgress
    time.sleep(5)

    # initialize main class
    app = Main(channels, api_id, api_hash, TELEGRAM_SESSON, db_name, user, password, db_host, db_port)

    # main loop
    logger.info("Main loop")
    loop = asyncio.get_event_loop()
    loop.run_until_complete(app.run())
