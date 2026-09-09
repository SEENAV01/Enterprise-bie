import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parents[1]/"src"))
from queue import review_item,enqueue,dequeue
from assignment import reviewer,assign
from decision import review_decision
from escalation import escalation
from override import override_request,approve_override

def test_queue():
 q=[]; enqueue(q,review_item("a",5,{}))
 assert dequeue(q)["status"]=="IN_REVIEW"

def test_assignment():
 r=reviewer("r",["EDITOR"])
 i=assign(review_item("a",1,{},required_role="EDITOR"),r)
 assert i["reviewer_id"]=="r"

def test_decision():
 assert review_decision("a","r","APPROVE","ok")["decision"]=="APPROVE"

def test_override():
 x=override_request("a","REJECT","APPROVE","r","reason")
 assert approve_override(x,"admin")["status"]=="APPROVED"

