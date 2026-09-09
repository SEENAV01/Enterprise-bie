from object_spec import visual_object,lifecycle
from layout import default_layout

def build_scene(scene,visual_events,knowledge=None):
    objects=[]
    lifecycles=[]
    for i,e in enumerate(visual_events):
        kind=e.get("kind","TEXT")
        obj=visual_object(
          f'{scene["scene_id"]}_obj_{i}',kind,e.get("content",""),
          e.get("region_id","main"),e.get("z",0),e.get("style"),
          e.get("bindings"))
        objects.append(obj)
        lifecycles.append(lifecycle(
          obj["id"],e.get("animation","APPEAR"),
          e.get("event_id"),e.get("animation_duration_s",0.4),
          e.get("animation_props")))
    return {
      "scene_id":scene["scene_id"],
      "start_s":scene["start_s"],"end_s":scene["end_s"],
      "layout":scene.get("layout",default_layout()),
      "objects":objects,"lifecycles":lifecycles,
      "knowledge_ids":scene.get("knowledge_ids",[]),
      "accessibility":{"captions_required":True,"contrast_check_required":True}
    }
