def timeline_item(item_id,kind,duration=None,start=None,end=None,
                 beat_ref=None,scene_ref=None):
    return {"item_id":item_id,"kind":kind,"duration":duration,
            "start":start,"end":end,"beat_ref":beat_ref,
            "scene_ref":scene_ref}

def derive_duration(item,signals=None):
    signals=signals or {}
    if item.get("duration") is not None:
        return item["duration"]
    return signals.get(item.get("kind"),None)
