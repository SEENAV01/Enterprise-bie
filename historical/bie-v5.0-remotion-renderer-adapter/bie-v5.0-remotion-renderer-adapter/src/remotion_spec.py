from component_registry import resolve_component
from frame_mapper import map_scene

def component_spec(obj):
    return {
      "component":resolve_component(obj["kind"]),
      "props":{
        "content":obj.get("content",""),
        "style":obj.get("style",{}),
        "bindings":obj.get("bindings",{})
      },
      "lifecycle":obj.get("lifecycle",[]),
      "z":obj.get("z",0)
    }

def build_remotion_spec(visual):
    fps=visual["fps"]
    scenes=[]
    for scene in visual.get("scenes",[]):
        mapped=map_scene(scene,fps)
        mapped["components"]=[component_spec(o) for o in scene.get("objects",[])]
        scenes.append(mapped)
    return {
      "schema_version":"5.0",
      "renderer":"REMOTION",
      "fps":fps,
      "duration_s":visual["duration_s"],
      "duration_frames":round(visual["duration_s"]*fps),
      "scenes":scenes
    }
