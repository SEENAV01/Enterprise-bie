PRIMITIVES={
 "ARROW","LABEL","AXIS","POINT","LINE","VECTOR","FIELD_LINE",
 "PARTICLE","SHAPE","EQUATION","TABLE","CHART","GRID","CALLOUT",
 "TIMELINE","ICON","DIAGRAM_NODE","DIAGRAM_EDGE"
}
def primitive(kind,primitive_id,props=None):
    if kind not in PRIMITIVES: raise ValueError("UNKNOWN_PRIMITIVE")
    return {"primitive_id":primitive_id,"kind":kind,"props":props or {}}
