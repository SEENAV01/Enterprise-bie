import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parents[1]/"src"))
from events import audit_event
from log import append_event,validate_append_only
from audit import audit_query

def test_append_only():
 e={"event_id":"1"}
 old=[e]; new=append_event(old,{"event_id":"2"})
 assert validate_append_only(old,new)

def test_query():
 e=audit_event("1","RENDER","t","worker","video@1")
 assert audit_query([e],entity_ref="video@1")[0]["event_type"]=="RENDER"
