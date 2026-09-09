from orchestrator import orchestrate
from validator import validate

def compile_scene(scene,active_ids=None):
    r=orchestrate(scene,active_ids)
    r["validation"]=validate(r)
    r["schema_version"]="5.2"
    return r
