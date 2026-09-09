def verify_claim(claim, evidence, minimum_sources=1):
    supporting=[e for e in evidence if e["claim_id"]==claim["claim_id"]
                and e["relation"]=="SUPPORTS"]
    contradicting=[e for e in evidence if e["claim_id"]==claim["claim_id"]
                   and e["relation"]=="CONTRADICTS"]
    if contradicting:
        status="CONFLICT"
    elif len(supporting)>=minimum_sources:
        status="VERIFIED"
    else:
        status="INSUFFICIENT_EVIDENCE"
    return {
      "claim_id":claim["claim_id"],
      "status":status,
      "support_count":len(supporting),
      "contradiction_count":len(contradicting)
    }

def verify_packet(packet, minimum_sources=1):
    results=[verify_claim(c,packet["evidence"],minimum_sources)
             for c in packet["claims"]]
    if any(r["status"]=="CONFLICT" for r in results):
        packet["status"]="CONFLICT"
    elif all(r["status"]=="VERIFIED" for r in results):
        packet["status"]="VERIFIED"
    else:
        packet["status"]="UNVERIFIED"
    packet["verification"]=results
    return packet
