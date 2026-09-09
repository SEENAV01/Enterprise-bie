from components import validate_component

def compile_ir(ir,renderer_targets=None):
    errors=[]
    for lesson in ir.get("lessons",[]):
        for scene in lesson.get("scenes",[]):
            for c in scene.get("components",[]):
                if not validate_component(c):
                    errors.append("INVALID_COMPONENT")
    return {"schema_version":"5.66","ir":ir,
            "renderer_targets":renderer_targets or ["GENERIC"],
            "quality_gate":{"valid":not errors,"errors":errors}}
