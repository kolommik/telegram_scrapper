"""Основной модуль для организации процесса получения сообщений из каналов Telegram и их хранения
в базе данных PostgreSQL. Этот модуль объединяет функциональность классов TelegramScrapper и Database
из модулей tg_scrapper и db.
"""

import logging
import os
import asyncio
from utils.attachment_handler import AttachmentHandler
from utils.db import Database
from utils.tg_client import TelegramScrapper
from utils.config import (
    LOGS_DIR,
    IMAGES_DIR,
    ATTACHMENTS_DIR,
    TELEGRAM_SESSION_FILE,
    DEBUG_MODE,
    DEBUG_CHANNEL_ID,
    DEBUG_MESSAGE_ID_THRESHOLD,
    MESSAGE_FETCH_LIMIT,
    REPLY_FETCH_LIMIT,
)

logging.basicConfig(
    filename=os.path.join(LOGS_DIR, "main.log"),
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


class Main:
    """
    Основной класс, объединяющий функциональность TelegramScrapper и Database.

    Attributes:
    -----------
    const_api_id : str
        API ID, предоставленный Telegram.
    const_api_hash : str
        API Hash, предоставленный Telegram.
    const_session : str
        Расположение файла сессии.
    const_db_name : str
        Название базы данных.
    const_user : str
        Имя пользователя базы данных.
    const_password : str
        Пароль пользователя базы данных.
    const_db_host : str
        Хост базы данных.
    const_db_port : int
        Порт базы данных.
    const_images_path : str
        Путь к директории для сохранения изображений.
    const_attachments_path : str
        Путь к директории для сохранения остальных типов вложений.
    scrapper : TelegramScrapper
        Экземпляр класса для взаимодействия с Telegram.
    database : Database
        Экземпляр класса для взаимодействия с базой данных PostgreSQL.
    attachment_handler : AttachmentHandler
        Экземпляр класса для обработки и сохранения вложений.
    """

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
        """Инициализация экземпляра Main.

        Parameters:
        -----------
            const_api_id : str
                API ID, предоставленный Telegram.
            const_api_hash : str
                API Hash, предоставленный Telegram.
            const_session : str
                Расположение файла сессии.
            const_db_name : str
                Название базы данных.
            const_user : str
                Имя пользователя.
            const_password : str
                Пароль пользователя.
            const_db_host : str
                Хост базы данных.
            const_db_port : int
                Порт базы данных.
        """
        logger.info("Инициализация класса Main")

        try:
            self.scrapper = TelegramScrapper(
                const_api_id, const_api_hash, const_session
            )
            logger.debug(f"TelegramScrapper инициализирован с сессией: {const_session}")
        except Exception as e:
            logger.error(f"Не удалось инициализировать TelegramScrapper: {e}")
            raise

        try:
            self.database = Database(
                const_db_name, const_user, const_password, const_db_host, const_db_port
            )
            logger.debug(
                f"База данных инициализирована с dbname: {const_db_name}, user: {const_user}"
            )
        except Exception as e:
            logger.error(f"Не удалось инициализировать базу данных: {e}")
            raise

        try:
            self.attachment_handler = AttachmentHandler(
                const_images_path, const_attachments_path
            )
        except Exception as e:
            logger.error(f"Не удалось инициализировать AttachmentHandler: {e}")
            raise

    async def run(self) -> None:
        """
        Запуск скраппера и сохранение сообщений в базу данных.
        """
        logger.info("Попытка подключения к Telegram.")
        try:
            await self.scrapper.connect()
        except Exception as e:
            logger.error(f"Не удалось подключиться к Telegram из-за: {e}")
            return  # Если не удалось подключиться к Telegram, дальше продолжать не имеет смысла

        logger.info("Подключено к Telegram.")

        # get all channels
        logger.info("Получение списка диалогов.")
        try:
            dialogs = await self.scrapper.get_dialogs_list()
        except Exception as e:
            logger.error(f"Не удалось получить список диалогов из-за: {e}")
            return  # Если не удалось получить список диалогов, дальше продолжать не имеет смысла

        # FOR DEBUG ------------------------------------------------------
        if DEBUG_MODE:
            dialogs = [
                dialog for dialog in dialogs if dialog.get("id") == DEBUG_CHANNEL_ID
            ]
        # FOR DEBUG ------------------------------------------------------

        logger.debug(f"Получено {len(dialogs)} диалогов")

        for dialog in dialogs:
            dialog_type: str = dialog.get("_", " ")
            dialog_id: int = dialog.get("id", 0)
            dialog_title: str = dialog.get("title", " ")

            try:
                logger.debug(f"Обработка канала: {dialog_title}")
                self.database.check_and_add_channel(
                    dialog_id, dialog_title, dialog_type
                )
            except Exception as e:
                logger.error(f"Ошибка при добавлении канала {dialog_title}: {e}")
                continue

            try:
                logger.info(f"Получение сообщений из {dialog_title}...")
                last_message_id = self.database.get_last_message_id(dialog_id)

                # FOR DEBUG ------------------------------------------------------
                if DEBUG_MODE:
                    last_message_id = max(DEBUG_MESSAGE_ID_THRESHOLD, last_message_id)
                # FOR DEBUG ------------------------------------------------------

                new_messages = await self.scrapper.get_new_dialog_messages(
                    dialog_id, offset_id=last_message_id, limit=MESSAGE_FETCH_LIMIT
                )
                self.database.add_messages(dialog_id, new_messages)
            except Exception as e:
                logger.error(
                    f"Ошибка при получении или сохранении сообщений из {dialog_title}: {e}"
                )
                continue

            # пробегаемся по всем сообщениям
            for message in new_messages:
                # Обработка и сохранение приложенных к сообщению файлов
                try:
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
                                f"Сохранено вложение для сообщения {message.id} в {file_path}"
                            )
                except Exception as e:
                    logger.error(
                        f"Ошибка при обработке вложений для сообщения {message.id} в {dialog_title}: {e}"
                    )

                # Обработка и сохранение ответов на сообщения
                try:
                    if message.replies and message.replies.comments:
                        replies = await self.scrapper.get_message_replies(
                            dialog_id, message.id, limit=REPLY_FETCH_LIMIT
                        )
                        last_reply_id = self.database.get_last_reply_id(
                            dialog_id, message.id
                        )
                        for reply in replies:
                            if reply["id"] > last_reply_id:
                                self.database.add_reply(
                                    reply_id=reply["id"],
                                    main_dialog_id=dialog_id,
                                    main_message_id=message.id,
                                    reply_to_dialog_id=reply["reply_to_dialog_id"],
                                    reply_to_msg_id=reply["reply_to_message_id"],
                                    content=reply["content"],
                                    sender_id=reply["sender_id"],
                                    date=reply["date"],
                                )
                                logger.debug(
                                    f"Сохранен ответ {reply['id']} на сообщение {message.id}"
                                )
                except Exception as e:
                    logger.error(
                        f"Ошибка при обработке ответов на сообщение {message.id} в {dialog_title}: {e}"
                    )


def get_env_var(var_name: str) -> str:
    """
    Получение переменной окружения и запись ошибки, если она не установлена.
    """
    value = os.environ.get(var_name)
    if not value:
        logger.error(f"Переменная окружения {var_name} не установлена!")
        raise RuntimeError(f"{var_name} is not set")
    return value


if __name__ == "__main__":
    logger.info("Начало выполнения")

    # telegram session file location (hardcode)
    telegram_session = TELEGRAM_SESSION_FILE

    # environment variables
    api_id = get_env_var("TELEGRAM_API_ID")
    api_hash = get_env_var("TELEGRAM_API_HASH")

    db_name = get_env_var("POSTGRES_DB")
    user = get_env_var("POSTGRES_USER")
    password = get_env_var("POSTGRES_PASSWORD")

    db_host = get_env_var("DB_HOST")
    db_port = int(get_env_var("DB_PORT"))

    # need some time to up posgressql
    # time.sleep(10)

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
        const_images_path=IMAGES_DIR,
        const_attachments_path=ATTACHMENTS_DIR,
    )

    logger.info("Основной цикл")
    loop = asyncio.get_event_loop()
    loop.run_until_complete(app.run())
