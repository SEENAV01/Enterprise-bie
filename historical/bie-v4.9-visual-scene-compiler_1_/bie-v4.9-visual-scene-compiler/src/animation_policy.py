def choose_animation(event_type,importance="SUPPORTING"):
    mapping={
      "EQUATION":"WRITE",
      "HIGHLIGHT":"HIGHLIGHT",
      "PROCESS":"TRACE",
      "CAUSE":"MOVE",
      "APPLICATION":"TRANSFORM",
      "COMPARE":"MORPH",
      "DEFINITION":"APPEAR"
    }
    return mapping.get(event_type,"APPEAR")

def motion_limits():
    return {
      "avoid_decorative_motion":True,
      "motion_must_support_meaning":True,
      "simultaneous_complex_animations_limit":3
    }
