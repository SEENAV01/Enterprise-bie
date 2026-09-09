def weighted_score(items, weights=None):
    if not items:
        return 0.0
    if weights is None:
        weights = [1.0] * len(items)
    total = sum(weights)
    return sum(i["score"] * w for i,w in zip(items,weights)) / total if total else 0.0

def decision(score, pass_threshold=0.90, review_threshold=0.75):
    if score >= pass_threshold:
        return "PASS"
    if score >= review_threshold:
        return "REVIEW"
    return "FAIL"
