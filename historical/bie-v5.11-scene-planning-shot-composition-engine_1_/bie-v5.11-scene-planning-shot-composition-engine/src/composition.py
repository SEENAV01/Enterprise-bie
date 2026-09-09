def composition(composition_id, layout, focus=None,
                camera=None, staging=None):
    return {
      "composition_id":composition_id,
      "layout":layout,
      "focus":focus or [],
      "camera":camera or {},
      "staging":staging or {}
    }

def focus_hierarchy(primary, secondary=None, background=None):
    return {
      "primary":primary,
      "secondary":secondary or [],
      "background":background or []
    }
