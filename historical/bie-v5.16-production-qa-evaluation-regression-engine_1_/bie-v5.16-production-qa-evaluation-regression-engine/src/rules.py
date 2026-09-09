RULES={
 "structure":"Scene IDs, durations and required fields must be valid.",
 "timing":"Animation keyframes must be monotonic and frame-addressable.",
 "sync":"Captions and timeline objects must have valid ranges.",
 "assets":"Referenced assets must resolve before rendering.",
 "continuity":"Global style and registered visual identities must not drift.",
 "render":"Rendered outputs must match expected dimensions, FPS and duration."
}
def enabled_rules():
    return list(RULES)
