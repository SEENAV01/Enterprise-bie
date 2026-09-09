def deduplicate_assets(assets):
    seen={}
    unique=[]
    aliases={}
    for a in assets:
        key=a["fingerprint"]
        if key in seen: aliases[a["id"]]=seen[key]
        else:
            seen[key]=a["id"]; unique.append(a)
    return {"unique":unique,"aliases":aliases}
