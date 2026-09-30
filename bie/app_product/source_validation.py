from __future__ import annotations

import hashlib
import html
import re

from .contracts import AppProductError, SourceValidation


MAX_PDF_BYTES = 25 * 1024 * 1024
_PDF_HEADER = re.compile(br"%PDF-[12]\.[0-9]")


def _display_name(value: str | None) -> str:
    value = "Selected PDF" if value is None else value.strip()
    if (
        not value
        or len(value) > 256
        or any(ord(c) < 32 for c in value)
        or "/" in value
        or "\\" in value
        or value in {".", ".."}
    ):
        raise AppProductError("invalid_display_name")
    return value


def _media_type(value: str) -> str:
    if type(value) is not str:
        return ""
    return value.partition(";")[0].strip().lower()


def validate_source(
    payload: bytes,
    display_name: str | None,
    media_type: str,
    *,
    max_bytes: int = MAX_PDF_BYTES,
) -> SourceValidation:
    if type(payload) is not bytes:
        raise AppProductError("source_payload_must_be_bytes")
    if type(max_bytes) is not int or max_bytes < 1:
        raise AppProductError("invalid_source_limit")
    name = _display_name(display_name)
    mt = _media_type(media_type)
    issues: list[str] = []
    warnings: list[str] = []
    if mt != "application/pdf":
        issues.append("UNSUPPORTED_MEDIA_TYPE")
    if not payload:
        issues.append("EMPTY_SOURCE")
    elif len(payload) > max_bytes:
        issues.append("SOURCE_TOO_LARGE")
    header = _PDF_HEADER.search(payload[:1024]) if payload else None
    if payload and header is None:
        issues.append("PDF_HEADER_NOT_FOUND")
    if not name.lower().endswith(".pdf"):
        warnings.append("DISPLAY_NAME_NOT_PDF_SUFFIX")
    digest = hashlib.sha256(payload).hexdigest() if payload else None
    return SourceValidation(
        "REJECTED" if issues else "READY_TO_SUBMIT",
        name,
        mt or "application/octet-stream",
        len(payload),
        digest,
        tuple(issues),
        tuple(warnings),
        "NOT_RUN" if issues else "PENDING",
    )


def render_source_validation_html(view: SourceValidation) -> str:
    data = view.to_safe_dict()
    state = html.escape(data["status"])
    name = html.escape(data["display_name"])
    media = html.escape(data["media_type"])
    digest = html.escape(data["source_sha256"] or "not-computed")
    issues = "".join(f"<li>{html.escape(x)}</li>" for x in data["issues"]) or "<li>None</li>"
    warnings = "".join(f"<li>{html.escape(x)}</li>" for x in data["warnings"]) or "<li>None</li>"
    return (
        f'<section aria-label="Source validation" data-status="{state}">'
        f"<h2>Source validation</h2><dl>"
        f"<dt>Name</dt><dd>{name}</dd><dt>Media type</dt><dd>{media}</dd>"
        f"<dt>Bytes</dt><dd>{data['byte_length']}</dd><dt>SHA-256</dt><dd>{digest}</dd>"
        f"<dt>Native validation</dt><dd>{html.escape(data['native_validation'])}</dd></dl>"
        f"<h3>Issues</h3><ul>{issues}</ul><h3>Warnings</h3><ul>{warnings}</ul></section>"
    )
