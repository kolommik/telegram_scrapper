-- Создание таблицы типа диалога (Channel, User, Chat)
CREATE TABLE IF NOT EXISTS DialogTypes (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL
);

-- Создание таблицы диалога (чат, канал, группа)
CREATE TABLE IF NOT EXISTS Dialogs (
    id BIGINT PRIMARY KEY,
    dialogtype_id BIGINT NOT NULL REFERENCES DialogTypes (id),
    name VARCHAR(255) NOT NULL
);


-- Создание таблицы с собщениями диалога
CREATE TABLE IF NOT EXISTS Messages (
    id BIGINT NOT NULL,
    dialog_id BIGINT NOT NULL REFERENCES Dialogs (id),
    reply_to_msg_id BIGINT NOT NULL,
    text TEXT,
    created TIMESTAMP NOT NULL,
    grouped_id BIGINT,
    PRIMARY KEY (dialog_id, id)
);

-- Создание таблицы с типами вложений
CREATE TABLE IF NOT EXISTS AttachmentTypes (
    id SERIAL PRIMARY KEY,
    type VARCHAR(255) NOT NULL
);

-- Создание таблицы с вложениями
CREATE TABLE IF NOT EXISTS Attachments (
    id BIGINT PRIMARY KEY,
    type_id INTEGER NOT NULL REFERENCES AttachmentTypes (id),
    message_id BIGINT NOT NULL,
    dialog_id BIGINT NOT NULL,
    file_path VARCHAR(255) NOT NULL,
    FOREIGN KEY (dialog_id, message_id) REFERENCES Messages (dialog_id, id)
);


-- Создание таблицы с комментариями на сообщения диалога 
CREATE TABLE IF NOT EXISTS Replies (
    id BIGINT PRIMARY KEY,
    dialog_id BIGINT NOT NULL,
    reply_to_msg_id BIGINT NOT NULL,
    main_dialog_id BIGINT NOT NULL,
    main_message_id BIGINT NOT NULL,
    content TEXT,
    sender_id BIGINT,
    date TIMESTAMP,
    PRIMARY KEY (dialog_id, id),
    FOREIGN KEY (main_dialog_id, main_message_id) REFERENCES Messages (dialog_id, id)
);
