def teaching_decision(packet, knowledge_classification):
    if packet.get("status")=="VERIFIED":
        return {"allowed":True,"reason":"CLAIMS_VERIFIED"}
    if packet.get("status")=="CONFLICT":
        return {"allowed":False,"reason":"SOURCE_CONFLICT_REQUIRES_REVIEW"}
    return {"allowed":False,"reason":"INSUFFICIENT_VERIFICATION"}

def confidence(packet):
    if packet.get("status")=="VERIFIED": return "VERIFIED"
    if packet.get("status")=="CONFLICT": return "CONFLICTED"
    return "UNVERIFIED"
