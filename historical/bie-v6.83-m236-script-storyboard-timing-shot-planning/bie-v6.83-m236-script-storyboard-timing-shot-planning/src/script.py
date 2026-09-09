def script_segment(segment_id,concept_id,text,purpose="explain"):
    return {"segment_id":segment_id,"concept_id":concept_id,"text":text,"purpose":purpose}

def build_script(objectives,concepts):
    by_id={c["concept_id"]:c for c in concepts}
    out=[]
    for i,o in enumerate(objectives):
        for j,cid in enumerate(o.get("concept_ids",[])):
            c=by_id.get(cid,{"title":cid})
            out.append(script_segment(f"SEG-{i+1}-{j+1}",cid,
                f"{o['text']}. Key idea: {c['title']}."))
    return out
