def course_manifest(course_id,title,version=None,lessons=None,
                   global_assets=None,style_token=None):
    return {"course_id":course_id,"title":title,"version":version,
            "lessons":lessons or [],"global_assets":global_assets or [],
            "style_token":style_token}
