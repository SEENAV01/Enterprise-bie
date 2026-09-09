def route_correction(diagnosis,causes):
    mapping={
      "SOURCE":"M90_CONTENT_RETRIEVAL",
      "CONTENT":"M91_TRANSFORMATION",
      "PEDAGOGY":"M89_ADAPTIVE_PLANNING",
      "REPRESENTATION":"M92_REPRESENTATION_PLANNING",
      "TIMING":"M84_TEMPORAL_PLANNING",
      "AUDIO":"M85_AUDIO_SYNC",
      "VISUAL":"M95_RENDER_BACKEND",
      "INTERACTION":"M95_RENDER_BACKEND",
      "ACCESSIBILITY":"M93_PRODUCTION_CONTRACT",
      "RENDERER":"M95_RENDER_BACKEND",
      "CONTRACT":"M93_PRODUCTION_CONTRACT",
      "SYSTEM":"M94_BUILD_ENGINE"
    }
    return mapping.get(diagnosis.get("error_type"),"HUMAN_REVIEW")

def select_action(diagnosis,causes):
    layer=route_correction(diagnosis,causes)
    if layer=="M90_CONTENT_RETRIEVAL": return "RETRIEVE"
    if layer=="M91_TRANSFORMATION": return "TRANSFORM"
    if layer=="M92_REPRESENTATION_PLANNING": return "CHANGE_REPRESENTATION"
    if layer=="M95_RENDER_BACKEND": return "CHANGE_BACKEND"
    if layer=="M93_PRODUCTION_CONTRACT": return "UPDATE_CONTRACT"
    if layer=="M89_ADAPTIVE_PLANNING": return "REVIEW"
    if layer=="M94_BUILD_ENGINE": return "RETRY"
    return "REVIEW"
