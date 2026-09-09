def suitability_score(asset, requirements):
    score=1.0
    reasons=[]
    if requirements.get("media_type") and asset.get("media_type")!=requirements["media_type"]:
        score-=0.5; reasons.append("MEDIA_TYPE_MISMATCH")
    if requirements.get("min_width") and (asset.get("width") or 0)<requirements["min_width"]:
        score-=0.2; reasons.append("WIDTH_TOO_LOW")
    if requirements.get("min_height") and (asset.get("height") or 0)<requirements["min_height"]:
        score-=0.2; reasons.append("HEIGHT_TOO_LOW")
    return {"score":max(0.0,min(1.0,score)),"reasons":reasons}

def rank_assets(assets, requirements):
    return sorted(
        [{"asset":a,"suitability":suitability_score(a,requirements)} for a in assets],
        key=lambda x:x["suitability"]["score"],reverse=True)
