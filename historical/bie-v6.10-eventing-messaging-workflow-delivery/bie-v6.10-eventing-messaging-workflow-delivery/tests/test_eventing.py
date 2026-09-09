import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parents[1]/"src"))
from event import event,event_key
from topic import topic,valid
from queue import queue,can_enqueue
from delivery import delivery_policy,retryable
from idempotency import idempotency_key,already_processed,mark_processed
from ordering import ordering_policy,ordering_key
from dlq import dead_letter,requeue
from replay import replay_plan,start
from backpressure import backpressure_policy,should_throttle

def test_event_topic_queue():
 e=event("e","x","p","s",1,"t","1")
 assert event_key(e)==("t","x","e")
 assert valid(topic("x",2))
 assert can_enqueue(queue("q","AT_LEAST_ONCE",10),5)

def test_delivery_idempotency():
 d=delivery_policy("AT_LEAST_ONCE",30,3)
 assert retryable(d,2)
 k=idempotency_key("op","entity","req")
 store=set()
 assert not already_processed(store,tuple(k.values()))
 mark_processed(store,tuple(k.values()))
 assert already_processed(store,tuple(k.values()))

def test_order_dlq_replay():
 o=ordering_policy("workflow",True,"workflow_id")
 assert ordering_key({"workflow_id":"w"},o)=="w"
 assert requeue(dead_letter("m","q",5,"fail"))["status"]=="REQUEUED"
 assert start(replay_plan("t",0,5))["status"]=="RUNNING"

def test_backpressure():
 p=backpressure_policy(10,100,50)
 assert should_throttle(p,10,0)
 assert should_throttle(p,0,100)
