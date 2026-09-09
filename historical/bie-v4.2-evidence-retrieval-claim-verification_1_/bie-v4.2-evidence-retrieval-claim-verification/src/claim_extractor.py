def extract_claims(item):
    # Retrieval output supplies evidence passages; this module normalizes claim records.
    claims=item.get("claims") or [{
      "claim_id":item["id"]+"_claim_1",
      "text":item.get("content",""),
      "importance":"HIGH"
    }]
    return claims
