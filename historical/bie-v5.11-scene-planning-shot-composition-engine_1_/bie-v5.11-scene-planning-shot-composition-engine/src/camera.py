CAMERA_MOVES=[
"STATIC","PUSH_IN","PULL_OUT","PAN","TILT","ORBIT",
"TRACK","DOLLY","CUT","ZOOM"
]

def camera_plan(move="STATIC", start=None, end=None,
                target=None, easing="NARRATION_ALIGNED"):
    if move not in CAMERA_MOVES: raise ValueError("UNKNOWN_CAMERA_MOVE")
    return {
      "move":move,"start":start,"end":end,
      "target":target,"easing":easing
    }
