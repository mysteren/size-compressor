from pathlib import Path

from maxapi import Bot, Dispatcher, F
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

from app.use_case.attach import AttachUseCase
from app.use_case.user import UserUseCase


class MaxBotClient:
    def __init__(
        self, bot_token: str, attach_use_case: AttachUseCase, user_use_case: UserUseCase
    ):
        """
        Инициализация клиента для бота MAX.
        Args:
            bot_token: Секретный токен вашего бота, полученный от @MasterBot.
        """

        # 1. Создаем экземпляр класса Bot из библиотеки
        self._bot: Bot = Bot(token=bot_token)
        # 2. Создаем Dispatcher для маршрутизации событий
        self._dispatcher: Dispatcher = Dispatcher()

        self._attach_use_case: AttachUseCase = attach_use_case

        self._user_use_case: UserUseCase = user_use_case

    # --- Методы-обработчики ---
    async def _cmd_start(self, event: BotStarted):
        """Обработчик команды /start"""
        name = event.user.first_name
        _, user_id = event.get_ids()

        _ = await self._user_use_case.user_init(user_id=user_id, name=name)

        if event.bot:
            _ = await event.bot.send_message(
                chat_id=event.chat_id,
                text=f"Привет, {name}! я умею сжимать PDF файлы. Доступные команды: /help",
            )

    async def _cmd_help(self, event: MessageCreated):
        """Обработчик команды /help"""
        _ = await event.message.answer("Доступные команды: /help")

    async def _on_attachment(self, event: MessageCreated):
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

                        is_pdf, _ = self._attach_use_case.check_pdf(
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

                            old_file = None
                            new_file = None

                            try:
                                folder = Path("./uploads")
                                old_file = await bot.download_file(
                                    url=url, destination=folder
                                )

                                new_size, new_file = self._attach_use_case.compress_pdf(
                                    old_file
                                )

                                ratio = self._attach_use_case.compression_ratio(
                                    size, new_size
                                )

                                if size > new_size:
                                    upload_url = await bot.get_upload_url(
                                        UploadType.FILE,
                                    )

                                    upload_raw = await bot.upload_file(
                                        url=upload_url.url,
                                        path=new_file,
                                        type=UploadType.FILE,
                                    )

                                    upload_data = self._attach_use_case.getUploadDTO(
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

                            except Exception as ex:
                                message = f"❌ Ошибка: {str(ex)}"
                            finally:
                                self._attach_use_case.removeTrashFiles(
                                    old_file, new_file
                                )

                        else:
                            message = (
                                "⚠️ Файл имеет неразрешенный формат, такой как .pdf"
                            )
                        # ✅
                        _ = await event.message.answer(
                            text=message, attachments=answer_attachments
                        )

    # --- Привязка обработчиков ---
    def _register_handlers(self):
        # Привязываем методы класса к событиям
        self._dispatcher.bot_started()(self._cmd_start)
        self._dispatcher.message_created(Command("help"))(self._cmd_help)
        self._dispatcher.message_created(F.message.body.attachments)(
            self._on_attachment
        )

    async def start(self):
        print("MaxBot started")
        self._register_handlers()
        await self._bot.delete_webhook()
        await self._dispatcher.start_polling(self._bot)
