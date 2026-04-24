import io
from pathlib import Path

import fitz  # PyMuPDF
from PIL import Image


class PdfUtils:
    # def __init__(self):

    def compress_pdf(self, input_path: Path, output_path: Path, dpi: int = 72) -> int:
        """
        Сжать PDF через растеризацию с последующей сборкой.

        :param input_path: Путь к исходному PDF.
        :param output_path: Путь для сохранения сжатого PDF.
        :param dpi: Разрешение для растеризации страниц (по умолчанию 150).
        :return: Размер итогового файла в байтах.
        """
        # Список для хранения JPEG-байтов каждой страницы и её размеров в пунктах
        pages_data = []

        # 1. Преобразуем PDF в изображения и сжимаем каждую страницу
        src_doc = fitz.open(input_path)
        for page in src_doc:
            # Матрица для нужного DPI (72 – базовое разрешение PDF)
            mat = fitz.Matrix(dpi / 72, dpi / 72)
            pix = page.get_pixmap(matrix=mat, colorspace=fitz.csRGB)

            # Превращаем пиксмапу в Pillow Image
            if pix.n < 4:  # серый или палитровый, всё равно преобразуем в RGB
                img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
            else:  # RGBA или CMYK → конвертируем в RGB
                img = Image.frombytes(
                    "RGBA" if pix.alpha else "RGB", [pix.width, pix.height], pix.samples
                )
                if img.mode != "RGB":
                    img = img.convert("RGB")

            # Сжатие: сохраняем в JPEG в памяти
            buf = io.BytesIO()
            img.save(buf, format="JPEG", quality=74)
            jpeg_bytes = buf.getvalue()

            # Размеры страницы в пунктах: 1 пункт = 1/72 дюйма
            w_pt = img.width * 72.0 / dpi
            h_pt = img.height * 72.0 / dpi
            pages_data.append((jpeg_bytes, w_pt, h_pt))

        src_doc.close()

        # 2. Собираем новый PDF из сжатых JPEG
        out_doc = fitz.open()  # пустой документ
        for jpeg_bytes, w_pt, h_pt in pages_data:
            page = out_doc.new_page(width=w_pt, height=h_pt)
            # Вставляем изображение из памяти
            page.insert_image(
                fitz.Rect(0, 0, w_pt, h_pt), stream=jpeg_bytes, keep_proportion=False
            )

        out_doc.save(output_path, deflate=True, garbage=4)
        out_doc.close()

        # 3. Возвращаем размер итогового файла
        return output_path.stat().st_size
