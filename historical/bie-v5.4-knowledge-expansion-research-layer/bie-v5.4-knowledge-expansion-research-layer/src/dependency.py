def prerequisite_gap(concept, known_concepts, candidates):
    known=set(known_concepts)
    return [
      c for c in candidates
      if c.get("concept") not in known and
         concept in c.get("supports",[])
    ]

def higher_order_candidates(claim):
    return claim.get("candidate_connections",[])
