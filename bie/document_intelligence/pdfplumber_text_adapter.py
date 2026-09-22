"""Native PDF text-line geometry adapter backed by pdfplumber."""

from __future__ import annotations

from dataclasses import dataclass
from io import BytesIO
import math

import pdfplumber


class PdfPlumberTextAdapterError(ValueError):
    """Raised when native PDF text geometry cannot be extracted safely."""


@dataclass(frozen=True)
class NativeTextLine:
    page: int
    text: str
    x0: float
    top: float
    x1: float
    bottom: float
    box: tuple[float, float, float, float]


@dataclass(frozen=True)
class NativeTextPage:
    page: int
    width: float
    height: float
    lines: tuple[NativeTextLine, ...]


@dataclass(frozen=True)
class NativeTextDocument:
    page_count: int
    pages: tuple[NativeTextPage, ...]


def _finite_number(value: object, label: str) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError) as exc:
        raise PdfPlumberTextAdapterError(f"invalid {label}") from exc
    if not math.isfinite(number):
        raise PdfPlumberTextAdapterError(f"non-finite {label}")
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
        raise PdfPlumberTextAdapterError("text line geometry is outside its page")
    box = (
        round(x0 / width, 8),
        round(top / height, 8),
        round(x1 / width, 8),
        round(bottom / height, 8),
    )
    bx0, by0, bx1, by1 = box
    if not (0 <= bx0 < bx1 <= 1 and 0 <= by0 < by1 <= 1):
        raise PdfPlumberTextAdapterError("normalized text line geometry is invalid")
    return box


class PdfPlumberTextAdapter:
    """Extract trimmed native text lines and normalized geometry from PDF bytes."""

    def extract(self, data: bytes | bytearray) -> NativeTextDocument:
        if not isinstance(data, (bytes, bytearray)):
            raise PdfPlumberTextAdapterError("PDF input must be bytes")

        payload = bytes(data)
        try:
            pdf = pdfplumber.open(BytesIO(payload))
        except Exception as exc:
            raise PdfPlumberTextAdapterError(
                "pdfplumber could not open the PDF; it may be malformed or encrypted"
            ) from exc

        pages: list[NativeTextPage] = []
        try:
            for page_number, page in enumerate(pdf.pages, start=1):
                width = _finite_number(page.width, "page width")
                height = _finite_number(page.height, "page height")
                if width <= 0 or height <= 0:
                    raise PdfPlumberTextAdapterError("page geometry must be positive")

                try:
                    raw_lines = page.dedupe_chars().extract_text_lines(
                        strip=True,
                        return_chars=False,
                    )
                except Exception as exc:
                    raise PdfPlumberTextAdapterError(
                        f"native text extraction failed on page {page_number}"
                    ) from exc

                lines: list[NativeTextLine] = []
                for raw_line in raw_lines:
                    text = str(raw_line.get("text", "")).strip()
                    if not text:
                        continue
                    x0 = _finite_number(raw_line.get("x0"), "line x0")
                    top = _finite_number(raw_line.get("top"), "line top")
                    x1 = _finite_number(raw_line.get("x1"), "line x1")
                    bottom = _finite_number(raw_line.get("bottom"), "line bottom")
                    lines.append(
                        NativeTextLine(
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
                        )
                    )
                pages.append(
                    NativeTextPage(
                        page=page_number,
                        width=width,
                        height=height,
                        lines=tuple(lines),
                    )
                )
        except PdfPlumberTextAdapterError:
            raise
        except Exception as exc:
            raise PdfPlumberTextAdapterError("PDF text geometry inspection failed") from exc
        finally:
            pdf.close()

        return NativeTextDocument(page_count=len(pages), pages=tuple(pages))
