def render_project(project_id,entrypoint,compositions=None,
                  assets=None,audio=None,metadata=None):
    return {"project_id":project_id,"entrypoint":entrypoint,
            "compositions":compositions or [],"assets":assets or [],
            "audio":audio or [],"metadata":metadata or {}}
