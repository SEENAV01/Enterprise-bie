import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parents[1]/"src"))
from compiler import compile_transformation

def test_valid():
 req={"output_type":"EXPLANATION","allow_generation":True,
      "constraints":[{"kind":"REQUIRE_SOURCE_CITATION",
                     "severity":"required"}]}
 out=[{"output_id":"o","source_refs":["f1"],
       "generated_refs":[]}]
 r=compile_transformation(req,out,[{"fragment_id":"f1"}])
 assert r["quality_gate"]["valid"]

def test_missing_source():
 req={"output_type":"EXPLANATION"}
 out=[{"output_id":"o","source_refs":["missing"]}]
 r=compile_transformation(req,out,[{"fragment_id":"f1"}])
 assert not r["quality_gate"]["valid"]
