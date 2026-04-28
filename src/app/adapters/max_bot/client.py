import pprint
from pathlib import Path
from typing import TypedDict

from maxapi import Bot, Dispatcher, F
from maxapi.context.context import json
from maxapi.enums.upload_type import UploadType
from maxapi.types import (
    Attachment,
    BotStarted,
    Command,
    InputMedia,
    InputMediaBuffer,
    MessageCreated,
    OtherAttachmentPayload,
)
from maxapi.types.attachments.attachment import AttachmentType
from maxapi.utils.message import AttachmentUpload
from pydantic import BaseModel

from app.use_case.attach import AttachUseCase


class MaxBotClient:
    def __init__(self, bot_token: str, attach_use_case: AttachUseCase):
        """
        Инициализация клиента для бота MAX.
        Args:
            bot_token: Секретный токен вашего бота, полученный от @MasterBot.
        """

        # 1. Создаем экземпляр класса Bot из библиотеки
        self.bot: Bot = Bot(token=bot_token)
        # 2. Создаем Dispatcher для маршрутизации событий
        self.dispatcher: Dispatcher = Dispatcher()

        self.attach_use_case: AttachUseCase = attach_use_case

    # --- Методы-обработчики ---
    async def cmd_start(self, event: BotStarted):
        """Обработчик команды /start"""
        name = event.user.first_name

        print("bot start")

        if event.bot:
            _ = await event.bot.send_message(
                chat_id=event.chat_id, text=f"Привет, {name}! Я бот."
            )

    async def cmd_help(self, event: MessageCreated):
        """Обработчик команды /help"""
        _ = await event.message.answer("Доступные команды: /help")

    async def on_attachment(self, event: MessageCreated):
        bot = event.bot
        message = event.message
        if bot:
            if message.body and message.body.attachments:
                attachments = message.body.attachments
                for attach in attachments:
                    payload = attach.payload
                    type = attach.type

                    if type == AttachmentType.FILE and isinstance(
                        payload, OtherAttachmentPayload
                    ):
                        filename: str = getattr(attach, "filename", "")
                        size: int = getattr(attach, "size", 0)

                        is_pdf, _ = self.attach_use_case.check_pdf(
                            filename=filename, size=size
                        )

                        answer_attachments: list[
                            Attachment
                            | InputMedia
                            | InputMediaBuffer
                            | AttachmentUpload
                        ] = []

                        if is_pdf:
                            url = payload.url

                            try:
                                path = Path("./uploads")
                                result = await bot.download_file(
                                    url=url, destination=path
                                )

                                new_size, new_path = self.attach_use_case.compress_pdf(
                                    result
                                )

                                ratio = -1 * self.attach_use_case.compression_ratio(
                                    size, new_size
                                )

                                if size > new_size:
                                    upload_url = await bot.get_upload_url(
                                        UploadType.FILE,
                                    )

                                    upload_raw = await bot.upload_file(
                                        url=upload_url.url,
                                        path=new_path,
                                        type=UploadType.FILE,
                                    )

                                    upload_data = self.attach_use_case.getUploadDTO(
                                        upload_raw
                                    )

                                    new_attach = Attachment(
                                        type=AttachmentType.FILE,
                                        payload=OtherAttachmentPayload(
                                            url=upload_url.url, token=upload_data.token
                                        ),
                                    )
                                    #
                                    answer_attachments.append(new_attach)
                                    message = f"✅ Успешное сжатие: {ratio:.1f}%"
                                else:
                                    message = f"⚠️ Сжатие файла не удалось, размер файла превысил исходный на {ratio:.1f}%"

                                # pprint.pp(upload_result)
                            except Exception as ex:
                                message = f"❌ Ошибка: {str(ex)}"

                        else:
                            message = (
                                "⚠️ Файл имеет неразрешенный формат, такой как .pdf"
                            )
                        # ✅
                        _ = await event.message.answer(
                            text=message, attachments=answer_attachments
                        )

                        # path = Path("./uploads")

                        # result = await bot.download_file(
                        #     url=payload.url, destination=path
                        # )

                        # await event.message.answer("Получено вложение ")
                        # pprint.pp(result)

                    # if payload:
                    #     if hasattr(payload, 'type') and payload.type == UploadType.FILE

                    # if (
                    #     attach.payload
                    #     and attach.payload.type
                    #     and attach.payload.type == UploadType.FILE
                    # ):
                    #     url = attach.payload.url
                    #     print(url)

                    # url = event.bot.get_upload_url(UploadType.FILE)

        # print(attachments)

        # _ = await event.message.answer("Получено вложение")

    # async def echo_all(self, event: MessageCreated):
    #     """Обработчик любого текстового сообщения"""
    #     if event.message.body and event.message.body.text:
    #         text = event.message.body.text
    #         _ = await event.message.answer(f"Вы написали: {text}")

    # --- Привязка обработчиков ---
    def _register_handlers(self):
        # Привязываем методы класса к событиям
        self.dispatcher.bot_started()(self.cmd_start)
        self.dispatcher.message_created(Command("help"))(self.cmd_help)
        self.dispatcher.message_created(F.message.body.attachments)(self.on_attachment)

        # self.dispatcher.message_created()(self.echo_all)

    async def start(self):
        print("MaxBot started")
        self._register_handlers()
        await self.bot.delete_webhook()
        await self.dispatcher.start_polling(self.bot)
