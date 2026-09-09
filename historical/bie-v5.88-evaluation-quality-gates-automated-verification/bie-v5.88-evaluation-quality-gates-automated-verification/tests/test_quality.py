import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parents[1]/"src"))
from rubric import criterion,score_criterion,weighted_score
from evaluate import evaluation,regression
from gates import gate,evaluate_gate
from release import release_eligibility

def test_rubric():
 c=criterion("accuracy",1,.8)
 r=score_criterion(c,.9)
 assert weighted_score([r])==.9
 assert r["passed"]

def test_gate():
 ev=evaluation("a",[score_criterion(
     criterion("x",1,.8),.9)])
 g=gate("publish",.85,["schema"])
 checks=[{"name":"schema","passed":True}]
 assert evaluate_gate(g,ev,checks)["passed"]

def test_regression():
 a=evaluation("a",[score_criterion(
     criterion("x",1,0),.8)])
 b=evaluation("b",[score_criterion(
     criterion("x",1,0),.9)])
 assert regression(a,b)["regressed"]

def test_release():
 assert release_eligibility([{"passed":True}],True,.95,.9)["eligible"]
