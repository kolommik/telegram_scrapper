"""The main module for organizing the process of receiving messages from Telegram channels and storing them
in a PostgreSQL database. This module combines the functionality of TelegramScrapper and Database classes
classes from the tg_scrapper and db modules.
"""
import logging
import os
import time
import asyncio
import psycopg2
from utils.attachment_handler import AttachmentHandler
from utils.db import Database
from utils.tg_client import TelegramScrapper

logging.basicConfig(
    filename=os.path.join("logs", "main.log"),
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


class Main:
    """The main class that combines functionality of TelegramScrapper and Database."""

    def __init__(
        self,
        const_api_id: str,
        const_api_hash: str,
        const_session: str,
        const_db_name: str,
        const_user: str,
        const_password: str,
        const_db_host: str,
        const_db_port: int,
        const_images_path: str,
        const_attachments_path: str,
    ) -> None:
        """Initialize Main instance.

        Args:
        -----
            const_api_id (str): API ID provided by Telegram.
            const_api_hash (str): API Hash provided by Telegram.
            const_session (str): Session file location.
            const_db_name (str): The name of the database.
            const_user (str): The name of the user.
            const_password (str): The user's password.
            const_db_host(str): The host of the database.
            const_db_port(int): The port of the database.
        """
        logger.info("Initializing Main class...")

        try:
            self.scrapper = TelegramScrapper(
                const_api_id, const_api_hash, const_session
            )
            logger.debug(f"TelegramScrapper initialized with session: {const_session}")
        except Exception as e:
            logger.error(f"Failed to initialize TelegramScrapper: {e}")
            raise

        try:
            self.database = Database(
                const_db_name, const_user, const_password, const_db_host, const_db_port
            )
            logger.debug(
                f"Database initialized with dbname: {const_db_name}, user: {const_user}"
            )
        except Exception as e:
            logger.error(f"Failed to initialize Database: {e}")
            raise

        try:
            self.attachment_handler = AttachmentHandler(
                const_images_path, const_attachments_path
            )
        except Exception as e:
            logger.error(f"Failed to initialize AttachmentHandler: {e}")
            raise

    async def run(self) -> None:
        """Run the scrapper and store messages into the database."""
        logger.info("Attempting to connect to Telegram...")
        try:
            await self.scrapper.connect()
        except Exception as e:
            logger.error(f"Failed to connect to Telegram due to: {e}")
            return  # Если не удалось подключиться к Telegram, дальше продолжать не имеет смысла

        logger.info("Connected to Telegram.")

        # get all channels
        logger.info("Fetching dialogs...")
        try:
            dialogs = await self.scrapper.get_dialogs_list()
        except Exception as e:
            logger.error(f"Failed to fetch dialogs due to: {e}")
            return  # Если не удалось получить список диалогов, дальше продолжать не имеет смысла

        logger.debug(f"Fetched {len(dialogs)} dialogs")

        for dialog in dialogs:
            dialog_type: str = dialog.get("_", " ")
            dialog_id: int = dialog.get("id", 0)
            dialog_title: str = dialog.get("title", " ")

            try:
                logger.debug(f"Processing channel: {dialog_title}")
                self.database.check_and_add_channel(
                    dialog_id, dialog_title, dialog_type
                )

                logger.info(f"Fetching messages from {dialog_title}...")

                # Получение ID последнего сохраненного сообщения для диалога
                last_message_id = self.database.get_last_message_id(dialog_id)

                # Получение новых сообщений
                new_messages = await self.scrapper.get_new_dialog_messages(
                    dialog_id, offset_id=last_message_id, limit=50
                )
                # Сохранение новых сообщений в базу данных
                self.database.add_messages(dialog_id, new_messages)

                # Сохраняем attachments
                for message in new_messages:
                    attachments = await self.scrapper.get_message_attachments(message)

                    for attachment in attachments:
                        file_path = await self.attachment_handler.save_attachment(
                            self.scrapper.client, attachment
                        )
                        if file_path:
                            attachment_type_id = self.database.add_attachment_type(
                                attachment["type"]
                            )
                            self.database.add_attachment(
                                attachment["id"],
                                message.id,
                                dialog_id,
                                attachment_type_id,
                                file_path,
                            )
                            logger.debug(
                                f"Saved attachment for message {message.id} to {file_path}"
                            )

            except AttributeError as e:
                logger.error(f"Attribute error while processing {dialog_title}: {e}")
                continue
            except psycopg2.Error as e:
                logger.error(
                    f"Database error while processing {dialog_title}: {e.pgcode} - {e.pgerror}"
                )
                continue
            except Exception as e:
                logger.error(f"Unexpected error while processing {dialog_title}: {e}")
                continue
            else:
                logger.info(
                    f"Successfully fetched and saved {len(new_messages)} messages from {dialog_title}"
                )


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
    telegram_session = "session/telegram_session"

    # environment variables
    api_id = get_env_var("TELEGRAM_API_ID")
    api_hash = get_env_var("TELEGRAM_API_HASH")

    db_name = get_env_var("POSTGRES_DB")
    user = get_env_var("POSTGRES_USER")
    password = get_env_var("POSTGRES_PASSWORD")

    db_host = get_env_var("DB_HOST")
    db_port = int(get_env_var("DB_PORT"))

    # need some time to up posgressql
    time.sleep(10)

    # initialize main class
    app = Main(
        const_api_id=api_id,
        const_api_hash=api_hash,
        const_session=telegram_session,
        const_db_name=db_name,
        const_user=user,
        const_password=password,
        const_db_host=db_host,
        const_db_port=db_port,
        const_images_path="/data/images",
        const_attachments_path="/data/attachments",
    )

    logger.info("Main loop")
    loop = asyncio.get_event_loop()
    loop.run_until_complete(app.run())
