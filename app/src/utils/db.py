"""A module for interacting with PostgreSQL database.
The module provides the Database class to manage channels and messages in the database.
"""
from typing import List
import logging
import psycopg2
from telethon.tl.custom.message import Message

logger = logging.getLogger(__name__)


class Database:
    """A class used to interact with the PostgreSQL database."""

    def __init__(
        self,
        db_name: str,
        user: str,
        password: str,
        host: str = "localhost",
        port: str = "5432",
    ) -> None:
        """Initialize Database instance.

        Args:
        -----
            db_name (str): The name of the database.
            user (str): The name of the user.
            password (str): The user's password.
            host (str): The host of the PostgreSQL server. Defaults to localhost.
            port (str): The port of the PostgreSQL server. Defaults to 5432.
        """
        try:
            self.conn = psycopg2.connect(
                dbname=db_name, user=user, password=password, host=host, port=port
            )
        except psycopg2.Error as e:
            logger.error(e)
            raise

    def check_and_add_channel(
        self, dialog_id: int, dialog_title: str, dialog_type: str
    ) -> None:
        """Check if the dialog exists in the Dialogs table. If not, adds it.
        Also adds the dialog type to the DialogTypes table if it does not exist.

        Args:
        -----
            dialog_id (int): The ID of the dialog.
            dialog_title (str): The name of the dialog.
            dialog_type (str): The type of the dialog.
        """
        # check if the dialog type exists
        cursor = self.conn.cursor()
        try:
            cursor.execute("SELECT id FROM DialogTypes WHERE name = %s;", (dialog_type,))
            query_results = cursor.fetchone()
            if query_results is not None:
                type_id = query_results[0]
                logger.info(f"DialogType {dialog_type} already exists")
            else:
                cursor.execute(
                    "INSERT INTO DialogTypes (name) VALUES (%s) RETURNING id;",
                    (dialog_type,)
                )
                type_id = cursor.fetchone()[0]
                self.conn.commit()
                logger.info(f"Add DialogType {dialog_type}")

            # check if the dialog exists
            cursor.execute("SELECT id FROM Dialogs WHERE id = %s;", (dialog_id,))
            if cursor.fetchone() is None:
                cursor.execute(
                    "INSERT INTO Dialogs (id, dialogtype_id, name) VALUES (%s, %s, %s);",
                    (dialog_id, type_id, dialog_title)
                )
                self.conn.commit()
                logger.info(f"Add channel {dialog_id}: {dialog_title}")

            cursor.close()
        except psycopg2.Error as e:
            logger.error(f"Failed to check and add channel: {e}")
            self.conn.rollback()
        finally:
            if cursor:
                cursor.close()

    def add_messages(self, channel_id: int, messages: List[Message]) -> None:
        """Add messages to the Messages table.

        Args:
        -----
            channel_id (int): The ID of the channel.
            messages (list): A list of messages.
        """
        cursor = self.conn.cursor()
        try:
            for message in messages:
                text = message.message or ""
                created = message.date.strftime("%Y-%m-%d %H:%M:%S")
                grouped_id = getattr(message, "grouped_id", None)

                query = """INSERT INTO Messages (id, dialog_id, text, created, grouped_id)
                        VALUES (%s, %s, %s, %s, %s)
                        ON CONFLICT (dialog_id, id) DO NOTHING;"""
                data_tuple = (message.id, channel_id, text, created, grouped_id)

                cursor.execute(query, data_tuple)
            self.conn.commit()
            logger.info(f"Add {len(messages)} messages to channel {channel_id}")

            cursor.close()
        except psycopg2.Error as e:
            logger.error(f"Failed to add messages: {e}")
            self.conn.rollback()
        finally:
            if cursor:
                cursor.close()

    def get_last_message_id(self, dialog_id: int) -> int:
        """Get the ID of the last saved message for a dialog.

        Args:
            dialog_id (int): The ID of the dialog.

        Returns:
            int: The ID of the last message or 0 if no messages are saved.
        """
        cursor = self.conn.cursor()
        try:
            cursor.execute(
                "SELECT MAX(id) FROM Messages WHERE dialog_id = %s;", (dialog_id,)
            )
            last_message_id = cursor.fetchone()[0]
            cursor.close()
            return last_message_id or 0
        except psycopg2.Error as e:
            logger.error(f"Failed to get last message ID: {e}")
            self.conn.rollback()
            return 0
        finally:
            if cursor:
                cursor.close()

    def add_attachment_type(self, attachment_type: str) -> int:
        """Add a new attachment type if it doesn't exist and return its ID.

        Args:
            attachment_type (str): The type of the attachment.

        Returns:
            int: The ID of the attachment type.
        """
        cursor = self.conn.cursor()
        try:
            cursor.execute(
                "SELECT id FROM AttachmentTypes WHERE type = %s;", (attachment_type,)
            )
            type_id = cursor.fetchone()
            if type_id is None:
                cursor.execute(
                    "INSERT INTO AttachmentTypes (type) VALUES (%s) RETURNING id;",
                    (attachment_type,),
                )
                type_id = cursor.fetchone()[0]
                self.conn.commit()
            cursor.close()
            return type_id or 0
        except psycopg2.Error as e:
            logger.error(f"Failed to add attachment type: {e}")
            self.conn.rollback()
            return 0
        finally:
            if cursor:
                cursor.close()

    def add_attachment(
        self,
        attachment_id: int,
        message_id: int,
        dialog_id: int,
        attachment_type_id: int,
        file_path: str,
    ) -> None:
        """Add an attachment to the Attachments table.

        Args:
            attachment_id (int): The ID of the attachment.
            message_id (int): The ID of the message the attachment belongs to.
            dialog_id (int): The ID of the dialog the attachment belongs to.
            attachment_type_id (int): The ID of the attachment type.
            file_path (str): The file path of the attachment.
        """
        cursor = self.conn.cursor()
        try:
            cursor.execute(
                """INSERT INTO Attachments (id, message_id, dialog_id, type_id, file_path)
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (id) DO NOTHING;""",
                (attachment_id, message_id, dialog_id, attachment_type_id, file_path),
            )
            self.conn.commit()
            cursor.close()
        except psycopg2.Error as e:
            logger.error(f"Failed to add attachment: {e}")
            self.conn.rollback()
        finally:
            if cursor:
                cursor.close()
