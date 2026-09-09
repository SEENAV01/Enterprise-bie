import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parents[1]/"src"))
from compiler import compile_representation_plan

def test_selects_animation():
 r=compile_representation_plan(
  ["c"],["o"],{"purpose":"VISUALIZE"},
  [{"candidate_id":"a","representation_type":"ANIMATION",
    "signals":{"fit":3}},
   {"candidate_id":"t","representation_type":"TEXT",
    "signals":{"fit":1}}],
  weights={"fit":1})
 assert r["selected"]["representation_type"]=="ANIMATION"

def test_requirement():
 r=compile_representation_plan(
  ["c"],["o"],{"purpose":"INTERACT"},
  [{"candidate_id":"t","representation_type":"TEXT",
    "signals":{"fit":5}}],
  [{"kind":"REQUIRE_INTERACTION","severity":"required"}])
 assert not r["quality_gate"]["valid"]
