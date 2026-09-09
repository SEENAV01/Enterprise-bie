def retrieve(evidence_items,query,limit=10):
    terms=set(query.lower().split())
    scored=[]
    for e in evidence_items:
        text=(e.get("excerpt_ref","")+" "+" ".join(e.get("claim_ids",[]))).lower()
        score=sum(t in text for t in terms)
        scored.append((score,e))
    return [e for score,e in sorted(scored,key=lambda x:x[0],reverse=True)[:limit] if score>0]
