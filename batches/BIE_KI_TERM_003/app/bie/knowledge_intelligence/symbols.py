class E(ValueError):pass
def bind(symbol,entity_id,kind,anchor):
 if not symbol.strip() or not entity_id or kind not in {"variable","constant","operator","unit","label"} or not anchor:raise E("symbol")
 return {"symbol":symbol.strip(),"entity_id":entity_id,"kind":kind,"anchor_id":anchor}
