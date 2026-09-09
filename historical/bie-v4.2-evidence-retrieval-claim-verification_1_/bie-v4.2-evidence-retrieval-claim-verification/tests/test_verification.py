import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parents[1]/"src"))
from verification_pipeline import prepare_verification
def test_verification():
 item={"id":"x","title":"X","content":"X"}
 src=[{"source_id":"s","title":"University","source_class":"UNIVERSITY"}]
 ev=[{"claim_id":"x_claim_1","source_id":"s","passage":"supports","relation":"SUPPORTS"}]
 r=prepare_verification(item,src,ev)
 assert r["evidence_packet"]["status"]=="VERIFIED"
