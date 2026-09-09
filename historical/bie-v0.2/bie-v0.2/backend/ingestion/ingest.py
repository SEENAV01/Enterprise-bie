"""M2 Book Ingestion Engine: PDF/EPUB-ready document normalization.

The engine preserves page-level provenance and separates raw layout blocks
from normalized semantic blocks. OCR is optional so native PDFs remain cheap.
"""
from __future__ import annotations
import hashlib, json, re
from dataclasses import dataclass, asdict, field
from pathlib import Path
from typing import Any, Iterable

try:
    import fitz  # PyMuPDF
except ImportError:  # pragma: no cover
    fitz = None

@dataclass
class BoundingBox:
    x0: float; y0: float; x1: float; y1: float

@dataclass
class Block:
    block_id: str
    page: int
    block_index: int
    block_type: str
    text: str
    bbox: BoundingBox | None = None
    source_hash: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

@dataclass
class Page:
    page_number: int
    width: float
    height: float
    blocks: list[Block]

@dataclass
class BookDocument:
    document_id: str
    filename: str
    sha256: str
    pages: list[Page]
    metadata: dict[str, Any] = field(default_factory=dict)

HEADING_RE = re.compile(r"^(.{1,140})$")
EQUATION_RE = re.compile(r"(?:=|≈|∝|∫|Σ|√|Δ|∂|\^|_).{1,180}")

def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()

def classify_block(text: str, font_size: float | None = None, bold: bool = False) -> str:
    t = " ".join(text.split())
    if not t:
        return "empty"
    if EQUATION_RE.search(t) and len(t) < 220:
        return "equation_candidate"
    if bold or (font_size is not None and font_size >= 15 and len(t) < 180):
        return "heading_candidate"
    return "paragraph"

def ingest_pdf(path: str | Path) -> BookDocument:
    if fitz is None:
        raise RuntimeError("PyMuPDF is required: pip install pymupdf")
    path = Path(path)
    digest = sha256_file(path)
    doc = fitz.open(path)
    pages: list[Page] = []
    for pno, page in enumerate(doc, start=1):
        blocks: list[Block] = []
        raw = page.get_text("dict")
        bi = 0
        for block in raw.get("blocks", []):
            if block.get("type") != 0:
                # Preserve image blocks as assets without pretending OCR text exists.
                rect = block.get("bbox")
                blocks.append(Block(
                    block_id=f"p{pno}_b{bi}", page=pno, block_index=bi,
                    block_type="image", text="", bbox=BoundingBox(*rect) if rect else None,
                    source_hash=digest, metadata={"raw_block_type": block.get("type")}
                )); bi += 1; continue
            lines = block.get("lines", [])
            text_parts=[]; max_size=None; bold=False
            for line in lines:
                for span in line.get("spans", []):
                    text_parts.append(span.get("text", ""))
                    size=span.get("size")
                    max_size=max(max_size or size, size or 0)
                    bold = bold or bool(span.get("flags", 0) & 16)
            text=" ".join(" ".join(text_parts).split())
            if not text: continue
            rect=block.get("bbox")
            blocks.append(Block(
                block_id=f"p{pno}_b{bi}", page=pno, block_index=bi,
                block_type=classify_block(text, max_size, bold), text=text,
                bbox=BoundingBox(*rect) if rect else None, source_hash=digest,
                metadata={"font_size_max": max_size, "bold": bold}
            )); bi += 1
        pages.append(Page(pno, page.rect.width, page.rect.height, blocks))
    metadata = {k:v for k,v in doc.metadata.items() if v}
    return BookDocument(path.stem, path.name, digest, pages, metadata)

def save_json(book: BookDocument, out: str | Path) -> None:
    payload=asdict(book)
    Path(out).write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

def iter_text(book: BookDocument) -> Iterable[str]:
    for page in book.pages:
        for block in page.blocks:
            if block.text:
                yield block.text
