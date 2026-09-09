def animation_behavior(animation_id,target,behavior,
                       trigger=None,params=None):
    return {"animation_id":animation_id,"target":target,
            "behavior":behavior,"trigger":trigger,"params":params or {}}

def behavior_types():
    return ["APPEAR","DISAPPEAR","MOVE","ROTATE","SCALE","DRAW",
            "TRANSFORM","MORPH","HIGHLIGHT","TRACE","REVEAL",
            "PULSE","FLOW","FADE"]
