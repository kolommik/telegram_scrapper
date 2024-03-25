"""Модуль для взаимодействия с базой данных PostgreSQL.

Этот модуль предоставляет класс Database для управления каналами и сообщениями в базе данных.
"""

from typing import List
import logging
import psycopg2
from telethon.tl.custom.message import Message

logger = logging.getLogger(__name__)


class Database:
    """
    Класс для взаимодействия с базой данных PostgreSQL.

    Attributes:
    -----------
    db_name : str
        Имя базы данных.
    user : str
        Имя пользователя.
    password : str
        Пароль пользователя.
    host : str
        Хост сервера PostgreSQL. По умолчанию localhost.
    port : str
        Порт сервера PostgreSQL. По умолчанию 5432.
    """

    def __init__(
        self,
        db_name: str,
        user: str,
        password: str,
        host: str = "localhost",
        port: str = "5432",
    ) -> None:
        """
        Инициализация экземпляра Database.

        Parameters:
        -----------
        db_name : str
            Имя базы данных.
        user : str
            Имя пользователя.
        password : str
            Пароль пользователя.
        host : str
            Хост сервера PostgreSQL. По умолчанию localhost.
        port : str
            Порт сервера PostgreSQL. По умолчанию 5432.
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
        """
        Проверяет существование диалога в таблице Dialogs. Если нет, добавляет его.
        Также добавляет тип диалога в таблицу DialogTypes, если он не существует.

        Parameters:
        -----------
        dialog_id : int
            ID диалога.
        dialog_title : str
            Название диалога.
        dialog_type : str
            Тип диалога.
        """
        # проверяем существование типа диалога
        cursor = self.conn.cursor()
        try:
            cursor.execute(
                "SELECT id FROM DialogTypes WHERE name = %s;", (dialog_type,)
            )
            query_results = cursor.fetchone()
            if query_results is not None:
                type_id = query_results[0]
                logger.info(f"Тип диалога {dialog_type} уже существует")
            else:
                cursor.execute(
                    "INSERT INTO DialogTypes (name) VALUES (%s) RETURNING id;",
                    (dialog_type,),
                )
                type_id = cursor.fetchone()[0]
                self.conn.commit()
                logger.info(f"Добавлен тип диалога {dialog_type}")

            # проверяем существование диалога
            cursor.execute("SELECT id FROM Dialogs WHERE id = %s;", (dialog_id,))
            if cursor.fetchone() is None:
                cursor.execute(
                    "INSERT INTO Dialogs (id, dialogtype_id, name) VALUES (%s, %s, %s);",
                    (dialog_id, type_id, dialog_title),
                )
                self.conn.commit()
                logger.info(f"Добавлен канал {dialog_id}: {dialog_title}")

            cursor.close()
        except psycopg2.Error as e:
            logger.error(f"Ошибка при проверке и добавлении канала: {e}")
            self.conn.rollback()
        finally:
            cursor.close()

    def add_messages(self, channel_id: int, messages: List[Message]) -> None:
        """Добавляет сообщения в таблицу Messages.

        Parameters:
        -----------
            channel_id : int
                ID канала.
            messages : list
                Список сообщений.
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
            logger.info(f"Добавлено {len(messages)} сообщений в канал {channel_id}")

            cursor.close()
        except psycopg2.Error as e:
            logger.error(f"Ошибка при добавлении сообщений: {e}")
            self.conn.rollback()
        finally:
            cursor.close()

    def get_last_message_id(self, dialog_id: int) -> int:
        """Получает ID последнего сохраненного сообщения для диалога.

        Parameters:
        -----------
            dialog_id : int
                ID диалога.

        Returns:
        --------
            int : ID последнего сообщения или 0, если сообщения не сохранены.
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
            logger.error(f"Ошибка при получении ID последнего сообщения: {e}")
            self.conn.rollback()
            return 0
        finally:
            cursor.close()

    def add_attachment_type(self, attachment_type: str) -> int:
        """Добавляет новый тип вложения, если он не существует, и возвращает его ID.

        Parameters:
        -----------
            attachment_type : str
                Тип вложения.

        Returns:
        --------
            int: ID типа вложения.
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
            logger.error(f"Ошибка при добавлении типа вложения: {e}")
            self.conn.rollback()
            return 0
        finally:
            cursor.close()

    def add_attachment(
        self,
        attachment_id: int,
        message_id: int,
        dialog_id: int,
        attachment_type_id: int,
        file_path: str,
    ) -> None:
        """Добавляет вложение в таблицу Attachments.

        Parameters:
        -----------
            attachment_id : int
                ID вложения.
            message_id : int
                ID сообщения, к которому относится вложение.
            dialog_id : int
                ID диалога, к которому относится вложение.
            attachment_type_id : int
                ID типа вложения.
            file_path : str
                Путь к файлу вложения.
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
            logger.error(f"Ошибка при добавлении вложения: {e}")
            self.conn.rollback()
        finally:
            cursor.close()

    def add_reply(
        self,
        reply_id: int,
        main_dialog_id: int,
        main_message_id: int,
        reply_to_dialog_id: int,
        reply_to_msg_id: int,
        content: str,
        sender_id: int,
        date: str,
    ) -> None:
        """Добавляет ответ в таблицу Replies.

        Parameters:
        -----------
            reply_id : int
                ID ответного сообщения.
            main_dialog_id : int
                ID основного диалога.
            main_message_id : int
                ID основного сообщения, на которое отвечают.
            reply_to_dialog_id : int
                ID диалога, в котором был размещен ответ.
            reply_to_msg_id : int
                ID сообщения, на которое был дан ответ.
            content : str
                Содержание ответа.
            sender_id : int
                Отправитель ответа.
            date : str
                Дата отправки ответа.
        """
        cursor = self.conn.cursor()
        try:
            cursor.execute(
                """INSERT INTO Replies
                (id, main_dialog_id, main_message_id, reply_to_dialog_id, reply_to_msg_id,
                content, sender_id, date)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (id) DO NOTHING;""",
                (
                    reply_id,
                    main_dialog_id,
                    main_message_id,
                    reply_to_dialog_id,
                    reply_to_msg_id,
                    content,
                    sender_id,
                    date,
                ),
            )
            self.conn.commit()
            logger.info(
                f"Добавлен ответ {reply_id} на сообщение {main_message_id} в диалоге {main_dialog_id}"
            )
        except psycopg2.Error as e:
            logger.error(f"Ошибка при добавлении ответа: {e}")
            self.conn.rollback()
        finally:
            cursor.close()

    def get_last_reply_id(self, main_dialog_id: int, main_message_id: int) -> int:
        """Получает ID последнего сохраненного ответа для сообщения.

        Parameters:
        -----------
            main_dialog_id : int
                ID основного диалога.
            main_message_id : int
                ID основного сообщения.

        Returns:
        --------
            int: ID последнего ответа или 0, если ответы не сохранены.
        """
        cursor = self.conn.cursor()
        try:
            cursor.execute(
                "SELECT MAX(id) FROM Replies WHERE main_dialog_id = %s AND main_message_id = %s;",
                (main_dialog_id, main_message_id),
            )
            last_reply_id = cursor.fetchone()[0]
            cursor.close()
            return last_reply_id or 0
        except psycopg2.Error as e:
            logger.error(f"Ошибка при получении ID последнего ответа: {e}")
            self.conn.rollback()
            return 0
        finally:
            cursor.close()
