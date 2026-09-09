def context(trace_id,span_id,
             correlation_id=None,workflow_id=None):
    return {"trace_id":trace_id,"span_id":span_id,
            "correlation_id":correlation_id,
            "workflow_id":workflow_id}

def child_context(parent,child_span_id):
    return context(parent["trace_id"],child_span_id,
                   parent.get("correlation_id"),
                   parent.get("workflow_id"))
