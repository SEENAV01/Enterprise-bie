def asset_id(namespace,name,version="1"):
    safe=name.strip().lower().replace(" ","-")
    return f"{namespace}:{safe}:v{version}"

def dependency_id(source_id,target_id):
    return f"{source_id}__requires__{target_id}"
