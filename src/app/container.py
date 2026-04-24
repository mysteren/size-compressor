from app.use_case.attach import AttachUseCase
from app.utils.file import FileUtils
from app.utils.pdf import PdfUtils

from .adapters.max_bot.client import MaxBotClient


class AppContainer:
    def __init__(self, bot_token: str):

        file_utils = FileUtils()

        pdf_utils = PdfUtils()

        attach_use_case = AttachUseCase(file_utils, pdf_utils)

        self.BotClient: MaxBotClient = MaxBotClient(bot_token, attach_use_case)
