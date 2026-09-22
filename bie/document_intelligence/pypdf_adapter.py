"""Production PDF inspection adapter backed by pypdf."""

from __future__ import annotations

from io import BytesIO
import math
from typing import TypeAlias

from pypdf import PdfReader


MetadataValue: TypeAlias = str | int | float | bool | None


class PyPdfAdapterError(ValueError):
    """Raised when a PDF cannot be inspected safely with pypdf."""


def _metadata_value(value: object) -> MetadataValue:
    if value is None or isinstance(value, (str, bool, int)):
        return value
    if isinstance(value, float):
        return value if math.isfinite(value) else str(value)
    return str(value)


def _metadata(reader: PdfReader) -> dict[str, MetadataValue]:
    try:
        raw = reader.metadata
        if raw is None:
            return {}
        items = sorted(raw.items(), key=lambda item: str(item[0]))
        return {str(key): _metadata_value(value) for key, value in items}
    except Exception as exc:
        raise PyPdfAdapterError("PDF metadata inspection failed") from exc


class PyPdfAdapter:
    """Satisfy the canonical ``adapter.inspect(data)`` PDF ingest contract."""

    def inspect(self, data: bytes | bytearray) -> dict[str, object]:
        if not isinstance(data, (bytes, bytearray)):
            raise PyPdfAdapterError("PDF input must be bytes")

        payload = bytes(data)
        try:
            reader = PdfReader(BytesIO(payload))
        except Exception as exc:
            raise PyPdfAdapterError("pypdf could not parse the PDF") from exc

        try:
            encrypted = bool(reader.is_encrypted)
        except Exception as exc:
            raise PyPdfAdapterError("PDF encryption state inspection failed") from exc

        if encrypted:
            raise PyPdfAdapterError(
                "encrypted PDF inspection requires credentials and is not supported"
            )

        try:
            page_count = len(reader.pages)
        except Exception as exc:
            raise PyPdfAdapterError("PDF page inventory failed") from exc

        text_pages = 0
        for page_number, page in enumerate(reader.pages, start=1):
            try:
                text = page.extract_text()
            except Exception as exc:
                raise PyPdfAdapterError(
                    f"PDF text inspection failed on page {page_number}"
                ) from exc
            if isinstance(text, str) and text.strip():
                text_pages += 1

        return {
            "page_count": page_count,
            "metadata": _metadata(reader),
            "encrypted": encrypted,
            "text_pages": text_pages,
        }
