def ingestion_policy():
    return {
      "source_identity_is_preserved":True,
      "document_structure_is_preserved":True,
      "reading_order_is_explicit":True,
      "equations_tables_and_figures_are_first_class":True,
      "semantic_chunks_keep_source_refs":True,
      "citations_are_machine_readable":True,
      "concept_mappings_keep_provenance":True,
      "ocr_or_extraction_uncertainty_must_not_be_hidden":True,
      "domain_reasoning_happens_after_ingestion":True
    }
