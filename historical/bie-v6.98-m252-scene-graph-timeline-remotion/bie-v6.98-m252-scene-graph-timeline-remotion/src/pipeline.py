from scene_graph import create_scene_graph,add_node,add_edge,validate_graph
from timeline import resolve_timeline,dependency_order
from layers import plan_layers,validate_layers
from camera import camera_plan,validate_camera
from remotion_contract import build_remotion_scene,validate_remotion_scene

def build_scene_graph_runtime():
    g=create_scene_graph("scene-c-field")
    for n in [
      {"id":"diagram","type":"diagram"},{"id":"equation","type":"equation"},
      {"id":"annotation","type":"annotation"},{"id":"narration","type":"narration"}]:
        add_node(g,n)
    add_edge(g,"diagram","equation","SUPPORTS")
    add_edge(g,"equation","annotation","PRECEDES")
    add_edge(g,"annotation","narration","SUPPORTS")
    graph_check=validate_graph(g)

    events=[
      {"id":"diagram-in","start_frame":0,"end_frame":30,"exclusive":False},
      {"id":"equation-in","start_frame":30,"end_frame":60,"exclusive":False},
      {"id":"annotation-in","start_frame":60,"end_frame":90,"exclusive":True},
      {"id":"narration","start_frame":0,"end_frame":90,"exclusive":False}]
    timeline=resolve_timeline(events)
    deps={"equation-in":["diagram-in"],"annotation-in":["equation-in"],"narration":["diagram-in"]}
    dep=dependency_order(events,deps)

    layers=plan_layers([
      {"id":"bg","type":"background"},{"id":"diagram","type":"diagram"},
      {"id":"equation","type":"equation"},{"id":"annotation","type":"annotation"}])
    layer_check=validate_layers(layers)

    camera=camera_plan([
      {"shot_id":"wide","start_frame":0,"end_frame":60,"focus":"diagram","scale":1.0},
      {"shot_id":"equation","start_frame":60,"end_frame":120,"focus":"equation","scale":1.15,"transition":"SMOOTH"}])
    camera_check=validate_camera(camera)

    scene=build_remotion_scene("scene-c-field",120,30,layers,camera,events)
    render_check=validate_remotion_scene(scene)
    valid=all([graph_check["valid"],timeline["valid"],dep["valid"],layer_check["valid"],
               camera_check["valid"],render_check["valid"]])
    return {"schema_version":"6.98","scene_graph":g,"graph_validation":graph_check,
            "timeline":timeline,"dependency_order":dep,"layers":layers,
            "layer_validation":layer_check,"camera":camera,"camera_validation":camera_check,
            "remotion_scene":scene,"render_validation":render_check,
            "render_contract_gate":{"valid":valid,"errors":[] if valid else ["SCENE_CONTRACT_FAILURE"]}}
