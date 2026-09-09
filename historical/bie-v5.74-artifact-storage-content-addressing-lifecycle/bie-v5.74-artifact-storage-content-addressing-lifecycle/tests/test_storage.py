import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parents[1]/"src"))
from identity import artifact_id
from store import put
from lifecycle import transition
from promotion import promotion_allowed

def test_same_bytes_same_id():
 assert artifact_id(b"abc")==artifact_id(b"abc")

def test_lifecycle():
 assert transition("STAGED","VALIDATED")=="VALIDATED"

def test_promotion():
 assert promotion_allowed({"from_state":"VALIDATED",
                            "to_state":"PROMOTED",
                            "validation_ref":"v1"})
