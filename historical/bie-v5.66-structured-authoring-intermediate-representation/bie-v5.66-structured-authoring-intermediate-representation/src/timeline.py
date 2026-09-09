def timeline(items=None,duration=None,fps=30):
    return {"items":items or [],"duration":duration,"fps":fps}

def timeline_item(item_id,start,duration,component_ref,
                  animation=None):
    return {"item_id":item_id,"start":start,
            "duration":duration,
            "component_ref":component_ref,
            "animation":animation or {}}
