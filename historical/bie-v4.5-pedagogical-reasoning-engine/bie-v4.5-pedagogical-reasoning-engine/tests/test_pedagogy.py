import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parents[1]/"src"))
from pedagogical_engine import plan
def test_plan():
 r=plan(
  [{"id":"a","dimension":"DEFINITION","properties":{"centrality":1}},
   {"id":"b","dimension":"DERIVATION","properties":{}}],
  ["a","b"],[{"source":"a","target":"b"}])
 assert r["schema_version"]=="4.5"
 assert r["dependency_order"]["order"]==["a","b"]
 assert r["strategies"][1]["mode"]=="DERIVE_STEP_BY_STEP"
