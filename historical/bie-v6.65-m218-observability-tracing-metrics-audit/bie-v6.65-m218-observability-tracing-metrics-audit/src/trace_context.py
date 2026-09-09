def context(trace_id_value,job_id,node_id=None,metadata=None):
    return {"trace_id":trace_id_value,"job_id":job_id,"node_id":node_id,
            "metadata":metadata or {}}
def child(parent,name,span_id):
    return {"span_id":span_id,"name":name,"parent_id":parent["span_id"]}
