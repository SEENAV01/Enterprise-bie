def perceptual_similarity(reference, candidate):
    ref=set(reference.get("features",[]))
    cand=set(candidate.get("features",[]))
    union=ref|cand
    similarity=len(ref&cand)/len(union) if union else 1.0
    return {"similarity":similarity,
            "matched_features":sorted(ref&cand),
            "missing_features":sorted(ref-cand)}

def above_threshold(result,threshold=0.8):
    return result["similarity"]>=threshold
