def classify(node,learner_level="INTERMEDIATE"):
    if node.get("required",False):
        return "CORE"
    if node.get("importance",0)>=0.8 and node.get("level","FOUNDATION") in ("FOUNDATION","INTERMEDIATE"):
        return "CORE"
    if node.get("kind") in ("COUNTEREXAMPLE","LIMITATION","MODERN_CONTEXT","CROSS_DOMAIN"):
        return "DEEP_DIVE"
    return "CORE" if node.get("level","FOUNDATION")=="FOUNDATION" else "DEEP_DIVE"
