def ranking(method="BM25",
            field_weights=None):
    if method not in {"BM25","BOOLEAN","CUSTOM"}:
        raise ValueError("INVALID_RANKING_METHOD")
    return {"method":method,
            "field_weights":field_weights or {}}

def score(record,query_terms):
    return sum(1 for term in query_terms
               if term in str(record).lower())
