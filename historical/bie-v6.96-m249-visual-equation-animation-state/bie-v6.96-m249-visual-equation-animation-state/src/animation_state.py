def create_animation_state(scene_id,diagram_state=None,equation_state=None):
    return {"scene_id":scene_id,"frame":0,"phase":"IDLE",
            "diagram":diagram_state or {},"equation":equation_state or {}}

def transition(state,phase,frame):
    allowed={"IDLE":{"INTRO","ACTIVE"},"INTRO":{"ACTIVE"},
             "ACTIVE":{"HIGHLIGHT","TRANSFORM","COMPLETE"},
             "HIGHLIGHT":{"TRANSFORM","ACTIVE"},
             "TRANSFORM":{"ACTIVE","COMPLETE"},"COMPLETE":{}}
    if phase not in allowed.get(state["phase"],set()):
        raise ValueError("INVALID_ANIMATION_TRANSITION")
    state["phase"]=phase; state["frame"]=frame
    return state

def sync_state(state,diagram=None,equation=None):
    if diagram is not None: state["diagram"]=diagram
    if equation is not None: state["equation"]=equation
    return state
