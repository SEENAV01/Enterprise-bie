def ranking_profile(name,
                    algorithm="BM25",
                    fields=None,
                    weights=None):
    if algorithm not in {"BM25","SCORE","NONE"}:
        raise ValueError("INVALID_RANKING_ALGORITHM")
    return {"name":name,
            "algorithm":algorithm,
            "fields":fields or [],
            "weights":weights or {}}

def score(record,terms):
    text=" ".join(str(v) for v in record.values()).lower()
    return sum(1 for term in terms
               if term.lower() in text)
