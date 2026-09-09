def rerank(results, query_terms=None):
    # Contract hook: production implementations may use a cross-encoder/LLM.
    return sorted(results,key=lambda x:(-x["score"],x["chunk"]["chunk_id"]))

def hybrid_retrieve(query, lexical_results, semantic_results, alpha=0.5):
    by_id={}
    for r in lexical_results:
        by_id.setdefault(r["chunk"]["chunk_id"],{"chunk":r["chunk"]})["lexical"]=r["score"]
    for r in semantic_results:
        by_id.setdefault(r["chunk"]["chunk_id"],{"chunk":r["chunk"]})["semantic"]=r["score"]
    out=[]
    for item in by_id.values():
        item["score"]=alpha*item.get("lexical",0)+(1-alpha)*item.get("semantic",0)
        out.append(item)
    return sorted(out,key=lambda x:(-x["score"],x["chunk"]["chunk_id"]))
