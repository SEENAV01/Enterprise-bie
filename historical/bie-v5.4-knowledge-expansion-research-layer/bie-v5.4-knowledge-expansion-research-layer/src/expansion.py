EXPANSION_TYPES=[
"PREREQUISITE","DEEPER_CONCEPT","HIGHER_ORDER","APPLICATION",
"CROSS_DOMAIN","COUNTEREXAMPLE","LIMITATION","MODERN_CONTEXT"
]

def expansion(expansion_id, source_claim_ids, kind, title, rationale,
              evidence_ids=None, confidence=0.0):
    if kind not in EXPANSION_TYPES: raise ValueError("UNKNOWN_EXPANSION_TYPE")
    return {
      "expansion_id":expansion_id,
      "source_claim_ids":source_claim_ids,
      "kind":kind,
      "title":title,
      "rationale":rationale,
      "evidence_ids":evidence_ids or [],
      "confidence":confidence,
      "status":"REVIEW_REQUIRED"
    }
