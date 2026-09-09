def annotation(annotation_id,review_id,category,
               severity,comment,location=None):
    return {"annotation_id":annotation_id,
            "review_id":review_id,"category":category,
            "severity":severity,"comment":comment,
            "location":location}

def add_annotation(case,record):
    out=dict(case)
    out["annotations"]=list(case.get("annotations",[]))+[record]
    return out
