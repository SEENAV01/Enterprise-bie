def render_job(render_id,composition_id,
              output_format,settings=None):
    return {"render_id":render_id,
            "composition_id":composition_id,
            "output_format":output_format,
            "settings":settings or {},
            "status":"QUEUED"}

def render_result(render_id,output_ref,content_hash,
                  duration=None,size_bytes=None):
    return {"render_id":render_id,
            "output":output_ref,"content_hash":content_hash,
            "duration":duration,"size_bytes":size_bytes,
            "status":"COMPLETE"}
