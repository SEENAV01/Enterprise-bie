def source(source_id,title,uri,source_type="REFERENCE",
           publisher=None,version=None):
    return {"source_id":source_id,"title":title,"uri":uri,
            "source_type":source_type,"publisher":publisher,"version":version}
def valid_source(s):
    return bool(s.get("source_id") and s.get("title") and s.get("uri"))
