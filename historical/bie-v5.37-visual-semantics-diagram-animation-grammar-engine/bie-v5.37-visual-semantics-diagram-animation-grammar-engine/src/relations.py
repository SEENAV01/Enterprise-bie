def visual_relation(source,target,relation_type,props=None):
    return {"source":source,"target":target,
            "relation_type":relation_type,"props":props or {}}

def relation_types():
    return ["ABOVE","BELOW","LEFT_OF","RIGHT_OF","INSIDE","CONNECTED_TO",
            "POINTS_TO","PARALLEL_TO","PERPENDICULAR_TO","EQUAL_TO",
            "CAUSES","DEPENDS_ON","TRANSFORMS_TO","HIGHLIGHTS"]
