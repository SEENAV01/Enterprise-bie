from math_renderer import equation_plan
from diagram_reconstructor import reconstruct_diagram,diagram_actions
from chart_table import chart_plan,table_plan
from media_compositor import media_layer,compose
from camera import camera_plan

def build(scene):
    visual=scene.get("visual",{})
    vtype=visual.get("type","mixed")
    plan={"scene_id":scene["scene_id"],"layers":[],"actions":[]}

    if vtype=="equation":
        for eq in scene.get("equations",[]):
            plan["layers"].append({"kind":"equation","spec":equation_plan(eq)})
    elif vtype=="diagram":
        d=reconstruct_diagram(
            visual.get("assets",["unknown"])[0],
            visual.get("instructions",""),
            visual.get("labels",[]),
            visual.get("relationships",[])
        )
        plan["layers"].append({"kind":"diagram","spec":d})
        plan["actions"] += diagram_actions(d)
    elif vtype=="chart":
        plan["layers"].append({"kind":"chart","spec":chart_plan("chart",visual.get("data_ref",""))})
    elif vtype=="table":
        plan["layers"].append({"kind":"table","spec":table_plan(visual.get("data_ref",""),visual.get("rows",[]))})
    elif vtype in {"real_world","video","image"}:
        for ref in visual.get("assets",[]):
            plan["layers"].append({"kind":"media","spec":media_layer(ref,vtype)})
    else:
        plan["layers"].append({"kind":"text","spec":{"text":scene.get("on_screen_text",[])}})

    plan["camera"]=camera_plan(scene.get("camera",{}).get("mode","static"))
    plan["sync_mode"]="AUDIO_MARKER_DRIVEN"
    return plan
