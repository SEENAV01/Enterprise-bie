def trace_response(response,skill_ids):
    score=float(response.get("score",0))
    return [{"skill_id":s,"score":score,"item_id":response.get("item_id")}
            for s in skill_ids]

def trace_batch(responses):
    return [x for r in responses for x in trace_response(r,r.get("skill_ids",[]))]
