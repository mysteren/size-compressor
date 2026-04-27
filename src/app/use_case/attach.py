import os
from pathlib import Path
from urllib.parse import unquote

from app.utils.file import FileUtils
from app.utils.pdf import PdfUtils


class AttachUseCase:
    def __init__(self, file_utils: FileUtils, pdf_utils: PdfUtils):
        self.file_utils: FileUtils = file_utils
        self.pdf_utils: PdfUtils = pdf_utils

    def check_pdf(self, filename: str, size: int):

        ext = self.file_utils.get_file_extension(filename=filename)
        is_pdf = ext == "pdf"
        size_string = self.file_utils.human_readable_size(size)

        return is_pdf, size_string

    def compress_pdf(self, path: Path):

        # output = Path(unquote(str(self.file_utils.add_suffix_to_path(path, "_cmprss"))))
        output = self.file_utils.add_suffix_to_path(path, "_cmprss")

        size = self.pdf_utils.compress_pdf(path, output, 74)

        # size_string = self.file_utils.human_readable_size(size)

        new_path = unquote(str(path))

        os.replace(output, new_path)

        return (size, new_path)

    def compression_ratio(self, original: int, compressed: int):
        return (original - compressed) / original * 100
