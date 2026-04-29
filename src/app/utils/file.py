# app/utils/file.py
from __future__ import annotations

from pathlib import Path

from fitz import os


class FileUtils:
    def human_readable_size(self, size: int, binary: bool = True) -> str:
        """
        Преобразует размер в байтах в строку с удобочитаемыми единицами измерения.

        Аргументы:
            size (int): размер в байтах
            binary (bool): если True, используются двоичные приставки (1024),
                           если False – десятичные (1000). По умолчанию True.

        Возвращает:
            str: строка с размером и единицами измерения (например, "12.34 MB")
        """
        if size == 0:
            return "0 B"

        # Единицы измерения (для двоичного и десятичного вариантов)
        units = ["B", "KB", "MB", "GB", "TB", "PB"]
        base = 1024 if binary else 1000

        # Определяем подходящую единицу
        unit_index = 0
        temp_size = abs(size)
        while temp_size >= base and unit_index < len(units) - 1:
            temp_size /= base
            unit_index += 1

        # Форматируем результат
        formatted_size = (
            f"{temp_size:.2f}" if temp_size % 1 != 0 else f"{temp_size:.0f}"
        )
        return f"{formatted_size} {units[unit_index]}"

    def get_file_extension(self, filename: str, with_dot: bool = False) -> str:
        """
        Возвращает расширение файла по его имени.

        Аргументы:
            filename (str): имя файла (например, "document.pdf" или "archive.tar.gz")
            with_dot (bool): если True, возвращает расширение с точкой (например, ".py"),
                             если False – без точки (например, "py"). По умолчанию False.

        Возвращает:
            str: расширение файла (для сложных случаев типа .tar.gz – только последнее,
                 если нужно полное – см. функцию ниже)
        """
        if not filename or "." not in filename:
            return ""

        # Отделяем расширение (после последней точки)
        extension = filename.split(".")[-1].lower()

        # Возвращаем с точкой или без
        return f".{extension}" if with_dot else extension

    # Альтернативная функция для получения составного расширения (например, "tar.gz")
    def get_full_extension(self, filename: str, with_dot: bool = False) -> str:
        """
        Возвращает полное расширение файла, включая все точки после базового имени.
        Пример: "archive.tar.gz" -> "tar.gz" (или ".tar.gz" если with_dot=True)
        """
        if not filename or "." not in filename:
            return ""

        parts = filename.split(".")
        # Если только одна точка – это обычное расширение
        if len(parts) == 2:
            extension = parts[1].lower()
        else:
            # Берём всё после первого фрагмента (например, "script.min.js" -> "min.js")
            extension = ".".join(parts[1:]).lower()

        return f".{extension}" if with_dot else extension

    def add_suffix_to_filename(self, file_path: str, suffix: str) -> str:
        """
        Добавляет суффикс к имени файла перед расширением.

        Аргументы:
            file_path (str): Исходный путь к файлу.
            suffix (str): Суффикс, который нужно добавить (например, '_compressed').

        Возвращает:
            str: Новый путь к файлу с добавленным суффиксом.
        """
        # Разделяем путь на каталог, имя файла и расширение
        dir_name, base_name = os.path.split(file_path)
        name, ext = os.path.splitext(base_name)
        # Собираем новое имя: имя + суффикс + расширение
        new_base_name = f"{name}{suffix}{ext}"
        # Формируем полный путь
        return os.path.join(dir_name, new_base_name)

    def add_suffix_to_path(self, file_path: Path, suffix: str) -> Path:
        """
        Добавляет суффикс к имени файла (перед расширением) для объекта Path.

        Аргументы:
            file_path (Path): Исходный путь к файлу.
            suffix (str): Суффикс, например '_compressed'.

        Возвращает:
            Path: Новый путь с добавленным суффиксом.
        """
        # Получаем родительскую директорию, чистое имя (без расширения) и расширение
        parent = file_path.parent
        stem = file_path.stem
        ext = file_path.suffix  # включает точку, например '.pdf'

        # Собираем новое имя и возвращаем новый Path
        new_stem = f"{stem}{suffix}"
        return parent / (new_stem + ext)
