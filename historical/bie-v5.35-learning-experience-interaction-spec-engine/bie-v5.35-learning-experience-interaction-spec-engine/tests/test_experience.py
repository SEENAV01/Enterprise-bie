import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parents[1]/"src"))
from compiler import compile_experience

def test_contract():
 c={"lesson_id":"l1","interaction_refs":["i1"]}
 r=compile_experience(c,[{"interaction_id":"i1"}])
 assert r["quality_gate"]["valid"]

def test_missing():
 c={"lesson_id":"l1","interaction_refs":["missing"]}
 r=compile_experience(c,[])
 assert not r["quality_gate"]["valid"]
