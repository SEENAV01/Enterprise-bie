def collect_assets(pages):
    assets=[]
    for p in pages:
        for b in p.get("blocks",[]):
            if b.get("block_type") in {"figure","table","equation"}:
                assets.append({
                    "asset_ref":b.get("asset_ref") or b["block_id"],
                    "page":p["page"],
                    "type":b["block_type"],
                    "bbox":b.get("bbox"),
                    "text":b.get("text","")
                })
    return assets

def asset_review(asset):
    if asset["type"]=="table":
        return {"mode":"table_parse_then_verify","status":"REVIEW"}
    if asset["type"]=="figure":
        return {"mode":"vision_interpretation","status":"REVIEW"}
    if asset["type"]=="equation":
        return {"mode":"math_parse_then_verify","status":"REVIEW"}
    return {"mode":"unknown","status":"REVIEW"}
