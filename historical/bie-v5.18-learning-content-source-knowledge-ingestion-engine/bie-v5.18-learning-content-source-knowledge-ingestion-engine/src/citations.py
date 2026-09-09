def citation(citation_id,source_id,locator,quote_ref=None):
    return {"citation_id":citation_id,"source_id":source_id,
            "locator":locator,"quote_ref":quote_ref}
def attach_citation(chunk,citation_ref):
    chunk["citation_refs"]=chunk.get("citation_refs",[])+[citation_ref]
    return chunk
