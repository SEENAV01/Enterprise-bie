def ingest_document(document_id, text, metadata=None):
    return {"document_id":document_id,"text":text,"metadata":metadata or {},
            "status":"INGESTED"}

def document_version(document_id, version, source_uri, updated_at):
    return {"document_id":document_id,"version":version,"source_uri":source_uri,
            "updated_at":updated_at}
