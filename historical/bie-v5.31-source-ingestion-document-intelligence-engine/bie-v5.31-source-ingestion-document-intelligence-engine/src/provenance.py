def provenance(document_id,page_number,region_id=None,
                bbox=None,extraction_method=None,confidence=None):
    return {"document_id":document_id,"page_number":page_number,
            "region_id":region_id,"bbox":bbox,
            "extraction_method":extraction_method,
            "confidence":confidence}
