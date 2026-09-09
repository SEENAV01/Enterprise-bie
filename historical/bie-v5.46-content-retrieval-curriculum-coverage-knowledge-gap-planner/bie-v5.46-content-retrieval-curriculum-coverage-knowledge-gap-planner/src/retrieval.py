def retrieval_query(query_id,objective_refs=None,concept_refs=None,
                   terms=None,filters=None,top_k=10):
    return {"query_id":query_id,"objective_refs":objective_refs or [],
            "concept_refs":concept_refs or [],"terms":terms or [],
            "filters":filters or {},"top_k":top_k}

def rank_fragment(fragment,signals=None,weights=None):
    signals=signals or {}
    weights=weights or {}
    return sum(v*weights.get(k,1.0) for k,v in signals.items()
               if isinstance(v,(int,float)))
