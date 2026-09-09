from renderer_ir import scene_ir,add_layer,add_animation
from remotion_adapter import remotion_composition
from validation import validate_ir

def compile_shot_plan(shots,components=None,renderer="remotion"):
    components=components or []; scenes=[]; errors=[]
    for sh in shots:
        ir=scene_ir(sh["shot_id"])
        t=sh.get("timing",{}); start=t.get("start_frame"); end=t.get("end_frame")
        ir["duration_in_frames"]=max(0,end-start) if start is not None and end is not None else 0
        for c in components:
            if c.get("shot_id")==sh["shot_id"]:
                add_layer(ir,c["layer_id"],c["component"],c.get("props",{}),c.get("z_index",0))
                for a in c.get("animations",[]):
                    add_animation(ir,a["target_id"],a["property"],a["keyframes"],a.get("easing","linear"))
        q=validate_ir(ir); errors.extend(q["errors"]); scenes.append(ir)
    out={"schema_version":"5.12","renderer":renderer,"scenes":scenes,
         "quality_gate":{"valid":not errors,"errors":errors}}
    if renderer=="remotion": out["remotion"]=[remotion_composition(s) for s in scenes]
    return out
