def validate_build_environment(node_version=None, remotion_version=None):
    errors=[]
    if node_version is None: errors.append("NODE_VERSION_UNSET")
    if remotion_version is None: errors.append("REMOTION_VERSION_UNSET")
    return {"valid":not errors,"errors":errors}

def build_project(composition_source, project_dir):
    return {"project_dir":project_dir,"composition_source":composition_source,
            "status":"BUILD_REQUESTED"}
