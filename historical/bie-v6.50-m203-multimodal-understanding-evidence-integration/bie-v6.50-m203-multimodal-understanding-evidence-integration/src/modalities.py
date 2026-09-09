SUPPORTED_MODALITIES = {
    "TEXT", "IMAGE", "TABLE", "EQUATION", "LAYOUT"
}

def modality_record(record_id, source_id, modality, content_ref,
                    page=None, bbox=None, confidence=1.0):
    if modality not in SUPPORTED_MODALITIES:
        raise ValueError("UNSUPPORTED_MODALITY")
    return {
        "record_id": record_id, "source_id": source_id,
        "modality": modality, "content_ref": content_ref,
        "page": page, "bbox": bbox, "confidence": confidence
    }

def valid(record):
    return (
        record["modality"] in SUPPORTED_MODALITIES
        and bool(record["source_id"])
        and bool(record["content_ref"])
    )
