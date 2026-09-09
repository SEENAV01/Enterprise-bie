def trace(trace_id,root_span_id,operation,
          service,correlation_id=None,workflow_id=None):
    return {"trace_id":trace_id,"root_span_id":root_span_id,
            "operation":operation,"service":service,
            "correlation_id":correlation_id,
            "workflow_id":workflow_id}

def child_span_id(trace_id,span_id):
    return f"{trace_id}:{span_id}"
