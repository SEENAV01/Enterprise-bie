from ingestion import ingest_document,document_version
from chunking import chunk_document
from indexing import index_documents
from retrieval import retrieve
from rerank import rerank,hybrid_retrieve
from citations import map_citations
from freshness import freshness_status,source_allowed

def build_m276_runtime():
    doc=ingest_document("book-001","Electric charge is a property of matter. "
                        "Like charges repel and unlike charges attract.",
                        {"title":"Physics Source"})
    ver=document_version("book-001",2,"library://book-001","2026-08-31")
    chunks=chunk_document(doc,120,20)
    index=index_documents(chunks)
    lexical=retrieve("electric charge repel",index,3)
    semantic=[{"chunk":chunks[0],"score":0.95}]
    hybrid=hybrid_retrieve("electric charge",lexical,semantic,0.5)
    ranked=rerank(hybrid)
    versions={"book-001":ver["version"]}
    citations=map_citations(ranked,versions)
    freshness=freshness_status(2,2)
    allowed=source_allowed(freshness)
    return {"schema_version":"7.23","document":doc,"version":ver,"chunks":chunks,
            "index_size":len(index),"retrieval":{"lexical":lexical,"hybrid":hybrid,"reranked":ranked},
            "citations":citations,"freshness":{"status":freshness,"allowed":allowed},
            "knowledge_grounding_gate":{"valid":doc["status"]=="INGESTED" and
                                        len(chunks)>0 and len(index)>0 and
                                        len(citations)>0 and allowed,"errors":[]}}
