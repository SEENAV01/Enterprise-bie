def infer_dependency(candidate):
    return {
      "source":candidate["source"],
      "target":candidate["target"],
      "type":candidate.get("type","PREREQUISITE"),
      "scope":"MODEL_INFERRED",
      "confidence":candidate.get("confidence",.50),
      "evidence_ids":candidate.get("evidence_ids",[]),
      "reason":candidate.get("reason","Model-inferred prerequisite relationship"),
      "requires_validation":True
    }

def validate_dependency(d):
    return bool(d.get("source") and d.get("target") and d.get("type") and d.get("scope"))
