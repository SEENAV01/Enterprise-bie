RELATIONS=[
"PRECEDES","FOLLOWS","CAUSES","EXPLAINS","REQUIRES",
"DERIVES_FROM","RESULTS_IN","EXEMPLIFIES","APPLIES_TO",
"CONTRASTS_WITH","LIMITED_BY","EXCEPTS","SUPPORTS"
]

def link(source_id,target_id,relation,confidence="CANDIDATE"):
    if relation not in RELATIONS: raise ValueError("UNKNOWN_RELATION")
    return {"source":source_id,"target":target_id,
            "relation":relation,"confidence":confidence}
