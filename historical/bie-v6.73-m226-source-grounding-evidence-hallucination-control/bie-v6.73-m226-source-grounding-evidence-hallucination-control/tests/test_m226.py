import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parents[1]/"src"))
from source import source,valid_source
from evidence import evidence
from grounding import ground_claim
from hallucination import risk
def test_m226():
 s=source("s","Book","ref://book"); assert valid_source(s)
 e=evidence("e","s","electric force",["c"],.9)
 g=ground_claim({"claim_id":"c","text":"x"},[e])
 assert g["grounded"]
 assert risk({"claim_id":"c"},g)["level"]=="LOW"
