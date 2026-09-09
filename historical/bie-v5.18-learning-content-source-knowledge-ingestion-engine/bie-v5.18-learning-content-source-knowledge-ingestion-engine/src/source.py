def source_record(source_id,source_type,title,uri=None,metadata=None):
    return {"source_id":source_id,"source_type":source_type,"title":title,
            "uri":uri,"metadata":metadata or {}}
