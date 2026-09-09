def citation_for(chunk, source_version):
    return {"chunk_id":chunk["chunk_id"],"document_id":chunk["document_id"],
            "version":source_version,"locator":chunk["index"]}

def map_citations(results, versions):
    return [citation_for(r["chunk"],versions[r["chunk"]["document_id"]]) for r in results
            if r["chunk"]["document_id"] in versions]
