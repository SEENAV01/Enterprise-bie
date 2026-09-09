import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parents[1]/"src"))
from principals import principal
from policies import policy,rule
from compiler import authorize
from separation import separation_check

def test_allow():
 p=principal("u",capabilities=["GENERATE"])
 pol=policy("p","1",[rule("r","GENERATE","CONTENT")])
 r=authorize({"action":"GENERATE","resource":"CONTENT",
              "capability":"GENERATE"},p,pol)
 assert r["decision"]=="ALLOW"

def test_missing_capability():
 p=principal("u")
 pol=policy("p","1",[rule("r","GENERATE","CONTENT")])
 r=authorize({"action":"GENERATE","resource":"CONTENT",
              "capability":"GENERATE"},p,pol)
 assert r["decision"]=="DENY"

def test_separation():
 assert not separation_check("u",["u"])["valid"]
