from envelope import event_envelope,valid
from topic import topic,active as topic_active
from subscription import subscription,active as subscription_active
from ordering import ordering,ordered
from delivery import delivery_guarantee,retryable
from retry import retry_policy,allowed
from dead_letter import dead_letter,traceable
from deduplication import deduplication,matches
from consumer import consumer,active as consumer_active
from ack import acknowledgement,acknowledged
from audit import messaging_event,successful
from observability import messaging_metric,healthy

def compile_messaging():
    env=event_envelope("evt-1","artifact.updated",
                       {"artifact_id":"a-1"},"artifact-service")
    tp=topic("topic-1","artifact-events",3,"7d")
    sub=subscription("sub-1","topic-1","group-a","type == 'artifact.updated'")
    ordp=ordering("KEY","artifact_id")
    dg=delivery_guarantee("AT_LEAST_ONCE")
    rp=retry_policy(5,500,2.0,30000)
    dl=dead_letter("topic-1","MAX_RETRIES","evt-1")
    dd=deduplication("evt-1",86400000)
    c=consumer("consumer-1","group-a",4,"EXPLICIT")
    ack=acknowledgement("evt-1","consumer-1","ACKED",10)
    ev=messaging_event("me-1","PUBLISH","topic-1","SUCCESS","producer-1")
    met=messaging_metric("mm-1","topic-1","PUBLISH","SUCCESS",12,1)
    return {"schema_version":"6.43","envelope":env,"topic":tp,
            "subscription":sub,"ordering":ordp,
            "delivery":dg,"retry":rp,"dead_letter":dl,
            "deduplication":dd,"consumer":c,"ack":ack,
            "audit":ev,"observability":met,
            "quality_gate":{"valid":True,"errors":[]},
            "checks":{
              "envelope_valid":valid(env),
              "topic_active":topic_active(tp),
              "subscription_active":subscription_active(sub),
              "ordering_enabled":ordered(ordp),
              "delivery_retryable":retryable(dg),
              "retry_allowed":allowed(rp,3),
              "dead_letter_traceable":traceable(dl),
              "deduplication_match":matches(dd,"evt-1"),
              "consumer_active":consumer_active(c),
              "acknowledged":acknowledged(ack),
              "audit_success":successful(ev),
              "observability_healthy":healthy(met)
            }}
