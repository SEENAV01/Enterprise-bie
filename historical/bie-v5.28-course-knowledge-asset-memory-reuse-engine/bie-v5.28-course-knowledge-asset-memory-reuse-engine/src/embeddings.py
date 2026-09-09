def semantic_index_record(record_id,text,embedding_ref=None,
                         metadata=None):
    return {"record_id":record_id,"text":text,
            "embedding_ref":embedding_ref,"metadata":metadata or {}}

def similarity_score(query_embedding,record_embedding):
    # Placeholder for a vector-store adapter.
    return None
