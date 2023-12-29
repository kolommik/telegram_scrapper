import os
from telethon.sync import TelegramClient


class AttachmentHandler:
    def __init__(self, images_path: str, attachments_path: str):
        self.images_path = images_path
        self.attachments_path = attachments_path
        os.makedirs(images_path, exist_ok=True)
        os.makedirs(attachments_path, exist_ok=True)

    async def save_attachment(self, client: TelegramClient, attachment: dict) -> str:
        """Save an attachment and return the file path."""

        file_path = None

        try:
            # photo - фотки берем
            # document - документы берем

            # web_preview - не берем, превью не нужно
            # audio - не берем, не ясно как юзать
            # voice - не берем, не ясно как юзать
            # video - не берем, не ясно как юзать
            # video_note - не берем, не ясно как юзать
            # gif - не берем, это как правило фигня
            # sticker - не берем, не нужно

            if attachment["type"] == "photo":
                file_path = os.path.join(self.images_path, f"{attachment['id']}.jpg")
                await client.download_media(attachment["file"], file=file_path)
            elif attachment["type"] == "document":
                file_path = os.path.join(
                    self.attachments_path, f"{attachment['id']}{attachment['ext']}"
                )
                await client.download_media(attachment["file"], file=file_path)

        except OSError as e:
            print(f"An error occurred while saving the attachment: {e}")
            file_path = None
        except Exception as e:
            print(f"An unexpected error occurred: {e}")
            file_path = None

        return file_path
