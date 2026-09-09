def integrity_policy():
    return {
      "claims_require_traceable_evidence":True,
      "unsupported_claims_require_review":True,
      "contradictions_are_release_blocking":True,
      "numeric_checks_are_explicit":True,
      "unit_checks_are_explicit":True,
      "cross_representation_consistency_is_checked":True,
      "provenance_is_preserved":True,
      "semantic_similarity_never_replaces_evidence":True,
      "integrity_checks_are_domain_agnostic":True
    }
