def grounding_policy():
    return {
      "source_facts_require_evidence":True,
      "inferences_require_reasoning_notes":True,
      "enrichment_must_be_labeled":True,
      "unsupported_required_claims_block_export":True,
      "video_elements_must_trace_to_claims":True,
      "no_silent_source_replacement":True
    }
