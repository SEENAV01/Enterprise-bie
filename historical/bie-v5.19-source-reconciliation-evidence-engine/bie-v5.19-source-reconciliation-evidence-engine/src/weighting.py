DEFAULT_WEIGHTS={
 "PRIMARY_SOURCE":1.0,"SECONDARY_SOURCE":0.8,"TERTIARY_SOURCE":0.6,
 "TEXTBOOK":0.9,"PEER_REVIEWED":1.0,"OFFICIAL":1.0
}
def evidence_weight(source_type,quality=1.0):
    return DEFAULT_WEIGHTS.get(source_type,0.5)*quality

def aggregate_support(evidence_items):
    support=sum((e.get("weight") or 0) for e in evidence_items
                if e.get("support")=="SUPPORTS")
    oppose=sum((e.get("weight") or 0) for e in evidence_items
               if e.get("support") in ("CONTRADICTS","REFUTES"))
    if support==oppose: return {"direction":"UNRESOLVED","score":0}
    return {"direction":"SUPPORTS" if support>oppose else "CONTRADICTS",
            "score":abs(support-oppose)}
