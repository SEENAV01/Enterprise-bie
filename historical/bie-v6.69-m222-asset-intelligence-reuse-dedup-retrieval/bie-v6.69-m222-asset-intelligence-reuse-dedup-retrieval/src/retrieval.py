def score(asset,query):
    q=set(query.lower().split())
    fields=set(asset.get("tags",[]))
    fields.update(str(asset.get("metadata",{}).get("subject","")).lower().split())
    fields.update(str(asset.get("asset_type","")).lower().split())
    return len(q & fields)

def retrieve(index,query,asset_type=None,limit=10):
    candidates=index.all()
    if asset_type:
        candidates=[a for a in candidates if a["asset_type"]==asset_type]
    return sorted(candidates,key=lambda a:score(a,query),reverse=True)[:limit]
