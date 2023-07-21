-- Создание таблицы диалога (чат, канал, группа)
CREATE TABLE  IF NOT EXISTS Dialogs (
    id BIGINT PRIMARY KEY,
    name VARCHAR(255) NOT NULL
);

-- Создание таблицы с собщениями диалога
CREATE TABLE  IF NOT EXISTS Messages (
    id BIGINT PRIMARY KEY,
    dialog_id BIGINT NOT NULL REFERENCES Dialogs (id),
    text TEXT
);

-- Создание таблицы с типами вложений
CREATE TABLE  IF NOT EXISTS AttachmentTypes (
    id SERIAL PRIMARY KEY,
    type VARCHAR(255) NOT NULL
);

-- Создание таблицы с вложениями
-- Описание что за вожеие и где лежит
CREATE TABLE  IF NOT EXISTS Attachments (
    id BIGINT PRIMARY KEY,
    type_id INTEGER NOT NULL REFERENCES AttachmentTypes (id),
    message_id BIGINT NOT NULL REFERENCES Messages (id),
    file_path VARCHAR(255) NOT NULL
);

-- Создание таблицы с комментариями на сообщения диалога 
CREATE TABLE  IF NOT EXISTS Replies (
    id BIGINT PRIMARY KEY,
    message_id BIGINT NOT NULL REFERENCES Messages (id),
    reply_to_message_id BIGINT REFERENCES Messages (id),
    content TEXT,
    sender VARCHAR(255),
    date TIMESTAMP
);