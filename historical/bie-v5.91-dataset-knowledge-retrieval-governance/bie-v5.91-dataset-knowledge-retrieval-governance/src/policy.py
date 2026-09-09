def knowledge_policy():
    return {
      "datasets_are_versioned":True,
      "documents_have_stable_identity":True,
      "chunks_have_stable_identity":True,
      "ingestion_runs_are_versioned":True,
      "source_provenance_is_recorded":True,
      "indexes_are_versioned":True,
      "embedding_versions_are_recorded":True,
      "retrieval_evidence_is_explicit":True,
      "freshness_is_supported":True,
      "access_constraints_are_supported":True,
      "knowledge_snapshots_are_supported":True,
      "stale_data_can_be_detected":True
    }
