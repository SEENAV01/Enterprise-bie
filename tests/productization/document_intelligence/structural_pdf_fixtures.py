"""STRUCTURAL RUNTIME FIXTURES; these are not real-book acceptance evidence."""

from __future__ import annotations

from io import BytesIO

from pypdf import PdfWriter
from pypdf.generic import DecodedStreamObject, DictionaryObject, NameObject


def structural_pdf(
    page_count: int = 1,
    *,
    text_pages: set[int] | None = None,
    metadata: dict[str, str] | None = None,
    text: str = "BIE structural runtime fixture",
) -> bytes:
    writer = PdfWriter()
    selected_text_pages = text_pages or set()

    for page_index in range(page_count):
        page = writer.add_blank_page(width=612, height=792)
        if page_index in selected_text_pages:
            font = DictionaryObject(
                {
                    NameObject("/Type"): NameObject("/Font"),
                    NameObject("/Subtype"): NameObject("/Type1"),
                    NameObject("/BaseFont"): NameObject("/Helvetica"),
                }
            )
            page[NameObject("/Resources")] = DictionaryObject(
                {
                    NameObject("/Font"): DictionaryObject(
                        {NameObject("/F1"): writer._add_object(font)}
                    )
                }
            )
            stream = DecodedStreamObject()
            escaped = text.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
            stream.set_data(
                f"BT /F1 12 Tf 72 720 Td ({escaped}) Tj ET".encode("latin-1")
            )
            page[NameObject("/Contents")] = writer._add_object(stream)

    if metadata:
        writer.add_metadata(metadata)

    output = BytesIO()
    writer.write(output)
    return output.getvalue()


def positioned_text_pdf(
    pages: list[list[tuple[float, float, str]]],
) -> bytes:
    """Create structural pages with native text at explicit PDF coordinates."""

    writer = PdfWriter()
    for positioned_lines in pages:
        page = writer.add_blank_page(width=612, height=792)
        if not positioned_lines:
            continue
        font = DictionaryObject(
            {
                NameObject("/Type"): NameObject("/Font"),
                NameObject("/Subtype"): NameObject("/Type1"),
                NameObject("/BaseFont"): NameObject("/Helvetica"),
            }
        )
        page[NameObject("/Resources")] = DictionaryObject(
            {
                NameObject("/Font"): DictionaryObject(
                    {NameObject("/F1"): writer._add_object(font)}
                )
            }
        )
        commands: list[str] = []
        for x, y, text in positioned_lines:
            escaped = text.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
            commands.append(f"BT /F1 12 Tf {x} {y} Td ({escaped}) Tj ET")
        stream = DecodedStreamObject()
        stream.set_data("\n".join(commands).encode("latin-1"))
        page[NameObject("/Contents")] = writer._add_object(stream)

    output = BytesIO()
    writer.write(output)
    return output.getvalue()
