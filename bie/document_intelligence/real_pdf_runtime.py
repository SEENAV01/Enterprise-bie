"""Genuine PDF inspection runtime composed from canonical DI contracts."""

from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType
from typing import Mapping

from .pdf_ingest import PDFIngestError, ingest_pdf
from .pypdf_adapter import MetadataValue, PyPdfAdapter, PyPdfAdapterError
from .real_pdf_contract import E as RealPdfContractError
from .real_pdf_contract import inspect_pdf
from .source_hash import HashError, source_sha256


class RealPdfRuntimeError(ValueError):
    """Raised when genuine PDF inspection cannot satisfy canonical contracts."""


@dataclass(frozen=True)
class RealPdfInspection:
    source_hash: str
    byte_length: int
    page_count: int
    text_pages: int
    encrypted: bool
    metadata: Mapping[str, MetadataValue]

    def to_dict(self) -> dict[str, object]:
        return {
            "source_hash": self.source_hash,
            "byte_length": self.byte_length,
            "page_count": self.page_count,
            "text_pages": self.text_pages,
            "encrypted": self.encrypted,
            "metadata": dict(self.metadata),
        }


def inspect_real_pdf(data: bytes | bytearray) -> RealPdfInspection:
    """Inspect real PDF bytes through pypdf and the existing DI contracts."""

    if not isinstance(data, (bytes, bytearray)):
        raise RealPdfRuntimeError("PDF input must be bytes")
    payload = bytes(data)

    try:
        inventory = ingest_pdf(PyPdfAdapter(), payload)
        contract = inspect_pdf(payload, inventory.page_count)
        canonical_hash = source_sha256(payload)
    except (
        PDFIngestError,
        PyPdfAdapterError,
        RealPdfContractError,
        HashError,
    ) as exc:
        raise RealPdfRuntimeError("real PDF inspection failed") from exc

    if contract["source_hash"] != canonical_hash:
        raise RealPdfRuntimeError("canonical source hash mismatch")

    metadata = MappingProxyType(dict(sorted(inventory.metadata.items())))
    return RealPdfInspection(
        source_hash=canonical_hash,
        byte_length=contract["byte_length"],
        page_count=contract["page_count"],
        text_pages=inventory.text_pages,
        encrypted=inventory.encrypted,
        metadata=metadata,
    )
