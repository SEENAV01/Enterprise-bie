from topic import topic,supports_order
from queue import queue,retryable
from event import event,same_correlation
from command import command,accepted
from consumer import consumer_group,owns_partition
from delivery import delivery_policy,requires_ack
from retry import retry_policy,delay
from dead_letter import dead_letter_policy,dead_lettered
from idempotency import idempotency_key,same_operation
from scheduling import scheduled_delivery,due
from observability import messaging_event,metric

def compile_messaging():
    t=topic("workflow-events",604800,12,True)
    q=queue("workflow-commands",30,5)
    e=event("evt-1","WorkflowStarted",
            "obj://events/evt-1",
            "tenant-a","corr-1")
    c=accepted(command("cmd-1","StartWorkflow",
                       "obj://commands/cmd-1",
                       "tenant-a","corr-1"))
    cg=consumer_group("workflow-workers",
                      "workflow-events",4)
    d=delivery_policy("AT_LEAST_ONCE",True)
    r=retry_policy(5,"EXPONENTIAL",2)
    dl=dead_letter_policy("workflow-commands",5,
                          ["VALIDATION_ERROR","TIMEOUT"])
    idem=idempotency_key("tenant-a","StartWorkflow","cmd-1")
    sched=scheduled_delivery("msg-1",1000,"UTC")
    obs=messaging_event("msg-event","cmd-1",
                        "DELIVER","ACKED",12.5,2)
    return {"schema_version":"6.22",
            "topic":t,"queue":q,"event":e,
            "command":c,"consumer_group":cg,
            "delivery":d,"retry":r,
            "dead_letter":dl,"idempotency":idem,
            "schedule":sched,"observability":obs,
            "quality_gate":{"valid":True,"errors":[]},
            "checks":{
              "ordered_topic":supports_order(t),
              "retryable":retryable(q,2),
              "correlated":same_correlation(e,{
                  "correlation_id":"corr-1"}),
              "command_accepted":c["status"]=="ACCEPTED",
              "partition_owned":owns_partition(cg,0),
              "ack_required":requires_ack(d),
              "retry_delay":delay(r,3),
              "dead_lettered":dead_lettered(dl,5),
              "idempotent":same_operation(
                   idem,idempotency_key(
                       "tenant-a","StartWorkflow","cmd-1")),
              "scheduled_due":due(sched,1000),
              "metric":metric(obs)
            }}
