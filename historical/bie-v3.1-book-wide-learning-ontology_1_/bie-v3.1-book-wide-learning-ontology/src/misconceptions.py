def misconception_record(topic, misconception, evidence_ids=None):
    return {
      "topic":topic,
      "misconception":misconception,
      "correction_status":"UNVERIFIED",
      "evidence_ids":evidence_ids or [],
      "requires_grounded_check":True
    }
