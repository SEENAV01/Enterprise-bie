import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parents[1]/"src"))
from system import compile_component
def test_equation():
 r=compile_component({"type":"EQUATION","expression":"P=VI"})
 assert r["quality"]["valid"]
 assert r["component_contract"]["semantic_role"]=="mathematical_reasoning"
def test_graph():
 r=compile_component({"type":"GRAPH","x":[0,1],
  "series":[{"name":"x","values":[1,2]}]})
 assert r["quality"]["valid"]
