def check_result(check_id,category,status,
                severity="INFO",message="",evidence=None):
    return {"check_id":check_id,"category":category,
            "status":status,"severity":severity,
            "message":message,"evidence":evidence or {}}

def summarize(results):
    counts={"PASS":0,"WARN":0,"FAIL":0}
    for r in results:
        counts[r.get("status","WARN")]=counts.get(r.get("status","WARN"),0)+1
    return counts
