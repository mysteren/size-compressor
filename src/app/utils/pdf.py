import io
import traceback
from pathlib import Path

import fitz  # PyMuPDF
import numpy as np
from PIL import Image


class PdfUtils:
    @staticmethod
    def _jpeg_quality(pix: fitz.Pixmap, base_quality: int) -> tuple[int, int]:
        """
        Возвращает (quality, subsampling) под конкретное изображение.
        std пикселей → 3 уровня энтропии:
          high  → фото        → base quality,     4:2:0
          mid   → UI/скрин    → base + 8,         4:2:2
          low   → диаграмма   → base + 18,        4:2:2 (цветные края важны)
        """
        std = float(np.frombuffer(pix.samples_mv, dtype=np.uint8).std())
        if std > 35:
            return min(base_quality, 92), 2  # фото: 4:2:0
        elif std > 18:
            return min(base_quality + 8, 88), 1  # скриншот: 4:2:2
        else:
            return min(base_quality + 18, 92), 1  # диаграмма: 4:2:2

    @staticmethod
    def _to_jpeg_bytes(pix: fitz.Pixmap, quality: int, subsampling: int) -> bytes:
        """
        Кодирует Pixmap в JPEG через Pillow.
        optimize=True строит кастомную таблицу Хаффмана → −5–15% размера
        без потери качества.
        progressive=False — PDF-ридеры могут не поддерживать progressive JPEG.
        """
        mode = "L" if pix.n == 1 else "RGB"
        img = Image.frombytes(mode, (pix.width, pix.height), bytes(pix.samples_mv))
        buf = io.BytesIO()
        img.save(
            buf,
            format="JPEG",
            quality=quality,
            optimize=True,  # кастомные таблицы Хаффмана
            subsampling=subsampling if mode == "RGB" else 0,
            progressive=False,  # PDF: только baseline JPEG
        )
        return buf.getvalue()

    def compress_pdf(
        self,
        input_path: Path,
        output_path: Path,
        quality=70,
        dpi_threshold: int = 150,
        dpi_target: int = 120,  # А4 print-to-screen оптимум
    ) -> int:
        """
        Сжимает PDF файл и возвращает размер нового файла в байтах.

        :param input_path: Путь к исходному PDF файлу
        :param output_path: Путь для сохранения сжатого PDF файла
        :return: Размер сжатого файла в байтах (int)
        """

        MIN_IMAGE_PIXELS = 32 * 32

        try:
            # Открываем исходный документ
            doc = fitz.open(input_path)

            # ── 1. Удаляем метаданные и «мусор» ──────────────────────────
            # scrub убирает thumbnails (могут весить MB), embedded/attached файлы,
            # XML метаданные, info-словарь. Ссылки и поля форм сохраняем.
            try:
                doc.scrub(
                    metadata=True,
                    xml_metadata=True,
                    attached_files=True,
                    embedded_files=True,
                    thumbnails=True,
                    reset_fields=False,
                    reset_responses=False,
                    remove_links=False,
                )
            except RuntimeError:
                # Pre-clean и повторная попытка
                buf = doc.tobytes(garbage=4, clean=True)
                doc.close()
                doc = fitz.open(stream=buf, filetype="pdf")
                doc.scrub(
                    metadata=True,
                    xml_metadata=True,
                    attached_files=True,
                    embedded_files=True,
                    thumbnails=True,
                    reset_fields=False,
                    reset_responses=False,
                    remove_links=False,
                )

            # 2. Подсекаем шрифты — удаляем неиспользуемые глифы
            doc.subset_fonts()

            # ── 3. Нормализуем content streams ────────────────────────────
            # Убирает мусор от Word/LibreOffice: лишние q/Q, cm, setfont...
            for page in doc:
                page.clean_contents()

            # ── 5a. Lossy-изображения (JPEG) ──────────────────────────────
            # rewrite_images умеет DPI-даунсемплинг — делегируем ему.
            # lossless=False — PNG обрабатываем вручную ниже с fallback-логикой.
            doc.rewrite_images(
                dpi_threshold=dpi_threshold,  # уменьшаем только очень большие изображения
                dpi_target=dpi_target,
                quality=quality,
                lossy=False,
                lossless=False,  # PNG обрабатываем вручную ниже
                bitonal=True,  # включать монохромные изображения
            )

            # ── 5b. Lossless-изображения (PNG и др.) — fallback ───────────
            # Для каждого PNG: сравниваем размер оригинала с JPEG-версией.
            # Заменяем только если экономим ≥10%.
            # SAFE_CS = ("DeviceRGB", "DeviceGray", "CalRGB", "CalGray")
            seen_xrefs: set[int] = set()
            for page in doc:
                for img in page.get_images(full=True):
                    xref = img[0]
                    smask = img[1]

                    if xref in seen_xrefs:
                        continue
                    seen_xrefs.add(xref)

                    if smask != 0:
                        continue

                    try:
                        img_info = doc.extract_image(xref)
                        ext = img_info.get("ext", "")
                        cs_name = img_info.get("cs-name", "")

                        # Только обрабатываемые форматы
                        if ext not in ("jpeg", "jpg", "png", "bmp", "tiff", "pnm"):
                            continue

                        # is_safe = not cs_name or any(
                        #     cs_name.startswith(s) for s in SAFE_CS
                        # )
                        is_separation = (
                            cs_name.startswith("Separation") and "Black" in cs_name
                        )

                        # Indexed(CMYK) и прочая экзотика — пропускаем
                        # if not (is_safe or is_separation):
                        #     continue

                        is_jpeg = ext in ("jpeg", "jpg")
                        original_img_size = len(img_info["image"])
                        xres = img_info.get("xres") or 72
                        needs_downscale = xres > dpi_threshold

                        # JPEG без downscale и без Separation — не трогаем (generation loss)
                        # JPEG c Separation — тоже пропускаем без downscale:
                        # Pillow перекодирует пиксели, но Separation ink-values
                        # без downscale не дадут выигрыша
                        # if is_jpeg and not needs_downscale:
                        #     continue

                        pix = fitz.Pixmap(doc, xref)

                        if pix.width * pix.height < MIN_IMAGE_PIXELS:
                            del pix
                            continue

                        # Downscale если нужно
                        if needs_downscale:
                            scale = dpi_target / xres
                            new_w = max(1, int(pix.width * scale))
                            new_h = max(1, int(pix.height * scale))
                            pix = fitz.Pixmap(pix, new_w, new_h)

                        # CMYK → RGB (для случаев где n=4 проскочило)
                        if pix.n not in (1, 3):
                            pix = fitz.Pixmap(fitz.csRGB, pix)

                        adaptive_q, subsampling = self._jpeg_quality(pix, quality)
                        jpeg_bytes = self._to_jpeg_bytes(pix, adaptive_q, subsampling)

                        # JPEG с downscale — заменяем всегда (пиксели всё равно изменились)
                        # PNG → заменяем если экономия ≥5%
                        should_replace = (is_jpeg and needs_downscale) or len(
                            jpeg_bytes
                        ) < original_img_size * 0.95

                        if should_replace:
                            cs = "/DeviceGray" if pix.n == 1 else "/DeviceRGB"
                            doc.update_stream(xref, jpeg_bytes, compress=False)
                            doc.xref_set_key(xref, "Filter", "/DCTDecode")
                            doc.xref_set_key(xref, "DecodeParms", "null")
                            doc.xref_set_key(xref, "ColorSpace", cs)
                            doc.xref_set_key(xref, "BitsPerComponent", "8")
                            doc.xref_set_key(xref, "Width", str(pix.width))
                            doc.xref_set_key(xref, "Height", str(pix.height))
                            # Separation ink-values: 0=белый, /Decode [1 0] инвертирует для DeviceGray
                            doc.xref_set_key(
                                xref, "Decode", "[1 0]" if is_separation else "null"
                            )

                        del pix

                    except Exception as e:
                        print(f"Ошибка при обработке изображения xref={xref}: {e}")
                        traceback.print_exc()
                        continue

            # Сохраняем с максимальной оптимизацией
            doc.save(
                output_path,
                garbage=4,  # Удаляет неиспользуемые объекты (4 - максимальный уровень)
                clean=True,  # Очищает и исправляет синтаксис PDF
                deflate=True,  # Сжимает несжатые потоки
                deflate_fonts=True,  # Сжимает шрифты
                use_objstms=True,
                pretty=False,
            )

            doc.close()

        except Exception as e:
            traceback.print_exc()  #
            # В случае ошибки можно добавить логирование или пробросить исключение дальше
            raise RuntimeError(f"Ошибка при сжатии PDF: {e}")

        # Возвращаем размер созданного файла в байтах
        return output_path.stat().st_size
