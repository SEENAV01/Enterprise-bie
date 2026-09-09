def make_animation_events(scene):
    typ=scene["scene_type"]
    events=[]
    if typ=="DEFINITION":
        events=[{"event":"REVEAL_TERM"},{"event":"REVEAL_DEFINITION"},{"event":"HIGHLIGHT_KEY_PHRASE"}]
    elif typ=="PROCESS":
        events=[{"event":"INTRODUCE_SYSTEM"},{"event":"ACTIVATE_STEP","step":"SEQUENTIAL"},{"event":"SHOW_RELATIONSHIP"}]
    elif typ=="DERIVATION":
        events=[{"event":"SHOW_INITIAL_EQUATION"},{"event":"TRANSFORM_STEP","step":"SEQUENTIAL"},{"event":"EMPHASIZE_RESULT"}]
    elif typ=="DIAGRAM":
        events=[{"event":"BUILD_DIAGRAM"},{"event":"LABEL_ELEMENTS"},{"event":"HIGHLIGHT_RELATIONSHIP"}]
    elif typ=="WORKED_EXAMPLE":
        events=[{"event":"SHOW_PROBLEM"},{"event":"REVEAL_GIVEN"},{"event":"SOLVE_STEPWISE"},{"event":"REVEAL_ANSWER"}]
    elif typ=="QUESTION":
        events=[{"event":"SHOW_QUESTION"},{"event":"WAIT_FOR_RESPONSE"},{"event":"REVEAL_EXPLANATION"}]
    else:
        events=[{"event":"ENTER"},{"event":"EMPHASIZE_CONTENT"},{"event":"EXIT"}]
    scene["animation_events"]=events
    return scene
