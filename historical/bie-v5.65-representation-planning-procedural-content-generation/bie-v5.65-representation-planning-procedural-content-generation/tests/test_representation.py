import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parents[1]/"src"))
from strategy import select_strategy
from validation import validate_representation

def test_strategy_selection():
 s={"modality":"animation","generator_type":"scene-template"}
 assert select_strategy({"modality":"animation"},[s])==s

def test_validation():
 assert validate_representation(
  {"output_ref":"x","semantic_refs":["force"]},
  {"checks":["HAS_OUTPUT","HAS_SEMANTIC_REFS"]})["valid"]
