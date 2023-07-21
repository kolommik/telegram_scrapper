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
            self.conn = psycopg2.connect(dbname=db_name, user=user, password=password, host=host, port=port)
        except psycopg2.Error as e:
            logger.error(e)

    def check_and_add_channel(self, channel_id: int, channel_name: str) -> None:
        """Check if the channel exists in the Dialogs table. If not, adds it.

        Args:
        -----
            channel_id (int): The ID of the channel.
            channel_name (str): The name of the channel.
        """
        cur = self.conn.cursor()
        cur.execute(f"SELECT id FROM Dialogs WHERE id={channel_id};")
        if cur.fetchone() is None:
            cur.execute(f"INSERT INTO Dialogs (id, name) VALUES ({channel_id}, '{channel_name}');")
            self.conn.commit()
            logger.info(f"Add chanel {channel_id}")

    def add_messages(self, channel_id: int, messages: List[Message]) -> None:
        """Add messages to the Messages table.

        Args:
        -----
            channel_id (int): The ID of the channel.
            messages (list): A list of messages.
        """
        cur = self.conn.cursor()
        for message in messages:
            cur.execute(
                f"INSERT INTO Messages (id, dialog_id, text) VALUES ({message.id}, {channel_id}, '{message.text}');"
            )
        self.conn.commit()
        logger.info(f"Add {len(messages)} messages to chanel {channel_id}")
