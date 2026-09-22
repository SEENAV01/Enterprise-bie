"""Native PDF typography observations backed by pdfplumber."""

from __future__ import annotations

from dataclasses import dataclass
from io import BytesIO
import math
from statistics import median

import pdfplumber


class PdfPlumberStructureAdapterError(ValueError):
    """Raised when native PDF structure signals cannot be extracted safely."""


_BOLD_TOKENS = ("bold", "semibold", "demibold", "demi", "black", "heavy")


@dataclass(frozen=True)
class NativeStructureLine:
    page: int
    text: str
    x0: float
    top: float
    x1: float
    bottom: float
    box: tuple[float, float, float, float]
    font_sizes: tuple[float, ...]
    font_names: tuple[str, ...]
    representative_font_size: float
    bold_fraction: float
    char_count: int


@dataclass(frozen=True)
class NativeStructurePage:
    page: int
    width: float
    height: float
    lines: tuple[NativeStructureLine, ...]


@dataclass(frozen=True)
class NativeStructureDocument:
    page_count: int
    pages: tuple[NativeStructurePage, ...]


def _finite_number(value: object, label: str) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError) as exc:
        raise PdfPlumberStructureAdapterError(f"invalid {label}") from exc
    if not math.isfinite(number):
        raise PdfPlumberStructureAdapterError(f"non-finite {label}")
    return number


def _normalized_box(
    x0: float,
    top: float,
    x1: float,
    bottom: float,
    width: float,
    height: float,
) -> tuple[float, float, float, float]:
    if not (0 <= x0 < x1 <= width and 0 <= top < bottom <= height):
        raise PdfPlumberStructureAdapterError("text line geometry is outside its page")
    box = (
        round(x0 / width, 8),
        round(top / height, 8),
        round(x1 / width, 8),
        round(bottom / height, 8),
    )
    bx0, by0, bx1, by1 = box
    if not (0 <= bx0 < bx1 <= 1 and 0 <= by0 < by1 <= 1):
        raise PdfPlumberStructureAdapterError(
            "normalized text line geometry is invalid"
        )
    return box


def _line_sort_key(
    item: tuple[int, NativeStructureLine],
) -> tuple[object, ...]:
    extraction_index, line = item
    return (
        line.top,
        line.x0,
        line.bottom,
        line.x1,
        line.text,
        extraction_index,
    )


def _is_bold(font_name: str) -> bool:
    normalized = font_name.casefold()
    return any(token in normalized for token in _BOLD_TOKENS)


class PdfPlumberStructureAdapter:
    """Extract deterministic text-line geometry and observed font signals."""

    def extract(self, data: bytes | bytearray) -> NativeStructureDocument:
        if not isinstance(data, (bytes, bytearray)):
            raise PdfPlumberStructureAdapterError("PDF input must be bytes")

        try:
            pdf = pdfplumber.open(BytesIO(bytes(data)))
        except Exception as exc:
            raise PdfPlumberStructureAdapterError(
                "pdfplumber could not open the PDF; it may be malformed or encrypted"
            ) from exc

        pages: list[NativeStructurePage] = []
        try:
            for page_number, page in enumerate(pdf.pages, start=1):
                width = _finite_number(page.width, "page width")
                height = _finite_number(page.height, "page height")
                if width <= 0 or height <= 0:
                    raise PdfPlumberStructureAdapterError(
                        "page geometry must be positive"
                    )

                try:
                    raw_lines = page.dedupe_chars().extract_text_lines(
                        strip=True,
                        return_chars=True,
                    )
                except Exception as exc:
                    raise PdfPlumberStructureAdapterError(
                        f"native style extraction failed on page {page_number}"
                    ) from exc

                lines: list[NativeStructureLine] = []
                for raw_line in raw_lines:
                    text = str(raw_line.get("text", "")).strip()
                    if not text:
                        continue
                    x0 = _finite_number(raw_line.get("x0"), "line x0")
                    top = _finite_number(raw_line.get("top"), "line top")
                    x1 = _finite_number(raw_line.get("x1"), "line x1")
                    bottom = _finite_number(raw_line.get("bottom"), "line bottom")
                    raw_chars = raw_line.get("chars")
                    if not isinstance(raw_chars, list) or not raw_chars:
                        raise PdfPlumberStructureAdapterError(
                            "native text line has no character style observations"
                        )

                    font_sizes: list[float] = []
                    font_names: list[str] = []
                    for char in raw_chars:
                        if not isinstance(char, dict):
                            raise PdfPlumberStructureAdapterError(
                                "invalid character style observation"
                            )
                        char_text = str(char.get("text", ""))
                        if not char_text or char_text.isspace():
                            continue
                        size = _finite_number(char.get("size"), "character font size")
                        if size <= 0:
                            raise PdfPlumberStructureAdapterError(
                                "character font size must be positive"
                            )
                        font_name = str(char.get("fontname", "")).strip()
                        if not font_name:
                            raise PdfPlumberStructureAdapterError(
                                "character font name is required"
                            )
                        font_sizes.append(round(size, 8))
                        font_names.append(font_name)

                    if not font_sizes:
                        raise PdfPlumberStructureAdapterError(
                            "native text line has no styled non-whitespace characters"
                        )
                    representative_size = round(float(median(font_sizes)), 8)
                    bold_fraction = round(
                        sum(_is_bold(name) for name in font_names) / len(font_names),
                        8,
                    )
                    lines.append(
                        NativeStructureLine(
                            page=page_number,
                            text=text,
                            x0=x0,
                            top=top,
                            x1=x1,
                            bottom=bottom,
                            box=_normalized_box(
                                x0,
                                top,
                                x1,
                                bottom,
                                width,
                                height,
                            ),
                            font_sizes=tuple(font_sizes),
                            font_names=tuple(font_names),
                            representative_font_size=representative_size,
                            bold_fraction=bold_fraction,
                            char_count=len(text),
                        )
                    )

                ordered_lines = tuple(
                    line for _, line in sorted(enumerate(lines), key=_line_sort_key)
                )
                pages.append(
                    NativeStructurePage(
                        page=page_number,
                        width=width,
                        height=height,
                        lines=ordered_lines,
                    )
                )
        except PdfPlumberStructureAdapterError:
            raise
        except Exception as exc:
            raise PdfPlumberStructureAdapterError(
                "PDF typography inspection failed"
            ) from exc
        finally:
            pdf.close()

        return NativeStructureDocument(page_count=len(pages), pages=tuple(pages))
