def enriched_node(expansion, support_class, confidence):
    return {
      "id":expansion["expansion_id"],
      "type":expansion["kind"],
      "title":expansion["title"],
      "source_claim_ids":expansion["source_claim_ids"],
      "evidence_ids":expansion["evidence_ids"],
      "support_class":support_class,
      "confidence":confidence,
      "status":"ENRICHED"
    }

def link(node_a,node_b,relation):
    return {"from":node_a,"to":node_b,"relation":relation}
