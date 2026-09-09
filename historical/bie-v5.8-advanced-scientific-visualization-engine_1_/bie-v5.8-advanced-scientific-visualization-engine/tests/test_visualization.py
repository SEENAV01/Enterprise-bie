import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parents[1]/"src"))
from compiler import compile_scientific_visuals
def test_valid():
 r=compile_scientific_visuals(
  equations=[{"equation_id":"e","latex":"x=y"}],
  derivations=[{"step_id":"s","expression":"x=y","operation":"definition"}],
  graphs=[{"graph_id":"g","x_label":"x","y_label":"y","domain":[0,1]}],
  visuals=[{"visual_id":"v","concept_id":"c","mathematical_state":{"x":1}}])
 assert r["quality_gate"]["valid"]
def test_invalid_graph():
 r=compile_scientific_visuals(
  graphs=[{"graph_id":"g","x_label":"","y_label":"y","domain":[0,1]}])
 assert not r["quality_gate"]["valid"]
