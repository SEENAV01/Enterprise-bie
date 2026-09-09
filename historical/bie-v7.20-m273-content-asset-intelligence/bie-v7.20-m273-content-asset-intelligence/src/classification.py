def classify_asset(meta):
    t=meta["media_type"]
    mapping={"image":"IMAGE","video":"VIDEO","audio":"AUDIO","document":"DOCUMENT",
             "3d":"THREE_D"}
    return {"asset_id":meta["asset_id"],"class":mapping.get(t,"OTHER")}

def tags_for_asset(meta):
    tags=[]
    if meta.get("media_type"): tags.append(meta["media_type"])
    if meta.get("duration") is not None: tags.append("timed")
    if meta.get("width") and meta.get("height"):
        tags.append("visual")
    return tags
