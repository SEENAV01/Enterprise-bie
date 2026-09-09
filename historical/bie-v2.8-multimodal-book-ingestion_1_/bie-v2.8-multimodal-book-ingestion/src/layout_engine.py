BLOCK_TYPES=["heading","paragraph","list","figure","caption","table","equation","footnote","reference","unknown"]

def classify_block(block):
    text=(block.get("text") or "").strip()
    if block.get("is_heading"): return "heading"
    if block.get("is_caption"): return "caption"
    if block.get("is_equation"): return "equation"
    if block.get("is_table"): return "table"
    if block.get("is_figure"): return "figure"
    return "paragraph" if text else "unknown"

def link_caption_to_asset(caption, assets):
    if not assets: return None
    return assets[0].get("asset_id")
