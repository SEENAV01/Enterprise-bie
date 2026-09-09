import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parents[1]/"src"))

from asset import asset,valid
from spec import specification
from prompt import prompt
from diagram import diagram_spec
from equation import equation_spec
from animation import animation_spec
from asset_evidence import evidence_binding,grounded
from manifest import manifest,valid as manifest_valid
from provenance import provenance,traceable
from verification import verification,passed

def test_asset_contracts():
    a=asset("a","DIAGRAM","Explain","s1","A diagram",evidence_ids=["e"])
    s=specification("s","a","VECTOR","1920x1080","SVG")
    p=prompt("p","a","Create a diagram.")
    d=diagram_spec("a","RELATIONSHIP",["x"],[],["x"])
    e=equation_spec("eq","F = ma")
    an=animation_spec("an",5,[{"action":"DRAW"}])
    b=evidence_binding("a",["e"],["record"])
    m=manifest("m","sb",[a])
    pr=provenance("m",["sb"],["s1"],["e"])
    v=verification("v","m","PASS",["e"])
    assert valid(a) and s["asset_id"]=="a" and p["asset_id"]=="a"
    assert d["diagram_type"]=="RELATIONSHIP" and e["latex"]=="F = ma"
    assert an["actions"] and grounded(b) and manifest_valid(m)
    assert traceable(pr) and passed(v)
