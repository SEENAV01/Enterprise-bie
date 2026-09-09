SUPPORTED_MODALITIES = {"VISUAL","AUDIO","TEXT","TIMING","CAPTION","MULTIMODAL"}

def modality_score(modality, score, confidence=1.0, evidence_refs=None, notes=None):
    if modality not in SUPPORTED_MODALITIES:
        raise ValueError("UNSUPPORTED_MODALITY")
    if not 0 <= score <= 1:
        raise ValueError("INVALID_SCORE")
    return {"modality":modality,"score":score,"confidence":confidence,
            "evidence_refs":evidence_refs or [],"notes":notes}

def valid(x):
    return x["modality"] in SUPPORTED_MODALITIES and 0 <= x["score"] <= 1
