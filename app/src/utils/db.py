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
        cur = self.conn.cursor()
        cur.execute(f"SELECT id FROM DialogTypes WHERE name='{dialog_type}';")
        sql_results = cur.fetchone()
        if sql_results is not None:
            type_id = sql_results[0]
            logger.info(f"DialogType {dialog_type} already exists")
        else:
            cur.execute(
                f"INSERT INTO DialogTypes (name) VALUES ('{dialog_type}') RETURNING id;"
            )
            type_id = cur.fetchone()[0]
            self.conn.commit()
            logger.info(f"Add DialogType {dialog_type}")

        # check if the dialog exists
        cur.execute(f"SELECT id FROM Dialogs WHERE id={dialog_id};")
        if cur.fetchone() is None:
            cur.execute(
                f"INSERT INTO Dialogs (id, dialogtype_id, name) VALUES ({dialog_id}, {type_id}, '{dialog_title}');"
            )
            self.conn.commit()
            logger.info(f"Add chanel {dialog_id}")

        cur.close()

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

        cur.close()
