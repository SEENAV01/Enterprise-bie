import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parents[1]/"src"))
from event import event,command
from topic import topic,subscription
from idempotent import consume_once
from retry import delivery_retry,retryable
from dead_letter import dead_letter,is_dead_letter
from replay import replay_request,replayable
from order import message_position,ordered

def test_event_ids():
 e=event("e","done",{}, "worker","wf","task")
 c=command("c","run",{},"planner","wf","e")
 assert e["correlation_id"]=="wf"
 assert c["causation_id"]=="e"

def test_idempotency():
 seen=set()
 assert consume_once(seen,"e","consumer")
 assert not consume_once(seen,"e","consumer")

def test_retry_dlq():
 r=delivery_retry("e",4,5)
 assert retryable(r)
 assert is_dead_letter(dead_letter("e",{}, "error",5))

def test_replay_order():
 assert replayable(replay_request("t",1,4))
 assert ordered(message_position(0,1),message_position(0,2))
