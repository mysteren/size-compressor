from pathlib import Path

import fitz  # PyMuPDF


class PdfUtils:
    def compress_pdf(self, input_path: Path, output_path: Path, quality=83) -> int:
        """
        Сжимает PDF файл и возвращает размер нового файла в байтах.

        :param input_path: Путь к исходному PDF файлу
        :param output_path: Путь для сохранения сжатого PDF файла
        :return: Размер сжатого файла в байтах (int)
        """
        try:
            # Открываем исходный документ
            doc = fitz.open(input_path)

            doc.rewrite_images(
                dpi_threshold=150,  # уменьшаем только очень большие изображения (>200 dpi)
                dpi_target=100,
                quality=quality,
                lossy=True,
                lossless=False,
                bitonal=True,
            )

            # Сохраняем с максимальной оптимизацией
            doc.save(
                output_path,
                garbage=4,  # Удаляет неиспользуемые объекты (4 - максимальный уровень)
                clean=True,  # Очищает и исправляет синтаксис PDF
                deflate=True,  # Сжимает несжатые потоки
                deflate_images=True,  # Сжимает изображения без потери качества (перекодирование в deflate)
                deflate_fonts=True,  # Сжимает шрифты
            )

            doc.close()

        except Exception as e:
            # В случае ошибки можно добавить логирование или пробросить исключение дальше
            raise RuntimeError(f"Ошибка при сжатии PDF: {e}")

        # Возвращаем размер созданного файла в байтах
        return output_path.stat().st_size
