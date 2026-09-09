def ingestion_policy():
    return {
      "source_documents_are_preserved":True,
      "page_provenance_is_required":True,
      "region_provenance_is_supported":True,
      "reading_order_is_explicit":True,
      "scanned_documents_can_use_ocr":True,
      "ocr_confidence_is_tracked":True,
      "tables_are_structured":True,
      "figures_are_preserved":True,
      "formulas_are_preserved":True,
      "low_confidence_extraction_requires_review":True,
      "canonical_source_is_renderer_independent":True,
      "domain_agnostic":True
    }
