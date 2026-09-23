"""Native PDF outline extraction backed by pypdf."""

from __future__ import annotations

from dataclasses import dataclass
from io import BytesIO
from typing import Sequence

from pypdf import PdfReader


class PyPdfOutlineAdapterError(ValueError):
    """Raised when a native PDF outline cannot be represented safely."""


@dataclass(frozen=True)
class NativeOutlineEntry:
    order: int
    depth: int
    title: str
    destination_page: int | None


@dataclass(frozen=True)
class NativeOutlineDocument:
    page_count: int
    entries: tuple[NativeOutlineEntry, ...]


def _flatten_outline(
    reader: PdfReader,
    nodes: Sequence[object],
    *,
    depth: int,
    entries: list[NativeOutlineEntry],
) -> None:
    if not isinstance(nodes, (list, tuple)):
        raise PyPdfOutlineAdapterError("invalid native outline structure")

    parent_seen = False
    for node in nodes:
        if isinstance(node, (list, tuple)):
            if not parent_seen:
                raise PyPdfOutlineAdapterError("outline children have no parent")
            _flatten_outline(reader, node, depth=depth + 1, entries=entries)
            continue

        title = getattr(node, "title", None)
        if not isinstance(title, str):
            raise PyPdfOutlineAdapterError("unsupported native outline entry")
        title = title.strip()
        if not title:
            raise PyPdfOutlineAdapterError("native outline title is empty")

        try:
            page_index = reader.get_destination_page_number(node)
        except Exception as exc:
            raise PyPdfOutlineAdapterError(
                "native outline destination inspection failed"
            ) from exc

        if page_index is None:
            destination_page = None
        elif isinstance(page_index, bool) or not isinstance(page_index, int):
            raise PyPdfOutlineAdapterError("invalid native outline page index")
        else:
            destination_page = page_index + 1
            if not 1 <= destination_page <= len(reader.pages):
                raise PyPdfOutlineAdapterError(
                    "native outline destination is outside the document"
                )

        entries.append(
            NativeOutlineEntry(
                order=len(entries) + 1,
                depth=depth,
                title=title,
                destination_page=destination_page,
            )
        )
        parent_seen = True


class PyPdfOutlineAdapter:
    """Extract deterministic native PDF outline entries with physical pages."""

    def inspect(self, data: bytes | bytearray) -> NativeOutlineDocument:
        if not isinstance(data, (bytes, bytearray)):
            raise PyPdfOutlineAdapterError("PDF input must be bytes")
        try:
            reader = PdfReader(BytesIO(bytes(data)))
        except Exception as exc:
            raise PyPdfOutlineAdapterError("pypdf could not parse the PDF") from exc

        try:
            if reader.is_encrypted:
                raise PyPdfOutlineAdapterError(
                    "encrypted PDF outline inspection is not supported"
                )
            page_count = len(reader.pages)
            if page_count < 1:
                raise PyPdfOutlineAdapterError("PDF has no physical pages")
            outline = reader.outline
        except PyPdfOutlineAdapterError:
            raise
        except Exception as exc:
            raise PyPdfOutlineAdapterError("PDF outline inventory failed") from exc

        if outline is None:
            outline = []
        if not isinstance(outline, (list, tuple)):
            raise PyPdfOutlineAdapterError("invalid native outline root")

        entries: list[NativeOutlineEntry] = []
        _flatten_outline(reader, outline, depth=0, entries=entries)
        return NativeOutlineDocument(page_count=page_count, entries=tuple(entries))
