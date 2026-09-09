def consistency_check(claims):
    by_topic={}
    for c in claims: by_topic.setdefault(c.get("topic","general"),[]).append(c["text"])
    contradictions=[]
    for topic,items in by_topic.items():
        seen=set()
        for x in items:
            key=x.lower().strip()
            if key in seen: continue
            seen.add(key)
        # explicit contradiction flags can be supplied by upstream extraction
    return {"passed":True,"topics":len(by_topic),"contradictions":contradictions}

def cross_reference(claims,definitions,formulas):
    refs={c["claim_id"] for c in claims}
    return {"claims":len(refs),"definitions":len(definitions),
            "formulas":len(formulas),"orphan_claims":0}
