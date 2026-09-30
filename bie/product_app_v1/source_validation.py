from __future__ import annotations

from dataclasses import dataclass
from html import escape
import hashlib

from .models import OperatorError

MAX_SOURCE_BYTES = 25 * 1024 * 1024
PDF_HEADER_WINDOW = 1024


@dataclass(frozen=True)
class SourceValidation:
    accepted: bool
    status: str
    media_type: str
    byte_length: int
    sha256: str | None
    signature_offset: int | None
    diagnostics: tuple[str, ...]

    def to_safe_dict(self) -> dict[str, object]:
        return {
            "accepted": self.accepted,
            "status": self.status,
            "media_type": self.media_type,
            "byte_length": self.byte_length,
            "sha256": self.sha256,
            "signature_offset": self.signature_offset,
            "diagnostics": list(self.diagnostics),
            "deep_document_validation": "DEFERRED_TO_CANONICAL_DOCUMENT_INTELLIGENCE",
        }


def validate_pdf_source(
    payload: bytes,
    *,
    media_type: str = "application/pdf",
    max_bytes: int = MAX_SOURCE_BYTES,
) -> SourceValidation:
    if type(payload) is not bytes:
        raise OperatorError("source_payload_must_be_bytes")
    if type(media_type) is not str:
        raise OperatorError("media_type_must_be_string")
    normalized = media_type.partition(";")[0].strip().lower()
    diagnostics: list[str] = []
    if normalized != "application/pdf":
        diagnostics.append("UNSUPPORTED_MEDIA_TYPE")
    if len(payload) == 0:
        diagnostics.append("EMPTY_SOURCE")
    if len(payload) > max_bytes:
        diagnostics.append("SOURCE_TOO_LARGE")
    offset = payload[:PDF_HEADER_WINDOW].find(b"%PDF-") if payload else -1
    if payload and offset < 0:
        diagnostics.append("PDF_SIGNATURE_NOT_FOUND")
    accepted = not diagnostics
    return SourceValidation(
        accepted=accepted,
        status="BASIC_VALIDATED" if accepted else "REJECTED",
        media_type=normalized,
        byte_length=len(payload),
        sha256=hashlib.sha256(payload).hexdigest() if payload else None,
        signature_offset=offset if offset >= 0 else None,
        diagnostics=tuple(diagnostics),
    )


def render_source_validation(validation: SourceValidation, *, display_name: str) -> str:
    name = escape(str(display_name), quote=True)
    state = "accepted" if validation.accepted else "rejected"
    rows = [
        ("Status", validation.status),
        ("File", name),
        ("Media type", escape(validation.media_type)),
        ("Bytes", str(validation.byte_length)),
        ("SHA-256", escape(validation.sha256 or "not-computed")),
        ("PDF header offset", str(validation.signature_offset) if validation.signature_offset is not None else "not-found"),
    ]
    body = "".join(
        f"<tr><th scope='row'>{escape(label)}</th><td>{value}</td></tr>"
        for label, value in rows
    )
    diagnostics = "".join(
        f"<li>{escape(code)}</li>" for code in validation.diagnostics
    ) or "<li>None</li>"
    return (
        "<section class='source-validation' aria-labelledby='source-validation-title' "
        f"data-validation-state='{state}'>"
        "<h2 id='source-validation-title'>Source validation</h2>"
        "<p>Basic transport validation only. Deep document validation is performed by the canonical document-intelligence runtime.</p>"
        f"<table><tbody>{body}</tbody></table>"
        f"<h3>Diagnostics</h3><ul>{diagnostics}</ul>"
        "</section>"
    )
