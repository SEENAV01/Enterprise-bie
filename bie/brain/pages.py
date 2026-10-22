"""Book pages for the brain: native text blocks from the canonical DI runtime plus a page image.

The text comes from ``bie.document_intelligence.real_pdf_text_runtime`` (the same real upstream the
pipeline uses), so block ids such as ``p0003-b0007`` are the pipeline's own source anchors. The
image is rendered with pypdfium2 (installed with pdfplumber) so a vision model can read tables,
diagrams, labels and equations that have no text layer.
"""
from __future__ import annotations

import base64
import hashlib
import io
from dataclasses import dataclass

MAX_IMAGE_EDGE = 1568        # long edge in pixels; vision models downscale larger images anyway
JPEG_QUALITY = 90


@dataclass(frozen=True)
class Block:
    id: str
    text: str
    box: tuple              # (x0, y0, x1, y1) as fractions of the page


@dataclass(frozen=True)
class Page:
    number: int
    blocks: tuple
    image: bytes | None = None
    media_type: str = "image/png"
    width: int = 0
    height: int = 0

    @property
    def block_ids(self):
        return tuple(b.id for b in self.blocks)

    def image_part(self):
        if not self.image:
            return None
        return {"type": "image", "media_type": self.media_type, "data": base64.b64encode(self.image).decode("ascii")}

    def image_sha256(self):
        return hashlib.sha256(self.image).hexdigest() if self.image else None


def parse_page_range(spec: str | None, page_count: int):
    if not spec:
        return list(range(1, page_count + 1))
    wanted = set()
    for part in str(spec).split(","):
        part = part.strip()
        if not part:
            continue
        if "-" in part:
            first, last = (int(x) for x in part.split("-", 1))
        else:
            first = last = int(part)
        if not 1 <= first <= last <= page_count:
            raise ValueError(f"page range {part} is outside 1-{page_count}")
        wanted.update(range(first, last + 1))
    return sorted(wanted)


def render_page_image(pdf_bytes: bytes, number: int, *, max_edge: int = MAX_IMAGE_EDGE):
    """(image bytes, media type, width, height) of page ``number`` (1-based)."""
    import pypdfium2 as pdfium

    document = pdfium.PdfDocument(pdf_bytes)
    try:
        page = document[number - 1]
        width_pt, height_pt = page.get_size()
        scale = max_edge / max(width_pt, height_pt)
        image = page.render(scale=scale).to_pil().convert("RGB")
    finally:
        document.close()
    png = io.BytesIO()
    image.save(png, format="PNG", optimize=True)
    data, media = png.getvalue(), "image/png"
    if len(data) > 700_000:                         # photo-heavy pages: JPEG keeps the request small
        jpeg = io.BytesIO()
        image.save(jpeg, format="JPEG", quality=JPEG_QUALITY)
        data, media = jpeg.getvalue(), "image/jpeg"
    return data, media, image.width, image.height


def load_pages(pdf_bytes: bytes, pages: str | None = None, *, with_images: bool = True):
    """(source sha256, page count, [Page]) for the selected pages."""
    from bie.document_intelligence.real_pdf_text_runtime import inspect_real_pdf_text

    inspection = inspect_real_pdf_text(pdf_bytes)
    wanted = parse_page_range(pages, inspection.page_count)
    result = []
    for layout in inspection.pages:
        if layout.page not in wanted:
            continue
        ordered = sorted(layout.source_linked_blocks, key=lambda item: item.order_index)
        blocks = tuple(Block(item.block.block_id, item.block.text, tuple(round(v, 4) for v in item.region.box))
                       for item in ordered)
        if with_images:
            data, media, width, height = render_page_image(pdf_bytes, layout.page)
            result.append(Page(layout.page, blocks, data, media, width, height))
        else:
            result.append(Page(layout.page, blocks))
    return inspection.source_hash, inspection.page_count, result
