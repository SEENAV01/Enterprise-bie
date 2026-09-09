def build_context(results, evidence, window=1):
    pages=sorted(set(x.get("page_number") for x in results if x.get("page_number") is not None))
    selected=[]
    for e in evidence:
        p=e.get("page_number")
        if p is not None and any(abs(p-x)<=window for x in pages):
            selected.append(e)
    selected.sort(key=lambda x:(x.get("page_number",0),x.get("evidence_id","")))
    return selected
