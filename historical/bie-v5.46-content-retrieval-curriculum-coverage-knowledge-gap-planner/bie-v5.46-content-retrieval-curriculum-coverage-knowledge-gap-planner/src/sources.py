def source_document(source_id,source_type,title,uri=None,
                    metadata=None):
    return {"source_id":source_id,"source_type":source_type,
            "title":title,"uri":uri,"metadata":metadata or {}}

def source_types():
    return ["BOOK","PDF","ARTICLE","VIDEO","COURSE","NOTES",
            "TRANSCRIPT","WEB","DATASET","OTHER"]
