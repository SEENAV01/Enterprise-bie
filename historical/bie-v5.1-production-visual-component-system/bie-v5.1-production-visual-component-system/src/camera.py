def camera_event(kind, target=None, duration_s=0.5, easing="easeInOut"):
    return {
      "type":"CAMERA",
      "kind":kind,
      "target":target,
      "duration_s":duration_s,
      "easing":easing
    }
