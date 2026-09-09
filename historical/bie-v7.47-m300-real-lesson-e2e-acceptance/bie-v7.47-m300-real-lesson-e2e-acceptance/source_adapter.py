from pathlib import Path
import hashlib
import re
import zipfile
import xml.etree.ElementTree as ET

def _stable_id(prefix, text):
    digest = hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]
    return f"{prefix}:{digest}"

def read_text(path):
    return Path(path).read_text(encoding="utf-8")

def read_epub(path):
    """Extract readable XHTML/HTML documents from an EPUB container."""
    blocks = []
    with zipfile.ZipFile(path) as z:
        names = [n for n in z.namelist()
                 if n.lower().endswith((".xhtml", ".html", ".htm"))]
        for name in sorted(names):
            raw = z.read(name).decode("utf-8", errors="ignore")
            text = re.sub(r"<[^>]+>", " ", raw)
            text = re.sub(r"\s+", " ", text).strip()
            if text:
                blocks.append({
                    "source": name,
                    "text": text,
                    "block_id": _stable_id("block", name + "\n" + text)
                })
    return blocks

def read_pdf(path):
    """
    Page-aware PDF extraction using pypdf.
    OCR is intentionally a separate adapter: scanned/image-only PDFs are
    reported as needing OCR rather than silently pretending extraction worked.
    """
    try:
        from pypdf import PdfReader
    except ImportError as exc:
        raise RuntimeError(
            "PDF support requires pypdf. Install with: pip install pypdf"
        ) from exc

    reader = PdfReader(str(path))
    pages = []
    for number, page in enumerate(reader.pages, start=1):
        text = (page.extract_text() or "").strip()
        pages.append({
            "page": number,
            "text": text,
            "block_id": _stable_id("page", f"{path}:{number}:{text}")
        })
    nonempty = sum(bool(p["text"]) for p in pages)
    return {
        "pages": pages,
        "page_count": len(pages),
        "text_pages": nonempty,
        "needs_ocr": len(pages) > 0 and nonempty == 0
    }

def ingest_source(path):
    p = Path(path)
    suffix = p.suffix.lower()
    if suffix == ".pdf":
        result = read_pdf(p)
        return {
            "input_kind": "pdf",
            "source_uri": str(p.resolve()),
            "content": result,
            "status": "NEEDS_OCR" if result["needs_ocr"] else "INGESTED"
        }
    if suffix == ".epub":
        blocks = read_epub(p)
        return {
            "input_kind": "epub",
            "source_uri": str(p.resolve()),
            "content": {"blocks": blocks, "block_count": len(blocks)},
            "status": "INGESTED" if blocks else "EMPTY"
        }
    if suffix in {".txt", ".md"}:
        text = read_text(p)
        block = {"source": p.name, "text": text,
                 "block_id": _stable_id("block", p.name + "\n" + text)}
        return {
            "input_kind": "text",
            "source_uri": str(p.resolve()),
            "content": {"blocks": [block], "block_count": 1},
            "status": "INGESTED" if text.strip() else "EMPTY"
        }
    raise ValueError(f"Unsupported source type: {suffix}")

def build_document_ir(source):
    content = source["content"]
    if source["input_kind"] == "pdf":
        blocks = [
            {"locator": {"page": p["page"]}, "text": p["text"],
             "block_id": p["block_id"]}
            for p in content["pages"] if p["text"]
        ]
    else:
        blocks = [
            {"locator": {"source": b["source"]}, "text": b["text"],
             "block_id": b["block_id"]}
            for b in content["blocks"] if b["text"].strip()
        ]
    return {
        "ir_version": "1.0",
        "source_uri": source["source_uri"],
        "input_kind": source["input_kind"],
        "status": source["status"],
        "blocks": blocks,
        "block_count": len(blocks),
        "requires_ocr": source["status"] == "NEEDS_OCR"
    }
