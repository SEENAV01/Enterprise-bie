def provenance(node_id, node_type, claim_ids=None, evidence_ids=None,
               parent_ids=None, transformation=None):
    return {
      "node_id":node_id,"node_type":node_type,
      "claim_ids":claim_ids or [],
      "evidence_ids":evidence_ids or [],
      "parent_ids":parent_ids or [],
      "transformation":transformation or {}
    }
