"""
Модуль конфигурации для настройки параметров работы скраппера Telegram.

Этот модуль содержит глобальные переменные, которые определяют различные параметры работы скраппера,
такие как лимиты на количество извлекаемых сообщений и ответов, пути к директориям для сохранения
логов и вложений, а также параметры для отладки.
"""

"""Модуль конфигурации для настройки параметров работы скраппера.

Attributes:
----------
MESSAGE_FETCH_LIMIT : int
    Максимальное количество сообщений, извлекаемых за один запрос.
REPLY_FETCH_LIMIT : int
    Максимальное количество ответов на сообщение, извлекаемых за один запрос.
DEBUG_CHANNEL_ID : int
    Идентификатор канала для отладки.
DEBUG_MESSAGE_ID_THRESHOLD : int
    Пороговое значение ID сообщения для отладки.
LOGS_DIR : str
    Путь к директории для сохранения логов.
IMAGES_DIR : str
    Путь к директории для сохранения изображений.
ATTACHMENTS_DIR : str
    Путь к директории для сохранения остальных типов вложений.
TELEGRAM_SESSION_FILE : str
    Путь к файлу сессии Telegram.
DEBUG_MODE : bool
    Флаг режима отладки.
"""

# Ограничения
MESSAGE_FETCH_LIMIT = 50
REPLY_FETCH_LIMIT = 5

# Идентификаторы для отладки
DEBUG_CHANNEL_ID = 1380524958
DEBUG_MESSAGE_ID_THRESHOLD = 1345

# Пути к файлам и директориям
LOGS_DIR = "logs"
IMAGES_DIR = "/data/images"
ATTACHMENTS_DIR = "/data/attachments"
TELEGRAM_SESSION_FILE = "session/telegram_session"

DEBUG_MODE = True
