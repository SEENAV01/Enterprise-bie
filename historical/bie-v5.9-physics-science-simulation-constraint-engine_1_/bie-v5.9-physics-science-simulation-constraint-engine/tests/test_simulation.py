import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parents[1]/"src"))
from compiler import compile_simulation
def test_valid():
 r=compile_simulation(
  laws=[{"law_id":"l","equation":"x=y","domain":"demo"}],
  simulations=[{"simulation_id":"s","dt":.1,"steps":10,"equations":["x'=1"]}])
 assert r["quality_gate"]["valid"]
def test_bad_dimension():
 r=compile_simulation(
  dimension_checks=[{"lhs":{"dimension":{"exponents":{"m":1}}},
                    "rhs":[{"dimension":{"exponents":{"s":1}}}]}])
 assert not r["quality_gate"]["valid"]
