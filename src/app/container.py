from functools import cached_property

from app.adapters.max_bot.client import MaxBotClient
from app.infrastructure.database import Database
from app.infrastructure.migrations import Migrator
from app.repositories.user import UserRepository
from app.use_case.attach import AttachUseCase
from app.use_case.user import UserUseCase
from app.utils.file import FileUtils
from app.utils.pdf import PdfUtils


class AppContainer:
    def __init__(self, bot_token: str, db_path: str):
        self._bot_token: str = bot_token
        self._db_path: str = db_path

    # --- INFRASTRUCTURE LAYER ---

    @cached_property
    def db(self) -> Database:
        # Migrator лучше передавать как класс, если Database сам его инстанцирует,
        # либо инстанцировать тут: Migrator()
        return Database(self._db_path, Migrator)

    @cached_property
    def file_utils(self) -> FileUtils:
        return FileUtils()

    @cached_property
    def pdf_utils(self) -> PdfUtils:
        return PdfUtils()

    # --- REPOSITORY LAYER ---

    @cached_property
    def user_repo(self) -> UserRepository:
        return UserRepository(self.db)

    # --- USE CASES LAYER ---

    @cached_property
    def attach_use_case(self) -> AttachUseCase:
        return AttachUseCase(
            file_utils=self.file_utils,
            pdf_utils=self.pdf_utils,  # Use case должен уметь сохранять аттачи
        )

    @cached_property
    def user_use_case(self) -> UserUseCase:
        return UserUseCase(
            user_repository=self.user_repo
        )  # Use case должен уметь читать юзеров

    # --- ADAPTERS LAYER ---

    @cached_property
    def max_bot_client(self) -> MaxBotClient:
        return MaxBotClient(
            bot_token=self._bot_token,
            attach_use_case=self.attach_use_case,
            user_use_case=self.user_use_case,
        )
