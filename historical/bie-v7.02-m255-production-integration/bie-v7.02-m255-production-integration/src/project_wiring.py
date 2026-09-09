def wire_remotion_project(project_dir, composition_source, assets=None, audio=None):
    return {"project_dir":project_dir,"composition_source":composition_source,
            "assets":assets or [],"audio":audio or [],"status":"WIRED"}

def validate_project_wiring(wiring):
    errors=[]
    if not wiring.get("project_dir"): errors.append("PROJECT_DIR_MISSING")
    if not wiring.get("composition_source"): errors.append("COMPOSITION_SOURCE_MISSING")
    return {"valid":not errors,"errors":errors}
