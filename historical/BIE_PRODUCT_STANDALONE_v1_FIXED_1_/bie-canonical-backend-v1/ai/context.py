def assemble_context(sources, max_items=None):
    selected=sources if max_items is None else sources[:max_items]
    return {"items":selected,"count":len(selected)}

def grounded_context(sources, citations):
    return {"sources":sources,"citations":citations,
            "grounding_required":bool(sources)}
