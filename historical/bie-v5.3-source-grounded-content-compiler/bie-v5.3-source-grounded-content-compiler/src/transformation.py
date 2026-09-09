def transformation(kind,description,parent_claim_ids=None):
    return {
      "kind":kind,
      "description":description,
      "parent_claim_ids":parent_claim_ids or []
    }

def allowed_transformations():
    return [
      "PARAPHRASE","SUMMARIZE","SEQUENCE","DERIVE",
      "EXPLAIN","EXEMPLIFY","GENERALIZE","ENRICH"
    ]
