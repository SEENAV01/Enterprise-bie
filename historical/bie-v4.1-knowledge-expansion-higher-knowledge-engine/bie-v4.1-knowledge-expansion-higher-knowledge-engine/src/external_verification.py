def build_verification_request(item):
    return {
      "knowledge_id":item["id"],
      "query":item["title"]+" "+item["content"],
      "requirements":[
        "independent_authoritative_source",
        "date_or_version_when_relevant",
        "claim_level_provenance"
      ],
      "status":"PENDING_EXTERNAL_VERIFICATION"
    }

def accept_external_evidence(item, sources):
    # Sources are supplied by a retrieval layer; this module only records the result.
    if not sources:
        item["confidence"]="UNVERIFIED"
        item["allowed_for_teaching"]=False
        return item
    item["confidence"]="VERIFIED"
    item["allowed_for_teaching"]=True
    return item
