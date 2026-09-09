from primitives import PRIMITIVES,ANIMATIONS

def visual_object(object_id,kind,content,region_id="main",
                  z=0,style=None,bindings=None):
    if kind not in PRIMITIVES: raise ValueError("UNKNOWN_PRIMITIVE")
    return {
      "id":object_id,"kind":kind,"content":content,
      "region_id":region_id,"z":z,"style":style or {},
      "bindings":bindings or {}, "lifecycle":[]
    }

def lifecycle(object_id,animation,at_event,duration_s=0.4,props=None):
    if animation not in ANIMATIONS: raise ValueError("UNKNOWN_ANIMATION")
    return {"object_id":object_id,"animation":animation,
            "at_event":at_event,"duration_s":duration_s,
            "props":props or {}}
