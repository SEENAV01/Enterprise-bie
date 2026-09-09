ROLE_PRIORITY={
"PRIMARY":100,"SECONDARY":70,"SUPPORTING":40,"DECORATIVE":10
}

def rank_object(obj):
    return (
      ROLE_PRIORITY.get(obj.get("role","SUPPORTING"),40),
      float(obj.get("semantic_importance",0)),
      float(obj.get("narration_relevance",0))
    )

def rank_objects(objects):
    return sorted(objects,key=rank_object,reverse=True)
