import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parents[1]/"src"))
from events import event
from consumer import deliver
from retry import retry_delay
from routing import approval_signal

def test_event():
 e=event("REVIEW_APPROVED",{},correlation_id="c")
 assert e["event_type"]=="REVIEW_APPROVED"
 assert approval_signal(e)

def test_idempotent():
 seen=[]
 processed=set()
 e=event("X",{})
 f=lambda x: seen.append(x["event_id"])
 assert deliver(e,"c",f,processed)["status"]=="DELIVERED"
 assert deliver(e,"c",f,processed)["status"]=="DUPLICATE"
 assert len(seen)==1

def test_retry():
 assert retry_delay(3)==4
