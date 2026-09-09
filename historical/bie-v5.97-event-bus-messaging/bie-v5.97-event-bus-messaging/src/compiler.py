from event import event
from topic import topic,subscription
from bus import publish

def compile_message(event_id,event_type,payload,
                    producer,topic_id,
                    correlation_id=None,
                    causation_id=None):
    e=event(event_id,event_type,payload,producer,
            correlation_id,causation_id)
    t=topic(topic_id,[event_type])
    return {"schema_version":"5.97",
            "event":e,"topic":t,
            "publication":publish(e,topic_id),
            "quality_gate":{"valid":True,"errors":[]}}
