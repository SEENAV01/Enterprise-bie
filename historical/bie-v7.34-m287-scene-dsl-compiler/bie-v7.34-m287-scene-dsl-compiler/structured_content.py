import re
from collections import defaultdict

def detect_table_from_lines(lines):
    """Conservative table detector for text extracted from a page."""
    rows = []
    for line in lines:
        text = (line.get("text") or "").strip()
        if not text:
            continue
        if "|" in text:
            cells = [c.strip() for c in text.split("|")]
            if len(cells) >= 2:
                rows.append(cells)
        elif re.search(r"\S+\s{3,}\S+", text):
            cells = [c.strip() for c in re.split(r"\s{3,}", text) if c.strip()]
            if len(cells) >= 2:
                rows.append(cells)
    if len(rows) >= 2:
        width = max(map(len, rows))
        normalized = [r + [""] * (width-len(r)) for r in rows]
        return {"kind":"TABLE","rows":normalized,"confidence":0.65}
    return None

def detect_equation(text):
    t = text.strip()
    signals = [
        r"=", r"\\frac", r"\\sqrt", r"\\alpha", r"\\beta",
        r"∫", r"∑", r"√", r"≤", r"≥", r"\^"
    ]
    score = sum(bool(re.search(p, t)) for p in signals)
    if score >= 1 and len(t) < 500:
        return {"kind":"EQUATION_CANDIDATE","text":t,"signals":score}
    return None

def link_captions(blocks):
    links = []
    for i, block in enumerate(blocks):
        text = (block.get("text") or "").strip()
        if re.match(r"^(figure|fig\.|table)\s*\d+", text, re.I):
            target = None
            for j in range(max(0, i-2), min(len(blocks), i+3)):
                if j != i and blocks[j].get("kind") in {"FIGURE","TABLE"}:
                    target = blocks[j].get("block_id")
                    break
            links.append({"caption_block":block.get("block_id"),
                          "target_block":target,
                          "linked":target is not None})
    return links

def reading_order(blocks):
    """Stable top-to-bottom, left-to-right ordering by bounding box."""
    def key(b):
        bbox=b.get("bbox") or [0,0,0,0]
        return (round(float(bbox[1]),1), round(float(bbox[0]),1), b.get("block_id",""))
    return sorted(blocks,key=key)

def enrich_page(page):
    blocks = page.get("blocks", [])
    ordered = reading_order(blocks)
    text_lines = [{"text":b.get("text","")} for b in ordered if b.get("text")]
    table = detect_table_from_lines(text_lines)
    enriched = []
    for b in ordered:
        item=dict(b)
        eq=detect_equation(item.get("text",""))
        if eq and item.get("kind")=="PARAGRAPH":
            item["kind"]="EQUATION_CANDIDATE"
            item["equation"]=eq
        enriched.append(item)
    if table:
        enriched.append({
            "block_id":f"page:{page['page']}:table:0",
            "kind":"TABLE",
            "rows":table["rows"],
            "confidence":table["confidence"],
            "bbox":None
        })
    return {"page":page["page"],"blocks":enriched}

def enrich_document(layout_ir):
    pages=[enrich_page(p) for p in layout_ir.get("pages",[])]
    all_blocks=[b for p in pages for b in p["blocks"]]
    return {
        "ir_version":"2.1",
        "source_uri":layout_ir.get("source_uri"),
        "input_kind":layout_ir.get("input_kind"),
        "page_count":len(pages),
        "pages":pages,
        "sections":layout_ir.get("sections",[]),
        "figure_count":sum(b.get("kind")=="FIGURE" for b in all_blocks),
        "table_count":sum(b.get("kind")=="TABLE" for b in all_blocks),
        "equation_count":sum(b.get("kind")=="EQUATION_CANDIDATE" for b in all_blocks),
        "caption_links":link_captions(all_blocks),
        "reading_order":"bbox_y_then_x"
    }

def content_inventory(ir):
    kinds=defaultdict(int)
    for page in ir.get("pages",[]):
        for block in page.get("blocks",[]):
            kinds[block.get("kind","UNKNOWN")]+=1
    return dict(kinds)
