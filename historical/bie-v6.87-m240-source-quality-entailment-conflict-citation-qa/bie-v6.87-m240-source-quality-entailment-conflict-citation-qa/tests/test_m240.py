import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parents[1]/"src"))
from source_quality import rank_source
from entailment import entailment
from conflicts import detect_conflicts
from citation_qa import citation_completeness
def test_m240():
 assert rank_source({"source_id":"s","authority":1,"recency":1,"specificity":1,"stability":1})["score"]==1
 assert entailment({"claim_id":"c"},{"evidence_id":"e","text":"same claim"})["score"]>=0
 assert detect_conflicts([{"claim_id":"a","topic":"x","polarity":1},{"claim_id":"b","topic":"x","polarity":-1}])
 assert citation_completeness([{"claim_id":"c"}],[{"claim_id":"c","evidence":[1]}])["completeness"]==1
