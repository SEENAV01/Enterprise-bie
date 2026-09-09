ASSET_CLASSES = [
    "figure","diagram","photo","illustration","chart","table",
    "equation","formula","map","timeline","screenshot","decorative","unknown"
]

def classify_asset(metadata):
    text=(metadata.get("caption","")+" "+metadata.get("ocr_text","")).lower()
    if "table" in text: return "table"
    if "figure" in text or "diagram" in text: return "diagram"
    if any(x in text for x in ["equation","formula"]): return "equation"
    if "chart" in text or "graph" in text: return "chart"
    return metadata.get("hint","unknown")

def quality_score(asset):
    scores=[]
    if asset.get("width",0)>=800: scores.append(1)
    if asset.get("height",0)>=600: scores.append(1)
    if asset.get("ocr_confidence",1)>=.9: scores.append(1)
    if asset.get("has_caption"): scores.append(1)
    return round(sum(scores)/max(1,len(scores)),2)

def make_record(asset_id, metadata):
    cls=classify_asset(metadata)
    q=quality_score(metadata)
    return {
        "asset_id":asset_id,
        "class":cls,
        "quality_score":q,
        "source_page":metadata.get("source_page"),
        "caption":metadata.get("caption"),
        "ocr_text":metadata.get("ocr_text"),
        "reuse_policy":"REUSE_SOURCE" if q>=.75 else "RECONSTRUCT_OR_GENERATE",
        "provenance":{"origin":"BOOK","source_page":metadata.get("source_page")}
    }
