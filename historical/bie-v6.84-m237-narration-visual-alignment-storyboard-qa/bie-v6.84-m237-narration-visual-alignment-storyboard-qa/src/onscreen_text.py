def text_overlay(overlay_id,segment_id,text,kind="KEY_TERM",
                 start=None,end=None):
    return {"overlay_id":overlay_id,"segment_id":segment_id,"text":text,
            "kind":kind,"start":start,"end":end}

def plan_overlays(segments):
    return [text_overlay(f"TXT-{i+1}",s["segment_id"],
                         s.get("text",""),"SUMMARY")
            for i,s in enumerate(segments)]

def validate_overlays(overlays,max_words=18):
    errors=[]
    for o in overlays:
        if len(o["text"].split())>max_words:
            errors.append({"overlay_id":o["overlay_id"],"error":"TOO_DENSE"})
    return {"passed":not errors,"errors":errors}
