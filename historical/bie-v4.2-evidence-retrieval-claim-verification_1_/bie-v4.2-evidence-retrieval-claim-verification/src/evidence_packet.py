def evidence_record(claim_id,source_id,passage,support="SUPPORTS",
                    locator=None,quote=None):
    return {"claim_id":claim_id,"source_id":source_id,
            "passage":passage,"relation":support,
            "locator":locator,"quote":quote}

def build_packet(item, claims, evidences):
    return {
      "knowledge_id":item["id"],
      "claims":claims,
      "evidence":evidences,
      "status":"UNVERIFIED"
    }
