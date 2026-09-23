"""STRUCTURAL RUNTIME FIXTURES; these are not real-book acceptance evidence."""

from __future__ import annotations

from io import BytesIO

from pypdf import PdfReader, PdfWriter
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


def styled_text_pdf(
    pages: list[list[tuple[float, float, str, float, bool]]],
    *,
    width: float = 612,
    height: float = 792,
) -> bytes:
    """Create deterministic native text with position, font size, and bold style."""

    writer = PdfWriter()
    for styled_lines in pages:
        page = writer.add_blank_page(width=width, height=height)
        if not styled_lines:
            continue
        regular_font = DictionaryObject(
            {
                NameObject("/Type"): NameObject("/Font"),
                NameObject("/Subtype"): NameObject("/Type1"),
                NameObject("/BaseFont"): NameObject("/Helvetica"),
            }
        )
        bold_font = DictionaryObject(
            {
                NameObject("/Type"): NameObject("/Font"),
                NameObject("/Subtype"): NameObject("/Type1"),
                NameObject("/BaseFont"): NameObject("/Helvetica-Bold"),
            }
        )
        page[NameObject("/Resources")] = DictionaryObject(
            {
                NameObject("/Font"): DictionaryObject(
                    {
                        NameObject("/F1"): writer._add_object(regular_font),
                        NameObject("/F2"): writer._add_object(bold_font),
                    }
                )
            }
        )
        commands: list[str] = []
        for x, y, text, font_size, bold in styled_lines:
            escaped = text.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
            font = "/F2" if bold else "/F1"
            commands.append(
                f"BT {font} {font_size:g} Tf {x:g} {y:g} Td ({escaped}) Tj ET"
            )
        stream = DecodedStreamObject()
        stream.set_data("\n".join(commands).encode("latin-1"))
        page[NameObject("/Contents")] = writer._add_object(stream)

    output = BytesIO()
    writer.write(output)
    return output.getvalue()


def hierarchy_pdf() -> bytes:
    """Create a deterministic five-page numbered hierarchy fixture."""

    headings = (
        "CHAPTER 1 Foundation",
        "1.1 First Section",
        "1.1.1 First Subsection",
        "CHAPTER 2 Continuation",
        "2.1 Second Section",
    )
    return styled_text_pdf(
        [
            [
                (72, 740, heading, 22, True),
                (72, 680, "Ordinary hierarchy fixture body line one.", 12, False),
                (72, 660, "Ordinary hierarchy fixture body line two.", 12, False),
                (72, 640, "Ordinary hierarchy fixture body line three.", 12, False),
            ]
            for heading in headings
        ]
    )


def hierarchy_pdf_with_outline(
    entries: tuple[tuple[str, int | None, int | None], ...] | None = None,
) -> bytes:
    """Add deterministic native bookmarks to the hierarchy structural fixture.

    Each tuple is ``(title, zero_based_page, parent_entry_index)``. A ``None``
    page intentionally creates a valid bookmark with an unresolved destination.
    """

    if entries is None:
        entries = (
            ("CHAPTER 1 Foundation", 0, None),
            ("1.1 First Section", 1, 0),
            ("1.1.1 First Subsection", 2, 1),
            ("CHAPTER 2 Continuation", 3, None),
            ("2.1 Second Section", 4, 3),
        )

    reader = PdfReader(BytesIO(hierarchy_pdf()))
    writer = PdfWriter()
    writer.append_pages_from_reader(reader)
    outline_objects: list[object] = []
    for index, (title, page_index, parent_index) in enumerate(entries):
        if parent_index is not None and not 0 <= parent_index < index:
            raise ValueError("outline parent must reference an earlier entry")
        parent = outline_objects[parent_index] if parent_index is not None else None
        outline_objects.append(
            writer.add_outline_item(title, page_index, parent=parent)
        )

    output = BytesIO()
    writer.write(output)
    return output.getvalue()
