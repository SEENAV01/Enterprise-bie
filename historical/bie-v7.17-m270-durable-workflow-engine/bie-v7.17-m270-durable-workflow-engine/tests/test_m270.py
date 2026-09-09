import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parents[1]/"src"))
from definition import workflow_definition
from engine import start,transition
from persistence import persist,resume
def test_m270():
 d=workflow_definition("w",["A","B","COMPLETED"],{"A:GO":"B","B:DONE":"COMPLETED"},"A")
 i=start(d,"1"); assert transition(d,i,"GO")["ok"]; assert i["state"]=="B"
 assert transition(d,i,"BAD")["ok"] is False
 s={}; persist(i,s); assert resume("1",s)["ok"]
