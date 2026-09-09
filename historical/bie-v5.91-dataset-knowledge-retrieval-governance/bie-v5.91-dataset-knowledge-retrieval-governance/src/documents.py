def document(doc_id,content_hash,source_uri=None,
             version=None,authority=None,metadata=None):
    return {"doc_id":doc_id,"content_hash":content_hash,
            "source_uri":source_uri,"version":version,
            "authority":authority,"metadata":metadata or {}}

def chunk(chunk_id,doc_id,chunk_hash,start,end,
          text_ref=None):
    return {"chunk_id":chunk_id,"doc_id":doc_id,
            "chunk_hash":chunk_hash,"start":start,"end":end,
            "text_ref":text_ref}
