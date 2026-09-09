def retrieval_query(query_id,text,index_ref,
                    top_k=5,filters=None):
    return {"query_id":query_id,"text":text,
            "index":index_ref,"top_k":top_k,
            "filters":filters or {}}

def retrieval_hit(chunk_ref,score,rank):
    return {"chunk":chunk_ref,"score":score,"rank":rank}

def retrieval_evidence(query,hits):
    return {"query":query,"hits":hits}
