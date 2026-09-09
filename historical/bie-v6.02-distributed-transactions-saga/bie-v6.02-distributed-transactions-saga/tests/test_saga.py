import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parents[1]/"src"))
from saga import step,saga
from compensation import compensation_order
from outbox import outbox_record,mark_published
from inbox import inbox_record,already_processed,mark_processed
from retry import retry_policy,retryable
from transaction import transaction_boundary,is_distributed

def test_saga_steps():
 a=step("a","do_a","undo_a","k1")
 b=step("b","do_b","undo_b","k2")
 s=saga("s","w",[a,b])
 assert compensation_order(["a","b"])==["b","a"]
 assert s["status"]=="STARTED"

def test_outbox_inbox():
 o=mark_published(outbox_record("r","a","E",{},1))
 assert o["status"]=="PUBLISHED"
 i=mark_processed(inbox_record("m","c",1))
 assert already_processed(i)

def test_retry_tx():
 p=retry_policy(3)
 assert retryable(2,p)
 assert is_distributed(transaction_boundary("x",["db","bus"]))

