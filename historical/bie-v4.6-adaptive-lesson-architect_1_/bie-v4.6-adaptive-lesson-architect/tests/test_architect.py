import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parents[1]/"src"))
from lesson_architect import architect
def test_architect():
 r=architect([{"knowledge_id":"x","importance":"CORE","teaching_mode":"DERIVE_STEP_BY_STEP","prerequisites":[]}])
 assert r["schema_version"]=="4.6"
 assert any(b["type"]=="DERIVATION" for b in r["blocks"])
 assert r["policy"]["audio_drives_final_timing"]
