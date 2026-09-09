def semantic_chunk(chunk_id,text,source_ref,section_id=None,
                   element_refs=None,chunk_type="TEXT"):
    return {"chunk_id":chunk_id,"text":text,"source_ref":source_ref,
            "section_id":section_id,"element_refs":element_refs or [],
            "chunk_type":chunk_type}
def chunk_document(blocks,max_chars=1800):
    chunks=[]; buf=""; refs=[]
    for b in blocks:
        t=b.get("text","").strip()
        if not t: continue
        if buf and len(buf)+len(t)+1>max_chars:
            chunks.append({"text":buf,"element_refs":refs})
            buf=""; refs=[]
        buf=(buf+" "+t).strip(); refs.append(b.get("element_id"))
    if buf: chunks.append({"text":buf,"element_refs":refs})
    return chunks
