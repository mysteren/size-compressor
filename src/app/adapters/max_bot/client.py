import pprint
from pathlib import Path

from maxapi import Bot, Dispatcher, F
from maxapi.types import BotStarted, Command, MessageCreated, OtherAttachmentPayload
from maxapi.types.attachments.attachment import AttachmentType


class MaxBotClient:
    def __init__(self, bot_token: str):
        """
        Инициализация клиента для бота MAX.
        Args:
            bot_token: Секретный токен вашего бота, полученный от @MasterBot.
        """
        print(f"Инициализация бота с токеном: {bot_token}")
        # 1. Создаем экземпляр класса Bot из библиотеки
        self.bot: Bot = Bot(token=bot_token)
        # 2. Создаем Dispatcher для маршрутизации событий
        self.dispatcher: Dispatcher = Dispatcher()
        # 3. Здесь же можно зарегистрировать обработчики команд,
        #    но для чистоты кода сделаем это в отдельном методе.

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
            # url = await event.bot.get_upload_url(UploadType.FILE)
            # print(url)

            if message.body and message.body.attachments:
                attachments = message.body.attachments

                for attach in attachments:
                    pprint.pp(attach)
                    payload = attach.payload
                    type = attach.type

                    if type == AttachmentType.FILE and isinstance(
                        payload, OtherAttachmentPayload
                    ):
                        # type = payload.type
                        #
                        path = Path("./uploads")

                        result = await bot.download_file(
                            url=payload.url, destination=path
                        )
                        pprint.pp(result)

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

        _ = await event.message.answer("Получено вложение")

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
