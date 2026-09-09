def detect_candidate_conflicts(evidence):
    # Lightweight signal: same normalized topic/label with different source pages.
    groups={}
    for e in evidence:
        key=(e.get("content","").lower().replace(" ","")[:80])
        groups.setdefault(key,[]).append(e)
    conflicts=[]
    for key,items in groups.items():
        pages=sorted(set(x.get("page_number") for x in items))
        if len(pages)>1:
            conflicts.append({"signature":key,"pages":pages,"status":"REVIEW"})
    return conflicts
