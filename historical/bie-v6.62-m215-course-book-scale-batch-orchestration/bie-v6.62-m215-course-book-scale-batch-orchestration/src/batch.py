def batch(i,course,nodes,max_parallel=4): return {"batch_id":i,"course_ref":course,"node_ids":nodes,"max_parallel":max_parallel,"status":"QUEUED"}
def valid(b): return bool(b["batch_id"] and b["course_ref"] and b["node_ids"] and b["max_parallel"]>0)
