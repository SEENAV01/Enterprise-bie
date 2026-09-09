def initial_state():
    return {"status":"PLANNED","chapters":{},"lessons":{},"scenes":{}}

def update_lesson(state, lesson_id, status, fingerprint=None):
    state["lessons"][lesson_id]={"status":status,"fingerprint":fingerprint}
    return state
