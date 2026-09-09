MODALITIES=[
 "STATIC_DIAGRAM","2D_ANIMATION","3D_ANIMATION","CHART",
 "SIMULATION","PROCESS_DIAGRAM","TIMELINE","EQUATION_BUILD",
 "TABLE","VISUAL_METAPHOR","MAP","CODE_VISUALIZATION"
]
def modality(name,reason=None):
    if name not in MODALITIES: raise ValueError("UNKNOWN_MODALITY")
    return {"modality":name,"reason":reason}
