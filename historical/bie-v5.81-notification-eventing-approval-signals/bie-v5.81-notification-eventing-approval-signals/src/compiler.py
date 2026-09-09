from events import event
from routing import approval_signal

def compile_domain_event(event_type,payload,source="bie",
                         correlation_id=None,causation_id=None):
    evt=event(event_type,payload,source,
              correlation_id,causation_id)
    return {"schema_version":"5.81",
            "event":evt,
            "signal":approval_signal(evt),
            "quality_gate":{"valid":True,"errors":[]}}
