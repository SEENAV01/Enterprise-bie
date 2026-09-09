import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parents[1]/"src"))
from contracts import REQUIRED_STAGES,stage_contract
from pipeline import pipeline_run,advance
from artifact import artifact,grounded
from lineage import lineage,traceable
from config import canonical_config,compatible
from validation import validate_pipeline,complete

def test_contract_order():
 r=pipeline_run("r","book://x")
 assert [x["stage"] for x in r["stages"]]==REQUIRED_STAGES
 assert all(stage_contract(s)["stage"]==s for s in REQUIRED_STAGES)

def test_advance_and_validation():
 r=pipeline_run("r","book://x")
 for s in REQUIRED_STAGES: r=advance(r,s,"COMPLETE",f"ref://{s}")
 assert validate_pipeline(r)["valid"]
 assert complete(r)

def test_lineage_grounding():
 a=artifact("a","lesson","lesson","ref",["book://x"])
 l=lineage("a",["script"],["book://x"])
 assert grounded(a) and traceable(l)
 assert compatible(canonical_config())
