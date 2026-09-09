def correlation_context(correlation_id,workflow_id=None,
                       request_id=None):
    return {"correlation_id":correlation_id,
            "workflow_id":workflow_id,
            "request_id":request_id}

def attach(record,context):
    out=dict(record); out.update(context); return out
