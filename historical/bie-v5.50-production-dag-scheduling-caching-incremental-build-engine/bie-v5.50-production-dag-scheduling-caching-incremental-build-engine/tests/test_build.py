import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parents[1]/"src"))
from compiler import compile_build

def test_parallel_and_dependency():
 nodes=[
  {"node_id":"a","dependencies":[],"status":"PENDING"},
  {"node_id":"b","dependencies":[],"status":"PENDING"},
  {"node_id":"c","dependencies":["a"],"status":"PENDING"}]
 r=compile_build(nodes,max_parallel=4)
 assert set(r["batches"][0])=={"a","b"}
 assert r["batches"][1]==["c"]
 assert r["quality_gate"]["valid"]

def test_incremental_invalidation():
 nodes=[
  {"node_id":"a","dependencies":[],"status":"COMPLETE"},
  {"node_id":"b","dependencies":["a"],"status":"COMPLETE"},
  {"node_id":"c","dependencies":["b"],"status":"COMPLETE"},
  {"node_id":"x","dependencies":[],"status":"COMPLETE"}]
 r=compile_build(nodes,changed_ids=["b"])
 assert set(r["invalidated"])=={"b","c"}
 assert "x" not in r["invalidated"]
