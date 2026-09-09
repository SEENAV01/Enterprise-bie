def choose_strategy(complexity,features):
    level=complexity["level"]
    if features.get("3d",0)>0 or features.get("simulation",0)>=2:
        strategy="GPU_3D_SIMULATION"
    elif features.get("simulation",0)>0:
        strategy="HYBRID_2D_SIMULATION"
    elif features.get("equations",0)>=4 or features.get("code",0)>=2:
        strategy="DIAGRAM_CODE_MOTION"
    elif level=="LOW":
        strategy="LIGHTWEIGHT_2D"
    else:
        strategy="STANDARD_2D_MOTION"
    return {"strategy":strategy,"rationale_level":level}
