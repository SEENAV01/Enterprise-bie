import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parents[1]/"src"))
from load import cognitive_load,validate_load
from granularity import estimate_granularity,validate_granularity
from sequencing import optimize_sequence
def test_m243():
 u=[{"concept_id":"a","concept_ids":["a"],"duration_minutes":5}]
 assert cognitive_load(u[0])["total"]==1.0
 assert validate_load(cognitive_load(u[0]))["passed"]
 assert validate_granularity(estimate_granularity(u[0]))["passed"]
 assert optimize_sequence(u, {})["order"]==["a"]
