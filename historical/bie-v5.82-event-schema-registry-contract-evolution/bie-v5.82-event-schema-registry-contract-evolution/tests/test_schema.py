import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parents[1]/"src"))
from registry import register,get
from validate import validate_event
from compatibility import compatibility
from contracts import contract_match
from evolution import evolution_plan

def test_registry():
 r={}; register(r,"X","1",{"required":["a"]})
 assert get(r,"X","1")

def test_validation():
 assert validate_event({"a":1},{"required":["a"]})["valid"]

def test_compat():
 assert compatibility({"required":["a"]},
                       {"required":["a","b"]})["backward"] is False

def test_contract():
 p={"event_type":"X","version":"1"}
 c={"event_type":"X","accepted_versions":["1","2"]}
 assert contract_match(p,c)
