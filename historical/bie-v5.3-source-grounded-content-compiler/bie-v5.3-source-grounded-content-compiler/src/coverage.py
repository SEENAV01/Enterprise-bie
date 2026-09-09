def coverage(claims):
    required=[c for c in claims if c.get("required",True)]
    grounded=sum(bool(c.get("evidence_ids")) for c in required
                 if c.get("claim_type")=="SOURCE_FACT")
    total=sum(1 for c in required if c.get("claim_type")=="SOURCE_FACT")
    return {
      "source_fact_grounding_ratio": grounded/total if total else 1.0,
      "required_claims":len(required)
    }
