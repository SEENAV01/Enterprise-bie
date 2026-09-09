def render_result(job_id, status, output_path=None,
                 duration_sec=None, frame_count=None,
                 file_size_bytes=None, checksum=None, errors=None):
    return {"job_id":job_id,"status":status,"output_path":output_path,
            "duration_sec":duration_sec,"frame_count":frame_count,
            "file_size_bytes":file_size_bytes,"checksum":checksum,
            "errors":errors or []}

def successful(r):
    return r["status"]=="SUCCEEDED" and bool(r.get("output_path"))
