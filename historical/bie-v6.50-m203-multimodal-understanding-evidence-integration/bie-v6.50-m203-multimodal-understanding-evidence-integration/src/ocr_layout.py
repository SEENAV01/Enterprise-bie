def extraction(extraction_id, source_id, page,
               text, ocr=False, layout_aware=False, confidence=1.0):
    return {
        "extraction_id": extraction_id, "source_id": source_id,
        "page": page, "text": text, "ocr": ocr,
        "layout_aware": layout_aware, "confidence": confidence
    }

def usable(record):
    return bool(record["text"]) and record["confidence"] >= 0.0
