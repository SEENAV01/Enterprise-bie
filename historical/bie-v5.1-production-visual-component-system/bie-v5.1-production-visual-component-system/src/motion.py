MOTION={
"APPEAR":"opacity 0→1",
"FADE":"opacity 1→0",
"WRITE":"progressive mathematical reveal",
"DRAW":"path progressive reveal",
"TRACE":"follow semantic path",
"MOVE":"position interpolation",
"MORPH":"shape/state interpolation",
"HIGHLIGHT":"attention emphasis",
"TRANSFORM":"structured transformation"
}

def motion_spec(kind, start_frame, end_frame, easing="easeInOut", props=None):
    if kind not in MOTION: raise ValueError("UNKNOWN_MOTION")
    return {
      "kind":kind,"start_frame":start_frame,"end_frame":end_frame,
      "easing":easing,"props":props or {}
    }
