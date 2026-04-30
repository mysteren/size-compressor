import os
from pathlib import Path
from urllib.parse import unquote

from pydantic import BaseModel

from app.utils.file import FileUtils
from app.utils.pdf import PdfUtils


class UploadDto(BaseModel):
    fileId: int
    token: str


class AttachUseCase:
    def __init__(self, file_utils: FileUtils, pdf_utils: PdfUtils):
        self._file_utils: FileUtils = file_utils
        self._pdf_utils: PdfUtils = pdf_utils

    def check_pdf(self, filename: str, size: int):

        ext = self._file_utils.get_file_extension(filename=filename)
        is_pdf = ext == "pdf"
        size_string = self._file_utils.human_readable_size(size)

        return is_pdf, size_string

    def compress_pdf(self, path: Path):

        # output = Path(unquote(str(self.file_utils.add_suffix_to_path(path, "_cmprss"))))
        output = self._file_utils.add_suffix_to_path(path, "_cmprss")

        size = self._pdf_utils.compress_pdf(path, output, 74)

        # size_string = self.file_utils.human_readable_size(size)

        new_path = unquote(str(path))

        os.replace(output, new_path)

        return (size, new_path)

    def compression_ratio(self, original: int, compressed: int):
        return (compressed - original) / original * 100

    def getUploadDTO(self, raw: str):
        return UploadDto.model_validate_json(raw)

    def removeTrashFiles(self, *paths: Path | str | None):
        for path in paths:
            if path is None:
                continue
            try:
                Path(path).unlink(missing_ok=True)
            except Exception:
                pass  # не получилось удалить — ничего не делаем
