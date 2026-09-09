import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parents[1]/"src"))
from source import source,valid
from segments import segment,ordered
from evidence import evidence,grounded
from knowledge import concept,relationship
from provenance import provenance,traceable
from verification import verification,passed

def test_source_and_segments():
    s=source("s","file://x")
    assert valid(s)
    xs=ordered([segment("b","s",2,1),segment("a","s",1,1)])
    assert [x["segment_id"] for x in xs]==["a","b"]

def test_grounding_and_verification():
    e=evidence("e","s",["a"],"claim")
    c=concept("c","Concept",evidence_ids=["e"])
    p=provenance("c",["s"],["e"],"extract")
    v=verification("v","c","PASS",["e"])
    assert grounded(e)
    assert c["evidence_ids"]==["e"]
    assert traceable(p) and passed(v)
    assert relationship("r","c","c","related",["e"])["evidence_ids"]==["e"]
