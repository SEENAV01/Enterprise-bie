from trace import trace
from span import span
from propagation import context
from log import log_event
from metric import metric

def compile_observability(trace_id,span_id,
                          operation,service,
                          correlation_id=None,
                          workflow_id=None):
    t=trace(trace_id,span_id,operation,service,
            correlation_id,workflow_id)
    s=span(span_id,trace_id,None,operation,
           service,0,None,"OK")
    c=context(trace_id,span_id,
              correlation_id,workflow_id)
    l=log_event(0,"INFO",operation,service,
                trace_id,span_id,correlation_id)
    m=metric("operation.started",1,0,
             {"service":service,"operation":operation})
    return {"schema_version":"6.03",
            "trace":t,"span":s,
            "propagation_context":c,
            "log":l,"metric":m,
            "quality_gate":{"valid":True,"errors":[]}}
