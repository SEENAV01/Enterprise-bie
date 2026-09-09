def deliverable_manifest(course_id,title,version,artifacts,
                        captions=None,accessibility=None):
    return {"course_id":course_id,"title":title,"version":version,
            "artifacts":artifacts,"captions":captions or [],
            "accessibility":accessibility or {},"status":"READY"}

def artifact_record(artifact_id,path,media_type,sha256=None,
                    duration_frames=None):
    return {"artifact_id":artifact_id,"path":path,"media_type":media_type,
            "sha256":sha256,"duration_frames":duration_frames}
