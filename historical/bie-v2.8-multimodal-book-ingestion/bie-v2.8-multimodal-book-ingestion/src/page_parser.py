def normalize_text(text):
    return " ".join((text or "").split())

def parse_page(page_number, text_blocks=None, images=None, tables=None, equations=None):
    return {
        "page_id":f"p{page_number}",
        "page_number":page_number,
        "text_blocks":[{"block_id":f"p{page_number}_t{i+1}","text":normalize_text(x)} for i,x in enumerate(text_blocks or [])],
        "images":images or [],
        "tables":tables or [],
        "equations":equations or []
    }
