import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parents[1]/"src"))
from review import review_case,transition
from reviewer import reviewer,authorized
from approval import valid_decision
from override import override_allowed
from dual_control import dual_control

def test_transition():
 c=review_case("r","a","QUALITY")
 c=transition(c,"IN_REVIEW")
 assert c["state"]=="IN_REVIEW"

def test_authorized():
 assert authorized(reviewer("x",["SUBJECT"]), "SUBJECT")

def test_decision():
 assert valid_decision({"decision":"APPROVE","rationale":"ok"})

def test_override():
 assert override_allowed({"reason":"exception",
                          "authority":"SENIOR_REVIEWER"})

def test_dual():
 ds=[{"reviewer_id":"a","decision":"APPROVE"},
     {"reviewer_id":"b","decision":"APPROVE"}]
 assert dual_control(ds)
