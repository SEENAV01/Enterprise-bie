from asset_intelligence import make_record

def inspect_book_assets(extracted_assets):
    records=[]
    for a in extracted_assets:
        records.append(make_record(a["asset_id"],a))
    return records

def select_visual_asset(records, required_class=None):
    candidates=[r for r in records if required_class is None or r["class"]==required_class]
    candidates.sort(key=lambda x:x["quality_score"],reverse=True)
    if candidates and candidates[0]["quality_score"]>=.75:
        return {"strategy":"REUSE_SOURCE","asset":candidates[0]}
    if candidates:
        return {"strategy":"RECONSTRUCT","asset":candidates[0]}
    return {"strategy":"GENERATE_FALLBACK","asset":None}
