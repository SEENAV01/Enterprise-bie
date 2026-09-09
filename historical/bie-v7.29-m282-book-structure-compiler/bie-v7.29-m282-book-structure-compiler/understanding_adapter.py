from pathlib import Path
import re

def _clean(text):
    return re.sub(r"\s+", " ", (text or "")).strip()

def _heading_level(text):
    t = _clean(text)
    if not t:
        return None
    if re.match(r"^(chapter|unit|part)\s+\d+\b", t, re.I):
        return 1
    if re.match(r"^\d+(\.\d+)*\s+\S+", t):
        return min(3, t.split()[0].count(".") + 1)
    if len(t) <= 90 and not t.endswith((".", ",", ";", ":")):
        return 2
    return None

def classify_block(text, font_size=None, is_bold=False):
    t = _clean(text)
    if not t:
        return "EMPTY"
    if _heading_level(t):
        return "HEADING"
    if re.search(r"\b(definition|theorem|law|principle|example)\b", t, re.I):
        return "SEMANTIC_BLOCK"
    if re.search(r"[=∫∑√]|\\frac|\\sqrt|\\alpha|\\beta", t):
        return "EQUATION_CANDIDATE"
    return "PARAGRAPH"

def pdf_layout_ir(path):
    try:
        import fitz
    except ImportError as exc:
        raise RuntimeError(
            "Layout-aware PDF support requires PyMuPDF. Install requirements.txt."
        ) from exc

    doc = fitz.open(str(path))
    pages = []
    total_images = 0
    for page_no, page in enumerate(doc, start=1):
        data = page.get_text("dict")
        blocks = []
        for block_no, block in enumerate(data.get("blocks", [])):
            bbox = block.get("bbox")
            if block.get("type") == 1:
                total_images += 1
                blocks.append({
                    "block_id": f"page:{page_no}:image:{block_no}",
                    "kind": "FIGURE",
                    "bbox": list(bbox) if bbox else None
                })
                continue
            lines = []
            for line in block.get("lines", []):
                spans = line.get("spans", [])
                text = _clean("".join(s.get("text", "") for s in spans))
                if text:
                    lines.append({
                        "text": text,
                        "font_size": max((s.get("size", 0) for s in spans), default=0),
                        "bold": any("bold" in s.get("font", "").lower() for s in spans)
                    })
            text = _clean(" ".join(x["text"] for x in lines))
            if text:
                size = max((x["font_size"] for x in lines), default=0)
                bold = any(x["bold"] for x in lines)
                blocks.append({
                    "block_id": f"page:{page_no}:block:{block_no}",
                    "kind": classify_block(text, size, bold),
                    "text": text,
                    "bbox": list(bbox) if bbox else None,
                    "font_size": size,
                    "bold": bold
                })
        pages.append({"page": page_no, "blocks": blocks})

    return {
        "ir_version": "2.0",
        "input_kind": "pdf",
        "source_uri": str(Path(path).resolve()),
        "page_count": len(pages),
        "pages": pages,
        "figure_count": total_images,
        "layout_aware": True
    }

def build_hierarchy(layout_ir):
    sections = []
    current = None
    for page in layout_ir.get("pages", []):
        for block in page["blocks"]:
            if block["kind"] == "HEADING":
                level = _heading_level(block["text"]) or 2
                current = {
                    "section_id": block["block_id"],
                    "level": level,
                    "title": block["text"],
                    "start_page": page["page"],
                    "blocks": []
                }
                sections.append(current)
            elif block["kind"] != "FIGURE":
                if current is None:
                    current = {
                        "section_id": "preamble",
                        "level": 1,
                        "title": "Preamble",
                        "start_page": page["page"],
                        "blocks": []
                    }
                    sections.append(current)
                current["blocks"].append(block["block_id"])
    return sections

def ocr_image(path):
    try:
        from PIL import Image
        import pytesseract
    except ImportError as exc:
        raise RuntimeError(
            "OCR support requires Pillow and pytesseract. Install requirements.txt."
        ) from exc
    text = pytesseract.image_to_string(Image.open(path))
    return {
        "status": "OCR_COMPLETE" if text.strip() else "OCR_EMPTY",
        "text": text,
        "engine": "tesseract"
    }

def ocr_pdf(path, dpi=150):
    try:
        import fitz
        from PIL import Image
        import pytesseract
    except ImportError as exc:
        raise RuntimeError(
            "PDF OCR requires PyMuPDF, Pillow and pytesseract."
        ) from exc

    doc = fitz.open(str(path))
    pages = []
    for number, page in enumerate(doc, start=1):
        pix = page.get_pixmap(dpi=dpi, alpha=False)
        image = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
        text = pytesseract.image_to_string(image)
        pages.append({
            "page": number,
            "text": text,
            "status": "OCR_COMPLETE" if text.strip() else "OCR_EMPTY"
        })
    return {"status": "OCR_COMPLETE", "pages": pages, "engine": "tesseract"}

def analyze_source(path):
    suffix = Path(path).suffix.lower()
    if suffix != ".pdf":
        raise ValueError("M280 layout-aware analyzer currently targets PDF sources.")
    layout = pdf_layout_ir(path)
    layout["sections"] = build_hierarchy(layout)
    return layout
