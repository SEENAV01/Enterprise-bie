import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parents[1]/"src"))
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

def test_topic_queue_event_command():
 t=topic("t",partitions=2,ordered=True)
 assert supports_order(t)
 assert retryable(queue("q",10,3),2)
 e=event("e","X","p",correlation_id="c")
 assert same_correlation(e,{"correlation_id":"c"})
 assert accepted(command("c","X","p"))["status"]=="ACCEPTED"

def test_delivery_retry_dlq_idempotency():
 g=consumer_group("g","t",2)
 assert owns_partition(g,1)
 d=delivery_policy()
 assert requires_ack(d)
 r=retry_policy(5,"EXPONENTIAL",2)
 assert delay(r,3)==8
 dl=dead_letter_policy("q",5)
 assert dead_lettered(dl,5)
 i=idempotency_key("s","op","k")
 assert same_operation(i,i)

def test_schedule_observability():
 s=scheduled_delivery("m",10)
 assert due(s,10)
 e=messaging_event("e","m","GET","ACKED",2.5,1)
 assert metric(e)["status"]=="ACKED"
